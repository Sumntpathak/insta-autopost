"""Editorial page drawing for Arena reels (skia), matching the Lab grid and type.

Text is positioned by cap height, so a line's vertical centre sits exactly on its grid slot.
"""
import subprocess
from pathlib import Path

import numpy as np
import skia

from .. import brand

G = brand.ARENA
FPS = 60
FRAMES = FPS * brand.SECONDS


def color(hex_color, alpha=1.0):
    r, g, b = brand.rgb(hex_color)
    return skia.Color(r, g, b, int(255 * alpha))


def paint(hex_color, alpha=1.0, stroke=None, cap=None):
    p = skia.Paint(Color=color(hex_color, alpha), AntiAlias=True)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        if cap == 'round':
            p.setStrokeCap(skia.Paint.kRound_Cap)
    return p


def _weight(path, wght):
    tf = skia.Typeface.MakeFromFile(str(path))
    C = skia.FontArguments.VariationPosition
    args = skia.FontArguments()
    args.setVariationDesignPosition(C(C.Coordinates([C.Coordinate(int.from_bytes(b'wght', 'big'), float(wght))])))
    return tf.makeClone(args)


class Type:
    def __init__(self):
        self.serif = skia.Typeface.MakeFromFile(str(brand.SERIF))
        self.italic = skia.Typeface.MakeFromFile(str(brand.SERIF_ITALIC))
        self.sans = _weight(brand.SANS, 400)
        self.sans_medium = _weight(brand.SANS, 500)
        self.sans_semi = _weight(brand.SANS, 600)
        self.mono = _weight(brand.MONO, 500)
        self._cache = {}

    def font(self, face, cap_px):
        key = (id(face), cap_px)
        if key not in self._cache:
            probe = skia.Font(face, 100)
            ratio = probe.getMetrics().fCapHeight / 100 or 0.7
            f = skia.Font(face, cap_px / ratio)
            f.setEdging(skia.Font.Edging.kAntiAlias)
            f.setSubpixel(True)
            self._cache[key] = (f, cap_px)
        return self._cache[key]

    def text(self, c, s, x, y, face, cap, hex_color, align='left', alpha=1.0):
        """Draw s with its cap-height centre at y. Returns the drawn width."""
        f, cap = self.font(face, cap)
        w = f.measureText(s)
        if align == 'right':
            x -= w
        elif align == 'center':
            x -= w / 2
        c.drawString(s, x, y + cap / 2, f, paint(hex_color, alpha))
        return w

    def width(self, s, face, cap):
        return self.font(face, cap)[0].measureText(s)


class Page:
    """Header/footer blocks shared by every Arena reel."""

    def __init__(self):
        self.t = Type()

    def masthead(self, c, kicker):
        self.t.text(c, kicker, brand.LEFT_X, G['MAST'], self.t.sans_semi, brand.KICK_CAP, brand.ACCENT)
        self.t.text(c, brand.HANDLE, brand.RIGHT_X, G['MAST'], self.t.mono, brand.KICK_CAP, brand.MUTED, 'right')
        self.hairline(c, G['RULE_1'])

    def hairline(self, c, y):
        c.drawLine(brand.LEFT_X, y, brand.RIGHT_X, y, paint(brand.RULE, 1, stroke=1.6))

    def headline(self, c, line1, line2, accent, accent_color=None, alpha=1.0):
        """Two serif lines; `accent` is appended to line 2 in italic indigo."""
        t = self.t
        t.text(c, line1, brand.LEFT_X, G['HEAD_1'], t.serif, brand.HEAD_CAP, brand.INK, alpha=alpha)
        w = t.text(c, line2, brand.LEFT_X, G['HEAD_2'], t.serif, brand.HEAD_CAP, brand.INK, alpha=alpha) if line2 else 0
        t.text(c, accent, brand.LEFT_X + w, G['HEAD_2'], t.italic, brand.HEAD_CAP, accent_color or brand.ACCENT, alpha=alpha)

    def dek(self, c, text, right_text=None, right_color=None):
        self.t.text(c, text, brand.LEFT_X, G['DEK'], self.t.sans, brand.DEK_CAP, brand.MUTED)
        if right_text:
            self.t.text(c, right_text, brand.RIGHT_X, G['DEK'], self.t.mono, 30, right_color or brand.INK, 'right')

    def board_head(self, c, label):
        self.hairline(c, G['RULE_2'])
        self.t.text(c, label, brand.LEFT_X, G['BOARD_HEAD'], self.t.sans_semi, 16, brand.MUTED)

    def cells(self):
        """Six scoreboard cells (x0, x1, y): 3 columns x 2 rows across the text column."""
        width = (brand.RIGHT_X - brand.LEFT_X + 48) / 3
        return [(brand.LEFT_X + col * width, brand.LEFT_X + col * width + width - 48, G['BOARD'][row])
                for row in range(2) for col in range(3)]

    def conclusion(self, c, before, accent, after='', alpha=1.0, cap=38):
        """One serif line with an italic accent; shrinks to fit the text column, never overflows."""
        t = self.t
        total = t.width(before, t.serif, cap) + t.width(accent, t.italic, cap) + t.width(after, t.serif, cap)
        cap = min(cap, cap * (brand.RIGHT_X - brand.LEFT_X) / max(total, 1))
        x = brand.LEFT_X
        x += t.text(c, before, x, G['END'], t.serif, cap, brand.ACCENT, alpha=alpha)
        x += t.text(c, accent, x, G['END'], t.italic, cap, brand.ACCENT, alpha=alpha)
        t.text(c, after, x, G['END'], t.serif, cap, brand.ACCENT, alpha=alpha)


class Encoder:
    """Pipe RGBA frames + a WAV into a verified-format MP4 (H.264/AAC, 1080x1920, 60 fps)."""

    def __init__(self, out, wav):
        self.out = Path(out)
        self.out.parent.mkdir(parents=True, exist_ok=True)
        self.proc = subprocess.Popen(
            ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pixel_format', 'rgba',
             '-video_size', f'{brand.W}x{brand.H}', '-framerate', str(FPS), '-i', 'pipe:0', '-i', str(wav),
             '-c:v', 'libx264', '-preset', 'medium', '-tune', 'animation', '-crf', '17', '-pix_fmt', 'yuv420p',
             '-r', str(FPS), '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-frames:v', str(FRAMES),
             '-t', str(brand.SECONDS), '-movflags', '+faststart', str(self.out)], stdin=subprocess.PIPE)

    def write(self, surface):
        self.proc.stdin.write(surface.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())

    def close(self):
        try:
            self.proc.stdin.close()
        except BrokenPipeError:
            pass
        if self.proc.wait():
            raise RuntimeError('ffmpeg failed')
        return self.out


def new_surface():
    s = skia.Surface(brand.W, brand.H)
    s.getCanvas().clear(color(brand.PAPER))
    return s
