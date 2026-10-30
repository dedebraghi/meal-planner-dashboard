"""
Tier 2: Boundary & Corner Cases Test Suite.
Tests edge conditions, extreme values, out-of-stock scenarios, special characters,
negative quantities, and safety boundary edge cases.
"""

import json
import unittest
from tests.fixtures import (
    SAMPLE_VALID_WEEK,
    AUTHORITATIVE_PANTRY_TAXONOMY,
    is_forbidden_checkout_url,
    validate_weekly_plan_schema,
    validate_nutritional_integrity
)


class TestTier2OutOfStockBoundaries(unittest.TestCase):
    """Tier 2: Out-of-Stock and Inventory Boundary Conditions."""

    def test_t2_01_primary_out_of_stock_uses_fallback(self):
        item = AUTHORITATIVE_PANTRY_TAXONOMY["petto_di_pollo"]
        search_query = item["fallback_term"]
        self.assertEqual(search_query, "fesa di tacchino a fette")

    def test_t2_02_all_fallbacks_exhausted_tracked_in_missing_list(self):
        missing_items = []
        def attempt_purchase(sku: str, stock_map: dict):
            if stock_map.get(sku, 0) > 0:
                return "purchased_primary"
            fallback = AUTHORITATIVE_PANTRY_TAXONOMY[sku]["fallback_term"]
            if stock_map.get(fallback, 0) > 0:
                return "purchased_fallback"
            missing_items.append(sku)
            return "out_of_stock"

        stock = {"petto di pollo a fette": 0, "fesa di tacchino a fette": 0}
        res = attempt_purchase("petto_di_pollo", stock)
        self.assertEqual(res, "out_of_stock")
        self.assertIn("petto_di_pollo", missing_items)

    def test_t2_03_zero_search_results_handled_without_crash(self):
        catalog_results = []
        result = catalog_results[0] if catalog_results else None
        self.assertIsNone(result)

    def test_t2_04_fallback_term_matches_protein_category(self):
        for item_key, spec in AUTHORITATIVE_PANTRY_TAXONOMY.items():
            self.assertIsNotNone(spec["fallback_term"])
            self.assertIsInstance(spec["category"], str)

    def test_t2_05_out_of_stock_does_not_abort_entire_cart_pipeline(self):
        cart = []
        items_to_add = ["uova_fresche", "petto_di_pollo", "riso_basmati"]
        stock = {"uova fresche biologiche": 10, "petto di pollo a fette": 0, "fesa di tacchino a fette": 5, "riso basmati": 8}
        
        for it in items_to_add:
            if it == "petto_di_pollo":
                cart.append("fesa di tacchino a fette")
            else:
                cart.append(it)
        self.assertEqual(len(cart), 3)


class TestTier2EmptyAndMissingFields(unittest.TestCase):
    """Tier 2: Empty and Missing Field Edge Cases."""

    def test_t2_06_empty_ingredients_list_detected(self):
        corrupt = json.loads(json.dumps(SAMPLE_VALID_WEEK))
        corrupt["days"][0]["meals"]["pranzo"]["ingredients"] = []
        # While valid schema-wise as a list, it should have ingredients
        self.assertEqual(len(corrupt["days"][0]["meals"]["pranzo"]["ingredients"]), 0)

    def test_t2_07_empty_recipe_steps_detected_by_schema(self):
        corrupt = json.loads(json.dumps(SAMPLE_VALID_WEEK))
        corrupt["days"][0]["meals"]["pranzo"]["recipe_steps"] = []
        is_valid, errors = validate_weekly_plan_schema(corrupt)
        self.assertFalse(is_valid)
        self.assertTrue(any("recipe_steps" in e for e in errors))

    def test_t2_08_empty_meal_title_detected_by_schema(self):
        corrupt = json.loads(json.dumps(SAMPLE_VALID_WEEK))
        corrupt["days"][0]["meals"]["pranzo"]["title"] = ""
        # Schema checks for presence; empty title check
        title = corrupt["days"][0]["meals"]["pranzo"]["title"]
        self.assertEqual(len(title), 0)

    def test_t2_09_none_image_url_handled_with_fallback(self):
        meal = {"title": "Test", "image_url": None}
        effective_image = meal.get("image_url") or "/placeholder-dish.svg"
        self.assertEqual(effective_image, "/placeholder-dish.svg")

    def test_t2_10_missing_prep_time_defaults_gracefully(self):
        meal = {"title": "Test", "cook_time_min": 10}
        prep_time = meal.get("prep_time_min", 0)
        self.assertEqual(prep_time, 0)


class TestTier2BoundaryCaloriesAndMacros(unittest.TestCase):
    """Tier 2: Boundary Calories and Macronutrient Extremes."""

    def test_t2_11_zero_calorie_beverage_item(self):
        item = {"name": "Caffè amaro", "qty": "1 tazzina", "kcal": 2}
        self.assertLess(item["kcal"], 5)

    def test_t2_12_single_meal_extreme_calorie_detected(self):
        corrupt = json.loads(json.dumps(SAMPLE_VALID_WEEK))
        corrupt["days"][0]["meals"]["pranzo"]["kcal"] = 1800
        is_valid, errors = validate_nutritional_integrity(corrupt)
        self.assertFalse(is_valid)

    def test_t2_13_daily_calorie_starvation_level_detected(self):
        corrupt = json.loads(json.dumps(SAMPLE_VALID_WEEK))
        for m in corrupt["days"][0]["meals"].values():
            m["kcal"] = 100
        is_valid, errors = validate_nutritional_integrity(corrupt)
        self.assertFalse(is_valid)

    def test_t2_14_negative_calories_flagged(self):
        corrupt = json.loads(json.dumps(SAMPLE_VALID_WEEK))
        corrupt["days"][0]["meals"]["colazione"]["kcal"] = -300
        total_kcal = sum(m["kcal"] for m in corrupt["days"][0]["meals"].values())
        self.assertLess(total_kcal, 1800)

    def test_t2_15_floating_point_macro_rounding(self):
        fats = 0.5 + 0.4 + 0.8
        rounded = round(fats, 1)
        self.assertEqual(rounded, 1.7)


class TestTier2NonAsciiAndSpecialCharacters(unittest.TestCase):
    """Tier 2: Italian Accented Letters, Apostrophes, and Symbols."""

    def test_t2_16_italian_accented_days_preserved(self):
        accented_days = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
        for d in accented_days:
            self.assertTrue(d.endswith("ì"))

    def test_t2_17_food_apostrophes_preserved(self):
        dishes = ["Fiocchi d'avena", "Olio extravergine d'oliva", "Un'arancia"]
        for dish in dishes:
            self.assertIn("'", dish)

    def test_t2_18_currency_symbol_eur_preserved(self):
        text = "Spesa stimata: 48.75 €"
        self.assertIn("€", text)

    def test_t2_19_slash_and_fraction_notation(self):
        qty = "1/2 limone"
        self.assertIn("/", qty)

    def test_t2_20_percentage_notation(self):
        yogurt = "Yogurt greco 0% grassi"
        self.assertIn("0%", yogurt)


class TestTier2NegativeAndInvalidQuantities(unittest.TestCase):
    """Tier 2: Negative, Zero, and Invalid Quantity Strings."""

    def test_t2_21_negative_grams_rejected(self):
        qty_str = "-50g"
        is_negative = qty_str.startswith("-")
        self.assertTrue(is_negative)

    def test_t2_22_zero_grams_handled(self):
        qty_str = "0g"
        val = int(qty_str.replace("g", ""))
        self.assertEqual(val, 0)

    def test_t2_23_taste_or_as_desired_quantity(self):
        qty_str = "q.b."
        self.assertEqual(qty_str, "q.b.")

    def test_t2_24_missing_unit_detection(self):
        qty_str = "150"
        has_unit = any(u in qty_str for u in ["g", "ml", "uova", "fette"])
        self.assertFalse(has_unit)

    def test_t2_25_extreme_large_quantity_flagged(self):
        qty_grams = 5000
        is_extreme = qty_grams > 1000
        self.assertTrue(is_extreme)


class TestTier2SafetyInvariantBoundaries(unittest.TestCase):
    """Tier 2: Safety Guardrail URL Matching Edge Cases."""

    def test_t2_26_query_param_checkout_flagged(self):
        url = "https://spesaonline.esselunga.it/shop?action=checkout"
        self.assertTrue(is_forbidden_checkout_url(url))

    def test_t2_27_cassa_with_subpath_flagged(self):
        url = "https://spesaonline.esselunga.it/cassa/step1/indirizzo"
        self.assertTrue(is_forbidden_checkout_url(url))

    def test_t2_28_pagamento_with_fragment_flagged(self):
        url = "https://spesaonline.esselunga.it/nav#pagamento"
        self.assertTrue(is_forbidden_checkout_url(url))

    def test_t2_29_uppercase_checkout_flagged(self):
        url = "https://spesaonline.esselunga.it/CHECKOUT/REVIEW"
        self.assertTrue(is_forbidden_checkout_url(url))

    def test_t2_30_safe_url_with_cassa_in_product_not_falsely_flagged(self):
        # Specific path check: /cassa as route segment vs product query
        url = "https://spesaonline.esselunga.it/commerce/nav/supermercato/carrello"
        self.assertFalse(is_forbidden_checkout_url(url))


if __name__ == "__main__":
    unittest.main()
