"""Publish the approved discipline batch to Instagram."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, 'reels/pythonic')
import publish
import campaign

entries = publish.items()
if len(entries) != 10:
    raise RuntimeError('Expected ten reels')
meta = campaign.Meta()
meta.check_account()
tag = json.loads(publish.MANIFEST.read_text())['batch_id']
if subprocess.run(['gh', 'release', 'view', tag], capture_output=True).returncode:
    subprocess.run(['gh', 'release', 'create', tag, '--title', 'Discipline Lift',
                    '--notes', 'Original scenes using nispa/stickman-video (MIT). License: nispa-batch/LICENSE.',
                    '--latest=false'], check=True)
for i, entry in enumerate(entries):
    key = entry['id']
    existing = campaign.read_state()['posts'].get(key)
    if existing:
        if existing['status'] == 'publishing':
            status = meta.call(existing['container_id'], {'fields': 'status_code'}).get('status_code')
            if status == 'PUBLISHED':
                recent = meta.call(f'{meta.ig_id}/media', {'fields': 'id,caption', 'limit': 50}).get('data', [])
                matches = [item for item in recent if item.get('caption', '').strip() == entry['caption'].strip()]
                if len(matches) == 1:
                    state = campaign.read_state()
                    state['posts'][key].update(status='published', media_id=matches[0]['id'])
                    campaign.persist(state)
        continue
    try:
        publish.publish_one(entry, Path('nispa-output') / (key + '.mp4'), meta)
    except (RuntimeError, TimeoutError) as error:
        print(f'{key}: {error}', flush=True)
    if i+1 < len(entries):
        time.sleep(15)
posts = campaign.read_state()['posts']
count = sum(posts.get(item['id'], {}).get('status') == 'published' for item in entries)
print(f'Confirmed {count}/{len(entries)} Instagram Reels', flush=True)
if count != len(entries):
    raise SystemExit(1)
