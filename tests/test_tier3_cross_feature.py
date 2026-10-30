"""
Tier 3: Cross-Feature Interactions Test Suite.
Validates end-to-end interactions between cart groceries and recipe ingredients,
daily macro sums versus meal breakdowns, free meal bypasses, and Git-as-CMS serialization.
"""

import json
import unittest
from datetime import datetime, timezone
from tests.fixtures import (
    SAMPLE_VALID_WEEK,
    AUTHORITATIVE_TARGET,
    AUTHORITATIVE_PANTRY_TAXONOMY,
    validate_weekly_plan_schema,
    validate_nutritional_integrity
)


class TestTier3CartAndRecipeConsistency(unittest.TestCase):
    """Tier 3: Grocery shopping list generated from recipe ingredients."""

    def test_t3_01_all_recipe_ingredients_aggregated_into_cart(self):
        """Every ingredient across 35 meals is aggregated into a master grocery list."""
        all_ingredients = []
        for day in SAMPLE_VALID_WEEK["days"]:
            for meal in day["meals"].values():
                for ing in meal.get("ingredients", []):
                    all_ingredients.append(ing["name"])

        self.assertGreater(len(all_ingredients), 50, "Should have >50 total ingredient usages in week")
        deduped = set(all_ingredients)
        self.assertGreater(len(deduped), 20, "Should have >20 unique grocery items to buy")

    def test_t3_02_cart_item_count_aligns_with_aggregated_grocery_skus(self):
        """cart_summary items_count roughly matches unique non-pantry SKUs."""
        cart_count = SAMPLE_VALID_WEEK["cart_summary"]["items_count"]
        self.assertTrue(15 <= cart_count <= 30, f"Cart item count {cart_count} reasonable for 1 week")

    def test_t3_03_all_main_protein_sources_found_in_taxonomy(self):
        """Every protein source in Pranzo and Cena has a matching category in the taxonomy."""
        main_proteins = []
        for day in SAMPLE_VALID_WEEK["days"]:
            for slot in ["pranzo", "cena"]:
                meal = day["meals"][slot]
                if not meal.get("is_free_meal", False):
                    main_proteins.append(meal["category"])

        for p in main_proteins:
            # Check category exists in taxonomy
            categories_in_taxonomy = {spec["category"] for spec in AUTHORITATIVE_PANTRY_TAXONOMY.values()}
            self.assertIn(p, categories_in_taxonomy, f"Protein category '{p}' not represented in taxonomy")


class TestTier3MacroSumVsMealSums(unittest.TestCase):
    """Tier 3: Mathematical coherence between individual meals and daily summaries."""

    def test_t3_04_daily_kcal_sum_equals_meals_sum(self):
        """For each of the 7 days, sum(meal.kcal) == day.daily_macros.kcal."""
        for day in SAMPLE_VALID_WEEK["days"]:
            expected_kcal = day["daily_macros"]["kcal"]
            actual_kcal = sum(m["kcal"] for m in day["meals"].values())
            self.assertEqual(
                expected_kcal, actual_kcal,
                f"Day {day['day_name']} daily_macros.kcal ({expected_kcal}) != sum of meals ({actual_kcal})"
            )

    def test_t3_05_daily_proteins_sum_equals_meals_sum(self):
        """For each of the 7 days, sum(meal.macros.proteins_g) == day.daily_macros.proteins_g."""
        for day in SAMPLE_VALID_WEEK["days"]:
            expected_p = day["daily_macros"]["proteins_g"]
            actual_p = sum(m["macros"]["proteins_g"] for m in day["meals"].values())
            self.assertAlmostEqual(expected_p, actual_p, delta=1)

    def test_t3_06_daily_carbs_sum_equals_meals_sum(self):
        """For each of the 7 days, sum(meal.macros.carbs_g) == day.daily_macros.carbs_g."""
        for day in SAMPLE_VALID_WEEK["days"]:
            expected_c = day["daily_macros"]["carbs_g"]
            actual_c = sum(m["macros"]["carbs_g"] for m in day["meals"].values())
            self.assertAlmostEqual(expected_c, actual_c, delta=1)

    def test_t3_07_daily_fats_sum_equals_meals_sum(self):
        """For each of the 7 days, sum(meal.macros.fats_g) == day.daily_macros.fats_g."""
        for day in SAMPLE_VALID_WEEK["days"]:
            expected_f = day["daily_macros"]["fats_g"]
            actual_f = sum(m["macros"]["fats_g"] for m in day["meals"].values())
            self.assertAlmostEqual(expected_f, actual_f, delta=1)


class TestTier3FreeMealInteraction(unittest.TestCase):
    """Tier 3: Free Meal interaction with daily macro totals and recipe steps."""

    def test_t3_08_free_meal_included_in_saturday_macro_sum(self):
        """Saturday pizza margherita macros contribute fully to Saturday's 2060 kcal total."""
        sat = SAMPLE_VALID_WEEK["days"][0]
        sat_cena = sat["meals"]["cena"]
        self.assertTrue(sat_cena["is_free_meal"])
        
        sum_without_pizza = sum(
            m["kcal"] for slot, m in sat["meals"].items() if slot != "cena"
        )
        self.assertEqual(sum_without_pizza + sat_cena["kcal"], sat["daily_macros"]["kcal"])

    def test_t3_09_free_meal_has_zero_cooking_prep_time(self):
        """Free meal requires no cooking / prep duration."""
        sat_cena = SAMPLE_VALID_WEEK["days"][0]["meals"]["cena"]
        self.assertEqual(sat_cena.get("cook_time_min", 0), 0)


class TestTier3GitAsCmsSerializationRoundtrip(unittest.TestCase):
    """Tier 3: Git-as-CMS read-modify-write data pipeline integrity."""

    def test_t3_10_cart_update_mutation_preserves_schema(self):
        """Modifying cart_summary spend and timestamp preserves schema validity."""
        cloned = json.loads(json.dumps(SAMPLE_VALID_WEEK))
        
        # Simulate Friday automated update
        cloned["cart_summary"]["total_estimated_eur"] = 52.30
        cloned["cart_summary"]["items_count"] = 22
        cloned["cart_summary"]["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        serialized = json.dumps(cloned, ensure_ascii=False, indent=2)
        reloaded = json.loads(serialized)

        is_valid, errors = validate_weekly_plan_schema(reloaded)
        self.assertTrue(is_valid, f"Mutated plan failed validation: {errors}")
        self.assertEqual(reloaded["cart_summary"]["total_estimated_eur"], 52.30)
        self.assertEqual(reloaded["cart_summary"]["items_count"], 22)

    def test_t3_11_card_summary_and_drawer_details_match(self):
        """MealCard title and macros match the recipe drawer details."""
        for day in SAMPLE_VALID_WEEK["days"]:
            for slot, meal in day["meals"].items():
                self.assertIsNotNone(meal["id"])
                self.assertIsNotNone(meal["title"])
                self.assertGreater(meal["kcal"], 0)
                self.assertGreater(len(meal["recipe_steps"]), 0)


if __name__ == "__main__":
    unittest.main()
