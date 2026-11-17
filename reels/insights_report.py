"""Turn the raw insights export into design decisions.

`campaign.py insights` saves Meta's per-media numbers; `state.json` knows how each reel
was made (scene, variant, length, when the winner is revealed, publish time). This joins
the two and ranks creative choices by audience response, so the next reels are designed
from evidence instead of guesses.

Rules (same as the experiment plan): missing metrics stay missing, never zero; groups
with fewer than MIN_N posts are reported but flagged as low confidence.

Usage: python reels/insights_report.py [--insights reels/out/insights.json]
           [--state reels/state.json] [--out reels/out/insights-report.md]
Read-only: no network, no API calls.
"""
import argparse
import datetime as dt
import json
import statistics
from collections import defaultdict
from pathlib import Path

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
MIN_N = 3
# Rates per reach. Shares and saves are the strongest distribution signals for Reels.
RATES = {'share_rate': 'shares', 'save_rate': 'saved', 'like_rate': 'likes', 'comment_rate': 'comments'}


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def creative(post):
    """Design attributes recorded when the reel was rendered."""
    source = post.get('source') if isinstance(post.get('source'), dict) else {}
    seconds = number(post.get('seconds')) or number(source.get('seconds'))
    reveal = number(source.get('pop_seconds')) or number(source.get('source_win_seconds'))
    attrs = {'scene': post.get('scene') or 'unknown',
             'collection': post.get('collection') or 'campaign',
             'length': None, 'reveal': None, 'hour_ist': None}
    if seconds:
        attrs['length'] = '<=15s' if seconds <= 15.5 else '16-30s' if seconds <= 30 else '>30s'
    if reveal and seconds:
        share = reveal / max(seconds, reveal)
        attrs['reveal'] = 'early (<60%)' if share < 0.6 else 'mid (60-85%)' if share < 0.85 else 'late (>=85%)'
    if post.get('published_at'):
        hour = dt.datetime.fromisoformat(post['published_at']).astimezone(IST).hour
        attrs['hour_ist'] = f'{hour // 3 * 3:02d}-{hour // 3 * 3 + 3:02d}h'
    return attrs, seconds


def rows(insights, state):
    by_media = {p['media_id']: (k, p) for k, p in state.get('posts', {}).items() if p.get('media_id')}
    out = []
    for media in insights.get('posts', []):
        if media['id'] not in by_media:
            continue  # carousels / manual posts: no creative metadata to learn from
        key, post = by_media[media['id']]
        metrics = {k: number(v) for k, v in media.get('metrics', {}).items() if number(v) is not None}
        attrs, seconds = creative(post)
        row = {'id': key, 'permalink': media.get('permalink'), **attrs, **metrics}
        reach = metrics.get('reach')
        if reach:
            for rate, metric in RATES.items():
                if metric in metrics:
                    row[rate] = metrics[metric] / reach
        watch = metrics.get('ig_reels_avg_watch_time')  # milliseconds
        if watch is not None and seconds:
            row['watch_ratio'] = watch / 1000 / seconds
        out.append(row)
    return out


def median(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def group(data, dimension):
    buckets = defaultdict(list)
    for row in data:
        if row.get(dimension) is not None:
            buckets[row[dimension]].append(row)
    table = []
    for name, items in buckets.items():
        table.append({'value': name, 'n': len(items),
                      'views': median(r.get('views') for r in items),
                      'reach': median(r.get('reach') for r in items),
                      'share_rate': median(r.get('share_rate') for r in items),
                      'save_rate': median(r.get('save_rate') for r in items),
                      'watch_ratio': median(r.get('watch_ratio') for r in items),
                      'low_confidence': len(items) < MIN_N})
    # Rank by distribution signal first (shares+saves per reach), then reach.
    def score(g):
        return ((g['share_rate'] or 0) + (g['save_rate'] or 0), g['reach'] or 0)
    return sorted(table, key=score, reverse=True)


def recommendations(data, groups):
    notes = []
    scenes = [g for g in groups['scene'] if not g['low_confidence']]
    if len(scenes) >= 2:
        best, worst = scenes[0], scenes[-1]
        notes.append(f"Make more **{best['value']}** (n={best['n']}): best shares+saves per reach. "
                     f"Retire or redesign **{worst['value']}** (n={worst['n']}).")
    watched = [r for r in data if r.get('watch_ratio') is not None]
    if watched:
        med = median(r['watch_ratio'] for r in watched)
        notes.append(f"Median watch ratio is {med:.0%} of reel length. "
                     + ("Most viewers leave before the end: move the payoff earlier and cut the tail."
                        if med < 0.6 else "Viewers mostly finish: keep the length, test a stronger loop back to frame 1."))
    reveal = [g for g in groups['reveal'] if not g['low_confidence'] and g['watch_ratio'] is not None]
    if len(reveal) >= 2:
        top = max(reveal, key=lambda g: g['watch_ratio'])
        notes.append(f"Winner reveal timed **{top['value']}** holds viewers best ({top['watch_ratio']:.0%} watched).")
    lengths = [g for g in groups['length'] if not g['low_confidence']]
    if len(lengths) >= 2:
        notes.append(f"Length with best response: **{lengths[0]['value']}**.")
    hours = [g for g in groups['hour_ist'] if not g['low_confidence'] and g['reach']]
    if len(hours) >= 2:
        notes.append(f"Highest median reach when posted at **{max(hours, key=lambda g: g['reach'])['value']} IST**.")
    if not notes:
        notes.append('Not enough matched reels with metrics yet; keep collecting daily snapshots.')
    return notes


def fmt(value, pct=False):
    if value is None:
        return 'n/a'
    return f'{value:.1%}' if pct else f'{value:,.0f}'


def render(data, collected_at):
    dims = ['scene', 'collection', 'reveal', 'length', 'hour_ist']
    groups = {d: group(data, d) for d in dims}
    lines = ['# Reel insights: what to design next', '',
             f'Snapshot: {collected_at or "unknown"} · matched reels: {len(data)} · '
             f'groups under {MIN_N} posts are marked *. Missing metrics are excluded, never counted as zero.', '',
             '## Recommendations', '']
    lines += [f'- {n}' for n in recommendations(data, groups)]
    for d in dims:
        if not groups[d]:
            continue
        lines += ['', f'## By {d}', '', '| value | n | median views | median reach | shares/reach | saves/reach | watched |',
                  '|---|---:|---:|---:|---:|---:|---:|']
        for g in groups[d]:
            lines.append(f"| {g['value']}{'*' if g['low_confidence'] else ''} | {g['n']} | {fmt(g['views'])} | "
                         f"{fmt(g['reach'])} | {fmt(g['share_rate'], True)} | {fmt(g['save_rate'], True)} | "
                         f"{fmt(g['watch_ratio'], True)} |")
    top = sorted((r for r in data if r.get('reach')), key=lambda r: (r.get('share_rate', 0) + r.get('save_rate', 0)), reverse=True)[:5]
    if top:
        lines += ['', '## Top 5 reels to study', '']
        lines += [f"- [{r['id']}]({r.get('permalink') or '#'}) · {r['scene']} · reach {fmt(r.get('reach'))} · "
                  f"shares {fmt(r.get('share_rate'), True)} · saves {fmt(r.get('save_rate'), True)}" for r in top]
    return '\n'.join(lines) + '\n', groups


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--insights', default='reels/out/insights.json')
    ap.add_argument('--state', default='reels/state.json')
    ap.add_argument('--out', default='reels/out/insights-report.md')
    args = ap.parse_args()
    insights = json.loads(Path(args.insights).read_text())
    data = rows(insights, json.loads(Path(args.state).read_text()))
    text, groups = render(data, insights.get('collected_at'))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(text)
    Path(args.out).with_suffix('.json').write_text(json.dumps({'rows': data, 'groups': groups}, indent=2))
    print(text)


if __name__ == '__main__':
    main()
