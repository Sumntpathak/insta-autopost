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


def mark(size):
    """Logo mark: '>_' on the accent, rounded square."""
    s = size * 2
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, s - 1, s - 1), radius=round(s * 0.24), fill=ACCENT)
    f = mono(round(s * 0.44), 800)
    l, t, r, b = d.textbbox((0, 0), '>_', font=f)
    d.text(((s - (r - l)) / 2 - l, (s - (b - t)) / 2 - t), '>_', font=f, fill=BG)
    return im.resize((size, size), Image.Resampling.LANCZOS)


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
