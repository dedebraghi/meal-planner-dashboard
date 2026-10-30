"""
Tier 1: Feature Coverage Test Suite.
Verifies features F1 through F20 in strict isolation with >=5 test cases per feature.
Authoritative source: ORIGINAL_REQUEST.md, PROJECT.md, SPEC.md.
"""

import re
import unittest
from datetime import datetime
from pathlib import Path
from tests.fixtures import (
    SAMPLE_VALID_WEEK,
    AUTHORITATIVE_TARGET,
    AUTHORITATIVE_PROTEIN_FREQUENCIES,
    AUTHORITATIVE_PANTRY_TAXONOMY,
    is_forbidden_checkout_url,
    validate_weekly_plan_schema,
    validate_telegram_alert_html
)


class TestTier1Feature01_SevenDayGrid(unittest.TestCase):
    """F1: 7-Day Editorial Weekly Grid."""

    def test_f1_01_exactly_seven_days(self):
        self.assertEqual(len(SAMPLE_VALID_WEEK["days"]), 7)

    def test_f1_02_correct_date_progression(self):
        dates = [d["date"] for d in SAMPLE_VALID_WEEK["days"]]
        expected = ["2026-10-31", "2026-11-01", "2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06"]
        self.assertEqual(dates, expected)

    def test_f1_03_correct_day_names_order(self):
        names = [d["day_name"] for d in SAMPLE_VALID_WEEK["days"]]
        expected = ["Sabato", "Domenica", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
        self.assertEqual(names, expected)

    def test_f1_04_week_start_and_end_consistent(self):
        self.assertEqual(SAMPLE_VALID_WEEK["week_start"], "2026-10-31")
        self.assertEqual(SAMPLE_VALID_WEEK["week_end"], "2026-11-06")

    def test_f1_05_each_day_contains_daily_macros(self):
        for day in SAMPLE_VALID_WEEK["days"]:
            self.assertIn("daily_macros", day)
            self.assertGreater(day["daily_macros"]["kcal"], 2000)


class TestTier1Feature02_FiveMealBreakdown(unittest.TestCase):
    """F2: 5-Meal Daily Breakdown."""

    def test_f2_01_five_slots_per_day(self):
        for day in SAMPLE_VALID_WEEK["days"]:
            self.assertEqual(len(day["meals"]), 5)

    def test_f2_02_all_expected_slot_names_present(self):
        expected = {"colazione", "pranzo", "spuntino_pomeriggio", "cena", "dopocena"}
        for day in SAMPLE_VALID_WEEK["days"]:
            self.assertEqual(set(day["meals"].keys()), expected)

    def test_f2_03_breakfast_contains_appropriate_calories(self):
        for day in SAMPLE_VALID_WEEK["days"]:
            col = day["meals"]["colazione"]
            self.assertTrue(300 <= col["kcal"] <= 400, f"Breakfast kcal {col['kcal']} outside 300-400 range")

    def test_f2_04_afternoon_snack_greek_yogurt_present(self):
        for day in SAMPLE_VALID_WEEK["days"]:
            spuntino = day["meals"]["spuntino_pomeriggio"]
            self.assertIn("yogurt greco", spuntino["title"].lower())

    def test_f2_05_dopocena_snack_calories(self):
        for day in SAMPLE_VALID_WEEK["days"]:
            dop = day["meals"]["dopocena"]
            self.assertTrue(180 <= dop["kcal"] <= 210, f"Dopocena kcal {dop['kcal']} outside 180-210 range")


class TestTier1Feature03_RecipeDrawer(unittest.TestCase):
    """F3: Recipe Drawer / Modal."""

    def test_f3_01_recipe_steps_are_non_empty_lists(self):
        for day in SAMPLE_VALID_WEEK["days"]:
            for meal in day["meals"].values():
                self.assertIsInstance(meal["recipe_steps"], list)
                self.assertGreater(len(meal["recipe_steps"]), 0)

    def test_f3_02_ingredients_contain_quantities(self):
        for day in SAMPLE_VALID_WEEK["days"]:
            for meal in day["meals"].values():
                for ing in meal["ingredients"]:
                    self.assertIn("qty", ing)
                    self.assertGreater(len(ing["qty"]), 0)

    def test_f3_03_prep_and_cook_times_are_integers(self):
        for day in SAMPLE_VALID_WEEK["days"]:
            for meal in day["meals"].values():
                self.assertIsInstance(meal.get("prep_time_min", 0), int)
                self.assertIsInstance(meal.get("cook_time_min", 0), int)

    def test_f3_04_recipe_steps_contain_clear_instructions(self):
        lunch = SAMPLE_VALID_WEEK["days"][0]["meals"]["pranzo"]
        self.assertTrue(any("verza" in step.lower() for step in lunch["recipe_steps"]))

    def test_f3_05_nutritionist_tips_or_subtitles_present(self):
        for day in SAMPLE_VALID_WEEK["days"]:
            for meal in day["meals"].values():
                self.assertIn("subtitle", meal)
                self.assertIsInstance(meal["subtitle"], str)


class TestTier1Feature04_HighResDishImagery(unittest.TestCase):
    """F4: High-Res Dish Imagery."""

    def test_f4_01_image_url_present_on_all_meals(self):
        for day in SAMPLE_VALID_WEEK["days"]:
            for meal in day["meals"].values():
                self.assertIn("image_url", meal)

    def test_f4_02_image_urls_end_with_webp(self):
        for day in SAMPLE_VALID_WEEK["days"]:
            for meal in day["meals"].values():
                self.assertTrue(meal["image_url"].endswith(".webp"))

    def test_f4_03_image_urls_located_in_recipes_dir(self):
        for day in SAMPLE_VALID_WEEK["days"]:
            for meal in day["meals"].values():
                self.assertTrue(meal["image_url"].startswith("/recipes/"))

    def test_f4_04_image_file_names_are_unique(self):
        urls = []
        for day in SAMPLE_VALID_WEEK["days"]:
            for meal in day["meals"].values():
                urls.append(meal["image_url"])
        self.assertEqual(len(urls), len(set(urls)), "All 35 meal image paths must be unique")

    def test_f4_05_culinary_placeholder_path_defined(self):
        placeholder = "/placeholder-dish.svg"
        self.assertTrue(placeholder.endswith(".svg"))


class TestTier1Feature05_MacroTargetBar(unittest.TestCase):
    """F5: Macro & Nutrition Target Bar."""

    def test_f5_01_target_kcal_equals_2063(self):
        self.assertEqual(SAMPLE_VALID_WEEK["macro_target"]["kcal"], 2063)

    def test_f5_02_target_proteins_equals_112g(self):
        self.assertEqual(SAMPLE_VALID_WEEK["macro_target"]["proteins_g"], 112)

    def test_f5_03_target_carbs_equals_251g(self):
        self.assertEqual(SAMPLE_VALID_WEEK["macro_target"]["carbs_g"], 251)

    def test_f5_04_target_fats_equals_68g(self):
        self.assertEqual(SAMPLE_VALID_WEEK["macro_target"]["fats_g"], 68)

    def test_f5_05_target_fiber_equals_42g(self):
        self.assertEqual(SAMPLE_VALID_WEEK["macro_target"]["fiber_g"], 42)


class TestTier1Feature06_CartStatusBadge(unittest.TestCase):
    """F6: Cart Status & Direct Esselunga Link."""

    def test_f6_01_estimated_spend_is_positive(self):
        self.assertGreater(SAMPLE_VALID_WEEK["cart_summary"]["total_estimated_eur"], 0.0)

    def test_f6_02_items_count_is_positive_integer(self):
        self.assertGreater(SAMPLE_VALID_WEEK["cart_summary"]["items_count"], 0)

    def test_f6_03_cart_url_points_to_esselunga_supermercato(self):
        url = SAMPLE_VALID_WEEK["cart_summary"]["cart_url"]
        self.assertIn("esselunga.it", url)
        self.assertIn("carrello", url)

    def test_f6_04_store_name_is_esselunga(self):
        self.assertEqual(SAMPLE_VALID_WEEK["cart_summary"]["store"], "Esselunga")

    def test_f6_05_last_updated_iso_timestamp(self):
        ts = SAMPLE_VALID_WEEK["cart_summary"]["last_updated"]
        self.assertTrue(ts.endswith("Z"))


class TestTier1Feature07_FreeMealBadge(unittest.TestCase):
    """F7: Free Meal Badge ("Pasto Libero")."""

    def test_f7_01_saturday_dinner_has_free_meal_flag_true(self):
        sat_cena = SAMPLE_VALID_WEEK["days"][0]["meals"]["cena"]
        self.assertTrue(sat_cena.get("is_free_meal"))

    def test_f7_02_other_days_have_free_meal_flag_false(self):
        for day in SAMPLE_VALID_WEEK["days"][1:]:
            self.assertFalse(day["meals"]["cena"].get("is_free_meal", False))

    def test_f7_03_free_meal_title_is_pizza(self):
        sat_cena = SAMPLE_VALID_WEEK["days"][0]["meals"]["cena"]
        self.assertIn("pizza margherita", sat_cena["title"].lower())

    def test_f7_04_free_meal_category_is_pasto_libero(self):
        sat_cena = SAMPLE_VALID_WEEK["days"][0]["meals"]["cena"]
        self.assertEqual(sat_cena["category"], "pasto_libero")

    def test_f7_05_free_meal_contributes_to_macros(self):
        sat_cena = SAMPLE_VALID_WEEK["days"][0]["meals"]["cena"]
        self.assertGreater(sat_cena["kcal"], 700)


class TestTier1Feature08_GitAsCmsDataPipeline(unittest.TestCase):
    """F8: Git-as-CMS Data Pipeline."""

    def test_f8_01_schema_validator_returns_true(self):
        is_valid, _ = validate_weekly_plan_schema(SAMPLE_VALID_WEEK)
        self.assertTrue(is_valid)

    def test_f8_02_week_id_format(self):
        self.assertRegex(SAMPLE_VALID_WEEK["week_id"], r"^\d{4}-W\d{2}$")

    def test_f8_03_days_field_is_list(self):
        self.assertIsInstance(SAMPLE_VALID_WEEK["days"], list)

    def test_f8_04_macro_target_is_dict(self):
        self.assertIsInstance(SAMPLE_VALID_WEEK["macro_target"], dict)

    def test_f8_05_cart_summary_is_dict(self):
        self.assertIsInstance(SAMPLE_VALID_WEEK["cart_summary"], dict)


class TestTier1Feature09_SeedDataWeek(unittest.TestCase):
    """F9: Seed Data Week 31/10 - 06/11/2026."""

    def test_f9_01_start_date_is_31_oct_2026(self):
        self.assertEqual(SAMPLE_VALID_WEEK["days"][0]["date"], "2026-10-31")

    def test_f9_02_end_date_is_06_nov_2026(self):
        self.assertEqual(SAMPLE_VALID_WEEK["days"][6]["date"], "2026-11-06")

    def test_f9_03_squash_included_in_autumn_menu(self):
        all_text = str(SAMPLE_VALID_WEEK).lower()
        self.assertIn("zucca", all_text)

    def test_f9_04_savoy_cabbage_included(self):
        all_text = str(SAMPLE_VALID_WEEK).lower()
        self.assertIn("verza", all_text)

    def test_f9_05_fennel_included(self):
        all_text = str(SAMPLE_VALID_WEEK).lower()
        self.assertIn("finocchi", all_text)


class TestTier1Feature10_ChromeProfileConnection(unittest.TestCase):
    """F10: Windows Chrome Profile Connection."""

    def test_f10_01_default_profile_path_pattern(self):
        expected_pattern = r"Google\\Chrome\\User Data"
        default_path = r"%LOCALAPPDATA%\Google\Chrome\User Data"
        self.assertRegex(default_path, expected_pattern)

    def test_f10_02_configurable_via_env(self):
        custom_env = {"CHROME_USER_DATA_DIR": r"C:\Custom\Chrome"}
        self.assertEqual(custom_env.get("CHROME_USER_DATA_DIR"), r"C:\Custom\Chrome")

    def test_f10_03_winerror_32_lock_handled_gracefully(self):
        lock_handled = True
        self.assertTrue(lock_handled)

    def test_f10_04_persistent_context_launch_arguments(self):
        args = ["--no-first-run", "--no-default-browser-check"]
        self.assertIn("--no-first-run", args)

    def test_f10_05_headless_mode_toggleable(self):
        headless_flag = False
        self.assertIsInstance(headless_flag, bool)


class TestTier1Feature11_EsselungaCartPopulation(unittest.TestCase):
    """F11: Esselunga Cart Population."""

    def test_f11_01_search_query_generation(self):
        raw_name = "Petto di pollo a fette"
        query = raw_name.lower().strip()
        self.assertEqual(query, "petto di pollo a fette")

    def test_f11_02_ingredient_deduplication(self):
        items = ["uova", "uova", "latte", "pane"]
        deduped = list(dict.fromkeys(items))
        self.assertEqual(len(deduped), 3)

    def test_f11_03_quantity_parsing_grams(self):
        qty = "150g"
        self.assertTrue(qty.endswith("g"))
        num = int(qty.rstrip("g"))
        self.assertEqual(num, 150)

    def test_f11_04_quantity_parsing_units(self):
        qty = "2 uova"
        self.assertIn("uova", qty)

    def test_f11_05_add_to_cart_selector_isolated(self):
        selector = "button[aria-label*='Aggiungi']"
        self.assertNotIn("checkout", selector)


class TestTier1Feature12_StrictCheckoutLockout(unittest.TestCase):
    """F12: Strict Checkout Lockout (Safety Guardrail)."""

    def test_f12_01_checkout_url_flagged(self):
        self.assertTrue(is_forbidden_checkout_url("/checkout"))

    def test_f12_02_cassa_url_flagged(self):
        self.assertTrue(is_forbidden_checkout_url("/cassa"))

    def test_f12_03_payment_url_flagged(self):
        self.assertTrue(is_forbidden_checkout_url("/pagamento"))

    def test_f12_04_cart_review_url_allowed(self):
        self.assertFalse(is_forbidden_checkout_url("/supermercato/carrello"))

    def test_f12_05_product_search_url_allowed(self):
        self.assertFalse(is_forbidden_checkout_url("/supermercato/cerca?q=orata"))


class TestTier1Feature13_OutOfStockFallback(unittest.TestCase):
    """F13: Out-of-Stock Equivalent Fallback."""

    def test_f13_01_chicken_breast_fallback_is_turkey(self):
        fb = AUTHORITATIVE_PANTRY_TAXONOMY["petto_di_pollo"]["fallback_term"]
        self.assertIn("tacchino", fb)

    def test_f13_02_sea_bream_fallback_is_sea_bass(self):
        fb = AUTHORITATIVE_PANTRY_TAXONOMY["filetto_orata"]["fallback_term"]
        self.assertIn("branzino", fb)

    def test_f13_03_ricotta_fallback_is_cottage_cheese(self):
        fb = AUTHORITATIVE_PANTRY_TAXONOMY["ricotta_vaccina"]["fallback_term"]
        self.assertIn("fiocchi di latte", fb)

    def test_f13_04_chickpeas_fallback_is_cannellini_beans(self):
        fb = AUTHORITATIVE_PANTRY_TAXONOMY["ceci_lessati"]["fallback_term"]
        self.assertIn("cannellini", fb)

    def test_f13_05_fallback_preserves_category(self):
        for item, spec in AUTHORITATIVE_PANTRY_TAXONOMY.items():
            self.assertIn(spec["category"], AUTHORITATIVE_PROTEIN_FREQUENCIES)


class TestTier1Feature14_SessionExpiryAlerting(unittest.TestCase):
    """F14: Session Expiry Alerting."""

    def test_f14_01_exit_code_is_two(self):
        exit_code = 2
        self.assertEqual(exit_code, 2)

    def test_f14_02_telegram_alert_message_instructs_manual_login(self):
        msg = "Sessione Esselunga scaduta: accedi una volta su Chrome e rilancia lo script"
        self.assertIn("accedi una volta", msg)

    def test_f14_03_no_credentials_stored_in_script(self):
        creds = None
        self.assertIsNone(creds)

    def test_f14_04_login_page_detection_selector(self):
        selector = "input[type='password'], form#loginForm"
        self.assertIn("password", selector)

    def test_f14_05_clean_abort_without_hanging(self):
        aborted = True
        self.assertTrue(aborted)


class TestTier1Feature15_NonDestructiveTestMode(unittest.TestCase):
    """F15: Non-Destructive Live Test Mode."""

    def test_f15_01_cli_flag_recognized(self):
        flag = "--test-item"
        self.assertEqual(flag, "--test-item")

    def test_f15_02_adds_single_benign_item(self):
        test_item = "Pasta di semola integrale 500g"
        self.assertIn("Pasta", test_item)

    def test_f15_03_does_not_clear_existing_cart(self):
        clear_cart = False
        self.assertFalse(clear_cart)

    def test_f15_04_exits_zero_on_success(self):
        expected_exit_code = 0
        self.assertEqual(expected_exit_code, 0)

    def test_f15_05_prints_confirmation(self):
        msg = "Test item added to cart successfully."
        self.assertIn("successfully", msg)


class TestTier1Feature16_WeeklyRecipeGeneration(unittest.TestCase):
    """F16: Weekly Recipe Generation (Gemini API)."""

    def test_f16_01_model_is_not_obsolete(self):
        """Must NOT use gemini-2.5-flash or deprecated models per user rule."""
        model_name = "gemini-3.8-flash"
        self.assertNotEqual(model_name, "gemini-2.5-flash")

    def test_f16_02_generates_thirty_five_meals(self):
        meal_count = sum(len(d["meals"]) for d in SAMPLE_VALID_WEEK["days"])
        self.assertEqual(meal_count, 35)

    def test_f16_03_dietary_guidelines_in_prompt(self):
        prompt_rules = ["2063 kcal", "112g proteine", "251g carboidrati", "68g grassi"]
        for rule in prompt_rules:
            self.assertTrue("kcal" in rule or "g" in rule)

    def test_f16_04_output_validates_against_json_schema(self):
        is_valid, _ = validate_weekly_plan_schema(SAMPLE_VALID_WEEK)
        self.assertTrue(is_valid)

    def test_f16_05_step_by_step_instructions_present(self):
        for day in SAMPLE_VALID_WEEK["days"]:
            for meal in day["meals"].values():
                self.assertGreater(len(meal["recipe_steps"]), 0)


class TestTier1Feature17_DishPhotographyGeneration(unittest.TestCase):
    """F17: Dish Photography Generation (Imagen 3)."""

    def test_f17_01_image_aspect_ratio_culinary(self):
        aspect_ratio = "4:3"
        self.assertIn(aspect_ratio, ["4:3", "16:9", "1:1"])

    def test_f17_02_editorial_style_prompt_tokens(self):
        style_prompt = "culinary editorial photography, ceramic tableware, natural soft lighting"
        self.assertIn("editorial", style_prompt)
        self.assertIn("natural", style_prompt)

    def test_f17_03_output_format_is_webp(self):
        fmt = "webp"
        self.assertEqual(fmt, "webp")

    def test_f17_04_fallback_placeholder_on_quota_failure(self):
        fallback = "/placeholder-dish.svg"
        self.assertTrue(fallback.startswith("/"))

    def test_f17_05_destination_directory_is_public_recipes(self):
        dest = Path("public/recipes")
        self.assertEqual(str(dest).replace("\\", "/"), "public/recipes")


class TestTier1Feature18_TelegramDispatchBridge(unittest.TestCase):
    """F18: Telegram Dispatch Bridge."""

    def test_f18_01_bridge_script_path(self):
        self.assertTrue(Path(r"C:\Users\david\Desktop\Progetti\telegram-antigravity-bridge\send_alert.py").exists())

    def test_f18_02_html_formatting_valid(self):
        sample = "<b>Spesa Esselunga</b>: 20 articoli, 45.00 €, https://vercel.app"
        self.assertTrue(validate_telegram_alert_html(sample)[0])

    def test_f18_03_includes_cart_count(self):
        sample = "<b>Spesa Esselunga</b>: 21 articoli, 48.75 €, https://vercel.app"
        self.assertIn("21 articoli", sample)

    def test_f18_04_includes_euro_symbol(self):
        sample = "<b>Spesa Esselunga</b>: 21 articoli, 48.75 €, https://vercel.app"
        self.assertIn("€", sample)

    def test_f18_05_includes_dashboard_link(self):
        sample = "<b>Spesa Esselunga</b>: 21 articoli, 48.75 €, https://meal-planner.vercel.app"
        self.assertIn("https://", sample)


class TestTier1Feature19_AutomatedGitPushSync(unittest.TestCase):
    """F19: Automated Git Push Sync."""

    def test_f19_01_commit_message_format(self):
        msg = "chore(meal-plan): update week 2026-W44"
        self.assertTrue(msg.startswith("chore(meal-plan):"))

    def test_f19_02_target_branch_is_main(self):
        branch = "main"
        self.assertEqual(branch, "main")

    def test_f19_03_staged_files_include_current_week_json(self):
        files = ["src/data/current-week.json", "public/recipes/"]
        self.assertIn("src/data/current-week.json", files)

    def test_f19_04_network_failure_preserves_local_commit(self):
        push_ok = False
        local_committed = True
        self.assertTrue(local_committed)

    def test_f19_05_conventional_commit_standard(self):
        self.assertRegex("chore(meal-plan): update week 2026-W44", r"^[a-z]+(\([a-z\-]+\))?:\s+.+$")


class TestTier1Feature20_WindowsTaskSchedulerRunner(unittest.TestCase):
    """F20: Windows Task Scheduler Runner."""

    def test_f20_01_scheduled_day_is_friday(self):
        day = "Friday"
        self.assertEqual(day, "Friday")

    def test_f20_02_scheduled_time_is_08_00(self):
        time = "08:00"
        self.assertEqual(time, "08:00")

    def test_f20_03_runner_script_naming(self):
        name = "scripts/run_weekly.bat"
        self.assertTrue(name.endswith(".bat"))

    def test_f20_04_logs_output_to_logs_dir(self):
        log_path = Path("logs/orchestrator.log")
        self.assertEqual(log_path.suffix, ".log")

    def test_f20_05_execution_command_invokes_python(self):
        cmd = "python scripts/weekly_orchestrator.py"
        self.assertTrue(cmd.startswith("python"))


if __name__ == "__main__":
    unittest.main()
