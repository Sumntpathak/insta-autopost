"""The ShipStack Lab page grid. Every Lab reel is built from these slots, so spacing is
identical across reels and nothing is placed by eye.

Horizontal: one text/figure column from LEFT to RIGHT (84 -> 996 px, 912 px wide).
Vertical slots (px, centres unless noted). Blocks are separated by equal breathing room
(~64-80 px); the masthead starts below Instagram's top bar (~140 px) and the page fills the
full height down to ~1745 px:

    MAST      164   kicker (left) + handle (right)
    RULE_1    200   hairline
    HEAD_1    280   headline line 1   (serif, 84 px cap)
    HEAD_2    386   headline line 2
    DEK       504   one-line subtitle (sans, 24 px cap)
    FIG       584 -> 1262   figure box (top/bottom edges)
    RULE_2    1334  hairline
    EQ        1406  equation (left) + note (right); single-line maths only
    TABLE     1494  column headers;  rows at 1556, 1622
    END       1720  conclusion line (page fills the full height)
"""
import numpy as np
from manim import RIGHT, DecimalNumber, Line, MarkupText, MathTex, Text, VGroup

from . import style as S

from .. import brand

LEFT_X, RIGHT_X = brand.LEFT_X, brand.RIGHT_X
WIDTH = RIGHT_X - LEFT_X
_g = brand.LAB
MAST, RULE_1, HEAD_1, HEAD_2, DEK = _g['MAST'], _g['RULE_1'], _g['HEAD_1'], _g['HEAD_2'], _g['DEK']
FIG_TOP, FIG_BOTTOM = _g['FIG_TOP'], _g['FIG_BOTTOM']
RULE_2, EQ, TABLE_HEAD, ROWS, END = _g['RULE_2'], _g['EQ'], _g['TABLE_HEAD'], _g['ROWS'], _g['END']
HEAD_CAP, DEK_CAP, KICK_CAP = brand.HEAD_CAP, brand.DEK_CAP, brand.KICK_CAP


def right(mob, x, y):
    """Place mob with its right edge at x px, vertical centre at y px."""
    return mob.move_to(S.P(x, y), aligned_edge=RIGHT)


def hairline(y):
    return Line(S.P(LEFT_X, y), S.P(RIGHT_X, y), stroke_width=1.6, color=S.RULE)


def masthead(kicker):
    k = S.left(Text(kicker, font=S.SANS, weight='SEMIBOLD', font_size=S.fs(KICK_CAP), color=S.ACCENT), LEFT_X, MAST)
    h = right(Text('@shipstack_', font=S.MONO, font_size=S.fs(KICK_CAP), color=S.MUTED), RIGHT_X, MAST)
    return VGroup(k, h)


def kicker_only(kicker):
    return S.left(Text(kicker, font=S.SANS, weight='SEMIBOLD', font_size=S.fs(KICK_CAP), color=S.ACCENT), LEFT_X, MAST)


def headline(line1, line2_markup):
    """Two serif lines; put the accent word of line 2 in <i>…</i> (italic + accent colour)."""
    line2 = line2_markup.replace('<i>', f'<i><span foreground="{S.ACCENT}">').replace('</i>', '</span></i>')
    a = S.left(MarkupText(line1, font=S.SERIF, font_size=S.fs(HEAD_CAP), color=S.INK), LEFT_X, HEAD_1)
    b = S.left(MarkupText(line2, font=S.SERIF, font_size=S.fs(HEAD_CAP), color=S.INK), LEFT_X, HEAD_2)
    return VGroup(a, b)


def dek(text):
    return S.left(Text(text, font=S.SANS, font_size=S.fs(DEK_CAP), color=S.MUTED), LEFT_X, DEK)


def equation(tex, note):
    e = S.left(MathTex(tex, font_size=S.fs(44), color=S.INK), LEFT_X, EQ)
    if e.height * 120 > 76:                      # keep tall maths inside its slot
        e.scale_to_fit_height(76 / 120)
        S.left(e, LEFT_X, EQ)
    n = right(Text(note, font=S.SANS, font_size=S.fs(19), color=S.MUTED), RIGHT_X, EQ)
    return VGroup(e, n)


def conclusion(markup, color=None):
    return S.left(MarkupText(markup, font=S.SERIF, font_size=S.fs(38), color=color or S.ACCENT), LEFT_X, END)


def legend(items, y=None):
    """Row of (dot colour, markup label) at the top of the figure box."""
    from manim import Dot
    y = y or FIG_TOP + 14
    g, x = VGroup(), LEFT_X
    for color, label in items:
        d = Dot(S.P(x + 9, y), radius=9 / 120, color=color)
        t = S.left(MarkupText(label, font=S.SERIF, font_size=S.fs(30), color=S.INK), x + 30, y)
        g.add(d, t)
        x = t.get_right()[0] * 120 + S.W / 2 + 44
    return g


class Table:
    """Label column at LEFT_X plus right-aligned numeric columns; units live in the headers."""

    def __init__(self, columns):
        # columns: [(header, right_edge_px)]; first column is the row label.
        self.columns = columns
        self.header = VGroup()
        for title, x in columns[1:]:
            self.header.add(right(Text(title, font=S.SANS, weight='SEMIBOLD', font_size=S.fs(16), color=S.MUTED), x, TABLE_HEAD))
        self.rows = VGroup()

    def row(self, index, label, color, values, decimals):
        y = ROWS[index]
        name = S.left(MathTex(label, font_size=S.fs(38), color=color), LEFT_X, y)
        nums = []
        for (_, x), v, d in zip(self.columns[1:], values, decimals):
            num = DecimalNumber(v, num_decimal_places=d, font_size=S.fs(38), color=S.INK)
            right(num, x, y)
            nums.append((num, x, y))
        self.rows.add(VGroup(name, *[n for n, *_ in nums]))
        return nums


def fit(points, pad=0.0, top=FIG_TOP, bottom=FIG_BOTTOM):
    """Scale/translate pixel-space geometry to fill the figure box (uniform scale, centred)."""
    pts = np.asarray(points, dtype=float)
    lo, hi = pts.min(axis=0) - pad, pts.max(axis=0) + pad
    scale = min(WIDTH / (hi[0] - lo[0]), (bottom - top) / (hi[1] - lo[1]))
    off = np.array([LEFT_X + (WIDTH - (hi[0] - lo[0]) * scale) / 2,
                    top + (bottom - top - (hi[1] - lo[1]) * scale) / 2])
    return lambda p: (np.asarray(p, dtype=float) - lo) * scale + off, scale


def grid_overlay():
    """Debug: draw every slot line (use with --grid to check alignment)."""
    g = VGroup()
    for y in (MAST, RULE_1, HEAD_1, HEAD_2, DEK, FIG_TOP, FIG_BOTTOM, RULE_2, EQ, TABLE_HEAD, *ROWS, END, S.SAFE_BOTTOM):
        g.add(Line(S.P(0, y), S.P(S.W, y), stroke_width=1, color='#00A3FF', stroke_opacity=0.5))
    for x in (LEFT_X, RIGHT_X):
        g.add(Line(S.P(x, 0), S.P(x, S.H), stroke_width=1, color='#00A3FF', stroke_opacity=0.5))
    return g
