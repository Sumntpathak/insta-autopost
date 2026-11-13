"""Render Galperin's frictionless, perfectly elastic two-block experiment."""
import bisect
import math
from pathlib import Path
import subprocess
import wave

from PIL import Image, ImageDraw, ImageFont
import numpy as np

W, H, FPS = 1080, 1920, 30
WALL, FLOOR, SMALL = 116, 1070, 120
ROUNDS = [(1, 120, 0, 3.55), (100, 155, 3.55, 6.65),
          (10_000, 192, 6.65, 9.75), (1_000_000, 237, 9.75, 13.4)]
FONT_ROOT = Path('/usr/share/fonts/truetype/dejavu')
COLORS = {'ink': '#152949', 'soft': '#4c6381', 'blue': '#0077a8', 'orange': '#9e4a12'}

def simulate(mass):
    x, y, u, v = 112.0, 535.0, 0.0, -1.0
    events = [(x, y, u, v, None)]
    while True:
        wall = -x / u if u < 0 else math.inf
        blocks = (y - x - SMALL) / (u - v) if u > v else math.inf
        step = min(wall, blocks)
        if not math.isfinite(step):
            return events
        x += u * step
        y += v * step
        if wall <= blocks:
            x = 0.0
            u = -u
            edge = 'wall'
        else:
            y = x + SMALL
            u, v = ((1-mass)*u + 2*mass*v)/(1+mass), (2*u + (mass-1)*v)/(1+mass)
            edge = 'blocks'
        events.append((x, y, u, v, edge))

SIMS = [simulate(r[0]) for r in ROUNDS]
assert [len(e)-1 for e in SIMS] == [3, 31, 314, 3141]

def retime(count, span):
    if count == 3:
        return [.36, 1.27, 1.89, 2.55]
    if count == 31:
        return [0, .57, .79, .99] + [1.12+1.09*(i-4)/(count-4) for i in range(4,count+1)]
    if count == 314:
        return [0, .45, .68, .90] + [1.02+1.29*(i-4)/(count-4) for i in range(4,count+1)]
    return [0, .44, .69, .94] + [1.12+1.42*(i-4)/(count-4) for i in range(4,count+1)]

TIMES = [retime(len(e)-1, end-start) for e, (_,_,start,end) in zip(SIMS, ROUNDS)]
def font(size, bold=True):
    name = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    return ImageFont.truetype(str(FONT_ROOT / name), size)
FONTS = {s: font(s) for s in (23,25,27,28,32,36,39,42,48,50,52,62,73,104,118,160)}
def label(draw, xy, text, size, color=COLORS['ink'], anchor='mm'):
    draw.text(xy, text, font=FONTS[size], fill=color, anchor=anchor)

def make_background():
    im = Image.new('RGB',(W,H),'#eff3f7')
    d = ImageDraw.Draw(im)
    d.rectangle((0,0,W,21),fill='#123153')
    d.rounded_rectangle((65,550,1015,1160),radius=29,fill='#fffdf7',outline='#b6c3d2',width=3)
    for x in range(113,990,24):
        for y in range(603,1100,24):
            d.point((x,y),fill='#b8c5d0')
    d.line((WALL, FLOOR, 978, FLOOR),fill='#324d6b',width=4)
    d.line((WALL,670,WALL,FLOOR),fill='#324d6b',width=5)
    for y in range(689,FLOOR,22):
        d.line((WALL-18,y+10,WALL-4,y),fill='#849bb2',width=2)
    d.line((90,1510,990,1510),fill='#cad4e0',width=2)
    label(d,(540,1560),'@shipstack_',28,COLORS['soft'])
    return im
BACKGROUND = make_background()

def block(draw, x, size, fill, edge, name):
    x = round(WALL+x)
    top = FLOOR-size
    draw.rectangle((x,top,x+size,FLOOR-2),fill=fill,outline=edge,width=3)
    draw.line((x+4,top+4,x+size-4,top+4),fill='#ffffff',width=2)
    label(draw,(x+size//2,top+size//2),name,25,edge)

def frame(t):
    i = bisect.bisect_right([3.55,6.65,9.75], t)
    mass, width, start, end = ROUNDS[i]
    local = t-start
    events, times = SIMS[i], TIMES[i]
    count = max(0,bisect.bisect_right(times,local)-1)
    x,y,u,v,edge = events[count]
    if count < len(events)-1:
        amount = max(0,(local-times[count])/(times[count+1]-times[count]))
        x += (events[count+1][0]-x)*amount
        y += (events[count+1][1]-y)*amount
    else:
        progress = min(1,(local-times[-1])/.55)
        # Let the blocks separate naturally after the last impact.
        x += max(0,u)*progress*92
        y += max(0,v)*progress*92
    done = count == len(events)-1
    im = BACKGROUND.copy()
    d = ImageDraw.Draw(im)
    label(d,(540,198),'THE COLLISION COUNTER',32,COLORS['blue'])
    label(d,(540,320),'Two blocks',104)
    label(d,(540,429),'can calculate π',104)
    stage = 'SAME MASS' if i == 0 else f'{mass:,}× HEAVIER'
    label(d,(92,603),stage,32,COLORS['soft'],'lm')
    if i == 3 and .41 < local < 1.12:
        label(d,(980,603),'SLOW MOTION',23,COLORS['blue'],'rm')
    block(d,x,SMALL,'#9fe1f2',COLORS['blue'],'1 kg')
    block(d,y,width,'#ffd7a8',COLORS['orange'],f'{mass:,} kg')
    if count and local-times[count] < .074 and (i == 0 or count <= 3 or done):
        at = WALL if edge == 'wall' else WALL + round(y)
        d.line((at,FLOOR-100,at,FLOOR-14),fill='#ffffff',width=5)
    label(d,(540,1218),'COLLISIONS',28,COLORS['soft'])
    label(d,(540,1330),f'{count:,}',160)
    digits = ['3', '3.1', '3.14', '3.141']
    shown = digits[i] if done else (digits[i-1] if i else '…')
    label(d,(540,1455),f'π ≈ {shown}' if shown != '…' else 'BLOCK + WALL HITS',50,COLORS['blue'])
    if t >= 13.4:
        label(d,(540,645),'Each 100× mass ratio adds one digit',27,COLORS['soft'])
    return im

def render_audio(path):
    rate = 48000
    samples = np.zeros(rate*15)
    def tone(at, frequency, gain, seconds=.12):
        x = np.arange(round(seconds*rate))/rate
        data = gain*np.sin(2*np.pi*frequency*x)*np.exp(-x/(seconds/5))*np.minimum(x*390,1)
        idx = round(at*rate)
        samples[idx:idx+len(data)] += data
    for i, (_,_,start,end) in enumerate(ROUNDS):
        times = TIMES[i]
        step = max(1,(len(times)-4)//18)
        for index in sorted(set(range(1,4)) | set(range(4,len(times)-1,step)) | {len(times)-1}):
            if index < len(times):
                tone(start+times[index], 440 if index%2 else 680, .27 if index<4 else .14)
    for i,freq in enumerate([392,494,587,784]):
        tone(13.52+i*.14,freq,.24,.55)
    with wave.open(str(path),'wb') as output:
        output.setparams((1,2,rate,0,'NONE','not compressed'))
        output.writeframes((np.clip(samples,-.9,.9)*32767).astype('<i2').tobytes())

def render(path):
    audio = path.with_suffix('.wav')
    render_audio(audio)
    command = ['ffmpeg','-y','-v','error','-f','rawvideo','-pixel_format','rgb24',
               '-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-','-i',str(audio),
               '-c:v','libx264','-threads','4','-preset','fast','-crf','18','-pix_fmt','yuv420p',
               '-c:a','aac','-b:a','128k','-movflags','+faststart',str(path)]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
        for n in range(15*FPS):
            encoder.stdin.write(frame(n/FPS).tobytes())
        encoder.stdin.close()
        if encoder.wait():
            raise RuntimeError('FFmpeg encoding failed')

if __name__ == '__main__':
    import sys
    render(Path(sys.argv[1]))
