import datetime as dt
import importlib.util
import tempfile
import unittest
from pathlib import Path

path = Path(__file__).parents[2] / 'facebook-drive' / 'publish.py'
spec = importlib.util.spec_from_file_location('facebook_drive_publish', path)
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)

IST = d.guard.IST
NOW = dt.datetime(2026, 11, 22, 15, 0, tzinfo=IST)
HASH = 'a' * 64


class FakeFacebook:
    def __init__(self, events, fail=False):
        self.events, self.fail = events, fail

    def upload(self, _):
        self.events.append('upload')
        return '999'

    def finish(self, video, caption):
        self.events.append('finish')
        if self.fail:
            raise RuntimeError('Facebook publication unconfirmed')


class DriveTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.queue = {'items': [
            {'id': 'A', 'drive_id': 'x', 'sha256': HASH, 'caption': 'one'},
            {'id': 'B', 'drive_id': 'y', 'sha256': 'b' * 64, 'caption': 'two'}]}
        self.state = {'posts': {}}

    def run_once(self, fb=None, now=NOW, publish=True, fetch=None, queue=None):
        return d.publish_next(
            queue or self.queue, self.state, fb or FakeFacebook(self.events), now, publish=publish,
            persist=lambda s: self.events.append('persist:' + ','.join(p['status'] for p in s['posts'].values())),
            fetch=fetch or (lambda item, dest: item['sha256']),
            probe=lambda _: {'seconds': 14.0, 'width': 720, 'height': 1280}, workdir=self.tmp.name,
            clock=lambda: now)

    def test_journal_is_saved_before_publish(self):
        self.run_once()
        self.assertEqual(self.events, ['upload', 'persist:publishing', 'finish', 'persist:published'])
        self.assertEqual(self.state['posts']['A']['video_id'], '999')

    def test_dry_run_posts_and_journals_nothing(self):
        self.assertIn('dry run ok', self.run_once(publish=False))
        self.assertEqual(self.events, [])
        self.assertEqual(self.state['posts'], {})

    def test_uncertain_result_is_never_retried(self):
        with self.assertRaises(RuntimeError):
            self.run_once(fb=FakeFacebook(self.events, fail=True))
        self.assertEqual(self.state['posts']['A']['status'], 'publishing')
        self.events.clear()
        with self.assertRaisesRegex(d.Blocked, 'reconcile'):
            self.run_once(now=NOW + dt.timedelta(hours=5))
        self.assertEqual(self.events, [])

    def test_sixty_minute_gap_is_enforced(self):
        self.run_once()
        self.events.clear()
        self.assertIn('waiting', self.run_once(now=NOW + dt.timedelta(minutes=30)))
        self.assertEqual(self.events, [])
        self.assertIn('published B', self.run_once(now=NOW + dt.timedelta(minutes=61)))

    def test_identical_video_is_blocked(self):
        self.state['posts']['old'] = {'status': 'published', 'content_sha256': HASH,
                                      'published_at': (NOW - dt.timedelta(days=1)).isoformat()}
        with self.assertRaisesRegex(d.Blocked, 'identical'):
            self.run_once()
        self.assertEqual(self.events, [])

    def test_hash_mismatch_never_uploads(self):
        def tampered(item, dest):
            raise d.Blocked('does not match the reviewed hash')
        with self.assertRaises(d.Blocked):
            self.run_once(fetch=tampered)
        self.assertEqual(self.events, [])

    def test_skipped_items_are_not_posted(self):
        self.queue['items'][0]['skip_reason'] = 'too long'
        self.run_once()
        self.assertIn('B', self.state['posts'])
        self.assertNotIn('A', self.state['posts'])

    def test_real_queue_hashes_are_well_formed(self):
        import json
        queue = json.loads(d.QUEUE.read_text())
        ids = [i['id'] for i in queue['items']]
        self.assertEqual(len(ids), len(set(ids)))
        for item in queue['items']:
            self.assertEqual(len(item['sha256']), 64)
            self.assertTrue(item.get('skip_reason') or item['caption'])


if __name__ == '__main__':
    unittest.main()
