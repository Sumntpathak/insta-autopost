"""Publish ten original climb episodes and reconcile prior attempts by video ID."""
import datetime as dt
import json
import os
from pathlib import Path
import time

from campaign import IST, persist, read_state
from facebook import Facebook

PAGE = '1390488964137653'


def main():
    os.environ['FB_PAGE_ID'] = PAGE
    fb = Facebook()
    if fb.check().get('name', '').casefold() != 'shipstack':
        raise RuntimeError('Unexpected Facebook destination')
    items = json.loads(Path('climb-pilot/batch.json').read_text())
    state = read_state()
    posts = state['posts']
    for item in items:
        key = item['id']
        record = posts.get(key)
        if record and record['facebook']['status'] == 'published':
            continue
        if record:
            video = record['facebook']['video_id']
        else:
            video = fb.upload(Path('climb-output') / (key + '.mp4'))
            now = dt.datetime.now(IST).isoformat()
            record = {**item, 'status': 'facebook_only',
                      'facebook': {'video_id': video, 'status': 'publishing', 'attempted_at': now}}
            posts[key] = record
            persist(state)
            try:
                fb.finish(video, item['caption'])
            except RuntimeError as error:
                print(f'{key}: {error}', flush=True)

        for _ in range(6):
            try:
                status = fb.call(video, {'fields': 'status'}).get('status', {})
                if status.get('publishing_phase', {}).get('publish_status') == 'published':
                    record['facebook'].update(status='published', published_at=dt.datetime.now(IST).isoformat())
                    persist(state)
                    print(f'FACEBOOK_PUBLISHED {key} {video}', flush=True)
                    break
            except RuntimeError as error:
                print(f'{key}: {error}', flush=True)
            time.sleep(4)
        if record['facebook']['status'] != 'published':
            print(f'Publication unconfirmed for {key}: {video}', flush=True)
        if item is not items[-1]:
            time.sleep(15)
    count = sum(posts.get(item['id'], {}).get('facebook', {}).get('status') == 'published' for item in items)
    print(f'Confirmed {count}/{len(items)}', flush=True)
    if count != len(items):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
