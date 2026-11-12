"""Publish the explicit overnight manifest once, preserving the common posting journal."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import datetime as dt

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
import campaign
from facebook import Facebook

MANIFEST=HERE/'batch.json'

def items():
    data=json.loads(MANIFEST.read_text())
    if not data.get('enabled'):raise RuntimeError('Overnight batch is disabled')
    entries=data['items']
    if len(entries)!=data['count'] or len({x['id'] for x in entries})!=len(entries):
        raise RuntimeError('Manifest count or IDs are invalid')
    if not 1<=len(entries)<=10:raise RuntimeError('This batch is limited to ten reels')
    return entries



def crosspost_facebook(item,file,record,state,facebook):
    if record.get('facebook'):
        print(item['id']+' Facebook already attempted: '+record['facebook']['status'],flush=True)
        return
    try:
        video=facebook.upload(file)
        record['facebook']={'video_id':video,'status':'publishing'};campaign.persist(state)
        facebook.finish(video,item['caption'])
        record['facebook'].update(status='published',published_at=dt.datetime.now(campaign.IST).isoformat())
        campaign.persist(state);print('FACEBOOK_PUBLISHED '+item['id']+' '+video,flush=True)
    except Exception as error:
        print('FACEBOOK_UNCONFIRMED '+item['id']+': '+str(error),flush=True)


def publish_one(item,file,meta,facebook=None):
    if item not in items():raise RuntimeError('Item is not in the authorized batch manifest')
    state=campaign.read_state();done=state['posts'].get(item['id'])
    if done:
        print(item['id']+' already attempted: '+done['status'],flush=True)
        if facebook and done['status']=='published':
            crosspost_facebook(item,file,done,state,facebook)
        return done
    file=Path(file)
    info=json.loads(file.with_suffix('.mp4.json').read_text())
    if info['scene']!=item['scene'] or info['variant']!=item['variant'] or info['seconds']!=15:
        raise RuntimeError('Rendered metadata does not match the selected item')
    digest=hashlib.sha256(file.read_bytes()).hexdigest()
    if any(p.get('content_sha256')==digest for p in state['posts'].values()):
        raise RuntimeError('An identical clip is already in the posting journal')
    repo=__import__('os').environ['GITHUB_REPOSITORY']
    tag=json.loads(MANIFEST.read_text())['batch_id']
    subprocess.run(['gh','release','upload',tag,str(file),'--clobber'],check=True)
    url=f'https://github.com/{repo}/releases/download/{tag}/{file.name}'
    container=meta.call(f'{meta.ig_id}/media',{'media_type':'REELS','video_url':url,
                        'caption':item['caption'],'share_to_feed':'true'},'POST')['id']
    meta.ready(container)
    record=dict(item,date=dt.datetime.now(campaign.IST).date().isoformat(),status='publishing',
                container_id=container,content_sha256=digest,source=info,
                attempted_at=dt.datetime.now(campaign.IST).isoformat())
    state['posts'][item['id']]=record
    campaign.persist(state)
    media=meta.call(f'{meta.ig_id}/media_publish',{'creation_id':container},'POST')['id']
    record.update(status='published',media_id=media,published_at=dt.datetime.now(campaign.IST).isoformat())
    campaign.persist(state)
    print('INSTAGRAM_PUBLISHED '+item['id']+' '+str(media),flush=True)
    if facebook:
        crosspost_facebook(item,file,record,state,facebook)
    return record


def main():
    p=argparse.ArgumentParser();p.add_argument('--dir',default='reels/out/pythonic');p.add_argument('--spacing',type=int,default=45)
    args=p.parse_args();entries=items();meta=campaign.Meta();print('Account: '+meta.check_account()['username'],flush=True)
    fb=None
    try:
        fb=Facebook();page=fb.check();print('Facebook Page: '+page['name'],flush=True)
    except RuntimeError as error:
        print('FACEBOOK_BLOCKED: '+str(error),flush=True);fb=None
    tag=json.loads(MANIFEST.read_text())['batch_id']
    exists=subprocess.run(['gh','release','view',tag],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if exists.returncode:
        subprocess.run(['gh','release','create',tag,'--target','main','--title','Pythonic Life overnight batch',
                        '--notes','Original renders adapted from MIT-licensed Pythonic Life scripts; attribution in reels/pythonic/UPSTREAM.md.','--latest=false'],check=True)
    for index,item in enumerate(entries):
        before=campaign.read_state()['posts'].get(item['id'])
        result=publish_one(item,Path(args.dir)/(item['id']+'.mp4'),meta,fb)
        if before is None and result.get('status')=='published' and index<len(entries)-1:
            time.sleep(max(0,min(args.spacing,120)))
    records=campaign.read_state()['posts']
    count=sum(records.get(item['id'],{}).get('status')=='published' for item in entries)
    print(f'BATCH_RESULT {count}/{len(entries)} Instagram reels confirmed',flush=True)

if __name__=='__main__':main()
