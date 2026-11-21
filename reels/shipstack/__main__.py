"""Render any ShipStack format by name (all output passes reels/verify.py).

    python -m reels.shipstack --list
    python -m reels.shipstack --format ring --out reels/out/ring.mp4 [--episode 3] [--seed 123]
"""
import argparse

FORMATS = {
    'lab01': 'Lab Nº 01 · Which ball arrives first? (brachistochrone, Manim, 30 fps)',
    'lab02': 'Lab Nº 02 · Can random dots find pi? (Monte Carlo, Manim, 30 fps)',
    'ring': 'Arena · Ring Escape, pick a ball 1-6 (pymunk + skia, 60 fps)',
    'strings': 'Arena · Country String Battle (skia, 60 fps)',
    'balloon': 'Arena · Balloon Pop, pick a balloon 1-6 (skia, 60 fps, slow-motion finish)',
    'automation': 'Studio · AI Automation: text-only typed reel (Remotion, 30 fps); episode N = film/src/automations.json entry N',
    'dsa': 'Studio · DSA debugger: real code stepped line by line; episode N = problem #N (Pillow, 30 fps)',
}


def _arena(fmt, out, episode, seed):
    if fmt == 'ring':
        from .arena import ring
        return ring.render(out, 2026 + 1000 * episode if seed is None else seed, episode)   # disjoint search ranges
    if fmt == 'strings':
        from .arena import strings
        return strings.render(out, episode=episode, seed=seed)
    from .arena import balloon
    return balloon.render(out, episode=episode, seed=seed)


def render(fmt, out, episode=1, seed=None):
    if fmt.startswith('lab'):
        from .lab.__main__ import render as lab
        return lab(fmt, out, variant=episode - 1)          # Lab: episode N = variant N-1
    if fmt in ('ring', 'strings', 'balloon'):
        result = _arena(fmt, out, episode, seed)
        from . import badge
        badge.apply(out, episode)          # big '#NN' so grid covers never look like re-uploads
        return result
    if fmt == 'automation':
        import os
        import subprocess
        from pathlib import Path
        film = Path(__file__).resolve().parents[2] / 'film'
        out_abs = Path(out).resolve()
        out_abs.parent.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, COMP='AutomationReel', EPISODE=str(episode), OUT=str(out_abs))
        subprocess.run(['node', 'render.mjs'], cwd=film, env=env, check=True)
        return out
    if fmt == 'dsa':
        from .studio import dsa
        return dsa.render(out, episode)
    raise SystemExit(f'Unknown format {fmt}; see --list')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--format', choices=sorted(FORMATS))
    ap.add_argument('--out')
    ap.add_argument('--episode', type=int, default=1, help='episode number: a new race (Arena) or setup (Lab)')
    ap.add_argument('--seed', type=int, help='Arena formats: explicit base seed')
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args()
    if a.list or not a.format:
        for k, v in FORMATS.items():
            print(f'{k:8} {v}')
        return
    print(render(a.format, a.out or f'reels/out/{a.format}.mp4', a.episode, a.seed))


if __name__ == '__main__':
    main()
