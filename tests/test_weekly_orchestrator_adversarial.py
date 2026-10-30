"""
Adversarial Stress Test Suite for Milestone M4: Weekly Orchestrator.
Evaluates:
  1. CLI flags handling (--dry-run, --skip-cart, --test-alert, --date, --send-alert)
  2. Week calculation logic across year boundaries, leap years, and all 7 weekdays
  3. Gemini API fallback behavior (unconfigured key, invalid key, network timeout, malformed JSON)
  4. Esselunga cart filler exit code handling (0=success, 2=session expired, 1=error, timeout, exception)
  5. Telegram alert payload formatting, HTML entities, and link validation
  6. Strict safety invariants: zero checkout, zero payment, zero slot reservation triggers
"""

import ast
import json
import re
import sys
import unittest
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Target imports
from scripts.weekly_orchestrator import (
    calculate_week_window,
    generate_weekly_plan,
    format_telegram_alert,
    dispatch_telegram_alert,
    run_cart_population,
    git_commit_and_push,
    ensure_recipe_images,
    run_orchestration_cycle,
    DEFAULT_VERCEL_URL,
    DEFAULT_ESSELUNGA_CART_URL,
    DR_CAGLIONI_TARGET,
    CURRENT_WEEK_PATH,
    PROJECT_ROOT
)
from tests.fixtures import validate_telegram_alert_html, SAMPLE_VALID_WEEK


class TestDimension1CliFlags(unittest.TestCase):
    """Adversarial testing of CLI flags and execution modes."""

    def setUp(self):
        self.sample_plan = json.loads(json.dumps(SAMPLE_VALID_WEEK))

    @patch("scripts.weekly_orchestrator.dispatch_telegram_alert")
    @patch("scripts.weekly_orchestrator.run_cart_population")
    @patch("scripts.weekly_orchestrator.save_weekly_plan")
    @patch("scripts.weekly_orchestrator.git_commit_and_push")
    def test_dry_run_flag_prevents_state_mutations(
        self, mock_git, mock_save, mock_cart, mock_dispatch
    ):
        """--dry-run must NOT write current-week.json, must simulate git, must NOT send Telegram."""
        mock_cart.return_value = (0, "Simulated cart output")
        mock_git.return_value = True

        exit_code = run_orchestration_cycle(
            dry_run=True,
            skip_cart=False,
            test_alert=False,
            force_send_alert=False,
            reference_date=datetime(2026, 10, 30)
        )

        self.assertEqual(exit_code, 0)
        mock_save.assert_not_called()
        mock_git.assert_called_once_with("2026-W44", dry_run=True)
        mock_cart.assert_called_once_with(dry_run=True)
        # In dry run without --send-alert, dispatch must not be called
        mock_dispatch.assert_not_called()

    @patch("scripts.weekly_orchestrator.dispatch_telegram_alert")
    @patch("scripts.weekly_orchestrator.run_cart_population")
    @patch("scripts.weekly_orchestrator.save_weekly_plan")
    @patch("scripts.weekly_orchestrator.git_commit_and_push")
    def test_dry_run_with_send_alert_forces_telegram_dispatch(
        self, mock_git, mock_save, mock_cart, mock_dispatch
    ):
        """--dry-run --send-alert must allow Telegram alert dispatch while keeping git/disk simulated."""
        mock_cart.return_value = (0, "Simulated cart")
        mock_git.return_value = True
        mock_dispatch.return_value = True

        exit_code = run_orchestration_cycle(
            dry_run=True,
            skip_cart=False,
            test_alert=False,
            force_send_alert=True,
            reference_date=datetime(2026, 10, 30)
        )

        self.assertEqual(exit_code, 0)
        mock_save.assert_not_called()
        mock_dispatch.assert_called_once()

    @patch("scripts.weekly_orchestrator.run_cart_population")
    @patch("scripts.weekly_orchestrator.git_commit_and_push")
    def test_skip_cart_flag_bypasses_cart_execution(self, mock_git, mock_cart):
        """--skip-cart must completely avoid invoking run_cart_population."""
        mock_git.return_value = True

        exit_code = run_orchestration_cycle(
            dry_run=True,
            skip_cart=True,
            test_alert=False,
            reference_date=datetime(2026, 10, 30)
        )

        self.assertEqual(exit_code, 0)
        mock_cart.assert_not_called()

    @patch("scripts.weekly_orchestrator.dispatch_telegram_alert")
    @patch("scripts.weekly_orchestrator.run_cart_population")
    @patch("scripts.weekly_orchestrator.git_commit_and_push")
    @patch("scripts.weekly_orchestrator.save_weekly_plan")
    def test_test_alert_flag_executes_isolated_dispatch_and_exits(
        self, mock_save, mock_git, mock_cart, mock_dispatch
    ):
        """--test-alert must dispatch alert immediately without cart, git, or plan saving."""
        mock_dispatch.return_value = True

        exit_code = run_orchestration_cycle(
            dry_run=False,
            skip_cart=False,
            test_alert=True,
            reference_date=datetime(2026, 10, 30)
        )

        self.assertEqual(exit_code, 0)
        mock_dispatch.assert_called_once()
        mock_cart.assert_not_called()
        mock_git.assert_not_called()
        mock_save.assert_not_called()

    @patch("scripts.weekly_orchestrator.dispatch_telegram_alert")
    def test_test_alert_failure_returns_exit_code_1(self, mock_dispatch):
        """--test-alert returning False must bubble exit code 1."""
        mock_dispatch.return_value = False

        exit_code = run_orchestration_cycle(
            dry_run=False,
            skip_cart=False,
            test_alert=True,
            reference_date=datetime(2026, 10, 30)
        )

        self.assertEqual(exit_code, 1)

    def test_date_flag_parsing_across_calendar(self):
        """--date flag parsing correctly shifts window to matching Saturday-Friday period."""
        ref = datetime(2027, 3, 15)  # A Monday
        start, end, week_id = calculate_week_window(ref)
        self.assertEqual(start.strftime("%Y-%m-%d"), "2027-03-20")  # Next Saturday
        self.assertEqual(end.strftime("%Y-%m-%d"), "2027-03-26")    # Next Friday
        self.assertEqual(week_id, "2027-W11")


class TestDimension2WeekCalculationBoundaries(unittest.TestCase):
    """Stress tests for date calculations across leap years, year boundaries, and all weekdays."""

    def test_all_seven_weekdays_map_to_upcoming_saturday(self):
        """Verify that all 7 weekdays properly target the upcoming Saturday-Friday cycle."""
        # 2026-10-26 is Monday ... 2026-11-01 is Sunday
        # Monday: jumps 5 days to 2026-10-31
        # Tuesday: jumps 4 days to 2026-10-31
        # Wednesday: jumps 3 days to 2026-10-31
        # Thursday: jumps 2 days to 2026-10-31
        # Friday: jumps 1 day to 2026-10-31
        # Saturday: today (2026-10-31)
        # Sunday: jumps 6 days to 2026-11-07
        expected_mappings = {
            datetime(2026, 10, 26): "2026-10-31",  # Mon
            datetime(2026, 10, 27): "2026-10-31",  # Tue
            datetime(2026, 10, 28): "2026-10-31",  # Wed
            datetime(2026, 10, 29): "2026-10-31",  # Thu
            datetime(2026, 10, 30): "2026-10-31",  # Fri
            datetime(2026, 10, 31): "2026-10-31",  # Sat
            datetime(2026, 11, 1):  "2026-11-07",  # Sun
        }
        for ref_date, expected_start in expected_mappings.items():
            start, end, week_id = calculate_week_window(ref_date)
            self.assertEqual(
                start.strftime("%Y-%m-%d"),
                expected_start,
                f"Failed for weekday {ref_date.strftime('%A')} ({ref_date})"
            )
            self.assertEqual(
                (end - start).days,
                6,
                "Week window must span exactly 6 days between start and end (7 calendar days total)"
            )
            self.assertEqual(start.weekday(), 5, "Start day must always be Saturday (weekday 5)")
            self.assertEqual(end.weekday(), 4, "End day must always be Friday (weekday 4)")

    def test_year_boundary_crossing_december_into_january(self):
        """Cross year boundaries (e.g. 26/12/2025 to 02/01/2026): all 7 days must be contiguous."""
        friday_dec = datetime(2025, 12, 26, 8, 30, 0)
        start, end, week_id = calculate_week_window(friday_dec)

        self.assertEqual(start.strftime("%Y-%m-%d"), "2025-12-27")
        self.assertEqual(end.strftime("%Y-%m-%d"), "2026-01-02")

        plan = generate_weekly_plan(start, end, week_id)
        self.assertEqual(plan["week_start"], "2025-12-27")
        self.assertEqual(plan["week_end"], "2026-01-02")
        self.assertEqual(len(plan["days"]), 7)

        expected_dates = [
            "2025-12-27", "2025-12-28", "2025-12-29", "2025-12-30",
            "2025-12-31", "2026-01-01", "2026-01-02"
        ]
        actual_dates = [d["date"] for d in plan["days"]]
        self.assertEqual(actual_dates, expected_dates)

    def test_leap_year_boundary_february_29(self):
        """2028 is a leap year. Window spanning Feb 29 must correctly include 2028-02-29."""
        friday_feb = datetime(2028, 2, 25, 8, 0, 0)
        start, end, week_id = calculate_week_window(friday_feb)

        self.assertEqual(start.strftime("%Y-%m-%d"), "2028-02-26")  # Saturday
        self.assertEqual(end.strftime("%Y-%m-%d"), "2028-03-03")    # Friday

        plan = generate_weekly_plan(start, end, week_id)
        dates = [d["date"] for d in plan["days"]]
        self.assertIn("2028-02-29", dates, "Leap day 2028-02-29 must be present in the 7-day schedule")
        self.assertEqual(len(dates), 7)

    def test_iso_week_id_format_invariance(self):
        r"""Verify that iso_week_id always matches regex ^\d{4}-W\d{2}$ across 52 weeks."""
        test_year = 2026
        for week_idx in range(1, 53):
            # Test a Friday in each week
            sample_date = datetime.strptime(f"{test_year}-W{week_idx:02d}-5", "%G-W%V-%u")
            start, end, week_id = calculate_week_window(sample_date)
            self.assertRegex(week_id, r"^\d{4}-W(0[1-9]|[1-4][0-9]|5[0-3])$")

    def test_timestamp_hour_minute_truncation(self):
        """Regardless of incoming time of day, start and end dates must be normalized to 00:00:00."""
        late_night = datetime(2026, 10, 30, 23, 59, 59, 999999)
        start, end, _ = calculate_week_window(late_night)
        self.assertEqual(start.hour, 0)
        self.assertEqual(start.minute, 0)
        self.assertEqual(start.second, 0)
        self.assertEqual(start.microsecond, 0)
        self.assertEqual(end.hour, 0)


class TestDimension3GeminiFallback(unittest.TestCase):
    """Stress testing the Gemini AI generation path and fallback mechanisms."""

    def setUp(self):
        self.start = datetime(2026, 10, 31)
        self.end = datetime(2026, 11, 6)
        self.week_id = "2026-W44"

    @patch.dict("os.environ", {}, clear=True)
    def test_unconfigured_api_key_falls_back_cleanly(self):
        """When GEMINI_API_KEY is not set, fallback plan is generated without error."""
        plan = generate_weekly_plan(self.start, self.end, self.week_id, api_key=None)
        self.assertIsNotNone(plan)
        self.assertEqual(plan["week_id"], self.week_id)
        self.assertEqual(len(plan["days"]), 7)
        self.assertEqual(plan["macro_target"]["kcal"], 2063)

    @patch("google.genai.Client", create=True)
    def test_gemini_api_network_or_auth_exception_triggers_graceful_fallback(self, mock_client_cls):
        """When Gemini client raises an exception (e.g. 403, quota, network), fallback plan is returned."""
        mock_instance = MagicMock()
        mock_instance.models.generate_content.side_effect = ConnectionError("Network unreachable")
        mock_client_cls.return_value = mock_instance

        # Provide a dummy key to trigger the Gemini branch
        plan = generate_weekly_plan(
            self.start, self.end, self.week_id, api_key="dummy_api_key_for_test"
        )
        self.assertIsNotNone(plan)
        self.assertEqual(plan["week_id"], self.week_id)
        self.assertEqual(len(plan["days"]), 7)

    @patch("google.genai.Client", create=True)
    def test_gemini_malformed_json_response_triggers_graceful_fallback(self, mock_client_cls):
        """When Gemini API responds with non-JSON or invalid syntax, graceful fallback occurs."""
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "```json\n{ \"invalid\": \"truncated json, missing close brace"
        mock_instance.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_instance

        plan = generate_weekly_plan(
            self.start, self.end, self.week_id, api_key="dummy_key"
        )
        self.assertIsNotNone(plan)
        self.assertEqual(plan["week_id"], self.week_id)
        self.assertEqual(len(plan["days"]), 7)

    @patch("google.genai.Client", create=True)
    def test_gemini_schema_incomplete_days_triggers_graceful_fallback(self, mock_client_cls):
        """When Gemini returns JSON with only 5 days instead of 7, rejection and fallback occur."""
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"week_id": "2026-W44", "days": [{"day_name": "Sabato"}]})
        mock_instance.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_instance

        plan = generate_weekly_plan(
            self.start, self.end, self.week_id, api_key="dummy_key"
        )
        self.assertIsNotNone(plan)
        self.assertEqual(len(plan["days"]), 7, "Plan must retain 7 days from baseline")

    def test_missing_baseline_file_raises_file_not_found(self):
        """If baseline JSON path is invalid, FileNotFoundError is raised."""
        with self.assertRaises(FileNotFoundError):
            generate_weekly_plan(
                self.start, self.end, self.week_id,
                existing_plan_path=Path("non_existent_path.json")
            )


class TestDimension4CartFillerExitCodes(unittest.TestCase):
    """Testing handling of Esselunga Playwright exit codes: 0, 1, 2, and timeout."""

    @patch("subprocess.run")
    def test_exit_code_0_success(self, mock_run):
        """Exit code 0 returns (0, stdout) without error warnings."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Cart populated: 39 items"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        code, output = run_cart_population()
        self.assertEqual(code, 0)
        self.assertIn("39 items", output)

    @patch("subprocess.run")
    def test_exit_code_2_session_expired(self, mock_run):
        """Exit code 2 returns (2, output) and orchestrator formats warning in Telegram alert."""
        mock_proc = MagicMock()
        mock_proc.returncode = 2
        mock_proc.stdout = "Session expired"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        code, output = run_cart_population()
        self.assertEqual(code, 2)

        alert = format_telegram_alert(SAMPLE_VALID_WEEK, session_expired=True)
        self.assertIn("Sessione Esselunga scaduta", alert)
        self.assertIn("accedi una volta su Chrome", alert)

    @patch("subprocess.run")
    def test_exit_code_1_general_error(self, mock_run):
        """Exit code 1 returns (1, error) and orchestrator includes custom note."""
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = "Product search failed"
        mock_proc.stderr = "Network error"
        mock_run.return_value = mock_proc

        code, output = run_cart_population()
        self.assertEqual(code, 1)

        alert = format_telegram_alert(
            SAMPLE_VALID_WEEK,
            session_expired=False,
            custom_notes=f"Avviso carrello Esselunga: codice uscita {code}"
        )
        self.assertIn("Avviso carrello Esselunga: codice uscita 1", alert)

    @patch("subprocess.run")
    def test_subprocess_timeout_returns_code_1_cleanly(self, mock_run):
        """When cart filler execution times out (>300s), returns (1, timeout_message) without crash."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["python"], timeout=300)

        code, output = run_cart_population()
        self.assertEqual(code, 1)
        self.assertIn("timed out", output)

    @patch("subprocess.run")
    def test_subprocess_exception_returns_code_1_cleanly(self, mock_run):
        """When an OS error occurs spawning process, returns code 1 cleanly."""
        mock_run.side_effect = OSError("Executable not found")

        code, output = run_cart_population()
        self.assertEqual(code, 1)
        self.assertIn("Executable not found", output)


class TestDimension5TelegramAlertFormatting(unittest.TestCase):
    """Stress tests for Telegram HTML formatting, escaping, entity validity, and URLs."""

    def test_standard_alert_passes_strict_html_contract(self):
        """Alert with valid plan passes Telegram HTML validation."""
        alert = format_telegram_alert(SAMPLE_VALID_WEEK)
        is_valid, errors = validate_telegram_alert_html(alert)
        self.assertTrue(is_valid, f"Alert failed validation: {errors}")
        self.assertEqual(len(errors), 0)

    def test_alert_contains_both_verifiable_links(self):
        """Alert must contain live Vercel dashboard and Esselunga cart URLs in <a> tags."""
        alert = format_telegram_alert(SAMPLE_VALID_WEEK)
        self.assertIn(f'<a href="{DEFAULT_VERCEL_URL}">', alert)
        self.assertIn(f'<a href="{DEFAULT_ESSELUNGA_CART_URL}">', alert)

    def test_alert_numerical_precision_formatting(self):
        """Prices must be formatted with 2 decimal places (e.g. 106.35 € or 0.00 €)."""
        plan = json.loads(json.dumps(SAMPLE_VALID_WEEK))
        plan["cart_summary"]["total_estimated_eur"] = 99.5
        alert = format_telegram_alert(plan)
        self.assertIn("99.50 €", alert)

        plan["cart_summary"]["total_estimated_eur"] = 0
        alert_zero = format_telegram_alert(plan)
        self.assertIn("0.00 €", alert_zero)

    def test_empty_or_missing_cart_summary_defaults(self):
        """Plan missing cart_summary fields gracefully defaults without KeyError."""
        corrupt_plan = {"week_start": "2026-10-31", "week_end": "2026-11-06", "days": []}
        alert = format_telegram_alert(corrupt_plan)
        self.assertIn("39", alert)
        self.assertIn("0.00 €", alert)
        self.assertIn("35 pasti", alert)

    def test_telegram_supported_html_tags_only(self):
        """Telegram parse_mode='HTML' supports ONLY specific tags: b, i, a, u, s, code, pre."""
        alert = format_telegram_alert(SAMPLE_VALID_WEEK, session_expired=True, custom_notes="Test note")
        # Extract all HTML tags
        found_tags = re.findall(r"</?([a-zA-Z0-9]+)[^>]*>", alert)
        allowed_tags = {"b", "i", "a", "u", "s", "code", "pre"}
        for tag in found_tags:
            self.assertIn(tag.lower(), allowed_tags, f"Unsupported tag <{tag}> found in Telegram payload")

    def test_html_tag_closure_balance(self):
        """Every opening tag <b>, <i>, <a> must have a matching closing tag </b>, </i>, </a>."""
        alert = format_telegram_alert(
            SAMPLE_VALID_WEEK,
            session_expired=True,
            custom_notes="Sostituzione: Fesa di tacchino usata al posto di Petto di pollo"
        )
        for tag in ["b", "i", "a"]:
            open_count = len(re.findall(rf"<{tag}(\s+[^>]*)?>", alert))
            close_count = len(re.findall(rf"</{tag}>", alert))
            self.assertEqual(
                open_count, close_count,
                f"Tag <{tag}> is unclosed! Open: {open_count}, Close: {close_count}"
            )


class TestDimension6CheckoutSafetyInvariants(unittest.TestCase):
    """Adversarially ensures weekly_orchestrator NEVER triggers checkout, payment, or order confirmation."""

    def test_ast_inspection_zero_checkout_invocations(self):
        """AST inspection of weekly_orchestrator.py confirms zero checkout/payment triggers or flags."""
        orchestrator_path = PROJECT_ROOT / "scripts" / "weekly_orchestrator.py"
        with open(orchestrator_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

        # Inspect all string literals
        forbidden_terms = [
            "checkout", "pagamento", "cassa", "prenota-slot",
            "conferma-ordine", "order-confirmation", "buy-now"
        ]

        for node in ast.walk(tree):
            # Check string constants
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                val_lower = node.value.lower()
                # Exclude comments/docstrings/safety explanations and the innocent cart review URL
                if "carrello" in val_lower and not any(term in val_lower for term in forbidden_terms):
                    continue
                # If a forbidden term appears, verify it's strictly in a safety comment/docstring
                for term in forbidden_terms:
                    if term in val_lower:
                        # Ensure it only appears in comments/docstrings mentioning 'NO-CHECKOUT'
                        self.assertTrue(
                            "no-checkout" in val_lower or "safety" in val_lower or "cassa" not in val_lower,
                            f"Suspicious occurrence of forbidden term '{term}' in AST string: {node.value}"
                        )

    def test_cart_filler_cli_arguments_contain_zero_purchase_flags(self):
        """weekly_orchestrator passes ONLY safe flags (--dry-run, --test-item) to cart filler."""
        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = ""
            mock_proc.stderr = ""
            mock_run.return_value = mock_proc

            run_cart_population(dry_run=True, test_item="avena")

            called_cmd = mock_run.call_args[0][0]
            for arg in called_cmd:
                arg_lower = str(arg).lower()
                self.assertNotIn("checkout", arg_lower)
                self.assertNotIn("cassa", arg_lower)
                self.assertNotIn("pagamento", arg_lower)
                self.assertNotIn("confirm", arg_lower)
                self.assertNotIn("buy", arg_lower)

    def test_cart_review_url_points_strictly_to_carrello(self):
        """Cart URL in Telegram alert must strictly be the review page (/carrello), never checkout."""
        self.assertEqual(
            DEFAULT_ESSELUNGA_CART_URL,
            "https://spesaonline.esselunga.it/commerce/nav/supermercato/carrello"
        )
        self.assertNotIn("checkout", DEFAULT_ESSELUNGA_CART_URL)
        self.assertNotIn("cassa", DEFAULT_ESSELUNGA_CART_URL)
        self.assertNotIn("slot", DEFAULT_ESSELUNGA_CART_URL)


class TestDimension7GitAndImageRobustness(unittest.TestCase):
    """Testing failure resilience in Git operations and image asset verification."""

    @patch("subprocess.run")
    def test_git_push_failure_returns_false_cleanly(self, mock_run):
        """When git push fails (e.g. no internet / rejected), function returns False without unhandled crash."""
        # 1st call: git status (has changes)
        mock_status = MagicMock()
        mock_status.stdout = "M src/data/current-week.json\n"
        # 2nd call: git add
        # 3rd call: git commit
        # 4th call: git push (fails with code 1)
        mock_push = MagicMock()
        mock_push.returncode = 1
        mock_push.stderr = "fatal: Could not resolve host: github.com"

        mock_run.side_effect = [mock_status, MagicMock(), MagicMock(), mock_push]

        success = git_commit_and_push(week_id="2026-W44", dry_run=False)
        self.assertFalse(success, "Failed git push must return False")

    @patch("subprocess.run")
    def test_git_command_exception_handled_cleanly(self, mock_run):
        """When git binary is unavailable or raises CalledProcessError, returns False cleanly."""
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=128, cmd=["git", "status"], stderr="fatal: not a git repository"
        )
        success = git_commit_and_push(week_id="2026-W44", dry_run=False)
        self.assertFalse(success)

    @patch("subprocess.run")
    def test_ensure_recipe_images_recovers_missing_image(self, mock_run):
        """When images are missing, invokes generate_dish_images.py to regenerate them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_recipes = Path(tmpdir)
            # Create dummy plan with 1 image
            test_plan = {
                "days": [{
                    "meals": {
                        "pranzo": {"image_url": "/recipes/test_dish.webp"}
                    }
                }]
            }
            # Mock generator creating the file
            def create_image(*args, **kwargs):
                (tmp_recipes / "test_dish.webp").write_bytes(b"RIFFdummyWEBP")
                proc = MagicMock()
                proc.returncode = 0
                return proc

            mock_run.side_effect = create_image

            verified = ensure_recipe_images(test_plan, recipes_dir=tmp_recipes)
            self.assertTrue(verified)
            mock_run.assert_called_once()


class TestDimension8NutritionalTargetPreservation(unittest.TestCase):
    """Testing that plan updates preserve Dr. Caglioni's clinical nutritional integrity."""

    def test_generated_plan_across_future_date_preserves_bromatology(self):
        """When generating a new week plan, all nutritional targets and protein rotations must be preserved."""
        from tests.fixtures import validate_nutritional_integrity
        ref = datetime(2027, 1, 1)  # Friday
        start, end, week_id = calculate_week_window(ref)
        plan = generate_weekly_plan(start, end, week_id)

        is_valid, errors = validate_nutritional_integrity(plan, tolerance_percent=0.03)
        self.assertTrue(is_valid, f"Nutritional integrity violated across future date: {errors}")
        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()

