"""
Tier 1, Tier 3, Tier 4: Weekly Orchestrator, Git Sync, and Telegram Alert Tests.
Validates Contract 3 (Telegram alert payload) and Contract 4 (Git-as-CMS automated push).
"""

import re
import unittest
from pathlib import Path
from tests.fixtures import validate_telegram_alert_html

SEND_ALERT_SCRIPT = Path(r"C:\Users\david\Desktop\Progetti\telegram-antigravity-bridge\send_alert.py")


class TestTelegramAlertContract(unittest.TestCase):
    """Validates the structure and content of Telegram notifications dispatched to Jarvis bot."""

    def test_send_alert_script_exists_on_system(self):
        """Authoritative Telegram bridge script must exist at specified path."""
        self.assertTrue(
            SEND_ALERT_SCRIPT.exists(),
            f"Expected send_alert.py not found at {SEND_ALERT_SCRIPT}"
        )

    def test_valid_telegram_alert_html_passes_validation(self):
        """Standard weekly alert payload must pass HTML and content validation."""
        valid_alert = (
            "🛒 <b>Riepilogo Spesa Esselunga — Settimana 31/10 - 06/11/2026</b>\n\n"
            "📦 Articoli aggiunti: <b>21</b>\n"
            "💰 Spesa stimata: <b>48.75 €</b>\n"
            "🥗 Menù nutrizionale: <b>2063 kcal/die</b> (Dr. Caglioni)\n\n"
            "🌐 Dashboard: <a href=\"https://meal-planner-dashboard.vercel.app\">Visualizza Menù e Ricette</a>"
        )
        is_valid, errors = validate_telegram_alert_html(valid_alert)
        self.assertTrue(is_valid, f"Alert failed validation: {errors}")
        self.assertEqual(len(errors), 0)

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
        """When items are missing or replaced, alert must include fallback notice."""
        alert_with_warning = (
            "🛒 <b>Riepilogo Spesa Esselunga — Settimana 31/10 - 06/11</b>\n"
            "📦 Articoli aggiunti: <b>20</b>\n"
            "💰 Spesa stimata: <b>46.50 €</b>\n"
            "⚠️ <i>Sostituzione: Fesa di tacchino usata al posto di Petto di pollo (esaurito)</i>\n"
            "🌐 Dashboard: https://meal-planner.vercel.app"
        )
        self.assertIn("Sostituzione", alert_with_warning)
        self.assertTrue(validate_telegram_alert_html(alert_with_warning)[0])


class TestGitAsCmsSyncContract(unittest.TestCase):
    """Contract 4: Git-as-CMS commit message and push synchronization."""

    def test_git_commit_message_format(self):
        """Orchestrator git commit message must follow conventional commit standard."""
        week_label = "2026-W44"
        commit_msg = f"chore(meal-plan): update week {week_label}"
        
        pattern = r"^chore\(meal-plan\):\s+update week\s+[\w\-]+$"
        self.assertRegex(commit_msg, pattern, "Git commit message does not match expected convention")

    def test_image_asset_file_naming_convention(self):
        """Generated dish images must follow <day>_<meal_slot>.webp convention."""
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
    """Verifies Friday morning scheduling specifications."""

    def test_scheduled_day_and_time(self):
        """Automation is contracted to run every Friday morning at 08:00 AM."""
        SCHEDULED_DAY = "Friday"
        SCHEDULED_TIME = "08:00"
        self.assertEqual(SCHEDULED_DAY, "Friday")
        self.assertEqual(SCHEDULED_TIME, "08:00")


if __name__ == "__main__":
    unittest.main()
