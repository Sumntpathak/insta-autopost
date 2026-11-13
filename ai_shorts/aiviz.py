"""
aiviz — shared toolkit for the AI/ML vertical-video series.

Everything is drawn with numpy into a float RGB canvas: anti-aliased,
sub-pixel discs, lines, rounded rects, glows, particle splats and text.
Each episode script defines render(t) -> frame and audio(au), then calls run().

Common CLI for every episode:
  python3 epXX_name.py all                 # full video with sound -> epXX_name.mp4
  python3 epXX_name.py still --t 5.2       # one PNG for checking a moment
  python3 epXX_name.py video --start 0 --end 600 --out part.mp4   # a chunk
  python3 epXX_name.py info                # duration and frame count
Needs: numpy, scipy, pillow, ffmpeg on PATH.
"""
import argparse
import math
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 60

# ------------------------------------------------------------------ palette
BG = np.array((6, 7, 15), np.float32)
CYAN = (64, 210, 255)
MAGENTA = (255, 72, 180)
GOLD = (255, 200, 80)
LIME = (140, 240, 110)
ORANGE = (255, 140, 60)
VIOLET = (150, 110, 255)
RED = (255, 84, 96)
TEAL = (40, 220, 190)
WHITE = (245, 246, 250)
GREY = (150, 154, 172)
DIM = (70, 74, 96)
CLUSTER = [CYAN, MAGENTA, GOLD, LIME, VIOLET, ORANGE]

# ------------------------------------------------------------------- layout
HEADER_Y = 230
ROUND_Y, TITLE_Y, SUB_Y = 420, 482, 540
PANEL = (90, 600, 990, 1500)          # x0, y0, x1, y1 (900 x 900)
COUNT_LABEL_Y, COUNT_Y = 1590, 1668
CAPTION_Y = 1790


# --------------------------------------------------------------------- math
def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def smoother(x):
    x = clamp(x)
    return x * x * x * (x * (x * 6 - 15) + 10)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def mix(c1, c2, t):
    return tuple(lerp(a, b, t) for a, b in zip(c1, c2))


def hsv(h, s=0.75, v=1.0):
    h = (h % 1.0) * 6
    i = int(h); f = h - i
    p, q, r = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    rgb = [(v, r, p), (q, v, p), (p, v, r), (p, q, v), (r, p, v), (v, p, q)][i % 6]
    return tuple(255 * c for c in rgb)


def fmt(n):
    return f"{int(round(n)):,}"


class Plot:
    """Maps data coordinates into a screen rectangle (default: the panel)."""

    def __init__(self, xmin, xmax, ymin, ymax, rect=None, pad=50):
        self.xmin, self.xmax, self.ymin, self.ymax = xmin, xmax, ymin, ymax
        x0, y0, x1, y1 = rect or PANEL
        self.rect = (x0, y0, x1, y1)
        self.sx0, self.sy0, self.sx1, self.sy1 = x0 + pad, y0 + pad, x1 - pad, y1 - pad

    def px(self, x, y):
        X = self.sx0 + (np.asarray(x) - self.xmin) / (self.xmax - self.xmin) * (self.sx1 - self.sx0)
        Y = self.sy1 - (np.asarray(y) - self.ymin) / (self.ymax - self.ymin) * (self.sy1 - self.sy0)
        return X, Y


class Seg:
    """A time window with fade in/out (seconds)."""

    def __init__(self, start, end, fade_in=0.35, fade_out=0.4):
        self.start, self.end, self.fi, self.fo = start, end, fade_in, fade_out

    def alpha(self, t):
        if t < self.start or t > self.end:
            return 0.0
        return smooth((t - self.start) / self.fi) * smooth((self.end - t) / self.fo)

    def local(self, t):
        return t - self.start


# ------------------------------------------------------------------- canvas
_bg_cache = {}


def background(panel=True, grid=True):
    key = (panel, grid)
    if key not in _bg_cache:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        bg = BG[None, None, :] + np.zeros((H, W, 3), np.float32)
        for (cx, cy, rx, ry, col, k) in ((W * 0.2, 700, 650, 600, VIOLET, 0.075),
                                         (W * 0.85, 1350, 600, 700, CYAN, 0.055),
                                         (W * 0.5, 1900, 900, 400, MAGENTA, 0.045)):
            g = np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))
            bg += g[..., None] * np.array(col, np.float32) * k
        if panel:
            x0, y0, x1, y1 = PANEL
            box = Image.new("L", (W, H), 0)
            d = ImageDraw.Draw(box)
            if grid:
                for i in range(1, 9):
                    x = x0 + i * (x1 - x0) / 9; y = y0 + i * (y1 - y0) / 9
                    d.line((x, y0 + 4, x, y1 - 4), fill=22)
                    d.line((x0 + 4, y, x1 - 4, y), fill=22)
            d.rounded_rectangle((x0, y0, x1, y1), radius=28, outline=70, width=2)
            m = np.asarray(box, np.float32) / 255.0
            inside = Image.new("L", (W, H), 0)
            ImageDraw.Draw(inside).rounded_rectangle((x0, y0, x1, y1), radius=28, fill=255)
            mi = np.asarray(inside.filter(ImageFilter.GaussianBlur(1)), np.float32) / 255.0
            bg = bg * (1 - 0.35 * mi[..., None]) + mi[..., None] * np.array((10, 12, 24), np.float32) * 0.35
            bg += m[..., None] * np.array((120, 130, 190), np.float32)
        bg += np.random.default_rng(1).uniform(-0.6, 0.6, bg.shape).astype(np.float32)
        _bg_cache[key] = bg
    return _bg_cache[key].copy()


def _region(x0, y0, x1, y1):
    x0, y0 = max(0, int(math.floor(x0))), max(0, int(math.floor(y0)))
    x1, y1 = min(W, int(math.ceil(x1))), min(H, int(math.ceil(y1)))
    return x0, y0, x1, y1


def _apply(fr, x0, y0, cov, glow, color, a, glow_k):
    col = np.array(color, np.float32)
    reg = fr[y0:y0 + cov.shape[0], x0:x0 + cov.shape[1]]
    if glow is not None and glow_k > 0:
        reg += glow[..., None] * (col * glow_k * a)
    if cov is not None:
        m = cov[..., None] * a
        reg *= 1 - m
        reg += m * col


def disc(fr, x, y, r, color, a=1.0, glow=0.0, glow_r=None, ring=0.0):
    """Anti-aliased disc (or ring of width `ring`) at sub-pixel centre."""
    if a <= 0.003:
        return
    gr = glow_r or r * 1.8
    R = r + (3 * gr if glow > 0 else 2)
    x0, y0, x1, y1 = _region(x - R, y - R, x + R, y + R)
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d = np.sqrt((xx + 0.5 - x) ** 2 + (yy + 0.5 - y) ** 2)
    if ring > 0:
        cov = np.clip(ring / 2 - np.abs(d - r) + 0.5, 0, 1)
    else:
        cov = np.clip(r - d + 0.5, 0, 1)
    g = np.exp(-(np.maximum(d - r, 0) / gr) ** 2) if glow > 0 else None
    _apply(fr, x0, y0, cov, g, color, a, glow)


def polyline(fr, pts, width, color, a=1.0, glow=0.0, glow_r=10.0):
    """Anti-aliased polyline with round joins; pts = [(x, y), ...]."""
    if a <= 0.003 or len(pts) < 2:
        return
    P = np.asarray(pts, np.float32)
    pad = width / 2 + (3 * glow_r if glow > 0 else 2)
    x0, y0, x1, y1 = _region(P[:, 0].min() - pad, P[:, 1].min() - pad, P[:, 0].max() + pad, P[:, 1].max() + pad)
    if x1 <= x0 or y1 <= y0:
        return
    dmin = np.full((y1 - y0, x1 - x0), np.inf, np.float32)
    for (ax, ay), (bx, by) in zip(P[:-1], P[1:]):
        sx0, sy0, sx1, sy1 = _region(min(ax, bx) - pad, min(ay, by) - pad, max(ax, bx) + pad, max(ay, by) + pad)
        sx0, sy0, sx1, sy1 = max(sx0, x0), max(sy0, y0), min(sx1, x1), min(sy1, y1)
        if sx1 <= sx0 or sy1 <= sy0:
            continue
        yy, xx = np.mgrid[sy0:sy1, sx0:sx1].astype(np.float32)
        px, py = xx + 0.5 - ax, yy + 0.5 - ay
        vx, vy = bx - ax, by - ay
        L2 = vx * vx + vy * vy
        h = np.clip((px * vx + py * vy) / L2, 0, 1) if L2 > 1e-9 else 0.0
        d = np.sqrt((px - vx * h) ** 2 + (py - vy * h) ** 2)
        sub = dmin[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0]
        np.minimum(sub, d, out=sub)
    cov = np.clip(width / 2 - dmin + 0.5, 0, 1)
    g = np.exp(-(np.maximum(dmin - width / 2, 0) / glow_r) ** 2) if glow > 0 else None
    _apply(fr, x0, y0, cov, g, color, a, glow)


def line(fr, x0, y0, x1, y1, width, color, a=1.0, glow=0.0, glow_r=10.0):
    polyline(fr, [(x0, y0), (x1, y1)], width, color, a, glow, glow_r)


def dashed(fr, x0, y0, x1, y1, width, color, a=1.0, dash=18, gap=12):
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1:
        return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    s = 0.0
    while s < L:
        e = min(L, s + dash)
        line(fr, x0 + ux * s, y0 + uy * s, x0 + ux * e, y0 + uy * e, width, color, a)
        s = e + gap


def rect(fr, x0, y0, x1, y1, color, a=1.0, radius=0.0, glow=0.0, glow_r=14.0, outline=0.0):
    """Anti-aliased (rounded) rectangle, filled or outlined, sub-pixel."""
    if a <= 0.003:
        return
    pad = 3 * glow_r if glow > 0 else 2
    rx0, ry0, rx1, ry1 = _region(x0 - pad, y0 - pad, x1 + pad, y1 + pad)
    if rx1 <= rx0 or ry1 <= ry0:
        return
    yy, xx = np.mgrid[ry0:ry1, rx0:rx1].astype(np.float32)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hx, hy = (x1 - x0) / 2 - radius, (y1 - y0) / 2 - radius
    qx, qy = np.abs(xx + 0.5 - cx) - hx, np.abs(yy + 0.5 - cy) - hy
    d = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - radius
    cov = np.clip(outline / 2 - np.abs(d + outline / 2) + 0.5, 0, 1) if outline > 0 else np.clip(0.5 - d, 0, 1)
    g = np.exp(-(np.maximum(d, 0) / glow_r) ** 2) if glow > 0 else None
    _apply(fr, rx0, ry0, cov, g, color, a, glow)


def field(fr, rgb, x0, y0, x1, y1, a=1.0, mask_round=0):
    """Blend a low-res RGB array (h, w, 3) stretched smoothly over a rectangle."""
    if a <= 0.003:
        return
    X0, Y0, X1, Y1 = int(x0), int(y0), int(x1), int(y1)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).resize((X1 - X0, Y1 - Y0), Image.BILINEAR)
    arr = np.asarray(img, np.float32)
    reg = fr[Y0:Y1, X0:X1]
    if mask_round:
        m = Image.new("L", (X1 - X0, Y1 - Y0), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, X1 - X0 - 1, Y1 - Y0 - 1), radius=mask_round, fill=255)
        k = (np.asarray(m, np.float32) / 255.0)[..., None] * a
    else:
        k = a
    reg *= 1 - k
    reg += arr * k


def particles(fr, xs, ys, colors, a=1.0, size=1.6, glow=0.8):
    """Fast glowing point cloud: bilinear splats, small blur for the core,
    a wide blur at quarter resolution for the glow. colors: (N, 3)."""
    from scipy.ndimage import gaussian_filter
    if a <= 0.003 or len(xs) == 0:
        return
    xs, ys = np.asarray(xs, np.float32), np.asarray(ys, np.float32)
    cols = np.asarray(colors, np.float32) * a
    pad = 40
    x0, y0, x1, y1 = _region(xs.min() - pad, ys.min() - pad, xs.max() + pad, ys.max() + pad)
    if x1 <= x0 or y1 <= y0:
        return
    h, w = y1 - y0, x1 - x0
    layer = np.zeros((h, w, 3), np.float32)
    fx, fy = xs - x0, ys - y0
    ix, iy = np.floor(fx).astype(int), np.floor(fy).astype(int)
    tx, ty = fx - ix, fy - iy
    for dx, dy, wgt in ((0, 0, (1 - tx) * (1 - ty)), (1, 0, tx * (1 - ty)), (0, 1, (1 - tx) * ty), (1, 1, tx * ty)):
        jx, jy = ix + dx, iy + dy
        ok = (jx >= 0) & (jx < w) & (jy >= 0) & (jy < h)
        for c in range(3):
            np.add.at(layer[..., c], (jy[ok], jx[ok]), cols[ok, c] * wgt[ok])
    core = gaussian_filter(layer, sigma=(size, size, 0)) * (2 * math.pi * size * size) * 0.55
    gl = gaussian_filter(layer[: h // 4 * 4, : w // 4 * 4].reshape(h // 4, 4, w // 4, 4, 3).sum((1, 3)), sigma=(3, 3, 0))
    gl_img = np.asarray(Image.fromarray(np.clip(gl * 8, 0, 255).astype(np.uint8)).resize((w // 4 * 4, h // 4 * 4), Image.BILINEAR), np.float32) / 8
    reg = fr[y0:y1, x0:x1]
    reg += np.minimum(core, 255)
    reg[: gl_img.shape[0], : gl_img.shape[1]] += gl_img * glow * 2.2


# --------------------------------------------------------------------- text
_txt = {}


def font(weight, size):
    for p in (os.path.join(HERE, "fonts", f"Poppins-{weight}.ttf"),
              "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def text_mask(s, weight="Bold", size=60):
    key = (s, weight, size)
    if key not in _txt:
        f = font(weight, size)
        l, tp, r, b = f.getbbox(s)
        asc, desc = f.getmetrics()
        im = Image.new("L", (max(1, r - l) + 8, asc + desc + 8), 0)
        ImageDraw.Draw(im).text((4 - l, 4), s, font=f, fill=255)
        _txt[key] = np.asarray(im, np.float32) / 255.0
    return _txt[key]


def text(fr, s, weight, size, x, y, color, a=1.0, anchor="center", glow=0.0):
    """Draw text; anchor 'center' | 'left' | 'right' on x, vertically centred on y."""
    if a <= 0.003 or not s:
        return
    m = text_mask(s, weight, size)
    h, w = m.shape
    X = x - w / 2 if anchor == "center" else x - 4 if anchor == "left" else x - w + 4
    X0, Y0 = int(round(X)), int(round(y - h / 2))
    x0, y0, x1, y1 = max(0, X0), max(0, Y0), min(W, X0 + w), min(H, Y0 + h)
    if x1 <= x0 or y1 <= y0:
        return
    cov = m[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0]
    g = None
    if glow > 0:
        g = np.asarray(Image.fromarray((cov * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10)), np.float32) / 255
    _apply(fr, x0, y0, cov, g, color, a, glow)


def text_width(s, weight, size):
    return text_mask(s, weight, size).shape[1] - 8


# ------------------------------------------------------------ show elements
def header(fr, t, stages, y=HEADER_Y, fade_end=None):
    """stages: [(t_start, [(line, color, size), ...]), ...]; crossfades on change."""
    idx = max([i for i, (ts, _) in enumerate(stages) if t >= ts] or [0])
    ts = stages[idx][0]
    k = smooth((t - ts) / 0.4) if idx > 0 else 1.0
    fa = 1.0 if fade_end is None else 1 - smooth((t - fade_end + 1.0) / 1.0)

    def draw(lines, a, dy):
        n = len(lines)
        step = max(sz for _, _, sz in lines) * 1.12
        for i, (s, col, sz) in enumerate(lines):
            text(fr, s, "Bold", sz, W / 2, y + (i - (n - 1) / 2) * step + dy, col, a)
    if k < 1:
        draw(stages[idx - 1][1], (1 - k) * fa, -24 * k)
    draw(stages[idx][1], k * fa, 24 * (1 - k))


def round_titles(fr, n, title, sub, a, sub_color=GREY):
    text(fr, f"ROUND {n}", "Medium", 30, W / 2, ROUND_Y, GREY, a)
    text(fr, title, "Bold", 62, W / 2, TITLE_Y, WHITE, a)
    if sub:
        text(fr, sub, "Medium", 34, W / 2, SUB_Y, sub_color, a)


def counter(fr, label, value, a, color=WHITE, x=W / 2, size=104):
    text(fr, label, "Medium", 30, x, COUNT_LABEL_Y, GREY, a)
    text(fr, value, "Bold", size, x, COUNT_Y, color, a)


def counters(fr, items, a):
    """Two or three counters side by side: [(label, value, color), ...]."""
    n = len(items)
    for i, (lab, val, col) in enumerate(items):
        counter(fr, lab, val, a, col, x=W * (i + 1) / (n + 1), size=88 if n == 2 else 72)


def caption(fr, s, a, color=GREY, size=34):
    text(fr, s, "Medium", size, W / 2, CAPTION_Y, color, a)


def tag(fr, s, x, y, color, a, size=30):
    """Small glowing pill label."""
    w = text_width(s, "SemiBold", size) + 36
    rect(fr, x - w / 2, y - size * 0.85, x + w / 2, y + size * 0.85, tuple(c * 0.22 for c in color), a * 0.9,
         radius=size * 0.85, glow=0.25, glow_r=12)
    rect(fr, x - w / 2, y - size * 0.85, x + w / 2, y + size * 0.85, color, a, radius=size * 0.85, outline=2.5)
    text(fr, s, "SemiBold", size, x, y, color, a)


def finish(fr, t, duration):
    k = 1 - smooth((t - (duration - 0.8)) / 0.8)
    if k < 1:
        fr[:] = BG + (fr - BG) * k
    return np.clip(fr, 0, 255).astype(np.uint8)


# -------------------------------------------------------------------- audio
class Audio:
    def __init__(self, duration, sr=48000):
        self.sr = sr
        self.n = int(duration * sr)
        self.buf = np.zeros(self.n + sr * 2, np.float32)
        self.rng = np.random.default_rng(5)

    def _add(self, t, sig):
        i = int(t * self.sr)
        if i < 0 or i >= self.n:
            return
        j = min(len(self.buf), i + len(sig))
        self.buf[i:j] += sig[: j - i]

    def tick(self, t, freq=2200, amp=0.25, decay=0.004):
        tk = np.arange(int(0.03 * self.sr)) / self.sr
        s = np.sin(2 * np.pi * freq * tk) * np.exp(-tk / decay) + 0.3 * self.rng.normal(size=tk.size) * np.exp(-tk / 0.001)
        self._add(t, (s * amp).astype(np.float32))

    def blip(self, t, freq=660, amp=0.18, dur=0.12):
        tk = np.arange(int(dur * self.sr)) / self.sr
        env = np.minimum(1, tk / 0.004) * np.exp(-tk / (dur / 3))
        self._add(t, (np.sin(2 * np.pi * freq * tk) * env * amp).astype(np.float32))

    def chime(self, t, base=880, amp=0.16, dur=1.4):
        tk = np.arange(int(dur * self.sr)) / self.sr
        s = sum(w * np.sin(2 * np.pi * base * r * tk) for r, w in ((1, 1), (1.5, 0.5), (2, 0.3), (3, 0.12)))
        self._add(t, (s * np.exp(-tk / 0.4) * np.minimum(1, tk / 0.005) * amp).astype(np.float32))

    def buzz(self, t, freq=110, amp=0.14, dur=0.35):
        tk = np.arange(int(dur * self.sr)) / self.sr
        s = np.sign(np.sin(2 * np.pi * freq * tk)) * 0.5 + np.sin(2 * np.pi * freq * 1.5 * tk) * 0.3
        self._add(t, (s * np.exp(-tk / (dur / 2.5)) * amp).astype(np.float32))

    def whoosh(self, t, amp=0.10, dur=0.6, rise=True):
        from scipy.signal import lfilter
        tk = np.arange(int(dur * self.sr)) / self.sr
        noise = self.rng.normal(size=tk.size)
        noise = lfilter([0.08], [1, -0.92], noise)
        env = np.sin(np.pi * tk / dur) ** 2
        self._add(t, (noise * env * amp * 3).astype(np.float32))

    def sweep(self, t, f0=300, f1=900, amp=0.08, dur=0.5):
        tk = np.arange(int(dur * self.sr)) / self.sr
        ph = 2 * np.pi * np.cumsum(np.linspace(f0, f1, tk.size)) / self.sr
        self._add(t, (np.sin(ph) * np.sin(np.pi * tk / dur) * amp).astype(np.float32))

    def pad(self, t0, t1, notes=(220, 277.2, 329.6), amp=0.035):
        """Quiet sustained chord bed with slow fades."""
        n = int((t1 - t0) * self.sr)
        tk = np.arange(n) / self.sr
        s = sum(np.sin(2 * np.pi * f * tk + i) + 0.3 * np.sin(2 * np.pi * 2 * f * tk) for i, f in enumerate(notes))
        env = np.minimum(1, tk / 1.5) * np.minimum(1, (tk[-1] - tk) / 1.5)
        self._add(t0, (s * env * amp / len(notes)).astype(np.float32))

    def write(self, path):
        from scipy.io import wavfile
        out = np.tanh(self.buf[: self.n] * 1.3) * 0.85
        wavfile.write(path, self.sr, (np.stack([out, out], 1) * 32767).astype(np.int16))


# ---------------------------------------------------------------------- run
def run(render, duration, audio_fn, default_out):
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["all", "video", "audio", "still", "info"])
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=-1)
    ap.add_argument("--t", type=float, default=0.0)
    ap.add_argument("--out", default=default_out)
    a = ap.parse_args()
    total = int(round(duration * FPS))

    def encode(path, f0, f1):
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-threads", "3", "-preset", "veryfast", "-crf", "16",
               "-pix_fmt", "yuv420p", path]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for f in range(f0, f1):
            p.stdin.write(render(f / FPS).tobytes())
            if f % 120 == 0:
                print(f"  frame {f}/{f1}", flush=True)
        p.stdin.close()
        if p.wait():
            raise RuntimeError("FFmpeg render failed")

    if a.mode == "info":
        print(f"{duration:.2f}s = {total} frames @ {FPS} fps")
    elif a.mode == "still":
        out = a.out if a.out.endswith(".png") else a.out.replace(".mp4", f"_{a.t:05.2f}s.png")
        Image.fromarray(render(a.t)).save(out); print("wrote", out)
    elif a.mode == "video":
        encode(a.out, a.start, total if a.end < 0 else min(a.end, total))
    elif a.mode == "audio":
        au = Audio(duration); audio_fn(au); au.write(a.out)
    else:
        encode("_v.mp4", 0, total)
        au = Audio(duration); audio_fn(au); au.write("_a.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "_v.mp4", "-i", "_a.wav", "-c:v", "copy", "-c:a", "aac",
                        "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.out], check=True)
        os.remove("_v.mp4"); os.remove("_a.wav")
        print("wrote", a.out)
