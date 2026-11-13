#!/usr/bin/env python3
"""EP03 — One neuron can't solve this. Two layers can.

Real training with numpy (full-batch gradient descent on cross-entropy).
The background shows the network's live decision: cyan side vs magenta side.
Round 1: two blobs, a single neuron separates them.
Round 2: XOR (opposite corners match), a single neuron is stuck.
Round 3: same XOR, add a hidden layer of 8 neurons and it bends the boundary.
Run: python3 ep03_layers.py all
"""
import numpy as np
import aiviz as V

rng = np.random.default_rng(4)


def blobs():
    a = rng.normal((-0.45, -0.35), 0.17, (40, 2)); b = rng.normal((0.45, 0.4), 0.17, (40, 2))
    return np.concatenate([a, b]), np.repeat([0, 1], 40)


def xor():
    c = np.array([[-.5, -.5], [.5, .5], [-.5, .5], [.5, -.5]])
    X = np.concatenate([c[i] + rng.normal(0, .14, (22, 2)) for i in range(4)])
    return X, np.repeat([0, 0, 1, 1], 22)


GRID = np.stack(np.meshgrid(np.linspace(-1.1, 1.1, 80), np.linspace(1.1, -1.1, 80)), -1).reshape(-1, 2)


def train(X, y, hidden, epochs, lr, snaps=90, seed=1):
    r = np.random.default_rng(seed)
    if hidden:
        W1 = r.normal(0, 1, (2, hidden)); b1 = np.zeros(hidden); W2 = r.normal(0, 1, hidden); b2 = 0.0
    else:
        w = np.array([-1.2, 0.9]); b = 0.6
    keep = set(np.unique(np.round(np.geomspace(1, epochs, snaps)).astype(int)) - 1) | {0}
    out = []

    def forward(Z):
        if hidden:
            return 1 / (1 + np.exp(-(np.tanh(Z @ W1 + b1) @ W2 + b2)))
        return 1 / (1 + np.exp(-(Z @ w + b)))
    for e in range(epochs):
        if e in keep:
            p = forward(X)
            out.append(dict(epoch=e + 1, acc=float(((p > 0.5) == y).mean()), grid=forward(GRID).reshape(80, 80),
                            pred=p > 0.5))
        p = forward(X); g = (p - y) / len(y)
        if hidden:
            h = np.tanh(X @ W1 + b1)
            gh = np.outer(g, W2) * (1 - h ** 2)
            W2 -= lr * h.T @ g; b2 -= lr * g.sum(); W1 -= lr * X.T @ gh; b1 -= lr * gh.sum(0)
        else:
            w -= lr * X.T @ g; b -= lr * g.sum()
    return out


X1, y1 = blobs()
X2, y2 = xor()
ROUNDS = [
    dict(X=X1, y=y1, hidden=0, epochs=300, lr=0.8, title="Two groups", sub="1 neuron",
         result=("1 neuron:", "solved"), col=V.LIME),
    dict(X=X2, y=y2, hidden=0, epochs=300, lr=0.8, title="Opposite corners", sub="1 neuron",
         result=("1 neuron:", "impossible"), col=V.RED),
    dict(X=X2, y=y2, hidden=8, epochs=900, lr=0.12, title="Opposite corners", sub="add a hidden layer of 8",
         result=("Add a layer:", "solved"), col=V.GOLD),
]
TRAIN_T = 5.0
t = 0.0
for i, r in enumerate(ROUNDS):
    r["snaps"] = train(r["X"], r["y"], r["hidden"], r["epochs"], r["lr"])
    start = t + (0.2 if i else 0.0)
    r["go"] = start + (2.0 if i == 0 else 1.0)
    r["done"] = r["go"] + TRAIN_T
    r["seg"] = V.Seg(start, r["done"] + 1.4)
    t = r["seg"].end
OUTRO = t + 0.2
DUR = OUTRO + 4.4
PLOT = V.Plot(-1.1, 1.1, -1.1, 1.1, pad=0)
HEADERS = [(0.0, [("Can one line", V.WHITE, 68), ("split the colours?", V.GOLD, 68)])]
for r in ROUNDS:
    HEADERS.append((r["done"] + 0.3, [(r["result"][0], V.WHITE, 64), (r["result"][1], r["col"], 78)]))
HEADERS.append((OUTRO, [("This is why networks", V.WHITE, 64), ("have layers", V.GOLD, 74)]))

C0 = np.array(V.CYAN, np.float32); C1 = np.array(V.MAGENTA, np.float32)


def field_rgb(p):
    base = (C0 * (1 - p[..., None]) + C1 * p[..., None]) * (0.18 + 0.22 * np.abs(p[..., None] - 0.5) * 2)
    gy, gx = np.gradient(p)
    dist = np.abs(p - 0.5) / (np.hypot(gx, gy) + 1e-6)      # distance to the boundary, in grid cells
    edge = np.exp(-(dist / 0.9) ** 2)[..., None] * np.array((255, 255, 255), np.float32) * 0.6
    return base + edge


def snap(r, t):
    s = V.clamp((t - r["go"]) / TRAIN_T)
    i = s * (len(r["snaps"]) - 1)
    k = min(int(i), len(r["snaps"]) - 2)
    f = i - k
    A, B = r["snaps"][k], r["snaps"][k + 1]
    return A, B, f


def net_icon(fr, cx, cy, hidden, a, col, phase):
    layers = [2] + ([hidden] if hidden else []) + [1]
    xs = np.linspace(cx - 150, cx + 150, len(layers))
    pos = [[(x, cy + (j - (n - 1) / 2) * (26 if n < 4 else 21)) for j in range(n)] for x, n in zip(xs, layers)]
    for L in range(len(pos) - 1):
        for p0 in pos[L]:
            for p1 in pos[L + 1]:
                V.line(fr, p0[0], p0[1], p1[0], p1[1], 1.6, V.DIM, a * 0.9)
    for L, layer in enumerate(pos):
        for j, (x, y) in enumerate(layer):
            pulse = 0.5 + 0.5 * np.sin(phase * 6 - L * 1.4 + j)
            c = V.WHITE if L == 0 else col
            V.disc(fr, x, y, 9 if len(layer) < 4 else 7, c, a, glow=0.2 + 0.3 * pulse, glow_r=8)


def render(t):
    fr = V.background()
    V.header(fr, t, HEADERS)
    x0, y0, x1, y1 = V.PANEL
    for n, r in enumerate(ROUNDS, 1):
        a = r["seg"].alpha(t)
        if a <= 0:
            continue
        V.round_titles(fr, n, r["title"], r["sub"], a, r["col"])
        A, B, f = snap(r, t)
        p = A["grid"] * (1 - f) + B["grid"] * f
        V.field(fr, field_rgb(p), x0 + 2, y0 + 2, x1 - 2, y1 - 2, a, mask_round=26)
        pred = B["pred"] if f > 0.5 else A["pred"]
        pxs, pys = PLOT.px(r["X"][:, 0], r["X"][:, 1])
        for xp, yp, lab, pr in zip(pxs, pys, r["y"], pred):
            col = V.CYAN if lab == 0 else V.MAGENTA
            V.disc(fr, float(xp), float(yp), 12, col, a, glow=0.45, glow_r=12)
            V.disc(fr, float(xp), float(yp), 12, V.WHITE, a * 0.9, ring=2.5)
            if pr != lab and t > r["go"]:
                V.disc(fr, float(xp), float(yp), 19, V.RED, a * 0.9, ring=3)
        acc = A["acc"] * (1 - f) + B["acc"] * f
        epoch = int(round(A["epoch"] * (1 - f) + B["epoch"] * f)) if t > r["go"] else 0
        col = r["col"] if t > r["done"] else V.WHITE
        V.counter(fr, "ACCURACY", f"{acc * 100:.0f}%", a, col, x=V.W * 0.3)
        V.text(fr, "THE NETWORK", "Medium", 30, V.W * 0.7, V.COUNT_LABEL_Y, V.GREY, a)
        net_icon(fr, V.W * 0.7, V.COUNT_Y, r["hidden"], a, r["col"], t)
        V.caption(fr, f"training round {epoch} of {r['epochs']}", a * 0.9)
    if t >= OUTRO:
        a = V.smooth((t - OUTRO) / 0.5)
        V.text(fr, "One neuron draws", "Bold", 58, V.W / 2, 900, V.WHITE, a)
        V.text(fr, "one straight line.", "Bold", 58, V.W / 2, 970, V.WHITE, a)
        V.text(fr, "Layers let it bend.", "Bold", 70, V.W / 2, 1100, V.GOLD, V.smooth((t - OUTRO - 0.6) / 0.5), glow=0.4)
    return V.finish(fr, t, DUR)


def audio(au):
    au.pad(0, DUR, notes=(220, 261.6, 329.6), amp=0.03)
    for r in ROUNDS:
        last = None
        for k in range(60):
            tt = r["go"] + k * TRAIN_T / 60
            A, B, f = snap(r, tt)
            acc = A["acc"]
            au.tick(tt, freq=600 + 1800 * acc, amp=0.08)
            if last is not None and acc > last + 0.04:
                au.blip(tt, 500 + 700 * acc, 0.10)
            last = acc
        (au.buzz if r["col"] == V.RED else au.chime)(r["done"] + 0.3)
    au.chime(OUTRO + 0.6, 660, amp=0.14)


if __name__ == "__main__":
    V.run(render, DUR, audio, "ep03_layers.mp4")
