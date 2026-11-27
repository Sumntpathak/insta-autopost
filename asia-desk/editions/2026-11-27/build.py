import json
from datetime import datetime,timedelta
from pathlib import Path
from PIL import Image
from render import frame
ROOT=Path(__file__).resolve().parent
stories=[
dict(desk='JAPAN',source='The Japan Times',label='PARLIAMENT',headline='Upper House rejects Seki censure',deck='The nonbinding motion failed by 124 votes to 120 on Friday.',url='https://www.japantimes.co.jp/news/2026/11/27/japan/politics/censure-motion-voted-down/',time='27 Nov · Date only · JST',published='2026-11-27',updated=None,timezone='Asia/Tokyo',precision='date',listing='https://www.japantimes.co.jp/latest-news/1/',position=1),
dict(desk='SOUTH KOREA',source='The Korea Herald',label='REPATRIATION',headline='Six rescued North Korean fishers return home',deck='South Korea repatriated six crew members Friday. A seventh requested protection and remained, the Unification Ministry said.',url='https://www.koreaherald.com/article/10951950',time='27 Nov · 14:59 KST · Published',published='2026-11-27T14:59:09+09:00',updated=None,timezone='Asia/Seoul',precision='second',listing='https://www.koreaherald.com/',position=1),
dict(desk='HONG KONG',source='South China Morning Post',label='JUSTICE',headline='Top court overturns flag convictions',deck='Hong Kong’s Court of Final Appeal quashed an autistic man’s three convictions Friday, finding insufficient evidence to pursue the prosecution.',url='https://www.scmp.com/news/hong-kong/law-and-crime/article/3376017/hong-kongs-top-court-quashes-flag-desecration-conviction-autistic-man',time='27 Nov · 17:38 HKT · Updated',published='2026-11-27T15:30:00+08:00',updated='2026-11-27T17:38:00+08:00',timezone='Asia/Hong_Kong',precision='minute',listing='https://www.scmp.com/news/hong-kong',position=1),
dict(desk='SINGAPORE',source='The Straits Times',label='AI ECONOMY',headline='Nageswaran warns of AI-heavy growth risks',deck='India’s chief economic adviser raised concentration concerns at Singapore’s Asia Future Summit.',url='https://www.straitstimes.com/business/global-economy-risks-hangover-as-growth-over-reliant-on-ai-boom-india-chief-economic-adviser',time='27 Nov · 22:07 SGT · Updated',published='2026-11-27T17:36:00+08:00',updated='2026-11-27T22:07:00+08:00',timezone='Asia/Singapore',precision='minute',listing='https://www.straitstimes.com/global',position=3),
dict(desk='INDIA',source='The Indian Express',label='LEGISLATION',headline='Cabinet clears revised women’s reservation proposal',deck='Sources say the Bill pairs women’s reservation with a proposed 50% Lok Sabha seat increase across states. Parliamentary passage is still required.',url='https://indianexpress.com/article/india/women-reservation-delimitation-gets-cabinet-approval-10980995/',time='27 Nov · 17:41 IST · Updated',published=None,updated='2026-11-27T17:41:00+05:30',timezone='Asia/Kolkata',precision='minute',listing='https://indianexpress.com/',position=2),
dict(desk='INDONESIA',source='The Jakarta Post',label='TEACHER PAY',headline='Prabowo promises teacher pay rise without timetable',deck='At Thursday’s Teachers’ Day event, the president said salaries would rise when conditions allowed. He gave no date and linked increases to stronger state finances.',url='https://www.thejakartapost.com/indonesia/2026/11/27/teachers-to-get-pay-rise-when-the-time-comes-prabowo-says',time='27 Nov · 09:57 WIB · Published',published='2026-11-27T09:57:23+07:00',updated=None,timezone='Asia/Jakarta',precision='second',listing='https://www.thejakartapost.com/indonesia/',position=2),
dict(desk='PAKISTAN',source='Dawn',label='DIPLOMACY',headline='Makkah alliance talks begin in Islamabad',deck='The three partners’ expected agenda includes the Yemen conflict.',url='https://www.dawn.com/news/2047415/makkah-defence-alliance-meeting-in-islamabad-begins-with-yemen-conflict-also-on-agenda',time='27 Nov · 17:13 PKT · Updated',published='2026-11-27',updated='2026-11-27T17:13:00+05:00',timezone='Asia/Karachi',precision='minute',listing='https://www.dawn.com/',position=1),
]
for s in stories:
 s['verified']=True
 s['published_precision']='date' if s['published'] and len(s['published'])==10 else ('not_exposed' if s['published'] is None else s['precision'])
 s['updated_precision']=s['precision'] if s['updated'] else 'not_exposed'
 s['verification_note']='Original publisher URL and prominent listing checked. Missing separate timestamps remain null; local time zone and timestamp precision preserved.'
for i in (0,2,5):stories[i]['verification_note']+=' Direct access restricted; original publisher content and timestamp verified through indexed publisher pages.'
stories[0]['verification_note']+=' Date-only publication; no clock time asserted.'
stories[2]['verification_note']+=' Latest observed indexed update 17:38 HKT; earlier indexed versions exposed earlier updates.'
stories[3]['verification_note']+=' Attributed risk warning, not a prediction stated as fact. Front page changed after initial selection; story occupied third prominent slot at initial review.'
stories[4]['verification_note']+=' Only updated time exposed. Cabinet approval reported by sources is not parliamentary enactment. 50% refers to proposed seat expansion, not the women’s quota.'
stories[5]['verification_note']+=' Friday publication reports Thursday remarks; no pay rise date or enacted increase asserted.'
stories[6]['verification_note']+=' Publication date only; exact update exposed. Meeting beginning is a new development after prior edition’s planned meeting; no outcome asserted.'
data=dict(id='ASIA-20261127',date='2026-11-27',edition='Friday, 27 November 2026',cutoff='27 NOV · 19:43 IST',window_start='2026-11-26T19:43:00+05:30',window_end='2026-11-27T19:43:00+05:30',release_tag='asia-desk-2026-11-27',stories=stories,selection_note='Up to first three prominent stories per publisher reviewed. Seven distinct events; no shared wire event selected twice. Freshness uses published or updated timestamps; date-only publication cannot establish an exact age. Today’s date and current event relevance support the Japan selection. Indexed publisher content used where direct access was restricted.')
data['reviewed_candidates']={'The Japan Times':['Censure','Schools','Tariffs'],'The Korea Herald':['Repatriation','Myeongdong retail','Exam cheating'],'South China Morning Post':['Court ruling','Huawei weekly','Ferry crash'],'The Straits Times':['ASEAN','Trade leverage','AI'],'The Indian Express':['Delimitation history','Cabinet Bill','Pawar opposition'],'The Jakarta Post':['Police chief remarks','Teacher pay','Philippines scam arrests'],'Dawn':['Makkah','Jazan','Karachi']}
data['rejected_stale_candidate']={'source':'The Jakarta Post','url':'https://www.thejakartapost.com/indonesia/2026/11/27/141-indonesians-arrested-in-philippines-over-alleged-online-scam-operations','published':'2026-11-26T17:03:11+07:00','reason':'Outside preceding 24 hours despite a November 27 path/header; no newer update verified.'}
cutoff=datetime.fromisoformat(data['window_end'])
for s in stories:
 stamp=s['updated'] or s['published']
 if stamp and 'T' in stamp: assert cutoff-timedelta(hours=24)<=datetime.fromisoformat(stamp)<=cutoff,(s['source'],stamp)
(ROOT/'edition.json').write_text(json.dumps(data,indent=2,ensure_ascii=False))
out=ROOT/'slides';out.mkdir(exist_ok=True)
for i,s in enumerate([None]+stories):
 art=Image.open(ROOT/f'art/{i:02d}.png').convert('RGB')
 frame(data,i+1,art,s).save(out/f'{i+1:02d}.jpg',quality=87,optimize=True)
caption='Asia in Seven Headlines | 27 November 2026\n\nJustice, public policy and diplomacy across seven newspapers.\n\nTimes are local to each publisher. AI editorial illustrations.\n\nSources\n'+'\n'.join(s['url'] for s in stories)
assert len(caption)<2200
(ROOT/'caption.txt').write_text(caption)
board=Image.new('RGB',(864,540),'white')
for i,f in enumerate(sorted(out.glob('*.jpg'))):
 im=Image.open(f);assert im.size==(1080,1350)
 board.paste(im.resize((216,270)),((i%4)*216,(i//4)*270))
board.save(ROOT/'preview.jpg')
print('Rendered 8 slides; caption characters:',len(caption))
