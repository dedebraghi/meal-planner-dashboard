import math
from pathlib import Path
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = PROJECT_ROOT / "public" / "icons"
ICONS_DIR.mkdir(parents=True, exist_ok=True)

# Brand colors
BG_SAGE = (74, 107, 83)       # #4A6B53
BG_WARM = (250, 249, 246)     # #FAF9F6
ACCENT_GOLD = (212, 163, 115) # #D4A373
WHITE = (255, 255, 255)
TERRACOTTA = (194, 94, 63)    # #C25E3F

def create_brand_icon(size: int, maskable: bool = False) -> Image.Image:
    """
    Creates an artisanal brand icon.
    For maskable=True, safe zone is inner 80% circle (padding of 10% on all sides).
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if maskable:
        # Full solid background filling entire canvas (Android crops it)
        draw.rectangle([0, 0, size, size], fill=BG_SAGE)
    else:
        # Rounded squircle for standalone icon
        corner_r = int(size * 0.22)
        draw.rounded_rectangle([0, 0, size, size], radius=corner_r, fill=BG_SAGE)

    # Scale factor based on size and maskable safe zone
    scale = size / 512.0 * (0.75 if maskable else 0.88)
    cx, cy = size / 2.0, size / 2.0

    # Draw inner subtle gold ring
    ring_r = int(190 * scale)
    draw.ellipse(
        [cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r],
        outline=(255, 255, 255, 60),
        width=max(2, int(4 * scale))
    )

    # Draw stylized cloche / dome cover
    # 1. Knob on top of cloche
    knob_r = int(18 * scale)
    knob_y = cy - int(95 * scale)
    draw.ellipse(
        [cx - knob_r, knob_y - knob_r, cx + knob_r, knob_y + knob_r],
        fill=WHITE
    )

    # 2. Cloche dome (upper half ellipse)
    dome_w = int(140 * scale)
    dome_h = int(100 * scale)
    dome_bottom = cy + int(10 * scale)
    draw.pieslice(
        [cx - dome_w, dome_bottom - dome_h * 2, cx + dome_w, dome_bottom],
        start=0,
        end=180,
        fill=WHITE
    )

    # 3. Serving platter base line
    platter_w = int(175 * scale)
    platter_h = int(14 * scale)
    draw.rounded_rectangle(
        [cx - platter_w, dome_bottom, cx + platter_w, dome_bottom + platter_h],
        radius=int(6 * scale),
        fill=WHITE
    )

    # 4. Stylized green leaf / sprout on top symbolizing organic nutrition
    leaf_w = int(24 * scale)
    leaf_h = int(36 * scale)
    leaf_cx = cx + int(18 * scale)
    leaf_cy = knob_y - int(24 * scale)
    draw.ellipse(
        [leaf_cx - leaf_w, leaf_cy - leaf_h, leaf_cx + leaf_w, leaf_cy + leaf_h],
        fill=ACCENT_GOLD
    )

    # 5. Small subtle decorative stars / sparkles (nutritional excellence)
    sparkle_x = cx - int(110 * scale)
    sparkle_y = cy - int(55 * scale)
    sp_r = int(8 * scale)
    draw.ellipse([sparkle_x - sp_r, sparkle_y - sp_r, sparkle_x + sp_r, sparkle_y + sp_r], fill=ACCENT_GOLD)

    return img.convert("RGBA")

def generate_all_icons():
    print(f"Generating PWA icons in {ICONS_DIR}...")
    
    # 1. 192x192 regular
    icon_192 = create_brand_icon(192, maskable=False)
    icon_192.save(ICONS_DIR / "icon-192.png", format="PNG")
    print("  Created icon-192.png")

    # 2. 192x192 maskable
    icon_192_m = create_brand_icon(192, maskable=True)
    icon_192_m.save(ICONS_DIR / "icon-192-maskable.png", format="PNG")
    print("  Created icon-192-maskable.png")

    # 3. 512x512 regular
    icon_512 = create_brand_icon(512, maskable=False)
    icon_512.save(ICONS_DIR / "icon-512.png", format="PNG")
    print("  Created icon-512.png")

    # 4. 512x512 maskable
    icon_512_m = create_brand_icon(512, maskable=True)
    icon_512_m.save(ICONS_DIR / "icon-512-maskable.png", format="PNG")
    print("  Created icon-512-maskable.png")

    # 5. Apple Touch Icon (180x180)
    apple_icon = create_brand_icon(180, maskable=False)
    apple_icon.save(ICONS_DIR / "apple-touch-icon.png", format="PNG")
    print("  Created apple-touch-icon.png")

    # 6. Favicon PNG (32x32)
    fav_32 = create_brand_icon(32, maskable=False)
    fav_32.save(ICONS_DIR / "favicon-32x32.png", format="PNG")
    
    # Also save favicon.ico in public/
    fav_ico = create_brand_icon(48, maskable=False)
    fav_ico.save(PROJECT_ROOT / "public" / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print("  Created favicon.ico in public/")

    print("All PWA icons successfully generated!")

if __name__ == "__main__":
    generate_all_icons()
