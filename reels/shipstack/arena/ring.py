"""ShipStack Arena: Ring Escape (pick a ball 1-6). python -m reels.shipstack.arena.ring --out x.mp4 [--seed N]

Real pymunk simulation (ring_physics.py); the pacing search only chooses a seed whose
natural outcome has a clear winner inside the target window. Editorial page, 60 fps.
"""
import argparse
import math
import tempfile
from pathlib import Path

import numpy as np
import skia

from .. import brand
from ..lab import sound
from . import page as P, ring_physics as sim

RELEASE = 1.0                     # no countdown: the headline is the hook
G = brand.ARENA
BOX_C = ((brand.LEFT_X + brand.RIGHT_X) / 2, (G['FIG_TOP'] + G['FIG_BOTTOM']) / 2)
HOLD = 30                         # winner rests this far outside the gap (px, sim frame)
SCALE = ((G['FIG_BOTTOM'] - G['FIG_TOP']) / 2 - 8) / (sim.RADIUS + sim.BALL_R + HOLD)


def to_box(p):
    return (BOX_C[0] + (p[0] - sim.CENTER[0]) * SCALE, BOX_C[1] + (p[1] - sim.CENTER[1]) * SCALE)


def ease(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


class RingReel:
    def __init__(self, seed, episode):
        self.run = sim.choose(seed)
        self.episode = episode
        self.page = P.Page()
        self.win = self.run.winner
        self.t_win = self.run.escapes[self.win]
        self.reveal = RELEASE + self.t_win + 0.25
        self.win_step = int(self.t_win * sim.HZ)
        imp = np.array([(t, b) for t, b, *_ in self.run.impacts]) if self.run.impacts else np.zeros((0, 2))
        self.imp = imp

    def step(self, sec):
        return int(min(max(0.0, sec - RELEASE), sim.SIM_SECONDS) * sim.HZ)

    def bounces(self, ball, sec):
        t = sec - RELEASE
        if not len(self.imp):
            return 0
        end = min(t, self.run.escapes.get(ball, math.inf))
        return int(((self.imp[:, 1] == ball) & (self.imp[:, 0] <= end)).sum())

    def frame(self, sec):
        surface = P.new_surface()
        c = surface.getCanvas()
        pg, t = self.page, self.page.t
        revealed = sec >= self.reveal
        pg.masthead(c, f'SHIPSTACK ARENA  ·  Nº {self.episode:02d}  ·  RING ESCAPE')
        if revealed:
            a = ease((sec - self.reveal) / 0.35)
            pg.headline(c, f'Ball {self.win + 1}', '', 'escapes first.', brand.BALLS[self.win], alpha=a)
        else:
            pg.headline(c, 'Which ball', 'escapes ', 'first?')
        share = sim.GAP / (2 * math.pi)
        elapsed = max(0.0, min(sec, self.reveal) - RELEASE)
        pg.dek(c, f'Six balls, one gap: just {share:.1%} of the ring.', f'{elapsed:4.1f}s',
               brand.ACCENT if revealed else brand.INK)

        # Figure (clipped to its box so escaped balls fall out of frame cleanly).
        c.save()
        c.clipRect(skia.Rect(0, G['FIG_TOP'], brand.W, G['FIG_BOTTOM']))
        k = self.step(sec)
        ang = self.run.ring_angle[k]
        r = sim.RADIUS * SCALE
        rect = skia.Rect(BOX_C[0] - r, BOX_C[1] - r, BOX_C[0] + r, BOX_C[1] + r)
        path = skia.Path()
        path.addArc(rect, math.degrees(ang + sim.GAP / 2), math.degrees(2 * math.pi - sim.GAP))
        c.drawPath(path, P.paint(brand.INK, 1, stroke=5, cap='round'))
        br = sim.BALL_R * SCALE
        for i, col in enumerate(brand.BALLS):
            pos = self.run.positions[k, i]
            if i == self.win and k > self.win_step:          # hold the winner just outside the gap
                ex, ey = self.run.positions[self.win_step, i]
                dx, dy = ex - sim.CENTER[0], ey - sim.CENTER[1]
                n = math.hypot(dx, dy) or 1
                o = ease((k - self.win_step) / (0.35 * sim.HZ))
                pos = (ex + dx / n * HOLD * o, ey + dy / n * HOLD * o)
            x, y = to_box(pos)
            if sec > RELEASE:                                # short motion trail
                for back, alpha in ((12, 0.08), (8, 0.13), (4, 0.2)):
                    tx, ty = to_box(self.run.positions[max(0, k - back), i])
                    if math.hypot(tx - x, ty - y) > 4 and not (i == self.win and k > self.win_step):
                        c.drawCircle(tx, ty, br * 0.82, P.paint(col, alpha))
            dim = 0.35 if revealed and i != self.win else 1.0
            c.drawCircle(x, y, br, P.paint(col, dim))
            t.text(c, str(i + 1), x, y, t.sans_semi, br * 0.78, brand.PAPER, 'center', dim)
            if revealed and i == self.win:
                c.drawCircle(x, y, br + 9, P.paint(brand.ACCENT, ease((sec - self.reveal) / 0.3), stroke=3))
        c.restore()

        # Scoreboard: rim bounces per ball; the winner's cell turns into its escape time.
        pg.board_head(c, 'BOUNCES OFF THE RIM')
        for i, (x0, x1, y) in enumerate(pg.cells()):
            col = brand.BALLS[i]
            c.drawCircle(x0 + 18, y, 18, P.paint(col))
            t.text(c, str(i + 1), x0 + 18, y, t.sans_semi, 15, brand.PAPER, 'center')
            out = self.run.escapes.get(i)
            if out is not None and sec >= RELEASE + out:
                t.text(c, f'out {out:.1f}s', x1, y, t.mono, 22, brand.ACCENT if i == self.win else brand.MUTED, 'right')
            else:
                t.text(c, str(self.bounces(i, sec)), x1, y, t.mono, 26, brand.INK, 'right')
        if revealed:
            n = self.bounces(self.win, sec)
            pg.conclusion(c, f'{n} bounces, then through the gap. ', 'Did you pick it?',
                          alpha=ease((sec - self.reveal - 0.3) / 0.4))
        return surface

    def soundtrack(self, path):
        tl = sound.Timeline(brand.SECONDS)
        tl.add(0, sound.pad(float(brand.SECONDS), 65.41), 0.45)
        tl.add(RELEASE, sound.pluck(sound.PENTA[7], 0.5), 0.45)
        last = {}
        for t, ball, strength, x in self.run.impacts:
            at = RELEASE + t
            if at > self.reveal + 2.5 or at - last.get(ball, -1) < 0.08:
                continue
            last[ball] = at
            pan = float(np.clip((x - sim.CENTER[0]) / sim.RADIUS, -0.8, 0.8))
            tl.add(at, sound.pluck(sound.PENTA[ball % 5 + (5 if strength > 0.6 else 0)], 0.3), 0.06 + 0.14 * strength, pan)
        for ball, t in self.run.escapes.items():
            tl.add(RELEASE + t, sound.pluck(sound.PENTA[9 if ball == self.win else 3], 0.8), 0.5 if ball == self.win else 0.15)
        tl.add(self.reveal, sound.chord(261.63, 2.6), 0.45)
        tl.write(path)


def render(out, seed=2026, episode=2):
    reel = RingReel(seed, episode)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / 'audio.wav'
        reel.soundtrack(wav)
        enc = P.Encoder(out, wav)
        for f in range(P.FRAMES):
            enc.write(reel.frame(f / P.FPS))
        enc.close()
    print(f'Ring Escape: seed {reel.run.seed}, winner ball {reel.win + 1} at {reel.t_win:.2f}s')
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='reels/out/arena-ring.mp4')
    ap.add_argument('--seed', type=int, default=2026)
    ap.add_argument('--episode', type=int, default=2)
    a = ap.parse_args()
    render(a.out, a.seed, a.episode)
