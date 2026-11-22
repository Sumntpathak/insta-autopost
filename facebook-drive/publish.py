"""Post purchased clips from Google Drive to the ShipStack Facebook Page, one per run.

Safety rules (same as AGENTS.md): dry run by default; the posting guard (60 min gap, 12/day,
counted on this pipeline's own journal) must pass; the journal is pushed BEFORE the Reel is
published; an ambiguous result (journal says `publishing`) is never retried automatically.

    python facebook-drive/publish.py                     # dry run: checks everything, posts nothing
    python facebook-drive/publish.py --publish           # post the next clip if the guard allows
    python facebook-drive/publish.py --scheduled --publish   # same, but only if queue.json enabled
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(ROOT / 'reels'), str(ROOT / 'reels' / 'pythonic')]
import guard  # noqa: E402

QUEUE = HERE / 'queue.json'
STATE = HERE / 'state.json'
MIN_SECONDS, MAX_SECONDS = 3, 90
DRIVE = 'https://drive.usercontent.google.com/download?id={}&export=download'


class Blocked(RuntimeError):
    """Posting must not continue; the message says why."""


def read_state(path=None):
    path = path or STATE
    return json.loads(path.read_text()) if path.exists() else {'posts': {}}


def persist(state):
    """Save the journal and push it. Fails closed: if the push fails, nothing is published."""
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2) + '\n')
    tmp.replace(STATE)
    if not os.environ.get('GITHUB_ACTIONS'):
        return
    subprocess.run(['git', 'add', str(STATE)], check=True)
    if subprocess.run(['git', 'diff', '--cached', '--quiet']).returncode == 0:
        return
    subprocess.run(['git', 'commit', '-m', 'Record Facebook Drive clip state'], check=True)
    branch = os.environ['GITHUB_REF_NAME']
    for attempt in range(4):
        if subprocess.run(['git', 'push', 'origin', f'HEAD:{branch}']).returncode == 0:
            return
        subprocess.run(['git', 'pull', '--rebase', 'origin', branch], check=True)
    raise Blocked('could not push the journal; not publishing')


def fetch(item, dest):
    """Download from Drive and require the exact file that was reviewed."""
    request = urllib.request.Request(DRIVE.format(item['drive_id']))
    with urllib.request.urlopen(request, timeout=180) as response:
        dest.write_bytes(response.read())
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    if digest != item['sha256']:
        raise Blocked(f"{item['id']}: downloaded file does not match the reviewed hash")
    return digest


def probe(path):
    """H.264 + audio, vertical, 3-90 s (Facebook Reel limits). Raises Blocked otherwise."""
    out = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,codec_name,width,height',
         '-show_entries', 'format=duration', '-of', 'json', str(path)],
        capture_output=True, text=True, check=True).stdout
    info = json.loads(out)
    video = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)
    audio = next((s for s in info['streams'] if s['codec_type'] == 'audio'), None)
    seconds = float(info['format']['duration'])
    if not video or video['codec_name'] != 'h264' or not audio:
        raise Blocked('needs H.264 video with an audio track')
    if video['height'] < video['width'] * 1.7:
        raise Blocked('needs vertical 9:16 video')
    if not MIN_SECONDS <= seconds <= MAX_SECONDS:
        raise Blocked(f'{seconds:.1f}s is outside the {MIN_SECONDS}-{MAX_SECONDS}s Reel range')
    return {'seconds': round(seconds, 1), 'width': video['width'], 'height': video['height']}


def next_item(queue, state):
    posts = state['posts']
    stuck = [k for k, p in posts.items() if p.get('status') == 'publishing']
    if stuck:
        raise Blocked(f"{stuck[0]} is in 'publishing' state; reconcile it by hand from its video id")
    for item in queue['items']:
        if item.get('skip_reason'):
            continue
        if posts.get(item['id'], {}).get('status') == 'published':
            continue
        return item
    return None


def publish_next(queue, state, fb, now, publish=False, persist=persist, fetch=fetch, probe=probe, workdir=None,
                 clock=lambda: dt.datetime.now(guard.IST)):
    """Return a one-line result. Posts at most one clip."""
    item = next_item(queue, state)
    if item is None:
        return 'nothing left to post'
    reason = guard.blocked(state['posts'], now)
    if reason:
        return f'waiting: {reason}'
    workdir = Path(workdir or HERE / 'tmp')
    workdir.mkdir(exist_ok=True)
    clip = workdir / f"{item['id']}.mp4"
    digest = fetch(item, clip)
    duplicate = next((k for k, p in state['posts'].items()
                      if p.get('content_sha256') == digest and p.get('status') == 'published'), None)
    if duplicate:
        raise Blocked(f"{item['id']} is identical to already-published {duplicate}")
    details = probe(clip)
    if not publish:
        return f"dry run ok: would post {item['id']} {details}"
    video = fb.upload(clip)  # creates an unpublished container; nothing is public yet
    record = {'id': item['id'], 'drive_id': item['drive_id'], 'content_sha256': digest,
              'caption': item['caption'], 'status': 'publishing', 'video_id': video,
              'attempted_at': now.isoformat(), **details}
    state['posts'][item['id']] = record
    persist(state)  # journal is pushed BEFORE the publish call
    fb.finish(video, item['caption'])  # raises on an uncertain result; never retried
    record.update(status='published', published_at=clock().isoformat())
    persist(state)
    return f"published {item['id']} as video {video}"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--scheduled', action='store_true')
    args = parser.parse_args(argv)
    queue = json.loads(QUEUE.read_text())
    if args.scheduled and not queue.get('enabled'):
        print('queue disabled (enabled=false); nothing to do')
        return 0
    from facebook import Facebook
    fb = Facebook()
    if fb.check().get('name', '').casefold() != 'shipstack':
        raise Blocked('Facebook Page did not match ShipStack')
    state = read_state()
    try:
        print(publish_next(queue, state, fb, dt.datetime.now(guard.IST), publish=args.publish))
    except Blocked as exc:
        print('BLOCKED:', exc)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
