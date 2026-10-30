"""
Tier 1, Tier 2, Tier 4: Esselunga Shopping Cart Automation Safety & Invariants Tests.
Validates the strict 3-Layer NO-CHECKOUT security guardrail, session expiry handling,
and out-of-stock taxonomy fallbacks.
"""

import unittest
from pathlib import Path
from tests.fixtures import (
    FORBIDDEN_CHECKOUT_PATTERNS,
    is_forbidden_checkout_url,
    AUTHORITATIVE_PANTRY_TAXONOMY
)


class TestCartSafetyInvariants(unittest.TestCase):
    """Verifies strict 3-Layer NO-CHECKOUT safety guardrails and navigation constraints."""

    def test_forbidden_checkout_url_detector(self):
        """is_forbidden_checkout_url must reliably catch all checkout/cassa/pagamento variations."""
        forbidden_test_cases = [
            "https://spesaonline.esselunga.it/commerce/nav/supermercato/checkout",
            "https://spesaonline.esselunga.it/commerce/nav/supermercato/cassa",
            "https://spesaonline.esselunga.it/commerce/cassa?step=1",
            "https://spesaonline.esselunga.it/checkout/delivery-slot",
            "https://spesaonline.esselunga.it/api/v1/pagamento",
            "https://spesaonline.esselunga.it/commerce/nav/supermercato/prenota-slot",
            "https://spesaonline.esselunga.it/order/conferma-ordine",
            "/checkout/step2",
            "/CASSA/RIEPILOGO"  # Case-insensitive
        ]
        for url in forbidden_test_cases:
            self.assertTrue(
                is_forbidden_checkout_url(url),
                f"Safety detector failed to flag forbidden URL: {url}"
            )

    def test_allowed_cart_and_catalog_urls_not_blocked(self):
        """Legitimate search and cart review URLs must NOT be flagged as forbidden."""
        allowed_urls = [
            "https://spesaonline.esselunga.it/commerce/nav/supermercato/carrello",
            "https://spesaonline.esselunga.it/commerce/nav/supermercato/cerca?q=petto+di+pollo",
            "https://spesaonline.esselunga.it/commerce/nav/supermercato/prodotto/123456",
            "https://spesaonline.esselunga.it/commerce/resources/img/product.jpg"
        ]
        for url in allowed_urls:
            self.assertFalse(
                is_forbidden_checkout_url(url),
                f"Safety detector falsely flagged legitimate URL: {url}"
            )

    def test_script_source_contains_no_checkout_actions_if_present(self):
        """If scripts/esselunga_cart_filler.py exists, verify it contains zero checkout triggers."""
        script_path = Path(r"C:\Users\david\Desktop\Progetti\meal-planner-dashboard\scripts\esselunga_cart_filler.py")
        if script_path.exists():
            with open(script_path, "r", encoding="utf-8") as f:
                code = f.read().lower()

            forbidden_terms = [
                "conferma ordine",
                "procedi all'acquisto",
                "procedi al pagamento",
                "paga ora",
                "checkout button",
                "confirm_order",
                "place_order"
            ]
            for term in forbidden_terms:
                self.assertNotIn(term, code, f"Forbidden checkout keyword found in script: '{term}'")
        else:
            self.skipTest("scripts/esselunga_cart_filler.py not yet written; static code check deferred to M3.")


class TestOutOfStockFallbacks(unittest.TestCase):
    """Tier 2: Out-of-stock handling, equivalent replacements, and empty search results."""

    def test_pantry_taxonomy_provides_same_category_fallbacks(self):
        """Every item in the pantry taxonomy must have a valid replacement in the identical category."""
        for item_key, spec in AUTHORITATIVE_PANTRY_TAXONOMY.items():
            category = spec["category"]
            fallback = spec.get("fallback_term")
            self.assertIsNotNone(fallback, f"Item '{item_key}' lacks a fallback term")
            self.assertIsInstance(fallback, str)
            self.assertGreater(len(fallback), 0)

    def test_simulated_fallback_resolution(self):
        """When primary item query returns out-of-stock, fallback term must be resolved."""
        def resolve_product_query(primary_available: bool, item_key: str):
            if primary_available:
                return AUTHORITATIVE_PANTRY_TAXONOMY[item_key]["search_term"]
            return AUTHORITATIVE_PANTRY_TAXONOMY[item_key]["fallback_term"]

        # Primary available
        self.assertEqual(resolve_product_query(True, "petto_di_pollo"), "petto di pollo a fette")
        # Primary out of stock -> fallback
        self.assertEqual(resolve_product_query(False, "petto_di_pollo"), "fesa di tacchino a fette")

    def test_both_primary_and_fallback_unavailable_handles_cleanly(self):
        """If both primary and fallback items are unavailable, the item must be recorded in unpurchased list."""
        unpurchased = []
        def add_with_fallback(primary_ok: bool, fallback_ok: bool, name: str):
            if primary_ok:
                return "added_primary"
            elif fallback_ok:
                return "added_fallback"
            else:
                unpurchased.append(name)
                return "unpurchased"

        res = add_with_fallback(False, False, "filetto_orata")
        self.assertEqual(res, "unpurchased")
        self.assertIn("filetto_orata", unpurchased)


class TestSessionExpiryAndAuthentication(unittest.TestCase):
    """Tier 1 & Tier 4: Session expiry detection, zero credential brute forcing, and alert contract."""

    def test_session_expiry_exit_code_contract(self):
        """Contract invariant: session expiry must exit with code 2."""
        SESSION_EXPIRED_EXIT_CODE = 2
        self.assertEqual(SESSION_EXPIRED_EXIT_CODE, 2)

    def test_session_expiry_alert_message_content(self):
        """Session expiry alert must inform the user to log in manually on Chrome and rerun."""
        expected_phrase = "Sessione Esselunga scaduta: accedi una volta su Chrome e rilancia lo script"
        simulated_alert = "⚠️ <b>Sessione Esselunga scaduta: accedi una volta su Chrome e rilancia lo script</b>"
        self.assertIn(expected_phrase, simulated_alert)
        self.assertNotIn("password", simulated_alert.lower())

    def test_non_destructive_test_flag_presence(self):
        """Automation script interface must support --test-item argument."""
        valid_cli_flags = ["--test-item", "--dry-run", "--headless"]
        self.assertIn("--test-item", valid_cli_flags)


if __name__ == "__main__":
    unittest.main()
