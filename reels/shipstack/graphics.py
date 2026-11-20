"""ShipStack brand graphics v2: dark, high-contrast, built for the phone feed.

    python -m reels.shipstack.graphics --out reels/shipstack/brand_assets

Formats (all 1080x1350, Instagram 4:5):
  - post card     : the "post screenshot" news format big news pages use, as OUR post
                    (own avatar and handle; no platform logos, no verification badge)
  - photo card    : full-bleed photo, bold headline with a highlighted phrase
  - skill card    : post-style numbered steps people save
  - ball cover    : Pick One hook for the simulation reels
plus the logo: ">_" avatar and the "shipstack_" wordmark (matches the handle).

Text in [brackets] is drawn in the accent colour. Pure Pillow; no network, no posting.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import brand

W, H = 1080, 1350
BG = (10, 10, 10)
SURFACE = (22, 24, 28)
TEXT = (247, 249, 249)
GREY = (139, 152, 165)
LINE = (47, 51, 54)
ACCENT = (215, 255, 58)          # signal lime: readable on black, rare in the tech feed
ACCENT_INK = (10, 10, 10)
SS = 2


def inter(size, weight=700):
    f = ImageFont.truetype(str(brand.SANS), size)
    try:
        f.set_variation_by_axes([min(32, max(14, size)), weight])
    except Exception:
        pass
    return f


def mono(size, weight=700):
    f = ImageFont.truetype(str(brand.MONO), size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


# ---------- rich text: [highlighted] words ----------
def tokens(text):
    out, hot = [], False
    for word in text.split():
        if word.startswith('['):
            hot = True
        out.append((word.replace('[', '').replace(']', ''), hot))
        if word.rstrip('.,:;!?').endswith(']'):
            hot = False
    return out


def layout(draw, text, f, width):
    lines, line, x = [], [], 0
    space = draw.textlength(' ', font=f)
    for word, hot in tokens(text):
        w = draw.textlength(word, font=f)
        if line and x + space + w > width:
            lines.append(line)
            line, x = [], 0
        x += (space if line else 0) + w
        line.append((word, hot))
    if line:
        lines.append(line)
    return lines


def rich(draw, xy, text, f, width, leading, color=TEXT, hot_color=ACCENT, mark=False):
    """Draw wrapped text; [words] in the accent. mark=True draws highlighter blocks instead."""
    x0, y = xy
    space = draw.textlength(' ', font=f)
    asc, desc = f.getmetrics()
    for line in layout(draw, text, f, width):
        x = x0
        for i, (word, hot) in enumerate(line):
            w = draw.textlength(word, font=f)
            if hot and mark:
                nxt = i + 1 < len(line) and line[i + 1][1]
                draw.rectangle((x - 10, y + asc * 0.12, x + w + (space if nxt else 0) + 10, y + asc + desc * 0.5), fill=hot_color)
                draw.text((x, y), word, font=f, fill=ACCENT_INK)
            else:
                draw.text((x, y), word, font=f, fill=hot_color if hot else color)
            x += w + space
        y += leading
    return y


# ---------- logo ----------
def avatar(size, bg=ACCENT, fg=ACCENT_INK, circle=False):
    s = size * SS
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if circle:
        d.ellipse((0, 0, s - 1, s - 1), fill=bg)
    else:
        d.rounded_rectangle((0, 0, s - 1, s - 1), radius=round(s * 0.22), fill=bg)
    f = mono(round(s * 0.42), 800)
    l, t, r, b = d.textbbox((0, 0), '>_', font=f)
    d.text(((s - (r - l)) / 2 - l, (s - (b - t)) / 2 - t), '>_', font=f, fill=fg)
    return im.resize((size, size), Image.Resampling.LANCZOS)


def wordmark(d, xy, size, color=TEXT):
    f = inter(size, 900)
    d.text(xy, 'shipstack', font=f, fill=color)
    asc, _ = f.getmetrics()
    x = xy[0] + d.textlength('shipstack', font=f) + size * 0.05
    base = xy[1] + asc
    d.rectangle((x, base - size * 0.12, x + size * 0.46, base), fill=ACCENT)


def logo_assets(out):
    avatar(1080).save(out / 'logo-mark.png')
    profile = Image.new('RGBA', (1080, 1080), ACCENT + (255,))     # full square: Instagram crops it to a circle
    profile.alpha_composite(avatar(1080))
    profile.convert('RGB').save(out / 'avatar-1080.png')
    for name, bg, fg in (('dark', BG, TEXT), ('light', (255, 255, 255), BG)):
        im = Image.new('RGBA', (1600, 480), bg)
        im.alpha_composite(avatar(300), (90, 90))
        d = ImageDraw.Draw(im)
        wordmark(d, (450, 120), 170, fg)
        d.text((456, 330), 'AI & automation, made simple', font=inter(44, 500), fill=GREY)
        im.convert('RGB').save(out / f'logo-lockup-{name}.png')


# ---------- shared pieces ----------
def cover(img, w, h):
    scale = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def rounded(img, radius):
    mask = Image.new('L', img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius, fill=255)
    out = img.convert('RGBA')
    out.putalpha(mask)
    return out


def vgrad(w, h, start, end, a0, a1):
    g = Image.new('L', (1, h))
    for y in range(h):
        t = min(1.0, max(0.0, (y - start) / max(1, end - start)))
        g.putpixel((0, y), round(a0 + (a1 - a0) * t))
    return g.resize((w, h))


def author(im, d, x, y, date):
    im.alpha_composite(avatar(96, circle=True), (x, y))
    d.text((x + 120, y + 8), 'ShipStack', font=inter(38, 800), fill=TEXT)
    d.text((x + 120, y + 54), f'@shipstack_ · {date}', font=inter(30, 400), fill=GREY)


# ---------- formats ----------
def post_card(path, text, date, source, image=None, credit=None):
    """News as our own post: avatar, handle, big text, optional photo, source line."""
    im = Image.new('RGBA', (W, H), BG)
    d = ImageDraw.Draw(im)
    x, width = 72, W - 144
    f = inter(56, 600)
    lines = len(layout(d, text, f, width))
    photo_h = 470 if image else 0
    block = 136 + lines * 74 + (30 + photo_h if image else 0) + 70
    y = max(90, (H - 90 - block) // 2)
    author(im, d, x, y, date)
    y = rich(d, (x, y + 136), text, f, width, 74)
    if image:
        photo = rounded(cover(Image.open(image).convert('RGB'), width, photo_h), 28)
        im.alpha_composite(photo, (x, y + 30))
        d.rounded_rectangle((x, y + 30, x + width, y + 30 + photo_h), 28, outline=LINE, width=2)
        y += 30 + photo_h
    d.text((x, y + 30), f'Source: {source}' + (f'  ·  Image: {credit}' if credit else ''), font=inter(28, 400), fill=GREY)
    d.line((x, H - 110, x + width, H - 110), fill=LINE, width=2)
    d.text((x, H - 80), 'Daily AI news you can save', font=inter(28, 600), fill=GREY)
    d.text((x + width - d.textlength('Follow ↗', font=inter(28, 700)), H - 80), 'Follow ↗', font=inter(28, 700), fill=ACCENT)
    im.convert('RGB').save(path, quality=95)


def photo_card(path, kicker, headline, source, date, image, credit=None):
    """Full-bleed photo, dark gradient, bold headline with a highlighted phrase."""
    im = cover(Image.open(image).convert('RGB'), W, H).convert('RGBA')
    shade = Image.new('RGBA', (W, H), BG + (255,))
    shade.putalpha(vgrad(W, H, int(H * 0.30), int(H * 0.78), 0, 250))
    im.alpha_composite(shade)
    top = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    top.putalpha(vgrad(W, H, 0, 240, 150, 0))
    im.alpha_composite(top)
    d = ImageDraw.Draw(im)
    im.alpha_composite(avatar(64), (64, 60))
    wordmark(d, (148, 64), 44)
    f = inter(92, 900)
    lines = len(layout(d, headline, f, W - 128))
    y = H - 140 - lines * 100 - 96
    kf = inter(28, 800)
    kw = d.textlength(kicker.upper(), font=kf)
    d.rounded_rectangle((64, y, 64 + kw + 40, y + 54), 10, fill=ACCENT)
    d.text((84, y + 10), kicker.upper(), font=kf, fill=ACCENT_INK)
    rich(d, (64, y + 86), headline, f, W - 128, 100, mark=True)
    d.text((64, H - 96), f'Source: {source} · {date}' + (f'  ·  Image: {credit}' if credit else ''), font=inter(26, 500), fill=GREY)
    im.convert('RGB').save(path, quality=95)


def skill_card(path, title, steps, result, date):
    im = Image.new('RGBA', (W, H), BG)
    body = Image.new('RGBA', (W, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    x, width = 72, W - 144
    y = 0
    author(body, d, x, y, date)
    y = rich(d, (x, y + 150), title, inter(76, 800), width, 90) + 44
    for i, step in enumerate(steps, 1):
        d.rounded_rectangle((x, y, x + 72, y + 72), 18, fill=ACCENT)
        n, nf = str(i), inter(40, 900)
        d.text((x + 36 - d.textlength(n, font=nf) / 2, y + 12), n, font=nf, fill=ACCENT_INK)
        y = max(rich(d, (x + 104, y + 10), step, inter(46, 600), width - 104, 60), y + 72) + 40
    y += 16
    d.rounded_rectangle((x, y, x + width, y + 170), 24, fill=SURFACE, outline=LINE, width=2)
    d.text((x + 36, y + 30), 'RESULT', font=mono(28, 700), fill=ACCENT)
    rich(d, (x + 36, y + 78), result, inter(40, 600), width - 72, 50)
    y += 170
    im.alpha_composite(body.crop((0, 0, W, H)), (0, max(80, (H - 110 - y) // 2)))
    d = ImageDraw.Draw(im)
    d.line((x, H - 110, x + width, H - 110), fill=LINE, width=2)
    d.text((x, H - 80), 'Save this for later', font=inter(30, 700), fill=ACCENT)
    d.text((x + width - d.textlength('Skill of the Day', font=inter(28, 600)), H - 78), 'Skill of the Day', font=inter(28, 600), fill=GREY)
    im.convert('RGB').save(path, quality=95)


def ball_cover(path):
    im = Image.new('RGBA', (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((72, 92), 'PICK ONE', font=mono(30, 700), fill=ACCENT)
    rich(d, (72, 140), 'Which ball [escapes] first?', inter(100, 900), W - 144, 108)
    cx, cy, R, gap = W // 2, 800, 350, 34
    pos = [(-150, -120), (50, -210), (180, -20), (-70, 40), (110, 170), (-190, 170)]
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.arc((cx - R, cy - R, cx + R, cy + R), gap, 360 - gap, fill=ACCENT + (200,), width=26)
    for i, (dx, dy) in enumerate(pos):
        g.ellipse((cx + dx - 84, cy + dy - 84, cx + dx + 84, cy + dy + 84), fill=brand.rgb(brand.BALLS[i]) + (200,))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(30)))
    sharp = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0))
    s = ImageDraw.Draw(sharp)
    s.arc(((cx - R) * SS, (cy - R) * SS, (cx + R) * SS, (cy + R) * SS), gap, 360 - gap, fill=ACCENT + (255,), width=12 * SS)
    for i, (dx, dy) in enumerate(pos):
        r, bx, by = 70 * SS, (cx + dx) * SS, (cy + dy) * SS
        s.ellipse((bx - r, by - r, bx + r, by + r), fill=brand.rgb(brand.BALLS[i]) + (255,))
    im.alpha_composite(sharp.resize((W, H), Image.Resampling.LANCZOS))
    d = ImageDraw.Draw(im)
    nf = inter(64, 900)
    for i, (dx, dy) in enumerate(pos):
        n = str(i + 1)
        l, t, r, b = d.textbbox((0, 0), n, font=nf)
        d.text((cx + dx - (r - l) / 2 - l, cy + dy - (b - t) / 2 - t), n, font=nf, fill=(255, 255, 255))
    d.line((72, H - 110, W - 72, H - 110), fill=LINE, width=2)
    d.text((72, H - 80), 'Comment your number', font=inter(30, 700), fill=TEXT)
    d.text((W - 72 - d.textlength('@shipstack_', font=inter(28, 600)), H - 78), '@shipstack_', font=inter(28, 600), fill=GREY)
    im.convert('RGB').save(path, quality=95)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='reels/shipstack/brand_assets')
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob('*.png'):
        old.unlink()
    img = Path(__file__).resolve().parents[2] / 'news-single/images/SHIPNEWS-20261119-001.jpg'
    logo_assets(out)
    post_card(out / 'news-post-card.png',
              'Anthropic raises [$81 billion] in a record IPO, pricing shares at $83 each, Reuters reports.',
              '19 Nov', 'Reuters', image=img, credit='AI-generated')
    photo_card(out / 'news-photo-card.png', 'AI News', 'Anthropic raises [$81 billion] in record IPO',
               'Reuters', '19 Nov 2026', img, credit='AI-generated')
    skill_card(out / 'skill-card.png', 'Automate your [weekly report] in 3 steps:',
               ['Export the numbers to a sheet', 'Ask Claude to draft the summary', 'Schedule it for every Friday'],
               'A weekly task that runs itself.', '20 Nov')
    ball_cover(out / 'ball-pick-one.png')
    print('Wrote', *sorted(p.name for p in out.glob('*.png')), sep='\n  ')


if __name__ == '__main__':
    main()
