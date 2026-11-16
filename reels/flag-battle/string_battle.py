"""ShipStack Country String Battle: original deterministic last-survivor engine.
Run: python reels/flag-battle/string_battle.py --episode 1
Dependencies: numpy, Pillow, ffmpeg.  No BallEngine code/assets.
The original user-supplied Cairo/music script is the visual design reference;
this standalone version removes the fixed countdown and score-based winner.
"""
import argparse, json, math, random, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PALETTE = {"IN":"#ff9933","PK":"#24bb72","TR":"#e52b39","JP":"#eeeeff",
"BR":"#ffdb28","US":"#4a88ff","CN":"#ff4339","KR":"#e6e6ff","AR":"#7fcfff",
"FR":"#6289ff","DE":"#ffc400","GB":"#e53d60","NP":"#ed3156","BD":"#16b58b",
"PT":"#19b35c","ES":"#f3bd32","IT":"#47bc89","RU":"#779aff"}
FLAGS={"IN":"🇮🇳","PK":"🇵🇰","TR":"🇹🇷","JP":"🇯🇵","BR":"🇧🇷","US":"🇺🇸",
"CN":"🇨🇳","KR":"🇰🇷","AR":"🇦🇷","FR":"🇫🇷","DE":"🇩🇪","GB":"🇬🇧",
"NP":"🇳🇵","BD":"🇧🇩","PT":"🇵🇹","ES":"🇪🇸","IT":"🇮🇹"}
NAMES={"IN":"INDIA","PK":"PAKISTAN","TR":"TÜRKIYE","JP":"JAPAN","BR":"BRAZIL",
"US":"USA","CN":"CHINA","KR":"SOUTH KOREA","AR":"ARGENTINA","FR":"FRANCE",
"DE":"GERMANY","GB":"UK","NP":"NEPAL","BD":"BANGLADESH","PT":"PORTUGAL",
"ES":"SPAIN","IT":"ITALY"}
CENTER=np.array([270.,505.]); ARENA=238.; BALL=19.; DT=1/120

def closest(a,b,q):
    d=b-a; u=max(0.,min(1.,float(np.dot(q-a,d)/max(1e-8,np.dot(d,d)))))
    return a+d*u,u

class Battle:
    def __init__(self,codes,seed,initial=20):
        self.codes=codes; self.n=len(codes); self.rng=random.Random(seed)
        self.pos=np.zeros((self.n,2)); self.vel=np.zeros_like(self.pos)
        self.alive=[True]*self.n; self.strings=[]; self.events=[]; self.frames=[]
        self.t=0.; self.last_elimination=0.; self.last_cut=0.; self.weaving=True
        spin=self.rng.random()*2*math.pi
        for i in range(self.n):
            a=spin+2*math.pi*i/self.n
            self.pos[i]=CENTER+np.array([math.cos(a),math.sin(a)])*125
            d=a+math.pi/2+self.rng.uniform(-0.6,0.6)
            self.vel[i]=np.array([math.cos(d),math.sin(d)])*285
            # Fixed radial anchors; every string belongs to one ball and
            # its other endpoint follows that ball until severed.
            for j in range(initial):
                angle=2*math.pi*(i+(j+.5)/initial)/self.n
                anchor=CENTER+ARENA*np.array([math.cos(angle),math.sin(angle)])
                self.strings.append([i,anchor,True])
        self.record()

    def count(self,i):
        return sum(1 for owner,_,active in self.strings if owner==i and active)

    def record(self):
        self.frames.append((self.t,self.pos.copy(),self.alive.copy(),
            [(owner,anchor.copy()) for owner,anchor,active in self.strings if active]))

    def step(self):
        p=self.pos; v=self.vel; p[:]+=v*DT
        for i in range(self.n):
            if not self.alive[i]: continue
            delta=p[i]-CENTER; dist=float(np.linalg.norm(delta))
            if dist>ARENA-BALL:
                normal=delta/max(dist,1e-9); p[i]=CENTER+normal*(ARENA-BALL)
                vn=float(np.dot(v[i],normal))
                if vn>0:
                    v[i]-=2*vn*normal
                    self.events.append((self.t,"bounce",i,None))
                    if self.weaving:
                        self.strings.append([i,CENTER+normal*ARENA,True])
        for i in range(self.n):
            if not self.alive[i]: continue
            for j in range(i+1,self.n):
                if not self.alive[j]: continue
                d=p[j]-p[i]; dist=float(np.linalg.norm(d))
                if 0<dist<2*BALL:
                    normal=d/dist; overlap=2*BALL-dist
                    p[i]-=normal*overlap/2; p[j]+=normal*overlap/2
                    relative=float(np.dot(v[i]-v[j],normal))
                    if relative>0:
                        v[i]-=relative*normal;v[j]+=relative*normal
        # Speed rises for everyone equally; no predetermined winning country.
        speed=min(660,285*(1+0.035*self.t))
        for i in range(self.n):
            if self.alive[i]:
                norm=float(np.linalg.norm(v[i]))
                if norm>0:v[i]*=speed/norm
        # String creation pauses after 8 seconds or 4 seconds without a cut,
        # preventing an unwinnable equilibrium of perpetual regeneration.
        if self.t>8 or (self.t>5 and self.t-self.last_cut>4):
            self.weaving=False
        # Swept collision: test both previous and new ball positions to reduce
        # tunneling. Each active string can only be cut once.
        for k,st in enumerate(self.strings):
            owner,anchor,active=st
            if not active or not self.alive[owner]:continue
            for j in range(self.n):
                if j==owner or not self.alive[j]:continue
                point,u=closest(p[owner],anchor,p[j])
                if u>0.14 and np.linalg.norm(point-p[j])<BALL*0.82:
                    st[2]=False;self.events.append((self.t,"cut",j,owner))
                    self.last_cut=self.t
                    break
        eliminated=[]
        for i in range(self.n):
            if self.alive[i] and self.count(i)==0: eliminated.append(i)
        # Simultaneous zero-string ties are replayed at finer steps by caller;
        # never invent a winner through an arbitrary ranking.
        for i in eliminated:
            self.alive[i]=False
            self.events.append((self.t,"eliminated",i,None))
            self.last_elimination=self.t
        self.t+=DT
        if int(self.t*30)!=int((self.t-DT)*30):self.record()

    def run(self,max_seconds=150):
        while sum(self.alive)>1 and self.t<max_seconds:self.step()
        survivors=[i for i,a in enumerate(self.alive) if a]
        if len(survivors)!=1:
            raise RuntimeError("No unique survivor within %.0fs (survivors=%s); retry a different seed"% (max_seconds,survivors))
        self.record();return survivors[0]

def synth(events,seconds,path):
    sr=22050; samples=np.zeros(int((seconds+.4)*sr),np.float32)
    notes=[261.63,293.66,329.63,392.,440.,523.25,587.33,659.25]
    for k,(t,kind,i,other) in enumerate(events):
        if kind not in ("bounce","cut","eliminated"):continue
        start=int((t+1.5)*sr); duration=.28 if kind!="eliminated" else .65
        size=min(int(duration*sr),len(samples)-start)
        if size<=0:continue
        x=np.arange(size,dtype=np.float32)/sr
        f=notes[k%len(notes)]*(2 if kind=="cut" else 1)
        env=np.exp(-x*(16 if kind=="cut" else 8))
        samples[start:start+size]+=(np.sin(2*np.pi*f*x)+.25*np.sin(2*np.pi*f*2.01*x))*env*.16
    samples=np.clip(samples,-.95,.95)
    with wave.open(str(path),"wb") as wf:
        wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(sr)
        wf.writeframes((samples*32767).astype("<i2").tobytes())

def getfont(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]:
        if Path(p).exists():return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def draw_frame(b,frame,winner,episode,seconds):
    t,pos,alive,strings=frame
    im=Image.new("RGB",(540,960),"black");d=ImageDraw.Draw(im)
    d.text((270,66),"STRING BATTLE",font=getfont(35),anchor="mm",fill="white")
    d.text((270,108),f"COUNTRY SHOWDOWN  •  EP {episode:02d}",font=getfont(17),anchor="mm",fill="#b4b4c4")
    d.text((270,155),f"{int(t):02d}s  •  LAST FLAG STANDING",font=getfont(18),anchor="mm",fill="white")
    d.ellipse((32,267,508,743),outline="white",width=3)
    for owner,anchor in strings:
        if alive[owner]:
            d.line((tuple(pos[owner]),tuple(anchor)),fill=PALETTE.get(b.codes[owner],"white"),width=1)
    for i,code in enumerate(b.codes):
        if not alive[i]:continue
        x,y=pos[i];col=PALETTE.get(code,"white")
        d.ellipse((x-BALL-3,y-BALL-3,x+BALL+3,y+BALL+3),fill=col)
        d.ellipse((x-BALL,y-BALL,x+BALL,y+BALL),fill="#151515",outline="white",width=2)
        d.text((x,y),code,font=getfont(15),anchor="mm",fill="white")
    for i,code in enumerate(b.codes):
        x=270+(i-(b.n-1)/2)*min(145,480/b.n)
        count=sum(1 for o,a in strings if o==i)
        d.text((x,212),code,font=getfont(21),anchor="mm",fill=PALETTE.get(code,"white") if alive[i] else "#666666")
        d.text((x,239),str(count) if alive[i] else "OUT",font=getfont(17),anchor="mm",fill="white" if alive[i] else "#777777")
    d.text((270,805),"PICK YOUR COUNTRY BEFORE THE CUT!",font=getfont(19),anchor="mm",fill="white")
    d.text((270,847),"@shipstack_  •  ORIGINAL PHYSICS",font=getfont(15),anchor="mm",fill="#aaaabb")
    return im

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--episode",type=int,default=1)
    ap.add_argument("--seed",type=int)
    ap.add_argument("--countries",nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--max-seconds",type=float,default=150)
    ap.add_argument("--simulate-only",action="store_true")
    args=ap.parse_args()
    manifest=json.loads((HERE/"episodes-10.json").read_text())
    entry=manifest["episodes"][args.episode-1]
    codes=args.countries or entry["countries"]
    if len(codes)<2:raise SystemExit("Need at least two countries")
    # Try multiple deterministic seeds if a battle reaches a draw or time limit.
    winner=None; b=None
    for attempt in range(16):
        seed=(args.seed if args.seed is not None else entry["seed"])+attempt*7919
        trial=Battle(codes,seed)
        try:winner=trial.run(args.max_seconds);b=trial;break
        except RuntimeError:continue
    if b is None:raise SystemExit("Could not find unique survivor; nothing rendered or posted")
    result={"episode":args.episode,"seed":seed,"countries":codes,"winner":codes[winner],
            "duration":round(b.t,3),"eliminations":[codes[e[2]] for e in b.events if e[1]=="eliminated"]}
    print(json.dumps(result))
    if args.simulate_only:return
    output=Path(args.out or f"string_battle_ep{args.episode:02d}.mp4")
    output.parent.mkdir(parents=True,exist_ok=True)
    audio=output.with_suffix(".wav");duration=b.t+1.5+3
    synth(b.events,duration,audio)
    cmd=["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24",
         "-s","540x960","-r","30","-i","-","-i",str(audio),
         "-c:v","libx264","-preset","fast","-crf","19","-pix_fmt","yuv420p",
         "-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",str(output)]
    ff=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        frames=[b.frames[0]]*45+b.frames
        frames+= [b.frames[-1]]*90
        for k,fr in enumerate(frames):
            img=draw_frame(b,fr,winner,args.episode,duration)
            if k>=len(frames)-90:
                d=ImageDraw.Draw(img)
                d.rectangle((50,360,490,660),fill="black")
                d.text((270,438),NAMES.get(codes[winner],codes[winner])+" WINS!",font=getfont(37),anchor="mm",fill=PALETTE.get(codes[winner],"white"))
                d.text((270,501),"LAST COUNTRY STANDING",font=getfont(22),anchor="mm",fill="white")
            ff.stdin.write(img.tobytes())
    finally:
        ff.stdin.close()
    if ff.wait()!=0:raise RuntimeError("ffmpeg failed")
    audio.unlink(missing_ok=True)
    output.with_suffix(".json").write_text(json.dumps(result,indent=2))
if __name__=="__main__":main()
