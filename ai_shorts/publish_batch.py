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
            raise SystemExit(f'{key} requires reconciliation before resubmitting')
        print(f'{key} already published', flush=True)
        continue
    publish.publish_one(entry, Path('output', key + '.mp4'), meta)
    time.sleep(12)
print('Confirmed 10 Instagram Reels', flush=True)
