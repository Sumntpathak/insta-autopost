"""Raster figure for many-particle scenes: skia draws into the figure slot, Manim shows it.

Thousands of dots or balls are too heavy as Manim mobjects; skia renders them anti-aliased
in a few milliseconds. The image is exactly the figure box size, so it sits 1:1 on the grid.
"""
import numpy as np
import skia
from manim import ImageMobject

from . import layout as L, style as S


def argb(hex_color, alpha=1.0):
    h = hex_color.lstrip('#')
    return (int(alpha * 255) << 24) | int(h, 16)


class SkiaFigure:
    def __init__(self, width=L.WIDTH, height=L.FIG_BOTTOM - L.FIG_TOP, top=L.FIG_TOP):
        self.w, self.h, self.top = width, height, top
        self.mob = ImageMobject(np.zeros((height, width, 4), dtype=np.uint8))
        self.mob.height = height / 120
        self.mob.move_to(S.P(L.LEFT_X + width / 2, top + height / 2))

    def show(self, draw, keep=False):
        """draw(canvas) paints one frame; the result replaces the image pixels.

        keep=True reuses one canvas across frames (draw only what is new, e.g. accumulating dots).
        """
        if not keep or not hasattr(self, '_surface'):
            self._surface = skia.Surface(self.w, self.h)
            self._surface.getCanvas().clear(argb(S.PAPER))   # opaque paper: no alpha mismatch with Manim
        draw(self._surface.getCanvas())
        self.mob.pixel_array = self._surface.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)


def paint(hex_color, alpha=1.0, stroke=None):
    p = skia.Paint(Color=argb(hex_color, alpha), AntiAlias=True)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
    return p
