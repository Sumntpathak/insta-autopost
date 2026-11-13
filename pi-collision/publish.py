"""Publish the one approved original π animation to Instagram."""
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, 'reels/pythonic')
import publish

entries = publish.items()
assert len(entries) == 1
entry = entries[0]
state = publish.campaign.read_state()
if entry['id'] in state['posts']:
    print(entry['id'], state['posts'][entry['id']]['status'])
    if state['posts'][entry['id']]['status'] != 'published':
        raise SystemExit('An earlier publish attempt needs reconciliation.')
    raise SystemExit(0)
meta = publish.campaign.Meta()
meta.check_account()
tag = json.loads(publish.MANIFEST.read_text())['batch_id']
if subprocess.run(['gh', 'release', 'view', tag], capture_output=True).returncode:
    subprocess.run(['gh', 'release', 'create', tag, '--title', 'ShipStack Pi Collisions',
                    '--notes', 'Original animation of Galperin’s idealized collision experiment.',
                    '--latest=false'], check=True)
clip = Path(entry['id'] + '.mp4')
clip.with_suffix('.mp4.json').write_text(json.dumps({
    'scene': entry['scene'], 'variant': entry['variant'], 'seconds': 15
}))
record = publish.publish_one(entry, clip, meta)
assert record['status'] == 'published'
print('Confirmed Instagram media ID:', record['media_id'])
