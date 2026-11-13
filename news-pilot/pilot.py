import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import urllib.request
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
DATE = '2026-11-13'
TAG = 'technology-brief-' + DATE
FEEDS = {
    'Google': 'https://blog.google/rss/',
    'AWS': 'https://aws.amazon.com/about-aws/whats-new/recent/feed/',
    'OpenAI': 'https://openai.com/news/rss.xml',
    'Search Engine Journal': 'https://www.searchenginejournal.com/feed/',
    'Marketing Dive': 'https://www.marketingdive.com/feeds/news/',
}

def scan():
    for name, url in FEEDS.items():
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'Technology Brief news monitor/1.0'})
            with urllib.request.urlopen(request, timeout=12) as response:
                feed = ET.fromstring(response.read(3_000_000))
            print(json.dumps({'feed': name, 'headlines': [
                {'title': item.findtext('title'), 'url': item.findtext('link'), 'date': item.findtext('pubDate')}
                for item in feed.findall('.//item')[:5]
            ]}))
        except (OSError, ET.ParseError) as error:
            print(f'{name}: {type(error).__name__}')

def render(item, directory):
    directory.mkdir(parents=True, exist_ok=True)
    ink, paper, muted, accent = '#171a17', '#f7f4eb', '#4e544a', '#c32d22'
    def font(size, serif=False, bold=False):
        family = 'Serif' if serif else 'Sans'
        suffix = '-Bold' if bold else ''
        return ImageFont.truetype(f'/usr/share/fonts/truetype/dejavu/DejaVu{family}{suffix}.ttf',size)

    cover_titles = {'ENTERPRISE AI':'Google’s API for 1,000 decisions',
                    'BIG TECH':'Google puts Gemini in glasses',
                    'MARKETING':'Ads enter Google’s AI search'}
    cards = [[cover_titles.get(item['section'], item['headline']),item['deck']], *item['slides']]
    for i,(title,body) in enumerate(cards):
        im = Image.new('RGB',(1080,1350),paper)
        d = ImageDraw.Draw(im)
        def block(value,x,y,face,fill,leading,width=936):
            line = ''
            for word in value.split():
                trial = f'{line} {word}'.strip()
                if line and d.textlength(trial,font=face)>width:
                    d.text((x,y),line,font=face,fill=fill)
                    y += leading
                    line = word
                else:
                    line = trial
            d.text((x,y),line,font=face,fill=fill)
            return y + leading
        d.text((72,54),'The Technology Brief',font=font(51,True,True),fill=ink)
        d.text((1008,81),'13 NOV 2026',font=font(24),fill=muted,anchor='ra')
        d.line((72,140,1008,140),fill=ink,width=3)
        d.text((72,174),item['section'],font=font(25,bold=True),fill=accent)
        y = block(title,72,230,font(89 if i==0 else 76,True,True),ink,101 if i==0 else 89)
        if i == 0:
            block(body,74,y+17,font(37),muted,51)
            d.rectangle((72,615,1008,1165),fill='#dbe2d2')
            if item['section']=='BIG TECH':
                d.ellipse((320,650,778,1108),fill='#eab56e')
                d.rounded_rectangle((160,795,487,1005),radius=78,fill='#f6e3ac',outline=ink,width=22)
                d.rounded_rectangle((594,795,921,1005),radius=78,fill='#f6e3ac',outline=ink,width=22)
                d.arc((470,827,610,930),195,345,fill=ink,width=18)
                d.line((162,815,106,761),fill=ink,width=21)
                d.line((918,815,974,761),fill=ink,width=21)
                for x in (244,677):
                    d.line((x,950,x+105,841),fill='#fff6d6',width=17)
                d.ellipse((873,820,896,843),fill=accent)
            else:
                value,label = ('1,000','QUESTIONS PER INPUT') if item['section']=='ENTERPRISE AI' else ('10','MARKETS IN THE EXPANSION')
                for x in range(120,975,44):
                    for yy in range(652,1112,44):
                        d.ellipse((x,yy,x+6,yy+6),fill='#a9b4a4')
                d.rectangle((117,733,959,1049),fill='#dbe2d2')
                d.text((540,871),value,font=font(248,True,True),fill=ink,anchor='mm')
                d.text((540,1034),label,font=font(29,bold=True),fill=accent,anchor='mm')
        elif i == 3:
            d.rectangle((72,520,1008,1130),fill='#dbe2d2')
            sentences = body.rstrip('.').split('. ')
            y = 571
            for n,sentence in enumerate(sentences,1):
                d.text((111,y),f'{n:02}',font=font(37,True,True),fill=accent)
                y = block(sentence+'.',203,y,font(39),ink,52,755)+34
                if n<len(sentences):
                    d.line((111,y-16,963,y-16),fill='#99a395',width=2)
        else:
            d.line((72,y+23,222,y+23),fill=accent,width=6)
            block(body,72,y+80,font(52),ink,72)
        d.line((72,1211,1008,1211),fill=ink,width=2)
        d.text((72,1249),item['credit'],font=font(25),fill=muted)
        d.text((1008,1249),f'{i+1} / 4',font=font(25,bold=True),fill=accent,anchor='ra')
        im.save(directory / f"{item['id']}-{i+1}.jpg",quality=94,subsampling=0)

def publish(item):
    from campaign import IST, Meta, persist, read_state
    state = read_state()
    key = item['id']
    if key in state['posts']:
        return
    meta = Meta()
    meta.check_account()
    directory = ROOT / 'out'
    render(item,directory)
    repo = os.environ['GITHUB_REPOSITORY']
    if subprocess.run(['gh','release','view',TAG],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
        subprocess.run(['gh','release','create',TAG,'--title','Technology Brief | 13 Nov 2026','--latest=false'],check=True)
    files = sorted(directory.glob(f'{key}-*.jpg'))
    subprocess.run(['gh','release','upload',TAG,*map(str,files),'--clobber'],check=True)
    children=[]
    for file in files:
        url=f'https://github.com/{repo}/releases/download/{TAG}/{file.name}'
        child=meta.call(f'{meta.ig_id}/media',{'image_url':url,'is_carousel_item':'true'},'POST')['id']
        meta.ready(child)
        children.append(child)
    caption=f"{item['headline']}\n\n{item['deck']}\n\n{item['slides'][-1][1]}\n\nSources\n" + '\n'.join(item['sources'])
    parent=meta.call(f'{meta.ig_id}/media',{'media_type':'CAROUSEL','children':','.join(children),'caption':caption},'POST')['id']
    meta.ready(parent)
    record=dict(id=key,date=DATE,scene='technology-brief',caption=caption,status='publishing',
                container_id=parent,attempted_at=dt.datetime.now(IST).isoformat())
    state['posts'][key]=record
    persist(state)
    media=meta.call(f'{meta.ig_id}/media_publish',{'creation_id':parent},'POST')['id']
    record.update(status='published',media_id=media,published_at=dt.datetime.now(IST).isoformat())
    persist(state)
    print(f'{key} published as {media}')

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['scan','publish','preview'])
    mode=parser.parse_args().mode
    editions=json.loads((ROOT/'editions.json').read_text())
    if mode=='preview':
        for item in editions:
            render(item,ROOT/'out')
    else:
        from campaign import IST, read_state
        now=dt.datetime.now(IST)
        if now.date().isoformat()==DATE:
            if mode=='scan':
                scan()
            else:
                posts=read_state()['posts']
                for item in editions:
                    if item['id'] not in posts and item['time']<=now.strftime('%H:%M'):
                        publish(item)
                        break
