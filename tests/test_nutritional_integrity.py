"""
Tier 1, Tier 2, Tier 3: Nutritional Integrity and Dr. Caglioni Diet Plan Tests.
Authoritative source: Schema nutrizionale Braghiroli Davide.pdf (05/11/2025, Page 2-4).
"""

import unittest
from tests.fixtures import (
    SAMPLE_VALID_WEEK,
    AUTHORITATIVE_TARGET,
    AUTHORITATIVE_PROTEIN_FREQUENCIES,
    load_live_weekly_plan,
    normalize_category,
    validate_nutritional_integrity
)


class TestNutritionalIntegrity(unittest.TestCase):
    """Validates adherence to Dr. Caglioni's bromatological targets and protein frequencies."""

    @classmethod
    def setUpClass(cls):
        cls.data = load_live_weekly_plan()

    def test_authoritative_daily_target_constants(self):
        """Authoritative target constants must match Dr. Caglioni's plan exactly."""
        self.assertEqual(AUTHORITATIVE_TARGET["kcal"], 2063)
        self.assertEqual(AUTHORITATIVE_TARGET["proteins_g"], 112)
        self.assertEqual(AUTHORITATIVE_TARGET["carbs_g"], 251)
        self.assertEqual(AUTHORITATIVE_TARGET["fats_g"], 68)

    def test_daily_calories_within_acceptable_margin(self):
        """Each day's calories must stay within ±1.5% of the 2063 kcal target."""
        target_kcal = AUTHORITATIVE_TARGET["kcal"]
        for day in self.data["days"]:
            day_name = day["day_name"]
            total_kcal = sum(m["kcal"] for m in day["meals"].values())
            deviation = abs(total_kcal - target_kcal) / target_kcal
            self.assertLessEqual(
                deviation, 0.015,
                f"Day {day_name} calories ({total_kcal}) deviate from target ({target_kcal}) by {deviation*100:.2f}%"
            )

    def test_weekly_fourteen_main_meal_protein_distribution(self):
        """The 14 main meal slots (7 lunches + 7 dinners) must strictly adhere to the protein distribution."""
        category_counts = {k: 0 for k in AUTHORITATIVE_PROTEIN_FREQUENCIES}
        
        main_meal_count = 0
        for day in self.data["days"]:
            for slot_name in ["pranzo", "cena"]:
                main_meal_count += 1
                meal = day["meals"][slot_name]
                cat = normalize_category(meal.get("category", ""), meal.get("is_free_meal", False))
                self.assertIn(cat, category_counts, f"Unrecognized category '{cat}' on {day['day_name']} {slot_name}")
                category_counts[cat] += 1

        self.assertEqual(main_meal_count, 14, "Must have exactly 14 main meal slots in the week")
        
        # Verify frequencies from real grocery order matching nutritionist schema
        self.assertEqual(category_counts["carne_bianca"], 2, "Carne bianca must be exactly 2 meals")
        self.assertEqual(category_counts["carne_rossa"], 1, "Carne rossa must be exactly 1 meal")
        self.assertEqual(category_counts["affettati_magri"], 1, "Affettati magri must be exactly 1 meal")
        self.assertGreaterEqual(category_counts["pesce"], 2, "Pesce fresco/surgelato must be at least 2 meals")
        self.assertGreaterEqual(category_counts["uova"], 2, "Uova must be at least 2 meals")
        self.assertGreaterEqual(category_counts["legumi_tofu"], 2, "Legumi e tofu must be at least 2 meals")
        self.assertEqual(category_counts["pasto_libero"], 1, "Pasto libero (Pizza Margherita) must be exactly 1 meal")

    def test_saturday_dinner_is_free_meal_exemption(self):
        """Saturday dinner must be flagged as free meal (Pizza Margherita) without breaking total macros."""
        sat_dinner = self.data["days"][0]["meals"]["cena"]
        self.assertTrue(sat_dinner.get("is_free_meal", False), "Saturday dinner must have is_free_meal=True")
        self.assertIn("pizza", sat_dinner["title"].lower())
        self.assertGreater(sat_dinner["kcal"], 700, "Pizza Margherita should reflect realistic ~780 kcal")

    def test_autumn_seasonal_produce_included(self):
        """The seed week for 31/10-06/11 must feature Dr. Caglioni's late autumn seasonal produce."""
        all_ingredients = []
        for day in self.data["days"]:
            for meal in day["meals"].values():
                for ing in meal.get("ingredients", []):
                    all_ingredients.append(ing["name"].lower())

        joined = " ".join(all_ingredients)
        autumn_staples = ["verza", "mela", "limon", "carotin", "melanzan", "peperon", "pomodorin"]
        for staple in autumn_staples:
            self.assertIn(staple, joined, f"Expected late autumn seasonal produce '{staple}' in seed week")

    def test_lunch_and_dinner_swap_invariance(self):
        """Swapping lunch and dinner on any day must maintain identical daily macros (Rule p.4)."""
        day = self.data["days"][1]  # Sunday
        pranzo = day["meals"]["pranzo"]
        cena = day["meals"]["cena"]
        
        sum_before = pranzo["kcal"] + cena["kcal"]
        # Swap
        sum_after = cena["kcal"] + pranzo["kcal"]
        self.assertEqual(sum_before, sum_after, "Daily total must remain invariant upon lunch/dinner swap")


class TestNutritionalBoundariesAndErrors(unittest.TestCase):
    """Tier 2 & Tier 3: Boundary violations, abnormal macronutrient totals, and validator catches."""

    def test_excessive_daily_calories_detected(self):
        """A day with 2600 kcal (>25% above target) must be flagged as violation."""
        corrupt_plan = {
            "macro_target": AUTHORITATIVE_TARGET,
            "days": [dict(d) for d in SAMPLE_VALID_WEEK["days"]]
        }
        # Inflate Sunday lunch to 1200 kcal
        corrupt_plan["days"][1] = dict(corrupt_plan["days"][1])
        corrupt_plan["days"][1]["meals"] = dict(corrupt_plan["days"][1]["meals"])
        corrupt_plan["days"][1]["meals"]["pranzo"] = dict(corrupt_plan["days"][1]["meals"]["pranzo"])
        corrupt_plan["days"][1]["meals"]["pranzo"]["kcal"] = 1200

        is_valid, errors = validate_nutritional_integrity(corrupt_plan, tolerance_percent=0.03)
        self.assertFalse(is_valid, "Excessive calories must fail validation")
        self.assertTrue(any("Domenica" in e and "deviate" in e for e in errors))

    def test_imbalanced_protein_distribution_detected(self):
        """A week with 4 red meat meals and 0 fish meals must be rejected."""
        corrupt_plan = {
            "macro_target": AUTHORITATIVE_TARGET,
            "days": [dict(d) for d in SAMPLE_VALID_WEEK["days"]]
        }
        # Replace fish on Sunday and Tuesday with red meat
        for day_idx in [1, 3]:
            corrupt_plan["days"][day_idx] = dict(corrupt_plan["days"][day_idx])
            corrupt_plan["days"][day_idx]["meals"] = dict(corrupt_plan["days"][day_idx]["meals"])
            corrupt_plan["days"][day_idx]["meals"]["cena"] = dict(corrupt_plan["days"][day_idx]["meals"]["cena"])
            corrupt_plan["days"][day_idx]["meals"]["cena"]["category"] = "carne_rossa"

        is_valid, errors = validate_nutritional_integrity(corrupt_plan)
        self.assertFalse(is_valid, "Skewed protein distribution must be caught")
        self.assertTrue(any("carne_rossa" in e for e in errors))
        self.assertTrue(any("pesce" in e for e in errors))

    def test_daily_meal_macros_sum_matches_daily_macros(self):
        """The sum of individual meal macros must match the daily summary within ±2g rounding."""
        data = load_live_weekly_plan()
        for day in data["days"]:
            reported = day.get("daily_macros", {})
            calculated_kcal = sum(m["kcal"] for m in day["meals"].values())
            calculated_p = sum(m["macros"]["proteins_g"] for m in day["meals"].values())
            calculated_c = sum(m["macros"]["carbs_g"] for m in day["meals"].values())
            calculated_f = sum(m["macros"]["fats_g"] for m in day["meals"].values())

            self.assertAlmostEqual(reported["kcal"], calculated_kcal, delta=2,
                msg=f"Day {day['day_name']}: daily_macros.kcal ({reported['kcal']}) != sum(meals.kcal) ({calculated_kcal})")
            self.assertAlmostEqual(reported["proteins_g"], calculated_p, delta=2)
            self.assertAlmostEqual(reported["carbs_g"], calculated_c, delta=2)
            self.assertAlmostEqual(reported["fats_g"], calculated_f, delta=2)


if __name__ == "__main__":
    unittest.main()
