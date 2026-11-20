"""Launch publisher: stories don't count toward the feed plan, the live account check blocks,
the journal is pushed before media_publish, and nothing is posted twice."""
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
NOW = dt.datetime(2026, 11, 21, 9, 0, tzinfo=guard.IST)


class FakeMeta:
    ig_id = '1'

    def __init__(self, events, live=()):
        self.events, self.live, self.n = events, list(live), 0

    def check_account(self):
        self.events.append('check')

    def ready(self, container):
        pass

    def call(self, path, data=None, method='GET'):
        if method == 'GET':
            return {'data': [{'timestamp': t.strftime('%Y-%m-%dT%H:%M:%S%z')} for t in self.live]}
        self.n += 1
        if 'media_publish' in path:
            self.events.append('publish')
        elif data.get('media_type') == 'CAROUSEL':
            self.events.append('carousel-container')
        return {'id': f'id{self.n}'}


class AnnounceTests(unittest.TestCase):
    def test_story_does_not_count_toward_feed_plan(self):
        story = {'s': {'kind': 'story', 'published_at': (NOW - dt.timedelta(minutes=5)).isoformat()}}
        self.assertIsNone(guard.blocked(story, NOW))

    def test_journal_precedes_publish_and_no_repeat(self):
        events, state = [], {'posts': {}}
        def persist(s):
            events.append('persist:' + ','.join(f"{k}={v['status']}" for k, v in sorted(s['posts'].items())))
        announce.publish_launch('https://x/', NOW, FakeMeta(events), lambda: state, persist)
        i_pub = events.index('publish')
        self.assertIn(f'{announce.CAROUSEL_KEY}=publishing', events[i_pub - 1])
        self.assertEqual(events.count('publish'), 2)                          # carousel + story
        self.assertEqual(state['posts'][announce.STORY_KEY]['kind'], 'story')
        with self.assertRaises(RuntimeError):
            announce.publish_launch('https://x/', NOW, FakeMeta([]), lambda: state, persist)

    def test_live_account_check_blocks(self):
        busy = [NOW - dt.timedelta(minutes=20)]                              # someone posted 20 min ago
        with self.assertRaises(RuntimeError):
            announce.publish_launch('https://x/', NOW, FakeMeta([], busy), lambda: {'posts': {}}, lambda s: None)


if __name__ == '__main__':
    unittest.main()
