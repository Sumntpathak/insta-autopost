"""Contextual public replies. No like/follow DMs or comment prompt execution."""
from datetime import datetime,timezone
import hashlib
import re
from .storage import now,persist


def reply_text(comment,post=None):
    text=(comment or '').strip()
    if not text: return None
    lower=text.casefold()
    # Route sensitive matters, complaints and uncertain factual questions to review.
    if any(w in lower for w in ('suicide','self-harm','refund','scam','lawsuit','copyright','medical','diagnos','password','api key','access token','ignore previous','system prompt')):
        return None
    if re.search(r'https?://',text) or len(text)>500: return None
    if any(w in lower for w in ('thanks','thank you','love this','awesome','great','nice')):
        return 'Glad you enjoyed it! What would you like to try next?'
    if re.fullmatch(r'[1-6]|cup\s*[1-3]|yes|no|a|b',lower):
        return 'Thanks for playing! Compare your guess with the reveal at the end.'
    if any(w in lower for w in ('follow','subscribe')):
        return 'Follow @shipstack_ for smart tools, useful explainers and fresh brain games.'
    if any(w in lower for w in ('source','link')) and post and post.get('source'):
        return 'The source is linked in the caption so you can check the original announcement.'
    # Unknown language or question is held instead of a confident invented answer.
    return None


def reply_key(platform,comment_id):
    return hashlib.sha256(f'{platform}:comment:{comment_id}'.encode()).hexdigest()


def handle(client,platform,comment,post,state,cfg,at):
    key=reply_key(platform,comment['id'])
    if key in state['replies']: return 'already_handled'
    author=comment.get('from',{})
    if str(author.get('id'))==str(client.id) or author.get('username','').casefold()==cfg['instagram_account'].casefold():
        return 'self'
    stamp=comment.get('timestamp',comment.get('created_time'))
    if not stamp: return 'missing_timestamp'
    created=datetime.fromisoformat(stamp.replace('Z','+00:00'))
    start=datetime.fromisoformat(state['start_at']) if state.get('start_at') else at
    if created<start: return 'before_pilot'
    text=reply_text(comment.get('text',comment.get('message','')),post)
    record={'platform':platform,'comment_id':comment['id'],'media_id':post.get('media_id'),
            'status':'needs_review' if text is None else 'replying','at':at.isoformat()}
    state['replies'][key]=record; persist(state)
    if text is None: return 'needs_review'
    try:
        result=client.comment(comment['id'],text)
    except Exception:
        record['status']='uncertain'; persist(state)
        raise
    record.update(status='replied',reply_id=str(result)); persist(state)
    return 'replied'


def poll(clients,state,cfg,at):
    if not cfg['enabled'] or not cfg['auto_replies'] or not state.get('start_at'): return {'active':False}
    start=datetime.fromisoformat(state['start_at'])
    if not 0<=(at-start).total_seconds()<cfg['pilot_days']*86400:return {'active':False}
    counts={}; handled=0
    posts=[p for p in state['posts'].values() if p.get('status')=='published' and p.get('media_id')]
    # Rotate the inspected post batch; retain comment-level idempotency across runs.
    cursor=state.get('community_cursor',0)
    selected=(posts[cursor:]+posts[:cursor])[:20] if posts else []
    state['community_cursor']=(cursor+len(selected))%len(posts) if posts else 0
    for post in selected:
        platform=post['platform']; client=clients[platform]
        fields='id,text,timestamp,from' if platform=='instagram' else 'id,message,created_time,from'
        for comment in client.pages(post['media_id']+'/comments',{'fields':fields,'limit':100}):
            if handled>=cfg['max_replies_per_cycle']: break
            result=handle(client,platform,comment,post,state,cfg,at)
            counts[result]=counts.get(result,0)+1
            if result in ('replied','needs_review'): handled+=1
    persist(state)
    return {'active':True,'counts':counts,'coverage':'Rotating polling batch, not an instantaneous guarantee of every comment'}
