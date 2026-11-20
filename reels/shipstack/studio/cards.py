"""News and AI Automation posts (1080x1350) in the same Studio design as the DSA reels.

    python -m reels.shipstack.studio.cards --out reels/shipstack/studio/samples

Same header (shipstack / series / episode + series tag), same panels, same footer; only the
content changes. Text in [brackets] is drawn in the accent colour. No network, no posting.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw

from . import theme as T

W, H = 1080, 1350
X0, X1 = 64, W - 64


def rich(d, xy, text, f, width, leading, color=T.TEXT):
    """Wrapped text; [words] in the accent."""
    x0, y = xy
    space = d.textlength(' ', font=f)
    words, hot = [], False
    for w in text.split():
        if w.startswith('['):
            hot = True
        words.append((w.replace('[', '').replace(']', ''), hot))
        if w.rstrip('.,:;!?').endswith(']'):
            hot = False
    x = x0
    for word, on in words:
        ww = d.textlength(word, font=f)
        if x > x0 and x + ww > x0 + width:
            x, y = x0, y + leading
        d.text((x, y), word, font=f, fill=T.ACCENT if on else color)
        x += ww + space
    return y + leading


def cover(img, w, h):
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.Resampling.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def news(path, crumb, headline, deck, source, date, image=None, credit=None):
    im = Image.new('RGBA', (W, H), T.BG + (255,))
    T.header(im, 'news', crumb)
    d = ImageDraw.Draw(im)
    top, photo_h = 210, 500 if image else 0
    if image:
        ph = cover(Image.open(image).convert('RGB'), X1 - X0, photo_h).convert('RGBA')
        mask = Image.new('L', ph.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, ph.width - 1, ph.height + 40), 22, fill=255)
        im.paste(ph, (X0, top), mask)
    y = top + photo_h + 40
    y = rich(d, (X0, y), headline, T.sans(64, 800), X1 - X0, 76)
    y += 10
    for line in T.wrap(d, deck, T.sans(34, 500), X1 - X0)[:3]:
        d.text((X0, y), line, font=T.sans(34, 500), fill=T.MUTED)
        y += 46
    meta = f'source: {source} · {date}' + (f' · image: {credit}' if credit else '')
    d.text((X0, y + 18), meta, font=T.mono(24, 500), fill=T.MUTED)
    T.footer(im, 'Daily AI news you can save')
    im.convert('RGB').save(path, quality=95)


def automation(path, crumb, title, steps, result, tool=None):
    im = Image.new('RGBA', (W, H), T.BG + (255,))
    T.header(im, 'automation', crumb)
    d = ImageDraw.Draw(im)
    row = 132
    title_lines = len(T.wrap(d, title.replace('[', '').replace(']', ''), T.sans(72, 800), X1 - X0))
    block = title_lines * 86 + 36 + 58 + row * len(steps) + 170
    y0 = 200 + max(0, (H - 160 - 200 - block) // 2)
    top = rich(d, (X0, y0), title, T.sans(72, 800), X1 - X0, 86) + 36
    bottom = top + 58 + row * len(steps) + 170
    if tool:
        d.text((X0, top + 4), tool, font=T.mono(26, 600), fill=T.MUTED)
    y = top + 70
    for i, step in enumerate(steps, 1):
        n = f'{i:02d}'
        d.text((X0, y - 6), n, font=T.mono(54, 800), fill=T.ACCENT)
        lines = T.wrap(d, step, T.sans(44, 600), X1 - X0 - 130)[:2]
        for j, line in enumerate(lines):
            d.text((X0 + 130, y + 2 + j * 52), line, font=T.sans(44, 600), fill=T.TEXT)
        y += row
    d.rounded_rectangle((X0, y + 10, X1, y + 180), 28, fill=T.PANEL)
    d.text((X0 + 36, y + 40), 'RESULT', font=T.mono(26, 700), fill=T.MUTED)
    rich(d, (X0 + 36, y + 84), result, T.sans(46, 700), X1 - X0 - 72, 54)
    T.footer(im, 'Save this for later')
    im.convert('RGB').save(path, quality=95)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='reels/shipstack/studio/samples')
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[3]
    news(out / 'news-sample.png', '19-nov', 'Anthropic raises [$81 billion] in a record IPO',
         'The AI company priced its public offering at $83 a share, Reuters reports.',
         'Reuters', '19 Nov 2026', image=root / 'news-single/images/SHIPNEWS-20261119-001.jpg', credit='AI-generated')
    automation(out / 'automation-sample.png', '#0001', 'Automate your [weekly report]',
               ['Export the numbers to a sheet', 'Ask Claude to draft the summary',
                'Schedule it to send every Friday'],
               'A weekly task that [runs itself].', tool='sheets + claude')
    profile = Image.new('RGBA', (1080, 1080), T.BG + (255,))   # profile picture: full square, IG crops it
    profile.alpha_composite(T.mark(1080, bg=T.BG))
    profile.convert('RGB').save(out / 'avatar-1080.png')
    T.mark(1080, tile=False).save(out / 'logo-mark.png')
    T.lockup(320).convert('RGB').save(out / 'logo-lockup-dark.png')
    T.lockup(320, dark=False).convert('RGB').save(out / 'logo-lockup-light.png')
    print('Wrote', *sorted(p.name for p in out.glob('*.png')), sep='\n  ')


if __name__ == '__main__':
    main()
