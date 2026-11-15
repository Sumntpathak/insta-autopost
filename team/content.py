"""Source-backed news and original global-English educational briefs."""
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
import hashlib
import html
import json
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from .storage import ROOT,now
from .glass_engine.engine import COLORS

FEEDS={
    'Google':'https://blog.google/rss/',
    'OpenAI':'https://openai.com/news/rss.xml',
    'GitHub':'https://github.blog/feed/',
    'Microsoft':'https://blogs.microsoft.com/feed/',
}
REELS=['memory','odd_one_out','stroop','follow_ball','squares','will_they_meet','eye_reset','breathing']


def clean(value): return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',value or ''))).strip()


def news(cfg,at):
    output=[]; errors=[]
    for publisher,url in FEEDS.items():
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'ShipStack editorial research/1.0'})
            with urllib.request.urlopen(request,timeout=20) as response: data=response.read(2_000_001)
            if len(data)>2_000_000: raise ValueError('Feed too large')
            feed=ET.fromstring(data)
            for item in feed.findall('.//item'):
                try: published=parsedate_to_datetime(item.findtext('pubDate') or '')
                except (ValueError,TypeError): continue
                if published.tzinfo is None: published=published.replace(tzinfo=timezone.utc)
                if not 0<=(at-published).total_seconds()<=cfg['news_max_age_hours']*3600: continue
                link=item.findtext('link') or ''
                if not link.startswith('https://'): continue
                title=clean(item.findtext('title'))
                if not 10<=len(title)<=240: continue
                output.append({'title':title,'source':link,'publisher':publisher,'published_at':published.isoformat(),
                               'kind':'news','fingerprint':hashlib.sha256(link.encode()).hexdigest()})
        except (OSError,ET.ParseError,ValueError) as exc: errors.append({'publisher':publisher,'error':type(exc).__name__})
    return sorted(output,key=lambda x:x['published_at'],reverse=True),errors


def reel_brief(slot,cfg):
    fmt=REELS[slot['seed']%len(REELS)]
    title,instruction,music={
      'memory':('Memory test','Remember the order','bounce'),
      'odd_one_out':('Odd one out','Find the one looking LEFT','focus'),
      'stroop':('Stroop test','Say the COLOR, not the word','focus'),
      'follow_ball':('Follow the ball','Keep your eyes on Sunny','bounce'),
      'squares':('Count the squares','Count squares of every size','focus'),
      'will_they_meet':('Will they meet?','Does Blu reach Coral?','bounce'),
      'eye_reset':('Screen break','Follow Blu gently with your eyes','calm'),
      'breathing':('A moment to pause','Breathe at your own comfortable pace','calm'),
    }[fmt]
    seed=slot['seed']
    composition={'version':1,'format':fmt,'title':title,'instruction':instruction,'cta':'How did you do?',
                 'duration':cfg['reel_seconds'],'reveal_at':cfg['reel_seconds']-3,'music':music,'seed':seed,
                 'order':[(seed//(6**i))%6 for i in range(5)],'hide_at':4,'target':seed%36,'grid_size':2+seed%4,'swaps':4+seed%5}
    return {'kind':'reel','title':title,'composition':composition,'fingerprint':hashlib.sha256(f'{fmt}:{seed}'.encode()).hexdigest(),
            'caption':f'{title}: try today’s challenge.\n\n{instruction}. The answer is revealed at the end.\n\nFollow @shipstack_ for smart tools and sharper thinking.\n#ShipStack #BrainGames #Focus'}


def authored_briefs():
    path=ROOT/'data/editorial.json'
    return json.loads(path.read_text()) if path.exists() else []


def choose(slot,cfg,state,headlines):
    if slot['format']=='reel': return reel_brief(slot,cfg)
    used={p.get('fingerprint') for p in state['posts'].values() if p.get('fingerprint')}
    today_news=sum(1 for p in state['posts'].values() if p.get('day')==slot['day'] and p.get('kind')=='news')
    if slot['format']=='carousel' and today_news<cfg['news_daily_cap']:
        candidates=[h for h in headlines if h['fingerprint'] not in used]
        if candidates:
            # News headlines become research briefs, not unchecked publishable stories.
            candidate=candidates[0]
            verified=next((b for b in authored_briefs() if b.get('source')==candidate['source'] and b.get('verified') is True),None)
            if verified: return {**verified,'kind':'news','fingerprint':candidate['fingerprint']}
            from .editor import available,draft
            if available():
                verified=draft(slot,candidate)
                return {**verified,'kind':'news','fingerprint':candidate['fingerprint']}
    for brief in authored_briefs():
        fp=hashlib.sha256((brief['title']+'|'+slot['format']).encode()).hexdigest()
        if fp not in used and brief.get('verified') is True:
            return {**brief,'kind':'education','fingerprint':fp}
    from .editor import available,draft,evergreen_candidates
    if available():
        for topic in evergreen_candidates():
            fp=hashlib.sha256((topic['title']+'|'+slot['format']).encode()).hexdigest()
            if fp not in used:
                return {**draft(slot,topic),'kind':'education','fingerprint':fp}
    return None


def quality(brief,slot):
    errors=[]
    if not brief: return ['Editorial backlog exhausted; no verified content for this slot']
    caption=brief.get('caption','')
    if not caption or len(caption)>2200: errors.append('Caption missing or exceeds Instagram limit')
    if brief.get('kind')!='reel':
        if brief.get('verified') is not True or not brief.get('source','').startswith('https://'):
            errors.append('A verified source-backed editorial item is required')
        cards=brief.get('cards',[])
        if not cards or any(not card.get('title') or not card.get('body') for card in cards):
            errors.append('Slide title or body missing')
        if any(len(card['title'])>100 or len(card['body'])>500 for card in cards):
            errors.append('Slide text too dense')
    if re.search(r'only \d+%|guaranteed|cures? anxiety|boosts? iq',caption,re.I):
        errors.append('Unsupported engagement or health claim')
    return errors


def render_cards(brief,slot,directory):
    from .glass_engine.premium import Scene
    c=reel_brief(slot,{'reel_seconds':12})['composition']; scene=Scene(c)
    cards=brief['cards'] if slot['format']=='carousel' else brief['cards'][:1]
    outputs=[]
    for n,card in enumerate(cards,1):
        scene.im=scene.bg.crop((0,0,720,900)); scene.d=ImageDraw.Draw(scene.im)
        scene.text((360,105),'S H I P S T A C K',20,(43,60,82))
        scene.text((360,171),'SMART TOOLS / SHARPER THINKING',13,(76,94,113))
        scene.glass((40,230,680,770),38)
        y=280
        def block(text,size,color,line_height):
            nonlocal y
            font=scene.font(size); words=text.split(); line=''
            for word in words:
                trial=(line+' '+word).strip()
                if scene.d.textlength(trial,font=font)>550:
                    if y>715: raise ValueError('Slide overflow; shorten editorial copy')
                    scene.d.text((85,y),line,font=font,fill=color); y+=line_height; line=word
                else: line=trial
            if y>715: raise ValueError('Slide overflow; shorten editorial copy')
            scene.d.text((85,y),line,font=font,fill=color); y+=line_height
        block(card['title'],36,(24,41,65),48); y+=40
        block(card['body'],25,(62,79,101),38)
        scene.text((360,805),f'{n:02d} / {len(cards):02d}',16,(66,86,109))
        scene.text((360,850),'Source in caption · @shipstack_',15,(75,93,112))
        # Feed cards use a consistent 4:5 canvas, independent from reel framing.
        im=scene.im.convert('RGB').resize((1080,1350),Image.Resampling.LANCZOS)
        file=directory/f'{slot["id"]}-{n}.jpg'; im.save(file,quality=95,subsampling=0); outputs.append(file)
    return outputs
