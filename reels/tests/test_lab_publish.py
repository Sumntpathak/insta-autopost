"""Posting plan guard and the Lab publisher's journal-before-publish contract."""
import datetime as dt
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'reels'))
import guard  # noqa: E402

spec = importlib.util.spec_from_file_location('lab_publish', ROOT / 'reels/shipstack/publish.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)

NOW = dt.datetime(2026, 11, 20, 18, 0, tzinfo=guard.IST)


def post(minutes_ago, field='published_at'):
    return {field: (NOW - dt.timedelta(minutes=minutes_ago)).isoformat()}


class GuardTests(unittest.TestCase):
    def test_gap_and_daily_cap(self):
        self.assertIsNone(guard.blocked({}, NOW))
        self.assertIn('min ago', guard.blocked({'a': post(30)}, NOW))
        self.assertIn('min ago', guard.blocked({'a': post(30, 'attempted_at')}, NOW))   # uncertain attempts count
        self.assertIsNone(guard.blocked({'a': post(guard.MIN_GAP_MINUTES + 1)}, NOW))
        busy = {str(i): {'published_at': (NOW.replace(hour=0, minute=5) + dt.timedelta(minutes=61 * i)).isoformat()}
                for i in range(guard.DAILY_CAP)}
        self.assertIn('daily cap', guard.blocked(busy, NOW))
        yesterday = {str(i): post(24 * 60 + i) for i in range(10)}
        self.assertIsNone(guard.blocked(yesterday, NOW))


class FakeMeta:
    ig_id = '1'

    def __init__(self, events):
        self.events = events

    def check_account(self):
        self.events.append('check')

    def ready(self, container):
        self.events.append('ready')

    def call(self, path, data=None, method='GET'):
        self.events.append('publish' if 'media_publish' in path else 'create')
        return {'id': 'media-1' if 'media_publish' in path else 'box-1'}


class LabPublishTests(unittest.TestCase):
    def test_journal_precedes_publish(self):
        events, state = [], {'posts': {}}
        def persist(s):
            events.append(f"persist:{s['posts']['SS-2026-11-20-lab01']['status']}")
        lab.publish('lab01', 'https://x/y.mp4', NOW, FakeMeta(events), lambda: state, persist)
        self.assertEqual(events, ['check', 'create', 'ready', 'persist:publishing', 'publish', 'persist:published'])
        self.assertEqual(state['posts']['SS-2026-11-20-lab01']['media_id'], 'media-1')

    def test_guard_and_duplicate_block_before_any_api_call(self):
        events = []
        busy = {'posts': {'x': post(10)}}
        with self.assertRaises(RuntimeError):
            lab.publish('lab01', 'https://x/y.mp4', NOW, FakeMeta(events), lambda: busy, lambda s: None)
        dup = {'posts': {'SS-2026-11-20-lab01': {'status': 'publishing'}}}
        with self.assertRaises(RuntimeError):
            lab.publish('lab01', 'https://x/y.mp4', NOW, FakeMeta(events), lambda: dup, lambda s: None)
        self.assertEqual(events, [])

    def test_dry_run_makes_no_calls(self):
        events = []
        self.assertIsNone(lab.publish('lab02', 'https://x/y.mp4', NOW, FakeMeta(events), lambda: {'posts': {}},
                                      lambda s: None, dry_run=True))
        self.assertEqual(events, [])


if __name__ == '__main__':
    unittest.main()
