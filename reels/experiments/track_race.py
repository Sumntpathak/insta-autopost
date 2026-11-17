"""ShipStack Lab: 'Which path is faster?' brachistochrone race (15 s, 9:16).

Real physics, not animation: each ball is a frictionless bead released from rest at the
same height; speed comes from energy conservation, v = sqrt(2 g h). Both runs are shown
in the same slow-motion factor, so the race order and time ratio are exactly the
simulated ones. The longer, curved path wins because it drops steeply first and carries
that speed - the classic brachistochrone result, so the reveal is true, not staged.

Design (from reel retention basics; tune with reels/insights_report.py output):
  0.0-0.6 s  hook: question + both paths visible on the first frame (no blank intro)
  0.6-2.6 s  "pick A or B" countdown, balls glowing at the start line
  2.6-~10 s  race with speed readouts, trails and position-tracking audio
  winner     finish flash + chord the instant it actually arrives
  ~11-15 s   one-line explanation, CTA; key text stays out of IG's bottom/right UI zones

Usage: python reels/experiments/track_race.py --out race.mp4 [--width 360 for preview]
Requires numpy, Pillow, ffmpeg. No network, no Instagram API calls.
"""
import argparse
import math
import os
from pathlib import Path
import subprocess
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FPS, SECONDS = 30, 15
FRAMES = FPS * SECONDS
SR = 48000
FONT = Path(__file__).resolve().parents[2] / 'team/assets/fonts/DejaVuSans-Bold.ttf'
G = 9.81
PX_PER_M = 400.0                     # 1080-wide canvas ~ 2.7 m wide
START, END = (150.0, 640.0), (930.0, 1000.0)
LANE_A = -70.0                       # lane A drawn 70 px higher: identical 0.9 m drop, balls never overlap
RACE_START = 2.6
RACE_SPAN = 7.4                      # on-screen seconds for the slower ball (same factor for both)
BG, GRID, MUTED = (7, 10, 19), (16, 23, 38), (142, 155, 180)
COLORS = [(255, 175, 72), (65, 229, 246)]   # A = straight (orange), B = curve (cyan)
NAMES = ['A  STRAIGHT', 'B  CURVE']


def cycloid(start, end, n=2000):
    """Brachistochrone between two points (screen y grows downward)."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    lo, hi = 1e-3, 2 * math.pi - 1e-3          # solve (t - sin t)/(1 - cos t) = dx/dy
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if (mid - math.sin(mid)) / (1 - math.cos(mid)) > dx / dy else (mid, hi)
    theta = (lo + hi) / 2
    r = dy / (1 - math.cos(theta))
    t = np.linspace(0, theta, n)
    return np.stack([start[0] + r * (t - np.sin(t)), start[1] + r * (1 - np.cos(t))], axis=1)


def straight(start, end, n=2000):
    t = np.linspace(0, 1, n)[:, None]
    return np.array(start) * (1 - t) + np.array(end) * t


def simulate(path):
    """Arrival time (seconds, real physics) at every point of a polyline released from rest."""
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1) / PX_PER_M
    drop = (path[:, 1] - path[0, 1]) / PX_PER_M
    v = np.sqrt(2 * G * np.maximum(drop, 0))
    v_mid = (v[:-1] + v[1:]) / 2
    # Exact for the first segment from rest on a locally straight piece: t = 2 s / v_end.
    dt = np.where(v_mid > 0, seg / np.maximum(v_mid, 1e-9), 0)
    dt[0] = 2 * seg[0] / max(v[1], 1e-9)
    return np.concatenate([[0], np.cumsum(dt)]), v


def physics():
    lift = np.array([0.0, LANE_A])
    paths = [straight(np.array(START) + lift, np.array(END) + lift), cycloid(START, END)]
    runs = [simulate(p) for p in paths]
    totals = [float(t[-1]) for t, _ in runs]
    winner = int(np.argmin(totals))
    slow = RACE_SPAN / max(totals)       # one shared slow-motion factor keeps the race honest
    return paths, runs, totals, winner, slow


def state_at(sec, path, run, slow):
    """Position, speed (m/s) and finished flag at on-screen time sec."""
    times, speed = run
    real = max(0.0, (sec - RACE_START) / slow)
    if real >= times[-1]:
        return path[-1], speed[-1], True
    i = int(np.searchsorted(times, real))
    i = min(max(i, 1), len(times) - 1)
    f = (real - times[i - 1]) / max(times[i] - times[i - 1], 1e-12)
    return path[i - 1] + f * (path[i] - path[i - 1]), speed[i - 1] + f * (speed[i] - speed[i - 1]), False


def soundtrack(path, runs, totals, winner, slow):
    """48 kHz stereo; every sound is tied to a simulation event. A pans left, B right."""
    n = SR * SECONDS
    out = np.zeros((n, 2))
    t_all = np.arange(n) / SR

    def note(at, freq, dur, vol, pan=0.0, bright=0.25):
        s = int(at * SR); m = min(int(dur * SR), n - s)
        if m <= 0: return
        u = np.arange(m) / SR
        env = np.minimum(1, u / 0.005) * np.exp(-u * 5 / dur)
        w = vol * env * (np.sin(2 * np.pi * freq * u) + bright * np.sin(4 * np.pi * freq * u))
        out[s:s + m, 0] += w * (1 - pan) / 2 * 2 ** 0.5
        out[s:s + m, 1] += w * (1 + pan) / 2 * 2 ** 0.5

    # Soft pulse bed (90 bpm) under the hook and race, ducked at the reveal.
    for k, at in enumerate(np.arange(0, 11.5, 60 / 90)):
        note(at, 110 if k % 4 else 82.5, 0.35, 0.10, 0, 0.6)
    for i in range(3):                                         # countdown ticks: 3, 2, 1
        note(RACE_START - 2 + i * (2 / 3), 880, 0.08, 0.16)
    note(RACE_START, 1320, 0.15, 0.2)                          # release
    # Rolling tone: pitch follows each ball's real speed while it runs.
    for k, (times, speed) in enumerate(runs):
        on = (t_all >= RACE_START) & (t_all < RACE_START + totals[k] * slow)
        real = np.clip((t_all - RACE_START) / slow, 0, times[-1])
        v = np.interp(real, times, speed)
        freq = 180 + 60 * v + (0 if k == 0 else 7)
        phase = 2 * np.pi * np.cumsum(freq) / SR
        w = 0.05 * on * (np.sin(phase) + 0.3 * np.sin(2 * phase))
        pan = -0.7 if k == 0 else 0.7
        out[:, 0] += w * (1 - pan) / 2 * 2 ** 0.5
        out[:, 1] += w * (1 + pan) / 2 * 2 ** 0.5
        finish = RACE_START + totals[k] * slow
        note(finish, 660 if k != winner else 990, 0.25, 0.22, pan)
    win_at = RACE_START + totals[winner] * slow
    for i, f in enumerate((523.25, 659.25, 783.99, 1046.5)):   # winner chord
        note(win_at + 0.05 + i * 0.09, f, 0.9, 0.12)
    out = np.tanh(out * 1.4)
    out *= 0.89 / max(1e-9, np.max(np.abs(out)))
    fade = int(0.4 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return (out * 32767).astype(np.int16)


def render(out, width=1080):
    height = width * 16 // 9
    s = width / 1080
    P = lambda v: int(round(v * s))
    fonts = {}
    font = lambda size: fonts.setdefault(size, ImageFont.truetype(str(FONT), max(10, P(size))))
    paths, runs, totals, winner, slow = physics()
    loser = 1 - winner
    win_at = RACE_START + totals[winner] * slow
    lose_at = RACE_START + totals[loser] * slow
    margin = totals[loser] / totals[winner]

    base = Image.new('RGB', (width, height), BG)
    d = ImageDraw.Draw(base)
    for y in range(160, 1880, 72):
        d.line((P(40), P(y), P(1040), P(y)), fill=GRID, width=max(1, P(1)))
    for k, path in enumerate(paths):
        pts = [(P(x), P(y)) for x, y in path[::20]] + [(P(path[-1][0]), P(path[-1][1]))]
        d.line(pts, fill=(30, 40, 58), width=P(22), joint='curve')
        d.line(pts, fill=tuple(c // 2 for c in COLORS[k]), width=max(2, P(6)), joint='curve')
    d.line((P(END[0] + 40), P(END[1] - 150), P(END[0] + 40), P(END[1] + 40)), fill='white', width=P(5))
    for i, y in enumerate(range(int(END[1]) - 150, int(END[1]) + 30, 24)):
        d.rectangle((P(END[0] + 42), P(y), P(END[0] + 60), P(y + 12)), fill='white' if i % 2 == 0 else BG)
    d.text((P(80), P(110)), 'SHIPSTACK LAB', font=font(30), fill=COLORS[1])

    trails = [[], []]
    with tempfile.TemporaryDirectory() as tmp:
        audio = os.path.join(tmp, 'race.wav')
        with wave.open(audio, 'wb') as wf:
            wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
            wf.writeframes(soundtrack(paths, runs, totals, winner, slow).tobytes())
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pixel_format', 'rgb24',
               '-video_size', f'{width}x{height}', '-framerate', str(FPS), '-i', 'pipe:0', '-i', audio,
               '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', str(FPS),
               '-c:a', 'aac', '-b:a', '192k', '-ar', str(SR), '-frames:v', str(FRAMES), '-t', str(SECONDS),
               '-movflags', '+faststart', str(out)]
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        try:
            for frame in range(FRAMES):
                proc.stdin.write(frame_image(frame / FPS, base, P, font, paths, runs, slow, winner,
                                             win_at, lose_at, margin, trails).tobytes())
            proc.stdin.close()
        except BrokenPipeError:
            pass                      # ffmpeg died; its exit code below carries the real error
        finally:
            code = proc.wait()
    if code:
        raise RuntimeError(f'ffmpeg exited {code}')
    print(f'Winner: {"AB"[winner]} ({NAMES[winner].split()[1].lower()}); real times '
          f'A={totals[0]:.3f}s B={totals[1]:.3f}s; shown at {slow:.1f}x slow motion')


def centered(d, y, text, f, fill, P, width):
    w = d.textlength(text, font=f)
    d.text(((width - w) / 2, P(y)), text, font=f, fill=fill)


def frame_image(sec, base, P, font, paths, runs, slow, winner, win_at, lose_at, margin, trails):
    im = base.copy()
    width = im.width
    glow = Image.new('RGB', im.size, (0, 0, 0))
    g = ImageDraw.Draw(glow)
    d = ImageDraw.Draw(im)

    # Hook: big question on frame 1, so the paused first frame already sells the reel.
    pop = min(1, sec / 0.25)
    d.text((P(80), P(185)), 'WHICH BALL', font=font(int(64 + 14 * pop)), fill='white')
    d.text((P(80), P(285)), 'ARRIVES FIRST?', font=font(int(64 + 14 * pop)), fill='white')
    d.text((P(80), P(395)), 'Same drop. Same finish line. Only gravity.', font=font(30), fill=MUTED)

    for k in range(2):
        pos, speed, done = state_at(sec, paths[k], runs[k], slow)
        x, y = P(pos[0]), P(pos[1])
        if RACE_START <= sec and not done:
            trails[k].append((x, y))
        for i, (tx, ty) in enumerate(trails[k][-14:]):
            r = P(4 + i)
            g.ellipse((tx - r, ty - r, tx + r, ty + r), fill=tuple(c // 3 for c in COLORS[k]))
        r = P(26)
        pulse = 1 + (0.15 * math.sin(sec * 9) if sec < RACE_START else 0)
        gr = int(r * 1.9 * pulse)
        g.ellipse((x - gr, y - gr, x + gr, y + gr), fill=COLORS[k])
        d.ellipse((x - r, y - r, x + r, y + r), fill=COLORS[k])
        d.ellipse((x - r // 2, y - r // 2, x - r // 8, y - r // 8), fill='white')
        label_y = y - P(78) if k == 0 else y + P(38)
        d.text((x - P(14), label_y), 'AB'[k], font=font(40), fill=COLORS[k])
        # Speed readouts (real m/s) - the visible "why" while the race runs.
        d.text((P(80 + 470 * k), P(1130)), NAMES[k], font=font(30), fill=COLORS[k])
        d.text((P(80 + 470 * k), P(1172)), f'{speed:4.1f} m/s', font=font(46), fill='white')

    im = Image.fromarray(np.minimum(255, np.asarray(im, np.uint16) +
                                    np.asarray(glow.filter(ImageFilter.GaussianBlur(P(16))), np.uint16)).astype(np.uint8))
    d = ImageDraw.Draw(im)

    # Status card; kept above y=1500 so IG caption/buttons never cover it.
    d.rounded_rectangle((P(80), P(1270), P(1000), P(1440)), radius=P(34), fill=(19, 27, 44))
    if sec < RACE_START:
        status, colour = f'PICK  A  OR  B  ·  {math.ceil(RACE_START - sec)}', 'white'
    elif sec < win_at:
        status, colour = 'GO!' if sec < RACE_START + 0.5 else 'RACING…', 'white'
    else:
        status, colour = f'{"AB"[winner]} WINS · {margin:.2f}× FASTER', COLORS[winner]
    centered(d, 1322, status, font(54), colour, P, width)
    if win_at <= sec < win_at + 0.25:                        # finish flash
        flash = Image.new('RGB', im.size, COLORS[winner])
        im = Image.blend(im, flash, 0.25 * (1 - (sec - win_at) / 0.25))
        d = ImageDraw.Draw(im)

    if sec >= max(lose_at, win_at + 1.0):                   # explanation + CTA
        a = min(1, (sec - max(lose_at, win_at + 1.0)) / 0.4)
        c = tuple(int(v * a) for v in (255, 255, 255))
        m = tuple(int(v * a) for v in MUTED)
        centered(d, 1470, 'Same final speed. B just got it sooner:', font(36), c, P, width)
        centered(d, 1522, 'the steep drop pays off early.', font(36), c, P, width)
        centered(d, 1590, 'Did you guess right? Comment A or B', font(30), m, P, width)
    return im


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='track_race.mp4')
    ap.add_argument('--width', type=int, default=1080)
    args = ap.parse_args()
    render(args.out, args.width)
