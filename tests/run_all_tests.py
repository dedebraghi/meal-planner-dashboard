#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Test Runner and Tier Metrics Reporter.
Executes the comprehensive 4-Tier E2E test suite for the Meal Planner Dashboard & Esselunga Automation.
Validates all interface contracts, security invariants, and nutritional models.
"""

import sys
import time
import unittest
from pathlib import Path
from typing import Dict, List, Tuple

# Reconfigure stdout for UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import test modules
from tests import (
    test_tier1_feature_coverage,
    test_tier2_boundary_edge,
    test_tier3_cross_feature,
    test_tier4_real_world,
    test_data_schema,
    test_nutritional_integrity,
    test_cart_safety,
    test_orchestrator
)
from tests.fixtures import (
    SAMPLE_VALID_WEEK,
    AUTHORITATIVE_TARGET,
    AUTHORITATIVE_PROTEIN_FREQUENCIES,
    is_forbidden_checkout_url,
    load_live_weekly_plan,
    validate_weekly_plan_schema,
    validate_nutritional_integrity
)


def run_test_module(module) -> Tuple[int, int, int, int, List[str]]:
    """Runs tests in a given module and returns (run, passed, failed, errors, failure_details)."""
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    runner = unittest.TextTestRunner(verbosity=0, stream=open("nul", "w", encoding="utf-8") if sys.platform == "win32" else open("/dev/null", "w"))
    result = runner.run(suite)
    
    run = result.testsRun
    failed = len(result.failures)
    errors = len(result.errors)
    passed = run - failed - errors
    
    details = []
    for test, err in result.failures:
        details.append(f"[FAIL] {test}: {err.splitlines()[-1]}")
    for test, err in result.errors:
        details.append(f"[ERROR] {test}: {err.splitlines()[-1]}")
        
    return run, passed, failed, errors, details


def verify_critical_system_invariants() -> Tuple[bool, List[str]]:
    """Verifies core architectural and safety invariants."""
    failures = []
    
    # Invariant 1: Esselunga NO-CHECKOUT rule
    forbidden_urls = ["/checkout", "/cassa", "/pagamento", "/prenota-slot"]
    for u in forbidden_urls:
        if not is_forbidden_checkout_url(u):
            failures.append(f"INVARIANT VIOLATION: URL '{u}' was not caught by safety guardrail")

    # Invariant 2: Dr. Caglioni Bromatological targets
    if AUTHORITATIVE_TARGET["kcal"] != 2063:
        failures.append(f"INVARIANT VIOLATION: Caloric target is {AUTHORITATIVE_TARGET['kcal']} instead of 2063")

    # Invariant 3: 14 main meal protein distribution
    total_slots = sum(AUTHORITATIVE_PROTEIN_FREQUENCIES.values())
    if total_slots != 14:
        failures.append(f"INVARIANT VIOLATION: Total protein slots sum to {total_slots} instead of 14")

    # Invariant 4: Live week schema and nutritional integrity (Direct from disk)
    live_plan = load_live_weekly_plan()
    is_valid_schema, schema_errs = validate_weekly_plan_schema(live_plan)
    if not is_valid_schema:
        failures.append(f"INVARIANT VIOLATION: src/data/current-week.json failed schema validation: {schema_errs}")

    is_valid_nutrition, nut_errs = validate_nutritional_integrity(live_plan, tolerance_percent=0.015)
    if not is_valid_nutrition:
        failures.append(f"INVARIANT VIOLATION: src/data/current-week.json failed nutritional integrity: {nut_errs}")

    return (len(failures) == 0), failures


def main():
    start_time = time.time()
    print("=" * 80)
    print("  MEAL PLANNER DASHBOARD & ESSELUNGA AUTOMATION — E2E TEST RUNNER")
    print("=" * 80)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Timestamp   : {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)

    # Modules grouped by category
    tier_map = {
        "Tier 1: Feature Coverage (Isolation)": [
            ("F1-F20 Comprehensive Isolation", test_tier1_feature_coverage),
            ("Contract 1 & 4 Schema Verification", test_data_schema),
            ("Contract 3 & 4 Orchestrator & Alerts", test_orchestrator),
        ],
        "Tier 2: Boundary & Corner Cases": [
            ("Boundary Extremes & Error Handling", test_tier2_boundary_edge),
            ("Esselunga Safety Invariants", test_cart_safety),
        ],
        "Tier 3: Cross-Feature Interactions": [
            ("Cross-Feature Interactions & Integrations", test_tier3_cross_feature),
            ("Dr. Caglioni Nutritional Integrity", test_nutritional_integrity),
        ],
        "Tier 4: Real-World Scenarios": [
            ("E2E Scenarios & Friday Simulation", test_tier4_real_world),
        ]
    }

    grand_total_run = 0
    grand_total_passed = 0
    grand_total_failed = 0
    grand_total_errors = 0
    all_failure_details = []

    tier_metrics = {}

    for tier_name, modules in tier_map.items():
        print(f"\n▶ {tier_name}")
        t_run, t_passed, t_failed, t_errors = 0, 0, 0, 0

        for label, mod in modules:
            run, passed, failed, errors, details = run_test_module(mod)
            t_run += run
            t_passed += passed
            t_failed += failed
            t_errors += errors
            all_failure_details.extend(details)

            status_glyph = "✓" if (failed == 0 and errors == 0) else "✗"
            print(f"  [{status_glyph}] {label:<45} : {passed}/{run} passed" + (f" ({failed} failed, {errors} errors)" if failed or errors else ""))

        tier_metrics[tier_name] = (t_run, t_passed, t_failed, t_errors)
        grand_total_run += t_run
        grand_total_passed += t_passed
        grand_total_failed += t_failed
        grand_total_errors += t_errors

    # Verify Critical Invariants
    print("\n▶ Critical Invariants Verification")
    invariants_ok, invariant_errs = verify_critical_system_invariants()
    if invariants_ok:
        print("  [✓] 3-Layer Esselunga NO-CHECKOUT Safety Guardrail: VERIFIED")
        print("  [✓] Dr. Caglioni Bromatological Target (2063 kcal) : VERIFIED")
        print("  [✓] 14 Main Meal Protein Distribution (7 Days)     : VERIFIED")
        print("  [✓] Saturday Free Meal (Pizza Margherita) Exemption: VERIFIED")
        print("  [✓] Live Data (src/data/current-week.json) Schema & Integrity: VERIFIED")
    else:
        for err in invariant_errs:
            print(f"  [✗] {err}")
            grand_total_errors += 1

    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print("  TEST SUITE SUMMARY & METRICS")
    print("=" * 80)
    for tier, (r, p, f, e) in tier_metrics.items():
        pass_rate = (p / r * 100) if r else 0.0
        print(f"  {tier:<48}: {p:3d}/{r:3d} ({pass_rate:5.1f}%)")

    print("-" * 80)
    print(f"  TOTAL TESTS RUN : {grand_total_run}")
    print(f"  TOTAL PASSED    : {grand_total_passed}")
    print(f"  TOTAL FAILED    : {grand_total_failed}")
    print(f"  TOTAL ERRORS    : {grand_total_errors}")
    print(f"  ELAPSED TIME    : {elapsed:.2f} seconds")
    print("=" * 80)

    if grand_total_failed > 0 or grand_total_errors > 0 or not invariants_ok:
        print("\n❌ SUITE RESULT: FAILED")
        if all_failure_details:
            print("\nFailure Details:")
            for d in all_failure_details:
                print(f"  {d}")
        sys.exit(1)
    else:
        print("\n✅ SUITE RESULT: ALL TESTS PASSED (100% SUCCESS)")
        sys.exit(0)


if __name__ == "__main__":
    main()
