#!/usr/bin/env python3
"""EP01 — Watch a machine learn to draw a line.

Exact full-batch gradient descent on mean squared error for y = w·x + b.
Round 1: learning rate too small (crawls). Round 2: just right (converges).
Round 3: too big (overshoots and swings before settling).
Run: python3 ep01_line_fit.py all
"""
import math
import numpy as np
import aiviz as V

rng = np.random.default_rng(2)
X = np.sort(rng.uniform(-1, 1, 26))
Y = 0.8 * X + 0.25 + rng.normal(0, 0.17, X.size)
W0, B0 = -0.9, -0.65
STEPS, STEP_DT = 48, 0.10

ROUNDS = [
    dict(lr=0.02, title="Tiny steps", result=("Tiny steps:", "too slow"), col=V.CYAN),
    dict(lr=0.30, title="Just-right steps", result=("Right-size steps:", "it learns"), col=V.LIME),
    dict(lr=0.985, title="Giant steps", result=("Giant steps:", "it overshoots"), col=V.MAGENTA),
]


def descend(lr):
    w, b, hist = W0, B0, []
    for _ in range(STEPS + 1):
        err = w * X + b - Y
        hist.append((w, b, float(np.mean(err ** 2))))
        w, b = w - lr * 2 * np.mean(err * X), b - lr * 2 * np.mean(err)
    return hist


t = 0.0
for i, r in enumerate(ROUNDS):
    r["hist"] = descend(r["lr"])
    start = t + (0.2 if i else 0.0)
    r["go"] = start + (1.9 if i == 0 else 0.9)
    r["done"] = r["go"] + STEPS * STEP_DT
    r["seg"] = V.Seg(start, r["done"] + 1.3)
    t = r["seg"].end
OUTRO = t + 0.2
DUR = OUTRO + 4.4
PLOT = V.Plot(-1.15, 1.15, -1.6, 1.6)
LOSS0 = ROUNDS[0]["hist"][0][2]

HEADERS = [(0.0, [("Watch a machine", V.WHITE, 66), ("learn to draw a line", V.GOLD, 66)])]
for r in ROUNDS:
    HEADERS.append((r["done"] + 0.3, [(r["result"][0], V.WHITE, 64), (r["result"][1], r["col"], 76)]))
HEADERS.append((OUTRO, [("Every AI learns", V.WHITE, 70), ("like this", V.GOLD, 70)]))


def params(r, t):
    """Smoothly interpolated (w, b, loss, step) between gradient steps."""
    h = r["hist"]
    s = (t - r["go"]) / STEP_DT
    if s <= 0:
        return h[0][0], h[0][1], h[0][2], 0
    k = min(int(s), STEPS - 1) if s < STEPS else STEPS - 1
    f = V.smoother(s - k) if s < STEPS else 1.0
    w = V.lerp(h[k][0], h[k + 1][0], f); b = V.lerp(h[k][1], h[k + 1][1], f)
    err = w * X + b - Y
    return w, b, float(np.mean(err ** 2)), min(STEPS, int(math.floor(s)) + (1 if s >= STEPS else 0))


def render(t):
    fr = V.background()
    V.header(fr, t, HEADERS)
    for n, r in enumerate(ROUNDS, 1):
        a = r["seg"].alpha(t)
        if a <= 0:
            continue
        w, b, loss, step = params(r, t)
        V.round_titles(fr, n, r["title"], f"learning rate  {r['lr']}", a, r["col"])
        # residuals: how wrong the line is at every point
        pxs, pys = PLOT.px(X, Y)
        _, lys = PLOT.px(X, w * X + b)
        for x_, y_, ly in zip(pxs, pys, lys):
            e = min(1.0, abs(y_ - ly) / 260)
            V.line(fr, x_, y_, x_, ly, 3, V.mix(V.LIME, V.RED, e), a * (0.35 + 0.5 * e))
        # the model's line, clipped to the panel
        xa, xb = -1.12, 1.12
        (lx0, lx1), (ly0, ly1) = PLOT.px([xa, xb], [w * xa + b, w * xb + b])
        y_lo, y_hi = V.PANEL[1] + 14, V.PANEL[3] - 14
        if abs(ly1 - ly0) > 1e-6:
            def clip(xp, yp, xo, yo):
                yc = min(max(yp, y_lo), y_hi)
                return xp + (yc - yp) * (xo - xp) / (yo - yp) if yc != yp else xp, yc
            lx0, ly0c = clip(lx0, ly0, lx1, ly1); lx1, ly1c = clip(lx1, ly1, lx0, ly0)
            ly0, ly1 = ly0c, ly1c
        V.line(fr, lx0, ly0, lx1, ly1, 7, V.GOLD, a, glow=0.55, glow_r=16)
        for i, (x_, y_) in enumerate(zip(pxs, pys)):
            col = V.mix(V.CYAN, V.MAGENTA, i / (len(X) - 1))
            V.disc(fr, x_, y_, 11, col, a, glow=0.5, glow_r=14)
        # loss sparkline in the bottom strip of the panel
        hist = [h[2] for h in r["hist"][: step + 1]] + [loss]
        sx0, sx1, sy0, sy1 = V.PANEL[0] + 60, V.PANEL[2] - 60, V.PANEL[3] - 150, V.PANEL[3] - 40
        pts = [(sx0 + (sx1 - sx0) * i / STEPS,
                sy1 - (sy1 - sy0) * min(1, math.log1p(9 * hv / LOSS0) / math.log(10))) for i, hv in enumerate(hist)]
        V.text(fr, "error over time", "Medium", 24, sx0, sy0 - 16, V.GREY, a * 0.8, anchor="left")
        V.polyline(fr, pts, 3.5, r["col"], a * 0.9, glow=0.4, glow_r=8)
        V.counters(fr, [("ERROR", f"{loss:.3f}", V.WHITE), ("STEP", f"{step} / {STEPS}", r["col"])], a)
    if t >= OUTRO:
        a = V.smooth((t - OUTRO) / 0.5)
        V.text(fr, "Guess, measure the error,", "Bold", 54, V.W / 2, 900, V.WHITE, a)
        V.text(fr, "step a little downhill.", "Bold", 54, V.W / 2, 970, V.WHITE, a)
        V.text(fr, "Repeat.", "Bold", 80, V.W / 2, 1100, V.GOLD, V.smooth((t - OUTRO - 0.6) / 0.5), glow=0.4)
        V.caption(fr, "This is gradient descent", V.smooth((t - OUTRO - 1.2) / 0.5))
    return V.finish(fr, t, DUR)


def audio(au):
    au.pad(0, DUR, amp=0.03)
    for r in ROUNDS:
        for k in range(STEPS):
            loss = r["hist"][k + 1][2]
            au.tick(r["go"] + k * STEP_DT, freq=900 + 1600 / (1 + 6 * loss), amp=0.16)
        (au.chime if r["lr"] == 0.30 else au.blip)(r["done"] + 0.3, 880 if r["lr"] == 0.30 else 330)
    au.chime(OUTRO + 0.6, 660, amp=0.14)


if __name__ == "__main__":
    V.run(render, DUR, audio, "ep01_line_fit.mp4")
