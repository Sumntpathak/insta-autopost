"""Launch publisher: stories don't count toward the feed plan, the daily-cap override never lifts the
60-min gap, the live account check blocks, the journal is pushed before media_publish, no repeats,
and unverified posts can't go out."""
import datetime as dt
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'reels'))
import guard  # noqa: E402

spec = importlib.util.spec_from_file_location('announce', ROOT / 'reels/shipstack/announce.py')
announce = importlib.util.module_from_spec(spec)
spec.loader.exec_module(announce)
NOW = dt.datetime(2026, 11, 20, 17, 30, tzinfo=guard.IST)
POSTS = {'logo': {'key': 'L-logo', 'story_key': 'L-story', 'type': 'REELS', 'file': 'a.mp4', 'story_file': 'a.mp4',
                  'ready': True, 'caption': 'c'},
         'news': {'key': 'L-news', 'type': 'IMAGE', 'file': 'n.jpg', 'ready': False, 'caption': ''}}


class FakeMeta:
    ig_id = '1'

    def __init__(self, events, live=()):
        self.events, self.live, self.n = events, list(live), 0

    def check_account(self):
        pass

    def ready(self, container):
        pass

    def call(self, path, data=None, method='GET'):
        if method == 'GET':
            return {'data': [{'timestamp': t.strftime('%Y-%m-%dT%H:%M:%S%z')} for t in self.live]}
        self.n += 1
        if 'media_publish' in path:
            self.events.append('publish')
        return {'id': f'id{self.n}'}


def day_of_posts(n, last_minutes_ago):
    return [NOW - dt.timedelta(minutes=last_minutes_ago + 61 * i) for i in range(n)]


class AnnounceTests(unittest.TestCase):
    def test_story_does_not_count_toward_feed_plan(self):
        story = {'s': {'kind': 'story', 'published_at': (NOW - dt.timedelta(minutes=5)).isoformat()}}
        self.assertIsNone(guard.blocked(story, NOW))

    def test_journal_precedes_publish_and_no_repeat(self):
        events, state = [], {'posts': {}}
        def persist(s):
            events.append('persist:' + ','.join(f"{k}={v['status']}" for k, v in sorted(s['posts'].items())))
        announce.publish_post('logo', 'https://x/', NOW, FakeMeta(events), lambda: state, persist, posts=POSTS)
        first = events.index('publish')
        self.assertIn('L-logo=publishing', events[first - 1])
        self.assertEqual(events.count('publish'), 2)                    # feed reel + story
        with self.assertRaises(RuntimeError):
            announce.publish_post('logo', 'https://x/', NOW, FakeMeta([]), lambda: state, persist, posts=POSTS)

    def test_override_lifts_cap_but_not_gap(self):
        busy_day = day_of_posts(20, 120)                                 # 20 posts today, last 2 h ago
        with self.assertRaises(RuntimeError):                            # cap applies by default
            announce.publish_post('logo', 'https://x/', NOW, FakeMeta([], busy_day), lambda: {'posts': {}},
                                  lambda s: None, posts=POSTS)
        state = {'posts': {}}
        announce.publish_post('logo', 'https://x/', NOW, FakeMeta([], busy_day), lambda: state, lambda s: None,
                              override_daily_cap=True, posts=POSTS)
        self.assertIn('plan_override', state['posts']['L-logo'])
        recent = day_of_posts(3, 20)                                     # last post 20 min ago
        with self.assertRaises(RuntimeError):
            announce.publish_post('logo', 'https://x/', NOW, FakeMeta([], recent), lambda: {'posts': {}},
                                  lambda s: None, override_daily_cap=True, posts=POSTS)

    def test_unverified_post_cannot_go_out(self):
        with self.assertRaises(RuntimeError):
            announce.publish_post('news', 'https://x/', NOW, FakeMeta([]), lambda: {'posts': {}}, lambda s: None,
                                  posts=POSTS)


if __name__ == '__main__':
    unittest.main()
