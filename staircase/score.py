import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'nispa-batch'))
import audio

index = int(sys.argv[1])
part = index % 2
track = audio.music([('mystery', 8.2), ('hope' if part else 'tense', 2.9), ('finale', 3.9)]) * .30
for step in range(1, 9):
    audio.place(track, audio.thud(d=.11, f0=180, f1=92), step * 7.8 / 8 + (.85 if part else 0), .20)
audio.place(track, audio.swish(), 8.2, .34)
audio.place(track, audio.gold() if part else audio.boing(), 9.05, .47)
audio.place(track, audio.bell(f=880, d=.50), 11.1, .24)
wavfile.write('score.wav', audio.SR, (audio.norm(track, .82) * 32767).astype(np.int16))
