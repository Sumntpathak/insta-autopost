import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0,'reels/pythonic')
import publish

campaign=publish.campaign
meta=campaign.Meta()
meta.check_account()
items=publish.items()
key=items[0]['id']
state=campaign.read_state()
if state['posts'].get(key,{}).get('status')!='published':
    recent=meta.call(f'{meta.ig_id}/media', {'fields':'id,caption,permalink','limit':50}).get('data',[])
    matches=[r for r in recent if r.get('caption','').strip()==items[0]['caption'].strip()]
    container='17896295262522936'
    if len(matches)==1:
        media=matches[0]['id']
    elif not matches:
        status=meta.call(container,{'fields':'status_code'}).get('status_code')
        if status!='FINISHED':
            raise SystemExit(f'Balloon container status: {status}')
        url=meta.api.rstrip('/')+f'/{meta.ig_id}/media_publish'
        req=urllib.request.Request(url,data=urllib.parse.urlencode({'creation_id':container}).encode(),
                                   headers={'Authorization':'Bearer '+meta.token},method='POST')
        try:
            with urllib.request.urlopen(req,timeout=60) as response:
                media=json.load(response)['id']
        except urllib.error.HTTPError as exc:
            try: detail=json.load(exc).get('error',{})
            except ValueError: detail={}
            print('PUBLISH_REJECTED',exc.code,{k:detail.get(k) for k in ('code','error_subcode','type','is_transient')},flush=True)
            raise SystemExit(1)
    else:
        raise SystemExit('Multiple matching balloon reels.')
    state['posts'][key]={**items[0],'status':'published','media_id':media,'container_id':container,
                        'published_at':dt.datetime.now(campaign.IST).isoformat()}
    campaign.persist(state)
print('CONFIRMED',key,flush=True)
