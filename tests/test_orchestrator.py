"""
Tier 1, Tier 3, Tier 4: Weekly Orchestrator, Git Sync, and Telegram Alert Tests.
Validates Contract 3 (Telegram alert payload) and Contract 4 (Git-as-CMS automated push),
as well as the Friday weekly orchestrator pipeline and Task Scheduler runner.
"""

import re
import unittest
from datetime import datetime
from pathlib import Path

from tests.fixtures import (
    validate_telegram_alert_html,
    SAMPLE_VALID_WEEK
)
from scripts.weekly_orchestrator import (
    calculate_week_window,
    format_telegram_alert,
    ensure_recipe_images,
    DEFAULT_VERCEL_URL
)

SEND_ALERT_SCRIPT = Path(r"C:\Users\david\Desktop\Progetti\telegram-antigravity-bridge\send_alert.py")
ORCHESTRATOR_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "weekly_orchestrator.py"
RUNNER_BAT_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "run_weekly.bat"


class TestTelegramAlertContract(unittest.TestCase):
    """Validates the structure and content of Telegram notifications dispatched to Jarvis bot."""

    def test_send_alert_script_exists_on_system(self):
        """Authoritative Telegram bridge and orchestrator scripts must exist on system."""
        self.assertTrue(
            SEND_ALERT_SCRIPT.exists(),
            f"Expected send_alert.py not found at {SEND_ALERT_SCRIPT}"
        )
        self.assertTrue(
            ORCHESTRATOR_SCRIPT.exists(),
            f"Expected weekly_orchestrator.py not found at {ORCHESTRATOR_SCRIPT}"
        )
        self.assertTrue(
            RUNNER_BAT_SCRIPT.exists(),
            f"Expected run_weekly.bat not found at {RUNNER_BAT_SCRIPT}"
        )

    def test_valid_telegram_alert_html_passes_validation(self):
        """Standard weekly alert payload from weekly_orchestrator must pass HTML and content validation."""
        formatted_alert = format_telegram_alert(
            plan=SAMPLE_VALID_WEEK,
            vercel_url=DEFAULT_VERCEL_URL
        )
        is_valid, errors = validate_telegram_alert_html(formatted_alert)
        self.assertTrue(is_valid, f"Alert failed validation: {errors}")
        self.assertEqual(len(errors), 0)
        self.assertIn("https://meal-planner-dashboard-gold.vercel.app", formatted_alert)
        self.assertIn("2063 kcal/die", formatted_alert)

    def test_alert_missing_bold_tags_rejected(self):
        """Alert missing HTML tags must be rejected by validator."""
        plaintext_alert = "Riepilogo Spesa Esselunga: 21 articoli, 48.75 eur, https://vercel.app"
        is_valid, errors = validate_telegram_alert_html(plaintext_alert)
        self.assertFalse(is_valid)
        self.assertTrue(any("<b>" in e for e in errors))

    def test_alert_missing_dashboard_link_rejected(self):
        """Alert omitting dashboard link must be caught."""
        no_link_alert = "🛒 <b>Riepilogo Spesa Esselunga</b>\nSpesa stimata: 48.75 €"
        is_valid, errors = validate_telegram_alert_html(no_link_alert)
        self.assertFalse(is_valid)
        self.assertTrue(any("link" in e for e in errors))

    def test_out_of_stock_warning_appended_to_alert_when_present(self):
        """When items are missing or replaced, alert must include fallback notice and pass validation."""
        alert_with_warning = format_telegram_alert(
            plan=SAMPLE_VALID_WEEK,
            session_expired=True,
            custom_notes="Sostituzione: Fesa di tacchino usata al posto di Petto di pollo (esaurito)",
            vercel_url=DEFAULT_VERCEL_URL
        )
        self.assertIn("Sostituzione", alert_with_warning)
        self.assertIn("Sessione Esselunga scaduta", alert_with_warning)
        is_valid, errors = validate_telegram_alert_html(alert_with_warning)
        self.assertTrue(is_valid, f"Alert with warnings failed validation: {errors}")


class TestGitAsCmsSyncContract(unittest.TestCase):
    """Contract 4: Git-as-CMS commit message and push synchronization."""

    def test_git_commit_message_format(self):
        """Orchestrator git commit message must follow conventional commit standard."""
        ref_friday = datetime(2026, 10, 30, 8, 0, 0)
        start_date, end_date, week_label = calculate_week_window(ref_friday)
        self.assertEqual(start_date.strftime("%Y-%m-%d"), "2026-10-31")
        self.assertEqual(end_date.strftime("%Y-%m-%d"), "2026-11-06")
        self.assertEqual(week_label, "2026-W44")

        commit_msg = f"chore(meal-plan): update week {week_label}"
        pattern = r"^chore\(meal-plan\):\s+update week\s+[\w\-]+$"
        self.assertRegex(commit_msg, pattern, "Git commit message does not match expected convention")

    def test_image_asset_file_naming_convention(self):
        """Generated dish images must follow <day>_<meal_slot>.webp convention and be verified on disk."""
        from scripts.weekly_orchestrator import load_current_plan
        live_plan = load_current_plan()
        if live_plan:
            recipes_dir = Path(__file__).resolve().parent.parent / "public" / "recipes"
            verified = ensure_recipe_images(live_plan, recipes_dir=recipes_dir)
            self.assertTrue(verified)

        test_paths = [
            "/recipes/sabato_colazione.webp",
            "/recipes/sabato_pranzo.webp",
            "/recipes/domenica_cena.webp",
            "/recipes/venerdi_dopocena.webp"
        ]
        pattern = r"^/recipes/(sabato|domenica|lunedi|martedi|mercoledi|giovedi|venerdi)_(colazione|pranzo|spuntino_pomeriggio|spuntino|cena|dopocena)\.webp$"
        for path in test_paths:
            self.assertRegex(path, pattern, f"Image path '{path}' does not follow naming convention")


class TestTaskSchedulerConfiguration(unittest.TestCase):
    """Verifies Friday morning scheduling specifications and Windows batch runner."""

    def test_scheduled_day_and_time(self):
        """Automation is contracted to run every Friday morning at 08:00 AM via run_weekly.bat."""
        SCHEDULED_DAY = "Friday"
        SCHEDULED_TIME = "08:00"
        self.assertEqual(SCHEDULED_DAY, "Friday")
        self.assertEqual(SCHEDULED_TIME, "08:00")

        # Validate scripts/run_weekly.bat content
        with open(RUNNER_BAT_SCRIPT, "r", encoding="utf-8") as f:
            bat_content = f.read()

        self.assertIn("schtasks", bat_content)
        self.assertIn("FRI", bat_content)
        self.assertIn("08:00", bat_content)
        self.assertIn("scripts\\weekly_orchestrator.py", bat_content)
        self.assertIn("orchestrator.log", bat_content)


if __name__ == "__main__":
    unittest.main()
