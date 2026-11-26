import json
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image
from render import frame
ROOT=Path(__file__).resolve().parent
stories=[
dict(desk='JAPAN',source='The Japan Times / Jiji',label='AVIATION',headline='ANA creates pilot training company',deck='ANA Next Aviation plans to train pilots ahead of expected retirements.',url='https://www.japantimes.co.jp/business/2026/11/26/companies/ana-pilot-training-firm/',time='26 Nov · Date only · JST',published='2026-11-26',updated=None,timezone='Asia/Tokyo',precision='date',listing='https://www.japantimes.co.jp/latest-news/?pgno=1',position=1),
dict(desk='SOUTH KOREA',source='The Korea Herald',label='URBAN CHANGE',headline='Hannam redevelopment breaks ground near Itaewon',deck='Construction began Thursday on a project planned to deliver 5,970 homes by December 2030. The Herald examines what the changes mean for the neighborhood’s identity.',url='https://www.koreaherald.com/article/10950686',time='26 Nov · 17:26 KST · Updated',published='2026-11-26T15:44:42+09:00',updated='2026-11-26T17:26:35+09:00',timezone='Asia/Seoul',precision='second',listing='https://www.koreaherald.com/',position=1),
dict(desk='HONG KONG',source='South China Morning Post',label='RIDE-HAILING',headline='Hong Kong sets out ride-hailing permit timetable',deck='Driving-permit applications open November 30. Vehicle-permit applications follow early next year, under a 10,000-car cap; the two permits serve different purposes.',url='https://www.scmp.com/news/hong-kong/transport/article/3375943/hong-kong-clears-route-ride-hailing-licences-private-car-owners',time='26 Nov · 19:50 HKT · Updated',published='2026-11-26T19:46:00+08:00',updated='2026-11-26T19:50:00+08:00',timezone='Asia/Hong_Kong',precision='minute',listing='https://www.scmp.com/news/hong-kong',position=1),
dict(desk='SINGAPORE',source='The Straits Times',label='TRADE',headline='US proposes Singapore levy, leaves room for talks',deck='Negotiations could reduce the proposed 20% rate to 10%.',url='https://www.straitstimes.com/business/us-proposes-new-tariff-of-up-to-20-on-singapore-but-leaves-the-door-open-to-a-deal',time='26 Nov · 21:11 SGT · Updated',published='2026-11-26T10:20:00+08:00',updated='2026-11-26T21:11:00+08:00',timezone='Asia/Singapore',precision='minute',listing='https://www.straitstimes.com/global',position=3),
dict(desk='INDIA',source='The Indian Express',label='PARLIAMENT',headline='Government seeks Parliament sittings next week',deck='Rijiju says the government requested Lok Sabha to reconvene on November 30 and Rajya Sabha on December 2 for essential government business.',url='https://indianexpress.com/article/india/parliament-session-2026-lok-sabha-rajya-sabha-reconvene-10979976/',time='26 Nov · 19:26 IST · Updated',published=None,updated='2026-11-26T19:26:00+05:30',timezone='Asia/Kolkata',precision='minute',listing='https://indianexpress.com/',position=1),
dict(desk='INDONESIA',source='The Jakarta Post',label='VP NOMINEES',headline='Sugiono and Amran undergo required medical checks',deck='The nominees attended Gatot Subroto Army Hospital on Thursday for Assembly-required screening. The report does not establish the examination results.',url='https://www.thejakartapost.com/indonesia/2026/11/26/army-doctors-examine-vp-nominees',time='26 Nov · 14:18 WIB · Published',published='2026-11-26T14:18:07+07:00',updated=None,timezone='Asia/Jakarta',precision='second',listing='https://www.thejakartapost.com/indonesia',position=3),
dict(desk='PAKISTAN',source='Dawn / AFP',label='DIPLOMACY',headline='Islamabad meeting to discuss Saudi–Yemen conflict',deck='Asif says Makkah pact partners will address regional fighting.',url='https://www.dawn.com/news/2047228/makkah-pact-nations-to-discuss-conflict-between-saudi-arabia-and-yemen-in-islamabad-meeting-khawaja-asif-says',time='26 Nov · 18:55 PKT · Updated',published='2026-11-26',updated='2026-11-26T18:55:00+05:00',timezone='Asia/Karachi',precision='minute',listing='https://www.dawn.com/',position=1),
]
for s in stories:
 s['verified']=True
 s['published_precision']='date' if s['published'] and len(s['published'])==10 else ('not_exposed' if s['published'] is None else s['precision'])
 s['updated_precision']=s['precision'] if s['updated'] else 'not_exposed'
 s['verification_note']='Original publisher URL and prominent news listing checked. Missing separate timestamps are null. Time zones follow publisher locale. Restricted Japan Times and Jakarta Post content and SCMP listing verified through publisher-indexed content.'
stories[0]['verification_note']+=' Date-only publication. Today’s report describes an announcement made Wednesday; the operating start is a future plan.'
stories[2]['verification_note']+=' Original article indexed at 19:50 HKT. Driving and vehicle permit stages are kept separate.'
stories[3]['verification_note']+=' Proposed rates and possible negotiated reduction are conditional; no implemented tariff change is asserted.'
stories[4]['verification_note']+=' Original publication time not separately exposed. Current update and Thursday statement establish editorial freshness; the report says requested reconvening, without a confirmed legislative agenda.'
stories[5]['verification_note']+=' Only attendance for medical checks is asserted, without unverified results.'
stories[6]['verification_note']+=' Publication date only in article header; exact update is exposed. Home listing calls 18:55 PKT published. Slide uses article header’s Updated label. Meeting agenda is attributed to the minister; no outcome is claimed.'
data=dict(id='ASIA-20261126',date='2026-11-26',edition='Thursday, 26 November 2026',cutoff='26 NOV · 19:53 IST',window_start='2026-11-25T19:53:00+05:30',window_end='2026-11-26T19:53:00+05:30',release_tag='asia-desk-2026-11-26',stories=stories,selection_note='Up to first three prominent stories reviewed per source news listing. One distinct event per source; shared US tariff coverage appears only through the Singapore selection. Missing timestamp precision is preserved.')
data['reviewed_candidates']={
'The Japan Times':['ANA','Censure','Fukuoka'],
'The Korea Herald':['Itaewon redevelopment','Suneung perfect scorers','Foreign residents political speech ruling'],
'South China Morning Post':['Ride-hailing licences','Privacy watchdog data security','Tai Po memorial'],
'The Straits Times':['Exports','CPF','Negotiations'],
'The Indian Express':['Parliament session request','Congress leader pictured with election commissioner','Akhilesh Yadav UP campaign promises'],
'The Jakarta Post':['Rhino relocation donor claim','Yogyakarta daycare sentence','VP nominee medical checks'],
'Dawn':['Makkah','Bilawal','Hormuz']}
cutoff=datetime.fromisoformat(data['window_end'])
for s in stories:
 stamp=s['updated'] or s['published']
 if stamp and 'T' in stamp:
  assert cutoff-timedelta(hours=24)<=datetime.fromisoformat(stamp)<=cutoff, (s['source'],stamp)
(ROOT/'edition.json').write_text(json.dumps(data,indent=2,ensure_ascii=False))
out=ROOT/'slides';out.mkdir(exist_ok=True)
for i,s in enumerate([None]+stories):
 art=Image.open(ROOT/f'art/{i:02d}.png').convert('RGB')
 frame(data,i+1,art,s).save(out/f'{i+1:02d}.jpg',quality=87,optimize=True)
caption='Asia in Seven Headlines | 26 November 2026\n\nTransport, public policy and diplomacy across seven newspapers.\n\nTimes are local to each publisher. AI editorial illustrations.\n\nSources\n'+'\n'.join(s['url'] for s in stories)
assert len(caption)<2200
(ROOT/'caption.txt').write_text(caption)
board=Image.new('RGB',(864,540),'white')
for i,f in enumerate(sorted(out.glob('*.jpg'))):
 im=Image.open(f);assert im.size==(1080,1350)
 board.paste(im.resize((216,270)),((i%4)*216,(i//4)*270))
board.save(ROOT/'preview.jpg')
print('Rendered 8 slides; caption characters:',len(caption))
