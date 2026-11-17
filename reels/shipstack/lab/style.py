"""ShipStack Lab editorial style. One place for type, colour, grid and timing.

Magazine layout, no cards or borders: paper background, serif headline with one italic
accent word, small-caps kicker, hairline rules, LaTeX equations, monospaced live numbers.
Canvas: 1080x1920 @ 30 fps; Manim frame is 9 x 16 units, so 1 unit = 120 px.
"""
from pathlib import Path

import manimpango
import numpy as np
from manim import config

from .. import brand

FONTS = brand.FONTS
for _f in FONTS.glob('*.ttf'):
    manimpango.register_font(str(_f))

SERIF, SANS, MONO = 'Instrument Serif', 'Inter', 'JetBrains Mono'
PAPER, INK, MUTED, RULE, ACCENT, SOFT = brand.PAPER, brand.INK, brand.MUTED, brand.RULE, brand.ACCENT, brand.SOFT
BLUE = '#0EA5E9'        # second series colour
W, H, FPS, SECONDS = 1080, 1920, 30, 15
MARGIN = 84             # left text edge, px
SAFE_BOTTOM = 1620      # IG caption overlay sits below this (short captions)


def setup(out_dir, name):
    config.pixel_width, config.pixel_height = W, H
    config.frame_height, config.frame_width = 16.0, 9.0
    config.frame_rate = FPS
    config.background_color = PAPER
    config.media_dir = str(out_dir)
    config.output_file = name
    config.disable_caching = True
    config.verbosity = 'WARNING'
    config.progress_bar = 'none'


def P(x, y):
    """Pixel position (x right, y down) to Manim coordinates."""
    return np.array([(x - W / 2) / 120, (H / 2 - y) / 120, 0.0])


def fs(cap_px):
    """Font size giving the requested cap height in pixels."""
    return cap_px / 1.2


def left(mob, x, y):
    """Place mob with its left edge at x px and vertical centre at y px."""
    mob.move_to(P(x, y), aligned_edge=np.array([-1, 0, 0]))
    mob.shift((P(x, 0)[0] - mob.get_left()[0]) * np.array([1, 0, 0]))
    return mob
