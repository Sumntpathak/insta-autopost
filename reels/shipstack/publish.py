"""Publish one rendered ShipStack reel, safely. Used by .github/workflows/shipstack-reel.yml.

    python -m reels.shipstack.publish --reel ring --url https://.../ring.mp4 [--dry-run]

Safety (same contract as reels/campaign.py):
  1. reels/guard.py must allow posting now (60 min gap, 12/day cap) and the reel must not
     already have been posted today.
  2. The container is created and processed; then a 'publishing' record with its id is
     pushed to reels/state.json BEFORE media_publish, so an ambiguous failure is never retried.
  3. Only after Meta returns a media id is the record marked 'published'.
No Manim import: this runs on a small runner after the render job.
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'reels'))
import campaign  # noqa: E402
import guard  # noqa: E402

TAGS = '#physics #maths #science #stem #learning'
CAPTIONS = {
    'lab01': ('Which ball arrives first: the straight line or the curve?\n\n'
              'The curve wins. It drops steeply first and carries that speed the whole way. '
              'Johann Bernoulli posed this in 1696; the fastest slide is a cycloid.\n\n'
              'Save this for the next time someone says the shortest path is the fastest.\n\n'
              f'ShipStack Lab Nº 01 · @shipstack_\n{TAGS} #brachistochrone'),
    'lab02': None,    # computed per episode by caption(): the result changes with the seed
    'dsa': None,      # computed per episode by caption(): one problem per episode
    'ring': ('Which ball escapes first? Pick one before you watch.\n\n'
             'Six balls bounce inside a spinning ring with one tiny gap: just 4.1% of the rim. '
             'Real physics, no edits.\n\n'
             'Comment your number. Follow for the next race.\n\n'
             'ShipStack Arena · @shipstack_\n#physics #simulation #satisfying #pickone'),
    'strings': ('Which country survives the string battle?\n\n'
                "Every ball shoots strings to the wall. Touch another country's string and it is cut. "
                'At each knockout the country with the fewest strings is out. Real simulation, no edits.\n\n'
                'Comment your country for the next battle.\n\n'
                'ShipStack Arena · @shipstack_\n#simulation #satisfying #countries #physics'),
}
CAPTIONS['story'] = ('We ship.\n\n'
                    'From today, ShipStack posts three things:\n'
                    '→ AI news, verified, every source shown\n'
                    '→ AI automations you can copy\n'
                    '→ 1,200 DSA problems, debugged line by line\n\n'
                    "Follow so you don't miss #0001.\n\n"
                    '#ai #automation #dsa #coding #leetcode #programming')
CAPTIONS['balloon'] = ('Which balloon pops first? Pick one before you watch.\n\n'
                       'Every hit from the ball inside inflates it a little. 100% = pop. '
                       'Real simulation; the last second is in slow motion.\n\n'
                       'Comment your number. Follow for the next race.\n\n'
                       'ShipStack Arena · @shipstack_\n#satisfying #simulation #physics #pickone')
# Cover frame (ms into the clip) shown on the grid: a moment that differs per episode and is never black.
THUMB_MS = {'lab01': 2500, 'lab02': 2500, 'ring': 7000, 'strings': 7000, 'balloon': 7000, 'dsa': 1000, 'story': 3500}
COLLECTION = {'story': 'shipstack-brand', 'dsa': 'shipstack-dsa', 'lab01': 'shipstack-lab', 'lab02': 'shipstack-lab', 'ring': 'shipstack-arena',
              'strings': 'shipstack-arena', 'balloon': 'shipstack-arena'}


def caption(reel, episode=1):
    if reel == 'dsa':
        sys.path.insert(0, str(ROOT))
        from reels.shipstack.studio.problems import PROBLEMS
        p = PROBLEMS[episode]
        return (f"DSA #{episode:04d} · {p['title']}\n\n"
                f"{p['prompt']} Watch the code run line by line, with every variable shown.\n\n"
                f"Pattern: {p['pattern']} · {p['complexity']}\n\n"
                'Save this for your next interview. Follow for the next problem.\n\n'
                '#dsa #leetcode #coding #python #interviewprep #programming')
    if reel == 'lab02':
        sys.path.insert(0, str(ROOT))
        from reels.shipstack.lab import pi_math
        est, err = pi_math.final_estimate(episode - 1)
        return ('Can random dots find π?\n\n'
                'Drop dots in a square: the share inside the quarter circle is π/4. '
                f'{pi_math.N:,} random dots give π ≈ {est:.4f}, off by {err:.2%}.\n\n'
                'Save this: Monte Carlo error shrinks like 1/√n. 4× the dots, 2× the accuracy.\n\n'
                f'ShipStack Lab Nº 02 · @shipstack_\n{TAGS} #pi #probability')
    return CAPTIONS[reel]


def publish(reel, url, now=None, meta=None, read_state=campaign.read_state, persist=campaign.persist, dry_run=False,
            key=None, episode=1):
    if reel not in CAPTIONS:
        raise ValueError(f'Unknown reel {reel}')
    if not url.startswith('https://'):
        raise ValueError('A public HTTPS video URL is required')
    now = now or dt.datetime.now(guard.IST)
    state = read_state()
    key = key or f'SS-{now.date().isoformat()}-{reel}'
    if key in state['posts']:
        raise RuntimeError(f'{key} was already attempted; reconcile it instead of re-posting')
    reason = guard.blocked(state['posts'], now)
    if reason:
        raise RuntimeError(f'Posting plan blocks this publish: {reason}')
    if dry_run:
        print(f'Dry run OK: {key} would be published now.')
        return None
    meta = meta or campaign.Meta()
    meta.check_account()
    container = meta.call(f'{meta.ig_id}/media', {'media_type': 'REELS', 'video_url': url,
                                                   'caption': caption(reel, episode), 'share_to_feed': 'true',
                                                   'thumb_offset': str(THUMB_MS.get(reel, 2000))}, 'POST')['id']
    meta.ready(container)
    record = {'id': key, 'date': now.date().isoformat(), 'scene': reel, 'collection': COLLECTION[reel],
              'seconds': 15, 'episode': episode, 'caption': caption(reel, episode), 'container_id': container,
              'status': 'publishing', 'attempted_at': now.isoformat()}
    state['posts'][key] = record
    persist(state)
    media = meta.call(f'{meta.ig_id}/media_publish', {'creation_id': container}, 'POST')['id']
    record.update(status='published', media_id=media, published_at=dt.datetime.now(guard.IST).isoformat())
    persist(state)
    print(f'Published {key} as {media}')
    return media


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reel', required=True, choices=sorted(CAPTIONS))
    ap.add_argument('--url', required=True)
    ap.add_argument('--key', help='journal id (the calendar slot id); default SS-<date>-<reel>')
    ap.add_argument('--episode', type=int, default=1)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    publish(a.reel, a.url, dry_run=a.dry_run, key=a.key, episode=a.episode)


if __name__ == '__main__':
    main()
