"""ShipStack Lab Nº 02: find π with random dots. python -m reels.shipstack.lab.montecarlo_pi --out x.mp4 [--grid]

Real Monte Carlo: a fixed seed scatters N points in a square; the share inside the quarter
circle is π/4. Every number on screen is computed from the dots drawn so far.
"""
import argparse
import math

import numpy as np
from manim import UP, FadeIn, FadeOut, Scene, Text, ValueTracker, VGroup, Write, linear

from . import figure as F, layout as L, pi_math, pipeline, sound, style as S

N = pi_math.N                    # large enough that the error visibly shrinks
VARIANT = 0                      # set by the renderer; each variant is a different fixed seed
START, END = 0.5, 10.5            # dots arrive on an accelerating schedule between these times
SIDE = L.FIG_BOTTOM - L.FIG_TOP   # square fills the figure height, left-aligned


def dots():
    return pi_math.dots(VARIANT)


def count_at(sec):
    x = min(max((sec - START) / (END - START), 0.0), 1.0)
    return int(round(N * x ** 2))


def estimate(n, inside):
    return 4 * inside[:n].sum() / n if n else 0.0


class MonteCarloPi(pipeline.Clocked, Scene):
    grid = False

    def construct(self):
        if self.grid:
            self.add(L.grid_overlay())
        pts, inside = dots()
        clock = ValueTracker(0.0)
        mast = L.masthead('SHIPSTACK LAB  ·  Nº 02  ·  PROBABILITY')
        head = L.headline('Can random dots', 'find <i>π?</i>')
        sub = L.dek('Throw dots at a square. Count the ones inside the arc.')

        fig = F.SkiaFigure()
        px = pts * (SIDE - 8) + 4                                 # unit square -> pixels (y up = row down)
        px[:, 1] = SIDE - px[:, 1]

        drawn = [0]
        pin, pout = F.paint(S.ACCENT, 0.85), F.paint(S.SOFT, 0.9)
        frame_paint = F.paint(S.INK, 1, stroke=2)
        arc = F.skia.Path()
        arc.addArc(F.skia.Rect(4 - (SIDE - 8), 4, SIDE - 4, 2 * SIDE - 12), 270, 90)

        def draw(c):                                          # only the dots added since the last frame
            n = count_at(clock.get_value())
            for (x, y), ins in zip(px[drawn[0]:n], inside[drawn[0]:n]):
                c.drawCircle(float(x), float(y), 2.3, pin if ins else pout)
            drawn[0] = n
            c.drawRect(F.skia.Rect(2, 2, SIDE - 2, SIDE - 2), frame_paint)
            c.drawPath(arc, F.paint(S.INK, 1, stroke=3))

        fig.show(draw, keep=True)
        fig.mob.add_updater(lambda m: fig.show(draw, keep=True))

        # Right column inside the figure slot: the live estimate, typeset as a magazine sidebar.
        col = L.LEFT_X + SIDE + 48
        lab = lambda t, y: S.left(Text(t, font=S.SANS, weight='SEMIBOLD', font_size=S.fs(16), color=S.MUTED), col, y)
        from manim import DecimalNumber, MathTex
        est = DecimalNumber(0, num_decimal_places=4, font_size=S.fs(60), color=S.ACCENT)
        est.add_updater(lambda m: S.left(m.set_value(estimate(count_at(clock.get_value()), inside)), col, L.FIG_TOP + 118)
                       .set_opacity(1 if count_at(clock.get_value()) else 0))
        true_v = S.left(MathTex(r'3.1416\ldots', font_size=S.fs(36), color=S.INK), col, L.FIG_TOP + 262)
        err = DecimalNumber(0, num_decimal_places=2, unit=r'\%', font_size=S.fs(36), color=S.INK)
        err.add_updater(lambda m: S.left(m.set_value(
            100 * abs(estimate(count_at(clock.get_value()), inside) - math.pi) / math.pi if count_at(clock.get_value()) else 0), col, L.FIG_TOP + 392)
            .set_opacity(1 if count_at(clock.get_value()) else 0))
        sidebar = VGroup(lab('ESTIMATE  π ≈', L.FIG_TOP + 48), lab('TRUE VALUE', L.FIG_TOP + 210),
                         lab('ERROR', L.FIG_TOP + 340), true_v)

        eq = L.equation(r'\pi \approx 4 \times \frac{\text{inside}}{\text{total}}', 'quarter circle ÷ square = π/4')
        table = L.Table([('', 0), ('DOTS', 640), ('SHARE  %', L.RIGHT_X)])
        for k, (label, color) in enumerate(((r'\text{inside}', S.ACCENT), (r'\text{outside}', S.MUTED))):
            for col_i, (num, x, y) in enumerate(table.row(k, label, color, [0, 0], [0, 1])):
                def upd(m, k=k, col_i=col_i, x=x, y=y):
                    n = count_at(clock.get_value())
                    k_in = int(inside[:n].sum())
                    count = k_in if k == 0 else n - k_in
                    L.right(m.set_value(count if col_i == 0 else (100 * count / n if n else 0)), x, y)
                num.add_updater(upd)

        self.add(mast, L.hairline(L.RULE_1), head, sub, fig.mob, sidebar, est, err,
                 L.hairline(L.RULE_2), eq, table.header, table.rows)
        self.timed(clock.animate.set_value(END), run_time=END, rate_func=linear)
        final = estimate(N, inside)
        result = L.conclusion(f'{N:,} dots give π ≈ {final:.4f} — <i>off by {abs(final - math.pi) / math.pi:.2%}.</i>')
        self.timed(Write(result), run_time=1.0)
        self.timed(clock.animate.set_value(END + 0.01), run_time=0.4, rate_func=linear)

        kick2 = L.kicker_only('THE RULE  ·  SAVE THIS')
        head2 = L.headline('Count enough,', 'chance gets <i>precise.</i>')
        sub2 = L.dek('Monte Carlo: 4× the dots, 2× the accuracy.')
        eq2 = L.equation(r'\text{error} \propto 1/\sqrt{n}', 'used in physics, finance and AI')
        self.timed(FadeOut(VGroup(mast[0], head, sub, eq), shift=UP * 0.2),
                   FadeIn(VGroup(kick2, head2, sub2, eq2), shift=UP * 0.2), run_time=1.2)
        self.finish()


def soundtrack(path):
    pts, inside = dots()
    tl = sound.Timeline(S.SECONDS)
    tl.add(0, sound.pad(float(S.SECONDS), 73.42), 0.5)
    last = 0
    for f in range(int(START * S.FPS), int(END * S.FPS)):        # soft texture that follows the dot rate
        sec = f / S.FPS
        n = count_at(sec)
        if n - last >= 1 and f % 2 == 0:
            new_in = int(inside[last:n].sum())
            tl.add(sec, sound.pluck(sound.PENTA[(f // 2) % 5 + (5 if new_in > (n - last) / 2 else 0)], 0.25),
                   min(0.22, 0.05 + 0.002 * (n - last)), ((f * 37) % 100) / 100 - 0.5)
            last = n
    for i, n in enumerate(range(N // 5, N + 1, N // 5)):          # milestone every fifth of the dots
        sec = START + (END - START) * math.sqrt(n / N)
        tl.add(sec, sound.pluck(sound.PENTA[5 + i], 0.7), 0.4)
    tl.add(END + 0.1, sound.chord(293.66), 0.45)
    tl.add(11.6, sound.chord(196.0, 2.8), 0.35)
    tl.write(path)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='reels/out/lab02.mp4')
    ap.add_argument('--grid', action='store_true')
    a = ap.parse_args()
    pipeline.render(MonteCarloPi, a.out, soundtrack, 'lab02', a.grid)
