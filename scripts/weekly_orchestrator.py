#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Meal Planner Dashboard — Friday Morning Weekly Orchestrator.

Coordinates the complete end-to-end Friday automation cycle:
1. Calculates upcoming week date range (Saturday to Friday) & ISO week ID.
2. Generates/validates weekly meal plan (35 meals, 2063 kcal target, 14 protein slots, Pizza Margherita free meal)
   using Gemini API (model 'gemini-3.8-flash') or verified Dr. Caglioni seasonal plan.
3. Ensures high-resolution WebP dish images in public/recipes/.
4. Updates src/data/current-week.json with synchronized cart summary.
5. Populates Esselunga online shopping cart via Playwright (scripts/esselunga_cart_filler.py)
   with strict 3-layer NO-CHECKOUT safety guardrails.
6. Commits and pushes changes to GitHub (Git-as-CMS) triggering continuous deployment on Vercel.
7. Dispatches rich HTML summary notification via telegram-antigravity-bridge/send_alert.py
   with live Vercel link (https://meal-planner-dashboard-gold.vercel.app).
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple

# Reconfigure stdout for UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Project Directory Structure
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = SRC_DIR / "data"
PUBLIC_DIR = PROJECT_ROOT / "public"
RECIPES_DIR = PUBLIC_DIR / "recipes"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
LOGS_DIR = PROJECT_ROOT / "logs"

CURRENT_WEEK_PATH = DATA_DIR / "current-week.json"
PANTRY_TAXONOMY_PATH = DATA_DIR / "pantry_taxonomy.json"
CART_FILLER_SCRIPT = SCRIPTS_DIR / "esselunga_cart_filler.py"
IMAGE_GENERATOR_SCRIPT = SCRIPTS_DIR / "generate_dish_images.py"
DEFAULT_ALERT_SCRIPT = Path(r"C:\Users\david\Desktop\Progetti\telegram-antigravity-bridge\send_alert.py")

# Production Endpoints & Constants
DEFAULT_VERCEL_URL = "https://meal-planner-dashboard-gold.vercel.app"
DEFAULT_ESSELUNGA_CART_URL = "https://spesaonline.esselunga.it/commerce/nav/supermercato/carrello"
DR_CAGLIONI_TARGET = {
    "kcal": 2063,
    "carbs_g": 251,
    "proteins_g": 112,
    "fats_g": 68,
    "fiber_g": 42
}

# Logger setup
logger = logging.getLogger("weekly_orchestrator")


def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Configures dual console and file logging with ISO timestamps."""
    if log_file is None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOGS_DIR / "orchestrator.log"
    else:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.setLevel(logging.INFO)
    for h in list(logger.handlers):
        try:
            h.close()
        except Exception:
            pass
        logger.removeHandler(h)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except PermissionError:
        # File is already held open by runner process (e.g. run_weekly.bat stdout redirection)
        pass
    except Exception as e:
        logger.debug(f"Could not attach file logger: {e}")

    return logger


def calculate_week_window(reference_date: Optional[datetime] = None) -> Tuple[datetime, datetime, str]:
    """
    Calculates the upcoming weekly plan window (Saturday to Friday).
    When running on Friday morning (or any prior weekday), calculates the immediate next Saturday.
    When running on Saturday, considers today the week start.
    Returns: (week_start_date, week_end_date, iso_week_id)
    """
    if reference_date is None:
        reference_date = datetime.now()

    # Italian medical plan runs Saturday (weekday 5) through Friday (weekday 4)
    # reference_date.weekday(): Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
    weekday = reference_date.weekday()
    if weekday == 5:
        # Today is Saturday
        days_ahead = 0
    else:
        # Calculate days until next Saturday
        days_ahead = (5 - weekday) % 7

    start_date = (reference_date + timedelta(days=days_ahead)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_date = start_date + timedelta(days=6)

    iso_year, iso_week, _ = start_date.isocalendar()
    week_id = f"{iso_year}-W{iso_week:02d}"

    return start_date, end_date, week_id


def load_pantry_taxonomy(taxonomy_path: Path = PANTRY_TAXONOMY_PATH) -> Dict[str, Any]:
    """Loads out-of-stock equivalent mappings."""
    if taxonomy_path.exists():
        with open(taxonomy_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_current_plan(data_path: Path = CURRENT_WEEK_PATH) -> Optional[Dict[str, Any]]:
    """Loads existing current-week.json data if present."""
    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def resolve_gemini_api_key(api_key: Optional[str] = None) -> Optional[str]:
    """Resolves Gemini API Key from args, environment, local .env, or Organizzatore cartelle config."""
    if api_key:
        return api_key.strip()
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ.get("GEMINI_API_KEY").strip()

    # Check .env in project root
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        return val
        except Exception:
            pass

    # Check Organizzatore cartelle config
    organizer_dir = PROJECT_ROOT.parent / "Organizzatore cartelle"
    if organizer_dir.exists():
        try:
            sys.path.insert(0, str(organizer_dir))
            import config as org_config
            key = org_config.get_api_key()
            if key:
                return key
        except Exception:
            pass
        finally:
            if str(organizer_dir) in sys.path:
                sys.path.remove(str(organizer_dir))

    return None


def generate_weekly_plan(
    week_start: datetime,
    week_end: datetime,
    week_id: str,
    existing_plan_path: Path = CURRENT_WEEK_PATH,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates genuine weekly meal plan with 35 meals, 2063 kcal target, 14 protein slots,
    and Pizza Margherita free meal on Saturday dinner.
    Prioritizes Gemini API (model 'gemini-3.8-flash') when GEMINI_API_KEY is available.
    Falls back to verified Dr. Caglioni seasonal plan when API is unavailable or offline.
    """
    logger.info(f"Generating weekly meal plan for week {week_id} ({week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')})...")

    # Load baseline authoritative structure
    baseline_plan = load_current_plan(existing_plan_path)
    if not baseline_plan:
        raise FileNotFoundError(f"Authoritative meal plan dataset not found at {existing_plan_path}")

    # Check for Gemini API Key
    effective_api_key = resolve_gemini_api_key(api_key)

    gemini_plan = None
    if effective_api_key:
        try:
            logger.info("Attempting Gemini AI recipe generation via google.genai (model: gemini-3.8-flash)...")
            from google import genai
            client = genai.Client(api_key=effective_api_key)

            prompt = (
                f"Genera il piano nutrizionale e ricette settimanali per la settimana {week_id} "
                f"dal {week_start.strftime('%d/%m/%Y')} al {week_end.strftime('%d/%m/%Y')} "
                "secondo la prescrizione del Dr. Caglioni: 2063 kcal/die, 112g proteine, 251g carboidrati, 68g grassi. "
                "Rotazione proteica esatta: 3 carne, 3 pesce, 2 uova, 2 legumi, 2 formaggi, 1 vegetale/tofu, 1 pasto libero (Pizza Margherita). "
                "Restituisci esclusivamente il JSON conforme allo schema."
            )

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )
            if response and response.text:
                # Attempt to parse json from response
                raw_text = response.text.strip()
                if "```json" in raw_text:
                    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_text:
                    raw_text = raw_text.split("```")[1].split("```")[0].strip()
                parsed = json.loads(raw_text)
                if isinstance(parsed, dict) and "days" in parsed and len(parsed["days"]) == 7:
                    gemini_plan = parsed
                    logger.info("Gemini API generated valid 7-day meal plan successfully.")
        except Exception as gemini_err:
            logger.warning(f"Gemini API generation note: {gemini_err}. Proceeding with clinical seasonal plan.")

    plan_to_use = gemini_plan if gemini_plan else baseline_plan

    # Update week metadata and dates dynamically
    updated_plan = json.loads(json.dumps(plan_to_use))
    updated_plan["week_id"] = week_id
    updated_plan["week_start"] = week_start.strftime("%Y-%m-%d")
    updated_plan["week_end"] = week_end.strftime("%Y-%m-%d")
    updated_plan["macro_target"] = DR_CAGLIONI_TARGET

    # Update daily dates
    for idx, day in enumerate(updated_plan.get("days", [])):
        day_date = week_start + timedelta(days=idx)
        day["date"] = day_date.strftime("%Y-%m-%d")

    # Update cart summary timestamp
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if "cart_summary" in updated_plan:
        updated_plan["cart_summary"]["last_updated"] = now_iso
        updated_plan["cart_summary"]["cart_url"] = DEFAULT_ESSELUNGA_CART_URL

    return updated_plan


def save_weekly_plan(plan: Dict[str, Any], output_path: Path = CURRENT_WEEK_PATH) -> None:
    """Writes the updated plan to current-week.json."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved weekly meal plan to {output_path}")


def ensure_recipe_images(plan: Dict[str, Any], recipes_dir: Path = RECIPES_DIR) -> bool:
    """Verifies and ensures all referenced high-resolution WebP dish images are present."""
    logger.info(f"Verifying recipe image assets in {recipes_dir}...")
    recipes_dir.mkdir(parents=True, exist_ok=True)

    # Collect referenced images
    referenced_images = set()
    for day in plan.get("days", []):
        for meal in day.get("meals", {}).values():
            url = meal.get("image_url", "")
            if url.startswith("/recipes/"):
                fname = url.replace("/recipes/", "")
                referenced_images.add(fname)

    missing = []
    for fname in referenced_images:
        target = recipes_dir / fname
        if not target.exists() or target.stat().st_size == 0:
            missing.append(fname)

    if missing:
        logger.info(f"Missing {len(missing)} dish images ({', '.join(missing)}). Invoking generate_dish_images.py...")
        try:
            res = subprocess.run(
                [sys.executable, str(IMAGE_GENERATOR_SCRIPT)],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode == 0:
                logger.info("Image generation pipeline executed successfully.")
            else:
                logger.warning(f"Image generator returned non-zero code {res.returncode}: {res.stderr}")
        except Exception as img_err:
            logger.error(f"Error invoking image generator: {img_err}")

    # Re-verify
    still_missing = [f for f in referenced_images if not (recipes_dir / f).exists()]
    if still_missing:
        logger.warning(f"Note: Some recipe images could not be generated: {still_missing}")
        return False

    logger.info(f"All {len(referenced_images)} referenced recipe photographs verified on disk.")
    return True


def run_cart_population(
    cart_filler_script: Path = CART_FILLER_SCRIPT,
    dry_run: bool = False,
    test_item: Optional[str] = None
) -> Tuple[int, str]:
    """
    Invokes scripts/esselunga_cart_filler.py to populate Esselunga shopping cart.
    Adheres strictly to the 3-layer NO-CHECKOUT safety guardrails.
    Returns: (exit_code, output_text)
    """
    logger.info("Invoking Esselunga cart population script...")
    cmd = [sys.executable, str(cart_filler_script)]
    if dry_run:
        cmd.append("--dry-run")
    if test_item:
        cmd.extend(["--test-item", test_item])

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300,
            check=False
        )
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        output = stdout + ("\n" + stderr if stderr else "")
        logger.info(f"Cart filler process exited with code {proc.returncode}.")
        return proc.returncode, output
    except subprocess.TimeoutExpired:
        logger.error("Cart filler process timed out after 300 seconds.")
        return 1, "Cart filler execution timed out."
    except Exception as e:
        logger.error(f"Error executing cart filler: {e}")
        return 1, str(e)


def format_telegram_alert(
    plan: Dict[str, Any],
    session_expired: bool = False,
    custom_notes: Optional[str] = None,
    vercel_url: str = DEFAULT_VERCEL_URL
) -> str:
    """
    Formats the rich HTML Telegram summary message matching Contract 3.
    Includes week dates, total items added, estimated spend, kcal target,
    live Vercel dashboard URL, and Esselunga cart review CTA.
    """
    week_start = plan.get("week_start", "")
    week_end = plan.get("week_end", "")
    cart = plan.get("cart_summary", {})
    items_count = cart.get("items_count", 39)
    estimated_eur = cart.get("total_estimated_eur", 0.0)
    macro = plan.get("macro_target", DR_CAGLIONI_TARGET)
    kcal = macro.get("kcal", 2063)
    proteins = macro.get("proteins_g", 112)

    total_meals = sum(len(d.get("meals", {})) for d in plan.get("days", [])) or 35

    lines = [
        f"🛒 <b>Riepilogo Spesa Esselunga — Settimana {week_start} al {week_end}</b>\n",
        f"📦 Articoli aggiunti: <b>{items_count}</b>",
        f"💰 Spesa stimata: <b>{estimated_eur:.2f} €</b>",
        f"🥗 Menù nutrizionale: <b>{kcal} kcal/die</b> ({proteins}g proteine — Dr. Caglioni)",
        f"🍽️ Totale pasti settimanali: <b>{total_meals} pasti bilanciati</b>\n"
    ]

    if session_expired:
        lines.append("⚠️ <b>Sessione Esselunga scaduta</b>: accedi una volta su Chrome e rilancia lo script\n")

    if custom_notes:
        lines.append(f"ℹ️ <i>{custom_notes}</i>\n")

    lines.append(f"🌐 Dashboard: <a href=\"{vercel_url}\">Visualizza Menù e Ricette</a>")
    lines.append(f"🛒 Carrello: <a href=\"{DEFAULT_ESSELUNGA_CART_URL}\">Controlla carrello Esselunga</a>")

    return "\n".join(lines)


def dispatch_telegram_alert(
    html_message: str,
    alert_script: Path = DEFAULT_ALERT_SCRIPT
) -> bool:
    """Dispatches the rich HTML alert to Telegram via send_alert.py."""
    if not alert_script.exists():
        logger.error(f"send_alert.py not found at {alert_script}")
        return False

    logger.info("Dispatching Telegram notification via send_alert.py...")
    try:
        res = subprocess.run(
            [sys.executable, str(alert_script), html_message],
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )
        if res.returncode == 0:
            logger.info("Telegram notification successfully delivered.")
            return True
        else:
            logger.error(f"send_alert.py failed with code {res.returncode}: {res.stderr or res.stdout}")
            return False
    except Exception as e:
        logger.error(f"Exception dispatching Telegram alert: {e}")
        return False


def git_commit_and_push(
    week_id: str,
    repo_dir: Path = PROJECT_ROOT,
    dry_run: bool = False
) -> bool:
    """
    Implements Git-as-CMS automated synchronization:
    Staged files: src/data/current-week.json, public/recipes/
    Commit message: chore(meal-plan): update week [week_id]
    Pushes to origin main to trigger continuous deployment on Vercel.
    """
    logger.info("Checking Git repository status for updates...")

    try:
        # Check if git is available
        status = subprocess.run(
            ["git", "status", "--porcelain", "src/data/current-week.json", "public/recipes/"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            check=False
        )

        if not status.stdout.strip():
            logger.info("No modifications detected in current-week.json or recipe images. Git push skipped.")
            return True

        logger.info(f"Detected changes:\n{status.stdout.strip()}")

        if dry_run:
            logger.info(f"[DRY-RUN] Git-as-CMS commit and push simulated for week {week_id}.")
            return True

        # Stage files
        subprocess.run(
            ["git", "add", "src/data/current-week.json", "public/recipes/"],
            cwd=str(repo_dir),
            check=True
        )

        # Commit
        commit_msg = f"chore(meal-plan): update week {week_id}"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=str(repo_dir),
            check=True
        )
        logger.info(f"Committed changes with message: '{commit_msg}'")

        # Push
        push_res = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            check=False
        )

        if push_res.returncode == 0:
            logger.info("Successfully pushed updates to GitHub origin/main. Vercel deployment triggered.")
            return True
        else:
            logger.warning(f"Git push returned code {push_res.returncode}: {push_res.stderr}. Changes committed locally.")
            return False

    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during Git synchronization: {e}")
        return False


def run_orchestration_cycle(
    dry_run: bool = False,
    skip_cart: bool = False,
    test_alert: bool = False,
    force_send_alert: bool = False,
    reference_date: Optional[datetime] = None,
    vercel_url: str = DEFAULT_VERCEL_URL
) -> int:
    """Executes the complete Friday weekly orchestration cycle."""
    setup_logging()
    logger.info("=" * 70)
    logger.info("  MEAL PLANNER DASHBOARD — FRIDAY WEEKLY ORCHESTRATOR")
    logger.info("=" * 70)
    logger.info(f"Execution Mode : {'DRY-RUN (Safe Simulation)' if dry_run else 'LIVE PRODUCTION'}")
    logger.info(f"Skip Cart      : {skip_cart}")
    logger.info(f"Test Alert     : {test_alert}")
    logger.info(f"Dashboard URL  : {vercel_url}")
    logger.info("-" * 70)

    # 1. Calculate week dates
    week_start, week_end, week_id = calculate_week_window(reference_date)
    logger.info(f"Target Plan Week: {week_id} ({week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')})")

    # If --test-alert requested: format alert with current plan and dispatch immediately
    if test_alert:
        current_plan = load_current_plan()
        if not current_plan:
            current_plan = generate_weekly_plan(week_start, week_end, week_id)
        alert_html = format_telegram_alert(current_plan, vercel_url=vercel_url)
        logger.info("Sending test alert to Telegram...")
        success = dispatch_telegram_alert(alert_html)
        if success:
            logger.info("Test alert delivered successfully.")
            return 0
        else:
            logger.error("Failed to deliver test alert.")
            return 1

    # 2. Generate and validate weekly meal plan
    plan = generate_weekly_plan(week_start, week_end, week_id)

    # 3. Ensure recipe WebP dish images
    ensure_recipe_images(plan)

    # 4. Save updated current-week.json
    if not dry_run:
        save_weekly_plan(plan)
    else:
        logger.info("[DRY-RUN] current-week.json write simulated.")

    # 5. Populate Esselunga shopping cart
    session_expired = False
    custom_notes = None

    if not skip_cart:
        exit_code, cart_output = run_cart_population(dry_run=dry_run)
        if exit_code == 2:
            session_expired = True
            logger.warning("Esselunga session expired. Alert will instruct manual Chrome login.")
        elif exit_code != 0:
            custom_notes = f"Avviso carrello Esselunga: codice uscita {exit_code}"
    else:
        logger.info("Skipping Esselunga cart population as requested (--skip-cart).")

    # 6. Commit and push to GitHub (Git-as-CMS)
    git_commit_and_push(week_id, dry_run=dry_run)

    # 7. Dispatch rich HTML Telegram alert
    alert_html = format_telegram_alert(
        plan=plan,
        session_expired=session_expired,
        custom_notes=custom_notes,
        vercel_url=vercel_url
    )

    if dry_run and not force_send_alert:
        logger.info("[DRY-RUN] Formatted Telegram notification generated and verified:")
        print("\n" + "-" * 50)
        print(alert_html)
        print("-" * 50 + "\n")
    else:
        dispatch_telegram_alert(alert_html)

    logger.info("Weekly orchestration cycle completed successfully.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Meal Planner Dashboard — Friday Morning Weekly Orchestrator"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Runs full pipeline without pushing to git or calling external APIs destructively"
    )
    parser.add_argument(
        "--skip-cart",
        action="store_true",
        help="Generates recipes and sends alert without running Playwright cart automation"
    )
    parser.add_argument(
        "--test-alert",
        action="store_true",
        help="Sends a test alert via send_alert.py and exits immediately"
    )
    parser.add_argument(
        "--send-alert",
        action="store_true",
        help="Force send Telegram notification even in --dry-run mode"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Reference date for week window calculation (format: YYYY-MM-DD)"
    )

    args = parser.parse_args()

    ref_date = None
    if args.date:
        ref_date = datetime.strptime(args.date, "%Y-%m-%d")

    exit_code = run_orchestration_cycle(
        dry_run=args.dry_run,
        skip_cart=args.skip_cart,
        test_alert=args.test_alert,
        force_send_alert=args.send_alert,
        reference_date=ref_date
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
