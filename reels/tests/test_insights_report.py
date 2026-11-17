import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('insights_report', Path(__file__).parents[1] / 'insights_report.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def reel(i, scene, win, published='2026-11-14T19:10:00+05:30'):
    return {'scene': scene, 'media_id': f'm{i}', 'published_at': published, 'seconds': 15,
            'source': {'seconds': 15, 'source_win_seconds': win}}


STATE = {'posts': {f'R{i}': reel(i, 'pl-balloon' if i < 4 else 'pl-ring', 6 if i < 4 else 14.5) for i in range(8)}}
INSIGHTS = {'collected_at': 'now', 'posts': [
    {'id': f'm{i}', 'metrics': {'reach': 1000, 'views': 2000, 'shares': 40 if i < 4 else 5, 'saved': 20 if i < 4 else 2,
                                'ig_reels_avg_watch_time': 12000 if i < 4 else 6000}} for i in range(8)
] + [{'id': 'carousel', 'metrics': {'reach': 9}}, {'id': 'm7x', 'metrics': {}}]}


class InsightsReportTests(unittest.TestCase):
    def test_joins_creative_metadata_and_ignores_unknown_media(self):
        rows = r.rows(INSIGHTS, STATE)
        self.assertEqual(len(rows), 8)
        self.assertAlmostEqual(rows[0]['share_rate'], 0.04)
        self.assertAlmostEqual(rows[0]['watch_ratio'], 0.8)
        self.assertEqual(rows[0]['reveal'], 'early (<60%)')
        self.assertEqual(rows[7]['reveal'], 'late (>=85%)')
        self.assertEqual(rows[0]['hour_ist'], '18-21h')

    def test_missing_metrics_are_not_zero(self):
        state = {'posts': {'R': reel(0, 'x', 5)}}
        rows = r.rows({'posts': [{'id': 'm0', 'metrics': {'reach': 100, 'saved': None}}]}, state)
        self.assertNotIn('save_rate', rows[0])
        self.assertIsNone(r.group(rows, 'scene')[0]['save_rate'])

    def test_ranking_and_recommendations_follow_evidence(self):
        text, groups = r.render(r.rows(INSIGHTS, STATE), 'now')
        self.assertEqual(groups['scene'][0]['value'], 'pl-balloon')
        self.assertIn('Make more **pl-balloon**', text)
        self.assertIn('early (<60%)', text.split('## Recommendations')[1].split('##')[0])

    def test_small_groups_flagged(self):
        rows = r.rows(INSIGHTS, {'posts': {'R0': reel(0, 'solo', 5)}})
        self.assertTrue(r.group(rows, 'scene')[0]['low_confidence'])


if __name__ == '__main__':
    unittest.main()
