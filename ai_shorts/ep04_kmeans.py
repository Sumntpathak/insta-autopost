#!/usr/bin/env python3
"""EP04 — How AI finds groups with no teacher (k-means clustering).

Each iteration: every dot joins its nearest marker (dots recolour),
then each marker jumps to the centre of its dots (markers glide).
Rounds: 2 groups, 3 groups, 5 groups, and a bad start that settles on a wrong answer.
Run: python3 ep04_kmeans.py all
"""
import numpy as np
import aiviz as V

rng = np.random.default_rng(11)


def make(centres, n=34, spread=0.13):
    return np.concatenate([rng.normal(c, spread, (n, 2)) for c in centres])


def kmeans(X, C, max_it=12):
    hist = [dict(C=C.copy(), lab=np.argmin(((X[:, None] - C[None]) ** 2).sum(-1), 1))]
    for _ in range(max_it):
        lab = np.argmin(((X[:, None] - C[None]) ** 2).sum(-1), 1)
        newC = np.array([X[lab == k].mean(0) if (lab == k).any() else C[k] for k in range(len(C))])
        hist.append(dict(C=newC, lab=lab))
        if np.allclose(newC, C, atol=1e-6):
            break
        C = newC
    hist[-1]["lab"] = np.argmin(((X[:, None] - hist[-1]["C"][None]) ** 2).sum(-1), 1)
    return hist


three = [(-0.5, -0.45), (0.55, -0.35), (0.0, 0.55)]
ROUNDS = [
    dict(X=make([(-0.45, 0.35), (0.45, -0.35)], 40), C=np.array([[-0.9, -0.8], [-0.6, -0.9]]),
         title="2 groups", sub="2 markers", result=("2 markers:", "2 groups found"), col=V.LIME),
    dict(X=make(three), C=np.array([[-0.95, -0.1], [0.95, 0.15], [0.1, 0.98]]),
         title="3 groups", sub="3 markers", result=("3 markers:", "3 groups found"), col=V.LIME),
    dict(X=make([(-0.55, 0.5), (0.5, 0.55), (0.0, 0.0), (-0.5, -0.55), (0.55, -0.5)], 28, 0.11),
         C=np.array([[-0.95, 0.15], [0.15, 1.0], [1.0, 0.05], [-0.25, -1.0], [0.65, -1.0]]),
         title="5 groups", sub="5 markers", result=("5 markers:", "5 groups found"), col=V.LIME),
    dict(X=make(three), C=np.array([[-0.62, -0.5], [-0.38, -0.4], [0.3, 0.2]]),
         title="A bad start", sub="3 markers, unlucky first guess", result=("Bad start:", "wrong answer"), col=V.RED),
]
IT_DT = 0.95
t = 0.0
for i, r in enumerate(ROUNDS):
    r["hist"] = kmeans(r["X"], r["C"])
    r["n_it"] = len(r["hist"]) - 1
    start = t + (0.2 if i else 0.0)
    r["go"] = start + (2.0 if i == 0 else 1.0)
    r["done"] = r["go"] + r["n_it"] * IT_DT
    r["seg"] = V.Seg(start, r["done"] + 1.3)
    t = r["seg"].end
OUTRO = t + 0.2
DUR = OUTRO + 4.6
PLOT = V.Plot(-1.15, 1.15, -1.15, 1.15, pad=20)
HEADERS = [(0.0, [("How AI finds groups", V.WHITE, 66), ("with no teacher", V.GOLD, 70)])]
for r in ROUNDS:
    HEADERS.append((r["done"] + 0.3, [(r["result"][0], V.WHITE, 64), (r["result"][1], r["col"], 74)]))
HEADERS.append((OUTRO, [("No labels.", V.WHITE, 70), ("It found them itself.", V.GOLD, 66)]))
GX, GY = np.meshgrid(np.linspace(-1.15, 1.15, 90), np.linspace(1.15, -1.15, 90))
COLS = np.array(V.CLUSTER, np.float32)


def state(r, t):
    """Interpolated markers + per-dot colour for time t."""
    h = r["hist"]
    s = (t - r["go"]) / IT_DT
    if s <= 0:
        return h[0]["C"], np.tile(np.array(V.GREY, np.float32), (len(r["X"]), 1)), 0
    k = min(int(s), r["n_it"] - 1) if s < r["n_it"] else r["n_it"] - 1
    f = s - k if s < r["n_it"] else 1.0
    lab_old = h[k]["lab"] if k > 0 else None
    lab_new = h[k + 1]["lab"]
    ca = V.smooth(f / 0.45)                               # phase A: dots recolour
    cb = V.smoother((f - 0.45) / 0.55)                    # phase B: markers glide
    old = COLS[lab_old] if lab_old is not None else np.tile(np.array(V.GREY, np.float32), (len(r["X"]), 1))
    cols = old * (1 - ca) + COLS[lab_new] * ca
    C = h[k]["C"] * (1 - cb) + h[k + 1]["C"] * cb
    return C, cols, min(r["n_it"], k + (1 if cb > 0.5 else 0))


def render(t):
    fr = V.background()
    V.header(fr, t, HEADERS)
    x0, y0, x1, y1 = V.PANEL
    for n, r in enumerate(ROUNDS, 1):
        a = r["seg"].alpha(t)
        if a <= 0:
            continue
        V.round_titles(fr, n, r["title"], r["sub"], a, r["col"] if t > r["done"] else V.GREY)
        C, cols, it = state(r, t)
        # territory of each marker (faint Voronoi regions)
        d = (GX[..., None] - C[:, 0]) ** 2 + (GY[..., None] - C[:, 1]) ** 2
        own = np.argmin(d, -1)
        terr = COLS[own] * 0.13
        if t > r["go"]:
            V.field(fr, terr, x0 + 2, y0 + 2, x1 - 2, y1 - 2, a, mask_round=26)
        pxs, pys = PLOT.px(r["X"][:, 0], r["X"][:, 1])
        for xp, yp, c in zip(pxs, pys, cols):
            V.disc(fr, float(xp), float(yp), 9, tuple(c), a, glow=0.45, glow_r=11)
        cx, cy = PLOT.px(C[:, 0], C[:, 1])
        for k, (u, v) in enumerate(zip(cx, cy)):
            col = V.CLUSTER[k]
            V.disc(fr, float(u), float(v), 26, col, a, ring=5, glow=0.8, glow_r=18)
            V.line(fr, u - 12, v, u + 12, v, 4, V.WHITE, a)
            V.line(fr, u, v - 12, u, v + 12, 4, V.WHITE, a)
        spread = float(np.mean(np.min(((r["X"][:, None] - C[None]) ** 2).sum(-1), 1)))
        V.counters(fr, [("MOVES", str(it), r["col"] if t > r["done"] else V.WHITE),
                        ("SPREAD", f"{spread:.3f}", V.WHITE)], a)
    if t >= OUTRO:
        a = V.smooth((t - OUTRO) / 0.5)
        V.text(fr, "Join the nearest marker.", "Bold", 56, V.W / 2, 880, V.WHITE, a)
        V.text(fr, "Move to the middle.", "Bold", 56, V.W / 2, 950, V.WHITE, a)
        V.text(fr, "Repeat.", "Bold", 80, V.W / 2, 1080, V.GOLD, V.smooth((t - OUTRO - 0.6) / 0.5), glow=0.4)
        V.caption(fr, "Real systems try many starts and keep the best", V.smooth((t - OUTRO - 1.2) / 0.5))
    return V.finish(fr, t, DUR)


def audio(au):
    au.pad(0, DUR, notes=(233.1, 293.7, 349.2), amp=0.03)
    for r in ROUNDS:
        for k in range(r["n_it"]):
            au.whoosh(r["go"] + k * IT_DT + 0.40, amp=0.06, dur=0.5)
            au.blip(r["go"] + k * IT_DT + 0.05, 520 + 90 * k, 0.11)
        (au.buzz if r["col"] == V.RED else au.chime)(r["done"] + 0.3)
    au.chime(OUTRO + 0.6, 698, amp=0.14)


if __name__ == "__main__":
    V.run(render, DUR, audio, "ep04_kmeans.mp4")
