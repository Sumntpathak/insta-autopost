import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, 'reels/pythonic')
import publish

meta = publish.campaign.Meta()
meta.check_account()
entries = publish.items()
tag = json.loads(publish.MANIFEST.read_text())['batch_id']
if subprocess.run(['gh', 'release', 'view', tag], capture_output=True).returncode:
    subprocess.run(['gh', 'release', 'create', tag, '--title', 'Approved ShipStack Reels',
                    '--notes', 'Three-Balloon Race and a pi demonstration credited to @phys_icsbox.',
                    '--latest=false'], check=True)
for entry in entries:
    key = entry['id']
    clip = Path('approved-reels', key + '.mp4')
    clip.with_suffix('.mp4.json').write_text(json.dumps({k:entry[k] for k in ('scene','variant','seconds')}))
    try:
        result = publish.publish_one(entry, clip, meta)
        if result['status'] == 'published':
            detail = meta.call(result['media_id'], {'fields':'permalink'})
            print('CONFIRMED', key, detail.get('permalink'), flush=True)
    except (RuntimeError, TimeoutError) as exc:
        print(key, exc, flush=True)
    time.sleep(8)
state = publish.campaign.read_state()
if any(state['posts'].get(e['id'], {}).get('status') != 'published' for e in entries):
    raise SystemExit(1)
