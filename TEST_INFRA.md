# Testing Infrastructure & E2E Test Suite Specification

## 1. Executive Summary & Testing Philosophy

This test suite provides comprehensive, requirement-driven, opaque-box E2E validation for the **Meal Planner Dashboard & Esselunga Automation** system.

Following strict Dual-Track E2E testing principles:
- **Requirement-Driven**: Tests are derived directly from the authoritative specifications in `ORIGINAL_REQUEST.md`, `SPEC.md`, `PROJECT.md`, and Dr. Caglioni's nutritional plan (`Schema nutrizionale Braghiroli Davide.pdf`).
- **Opaque-Box**: Tests treat the implementation as an external system, testing behavior, data contracts, security invariants, and user workflows rather than internal implementation details.
- **Progressive Testability**: All tests are self-contained, independent, deterministic, and runnable without third-party pip dependencies via Python's built-in `unittest` runner.
- **Authoritative Oracles**: Expected outputs are derived from medical nutritional specifications, exact bromatological formulas, Telegram bot contracts, and strict security safety invariants.

---

## 2. The 4-Tier Testing Architecture

```
                    ┌────────────────────────────────────────┐
                    │    Tier 4: Real-World Scenarios        │
                    │   (Weekly Cycle, NO-CHECKOUT, Alert)   │
                    ├────────────────────────────────────────┤
                    │   Tier 3: Cross-Feature Interactions   │
                    │ (Cart vs Recipes, Macro Sums, Git-CMS) │
                    ├────────────────────────────────────────┤
                    │    Tier 2: Boundary & Corner Cases     │
                    │(Out-of-Stock, Non-ASCII, Negative Qty) │
                    ├────────────────────────────────────────┤
                    │      Tier 1: Feature Coverage          │
                    │ (20 Features in Isolation, >=5/feature)│
                    └────────────────────────────────────────┘
```

### Tier 1: Feature Coverage (Isolated Functional Verification)
Verifies each feature independently to ensure functional correctness:
- **F1 (7-Day Grid)**: 7 distinct days, correct date progression (`2026-10-31` to `2026-11-06`), weekday ordering.
- **F2 (5-Meal Breakdown)**: Exactly 5 meal slots per day (`colazione`, `pranzo`, `spuntino_pomeriggio`, `cena`, `dopocena`).
- **F3 (Recipe Drawer)**: Ingredients list with quantities, step-by-step instructions, prep/cook time, nutritionist tips.
- **F4 (Dish Imagery)**: WebP image paths, aspect ratio compliance, culinary fallback placeholder handling.
- **F5 (Macro Bar)**: Target calories (2063 kcal), proteins (112g), carbs (251g), fats (68g), daily percentages.
- **F6 (Cart Status Badge)**: Total estimated spend (€), total item count, direct Esselunga cart link.
- **F7 (Free Meal Badge)**: Saturday dinner "Pasto Libero" (Pizza Margherita) flag and nutrition inclusion.
- **F8 (Git-as-CMS Data)**: Single source of truth in `src/data/current-week.json` validated against TypeScript interface.
- **F9 (Seed Data Week)**: Initial 35 meals matching late autumn seasonal produce (zucca, verza, finocchi, etc.).
- **F10 (Chrome Profile Connection)**: Windows persistent profile configuration (`%LOCALAPPDATA%\Google\Chrome\User Data`).
- **F11 (Cart Population)**: Search query generation, ingredient aggregation, and item deduplication.
- **F12 (Strict Checkout Lockout)**: Multi-layer guardrail prohibiting any checkout, slot selection, or payment action.
- **F13 (Out-of-Stock Fallback)**: Deterministic replacement from same nutritional category (pantry taxonomy).
- **F14 (Session Expiry Alert)**: Clean exit with code 2 and Telegram notification on auth failure without brute force.
- **F15 (Non-Destructive Test Mode)**: Support for `--test-item` CLI flag adding a benign product.
- **F16 (Weekly Recipe Generation)**: Dietary guidelines adherence and 35-meal generation via Gemini prompt rules.
- **F17 (Dish Photography Generation)**: Editorial visual style requirements (ceramic tableware, natural lighting).
- **F18 (Telegram Dispatch Bridge)**: Formatted HTML summary via `telegram-antigravity-bridge\send_alert.py`.
- **F19 (Automated Git Push Sync)**: Conventional commit formatting (`chore(meal-plan): update week [date]`).
- **F20 (Windows Task Scheduler Runner)**: Execution script structure for Friday morning 08:00 automated run.

### Tier 2: Boundary & Corner Cases (Robustness & Error Handling)
Stresses system boundaries and unexpected inputs:
- **Out-of-Stock Scenarios**: Primary item unavailable, secondary fallback item unavailable, handling empty catalog search results.
- **Empty & Null Fields**: Missing recipe steps, empty ingredients list, omitted image URL, null nutritionist note.
- **Boundary Calories & Macros**: Single meal exceeding 1500 kcal, zero-calorie meal items (tea/water), rounding edge cases.
- **Encoding & Non-ASCII**: Italian accented letters (`è`, `é`, `à`, `ò`, `ù`), apostrophes (`d'avena`, `un'arancia`), currency symbols (`€`), punctuation.
- **Negative & Invalid Quantities**: Negative grams (`-50g`), non-numeric strings, zero portions, invalid unit strings.
- **Safety Invariant Boundaries**: Partial URL matches (`/checkout-review`, `/cassa/step1`, `/api/payment`), mixed case URLs, redirect chains.

### Tier 3: Cross-Feature Interactions (Integration & Data Flow)
Validates that disparate modules interact harmoniously:
- **Cart vs Recipe Consistency**: Every ingredient in all 35 recipes is accounted for in the aggregated grocery cart list.
- **Macro Sum Coherence**: The sum of carbs, proteins, fats, and calories across the 5 daily meals matches the reported daily total within rounding tolerance (±1%).
- **Free Meal vs Cooking Steps**: Saturday dinner has `is_free_meal: true`, does not require complex cooking steps, yet accurately contributes to weekly macros.
- **Git-as-CMS Serialization Roundtrip**: Loading JSON -> mutating values -> serializing back to disk produces identical schema and character fidelity without losing accents or keys.
- **Pantry Taxonomy Mapping**: Every ingredient in the seed dataset has an identifiable nutritional category and fallback mapping in the taxonomy.

### Tier 4: Real-World Scenarios (End-to-End User Journeys)
Exercises complete end-to-end workflows:
- **Full Friday Orchestration Simulation**: Recipe generation -> photo assignment -> cart compilation -> Git commit -> Telegram dispatch.
- **Esselunga NO-CHECKOUT Safety Invariant**: Verifies that any simulated cart-filler execution rigorously aborts network requests to `/checkout`, `/cassa`, or `/pagamento` and contains zero checkout click actions.
- **Telegram Alert Delivery Contract**: Validates the complete HTML notification payload dispatched to `send_alert.py`, verifying required tags, links, item counts, and cost summaries.
- **Session Expiry Recovery Flow**: Simulates an expired session, verifies exit code 2, verifies no password prompts, and verifies that the exact recovery alert is formatted for Telegram.

---

## 3. Authoritative Specifications & Ground Truth

### 3.1 Dr. Caglioni Bromatological Target (Page 2 of Medical Plan)
- **Daily Calories**: `2063 kcal`
- **Proteins**: `112 g` (22% of total energy)
- **Carbohydrates**: `251 g` (49% of total energy, sugars: `85 g`)
- **Fats**: `68 g` (29% of total energy, saturated: `19 g`)
- **Fiber**: `42 g`
- **Cholesterol**: `260 mg`
- **Hydration**: Minimum `2.0 L/day`

### 3.2 Weekly Protein Rotation (14 Main Meals)
- **White meat** (150g): 2 meals
- **Red meat** (120g): 1 meal
- **Lean cold cuts** (100g): 1 meal
- **Fresh/frozen fish** (200g or 125g salmon): 2 meals
- **Eggs** (2 eggs): 2 meals
- **Legumes / Tofu** (150g cooked / 50g dry / 125g tofu): 3 meals
- **Fresh / aged cheese** (100g fresh / 70g aged): 2 meals
- **Free meal** (Pizza Margherita napoletana): 1 meal
- **Total**: Exactly 14 main meal slots.

### 3.3 Strict 3-Layer Security Guardrail (Esselunga)
1. **Selector Guardrail**: Zero selectors for checkout, cassa, conferma ordine, or slot reservation.
2. **Network Route Abort**: Unconditional route abort on any request matching `*checkout*`, `*cassa*`, `*pagamento*`, `*prenotazione-slot*`.
3. **URL Assertion**: Post-execution assertion verifying current URL remains in cart review (`/carrello`) and has never navigated to checkout.

### 3.4 Telegram Alert Contract (`send_alert.py`)
- HTML payload format:
  ```html
  🛒 <b>Riepilogo Spesa Esselunga — Settimana [Date Range]</b>
  📦 Articoli aggiunti: <b>[Count]</b>
  💰 Spesa stimata: <b>[Total] €</b>
  🌐 Dashboard: <a href="[URL]">Visualizza Menù</a>
  ```

---

## 4. Test Suite File Map

```
C:\Users\david\Desktop\Progetti\meal-planner-dashboard\
├── TEST_INFRA.md                   # This specification document
├── TEST_READY.md                   # Formal readiness certificate
└── tests/
    ├── __init__.py                 # Test package marker
    ├── fixtures.py                 # Authoritative models, mock environments, reference data
    ├── test_data_schema.py         # Contract 1 & 4 schema integrity tests
    ├── test_nutritional_integrity.py # Dr. Caglioni bromatological & rotation tests
    ├── test_cart_safety.py         # Esselunga automation safety & guardrail tests
    ├── test_orchestrator.py        # Friday pipeline & Telegram alert contract tests
    ├── test_tier1_feature_coverage.py # Comprehensive Tier 1 feature suite (F1-F20)
    ├── test_tier2_boundary_edge.py    # Comprehensive Tier 2 boundary suite
    ├── test_tier3_cross_feature.py    # Comprehensive Tier 3 cross-feature suite
    ├── test_tier4_real_world.py       # Comprehensive Tier 4 scenario suite
    └── run_all_tests.py            # Master runner, tier metrics reporter, exit code 0
```

---

## 5. Execution & Verification

### Running the Full Test Suite
From the project root:
```powershell
python tests/run_all_tests.py
```

### Running Specific Test Modules
```powershell
python -m unittest tests/test_tier1_feature_coverage.py
python -m unittest tests/test_tier2_boundary_edge.py
python -m unittest tests/test_tier3_cross_feature.py
python -m unittest tests/test_tier4_real_world.py
python -m unittest tests/test_cart_safety.py
```

### Exit Codes
- `0`: All tests passed across all tiers. Invariants strictly verified.
- `1`: One or more tests failed, or an invariant violation was detected.
