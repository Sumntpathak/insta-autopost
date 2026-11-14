"""Original collision-led electronic score for the generated fallback reel."""
import wave

import numpy as np


def render_score(path, rounds, collision_times):
    rate = 48_000
    mix = np.zeros((rate * 15, 2))
    rng = np.random.default_rng(281)

    def place(at, samples, pan=0):
        offset = round(at * rate)
        length = min(len(samples), len(mix) - offset)
        if length > 0:
            mix[offset:offset + length] += samples[:length, None] * [1 - .4 * pan, 1 + .4 * pan]

    def note(at, hz, duration, gain, pan=0, decay=5, sweep=0):
        t = np.arange(round(duration * rate)) / rate
        phase = 2 * np.pi * (hz * t + sweep * t * t / 2)
        body = np.sin(phase) + .22 * np.sin(2 * phase) + .08 * np.sin(3 * phase)
        envelope = np.minimum(t * 600, 1) * np.exp(-decay * t / duration)
        place(at, gain * body * envelope, pan)

    def tick(at, gain, pan):
        t = np.arange(round(.036 * rate)) / rate
        noise = np.diff(rng.normal(0, 1, len(t) + 1))
        place(at, gain * noise * np.exp(-t * 160) * np.minimum(t * 1200, 1), pan)

    # A soft sub pulse and dry offbeat ticks leave space for the collision rhythm.
    beat = 60 / 116
    for step in range(27):
        at = step * beat
        if 12.92 < at < 13.4:
            continue
        note(at, (55, 55, 65.41, 49)[(step // 4) % 4], .42, .18 if step % 4 == 0 else .12,
             decay=3.2, sweep=-13)
        if at + beat / 2 < 13.0:
            tick(at + beat / 2, .038, -.24 if step % 2 else .24)

    for round_index, (_, _, start, _) in enumerate(rounds):
        times = collision_times[round_index]
        # Keep isolated impacts exact. Group fast collisions into audible bursts.
        grouped = {}
        for i, elapsed in enumerate(times[1:], 1):
            if i <= 3 or i == len(times)-1:
                note(start + elapsed, 570 if i % 2 else 820, .16, .31, .48 if i % 2 else -.48)
            else:
                slot = int(elapsed / .041)
                grouped.setdefault(slot, []).append((elapsed, i))
        for impacts in grouped.values():
            elapsed, i = impacts[0]
            intensity = min(.22, .085 + .032 * np.log1p(len(impacts)))
            note(start + elapsed, 820 + 110 * round_index + 95 * (i % 2), .08, intensity,
                 .38 if i % 2 else -.38)
    for i, hz in enumerate((261.63, 392, 523.25, 659.25)):
        note(13.4 + .12 * i, hz, .63, .23, -.44 + i * .29, decay=3.4)
    mix *= .88 / max(.88, np.abs(mix).max())
    with wave.open(str(path), 'wb') as output:
        output.setparams((2, 2, rate, 0, 'NONE', 'not compressed'))
        output.writeframes((mix * 32767).astype('<i2').tobytes())
