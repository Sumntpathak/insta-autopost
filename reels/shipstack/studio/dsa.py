"""DSA debugger reels: a smooth step-through of real code, from a problem spec only.

    python -m reels.shipstack --format dsa --episode 1 --out reels/out/dsa-0001.mp4
    python -m reels.shipstack.studio.dsa --episode 1 --out reels/out/dsa-0001.mp4 [--still 200]

Nothing is designed per episode: the code is taken from the solution function, the trace comes
from running it under sys.settrace, and the same template draws code, pointers, watch panel and
narration. Output: 1080x1920, 30 fps, exactly 15 s, H.264 + AAC (passes reels/verify.py).
"""
import argparse
import copy
import inspect
import keyword
import math
import re
import subprocess
import sys
import tempfile
import textwrap
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from . import theme as T
from .problems import PROBLEMS

W, H, FPS, SECONDS = 1080, 1920, 30, 15
FRAMES = FPS * SECONDS
INTRO, OUTRO = 45, 75                     # frames
X0, X1 = 64, W - 64
BUILTINS = {'len', 'range', 'enumerate', 'min', 'max', 'print', 'sorted', 'sum', 'abs'}


# ---------------------------------------------------------------- trace
def trace(spec):
    fn = spec['fn']
    src, start = inspect.getsourcelines(fn)
    code = textwrap.dedent(''.join(src)).rstrip('\n').split('\n')
    events = []

    def snap(frame):
        return {k: copy.deepcopy(v) for k, v in frame.f_locals.items()}

    def local(frame, event, arg):
        if event == 'line':
            events.append({'line': frame.f_lineno - start, 'vars': snap(frame)})
        elif event == 'return':
            events.append({'line': events[-1]['line'] if events else 0, 'vars': snap(frame), 'result': arg})
        return local

    def glob(frame, event, arg):
        return local if frame.f_code is fn.__code__ else None

    sys.settrace(glob)
    try:
        result = fn(**copy.deepcopy(spec['args']))
    finally:
        sys.settrace(None)
    return code, events, result


# ---------------------------------------------------------------- drawing helpers
TOKEN = re.compile(r'(#.*$)|("[^"]*"|\'[^\']*\')|(\b\d+\b)|([A-Za-z_]\w*)|(\s+)|(.)')


def tokens(line):
    out, prev = [], ''
    for m in TOKEN.finditer(line):
        com, s, num, name, space, op = m.groups()
        text = m.group(0)
        if com:
            kind = 'com'
        elif s:
            kind = 'str'
        elif num:
            kind = 'num'
        elif name:
            kind = 'kw' if keyword.iskeyword(name) else 'fn' if prev == 'def' else 'builtin' if name in BUILTINS else 'name'
            prev = name
        else:
            kind = 'op'
        out.append((text, kind))
    return out


def fmt(value, limit=30):
    if isinstance(value, dict):
        s = '{' + ', '.join(f'{k}: {v}' for k, v in value.items()) + '}'
    else:
        s = repr(value)
    return s if len(s) <= limit else s[:limit - 1] + '…'


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- template
class Reel:
    def __init__(self, episode):
        self.ep = episode
        self.spec = PROBLEMS[episode]
        self.code, self.events, self.result = trace(self.spec)
        self.arr = self.spec['args'][self.spec['array']]
        self.layout()
        self.static()

    def layout(self):
        n = len(self.code)
        self.lh = 52 if n <= 9 else 44
        self.code_font = T.mono(32 if n <= 9 else 29, 500)
        self.code_top = 480
        self.code_y0 = self.code_top + 72
        self.code_bottom = self.code_y0 + n * self.lh + 24
        self.state_top = self.code_bottom + 36
        k = len(self.arr)
        self.cell = min(124, (X1 - X0 - 48 - 14 * (k - 1)) // k)
        self.arr_x0 = X0 + 24 + ((X1 - X0 - 48) - (k * self.cell + 14 * (k - 1))) // 2
        self.arr_y = self.state_top + 60
        self.ptr_y = self.arr_y + self.cell + 40
        self.watch_y = self.ptr_y + 30 * len(self.spec['pointers']) + 50
        rows = math.ceil(len(self.spec['show']) / 2)
        self.state_bottom = self.watch_y + rows * 50 + 14
        self.note_y = self.state_bottom + 30

    def static(self):
        im = Image.new('RGBA', (W, H), T.BG + (255,))
        T.header(im, 'dsa', f'#{self.ep:04d}', top=100)
        d = ImageDraw.Draw(im)
        s = self.spec
        d.text((X0, 238), s['title'], font=T.sans(68 if len(s['title']) < 22 else 54, 800), fill=T.TEXT)
        d.text((X0, 326), s['pattern'].upper(), font=T.mono(26, 700), fill=T.ACCENT)
        y = 370
        for line in T.wrap(d, s['prompt'], T.sans(34, 500), X1 - X0)[:1]:
            d.text((X0, y), line, font=T.sans(34, 500), fill=T.MUTED)
            y += 46
        # code panel
        d.rounded_rectangle((X0, self.code_top, X1, self.code_bottom), 22, fill=T.PANEL, outline=T.BORDER, width=2)
        d.line((X0, self.code_top + 56, X1, self.code_top + 56), fill=T.BORDER, width=2)
        d.text((X0 + 28, self.code_top + 14), f"{s['fn'].__name__}.py", font=T.mono(24, 600), fill=T.MUTED)
        d.text((X1 - 28 - d.textlength('debug ▶', font=T.mono(24, 600)), self.code_top + 14), 'debug ▶',
               font=T.mono(24, 600), fill=T.SERIES['dsa'][1])
        # state panel
        d.rounded_rectangle((X0, self.state_top, X1, self.state_bottom), 22, fill=T.PANEL, outline=T.BORDER, width=2)
        d.text((X0 + 28, self.state_top + 18), s['array'], font=T.mono(24, 600), fill=T.MUTED)
        d.text((X0 + 28, self.watch_y - 40), 'watch', font=T.mono(24, 600), fill=T.MUTED)
        self.base = im.convert('RGB')
        # code text layer (drawn over the moving highlight)
        txt = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        td = ImageDraw.Draw(txt)
        nf = T.mono(26, 500)
        for i, line in enumerate(self.code):
            y = self.code_y0 + i * self.lh
            td.text((X0 + 22, y + 8), f'{i + 1:>2}', font=nf, fill=T.BORDER)
            x = X0 + 76
            for text, kind in tokens(line):
                td.text((x, y + 4), text, font=self.code_font, fill=T.SYNTAX[kind])
                x += td.textlength(text, font=self.code_font)
        self.code_layer = txt

    # -------------------------------------------------------------- per frame
    def schedule(self):
        steps = self.events
        span = FRAMES - INTRO - OUTRO
        per = span / len(steps)
        return [(INTRO + round(i * per), e) for i, e in enumerate(steps)], per

    def frame(self, f, sched, per):
        im = self.base.copy()
        d = ImageDraw.Draw(im, 'RGBA')
        # which step
        k = 0
        for i, (start, _) in enumerate(sched):
            if f >= start:
                k = i
        start, ev = sched[k]
        prev = sched[k - 1][1] if k else ev
        t = ease((f - start) / max(1, min(8, per * 0.5))) if f >= INTRO else 0
        # code reveal during intro
        reveal = len(self.code) if f >= INTRO else int(len(self.code) * min(1, f / (INTRO * 0.8))) + 1
        if f >= INTRO:
            y = lerp(self.code_y0 + prev['line'] * self.lh, self.code_y0 + ev['line'] * self.lh, t)
            d.rounded_rectangle((X0 + 10, y, X1 - 10, y + self.lh), 10, fill=T.ACCENT + (38,))
            d.rectangle((X0 + 10, y, X0 + 16, y + self.lh), fill=T.ACCENT)
        clip = self.code_layer.crop((0, 0, W, self.code_y0 + reveal * self.lh))
        im.paste(clip, (0, 0), clip)
        vars_now = ev['vars'] if f >= INTRO else {}
        vars_prev = prev['vars'] if f >= INTRO else {}
        self.draw_array(d, vars_now, vars_prev, t)
        self.draw_watch(d, vars_now, vars_prev, (f - start) / max(1, per))
        self.draw_note(d, ev, f)
        if f >= FRAMES - OUTRO:
            self.draw_result(im, (f - (FRAMES - OUTRO)) / 12)
        return im

    def draw_array(self, d, now, prev, t):
        ptrs = self.spec['pointers']
        active = {now[v] for v in ptrs if isinstance(now.get(v), int) and 0 <= now[v] < len(self.arr)}
        vf, idf = T.mono(40 if self.cell > 100 else 34, 700), T.mono(22, 500)
        for i, val in enumerate(self.arr):
            x = self.arr_x0 + i * (self.cell + 14)
            on = i in active
            d.rounded_rectangle((x, self.arr_y, x + self.cell, self.arr_y + self.cell), 16,
                                fill=T.PANEL_2 if not on else T.ACCENT + (60,), outline=T.ACCENT if on else T.BORDER, width=3)
            s = str(val)
            d.text((x + (self.cell - d.textlength(s, font=vf)) / 2, self.arr_y + self.cell / 2 - 24), s, font=vf,
                   fill=T.TEXT)
            d.text((x + (self.cell - d.textlength(str(i), font=idf)) / 2, self.arr_y + self.cell + 8), str(i),
                   font=idf, fill=T.MUTED)
        # pointers: arrows that glide between indices
        row = {}
        for j, (var, label) in enumerate(ptrs.items()):
            if not isinstance(now.get(var), int):
                continue
            a = prev.get(var, now[var]) if isinstance(prev.get(var), int) else now[var]
            pos = lerp(a, now[var], t)
            if not -0.5 <= pos <= len(self.arr) - 0.5:
                continue
            cx = self.arr_x0 + pos * (self.cell + 14) + self.cell / 2
            slot = row.setdefault(round(now[var]), 0)
            row[round(now[var])] += 1
            y = self.ptr_y + slot * 34
            color = [T.ACCENT, T.SERIES['dsa'][1], T.SERIES['news'][1]][j % 3]
            d.polygon([(cx, y), (cx - 11, y + 16), (cx + 11, y + 16)], fill=color)
            lf = T.mono(24, 700)
            d.text((cx + 16, y - 4), label, font=lf, fill=color)

    def draw_watch(self, d, now, prev, since):
        names = self.spec['show']
        colw = (X1 - X0 - 56) // 2
        for i, name in enumerate(names):
            x = X0 + 28 + (i % 2) * colw
            y = self.watch_y + (i // 2) * 50
            changed = name in now and (name not in prev or prev.get(name) != now.get(name))
            if changed and since < 1:
                d.rounded_rectangle((x - 10, y - 6, x + colw - 16, y + 46), 10,
                                    fill=T.ACCENT + (round(70 * (1 - since)),))
            d.text((x, y), name, font=T.mono(28, 600), fill=T.MUTED)
            val = fmt(now[name], 15) if name in now else '—'
            d.text((x + 150, y), val, font=T.mono(30, 700), fill=T.TEXT if name in now else T.BORDER)

    def draw_note(self, d, ev, f):
        if f < INTRO:
            text = 'Watch the code run, line by line.'
        elif 'result' in ev:
            text = 'Done.'
        else:
            line = self.code[ev['line']].strip()
            text = self.spec['notes'].get(line, '')
        if not text:
            return
        d.rectangle((X0, self.note_y, X0 + 8, self.note_y + 64), fill=T.ACCENT)
        d.text((X0 + 32, self.note_y + 10), text, font=T.sans(38, 650), fill=T.TEXT)

    def draw_result(self, im, t):
        a = ease(t)
        d = ImageDraw.Draw(im, 'RGBA')
        top = self.note_y - 10
        d.rounded_rectangle((X0, top, X1, top + 196), 22, fill=T.PANEL_2 + (round(255 * a),),
                            outline=T.ACCENT + (round(255 * a),), width=3)
        if a > 0.3:
            d.text((X0 + 32, top + 20), f'return {fmt(self.result, 24)}', font=T.mono(44, 800), fill=T.ACCENT)
            d.text((X0 + 32, top + 86), self.spec['complexity'], font=T.mono(28, 600), fill=T.MUTED)
            nxt = PROBLEMS.get(self.ep + 1)
            d.text((X0 + 32, top + 136), f"Next: #{self.ep + 1:04d} {nxt['title']}" if nxt else 'Follow for the next one',
                   font=T.sans(30, 700), fill=T.TEXT)


# ---------------------------------------------------------------- audio
def soundtrack(path, ticks):
    sr = 44100
    t = np.arange(SECONDS * sr) / sr
    chords = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (130.81, 196.0, 261.63), (196.0, 246.94, 293.66)]
    pad = np.zeros_like(t)
    seg = len(t) // len(chords)
    for i, ch in enumerate(chords):
        s = slice(i * seg, (i + 1) * seg if i < len(chords) - 1 else len(t))
        tt = t[s]
        env = np.minimum(1, np.minimum((tt - tt[0]) / 0.4, (tt[-1] - tt + 1e-9) / 0.4))
        pad[s] = env * sum(np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt) for f in ch) / len(ch)
    out = 0.22 * pad
    for frame in ticks:
        i0 = int(frame / FPS * sr)
        n = int(0.06 * sr)
        if i0 + n < len(out):
            tt = np.arange(n) / sr
            out[i0:i0 + n] += 0.25 * np.sin(2 * np.pi * 1320 * tt) * np.exp(-tt * 70)
    out = np.clip(out, -1, 1)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((out * 32767).astype('<i2').tobytes())


# ---------------------------------------------------------------- render
def render(out, episode=1):
    reel = Reel(episode)
    sched, per = reel.schedule()
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / 'a.wav'
        soundtrack(wav, [s for s, _ in sched])
        cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
               '-i', '-', '-i', str(wav), '-frames:v', str(FRAMES), '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
               '-preset', 'medium', '-crf', '18', '-c:a', 'aac', '-b:a', '160k', '-t', str(SECONDS),
               '-movflags', '+faststart', str(out)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for f in range(FRAMES):
            proc.stdin.write(reel.frame(f, sched, per).tobytes())
        proc.stdin.close()
        if proc.wait():
            raise RuntimeError('ffmpeg failed')
    print(f'Wrote {out} (DSA #{episode:04d} {reel.spec["title"]}, {len(reel.events)} traced steps)')
    return out


def still(path, episode, f):
    reel = Reel(episode)
    sched, per = reel.schedule()
    reel.frame(f, sched, per).save(path)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--episode', type=int, default=1)
    ap.add_argument('--out', default='reels/out/dsa.mp4')
    ap.add_argument('--still', type=int, help='save this frame as PNG instead of rendering the video')
    a = ap.parse_args()
    if a.still is not None:
        print(still(a.out, a.episode, a.still))
    else:
        render(a.out, a.episode)


if __name__ == '__main__':
    main()
