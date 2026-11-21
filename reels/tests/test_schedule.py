"""Month calendar: unique slots, correct mix, due/stale/paused rules."""
import datetime as dt
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from reels.shipstack import schedule as S  # noqa: E402


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.cal = S.make(dt.date(2026, 11, 19), 30)

    def test_month_mix_and_unique_ids(self):
        slots = self.cal['slots']
        self.assertEqual(len(slots), 360)
        self.assertEqual(len({s['id'] for s in slots}), 360)
        per = {f: sum(1 for s in slots if s['format'] == f) for f in ('news', 'dsa', 'automation')}
        self.assertEqual(per, {'news': 120, 'dsa': 120, 'automation': 120})
        self.assertTrue(all(s['episode'] == 'next' for s in slots))
        self.assertEqual(sum(1 for s in slots if s['date'] == '2026-11-19'), 12)

    def test_due_rules(self):
        at = lambda d, hm: dt.datetime.fromisoformat(f'{d}T{hm}:00').replace(tzinfo=S.IST)
        self.assertIsNone(S.due(self.cal, {}, at('2026-11-19', '06:00')))
        first = S.due(self.cal, {}, at('2026-11-19', '06:40'))
        self.assertEqual(first['format'], 'news')
        self.assertNotEqual(S.due(self.cal, {first['id']: {}}, at('2026-11-19', '08:05'))['id'], first['id'])
        self.assertIsNone(S.due(dict(self.cal, paused=True), {}, at('2026-11-19', '06:40')))

    def test_stale_slot_is_skipped(self):
        at = lambda d, hm: dt.datetime.fromisoformat(f'{d}T{hm}:00').replace(tzinfo=S.IST)
        only = dict(self.cal, slots=self.cal['slots'][:1])           # the 06:30 slot alone
        self.assertIsNotNone(S.due(only, {}, at('2026-11-19', '09:20')))
        self.assertIsNone(S.due(only, {}, at('2026-11-19', '09:40')))   # > 3 h late

    def test_episode_resolution_and_fallback(self):
        posts = {'a': {'scene': 'automation', 'episode': 1, 'status': 'published'}}
        self.assertEqual(S.resolve({'format': 'automation', 'episode': 'next'}, posts), ('automation', 2))
        self.assertEqual(S.resolve({'format': 'dsa', 'episode': 'next'}, posts), ('dsa', S.FIRST_DSA))
        self.assertEqual(S.resolve({'format': 'news', 'episode': 'next'}, posts), ('news', 1))
        everything = {f'd{e}': {'scene': 'dsa', 'episode': e, 'status': 'published'} for e in S.available('dsa')}
        self.assertEqual(S.resolve({'format': 'dsa', 'episode': 'next'}, everything)[0], 'news')    # pool empty: news fills the slot
        pending = {'p': {'scene': 'automation', 'episode': 2, 'status': 'publishing'}}               # ambiguous attempts count as used
        self.assertEqual(S.resolve({'format': 'automation', 'episode': 'next'}, pending), ('automation', 1))

    def test_daily_slots_respect_the_guard_gap(self):
        from reels import guard
        times = [dt.datetime.strptime(t, '%H:%M') for t, _ in S.DAY]
        gaps = [(b - a).total_seconds() / 60 for a, b in zip(times, times[1:])]
        self.assertGreaterEqual(min(gaps), guard.MIN_GAP_MINUTES)
        self.assertLessEqual(len(S.DAY), guard.DAILY_CAP)


if __name__ == '__main__':
    unittest.main()
