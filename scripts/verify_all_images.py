import json
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECIPES_DIR = PROJECT_ROOT / "public" / "recipes"
JSON_PATH = PROJECT_ROOT / "src" / "data" / "current-week.json"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"{'DAY':<10} | {'MEAL':<8} | {'IMAGE FILE':<22} | {'DIMENSIONS':<12} | {'SIZE':<9} | {'RECIPE TITLE'}")
print("-" * 110)

all_ok = True
for day in data["days"]:
    for meal_key in ["pranzo", "cena"]:
        m = day["meals"][meal_key]
        img_url = m.get("image_url")
        filename = Path(img_url).name
        file_path = RECIPES_DIR / filename
        
        if not file_path.exists():
            print(f"MISSING: {filename}")
            all_ok = False
            continue
            
        with Image.open(file_path) as im:
            w, h = im.size
            size_kb = file_path.stat().st_size / 1024
            dim_str = f"{w}x{h}"
            size_str = f"{size_kb:.1f} KB"
            title = m.get("title", "")[:45]
            print(f"{day['day_name']:<10} | {meal_key:<8} | {filename:<22} | {dim_str:<12} | {size_str:<9} | {title}")

print("-" * 110)
print(f"All 14 dish images verified: {all_ok}")
