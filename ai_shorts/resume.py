import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, 'reels/pythonic')
import publish

entries = publish.items()
meta = publish.campaign.Meta()
meta.check_account()
tag = json.loads(publish.MANIFEST.read_text())['batch_id']
if subprocess.run(['gh', 'release', 'view', tag], capture_output=True).returncode:
    subprocess.run(['gh', 'release', 'create', tag, '--title', 'ShipStack AI in Motion',
                    '--notes', 'Ten vertical educational shorts.', '--latest=false'], check=True)
    subprocess.run(['gh', 'release', 'upload', tag, *map(str, sorted(Path('output').glob('*.mp4')))], check=True)
for entry in entries:
    key = entry['id']
    existing = publish.campaign.read_state()['posts'].get(key)
    if existing:
        if existing['status'] != 'published':
            from datetime import datetime
            recent = meta.call(f'{meta.ig_id}/media', {'fields':'id,caption,permalink','limit':50}).get('data', [])
            matches = [m for m in recent if m.get('caption','').strip() == entry['caption'].strip()]
            container = existing['container_id']
            status = meta.call(container, {'fields':'status_code'}).get('status_code')
            print(key, 'container', status, flush=True)
            if len(matches) == 1:
                media = matches[0]['id']
            elif not matches and status == 'FINISHED':
                media = meta.call(f'{meta.ig_id}/media_publish', {'creation_id':container}, 'POST')['id']
            else:
                raise SystemExit(f'{key} requires reconciliation before resubmitting')
            state = publish.campaign.read_state()
            state['posts'][key].update(status='published', media_id=media, published_at=datetime.now(publish.campaign.IST).isoformat())
            publish.campaign.persist(state)
        print(f'{key} already published', flush=True)
        continue
    if not Path('output', key + '.mp4').exists():
        raise SystemExit(f'Asset missing for {key}')
    publish.publish_one(entry, Path('output', key + '.mp4'), meta)
    time.sleep(12)
print('Confirmed 10 Instagram Reels', flush=True)
