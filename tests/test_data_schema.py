"""
Tier 1 & Tier 2: Data Schema and Git-as-CMS Contract Tests.
Validates Contract 1 (WeeklyPlanData) and Contract 4 (Git-as-CMS serialization).
"""

import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from tests.fixtures import (
    SAMPLE_VALID_WEEK,
    load_live_weekly_plan,
    validate_weekly_plan_schema
)

LIVE_DATA_PATH = Path(r"C:\Users\david\Desktop\Progetti\meal-planner-dashboard\src\data\current-week.json")


class TestDataSchemaContract(unittest.TestCase):
    """Tests schema validation, data types, and required fields for current-week.json."""

    @classmethod
    def setUpClass(cls):
        cls.data = load_live_weekly_plan()

    def test_live_data_passes_schema(self):
        """Live src/data/current-week.json must pass schema validation cleanly."""
        is_valid, errors = validate_weekly_plan_schema(self.data)
        self.assertTrue(is_valid, f"Live current-week.json failed schema validation: {errors}")
        self.assertEqual(len(errors), 0)

    def test_sample_valid_week_passes_schema(self):
        """Authoritative reference fixture must pass schema validation cleanly."""
        is_valid, errors = validate_weekly_plan_schema(SAMPLE_VALID_WEEK)
        self.assertTrue(is_valid, f"Reference dataset failed schema validation: {errors}")
        self.assertEqual(len(errors), 0)

    def test_top_level_required_keys_present(self):
        """Top level JSON object must contain all required metadata keys."""
        required_keys = ["week_id", "week_start", "week_end", "macro_target", "cart_summary", "days"]
        for key in required_keys:
            self.assertIn(key, self.data, f"Missing required top-level key: {key}")

    def test_week_dates_consecutive_seven_days(self):
        """week_start to week_end must span exactly 7 consecutive days."""
        start_dt = datetime.strptime(self.data["week_start"], "%Y-%m-%d")
        end_dt = datetime.strptime(self.data["week_end"], "%Y-%m-%d")
        delta = (end_dt - start_dt).days + 1
        self.assertEqual(delta, 7, f"Week date range must span 7 days, got {delta}")

    def test_seven_days_present_and_unique(self):
        """Must contain exactly 7 day records with distinct dates and names."""
        days = self.data["days"]
        self.assertEqual(len(days), 7, "Weekly plan must contain exactly 7 days")
        dates = [d["date"] for d in days]
        self.assertEqual(len(set(dates)), 7, "Each day must have a unique date")
        day_names = [d["day_name"] for d in days]
        expected_days = ["Sabato", "Domenica", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
        self.assertEqual(day_names, expected_days, f"Days must follow Saturday-to-Friday order: {expected_days}")

    def test_five_meals_per_day_strictly_defined(self):
        """Every single day must contain exactly the 5 Dr. Caglioni meal slots."""
        expected_slots = ["colazione", "pranzo", "spuntino_pomeriggio", "cena", "dopocena"]
        for day in self.data["days"]:
            meals = day["meals"]
            self.assertEqual(len(meals), 5, f"Day {day['day_name']} must have exactly 5 meals")
            for slot in expected_slots:
                self.assertIn(slot, meals, f"Day {day['day_name']} missing meal slot '{slot}'")

    def test_meal_fields_contract(self):
        """Every meal must satisfy the Meal TypeScript interface contract."""
        for day in self.data["days"]:
            for slot_name, meal in day["meals"].items():
                self.assertIsInstance(meal.get("title"), str, f"Meal {slot_name} missing string title")
                self.assertGreater(len(meal["title"]), 0, f"Meal {slot_name} title cannot be empty")
                self.assertIsInstance(meal.get("kcal"), (int, float), f"Meal {slot_name} kcal must be numeric")
                self.assertGreater(meal["kcal"], 0, f"Meal {slot_name} kcal must be positive")
                
                # Check macros dictionary
                macros = meal.get("macros", {})
                self.assertIsInstance(macros, dict, f"Meal {slot_name} macros must be a dict")
                for m in ["carbs_g", "proteins_g", "fats_g"]:
                    self.assertIn(m, macros, f"Meal {slot_name} macros missing '{m}'")
                    self.assertIsInstance(macros[m], (int, float))

                # Check ingredients
                ingredients = meal.get("ingredients")
                self.assertIsInstance(ingredients, list, f"Meal {slot_name} ingredients must be a list")
                for ing in ingredients:
                    self.assertIn("name", ing)
                    self.assertIn("qty", ing)
                    self.assertIn("category", ing)

                # Check recipe steps
                steps = meal.get("recipe_steps")
                self.assertIsInstance(steps, list, f"Meal {slot_name} recipe_steps must be a list")
                self.assertGreater(len(steps), 0, f"Meal {slot_name} must have at least 1 recipe step")

    def test_cart_summary_contract(self):
        """cart_summary must provide total_estimated_eur, items_count, and valid cart_url."""
        cart = self.data["cart_summary"]
        self.assertIsInstance(cart.get("total_estimated_eur"), (int, float))
        self.assertGreater(cart["total_estimated_eur"], 0.0)
        self.assertIsInstance(cart.get("items_count"), int)
        self.assertGreater(cart["items_count"], 0)
        self.assertIn("esselunga", cart.get("cart_url", "").lower())


class TestDataSerializationAndBoundaries(unittest.TestCase):
    """Tier 2: Boundary conditions, malformed JSON, unicode preservation, and serialization roundtrips."""

    def test_missing_top_level_keys_fails_validation(self):
        """Omitting any top-level key must trigger schema rejection."""
        for key in ["week_id", "week_start", "days", "macro_target", "cart_summary"]:
            corrupt = dict(SAMPLE_VALID_WEEK)
            del corrupt[key]
            is_valid, errors = validate_weekly_plan_schema(corrupt)
            self.assertFalse(is_valid, f"Schema validation should fail when '{key}' is missing")
            self.assertTrue(any(key in err for err in errors))

    def test_fewer_than_seven_days_fails_validation(self):
        """A week with only 6 days must be rejected."""
        corrupt = dict(SAMPLE_VALID_WEEK)
        corrupt["days"] = corrupt["days"][:6]
        is_valid, errors = validate_weekly_plan_schema(corrupt)
        self.assertFalse(is_valid, "Plan with 6 days must fail validation")

    def test_missing_meal_slot_fails_validation(self):
        """Omitting a required meal slot (e.g. dopocena) must be rejected."""
        corrupt_days = [dict(d) for d in SAMPLE_VALID_WEEK["days"]]
        # Remove dopocena from Monday
        corrupt_days[2] = dict(corrupt_days[2])
        corrupt_days[2]["meals"] = dict(corrupt_days[2]["meals"])
        del corrupt_days[2]["meals"]["dopocena"]
        
        corrupt_plan = dict(SAMPLE_VALID_WEEK)
        corrupt_plan["days"] = corrupt_days
        is_valid, errors = validate_weekly_plan_schema(corrupt_plan)
        self.assertFalse(is_valid, "Missing dopocena slot must be caught")

    def test_utf8_accented_characters_preserved_on_serialization(self):
        """Italian accented letters (è, é, à, ò, ù) and symbols must survive JSON dumps/loads intact."""
        serialized = json.dumps(SAMPLE_VALID_WEEK, ensure_ascii=False, indent=2)
        deserialized = json.loads(serialized)
        
        # Check specific accented strings
        lun_title = deserialized["days"][2]["meals"]["pranzo"]["title"]
        self.assertIn("Lunedì", deserialized["days"][2]["day_name"])
        self.assertIn("ceci", lun_title)
        self.assertEqual(deserialized["days"][4]["day_name"], "Mercoledì")

    def test_non_dictionary_root_fails_validation(self):
        """Passing an array or string as root object must fail gracefully."""
        self.assertFalse(validate_weekly_plan_schema(["not", "a", "dict"])[0])
        self.assertFalse(validate_weekly_plan_schema("string")[0])
        self.assertFalse(validate_weekly_plan_schema(None)[0])


if __name__ == "__main__":
    unittest.main()
