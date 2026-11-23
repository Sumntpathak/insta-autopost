import json
from pathlib import Path
from PIL import Image
from render import frame
ROOT=Path(__file__).resolve().parent
stories=[
dict(desk='JAPAN',source='The Japan Times / Jiji',label='DIPLOMACY',headline='Japan–North Korea intelligence contact reported',deck='Officials reportedly met during the Asian Games; the account emerged Monday.',url='https://www.japantimes.co.jp/news/2026/11/23/japan/japan-nk-intel-asian-games/',time='23 Nov · Date only · JST',published='2026-11-23',updated=None,timezone='Asia/Tokyo',precision='date',listing='https://www.japantimes.co.jp/latest-news/?pgno=1',position=1),
dict(desk='SOUTH KOREA',source='The Korea Herald',label='APPOINTMENTS',headline='Lee nominates new security leadership',deck='Kang Kum-sil is nominated to lead the intelligence agency. If appointed, she would be its first female chief; foreign and unification ministry nominees were also announced.',url='https://www.koreaherald.com/article/10946349',time='23 Nov · 18:31 KST · Updated',published='2026-11-23T15:32:17+09:00',updated='2026-11-23T18:31:16+09:00',timezone='Asia/Seoul',precision='second',listing='https://www.koreaherald.com/',position=1),
dict(desk='HONG KONG',source='South China Morning Post',label='AIRSPACE',headline='Hong Kong sets flight restrictions for Interpol assembly',deck='Drones, kites, balloons and paragliders face a citywide restriction during the November 30–December 3 meeting. Police also announced sea and road controls.',url='https://www.scmp.com/news/hong-kong/transport/article/3375443/hong-kong-ban-drones-kites-balloons-across-city-interpol-general-assembly',time='23 Nov · 16:15 HKT · Updated',published='2026-11-23T14:13:00+08:00',updated='2026-11-23T16:15:00+08:00',timezone='Asia/Hong_Kong',precision='minute',listing='https://www.scmp.com/news/hong-kong',position=3),
dict(desk='SINGAPORE',source='The Straits Times',label='AVIATION',headline='Wong arrives at Western Sydney’s new airport',deck='He travelled on Singapore Airlines’ inaugural flight to the airport.',url='https://www.straitstimes.com/singapore/newest-chapter-of-our-friendship-pm-wong-arrives-at-new-sydney-airport-on-inaugural-sia-flight',time='23 Nov · 22:17 SGT · Updated',published='2026-11-23T18:28:00+08:00',updated='2026-11-23T22:17:00+08:00',timezone='Asia/Singapore',precision='minute',listing='https://www.straitstimes.com/global',position=1),
dict(desk='INDIA',source='The Indian Express',label='TECHNOLOGY',headline='Nvidia board reinstates Jensen Huang as CEO',deck='An Express explainer examines the board’s unanimous reversal and the campaign for Huang’s return. The company announced his reinstatement on Monday.',url='https://indianexpress.com/article/explained/explained-ai/why-trump-wants-jensen-huang-back-at-nvidia-and-why-its-board-is-resisting-10974781/',time='23 Nov · 20:19 IST · Updated',published=None,updated='2026-11-23T20:19:00+05:30',timezone='Asia/Kolkata',precision='minute',listing='https://indianexpress.com/',position=1),
dict(desk='INDONESIA',source='The Jakarta Post',label='VP NOMINATIONS',headline='Prabowo submits Amran and Sugiono as VP nominees',deck='The president delivered the two names to the People’s Consultative Assembly. Its vote to choose a vice president is now scheduled for December 11.',url='https://www.thejakartapost.com/indonesia/2026/11/23/breaking-prabowo-submits-ministers-amran-and-sugiono-as-vp-nominees',time='23 Nov · 17:19 WIB · Published',published='2026-11-23T17:19:45+07:00',updated=None,timezone='Asia/Jakarta',precision='second',listing='https://www.thejakartapost.com/indonesia',position=2),
dict(desk='PAKISTAN',source='Dawn',label='CRICKET',headline='Peshawar chosen for PSL opening',deck='The PCB chief says the city will host next year’s opening ceremony and first match.',url='https://www.dawn.com/news/2046559/peshawar-to-host-opening-ceremony-inaugural-match-for-12th-edition-of-psl-pcb-chief',time='23 Nov · 20:05 PKT · Updated',published='2026-11-23',updated='2026-11-23T20:05:00+05:00',timezone='Asia/Karachi',precision='minute',listing='https://www.dawn.com/',position=1),
]
for s in stories:
 s['verified']=True
 s['published_precision']='date' if s['published'] and len(s['published'])==10 else ('not_exposed' if s['published'] is None else s['precision'])
 s['updated_precision']=s['precision'] if s['updated'] else 'not_exposed'
 s['verification_note']='Original publisher URL and news listing checked at research cutoff. For restricted pages, publisher-indexed content was used. Null means no separate timestamp was exposed. Time zones follow publisher locale.'
stories[0]['verification_note']+=' Publication is date-only; no exact time or update is exposed. New reporting is dated today, with September–October events as context.'
stories[2]['verification_note']+=' Indexed article variants show updates at 15:04 and 16:15 HKT; latest observed 16:15 retained.'
stories[4]['verification_note']+=' Original publication time not exposed; current update and Monday reinstatement establish editorial freshness.'
stories[6]['verification_note']+=' Article publication is date-only; home listing separately showed initial publication at 19:03 PKT.'
data=dict(id='ASIA-20261123',date='2026-11-23',edition='Monday, 23 November 2026',cutoff='23 NOV · 20:39 IST',window_start='2026-11-22T20:39:00+05:30',window_end='2026-11-23T20:39:00+05:30',release_tag='asia-desk-2026-11-23',stories=stories,selection_note='First three prominent stories reviewed per source listing. Seven distinct events; Nvidia repeats on several home pages but appears only once in this edition. No shared wire event repeated.')
data['reviewed_candidates']={
'The Japan Times':['Japanese and North Korean intel officials likely had contact during Asian Games','Japan’s Tamagotchi digital pet toy marks 30th anniversary','Ukraine sinks Russian warship in Libya as conflict spreads beyond Europe'],
'The Korea Herald':['Lee reshuffles security team, names first female spy chief',"Kim Jong-un's luxury fleet appears to grow despite sanctions","K-pop's next big creative partners are bestselling novelists"],
'South China Morning Post':['Hong Kong customs seizes HK$68m in suspected fake goods in Double 11 crackdown','How shared stories loosen grip of Tai Po inferno on traumatised domestic helpers','Hong Kong to ban drones, kites and balloons from airspace for Interpol assembly'],
'The Straits Times':['PM Wong arrives at new Sydney airport on inaugural SIA flight','Nvidia reinstates Jensen Huang as CEO','Singapore hopes setback from COP31 failure will not pull nations apart: Grace Fu'],
'The Indian Express':['Why Nvidia reinstated Jensen Huang as CEO','Jensen Huang’s first words after reinstatement','What Jensen Huang’s return means for NVIDIA and the AI ecosystem'],
'The Jakarta Post':['Top cop shakes up Yogyakarta police leadership','Prabowo submits ministers Amran and Sugiono as VP nominees','Death toll hits 24 in factory blaze as dozens remain missing'],
'Dawn':['Peshawar to host opening ceremony, inaugural match for 12th edition of PSL','Nvidia reinstates Jensen Huang as CEO after affair scandal','Iran seeks $290bn in damages against US']}
(ROOT/'edition.json').write_text(json.dumps(data,indent=2,ensure_ascii=False))
out=ROOT/'slides';out.mkdir(exist_ok=True)
for i,s in enumerate([None]+stories):
 art=Image.open(ROOT/f'art/{i:02d}.png').convert('RGB')
 frame(data,i+1,art,s).save(out/f'{i+1:02d}.jpg',quality=87,optimize=True)
caption='Asia in Seven Headlines | 23 November 2026\n\nDiplomacy, technology and public life across seven newspapers.\n\nTimes are local to each publisher. AI editorial illustrations.\n\nSources\n'+'\n'.join(s['url'] for s in stories)
assert len(caption)<2200
print('Caption characters:',len(caption))
(ROOT/'caption.txt').write_text(caption)
board=Image.new('RGB',(864,540),'white')
for i,f in enumerate(sorted(out.glob('*.jpg'))):
 im=Image.open(f);assert im.size==(1080,1350)
 board.paste(im.resize((216,270)),((i%4)*216,(i//4)*270))
board.save(ROOT/'preview.jpg')
