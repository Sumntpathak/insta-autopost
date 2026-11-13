#!/usr/bin/env python3
"""EP02 — A ball rolling downhill is how AI learns.

The ball is the model; its height is the error. Each step moves it
against the slope (gradient descent).
Round 1: a smooth bowl, it finds the bottom.
Round 2: a bumpy landscape, plain steps get stuck in a shallow dip.
Round 3: same landscape with momentum, it rolls through to the deepest valley.
Run: python3 ep02_downhill.py all
"""
import math
import numpy as np
import aiviz as V


def bowl(x):
    return 0.12 * x ** 2 + 0.05


def bumpy(x):
    return 0.07 * x ** 2 - 1.05 * np.exp(-(x - 1.35) ** 2 / 0.45) - 0.50 * np.exp(-(x + 1.55) ** 2 / 0.28) + 0.95


def grad(f, x, h=1e-5):
    return (f(x + h) - f(x - h)) / (2 * h)


def descend(f, x, lr, mom, n):
    v, xs = 0.0, [x]
    for _ in range(n):
        v = mom * v - lr * grad(f, x)
        x = x + v
        xs.append(x)
    return xs


STEP_DT = 0.12
ROUNDS = [
    dict(f=bowl, x0=-2.9, lr=0.9, mom=0.0, n=26, title="A smooth valley", sub="plain steps",
         result=("Smooth valley:", "found the bottom"), col=V.LIME, hue=(0.30, 0.50)),
    dict(f=bumpy, x0=-3.0, lr=0.5, mom=0.0, n=30, title="A bumpy valley", sub="plain steps",
         result=("Bumpy valley:", "stuck in a dip"), col=V.RED, hue=(0.75, 0.95)),
    dict(f=bumpy, x0=-3.0, lr=0.35, mom=0.86, n=46, title="Add momentum", sub="steps keep some speed",
         result=("With momentum:", "it escapes"), col=V.GOLD, hue=(0.75, 0.95)),
]
PLOT = V.Plot(-3.3, 3.3, -0.45, 1.75, pad=40)

t = 0.0
for i, r in enumerate(ROUNDS):
    r["xs"] = descend(r["f"], r["x0"], r["lr"], r["mom"], r["n"])
    start = t + (0.2 if i else 0.0)
    r["go"] = start + (1.9 if i == 0 else 1.0)
    r["done"] = r["go"] + r["n"] * STEP_DT
    r["seg"] = V.Seg(start, r["done"] + 1.4)
    t = r["seg"].end
OUTRO = t + 0.2
DUR = OUTRO + 4.4

HEADERS = [(0.0, [("A ball rolling downhill", V.WHITE, 62), ("is how AI learns", V.GOLD, 66)])]
for r in ROUNDS:
    HEADERS.append((r["done"] + 0.3, [(r["result"][0], V.WHITE, 62), (r["result"][1], r["col"], 74)]))
HEADERS.append((OUTRO, [("Training a network", V.WHITE, 66), ("= finding the valley", V.GOLD, 66)]))


def terrain_layer(f, hue):
    """Pre-rendered filled landscape for the panel (colour + coverage)."""
    x0, y0, x1, y1 = V.PANEL
    w, h = x1 - x0, y1 - y0
    cols = np.arange(w) + x0 + 0.5
    xd = PLOT.xmin + (cols - PLOT.sx0) / (PLOT.sx1 - PLOT.sx0) * (PLOT.xmax - PLOT.xmin)
    _, cy = PLOT.px(xd, f(xd))
    rows = np.arange(h)[:, None] + y0 + 0.5
    cov = np.clip(rows - cy[None, :] + 0.5, 0, 1)
    depth = np.clip((rows - cy[None, :]) / 520, 0, 1)
    top = np.array([V.hsv(V.lerp(hue[0], hue[1], u), 0.7, 0.85) for u in np.linspace(0, 1, w)], np.float32)
    col = top[None, :, :] * (1 - depth[..., None]) * 0.55 + np.array((10, 12, 28), np.float32) * depth[..., None]
    return col, cov * 0.92, xd, cy


for r in ROUNDS:
    r["layer"] = terrain_layer(r["f"], r["hue"])


def ball_x(r, t):
    s = (t - r["go"]) / STEP_DT
    if s <= 0:
        return r["xs"][0], 0
    if s >= r["n"]:
        return r["xs"][-1], r["n"]
    k = int(s)
    return V.lerp(r["xs"][k], r["xs"][k + 1], V.smoother(s - k)), k + 1


def render(t):
    fr = V.background()
    V.header(fr, t, HEADERS)
    for n, r in enumerate(ROUNDS, 1):
        a = r["seg"].alpha(t)
        if a <= 0:
            continue
        V.round_titles(fr, n, r["title"], r["sub"], a, r["col"])
        col, cov, xd, cy = r["layer"]
        x0, y0, x1, y1 = V.PANEL
        reg = fr[y0:y1, x0:x1]
        m = cov[..., None] * a
        reg *= 1 - m
        reg += col * m
        # glowing ridge line in colour bands
        pts = list(zip(np.arange(x0, x1, 6) + 3.0, np.interp(np.arange(x0, x1, 6) + 3.0, np.arange(x0, x1) + 0.5, cy)))
        mid = V.hsv(sum(r["hue"]) / 2, 0.6, 1.0)
        V.polyline(fr, pts, 5, mid, a, glow=0.5, glow_r=12)      # one glow pass, then colour bands
        k = max(2, len(pts) // 14)
        for j in range(0, len(pts) - 1, k):
            u = j / len(pts)
            V.polyline(fr, pts[j:j + k + 1], 5, V.hsv(V.lerp(r["hue"][0], r["hue"][1], u), 0.6, 1.0), a)
        # trail of previous positions
        bx, step = ball_x(r, t)
        f = r["f"]
        for j in range(max(0, step - 12), step):
            xj = r["xs"][j]
            px, py = PLOT.px(xj, f(xj))
            age = (step - j) / 12
            V.disc(fr, float(px), float(py) - 22, 6, r["col"], a * (1 - age) * 0.7, glow=0.4)
        # ball sits on the surface along the normal
        px, py = PLOT.px(bx, f(bx))
        slope_px = grad(f, bx) * (PLOT.sy1 - PLOT.sy0) / (PLOT.ymax - PLOT.ymin) / ((PLOT.sx1 - PLOT.sx0) / (PLOT.xmax - PLOT.xmin))
        nx, ny = slope_px, -1.0
        L = math.hypot(nx, ny); nx, ny = nx / L, ny / L
        R = 26
        cx, cyb = float(px) + nx * R, float(py) + ny * R
        # gradient arrow: which way is downhill
        g = -grad(f, bx)
        if abs(g) > 0.01 and step < r["n"]:
            L2 = min(140, 60 + 220 * abs(g)) * (1 if g > 0 else -1)
            tx, ty = 1 / math.hypot(1, slope_px), slope_px / math.hypot(1, slope_px)
            V.line(fr, cx, cyb, cx + tx * L2, cyb + ty * L2, 4, V.WHITE, a * 0.7)
            V.disc(fr, cx + tx * L2, cyb + ty * L2, 7, V.WHITE, a * 0.8)
        V.disc(fr, cx, cyb, R, r["col"], a, glow=0.9, glow_r=26)
        V.disc(fr, cx - 8, cyb - 9, 7, V.WHITE, a * 0.55)
        V.counters(fr, [("ERROR (HEIGHT)", f"{float(f(bx)):.2f}", V.WHITE), ("STEPS", str(step), r["col"])], a)
    if t >= OUTRO:
        a = V.smooth((t - OUTRO) / 0.5)
        V.text(fr, "Every tweak to an AI", "Bold", 56, V.W / 2, 920, V.WHITE, a)
        V.text(fr, "is one step downhill", "Bold", 56, V.W / 2, 990, V.WHITE, a)
        V.text(fr, "on a landscape of error", "Bold", 56, V.W / 2, 1060, V.GOLD, V.smooth((t - OUTRO - 0.5) / 0.5))
        V.caption(fr, "Momentum helps it roll past small dips", V.smooth((t - OUTRO - 1.1) / 0.5))
    return V.finish(fr, t, DUR)


def audio(au):
    au.pad(0, DUR, notes=(196, 246.9, 293.7), amp=0.03)
    for r in ROUNDS:
        for k in range(r["n"]):
            h = float(r["f"](r["xs"][k + 1]))
            au.tick(r["go"] + k * STEP_DT, freq=700 + 900 * max(0.0, 1.6 - h), amp=0.14)
        if r["col"] == V.RED:
            au.buzz(r["done"] + 0.3)
        else:
            au.chime(r["done"] + 0.3, 784 if r["mom"] else 660)
    au.chime(OUTRO + 0.5, 523, amp=0.14)


if __name__ == "__main__":
    V.run(render, DUR, audio, "ep02_downhill.mp4")
