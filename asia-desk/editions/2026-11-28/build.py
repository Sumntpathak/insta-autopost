import json
from datetime import datetime,timedelta
from pathlib import Path
from PIL import Image
from render import frame
ROOT=Path(__file__).resolve().parent
stories=[
dict(desk='JAPAN',source='The Japan Times / Jiji',label='DEFENCE POLICY',headline='Japan weighs nuclear-submarine wording',deck='Sources expect revised security documents to call for a decision; acquisition remains undecided.',url='https://www.japantimes.co.jp/news/2026/11/28/japan/japan-nuclear-submarines-security-documents/',time='28 Nov · Date only · JST',published='2026-11-28',updated=None,timezone='Asia/Tokyo',precision='date',listing='https://www.japantimes.co.jp/latest-news/1/',position=3),
dict(desk='SOUTH KOREA',source='The Korea Herald',label='DATA BREACH',headline='Korea Post confirms customer data breach',deck='One day’s analysis found 113,855 customers affected. Names, addresses and phone numbers were exposed; the postal service says the full extent remains under investigation.',url='https://www.koreaherald.com/article/10952405',time='28 Nov · 16:49 KST · Updated',published='2026-11-28T11:13:20+09:00',updated='2026-11-28T16:49:05+09:00',timezone='Asia/Seoul',precision='second',listing='https://www.koreaherald.com/',position=2),
dict(desk='HONG KONG',source='South China Morning Post',label='BUILDING SAFETY',headline='Scaffolding fire prompts Tuen Mun evacuation',deck='About 200 people left an industrial building Saturday. Police reported no injuries as of 2:50pm; the cause was under investigation.',url='https://www.scmp.com/news/hong-kong/society/article/3376121/about-200-evacuated-scaffolding-catches-fire-hong-kong-industrial-building',time='28 Nov · 21:32 HKT · Updated',published='2026-11-28T15:36:00+08:00',updated='2026-11-28T21:32:00+08:00',timezone='Asia/Hong_Kong',precision='minute',listing='https://www.scmp.com/news/hong-kong',position=1),
dict(desk='SINGAPORE',source='The Straits Times',label='REGIONAL REPORT',headline='Mumbai water plan raises fishing concerns',deck='Coastal communities fear desalination discharge could harm livelihoods.',url='https://www.straitstimes.com/asia/south-asia/mumbai-will-get-its-first-desalination-plant-but-fishermen-fear-their-catches-will-dry-up',time='28 Nov · 18:01 SGT · Updated',published='2026-11-28T15:00:00+08:00',updated='2026-11-28T18:01:00+08:00',timezone='Asia/Singapore',precision='minute',listing='https://www.straitstimes.com/global',position=1),
dict(desk='INDIA',source='The Indian Express',label='OPPOSITION',headline='INDIA bloc plans to oppose delimitation Bill',deck='After Saturday’s meeting, Kharge said the alliance would oppose the proposal. He alleged it would disadvantage SC/ST representation; those claims remain attributed to him.',url='https://indianexpress.com/article/political-pulse/mallikarjun-kharge-delimitation-bill-injustice-sc-st-attack-democracy-10982398/',time='28 Nov · 16:02 IST · Updated',published=None,updated='2026-11-28T16:02:00+05:30',timezone='Asia/Kolkata',precision='minute',listing='https://indianexpress.com/',position=2),
dict(desk='INDONESIA',source='The Jakarta Post',label='POLICE INQUIRY',headline='Police question Jokowi ally as witness',deck='Budi Arie Setiadi attended Friday’s questioning in an alleged treason inquiry. Fellow witness Devid Agus Yunanto did not attend and is to be summoned again Monday.',url='https://www.thejakartapost.com/indonesia/2026/11/28/police-summon-jokowi-allies-for-questioning-in-treason-probe',time='28 Nov · 17:07 WIB · Published',published='2026-11-28T17:07:52+07:00',updated=None,timezone='Asia/Jakarta',precision='second',listing='https://www.thejakartapost.com/indonesia',position=1),
dict(desk='PAKISTAN',source='Dawn',label='SPACE',headline='Pakistan’s leaders call astronaut in orbit',deck='Shehbaz and Munir spoke Saturday with Zeeshan Ali aboard China’s space station.',url='https://www.dawn.com/news/2047663/beacon-of-light-pm-shehbaz-cdf-munir-speak-with-astronaut-zeeshan-ali-aboard-chinas-space-station',time='28 Nov · 16:25 PKT · Updated',published='2026-11-28',updated='2026-11-28T16:25:00+05:00',timezone='Asia/Karachi',precision='minute',listing='https://www.dawn.com/',position=1),
]
for s in stories:
 s['verified']=True
 s['published_precision']='date' if s['published'] and len(s['published'])==10 else ('not_exposed' if s['published'] is None else s['precision'])
 s['updated_precision']=s['precision'] if s['updated'] else 'not_exposed'
 s['verification_note']='Original publisher URL and prominent listing checked. Missing separate timestamps remain null. Time zones follow publisher locale.'
for i in (0,2,5):stories[i]['verification_note']+=' Direct access restricted; indexed publisher article content used for verification.'
stories[0]['verification_note']+=' Date-only publication; exact age not determinable. Saturday report attributes expected wording to sources speaking Friday. No acquisition approval asserted.'
stories[1]['verification_note']+=' 113,855 is a lower bound from one day’s data, not a confirmed total for the incident.'
stories[2]['verification_note']+=' Latest observed indexed update 21:32 HKT; earlier indexed version showed 15:38. Injury status is explicitly limited to 14:50 HKT.'
stories[3]['verification_note']+=' Saturday original field report about a previously announced project. Environmental damage is a residents’ concern, not an established outcome. Singapore denotes publisher locale, not event location.'
stories[4]['verification_note']+=' Publication time not separately exposed. Saturday opposition meeting is a new development after yesterday’s Cabinet approval. Allegations attributed; Bill not presented as enacted.'
stories[5]['verification_note']+=' Witness status preserved; neither witness is described as convicted or charged. Saturday publication reports Friday questioning.'
stories[6]['verification_note']+=' Publication date only; exact update exposed. Saturday call is the fresh development, not a newly occurring launch.'
data=dict(id='ASIA-20261128',date='2026-11-28',edition='Saturday, 28 November 2026',cutoff='28 NOV · 19:47 IST',window_start='2026-11-27T19:47:00+05:30',window_end='2026-11-28T19:47:00+05:30',release_tag='asia-desk-2026-11-28',stories=stories,selection_note='First three prominent stories per source reviewed. Seven distinct events; shared events/wire copy not selected twice. Published/updated timestamp freshness checked; date-only precision retained. Today’s Japan policy report is relevant but exact hour cannot be established. Some publisher pages required indexed original content.')
data['reviewed_candidates']={'The Japan Times':['Births','Wrestling obituary','Submarine policy'],'The Korea Herald':['AI groundbreaking','Postal breach','North Korea visit speculation'],'South China Morning Post':['Industrial fire','Murder trial testimony','University town tenders'],'The Straits Times':['Water project','In-flight incident','Royal recovery film'],'The Indian Express':['Women’s quota electoral history','Opposition meeting','Delimitation questions'],'The Jakarta Post':['Witness questioning','Nusantara priorities','Teacher pay reaction'],'Dawn':['Space call','Iran live coverage','Bilawal remarks']}
data['selection_rejections']=['Japan births report not selected because substantially similar first-half figures were reported November 5; chose current policy wording report instead.','Indonesia teacher pay reaction not selected to avoid repeating yesterday’s central event.']
cutoff=datetime.fromisoformat(data['window_end'])
for s in stories:
 stamp=s['updated'] or s['published']
 if stamp and 'T' in stamp: assert cutoff-timedelta(hours=24)<=datetime.fromisoformat(stamp)<=cutoff,(s['source'],stamp)
(ROOT/'edition.json').write_text(json.dumps(data,indent=2,ensure_ascii=False))
out=ROOT/'slides';out.mkdir(exist_ok=True)
for i,s in enumerate([None]+stories):
 art=Image.open(ROOT/f'art/{i:02d}.png').convert('RGB')
 frame(data,i+1,art,s).save(out/f'{i+1:02d}.jpg',quality=87,optimize=True)
caption='Asia in Seven Headlines | 28 November 2026\n\nPublic policy, safety and science across seven newspapers.\n\nTimes are local to each publisher. AI editorial illustrations.\n\nSources\n'+'\n'.join(s['url'] for s in stories)
assert len(caption)<2200
(ROOT/'caption.txt').write_text(caption)
board=Image.new('RGB',(864,540),'white')
for i,f in enumerate(sorted(out.glob('*.jpg'))):
 im=Image.open(f);assert im.size==(1080,1350)
 board.paste(im.resize((216,270)),((i%4)*216,(i//4)*270))
board.save(ROOT/'preview.jpg')
print('Rendered 8 slides; caption characters:',len(caption))
