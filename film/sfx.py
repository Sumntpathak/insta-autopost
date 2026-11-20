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
