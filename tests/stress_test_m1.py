#!/usr/bin/env python3
"""
Adversarial Stress Test Suite for Milestone M1
Tests boundary inputs, UTF-8 resilience, missing fields, SVG fallback, and UI contract robustness.
"""

import os
import sys
import json
import xml.etree.ElementTree as ET
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DATA_DIR = os.path.join(PROJECT_ROOT, "src", "data")
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "public")

class TestM1AdversarialStress(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.json_path = os.path.join(SRC_DATA_DIR, "current-week.json")
        with open(cls.json_path, "r", encoding="utf-8") as f:
            cls.raw_content = f.read()
            cls.data = json.loads(cls.raw_content)

    def test_utf8_encoding_and_accents_integrity(self):
        """Stress-test non-ASCII characters and UTF-8 validity across the entire dataset."""
        # Must decode without replacement character
        self.assertNotIn("\ufffd", self.raw_content, "Corrupted Unicode replacement character found")
        # Ensure standard Italian accented letters are properly represented
        accented_chars = ["à", "è", "é", "ì", "ò", "ù"]
        found_accents = [c for c in accented_chars if c in self.raw_content]
        self.assertGreaterEqual(len(found_accents), 4, f"Expected Italian accented characters, found: {found_accents}")

    def test_all_35_meals_exist_and_conform_to_schema(self):
        """Check all 7 days have exactly 5 required meals each with valid fields."""
        days = self.data.get("days", [])
        self.assertEqual(len(days), 7, "Must contain exactly 7 days")
        
        required_meal_keys = ["colazione", "pranzo", "spuntino_pomeriggio", "cena", "dopocena"]
        total_meals = 0
        
        for day in days:
            self.assertIn("day_name", day)
            self.assertIn("daily_macros", day)
            meals = day.get("meals", {})
            for mkey in required_meal_keys:
                self.assertIn(mkey, meals, f"Day {day.get('day_name')} missing meal {mkey}")
                meal = meals[mkey]
                self.assertIsInstance(meal.get("id"), str)
                self.assertIsInstance(meal.get("title"), str)
                self.assertIsInstance(meal.get("kcal"), (int, float))
                self.assertGreater(meal.get("kcal"), 0, f"Meal {meal.get('id')} has non-positive kcal")
                self.assertIsInstance(meal.get("macros"), dict)
                self.assertIsInstance(meal.get("ingredients"), list)
                self.assertGreater(len(meal.get("ingredients")), 0, f"Meal {meal.get('id')} has empty ingredients")
                total_meals += 1

        self.assertEqual(total_meals, 35, "Must have exactly 35 meals across the week")

    def test_extreme_calorie_values_and_macro_conservation(self):
        """Stress-test daily calorie sums and extreme value checks."""
        macro_target = self.data.get("macro_target", {})
        target_kcal = macro_target.get("kcal", 2063)
        
        for day in self.data.get("days", []):
            meals = day.get("meals", {})
            sum_meal_kcal = sum(m.get("kcal", 0) for m in meals.values())
            daily_macro_kcal = day.get("daily_macros", {}).get("kcal", 0)
            
            # Daily kcal must be within reasonable nutritional bounds (1500 - 3000 kcal)
            self.assertGreater(daily_macro_kcal, 1500, f"Day {day['day_name']} daily kcal unusually low: {daily_macro_kcal}")
            self.assertLess(daily_macro_kcal, 3000, f"Day {day['day_name']} daily kcal unusually high: {daily_macro_kcal}")
            
            # The sum of meals should match daily_macros.kcal
            diff = abs(sum_meal_kcal - daily_macro_kcal)
            # All days meal sums must match daily_macros.kcal exactly
            self.assertEqual(diff, 0, f"Day {day['day_name']}: meal sum ({sum_meal_kcal}) deviates from daily_macros ({daily_macro_kcal})")

    def test_missing_optional_fields_resilience(self):
        """Verify schema allows missing optional fields without violating contracts."""
        optional_fields = ["subtitle", "notes", "recipe_steps", "prep_time_min", "cook_time_min", "image_url", "is_free_meal"]
        for day in self.data.get("days", []):
            for meal in day.get("meals", {}).values():
                # Meal must survive even if optional fields are absent
                for opt in optional_fields:
                    val = meal.get(opt)
                    if opt == "recipe_steps" and val is not None:
                        self.assertIsInstance(val, list)
                    elif opt in ["prep_time_min", "cook_time_min"] and val is not None:
                        self.assertIsInstance(val, (int, float))
                        self.assertGreaterEqual(val, 0)
                    elif opt == "is_free_meal" and val is not None:
                        self.assertIsInstance(val, bool)

    def test_svg_fallback_asset_integrity(self):
        """Empirically test public/placeholder-dish.svg for XML validity, dimensions, and render safety."""
        svg_path = os.path.join(PUBLIC_DIR, "placeholder-dish.svg")
        self.assertTrue(os.path.exists(svg_path), "placeholder-dish.svg must exist in public/")
        self.assertGreater(os.path.getsize(svg_path), 500, "placeholder-dish.svg is suspiciously small")
        
        # Parse XML tree
        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()
        except ET.ParseError as e:
            self.fail(f"placeholder-dish.svg failed XML parsing: {e}")
            
        self.assertTrue(root.tag.endswith("svg"), f"Root element is not svg: {root.tag}")
        self.assertIn("viewBox", root.attrib, "SVG must have a viewBox attribute")
        
        # Security: check absence of script tags
        scripts = [elem for elem in root.iter() if elem.tag.endswith("script")]
        self.assertEqual(len(scripts), 0, "SVG contains insecure <script> tag")

    def test_cart_summary_and_negative_values(self):
        """Stress-test cart summary against negative numbers and invalid URLs."""
        cart_summary = self.data.get("cart_summary", {})
        self.assertGreater(cart_summary.get("total_estimated_eur", 0), 0, "Cart estimate must be > 0")
        self.assertGreater(cart_summary.get("items_count", 0), 0, "Cart item count must be > 0")
        self.assertTrue(cart_summary.get("cart_url", "").startswith("https://"), "Cart URL must use secure HTTPS")
        self.assertEqual(cart_summary.get("store"), "Esselunga")

if __name__ == "__main__":
    unittest.main()
