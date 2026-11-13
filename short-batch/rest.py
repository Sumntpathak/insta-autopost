import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0,'reels/pythonic')
import publish

meta=publish.campaign.Meta()
meta.check_account()
tag=json.loads(publish.MANIFEST.read_text())['batch_id']
if subprocess.run(['gh','release','view',tag],capture_output=True).returncode:
    subprocess.run(['gh','release','create',tag,'--title','ShipStack 15-second physics','--notes','Original physics shorts.','--latest=false'],check=True)
for i,item in enumerate(publish.items()[1:]):
    if i:
        time.sleep(240)
    record=publish.publish_one(item,Path('output',item['id']+'.mp4'),meta)
    if record.get('status')!='published':
        raise SystemExit(f"{item['id']} needs reconciliation.")
    print('CONFIRMED',item['id'],record['media_id'],flush=True)
