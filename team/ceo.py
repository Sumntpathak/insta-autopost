"""Plain-language historical review grounded in collected counters."""
import csv
import io
from .storage import ROOT,now


def write(reports,state,cfg):
    lines=['# ShipStack: historical outcomes and pilot decision',
           '',f'Review collected at {now().isoformat()}.',
           '', 'This is a snapshot of API-returned media and counters, not a reconstruction of every historical day.',
           '', '| Platform | Returned posts | Current followers | Measured views | Measured likes/reactions |',
           '|---|---:|---:|---:|---:|']
    for report in reports:
        rows=report['posts']; counts=report.get('audience',{}).get('counts',{})
        def total(key):
            values=[r['metrics'][key] for r in rows if key in r['metrics']]
            return f'{sum(values):,} ({len(values)}/{len(rows)} posts)' if values else 'Unavailable'
        lines.append(f"| {report['platform'].title()} | {len(rows)} | {counts.get('followers_count','Unavailable')} | {total('views')} | {total('likes' if report['platform']=='instagram' else 'reactions')} |")
    lines+=['', '## What the evidence supports', '']
    for report in reports:
        rows=report['posts']; platform=report['platform'].title()
        lines.append(f'### {platform}')
        lines.append('')
        if not report['inventory_complete']:
            lines.append('The returned inventory is incomplete. Resolve collection errors before treating this as a complete account review.')
        for metric,label in [('views','Most measured views'),('saved','Most measured saves'),('shares','Most measured shares')]:
            eligible=[r for r in rows if metric in r['metrics']]
            if not eligible:continue
            top=max(eligible,key=lambda r:r['metrics'][metric]); value=top['metrics'][metric]
            if value<=0:continue
            link=top.get('permalink') or top['id']
            lines.append(f'- {label}: [{top["id"]}]({link}), {value:,}. These are observed lifetime counters, not a controlled comparison.')
        covered=sum('shares' in r['metrics'] for r in rows)
        lines.append(f'- Share-counter coverage: {covered}/{len(rows)} returned posts. Missing counters are not zero engagement.')
        demos=report.get('audience',{}).get('reached_audience_demographics')
        if not demos:lines.append('- Country-level audience evidence is unavailable here. Global scheduling is a targeting plan, not proof of global reach.')
        lines.append('')
    lines+=['## CEO decisions', '',
            '- Keep prediction-based brain games as a recognizable entertainment pillar. Test useful tool/news explainers alongside them; historical views alone do not prove the new pillar will work.',
            '- Test one clear audience benefit and one relevant CTA per post. Measure actual follow changes and profile actions over dated snapshots instead of treating current followers divided by lifetime views as a conversion rate.',
            '- Compare posts at matched ages. Small share counts can produce unstable rates, so do not crown a winner from one tiny sample.',
            '- The pilot target is 100 total daily deliveries, initially 50 per platform. Adjust only after the first 48 live hours and sufficient mature measurements.',
            '- Assess sponsorship readiness using repeated audience quality, retention, geographic fit and a verified media kit. These data do not establish ad revenue, advertiser demand or campaign ROI.',
            '', '## Operating status', '',
            f'- Pilot start: {state.get("start_at") or "Not initialized"}.',
            f'- Confirmed pilot publications: {sum(p.get("status")=="published" for p in state["posts"].values())}.',
            '- Resolve any media-processing failures, editorial model/backlog requirements and inbox hosting before promising unattended full-volume operation.',
            '', '## Data limits', '',
            'Summed post reach is not deduplicated account reach. Facebook unique media viewers, three-second video viewers and Instagram reach have different definitions. Missing or deprecated metrics remain labeled. No historical news-carousel winner can be inferred from an inventory consisting only of reels.', '']
    directory=ROOT/'out';directory.mkdir(exist_ok=True)
    path=directory/'ceo-review.md';path.write_text('\n'.join(lines))
    keys=sorted({k for report in reports for row in report['posts'] for k in row['metrics']})
    columns=['platform','id','video_id','timestamp','media_type','media_product_type','permalink',*keys,'unavailable']
    with (directory/'historical-metrics.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
        for report in reports:
            for row in report['posts']:
                writer.writerow({**{k:row.get(k,'') for k in columns[:7]},**row['metrics'],'unavailable':';'.join(row.get('unavailable',[]))})
    return path
