"""Paginated historical inventory and evidence-based daily/CEO reports."""
from datetime import datetime,timezone
import statistics
import re
from urllib.parse import urlparse
from .platforms import Instagram,Facebook,APIError
from .storage import now,save_report


def metric_value(entry):
    total=entry.get('total_value',{})
    if 'value' in total: return total['value']
    values=entry.get('values',[])
    return values[-1].get('value') if values else None


def collect(client,platform,expected):
    account=client.check(expected)
    audience={}; account_unavailable=[]
    fields='followers_count,follows_count,media_count' if platform=='instagram' else 'followers_count,fan_count'
    try: audience['counts']=client.call(client.id,{'fields':fields})
    except (APIError,RuntimeError): account_unavailable.append('follower/account counts')
    if platform=='instagram':
        for name in ('reached_audience_demographics','engaged_audience_demographics'):
            try:
                audience[name]=client.call(client.id+'/insights',{'metric':name,'period':'lifetime','metric_type':'total_value',
                                            'breakdown':'country','timeframe':'this_month'}).get('data',[])
                if not audience[name]:account_unavailable.append(name)
            except (APIError,RuntimeError):account_unavailable.append(name)
    path=client.id+('/media' if platform=='instagram' else '/published_posts')
    fields='id,caption,media_type,media_product_type,timestamp,permalink' if platform=='instagram' else 'id,created_time,permalink_url'
    rows=[]; errors=[]
    try:
        for item in client.pages(path,{'fields':fields,'limit':100}):
            row={'id':item['id'],'platform':platform,'timestamp':item.get('timestamp',item.get('created_time')),
                 'media_type':item.get('media_type','unknown'),'media_product_type':item.get('media_product_type'),
                 'permalink':item.get('permalink',item.get('permalink_url')),'metrics':{},'unavailable':[]}
            if platform=='instagram':
                names=['reach','views','likes','comments','saved','shares']
                if row['media_product_type']=='REELS': names+=['ig_reels_avg_watch_time','ig_reels_video_view_total_time']
                for name in names:
                    try:
                        data=client.call(item['id']+'/insights',{'metric':name}).get('data',[])
                        if not data: row['unavailable'].append(name)
                        for entry in data:
                            value=metric_value(entry)
                            if isinstance(value,(int,float)): row['metrics'][name]=value
                            else: row['unavailable'].append(name)
                    except (APIError,RuntimeError) as exc:
                        row['unavailable'].append(name);row.setdefault('metric_errors',{})[name]=str(exc)
            else:
                # Counter summaries remain useful even when Page insights permission is absent.
                for name,field in [('reactions','reactions.limit(0).summary(true)'),('comments','comments.limit(0).summary(true)'),('shares','shares')]:
                    try:
                        data=client.call(item['id'],{'fields':field})
                        value=data.get('shares',{}).get('count') if name=='shares' else data.get('reactions' if name=='reactions' else 'comments',{}).get('summary',{}).get('total_count')
                        if isinstance(value,(int,float)): row['metrics'][name]=value
                        else: row['unavailable'].append(name)
                    except (APIError,RuntimeError): row['unavailable'].append(name)
                for metric in ('post_media_view','post_total_media_view_unique'):
                    try:
                        data=client.call(item['id']+'/insights',{'metric':metric}).get('data',[])
                        value=metric_value(data[0]) if data else None
                        if isinstance(value,(int,float)): row['metrics']['views' if metric=='post_media_view' else 'unique_media_viewers']=value
                        else: row['unavailable'].append(metric)
                    except (APIError,RuntimeError) as exc:
                        row['unavailable'].append(metric);row.setdefault('metric_errors',{})[metric]=str(exc)
                # Reels have a Page post ID and a separate video ID. Some counters
                # are exposed only on the video object, as in the legacy FB reader.
                permalink=urlparse(row.get('permalink') or '')
                match=re.search(r'/reel/(\d+)',permalink.path) if permalink.hostname in ('facebook.com','www.facebook.com') else None
                if match:
                    video=match.group(1);row['video_id']=video;row['media_type']='VIDEO';row['media_product_type']='REELS'
                    row['metric_sources']={}
                    for metric,key in [('post_video_views','views'),('total_video_views','views'),('total_video_views_unique','unique_3_second_video_viewers'),('post_video_avg_time_watched','avg_watch_time_ms'),('total_video_avg_time_watched','avg_watch_time_ms')]:
                        if key in row['metrics']:continue
                        try:
                            data=client.call(video+'/video_insights',{'metric':metric}).get('data',[])
                            value=metric_value(data[0]) if data else None
                            if isinstance(value,(int,float)) and key not in row['metrics']:
                                row['metrics'][key]=value;row['metric_sources'][key]=metric
                        except (APIError,RuntimeError) as exc:
                            row['unavailable'].append(metric);row.setdefault('metric_errors',{})[metric]=str(exc)
                    if 'views' not in row['metrics']:
                        try:
                            value=client.call(video,{'fields':'views'}).get('views')
                            if isinstance(value,(int,float)):
                                row['metrics']['views']=value;row['metric_sources']['views']='video.views'
                        except (APIError,RuntimeError):pass
                    for key,field in [('reactions','reactions.limit(0).summary(true)'),('comments','comments.limit(0).summary(true)'),('shares','shares')]:
                        if key in row['metrics']:continue
                        try:
                            data=client.call(video,{'fields':field})
                            value=data.get('shares',{}).get('count') if key=='shares' else data.get(key,{}).get('summary',{}).get('total_count')
                            if isinstance(value,(int,float)):
                                row['metrics'][key]=value;row['metric_sources'][key]='video object summary'
                        except (APIError,RuntimeError):pass
            reach=row['metrics'].get('reach') or row['metrics'].get('unique_media_viewers')
            row['share_rate_denominator']='reach' if row['metrics'].get('reach') else 'unique_media_viewers'
            if reach and all(k in row['metrics'] for k in ('likes','comments','shares')):
                row['engagement_per_reach']=(sum(row['metrics'][k] for k in ('likes','comments','shares'))+row['metrics'].get('saved',0))/reach
            if reach and 'shares' in row['metrics']: row['share_rate']=row['metrics']['shares']/reach
            row['unavailable']=[m for m in row['unavailable'] if m not in row['metrics']]
            rows.append(row)
    except (APIError,RuntimeError) as exc: errors.append(str(exc))
    # Historical insights often have a finite retention window; never claim unavailable data.
    return {'platform':platform,'account':account,'audience':audience,'account_metrics_unavailable':account_unavailable,
            'collected_at':now().isoformat(),'inventory_complete':not errors,
            'coverage':'Every media page returned by the API; historical metrics only where available',
            'errors':errors,'posts':rows}


def summarize(reports):
    platforms={}
    for report in reports:
        rows=report['posts']; totals={}
        for metric in ('likes','reactions','comments','shares','saved','views','reach','unique_media_viewers','unique_3_second_video_viewers'):
            values=[r['metrics'][metric] for r in rows if metric in r['metrics']]
            totals[metric]={'sum':sum(values),'available_posts':len(values),'missing_posts':len(rows)-len(values)}
        winners=sorted((r for r in rows if 'share_rate' in r),key=lambda r:r['share_rate'],reverse=True)[:10]
        platforms[report['platform']]={'post_count':len(rows),'complete_inventory':report['inventory_complete'],
            'audience':report.get('audience',{}),'account_metrics_unavailable':report.get('account_metrics_unavailable',[]),
            'metric_error_examples':list(dict.fromkeys(e for r in rows for e in r.get('metric_errors',{}).values()))[:5],
            'totals':totals,'top_by_share_rate':winners,'errors':report['errors']}
    return {'created_at':now().isoformat(),'platforms':platforms,
            'interpretation':['Summed post reach is not deduplicated account reach.',
                              'Lifetime post counters are not daily increments; compare dated snapshots.',
                              'Missing metrics are not zeros; likes alone do not determine winners.',
                              'Facebook unique media viewers and Instagram reach are distinct platform definitions; three-second video viewers are never relabeled reach.',
                              'Historical results are observational; a one-week pilot cannot prove long-term growth or ad revenue.']}


def recommend_split(reports,state,cfg,at):
    if not state.get('start_at') or (at-datetime.fromisoformat(state['start_at'])).total_seconds()<48*3600:
        return dict(state['allocation']),'Waiting for 48 hours of live pilot data'
    scores={}
    for report in reports:
        eligible=[]
        for row in report['posts']:
            record=next((p for p in state['posts'].values() if p.get('media_id') and p.get('media_id') in (row['id'],row.get('video_id')) and p.get('platform')==report['platform']),None)
            if not record or record.get('status')!='published': continue
            stamp=datetime.fromisoformat(record['published_at'])
            if (at-stamp).total_seconds()<24*3600: continue
            reach=row['metrics'].get('reach') or row['metrics'].get('unique_media_viewers')
            shares=row['metrics'].get('shares')
            if reach and reach>=100 and shares is not None: eligible.append(shares/reach)
        if len(eligible)>=5: scores[report['platform']]=statistics.median(eligible)
    if len(scores)!=2: return dict(state['allocation']),'Insufficient comparable 24-hour-old pilot posts on both platforms'
    if max(scores.values())<=0 or max(scores.values())<1.2*min(scores.values()):
        return dict(state['allocation']),'No material difference in median share rate'
    winner=max(scores,key=scores.get); loser='facebook' if winner=='instagram' else 'instagram'
    allocation=dict(state['allocation']); move=min(cfg['max_allocation_change'],allocation[loser]-cfg['minimum_platform_slots'])
    allocation[winner]+=move; allocation[loser]-=move
    return allocation,'Tentative allocation based on mature pilot share rates; retain exploration, not a causal finding'


def recommend_formats(reports,state,cfg,at):
    current=dict(state.get('format_counts',cfg['daily_format_counts']))
    if not state.get('start_at') or (at-datetime.fromisoformat(state['start_at'])).total_seconds()<48*3600:
        return current,'Waiting for 48 hours of live pilot data'
    normalized={kind:[] for kind in current}
    for report in reports:
        groups={kind:[] for kind in current}
        for row in report['posts']:
            record=next((p for p in state['posts'].values() if p.get('media_id') and p.get('media_id') in (row['id'],row.get('video_id')) and p.get('platform')==report['platform']),None)
            if not record or record.get('status')!='published' or record.get('format') not in groups:continue
            if (at-datetime.fromisoformat(record['published_at'])).total_seconds()<86400:continue
            reach=row['metrics'].get('reach') or row['metrics'].get('unique_media_viewers'); shares=row['metrics'].get('shares')
            if reach and reach>=100 and shares is not None:groups[record['format']].append(shares/reach)
        # Compare formats within each platform, never raw Instagram vs Facebook views.
        if any(len(values)<5 for values in groups.values()):continue
        medians={kind:statistics.median(values) for kind,values in groups.items()}
        total=sum(medians.values())
        if total<=0:continue
        for kind,value in medians.items():normalized[kind].append(value/total)
    if not all(normalized.values()):return current,'Insufficient mature format samples; retain the initial format mix'
    scores={kind:statistics.mean(values) for kind,values in normalized.items()}
    best=max(scores,key=scores.get); worst=min(scores,key=scores.get)
    if scores[best]<scores[worst]*1.2:return current,'No material format difference'
    shift=min(5,max(0,current[worst]-10)); current[best]+=shift;current[worst]-=shift
    return current,'Exploratory next-day format adjustment, retaining at least ten slots per format'
