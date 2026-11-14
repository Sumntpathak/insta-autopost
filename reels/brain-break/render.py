"""Render the nine ShipStack Brain Break visual puzzles."""
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, DUR = 540, 960, 30, 15
HERE = Path(__file__).resolve().parent
FONT = Path("/usr/share/fonts/truetype/dejavu")
WHITE = "#f0f1f5"
MUTED = "#b6bccd"
INK = "#10131e"

PUZZLES = [
    ("ink-switch", "INK SWITCH", "Name the ink color", "Ignore the word itself.", "#f4ba85",
     "GREEN", "The letters spell BLUE."),
    ("odd-symbol", "ODD SYMBOL", "Find the odd arrow", "Watch for a different direction.", "#94e3ce",
     "ROW 3 · COL 4", "Its arrow points up-left."),
    ("digit-recall", "DIGIT RECALL", "Memorize six digits", "Repeat them before the reveal.", "#b9c8ff",
     "7  1  9  4  6  2", "How many did you get in order?"),
    ("location-memory", "LOCATION MEMORY", "Remember the tile positions", "Four tiles will light up.", "#e8acf1",
     "FOUR TILES", "Check the positions you remembered."),
    ("pulse-count", "PULSE COUNT", "Count the gold flashes", "Ignore the pale blue ones.", "#f5cf7c",
     "7 FLASHES", "Count only the gold circle."),
    ("rule-switch", "RULE SWITCH", "Find where the arrow ends", "Turn as each card tells you.", "#a2dffa",
     "POINTING LEFT", "Up → Right → Up → Right → Left"),
    ("next-number", "NEXT NUMBER", "Find the missing number", "What changes at each step?", "#f5aab8",
     "36", "The gaps are +5, +7, +9, +11."),
    ("spot-the-change", "SPOT THE CHANGE", "What changed in the grid?", "Remember the first arrangement.", "#b4e7a3",
     "ROW 2 · COL 3", "The triangle became a diamond."),
    ("order-recall", "ORDER RECALL", "Remember the shape order", "Name them in the same order.", "#ffc9aa",
     "CIRCLE · STAR", "Then square, then diamond."),
]

def font(size, face="bold"):
    filename = {"bold": "DejaVuSans-Bold.ttf", "regular": "DejaVuSans.ttf",
                "mono": "DejaVuSansMono.ttf"}[face]
    return ImageFont.truetype(str(FONT / filename), size)

F = {(size, face): font(size, face) for size, face in
     [(12,"mono"),(14,"mono"),(17,"regular"),(21,"regular"),(29,"bold"),
      (34,"bold"),(42,"bold"),(54,"bold"),(72,"bold"),(24,"bold")]}

def label(draw, txt, y, size, color=WHITE, face="bold", x=270):
    style = F[size, face]
    while draw.textlength(txt, font=style) > 440:
        size -= 1
        style = font(size, face)
    draw.text((x, y), txt, font=style, fill=color, anchor="mm")

def shape(draw, kind, x, y, size, color, width=3):
    n = size / 2
    box = (x-n, y-n, x+n, y+n)
    if kind == "circle":
        draw.ellipse(box, outline=color, width=width)
        return
    if kind == "square":
        draw.rounded_rectangle(box, radius=3, outline=color, width=width)
        return
    count = {"triangle":3,"diamond":4,"star":10}[kind]
    points = [
        (x + (n if kind != "star" or i % 2 == 0 else n*.45)*math.sin(i*math.tau/count),
         y - (n if kind != "star" or i % 2 == 0 else n*.45)*math.cos(i*math.tau/count))
        for i in range(count)
    ]
    draw.line(points+[points[0]], fill=color, width=width, joint="curve")

def arrow(draw, x, y, degrees, size, color):
    angle = math.radians(degrees)
    points = [(0,size*.5),(0,-size*.5),(-size*.24,-size*.23),(0,-size*.5),(size*.24,-size*.23)]
    points = [(x+a*math.cos(angle)-b*math.sin(angle),y+a*math.sin(angle)+b*math.cos(angle))
              for a,b in points]
    draw.line(points, fill=color, width=4, joint="curve")

def board(draw, accent):
    draw.rounded_rectangle((42,290,498,663), radius=30, fill="#141a28", outline="#313b50", width=1)
    draw.line((70,624,470,624), fill="#30384a")
    draw.ellipse((69,317,77,325),fill=accent)

def cells(draw, rows, cols, accent, marked=None):
    size = min(63, 360 // cols)
    for r in range(rows):
        for c in range(cols):
            x = 270 + (c-(cols-1)/2)*size
            y = 468 + (r-(rows-1)/2)*size
            color = accent if marked is not None and (r,c) in marked else "#283347"
            draw.rounded_rectangle((x-size/2+4,y-size/2+4,x+size/2-4,y+size/2-4),
                                   radius=9,fill="#1c2537",outline=color,width=2)
            yield r,c,x,y

SHAPES = ("circle","triangle","square","diamond","star","triangle","diamond","circle","star")
TILES = {(0,1),(1,3),(2,0),(3,2)}
PULSES = (2.1,2.63,3.20,3.58,4.17,4.60,5.09,5.78,6.22,6.74,7.27,7.82)
GOLD = {0,2,3,5,7,8,11}

def board_content(draw, index, t, accent):
    reveal = t >= 10.5
    footer = "ANSWER" if reveal else "WATCH" if t < 8.5 else "LOCK IN YOUR ANSWER"
    if index == 0:
        label(draw, "BLUE", 465, 72, "#88dba4")
        if reveal:
            shape(draw,"circle",270,550,26,"#88dba4")
    elif index == 1:
        hit = (2,3)
        for r,c,x,y in cells(draw,4,5,accent,{hit} if reveal else None):
            arrow(draw,x,y,315 if (r,c)==hit else 45,25,accent if reveal and (r,c)==hit else WHITE)
    elif index == 2:
        label(draw, "7 1 9 4 6 2" if 2 <= t < 5.4 or reveal else "• • • • • •", 465, 54,
              accent if reveal else WHITE)
        if 5.4 <= t < 8.5:
            footer = "REPEAT THE DIGITS"
    elif index == 3:
        active = TILES if 2 <= t < 5.6 or reveal else set()
        for r,c,x,y in cells(draw,4,4,accent,active):
            if (r,c) in active:
                draw.rounded_rectangle((x-16,y-16,x+16,y+16),radius=7,fill=accent)
        if 5.6 <= t < 8.5:
            footer = "PICTURE THE FOUR TILES"
    elif index == 4:
        flash = next((i for i, start in enumerate(PULSES) if start <= t < start+.26), None)
        color = "#ffd27c" if reveal or flash in GOLD else "#9db9e5"
        draw.ellipse((202,400,338,536),outline="#43526c",width=2)
        draw.ellipse((223,421,317,515),fill=color if flash is not None or reveal else "#253149")
    elif index == 5:
        if reveal:
            arrow(draw,270,462,270,112,accent)
        elif t < 3.0:
            arrow(draw,270,465,0,108,WHITE)
            footer = "START FACING UP"
        elif t < 8.5:
            cards = ("RIGHT 90°", "LEFT 90°", "RIGHT 90°", "LEFT 180°")
            i = min(3, int((t-3)/1.375))
            label(draw,cards[i],465,42,accent)
            footer = f"TURN {i+1} OF 4"
        else:
            label(draw,"WHICH WAY?",465,34)
    elif index == 6:
        label(draw,"4    9    16    25",430,42)
        label(draw,"36" if reveal else "?",525,72,accent)
    elif index == 7:
        changed = t >= 6.1
        hit = (1,2)
        for r,c,x,y in cells(draw,3,3,accent,{hit} if reveal else None):
            kind = "diamond" if changed and (r,c)==hit else SHAPES[r*3+c]
            if not 5.3 <= t < 6.1:
                shape(draw,kind,x,y,31,accent if reveal and (r,c)==hit else WHITE)
        if not reveal and t < 8.5:
            footer = "GRID B" if changed else "SWITCHING" if t >= 5.3 else "GRID A"
    else:
        kinds = ("circle","star","square","diamond")
        if reveal:
            for i,kind in enumerate(kinds):
                shape(draw,kind,120+100*i,465,44,accent)
        elif 2 <= t < 7.2:
            i = int((t-2)/1.3)
            shape(draw,kinds[i],270,465,106,accent,5)
            footer = f"SHAPE {i+1} OF 4"
        else:
            for i in range(4):
                label(draw,"?",465,34,MUTED,x=120+100*i)
    label(draw,footer,607,12,MUTED,"mono")

def scene_base(accent):
    yy, xx = np.mgrid[0:H,0:W]
    glow = np.exp(-(((xx-270)/350)**2+((yy-455)/480)**2)*2)
    rgb = np.asarray([int(accent[i:i+2],16) for i in (1,3,5)])
    col = np.array([10,13,23])[None,None,:] + glow[:,:,None]*rgb[None,None,:]*.075
    image = Image.fromarray(col.astype(np.uint8))
    d = ImageDraw.Draw(image)
    for y in range(305,681,20):
        for x in range(25,520,20):
            d.point((x,y), fill="#333849")
    return image

def frame(base, index, t):
    _, name, hook, note, accent, answer, why = PUZZLES[index]
    image = base.copy()
    d = ImageDraw.Draw(image)
    d.line((45,146,495,146),fill="#41475a")
    label(d,"S H I P S T A C K",121,14,accent,"mono",x=121)
    label(d,f"BRAIN BREAK  {index+1:02d}/09",121,12,MUTED,"mono",x=401)
    label(d,name,194,42)
    label(d,hook,243,21,accent,"regular")
    board(d,accent)
    if t < 2:
        label(d,"READY?",447,54)
        label(d,note,519,21,MUTED,"regular")
        k=int((2-t)*3)+1
        for i in range(6):
            d.ellipse((229+i*16,565,237+i*16,573),fill=accent if i<k else "#384056")
        label(d,"THE CHALLENGE STARTS IN A MOMENT",607,12,MUTED,"mono")
    else:
        board_content(d,index,t,accent)
    if 8.5 <= t < 10.5:
        label(d,"MAKE YOUR PICK",708,29)
    elif t >= 10.5:
        label(d,answer,710,34,accent)
        label(d,why,749,17,WHITE,"regular")
    else:
        label(d,note,711,17,MUTED,"regular")
    d.rounded_rectangle((53,791,487,795),radius=2,fill="#333b50")
    d.rounded_rectangle((53,791, max(57,53+434*t/DUR),795),radius=2,fill=accent)
    label(d,"SAVE TO TRY AGAIN   /   SHARE TO CHALLENGE A FRIEND" if t >= 12 else
          "@shipstack_",821,12,accent,"mono")
    return image

def soundtrack(path,index):
    rate=48000
    t = np.arange(DUR*rate)/rate
    f0 = 98 * 2**((index % 5)/12)
    bed = sum(np.sin(2*np.pi*f0*m*t+.12*np.sin(t)) for m in (1,1.5,2,2.52))*.024
    bed *= np.minimum(1,t/.85)*np.minimum(1,(DUR-t)/1.3)
    for start,m in ((.2,4),(2,5),(8.5,4),(10.5,6),(10.68,7.5),(10.86,9)):
        tau=t-start
        active=tau>=0
        part=tau[active]
        bed[active] += .12*np.sin(2*np.pi*f0*m*part)*np.minimum(1,part/.028)*np.exp(-part*4)
    stereo = np.column_stack((bed,bed*.94))
    with wave.open(str(path),"wb") as f:
        f.setparams((2,2,rate,0,"NONE","not compressed"))
        f.writeframes((stereo*32767).astype("<i2").tobytes())

def item(index):
    slug,name,hook,note,*_ = PUZZLES[index]
    return dict(id=f"BRAIN-20261114-{index+1:02}",scene=slug,variant=index,seconds=DUR,
                caption=f"{name.title()} · {hook}. {note}\n\n"
                        "How did you do? Save it for another round or send it to a friend.\n\n"
                        "#ShipStack #BrainBreak #BrainTeaser")

def render(index, out):
    out.mkdir(parents=True,exist_ok=True)
    entry=item(index)
    path=out/f"{entry['id']}.mp4"
    base=scene_base(PUZZLES[index][4])
    with tempfile.TemporaryDirectory() as temp:
        audio=Path(temp)/"score.wav"
        soundtrack(audio,index)
        with subprocess.Popen([
            "ffmpeg","-hide_banner","-loglevel","error","-y","-filter_threads","1",
            "-f","rawvideo","-pixel_format","rgb24","-video_size",f"{W}x{H}",
            "-framerate",str(FPS),"-i","-","-i",str(audio),
            "-vf","scale=1080:1920:flags=lanczos,setsar=1",
            "-c:v","libx264","-threads","2","-preset","veryfast","-crf","18",
            "-pix_fmt","yuv420p","-c:a","aac","-b:a","160k",
            "-movflags","+faststart","-t",str(DUR),str(path)
        ],stdin=subprocess.PIPE) as ff:
            for n in range(FPS*DUR):
                ff.stdin.write(frame(base,index,n/FPS).tobytes())
            ff.stdin.close()
            if ff.wait():
                raise RuntimeError("FFmpeg failed")
    subprocess.run([sys.executable,str(HERE.parent/"verify.py"),str(path)],check=True)
    path.with_suffix(".mp4.json").write_text(json.dumps({k:entry[k] for k in ("scene","variant","seconds")}))
    if index==0:
        (out/"manifest.json").write_text(json.dumps(dict(batch_id="shipstack-brain-break-2026-11-14",
            enabled=True,count=len(PUZZLES),items=[item(i) for i in range(len(PUZZLES))]),indent=2))

if __name__=="__main__":
    render(int(sys.argv[1]),Path(sys.argv[2]))
