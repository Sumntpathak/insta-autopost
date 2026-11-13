"""Original 15-second animated stories about getting unstuck."""
import argparse
from functools import lru_cache
import math
from pathlib import Path
import subprocess
import sys
import wave

from PIL import Image, ImageDraw, ImageFont
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reels/pythonic/upstream/shared'))
from race_kit import Mixer, SR

STORIES = [
    ('Beat distraction', 'PHONE', 'MUTE IT', 'FOCUS', '#2054ec', '#ed694e'),
    ('Start before you feel ready', 'DOUBT', 'ONE STEP', 'COURAGE', '#196a54', '#e88443'),
    ('Make the habit smaller', 'TOO MUCH', 'TEN MIN', 'MOMENTUM', '#6739bd', '#f27365'),
    ('Protect your time', 'REQUESTS', 'SAY NO', 'TIME BACK', '#245db4', '#df6641'),
    ('Finish one thing', 'NEW IDEAS', 'PICK ONE', 'FINISHED', '#235e83', '#d75979'),
    ('Practice past the miss', 'MISTAKES', 'TRY AGAIN', 'PROGRESS', '#6553c6', '#dc614f'),
    ('Trade scrolling for sleep', 'SCROLLING', 'LOG OFF', 'REST', '#245c83', '#e06a4d'),
    ('Ask for help sooner', 'STUCK', 'REACH OUT', 'UNSTUCK', '#33703d', '#e27847'),
    ('Build a buffer', 'SURPRISES', 'PLAN AHEAD', 'BREATHING ROOM', '#215dbe', '#dd664b'),
    ('Compare less. Create more.', 'COMPARISON', 'MAKE IT', 'YOUR PACE', '#7143af', '#d85e4d'),
]
W,H=720,1280
INK='#172438'
PAPER='#faf7ef'

@lru_cache(maxsize=40)
def font(size, bold=True):
    file='DejaVuSans-Bold' if bold else 'DejaVuSans'
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/'+file+'.ttf',size)

def label(d, x,y,word,size,color=INK,anchor='mm'):
    face=font(size)
    d.text((x,y),word,font=face,fill=color,anchor=anchor)

def ease(x):
    x=max(0,min(1,x))
    return x*x*(3-2*x)

def disk(d,x,y,r,fill):
    d.ellipse((x-r,y-r,x+r,y+r),fill=fill)

def spark(d,x,y,r,fill):
    d.polygon([(x,y-r),(x+r*.22,y-r*.22),(x+r,y),(x+r*.22,y+r*.22),
               (x,y+r),(x-r*.22,y+r*.22),(x-r,y),(x-r*.22,y-r*.22)],fill=fill)

def body(d,x,y,blue,t,hit):
    bob=2*math.sin(t*12)
    d.rounded_rectangle((x-57,y+31,x+65,y+45),radius=7,fill='#24334d')
    d.rounded_rectangle((x-57,y+25,x+65,y+36),radius=6,fill=blue)
    d.line((x-15,y-1,x+29,y+9,x+42,y+30),fill=INK,width=18,joint='curve')
    d.line((x-24,y+9,x+8,y+18,x+20,y+31),fill=INK,width=15,joint='curve')
    d.rounded_rectangle((x-47,y-54+bob,x+8,y+23),radius=24,fill=INK)
    d.rounded_rectangle((x-42,y-50+bob,x+4,y+17),radius=21,fill=blue)
    disk(d,x-18,y-70+bob,22,INK)
    disk(d,x-18,y-72+bob,18,'#ffe7c9')
    if hit:
        d.line((x-7,y-73,x+3,y-68),fill=INK,width=3)
        d.line((x-7,y-65,x+3,y-68),fill=INK,width=3)
    else:
        disk(d,x-7,y-74+bob,3,INK)
    d.line((x-17,y-28,x+15,y-12,x+34,y-26 if hit else y-5),fill=INK,width=12,joint='curve')
    disk(d,x+34,y-26 if hit else y-5,6,'#ffe7c9')

def frame(t,idx):
    title, obstacle, action, prize, blue, orange=STORIES[idx]
    im=Image.new('RGB',(W,H),PAPER)
    d=ImageDraw.Draw(im)
    label(d,53,116,'SHIPSTACK',19,blue,'lm')
    d.line((53,148,666,148),fill='#d4d8d7',width=2)
    size=48
    while font(size).getlength(title)>620:
        size-=1
    label(d,53,209,title,size,INK,'lm')
    d.rounded_rectangle((48,288,672,1082),radius=40,fill='#dedbd4')
    d.rounded_rectangle((48,278,672,1069),radius=40,fill='#ffffff')
    for x in range(86,650,29):
        for y in range(308,1040,29):
            disk(d,x,y,1,'#e6e8e8')
    lane=228+(idx%3)*12
    goal_y=365
    floor=976
    fail_y=618+(idx%4)*19
    fall_start=3.65+idx*.06
    recovery=fall_start+.79
    intervention=5.32+idx*.055
    arrive=9.65+idx*.09
    if t<fall_start:
        y=floor-(floor-fail_y)*ease(t/fall_start)
    elif t<recovery:
        y=fail_y+(floor-fail_y)*((t-fall_start)/.79)**1.65
    else:
        y=floor-(floor-goal_y-38)*ease((t-intervention)/(arrive-intervention))
    progress=(floor-y)/(floor-goal_y-38)
    d.rounded_rectangle((lane-12,goal_y,lane+12,floor+23),radius=9,fill='#dce3e9')
    d.rounded_rectangle((lane-5,y+7,lane+5,floor+23),radius=5,fill=blue)
    for n in range(8):
        sy=goal_y+70+n*67
        d.line((lane-34,sy,lane-25,sy),fill='#b4bec6',width=3)
    disk(d,lane,goal_y,37,blue if t>=arrive else '#ecf0f4')
    spark(d,lane,goal_y,24,'#ffffff' if t>=arrive else blue)
    label(d,lane+65,goal_y,prize,28,blue,'lm')

    cannon_x=556-(idx%2)*21
    d.rounded_rectangle((cannon_x-48,fail_y-108,cannon_x+57,fail_y+108),radius=20,fill='#eff0ee')
    label(d,cannon_x,fail_y-140,obstacle,23,orange)
    for j in (-1,0,1):
        cy=fail_y-27+j*44
        d.rounded_rectangle((cannon_x-62,cy-12,cannon_x+30,cy+12),radius=9,fill=INK)
        shot=(t-fall_start+.32-j*.055)/.32
        if 0<shot<1.07:
            x=cannon_x-63-(cannon_x-lane-108)*shot
            d.rounded_rectangle((x-15,cy-7,x+12,cy+7),radius=7,fill=orange)
        shot=(t-(intervention+2.05)+.27-j*.07)/.37
        if 0<shot<1:
            x=cannon_x-63-(cannon_x-476)*shot
            d.rounded_rectangle((x-15,cy-7,x+12,cy+7),radius=7,fill=orange)
        if 1<shot<1.21:
            spark(d,414,cy,17*(1.21-shot)/.21,orange)
    if t>=intervention:
        extent=ease((t-intervention)/.30)
        if extent>.04:
            d.rounded_rectangle((391,fail_y-111*extent,413,fail_y+111*extent),radius=10,fill=blue)
        label(d,402,fail_y+150,action,23,blue)
    if fall_start<=t<fall_start+.29:
        spark(d,lane+59,fail_y-26,40*(1-(t-fall_start)/.30),orange)
    body(d,lane+15,y,blue,t,fall_start<=t<recovery)
    if t>=arrive:
        age=t-arrive
        for n in range(11):
            a=n*math.tau/11
            radius=43+min(2,age)*56
            spark(d,lane+math.cos(a)*radius,goal_y+math.sin(a)*radius,
                  max(3,10-age*3),blue if n%2 else orange)
    message = ('The first setback' if t<recovery else
               'Change one thing' if t<intervention else
               action if t<arrive else 'Small change. Different outcome.')
    label(d,360,1125,message,27,blue if t>=intervention else INK)
    return im

def render(idx, out):
    t0=3.65+idx*.06
    t1=5.32+idx*.055
    end=9.65+idx*.09
    mixer=Mixer(15)
    mixer.beat(105+idx,roots=(110,130.81,146.83,98))
    mixer.mus*=.35
    for t in (1,2,3,6.8,7.5,8.7):
        mixer.ping(t,360+idx*13,.075)
    mixer.impact(t0,.65)
    mixer.thud(t0+.78,.34)
    mixer.ping(t1,660,.18)
    mixer.crack(t1+2.05,.28)
    mixer.chord(end,[523,659,784],.13)
    wav=out.with_suffix('.wav')
    with wave.open(str(wav),'wb') as f:
        f.setparams((1,2,SR,0,'NONE','not compressed'))
        f.writeframes((np.clip(mixer.final(),-1,1)*32767).astype(np.int16).tobytes())
    cmd=['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','30','-i','-',
         '-i',str(wav),'-vf','scale=1080:1920','-c:v','libx264','-threads','3','-preset','veryfast',
         '-crf','18','-pix_fmt','yuv420p','-c:a','aac','-ar','48000','-b:a','128k','-t','15',
         '-movflags','+faststart',str(out)]
    try:
        with subprocess.Popen(cmd,stdin=subprocess.PIPE) as proc:
            for n in range(450):
                proc.stdin.write(frame(n/30,idx).tobytes())
            proc.stdin.close()
            if proc.wait():
                raise RuntimeError('Encoding failed')
    finally:
        wav.unlink(missing_ok=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('index',type=int,choices=range(10))
    p.add_argument('output',type=Path)
    p.add_argument('--stills',action='store_true')
    a=p.parse_args()
    if a.stills:
        sheet=Image.new('RGB',(1080,640))
        for n,t in enumerate((3.77,7.43,10.6)):
            sheet.paste(frame(t,a.index).resize((360,640)),(n*360,0))
        sheet.save(a.output)
    else:
        render(a.index,a.output)
