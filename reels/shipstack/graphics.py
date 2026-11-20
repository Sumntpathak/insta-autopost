"""ShipStack brand graphics: logo, skill post, news card, ball (Pick One) graphic.

    python -m reels.shipstack.graphics --out reels/shipstack/brand_assets

Pure Pillow, no network, no posting. Uses reels/shipstack/brand.py for colour and fonts.
"""
import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import brand

SS = 2   # supersampling factor for crisp shapes


def font(path, size, variation=None):
    f = ImageFont.truetype(str(path), size)
    if variation:
        try:
            f.set_variation_by_name(variation)
        except Exception:
            pass
    return f


def serif(size):
    return font(brand.SERIF, size)


def sans(size, weight='Bold'):
    return font(brand.SANS, size, weight)


def mono(size, weight='Bold'):
    return font(brand.MONO, size, weight)


def wrap(draw, text, f, width):
    lines, line = [], ''
    for word in text.split():
        trial = (line + ' ' + word).strip()
        if draw.textlength(trial, font=f) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def shade(hex_color, k):
    r, g, b = brand.rgb(hex_color)
    return tuple(max(0, min(255, round(c * k))) for c in (r, g, b))


def draw_mark(img, cx, cy, size, color=brand.ACCENT, bg=None):
    """Three stacked isometric layers: 'ship' (the top layer is the deck) + 'stack'."""
    s = size * SS
    layer = Image.new('RGBA', (round(s * 1.0), round(s * 1.0)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = s, s
    half_w, half_h, gap = w * 0.5, h * 0.17, h * 0.2
    base = h * 0.62
    shades = [0.62, 0.82, 1.0]
    for i, k in enumerate(shades):
        cy_l = base - i * gap
        pts = [(w * 0.5, cy_l - half_h), (w * 0.5 + half_w * 0.96, cy_l), (w * 0.5, cy_l + half_h), (w * 0.5 - half_w * 0.96, cy_l)]
        fill = shade(color, k) if bg is None else (255, 255, 255, round(255 * k))
        d.polygon(pts, fill=fill)
    layer = layer.resize((size, size), Image.Resampling.LANCZOS)
    img.alpha_composite(layer, (round(cx - size / 2), round(cy - size / 2)))


def canvas(w, h, color):
    return Image.new('RGBA', (w, h), color)


def logo_assets(out):
    out.mkdir(parents=True, exist_ok=True)
    # Mark only (transparent)
    mark = canvas(1024, 1024, (0, 0, 0, 0))
    draw_mark(mark, 512, 512, 900)
    mark.save(out / 'logo-mark.png')
    # Horizontal lockups
    for name, bg, ink, accent in (('light', brand.PAPER, brand.INK, brand.ACCENT), ('dark', brand.INK, '#FFFFFF', '#8B85FF')):
        im = canvas(1600, 480, bg)
        draw_mark(im, 240, 240, 330, color=accent)
        d = ImageDraw.Draw(im)
        d.text((430, 110), 'ShipStack', font=serif(190), fill=ink)
        d.text((438, 372), 'AI & AUTOMATION, MADE SIMPLE', font=sans(36), fill=brand.MUTED if name == 'light' else '#98A2B3')
        im.convert('RGB').save(out / f'logo-lockup-{name}.png')
    # Profile avatar (circle-safe: mark centred with generous margin)
    av = canvas(1080, 1080, brand.ACCENT)
    draw_mark(av, 540, 597, 700, color='#FFFFFF', bg='white')
    av.convert('RGB').save(out / 'avatar-1080.png')


def chrome(im, tag, series):
    """Shared header/footer so every post is recognisable without the handle."""
    d = ImageDraw.Draw(im)
    w, h = im.size
    draw_mark(im, 118, 118, 90)
    d.text((176, 88), 'ShipStack', font=serif(52), fill=brand.INK)
    tag_font = sans(24)
    tw = d.textlength(tag, font=tag_font)
    d.rounded_rectangle((w - 84 - tw - 44, 84, w - 84, 140), 28, fill=brand.ACCENT)
    d.text((w - 84 - tw - 22, 96), tag, font=tag_font, fill='white')
    d.line((84, 176, w - 84, 176), fill=brand.RULE, width=3)
    d.line((84, h - 130, w - 84, h - 130), fill=brand.RULE, width=3)
    d.text((84, h - 100), series.upper(), font=sans(24), fill=brand.ACCENT)
    hf = sans(24)
    d.text((w - 84 - d.textlength(brand.HANDLE, font=hf), h - 100), brand.HANDLE, font=hf, fill=brand.MUTED)


def news_card(out, headline, deck, source, date, tag='AI'):
    im = canvas(1080, 1350, brand.PAPER)
    chrome(im, tag, 'ShipStack Brief')
    d = ImageDraw.Draw(im)
    d.text((84, 250), f'VERIFIED · {source.upper()}', font=mono(26), fill=brand.MUTED)
    y, f = 330, serif(104)
    for line in wrap(d, headline, f, 912):
        d.text((84, y), line, font=f, fill=brand.INK)
        y += 112
    y += 26
    d.rectangle((84, y, 84 + 120, y + 8), fill=brand.ACCENT)
    y += 52
    for line in wrap(d, deck, sans(38, 'Regular'), 912):
        d.text((84, y), line, font=sans(38, 'Regular'), fill=brand.MUTED)
        y += 54
    d.text((84, 1350 - 190), f'Source: {source} · {date}', font=mono(24, 'Regular'), fill=brand.MUTED)
    im.convert('RGB').save(out / 'news-card-sample.png')


def skill_card(out, title, steps, result):
    im = canvas(1080, 1350, brand.PAPER)
    chrome(im, 'SKILL', 'Skill of the Day')
    d = ImageDraw.Draw(im)
    y, f = 240, serif(96)
    for line in wrap(d, title, f, 912):
        d.text((84, y), line, font=f, fill=brand.INK)
        y += 102
    y += 60
    for i, step in enumerate(steps, 1):
        d.ellipse((84, y, 84 + 64, y + 64), fill=brand.ACCENT)
        n = str(i)
        d.text((84 + 32 - d.textlength(n, font=sans(34)) / 2, y + 12), n, font=sans(34), fill='white')
        sf = sans(36, 'SemiBold')
        for j, line in enumerate(wrap(d, step, sf, 780)):
            d.text((180, y + 8 + j * 46), line, font=sf, fill=brand.INK)
        y += 64 + 36 + 46 * (len(wrap(d, step, sf, 780)) - 1)
    box_top = max(y + 10, 930)
    d.rounded_rectangle((84, box_top, 996, box_top + 170), 24, fill='#F1F0FF')
    d.text((120, box_top + 26), 'RESULT', font=mono(24), fill=brand.ACCENT)
    for j, line in enumerate(wrap(d, result, sans(34, 'SemiBold'), 840)):
        d.text((120, box_top + 70 + j * 44), line, font=sans(34, 'SemiBold'), fill=brand.INK)
    d.text((84, 1350 - 190), 'Save this for later  ↓', font=sans(28), fill=brand.ACCENT)
    im.convert('RGB').save(out / 'post-skill-sample.png')


def ball_graphic(out):
    """'Pick One' cover: six numbered balls inside a ring with one gap."""
    W, H = 1080, 1350
    im = canvas(W * SS, H * SS, brand.PAPER)
    d = ImageDraw.Draw(im)
    cx, cy, R = W * SS // 2, 590 * SS, 360 * SS
    gap = (-38, 38)
    d.arc((cx - R, cy - R, cx + R, cy + R), gap[1], 360 + gap[0], fill=brand.INK, width=14 * SS)
    for ang in gap:
        x, y = cx + R * math.cos(math.radians(ang)), cy + R * math.sin(math.radians(ang))
        d.ellipse((x - 7 * SS, y - 7 * SS, x + 7 * SS, y + 7 * SS), fill=brand.INK)
    pos = [(-140, -110), (60, -210), (180, -10), (-80, 30), (100, 160), (-190, 180)]
    for i, (dx, dy) in enumerate(pos):
        x, y, r = cx + dx * SS, cy + dy * SS, 74 * SS
        d.ellipse((x - r, y - r, x + r, y + r), fill=brand.BALLS[i])
    im = im.resize((W, H), Image.Resampling.LANCZOS)
    d = ImageDraw.Draw(im)
    for i, (dx, dy) in enumerate(pos):   # numbers drawn after downscale for crisp text
        n = str(i + 1)
        d.text((W // 2 + dx - d.textlength(n, font=sans(68)) / 2, 590 + dy - 42), n, font=sans(68), fill='white')
    chrome(im, 'PICK ONE', 'Pick One')
    d = ImageDraw.Draw(im)
    d.text((84, 1000), 'Which ball escapes first?', font=serif(104), fill=brand.INK)
    d.text((84, 1128), 'Pick a number before you watch.', font=sans(38, 'Regular'), fill=brand.MUTED)
    im.convert('RGB').save(out / 'ball-pick-one.png')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='reels/shipstack/brand_assets')
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    logo_assets(out)
    news_card(out, 'Anthropic raises $81 billion in record IPO',
              'The AI company priced its public offering at $83 a share.', 'Reuters', '19 Nov 2026', 'AI')
    skill_card(out, 'Automate your weekly report',
               ['Export the numbers to a sheet', 'Ask Claude to draft the summary from it', 'Schedule it to send every Friday'],
               'A 90-minute weekly task now runs itself every Friday.')
    ball_graphic(out)
    print('Wrote', *sorted(p.name for p in out.glob('*.png')), sep='\n  ')


if __name__ == '__main__':
    main()
