"""Automation reels: data fits the layout, captions and collections are wired, today's calendar slots are guarded-publishable."""
import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from reels.shipstack import __main__ as M, publish  # noqa: E402

DATA = json.loads((ROOT / 'film' / 'src' / 'automations.json').read_text(encoding='utf-8'))


class AutomationTests(unittest.TestCase):
    def test_data_fits_layout(self):
        self.assertGreaterEqual(len(DATA), 4)
        for i, a in enumerate(DATA, 1):
            self.assertEqual(a['id'], i)
            self.assertIn(a['accentWord'], a['hook'])
            self.assertEqual(len(a['steps']), 4)
            self.assertTrue(all(len(s['text']) <= 28 for s in a['steps']))
            self.assertLessEqual(len(a['trigger']), 28)
            self.assertLessEqual(len(a['resultFrom']), 15)
            self.assertLess(len(a['caption']), 2200)
            self.assertIn('@shipstack_', a['caption'])

    def test_wired_into_pipeline(self):
        self.assertIn('automation', M.FORMATS)
        self.assertEqual(publish.COLLECTION['automation'], 'shipstack-automation')
        for i, a in enumerate(DATA, 1):
            self.assertEqual(publish.caption('automation', i), a['caption'])

    def test_calendar_slots_use_known_episodes(self):
        cal = json.loads((ROOT / 'reels' / 'shipstack' / 'calendar.json').read_text())
        slots = [s for s in cal['slots'] if s['format'] == 'automation']
        self.assertGreaterEqual(len(slots), 4)
        for s in slots:
            self.assertLessEqual(s['episode'], len(DATA))
            self.assertIn(s['id'], {f"CAL-{s['date']}-{s['time'].replace(':', '')}-automation"})
        times = sorted(s['time'] for s in slots if s['date'] == '2026-11-21')
        mins = [int(t[:2]) * 60 + int(t[3:]) for t in times]
        self.assertTrue(all(b - a >= 60 for a, b in zip(mins, mins[1:])))


if __name__ == '__main__':
    unittest.main()
