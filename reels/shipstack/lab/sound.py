"""Sound design: SignalFlow synthesises each voice once; numpy places them on the timeline.

Voices are short, soft and tuned (C major pentatonic) so event sounds stay musical:
  pluck   - a mallet-like FM tone for physical events (ticks, markers, arrivals)
  chord   - a warm reveal chord
  pad     - a quiet low drone under the whole reel (keeps silence from feeling empty)
All placement times come from the simulation, so audio and picture always agree.
"""
import functools
import wave

import numpy as np
from signalflow import (AudioGraph, AudioGraphConfig, AudioOut_Dummy, ASREnvelope, SineOscillator,
                        SVFilter, StereoPanner)

SR = 44100            # SignalFlow's offline graph runs at 44.1 kHz; ffmpeg resamples to 48 kHz
_graph = None


def _g():
    global _graph
    if _graph is None:
        cfg = AudioGraphConfig()
        cfg.sample_rate = SR
        _graph = AudioGraph(config=cfg, output_device=AudioOut_Dummy(2), start=False)
        assert _graph.sample_rate == SR, f'SignalFlow graph runs at {_graph.sample_rate} Hz, expected {SR}'
    return _graph


def _render(node, seconds):
    g = _g()
    g.play(node)
    buf = g.render_to_new_buffer(int(seconds * SR))
    g.stop(node)
    return np.array(buf.data, dtype=np.float64).T          # (n, 2)


@functools.lru_cache(maxsize=None)
def pluck(freq, dur=0.6, bright=2.0):
    _g()
    env = ASREnvelope(0.002, 0.02, dur)
    mod = SineOscillator(freq * 2.0) * freq * bright * ASREnvelope(0.001, 0.0, dur * 0.35)
    tone = SineOscillator(freq + mod) * env * 0.5
    return _render(StereoPanner(SVFilter(tone, 'low_pass', 4200, 0.3), 0.0), dur + 0.05)


@functools.lru_cache(maxsize=None)
def chord(root=261.63, dur=2.2):
    _g()
    voices = sum(SineOscillator(root * r) * a for r, a in ((1, .32), (1.25, .22), (1.5, .2), (2, .12)))
    env = ASREnvelope(0.04, 0.3, dur)
    return _render(StereoPanner(SVFilter(voices * env, 'low_pass', 2400, 0.2), 0.0), dur + 0.1)


@functools.lru_cache(maxsize=None)
def pad(seconds, root=65.41):
    _g()
    tone = (SineOscillator(root) * 0.18 + SineOscillator(root * 1.5) * 0.08 + SineOscillator(root * 2.003) * 0.05)
    return _render(StereoPanner(SVFilter(tone, 'low_pass', 600, 0.1), 0.0), seconds)


PENTA = [261.63, 293.66, 329.63, 392.0, 440.0, 523.25, 587.33, 659.25, 783.99, 880.0]


class Timeline:
    def __init__(self, seconds):
        self.out = np.zeros((int(seconds * SR), 2))

    def add(self, at, clip, gain=1.0, pan=0.0):
        s = int(at * SR)
        if s >= len(self.out) or s < 0:
            return
        clip = clip[: len(self.out) - s]
        left, right = np.sqrt((1 - pan) / 2) * 1.414, np.sqrt((1 + pan) / 2) * 1.414
        self.out[s:s + len(clip), 0] += clip[:, 0] * gain * left
        self.out[s:s + len(clip), 1] += clip[:, 1] * gain * right

    def write(self, path, fade=0.4):
        out = np.tanh(self.out * 1.2)
        out *= 0.89 / max(1e-9, float(np.max(np.abs(out))))
        n = int(fade * SR)
        out[-n:] *= np.linspace(1, 0, n)[:, None]
        with wave.open(str(path), 'wb') as wf:
            wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
            wf.writeframes((out * 32767).astype(np.int16).tobytes())
