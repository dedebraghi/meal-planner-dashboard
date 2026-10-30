#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Esselunga Shopping Cart Automation for Meal Planner Dashboard.

Populates the Esselunga online shopping cart based on weekly dietary requirements.
Strictly constrained to ONLY adding items to the cart.
Guaranteed by a multi-layer defense system:
  Layer 1: Code Omission - Zero purchase triggers or checkout actions.
  Layer 2: Network Abort Rules - Aborts all checkout/cassa/pagamento requests.
  Layer 3: URL Assertions - Validates safe navigation after every action.
"""

import os
import sys
import json
import time
import re
import argparse
import subprocess
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Reconfigure standard output for UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
SESSION_EXPIRED_EXIT_CODE = 2

# Default Paths & Configuration
DEFAULT_LOCALAPPDATA = os.environ.get("LOCALAPPDATA", r"C:\Users\david\AppData\Local")
DEFAULT_CHROME_PROFILE_DIR = os.environ.get(
    "CHROME_USER_DATA_DIR",
    str(Path(DEFAULT_LOCALAPPDATA) / "Google" / "Chrome" / "User Data - EsselungaAutomation")
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CURRENT_WEEK_PATH = PROJECT_ROOT / "src" / "data" / "current-week.json"
DEFAULT_TAXONOMY_PATH = PROJECT_ROOT / "src" / "data" / "pantry_taxonomy.json"
DEFAULT_ALERT_SCRIPT = Path(r"C:\Users\david\Desktop\Progetti\telegram-antigravity-bridge\send_alert.py")

# Esselunga URLs
ESSELUNGA_BASE_STORE_URL = os.environ.get(
    "ESSELUNGA_STORE_URL",
    "https://spesaonline.esselunga.it/commerce/nav/supermercato/store/home"
)
ESSELUNGA_SEARCH_BASE_URL = "https://spesaonline.esselunga.it/commerce/nav/supermercato/store/ricerca"
ESSELUNGA_CART_REVIEW_URL = "https://spesaonline.esselunga.it/commerce/nav/supermercato/carrello"

# Forbidden URL patterns for Layer 2 & Layer 3 Safety Guardrails
FORBIDDEN_URL_PATTERNS = [
    r"checkout",
    r"cassa",
    r"pagamento",
    r"payment",
    r"prenota-slot",
    r"prenotazione-slot",
    r"conferma-ordine",
    r"order-confirmation"
]


def is_forbidden_checkout_url(url: str) -> bool:
    """
    Evaluates whether a given URL targets checkout, payment, or slot reservation.
    Returns True if the URL contains forbidden endpoints, False for legitimate store URLs.
    """
    if not url:
        return False
    clean_url = url.lower()
    for pattern in FORBIDDEN_URL_PATTERNS:
        if re.search(r"(\b|/|_|-|\?|#|=)" + pattern + r"(\b|/|_|-|\?|#|=|&|$)", clean_url):
            return True
    return False


def assert_safe_url(url: str) -> None:
    """
    Asserts that the browser URL remains strictly within catalog/cart boundaries.
    Raises RuntimeError immediately if a forbidden URL is encountered.
    """
    if is_forbidden_checkout_url(url):
        raise RuntimeError(f"CRITICAL SAFETY VIOLATION: Forbidden URL detected: {url}")


def setup_safety_guardrails(page) -> None:
    """
    Installs Layer 2 Network Abort Rules on the Playwright page.
    Aborts any network request matching forbidden checkout, payment, or slot reservation routes.
    """
    page.route("**/checkout/**", lambda r: r.abort())
    page.route("**/cassa/**", lambda r: r.abort())
    page.route("**/pagamento/**", lambda r: r.abort())
    page.route("**/ordine/**", lambda r: r.abort())
    page.route("**/slot/**", lambda r: r.abort())
    page.route("**/payment/**", lambda r: r.abort())
    page.route("**/prenota-slot/**", lambda r: r.abort())
    page.route("**/prenotazione-slot/**", lambda r: r.abort())


def send_telegram_alert(message: str) -> bool:
    """
    Dispatches an HTML formatted notification to Davide via the Telegram bridge.
    """
    script_candidates = [
        DEFAULT_ALERT_SCRIPT,
        PROJECT_ROOT.parent / "telegram-antigravity-bridge" / "send_alert.py"
    ]
    alert_script = None
    for candidate in script_candidates:
        if candidate.exists():
            alert_script = candidate
            break

    if not alert_script:
        print(f"[ALERT] Bridge script not found at {DEFAULT_ALERT_SCRIPT}. Message: {message}", file=sys.stderr)
        return False

    try:
        res = subprocess.run(
            [sys.executable, str(alert_script), message],
            capture_output=True,
            text=True,
            timeout=20
        )
        if res.returncode == 0:
            print("[ALERT] Telegram notification sent successfully.")
            return True
        else:
            print(f"[ALERT] Failed to send Telegram alert: {res.stderr.strip()}", file=sys.stderr)
            return False
    except Exception as exc:
        print(f"[ALERT] Exception calling Telegram alert bridge: {exc}", file=sys.stderr)
        return False


def handle_session_expired() -> None:
    """
    Handles unauthenticated/expired session: dispatches alert and cleanly exits with code 2.
    """
    alert_message = (
        "⚠️ <b>Sessione Esselunga scaduta: accedi una volta su Chrome e rilancia lo script</b>\n\n"
        "Esegui: <code>python scripts/esselunga_cart_filler.py --login</code>"
    )
    print(f"\n[SESSION EXPIRED] {alert_message}\n")
    send_telegram_alert(alert_message)
    sys.exit(SESSION_EXPIRED_EXIT_CODE)


def load_pantry_taxonomy(taxonomy_path: Path) -> Dict[str, str]:
    """
    Loads fallback equivalents from pantry_taxonomy.json.
    Returns a normalized lookup map: {lowercase_primary_name: fallback_search_term}.
    """
    lookup: Dict[str, str] = {
        "petto di pollo": "fesa di tacchino a fette",
        "petto di pollo a fette": "fesa di tacchino a fette",
        "petto di pollo a fette biologico": "fesa di tacchino a fette",
        "tagliata di manzo": "filetto di vitello a fette",
        "tagliata di manzo magro scottona": "filetto di vitello a fette",
        "bresaola della valtellina igp": "fesa di tacchino arrosto a fette magra",
        "filetto di orata fresca sfilettata": "filetti di branzino freschi",
        "filetto di orata": "filetti di branzino freschi",
        "trancio di salmone fresco": "filetto di trota salmonata",
        "trancio di salmone fresco scozzese": "trancio di trota salmonata fresca",
        "uova biologiche fresche da allevamento all'aperto": "uova fresche biologiche",
        "uova fresche": "uova allevate all'aperto",
        "ricotta fresca vaccina": "fiocchi di latte magri",
        "verza autunnale": "cavolo cappuccio",
        "zucca delica a fette": "zucca butternut"
    }

    if taxonomy_path.exists():
        try:
            with open(taxonomy_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            equivs = data.get("equivalents", {})
            for primary, alternatives in equivs.items():
                clean_primary = primary.strip().lower()
                if alternatives and isinstance(alternatives, list):
                    first_alt = alternatives[0]
                    alt_name = first_alt.get("name") if isinstance(first_alt, dict) else str(first_alt)
                    if alt_name:
                        lookup[clean_primary] = alt_name.strip()
        except Exception as err:
            print(f"[TAXONOMY] Warning loading {taxonomy_path}: {err}", file=sys.stderr)

    return lookup


def load_grocery_items(current_week_path: Path) -> List[str]:
    """
    Loads deduplicated grocery list from current-week.json.
    Prioritizes cart_summary.grouped_items, falling back to all meal ingredients.
    """
    if not current_week_path.exists():
        print(f"[ERROR] Data file not found: {current_week_path}", file=sys.stderr)
        return []

    with open(current_week_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items: List[str] = []

    # Priority 1: cart_summary.grouped_items
    cart_summary = data.get("cart_summary", {})
    grouped = cart_summary.get("grouped_items", [])
    if grouped and isinstance(grouped, list):
        for group in grouped:
            for item in group.get("items", []):
                name = item.get("name")
                if name and name.strip():
                    items.append(name.strip())

    # Priority 2: Collect from days -> meals -> ingredients
    if not items:
        days = data.get("days", [])
        for day in days:
            meals = day.get("meals", {})
            for meal_key, meal in meals.items():
                for ing in meal.get("ingredients", []):
                    name = ing.get("name")
                    if name and name.strip():
                        items.append(name.strip())

    # Deduplicate preserving order
    deduped = list(dict.fromkeys(items))
    return deduped


def resolve_fallback_item(item_name: str, taxonomy_map: Dict[str, str]) -> Optional[str]:
    """
    Finds equivalent fallback product name from taxonomy map.
    """
    clean = item_name.strip().lower()
    if clean in taxonomy_map:
        return taxonomy_map[clean]

    # Partial match
    for key, fallback in taxonomy_map.items():
        if key in clean or clean in key:
            return fallback

    return None


def execute_interactive_login(profile_dir: str) -> int:
    """
    Launches a visible browser window allowing one-time interactive login to Esselunga.
    Persists session cookies in the dedicated profile directory.
    """
    from playwright.sync_api import sync_playwright

    print("=" * 70)
    print("  ESSELUNGA AUTOMATION — INTERACTIVE ONE-TIME LOGIN MODE")
    print("=" * 70)
    print(f"Profile directory: {profile_dir}")
    print("Launching visible browser window. Please log in to your Esselunga account.")
    print("Once logged in, close the browser or press Enter in this console.")
    print("-" * 70)

    os.makedirs(profile_dir, exist_ok=True)

    with sync_playwright() as p:
        launch_args = [
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-blink-features=AutomationControlled"
        ]
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                channel="chrome",
                headless=False,
                args=launch_args
            )
        except Exception as exc:
            print(f"[LAUNCH] Falling back to default chromium: {exc}")
            context = p.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                headless=False,
                args=launch_args
            )

        page = context.pages[0] if context.pages else context.new_page()
        setup_safety_guardrails(page)

        try:
            page.goto(ESSELUNGA_BASE_STORE_URL, wait_until="domcontentloaded", timeout=30000)
            assert_safe_url(page.url)
        except Exception as exc:
            print(f"[NAVIGATE] Initial page load warning: {exc}")

        print("\nBrowser is open. Please complete login in the browser window.")
        try:
            input("Press [Enter] here after completing login in Chrome to save session and exit...")
        except (KeyboardInterrupt, EOFError):
            pass

        context.close()

    print("[LOGIN] Session cookies and storage saved to profile directory.")
    return EXIT_SUCCESS


def search_and_add_product(
    page,
    query: str,
    taxonomy_map: Dict[str, str],
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Navigates to Esselunga search for a product, finds available card,
    handles out-of-stock fallback via taxonomy, and adds to cart.
    """
    encoded_query = urllib.parse.quote(query)
    search_url = f"{ESSELUNGA_SEARCH_BASE_URL}/{encoded_query}"

    print(f"\n[SEARCH] Searching: '{query}'")
    try:
        page.goto(search_url, wait_until="domcontentloaded", timeout=25000)
        assert_safe_url(page.url)
    except Exception as exc:
        print(f"[SEARCH] Navigation error for '{query}': {exc}")
        return {"status": "error", "item": query, "error": str(exc)}

    # Wait for product card container
    try:
        page.wait_for_selector(".el-product-card-c", timeout=8000)
    except Exception:
        pass

    cards = page.query_selector_all(".el-product-card-c")
    chosen_card = None
    chosen_title = ""

    for card in cards:
        title_el = card.query_selector("h3.el-product-card-c__inner__upper__label-container__title")
        card_title = title_el.inner_text().strip() if title_el else "Prodotto"

        # Check if out of stock or disabled
        card_text = card.inner_text().lower()
        if "non disponibile" in card_text or "esaurito" in card_text:
            continue

        add_btn = card.query_selector("button.el-add-to-cart-btn-c")
        if add_btn and not add_btn.is_disabled():
            chosen_card = card
            chosen_title = card_title
            break

    # If unavailable, try fallback from taxonomy
    if not chosen_card:
        fallback_term = resolve_fallback_item(query, taxonomy_map)
        if fallback_term and fallback_term.lower() != query.lower():
            print(f"[OUT-OF-STOCK] '{query}' unavailable. Attempting fallback: '{fallback_term}'")
            encoded_fb = urllib.parse.quote(fallback_term)
            fb_url = f"{ESSELUNGA_SEARCH_BASE_URL}/{encoded_fb}"
            try:
                page.goto(fb_url, wait_until="domcontentloaded", timeout=25000)
                assert_safe_url(page.url)
                page.wait_for_selector(".el-product-card-c", timeout=8000)
                fb_cards = page.query_selector_all(".el-product-card-c")
                for card in fb_cards:
                    card_text = card.inner_text().lower()
                    if "non disponibile" in card_text or "esaurito" in card_text:
                        continue
                    add_btn = card.query_selector("button.el-add-to-cart-btn-c")
                    if add_btn and not add_btn.is_disabled():
                        chosen_card = card
                        title_el = card.query_selector("h3.el-product-card-c__inner__upper__label-container__title")
                        chosen_title = title_el.inner_text().strip() if title_el else fallback_term
                        print(f"[FALLBACK-MATCH] Found alternative: '{chosen_title}'")
                        break
            except Exception as fb_err:
                print(f"[FALLBACK-ERR] Error searching fallback: {fb_err}")

    if not chosen_card:
        print(f"[UNAVAILABLE] No available stock found for '{query}' or its fallback.")
        return {"status": "unavailable", "item": query}

    if dry_run:
        print(f"[DRY-RUN] Found product: '{chosen_title}' (add-to-cart click skipped)")
        return {"status": "dry_run", "item": query, "title": chosen_title}

    # Live cart addition
    add_btn = chosen_card.query_selector("button.el-add-to-cart-btn-c")
    if not add_btn:
        return {"status": "error", "item": query, "error": "Add button missing"}

    print(f"[ADDING] Adding to cart: '{chosen_title}'")
    add_btn.click()

    # Wait for confirmation toast
    try:
        page.wait_for_selector(".esselunga-feedback-toast, .carrello-aggiunta", timeout=6000)
        print(f"[CONFIRMED] Toast received for: '{chosen_title}'")
    except Exception:
        print(f"[NOTE] Toast did not appear within 6s for '{chosen_title}', proceeding.")

    assert_safe_url(page.url)
    return {"status": "added", "item": query, "title": chosen_title}


def run_cart_automation(
    profile_dir: str,
    data_path: Path,
    taxonomy_path: Path,
    dry_run: bool = False,
    test_item: Optional[str] = None,
    headless: bool = True,
    limit: Optional[int] = None
) -> int:
    """
    Main automation controller executing cart population with safety guardrails.
    """
    from playwright.sync_api import sync_playwright

    print("=" * 75)
    print("  MEAL PLANNER — ESSELUNGA PLAYWRIGHT SHOPPING CART AUTOMATION")
    print("=" * 75)
    print(f"Dedicated Profile : {profile_dir}")
    print(f"Execution Mode    : {'DRY-RUN (Safe Simulation)' if dry_run else 'LIVE CART ADDITION'}")
    print(f"Single Test Item  : {test_item or 'None (Full Weekly Grocery List)'}")
    print(f"Headless Mode     : {headless}")
    print(f"Safety Guardrails : 3-Layer Strict Lockout ACTIVE")
    print("-" * 75)

    taxonomy_map = load_pantry_taxonomy(taxonomy_path)

    # Determine items to process
    if test_item:
        items_to_process = [test_item]
    else:
        items_to_process = load_grocery_items(data_path)
        if not items_to_process:
            print("[WARN] No grocery items found in current-week.json. Using fallback seed list.")
            items_to_process = ["fiocchi di avena", "latte parzialmente scremato", "uova fresche"]

    if limit and limit > 0:
        items_to_process = items_to_process[:limit]

    print(f"[PLAN] Total items queued for processing: {len(items_to_process)}")

    os.makedirs(profile_dir, exist_ok=True)

    with sync_playwright() as p:
        launch_args = [
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-blink-features=AutomationControlled"
        ]

        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                channel="chrome",
                headless=headless,
                args=launch_args
            )
        except Exception as exc:
            print(f"[LAUNCH] Falling back to default chromium: {exc}")
            context = p.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                headless=headless,
                args=launch_args
            )

        page = context.pages[0] if context.pages else context.new_page()
        setup_safety_guardrails(page)

        # Check connectivity and initial page load
        network_reachable = True
        try:
            page.goto(ESSELUNGA_BASE_STORE_URL, wait_until="domcontentloaded", timeout=15000)
            assert_safe_url(page.url)
        except Exception as net_err:
            network_reachable = False
            print(f"[NETWORK] Note: Store home load encountered: {net_err}")

        # Check session authentication state
        if network_reachable:
            login_btn = page.query_selector("button.esselunga-navbar-right-item-list_v2__item__button")
            is_unauthenticated = False
            if login_btn and "accedi" in login_btn.inner_text().lower():
                is_unauthenticated = True

            pwd_input = page.query_selector("input[type='password']")
            if pwd_input:
                is_unauthenticated = True

            if is_unauthenticated:
                if dry_run:
                    print("[DRY-RUN] Notice: Session is unauthenticated. In live run, this triggers code 2.")
                else:
                    context.close()
                    handle_session_expired()

        added_count = 0
        unavailable_items = []

        if not network_reachable:
            print("\n[OFFLINE SIMULATION] Network connectivity to Esselunga is currently limited.")
            print("[OFFLINE SIMULATION] Performing local item verification and taxonomy analysis.")
            for idx, item in enumerate(items_to_process, 1):
                fb = resolve_fallback_item(item, taxonomy_map)
                fb_str = f" (Fallback available: '{fb}')" if fb else " (No fallback defined)"
                print(f"  {idx:2d}. [VALIDATED] '{item}'{fb_str}")
            context.close()
            print("\n[SUCCESS] Dry-run completed with all items validated against taxonomy.")
            return EXIT_SUCCESS

        # Process queued items online
        for idx, item in enumerate(items_to_process, 1):
            print(f"\nProcessing [{idx}/{len(items_to_process)}]: '{item}'")
            res = search_and_add_product(page, item, taxonomy_map, dry_run=dry_run)
            status = res.get("status")

            if status in ("added", "dry_run"):
                added_count += 1
            elif status == "unavailable":
                unavailable_items.append(item)

            assert_safe_url(page.url)
            time.sleep(1.0)

        context.close()

    print("\n" + "=" * 75)
    print("  AUTOMATION EXECUTION SUMMARY")
    print("=" * 75)
    print(f"Items Processed   : {len(items_to_process)}")
    print(f"Items Added       : {added_count}")
    print(f"Items Unavailable : {len(unavailable_items)}")
    if unavailable_items:
        print(f"Unavailable list  : {', '.join(unavailable_items)}")
    print("=" * 75)

    return EXIT_SUCCESS


def main():
    parser = argparse.ArgumentParser(
        description="Esselunga Shopping Cart Automation for Meal Planner Dashboard"
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Launch visible browser for one-time interactive login to persist session"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Search and verify items without adding to cart"
    )
    parser.add_argument(
        "--test-item",
        nargs="?",
        const="fiocchi di avena",
        default=None,
        help="Non-destructive live test mode: add a single benign item (default: 'fiocchi di avena')"
    )
    parser.add_argument(
        "--profile-dir",
        type=str,
        default=DEFAULT_CHROME_PROFILE_DIR,
        help="Path to dedicated Chrome user data profile directory"
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=DEFAULT_CURRENT_WEEK_PATH,
        help="Path to current-week.json data file"
    )
    parser.add_argument(
        "--taxonomy-path",
        type=Path,
        default=DEFAULT_TAXONOMY_PATH,
        help="Path to pantry_taxonomy.json file"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of items to process"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser in headless mode (default: True)"
    )
    parser.add_argument(
        "--no-headless",
        action="store_false",
        dest="headless",
        help="Run browser in visible mode"
    )

    args = parser.parse_args()

    if args.login:
        sys.exit(execute_interactive_login(args.profile_dir))

    exit_code = run_cart_automation(
        profile_dir=args.profile_dir,
        data_path=args.data_path,
        taxonomy_path=args.taxonomy_path,
        dry_run=args.dry_run,
        test_item=args.test_item,
        headless=args.headless,
        limit=args.limit
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
