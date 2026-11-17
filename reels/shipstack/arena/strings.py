"""ShipStack Arena: Country String Battle. python -m reels.shipstack.arena.strings --out x.mp4 [--countries IN PK ...]

Game logic (weaving, cutting, drama-scored seed search) is adapted from the user-supplied
string_battle.py; visuals use the ShipStack editorial grid and sound comes from lab/sound.py.
Every ball weaves strings to the nearest point of the ring; touching another country's string
cuts it. At each knockout the country with the fewest strings is eliminated (its strings
snap back and its ball leaves the arena) until one country is left. 15 s, 60 fps.
"""
import argparse
import math
import random
import tempfile
from pathlib import Path

import numpy as np
import skia

from .. import brand
from ..lab import sound
from . import page as P

G = brand.ARENA
CX, CY, R = 540.0, 1010.0, 480.0           # simulation frame (px)
BR = 56.0                                 # big balls: more contact, reads as a fight
DT = 1 / 240
PRE, BATTLE = 0.8, 12.0                    # result shown from PRE + BATTLE to 15 s
KNOCKOUTS = (2.4, 4.4, 6.4, 8.2, 10.0)     # sim seconds; fewest strings among survivors is out
SPEED0, SPEED_MAX = 330.0, 560.0           # calm enough to follow each cut
WEAVE0, WEAVE1 = 34.0, 52.0                # dense string fans, so traces cross and get cut
GROW, SNAP = 0.11, 0.30

# name, string colour (tuned to read on white)
COUNTRIES = {
    'IN': ('India', '#F08A24'), 'PK': ('Pakistan', '#0F8A4B'), 'TR': ('Türkiye', '#E30A17'),
    'JP': ('Japan', '#C2185B'), 'BR': ('Brazil', '#D4A000'), 'US': ('USA', '#2F5BEA'),
    'DE': ('Germany', '#3A3A3A'), 'FR': ('France', '#1E40AF'), 'BD': ('Bangladesh', '#006A4E'),
    'NP': ('Nepal', '#DC143C'), 'CN': ('China', '#EE1C25'), 'GB': ('UK', '#C8102E'),
}
# This format uses a taller figure than the standard arena grid: the ring nearly fills the page
# width, and the scoreboard is a single row of six flags.
FIG_TOP, FIG_BOTTOM = 548, 1580
BOARD_RULE, BOARD_FLAG, BOARD_COUNT = 1604, 1650, 1696
END_Y = 1752
BOX_C = (brand.W / 2, (FIG_TOP + FIG_BOTTOM) / 2)
SCALE = ((FIG_BOTTOM - FIG_TOP) / 2 - 8) / (R + 6)


def to_box(x, y):
    return BOX_C[0] + (x - CX) * SCALE, BOX_C[1] + (y - CY) * SCALE


def ease(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


# ------------------------------------------------------------------ physics (from string_battle.py)
class Sim:
    def __init__(self, seed, n):
        rng = random.Random(seed)
        self.n = n
        self.p = np.zeros((n, 2)); self.v = np.zeros((n, 2))
        spin = rng.uniform(0, 2 * math.pi)
        for i in range(n):
            a = spin + 2 * math.pi * i / n
            self.p[i] = (CX + 250 * math.cos(a), CY + 250 * math.sin(a))
            d = a + math.pi + rng.uniform(-1.1, 1.1)      # head inwards: balls cross the arena and meet
            self.v[i] = (SPEED0 * math.cos(d), SPEED0 * math.sin(d))
        self.t = 0.0
        self.states = [self.p.copy()]
        self.strings = []                  # [owner, ax, ay, born, cut_time|None, cutter, cut_x, cut_y]
        self.active = [[] for _ in range(n)]
        self.wall_hits, self.cuts = [], []
        self.next_weave = [0.15] * n
        self.alive = [True] * n
        self.knockouts = []                # (t, ball, counts of survivors at that moment)
        self.cuts_made = [0] * n
        self._ko = list(KNOCKOUTS[:n - 1])

    def step(self):
        p, v, t, n = self.p, self.v, self.t, self.n
        live = self.alive
        if self._ko and t >= self._ko[0]:
            self._knockout(t)
        p += v * DT * np.array(live, float)[:, None]
        for i in range(n):
            for j in range(i + 1, n):
                if not (live[i] and live[j]):
                    continue
                d = p[j] - p[i]; dist = math.hypot(*d)
                if 0 < dist < 2 * BR:
                    nrm = d / dist; rel = float((v[i] - v[j]) @ nrm); over = 2 * BR - dist
                    p[i] -= nrm * over / 2; p[j] += nrm * over / 2
                    if rel > 0:
                        v[i] -= rel * nrm; v[j] += rel * nrm
        for i in range(n):
            if not live[i]:
                continue
            d = p[i] - (CX, CY); dist = math.hypot(*d)
            if dist > R - BR:
                nrm = d / dist; vn = float(v[i] @ nrm)
                if vn > 0:
                    v[i] -= 2 * vn * nrm
                    self.wall_hits.append((t, i, vn, CX + nrm[0] * R, CY + nrm[1] * R))
                p[i] = (CX, CY) + nrm * (R - BR)
        target = SPEED0 + (SPEED_MAX - SPEED0) * min(1, t / BATTLE) ** 1.3
        for i in range(n):
            sp = math.hypot(*v[i])
            if sp > 1e-6:
                v[i] *= target / sp
        rate = WEAVE0 + (WEAVE1 - WEAVE0) * min(1, t / BATTLE)
        for i in range(n):
            if not live[i]:
                continue
            d = p[i] - (CX, CY); dist = max(1e-6, math.hypot(*d)); nrm = d / dist
            if dist < 0.42 * R:
                continue
            if t >= self.next_weave[i]:
                self.next_weave[i] = t + 1 / rate
                self.strings.append([i, CX + nrm[0] * R, CY + nrm[1] * R, t, None, None, 0.0, 0.0])
                self.active[i].append(len(self.strings) - 1)
        for a in range(n):
            idx = self.active[a]
            if not idx:
                continue
            anc = np.array([[self.strings[k][1], self.strings[k][2]] for k in idx])
            seg = anc - p[a]; L2 = np.maximum((seg ** 2).sum(1), 1e-6)
            keep = np.ones(len(idx), bool)
            for b in range(n):
                if b == a or not live[b]:
                    continue
                rel = p[b] - p[a]
                u = np.clip((seg @ rel) / L2, 0, 1)
                close = np.hypot(*(rel[None, :] - seg * u[:, None]).T) < BR * 0.45
                close &= u > 0.12
                if close.any():
                    for k in np.nonzero(close & keep)[0]:
                        cp = p[a] + seg[k] * u[k]
                        st = self.strings[idx[k]]; st[4] = t; st[5] = b; st[6], st[7] = float(cp[0]), float(cp[1])
                        self.cuts.append((t, b, a, *cp))
                        self.cuts_made[b] += 1
                    keep &= ~close
            if not keep.all():
                self.active[a] = [k for k, f in zip(idx, keep) if f]
        self.t += DT
        self.states.append(p.copy())

    def _knockout(self, t):
        """Eliminate the survivor with the fewest live strings (ties: fewer cuts made, then order)."""
        self._ko.pop(0)
        survivors = [i for i in range(self.n) if self.alive[i]]
        counts = {i: len(self.active[i]) for i in survivors}
        out = min(survivors, key=lambda i: (counts[i], self.cuts_made[i], i))
        for k in self.active[out]:                     # its strings snap back to the wall
            st = self.strings[k]; st[4] = t; st[5] = None; st[6], st[7] = float(self.p[out][0]), float(self.p[out][1])
        self.active[out] = []
        self.alive[out] = False
        self.v[out] = 0
        self.knockouts.append((t, out, counts))

    @property
    def winner(self):
        return next(i for i in range(self.n) if self.alive[i])

    def run(self, until):
        while self.t < until:
            self.step()
        S = self.strings
        self.A = dict(own=np.array([s[0] for s in S], int), ax=np.array([s[1] for s in S]),
                      ay=np.array([s[2] for s in S]), born=np.array([s[3] for s in S]),
                      cut=np.array([np.inf if s[4] is None else s[4] for s in S]),
                      cx=np.array([s[6] for s in S]), cy=np.array([s[7] for s in S]))
        self.S = np.array(self.states)
        return self

    def count_at(self, s):
        A = self.A
        alive = (A['born'] <= s) & (A['cut'] > s)
        return np.bincount(A['own'][alive], minlength=self.n).tolist()


def drama(seed, n):
    """Prefer battles with lead changes, a close final duel and a comeback winner."""
    s = Sim(seed, n).run(BATTLE)
    if len(s.knockouts) != n - 1:
        return None
    samples = [s.count_at(x) for x in np.arange(1.0, KNOCKOUTS[0], 0.25)]
    leaders = [int(np.argmax(c)) for c in samples]
    changes = sum(1 for a, b in zip(leaders, leaders[1:]) if a != b)
    t, out, counts = s.knockouts[-1]
    duel = sorted(counts.values())
    if duel[1] == 0 or duel[0] / duel[1] < 0.6:     # the last two must be close
        return None
    comeback = 3 if leaders and leaders[0] != s.winner else 0
    return changes + comeback + 6 * duel[0] / duel[1], s


def find(n, start, tries=60):
    best = None
    for seed in range(start, start + tries):
        r = drama(seed, n)
        if r and (best is None or r[0] > best[1]):
            best = (seed, r[0], r[1])
        if best and best[1] >= 11:
            break
    if not best:
        raise SystemExit('No seed with a close final duel; raise --tries')
    return best


# ------------------------------------------------------------------ flags (drawn, no image files)
def _star(c, x, y, r, rot, p):
    path = skia.Path()
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.4
        a = rot + k * math.pi / 5
        (path.moveTo if k == 0 else path.lineTo)(x + rr * math.cos(a), y + rr * math.sin(a))
    path.close()
    c.drawPath(path, p)


def flag(c, code, x, y, r):
    c.save()
    clip = skia.Path(); clip.addCircle(x, y, r)
    c.clipPath(clip, doAntiAlias=True)
    c.translate(x, y)
    rect = lambda col, x0, y0, w, h: c.drawRect(skia.Rect.MakeXYWH(x0, y0, w, h), P.paint(col))
    disc = lambda col, cx, cy, rr: c.drawCircle(cx, cy, rr, P.paint(col))
    s = 2 * r
    if code == 'IN':
        rect('#FF9933', -r, -r, s, s / 3); rect('#FFFFFF', -r, -r / 3, s, s / 3); rect('#138808', -r, r / 3, s, s / 3)
        c.drawCircle(0, 0, r * 0.27, P.paint('#000080', stroke=max(1, r * 0.05)))
    elif code == 'PK':
        rect('#01411C', -r, -r, s, s); rect('#FFFFFF', -r, -r, r * 0.5, s)
        disc('#FFFFFF', r * 0.18, 0, r * 0.48); disc('#01411C', r * 0.32, -r * 0.1, r * 0.42)
        _star(c, r * 0.45, -r * 0.24, r * 0.15, -0.9, P.paint('#FFFFFF'))
    elif code == 'TR':
        rect('#E30A17', -r, -r, s, s); disc('#FFFFFF', -r * 0.18, 0, r * 0.48); disc('#E30A17', -r * 0.05, 0, r * 0.39)
        _star(c, r * 0.42, 0, r * 0.18, math.pi, P.paint('#FFFFFF'))
    elif code == 'JP':
        rect('#FFFFFF', -r, -r, s, s); disc('#BC002D', 0, 0, r * 0.52)
    elif code == 'BR':
        rect('#009C3B', -r, -r, s, s)
        d = skia.Path(); d.moveTo(0, -r * 0.78); d.lineTo(r * 0.95, 0); d.lineTo(0, r * 0.78); d.lineTo(-r * 0.95, 0); d.close()
        c.drawPath(d, P.paint('#FFDF00')); disc('#002776', 0, 0, r * 0.42)
    elif code == 'US':
        h = s / 13
        for k in range(13):
            rect('#B22234' if k % 2 == 0 else '#FFFFFF', -r, -r + k * h, s, h + 0.5)
        rect('#3C3B6E', -r, -r, r, 7 * h)
    elif code == 'DE':
        rect('#000000', -r, -r, s, s / 3); rect('#DD0000', -r, -r / 3, s, s / 3); rect('#FFCE00', -r, r / 3, s, s / 3)
    elif code == 'FR':
        rect('#002395', -r, -r, s / 3, s); rect('#FFFFFF', -r / 3, -r, s / 3, s); rect('#ED2939', r / 3, -r, s / 3, s)
    elif code == 'BD':
        rect('#006A4E', -r, -r, s, s); disc('#F42A41', -r * 0.08, 0, r * 0.5)
    elif code == 'NP':
        rect('#DC143C', -r, -r, s, s); disc('#FFFFFF', 0, r * 0.1, r * 0.25)
    elif code == 'CN':
        rect('#EE1C25', -r, -r, s, s); _star(c, -r * 0.25, -r * 0.2, r * 0.32, -math.pi / 2, P.paint('#FFDE00'))
    elif code == 'GB':
        rect('#012169', -r, -r, s, s); rect('#FFFFFF', -r, -r * 0.2, s, r * 0.4); rect('#FFFFFF', -r * 0.2, -r, r * 0.4, s)
        rect('#C8102E', -r, -r * 0.12, s, r * 0.24); rect('#C8102E', -r * 0.12, -r, r * 0.24, s)
    else:
        rect('#CCCCCC', -r, -r, s, s)
    c.restore()
    c.drawCircle(x, y, r, P.paint(brand.RULE, 1, stroke=1.5))


# ------------------------------------------------------------------ reel
class Battle:
    def __init__(self, codes, episode, seed=None):
        self.codes, self.ep = codes, episode
        self.names = [COUNTRIES[c][0] for c in codes]
        self.cols = [COUNTRIES[c][1] for c in codes]
        if seed is None:
            self.seed, _, self.sim = find(len(codes), episode * 500)
        else:
            self.seed, self.sim = seed, Sim(seed, len(codes)).run(BATTLE)
        self.final = self.sim.count_at(BATTLE)
        self.winner = self.sim.winner
        self.end = PRE + BATTLE
        self.page = P.Page()
        self.cut_t = np.array([c[0] for c in self.sim.cuts]) if self.sim.cuts else np.zeros(0)

    def pos(self, s):
        st = self.sim.S
        return st[min(len(st) - 1, int(round(s / DT)))]

    def frame(self, sec):
        surface = P.new_surface()
        c = surface.getCanvas()
        pg, t = self.page, self.page.t
        s = min(max(0.0, sec - PRE), BATTLE)
        kos = [(PRE + tk, b) for tk, b, _ in self.sim.knockouts]
        out_at = {b: v for v, b in kos}
        decided = sec >= kos[-1][0] + 0.4
        left = sum(1 for i in range(self.sim.n) if out_at.get(i, 99) > sec)
        pg.masthead(c, f'SHIPSTACK ARENA  ·  Nº {self.ep:02d}  ·  COUNTRY BATTLE')
        if decided:
            pg.headline(c, self.names[self.winner], '', 'survives.', self.cols[self.winner],
                        alpha=ease((sec - kos[-1][0] - 0.4) / 0.35))
        else:
            pg.headline(c, 'Which country', 'survives ', 'last?')
        pg.dek(c, 'Fewest strings at each knockout is out.',
               f'{left} LEFT', brand.ACCENT if left <= 2 else brand.INK)

        A, n = self.sim.A, self.sim.n
        pts = self.pos(s)
        c.save()
        c.clipRect(skia.Rect(0, FIG_TOP - 4, brand.W, FIG_BOTTOM + 4))
        alive = (A['born'] <= s) & (A['cut'] > s)
        for o in range(n):                                           # live strings, shooting out to the wall
            m = alive & (A['own'] == o)
            if not m.any():
                continue
            bx, by = to_box(*pts[o])
            e = 1 - (1 - np.clip((s - A['born'][m]) / GROW, 0, 1)) ** 3
            ax, ay = to_box(A['ax'][m], A['ay'][m])
            ex, ey = bx + (ax - bx) * e, by + (ay - by) * e
            path = skia.Path()
            for x, y in zip(ex.tolist(), ey.tolist()):
                path.moveTo(bx, by); path.lineTo(x, y)
            c.drawPath(path, P.paint(self.cols[o], 0.5, stroke=2.0, cap='round'))
        snap = np.nonzero((A['cut'] <= s) & (A['cut'] > s - SNAP))[0]  # cut strings recoil from the cut point
        for k in snap.tolist():
            o = A['own'][k]; q = (s - A['cut'][k]) / SNAP; e = ease(q)
            cx, cy = to_box(A['cx'][k], A['cy'][k]); ax, ay = to_box(A['ax'][k], A['ay'][k]); bx, by = to_box(*pts[o])
            p = P.paint(self.cols[o], 0.85 * (1 - q) ** 1.4, stroke=2.6, cap='round')
            c.drawLine(ax, ay, cx + (ax - cx) * e, cy + (ay - cy) * e, p)
            c.drawLine(bx, by, cx + (bx - cx) * e, cy + (by - cy) * e, p)
        lo, hi = np.searchsorted(self.cut_t, s - 0.25), np.searchsorted(self.cut_t, s, 'right')
        for ci in range(max(lo, hi - 30), hi):                        # small sparks in the cutter's colour
            tc, b, _, x, y = self.sim.cuts[ci]; q = (s - tc) / 0.25; rr = random.Random(ci)
            x, y = to_box(x, y)
            p = P.paint(self.cols[b], 0.9 * (1 - q), stroke=2, cap='round')
            for _ in range(5):
                ang = rr.uniform(0, 2 * math.pi); d0 = 3 + 22 * ease(q) * rr.uniform(0.6, 1.2)
                c.drawLine(x + d0 * math.cos(ang), y + d0 * math.sin(ang),
                           x + (d0 + 8 * (1 - q)) * math.cos(ang), y + (d0 + 8 * (1 - q)) * math.sin(ang), p)
        c.drawCircle(BOX_C[0], BOX_C[1], R * SCALE, P.paint(brand.INK, 1, stroke=3.5))
        br = BR * SCALE
        for o in range(n):
            x, y = to_box(*pts[o])
            ko = out_at.get(o)
            if ko is not None and sec >= ko:                         # knocked out: burst, shrink, "OUT" tag
                q = (sec - ko) / 0.6
                if q < 1:
                    c.drawCircle(x, y, br * (1 + 1.2 * ease(q)), P.paint(self.cols[o], 1 - q, stroke=5 * (1 - q) + 1))
                    shrink = 1 - ease(q)
                    if shrink > 0.05:
                        c.drawCircle(x, y, (br + 4) * shrink, P.paint(self.cols[o], 1 - q))
                        flag(c, self.codes[o], x, y, br * shrink)
                if q < 1.6:
                    t.text(c, 'OUT', x, y - br - 18 - 20 * ease(q / 1.6), t.sans_semi, 22, self.cols[o], 'center',
                           max(0.0, 1 - q / 1.6))
                continue
            c.drawCircle(x, y + 3, br + 3, P.paint(brand.INK, 0.12))
            c.drawCircle(x, y, br + 4, P.paint(self.cols[o]))
            flag(c, self.codes[o], x, y, br)
        c.restore()

        # Scoreboard: one row of six flags; knocked-out countries show OUT.
        pg.hairline(c, BOARD_RULE)
        counts = self.sim.count_at(s)
        cell = (brand.RIGHT_X - brand.LEFT_X) / n
        for i in range(n):
            x = brand.LEFT_X + cell * (i + 0.5)
            gone = out_at.get(i, 99) <= sec
            c.saveLayerAlpha(None, 90 if gone else 255)
            flag(c, self.codes[i], x, BOARD_FLAG, 20)
            c.restore()
            if gone:
                t.text(c, 'OUT', x, BOARD_COUNT, t.sans_semi, 18, brand.MUTED, 'center')
            else:
                lead = i == self.winner and decided
                t.text(c, str(counts[i]), x, BOARD_COUNT, t.mono, 26, brand.ACCENT if lead else brand.INK, 'center')
        if decided:
            w = self.winner
            alpha = ease((sec - kos[-1][0] - 0.8) / 0.4)
            t2 = 'Last one standing after 5 knockouts. '
            cap = 38
            total = t.width(t2, t.serif, cap) + t.width('Your country next?', t.italic, cap)
            cap = min(cap, cap * (brand.RIGHT_X - brand.LEFT_X) / total)
            x = brand.LEFT_X + t.text(c, t2, brand.LEFT_X, END_Y, t.serif, cap, brand.ACCENT, alpha=alpha)
            t.text(c, 'Your country next?', x, END_Y, t.italic, cap, brand.ACCENT, alpha=alpha)
        return surface

    def soundtrack(self, path):
        tl = sound.Timeline(brand.SECONDS)
        tl.add(0, sound.pad(float(brand.SECONDS), 73.42), 0.45)
        tl.add(PRE, sound.pluck(sound.PENTA[7], 0.5), 0.45)
        last, k = -1.0, 0
        for (tw, i, vn, hx, hy) in self.sim.wall_hits:             # the walls play the scale
            at = PRE + tw
            if at - last < 0.075:
                continue
            last = at
            tl.add(at, sound.pluck(sound.PENTA[k % 10], 0.35), 0.06 + 0.12 * min(1, vn / 1300), (hx - CX) / R * 0.8)
            k += 1
        last = -1.0
        for (tc, b, a, x, y) in self.sim.cuts:                     # cuts: short high pluck
            at = PRE + tc
            if at - last < 0.09:
                continue
            last = at
            tl.add(at, sound.pluck(sound.PENTA[8 + (int(tc * 100) % 2)], 0.18, 3.0), 0.07, (x - CX) / R * 0.8)
        for k, (tk, b, _) in enumerate(self.sim.knockouts):         # each knockout: a low hit, rising
            tl.add(PRE + tk, sound.pluck(65.41 * 2 ** (k / 5), 0.9, 4.0), 0.5)
            tl.add(PRE + tk + 0.02, sound.pluck(sound.PENTA[k], 0.5), 0.3)
        win_at = PRE + self.sim.knockouts[-1][0] + 0.4
        tl.add(win_at, sound.chord(261.63, 3.0), 0.45)
        tl.write(path)


def render(out, codes=('IN', 'PK', 'TR', 'JP', 'BR', 'US'), episode=1, seed=None):
    reel = Battle(list(codes), episode, seed)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / 'audio.wav'
        reel.soundtrack(wav)
        enc = P.Encoder(out, wav)
        for f in range(P.FRAMES):
            enc.write(reel.frame(f / P.FPS))
        enc.close()
    order = [reel.names[b] for _, b, _ in reel.sim.knockouts]
    print(f'Country battle: seed {reel.seed}, out in order {order}, winner {reel.names[reel.winner]}')
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='reels/out/arena-strings.mp4')
    ap.add_argument('--countries', nargs=6, default=['IN', 'PK', 'TR', 'JP', 'BR', 'US'], choices=sorted(COUNTRIES))
    ap.add_argument('--episode', type=int, default=1)
    ap.add_argument('--seed', type=int)
    a = ap.parse_args()
    render(a.out, a.countries, a.episode, a.seed)
