"""Deterministic compositions; time is measured in seconds, never wall-clock time."""
import json
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
TRACKS = {
    "focus": ("1-beat_focus_drive_140bpm.mp3", 140),
    "bounce": ("2-beat_brain_bounce_118bpm.mp3", 118),
    "calm": ("3-beat_calm_glow_72bpm.mp3", 72),
}
FORMATS = {"memory", "odd_one_out", "stroop", "follow_ball", "squares", "will_they_meet", "eye_reset", "breathing"}
COLORS = [(247,65,137), (36,127,248), (255,192,40), (20,199,151), (139,83,244), (255,137,47)]
INK = (26,24,65)


def load(path):
    data = json.loads(Path(path).read_text())
    validate(data)
    return data


def validate(c):
    if c.get("version") != 1:
        raise ValueError("version must be 1")
    if c.get("format") not in FORMATS:
        raise ValueError("unsupported format")
    for key in ("duration", "reveal_at"):
        if type(c.get(key)) not in (int, float) or not math.isfinite(c[key]):
            raise ValueError(f"{key} must be a finite number")
    if not 2 <= c["duration"] <= 90 or not 0 < c["reveal_at"] < c["duration"]:
        raise ValueError("require 2–90 seconds and 0 < reveal_at < duration")
    if c.get("music") not in TRACKS:
        raise ValueError("unknown music track")
    if type(c.get("seed", 1)) is not int:
        raise ValueError("seed must be an integer")
    for key in ("title", "instruction", "cta"):
        if not isinstance(c.get(key), str) or not 1 <= len(c[key]) <= 70:
            raise ValueError(f"{key} requires 1–70 characters")
    if c["format"] == "memory":
        order = c.get("order")
        if not isinstance(order, list) or len(order) != 5 or any(type(x) is not int or not 0 <= x < 6 for x in order):
            raise ValueError("memory order requires five color indices in 0..5")
        if not 0 < c.get("hide_at", 0) < c["reveal_at"]:
            raise ValueError("hide_at must precede reveal_at")
    if c["format"] == "odd_one_out" and (type(c.get("target")) is not int or not 0 <= c["target"] < 36):
        raise ValueError("target must be a cell index in 0..35")
    if c["format"] == "squares" and (type(c.get("grid_size")) is not int or not 2 <= c["grid_size"] <= 6):
        raise ValueError("grid_size must be an integer in 2..6")
    if c["format"] == "follow_ball" and (type(c.get("swaps", 6)) is not int or not 1 <= c.get("swaps", 6) <= 30):
        raise ValueError("swaps must be an integer in 1..30")


def cup_state(c, t):
    """A real permutation keeps the hidden ball under the correct cup."""
    rng = random.Random(c.get("seed", 1))
    swaps = [rng.sample(range(3), 2) for _ in range(c.get("swaps", 6))]
    progress = max(0, min(len(swaps), (t - 2) / max(.1, c["reveal_at"] - 2) * len(swaps)))
    order = [0, 1, 2]
    for a, b in swaps[:int(progress)]:
        order[a], order[b] = order[b], order[a]
    positions = [float(i) for i in range(3)]
    arc = [0., 0., 0.]
    if int(progress) < len(swaps):
        a, b = swaps[int(progress)]
        f = (1 - math.cos(math.pi * (progress % 1))) / 2
        positions[a], positions[b] = a + (b-a)*f, b + (a-b)*f
        arc[a], arc[b] = -45*math.sin(math.pi*f), 45*math.sin(math.pi*f)
    ball_slot = order.index(0)
    return order, positions, arc, ball_slot


class Scene:
    def __init__(self, c):
        validate(c)
        self.c = c
        self.fonts = {}
        self.bg = self.background()

    def font(self, size):
        if size not in self.fonts:
            path = ROOT / "assets/fonts/DejaVuSans-Bold.ttf"
            if not path.exists():
                path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
            self.fonts[size] = ImageFont.truetype(str(path), size)
        return self.fonts[size]

    def text(self, xy, text, size=28, fill=INK, outline=False, max_width=620):
        while size > 12 and self.d.textbbox((0,0), text, font=self.font(size))[2] > max_width:
            size -= 1
        self.d.text(xy, text, font=self.font(size), fill=fill, anchor="mm", stroke_width=2 if outline else 0, stroke_fill="white")

    def background(self):
        palettes = {
            "follow_ball": [(255,184,130),(255,228,165),(244,162,208)],
            "squares": [(119,226,193),(255,224,145),(155,192,251)],
            "odd_one_out": [(126,179,251),(167,228,224),(190,152,250)],
        }
        colors = palettes.get(self.c["format"], [(181,154,251),(249,167,208),(144,205,253)])
        small = Image.new("RGB", (90,160))
        px = small.load()
        for y in range(160):
            for x in range(90):
                w = [math.exp(-((x-a)**2+(y-b)**2)/6500) for a,b in [(0,0),(90,80),(0,160)]]
                px[x,y] = tuple(int(sum(colors[j][k]*w[j] for j in range(3))/sum(w)) for k in range(3))
        im = small.resize((720,1280), Image.Resampling.BICUBIC).convert("RGBA")
        d = ImageDraw.Draw(im)
        rng = random.Random(self.c.get("seed",1))
        for _ in range(45):
            x,y = rng.randrange(720), rng.randrange(1280)
            d.line((x-3,y,x+3,y), fill=(255,255,255,100))
            d.line((x,y-3,x,y+3), fill=(255,255,255,100))
        return im

    def glass(self, box, radius=30):
        layer = Image.new("RGBA", self.im.size)
        d = ImageDraw.Draw(layer)
        x0,y0,x1,y1 = box
        d.rounded_rectangle((x0,y0+10,x1,y1+10), radius, fill=(44,35,94,35))
        d.rounded_rectangle(box, radius, fill=(255,255,255,72), outline=(255,255,255,230), width=2)
        d.line((x0+radius,y0+4,x1-radius,y0+4), fill=(255,255,255,150), width=2)
        self.im = Image.alpha_composite(self.im, layer)
        self.d = ImageDraw.Draw(self.im)

    def marble(self, x,y,r,color,look=1,emotion="happy",blink=False):
        d=self.d
        d.ellipse((x-r,y+r*.7,x+r,y+r*1.12),fill=(91,68,122,65))
        for rr in range(int(r),0,-1):
            light=.65+.35*(1-rr/r)
            rgb=tuple(int(v*light) for v in color)
            d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=rgb)
        d.ellipse((x-r*.65,y-r*.7,x-r*.1,y-r*.33),fill=(255,255,255,245))
        for eye in [-.32,.32]:
            ex=x+eye*r
            if blink:
                d.arc((ex-r*.19,y-r*.04,ex+r*.19,y+r*.14),0,180,fill=INK,width=max(2,int(r*.065)))
                continue
            d.ellipse((ex-r*.16,y-r*.09,ex+r*.16,y+r*.3),fill="white")
            ex+=look*r*.045
            d.ellipse((ex-r*.095,y+r*.02,ex+r*.095,y+r*.22),fill=INK)
            d.ellipse((ex-r*.05,y+r*.035,ex,y+r*.085),fill="white")
            # Raised and asymmetric brows make reactions readable at phone size.
            brow_y=y-r*(.25 if emotion=="surprised" else .17)
            tilt=r*.09 if emotion=="curious" and eye<0 else 0
            d.line((ex-r*.17,brow_y-tilt,ex+r*.17,brow_y+tilt),fill=INK,width=max(2,int(r*.055)))
        if emotion=="surprised":
            d.ellipse((x-r*.12,y+r*.34,x+r*.12,y+r*.61),fill=INK)
        elif emotion=="curious":
            d.arc((x-r*.06,y+r*.28,x+r*.24,y+r*.48),5,140,fill=INK,width=max(2,int(r*.055)))
        else:
            d.ellipse((x-r*.24,y+r*.3,x+r*.24,y+r*.61),fill=INK)
            d.ellipse((x-r*.12,y+r*.47,x+r*.15,y+r*.6),fill=(255,133,169))
        for side in (-1,1):
            cx=x+side*r*.58
            d.ellipse((cx-r*.12,y+r*.27,cx+r*.12,y+r*.37),fill=(255,146,171))

    def frame(self,t):
        c=self.c
        self.im=self.bg.copy()
        self.d=ImageDraw.Draw(self.im)
        self.glass((275,105,445,141),18)
        self.text((360,123),"SHIPSTACK",16)
        self.text((360,204),c["title"].upper(),46,(120,83,213),True)
        self.glass((267,246,453,291),20)
        self.text((360,268),"REVEAL" if t>=c["reveal_at"] else "GUESS FIRST",19)
        self.text((360,335),c["instruction"],27)
        self.glass((35,391,685,826))
        self.puzzle(t)
        remain=max(0, c["reveal_at"]-t)
        self.glass((90,873,630,909),18)
        self.d.rounded_rectangle((96,879,96+max(2,528*remain/c["reveal_at"]),903),12,fill=COLORS[2])
        self.text((360,951),f"{math.ceil(remain)} seconds" if remain else self.answer(),26)
        self.glass((115,1030,680,1110))
        self.text((398,1070),c["cta"],23,max_width=525)
        # The host reacts throughout the puzzle, including while Sunny is hidden.
        revealed=t>=c["reveal_at"]
        host_y=1066-abs(math.sin(t*3.5))*(13 if revealed else 5)
        self.marble(64,host_y,40,COLORS[1],look=math.sin(t*2),emotion="happy" if revealed else "curious",blink=t%3.2<.13)
        return self.im.convert("RGB")

    def answer(self):
        c=self.c
        f=c["format"]
        if f=="squares":
            n=c["grid_size"]
            return f"{sum(k*k for k in range(1,n+1))} squares!"
        if f=="odd_one_out": return f"Row {c['target']//6+1}, column {c['target']%6+1}"
        if f=="follow_ball": return f"Cup {cup_state(c,c['reveal_at'])[3]+1}!"
        if f=="will_they_meet": return "Yes! Blu reaches Coral."
        if f=="stroop": return "BLUE · PINK · GOLD · MINT"
        if f=="memory": return "Did you remember the order?"
        return "Take a gentle breath."

    def puzzle(self,t):
        c=self.c; f=c["format"]; reveal=t>=c["reveal_at"]
        if f=="memory":
            hidden=c["hide_at"]<=t<c["reveal_at"]
            for i,col in enumerate(c["order"]):
                x=100+i*130
                if hidden:
                    self.glass((x-47,515,x+47,617),22); self.text((x,563),"?",44)
                else: self.marble(x,563,46,COLORS[col])
                self.text((x,665),str(i+1),24)
            self.text((360,752),"Remember..." if t<c["hide_at"] else "Which colour was first?",26)
        elif f=="odd_one_out":
            for i in range(36):
                x=115+(i%6)*98; y=447+(i//6)*65
                self.marble(x,y,26,COLORS[1],-1 if i==c["target"] else 1)
                if reveal and i==c["target"]:
                    self.d.ellipse((x-33,y-33,x+33,y+33),outline="white",width=4)
        elif f=="squares":
            n=c["grid_size"]; cell= min(75,340/n); left=360-n*cell/2; top=610-n*cell/2
            for y in range(n):
                for x in range(n):
                    self.d.rectangle((left+x*cell,top+y*cell,left+(x+1)*cell,top+(y+1)*cell),fill=(255,255,255,90),outline=INK,width=3)
        elif f=="stroop":
            for i,(word,col) in enumerate(zip(["RED","GREEN","BLUE","YELLOW"],[1,0,2,3])):
                y=461+i*89
                self.glass((145,y-30,575,y+30),16)
                self.text((360,y),word,35,COLORS[col])
        elif f=="follow_ball":
            order,positions,arcs,slot=cup_state(c,t)
            for i in range(3):
                x=180+positions[i]*180; y=590+arcs[i]
                if t<2 or reveal:
                    if order[i]==0:
                        elapsed=t-c["reveal_at"] if reveal else t
                        bounce=abs(math.sin(elapsed*7))*(27 if reveal else 12)
                        sway=math.sin(elapsed*4)*9
                        reaction="surprised" if reveal and elapsed<.55 else "happy" if reveal else "curious"
                        self.marble(x+sway,699-bounce,35,COLORS[2],look=math.sin(elapsed*3),emotion=reaction,blink=elapsed%2.7>2.55)
                    y-=70
                self.d.polygon([(x-42,y-65),(x+42,y-65),(x+59,y+55),(x-59,y+55)],fill=COLORS[0],outline="white",width=3)
                self.d.line((x-50,y+20,x+50,y+20),fill="white",width=5)
                self.text((180+i*180,779),str(i+1),22)
        elif f=="will_they_meet":
            self.d.line((90,500,410,650),fill=INK,width=8)
            self.d.line((380,760,650,735),fill=INK,width=8)
            p=max(0,min(1,(t-c["reveal_at"])/2))
            if p<.6:
                q=p/.6; x=110+300*q; y=455+150*q
            else:
                q=(p-.6)/.4; x=410+165*q; y=605+90*q*q
            self.marble(x,y,38,COLORS[1],emotion="surprised" if 0<p<1 else "happy" if p==1 else "curious")
            self.marble(620,693-abs(math.sin(t*5))*(8 if p==1 else 0),38,COLORS[0],look=-1,emotion="happy" if p==1 else "curious",blink=t%3<.12)
            if not reveal: self.text((530,570),"?",66,COLORS[2],True)
        elif f=="eye_reset":
            theta=t*math.pi/4
            self.marble(360+230*math.sin(theta),610+100*math.sin(2*theta),40,COLORS[1])
        elif f=="breathing":
            phase=t%10
            r=65+60*(1-math.cos(math.pi*min(phase,10-phase)/5))/2
            self.d.ellipse((360-r-25,610-r-25,360+r+25,610+r+25),outline="white",width=3)
            self.marble(360,610,r,COLORS[3])
            self.text((360,772),"Breathe in" if phase<5 else "Breathe out",28)
