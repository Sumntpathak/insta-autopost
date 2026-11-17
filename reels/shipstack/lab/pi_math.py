"""Pure maths for Lab Nº 02 (no Manim), shared by the renderer and the caption writer."""
import math

import numpy as np

N = 20000


def seed_for(variant):
    return 7 + 1009 * variant          # variant 0 is the original sample (seed 7)


def dots(variant=0):
    rng = np.random.default_rng(seed_for(variant))
    pts = rng.random((N, 2))
    return pts, (pts ** 2).sum(axis=1) <= 1.0


def final_estimate(variant=0):
    _, inside = dots(variant)
    est = 4 * inside.sum() / N
    return est, abs(est - math.pi) / math.pi
