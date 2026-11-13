#!/usr/bin/env python3
"""EP09 — Why AI needs attention.

Each word decides how much to "look at" every other word. Arc thickness is
the attention weight. The weights here are illustrative (hand-set to show the
idea, in the spirit of the classic "it = animal / street" example), not taken
from a real model; the caption says so on screen.
Round 1: "sat" looks at who sat. Round 2: "it" = the animal (tired).
Round 3: change one word and "it" = the street (wide).
Run: python3 ep09_attention.py all
"""
import math
import numpy as np
import aiviz as V

S2 = "The animal didn't cross the street because it was too".split()
ROUNDS = [
    dict(words="The cat sat on the mat".split(), focus=2,
         w=[0.05, 0.48, 0.10, 0.07, 0.05, 0.25], key=1,
         title="Who sat?", result=("“sat” looks at", "“cat”"), col=V.CYAN, type_dt=0.16),
    dict(words=S2 + ["tired"], focus=7,
         w=[0.02, 0.58, 0.03, 0.04, 0.02, 0.10, 0.03, 0.05, 0.03, 0.02, 0.08], key=1,
         title="What is “it”?", result=("“it” means", "the animal"), col=V.MAGENTA, type_dt=0.12),
    dict(words=S2 + ["wide"], focus=7,
         w=[0.02, 0.09, 0.03, 0.04, 0.03, 0.55, 0.03, 0.05, 0.03, 0.01, 0.12], key=5,
         title="Change one word", result=("Now “it” means", "the street"), col=V.GOLD, type_dt=0.0),
]
FONT, FS = "SemiBold", 54
CHIP_H, GAP_X, GAP_Y = 98, 20, 150
X0, Y0, X1, Y1 = V.PANEL


def layout(words):
    """Wrap word chips into centred lines inside the panel's lower part."""
    widths = [V.text_width(w, FONT, FS) + 44 for w in words]
    lines, cur, cw = [], [], 0
    maxw = X1 - X0 - 80
    for i, w in enumerate(widths):
        if cur and cw + GAP_X + w > maxw:
            lines.append(cur); cur, cw = [], 0
        cur.append(i); cw += (GAP_X if len(cur) > 1 else 0) + w
    lines.append(cur)
    pos = [None] * len(words)
    top = Y0 + (900 - (len(lines) - 1) * GAP_Y) / 2 + 60     # centred, nudged down to leave room for arcs
    for li, idx in enumerate(lines):
        total = sum(widths[i] for i in idx) + GAP_X * (len(idx) - 1)
        x = (X0 + X1) / 2 - total / 2
        for i in idx:
            pos[i] = (x + widths[i] / 2, top + li * GAP_Y, widths[i])
            x += widths[i] + GAP_X
    return pos


t = 0.0
for i, r in enumerate(ROUNDS):
    r["pos"] = layout(r["words"])
    start = t + (0.2 if i else 0.0)
    r["start"] = start
    r["typed"] = start + (1.6 if i == 0 else 0.6) + r["type_dt"] * len(r["words"])
    r["swap"] = r["typed"] if r["type_dt"] == 0 else None
    r["focus_t"] = r["typed"] + (0.9 if r["swap"] else 0.4)
    r["arcs_t"] = r["focus_t"] + 0.5
    r["done"] = r["arcs_t"] + 1.8
    r["seg"] = V.Seg(start, r["done"] + 1.7)
    t = r["seg"].end
OUTRO = t + 0.2
DUR = OUTRO + 4.4
HEADERS = [(0.0, [("Why AI needs", V.WHITE, 72), ("attention", V.GOLD, 90)])]
for r in ROUNDS:
    HEADERS.append((r["done"] + 0.2, [(r["result"][0], V.WHITE, 64), (r["result"][1], r["col"], 80)]))
HEADERS.append((OUTRO, [("This one idea powers", V.WHITE, 62), ("modern chatbots", V.GOLD, 74)]))


def bezier(p0, p1, lift, k=1.0, n=48):
    (ax, ay), (bx, by) = p0, p1
    cx, cy = (ax + bx) / 2, min(ay, by) - lift
    pts = []
    for j in range(int(n * k) + 1):
        u = j / n
        pts.append(((1 - u) ** 2 * ax + 2 * (1 - u) * u * cx + u * u * bx,
                    (1 - u) ** 2 * ay + 2 * (1 - u) * u * cy + u * u * by))
    return pts


def weight_col(w):
    return V.mix(V.VIOLET, V.MAGENTA, min(1, w / 0.2)) if w < 0.2 else V.mix(V.MAGENTA, V.GOLD, min(1, (w - 0.2) / 0.35))


def render(t):
    fr = V.background(grid=False)
    V.header(fr, t, HEADERS)
    for n, r in enumerate(ROUNDS, 1):
        a = r["seg"].alpha(t)
        if a <= 0:
            continue
        V.round_titles(fr, n, r["title"], None, a)
        words, pos, w = r["words"], r["pos"], r["w"]
        fx, fy, _ = pos[r["focus"]]
        ka = V.smoother((t - r["arcs_t"]) / 1.2)
        kw = V.smooth((t - r["arcs_t"] - 0.6) / 1.0)
        # attention arcs behind the chips
        if ka > 0:
            for j in sorted(range(len(words)), key=lambda j: w[j]):
                if j == r["focus"]:
                    continue
                tx, ty, _ = pos[j]
                dist = math.hypot(tx - fx, ty - fy)
                pts = bezier((fx, fy - CHIP_H / 2), (tx, ty - CHIP_H / 2), 70 + 0.28 * dist, ka)
                if len(pts) > 1:
                    V.polyline(fr, pts, 2 + 26 * w[j], weight_col(w[j]), a * (0.35 + 0.65 * min(1, w[j] * 3)),
                               glow=0.5 if w[j] > 0.2 else 0.15, glow_r=14)
                if w[j] > 0.2 and ka >= 1:            # pulses travelling along strong arcs
                    full = bezier((fx, fy - CHIP_H / 2), (tx, ty - CHIP_H / 2), 70 + 0.28 * dist)
                    for q in range(3):
                        u = ((t * 0.7 + q / 3) % 1.0)
                        px, py = full[int(u * (len(full) - 1))]
                        V.disc(fr, px, py, 7, V.WHITE, a * 0.8, glow=0.8)
        # word chips
        for j, word in enumerate(words):
            if r["swap"] is not None:
                appear = 1.0 if j < len(words) - 1 else V.ease_out((t - r["swap"]) / 0.35)
            else:
                appear = V.ease_out((t - r["start"] - (1.6 if n == 1 else 0.6) - j * r["type_dt"]) / 0.25)
            if appear <= 0:
                continue
            cx, cy, cw = pos[j]
            cy2 = cy + (1 - appear) * 30
            hot = kw * w[j] if j != r["focus"] else 0
            is_focus = j == r["focus"] and t >= r["focus_t"]
            edge = r["col"] if is_focus else (weight_col(w[j]) if hot > 0.02 else (90, 96, 128))
            fill = tuple(c * 0.16 for c in edge) if (is_focus or hot > 0.08) else (16, 18, 32)
            glow = (0.9 if is_focus else 0) + 3.0 * hot
            V.rect(fr, cx - cw / 2, cy2 - CHIP_H / 2, cx + cw / 2, cy2 + CHIP_H / 2, (12, 13, 24), a * appear, radius=22)
            V.rect(fr, cx - cw / 2, cy2 - CHIP_H / 2, cx + cw / 2, cy2 + CHIP_H / 2, fill, a * appear, radius=22, glow=glow, glow_r=18)
            V.rect(fr, cx - cw / 2, cy2 - CHIP_H / 2, cx + cw / 2, cy2 + CHIP_H / 2, edge, a * appear, radius=22, outline=3)
            V.text(fr, word, FONT, FS, cx, cy2 - 2, V.WHITE, a * appear)
            if j != r["focus"] and w[j] >= 0.08 and kw > 0:
                V.text(fr, f"{w[j] * 100 * kw:.0f}%", "Bold", 34, cx, cy2 + CHIP_H / 2 + 30, weight_col(w[j]), a * kw)
        key = r["key"]
        label = f"“{words[r['focus']]}” LOOKS AT “{words[key]}”"
        V.counter(fr, label.upper(), f"{w[key] * 100 * kw:.0f}%", a, r["col"] if kw >= 1 else V.WHITE)
        V.caption(fr, "illustrative attention weights", a * 0.8)
    if t >= OUTRO:
        a = V.smooth((t - OUTRO) / 0.5)
        V.text(fr, "Every word asks:", "Bold", 58, V.W / 2, 880, V.WHITE, a)
        V.text(fr, "which other words matter to me?", "Bold", 50, V.W / 2, 955, V.WHITE, a)
        V.text(fr, "That’s attention.", "Bold", 76, V.W / 2, 1090, V.GOLD, V.smooth((t - OUTRO - 0.6) / 0.5), glow=0.4)
        V.caption(fr, "The core idea inside transformers", V.smooth((t - OUTRO - 1.2) / 0.5))
    return V.finish(fr, t, DUR)


def audio(au):
    au.pad(0, DUR, notes=(196, 246.9, 311.1), amp=0.03)
    for n, r in enumerate(ROUNDS, 1):
        if r["swap"] is None:
            for j in range(len(r["words"])):
                au.tick(r["start"] + (1.6 if n == 1 else 0.6) + j * r["type_dt"], 1800, 0.10)
        else:
            au.blip(r["swap"], 520, 0.14)
        au.blip(r["focus_t"], 880, 0.12)
        au.sweep(r["arcs_t"], 400, 1200, amp=0.06, dur=1.2)
        au.chime(r["done"] + 0.2, 784)
    au.chime(OUTRO + 0.6, 659, amp=0.14)


if __name__ == "__main__":
    V.run(render, DUR, audio, "ep09_attention.mp4")
