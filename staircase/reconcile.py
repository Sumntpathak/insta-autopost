import datetime as dt
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, 'reels')
import campaign

meta = campaign.Meta()
meta.check_account()
state = campaign.read_state()
batch = json.load(open('staircase/batch.json'))['items']
recent = meta.call(f'{meta.ig_id}/media', {'fields': 'id,caption,permalink', 'limit': 100}).get('data', [])
try:
    quota = meta.call(f'{meta.ig_id}/content_publishing_limit', {'fields': 'quota_usage,config'})
    print('Publishing quota:', quota, flush=True)
except RuntimeError as error:
    print('Publishing quota unavailable:', error, flush=True)
for item in batch:
    record = state['posts'].get(item['id'])
    if not record or record['status'] == 'published':
        continue
    matches = [p for p in recent if p.get('caption', '').strip() == item['caption'].strip()]
    if len(matches) == 1:
        record.update(status='published', media_id=matches[0]['id'])
        campaign.persist(state)
        print(item['id'], 'already visible', flush=True)
        continue
    if matches:
        print(item['id'], 'multiple matches', flush=True)
        break
    container = record['container_id']
    status = meta.call(container, {'fields': 'status_code'}).get('status_code')
    print(item['id'], 'container', status, flush=True)
    if status != 'FINISHED':
        break
    request = urllib.request.Request(
        meta.api + f'{meta.ig_id}/media_publish',
        data=urllib.parse.urlencode({'creation_id': container}).encode(),
        headers={'Authorization': 'Bearer ' + meta.token}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            media = json.load(response)['id']
    except urllib.error.HTTPError as error:
        detail = json.load(error).get('error', {})
        fields = {key: detail[key] for key in ('code', 'error_subcode', 'is_transient') if key in detail}
        for key in ('message', 'error_user_title', 'error_user_msg'):
            value = detail.get(key, '')
            if isinstance(value, str) and 'http' not in value and meta.token not in value:
                fields[key] = value[:500]
        print(item['id'], 'publish rejected', error.code, json.dumps(fields), flush=True)
        break
    record.update(status='published', media_id=media, published_at=dt.datetime.now(campaign.IST).isoformat())
    campaign.persist(state)
    print(item['id'], 'published', media, flush=True)
print('Confirmed', sum(state['posts'].get(i['id'], {}).get('status') == 'published' for i in batch), 'of', len(batch), flush=True)
