import datetime as dt
import hashlib
import json
import time
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
        record = state['posts'][key]
    else:
        try:
            video = fb.upload(clip)
        except RuntimeError as exc:
            print('FB_UPLOAD_FAILED', key, str(exc), flush=True)
            continue
        record = {'id': key, 'scene': 'facebook-manual-physics', 'status': 'facebook_only',
                  'caption': item['caption'], 'content_sha256': digest,
                  'facebook': {'video_id': video, 'status': 'publishing',
                               'attempted_at': dt.datetime.now(IST).isoformat()}}
        state['posts'][key] = record
        persist(state)
        result = fb.call(fb.page+'/video_reels', {'upload_phase':'finish','video_id':video,
                         'video_state':'PUBLISHED','description':item['caption']}, 'POST')
        print('FB_FINISH_ACCEPTED', key, video, bool(result.get('success')), flush=True)
    for attempt in range(8):
        try:
            info = fb.call(video, {'fields': 'status,permalink_url'})
            phase = info.get('status', {}).get('publishing_phase', {})
            if phase.get('publish_status') == 'published':
                break
            if phase.get('status') == 'error':
                break
        except RuntimeError as exc:
            print('FB_STATUS_WAIT', key, attempt+1, str(exc), flush=True)
        time.sleep(5)
    else:
        phase = {}
    if phase.get('publish_status') != 'published':
        print('FB_UNCONFIRMED', key, video, flush=True)
        continue
    record['facebook'].update(status='published', published_at=dt.datetime.now(IST).isoformat())
    persist(state)
    print('FB_CONFIRMED', key, video, info.get('permalink_url'), flush=True)
