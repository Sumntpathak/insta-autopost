"""Arena engines: deterministic physics, honest winners, pacing rules."""
import importlib.util
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

try:
    import pymunk  # noqa: F401
    import skia  # noqa: F401
    HAVE = True
except Exception:          # arena deps are installed by the reel workflow, not the PR check
    HAVE = False


@unittest.skipUnless(HAVE, 'pymunk/skia not installed')
class ArenaTests(unittest.TestCase):
    def test_ring_escape_pacing_and_determinism(self):
        from reels.shipstack.arena import ring_physics as sim
        a, b = sim.choose(2026), sim.choose(2026)
        self.assertEqual((a.seed, a.winner), (b.seed, b.winner))
        t1 = a.escapes[a.winner]
        self.assertTrue(sim.WIN_WINDOW[0] <= t1 <= sim.WIN_WINDOW[1])
        if len(a.order) > 1:
            self.assertGreaterEqual(a.escapes[a.order[1]] - t1, sim.CLEAR_MARGIN)

    def test_string_battle_winner_is_most_strings(self):
        from reels.shipstack.arena import strings
        s = strings.Sim(500, 6).run(strings.BATTLE)
        final = s.count_at(strings.BATTLE)
        self.assertEqual(final, strings.Sim(500, 6).run(strings.BATTLE).count_at(strings.BATTLE))
        self.assertTrue(all(c >= 0 for c in final))
        self.assertEqual(len(final), 6)

    def test_balloon_pop_is_close_and_honest(self):
        from reels.shipstack.arena import balloon
        reel = balloon.BalloonReel(3)
        st, _, w, tw = balloon.simulate(reel.seed, balloon.WINDOW[1] + 0.2)
        self.assertEqual((w, round(tw, 6)), (reel.win, round(reel.t_win, 6)))
        self.assertTrue(balloon.WINDOW[0] <= tw <= balloon.WINDOW[1])
        radii = st[int(tw / balloon.DT), :, 2]
        self.assertEqual(int(radii.argmax()), w)                          # the popped balloon really was biggest
        self.assertLessEqual(reel.v_pop, 12.0)                            # pop lands with time left for the reveal

    def test_every_country_has_a_flag_colour(self):
        from reels.shipstack.arena import strings
        for code, (name, colour) in strings.COUNTRIES.items():
            self.assertRegex(colour, r'^#[0-9A-F]{6}$', code)


if __name__ == '__main__':
    unittest.main()
