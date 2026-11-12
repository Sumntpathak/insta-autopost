import datetime as dt
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('campaign', Path(__file__).parents[1] / 'campaign.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def at(day=1, hour=23, minute=0):
    return dt.datetime(2026, 12, day, hour, minute, tzinfo=c.IST)


class CampaignTests(unittest.TestCase):
    def test_inactive_before_start_and_after_day_30(self):
        state = {'start_date': '2026-12-01', 'posts': {}}
        self.assertIsNone(c.plan({'start_date': None, 'posts': {}}, at()))
        self.assertIsNone(c.plan(state, at() - dt.timedelta(days=1)))
        self.assertIsNotNone(c.plan(state, at(30)))
        self.assertIsNone(c.plan(state, at(30) + dt.timedelta(days=1)))

    def test_300_unique_slots_and_hard_daily_cap(self):
        state = {'start_date': '2026-12-01', 'posts': {}}
        ids, seeds, scenes = set(), set(), set()
        for day in range(1, 31):
            for _ in range(10):
                item = c.plan(state, at(day))
                self.assertIsNotNone(item)
                ids.add(item['id']); seeds.add(item['seed']); scenes.add(item['scene'])
                state['posts'][item['id']] = {'status': 'published'}
            self.assertIsNone(c.plan(state, at(day)))
        self.assertEqual(len(ids), 300)
        self.assertEqual(len(seeds), 300)
        self.assertEqual(len(scenes), 5)

    def test_due_times_and_no_backlog_from_previous_day(self):
        state = {'start_date': '2026-12-01', 'posts': {}}
        self.assertIsNone(c.plan(state, at(hour=6, minute=59)))
        first = c.plan(state, at(hour=7))
        self.assertEqual(first['slot'], '07:00')
        state['posts'][first['id']] = {'status': 'publishing'}
        self.assertIsNone(c.plan(state, at(hour=8)))
        self.assertEqual(c.plan(state, at(2))['date'], '2026-12-02')

    def test_uncertain_publish_is_not_selected_again(self):
        state = {'start_date': '2026-12-01', 'posts': {}}
        first = c.plan(state, at())
        state['posts'][first['id']] = {'status': 'publishing'}
        self.assertNotEqual(first['id'], c.plan(state, at())['id'])

    def test_journal_precedes_publish_and_failed_save_blocks_publish(self):
        now = dt.datetime.now(c.IST)
        state = {'start_date': now.date().isoformat(), 'posts': {}}
        item = {'id': 'test', 'caption': 'test'}
        events=[]
        class FakeMeta:
            ig_id='123'
            def check_account(self): events.append('check')
            def ready(self, container): events.append('ready')
            def call(self, path, data=None, method='GET'):
                if 'media_publish' in path: events.append('publish')
                return {'id':'123'}
        def persist(state): events.append('persist')
        with patch.object(c,'read_state',return_value=state), patch.object(c,'plan',return_value=item), patch.object(c,'Meta',FakeMeta), patch.object(c,'persist',side_effect=persist):
            c.publish(item,'https://example.org/reel.mp4')
        self.assertEqual(events,['check','ready','persist','publish','persist'])
        events.clear()
        with patch.object(c,'read_state',return_value=state), patch.object(c,'plan',return_value=item), patch.object(c,'Meta',FakeMeta), patch.object(c,'persist',side_effect=RuntimeError('git failed')):
            with self.assertRaises(RuntimeError): c.publish(item,'https://example.org/reel.mp4')
        self.assertNotIn('publish',events)

    def test_wrong_account_blocks_media_creation(self):
        import os
        with patch.dict(os.environ,{'META_TOKEN':'IGtest','IG_USER_ID':'123'}):
            meta=c.Meta()
        with patch.object(meta,'call',return_value={'username':'different_account'}):
            with self.assertRaises(RuntimeError): meta.check_account()


if __name__=='__main__': unittest.main()
