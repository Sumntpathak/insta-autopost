"""ShipStack track race: deterministic original 15-second challenge.
Usage: python reels/experiments/track_race.py --out race.mp4
Requires: numpy, Pillow, ffmpeg. Preview: --width 360
No Instagram API calls or publishing.
"""
import argparse, math, os, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS=30
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def render(out,width=1080):
    height=width*16//9
    s=width/1080
    P=lambda x:round(x*s)
    font=lambda n:ImageFont.truetype(FONT,max(10,P(n)))
    colors=[(65,229,246),(255,175,72)]
    def track(t,k):
        return (105+870*t,840+(130 if k==0 else 375)*math.sin(math.pi*t)**2)
    def travel(k):
        ts=np.linspace(0,1,1501)
        pts=np.array([track(float(t),k) for t in ts])
        distance=np.linalg.norm(np.diff(pts,axis=0),axis=1)
        drop=np.maximum(pts[:-1,1]-840,5)
        return float(np.sum(distance/(np.sqrt(2*980*drop)+65)))
    times=[travel(0),travel(1)]
    winner=int(np.argmin(times))
    race_start=2.6
    race_duration=8.6
    progress=lambda sec,k:min(1,max(0,(sec-race_start)/(times[k]/max(times)*race_duration)))
    os.makedirs(os.path.dirname(os.path.abspath(out)),exist_ok=True)
    audio=out+'.wav'
    sr=24000
    samples=np.zeros(sr*15,dtype=np.float64)
    def tone(t,f,d=.12,vol=.17):
        start=int(t*sr)
        n=min(int(d*sr),len(samples)-start)
        if n<=0:return
        u=np.arange(n)/sr
        samples[start:start+n]+=vol*np.minimum(1,u/.006)*np.exp(-u*26)*(np.sin(2*np.pi*f*u)+.24*np.sin(4*np.pi*f*u))
    for t in np.arange(0,12,.5):tone(float(t),220 if int(t*2)%2 else 330,.10,.08)
    for k in range(2):
        for p in (.25,.5,.75,1):
            tone(race_start+p*times[k]/max(times)*race_duration,(550 if k==0 else 660)+p*180,.16,.18)
    for i,f in enumerate((523,659,784,1046)):tone(11.7+i*.18,f,.3,.21)
    peak=max(1,float(np.max(np.abs(samples))/.86))
    with wave.open(audio,'wb') as wf:
        wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(sr)
        wf.writeframes(np.int16(np.clip(samples/peak,-1,1)*32767).tobytes())
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{width}x{height}','-framerate','30','-i','pipe:0','-i',audio,'-c:v','libx264','-preset','ultrafast','-crf','24','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-t','15','-movflags','+faststart',out]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for frame in range(450):
            sec=frame/FPS
            im=Image.new('RGB',(width,height),(7,10,19))
            d=ImageDraw.Draw(im)
            for j in range(22):
                y=P(180+j*74)
                d.line((P(50),y,P(1030),y),fill=(13,19,32),width=max(1,P(1)))
            d.text((P(85),P(100)),'SHIPSTACK / LAB 01',font=font(31),fill=colors[0])
            d.text((P(85),P(205)),'WHICH BALL',font=font(77),fill='white')
            d.text((P(85),P(300)),'WINS THE RACE?',font=font(71),fill='white')
            d.text((P(85),P(420)),'A vs B - PICK BEFORE THE REVEAL',font=font(29),fill=(142,155,180))
            for k in range(2):
                pts=[tuple(map(P,track(i/180,k))) for i in range(181)]
                d.line(pts,fill=(35,47,65),width=P(18))
                d.line(pts,fill=colors[k],width=max(2,P(5)))
            for k in range(2):
                t=progress(sec,k)
                x,y=map(P,track(t,k))
                r=P(25)
                d.ellipse((x-r,y-r,x+r,y+r),fill=colors[k])
                d.ellipse((x-r//2,y-r//2,x-r//6,y-r//6),fill='white')
                d.text((x-P(14),y-P(82)),'AB'[k],font=font(42),fill=colors[k])
            d.line((P(975),P(770),P(975),P(1000)),fill='white',width=P(6))
            for y in range(780,1000,30):
                d.rectangle((P(976),P(y),P(994),P(y+15)),fill='white')
            if sec<race_start:status=f'GET READY {max(1,math.ceil(race_start-sec))}'
            elif sec<race_start+race_duration:status=f'RACING - {max(0,race_start+race_duration-sec):04.1f}s'
            else:status=f'BALL {"AB"[winner]} WINS!'
            d.rounded_rectangle((P(85),P(1250),P(995),P(1435)),radius=P(36),fill=(21,29,46))
            d.text((P(120),P(1300)),status,font=font(55),fill=colors[winner] if sec>=race_start+race_duration else 'white')
            d.text((P(90),P(1540)),'DID YOU GUESS RIGHT?',font=font(51),fill='white')
            d.text((P(90),P(1630)),'COMMENT A OR B - FOLLOW FOR MORE',font=font(27),fill=(142,155,180))
            proc.stdin.write(im.tobytes())
    finally:
        proc.stdin.close()
        code=proc.wait()
        os.remove(audio)
    if code:raise RuntimeError(f'ffmpeg exited {code}')
    print(f'Winner: {"AB"[winner]}, estimated traversal times: {times}')

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',default='track_race.mp4')
    ap.add_argument('--width',type=int,default=1080)
    args=ap.parse_args()
    render(args.out,args.width)
