import sys

import numpy as np
from scipy.io import wavfile
import audio

i = int(sys.argv[1])
hit1 = 81 + i % 5 * 3
hit2 = 195 + i % 4 * 5
shield = hit2 + 40
win = 319 + i * 2
track = audio.music([('mystery', 4.2), ('tense', 4.15), ('hope', 2.85), ('finale', 3.8)]) * .38
for f, sound, gain in [
    (hit1-27, audio.missile, .29), (hit1, audio.impact, .68), (hit1+29, audio.thud, .55),
    (hit2-30, audio.missile, .28), (hit2, audio.impact, .69), (hit2+27, audio.thud, .55),
    (shield, audio.swish, .44), (shield+27, audio.clink, .60), (shield+41, audio.clink, .55),
    (shield+54, audio.clink, .58), (win, audio.gold, .70),
]:
    audio.place(track, sound(), f / 30, gain)
wavfile.write('score.wav', audio.SR, (audio.norm(track, .89) * 32767).astype(np.int16))
