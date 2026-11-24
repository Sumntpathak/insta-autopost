import json
from pathlib import Path
from PIL import Image
from render import frame
ROOT=Path(__file__).resolve().parent
stories=[
dict(desk='JAPAN',source='The Japan Times',label='ICC FUNDING',headline='Japan brings forward its ICC contribution',deck='Takaichi’s move aims to protect the court’s funding amid US sanctions.',url='https://www.japantimes.co.jp/news/2026/11/24/japan/politics/japan-pm-takaichi-icc-akane/',time='24 Nov · Date only · JST',published='2026-11-24',updated=None,timezone='Asia/Tokyo',precision='date',listing='https://www.japantimes.co.jp/latest-news/1/',position=1),
dict(desk='SOUTH KOREA',source='The Korea Herald',label='EXAM SECURITY',headline='Korea seeks tougher penalties for AI exam cheating',deck='The ministry plans nearly 8,000 metal detectors for high schools. Proposed legal changes would allow entrance-exam bans of up to 10 years for serious cheating.',url='https://www.koreaherald.com/article/10947539',time='24 Nov · 16:32 KST · Updated',published='2026-11-24T14:20:22+09:00',updated='2026-11-24T16:32:06+09:00',timezone='Asia/Seoul',precision='second',listing='https://www.koreaherald.com/',position=1),
dict(desk='HONG KONG',source='South China Morning Post',label='TOURISM',headline='Hong Kong records 5.1 million October arrivals',deck='Visitor numbers rose 12% from a year earlier, tourism board figures show. The first ten months brought more than 45.8 million arrivals.',url='https://www.scmp.com/news/hong-kong/hong-kong-economy/article/3375570/hong-kong-welcomes-51-million-visitors-october-12-year-year',time='24 Nov · 13:20 HKT · Updated',published='2026-11-24T13:18:00+08:00',updated='2026-11-24T13:20:00+08:00',timezone='Asia/Hong_Kong',precision='minute',listing='https://www.scmp.com/news/hong-kong?page=1',position=3),
dict(desk='SINGAPORE',source='The Straits Times',label='CHIP EXPORTS',headline='Singapore, US work on chip export enforcement',deck='Wong says cooperation continues as Singapore investigates Megaspeed.',url='https://www.straitstimes.com/singapore/spore-working-with-us-on-chip-export-enforcement-as-megaspeed-probe-continues-pm-wong',time='24 Nov · 22:08 SGT · Updated',published='2026-11-24T12:36:00+08:00',updated='2026-11-24T22:08:00+08:00',timezone='Asia/Singapore',precision='minute',listing='https://www.straitstimes.com/global',position=1),
dict(desk='INDIA',source='The Indian Express',label='MADURAI',headline='Madurai hilltop pillar remains unlit after court order',deck='The customary shrine’s lamp was lit Tuesday evening, while the separate pillar stayed dark. The Express reports that the state had obtained no stay on the order.',url='https://indianexpress.com/article/cities/chennai/tamil-nadu-defies-supreme-court-order-karthigai-deepam-lit-only-at-uchi-pillaiyar-thirupparankundram-hill-vijay-ctr-nirmal-kumar-10976857/',time='24 Nov · 19:25 IST · Updated',published=None,updated='2026-11-24T19:25:00+05:30',timezone='Asia/Kolkata',precision='minute',listing='https://indianexpress.com/',position=1),
dict(desk='INDONESIA',source='The Jakarta Post',label='CONSERVATION',headline='Minister seeks end to Ujung Kulon mining designation',deck='Indonesia’s environment minister wants mining-reserve status cancelled near the rhino habitat. The designation identifies reserves and does not itself authorise mining.',url='https://www.thejakartapost.com/indonesia/2026/11/24/environment-minister-asks-bahlil-to-cancel-ujung-kulon-mining-status',time='24 Nov · 17:31 WIB · Published',published='2026-11-24T17:31:05+07:00',updated=None,timezone='Asia/Jakarta',precision='second',listing='https://www.thejakartapost.com/indonesia',position=3),
dict(desk='PAKISTAN',source='Dawn',label='ONLINE POLICY',headline='Naqvi calls for online platform accountability',deck='The interior minister outlined speech limits and proposed enforcement steps.',url='https://www.dawn.com/news/2046770/freedom-of-speech-should-not-become-a-shield-for-those-crossing-red-lines-says-naqvi',time='24 Nov · 17:09 PKT · Updated',published='2026-11-24',updated='2026-11-24T17:09:00+05:00',timezone='Asia/Karachi',precision='minute',listing='https://www.dawn.com/',position=1),
]
for s in stories:
 s['verified']=True
 s['published_precision']='date' if s['published'] and len(s['published'])==10 else ('not_exposed' if s['published'] is None else s['precision'])
 s['updated_precision']=s['precision'] if s['updated'] else 'not_exposed'
 s['verification_note']='Original publisher URL and prominent news listing checked. Missing separate timestamps are null. Time zones follow publisher locale. Restricted Japan Times and Jakarta Post content and SCMP listing verified through publisher-indexed content.'
stories[0]['verification_note']+=' Date-only publication; no exact time or update exposed. Today’s reporting describes Tuesday’s ICC meeting.'
stories[2]['verification_note']+=' October data is newly released Tuesday; editorial freshness refers to release, not the measurement month.'
stories[4]['verification_note']+=' Original publication time not exposed; Tuesday evening events and 19:25 IST update establish freshness.'
stories[5]['verification_note']+=' Tuesday report concerns a letter described as sent late last week; no claim that the letter itself was sent today.'
stories[6]['verification_note']+=' Publication date only; exact update is exposed. Policy statements are attributed to minister, not presented as an assessment of lawful speech.'
data=dict(id='ASIA-20261124',date='2026-11-24',edition='Tuesday, 24 November 2026',cutoff='24 NOV · 19:53 IST',window_start='2026-11-23T19:53:00+05:30',window_end='2026-11-24T19:53:00+05:30',release_tag='asia-desk-2026-11-24',stories=stories,selection_note='First three prominent items reviewed per source listing. One distinct verified event per source; no shared event or wire copy repeated. Reporting dates and underlying event dates distinguished.')
data['reviewed_candidates']={
'The Japan Times':['ICC','Fujitsu','Loans'],
'The Korea Herald':['Expulsions, 10-year bans eyed to combat AI exam cheating','Number of ministries and agencies set to relocate to Sejong reduced to 31','Jensen Huang’s return eases HBM uncertainty for Samsung, SK hynix'],
'South China Morning Post':['Hong Kong customs arrests 7, seizes HK$23 million in suspected smuggled drugs','Driver who allegedly killed 1, injured 3 others in Tsim Sha Tsui crash denied bail','Hong Kong welcomes 5.1 million visitors in October, up 12% year on year'],
'The Straits Times':['Export enforcement','Megaspeed','ASEAN'],
'The Indian Express':['Vijay government leaves Madurai hilltop pillar unlit','GTA 6 in India: Price, platforms, features and gaming craze','Why an Ayushmann Khurrana movie has sparked a language row in Bengal'],
'The Jakarta Post':['Misprinted T-shirts, flags in Listyo treason case raise eyebrows','Death toll from candy factory fire rises to 26: Police','Environment minister asks Bahlil to cancel Ujung Kulon mining status'],
'Dawn':['Naqvi','KP','Riyadh']}
(ROOT/'edition.json').write_text(json.dumps(data,indent=2,ensure_ascii=False))
out=ROOT/'slides';out.mkdir(exist_ok=True)
for i,s in enumerate([None]+stories):
 art=Image.open(ROOT/f'art/{i:02d}.png').convert('RGB')
 frame(data,i+1,art,s).save(out/f'{i+1:02d}.jpg',quality=87,optimize=True)
caption='Asia in Seven Headlines | 24 November 2026\n\nPolicy, technology and public life across seven newspapers.\n\nTimes are local to each publisher. AI editorial illustrations.\n\nSources\n'+'\n'.join(s['url'] for s in stories)
assert len(caption)<2200
(ROOT/'caption.txt').write_text(caption)
board=Image.new('RGB',(864,540),'white')
for i,f in enumerate(sorted(out.glob('*.jpg'))):
 im=Image.open(f);assert im.size==(1080,1350)
 board.paste(im.resize((216,270)),((i%4)*216,(i//4)*270))
board.save(ROOT/'preview.jpg')
print('Rendered 8 slides; caption characters:',len(caption))
