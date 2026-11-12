import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

path=Path(__file__).parents[1]/'pythonic'/'publish.py'
spec=importlib.util.spec_from_file_location('night_publish',path)
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)

class BatchTests(unittest.TestCase):
    def setUp(self):
        self.item={'id':'PL-test','scene':'pl-balloon','variant':0,'caption':'Pick a balloon','collection':'pythonic-life'}
        self.state={'start_date':'2026-11-12','posts':{}}
        self.events=[]
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.file=Path(self.tmp.name)/'PL-test.mp4';self.file.write_bytes(b'tested clip bytes')
        self.file.with_suffix('.mp4.json').write_text(json.dumps({'scene':'pl-balloon','variant':0,'seconds':15}))
        self.patches=[patch.object(n,'items',return_value=[self.item]),patch.object(n.campaign,'read_state',return_value=self.state),
            patch.object(n.campaign,'persist',side_effect=lambda _:self.events.append('persist')),
            patch.object(n.subprocess,'run'),patch.dict('os.environ',{'GITHUB_REPOSITORY':'owner/repo'}),
            patch.object(n,'MANIFEST',Path(self.tmp.name)/'batch.json')]
        (Path(self.tmp.name)/'batch.json').write_text('{"batch_id":"test"}')
        for p in self.patches:p.start();self.addCleanup(p.stop)

    def meta(self,fail=False):
        events=self.events
        class Fake:
            ig_id='123'
            def ready(self,_):events.append('ready')
            def call(self,path,data=None,method='GET'):
                if path.endswith('media_publish'):
                    events.append('publish')
                    if fail:raise TimeoutError('uncertain API result')
                return {'id':'456'}
        return Fake()

    def test_persist_before_publish_and_record_success(self):
        result=n.publish_one(self.item,self.file,self.meta())
        self.assertEqual(self.events,['ready','persist','publish','persist'])
        self.assertEqual(result['status'],'published')
        self.assertEqual(result['content_sha256'],hashlib.sha256(self.file.read_bytes()).hexdigest())

    def test_uncertain_post_is_not_retried(self):
        with self.assertRaises(TimeoutError):n.publish_one(self.item,self.file,self.meta(fail=True))
        self.assertEqual(self.state['posts'][self.item['id']]['status'],'publishing')
        self.events.clear();n.publish_one(self.item,self.file,self.meta())
        self.assertEqual(self.events,[])

    def test_duplicate_video_is_blocked(self):
        self.state['posts']['old']={'status':'published','content_sha256':hashlib.sha256(self.file.read_bytes()).hexdigest()}
        with self.assertRaisesRegex(RuntimeError,'identical'):n.publish_one(self.item,self.file,self.meta())
        self.assertEqual(self.events,[])

    def test_render_must_match_manifest(self):
        self.file.with_suffix('.mp4.json').write_text('{"scene":"pl-ring","variant":0,"seconds":15}')
        with self.assertRaisesRegex(RuntimeError,'metadata'):n.publish_one(self.item,self.file,self.meta())

    def test_facebook_catchup_does_not_republish_instagram(self):
        self.state['posts'][self.item['id']]=dict(self.item,status='published',media_id='old')
        events=self.events
        class FB:
            def upload(self,file):events.append('fb-upload');return 'fb-1'
            def finish(self,video,caption):events.append('fb-finish')
        result=n.publish_one(self.item,self.file,self.meta(),FB())
        self.assertEqual(events,['fb-upload','persist','fb-finish','persist'])
        self.assertEqual(result['facebook']['status'],'published')
        events.clear();n.publish_one(self.item,self.file,self.meta(),FB())
        self.assertEqual(events,[])

    def test_unknown_item_is_blocked(self):
        with self.assertRaisesRegex(RuntimeError,'authorized'):n.publish_one(dict(self.item,id='other'),self.file,self.meta())

class ManifestTests(unittest.TestCase):
    def test_ten_distinct_video_plans(self):
        manifest=json.loads((Path(__file__).parents[1]/'pythonic'/'batch.json').read_text())
        self.assertEqual(len(manifest['items']),10)
        self.assertEqual(len({i['id'] for i in manifest['items']}),10)
        self.assertEqual(len({(i['scene'],i['variant']) for i in manifest['items']}),10)

if __name__=='__main__':unittest.main()
