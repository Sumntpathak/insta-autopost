#!/usr/bin/env python3
"""EP08 — How AI turns noise into an image (the diffusion idea).

Forward process: x_s = sqrt(ā(s))·x0 + sqrt(1 − ā(s))·ε with a cosine schedule.
On screen we run it backwards from pure noise (s = 1) to the clean shape (s = 0),
the path an image generator learns to follow. Here the clean shape is known,
so this is an exact illustration of the process, not a trained model.
Rounds: a heart, a star, a spiral galaxy.
Run: python3 ep08_diffusion.py all
"""
import math
import numpy as np
import aiviz as V

rng = np.random.default_rng(12)
NP = 1400


def heart(n):
    pts = []
    while len(pts) < n:
        x, y = rng.uniform(-1.3, 1.3, 2)
        if (x * x + y * y - 1) ** 3 - x * x * y ** 3 <= 0:
            pts.append((x, y))
    p = np.array(pts) * 0.62
    return p - [0, 0.05]


def star_np(n, k=5):
    """Star without matplotlib: sample in polar coords against the star radius."""
    out = []
    while len(out) < n:
        th = rng.uniform(0, 2 * np.pi); r = math.sqrt(rng.uniform(0, 1)) * 0.86
        a = (th - np.pi / 2) % (2 * np.pi / k) / (2 * np.pi / k)
        edge = 0.36 + (0.86 - 0.36) * abs(1 - 2 * a)      # tip at the arm, notch between arms
        if r <= edge:
            out.append((math.cos(th) * r, math.sin(th) * r))
    return np.array(out)


def galaxy(n):
    arm = rng.integers(0, 2, n)
    u = rng.uniform(0, 1, n) ** 0.7
    th = u * 3.6 * np.pi + arm * np.pi
    r = 0.06 + u * 0.8
    p = np.stack([np.cos(th) * r, np.sin(th) * r], 1) + rng.normal(0, 0.035 + 0.04 * u[:, None], (n, 2))
    core = rng.normal(0, 0.09, (n // 6, 2))
    return np.concatenate([p, core])[:n]


def abar(s):
    """Cosine noise schedule: 1 at s=0 (clean), ~0 at s=1 (pure noise)."""
    return math.cos((s + 0.008) / 1.008 * math.pi / 2) ** 2 / math.cos(0.008 / 1.008 * math.pi / 2) ** 2


SHAPES = [
    dict(x0=heart(NP), title="A heart", hue=(0.92, 1.08), result="a heart"),
    dict(x0=star_np(NP), title="A star", hue=(0.10, 0.18), result="a star"),
    dict(x0=galaxy(NP), title="A spiral galaxy", hue=(0.52, 0.80), result="a galaxy"),
]
DEN_T, HOLD0 = 4.6, 0.8
t = 0.0
for i, r in enumerate(SHAPES):
    r["eps"] = rng.normal(0, 1, (NP, 2)) * 0.42
    r["jit"] = rng.normal(0, 1, (240, NP, 2))      # small per-step wobble, shrinking with noise
    ang = np.arctan2(r["x0"][:, 1], r["x0"][:, 0]) / (2 * np.pi) + 0.5
    rad = np.linalg.norm(r["x0"], axis=1)
    hue = r["hue"][0] + (r["hue"][1] - r["hue"][0]) * (0.6 * ang + 0.4 * rad)
    r["cols"] = np.array([V.hsv(h, 0.65, 1.0) for h in hue], np.float32)
    start = t + (0.2 if i else 0.0)
    r["go"] = start + (2.0 if i == 0 else 0.9) + HOLD0
    r["done"] = r["go"] + DEN_T
    r["seg"] = V.Seg(start, r["done"] + 1.6)
    t = r["seg"].end
OUTRO = t + 0.2
DUR = OUTRO + 4.4
PLOT = V.Plot(-1.25, 1.25, -1.25, 1.25, pad=10)
HEADERS = [(0.0, [("How AI turns noise", V.WHITE, 68), ("into an image", V.GOLD, 74)])]
for r in SHAPES:
    HEADERS.append((r["done"] + 0.3, [("Step 0:", V.WHITE, 64), (r["result"], V.hsv(r["hue"][0]), 80)]))
HEADERS.append((OUTRO, [("Image generators learn", V.WHITE, 62), ("to undo noise", V.GOLD, 74)]))


def positions(r, t):
    s = 1.0 - V.clamp((t - r["go"]) / DEN_T)       # steps count down evenly
    ab = abar(s)
    x = math.sqrt(ab) * r["x0"] + math.sqrt(1 - ab) * r["eps"]
    k = int((t * 30) % 240)
    x = x + r["jit"][k] * 0.012 * math.sqrt(1 - ab)
    return x, s, ab


def render(t):
    fr = V.background(grid=False)
    V.header(fr, t, HEADERS)
    for n, r in enumerate(SHAPES, 1):
        a = r["seg"].alpha(t)
        if a <= 0:
            continue
        V.round_titles(fr, n, r["title"], "from pure noise", a, V.hsv(r["hue"][0]))
        x, s, ab = positions(r, t)
        X, Y = PLOT.px(x[:, 0], x[:, 1])
        grey = np.array((180, 186, 205), np.float32)
        k = math.sqrt(ab)
        cols = grey * (1 - k) + r["cols"] * k
        V.particles(fr, X, Y, cols * (0.9 + 0.4 * k), a, size=1.5, glow=0.35 + 0.6 * k)
        step = int(round(s * 1000))
        noise = math.sqrt(1 - ab) * 100
        V.counters(fr, [("DENOISING STEP", f"{step:,}", V.WHITE if step else V.hsv(r["hue"][0])),
                        ("NOISE LEFT", f"{noise:.0f}%", V.WHITE)], a)
        V.caption(fr, "an illustration of the diffusion process", a * 0.8)
    if t >= OUTRO:
        a = V.smooth((t - OUTRO) / 0.5)
        V.text(fr, "Add noise until nothing is left.", "Bold", 52, V.W / 2, 900, V.WHITE, a)
        V.text(fr, "Train a network to undo it,", "Bold", 52, V.W / 2, 970, V.WHITE, a)
        V.text(fr, "one small step at a time.", "Bold", 60, V.W / 2, 1090, V.GOLD, V.smooth((t - OUTRO - 0.6) / 0.5), glow=0.4)
        V.caption(fr, "This is how diffusion models make pictures", V.smooth((t - OUTRO - 1.2) / 0.5))
    return V.finish(fr, t, DUR)


def audio(au):
    au.pad(0, DUR, notes=(220, 293.7, 370), amp=0.03)
    for r in SHAPES:
        au.whoosh(r["go"] - 0.2, amp=0.12, dur=DEN_T + 0.4)
        au.sweep(r["go"], 180, 880, amp=0.06, dur=DEN_T)
        for k in range(20):
            au.tick(r["go"] + k * DEN_T / 20, 800 + 60 * k, 0.07)
        au.chime(r["done"] + 0.1, 880)
    au.chime(OUTRO + 0.6, 660, amp=0.14)


if __name__ == "__main__":
    V.run(render, DUR, audio, "ep08_diffusion.mp4")
