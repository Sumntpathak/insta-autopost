"""Publish one ShipStack launch post (and, with the logo post, the launch Story).

    python -m reels.shipstack.announce --post logo|news|dsa --base-url https://.../ [--override-daily-cap] [--dry-run]

The launch is three separate feed posts that fill the profile's top row, posted at least 60 min apart:
  logo  - the logo animation as a Reel with the announcement caption, plus the same clip as a Story
  news  - the first verified news card (only if launch/posts.json marks it verified)
  dsa   - DSA #0001 Two Sum, the debugger reel
Safety (same contract as publish.py):
  1. reels/guard.py must allow posting now, checked against the journal AND the live account (posts
     made by other pipelines). --override-daily-cap lifts only the 12/day cap, never the 60-min gap,
     and is recorded in the journal. Stories don't count toward the feed plan.
  2. Each container is processed first; a 'publishing' record with its id is pushed to reels/state.json
     BEFORE media_publish, so an ambiguous failure is never retried.
  3. A key already in the journal is never posted again.
Files and captions: reels/shipstack/launch/ and launch/posts.json.
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'reels'))
import campaign  # noqa: E402
import guard  # noqa: E402

POSTS = ROOT / 'reels/shipstack/launch/posts.json'
NO_CAP = 10 ** 6


def load_posts():
    return json.loads(POSTS.read_text())


def live_posts(meta):
    """The journal only knows this repo's posts; ask Instagram what actually went out."""
    data = meta.call(f'{meta.ig_id}/media', {'fields': 'timestamp', 'limit': 50}).get('data', [])
    return {f'live{i}': {'published_at': dt.datetime.strptime(m['timestamp'], '%Y-%m-%dT%H:%M:%S%z').isoformat()}
            for i, m in enumerate(data) if m.get('timestamp')}


def _publish(meta, state, persist, key, params, record, now):
    container = meta.call(f'{meta.ig_id}/media', params, 'POST')['id']
    meta.ready(container)
    record = {'id': key, 'date': now.date().isoformat(), 'container_id': container, 'status': 'publishing',
              'attempted_at': now.isoformat(), **record}
    state['posts'][key] = record
    persist(state)
    media = meta.call(f'{meta.ig_id}/media_publish', {'creation_id': container}, 'POST')['id']
    record.update(status='published', media_id=media, published_at=dt.datetime.now(guard.IST).isoformat())
    persist(state)
    print(f'Published {key} as {media}')
    return media


def publish_post(post, base_url, now=None, meta=None, read_state=campaign.read_state, persist=campaign.persist,
                 dry_run=False, override_daily_cap=False, posts=None):
    posts = posts or load_posts()
    if post not in posts:
        raise ValueError(f'Unknown launch post {post}; choose from {sorted(posts)}')
    item = posts[post]
    if not item.get('ready', False):
        raise RuntimeError(f'Launch post {post} is not ready (it needs verified content): {item.get("note", "")}')
    if not base_url.startswith('https://'):
        raise ValueError('A public HTTPS base URL is required')
    base_url = base_url.rstrip('/') + '/'
    now = now or dt.datetime.now(guard.IST)
    cap = NO_CAP if override_daily_cap else guard.DAILY_CAP
    state = read_state()
    key, story_key = item['key'], item.get('story_key')
    todo_feed = key not in state['posts']
    todo_story = bool(story_key) and story_key not in state['posts']
    if not todo_feed and not todo_story:
        raise RuntimeError(f'{key} was already attempted; reconcile it instead of re-posting')
    if todo_feed:
        reason = guard.blocked(state['posts'], now, cap=cap)
        if reason:
            raise RuntimeError(f'Posting plan blocks {key}: {reason}')
    if dry_run:
        print(f'Dry run OK: {key} feed={"yes" if todo_feed else "no"} story={"yes" if todo_story else "no"}'
              f'{" (daily cap overridden)" if override_daily_cap else ""}')
        return None
    meta = meta or campaign.Meta()
    meta.check_account()
    if todo_feed:
        reason = guard.blocked(live_posts(meta), now, cap=cap)
        if reason:
            raise RuntimeError(f'Posting plan blocks {key} (live account check): {reason}')
    extra = {'scene': f'launch-{post}', 'collection': 'shipstack-launch', 'caption': item['caption']}
    if override_daily_cap:
        extra['plan_override'] = 'daily cap lifted for the launch by the account owner; 60-min gap kept'
    results = {}
    if todo_feed:
        url = base_url + item['file']
        if item['type'] == 'REELS':
            params = {'media_type': 'REELS', 'video_url': url, 'caption': item['caption'], 'share_to_feed': 'true',
                      'thumb_offset': str(item.get('thumb_ms', 2000))}
        else:
            params = {'image_url': url, 'caption': item['caption']}
        results['feed'] = _publish(meta, state, persist, key, params, {**extra, 'kind': item['type'].lower()}, now)
    if todo_story:
        params = {'media_type': 'STORIES', 'video_url': base_url + item['story_file']}
        results['story'] = _publish(meta, state, persist, story_key, params,
                                    {'scene': f'launch-{post}', 'collection': 'shipstack-launch', 'kind': 'story'}, now)
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--post', required=True, choices=['logo', 'news', 'dsa'])
    ap.add_argument('--base-url', required=True, help='public HTTPS folder holding reels/shipstack/launch/ files')
    ap.add_argument('--override-daily-cap', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    publish_post(a.post, a.base_url, dry_run=a.dry_run, override_daily_cap=a.override_daily_cap)


if __name__ == '__main__':
    main()
