"""ShipStack Studio: one design for all three series (News, AI Automation, DSA).

Every post is a page in the same "developer workspace": a dark editor surface, a file-path
breadcrumb that names the series and episode (shipstack / dsa / #0001), one coloured series tag,
and the same footer. Only the content changes, never the design.
"""
from PIL import Image, ImageDraw, ImageFont

from .. import brand

BG = (13, 17, 23)            # editor background
PANEL = (22, 27, 34)         # cards / code panel
PANEL_2 = (30, 36, 44)
BORDER = (48, 54, 61)
TEXT = (230, 237, 243)
MUTED = (139, 148, 158)
ACCENT = (34, 211, 238)      # one brand accent (cyan) used for highlights everywhere

# Series tags: same shape and place on every post; colour tells the series apart.
SERIES = {
    'news': ('NEWS', (248, 113, 113)),
    'automation': ('AI AUTOMATION', (167, 139, 250)),
    'dsa': ('DSA', (52, 211, 153)),
}

# Code syntax colours (GitHub-dark-like, readable on BG)
SYNTAX = {'kw': (255, 123, 114), 'fn': (210, 168, 255), 'num': (121, 192, 255), 'str': (165, 214, 255),
          'com': (139, 148, 158), 'name': (230, 237, 243), 'op': (230, 237, 243), 'builtin': (255, 166, 87)}


def sans(size, weight=600):
    f = ImageFont.truetype(str(brand.SANS), size)
    try:
        f.set_variation_by_axes([min(32, max(14, size)), weight])
    except Exception:
        pass
    return f


def mono(size, weight=500):
    f = ImageFont.truetype(str(brand.MONO), size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def wrap(draw, text, f, width):
    lines, line = [], ''
    for word in text.split():
        trial = (line + ' ' + word).strip()
        if draw.textlength(trial, font=f) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_boat(d, s, color):
    """The ShipStack mark: a boat whose sail is a code chevron '>' (ship + code), on a 10x10 grid."""
    u = s / 10
    cx, cy, w, h, th = 5.2 * u, 3.75 * u, 3.4 * u, 3.5 * u, 1.25 * u * 1.15
    d.polygon([(cx - w / 2, cy - h / 2), (cx - w / 2 + th, cy - h / 2), (cx + w / 2, cy),
               (cx - w / 2 + th, cy + h / 2), (cx - w / 2, cy + h / 2), (cx + w / 2 - th, cy)], fill=color)
    y, hh = 6.15 * u, 1.75 * u
    d.polygon([(1.9 * u, y), (8.1 * u, y), (6.85 * u, y + hh), (3.15 * u, y + hh)], fill=color)


def mark(size, bg=BG, fg=ACCENT, tile=True, outline=True):
    """Logo mark. tile=True: rounded-square badge (thin border so it reads on dark pages);
    tile=False: the boat alone on transparent, in `fg`."""
    s = size * 4
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if tile:
        d.rounded_rectangle((0, 0, s - 1, s - 1), radius=round(s * 0.24), fill=bg,
                            outline=BORDER if outline else None, width=max(4, round(s * 0.03)) if outline else 0)
    draw_boat(d, s, fg)
    return im.resize((size, size), Image.Resampling.LANCZOS)


def lockup(height, dark=True):
    """Mark + 'shipstack_' wordmark (the cyan underscore matches the handle)."""
    bgc = BG if dark else (255, 255, 255)
    ink = TEXT if dark else BG
    f = sans(round(height * 0.5), 800)
    probe = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    word_w = probe.textlength('shipstack', font=f)
    w = round(height * 1.25 + word_w + height * 0.45)
    im = Image.new('RGBA', (w, height), bgc + (255,))
    im.alpha_composite(mark(round(height * 0.8)), (round(height * 0.1), round(height * 0.1)))
    d = ImageDraw.Draw(im)
    l, top, r, b = d.textbbox((0, 0), 'shipstack', font=f)
    tx, ty = round(height * 1.05), round((height - (b - top)) / 2 - top)
    d.text((tx, ty), 'shipstack', font=f, fill=ink)
    asc, _ = f.getmetrics()
    ux = tx + word_w + height * 0.04
    d.rectangle((ux, ty + asc - height * 0.07, ux + height * 0.24, ty + asc), fill=ACCENT)
    return im


def header(im, series, crumb, top=72):
    """Shared header: mark + 'shipstack / series / episode' breadcrumb + series tag."""
    d = ImageDraw.Draw(im)
    w = im.width
    im.alpha_composite(mark(64), (64, top))
    f = mono(30, 600)
    x = 148
    for i, part in enumerate(['shipstack', series, crumb]):
        if i:
            d.text((x, top + 14), '/', font=f, fill=BORDER)
            x += d.textlength('/ ', font=f) + 4
        d.text((x, top + 14), part, font=f, fill=TEXT if i == 2 else MUTED)
        x += d.textlength(part + ' ', font=f) + 4
    label, color = SERIES[series]
    tf = sans(24, 800)
    tw = d.textlength(label, font=tf)
    d.rounded_rectangle((w - 64 - tw - 36, top + 8, w - 64, top + 56), 24, outline=color, width=3)
    d.text((w - 64 - tw - 18, top + 18), label, font=tf, fill=color)
    d.line((64, top + 100, w - 64, top + 100), fill=BORDER, width=2)


def footer(im, left, right='@shipstack_', bottom=72):
    d = ImageDraw.Draw(im)
    w, h = im.size
    y = h - bottom - 32
    d.line((64, y - 28, w - 64, y - 28), fill=BORDER, width=2)
    d.text((64, y), left, font=sans(28, 700), fill=ACCENT)
    f = mono(26, 600)
    d.text((w - 64 - d.textlength(right, font=f), y + 2), right, font=f, fill=MUTED)
