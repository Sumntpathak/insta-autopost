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
        self.assertEqual(len(slots), 180)
        self.assertEqual(len({s['id'] for s in slots}), 180)
        self.assertEqual(len({(s['format'], s['episode']) for s in slots}), 180)        # no repeated race/setup
        per = {f: sum(1 for s in slots if s['format'] == f) for f in ('balloon', 'strings', 'ring', 'lab01', 'lab02')}
        self.assertEqual(per, {'balloon': 60, 'strings': 60, 'ring': 30, 'lab01': 15, 'lab02': 15})

    def test_due_rules(self):
        at = lambda d, hm: dt.datetime.fromisoformat(f'{d}T{hm}:00').replace(tzinfo=S.IST)
        self.assertIsNone(S.due(self.cal, {}, at('2026-11-19', '08:00')))
        first = S.due(self.cal, {}, at('2026-11-19', '08:20'))
        self.assertEqual(first['format'], 'lab01')
        self.assertNotEqual(S.due(self.cal, {first['id']: {}}, at('2026-11-19', '10:45'))['id'], first['id'])
        self.assertIsNone(S.due(self.cal, {}, at('2026-11-19', '10:30')))              # 08:10 slot is stale (>2 h)
        self.assertIsNone(S.due(dict(self.cal, paused=True), {}, at('2026-11-19', '08:20')))

    def test_daily_slots_respect_the_guard_gap(self):
        from reels import guard
        times = [dt.datetime.strptime(t, '%H:%M') for t, _ in S.DAY]
        gaps = [(b - a).total_seconds() / 60 for a, b in zip(times, times[1:])]
        self.assertGreaterEqual(min(gaps), guard.MIN_GAP_MINUTES)
        self.assertLessEqual(len(S.DAY), guard.DAILY_CAP)


if __name__ == '__main__':
    unittest.main()
