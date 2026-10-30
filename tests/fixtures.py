"""
Testing Fixtures and Authoritative Reference Models for Meal Planner Dashboard & Esselunga Automation.
Contains authoritative data models, schema validators, Dr. Caglioni bromatological calculators,
and safety invariants.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

LIVE_DATA_PATH = Path(__file__).resolve().parent.parent / "src" / "data" / "current-week.json"

CATEGORY_TAXONOMY_MAP: Dict[str, str] = {
    # Canonical tokens (self-mapping)
    "carne_bianca": "carne_bianca",
    "carne_rossa": "carne_rossa",
    "affettati_magri": "affettati_magri",
    "pesce": "pesce",
    "uova": "uova",
    "legumi_tofu": "legumi_tofu",
    "formaggi": "formaggi",
    "pasto_libero": "pasto_libero",
    # Italian UI display labels used in current-week.json
    "carne bianca": "carne_bianca",
    "carne rossa": "carne_rossa",
    "affettati magri": "affettati_magri",
    "pesce fresco": "pesce",
    "legumi": "legumi_tofu",
    "legumi e tofu": "legumi_tofu",
    "uova": "uova",
    "formaggi": "formaggi",
    "pasto libero": "pasto_libero",
}

def normalize_category(category_name: str, is_free_meal: bool = False) -> str:
    """Normalizes category name from UI display label or enum token into canonical protein category."""
    if is_free_meal:
        return "pasto_libero"
    clean = (category_name or "").strip().lower()
    return CATEGORY_TAXONOMY_MAP.get(clean, clean)

# Authoritative Nutritional Constants from Dr. Caglioni's Diet Plan (05/11/2025, Page 2)
AUTHORITATIVE_TARGET = {
    "kcal": 2063,
    "proteins_g": 112,
    "carbs_g": 251,
    "fats_g": 68,
    "fiber_g": 42,
    "cholesterol_mg": 260,
    "min_hydration_l": 2.0
}

# Required 14 main meal protein distribution across 7 days (Pranzo and Cena)
AUTHORITATIVE_PROTEIN_FREQUENCIES = {
    "carne_bianca": 2,       # 150g per meal
    "carne_rossa": 1,        # 120g per meal
    "affettati_magri": 1,    # 100g per meal (bresaola/tacchino/prosciutto sgrassato)
    "pesce": 2,              # 200g fresh/frozen or 125g salmon
    "uova": 2,               # 2 eggs per meal (4 eggs total)
    "legumi_tofu": 3,        # 150g cooked / 50g dry / 125g tofu per meal
    "formaggi": 2,           # 100g fresh or 70g aged per meal
    "pasto_libero": 1        # 1 free meal (Pizza Margherita / Ortolana)
}

# Authoritative Pantry Taxonomy with 1-to-1 fallbacks for out-of-stock items
AUTHORITATIVE_PANTRY_TAXONOMY = {
    "petto_di_pollo": {
        "category": "carne_bianca",
        "search_term": "petto di pollo a fette",
        "fallback_term": "fesa di tacchino a fette",
        "portion_g": 150
    },
    "tagliata_di_manzo": {
        "category": "carne_rossa",
        "search_term": "tagliata di manzo magro",
        "fallback_term": "filetto di vitello a fette",
        "portion_g": 120
    },
    "bresaola": {
        "category": "affettati_magri",
        "search_term": "bresaola della valtellina igp",
        "fallback_term": "fesa di tacchino arrosto",
        "portion_g": 100
    },
    "filetto_orata": {
        "category": "pesce",
        "search_term": "filetti di orata freschi",
        "fallback_term": "filetti di branzino freschi",
        "portion_g": 200
    },
    "trancio_salmone": {
        "category": "pesce",
        "search_term": "trancio di salmone fresco",
        "fallback_term": "filetto di trota salmonata",
        "portion_g": 125
    },
    "uova_fresche": {
        "category": "uova",
        "search_term": "uova fresche biologiche",
        "fallback_term": "uova allevate all'aperto",
        "portion_qty": 2
    },
    "ceci_lessati": {
        "category": "legumi_tofu",
        "search_term": "ceci lessati in vetro bio",
        "fallback_term": "fagioli cannellini lessati",
        "portion_g": 150
    },
    "lenticchie_lessate": {
        "category": "legumi_tofu",
        "search_term": "lenticchie lessate in vetro",
        "fallback_term": "lenticchie secche bio",
        "portion_g": 150
    },
    "tofu_al_naturale": {
        "category": "legumi_tofu",
        "search_term": "tofu al naturale bio",
        "fallback_term": "tofu affumicato bio",
        "portion_g": 125
    },
    "ricotta_vaccina": {
        "category": "formaggi",
        "search_term": "ricotta vaccina fresca",
        "fallback_term": "fiocchi di latte magri",
        "portion_g": 100
    },
    "parmigiano_reggiano": {
        "category": "formaggi",
        "search_term": "parmigiano reggiano dop 24 mesi",
        "fallback_term": "grana padano dop 16 mesi",
        "portion_g": 70
    }
}

# Forbidden keyword patterns for Esselunga safety guardrails (Strict NO-CHECKOUT)
FORBIDDEN_CHECKOUT_PATTERNS = [
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
    """Returns True if the URL attempts navigation towards checkout or payment."""
    clean_url = url.lower()
    for pattern in FORBIDDEN_CHECKOUT_PATTERNS:
        if re.search(r"(\b|/|_|-|\?|#|=)" + pattern + r"(\b|/|_|-|\?|#|=|&|$)", clean_url):
            return True
    return False

# Authoritative Seed Week Dataset for 31/10/2026 - 06/11/2026
SAMPLE_VALID_WEEK: Dict[str, Any] = {
    "week_id": "2026-W44",
    "week_start": "2026-10-31",
    "week_end": "2026-11-06",
    "macro_target": {
        "kcal": 2063,
        "carbs_g": 251,
        "proteins_g": 112,
        "fats_g": 68,
        "fiber_g": 42
    },
    "cart_summary": {
        "total_estimated_eur": 48.75,
        "items_count": 21,
        "cart_url": "https://spesaonline.esselunga.it/commerce/nav/supermercato/carrello",
        "last_updated": "2026-10-30T08:00:00Z",
        "store": "Esselunga"
    },
    "days": [
        {
            "day_name": "Sabato",
            "date": "2026-10-31",
            "daily_macros": {"kcal": 2060, "carbs_g": 250, "proteins_g": 112, "fats_g": 68},
            "meals": {
                "colazione": {
                    "id": "sab_col",
                    "meal_type": "colazione",
                    "title": "Biscotti Grancereale, latte parz. scremato e caffè",
                    "subtitle": "Colazione energetica classica",
                    "category": "colazione",
                    "kcal": 340,
                    "macros": {"carbs_g": 48, "proteins_g": 13, "fats_g": 10},
                    "ingredients": [
                        {"name": "Biscotti integrali Grancereale", "qty": "44g", "category": "cereali"},
                        {"name": "Latte vaccino parzialmente scremato", "qty": "200ml", "category": "latticini"},
                        {"name": "Caffè amaro", "qty": "1 tazzina", "category": "bevande"}
                    ],
                    "recipe_steps": [
                        "Scaldare 200ml di latte parzialmente scremato senza portarlo a ebollizione.",
                        "Preparare un caffè espresso moka e unirlo al latte o berlo a parte.",
                        "Servire con 44g di biscotti Grancereale integrali."
                    ],
                    "prep_time_min": 5,
                    "cook_time_min": 3,
                    "image_url": "/recipes/sabato_colazione.webp",
                    "is_free_meal": False
                },
                "pranzo": {
                    "id": "sab_pra",
                    "meal_type": "pranzo",
                    "title": "Involtini di verza autunnali con uova strapazzate e pane tostato",
                    "subtitle": "Proteine da uova (2 uova) con verdura di stagione",
                    "category": "uova",
                    "kcal": 580,
                    "macros": {"carbs_g": 64, "proteins_g": 47, "fats_g": 16.5},
                    "ingredients": [
                        {"name": "Uova fresche biologiche", "qty": "2 uova", "category": "uova"},
                        {"name": "Verza autunnale", "qty": "200g", "category": "verdure"},
                        {"name": "Pane integrale di frumento", "qty": "130g", "category": "carboidrati"},
                        {"name": "Olio extravergine d'oliva", "qty": "10g", "category": "condimenti"},
                        {"name": "Succo di limone", "qty": "1 cucchiaio", "category": "condimenti"}
                    ],
                    "recipe_steps": [
                        "Mondare la verza e scottare le foglie in acqua bollente leggermente salata per 3 minuti.",
                        "Sbattere 2 uova con un pizzico di pepe e cuocere a fuoco lento in padella antiaderente.",
                        "Arrotolare la verza e servire con 130g di pane tostato al forno con filo d'olio EVO."
                    ],
                    "prep_time_min": 10,
                    "cook_time_min": 12,
                    "image_url": "/recipes/sabato_pranzo.webp",
                    "is_free_meal": False
                },
                "spuntino_pomeriggio": {
                    "id": "sab_spu",
                    "meal_type": "spuntino_pomeriggio",
                    "title": "Yogurt greco 0% con mela a cubetti e cannella",
                    "subtitle": "Spuntino ad alto valore biologico",
                    "category": "spuntino",
                    "kcal": 165,
                    "macros": {"carbs_g": 24, "proteins_g": 16, "fats_g": 0.5},
                    "ingredients": [
                        {"name": "Yogurt greco naturale 0% grassi", "qty": "150g", "category": "latticini"},
                        {"name": "Mela fresca di stagione", "qty": "150g", "category": "frutta"},
                        {"name": "Cannella in polvere", "qty": "q.b.", "category": "spezie"}
                    ],
                    "recipe_steps": [
                        "Versare lo yogurt greco 0% in una ciotola di ceramica.",
                        "Lavare e tagliare la mela a dadini senza sbucciarla per preservare la fibra.",
                        "Spolverare con cannella macinata a piacere."
                    ],
                    "prep_time_min": 5,
                    "cook_time_min": 0,
                    "image_url": "/recipes/sabato_spuntino.webp",
                    "is_free_meal": False
                },
                "cena": {
                    "id": "sab_cen",
                    "meal_type": "cena",
                    "title": "Pizza Margherita Napoletana",
                    "subtitle": "Pasto Libero settimanale autorizzato dalla Dott.ssa Caglioni",
                    "category": "pasto_libero",
                    "kcal": 780,
                    "macros": {"carbs_g": 92, "proteins_g": 32, "fats_g": 28},
                    "ingredients": [
                        {"name": "Pizza margherita artigianale napoletana", "qty": "1 pizza", "category": "pasto_libero"}
                    ],
                    "recipe_steps": [
                        "Pasto Libero conviviale: gustare la pizza margherita con pomodoro, fior di latte e basilico fresco.",
                        "Nessuna preparazione richiesta, consentita dalla nutrizionista."
                    ],
                    "prep_time_min": 0,
                    "cook_time_min": 0,
                    "image_url": "/recipes/sabato_cena.webp",
                    "is_free_meal": True
                },
                "dopocena": {
                    "id": "sab_dop",
                    "meal_type": "dopocena",
                    "title": "Noci sgusciate e pera fresca a fette",
                    "subtitle": "Acidi grassi omega-3 e micronutrienti serali",
                    "category": "dopocena",
                    "kcal": 195,
                    "macros": {"carbs_g": 22, "proteins_g": 4, "fats_g": 13},
                    "ingredients": [
                        {"name": "Gherigli di noci", "qty": "20g", "category": "frutta_secca"},
                        {"name": "Pera Williams", "qty": "150g", "category": "frutta"}
                    ],
                    "recipe_steps": [
                        "Tagliare la pera fresca a fettine sottili.",
                        "Accompagnare con 20g di noci sgusciate crude."
                    ],
                    "prep_time_min": 3,
                    "cook_time_min": 0,
                    "image_url": "/recipes/sabato_dopocena.webp",
                    "is_free_meal": False
                }
            }
        },
        {
            "day_name": "Domenica",
            "date": "2026-11-01",
            "daily_macros": {"kcal": 2065, "carbs_g": 251, "proteins_g": 112, "fats_g": 68},
            "meals": {
                "colazione": {
                    "id": "dom_col",
                    "meal_type": "colazione",
                    "title": "Pane tostato con marmellata 100% frutta e latte",
                    "subtitle": "Colazione della domenica",
                    "category": "colazione",
                    "kcal": 350,
                    "macros": {"carbs_g": 58, "proteins_g": 14, "fats_g": 5},
                    "ingredients": [
                        {"name": "Pane integrale tostato", "qty": "75g", "category": "carboidrati"},
                        {"name": "Confettura 100% frutta", "qty": "25g", "category": "dolci"},
                        {"name": "Latte parz. scremato", "qty": "200ml", "category": "latticini"}
                    ],
                    "recipe_steps": [
                        "Tostare il pane a fette.",
                        "Spalmare la marmellata senza zuccheri aggiunti.",
                        "Accompagnare con tazza di latte caldo."
                    ],
                    "prep_time_min": 5,
                    "cook_time_min": 2,
                    "image_url": "/recipes/domenica_colazione.webp",
                    "is_free_meal": False
                },
                "pranzo": {
                    "id": "dom_pra",
                    "meal_type": "pranzo",
                    "title": "Bocconcini di pollo alla piastra con zucca al forno e riso basmati",
                    "subtitle": "Carne bianca (150g) e carboidrati nobili",
                    "category": "carne_bianca",
                    "kcal": 675,
                    "macros": {"carbs_g": 85, "proteins_g": 42, "fats_g": 17},
                    "ingredients": [
                        {"name": "Petto di pollo a fette", "qty": "150g", "category": "carne_bianca"},
                        {"name": "Zucca delica a fette", "qty": "250g", "category": "verdure"},
                        {"name": "Riso basmati", "qty": "100g", "category": "carboidrati"},
                        {"name": "Olio extravergine d'oliva", "qty": "10g", "category": "condimenti"}
                    ],
                    "recipe_steps": [
                        "Lessare il riso basmati al dente per 10 minuti.",
                        "Infornare la zucca a 180°C con rosmarino per 20 minuti.",
                        "Grigliare i bocconcini di pollo con gocce di limone."
                    ],
                    "prep_time_min": 10,
                    "cook_time_min": 20,
                    "image_url": "/recipes/domenica_pranzo.webp",
                    "is_free_meal": False
                },
                "spuntino_pomeriggio": {
                    "id": "dom_spu",
                    "meal_type": "spuntino_pomeriggio",
                    "title": "Yogurt greco 0% e pera fresca",
                    "subtitle": "Break pomeridiano leggero",
                    "category": "spuntino",
                    "kcal": 160,
                    "macros": {"carbs_g": 23, "proteins_g": 16, "fats_g": 0.5},
                    "ingredients": [
                        {"name": "Yogurt greco naturale 0%", "qty": "150g", "category": "latticini"},
                        {"name": "Pera abate", "qty": "150g", "category": "frutta"}
                    ],
                    "recipe_steps": ["Mescolare yogurt e pera a cubetti."],
                    "prep_time_min": 3,
                    "cook_time_min": 0,
                    "image_url": "/recipes/domenica_spuntino.webp",
                    "is_free_meal": False
                },
                "cena": {
                    "id": "dom_cen",
                    "meal_type": "cena",
                    "title": "Filetto di orata al cartoccio con finocchi gratinati e pane",
                    "subtitle": "Pesce fresco (200g) e verdura di stagione",
                    "category": "pesce",
                    "kcal": 680,
                    "macros": {"carbs_g": 68, "proteins_g": 33, "fats_g": 34},
                    "ingredients": [
                        {"name": "Filetti di orata freschi", "qty": "200g", "category": "pesce"},
                        {"name": "Finocchi di stagione", "qty": "250g", "category": "verdure"},
                        {"name": "Pane integrale tostato", "qty": "130g", "category": "carboidrati"},
                        {"name": "Olio extravergine d'oliva", "qty": "10g", "category": "condimenti"}
                    ],
                    "recipe_steps": [
                        "Avvolgere l'orata in carta forno con timo ed erbe aromatiche.",
                        "Cuocere in forno a 190°C per 15 minuti.",
                        "Servire con finocchi al vapore e pane tostato."
                    ],
                    "prep_time_min": 10,
                    "cook_time_min": 15,
                    "image_url": "/recipes/domenica_cena.webp",
                    "is_free_meal": False
                },
                "dopocena": {
                    "id": "dom_dop",
                    "meal_type": "dopocena",
                    "title": "Parmigiano Reggiano e mela fresca",
                    "subtitle": "Spuntino serale proteico",
                    "category": "dopocena",
                    "kcal": 200,
                    "macros": {"carbs_g": 17, "proteins_g": 7, "fats_g": 11.5},
                    "ingredients": [
                        {"name": "Parmigiano Reggiano DOP 24 mesi", "qty": "20g", "category": "formaggi"},
                        {"name": "Mela golden", "qty": "150g", "category": "frutta"}
                    ],
                    "recipe_steps": ["Tagliare a scaglie il Parmigiano e servire con fette di mela."],
                    "prep_time_min": 3,
                    "cook_time_min": 0,
                    "image_url": "/recipes/domenica_dopocena.webp",
                    "is_free_meal": False
                }
            }
        },
        {
            "day_name": "Lunedì",
            "date": "2026-11-02",
            "daily_macros": {"kcal": 2060, "carbs_g": 251, "proteins_g": 112, "fats_g": 68},
            "meals": {
                "colazione": {
                    "id": "lun_col",
                    "meal_type": "colazione",
                    "title": "Porridge d'avena caldo con cannella e caffè",
                    "subtitle": "Fibre solubili e sazietà prolungata",
                    "category": "colazione",
                    "kcal": 365,
                    "macros": {"carbs_g": 52, "proteins_g": 16, "fats_g": 9},
                    "ingredients": [
                        {"name": "Fiocchi d'avena integrali", "qty": "50g", "category": "cereali"},
                        {"name": "Latte parz. scremato", "qty": "200ml", "category": "latticini"}
                    ],
                    "recipe_steps": ["Cuocere l'avena nel latte caldo a fiamma dolce per 4 minuti."],
                    "prep_time_min": 3,
                    "cook_time_min": 4,
                    "image_url": "/recipes/lunedi_colazione.webp",
                    "is_free_meal": False
                },
                "pranzo": {
                    "id": "lun_pra",
                    "meal_type": "pranzo",
                    "title": "Pasta integrale con crema di ceci al rosmarino e cicoria",
                    "subtitle": "Legumi (150g) e carboidrati complessi",
                    "category": "legumi_tofu",
                    "kcal": 665,
                    "macros": {"carbs_g": 96, "proteins_g": 32, "fats_g": 15},
                    "ingredients": [
                        {"name": "Pasta integrale", "qty": "100g", "category": "carboidrati"},
                        {"name": "Ceci lessati in vetro", "qty": "150g", "category": "legumi_tofu"},
                        {"name": "Cicoria fresca", "qty": "200g", "category": "verdure"},
                        {"name": "Olio extravergine d'oliva", "qty": "10g", "category": "condimenti"}
                    ],
                    "recipe_steps": [
                        "Lessare la pasta integrale in acqua bollente salata al dente.",
                        "Frullare metà dei ceci con rosmarino e acqua di cottura per creare la crema.",
                        "Saltare la cicoria in padella e condire la pasta con la crema di ceci e olio EVO a crudo."
                    ],
                    "prep_time_min": 8,
                    "cook_time_min": 10,
                    "image_url": "/recipes/lunedi_pranzo.webp",
                    "is_free_meal": False
                },
                "spuntino_pomeriggio": {
                    "id": "lun_spu",
                    "meal_type": "spuntino_pomeriggio",
                    "title": "Yogurt greco 0% e kiwi a fette",
                    "subtitle": "Vitamina C e probiotici",
                    "category": "spuntino",
                    "kcal": 170,
                    "macros": {"carbs_g": 24, "proteins_g": 16, "fats_g": 0.8},
                    "ingredients": [
                        {"name": "Yogurt greco naturale 0%", "qty": "150g", "category": "latticini"},
                        {"name": "Kiwi freschi", "qty": "150g", "category": "frutta"}
                    ],
                    "recipe_steps": ["Sbucciare il kiwi, affettarlo e incorporarlo allo yogurt."],
                    "prep_time_min": 3,
                    "cook_time_min": 0,
                    "image_url": "/recipes/lunedi_spuntino.webp",
                    "is_free_meal": False
                },
                "cena": {
                    "id": "lun_cen",
                    "meal_type": "cena",
                    "title": "Tagliata di manzo magro con patate al forno e spinaci",
                    "subtitle": "Carne rossa magra (120g) e ferro bio-disponibile",
                    "category": "carne_rossa",
                    "kcal": 670,
                    "macros": {"carbs_g": 61, "proteins_g": 43, "fats_g": 32.2},
                    "ingredients": [
                        {"name": "Tagliata di manzo magro", "qty": "120g", "category": "carne_rossa"},
                        {"name": "Patate a pasta gialla", "qty": "400g", "category": "carboidrati"},
                        {"name": "Spinaci novelli", "qty": "200g", "category": "verdure"},
                        {"name": "Olio extravergine d'oliva", "qty": "10g", "category": "condimenti"},
                        {"name": "Limone fresco", "qty": "1/2 frutto", "category": "condimenti"}
                    ],
                    "recipe_steps": [
                        "Tagliare le patate a tocchetti e cuocere al vapore o al forno.",
                        "Scottare la tagliata di manzo 2 minuti per lato sulla piastra ben calda.",
                        "Servire con spinaci conditi con limone per favorire l'assorbimento del ferro."
                    ],
                    "prep_time_min": 10,
                    "cook_time_min": 15,
                    "image_url": "/recipes/lunedi_cena.webp",
                    "is_free_meal": False
                },
                "dopocena": {
                    "id": "lun_dop",
                    "meal_type": "dopocena",
                    "title": "Mandorle sgusciate e clementine",
                    "subtitle": "Magnesio e relax serale",
                    "category": "dopocena",
                    "kcal": 190,
                    "macros": {"carbs_g": 18, "proteins_g": 5, "fats_g": 11},
                    "ingredients": [
                        {"name": "Mandorle pelate", "qty": "20g", "category": "frutta_secca"},
                        {"name": "Clementine fresche", "qty": "150g", "category": "frutta"}
                    ],
                    "recipe_steps": ["Gustare mandorle e clementine a spicchi."],
                    "prep_time_min": 2,
                    "cook_time_min": 0,
                    "image_url": "/recipes/lunedi_dopocena.webp",
                    "is_free_meal": False
                }
            }
        },
        {
            "day_name": "Martedì",
            "date": "2026-11-03",
            "daily_macros": {"kcal": 2060, "carbs_g": 251, "proteins_g": 112, "fats_g": 68},
            "meals": {
                "colazione": {
                    "id": "mar_col",
                    "meal_type": "colazione",
                    "title": "Biscotti Grancereale con latte e caffè espresso",
                    "subtitle": "Colazione bilanciata",
                    "category": "colazione",
                    "kcal": 340,
                    "macros": {"carbs_g": 48, "proteins_g": 13, "fats_g": 10},
                    "ingredients": [
                        {"name": "Biscotti integrali Grancereale", "qty": "44g", "category": "cereali"},
                        {"name": "Latte parz. scremato", "qty": "200ml", "category": "latticini"}
                    ],
                    "recipe_steps": ["Scaldare il latte e inzuppare i biscotti."],
                    "prep_time_min": 3,
                    "cook_time_min": 2,
                    "image_url": "/recipes/martedi_colazione.webp",
                    "is_free_meal": False
                },
                "pranzo": {
                    "id": "mar_pra",
                    "meal_type": "pranzo",
                    "title": "Farro perlato con ricotta fresca vaccina e zucchine",
                    "subtitle": "Formaggio fresco (100g) e cereali antichi",
                    "category": "formaggi",
                    "kcal": 670,
                    "macros": {"carbs_g": 82, "proteins_g": 32, "fats_g": 22},
                    "ingredients": [
                        {"name": "Farro perlato", "qty": "100g", "category": "carboidrati"},
                        {"name": "Ricotta fresca vaccina", "qty": "100g", "category": "formaggi"},
                        {"name": "Zucchine scure", "qty": "200g", "category": "verdure"},
                        {"name": "Olio extravergine d'oliva", "qty": "10g", "category": "condimenti"}
                    ],
                    "recipe_steps": [
                        "Lessare il farro perlato per 18 minuti.",
                        "Trifolare le zucchine a rondelle con olio EVO e origano.",
                        "Amalgamare il farro con la ricotta fresca a crudo e le zucchine."
                    ],
                    "prep_time_min": 8,
                    "cook_time_min": 18,
                    "image_url": "/recipes/martedi_pranzo.webp",
                    "is_free_meal": False
                },
                "spuntino_pomeriggio": {
                    "id": "mar_spu",
                    "meal_type": "spuntino_pomeriggio",
                    "title": "Yogurt greco 0% con prugne secche",
                    "subtitle": "Regolarità e sazietà",
                    "category": "spuntino",
                    "kcal": 165,
                    "macros": {"carbs_g": 25, "proteins_g": 16, "fats_g": 0.5},
                    "ingredients": [
                        {"name": "Yogurt greco naturale 0%", "qty": "150g", "category": "latticini"},
                        {"name": "Prugne secche denocciolate", "qty": "30g", "category": "frutta_secca"}
                    ],
                    "recipe_steps": ["Sminuzzare le prugne secche nello yogurt."],
                    "prep_time_min": 3,
                    "cook_time_min": 0,
                    "image_url": "/recipes/martedi_spuntino.webp",
                    "is_free_meal": False
                },
                "cena": {
                    "id": "mar_cen",
                    "meal_type": "cena",
                    "title": "Trancio di salmone fresco con crema di broccoli e pane integrale",
                    "subtitle": "Pesce azzurro/grasso (125g) ricco di omega-3",
                    "category": "pesce",
                    "kcal": 690,
                    "macros": {"carbs_g": 74, "proteins_g": 47, "fats_g": 23},
                    "ingredients": [
                        {"name": "Trancio di salmone fresco", "qty": "125g", "category": "pesce"},
                        {"name": "Broccoli cime", "qty": "250g", "category": "verdure"},
                        {"name": "Pane integrale tostato", "qty": "130g", "category": "carboidrati"},
                        {"name": "Olio extravergine d'oliva", "qty": "10g", "category": "condimenti"}
                    ],
                    "recipe_steps": [
                        "Cuocere i broccoli al vapore e frullarli con un pizzico di sale e pepe.",
                        "Scottare il trancio di salmone in padella antiaderente 4 minuti per lato.",
                        "Servire sulla crema di broccoli accompagnato dal pane tostato."
                    ],
                    "prep_time_min": 10,
                    "cook_time_min": 12,
                    "image_url": "/recipes/martedi_cena.webp",
                    "is_free_meal": False
                },
                "dopocena": {
                    "id": "mar_dop",
                    "meal_type": "dopocena",
                    "title": "Noci sgusciate e mela Fuji",
                    "subtitle": "Snack serale salutare",
                    "category": "dopocena",
                    "kcal": 195,
                    "macros": {"carbs_g": 22, "proteins_g": 4, "fats_g": 12.5},
                    "ingredients": [
                        {"name": "Gherigli di noci", "qty": "20g", "category": "frutta_secca"},
                        {"name": "Mela Fuji", "qty": "150g", "category": "frutta"}
                    ],
                    "recipe_steps": ["Consumare mela e noci fresche."],
                    "prep_time_min": 2,
                    "cook_time_min": 0,
                    "image_url": "/recipes/martedi_dopocena.webp",
                    "is_free_meal": False
                }
            }
        },
        {
            "day_name": "Mercoledì",
            "date": "2026-11-04",
            "daily_macros": {"kcal": 2060, "carbs_g": 251, "proteins_g": 112, "fats_g": 68},
            "meals": {
                "colazione": {
                    "id": "mer_col",
                    "meal_type": "colazione",
                    "title": "Pane tostato con marmellata e latte tiepido",
                    "subtitle": "Tradizione e semplicità",
                    "category": "colazione",
                    "kcal": 350,
                    "macros": {"carbs_g": 58, "proteins_g": 14, "fats_g": 5},
                    "ingredients": [
                        {"name": "Pane integrale tostato", "qty": "75g", "category": "carboidrati"},
                        {"name": "Marmellata senza zuccheri", "qty": "25g", "category": "dolci"},
                        {"name": "Latte parz. scremato", "qty": "200ml", "category": "latticini"}
                    ],
                    "recipe_steps": ["Tostare il pane e spalmare la marmellata."],
                    "prep_time_min": 3,
                    "cook_time_min": 2,
                    "image_url": "/recipes/mercoledi_colazione.webp",
                    "is_free_meal": False
                },
                "pranzo": {
                    "id": "mer_pra",
                    "meal_type": "pranzo",
                    "title": "Zuppa rustica di pasta e lenticchie con bietole stufate",
                    "subtitle": "Legumi (150g) e profilo amminoacidico completo",
                    "category": "legumi_tofu",
                    "kcal": 665,
                    "macros": {"carbs_g": 96, "proteins_g": 33, "fats_g": 14.5},
                    "ingredients": [
                        {"name": "Pasta corta integrale", "qty": "100g", "category": "carboidrati"},
                        {"name": "Lenticchie lessate", "qty": "150g", "category": "legumi_tofu"},
                        {"name": "Bietole a coste", "qty": "200g", "category": "verdure"},
                        {"name": "Olio extravergine d'oliva", "qty": "10g", "category": "condimenti"}
                    ],
                    "recipe_steps": [
                        "Stufare le bietole tagliate a striscioline con poco brodo vegetale.",
                        "Aggiungere le lenticchie e calare la pasta nella zuppa a bollore.",
                        "Completare con un cucchiaio di olio EVO a crudo."
                    ],
                    "prep_time_min": 10,
                    "cook_time_min": 15,
                    "image_url": "/recipes/mercoledi_pranzo.webp",
                    "is_free_meal": False
                },
                "spuntino_pomeriggio": {
                    "id": "mer_spu",
                    "meal_type": "spuntino_pomeriggio",
                    "title": "Yogurt greco 0% e arancia pelata a vivo",
                    "subtitle": "Ricarica antiossidante",
                    "category": "spuntino",
                    "kcal": 160,
                    "macros": {"carbs_g": 22, "proteins_g": 16, "fats_g": 0.5},
                    "ingredients": [
                        {"name": "Yogurt greco naturale 0%", "qty": "150g", "category": "latticini"},
                        {"name": "Arancia tarocco", "qty": "150g", "category": "frutta"}
                    ],
                    "recipe_steps": ["Pelare l'arancia a vivo e mescolare con lo yogurt."],
                    "prep_time_min": 4,
                    "cook_time_min": 0,
                    "image_url": "/recipes/mercoledi_spuntino.webp",
                    "is_free_meal": False
                },
                "cena": {
                    "id": "mer_cen",
                    "meal_type": "cena",
                    "title": "Scaloppine di pollo al limone con purè di cavolfiore e pane di segale",
                    "subtitle": "Carne bianca (150g) ad alta digeribilità",
                    "category": "carne_bianca",
                    "kcal": 685,
                    "macros": {"carbs_g": 57, "proteins_g": 42, "fats_g": 39},
                    "ingredients": [
                        {"name": "Petto di pollo a fette", "qty": "150g", "category": "carne_bianca"},
                        {"name": "Cavolfiore bianco", "qty": "300g", "category": "verdure"},
                        {"name": "Pane di segale tostato", "qty": "130g", "category": "carboidrati"},
                        {"name": "Olio extravergine d'oliva", "qty": "10g", "category": "condimenti"},
                        {"name": "Succo di limone", "qty": "2 cucchiai", "category": "condimenti"}
                    ],
                    "recipe_steps": [
                        "Cuocere il cavolfiore al vapore e schiacciarlo a purè con noce moscata.",
                        "Rosolare le fette di pollo in padella antiaderente sfumando con succo di limone fresco.",
                        "Impiattare il pollo sul purè di cavolfiore con pane di segale tostato."
                    ],
                    "prep_time_min": 10,
                    "cook_time_min": 12,
                    "image_url": "/recipes/mercoledi_cena.webp",
                    "is_free_meal": False
                },
                "dopocena": {
                    "id": "mer_dop",
                    "meal_type": "dopocena",
                    "title": "Parmigiano Reggiano e pera a fette",
                    "subtitle": "Calcio e minerali",
                    "category": "dopocena",
                    "kcal": 200,
                    "macros": {"carbs_g": 18, "proteins_g": 7, "fats_g": 9},
                    "ingredients": [
                        {"name": "Parmigiano Reggiano DOP", "qty": "20g", "category": "formaggi"},
                        {"name": "Pera Williams", "qty": "150g", "category": "frutta"}
                    ],
                    "recipe_steps": ["Consumare a tocchetti."],
                    "prep_time_min": 2,
                    "cook_time_min": 0,
                    "image_url": "/recipes/mercoledi_dopocena.webp",
                    "is_free_meal": False
                }
            }
        },
        {
            "day_name": "Giovedì",
            "date": "2026-11-05",
            "daily_macros": {"kcal": 2065, "carbs_g": 251, "proteins_g": 112, "fats_g": 68},
            "meals": {
                "colazione": {
                    "id": "gio_col",
                    "meal_type": "colazione",
                    "title": "Fiocchi d'avena nel latte caldo e caffè",
                    "subtitle": "Colazione d'avena",
                    "category": "colazione",
                    "kcal": 365,
                    "macros": {"carbs_g": 52, "proteins_g": 16, "fats_g": 9},
                    "ingredients": [
                        {"name": "Fiocchi d'avena", "qty": "50g", "category": "cereali"},
                        {"name": "Latte parz. scremato", "qty": "200ml", "category": "latticini"}
                    ],
                    "recipe_steps": ["Scaldare il latte e unire l'avena."],
                    "prep_time_min": 3,
                    "cook_time_min": 3,
                    "image_url": "/recipes/giovedi_colazione.webp",
                    "is_free_meal": False
                },
                "pranzo": {
                    "id": "gio_pra",
                    "meal_type": "pranzo",
                    "title": "Riso Venere con tofu saltato allo zenzero e cavolo nero",
                    "subtitle": "Tofu vegetale (125g) e cereale integrale",
                    "category": "legumi_tofu",
                    "kcal": 670,
                    "macros": {"carbs_g": 84, "proteins_g": 31, "fats_g": 22.5},
                    "ingredients": [
                        {"name": "Riso venere integrale", "qty": "100g", "category": "carboidrati"},
                        {"name": "Tofu al naturale bio", "qty": "125g", "category": "legumi_tofu"},
                        {"name": "Cavolo nero toscano", "qty": "200g", "category": "verdure"},
                        {"name": "Olio extravergine d'oliva", "qty": "10g", "category": "condimenti"},
                        {"name": "Zenzero fresco grattugiato", "qty": "5g", "category": "spezie"}
                    ],
                    "recipe_steps": [
                        "Lessare il riso venere per 25 minuti.",
                        "Privare il cavolo nero della costa centrale e saltarlo in padella con zenzero.",
                        "Tagliare il tofu a cubetti, dorarlo in padella e unire al riso e alle verdure."
                    ],
                    "prep_time_min": 10,
                    "cook_time_min": 25,
                    "image_url": "/recipes/giovedi_pranzo.webp",
                    "is_free_meal": False
                },
                "spuntino_pomeriggio": {
                    "id": "gio_spu",
                    "meal_type": "spuntino_pomeriggio",
                    "title": "Yogurt greco 0% e mela a cubetti con cannella",
                    "subtitle": "Spuntino classico pomeridiano",
                    "category": "spuntino",
                    "kcal": 165,
                    "macros": {"carbs_g": 24, "proteins_g": 16, "fats_g": 0.5},
                    "ingredients": [
                        {"name": "Yogurt greco naturale 0%", "qty": "150g", "category": "latticini"},
                        {"name": "Mela fresca", "qty": "150g", "category": "frutta"}
                    ],
                    "recipe_steps": ["Comporre la ciotola di yogurt con dadini di mela."],
                    "prep_time_min": 3,
                    "cook_time_min": 0,
                    "image_url": "/recipes/giovedi_spuntino.webp",
                    "is_free_meal": False
                },
                "cena": {
                    "id": "gio_cen",
                    "meal_type": "cena",
                    "title": "Frittata al forno con porri e zucchine, pane tostato",
                    "subtitle": "Uova (2 uova) cotte al forno senza grassi aggiunti",
                    "category": "uova",
                    "kcal": 670,
                    "macros": {"carbs_g": 69, "proteins_g": 44, "fats_g": 25},
                    "ingredients": [
                        {"name": "Uova fresche biologiche", "qty": "2 uova", "category": "uova"},
                        {"name": "Porri e zucchine", "qty": "250g", "category": "verdure"},
                        {"name": "Pane di semola tostato", "qty": "130g", "category": "carboidrati"},
                        {"name": "Olio extravergine d'oliva", "qty": "10g", "category": "condimenti"}
                    ],
                    "recipe_steps": [
                        "Stufare i porri e le zucchine con un goccio d'acqua.",
                        "Sbattere 2 uova con erbe provenzali e incorporare le verdure.",
                        "Versare in teglia foderata di carta forno e cuocere a 180°C per 15 minuti."
                    ],
                    "prep_time_min": 8,
                    "cook_time_min": 15,
                    "image_url": "/recipes/giovedi_cena.webp",
                    "is_free_meal": False
                },
                "dopocena": {
                    "id": "gio_dop",
                    "meal_type": "dopocena",
                    "title": "Mandorle pelate e mela",
                    "subtitle": "Apporto lipidico salutare",
                    "category": "dopocena",
                    "kcal": 195,
                    "macros": {"carbs_g": 22, "proteins_g": 5, "fats_g": 11},
                    "ingredients": [
                        {"name": "Mandorle", "qty": "20g", "category": "frutta_secca"},
                        {"name": "Mela", "qty": "150g", "category": "frutta"}
                    ],
                    "recipe_steps": ["Consumare mela e mandorle."],
                    "prep_time_min": 2,
                    "cook_time_min": 0,
                    "image_url": "/recipes/giovedi_dopocena.webp",
                    "is_free_meal": False
                }
            }
        },
        {
            "day_name": "Venerdì",
            "date": "2026-11-06",
            "daily_macros": {"kcal": 2060, "carbs_g": 251, "proteins_g": 112, "fats_g": 68},
            "meals": {
                "colazione": {
                    "id": "ven_col",
                    "meal_type": "colazione",
                    "title": "Biscotti Grancereale, latte parz. scremato e caffè",
                    "subtitle": "Colazione del venerdì",
                    "category": "colazione",
                    "kcal": 340,
                    "macros": {"carbs_g": 48, "proteins_g": 13, "fats_g": 10},
                    "ingredients": [
                        {"name": "Biscotti Grancereale", "qty": "44g", "category": "cereali"},
                        {"name": "Latte parz. scremato", "qty": "200ml", "category": "latticini"}
                    ],
                    "recipe_steps": ["Consumare latte caldo con biscotti integrali."],
                    "prep_time_min": 3,
                    "cook_time_min": 2,
                    "image_url": "/recipes/venerdi_colazione.webp",
                    "is_free_meal": False
                },
                "pranzo": {
                    "id": "ven_pra",
                    "meal_type": "pranzo",
                    "title": "Panino integrale con Bresaola IGP, rucola, pomodoro e limone",
                    "subtitle": "Affettati magri (100g) freschi e pratici",
                    "category": "affettati_magri",
                    "kcal": 660,
                    "macros": {"carbs_g": 74, "proteins_g": 48, "fats_g": 18.2},
                    "ingredients": [
                        {"name": "Bresaola della Valtellina IGP", "qty": "100g", "category": "affettati_magri"},
                        {"name": "Pane integrale fresco", "qty": "130g", "category": "carboidrati"},
                        {"name": "Rucola fresca", "qty": "80g", "category": "verdure"},
                        {"name": "Pomodoro a fette", "qty": "150g", "category": "verdure"},
                        {"name": "Olio extravergine d'oliva", "qty": "10g", "category": "condimenti"},
                        {"name": "Succo di limone", "qty": "1 cucchiaino", "category": "condimenti"}
                    ],
                    "recipe_steps": [
                        "Tagliare a metà il pane integrale fresco e tostarlo leggermente.",
                        "Farcire con 100g di bresaola, fette di pomodoro e rucola fresca.",
                        "Condire con gocce di limone e olio EVO a crudo."
                    ],
                    "prep_time_min": 6,
                    "cook_time_min": 2,
                    "image_url": "/recipes/venerdi_pranzo.webp",
                    "is_free_meal": False
                },
                "spuntino_pomeriggio": {
                    "id": "ven_spu",
                    "meal_type": "spuntino_pomeriggio",
                    "title": "Yogurt greco 0% e kiwi a dadini",
                    "subtitle": "Merenda ricca di fibre",
                    "category": "spuntino",
                    "kcal": 170,
                    "macros": {"carbs_g": 24, "proteins_g": 16, "fats_g": 0.8},
                    "ingredients": [
                        {"name": "Yogurt greco naturale 0%", "qty": "150g", "category": "latticini"},
                        {"name": "Kiwi freschi", "qty": "150g", "category": "frutta"}
                    ],
                    "recipe_steps": ["Amalgamare kiwi e yogurt greco."],
                    "prep_time_min": 3,
                    "cook_time_min": 0,
                    "image_url": "/recipes/venerdi_spuntino.webp",
                    "is_free_meal": False
                },
                "cena": {
                    "id": "ven_cen",
                    "meal_type": "cena",
                    "title": "Gnocchi di patate al pomodoro con scaglie di Parmigiano Reggiano",
                    "subtitle": "Formaggio stagionato (70g) e gnocchi (200g max 2x/settimana)",
                    "category": "formaggi",
                    "kcal": 700,
                    "macros": {"carbs_g": 84, "proteins_g": 31, "fats_g": 26},
                    "ingredients": [
                        {"name": "Gnocchi di patate freschi", "qty": "200g", "category": "carboidrati"},
                        {"name": "Parmigiano Reggiano DOP a scaglie", "qty": "70g", "category": "formaggi"},
                        {"name": "Passata di pomodoro e basilico", "qty": "150g", "category": "verdure"},
                        {"name": "Insalata mista", "qty": "100g", "category": "verdure"},
                        {"name": "Olio extravergine d'oliva", "qty": "10g", "category": "condimenti"}
                    ],
                    "recipe_steps": [
                        "Cuocere gli gnocchi in abbondante acqua bollente salata e scolare non appena salgono a galla.",
                        "Condire con salsa di pomodoro semplice al basilico.",
                        "Completare con 70g di scaglie di Parmigiano Reggiano e servire con insalata mista fresca."
                    ],
                    "prep_time_min": 8,
                    "cook_time_min": 5,
                    "image_url": "/recipes/venerdi_cena.webp",
                    "is_free_meal": False
                },
                "dopocena": {
                    "id": "ven_dop",
                    "meal_type": "dopocena",
                    "title": "Noci sgusciate e albicocche secche",
                    "subtitle": "Chiusura della settimana alimentare",
                    "category": "dopocena",
                    "kcal": 190,
                    "macros": {"carbs_g": 21, "proteins_g": 4, "fats_g": 13},
                    "ingredients": [
                        {"name": "Noci sgusciate", "qty": "20g", "category": "frutta_secca"},
                        {"name": "Albicocche secche", "qty": "30g", "category": "frutta"}
                    ],
                    "recipe_steps": ["Consumare albicocche e noci."],
                    "prep_time_min": 2,
                    "cook_time_min": 0,
                    "image_url": "/recipes/venerdi_dopocena.webp",
                    "is_free_meal": False
                }
            }
        }
    ]
}


def load_live_weekly_plan() -> Dict[str, Any]:
    """Loads src/data/current-week.json directly from disk if present, else falls back to reference fixture."""
    if LIVE_DATA_PATH.exists():
        with open(LIVE_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return SAMPLE_VALID_WEEK


def validate_weekly_plan_schema(data: Any) -> Tuple[bool, List[str]]:
    """
    Validates a weekly plan data dictionary against Contract 1 (WeeklyPlanData).
    Returns (True, []) if valid, or (False, [error_strings]) if invalid.
    """
    errors: List[str] = []
    if not isinstance(data, dict):
        return False, ["Payload must be a dictionary"]

    # Top-level required keys
    required_top_keys = ["week_id", "week_start", "week_end", "macro_target", "cart_summary", "days"]
    for key in required_top_keys:
        if key not in data:
            errors.append(f"Missing top-level required key: '{key}'")

    if errors:
        return False, errors

    # Check macro_target
    target = data.get("macro_target", {})
    if not isinstance(target, dict):
        errors.append("macro_target must be a dictionary")
    else:
        for m_key in ["kcal", "carbs_g", "proteins_g", "fats_g"]:
            if m_key not in target or not isinstance(target[m_key], (int, float)):
                errors.append(f"macro_target must contain numeric '{m_key}'")

    # Check cart_summary
    cart = data.get("cart_summary", {})
    if not isinstance(cart, dict):
        errors.append("cart_summary must be a dictionary")
    else:
        for c_key in ["total_estimated_eur", "items_count", "cart_url"]:
            if c_key not in cart:
                errors.append(f"cart_summary missing key '{c_key}'")

    # Check days
    days = data.get("days", [])
    if not isinstance(days, list):
        errors.append("days must be a list")
    elif len(days) != 7:
        errors.append(f"days list must contain exactly 7 days, found {len(days)}")
    else:
        expected_slots = ["colazione", "pranzo", "spuntino_pomeriggio", "cena", "dopocena"]
        for idx, day in enumerate(days):
            if not isinstance(day, dict):
                errors.append(f"Day index {idx} must be a dictionary")
                continue
            for d_key in ["day_name", "date", "meals"]:
                if d_key not in day:
                    errors.append(f"Day index {idx} missing '{d_key}'")
            
            meals = day.get("meals", {})
            if not isinstance(meals, dict):
                errors.append(f"Day index {idx} 'meals' must be a dictionary")
                continue
            
            for slot in expected_slots:
                if slot not in meals:
                    errors.append(f"Day '{day.get('day_name', idx)}' missing meal slot '{slot}'")
                else:
                    meal = meals[slot]
                    if not isinstance(meal, dict):
                        errors.append(f"Meal '{slot}' in day '{day.get('day_name')}' must be a dictionary")
                    else:
                        for m_field in ["title", "kcal", "macros", "ingredients", "recipe_steps"]:
                            if m_field not in meal:
                                errors.append(f"Meal '{slot}' missing required field '{m_field}'")
                        if not isinstance(meal.get("ingredients", None), list):
                            errors.append(f"Meal '{slot}' ingredients must be a list")
                        if not isinstance(meal.get("recipe_steps", None), list) or len(meal.get("recipe_steps", [])) == 0:
                            errors.append(f"Meal '{slot}' recipe_steps must be a non-empty list")

    return (len(errors) == 0), errors


def validate_nutritional_integrity(data: Dict[str, Any], tolerance_percent: float = 0.03) -> Tuple[bool, List[str]]:
    """
    Validates that a weekly plan conforms to Dr. Caglioni's bromatological targets
    and the 14 main meal protein distributions.
    """
    errors: List[str] = []
    target = data.get("macro_target", AUTHORITATIVE_TARGET)
    target_kcal = target.get("kcal", 2063)
    target_p = target.get("proteins_g", 112)
    target_c = target.get("carbs_g", 251)
    target_f = target.get("fats_g", 68)

    protein_counts = {k: 0 for k in AUTHORITATIVE_PROTEIN_FREQUENCIES}

    for day in data.get("days", []):
        day_name = day.get("day_name", "Unknown")
        meals = day.get("meals", {})
        
        day_kcal = 0
        day_p = 0
        day_c = 0
        day_f = 0

        for slot_name in ["colazione", "pranzo", "spuntino_pomeriggio", "cena", "dopocena"]:
            meal = meals.get(slot_name, {})
            kcal = meal.get("kcal", 0)
            macros = meal.get("macros", {})
            p = macros.get("proteins_g", 0)
            c = macros.get("carbs_g", 0)
            f = macros.get("fats_g", 0)

            day_kcal += kcal
            day_p += p
            day_c += c
            day_f += f

            # Track protein categories for Pranzo and Cena (14 main meals)
            if slot_name in ["pranzo", "cena"]:
                raw_cat = meal.get("category", "")
                cat = normalize_category(raw_cat, meal.get("is_free_meal", False))
                if cat in protein_counts:
                    protein_counts[cat] += 1
                else:
                    errors.append(f"Main meal '{slot_name}' on {day_name} has invalid protein category '{raw_cat}'")

        # Check daily deviation against target
        kcal_diff = abs(day_kcal - target_kcal) / target_kcal
        if kcal_diff > tolerance_percent:
            errors.append(f"{day_name} calories ({day_kcal}) deviate from target ({target_kcal}) by {kcal_diff*100:.1f}%")

    # Check 14-meal protein rotation
    for cat, expected_qty in AUTHORITATIVE_PROTEIN_FREQUENCIES.items():
        actual_qty = protein_counts.get(cat, 0)
        if actual_qty != expected_qty:
            errors.append(f"Protein category '{cat}': expected {expected_qty} meals in week, got {actual_qty}")

    return (len(errors) == 0), errors


def validate_telegram_alert_html(html_text: str) -> Tuple[bool, List[str]]:
    """
    Validates Contract 3: HTML message dispatched to send_alert.py.
    """
    errors: List[str] = []
    if not html_text or not isinstance(html_text, str):
        return False, ["Alert text must be a non-empty string"]

    # Must contain HTML bold tags
    if "<b>" not in html_text or "</b>" not in html_text:
        errors.append("Alert text must use HTML <b> formatting")

    # Must mention Esselunga or Spesa
    if "esselunga" not in html_text.lower() and "spesa" not in html_text.lower():
        errors.append("Alert text must mention 'Esselunga' or 'Spesa'")

    # Must contain an estimated amount or currency symbol
    if "€" not in html_text and "eur" not in html_text.lower():
        errors.append("Alert text must include estimated cost (€)")

    # Must contain a link or dashboard reference
    if "http://" not in html_text and "https://" not in html_text and "vercel" not in html_text.lower():
        errors.append("Alert text must contain a link to the dashboard")

    return (len(errors) == 0), errors
