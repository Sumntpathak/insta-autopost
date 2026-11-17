"""The race result shown in the reel must be the real physics result."""
import importlib.util
import math
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('track_race', Path(__file__).parents[1] / 'experiments' / 'track_race.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)


class TrackRaceTests(unittest.TestCase):
    def test_simulation_matches_closed_form_times(self):
        paths, runs, totals, winner, slow = t.physics()
        dx, dy = (t.END[0] - t.START[0]) / t.PX_PER_M, (t.END[1] - t.START[1]) / t.PX_PER_M
        self.assertAlmostEqual(totals[0], math.hypot(dx, dy) * math.sqrt(2 / (t.G * dy)), places=4)
        c = paths[1]
        self.assertTrue(math.isclose(c[-1][0], t.END[0], abs_tol=0.5) and math.isclose(c[-1][1], t.END[1], abs_tol=0.5))
        self.assertGreater(c[:, 1].max(), t.END[1])  # brachistochrone dips below the finish here
        self.assertEqual(winner, 1)

    def test_lanes_share_drop_and_end_speed(self):
        paths, runs, *_ = t.physics()
        drops = [p[-1][1] - p[0][1] for p in paths]
        self.assertAlmostEqual(drops[0], drops[1])
        self.assertAlmostEqual(runs[0][1][-1], runs[1][1][-1], places=6)

    def test_one_slow_motion_factor_for_both(self):
        paths, runs, totals, winner, slow = t.physics()
        self.assertAlmostEqual(totals[1 - winner] * slow, t.RACE_SPAN)
        _, _, done = t.state_at(t.RACE_START + totals[winner] * slow + 1e-6, paths[winner], runs[winner], slow)
        _, _, loser_done = t.state_at(t.RACE_START + totals[winner] * slow + 1e-6, paths[1 - winner], runs[1 - winner], slow)
        self.assertTrue(done and not loser_done)


if __name__ == '__main__':
    unittest.main()
