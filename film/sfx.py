"""Original sound design for the film (no licensing): whoosh and sunrise pad."""
import wave
from pathlib import Path
import numpy as np

SR = 44100
OUT = Path(__file__).with_name('public') / 'sfx'
OUT.mkdir(parents=True, exist_ok=True)


def write(name, x):
    x = x / max(1e-9, np.abs(x).max()) * 0.8
    with wave.open(str(OUT / name), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())


rng = np.random.default_rng(7)
# whoosh: filtered noise sweeping down, 1.8 s
n = int(1.8 * SR); t = np.arange(n) / SR
noise = rng.standard_normal(n)
env = np.sin(np.pi * np.clip(t / 1.8, 0, 1)) ** 2
cut = np.linspace(0.35, 0.03, n)                     # simple one-pole low-pass, closing
y = np.zeros(n); acc = 0.0
for i in range(n):
    acc += cut[i] * (noise[i] - acc); y[i] = acc
write('whoosh.wav', y * env)

# sunrise pad: soft major-seventh chord with slow swell, 20 s
n = int(20 * SR); t = np.arange(n) / SR
pad = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * a for f, a in
          ((130.81, 1), (196.0, .7), (246.94, .5), (329.63, .4), (392.0, .25)))
pad *= (0.6 + 0.4 * np.sin(2 * np.pi * 0.08 * t)) * np.minimum(1, t / 2.5) * np.minimum(1, (20 - t) / 2)
write('sunrise-pad.wav', pad)
print('Wrote public/sfx/whoosh.wav, sunrise-pad.wav')

# logo sting, 4 s, cues match src/LogoSting.tsx
n = int(4 * SR); t = np.arange(n) / SR; out = np.zeros(n)


def at(sec, x, gain=1.0):
    i = int(sec * SR); m = min(len(x), n - i); out[i:i + m] += gain * x[:m]


def tone(f, dur, decay, shape=np.sin):
    tt = np.arange(int(dur * SR)) / SR
    return shape(2 * np.pi * f * tt) * np.exp(-tt * decay)


click = rng.standard_normal(int(0.012 * SR)) * np.exp(-np.arange(int(0.012 * SR)) / SR * 400)
for sec in (0.05, 0.38):
    at(sec, tone(1800, 0.05, 90), 0.25)                       # cursor blinks
m = int(0.6 * SR); tt = np.arange(m) / SR
sw = rng.standard_normal(m); y = np.zeros(m); acc = 0.0
for i in range(m):
    acc += (0.02 + 0.25 * tt[i] / 0.6) * (sw[i] - acc); y[i] = acc
at(0.4, y * np.sin(np.pi * tt / 0.6) ** 2, 0.6)               # line stretches
tk = np.arange(int(0.4 * SR)) / SR
at(0.88, np.sin(2 * np.pi * np.cumsum(55 + 90 * np.exp(-tk * 25)) / SR) * np.exp(-tk * 10), 0.8)   # hull thump
dr = np.arange(int(0.4 * SR)) / SR
at(1.15, np.sin(2 * np.pi * np.cumsum(400 + 500 * dr / 0.4) / SR) * 0.15 * np.sin(np.pi * dr / 0.4), 0.6)  # sail draws
for f, g in ((440, .5), (659.25, .4), (880, .3), (1318.5, .15)):
    at(1.6, tone(f, 2.2, 2.2), g)                              # sail snaps: chime
at(1.6, np.sin(2 * np.pi * np.cumsum(50 + 70 * np.exp(-tk * 30)) / SR) * np.exp(-tk * 8), 0.7)
for k in range(9):
    at(1.95 + k * 2 / 30, click, 0.35)                         # typing
write('logo-sting.wav', out)
print('Wrote public/sfx/logo-sting.wav')
