"""ShipStack Lab Nº 01: the brachistochrone. python -m reels.shipstack.lab.brachistochrone --out x.mp4 [--grid]

Question -> live calculation -> answer -> the rule (a frame worth saving).
Physics is the verified simulation from reels/experiments/track_race.py (matches the
closed-form cycloid time to 1e-7); both balls share one slow-motion factor.
"""
import argparse

import numpy as np
from manim import UP, DashedLine, Dot, FadeIn, FadeOut, MarkupText, Scene, Text, ValueTracker, VGroup, VMobject, Write, linear

from . import layout as L, pipeline, sound, style as S
from ...experiments import track_race as phys

VARIANTS = [(930.0, 1000.0), (900.0, 940.0), (950.0, 1060.0), (880.0, 900.0), (960.0, 980.0), (910.0, 1040.0)]
VARIANT = 0                        # set by the renderer: a different finish point (drop and distance)
RELEASE, RACE = 1.2, 7.4          # no countdown: the headline is the hook, the race starts quickly


def physics():
    phys.END = VARIANTS[VARIANT % len(VARIANTS)]
    paths, runs, totals, winner, _ = phys.physics()
    return paths, runs, totals, winner, RACE / max(totals)   # one shared slow-motion factor


def at(sec, path, run, slow):
    times, speed = run
    real = min(max(0.0, (sec - RELEASE) / slow), times[-1])
    i = int(np.clip(np.searchsorted(times, real), 1, len(times) - 1))
    f = (real - times[i - 1]) / max(times[i] - times[i - 1], 1e-12)
    return path[i - 1] + f * (path[i] - path[i - 1]), speed[i - 1] + f * (speed[i] - speed[i - 1]), real


class Brachistochrone(pipeline.Clocked, Scene):
    grid = False

    def construct(self):
        if self.grid:
            self.add(L.grid_overlay())
        paths, runs, totals, winner, slow = physics()
        colors = [S.INK, S.ACCENT]
        clock = ValueTracker(0.0)

        mast = L.masthead('SHIPSTACK LAB  ·  Nº 01  ·  PHYSICS')
        head = L.headline('Which ball', 'arrives <i>first?</i>')
        sub = L.dek('Same drop. Same finish line. Only gravity.')

        # Figure: legend row, then the real track geometry scaled to fill the rest of the box.
        legend = L.legend([(S.INK, '<i>A</i>  straight'), (S.ACCENT, '<i>B</i>  cycloid')])
        r = 22                                   # ball radius, px
        to_px, _ = L.fit(np.vstack(paths), pad=r + 4, top=L.FIG_TOP + 70)
        tracks = VGroup(*[VMobject(stroke_color=colors[k], stroke_width=5).set_points_smoothly(
            [S.P(*to_px(p)) for p in np.vstack([path[::10], path[-1:]])]) for k, path in enumerate(paths)])
        end_x = to_px(paths[0][-1])[0] + r + 8
        ys = [to_px(p[-1])[1] for p in paths]
        finish = DashedLine(S.P(end_x, min(ys) - 50), S.P(end_x, max(ys) + 40), dash_length=0.07, stroke_width=2, color=S.MUTED)
        balls = [Dot(S.P(*to_px(paths[k][0])), radius=r / 120, color=colors[k]) for k in range(2)]
        for k, b in enumerate(balls):
            b.add_updater(lambda m, k=k: m.move_to(S.P(*to_px(at(clock.get_value(), paths[k], runs[k], slow)[0]))))

        # Data: equation, then an aligned table (units in the headers, numbers right-aligned).
        eq = L.equation(r'v=\sqrt{2gh}', 'energy in = speed out')
        table = L.Table([('', 0), ('SPEED  m/s', 640), ('TIME  s', L.RIGHT_X)])
        for k in range(2):
            for col, (num, x, y) in enumerate(table.row(k, 'AB'[k], colors[k], [0, 0], [2, 3])):
                num.add_updater(lambda m, k=k, col=col, x=x, y=y:
                                L.right(m.set_value(at(clock.get_value(), paths[k], runs[k], slow)[1 + col]), x, y))

        self.add(mast, L.hairline(L.RULE_1), head, sub, legend, tracks, finish, *balls,
                 L.hairline(L.RULE_2), eq, table.header, table.rows)

        self.timed(clock.animate.set_value(RELEASE), run_time=RELEASE, rate_func=linear)
        self.timed(clock.animate.set_value(RELEASE + RACE), run_time=RACE, rate_func=linear)
        diff, ratio = totals[1 - winner] - totals[winner], 1 - totals[winner] / totals[1 - winner]
        result = L.conclusion(f'<i>B</i> arrives {diff:.3f} s sooner — <i>{ratio:.0%} less time.</i>')
        self.timed(Write(result), run_time=1.1)
        self.timed(clock.animate.set_value(RELEASE + RACE + 0.01), run_time=0.5, rate_func=linear)

        # The rule: the frame people save. Same slots, new words.
        kick2 = L.kicker_only('THE RULE  ·  SAVE THIS')
        head2 = L.headline('Speed early', 'beats <i>distance.</i>')
        sub2 = L.dek('Bernoulli, 1696: the fastest slide is a cycloid.')
        eq2 = L.equation(r'T=\int ds\,/\sqrt{2gy}', 'time = distance ÷ speed, summed')
        self.timed(FadeOut(VGroup(mast[0], head, sub, eq), shift=UP * 0.2),
                   FadeIn(VGroup(kick2, head2, sub2, eq2), shift=UP * 0.2), run_time=1.2)
        self.finish()


def soundtrack(path):
    paths, runs, totals, winner, slow = physics()
    tl = sound.Timeline(S.SECONDS)
    tl.add(0, sound.pad(float(S.SECONDS)), 0.5)
    tl.add(RELEASE, sound.pluck(sound.PENTA[7], 0.5), 0.5)
    for k in range(2):                                          # quarter-distance markers, panned per lane
        times = runs[k][0]
        for q, frac in enumerate((0.25, 0.5, 0.75)):
            tl.add(RELEASE + times[int(frac * (len(times) - 1))] * slow, sound.pluck(sound.PENTA[q + (3 if k else 0)], 0.35),
                   0.25, -0.5 if k == 0 else 0.5)
        tl.add(RELEASE + totals[k] * slow, sound.pluck(sound.PENTA[9 if k == winner else 4], 0.8),
               0.55 if k == winner else 0.3, -0.5 if k == 0 else 0.5)
    tl.add(RELEASE + RACE + 0.1, sound.chord(), 0.45)
    tl.add(RELEASE + RACE + 1.6, sound.chord(196.0, 2.8), 0.35)   # the rule appears
    tl.write(path)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='reels/out/lab01.mp4')
    ap.add_argument('--grid', action='store_true', help='overlay the page grid to check alignment')
    a = ap.parse_args()
    pipeline.render(Brachistochrone, a.out, soundtrack, 'lab01', a.grid)
