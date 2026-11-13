#!/usr/bin/env python3
"""EP05 — Memorising is not learning (overfitting).

Least-squares polynomial fits of growing flexibility to 12 noisy training dots.
Then 12 new dots arrive: the honest test.
Round 1: a straight line (too simple). Round 2: a gentle curve (just right).
Round 3: a curve flexible enough to pass through every dot (memorises the noise).
Run: python3 ep05_overfit.py all
"""
import numpy as np
from numpy.polynomial import chebyshev as C
import aiviz as V

rng = np.random.default_rng(8)


def truth(x):
    return 0.75 * np.sin(2.3 * x)


XT = np.sort(np.concatenate([np.linspace(-0.95, 0.95, 12) + rng.uniform(-0.04, 0.04, 12)]))
YT = truth(XT) + rng.normal(0, 0.16, XT.size)
XN = np.sort(rng.uniform(-0.95, 0.95, 12))
YN = truth(XN) + rng.normal(0, 0.16, XN.size)

ROUNDS = [
    dict(deg=1, title="Too simple", sub="a straight line", result=("Too simple:", "misses the pattern"), col=V.CYAN),
    dict(deg=3, title="Just right", sub="a gentle curve", result=("Just right:", "it learned"), col=V.LIME),
    dict(deg=11, title="Too flexible", sub="a curve through every dot", result=("Too flexible:", "it memorised"), col=V.MAGENTA),
]
for r in ROUNDS:
    r["coef"] = C.chebfit(XT, YT, r["deg"])
    r["train"] = float(np.mean((C.chebval(XT, r["coef"]) - YT) ** 2))
    r["test"] = float(np.mean((C.chebval(XN, r["coef"]) - YN) ** 2))

FIT_T, TEST_GAP = 1.8, 1.6
t = 0.0
for i, r in enumerate(ROUNDS):
    start = t + (0.2 if i else 0.0)
    r["go"] = start + (2.0 if i == 0 else 0.9)
    r["fit_done"] = r["go"] + FIT_T
    r["test_go"] = r["fit_done"] + 0.5
    r["done"] = r["test_go"] + TEST_GAP
    r["seg"] = V.Seg(start, r["done"] + 1.6)
    t = r["seg"].end
OUTRO = t + 0.2
DUR = OUTRO + 4.6
PLOT = V.Plot(-1.05, 1.05, -1.45, 1.45, pad=30)
HEADERS = [(0.0, [("Memorising", V.WHITE, 74), ("is not learning", V.GOLD, 74)])]
for r in ROUNDS:
    HEADERS.append((r["done"] + 0.3, [(r["result"][0], V.WHITE, 64), (r["result"][1], r["col"], 74)]))
HEADERS.append((OUTRO, [("Perfect on practice", V.WHITE, 64), ("≠ smart", V.GOLD, 80)]))
XS = np.linspace(-1.02, 1.02, 340)


def curve_runs(ys):
    """Split the curve where it leaves the panel, so it's clipped cleanly."""
    px, py = PLOT.px(XS, ys)
    lo, hi = V.PANEL[1] + 10, V.PANEL[3] - 10
    runs, cur = [], []
    for u, v in zip(px, py):
        if lo <= v <= hi:
            cur.append((float(u), float(v)))
        else:
            if cur:
                cur.append((float(u), float(min(max(v, lo), hi))))
                runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return runs


def render(t):
    fr = V.background()
    V.header(fr, t, HEADERS)
    for n, r in enumerate(ROUNDS, 1):
        a = r["seg"].alpha(t)
        if a <= 0:
            continue
        V.round_titles(fr, n, r["title"], r["sub"], a, r["col"])
        k = V.smoother((t - r["go"]) / FIT_T)          # curve morphs from flat to fitted
        fit = C.chebval(XS, r["coef"])
        ys = np.mean(YT) * (1 - k) + fit * k
        for run in curve_runs(ys):
            V.polyline(fr, run, 6, r["col"], a, glow=0.6, glow_r=14)
        # training dots
        tx, ty = PLOT.px(XT, YT)
        for xp, yp in zip(tx, ty):
            V.disc(fr, float(xp), float(yp), 12, V.WHITE, a, glow=0.5, glow_r=12)
        # new dots fall in: the test
        kt = V.clamp((t - r["test_go"]) / 0.8)
        if kt > 0:
            nx, ny = PLOT.px(XN, YN)
            _, fy = PLOT.px(XN, C.chebval(XN, r["coef"]))
            for j, (xp, yp, fp) in enumerate(zip(nx, ny, fy)):
                kj = V.ease_out((t - r["test_go"] - j * 0.05) / 0.45)
                if kj <= 0:
                    continue
                yy = float(yp) - (1 - kj) * 160
                fpc = min(max(float(fp), V.PANEL[1] + 10), V.PANEL[3] - 10)
                e = min(1.0, abs(yy - fpc) / 200)
                V.line(fr, float(xp), yy, float(xp), fpc, 3, V.mix(V.LIME, V.RED, e), a * kj * 0.8)
                V.rect(fr, float(xp) - 11, yy - 11, float(xp) + 11, yy + 11, V.GOLD, a * kj, radius=4, glow=0.5)
        train = r["train"] * k + float(np.mean((np.mean(YT) - YT) ** 2)) * (1 - k)
        test_val = f"{r['test'] * kt:.3f}" if kt > 0 else "?"
        tcol = V.RED if r["test"] > 0.1 and kt >= 1 else (V.LIME if kt >= 1 else V.WHITE)
        V.counters(fr, [("PRACTICE ERROR", f"{train:.3f}", V.WHITE), ("NEW-DATA ERROR", test_val, tcol)], a)
        lx, ly = V.PANEL[0] + 46, V.PANEL[1] + 38
        V.disc(fr, lx, ly, 9, V.WHITE, a * 0.9)
        V.text(fr, "practice dots", "Medium", 28, lx + 22, ly, V.WHITE, a * 0.8, anchor="left")
        ka = a * min(1, kt * 3)
        rx = V.PANEL[2] - 46 - V.text_width("new dots", "Medium", 28) - 22
        V.rect(fr, rx - 9, ly - 9, rx + 9, ly + 9, V.GOLD, ka, radius=3)
        V.text(fr, "new dots", "Medium", 28, rx + 22, ly, V.GOLD, ka, anchor="left")
    if t >= OUTRO:
        a = V.smooth((t - OUTRO) / 0.5)
        V.text(fr, "Learning means doing well", "Bold", 54, V.W / 2, 900, V.WHITE, a)
        V.text(fr, "on things you’ve never seen.", "Bold", 54, V.W / 2, 970, V.WHITE, a)
        V.text(fr, "That’s the real test.", "Bold", 70, V.W / 2, 1100, V.GOLD, V.smooth((t - OUTRO - 0.6) / 0.5), glow=0.4)
        V.caption(fr, "This is called overfitting", V.smooth((t - OUTRO - 1.2) / 0.5))
    return V.finish(fr, t, DUR)


def audio(au):
    au.pad(0, DUR, notes=(207.7, 261.6, 311.1), amp=0.03)
    for r in ROUNDS:
        au.sweep(r["go"], 300, 300 + 60 * r["deg"], amp=0.07, dur=FIT_T)
        for j in range(len(XN)):
            au.tick(r["test_go"] + j * 0.05 + 0.4, 1500 + 60 * j, 0.12)
        (au.chime if r["deg"] == 3 else au.buzz)(r["done"] + 0.3)
    au.chime(OUTRO + 0.6, 622, amp=0.14)


if __name__ == "__main__":
    V.run(render, DUR, audio, "ep05_overfit.mp4")
