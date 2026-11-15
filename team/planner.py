"""A 100-delivery UTC day, evenly spread and deduplicated across platforms."""
from datetime import datetime,timedelta,timezone
import hashlib


def slots(start,day,allocation,format_counts):
    if day not in range(7): raise ValueError('Pilot day must be 0..6')
    if sum(allocation.values())!=100 or any(v<0 for v in allocation.values()):
        raise ValueError('Allocation must total 100')
    if sum(format_counts.values())!=100: raise ValueError('Formats must total 100')
    formats=[]
    # Smoothly interleave formats instead of publishing all reels in one region.
    remaining=dict(format_counts); used={k:0 for k in remaining}
    for i in range(100):
        kind=max((k for k in remaining if remaining[k]>0),key=lambda k:(i+1)*format_counts[k]/100-used[k])
        formats.append(kind); used[kind]+=1; remaining[kind]-=1
    ig_used=0
    for index in range(100):
        target=round((index+1)*allocation['instagram']/100)
        platform='instagram' if target>ig_used else 'facebook'
        if platform=='instagram': ig_used+=1
        at=start+timedelta(days=day,seconds=index*864)
        key=f"SS-{start.date().isoformat()}-D{day+1:02d}-{index+1:03d}"
        seed=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)
        yield {'id':key,'day':day+1,'index':index,'platform':platform,'format':formats[index],
               'due_at':at.isoformat(),'seed':seed}


def due(state,cfg,at):
    if not cfg['enabled'] or not state.get('start_at'): return []
    start=datetime.fromisoformat(state['start_at'])
    if start.tzinfo is None: raise ValueError('start_at must include timezone')
    day=(at-start).days
    if not 0<=day<cfg['pilot_days']: return []
    output=[]
    for slot in slots(start,day,state['allocation'],cfg['daily_format_counts']):
        if slot['id'] in state['posts']: continue
        late=(at-datetime.fromisoformat(slot['due_at'])).total_seconds()
        if 0<=late<=cfg['max_lateness_minutes']*60: output.append(slot)
    return output[:cfg['max_jobs_per_cycle']]


def has_capacity(platform,records,at,limit):
    cutoff=at-timedelta(hours=24)
    used=sum(1 for p in records.values() if p.get('platform')==platform and p.get('attempted_at')
             and datetime.fromisoformat(p['attempted_at'])>cutoff
             and p.get('status') in ('publishing','published','uncertain'))
    return used<limit
