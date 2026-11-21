"""Studio: DSA episodes trace real code correctly and fit the template; captions exist."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from reels.shipstack.studio import dsa  # noqa: E402
from reels.shipstack.studio.problems import PROBLEMS  # noqa: E402

spec = importlib.util.spec_from_file_location('ss_publish', ROOT / 'reels/shipstack/publish.py')
publish = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish)

EXPECTED = {1: [2, 3], 2: 5, 3: 5}


class StudioTests(unittest.TestCase):
    def test_episodes_trace_real_results(self):
        for ep, spec_ in PROBLEMS.items():
            code, events, result = dsa.trace(spec_)
            self.assertEqual(result, spec_['fn'](**spec_['args']))
            if ep in EXPECTED:
                self.assertEqual(result, EXPECTED[ep])
            self.assertEqual(events[-1].get('result'), result)            # the video ends on the real answer
            self.assertTrue(all(0 <= e['line'] < len(code) for e in events))

    def test_episodes_fit_the_template(self):
        for ep, spec_ in PROBLEMS.items():
            code, events, _ = dsa.trace(spec_)
            self.assertLessEqual(len(code), 12, f'#{ep}: code too long for the panel')
            self.assertLessEqual(max(len(l) for l in code), 46, f'#{ep}: a code line is too wide')
            self.assertLessEqual(len(events), 40, f'#{ep}: too many steps for 15 s')
            self.assertLessEqual(len(spec_['args'][spec_['array']]), 8)
            stripped = {l.strip() for l in code}
            for line in spec_['notes']:
                self.assertIn(line, stripped, f'#{ep}: note for a line that is not in the code')

    def test_frame_size_and_caption(self):
        reel = dsa.Reel(1)
        sched, per = reel.schedule()
        self.assertEqual(reel.frame(dsa.INTRO + 5, sched, per).size, (1080, 1920))
        self.assertIn('Two Sum', publish.caption('dsa', 1))
        self.assertEqual(publish.COLLECTION['dsa'], 'shipstack-dsa')


class CoverTests(unittest.TestCase):
    def test_every_reel_format_has_a_cover_frame(self):
        for reel in publish.CAPTIONS:
            self.assertIn(reel, publish.THUMB_MS, f'{reel} needs a cover frame (thumb_offset)')
            self.assertGreater(publish.THUMB_MS[reel], 0)                 # never the black first frame


if __name__ == '__main__':
    unittest.main()


class AllEpisodesRender(unittest.TestCase):
    def test_every_episode_draws_frames(self):
        for ep in PROBLEMS:
            reel = dsa.Reel(ep)
            sched, per = reel.schedule()
            for f in (dsa.INTRO + 5, dsa.FRAMES // 2, dsa.FRAMES - 5):
                self.assertEqual(reel.frame(f, sched, per).size, (1080, 1920), f'#{ep} frame {f}')
            self.assertIn(PROBLEMS[ep]['title'], publish.caption('dsa', ep))
