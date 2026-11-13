"""Reconcile the first submission, then publish the revised soundtrack once."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, 'reels/pythonic')
import publish

entry, = publish.items()
campaign = publish.campaign
meta = campaign.Meta()
meta.check_account()
state = campaign.read_state()
key = entry['id']
record = state['posts'][key]
if record['status'] == 'published':
    print('Instagram already confirmed', record['media_id'], flush=True)
    sys.exit(0)

recent = meta.call(f'{meta.ig_id}/media', {'fields': 'id,caption,permalink', 'limit': 100}).get('data', [])
matches = [m for m in recent if m.get('caption', '').strip() == entry['caption'].strip()]
if len(matches) == 1:
    record.update(status='published', media_id=matches[0]['id'], published_at=dt.datetime.now(campaign.IST).isoformat())
    campaign.persist(state)
    print('Instagram already shows the reel', matches[0].get('permalink'), flush=True)
    sys.exit(0)
if matches:
    raise SystemExit('Multiple matching reels are already visible.')

previous = record['container_id']
status = meta.call(previous, {'fields': 'status_code'}).get('status_code')
print('Previous container:', status, flush=True)
if status not in {'FINISHED', 'ERROR', 'EXPIRED'} or record.get('previous_container_id'):
    raise SystemExit('Previous attempt needs reconciliation before another upload.')

clip = Path('PI-20261113-01.mp4')
tag = json.loads(publish.MANIFEST.read_text())['batch_id']
asset = clip.rename('Pi_Collisions_15s_ShipStack.mp4')
subprocess.run(['gh', 'release', 'upload', tag, str(asset)], check=True)
repo = 'Sumntpathak/insta-autopost'
url = f'https://github.com/{repo}/releases/download/{tag}/{asset}'
container = meta.call(f'{meta.ig_id}/media', {'media_type': 'REELS', 'video_url': url,
                      'caption': entry['caption'], 'share_to_feed': 'true'}, 'POST')['id']
meta.ready(container)
record.update(previous_container_id=previous, container_id=container,
              content_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),
              attempted_at=dt.datetime.now(campaign.IST).isoformat())
campaign.persist(state)
request = urllib.request.Request(meta.api + f'{meta.ig_id}/media_publish',
                                  data=urllib.parse.urlencode({'creation_id': container}).encode(),
                                  headers={'Authorization': 'Bearer ' + meta.token}, method='POST')
try:
    with urllib.request.urlopen(request, timeout=60) as response:
        media = json.load(response)['id']
except urllib.error.HTTPError as error:
    detail = json.load(error).get('error', {})
    print(f"Instagram rejected publication (HTTP {error.code}, code {detail.get('code')}, subcode {detail.get('error_subcode')})", flush=True)
    raise SystemExit(1)
record.update(status='published', media_id=media, published_at=dt.datetime.now(campaign.IST).isoformat())
campaign.persist(state)
media_detail = meta.call(media, {'fields': 'permalink'})
print('INSTAGRAM_PERMALINK', media_detail.get('permalink'), flush=True)
