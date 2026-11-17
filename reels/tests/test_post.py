"""Double-post protection in the carousel publisher (post.py)."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import datetime as dt

os.environ.setdefault('META_TOKEN', 'EAAtest-token')
os.environ.setdefault('IG_USER_ID', '1')
os.environ.setdefault('GITHUB_REPOSITORY', 'o/r')
spec = importlib.util.spec_from_file_location('post', Path(__file__).parents[2] / 'post.py')
post = importlib.util.module_from_spec(spec)
spec.loader.exec_module(post)

ITEM = {'id': 'S001', 'caption': 'c', 'slot': 'morning', 'date': '2026-11-01', 'images': ['a.jpg']}
NOW = dt.datetime(2026, 11, 2, 9, tzinfo=post.IST)


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.saved = []
        patcher = patch.object(post, 'save_posted', lambda p: self.saved.append([dict(r) for r in p]))
        patcher.start(); self.addCleanup(patcher.stop)
        patcher = patch.object(post, 'prepare_instagram', return_value='box-1')
        patcher.start(); self.addCleanup(patcher.stop)

    def test_container_is_journalled_before_media_publish(self):
        def call(path, data=None, method='POST'):
            self.assertEqual(self.saved[-1][-1]['status'], 'publishing')
            self.assertEqual(self.saved[-1][-1]['container_id'], 'box-1')
            return {'id': 'media-1'}
        posted = []
        with patch.object(post, 'call', side_effect=call):
            rec = post.publish(ITEM, ['u'], posted, NOW)
        self.assertEqual((rec['status'], rec['instagram']), ('published', 'media-1'))
        self.assertEqual(self.saved[-1][-1]['status'], 'published')

    def test_ambiguous_timeout_keeps_record_so_next_run_skips_it(self):
        posted = []
        with patch.object(post, 'call', side_effect=TimeoutError()), self.assertRaises(SystemExit):
            post.publish(ITEM, ['u'], posted, NOW)
        self.assertEqual(posted[0]['status'], 'publishing')

    def test_definite_rejection_removes_record_so_it_retries(self):
        posted = []
        with patch.object(post, 'call', side_effect=post.APIError('HTTP 400')), self.assertRaises(SystemExit):
            post.publish(ITEM, ['u'], posted, NOW)
        self.assertEqual(posted, [])

    def test_token_never_in_url_or_error(self):
        seen = {}
        class Err(post.urllib.error.HTTPError):
            def __init__(self): super().__init__('u', 400, 'bad', {}, None)
            def read(self): return b'{"error":{"message":"bad token EAAtest-token","code":190}}'
        def urlopen(req, timeout):
            seen['url'] = req.full_url; seen['auth'] = req.get_header('Authorization'); raise Err()
        with patch.object(post.urllib.request, 'urlopen', urlopen), self.assertRaises(post.APIError) as ctx:
            post.call('me', {'fields': 'username'}, 'GET')
        self.assertNotIn(post.TOKEN, seen['url'])
        self.assertEqual(seen['auth'], f'Bearer {post.TOKEN}')
        self.assertNotIn(post.TOKEN, str(ctx.exception))
        self.assertIn('190', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
