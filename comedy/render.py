"""Original, wordless black-and-white umbrella comedy. Pillow + FFmpeg.

python comedy/render.py --previews
python comedy/render.py --output comedy/out/umbrella-last-laugh.mp4
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import subprocess
import wave
import numpy as np
from PIL import Image,ImageDraw
from scipy import signal

HERE=Path(__file__).resolve().parent
W,H=720,1280
DURATION=27
FPS=30
BLACK=(18,18,18)
WHITE=(255,255,255)


def clamp(v,a=0.,b=1.):return max(a,min(b,v))
def ease(t,a,b):
    p=clamp((t-a)/(b-a));return p*p*(3-2*p)
def mix(a,b,p):return a+(b-a)*p
def point(a,b,p):return (mix(a[0],b[0],p),mix(a[1],b[1],p))


class Ink:
    def __init__(self,width=1080):
        self.s=2
        self.width=width
        self.im=Image.new('RGB',(W*self.s,H*self.s),'white')
        self.d=ImageDraw.Draw(self.im)
    def xy(self,p):return tuple(round(v*self.s) for v in p)
    def line(self,pts,w=2.8,fill=BLACK,round_ends=True):
        coords=[self.xy(p) for p in pts]
        self.d.line(coords,fill=fill,width=max(1,round(w*self.s)),joint='curve')
        if round_ends:
            r=w*self.s/2
            for x,y in (coords[0],coords[-1]):self.d.ellipse((x-r,y-r,x+r,y+r),fill=fill)
    def ellipse(self,box,fill=None,w=2.5,outline=BLACK):
        self.d.ellipse(tuple(round(v*self.s) for v in box),fill=fill,outline=outline,width=max(1,round(w*self.s)))
    def polygon(self,pts,fill=WHITE,w=2.5):
        self.d.polygon([self.xy(p) for p in pts],fill=fill)
        self.line([*pts,pts[0]],w)
    def curve(self,pts,w=2.8,fill=BLACK):
        pts=np.array(pts,float)
        u=np.linspace(0,1,30)
        if len(pts)==3:
            q=(1-u[:,None])**2*pts[0]+2*(1-u[:,None])*u[:,None]*pts[1]+u[:,None]**2*pts[2]
        else:
            q=(1-u[:,None])**3*pts[0]+3*(1-u[:,None])**2*u[:,None]*pts[1]+3*(1-u[:,None])*u[:,None]**2*pts[2]+u[:,None]**3*pts[3]
        self.line(q,w,fill)
    def finish(self):return self.im.resize((self.width,self.width*16//9),Image.Resampling.LANCZOS)


def drop(c,x,y,size=5,tilt=0):
    c.curve([(x,y-size),(x-size*.8,y+size*.2),(x-size*.45,y+size),(x,y+size)],1.5)
    c.curve([(x,y+size),(x+size*.9,y+size*.5),(x+size*.4,y),(x,y-size)],1.5)


def cloud(c,x,y,r=1):
    c.curve([(x-115*r,y+22*r),(x-145*r,y-25*r),(x-83*r,y-47*r),(x-58*r,y-25*r)],2)
    c.curve([(x-58*r,y-25*r),(x-61*r,y-87*r),(x+30*r,y-92*r),(x+43*r,y-37*r)],2)
    c.curve([(x+43*r,y-37*r),(x+114*r,y-72*r),(x+157*r,y+4*r),(x+107*r,y+22*r)],2)
    c.curve([(x+107*r,y+22*r),(x+35*r,y+35*r),(x-45*r,y+23*r),(x-115*r,y+22*r)],2)


def sun(c,t):
    x,y=550,300
    c.ellipse((x-47,y-47,x+47,y+47),WHITE,2.4)
    for n in range(12):
        a=n*math.tau/12;inner=62;outer=76+2*math.sin(t*2+n)
        c.line([(x+math.cos(a)*inner,y+math.sin(a)*inner),(x+math.cos(a)*outer,y+math.sin(a)*outer)],2.3)


def umbrella(c,x,y,inverted=0,tilt=0,fold=0,water=0,button=False):
    def tr(p):
        dx,dy=p
        a=tilt
        return (x+dx*math.cos(a)-dy*math.sin(a),y+dx*math.sin(a)+dy*math.cos(a))
    r=mix(142,13,fold)
    depth=mix(-102,65,inverted)
    depth=mix(depth,-125,fold)
    points=[]
    for u in np.linspace(-1,1,61):points.append(tr((u*r,depth*(1-u*u))))
    if inverted<.5:
        for u in np.linspace(1,-1,61):points.append(tr((u*r,10*abs(math.sin((u+1)*math.pi*2))*(1-fold))))
    else:
        for u in np.linspace(1,-1,61):points.append(tr((u*r,0)))
    # Draw the shaft before the canopy to keep the optical overlap clean.
    c.line([tr((0,depth)),tr((0,264))],3.1)
    c.curve([tr((0,264)),tr((0,294)),tr((35,294)),tr((33,267))],3)
    c.polygon(points,WHITE,2.9)
    for u in (-.55,0,.55):
        c.curve([tr((0,depth)),tr((u*r*.55,depth*.6)),tr((u*r,0))],1.5)
    for side in (-1,1):c.ellipse((*tr((side*r-2,-2)),*tr((side*r+2,2))),WHITE,1)
    if water>.02 and inverted>.55 and fold<.2:
        wy=9+max(0,1-water)*35
        half=r*math.sqrt(max(.05,1-wy/65))*.91
        c.ellipse((x-half,y+wy-6,x+half,y+wy+6),None,1.5)
        for dx in (-42,28):c.curve([(x+dx-14,y+wy),(x+dx,y+wy+4),(x+dx+14,y+wy)],1)
    if button:c.ellipse((x-4,y+223,x+4,y+235),WHITE,1.5)


def arm(c,shoulder,wrist,side=1,pointing=False,fist=False):
    sx,sy=shoulder;wx,wy=wrist
    delta=np.array([wx-sx,wy-sy],float);dist=np.linalg.norm(delta)
    mid=(np.array(shoulder)+np.array(wrist))/2
    perp=np.array([-delta[1],delta[0]])/max(1,dist)
    bend=min(53,max(9,math.sqrt(max(0,118**2-(dist/2)**2))))
    elbow=mid+perp*side*bend
    c.line([shoulder,elbow,wrist],3)
    if pointing:
        c.ellipse((wx-5,wy-4,wx+5,wy+4),WHITE,2)
        c.line([(wx,wy),(wx-24,wy-2)],2.5)
        c.line([(wx+2,wy+2),(wx-8,wy+8)],1.8)
    elif fist:
        c.ellipse((wx-7,wy-6,wx+7,wy+6),WHITE,2)
        c.line([(wx-3,wy-5),(wx-3,wy+1)],1.2)
    else:
        c.ellipse((wx-4,wy-4,wx+4,wy+4),WHITE,2)


def face(c,x,y,emotion,t,look=1,who='A'):
    r=48
    c.ellipse((x-r,y-r,x+r,y+r),WHITE,3)
    # Distinct minimal hair signatures keep the two characters recognizable.
    if who=='A':
        for dx in (-10,0,10):c.curve([(x+dx,y-r+2),(x+dx-6,y-r-10),(x+dx-1,y-r-14)],1.8)
    else:c.curve([(x+12,y-r+2),(x+30,y-r-12),(x+12,y-r-21),(x+7,y-r-9)],2)
    blink=((t+(0 if who=='A' else 1.1))%3.7)<.12
    for dx in (-17,17):
        ex=x+dx
        if emotion=='laugh':
            c.curve([(ex-8,y-2),(ex,y-10),(ex+8,y-2)],2.6)
        elif blink:
            c.line([(ex-7,y-1),(ex+7,y-1)],2)
        else:
            if emotion in ('annoyed','smug','angry'):
                c.ellipse((ex-8,y-5,ex+8,y+8),WHITE,1.6)
                c.line([(ex-8,y-2),(ex+8,y-2)],2)
                c.ellipse((ex-2+look*2,y-2,ex+2+look*2,y+5),BLACK,1)
            else:
                ey=9 if emotion in ('shock','hot') else 7
                c.ellipse((ex-7,y-ey,ex+7,y+ey),WHITE,1.7)
                c.ellipse((ex-2+look*2,y-4,ex+2+look*2,y+3),BLACK,1)
        if emotion=='angry':
            c.line([(ex-9,y-20+(-5 if dx<0 else 5)),(ex+9,y-20+(5 if dx<0 else -5))],3)
        elif emotion=='annoyed':
            c.curve([(ex-10,y-16),(ex,y-24+(5 if dx<0 else -3)),(ex+9,y-17)],2.4)
        elif emotion in ('shock','hot','beg'):
            c.curve([(ex-9,y-21),(ex,y-28),(ex+9,y-20)],2)
    if emotion=='laugh':
        c.ellipse((x-18,y+12,x+18,y+34),BLACK,2)
        c.curve([(x-15,y+15),(x,y+20),(x+15,y+15)],3.8,WHITE)
        c.curve([(x-9,y+29),(x,y+24),(x+9,y+29)],2,WHITE)
    elif emotion in ('shock','hot'):
        c.ellipse((x-6,y+17,x+6,y+33),WHITE,2.3)
        if emotion=='hot':c.curve([(x-2,y+26),(x+9,y+38),(x+12,y+24)],2)
    elif emotion=='angry':
        c.curve([(x-15,y+27),(x,y+15),(x+15,y+27)],2.8)
        for yy in (y-42,y-48):c.line([(x+34,yy),(x+42,yy-3)],1.7)
    elif emotion=='annoyed':c.line([(x-12,y+24),(x+12,y+24)],2.5)
    elif emotion=='sip':c.ellipse((x+11*look-5,y+18,x+11*look+5,y+24),WHITE,2)
    elif emotion=='beg':c.curve([(x-12,y+23),(x,y+16),(x+12,y+23)],2.3)
    else:c.curve([(x-14,y+17),(x,y+33),(x+16,y+15)],2.5)


def person(c,x,emotion,t,who='A',left=None,right=None,lean=0,bob=0,look=1,pointing=False,fists=False,wet=False,hot=False):
    hy=805+bob;hx=x+lean*25
    shoulder=(hx,hy+48);hip=(x,958+bob*.5)
    laugh=emotion=='laugh'
    # Grounded feet, bent knees and a flexible torso give weight to reactions.
    left_foot=(x-35,1104);right_foot=(x+39,1104)
    knee_l=(x-34-lean*14,1028+bob*.3)
    knee_r=(x+29-lean*14,1024+bob*.3)
    c.line([hip,knee_l,left_foot],3.5);c.line([hip,knee_r,right_foot],3.5)
    c.curve([shoulder,(hx-lean*30,898),(x+lean*14,927),hip],3.3)
    c.curve([(left_foot[0]+3,left_foot[1]),(left_foot[0]-11,left_foot[1]+5),(left_foot[0]-16,left_foot[1])],3)
    c.curve([(right_foot[0]-2,right_foot[1]),(right_foot[0]+12,right_foot[1]+4),(right_foot[0]+16,right_foot[1])],3)
    arm(c,shoulder,left or (x-62,971),-1,pointing,fists)
    arm(c,shoulder,right or (x+64,968),1,False,fists)
    face(c,hx,hy,emotion,t,look,who)
    if hot:
        for i in range(3):
            p=(t*.9+i*.31)%1;drop(c,hx+52+(i%2)*5,hy-28+p*65,3.5)
    if wet:
        for i in range(4):
            p=(t*1.1+i*.27)%1
            drop(c,hx-40+i*24,hy+31+p*55,3)
    return shoulder


def cup(c,x,y,tilt=0,water=True):
    def p(dx,dy):return (x+dx*math.cos(tilt)-dy*math.sin(tilt),y+dx*math.sin(tilt)+dy*math.cos(tilt))
    c.polygon([p(-15,-22),p(15,-22),p(12,19),p(-12,19)],WHITE,2.3)
    c.curve([p(15,-14),p(37,-20),p(36,12),p(13,9)],2.2)
    if water:c.line([p(-12,-10),p(12,-10)],1.4)


def frame(t,width=1080):
    c=Ink(width)
    raining=t<6.1
    if t<7.1:
        shift=ease(t,5.8,7.1)*850
        cloud(c,200-shift,260,.9);cloud(c,525+shift,305,.72)
    if t>6.2:sun(c,t)
    # Minimal ground and puddles. No colour, UI or text is used in the film.
    c.line([(62,1111),(662,1111)],1.8)
    if t<7.6 or t>17.2:
        if t<7.6:
            for x,rx in [(145,37),(352,62),(562,44)]:
                shrink=1-ease(t,6.3,7.6)
                if shrink>.02:c.ellipse((x-rx*shrink,1126-4*shrink,x+rx*shrink,1126+4*shrink),None,1.2)
        if t>17.2:
            size=ease(t,17.2,18.3)
            c.ellipse((505-84*size,1125-8*size,505+84*size,1125+8*size),None,1.6)
    if raining:
        for i in range(79):
            x=(i*137.3+t*53)%780-30;y=370+((i*83.71+t*570)%760)
            dry_b=(y>650 and 425<x<700)
            dry_a=(t<1.4 and y>650 and 145<x<415)
            if dry_b or dry_a:continue
            c.line([(x,y),(x-7,y+20)],1.1)
    # A deliberate anticipation pause makes the wind reversal readable.
    flip=ease(t,1.3,1.85)
    wobble=math.sin((t-1.5)*26)*math.exp(-max(0,t-1.5)*3)*.13 if 1.5<t<2.8 else 0
    if 1.05<t<2.5:
        drift=(t-1.05)*330
        for j in range(3):
            xx=-100+drift;yy=550+j*35
            c.curve([(xx,yy),(xx+70,yy-15),(xx+136,yy+10),(xx+200,yy-4)],1.6)
    if t<2.1:ae='shock' if t>1.35 else 'neutral'
    elif t<6.5:ae='annoyed'
    elif t<9.1:ae='smug'
    elif t<11.6:ae='sip' if t>10.3 else 'neutral'
    elif t<16.7:ae='smug'
    elif t<19.6:ae='shock'
    elif t<22.0:ae='laugh'
    else:ae='neutral'
    if t<2.2:be='neutral'
    elif t<5.4:be='laugh'
    elif t<7.5:be='smug'
    elif t<11.5:be='hot'
    elif t<14.5:be='beg'
    elif t<16.65:be='smug'
    elif t<18.3:be='shock'
    elif t<22.2:be='angry'
    elif t<24.2:be='annoyed'
    elif t<25.5:be='sip'
    else:be='neutral'
    ax,bx=212,515
    # A's one free hand dips, drinks, waits, then shares the remaining water.
    cup_pos=(150,960)
    cup_visible=t>8.45
    if t<9.45:cup_pos=point((150,960),(280,671),ease(t,8.45,9.45))
    elif t<10.6:cup_pos=point((280,671),(239,832),ease(t,9.65,10.6))
    elif t<11.7:cup_pos=(239+math.sin(t*4)*1.2,831)
    elif t<12.4:cup_pos=point((239,831),(163,929),ease(t,11.7,12.4))
    elif t<22.0:cup_pos=(163,929)
    elif t<23.8:cup_pos=point((163,929),(375,865),ease(t,22.0,23.8))
    elif t<24.6:cup_pos=point((375,865),(491,831),ease(t,23.8,24.6))
    else:cup_pos=(491,831)
    transfer=ease(t,14.4,16.0)
    umb_x=mix(280,580,transfer)
    a_right=(umb_x,900) if transfer<.5 else point((430,900),(273,958),ease(t,15.1,16.1))
    if t>=16:a_right=(273,958)
    a_left=(cup_pos[0]-16,cup_pos[1]+3) if cup_visible and t<23.8 else (150,966)
    if ae=='laugh':a_right=(245,925)
    b_right=(580,900)
    if 7.0<t<8.2:b_right=(580,900)
    elif 8.2<=t<14.4:b_right=(580,969)
    elif 14.4<=t<16:b_right=(umb_x,900)
    elif t>=16:b_right=(580,900)
    b_left=(453,973)
    if be=='laugh':b_left=(414,866+math.sin(t*14)*4)
    elif be=='hot':b_left=(552,782+math.sin(t*4)*6)
    elif be=='beg':b_left=point((453,973),(365,871),ease(t,11.5,12.25))
    elif 14.4<=t<16.5:b_left=(548,862)
    elif 16.5<=t<17:b_left=(580,882)
    elif be=='angry':b_left=(448,900+math.sin(t*19)*3)
    elif 22.0<t<23.8:b_left=point((448,900),(391,865),ease(t,22.3,23.8))
    elif t>=23.8:b_left=(cup_pos[0]+16,cup_pos[1]+3)
    abob=math.sin(t*16)*4+8 if ae=='laugh' else 0
    bbob=math.sin(t*16)*4+7 if be=='laugh' else 0
    alean=.75 if ae=='laugh' else -.42 if ae=='shock' and t<2.1 else -.18 if ae=='annoyed' else 0
    blean=-.5 if be=='hot' else -.52 if be=='laugh' else -.3 if be=='sip' else 0
    if be=='hot':
        bbob+=22
        b_left=(b_left[0]-8,b_left[1]+22)
    if be=='angry':bx+=math.sin(t*22)*1.8
    person(c,ax,ae,t,'A',a_left,a_right,lean=alean,bob=abob,look=1,wet=2<t<6.1)
    person(c,bx,be,t,'B',b_left,b_right,lean=blean,bob=bbob,look=-1,pointing=be=='laugh',fists=be=='angry',wet=17.1<t<24,hot=7.5<t<14)
    # The untouched umbrella is folded and put down before the handover.
    if t<8.2:
        folding=ease(t,7.1,7.9)
        umbrella(c,580,650+folding*170,fold=folding)
    else:
        umbrella(c,652,833,fold=1,tilt=-.12)
    # Flip back toward normal when B presses the button, spilling the stored rain.
    snap=ease(t,16.6,16.92)
    invert=flip*(1-snap)
    water=ease(t,1.9,5.9)*(1-ease(t,16.72,17.2))
    umbrella(c,umb_x,650,inverted=invert,tilt=wobble,water=water,button=transfer>.7)
    if 16.45<t<16.85:
        for j in range(5):
            a=math.pi+j*math.pi/4
            c.line([(580+math.cos(a)*17,878+math.sin(a)*17),(580+math.cos(a)*24,878+math.sin(a)*24)],1.6)
    if 16.85<t<18.65:
        p=clamp((t-16.85)/.8)
        # Falling arcs start at the canopy and land on B, not arbitrary particles.
        for i in range(11):
            phase=clamp((t-16.85-i*.035)/.7)
            if not 0<phase<1:continue
            sx=480+i*17;xx=mix(sx,515+(i-5)*6,phase)
            yy=660+phase*phase*385
            c.curve([(sx,660),(mix(sx,xx,.4),710),(xx,yy)],1.35)
            drop(c,xx,yy,4)
        if 17.25<t<18.25:
            for side in (-1,1):
                for j in range(4):
                    x=515+side*(55+j*12);y=774+j*21
                    c.curve([(515+side*47,777),(x,y-16),(x+side*10,y+7)],1.5)
    if cup_visible:
        tilt=-.35 if 10.5<t<11.6 else .35 if t>24.4 else 0
        cup(c,*cup_pos,tilt=tilt,water=t<25.2)
    if 18.7<t<20.6:
        # Angry nonverbal punctuation, drawn as short stress lines, not words.
        for j in range(3):
            x=561+j*10;y=727+j*7
            c.line([(x,y),(x+7,y-10)],1.7)
    return c.finish()


SR=48000


def voice(duration=.22,pitch=190,vowel='a',seed=1):
    rng=np.random.default_rng(seed);t=np.arange(int(SR*duration))/SR
    f=pitch*(1-.17*t/max(duration,.01))*(1+.015*np.sin(2*np.pi*6*t))
    phase=np.cumsum(f)/SR
    flow=np.maximum(0,np.sin(2*np.pi*phase))**3
    excitation=np.diff(flow,prepend=flow[0])+rng.normal(0,.018,len(t))
    formants=(730,1090,2440) if vowel=='a' else (450,900,2200)
    result=np.zeros(len(t))
    for center,gain,q in zip(formants,(1,.7,.28),(7,9,12)):
        b,a=signal.iirpeak(center,q,fs=SR)
        part=signal.lfilter(b,a,excitation)
        part/=max(.001,np.sqrt(np.mean(part*part)))
        result+=gain*part
    result/=max(1,np.max(np.abs(result)))
    env=np.minimum(1,t/.018)*np.minimum(1,(duration-t)/.035)*np.exp(-1.25*t/duration)
    return result*env


def soundtrack(path):
    rng=np.random.default_rng(491);audio=np.zeros((DURATION*SR,2),np.float64)
    def add(start,sound,gain=.3,pan=0):
        at=int(start*SR);length=min(len(sound),len(audio)-at)
        if length<=0:return
        gains=np.array([math.sqrt((1-pan)/2),math.sqrt((1+pan)/2)])
        audio[at:at+length]+=np.asarray(sound[:length])[:,None]*gains*gain
    def noise(d,cut=2500):
        n=rng.normal(size=int(SR*d));sos=signal.butter(2,cut,fs=SR,output='sos')
        return signal.sosfilt(sos,n)
    def tone(d,hz,fall=0):
        tt=np.arange(int(SR*d))/SR
        return np.sin(2*np.pi*(hz*tt+fall*tt*tt/2))*np.exp(-tt*7/d)
    def laugh(start,pitch,pan):
        for i in range(6):
            add(start+i*.235,voice(.19,pitch+(i%3)*14,'a',i+int(start*50)),.34 if i<4 else .22,pan)
        puff=noise(.13,1700)*np.linspace(1,0,int(SR*.13))
        add(start+1.43,puff,.1,pan)
    rain=noise(6.5,8500)
    envelope=np.clip(np.arange(len(rain))/SR/.35,0,1)*np.clip((6.45-np.arange(len(rain))/SR)/.7,0,1)
    add(0,rain*envelope,.045)
    gust=noise(1.1,1400)*np.sin(np.linspace(0,np.pi,int(SR*1.1)))**2
    add(1.05,gust,.3,-.3)
    for start in (1.5,16.72):
        tt=np.arange(int(SR*.36))/SR
        spring=signal.chirp(tt,f0=320,f1=90,t1=.36)*np.exp(-tt*13)
        add(start,spring,.22)
    laugh(2.4,175,.35)
    add(4.35,voice(.38,125,'u',45),.28,-.35)
    add(6.6,tone(.42,1175),.07)
    add(6.77,tone(.4,1568),.06)
    for start in (7.9,8.32):add(start,noise(.18,1300)*np.hanning(int(SR*.18)),.18,.4)
    for start in (9.3,9.55,10.55,10.85,23.95,24.2):
        add(start,tone(.11,740,2100),.1,-.3 if start<12 else .3)
    slurp=noise(.32,3300)*(.3+.7*np.sin(np.arange(int(SR*.32))/SR*70)**2)*np.hanning(int(SR*.32))
    add(10.65,slurp,.18,-.3)
    add(11.15,voice(.3,155,'a',50),.16,-.3)
    add(12.55,voice(.42,205,'u',60),.17,.3)
    click=noise(.025,6500)*np.exp(-np.arange(int(SR*.025))/SR*180)
    add(16.56,click,.45,.35)
    splash=noise(.8,6500)*np.exp(-np.arange(int(SR*.8))/SR*4)
    add(17.0,splash,.35,.25)
    for start in (17.5,18.0,18.6,20.0):add(start,tone(.15,600,1500),.09,.3)
    add(18.35,voice(.35,112,'u',68),.27,.35)
    grumble=voice(.62,87,'u',77)
    grumble*=.7+.3*np.sin(np.arange(len(grumble))/SR*math.tau*23)
    add(19.05,grumble,.32,.35)
    laugh(20.0,225,-.35)
    add(23.5,tone(.13,1280),.12)
    add(24.35,slurp,.17,.35)
    for i in range(3):add(25.2+i*.23,voice(.18,160+i*10,'a',90+i),.15,.3)
    # Original effects only: no dialogue, copyrighted clips or stock laugh track.
    fade=np.minimum(1,np.arange(len(audio))/(SR*.05))*np.minimum(1,(len(audio)-np.arange(len(audio)))/(SR*.35))
    audio*=fade[:,None]
    audio=np.tanh(audio*1.15)
    peak=np.max(np.abs(audio));audio*=.88/max(.88,peak)
    with wave.open(str(path),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR)
        f.writeframes((audio*32767).astype('<i2').tobytes())


def previews(directory):
    directory.mkdir(parents=True,exist_ok=True)
    times=[.7,1.8,3.5,8.3,10.8,14.9,17.4,19.2,22.9,25.8]
    sheet=Image.new('RGB',(1440,1024),'white')
    for i,t in enumerate(times):
        image=frame(t,288);sheet.paste(image,((i%5)*288,(i//5)*512))
        image.save(directory/f'frame-{i+1:02}.png')
    sheet.save(directory/'storyboard.png')
    poses=Image.new('RGB',(1440,960),'white')
    for i,emotion in enumerate(['neutral','shock','annoyed','laugh','hot','beg','angry','sip']):
        c=Ink(720)
        person(c,360,emotion,2+i*.31,'A' if i%2==0 else 'B',left=(280,880) if emotion=='laugh' else None,right=(430,870) if emotion=='beg' else None,look=1)
        crop=c.im.crop((430,1440,1010,2260)).resize((290,410),Image.Resampling.LANCZOS)
        poses.paste(crop,((i%4)*360+35,(i//4)*480+25))
    poses.save(directory/'character-sheet.png')


def render(output,width=1080,fps=30):
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    wav=output.with_suffix('.wav');soundtrack(wav)
    cmd=['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{width*16//9}','-r',str(fps),'-i','pipe:0','-i',str(wav),'-t',str(DURATION),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-af','loudnorm=I=-18:TP=-1.5:LRA=9','-ar','48000','-c:a','aac','-b:a','192k','-movflags','+faststart',str(output)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for i in range(DURATION*fps):
            proc.stdin.write(frame(i/fps,width).tobytes())
            if i%(fps*3)==0:print(f'Rendered {i/fps:.0f}/{DURATION}s',flush=True)
        proc.stdin.close();error=proc.stderr.read().decode()
        if proc.wait()!=0:raise RuntimeError(error)
    except BaseException:
        proc.kill();proc.wait();raise
    output.with_suffix('.json').write_text(json.dumps({'title':'The Last Laugh','duration':DURATION,'width':width,'height':width*16//9,'fps':fps,'style':'Original black ink on white; wordless stick-figure comedy','audio':'Original synthesized nonverbal cartoon laughter, grunts and foley','published':False},indent=2))
    print(output,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--previews',action='store_true');p.add_argument('--output',default=str(HERE/'out/umbrella-last-laugh.mp4'));p.add_argument('--width',type=int,default=1080);p.add_argument('--fps',type=int,default=30)
    a=p.parse_args()
    if a.previews:previews(HERE/'out')
    else:render(a.output,a.width,a.fps)
