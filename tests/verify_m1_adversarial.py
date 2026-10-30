"""
Adversarial Verification Script for Milestone M1
Empirically verifies:
1. Macronutrient math across all 7 days and 35 meals in src/data/current-week.json
2. Discrepancies between meal macros and daily totals
3. 14 protein frequency distributions against Dr. Caglioni's clinical rules
4. Seasonal produce validation
5. Cart summary mathematical consistency
"""

import json
import sys
from pathlib import Path

# Reconfigure stdout for UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DATA_FILE = Path(r"C:\Users\david\Desktop\Progetti\meal-planner-dashboard\src\data\current-week.json")

def verify():
    print("=" * 80)
    print("ADVERSARIAL EMPIRICAL VERIFICATION HARNESS - MILESTONE M1")
    print("=" * 80)

    if not DATA_FILE.exists():
        print(f"FAIL: File not found: {DATA_FILE}")
        return False

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    findings = []
    errors = []
    warnings = []

    # 1. Target macros
    target = data.get("macro_target", {})
    exp_target = {"kcal": 2063, "proteins_g": 112, "carbs_g": 251, "fats_g": 68}
    print(f"\n[1] Target Bromatological Baseline: {target}")
    for k, v in exp_target.items():
        if target.get(k) != v:
            errors.append(f"macro_target.{k} = {target.get(k)}, expected {v}")

    # 2. Check 7 days and 35 meals
    days = data.get("days", [])
    if len(days) != 7:
        errors.append(f"Expected 7 days, found {len(days)}")

    expected_meal_slots = ["colazione", "pranzo", "spuntino_pomeriggio", "cena", "dopocena"]
    total_meals_inspected = 0
    daily_stats = []

    for d_idx, day in enumerate(days):
        day_name = day.get("day_name", f"Day_{d_idx}")
        date_str = day.get("date", "")
        reported_daily = day.get("daily_macros", {})
        
        meals = day.get("meals", {})
        if len(meals) != 5:
            errors.append(f"{day_name} ({date_str}): expected 5 meals, found {len(meals)}")

        calc_kcal = 0
        calc_carbs = 0
        calc_proteins = 0
        calc_fats = 0

        for slot in expected_meal_slots:
            if slot not in meals:
                errors.append(f"{day_name} ({date_str}): missing slot '{slot}'")
                continue

            meal = meals[slot]
            total_meals_inspected += 1

            m_kcal = meal.get("kcal", 0)
            macros = meal.get("macros", {})
            m_carbs = macros.get("carbs_g", 0)
            m_prot = macros.get("proteins_g", 0)
            m_fats = macros.get("fats_g", 0)

            calc_kcal += m_kcal
            calc_carbs += m_carbs
            calc_proteins += m_prot
            calc_fats += m_fats

            # Sanity check: Atwater macro calculation (Carbs*4 + Prot*4 + Fats*9)
            atwater_kcal = round((m_carbs * 4) + (m_prot * 4) + (m_fats * 9), 1)
            if abs(atwater_kcal - m_kcal) > 40 and not meal.get("is_free_meal"):
                warnings.append(f"{day_name} {slot}: reported kcal {m_kcal} vs Atwater estimated {atwater_kcal} (diff={abs(atwater_kcal - m_kcal):.1f})")

            # Check ingredients
            ings = meal.get("ingredients", [])
            if len(ings) == 0 and not meal.get("is_free_meal"):
                errors.append(f"{day_name} {slot}: 0 ingredients")

            # Check recipe steps
            steps = meal.get("recipe_steps", [])
            if len(steps) == 0:
                errors.append(f"{day_name} {slot}: 0 recipe steps")

        # Compare calculated daily sums with reported daily_macros
        rep_kcal = reported_daily.get("kcal", 0)
        rep_carbs = reported_daily.get("carbs_g", 0)
        rep_prot = reported_daily.get("proteins_g", 0)
        rep_fats = reported_daily.get("fats_g", 0)

        diff_kcal = abs(calc_kcal - rep_kcal)
        diff_carbs = abs(calc_carbs - rep_carbs)
        diff_prot = abs(calc_proteins - rep_prot)
        diff_fats = abs(calc_fats - rep_fats)

        if diff_kcal > 2:
            errors.append(f"[MATH BUG] {day_name} ({date_str}): daily kcal mismatch: sum(meals)={calc_kcal} kcal vs daily_macros={rep_kcal} kcal (delta: {diff_kcal} kcal)")
        if diff_carbs > 2:
            errors.append(f"[MATH BUG] {day_name} ({date_str}): carbs mismatch: sum(meals)={calc_carbs}g vs daily_macros={rep_carbs}g")
        if diff_prot > 2:
            errors.append(f"[MATH BUG] {day_name} ({date_str}): proteins mismatch: sum(meals)={calc_proteins}g vs daily_macros={rep_prot}g")
        if diff_fats > 2:
            errors.append(f"[MATH BUG] {day_name} ({date_str}): fats mismatch: sum(meals)={calc_fats}g vs daily_macros={rep_fats}g")

        # Check target tolerance (±1.5% target kcal = 2063 -> 2032 to 2094 kcal)
        target_kcal = exp_target["kcal"]
        pct_dev = (calc_kcal - target_kcal) / target_kcal * 100
        if abs(pct_dev) > 1.5:
            errors.append(f"[CLINICAL DEFICIT] {day_name} ({date_str}): sum(meals)={calc_kcal} kcal deviates {pct_dev:+.2f}% from target ({target_kcal} kcal), exceeding ±1.5% tolerance")

        daily_stats.append({
            "day": day_name,
            "date": date_str,
            "calc_kcal": calc_kcal,
            "rep_kcal": rep_kcal,
            "calc_carbs": calc_carbs,
            "calc_prot": calc_proteins,
            "calc_fats": calc_fats,
            "pct_dev": pct_dev
        })

    print(f"\nTotal meals inspected: {total_meals_inspected} / 35")
    print("\n[2] Daily Macronutrient Reconciliation Table:")
    print(f"{'Day':<12} | {'Date':<10} | {'Sum(meals)':<11} | {'daily_macros':<12} | {'Carbs(g)':<8} | {'Prot(g)':<8} | {'Fats(g)':<8} | {'Dev from 2063':<13}")
    print("-" * 95)
    for s in daily_stats:
        status_flag = "✓" if abs(s['pct_dev']) <= 1.5 and abs(s['calc_kcal'] - s['rep_kcal']) <= 2 else "❌"
        print(f"{s['day']:<12} | {s['date']:<10} | {s['calc_kcal']:<11} | {s['rep_kcal']:<12} | {s['calc_carbs']:<8} | {s['calc_prot']:<8} | {s['calc_fats']:<8} | {s['pct_dev']:+.2f}% {status_flag}")

    # 3. Protein frequency distribution across 14 main meals (Pranzo and Cena)
    print("\n" + "=" * 80)
    print("[3] PROTEIN FREQUENCY VERIFICATION (14 MAIN MEALS)")
    print("=" * 80)

    AUTHORITATIVE_FREQUENCIES = {
        "carne_bianca": 2,
        "carne_rossa": 1,
        "affettati_magri": 1,
        "pesce": 2,
        "uova": 2,
        "legumi_tofu": 3,
        "formaggi": 2,
        "pasto_libero": 1
    }

    # Normalized mapping from UI strings to canonical tokens
    CATEGORY_NORMALIZATION = {
        "carne bianca": "carne_bianca",
        "carne rossa": "carne_rossa",
        "affettati magri": "affettati_magri",
        "pesce fresco": "pesce",
        "pesce": "pesce",
        "uova": "uova",
        "legumi": "legumi_tofu",
        "legumi e tofu": "legumi_tofu",
        "legumi_tofu": "legumi_tofu",
        "formaggi": "formaggi",
        "pasto libero": "pasto_libero",
        "pasto_libero": "pasto_libero"
    }

    normalized_counts = {k: 0 for k in AUTHORITATIVE_FREQUENCIES}
    raw_categories_used = []
    main_meals = []

    for day in days:
        for slot in ["pranzo", "cena"]:
            m = day["meals"][slot]
            raw_cat = m.get("category", "")
            raw_categories_used.append(raw_cat)
            is_free = m.get("is_free_meal", False)
            norm_key = "pasto_libero" if is_free else CATEGORY_NORMALIZATION.get(raw_cat.strip().lower(), "UNKNOWN")
            
            main_meals.append((day["day_name"], slot, m.get("title"), raw_cat, norm_key))
            if norm_key in normalized_counts:
                normalized_counts[norm_key] += 1
            else:
                errors.append(f"Unmapped protein category: '{raw_cat}' in {day['day_name']} {slot}")

    print(f"Total main meal slots: {len(main_meals)}")
    for day_name, slot, title, raw_cat, norm_key in main_meals:
        print(f"  {day_name:<10} {slot:<7}: raw='{raw_cat:<16}' -> normalized='{norm_key:<15}' | {title}")

    print("\nNormalized Category Distribution vs Dr. Caglioni Clinical Rules:")
    print(f"{'Category Token':<20} | {'Expected':<8} | {'Normalized':<10} | {'Status'}")
    print("-" * 55)
    for cat, exp_count in AUTHORITATIVE_FREQUENCIES.items():
        obs_count = normalized_counts.get(cat, 0)
        match = obs_count == exp_count
        status = "PASS ✓" if match else "FAIL ❌"
        print(f"{cat:<20} | {exp_count:<8} | {obs_count:<10} | {status}")
        if not match:
            errors.append(f"Protein category '{cat}': expected {exp_count}, observed {obs_count}")

    # Check raw category contract
    if any(raw_cat != norm_key for _, _, _, raw_cat, norm_key in main_meals if norm_key != "pasto_libero"):
        warnings.append("[CONTRACT INCONSISTENCY] Categories in current-week.json are capitalized Italian UI labels (e.g. 'Carne bianca', 'Pesce fresco') instead of canonical schema tokens (e.g. 'carne_bianca', 'pesce'). While semantic mapping matches, validate_nutritional_integrity rejects raw strings.")

    # 4. Cart summary verification
    print("\n" + "=" * 80)
    print("[4] CART SUMMARY RECONCILIATION")
    print("=" * 80)
    cart = data.get("cart_summary", {})
    grouped = cart.get("grouped_items", [])
    total_cart_items = 0
    total_cart_eur = 0.0
    for g in grouped:
        group_name = g.get("category", "Unknown")
        items = g.get("items", [])
        g_count = len(items)
        g_eur = sum(item.get("estimated_eur", 0.0) for item in items)
        total_cart_items += g_count
        total_cart_eur += g_eur
        print(f"  - {group_name:<25}: {g_count:>2} items, {g_eur:>6.2f} €")

    reported_items = cart.get("items_count", 0)
    reported_eur = cart.get("total_estimated_eur", 0.0)

    print(f"\nGrouped items sum: {total_cart_items} items, {total_cart_eur:.2f} €")
    print(f"cart_summary top : {reported_items} items, {reported_eur:.2f} €")
    print(f"Discrepancy      : {total_cart_items - reported_items:+d} items, {total_cart_eur - reported_eur:+.2f} €")

    if total_cart_items != reported_items:
        errors.append(f"[CART BUG] Cart items_count mismatch: top-level claims {reported_items} items, but grouped_items sums to {total_cart_items} items (diff: {total_cart_items - reported_items})")
    if abs(total_cart_eur - reported_eur) > 0.05:
        errors.append(f"[CART BUG] Cart total_estimated_eur mismatch: top-level claims {reported_eur:.2f} €, but grouped_items sums to {total_cart_eur:.2f} € (diff: {total_cart_eur - reported_eur:+.2f} €)")

    # 5. Seasonal Produce verification
    print("\n" + "=" * 80)
    print("[5] AUTUMN SEASONAL PRODUCE AUDIT")
    print("=" * 80)
    autumn_produce = ["zucca", "verza", "broccoli", "finocchi", "mela", "pera", "kiwi"]
    all_text = json.dumps(data, ensure_ascii=False).lower()
    for prod in autumn_produce:
        if prod not in all_text:
            errors.append(f"Missing autumn seasonal staple: '{prod}'")
        else:
            print(f"  - Seasonal produce '{prod}': FOUND ✓")

    # Summary
    print("\n" + "=" * 80)
    print("EMPIRICAL VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Errors   : {len(errors)}")
    print(f"Warnings : {len(warnings)}")
    for w in warnings:
        print(f"  [WARN]  {w}")
    for e in errors:
        print(f"  [FAIL]  {e}")

    if errors:
        print("\nOVERALL VERDICT: REQUEST_CHANGES (FAIL)")
        return False
    else:
        print("\nOVERALL VERDICT: APPROVE (PASS)")
        return True

if __name__ == "__main__":
    success = verify()
    sys.exit(0 if success else 1)
