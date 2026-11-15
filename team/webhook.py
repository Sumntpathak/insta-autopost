"""Signed Meta messaging inbox and durable worker; requires a hosted HTTPS service.

Run the WSGI app behind TLS using gunicorn team.webhook:application.
Run `python -m team.webhook` as a separate worker on the same persistent volume.
Never upload the private inbox database as a GitHub artifact.
"""
from datetime import datetime,timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3
import time
import urllib.parse
from .community import reply_text
from .platforms import Instagram,Facebook
from .storage import config,read,now


def database():
    path=Path(os.environ.get('SHIPSTACK_INBOX_DB','team/out/private-inbox.sqlite3'))
    path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=15)
    db.execute('CREATE TABLE IF NOT EXISTS inbox (id TEXT PRIMARY KEY, payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT "pending", received_at TEXT NOT NULL)')
    db.commit(); return db


def signature_ok(body,signature,secret):
    if not secret or not signature: return False
    expected='sha256='+hmac.new(secret.encode(),body,hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature,expected)


def application(environ,start_response):
    def respond(status,text):
        start_response(status,[('Content-Type','text/plain'),('Cache-Control','no-store')]); return [text.encode()]
    if environ.get('PATH_INFO') not in ('/webhook','/'):
        return respond('404 Not Found','Not found')
    if environ.get('REQUEST_METHOD')=='GET':
        q=urllib.parse.parse_qs(environ.get('QUERY_STRING',''))
        actual=q.get('hub.verify_token',[''])[0]; expected=os.environ.get('META_WEBHOOK_VERIFY_TOKEN','')
        if expected and q.get('hub.mode')==['subscribe'] and hmac.compare_digest(actual,expected):
            return respond('200 OK',q.get('hub.challenge',[''])[0])
        return respond('403 Forbidden','Verification failed')
    if environ.get('REQUEST_METHOD')!='POST': return respond('405 Method Not Allowed','POST required')
    try: size=int(environ.get('CONTENT_LENGTH') or '0')
    except ValueError:return respond('400 Bad Request','Invalid length')
    if not 0<size<=1_000_000:return respond('413 Payload Too Large','Invalid size')
    body=environ['wsgi.input'].read(size)
    secret=os.environ.get('META_APP_SECRET','')
    if not secret:return respond('503 Service Unavailable','Webhook secret is not configured')
    if not signature_ok(body,environ.get('HTTP_X_HUB_SIGNATURE_256',''),secret):
        return respond('403 Forbidden','Invalid signature')
    cfg=config(); state=read()
    if not cfg['enabled'] or not state.get('start_at'):return respond('200 OK','PILOT_INACTIVE')
    start=datetime.fromisoformat(state['start_at'])
    if not 0<=(now()-start).total_seconds()<cfg['pilot_days']*86400:return respond('200 OK','PILOT_INACTIVE')
    try: payload=json.loads(body)
    except ValueError:return respond('400 Bad Request','Invalid JSON')
    if not isinstance(payload,dict) or not isinstance(payload.get('entry',[]),list):
        return respond('400 Bad Request','Invalid event')
    with database() as db:
        for entry in payload.get('entry',[]):
            if not isinstance(entry,dict):continue
            for event in entry.get('messaging',[]):
                if not isinstance(event,dict):continue
                mid=event.get('message',{}).get('mid')
                if not mid:continue
                envelope={'object':payload.get('object'),'account':str(entry.get('id','')),'event':event}
                key=hashlib.sha256((envelope['account']+':'+mid).encode()).hexdigest()
                db.execute('INSERT OR IGNORE INTO inbox(id,payload,received_at) VALUES(?,?,?)',
                           (key,json.dumps(envelope),now().isoformat()))
    return respond('200 OK','EVENT_RECEIVED')


def handle(envelope,cfg,at):
    event=envelope['event']; message=event.get('message',{})
    if message.get('is_echo') or not message.get('text'): return 'ignored'
    stamp=event.get('timestamp')
    if not isinstance(stamp,(int,float)):return 'needs_review'
    age=(at-datetime.fromtimestamp(stamp/1000,timezone.utc)).total_seconds()
    if not 0<=age<24*3600:return 'outside_messaging_window'
    if envelope.get('object')=='instagram': client=Instagram(); expected=cfg['instagram_account']
    elif envelope.get('object')=='page': client=Facebook(); expected=cfg['facebook_page_name']
    else:return 'unsupported_object'
    if envelope['account']!=client.id or str(event.get('recipient',{}).get('id',''))!=client.id:
        return 'account_mismatch'
    sender=str(event.get('sender',{}).get('id',''))
    if not sender or sender==client.id:return 'ignored'
    text=message['text'].strip()
    if text.casefold() in ('stop','unsubscribe','do not contact me'):return 'opt_out'
    reply=reply_text(text)
    if text.casefold() in ('hi','hello','hey'):
        reply='Hi! Welcome to ShipStack. Which tool or brain game would you like help with?'
    if reply is None:return 'needs_review'
    client.check(expected)
    client.call(client.id+'/messages',{'recipient':json.dumps({'id':sender}),'message':json.dumps({'text':reply})},'POST')
    return 'replied'


def consume_once():
    cfg=config(); state=read()
    if not cfg['enabled'] or not cfg['auto_dm'] or not state.get('start_at'):return 0
    start=datetime.fromisoformat(state['start_at'])
    if not 0<=(now()-start).total_seconds()<cfg['pilot_days']*86400:return 0
    handled=0
    with database() as db:
        from datetime import timedelta
        db.execute('DELETE FROM inbox WHERE received_at < ?',((now()-timedelta(days=7)).isoformat(),))
        rows=db.execute('SELECT id,payload FROM inbox WHERE status="pending" ORDER BY received_at LIMIT 20').fetchall()
        for key,payload in rows:
            claimed=db.execute('UPDATE inbox SET status="replying" WHERE id=? AND status="pending"',(key,))
            db.commit()
            if claimed.rowcount!=1:continue
            try: status=handle(json.loads(payload),cfg,now())
            except Exception: status='uncertain'
            # Keep reviewable/uncertain messages briefly on private durable storage.
            retained=payload if status in ('needs_review','uncertain') else '{}'
            db.execute('UPDATE inbox SET status=?,payload=? WHERE id=?',(status,retained,key)); db.commit(); handled+=1
    return handled


if __name__=='__main__':
    while True:
        consume_once(); time.sleep(5)
