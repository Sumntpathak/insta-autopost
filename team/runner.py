"""Coordinated production/publishing worker, one shared durable journal."""
from datetime import datetime,timedelta,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
from . import content
from .analytics import collect,summarize,recommend_split,recommend_formats
from .community import poll
from .planner import due,has_capacity,slots
from .platforms import Instagram,Facebook
from .storage import ROOT,config,read,persist,save_report,now


def clients(): return {'instagram':Instagram(),'facebook':Facebook()}


def check(cfg):
    report={'checked_at':now().isoformat(),'platforms':{},'ready':True}
    from .editor import available
    report['production']={'editorial_model_configured':available(),'curated_items':len(content.authored_briefs()),
                          'pilot_enabled':cfg['enabled'],'messaging_webhook_deployed_by_this_workflow':False}
    for platform,constructor,name in [('instagram',Instagram,cfg['instagram_account']),('facebook',Facebook,cfg['facebook_page_name'])]:
        try:
            api=constructor(); account=api.check(name)
            record={'identity_verified':True,'account':account}
            if platform=='instagram': record['remaining_quota']=api.quota()
            report['platforms'][platform]=record
        except Exception as exc:
            report['ready']=False
            report['platforms'][platform]={'identity_verified':False,'error':str(exc)}
    report['limitations']=['Identity and quota checks do not certify media publication or comment/messaging permissions.',
                            'Recent legacy reel processing had HTTP 403; validate container access before enabling volume.']
    save_report('readiness.json',report)
    return report


def activate(cfg,state,start):
    if state.get('start_at'): raise RuntimeError('Pilot already initialized; preserve its journal')
    moment=datetime.fromisoformat(start.replace('Z','+00:00'))
    if moment.tzinfo is None or moment<now(): raise ValueError('Start must be a future timestamp with timezone')
    readiness=check(cfg)
    if not readiness['ready']: raise RuntimeError('Account readiness failed; review team/out/readiness.json')
    if not cfg['enabled']: raise RuntimeError('Set team/config.json enabled=true before activation')
    state['start_at']=moment.astimezone(timezone.utc).isoformat(); persist(state)


def host(files,slot):
    repo=os.environ['GITHUB_REPOSITORY']; tag='shipstack-team-'+slot['id'].split('-D')[0].removeprefix('SS-')
    result=subprocess.run(['gh','release','view',tag],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if result.returncode:
        subprocess.run(['gh','release','create',tag,'--title','ShipStack pilot assets','--notes','Original ShipStack content and licensed font assets.','--latest=false'],check=True)
    subprocess.run(['gh','release','upload',tag,*map(str,files),'--clobber'],check=True)
    return [f'https://github.com/{repo}/releases/download/{tag}/{file.name}' for file in files]


def produce(slot,brief,cfg):
    directory=ROOT/'out'/slot['id']; directory.mkdir(parents=True,exist_ok=True)
    if slot['format']=='reel':
        from .glass_engine.cli import render
        return [render(brief['composition'],directory/(slot['id']+'.mp4'),cfg['render_width'],cfg['render_fps'])]
    return content.render_cards(brief,slot,directory)


def run(cfg,state,at,live=False):
    if not cfg['enabled'] or not state.get('start_at'):
        return {'active':False,'reason':'Pilot disabled or not initialized'}
    start=datetime.fromisoformat(state['start_at']); day=(at-start).days
    if not 0<=day<cfg['pilot_days']: return {'active':False,'reason':'Outside seven-day pilot'}
    allocations=state.setdefault('allocation_by_day',{})
    if str(day) not in allocations:
        allocations[str(day)]=dict(state['allocation']); persist(state)
    formats=state.setdefault('formats_by_day',{})
    if str(day) not in formats:
        formats[str(day)]=dict(state.get('format_counts',cfg['daily_format_counts']));persist(state)
    frozen={**state,'allocation':allocations[str(day)]}
    day_cfg={**cfg,'daily_format_counts':formats[str(day)]}
    jobs=due(frozen,day_cfg,at); report={'active':True,'due':len(jobs),'live':live,'jobs':[]}
    if not jobs:return report
    apis=clients() if live else {}
    if live:
        apis['instagram'].check(cfg['instagram_account']); apis['facebook'].check(cfg['facebook_page_name'])
    headlines,feed_errors=content.news(cfg,at); report['feed_errors']=feed_errors
    save_report('news-research.json',{'collected_at':at.isoformat(),'headlines':headlines,'errors':feed_errors})
    for slot in jobs:
        try: brief=content.choose(slot,cfg,state,headlines)
        except Exception as exc:
            report['jobs'].append({'id':slot['id'],'status':'editorial_held','error':type(exc).__name__})
            break
        errors=content.quality(brief,slot)
        if errors:
            report['jobs'].append({'id':slot['id'],'status':'held','errors':errors}); continue
        if not live:
            report['jobs'].append({'id':slot['id'],'platform':slot['platform'],'status':'preview','brief':brief}); continue
        platform=slot['platform']; api=apis[platform]
        if not has_capacity(platform,state['posts'],at,70):
            report['jobs'].append({'id':slot['id'],'status':'quota_deferred'}); continue
        # Persist a claim before expensive rendering or uploads; failed pre-publication
        # claims are reviewed, not blindly replayed on the next runner.
        record={**slot,'status':'rendering','kind':brief['kind'],'fingerprint':brief['fingerprint'],
                'source':brief.get('source'),'caption':brief['caption'],'claimed_at':at.isoformat()}
        state['posts'][slot['id']]=record; persist(state)
        try:
            files=produce(slot,brief,cfg); urls=host(files,slot)
            record.update(status='preparing',urls=urls); persist(state)
            container=api.prepare(urls,brief['caption'],slot['format'])
            record.update(status='publishing',container_id=container,attempted_at=now().isoformat()); persist(state)
            media=api.publish(container,brief['caption'])
            record.update(status='published',media_id=media,published_at=now().isoformat()); persist(state)
            report['jobs'].append({'id':slot['id'],'status':'published','platform':platform})
        except Exception as exc:
            record['status']='uncertain' if record['status']=='publishing' else 'failed_before_publish'
            record['error']=str(exc); persist(state)
            report['jobs'].append({'id':slot['id'],'status':record['status'],'error':str(exc)})
            # Auth/permission failure should not trigger six identical failed jobs.
            break
    return report


def baseline(cfg,state):
    reports=[]
    for platform,constructor,name in [('instagram',Instagram,cfg['instagram_account']),('facebook',Facebook,cfg['facebook_page_name'])]:
        try: report=collect(constructor(),platform,name)
        except Exception as exc:
            report={'platform':platform,'posts':[],'inventory_complete':False,'errors':[str(exc)]}
        reports.append(report); save_report(platform+'-history.json',report)
    summary=summarize(reports)
    allocation,reason=recommend_split(reports,state,cfg,now())
    formats,format_reason=recommend_formats(reports,state,cfg,now())
    summary['recommendation']={'next_day_allocation':allocation,'reason':reason,'next_day_formats':formats,'format_reason':format_reason}
    if state.get('start_at'):
        day=(now()-datetime.fromisoformat(state['start_at'])).days
        if day>=2 and not any(d.get('pilot_day')==day for d in state['decisions']):
            state['decisions'].append({'at':now().isoformat(),'pilot_day':day,'allocation':allocation,'reason':reason})
            state['allocation']=allocation;state['format_counts']=formats;persist(state)
    summary['ceo_review']={
      'positioning':cfg['audience'],
      'pilot_target':{'daily_deliveries':100,'seven_day_deliveries':700},
      'published_pilot_posts':sum(p.get('status')=='published' for p in state['posts'].values()),
      'uncertain_posts':sum(p.get('status')=='uncertain' for p in state['posts'].values()),
      'editorial_backlog_items':len(content.authored_briefs()),
      'next_actions':['Fix any account or media-processing failures before scaling.',
                      'Compare formats at matched post ages, and audit missing metric coverage.',
                      'Expand verified global-English editorial inventory; do not invent news to fill slots.',
                      'Use the next-day allocation proposal only when evidence is sufficient.'],
      'commercial_status':'Sponsorship readiness assessment only; no paid campaigns, outreach or revenue claims.'}
    path=save_report('ceo-review.json',summary)
    return {'report':str(path),'platform_post_counts':{r['platform']:len(r['posts']) for r in reports},
            'complete_inventory':all(r['inventory_complete'] for r in reports)}
