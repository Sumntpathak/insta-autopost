"""Original soundtrack for the ShipStack story film (no licensing needed).

    python3 film/music.py            -> film/public/bgm.wav

120 BPM, A minor, 15 s. Cue points match the screenplay in docs/story-film.md.
"""
import wave
from pathlib import Path

import numpy as np

SR, BPM, SECONDS = 44100, 120, 15
BEAT = 60 / BPM
t = np.arange(SR * SECONDS) / SR
out = np.zeros_like(t)


def note(freq, start, dur, amp, shape='sine', attack=0.01, release=0.12):
    global out
    i0, n = int(start * SR), int(dur * SR)
    if i0 >= len(out):
        return
    n = min(n, len(out) - i0)
    tt = np.arange(n) / SR
    if shape == 'saw':
        wave_ = 2 * (tt * freq % 1) - 1
    elif shape == 'tri':
        wave_ = 2 * np.abs(2 * (tt * freq % 1) - 1) - 1
    else:
        wave_ = np.sin(2 * np.pi * freq * tt)
    env = np.minimum(1, tt / attack) * np.minimum(1, (dur - tt) / release).clip(0, 1)
    out[i0:i0 + n] += amp * wave_ * env


def kick(start, amp=0.9):
    i0, n = int(start * SR), int(0.35 * SR)
    n = min(n, len(out) - i0)
    tt = np.arange(n) / SR
    freq = 50 + 110 * np.exp(-tt * 30)
    out[i0:i0 + n] += amp * np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 9)


def click(start, amp=0.12):
    i0, n = int(start * SR), int(0.02 * SR)
    noise = np.random.default_rng(int(start * 1000)).standard_normal(n)
    out[i0:i0 + n] += amp * noise * np.exp(-np.arange(n) / SR * 300)


def hit(start, amp=0.35):
    for f in (440, 659.25, 880):
        note(f, start, 0.5, amp / 3, 'tri', 0.002, 0.45)
    kick(start, 0.7)


A, F, C, G = (220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (130.81, 196.0, 261.63), (196.0, 246.94, 293.66)
CHORDS = [A, F, C, G]

# pad: whole film, one chord per bar (2 s), final A minor rings out
for bar in range(6):
    for f in CHORDS[bar % 4]:
        note(f, bar * 4 * BEAT, 4 * BEAT + 0.3, 0.09, 'tri', 0.4, 0.5)
for f in A:
    note(f, 12.5, 2.5, 0.11, 'tri', 0.05, 2.0)

# scene 1: key clicks while '$ ship my-idea' types (frames 6..36), error at frame 45
for k in range(14):
    click(0.2 + k * 0.07)
note(110, 1.5, 0.4, 0.15, 'saw', 0.005, 0.3)

# scene 2: kicks on Learn it. / Build it. / Ship it.
for s in (2.0, 2.5, 3.0):
    kick(s)

# drop at 4 s: kick on every beat, sub bass, 16th arpeggio until 12.5 s
b = 4.0
while b < 12.49:
    kick(b, 0.8)
    b += BEAT
for bar in range(2, 7):
    root = CHORDS[bar % 4][0] / 2
    start = bar * 4 * BEAT
    if start >= 12.5:
        break
    note(root, start, min(4 * BEAT, 12.5 - start), 0.22, 'sine', 0.01, 0.1)
    for k in range(16):
        s = start + k * BEAT / 4
        if s < 4.0 or s >= 12.5:
            continue
        f = CHORDS[bar % 4][k % 3] * (2 if k % 8 >= 4 else 1)
        note(f, s, BEAT / 4, 0.05, 'saw', 0.003, 0.08)

# accent hits on the series cuts, logo landing and end card
for s in (4.0, 6.0, 8.1667, 10.3333, 12.5):
    hit(s)

out = out / max(1e-9, np.abs(out).max()) * 0.85
Path(__file__).with_name('public').mkdir(exist_ok=True)
with wave.open(str(Path(__file__).with_name('public') / 'bgm.wav'), 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((out * 32767).astype('<i2').tobytes())
print('Wrote film/public/bgm.wav')
