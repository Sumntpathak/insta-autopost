"""Publish the ShipStack launch: one carousel (logo animation + the three series) and one Story.

    python -m reels.shipstack.announce --base-url https://.../ [--dry-run] [--story-only]

Same safety contract as publish.py:
  1. reels/guard.py must allow posting now (60 min gap, 12/day). Stories are journaled with
     kind 'story' and do not count toward the feed plan (they never appear in the feed).
  2. Every container is created and processed first; a 'publishing' record with the container id
     is pushed to reels/state.json BEFORE media_publish, so an ambiguous failure is never retried.
  3. A key that is already in the journal is never posted again.
Assets live in reels/shipstack/launch/ and are hosted by the workflow as release assets.
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'reels'))
import campaign  # noqa: E402
import guard  # noqa: E402

SLIDES = [('slide1-logo.mp4', 'VIDEO'), ('slide2-news.jpg', 'IMAGE'), ('slide3-automation.jpg', 'IMAGE'),
          ('slide4-dsa.jpg', 'IMAGE')]
STORY = 'story-logo.mp4'
CAROUSEL_KEY = 'LAUNCH-2026-carousel'
STORY_KEY = 'LAUNCH-2026-story'
CAPTION = (
    'We ship. 🚢\n\n'
    'ShipStack is starting fresh. From today we post three things:\n\n'
    '📰 AI news: verified, with every source shown\n'
    '⚙️ AI automations: workflows you can copy in minutes\n'
    '💻 DSA: famous coding problems, debugged line by line (episode #0001 is next)\n\n'
    'Swipe for a preview of each series. Follow so you don\'t miss #0001.\n\n'
    '#ai #automation #dsa #coding #leetcode #programming #tech'
)


def live_blocked(meta, now):
    """The journal only knows this repo's posts; ask Instagram what actually went out today."""
    data = meta.call(f'{meta.ig_id}/media', {'fields': 'timestamp', 'limit': 50}).get('data', [])
    posts = {str(i): {'published_at': dt.datetime.strptime(m['timestamp'], '%Y-%m-%dT%H:%M:%S%z').isoformat()}
             for i, m in enumerate(data) if m.get('timestamp')}
    return guard.blocked(posts, now)


def publish_launch(base_url, now=None, meta=None, read_state=campaign.read_state, persist=campaign.persist,
                   dry_run=False, story_only=False):
    if not base_url.startswith('https://'):
        raise ValueError('A public HTTPS base URL is required')
    base_url = base_url.rstrip('/') + '/'
    now = now or dt.datetime.now(guard.IST)
    state = read_state()
    todo_carousel = not story_only and CAROUSEL_KEY not in state['posts']
    todo_story = STORY_KEY not in state['posts']
    if not todo_carousel and not todo_story:
        raise RuntimeError('The launch was already attempted; reconcile it instead of re-posting')
    if todo_carousel:
        reason = guard.blocked(state['posts'], now)
        if reason:
            raise RuntimeError(f'Posting plan blocks the launch carousel: {reason}')
    if dry_run:
        print(f'Dry run OK: carousel={"yes" if todo_carousel else "no"}, story={"yes" if todo_story else "no"}')
        return None
    meta = meta or campaign.Meta()
    meta.check_account()
    if todo_carousel:
        reason = live_blocked(meta, now)
        if reason:
            raise RuntimeError(f'Posting plan blocks the launch carousel (live account check): {reason}')
    results = {}
    if todo_carousel:
        children = []
        for name, kind in SLIDES:
            params = {'is_carousel_item': 'true'}
            if kind == 'VIDEO':
                params.update(media_type='VIDEO', video_url=base_url + name)
            else:
                params.update(image_url=base_url + name)
            child = meta.call(f'{meta.ig_id}/media', params, 'POST')['id']
            meta.ready(child)
            children.append(child)
        container = meta.call(f'{meta.ig_id}/media', {'media_type': 'CAROUSEL', 'children': ','.join(children),
                                                       'caption': CAPTION}, 'POST')['id']
        meta.ready(container)
        record = {'id': CAROUSEL_KEY, 'date': now.date().isoformat(), 'scene': 'launch', 'collection': 'shipstack-brand',
                  'kind': 'carousel', 'caption': CAPTION, 'container_id': container, 'children': children,
                  'status': 'publishing', 'attempted_at': now.isoformat()}
        state['posts'][CAROUSEL_KEY] = record
        persist(state)
        media = meta.call(f'{meta.ig_id}/media_publish', {'creation_id': container}, 'POST')['id']
        record.update(status='published', media_id=media, published_at=dt.datetime.now(guard.IST).isoformat())
        persist(state)
        results['carousel'] = media
        print(f'Published launch carousel as {media}')
    if todo_story:
        container = meta.call(f'{meta.ig_id}/media', {'media_type': 'STORIES', 'video_url': base_url + STORY}, 'POST')['id']
        meta.ready(container)
        record = {'id': STORY_KEY, 'date': now.date().isoformat(), 'scene': 'launch', 'collection': 'shipstack-brand',
                  'kind': 'story', 'container_id': container, 'status': 'publishing', 'attempted_at': now.isoformat()}
        state['posts'][STORY_KEY] = record
        persist(state)
        media = meta.call(f'{meta.ig_id}/media_publish', {'creation_id': container}, 'POST')['id']
        record.update(status='published', media_id=media, published_at=dt.datetime.now(guard.IST).isoformat())
        persist(state)
        results['story'] = media
        print(f'Published launch story as {media}')
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base-url', required=True, help='public HTTPS folder that holds the files in reels/shipstack/launch/')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--story-only', action='store_true')
    a = ap.parse_args()
    publish_launch(a.base_url, dry_run=a.dry_run, story_only=a.story_only)


if __name__ == '__main__':
    main()
