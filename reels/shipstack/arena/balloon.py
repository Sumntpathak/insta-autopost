"""ShipStack Arena: Balloon Pop (pick a balloon 1-6). python -m reels.shipstack.arena.balloon --out x.mp4 [--episode N]

Game logic adapted from the MIT-licensed Pythonic Life "Balloon Pop" (reels/pythonic/upstream/
19-balloon-pop, see its LICENSE): a ball bounces inside each balloon; every hit inflates it a
little; the first to reach full size pops. The seed search only chooses a race that is close
and has a late lead change; the result is never edited. The last moments before the pop are
shown in 0.4x slow motion (labelled on screen). 15 s, 60 fps, editorial page.
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
R0, RPOP, RB = 125.0, 178.0, 17.0           # balloon start/pop radius and ball radius (sim units)
SPEED, DT = 600.0, 1 / 240
PRE = 0.6                                    # hook frame before the balls start
SLOW, SLOW_FOR = 0.4, 1.4                    # last 1.4 s of the race at 0.4x
WINDOW = (7.4, 8.6)                          # pop time (sim seconds): lands at ~10.5-11.7 s on screen
CELL_W = (brand.RIGHT_X - brand.LEFT_X) / 3
CELL_H = (G['FIG_BOTTOM'] - G['FIG_TOP']) / 2
K = min(CELL_W / 2 - 8, CELL_H * 0.40) / RPOP          # sim units -> px, a full balloon fits its cell
CENTERS = [(brand.LEFT_X + CELL_W * (c + 0.5), G['FIG_TOP'] + CELL_H * (r + 0.43)) for r in range(2) for c in range(3)]


def ease(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def mix(a, b, t):
    ca, cb = brand.rgb(a), brand.rgb(b)
    return '#%02X%02X%02X' % tuple(round(x + (y - x) * t) for x, y in zip(ca, cb))


def simulate(seed, seconds=13.0):
    """Six independent balloons. Returns per-step (x, y, r) arrays, hits, winner, pop time."""
    rnd = random.Random(seed)
    st = []
    for k in range(6):
        a = rnd.uniform(0, 2 * math.pi)
        p = rnd.uniform(0, 2 * math.pi)                    # start off-centre so the number stays readable
        st.append(dict(x=0.55 * R0 * math.cos(p), y=0.55 * R0 * math.sin(p), vx=SPEED * math.cos(a), vy=SPEED * math.sin(a),
                       r=R0, rnd=random.Random(seed * 7 + k)))
    steps = int(seconds / DT)
    out = np.zeros((steps + 1, 6, 3))
    out[0] = [(b['x'], b['y'], b['r']) for b in st]  # noqa: E501
    hits, winner, t_win = [], None, None
    for n in range(1, steps + 1):
        t = n * DT
        for k, b in enumerate(st):
            b['x'] += b['vx'] * DT; b['y'] += b['vy'] * DT
            d = math.hypot(b['x'], b['y'])
            if d > b['r'] - RB:                                  # hit the skin: bounce and inflate
                nx, ny = b['x'] / d, b['y'] / d
                dot = b['vx'] * nx + b['vy'] * ny
                if dot > 0:
                    b['vx'] -= 2 * dot * nx; b['vy'] -= 2 * dot * ny
                    a = math.atan2(b['vy'], b['vx']) + math.radians(b['rnd'].uniform(-8, 8))
                    b['vx'], b['vy'] = SPEED * math.cos(a), SPEED * math.sin(a)
                    if winner is None:
                        b['r'] += b['rnd'].uniform(1.4, 3.0)
                        hits.append((t, k, b['r'], math.atan2(ny, nx)))
                        if b['r'] >= RPOP:
                            winner, t_win = k, t
                b['x'], b['y'] = nx * (b['r'] - RB), ny * (b['r'] - RB)
            out[n, k] = (b['x'], b['y'], b['r'])
    return out, hits, winner, t_win


def choose(start):
    """First seed from `start` with a pop in the window, a close runner-up and a late lead change."""
    for seed in range(start, start + 4000):
        st, hits, w, tw = simulate(seed, WINDOW[1] + 0.2)
        if w is None or not WINDOW[0] <= tw <= WINDOW[1]:
            continue
        at = lambda t: st[min(int(t / DT), len(st) - 1), :, 2]
        final = sorted(at(tw))
        three_before = at(tw - 3)
        if final[-2] > RPOP - 6 and int(np.argmax(three_before)) != w:
            return seed
    raise RuntimeError('no balloon race with a close finish found')


class BalloonReel:
    def __init__(self, episode, seed=None):
        self.episode = episode
        self.seed = choose(episode * 5000 + 1) if seed is None else seed     # disjoint search ranges per episode
        self.st, self.hits, self.win, self.t_win = simulate(self.seed, 13.0)
        self.s_slow = self.t_win - SLOW_FOR
        self.v_slow = PRE + self.s_slow
        self.v_pop = self.v_slow + SLOW_FOR / SLOW
        self.page = P.Page()
        self.hit_t = np.array([h[0] for h in self.hits])

    def sim_time(self, v):
        if v < PRE:
            return 0.0
        if v < self.v_slow:
            return v - PRE
        if v < self.v_pop:
            return self.s_slow + (v - self.v_slow) * SLOW
        return self.t_win + (v - self.v_pop)

    def at(self, s):
        return self.st[min(int(round(s / DT)), len(self.st) - 1)]

    def frame(self, v):
        surface = P.new_surface()
        c = surface.getCanvas()
        pg, t = self.page, self.page.t
        s = self.sim_time(v)
        popped = v >= self.v_pop
        pg.masthead(c, f'SHIPSTACK ARENA  ·  Nº {self.episode:02d}  ·  BALLOON POP')
        if popped:
            pg.headline(c, f'Balloon {self.win + 1}', '', 'pops first.', brand.BALLS[self.win], alpha=ease((v - self.v_pop) / 0.3))
        else:
            pg.headline(c, 'Which balloon', 'pops ', 'first?')
        slow = self.v_slow <= v < self.v_pop
        pg.dek(c, 'Every hit inflates it. 100% = pop.', 'SLOW 0.4×' if slow else f'{min(s, self.t_win):4.1f}s',
               brand.ACCENT if slow or popped else brand.INK)

        state = self.at(s)
        for k, (cx, cy) in enumerate(CENTERS):
            col = brand.BALLS[k]
            x, y, r = state[k]
            tension = min(1.0, (r - R0) / (RPOP - R0))
            rr = r * K * (1 + 0.012 * math.sin(v * 9 + k))
            if k == self.win and popped:
                self._burst(c, cx, cy, rr, col, v - self.v_pop)
                continue
            dim = 0.4 if popped else 1.0
            self._balloon(c, cx, cy, rr, col, tension, dim, v, k)
            t.text(c, str(k + 1), cx, cy - rr * 0.05, t.sans_semi, rr * 0.5, brand.PAPER, 'center', 0.9 * dim)
            lo, hi = np.searchsorted(self.hit_t, s - 0.12), np.searchsorted(self.hit_t, s, 'right')
            for th, kk, _, ang in self.hits[lo:hi]:                 # hit flash on the skin
                if kk == k:
                    a0 = math.degrees(ang)
                    path = skia.Path(); path.addArc(self._oval(cx, cy, rr), a0 - 14, 28)
                    c.drawPath(path, P.paint(brand.PAPER, 1 - (s - th) / 0.12, stroke=7, cap='round'))
            bx, by = cx + x * K, cy + y * K
            c.drawCircle(bx, by, RB * K + 2, P.paint(brand.PAPER, dim))
            c.drawCircle(bx, by, RB * K, P.paint(brand.INK, dim))

        pg.board_head(c, 'INFLATION')
        frozen = self.at(min(s, self.t_win))
        for k, (x0, x1, y) in enumerate(pg.cells()):
            col = brand.BALLS[k]
            pct = min(100, int(100 * (frozen[k][2] - R0) / (RPOP - R0)))
            c.drawCircle(x0 + 16, y - 6, 16, P.paint(col))
            t.text(c, str(k + 1), x0 + 16, y - 6, t.sans_semi, 14, brand.PAPER, 'center')
            label = 'POP' if (k == self.win and popped) else f'{pct}%'
            t.text(c, label, x1, y - 6, t.mono, 24, brand.ACCENT if k == self.win and popped else brand.INK, 'right')
            c.drawLine(x0 + 44, y + 22, x1, y + 22, P.paint(brand.RULE, 1, stroke=3))
            c.drawLine(x0 + 44, y + 22, x0 + 44 + (x1 - x0 - 44) * pct / 100, y + 22, P.paint(col, 1, stroke=3))
        if popped:
            n = sum(1 for h in self.hits if h[1] == self.win)
            pg.conclusion(c, f'Balloon {self.win + 1} popped after {n} hits. ', 'Did you pick it?',
                          alpha=ease((v - self.v_pop - 0.4) / 0.4))
        return surface

    @staticmethod
    def _oval(cx, cy, rr):
        """Balloon body: a little taller than wide; always contains the physics circle of radius rr."""
        return skia.Rect(cx - rr * 1.03, cy - rr * 1.10, cx + rr * 1.03, cy + rr * 1.16)

    def _balloon(self, c, cx, cy, rr, col, tension, dim, v, k):
        body = self._oval(cx, cy, rr)
        bottom = cy + rr * 1.16
        sway = 7 * math.sin(v * 2.6 + k)                        # string: a soft curve from the knot
        string = skia.Path(); string.moveTo(cx, bottom + 10)
        string.cubicTo(cx + sway, bottom + 40, cx - sway, bottom + 64, cx + sway * 0.5, bottom + 92)
        c.drawPath(string, P.paint(brand.SOFT, dim, stroke=2, cap='round'))
        knot = skia.Path(); knot.moveTo(cx - 8, bottom + 11); knot.lineTo(cx + 8, bottom + 11); knot.lineTo(cx, bottom - 4); knot.close()
        c.drawPath(knot, P.paint(mix(col, brand.INK, 0.2), dim))
        c.drawOval(body.makeOffset(4, 10), skia.Paint(Color=P.color(brand.INK, 0.10 * dim), AntiAlias=True,
                                                      MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
        light, mid, deep = mix(brand.PAPER, col, 0.35 + 0.25 * tension), mix(brand.PAPER, col, 0.75 + 0.2 * tension), mix(col, brand.INK, 0.18)
        shade = skia.GradientShader.MakeRadial(skia.Point(cx - rr * 0.38, cy - rr * 0.45), rr * 1.75,
                                               [P.color(light, dim), P.color(mid, dim), P.color(deep, dim)], [0.0, 0.55, 1.0])
        c.drawOval(body, skia.Paint(Shader=shade, AntiAlias=True))
        c.drawOval(body, P.paint(mix(col, brand.INK, 0.25), dim, stroke=1.6 + 1.6 * tension))
        gloss = skia.Rect(cx - rr * 0.62, cy - rr * 0.80, cx - rr * 0.18, cy - rr * 0.28)
        c.drawOval(gloss, skia.Paint(Color=P.color(brand.PAPER, 0.55 * dim), AntiAlias=True,
                                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, rr * 0.06)))

    def _burst(self, c, cx, cy, rr, col, dt):
        if dt < 0.5:                                            # expanding ring
            c.drawCircle(cx, cy, rr * (1 + 0.8 * ease(dt / 0.5)), P.paint(col, 1 - dt / 0.5, stroke=6 * (1 - dt / 0.5) + 1))
        if dt < 0.9:                                            # shreds fly out and fall
            for j in range(12):
                rnd = random.Random(j * 31 + self.seed)
                a = j * 2 * math.pi / 12 + rnd.uniform(-0.2, 0.2)
                dist = rr + 380 * dt * rnd.uniform(0.7, 1.2)
                px, py = cx + math.cos(a) * dist, cy + math.sin(a) * dist + 700 * dt * dt
                size = 14 * rnd.uniform(0.7, 1.3)
                tri = skia.Path(); tri.moveTo(px, py); tri.lineTo(px + size, py + size * 0.4); tri.lineTo(px + size * 0.3, py + size); tri.close()
                c.drawPath(tri, P.paint(col, 1 - dt / 0.9))

    def soundtrack(self, path):
        tl = sound.Timeline(brand.SECONDS)
        tl.add(0, sound.pad(float(brand.SECONDS), 65.41), 0.45)
        last = -1.0
        for th, k, r, ang in self.hits:                          # pitch climbs as balloons inflate
            v = self._video_time(th)
            if v - last < 0.05 or th > self.t_win:
                continue
            last = v
            step = min(9, int(10 * (r - R0) / (RPOP - R0)))
            tl.add(v, sound.pluck(sound.PENTA[step], 0.25), 0.08 + 0.06 * step / 9, (CENTERS[k][0] - brand.W / 2) / brand.W)
        tl.add(self.v_slow, sound.chord(130.81, 3.2), 0.25)        # tension under the slow-motion
        tl.add(self.v_pop, sound.pluck(65.41, 0.9, 4.0), 0.7)
        tl.add(self.v_pop + 0.05, sound.chord(261.63, 2.8), 0.45)
        tl.write(path)

    def _video_time(self, s):
        if s < self.s_slow:
            return PRE + s
        if s < self.t_win:
            return self.v_slow + (s - self.s_slow) / SLOW
        return self.v_pop + (s - self.t_win)


def render(out, episode=3, seed=None):
    reel = BalloonReel(episode, seed)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / 'audio.wav'
        reel.soundtrack(wav)
        enc = P.Encoder(out, wav)
        for f in range(P.FRAMES):
            enc.write(reel.frame(f / P.FPS))
        enc.close()
    print(f'Balloon Pop: seed {reel.seed}, balloon {reel.win + 1} pops at {reel.t_win:.2f}s (video {reel.v_pop:.2f}s)')
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='reels/out/arena-balloon.mp4')
    ap.add_argument('--episode', type=int, default=3)
    ap.add_argument('--seed', type=int)
    a = ap.parse_args()
    render(a.out, a.episode, a.seed)
