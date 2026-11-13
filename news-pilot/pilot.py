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
    'Search Engine Land': 'https://searchengineland.com/feed',
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
    navy, paper, red = '#172232', '#f8f3e7', '#a3322d'
    def font(size, serif=False):
        face = 'DejaVuSerif-Bold' if serif else 'DejaVuSans'
        return ImageFont.truetype(f'/usr/share/fonts/truetype/dejavu/{face}.ttf', size)
    cards = [[item['headline'], item['deck']], *item['slides']]
    for i, (title, body) in enumerate(cards):
        im = Image.new('RGB', (1080, 1350), paper)
        d = ImageDraw.Draw(im)
        def block(value, x, y, face, fill, leading, width=884):
            line = ''
            for word in value.split():
                trial = f'{line} {word}'.strip()
                if line and d.textlength(trial, font=face) > width:
                    d.text((x,y),line,font=face,fill=fill)
                    y += leading
                    line = word
                else:
                    line = trial
            d.text((x,y),line,font=face,fill=fill)
            return y + leading
        d.text((86,58),'The Technology Brief',font=font(47,True),fill=navy)
        d.text((994,75),'13 NOV 2026',font=font(23),fill=navy,anchor='ra')
        d.line((86,133,994,133),fill=navy,width=3)
        d.text((86,178),item['section'],font=font(27),fill=red)
        y=block(title,86,251,font(70 if i==0 else 66,True),navy,86)
        d.line((86,y+24,213,y+24),fill=red,width=6)
        bottom=block(body,86,y+77,font(43),navy,64)
        if i==0:
            top=max(bottom+30,765)
            d.rectangle((86,top,994,1097),fill='#eee5d2')
            motifs={'MARKETING':('10','MARKETS IN THE EXPANSION'),
                    'ENTERPRISE AI':('1,000','QUESTIONS PER INPUT'),
                    'BIG TECH':('AI','EYEWEAR WITH GEMINI')}
            value,label=motifs[item['section']]
            d.text((128,top+40),value,font=font(125,True),fill=red)
            d.text((134,top+199),label,font=font(30),fill=navy)
        elif i==3:
            d.line((86,bottom+32,994,bottom+32),fill=red,width=3)
        d.line((86,1163,994,1163),fill=navy,width=2)
        d.text((86,1202),item['credit'],font=font(25),fill=navy)
        d.text((994,1202),f'{i+1} / 4',font=font(25),fill=red,anchor='ra')
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
