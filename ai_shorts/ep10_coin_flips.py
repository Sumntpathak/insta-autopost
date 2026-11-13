#!/usr/bin/env python3
"""EP10 — Learning from one coin flip at a time (Bayesian updating).

A coin lands heads with a hidden probability of 0.70. After every flip the
AI updates its belief: an exact Beta(1 + heads, 1 + tails) posterior.
The curve is that belief: where it thinks the true value is, and how sure it is.
Rounds: 10 flips, 100 flips, 1,000 flips. The true value is revealed at the end.
Run: python3 ep10_coin_flips.py all
"""
import math
import numpy as np
from scipy.stats import beta as Beta
import aiviz as V

P_TRUE = 0.70
rng = np.random.default_rng(21)
ROUNDS = [
    dict(n=10, title="10 flips", result=("10 flips:", "a rough guess"), col=V.CYAN, cols=10, cell=72),
    dict(n=100, title="100 flips", result=("100 flips:", "getting sure"), col=V.MAGENTA, cols=20, cell=36),
    dict(n=1000, title="1,000 flips", result=("1,000 flips:", "confident"), col=V.GOLD, cols=50, cell=15.2),
]
FLIP_T = 4.4
t = 0.0
for i, r in enumerate(ROUNDS):
    r["flips"] = rng.random(r["n"]) < P_TRUE
    r["cum"] = np.concatenate([[0], np.cumsum(r["flips"])])
    start = t + (0.2 if i else 0.0)
    r["go"] = start + (2.0 if i == 0 else 0.9)
    r["done"] = r["go"] + FLIP_T
    r["reveal"] = r["done"] + 0.5
    r["seg"] = V.Seg(start, r["done"] + 2.0)
    t = r["seg"].end
OUTRO = t + 0.2
DUR = OUTRO + 4.6
HEADERS = [(0.0, [("Learning from one", V.WHITE, 68), ("coin flip at a time", V.GOLD, 70)])]
for r in ROUNDS:
    HEADERS.append((r["done"] + 0.3, [(r["result"][0], V.WHITE, 64), (r["result"][1], r["col"], 78)]))
HEADERS.append((OUTRO, [("More data,", V.WHITE, 72), ("more confidence", V.GOLD, 74)]))

X0, Y0, X1, Y1 = V.PANEL
TOK_TOP = Y0 + 40                       # coin grid area
CURVE = V.Plot(0, 1, 0, 1, rect=(X0, Y0 + 400, X1, Y1), pad=50)
XS = np.linspace(0, 1, 361)
HEADS, TAILS = V.GOLD, V.VIOLET


def count_at(r, t):
    """Flips shown so far: evenly paced, easing into the end of the round."""
    k = V.clamp((t - r["go"]) / FLIP_T)
    k = 1 - (1 - k) ** 1.6 if r["n"] > 10 else k
    return int(math.floor(k * r["n"] + 1e-9)), k * r["n"]


def render(t):
    fr = V.background(grid=False)
    V.header(fr, t, HEADERS)
    for n_r, r in enumerate(ROUNDS, 1):
        a = r["seg"].alpha(t)
        if a <= 0:
            continue
        V.round_titles(fr, n_r, r["title"], "true chance of heads: hidden", a)
        n, nf = count_at(r, t)
        h = int(r["cum"][n]); tl = n - h
        # coin grid
        cols, cell = r["cols"], r["cell"]
        rows = math.ceil(r["n"] / cols)
        gx0 = (X0 + X1) / 2 - cols * cell / 2
        for j in range(min(r["n"], math.ceil(nf))):
            pop = V.ease_out(nf - j)                      # each coin pops in as the count reaches it
            if pop <= 0:
                continue
            cx = gx0 + (j % cols + 0.5) * cell
            cy = TOK_TOP + (j // cols + 0.5) * cell
            col = HEADS if r["flips"][j] else TAILS
            rad = cell * 0.40 * (0.6 + 0.4 * pop)
            if cell > 30:
                V.disc(fr, cx, cy, rad, col, a * pop, glow=0.5, glow_r=rad * 0.8)
                V.text(fr, "H" if r["flips"][j] else "T", "Bold", int(cell * 0.42), cx, cy, (20, 16, 30), a * pop)
            else:
                V.rect(fr, cx - cell * 0.4, cy - cell * 0.4, cx + cell * 0.4, cy + cell * 0.4, col, a * pop, radius=2)
        # belief curve (posterior), scaled to its own peak so the narrowing is easy to see
        pdf = Beta.pdf(XS, 1 + h, 1 + tl)
        peak = pdf.max()
        ys = pdf / peak * 0.92
        px, py = CURVE.px(XS, ys)
        base = CURVE.px(0, 0)[1]
        lo, hi = Beta.ppf([0.025, 0.975], 1 + h, 1 + tl)
        band = (XS >= lo) & (XS <= hi)
        for j in range(0, len(XS) - 1, 2):              # filled area as thin columns
            colr = r["col"] if band[j] else V.DIM
            V.rect(fr, float(px[j]), float(py[j]), float(px[j + 2 if j + 2 < len(XS) else j + 1]), float(base),
                   tuple(c * 0.28 for c in colr), a, radius=0)
        V.polyline(fr, list(zip(px.tolist(), py.tolist())), 5, r["col"], a, glow=0.6, glow_r=14)
        V.line(fr, CURVE.sx0, float(base), CURVE.sx1, float(base), 2, V.GREY, a * 0.8)
        for v in (0, 0.25, 0.5, 0.75, 1.0):
            vx = float(CURVE.px(v, 0)[0])
            V.line(fr, vx, float(base), vx, float(base) + 10, 2, V.GREY, a * 0.7)
            V.text(fr, f"{v:g}", "Medium", 26, vx, float(base) + 32, V.GREY, a * 0.8)
        V.text(fr, "chance of heads", "Medium", 26, (CURVE.sx0 + CURVE.sx1) / 2, float(base) + 64, V.GREY, a * 0.7)
        mean = (1 + h) / (2 + n)
        mx = float(CURVE.px(mean, 0)[0])
        V.dashed(fr, mx, float(base), mx, float(CURVE.px(0, 0.95)[1]), 3, V.WHITE, a * 0.7)
        # reveal the truth
        kr = V.smooth((t - r["reveal"]) / 0.5)
        if kr > 0:
            tx = float(CURVE.px(P_TRUE, 0)[0])
            V.line(fr, tx, float(base), tx, float(CURVE.px(0, 1.0)[1]), 4, V.LIME, a * kr, glow=0.6)
            V.tag(fr, "true value 0.70", tx, float(CURVE.px(0, 1.0)[1]) - 30, V.LIME, a * kr, size=26)
        pm = 1.96 * math.sqrt(mean * (1 - mean) / (n + 3))
        V.counter(fr, "FLIPS", V.fmt(n), a, V.WHITE, x=V.W * 0.25, size=80)
        V.counter(fr, "BEST GUESS", f"{mean:.2f} ± {pm:.2f}", a, r["col"], x=V.W * 0.66, size=72)
        V.caption(fr, f"heads {h}   ·   tails {tl}", a * 0.85)
    if t >= OUTRO:
        a = V.smooth((t - OUTRO) / 0.5)
        V.text(fr, "Every new flip nudges", "Bold", 56, V.W / 2, 900, V.WHITE, a)
        V.text(fr, "the belief a little.", "Bold", 56, V.W / 2, 970, V.WHITE, a)
        V.text(fr, "Sure, but never certain.", "Bold", 64, V.W / 2, 1100, V.GOLD, V.smooth((t - OUTRO - 0.6) / 0.5), glow=0.4)
        V.caption(fr, "This is Bayesian learning", V.smooth((t - OUTRO - 1.2) / 0.5))
    return V.finish(fr, t, DUR)


def audio(au):
    au.pad(0, DUR, notes=(220, 277.2, 329.6), amp=0.03)
    for r in ROUNDS:
        last = 0
        steps = 240
        for s in range(steps + 1):
            tt = r["go"] + FLIP_T * s / steps
            n, _ = count_at(r, tt)
            for j in range(last, n):
                if j - last < 3:            # cap the clicks per moment for the 1,000-flip round
                    au.tick(tt, 2000 if r["flips"][j] else 1300, 0.10 if r["n"] <= 100 else 0.05)
            last = n
        au.chime(r["reveal"], 784)
    au.chime(OUTRO + 0.6, 659, amp=0.14)


if __name__ == "__main__":
    V.run(render, DUR, audio, "ep10_coin_flips.mp4")
