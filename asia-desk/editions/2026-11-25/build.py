import json
from pathlib import Path
from PIL import Image
from render import frame
ROOT=Path(__file__).resolve().parent
stories=[
dict(desk='JAPAN',source='The Japan Times / Bloomberg',label='INFLATION',headline='BOJ measure shows underlying inflation accelerating',deck='October’s reading rose to 3.5%, Wednesday’s report says.',url='https://www.japantimes.co.jp/business/2026/11/25/economy/boj-inflation-indicator-hike/',time='25 Nov · Date only · JST',published='2026-11-25',updated=None,timezone='Asia/Tokyo',precision='date',listing='https://www.japantimes.co.jp/latest-news/?pgno=1',position=2),
dict(desk='SOUTH KOREA',source='The Korea Herald',label='MARKETS',headline='Kospi drops 6.16% as volatility returns',deck='The index closed at 4,697.51 on Wednesday, reversing Tuesday’s rebound. The Herald examines renewed selling pressure and uncertainty surrounding the AI sector.',url='https://www.koreaherald.com/article/10949157',time='25 Nov · 17:02 KST · Updated',published='2026-11-25T15:22:09+09:00',updated='2026-11-25T17:02:32+09:00',timezone='Asia/Seoul',precision='second',listing='https://www.koreaherald.com/',position=1),
dict(desk='HONG KONG',source='South China Morning Post',label='PUBLIC AUDIT',headline='Audit flags Consumer Council performance gaps',deck='The watchdog missed complaint-handling targets from 2021 to 2025, an audit released Wednesday found. The review also identified shortfalls in product testing and consumer studies.',url='https://www.scmp.com/news/hong-kong/society/article/3375770/consumer-council-missed-targets-handling-complaints-product-tests-audit',time='25 Nov · 18:34 HKT · Updated',published='2026-11-25T18:31:00+08:00',updated='2026-11-25T18:34:00+08:00',timezone='Asia/Hong_Kong',precision='minute',listing='https://www.scmp.com/news/hong-kong',position=3),
dict(desk='SINGAPORE',source='The Straits Times',label='NEWS ANALYSIS',headline='Analysis: StarHub–M1 deal raises competition questions',deck='Today’s analysis examines possible pressure on budget mobile plans.',url='https://www.straitstimes.com/tech/tech-news/starhub-m1-merger-cheap-plans-are-on-borrowed-time-and-history-risks-repeating',time='25 Nov · 20:20 SGT · Updated',published='2026-11-25T13:15:00+08:00',updated='2026-11-25T20:20:00+08:00',timezone='Asia/Singapore',precision='minute',listing='https://www.straitstimes.com/global',position=2),
dict(desk='INDIA',source='The Indian Express',label='FAMILY ASSETS',headline='Lakshmi Venu seeks court partition of family assets',deck='Her Madras High Court filing escalates a dispute over economic ownership. The report distinguishes family property from individual companies’ management.',url='https://indianexpress.com/article/business/lakshmi-venu-moves-madras-high-court-partition-tvs-family-assets-venu-srinivasan-10978103/',time='25 Nov · 17:40 IST · Updated',published=None,updated='2026-11-25T17:40:00+05:30',timezone='Asia/Kolkata',precision='minute',listing='https://indianexpress.com/',position=1),
dict(desk='INDONESIA',source='The Jakarta Post',label='POLICE ETHICS',headline='Indonesian police dismiss general facing treason investigation',deck='Brig. Gen. Tedjo Kusumo was discharged after Tuesday’s ethics hearing, police said. The allegations remain under investigation.',url='https://www.thejakartapost.com/indonesia/2026/11/25/police-general-suspected-of-treason-sacked',time='25 Nov · 11:49 WIB · Published',published='2026-11-25T11:49:33+07:00',updated=None,timezone='Asia/Jakarta',precision='second',listing='https://www.thejakartapost.com/indonesia',position=1),
dict(desk='PAKISTAN',source='Dawn / Reuters',label='SPACE',headline='Zeeshan Ali boards China’s Tiangong space station',deck='The Pakistani astronaut arrived with the Shenzhou-24 crew on Wednesday.',url='https://www.dawn.com/news/2046753/a-new-era-begins-pakistans-zeeshan-ali-becomes-first-foreigner-to-board-chinas-tiangong-space-station',time='25 Nov · 18:17 PKT · Updated',published='2026-11-25',updated='2026-11-25T18:17:00+05:00',timezone='Asia/Karachi',precision='minute',listing='https://www.dawn.com/',position=2),
]
for s in stories:
 s['verified']=True
 s['published_precision']='date' if s['published'] and len(s['published'])==10 else ('not_exposed' if s['published'] is None else s['precision'])
 s['updated_precision']=s['precision'] if s['updated'] else 'not_exposed'
 s['verification_note']='Original publisher URL and prominent news listing checked at research cutoff. Missing separate timestamps are null. Time zones follow publisher locale. Restricted Japan Times and Jakarta Post content and SCMP listing verified through publisher-indexed content.'
stories[0]['verification_note']+=' Publication date only. Wednesday report releases October underlying-inflation data; no rate decision is implied.'
stories[3]['verification_note']+=' News analysis published today about Tuesday’s merger announcement; competition and future price effects are analysis, not observed price changes.'
stories[4]['verification_note']+=' Original publication time not separately exposed; current update and Wednesday statement establish editorial freshness. Court filing is not a judgment.'
stories[5]['verification_note']+=' Report published Wednesday describes Tuesday’s dismissal; exact hearing time not exposed. Suspect status is retained and no guilt is asserted. Alternative mine-flood report was not selected because subsequent wire updates changed casualty figures.'
stories[6]['verification_note']+=' Original publication date only; precise update is exposed. Article verifies Wednesday boarding, not merely planned launch.'
data=dict(id='ASIA-20261125',date='2026-11-25',edition='Wednesday, 25 November 2026',cutoff='25 NOV · 19:10 IST',window_start='2026-11-24T19:10:00+05:30',window_end='2026-11-25T19:10:00+05:30',release_tag='asia-desk-2026-11-25',stories=stories,selection_note='Up to first three prominently displayed items reviewed per source listing. One distinct verified event per source; no shared event or wire copy repeated. Newly published analysis and releases are distinguished from their underlying event or data period.')
data['reviewed_candidates']={
'The Japan Times':['Izumi','Inflation','Starbucks'],
'The Korea Herald':['Fragile Kospi faces fresh test','Beyond the port: Busan bets on international education','Lee’s choice of NIS chief faces scrutiny over China ties'],
'South China Morning Post':['Land lease application pending for 29 years','John Lee on housing and reforms','Consumer Council performance audit'],
'The Straits Times':['Shanghai','Telcos','Passports'],
'The Indian Express':['TVS family asset partition filing','Delhi comedian legal trouble','SP candidate list dispute'],
'The Jakarta Post':['Police general dismissal','Pekalongan procurement graft sentence','Bogor mine flooding'],
'Dawn':['Karachi','Tiangong','Hormuz']}
from datetime import datetime, timedelta
cutoff=datetime.fromisoformat(data['window_end'])
for story in stories:
 stamp=story['updated'] or story['published']
 if stamp and 'T' in stamp:
  instant=datetime.fromisoformat(stamp)
  assert cutoff-timedelta(hours=24) <= instant <= cutoff, (story['source'],stamp)
(ROOT/'edition.json').write_text(json.dumps(data,indent=2,ensure_ascii=False))
out=ROOT/'slides';out.mkdir(exist_ok=True)
for i,s in enumerate([None]+stories):
 art=Image.open(ROOT/f'art/{i:02d}.png').convert('RGB')
 frame(data,i+1,art,s).save(out/f'{i+1:02d}.jpg',quality=87,optimize=True)
caption='Asia in Seven Headlines | 25 November 2026\n\nMarkets, public policy and space across seven newspapers.\n\nTimes are local to each publisher. AI editorial illustrations.\n\nSources\n'+'\n'.join(s['url'] for s in stories)
assert len(caption)<2200
(ROOT/'caption.txt').write_text(caption)
board=Image.new('RGB',(864,540),'white')
for i,f in enumerate(sorted(out.glob('*.jpg'))):
 im=Image.open(f);assert im.size==(1080,1350)
 board.paste(im.resize((216,270)),((i%4)*216,(i//4)*270))
board.save(ROOT/'preview.jpg')
print('Rendered 8 slides; caption characters:',len(caption))
