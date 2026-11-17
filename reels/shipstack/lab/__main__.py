"""Render a ShipStack Lab reel by name.

    python -m reels.shipstack.lab --reel lab01 --out reels/out/lab01.mp4 [--grid]
    python -m reels.shipstack.lab --list
"""
import argparse
import importlib

from . import pipeline

REELS = {
    'lab01': ('brachistochrone', 'Brachistochrone', 'Which ball arrives first? (straight vs cycloid)'),
    'lab02': ('montecarlo_pi', 'MonteCarloPi', 'Can random dots find pi? (Monte Carlo)'),
}


def render(reel, out, grid=False, variant=0):
    module_name, scene_name, _ = REELS[reel]
    module = importlib.import_module(f'{__package__}.{module_name}')
    module.VARIANT = variant
    return pipeline.render(getattr(module, scene_name), out, module.soundtrack, reel, grid)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--reel', choices=sorted(REELS))
    ap.add_argument('--out', default=None)
    ap.add_argument('--grid', action='store_true', help='overlay the page grid to check alignment')
    ap.add_argument('--variant', type=int, default=0, help='a different fixed setup (drop / seed)')
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args()
    if a.list or not a.reel:
        for key, (_, _, title) in REELS.items():
            print(f'{key}  {title}')
        return
    print(render(a.reel, a.out or f'reels/out/{a.reel}.mp4', a.grid, a.variant))


if __name__ == '__main__':
    main()
