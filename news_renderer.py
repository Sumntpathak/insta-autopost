"""Pubity-style high-impact 4:5 Instagram news card renderer.

Produces 1080x1350 single-image editorial posts with:
- High-contrast visual framing
- Distinctive branded header badge ('SHIPSTACK NEWS')
- High-readability bold headline and deck over dynamic gradient
- Clean source attribution
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1080, 1350


def get_font(size, bold=True):
    font_candidates = [
        "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in font_candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def create_dynamic_background(topic="tech", base_color=(12, 22, 38)):
    """Generates a high-quality abstract editorial background when no custom image is supplied."""
    bg = Image.new("RGB", (W, H), base_color)
    d = ImageDraw.Draw(bg)
    
    # Modern subtle ambient circles/glows
    glow1 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_glow1 = ImageDraw.Draw(glow1)
    d_glow1.ellipse((W * 0.3, H * 0.1, W * 1.2, H * 0.7), fill=(20, 80, 140, 90))
    d_glow1.ellipse((-W * 0.2, H * 0.4, W * 0.6, H * 1.1), fill=(10, 130, 120, 75))
    
    glow1 = glow1.filter(ImageFilter.GaussianBlur(120))
    bg.paste(glow1, (0, 0), glow1)
    
    # Subtle modern grid lines
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_grid = ImageDraw.Draw(grid)
    for x in range(0, W, 90):
        d_grid.line((x, 0, x, H), fill=(255, 255, 255, 8), width=1)
    for y in range(0, H, 90):
        d_grid.line((0, y, W, y), fill=(255, 255, 255, 8), width=1)
        
    bg.paste(grid, (0, 0), grid)
    return bg


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        trial = " ".join(current_line + [word])
        if draw.textlength(trial, font=font) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def render_pubity_card(headline, deck, source, category="TECH & AI", bg_image_path=None, output_path="out.jpg"):
    """Renders a 1080x1350 Pubity-style editorial news graphic."""
    if bg_image_path and Path(bg_image_path).exists():
        im = Image.open(bg_image_path).convert("RGB")
        scale = max(W / im.width, H / im.height)
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.Resampling.LANCZOS)
        x = (im.width - W) // 2
        y = (im.height - H) // 2
        bg = im.crop((x, y, x + W, y + H))
        bg = ImageEnhance.Contrast(bg).enhance(1.1)
    else:
        bg = create_dynamic_background()

    # Dark overlay for maximum contrast and punch
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Top header bar (translucent dark gradient)
    draw.rectangle((0, 0, W, 220), fill=(5, 10, 20, 180))

    # Bottom content card (solid dark with smooth gradient transition)
    draw.rectangle((0, 720, W, H), fill=(6, 12, 22, 235))
    
    # Smooth gradient bridge
    for i in range(120):
        alpha = int(235 * (i / 120))
        y = 600 + i
        draw.line((0, y, W, y), fill=(6, 12, 22, alpha))

    # Accent divider line (vibrant cyan/teal)
    draw.line((64, 720, W - 64, 720), fill=(0, 229, 255, 255), width=4)

    # 1. Top Badges
    # Branded Pill
    draw.rounded_rectangle((64, 60, 360, 120), radius=18, fill=(0, 229, 255, 255))
    draw.text((88, 74), "SHIPSTACK NEWS", font=get_font(26, bold=True), fill=(6, 15, 26, 255))

    # Category & Verified indicator
    category_text = f"VERIFIED  ·  {category.upper()}"
    draw.text((64, 150), category_text, font=get_font(22, bold=True), fill=(0, 229, 255, 220))

    # 2. Main Headline (Bold, high-impact)
    font_h = get_font(56, bold=True)
    lines = wrap_text(draw, headline, font_h, max_width=940)
    
    # Cap to max 4 lines
    lines = lines[:4]
    y_text = 760
    for line in lines:
        # Subtle drop shadow
        draw.text((66, y_text + 2), line, font=font_h, fill=(0, 0, 0, 180))
        draw.text((64, y_text), line, font=font_h, fill=(255, 255, 255, 255))
        y_text += 70

    # 3. Deck / Subheadline
    if deck:
        y_text += 16
        font_d = get_font(28, bold=False)
        deck_lines = wrap_text(draw, deck, font_d, max_width=940)[:2]
        for line in deck_lines:
            draw.text((64, y_text), line, font=font_d, fill=(200, 218, 235, 255))
            y_text += 40

    # 4. Footer info & CTA
    footer_font = get_font(22, bold=False)
    draw.text((64, 1260), f"Source: {source}   ·   Full story & context in caption", font=footer_font, fill=(160, 185, 205, 240))
    draw.text((W - 250, 1260), "@shipstack_", font=get_font(22, bold=True), fill=(0, 229, 255, 240))

    # Composite & save
    final_img = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    final_img.save(output_path, "JPEG", quality=95, subsampling=0)
    return output_path


if __name__ == "__main__":
    out = render_pubity_card(
        headline="Anthropic Unveils Breakthrough Hybrid Architecture For Ultra-Fast AI Reasoning",
        deck="The new framework slashes inference costs by 65% while matching full frontier benchmark performance.",
        source="Reuters / Anthropic Research",
        category="ARTIFICIAL INTELLIGENCE",
        output_path="test_pubity.jpg"
    )
    print(f"Rendered test card to: {out}")
