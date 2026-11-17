"""ShipStack brand: the single source of truth for colour, type and page grids.

Pure Python (no Manim/skia imports) so every engine can use it:
  - lab/      editorial maths & physics reels (Manim)
  - arena/    ball races and country battles (skia, 60 fps)
"""
from pathlib import Path

FONTS = Path(__file__).resolve().parent / 'fonts'       # SIL OFL; licences in the folder
SERIF = FONTS / 'InstrumentSerif-Regular.ttf'
SERIF_ITALIC = FONTS / 'InstrumentSerif-Italic.ttf'
SANS = FONTS / 'Inter-Variable.ttf'
MONO = FONTS / 'JetBrainsMono-Variable.ttf'

# Palette: cool white page, near-black ink, one indigo accent (from the logo violet).
PAPER = '#FFFFFF'
INK = '#0D1117'
MUTED = '#667085'
RULE = '#E4E7EC'
ACCENT = '#4F46E5'
SOFT = '#B8BFCC'
HANDLE = '@shipstack_'

# Distinct colours that stay readable on white (balls 1-6).
BALLS = ['#E5484D', '#F76B15', '#D4A000', '#30A46C', '#0090FF', '#8E4EC6']

W, H = 1080, 1920
SECONDS = 15
LEFT_X, RIGHT_X = 84, 996                 # every text block and figure aligns to these edges

# Lab page grid (px, centres unless noted) — see lab/layout.py.
LAB = dict(MAST=164, RULE_1=200, HEAD_1=280, HEAD_2=386, DEK=504, FIG_TOP=584, FIG_BOTTOM=1262,
           RULE_2=1334, EQ=1406, TABLE_HEAD=1494, ROWS=(1556, 1622), END=1720)

# Arena page grid: same header, a taller figure, a 3x2 scoreboard instead of equation + table.
ARENA = dict(MAST=164, RULE_1=200, HEAD_1=280, HEAD_2=386, DEK=504, FIG_TOP=556, FIG_BOTTOM=1466,
             RULE_2=1500, BOARD_HEAD=1536, BOARD=(1586, 1650), END=1736)

HEAD_CAP, DEK_CAP, KICK_CAP = 84, 24, 20


def rgb(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
