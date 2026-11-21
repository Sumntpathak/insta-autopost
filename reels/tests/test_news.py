"""News reels: feed parsing (RSS + Atom), pick rules, caption credit. Offline: no network."""
import datetime as dt
import json
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from reels.shipstack import news_feed as N, publish  # noqa: E402

RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Chip maker unveils new AI accelerator</title><link>https://example.com/a</link>
<description>&lt;p&gt;The company said on Oct. 31 that it will ship in 2027. More follows.&lt;/p&gt; The post appeared first on Example.</description>
<pubDate>Sat, 21 Nov 2026 06:00:00 GMT</pubDate></item>
<item><title>APOD: 2026 November 21 - Something</title><link>https://example.com/apod</link><description>x</description><pubDate>Sat, 21 Nov 2026 06:00:00 GMT</pubDate></item>
<item><title>Old story from last week that should be skipped</title><link>https://example.com/old</link><description>old</description><pubDate>Sat, 14 Nov 2026 06:00:00 GMT</pubDate></item>
<item><title>Insecure link</title><link>http://example.com/http</link><description>x</description><pubDate>Sat, 21 Nov 2026 06:00:00 GMT</pubDate></item>
</channel></rss>"""
ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Atom headline works too</title>
<link href="https://example.org/b"/><summary>Short summary here.</summary><published>2026-11-21T05:00:00+00:00</published></entry></feed>"""
NOW = dt.datetime(2026, 11, 21, 12, 0, tzinfo=dt.timezone.utc)


class NewsTests(unittest.TestCase):
    def test_parse_rss_and_atom(self):
        rss = N.parse(RSS, 'Ex')
        self.assertEqual(rss[0]['summary'], 'The company said on Oct. 31 that it will ship in 2027.')    # no split at "Oct."
        self.assertEqual(len(rss), 3)                                                                     # http:// link dropped
        atom = N.parse(ATOM, 'At')
        self.assertEqual((atom[0]['url'], atom[0]['summary']), ('https://example.org/b', 'Short summary here.'))

    def test_pick_skips_old_used_and_apod(self):
        items = {'Ex': N.parse(RSS, 'Ex'), 'At': N.parse(ATOM, 'At')}
        got = N.pick(1, {'BBC News': items['Ex']}, set(), NOW)
        self.assertEqual(got['url'], 'https://example.com/a')
        self.assertIsNone(N.pick(1, {'BBC News': items['Ex']}, {'https://example.com/a'}, NOW))        # already posted
        self.assertIsNone(N.pick(1, {'BBC News': items['Ex']}, set(), NOW + dt.timedelta(days=5)))     # everything too old

    def test_rotation_prefers_the_episode_outlet(self):
        a = dict(source='BBC News', headline='First outlet headline here', summary='', url='https://a.com/1', published='2026-11-21T10:00:00+00:00')
        b = dict(source='Ars Technica', headline='Second outlet headline here', summary='', url='https://b.com/1', published='2026-11-21T09:00:00+00:00')
        self.assertEqual(N.pick(1, {'BBC News': [a], 'Ars Technica': [b]}, set(), NOW)['source'], 'BBC News')
        self.assertEqual(N.pick(2, {'BBC News': [a], 'Ars Technica': [b]}, set(), NOW)['source'], 'Ars Technica')

    def test_caption_credits_the_source(self):
        item = dict(source='BBC News', headline='H', summary='S.', url='https://www.bbc.co.uk/x', domain='bbc.co.uk', date='21 NOV 2026')
        cap = N.caption(item)
        self.assertIn('Source: BBC News (bbc.co.uk)', cap)
        self.assertIn('https://www.bbc.co.uk/x', cap)
        self.assertEqual(publish.COLLECTION['news'], 'shipstack-news')

    def test_used_urls_come_from_the_journal(self):
        tmp = Path(__file__).with_name('_state_tmp.json')
        tmp.write_text(json.dumps({'posts': {'k': {'news_url': 'https://x.com/1'}, 'j': {}}}))
        try:
            self.assertEqual(N.used_urls(tmp), {'https://x.com/1'})
        finally:
            tmp.unlink()


if __name__ == '__main__':
    unittest.main()
