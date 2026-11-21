"""Original keyboard + UI sounds for the text reels (no licensing): 3 key clicks, a step 'done' tick, a result sting."""
import wave
from pathlib import Path
import numpy as np

SR = 44100
OUT = Path(__file__).with_name('public') / 'sfx'
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(11)


def write(name, x, peak=0.8):
    x = x / max(1e-9, np.abs(x).max()) * peak
    with wave.open(str(OUT / name), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())


def click(freq, decay):
    n = int(0.09 * SR); t = np.arange(n) / SR
    thock = np.sin(2 * np.pi * freq * t) * np.exp(-t * decay)                 # key bottoming out
    tick = rng.standard_normal(n) * np.exp(-t * 700) * 0.7                     # plastic click
    return thock * 0.8 + tick


for i, (f, d) in enumerate([(210, 60), (250, 70), (180, 55)]):
    write(f'key{i}.wav', click(f, d), 0.6)

t = np.arange(int(0.35 * SR)) / SR
write('done.wav', (np.sin(2 * np.pi * 880 * t) + 0.5 * np.sin(2 * np.pi * 1320 * t)) * np.exp(-t * 14), 0.5)   # step complete

t = np.arange(int(1.0 * SR)) / SR
chord = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((523.25, 1), (659.25, .8), (783.99, .7), (1046.5, .4)))
write('result.wav', chord * np.exp(-t * 3.2) * np.minimum(1, t / 0.01), 0.7)
print('Wrote key0-2, done, result')
