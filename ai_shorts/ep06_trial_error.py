#!/usr/bin/env python3
"""EP06 — An AI that learns by trial and error (Q-learning).

Real tabular Q-learning in an 8×8 maze: −0.05 per step, +10 at the star,
−10 in lava. The cell colours are the AI's own estimate of how good each square is.
Round 1: episode 1 (knows nothing). Round 2: episode 40. Round 3: after 400 episodes.
Run: python3 ep06_trial_error.py all
"""
import numpy as np
import aiviz as V

MAP = ["......#G",
       ".##...#.",
       ".#..L...",
       ".#.##.#.",
       "...#..#.",
       ".L.#.L..",
       "...#....",
       "S.......", ]
ACTS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
START = (0, 7)


def move(x, y, a):
    nx, ny = x + ACTS[a][0], y + ACTS[a][1]
    if not (0 <= nx < 8 and 0 <= ny < 8) or MAP[ny][nx] == "#":
        return x, y
    return nx, ny


def train(seed=4, episodes=400):
    rng = np.random.default_rng(seed)
    Q = np.zeros((8, 8, 4))
    rec = {}
    for ep in range(1, episodes + 1):
        if ep in (1, 40):
            rec[ep] = {"Q": Q.copy()}
        x, y = START
        path, out = [(x, y)], "lost"
        eps = max(0.05, 0.5 * 0.99 ** ep)
        for _ in range(250):
            q = Q[y, x]
            a = rng.integers(4) if rng.random() < eps else rng.choice(np.flatnonzero(q == q.max()))
            nx, ny = move(x, y, a)
            c = MAP[ny][nx]
            r, done = -0.05, False
            if c == "G":
                r, done, out = 10.0, True, "goal"
            elif c == "L":
                r, done, out = -10.0, True, "lava"
            Q[y, x, a] += 0.5 * (r + (0 if done else 0.95 * Q[ny, nx].max()) - Q[y, x, a])
            x, y = nx, ny
            path.append((x, y))
            if done:
                break
        if ep in rec:
            rec[ep].update(path=path, out=out)
    # the trained agent, acting greedily
    x, y = START
    path = [(x, y)]
    while MAP[y][x] not in "GL" and len(path) < 60:
        x, y = move(x, y, int(np.argmax(Q[y, x])))
        path.append((x, y))
    rec[episodes] = dict(Q=Q.copy(), path=path, out="goal" if MAP[y][x] == "G" else "lava")
    return rec


REC = train()
ROUNDS = [dict(ep=1, title="Episode 1", sub="it knows nothing yet", col=V.RED),
          dict(ep=40, title="Episode 40", sub="it remembers what worked", col=V.ORANGE),
          dict(ep=400, title="Episode 400", sub="trained", col=V.GOLD)]
for r in ROUNDS:
    rr = REC[r["ep"]]
    r.update(Q=rr["Q"], path=rr["path"], out=rr["out"], steps=len(rr["path"]) - 1)
    r["result"] = (f"Episode {r['ep']}:", "fell in the lava" if r["out"] == "lava" else f"made it in {r['steps']} steps")
    r["dt"] = min(0.20, 4.2 / max(1, r["steps"]))
t = 0.0
for i, r in enumerate(ROUNDS):
    start = t + (0.2 if i else 0.0)
    r["go"] = start + (2.0 if i == 0 else 1.0)
    r["done"] = r["go"] + r["steps"] * r["dt"]
    r["seg"] = V.Seg(start, r["done"] + 1.5)
    t = r["seg"].end
OUTRO = t + 0.2
DUR = OUTRO + 4.4
HEADERS = [(0.0, [("An AI that learns", V.WHITE, 68), ("by trial and error", V.GOLD, 70)])]
for r in ROUNDS:
    HEADERS.append((r["done"] + 0.3, [(r["result"][0], V.WHITE, 64), (r["result"][1], r["col"], 72)]))
HEADERS.append((OUTRO, [("Nobody told it", V.WHITE, 70), ("the way", V.GOLD, 80)]))

X0, Y0, X1, Y1 = V.PANEL
CELL = (X1 - X0 - 40) / 8


def cell_xy(c, r):
    return X0 + 20 + (c + 0.5) * CELL, Y0 + 20 + (r + 0.5) * CELL


def value_colour(v):
    if v >= 0:
        k = min(1.0, v / 8.0) ** 0.6
        return V.mix((22, 24, 44), V.GOLD, k)
    k = min(1.0, -v / 6.0) ** 0.6
    return V.mix((22, 24, 44), V.VIOLET, k)


def agent_pos(r, t):
    s = (t - r["go"]) / r["dt"]
    path = r["path"]
    if s <= 0:
        return cell_xy(*path[0]), 0
    if s >= len(path) - 1:
        return cell_xy(*path[-1]), len(path) - 1
    k = int(s)
    f = V.smoother(s - k)
    (ax, ay), (bx, by) = cell_xy(*path[k]), cell_xy(*path[k + 1])
    return (V.lerp(ax, bx, f), V.lerp(ay, by, f)), k + 1


def render(t):
    fr = V.background(grid=False)
    V.header(fr, t, HEADERS)
    for n, r in enumerate(ROUNDS, 1):
        a = r["seg"].alpha(t)
        if a <= 0:
            continue
        V.round_titles(fr, n, r["title"], r["sub"], a, r["col"])
        Qv = r["Q"].max(-1)
        for row in range(8):
            for col in range(8):
                cx, cy = cell_xy(col, row)
                ch = MAP[row][col]
                x0, y0, x1, y1 = cx - CELL / 2 + 4, cy - CELL / 2 + 4, cx + CELL / 2 - 4, cy + CELL / 2 - 4
                if ch == "#":
                    V.rect(fr, x0, y0, x1, y1, (58, 62, 86), a, radius=14)
                elif ch == "L":
                    pulse = 0.5 + 0.5 * np.sin(t * 4 + col + row)
                    V.rect(fr, x0, y0, x1, y1, V.mix((140, 30, 30), V.RED, pulse), a, radius=14, glow=0.35)
                elif ch == "G":
                    V.rect(fr, x0, y0, x1, y1, (60, 50, 18), a, radius=14)
                    V.disc(fr, cx, cy, 24, V.GOLD, a, glow=1.0 + 0.4 * np.sin(t * 5), glow_r=22)
                else:
                    V.rect(fr, x0, y0, x1, y1, value_colour(Qv[row, col]), a, radius=14)
                    if ch == "S":
                        V.text(fr, "START", "SemiBold", 22, cx, cy, V.WHITE, a * 0.7)
                    if r["ep"] == 400 and ch == ".":       # learned direction in each square
                        dx, dy = ACTS[int(np.argmax(r["Q"][row, col]))]
                        V.line(fr, cx - dx * 18, cy - dy * 18, cx + dx * 18, cy + dy * 18, 4, V.WHITE, a * 0.55)
                        V.disc(fr, cx + dx * 18, cy + dy * 18, 6, V.WHITE, a * 0.6)
        (ax, ay), step = agent_pos(r, t)
        trail = [cell_xy(*p) for p in r["path"][: step + 1]] + [(ax, ay)]
        if len(trail) > 1:
            V.polyline(fr, trail, 6, r["col"], a * 0.75, glow=0.4, glow_r=10)
        V.disc(fr, ax, ay, 22, V.CYAN, a, glow=0.9, glow_r=20)
        V.disc(fr, ax - 7, ay - 7, 6, V.WHITE, a * 0.6)
        if t > r["done"] and r["out"] == "lava":
            V.disc(fr, ax, ay, 22 + 60 * V.ease_out((t - r["done"]) / 0.5), V.RED, a * (1 - V.clamp((t - r["done"]) / 0.6)), ring=5)
        res = "?" if t < r["done"] else ("★ goal" if r["out"] == "goal" else "lava")
        res_col = V.GOLD if r["out"] == "goal" else V.RED
        V.counters(fr, [("STEPS", str(step), V.WHITE), ("RESULT", res.replace("★ ", ""), res_col if t >= r["done"] else V.WHITE)], a)
        V.caption(fr, "gold squares = it expects a reward from here", a * 0.85)
    if t >= OUTRO:
        a = V.smooth((t - OUTRO) / 0.5)
        V.text(fr, "Try. Get rewarded or punished.", "Bold", 52, V.W / 2, 900, V.WHITE, a)
        V.text(fr, "Remember. Try again.", "Bold", 52, V.W / 2, 970, V.WHITE, a)
        V.text(fr, "That’s how AI beat us at games.", "Bold", 54, V.W / 2, 1100, V.GOLD, V.smooth((t - OUTRO - 0.6) / 0.5), glow=0.4)
        V.caption(fr, "This is reinforcement learning", V.smooth((t - OUTRO - 1.2) / 0.5))
    return V.finish(fr, t, DUR)


def audio(au):
    au.pad(0, DUR, notes=(185, 233.1, 277.2), amp=0.03)
    for r in ROUNDS:
        for k in range(r["steps"]):
            au.tick(r["go"] + (k + 0.5) * r["dt"], 900 + 30 * k, 0.12)
        (au.buzz if r["out"] == "lava" else au.chime)(r["done"] + 0.05)
    au.chime(OUTRO + 0.6, 740, amp=0.14)


if __name__ == "__main__":
    V.run(render, DUR, audio, "ep06_trial_error.mp4")
