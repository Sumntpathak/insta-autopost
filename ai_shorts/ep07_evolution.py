#!/usr/bin/env python3
"""EP07 — Nobody taught them to fly (a genetic algorithm).

60 rockets, each with a "DNA" of 150 thrust directions. They fly, get scored by
how close they got (and how fast they arrived), the best ones breed (crossover),
and a few genes mutate at random. Repeat.
Rounds show generations 1, 20, 30 and 90 of one deterministic run.
Run: python3 ep07_evolution.py all
"""
import numpy as np
import aiviz as V

rng = np.random.default_rng(7)
N, T = 60, 150
START = np.array([0.0, -0.85])
TARGET = np.array([0.0, 0.82])
TR = 0.07
OBS = (-0.45, 0.05, 0.45, 0.13)            # x0, y0, x1, y1 in world units
SHOW = [1, 20, 30, 90]


def fly(G):
    n = len(G)
    p = np.tile(START, (n, 1)); v = np.zeros((n, 2))
    alive = np.ones(n, bool); hit = np.zeros(n, bool); tdone = np.full(n, T)
    best = np.full(n, 9.0)
    path = np.zeros((T + 1, n, 2)); path[0] = p
    for k in range(T):
        acc = np.stack([np.cos(G[:, k]), np.sin(G[:, k])], 1) * 0.0009
        m = alive & ~hit
        v[m] += acc[m]; v[m] *= 0.995; p[m] += v[m]
        crash = m & ((np.abs(p[:, 0]) > 0.98) | (np.abs(p[:, 1]) > 0.98) |
                     ((p[:, 0] > OBS[0]) & (p[:, 0] < OBS[2]) & (p[:, 1] > OBS[1]) & (p[:, 1] < OBS[3])))
        alive[crash] = False; tdone[crash & (tdone == T)] = k
        d = np.linalg.norm(p - TARGET, axis=1)
        best = np.minimum(best, d)
        nh = m & ~crash & (d < TR)
        hit[nh] = True; tdone[nh] = k
        path[k + 1] = p
    return dict(path=path, alive=alive, hit=hit, tdone=tdone, best=best)


def evolve(gens):
    G = rng.uniform(-np.pi, np.pi, (N, T))
    rec = {}
    for gen in range(1, gens + 1):
        res = fly(G)
        f = 1 / (res["best"] + 0.02) ** 4
        f[res["hit"]] *= 10 * (1 + (T - res["tdone"][res["hit"]]) / T)
        f[~res["alive"]] *= 0.1
        if gen in SHOW:
            rec[gen] = dict(res, fit=f / f.max())
        elite = np.argsort(f)[-2:]                     # keep the two best unchanged
        par = rng.choice(N, (N, 2), p=f / f.sum())
        cut = rng.integers(1, T, N)
        child = np.where(np.arange(T)[None, :] < cut[:, None], G[par[:, 0]], G[par[:, 1]])
        mut = rng.random((N, T)) < 0.008
        child[mut] = rng.uniform(-np.pi, np.pi, mut.sum())
        child[:2] = G[elite]
        G = child
    return rec


REC = evolve(max(SHOW))
FLY_T = 4.2
ROUNDS = []
t = 0.0
for i, g in enumerate(SHOW):
    r = dict(gen=g, **REC[g])
    r["hits"] = int(r["hit"].sum()); r["crashes"] = int((~r["alive"]).sum())
    start = t + (0.2 if i else 0.0)
    r["go"] = start + (2.0 if i == 0 else 0.9)
    r["done"] = r["go"] + FLY_T
    r["seg"] = V.Seg(start, r["done"] + 1.3)
    r["col"] = [V.RED, V.ORANGE, V.LIME, V.GOLD][i]
    r["sub"] = ["random DNA", "the best got to breed", "", ""][i] or f"{r['hits']} of {N} made it"
    t = r["seg"].end
    ROUNDS.append(r)
OUTRO = t + 0.2
DUR = OUTRO + 4.4
PLOT = V.Plot(-1, 1, -1, 1, pad=10)
HEADERS = [(0.0, [("Nobody taught them", V.WHITE, 66), ("to fly", V.GOLD, 84)])]
for r in ROUNDS:
    msg = ("all crashed or lost" if r["gen"] == 1 else "none yet, but closer") if r["hits"] == 0 else f"{r['hits']} reached the star"
    HEADERS.append((r["done"] + 0.3, [(f"Generation {r['gen']}:", V.WHITE, 62), (msg, r["col"], 66)]))
HEADERS.append((OUTRO, [("Survival of the fittest", V.WHITE, 62), ("is an algorithm", V.GOLD, 70)]))


def render(t):
    fr = V.background()
    V.header(fr, t, HEADERS)
    for n, r in enumerate(ROUNDS, 1):
        a = r["seg"].alpha(t)
        if a <= 0:
            continue
        V.round_titles(fr, n, f"Generation {r['gen']}", r["sub"], a, r["col"])
        ox0, oy0 = PLOT.px(OBS[0], OBS[3]); ox1, oy1 = PLOT.px(OBS[2], OBS[1])
        V.rect(fr, float(ox0), float(oy0), float(ox1), float(oy1), (90, 96, 130), a, radius=10, glow=0.25)
        tx, ty = PLOT.px(*TARGET)
        V.disc(fr, float(tx), float(ty), 30, V.GOLD, a, glow=1.0 + 0.3 * np.sin(t * 5), glow_r=26)
        sx, sy = PLOT.px(*START)
        V.rect(fr, float(sx) - 50, float(sy) + 18, float(sx) + 50, float(sy) + 28, V.GREY, a * 0.8, radius=5)
        k = int(V.clamp((t - r["go"]) / FLY_T) * T)
        order = np.argsort(r["fit"])                       # draw the fittest on top
        hits = 0
        for j in order:
            end = min(k, r["tdone"][j])
            pts = r["path"][: end + 1, j]
            X, Y = PLOT.px(pts[:, 0], pts[:, 1])
            crashed = (not r["alive"][j]) and k >= r["tdone"][j]
            reached = r["hit"][j] and k >= r["tdone"][j]
            hits += int(reached)
            col = V.GOLD if reached else (V.mix(V.RED, (90, 40, 50), 0.4) if crashed else V.hsv(0.5 + 0.35 * r["fit"][j], 0.65, 1.0))
            if len(X) > 1:
                step = max(1, len(X) // 30)
                trail = list(zip(X[::step].tolist(), Y[::step].tolist())) + [(float(X[-1]), float(Y[-1]))]
                V.polyline(fr, trail, 2.0, col, a * (0.25 + 0.35 * r["fit"][j]))
            hx, hy = float(X[-1]), float(Y[-1])
            if len(X) > 2:
                dx, dy = X[-1] - X[-3], Y[-1] - Y[-3]
                L = float(np.hypot(dx, dy)) or 1.0
                V.line(fr, hx - dx / L * 16, hy - dy / L * 16, hx, hy, 8, col, a, glow=0.4, glow_r=8)
            else:
                V.disc(fr, hx, hy, 5, col, a)
        V.counters(fr, [("REACHED", f"{hits} / {N}", V.GOLD if hits else V.WHITE),
                        ("GENERATION", str(r["gen"]), r["col"])], a)
    if t >= OUTRO:
        a = V.smooth((t - OUTRO) / 0.5)
        V.text(fr, "Score them. Breed the best.", "Bold", 54, V.W / 2, 900, V.WHITE, a)
        V.text(fr, "Add a little random mutation.", "Bold", 54, V.W / 2, 970, V.WHITE, a)
        V.text(fr, "Repeat.", "Bold", 80, V.W / 2, 1100, V.GOLD, V.smooth((t - OUTRO - 0.6) / 0.5), glow=0.4)
        V.caption(fr, "This is a genetic algorithm", V.smooth((t - OUTRO - 1.2) / 0.5))
    return V.finish(fr, t, DUR)


def audio(au):
    au.pad(0, DUR, notes=(174.6, 220, 261.6), amp=0.03)
    for r in ROUNDS:
        au.whoosh(r["go"], amp=0.09, dur=FLY_T * 0.8)
        for j in range(N):
            tj = r["go"] + r["tdone"][j] / T * FLY_T
            if r["hit"][j]:
                au.blip(tj, 990 + 8 * j, 0.10)
            elif not r["alive"][j]:
                au.tick(tj, 400, 0.10, decay=0.008)
        (au.chime if r["hits"] else au.buzz)(r["done"] + 0.3)
    au.chime(OUTRO + 0.6, 587, amp=0.14)


if __name__ == "__main__":
    V.run(render, DUR, audio, "ep07_evolution.mp4")
