"""Publish the selected Instagram originals to ShipStack on Facebook."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import datetime as dt

from campaign import IST, persist, read_state
from facebook import Facebook

SHIPSTACK_ID = '1390488964137653'
MANIFEST = Path(__file__).with_name('selection.json')


def main():
    if os.environ['FB_PAGE_ID'].strip() not in {SHIPSTACK_ID, '61595003966637'}:
        raise RuntimeError('Configured destination is not a known ShipStack ID')
    os.environ['FB_PAGE_ID'] = SHIPSTACK_ID
    fb = Facebook()
    page = fb.check()
    if page.get('name', '').casefold() != 'shipstack':
        raise RuntimeError('Facebook Page name did not match ShipStack')
    print('Verified Facebook destination: ShipStack', flush=True)
    items = json.loads(MANIFEST.read_text())
    if len(items) != 10 or len({item['id'] for item in items}) != 10:
        raise RuntimeError('Expected ten distinct selected reels')
    state = read_state()
    if any(state['posts'].get(item['id'], {}).get('status') != 'published' for item in items):
        raise RuntimeError('A selected reel lacks a confirmed Instagram publication')
    with tempfile.TemporaryDirectory() as directory:
        clips = {}
        hashes = set()
        for item in items:
            source = Path(directory) / item['id']
            source.mkdir()
            subprocess.run(['gh', 'release', 'download', item['tag'], '--pattern', item['asset'],
                            '--dir', str(source)], check=True)
            file = source / item['asset']
            digest = hashlib.file_digest(file.open('rb'), 'sha256').hexdigest()
            if digest in hashes:
                raise RuntimeError('Two selected reels have identical media')
            hashes.add(digest)
            clips[item['id']] = file
        for i, item in enumerate(items):
            key = item['id']
            record = state['posts'][key]
            prior = record.get('facebook')
            if prior and prior['status'] == 'published':
                print('Already published:', key, flush=True)
                continue
            if prior:
                video = prior['video_id']
                try:
                    status = fb.call(video, {'fields': 'status'}).get('status', {})
                except RuntimeError as error:
                    print(f'Unconfirmed prior attempt {key}: {error}', flush=True)
                    continue
                phase = status.get('publishing_phase', {})
                if phase.get('publish_status') != 'published':
                    print(f'Unconfirmed prior attempt {key}: {video}', flush=True)
                    continue
            else:
                video = fb.upload(clips[key])
                record['facebook'] = {'video_id': video, 'status': 'publishing',
                                      'attempted_at': dt.datetime.now(IST).isoformat()}
                persist(state)
                try:
                    fb.finish(video, record['caption'])
                except RuntimeError as error:
                    print(f'Unconfirmed publication {key}: {error}', flush=True)
                    continue
            record['facebook'].update(status='published', published_at=dt.datetime.now(IST).isoformat())
            persist(state)
            print(f'FACEBOOK_PUBLISHED {key} {video}', flush=True)
            if i+1 < len(items):
                time.sleep(45)


if __name__ == '__main__':
    main()
