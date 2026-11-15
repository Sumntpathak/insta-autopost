import argparse
from datetime import datetime,timedelta,timezone
import json
from .storage import config,read,persist,save_report,now
from .planner import slots
from .runner import check,activate,run,baseline,clients
from .community import poll


def main():
    parser=argparse.ArgumentParser(description='ShipStack coordinated content team')
    parser.add_argument('mode',choices=['check','plan','activate','cycle','preview','baseline','community','status','pause'])
    parser.add_argument('--start'); parser.add_argument('--live',action='store_true')
    args=parser.parse_args(); cfg=config(); state=read()
    if args.mode=='check':
        result=check(cfg)
        print(json.dumps(result,indent=2))
        if not result['ready']: raise SystemExit(1)
        return
    if args.mode=='activate':
        if not args.start: parser.error('--start is required; no silent campaign initialization')
        activate(cfg,state,args.start); result={'start_at':state['start_at']}
    elif args.mode=='plan':
        start=datetime.fromisoformat(args.start.replace('Z','+00:00')) if args.start else datetime.combine(now().date()+timedelta(days=1),datetime.min.time(),timezone.utc)
        if start.tzinfo is None: parser.error('--start must include timezone')
        plan=[slot for day in range(7) for slot in slots(start,day,{'instagram':50,'facebook':50},cfg['daily_format_counts'])]
        result={'queue':str(save_report('seven-day-plan.json',{'planning_only':True,'slots':plan})),
                'deliveries':len(plan),'note':'Slots are briefs, not finished content or a live schedule'}
    elif args.mode in ('cycle','preview'):
        result=run(cfg,state,now(),live=args.mode=='cycle' and args.live)
        save_report('cycle.json',result)
    elif args.mode=='baseline': result=baseline(cfg,state)
    elif args.mode=='community':
        if not cfg['enabled'] or not state.get('start_at'): result={'active':False}
        else: result=poll(clients(),state,cfg,now())
        save_report('community-summary.json',result)
    elif args.mode=='pause':
        cfg['enabled']=False
        from .storage import ROOT
        (ROOT/'config.json').write_text(json.dumps(cfg,indent=2)+'\n')
        result={'paused':True,'note':'Commit the config change to stop hosted scheduling'}
    else:
        result={'enabled':cfg['enabled'],'start_at':state['start_at'],'published':sum(p.get('status')=='published' for p in state['posts'].values()),
                'uncertain':sum(p.get('status')=='uncertain' for p in state['posts'].values()),'allocation':state['allocation']}
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
