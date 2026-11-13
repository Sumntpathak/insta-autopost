import datetime as dt
import hashlib
import json
from pathlib import Path

from campaign import IST, persist, read_state
from facebook import Facebook

fb = Facebook()
if fb.check().get('name', '').casefold() != 'shipstack':
    raise SystemExit('Facebook Page did not match ShipStack.')
root = Path(__file__).parent
items = json.loads((root / '20261113.json').read_text())
state = read_state()
for item in items:
    key = item['id']
    existing = state['posts'].get(key, {}).get('facebook')
    if existing and existing['status'] == 'published':
        print('FB_CONFIRMED', key, existing['video_id'], flush=True)
        continue
    clip = root / item['file']
    digest = hashlib.sha256(clip.read_bytes()).hexdigest()
    duplicate = next((p['facebook'] for k,p in state['posts'].items()
                      if k != key and p.get('content_sha256') == digest
                      and p.get('facebook', {}).get('status') == 'published'), None)
    if duplicate:
        print('FB_EXISTING', key, duplicate['video_id'], flush=True)
        continue
    if existing:
        video = existing['video_id']
        status = fb.call(video, {'fields': 'status'}).get('status', {})
        if status.get('publishing_phase', {}).get('publish_status') != 'published':
            raise SystemExit(f'{key} has an unconfirmed publication.')
        record = state['posts'][key]
    else:
        video = fb.upload(clip)
        record = {'id': key, 'scene': 'facebook-manual-physics', 'status': 'facebook_only',
                  'caption': item['caption'], 'content_sha256': digest,
                  'facebook': {'video_id': video, 'status': 'publishing',
                               'attempted_at': dt.datetime.now(IST).isoformat()}}
        state['posts'][key] = record
        persist(state)
        fb.finish(video, item['caption'])
    record['facebook'].update(status='published', published_at=dt.datetime.now(IST).isoformat())
    persist(state)
    print('FB_CONFIRMED', key, video, flush=True)
