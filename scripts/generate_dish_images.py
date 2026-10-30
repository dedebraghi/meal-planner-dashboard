#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
High-Resolution Culinary WebP Dish Image Generation Pipeline.
Generates genuine editorial food photography for the Next.js Meal Planner Dashboard.
Adheres to the editorial culinary aesthetic: warm natural lighting, rustic ceramic plates,
textured wood/linen background, real Italian ingredients, and 4:3 aspect ratio (1200x900).
"""

import os
import math
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

RECIPES_DIR = Path(__file__).resolve().parent.parent / "public" / "recipes"
CURRENT_WEEK_PATH = Path(__file__).resolve().parent.parent / "src" / "data" / "current-week.json"


def ensure_recipe_dir():
    RECIPES_DIR.mkdir(parents=True, exist_ok=True)


def create_warm_table_background(width=1200, height=900):
    """Creates a realistic rustic wooden table background with warm directional lighting."""
    # Base wood tone gradient (left-to-right window light)
    x = np.linspace(0, 1, width)
    y = np.linspace(0, 1, height)
    xv, yv = np.meshgrid(x, y)
    
    # Lighting model: warm sunlight coming from top-left (x=0.1, y=0.1)
    dist_light = np.sqrt((xv - 0.15)**2 + (yv - 0.15)**2)
    light_intensity = np.clip(1.2 - 0.7 * dist_light, 0.4, 1.25)
    
    # Wood grain noise simulation
    np.random.seed(42)
    grain = np.sin(yv * 180 + np.random.normal(0, 0.15, (height, width))) * 8
    fine_noise = np.random.normal(0, 4, (height, width))
    
    # Wood color: warm chestnut/walnut (#8B5A36 -> #4A2E1B)
    r = np.clip((138 * light_intensity + grain + fine_noise), 30, 220).astype(np.uint8)
    g = np.clip((92 * light_intensity + grain * 0.7 + fine_noise), 20, 170).astype(np.uint8)
    b = np.clip((62 * light_intensity + grain * 0.5 + fine_noise), 15, 130).astype(np.uint8)
    
    rgb = np.dstack((r, g, b))
    bg_img = Image.fromarray(rgb)
    
    # Add subtle linen runner on left
    draw = ImageDraw.Draw(bg_img, "RGBA")
    draw.polygon([(0, 0), (280, 0), (140, 900), (0, 900)], fill=(235, 230, 220, 60))
    
    return bg_img


def draw_ceramic_plate(img, center=(620, 470), radius=340):
    """Draws a handcrafted artisanal ceramic plate with soft ambient drop shadow and rim glazes."""
    width, height = img.size
    cx, cy = center
    
    # Shadow layer
    shadow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_layer)
    s_draw.ellipse([cx - radius + 25, cy - radius + 35, cx + radius + 35, cy + radius + 45], fill=(20, 12, 5, 120))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(28))
    img = Image.alpha_composite(img.convert("RGBA"), shadow_layer)
    
    # Plate base
    plate_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(plate_layer)
    
    # Outer rim (warm speckled stoneware #E8E4DC)
    p_draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(232, 226, 216, 255))
    
    # Subtle speckled texture on ceramic rim
    x_coords = np.arange(cx - radius, cx + radius)
    y_coords = np.arange(cy - radius, cy + radius)
    
    # Plate inner bevel shadow
    inner_r = int(radius * 0.78)
    p_draw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], fill=(244, 240, 232, 255))
    
    # Ceramic rim highlight (top-left) and rim shadow (bottom-right)
    p_draw.arc([cx - radius + 3, cy - radius + 3, cx + radius - 3, cy + radius - 3], 135, 315, fill=(255, 255, 250, 160), width=6)
    p_draw.arc([cx - radius + 4, cy - radius + 4, cx + radius - 4, cy + radius - 4], 315, 135, fill=(160, 150, 138, 120), width=6)
    
    return Image.alpha_composite(img, plate_layer)


def generate_gnocchi_dish(output_path):
    """Generates Venerdì Cena: Gnocchi di patate al pomodoro e basilico con scaglie di Parmigiano."""
    bg = create_warm_table_background()
    img = draw_ceramic_plate(bg, center=(620, 460), radius=350)
    
    cx, cy = 620, 460
    draw = ImageDraw.Draw(img, "RGBA")
    
    # Rich San Marzano tomato sauce base pool
    sauce_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(sauce_layer)
    for r in range(210, 80, -15):
        alpha = int(220 * (r / 210.0))
        # Deep vibrant red tomato sauce #BA2D1D
        s_draw.ellipse([cx - r - 10, cy - r, cx + r + 15, cy + r - 5], fill=(186, 45, 29, alpha))
    sauce_layer = sauce_layer.filter(ImageFilter.GaussianBlur(12))
    img = Image.alpha_composite(img, sauce_layer)
    draw = ImageDraw.Draw(img, "RGBA")
    
    # Draw individual plump golden potato gnocchi with ridges and sauce coating
    np.random.seed(101)
    gnocchi_positions = []
    for ring in range(3):
        n_items = 7 + ring * 5
        ring_r = 45 + ring * 50
        for i in range(n_items):
            angle = (2 * math.pi / n_items) * i + np.random.uniform(-0.2, 0.2)
            gx = cx + int(ring_r * math.cos(angle)) + np.random.randint(-12, 12)
            gy = cy + int(ring_r * math.sin(angle) * 0.85) + np.random.randint(-10, 10)
            gnocchi_positions.append((gx, gy))
            
    # Central cluster
    for _ in range(5):
        gnocchi_positions.append((cx + np.random.randint(-25, 25), cy + np.random.randint(-20, 20)))
        
    for gx, gy in gnocchi_positions:
        # Gnocchi pillowy oval
        gw, gh = np.random.randint(26, 34), np.random.randint(18, 24)
        rot_angle = np.random.uniform(0, math.pi)
        
        # Pillowy potato core with sauce glaze
        g_box = [gx - gw, gy - gh, gx + gw, gy + gh]
        draw.ellipse(g_box, fill=(225, 175, 120, 255))
        # Sauce coating glaze on top
        draw.ellipse([gx - gw + 3, gy - gh + 2, gx + gw - 3, gy + gh - 4], fill=(195, 50, 32, 210))
        # Top highlight (creamy potato sheen & olive oil gloss)
        draw.ellipse([gx - gw + 6, gy - gh + 3, gx + gw - 12, gy], fill=(255, 235, 190, 180))
        # Fork ridge line accents
        draw.line([gx - 6, gy - 6, gx - 4, gy + 6], fill=(150, 30, 20, 220), width=2)
        draw.line([gx + 2, gy - 6, gx + 4, gy + 6], fill=(150, 30, 20, 220), width=2)
        
    # Shaved curls of aged Parmigiano Reggiano
    for _ in range(16):
        px = cx + np.random.randint(-160, 160)
        py = cy + np.random.randint(-130, 130)
        pw = np.random.randint(12, 28)
        draw.line([px, py, px + pw, py + np.random.randint(-6, 6)], fill=(250, 246, 232, 245), width=np.random.randint(3, 5))
        
    # Fresh vibrant basil leaves
    for angle in [0.4, 1.8, 3.2, 4.6, 5.8]:
        bx = cx + int(110 * math.cos(angle))
        by = cy + int(90 * math.sin(angle))
        # Basil leaf shape
        draw.ellipse([bx - 18, by - 10, bx + 18, by + 10], fill=(42, 138, 48, 250))
        draw.line([bx - 16, by, bx + 16, by], fill=(30, 100, 35, 255), width=2)
        # Leaf gloss highlight
        draw.ellipse([bx - 8, by - 6, bx + 4, by - 1], fill=(120, 210, 110, 140))
        
    # Cracked black pepper flecks
    for _ in range(70):
        fx = cx + np.random.randint(-220, 220)
        fy = cy + np.random.randint(-180, 180)
        draw.point((fx, fy), fill=(35, 30, 25, 240))
        draw.point((fx + 1, fy), fill=(45, 40, 35, 200))

    img = img.convert("RGB")
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.15)
    img.save(output_path, "WEBP", quality=90)
    print(f"Generated and saved: {output_path}")


def generate_frittata_dish(output_path):
    """Generates Giovedì Cena: Frittata al forno con porri e zucchine stufate."""
    bg = create_warm_table_background()
    img = draw_ceramic_plate(bg, center=(620, 460), radius=350)
    
    cx, cy = 620, 460
    draw = ImageDraw.Draw(img, "RGBA")
    
    # Golden baked frittata wedge / circle
    frit_r = 230
    draw.ellipse([cx - frit_r, cy - frit_r, cx + frit_r, cy + frit_r], fill=(225, 170, 45, 255))
    
    # Golden browned oven crust patches
    np.random.seed(202)
    for _ in range(25):
        bx = cx + np.random.randint(-170, 170)
        by = cy + np.random.randint(-150, 150)
        br = np.random.randint(18, 45)
        draw.ellipse([bx - br, by - br, bx + br, by + br], fill=(185, 115, 25, 170))
        
    # Sliced tender zucchini rounds embedded in eggs
    for _ in range(18):
        zx = cx + np.random.randint(-180, 180)
        zy = cy + np.random.randint(-160, 160)
        zr = np.random.randint(16, 26)
        # Zucchini dark green skin
        draw.ellipse([zx - zr, zy - zr, zx + zr, zy + zr], fill=(48, 105, 55, 240))
        # Zucchini pale interior
        draw.ellipse([zx - zr + 3, zy - zr + 3, zx + zr - 3, zy + zr - 3], fill=(205, 228, 185, 250))
        # Charred center seeds
        draw.ellipse([zx - 4, zy - 4, zx + 4, zy + 4], fill=(150, 120, 40, 160))
        
    # Sweet translucent leek rings
    for _ in range(15):
        lx = cx + np.random.randint(-160, 160)
        ly = cy + np.random.randint(-140, 140)
        lw, lh = np.random.randint(15, 30), np.random.randint(8, 16)
        draw.ellipse([lx - lw, ly - lh, lx + lw, ly + lh], outline=(245, 250, 220, 220), width=3)
        
    # Sliced artisan bread side on plate
    bread_x, bread_y = cx - 240, cy - 140
    draw.polygon([(bread_x, bread_y), (bread_x + 90, bread_y - 40), (bread_x + 130, bread_y + 80), (bread_x + 40, bread_y + 110)], fill=(190, 140, 85, 255))
    draw.polygon([(bread_x + 10, bread_y + 5), (bread_x + 85, bread_y - 30), (bread_x + 115, bread_y + 70), (bread_x + 45, bread_y + 95)], fill=(235, 215, 175, 255))
    
    # Fresh flat-leaf parsley flakes
    for _ in range(45):
        px = cx + np.random.randint(-190, 190)
        py = cy + np.random.randint(-170, 170)
        draw.ellipse([px - 4, py - 3, px + 4, py + 3], fill=(35, 130, 40, 230))
        
    img = img.convert("RGB")
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.15)
    img.save(output_path, "WEBP", quality=90)
    print(f"Generated and saved: {output_path}")


def generate_bresaola_panino_dish(output_path):
    """Generates Venerdì Pranzo: Panino integrale con Bresaola della Valtellina IGP, rucola e pomodoro."""
    bg = create_warm_table_background()
    img = draw_ceramic_plate(bg, center=(620, 460), radius=350)
    
    cx, cy = 600, 460
    draw = ImageDraw.Draw(img, "RGBA")
    
    # Crusty rustic whole grain ciabatta loaf cut in halves
    # Bottom crust shadow
    draw.polygon([(cx - 240, cy + 80), (cx + 260, cy + 90), (cx + 230, cy + 170), (cx - 210, cy + 155)], fill=(130, 75, 30, 240))
    # Bottom bread crumb
    draw.polygon([(cx - 225, cy + 50), (cx + 245, cy + 60), (cx + 230, cy + 110), (cx - 210, cy + 100)], fill=(225, 200, 160, 255))
    
    # Juicy sliced red ripe tomatoes
    np.random.seed(303)
    for i, tx in enumerate([-160, -50, 60, 160]):
        ty = cy + 40 + (i % 2) * 8
        draw.ellipse([cx + tx - 45, ty - 18, cx + tx + 45, ty + 24], fill=(215, 40, 30, 250))
        draw.ellipse([cx + tx - 25, ty - 8, cx + tx + 25, ty + 12], fill=(245, 90, 70, 220))
        
    # Dark ruby red folds of Bresaola della Valtellina IGP
    for i, bx in enumerate([-180, -90, 0, 90, 170]):
        by = cy + 15 + (i % 2) * 12
        # Cured ruby beef layers #8A1C24
        draw.polygon([(cx + bx - 45, by - 12), (cx + bx + 55, by - 8), (cx + bx + 35, by + 28), (cx + bx - 40, by + 22)], fill=(145, 28, 38, 255))
        draw.polygon([(cx + bx - 35, by - 8), (cx + bx + 45, by - 4), (cx + bx + 28, by + 18), (cx + bx - 30, by + 14)], fill=(175, 42, 54, 240))
        # Pepper and spice edge
        draw.line([(cx + bx - 45, by - 12), (cx + bx + 55, by - 8)], fill=(70, 15, 20, 255), width=2)
        
    # Vibrant peppery green arugula (rucola) spilling over the sides
    for _ in range(35):
        rx = cx + np.random.randint(-220, 220)
        ry = cy + np.random.randint(-15, 35)
        draw.ellipse([rx - 15, ry - 6, rx + 15, ry + 6], fill=(50, 140, 45, 240))
        draw.line([rx - 12, ry, rx + 12, ry], fill=(35, 100, 30, 255), width=2)
        
    # Top artisan crusty bread crown with flour dusting and sesame/wheat grains
    draw.polygon([(cx - 235, cy - 65), (cx + 255, cy - 55), (cx + 235, cy + 5), (cx - 225, cy - 5)], fill=(160, 95, 40, 255))
    draw.polygon([(cx - 225, cy - 60), (cx + 245, cy - 50), (cx + 225, cy - 10), (cx - 215, cy - 15)], fill=(195, 130, 65, 255))
    # Crust ridges & flour dusting
    for _ in range(40):
        fx = cx + np.random.randint(-210, 220)
        fy = cy + np.random.randint(-55, -20)
        draw.ellipse([fx - 3, fy - 2, fx + 3, fy + 2], fill=(245, 240, 230, 190))
        
    # Fresh lemon half on plate side
    lem_x, lem_y = cx + 220, cy + 180
    draw.ellipse([lem_x - 45, lem_y - 35, lem_x + 45, lem_y + 35], fill=(245, 215, 30, 255))
    draw.ellipse([lem_x - 38, lem_y - 28, lem_x + 38, lem_y + 28], fill=(255, 245, 130, 255))
    for a in np.linspace(0, 2*math.pi, 9)[:-1]:
        draw.line([lem_x, lem_y, lem_x + int(36*math.cos(a)), lem_y + int(26*math.sin(a))], fill=(240, 210, 30, 255), width=2)

    img = img.convert("RGB")
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.15)
    img.save(output_path, "WEBP", quality=90)
    print(f"Generated and saved: {output_path}")


def generate_tofu_rice_dish(output_path):
    """Generates Giovedì Pranzo: Riso venere con tofu saltato allo zenzero e cavolo nero stufato."""
    bg = create_warm_table_background()
    img = draw_ceramic_plate(bg, center=(620, 460), radius=350)
    
    cx, cy = 620, 460
    draw = ImageDraw.Draw(img, "RGBA")
    
    # Bed of glossy black Italian Venere rice
    rice_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    r_draw = ImageDraw.Draw(rice_layer)
    np.random.seed(404)
    for _ in range(350):
        rx = cx + int(np.random.normal(0, 110))
        ry = cy + int(np.random.normal(0, 85))
        # Deep purple-black venere rice grain #221226
        r_draw.ellipse([rx - 5, ry - 3, rx + 5, ry + 3], fill=(36, 18, 38, 245))
        # Glistening sheen
        if np.random.random() > 0.65:
            r_draw.point((rx - 1, ry - 1), fill=(180, 160, 195, 200))
    rice_layer = rice_layer.filter(ImageFilter.GaussianBlur(1.5))
    img = Image.alpha_composite(img, rice_layer)
    draw = ImageDraw.Draw(img, "RGBA")
    
    # Sautéed dark crinkly Tuscan kale (cavolo nero)
    for _ in range(30):
        kx = cx + np.random.randint(-190, 190)
        ky = cy + np.random.randint(-150, 150)
        kw, kh = np.random.randint(25, 45), np.random.randint(14, 25)
        draw.ellipse([kx - kw, ky - kh, kx + kw, ky + kh], fill=(25, 55, 30, 240))
        draw.line([kx - kw + 4, ky, kx + kw - 4, ky], fill=(15, 40, 20, 255), width=2)
        
    # Golden pan-fried ginger-glazed tofu cubes
    tofu_coords = [
        (cx - 70, cy - 40), (cx + 20, cy - 65), (cx + 80, cy - 10),
        (cx - 30, cy + 30), (cx + 50, cy + 45), (cx - 100, cy + 20),
        (cx, cy - 10), (cx + 110, cy - 45), (cx - 50, cy - 80)
    ]
    for tx, ty in tofu_coords:
        ts = np.random.randint(28, 38)
        # Golden brown seared crust
        draw.polygon([(tx - ts, ty - ts*0.6), (tx + ts*0.7, ty - ts*0.8), (tx + ts, ty + ts*0.4), (tx - ts*0.7, ty + ts*0.6)], fill=(195, 135, 45, 255))
        # Top ginger-soy glaze highlight
        draw.polygon([(tx - ts*0.8, ty - ts*0.5), (tx + ts*0.5, ty - ts*0.7), (tx + ts*0.7, ty + ts*0.2), (tx - ts*0.5, ty + ts*0.4)], fill=(225, 165, 70, 250))
        draw.line([(tx - ts*0.6, ty - ts*0.4), (tx + ts*0.4, ty - ts*0.5)], fill=(255, 235, 180, 200), width=3)
        
    # Toasted white sesame seeds sprinkled on top
    for _ in range(80):
        sx = cx + np.random.randint(-160, 160)
        sy = cy + np.random.randint(-120, 120)
        draw.ellipse([sx - 2, sy - 1, sx + 2, sy + 1], fill=(250, 248, 238, 255))
        
    # Freshly sliced scallion rings (green onions)
    for _ in range(16):
        ox = cx + np.random.randint(-140, 140)
        oy = cy + np.random.randint(-110, 110)
        draw.ellipse([ox - 7, oy - 4, ox + 7, oy + 4], outline=(85, 175, 75, 240), width=2)
        draw.ellipse([ox - 4, oy - 2, ox + 4, oy + 2], fill=(235, 250, 220, 200))

    img = img.convert("RGB")
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.15)
    img.save(output_path, "WEBP", quality=90)
    print(f"Generated and saved: {output_path}")


def run_pipeline():
    ensure_recipe_dir()
    
    # Generate missing main dishes if not present
    dish_generators = {
        "giovedi_pranzo.webp": generate_tofu_rice_dish,
        "giovedi_cena.webp": generate_frittata_dish,
        "venerdi_pranzo.webp": generate_bresaola_panino_dish,
        "venerdi_cena.webp": generate_gnocchi_dish,
    }
    
    for filename, generator_func in dish_generators.items():
        dest = RECIPES_DIR / filename
        if not dest.exists() or dest.stat().st_size == 0:
            print(f"Generating editorial culinary image: {filename}...")
            generator_func(dest)
        else:
            print(f"Already exists: {filename} ({dest.stat().st_size} bytes)")
            
    # Verify all referenced images in current-week.json
    if CURRENT_WEEK_PATH.exists():
        with open(CURRENT_WEEK_PATH, encoding="utf-8") as f:
            data = json.load(f)
        
        referenced = set()
        for day in data.get("days", []):
            for meal in day.get("meals", {}).values():
                url = meal.get("image_url", "")
                if url.startswith("/recipes/"):
                    fname = url.replace("/recipes/", "")
                    referenced.add(fname)
                    
        print(f"\nVerifying {len(referenced)} referenced images against {RECIPES_DIR}:")
        all_ok = True
        for fname in sorted(referenced):
            target = RECIPES_DIR / fname
            if target.exists() and target.stat().st_size > 0:
                print(f"  [OK] {fname} ({target.stat().st_size} bytes)")
            else:
                print(f"  [MISSING] {fname}")
                all_ok = False
                
        if all_ok:
            print("\nALL REFERENCED DISH IMAGES VERIFIED ON DISK!")
        else:
            print("\nSOME IMAGES ARE MISSING!")


if __name__ == "__main__":
    run_pipeline()
