"""One-month Reel experiment. No tokens required for planning or rendering."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = Path(__file__).resolve().parent
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
CONFIG = json.loads((HERE / 'config.json').read_text())
STATE = HERE / 'state.json'


def read_state():
    return json.loads(STATE.read_text())


def save(state):
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2) + '\n')
    tmp.replace(STATE)


def persist(state):
    """Push the journal BEFORE any publish attempt; fail closed on persistence failure."""
    save(state)
    subprocess.run(['git', 'add', 'reels/state.json'], check=True)
    changed = subprocess.run(['git', 'diff', '--cached', '--quiet'], check=False)
    if changed.returncode == 0:
        return
    subprocess.run(['git', 'commit', '-m', 'Record reel campaign state'], check=True)
    subprocess.run(['git', 'pull', '--rebase'], check=True)
    subprocess.run(['git', 'push'], check=True)


def active(state, now):
    if not state.get('start_date'):
        return False
    start = dt.date.fromisoformat(state['start_date'])
    return start <= now.date() < start + dt.timedelta(days=CONFIG['days'])


def plan(state, now):
    if CONFIG.get('paused', False) or not active(state, now):
        return None
    day = (now.date() - dt.date.fromisoformat(state['start_date'])).days
    for index, slot in enumerate(CONFIG['slots_ist']):
        hour, minute = map(int, slot.split(':'))
        due = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        key = f"R-{state['start_date']}-{day+1:02d}-{index+1:02d}"
        # Uncertain publish attempts also consume the slot. Never retry them blindly.
        if due <= now and key not in state['posts']:
            scene = CONFIG['scenes'][(day + index) % len(CONFIG['scenes'])]
            seed = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
            return {'id': key, 'date': now.date().isoformat(), 'slot': slot,
                    'scene': scene, 'seed': seed, 'caption': caption(scene, day, index)}
    return None


def caption(scene, day, index):
    hooks = {
        'spinner': ['One bounce. One more ball. Watch the circle fill.', 'What happens when every bounce adds another ball?'],
        'orbit': ['One circle. Hundreds of collisions.', 'Watch one ball become a crowd.'],
        'splitter': ['Three paddles. One growing cloud of color.', 'Can you follow one ball through the chaos?'],
        'ballPool': ['Tiny collisions, unexpected patterns.', 'Can you follow just one ball?'],
        'newtonsCradle': ['Watch where the energy goes.', 'One small push sets everything moving.'],
        'avalanche': ['Every collision changes the path.', 'A simple path becomes beautiful chaos.'],
        'restitution': ['Which shape bounces the longest?', 'Same gravity. Different bounce.'],
        'chains': ['Watch the ripple travel.', 'A small movement changes the whole chain.'],
    }
    return hooks[scene][(day + index//len(CONFIG['scenes'])) % 2] + '\n\nPhysics simulations · @shipstack_\n#physics #simulation #satisfying'


class Meta:
    def __init__(self):
        self.token = os.environ['META_TOKEN'].strip()
        self.ig_id = os.environ['IG_USER_ID'].strip()
        self.api = ('https://graph.instagram.com/' if self.token.startswith('IG')
                    else 'https://graph.facebook.com/') + 'v23.0'

    def call(self, path, data=None, method='GET'):
        query = urllib.parse.urlencode(data or {})
        url = f'{self.api}/{path}' + ('?' + query if method == 'GET' and query else '')
        req = urllib.request.Request(url, data=query.encode() if method == 'POST' else None,
                                     headers={'Authorization': f'Bearer {self.token}'}, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            # Never log response bodies: upstream errors can contain credentials/URLs.
            raise RuntimeError(f'Meta HTTP {error.code} on {path}') from None

    def check_account(self):
        me = self.call(self.ig_id, {'fields': 'username'})
        if me.get('username', '').lower() != CONFIG['account'].lower():
            raise RuntimeError('IG_USER_ID does not match the configured account')
        return me

    def ready(self, container):
        for _ in range(60):
            status = self.call(container, {'fields': 'status_code'}).get('status_code')
            if status == 'FINISHED':
                return
            if status in ('ERROR', 'EXPIRED'):
                raise RuntimeError(f'Reel container is {status}')
            time.sleep(5)
        raise RuntimeError('Reel processing timed out')


def publish(item, url):
    if not url.startswith('https://'):
        raise ValueError('A public HTTPS video URL is required')
    state = read_state()
    now = dt.datetime.now(IST)
    expected = plan(state, now)
    if not expected or expected['id'] != item['id']:
        raise RuntimeError('Slot is no longer due or has already been attempted')
    meta = Meta()
    meta.check_account()
    container = meta.call(f'{meta.ig_id}/media', {'media_type': 'REELS', 'video_url': url,
                              'caption': item['caption'], 'share_to_feed': 'true'}, 'POST')['id']
    meta.ready(container)
    state['posts'][item['id']] = dict(item, container_id=container,
                                   status='publishing', attempted_at=now.isoformat())
    persist(state)
    # An ambiguous timeout is intentionally NOT retried. Reconcile using container_id.
    media = meta.call(f'{meta.ig_id}/media_publish', {'creation_id': container}, 'POST')['id']
    state['posts'][item['id']].update(status='published', media_id=media,
                                      published_at=dt.datetime.now(IST).isoformat())
    persist(state)
    print(f"Published {item['id']} as {media}")


def insights(output):
    meta = Meta()
    account = meta.check_account()
    report = {'collected_at': dt.datetime.now(IST).isoformat(), 'account': account,
              'metrics': ['views', 'reach', 'saved', 'shares', 'likes', 'comments'], 'posts': []}
    # Include the existing carousels as a baseline, plus any campaign reels.
    media = meta.call(f'{meta.ig_id}/media', {'fields': 'id,caption,media_type,media_product_type,timestamp,permalink', 'limit': 100})
    for post in media.get('data', []):
        row = {**post, 'metrics': {}, 'unavailable': []}
        try:
            results = meta.call(f"{post['id']}/insights", {'metric': ','.join(report['metrics'])}).get('data', [])
        except RuntimeError:
            results = []
            for metric in report['metrics']:
                try:
                    results.extend(meta.call(f"{post['id']}/insights", {'metric': metric}).get('data', []))
                except RuntimeError:
                    pass
        for entry in results:
            value = entry.get('total_value', {}).get('value')
            if value is None:
                values = entry.get('values', [])
                value = values[0].get('value') if values else None
            if value is not None:
                row['metrics'][entry['name']] = value
        row['unavailable'] = [m for m in report['metrics'] if m not in row['metrics']]
        report['posts'].append(row)
    report['coverage'] = 'Most recent 100 media; point-in-time metrics, not a complete 300-post campaign report'
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(report, indent=2))
    print(f"Saved insights for {len(report['posts'])} recent media. Unavailable metrics remain missing, never zero.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['start', 'plan', 'publish', 'insights', 'check', 'active'])
    parser.add_argument('--date')
    parser.add_argument('--item', default='reels/out/item.json')
    parser.add_argument('--url')
    parser.add_argument('--output', default='reels/out/insights.json')
    args = parser.parse_args()
    state = read_state()
    now = dt.datetime.now(IST)
    if args.mode == 'start':
        if state.get('start_date'):
            raise RuntimeError('Campaign already initialized; refusing to reset posting history')
        start = dt.date.fromisoformat(args.date) if args.date else now.date() + dt.timedelta(days=1)
        if start < now.date():
            raise ValueError('Start date cannot be in the past')
        state['start_date'] = start.isoformat()
        persist(state)
        print(f"Campaign starts {start}: {CONFIG['days']} days, {CONFIG['daily_target']} reels/day")
    elif args.mode == 'active':
        print('true' if active(state, now) else 'false')
    elif args.mode == 'plan':
        item = plan(state, now)
        Path(args.item).parent.mkdir(parents=True, exist_ok=True)
        Path(args.item).write_text(json.dumps(item, indent=2))
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
                out.write(f"due={'true' if item else 'false'}\n")
                if item:
                    for k in ('id', 'scene', 'seed'):
                        out.write(f'{k}={item[k]}\n')
        print(json.dumps(item))
    elif args.mode == 'publish':
        publish(json.loads(Path(args.item).read_text()), args.url or '')
    elif args.mode == 'insights':
        insights(args.output)
    elif args.mode == 'check':
        print(Meta().check_account())


if __name__ == '__main__':
    main()
