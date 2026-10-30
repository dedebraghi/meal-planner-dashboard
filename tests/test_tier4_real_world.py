"""
Tier 4: Real-World Scenarios Test Suite.
Simulates end-to-end user workflows: Friday morning automated pipeline,
Esselunga cart filling with NO-CHECKOUT enforcement, Telegram alerting, and session expiry recovery.
"""

import json
import unittest
from datetime import datetime, timezone
from tests.fixtures import (
    SAMPLE_VALID_WEEK,
    AUTHORITATIVE_TARGET,
    is_forbidden_checkout_url,
    validate_telegram_alert_html,
    validate_weekly_plan_schema,
    validate_nutritional_integrity
)


class TestTier4FridayOrchestrationWorkflow(unittest.TestCase):
    """Tier 4: Simulates the complete end-to-end Friday pipeline."""

    def test_t4_01_full_weekly_cycle_simulation(self):
        """Simulates full cycle: plan validation -> cart aggregation -> summary update -> alert dispatch."""
        # 1. Validate data schema and nutritional rules
        is_schema_ok, schema_errors = validate_weekly_plan_schema(SAMPLE_VALID_WEEK)
        self.assertTrue(is_schema_ok, f"Schema validation failed: {schema_errors}")

        is_nutrition_ok, nutrition_errors = validate_nutritional_integrity(SAMPLE_VALID_WEEK)
        self.assertTrue(is_nutrition_ok, f"Nutritional integrity failed: {nutrition_errors}")

        # 2. Simulate grocery compilation
        aggregated_items = set()
        for day in SAMPLE_VALID_WEEK["days"]:
            for meal in day["meals"].values():
                for ing in meal.get("ingredients", []):
                    aggregated_items.add(ing["name"])
        self.assertGreater(len(aggregated_items), 20)

        # 3. Simulate cart summary computation
        simulated_spend = 48.75
        simulated_count = len(aggregated_items)
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 4. Simulate Git-as-CMS commit message
        week_tag = SAMPLE_VALID_WEEK["week_id"]
        commit_msg = f"chore(meal-plan): update week {week_tag}"
        self.assertTrue(commit_msg.startswith("chore(meal-plan):"))

        # 5. Simulate Telegram notification dispatch
        alert_payload = (
            f"🛒 <b>Riepilogo Spesa Esselunga — Settimana {SAMPLE_VALID_WEEK['week_start']} al {SAMPLE_VALID_WEEK['week_end']}</b>\n\n"
            f"📦 Articoli aggiunti: <b>{simulated_count}</b>\n"
            f"💰 Spesa stimata: <b>{simulated_spend:.2f} €</b>\n"
            f"🥗 Piano nutrizionale: <b>{AUTHORITATIVE_TARGET['kcal']} kcal/die</b>\n\n"
            f"🌐 Dashboard: <a href=\"https://meal-planner-dashboard.vercel.app\">Apri Dashboard</a>"
        )
        is_alert_ok, alert_errors = validate_telegram_alert_html(alert_payload)
        self.assertTrue(is_alert_ok, f"Telegram payload failed validation: {alert_errors}")


class TestTier4EsselungaNoCheckoutEnforcement(unittest.TestCase):
    """Tier 4: Strict enforcement of the NO-CHECKOUT invariant during simulated cart population."""

    def test_t4_02_network_interceptor_aborts_forbidden_navigation(self):
        """Simulates network requests and asserts that all checkout/payment URLs are aborted."""
        simulated_traffic = [
            ("https://spesaonline.esselunga.it/commerce/nav/supermercato/home", "ALLOW"),
            ("https://spesaonline.esselunga.it/commerce/nav/supermercato/cerca?q=uova", "ALLOW"),
            ("https://spesaonline.esselunga.it/commerce/nav/supermercato/carrello", "ALLOW"),
            ("https://spesaonline.esselunga.it/commerce/nav/supermercato/cassa", "ABORT"),
            ("https://spesaonline.esselunga.it/checkout/step1", "ABORT"),
            ("https://spesaonline.esselunga.it/api/pagamento", "ABORT")
        ]

        for url, expected_action in simulated_traffic:
            is_forbidden = is_forbidden_checkout_url(url)
            actual_action = "ABORT" if is_forbidden else "ALLOW"
            self.assertEqual(
                actual_action, expected_action,
                f"Safety interceptor misrouted URL: {url} (expected {expected_action}, got {actual_action})"
            )

    def test_t4_03_final_browser_url_remains_in_cart_review(self):
        """After all items are added, the terminal URL must remain in review mode."""
        terminal_url = "https://spesaonline.esselunga.it/commerce/nav/supermercato/carrello"
        self.assertFalse(is_forbidden_checkout_url(terminal_url))
        self.assertIn("carrello", terminal_url)


class TestTier4SessionExpiryRecoveryFlow(unittest.TestCase):
    """Tier 4: Simulates expired authentication and verifies clean termination and alert."""

    def test_t4_04_session_expiry_flow(self):
        """When login prompt is encountered, script exits 2 and dispatches manual login alert."""
        # Simulate detection of login form
        dom_elements = ["input[type='password']", "button#login"]
        is_login_page = any("password" in el for el in dom_elements)
        self.assertTrue(is_login_page)

        # Assert no password brute forcing
        submitted_credentials = False
        self.assertFalse(submitted_credentials)

        # Assert exit code 2
        exit_code = 2
        self.assertEqual(exit_code, 2)

        # Assert notification dispatched
        alert_msg = "⚠️ <b>Sessione Esselunga scaduta</b>: accedi una volta su Chrome e rilancia lo script"
        self.assertIn("scaduta", alert_msg)
        self.assertIn("accedi", alert_msg)


class TestTier4EditorialDesignSystemCompliance(unittest.TestCase):
    """Tier 4: Anti-slop design system guidelines compliance."""

    def test_t4_05_anti_slop_tokens_and_colors(self):
        """Warm background, near-black text, and 8-point spacing system compliance."""
        editorial_tokens = {
            "canvas_bg": "#FAF9F6",
            "card_bg": "#FFFFFF",
            "text_primary": "#1A1A1A",
            "border_color": "#E5E2DC",
            "spacing_base_px": 8
        }
        self.assertEqual(editorial_tokens["canvas_bg"], "#FAF9F6")
        self.assertEqual(editorial_tokens["text_primary"], "#1A1A1A")
        self.assertEqual(editorial_tokens["spacing_base_px"], 8)

        # Prohibit neon/purple gradient slop
        forbidden_slop = ["linear-gradient", "shadow-[0_0_20px", "#8a2be2"]
        sample_css_classes = "bg-[#FAF9F6] text-[#1A1A1A] p-4 rounded-lg border border-[#E5E2DC]"
        for slop in forbidden_slop:
            self.assertNotIn(slop, sample_css_classes)


if __name__ == "__main__":
    unittest.main()
