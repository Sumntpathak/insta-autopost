"""Ring Escape physics (pymunk) with pacing math.

Six balls bounce inside a rotating ring with one gap. The first ball whose centre leaves
the ring wins. Every reel is a real, deterministic simulation; the seed search only
*chooses* a seed whose natural outcome has good pacing - it never edits the result:
  - first escape lands inside the target window (payoff before viewers drift off)
  - clear winner: the runner-up escapes >= 0.5 s later, or not at all (no photo finish)
  - at least two near misses before the win (tension)
The renderer replays the recorded trajectory of the very run that passed these checks.
"""
import math
import random
from dataclasses import dataclass, field

import numpy as np
import pymunk



CENTER = (540.0, 1000.0)       # simulation frame (px); the renderer maps it into the figure box
RADIUS = 360.0
BALL_R = 34.0
GAP = 0.26                 # radians of opening (~94 px for a 68 px ball)
SPIN = 1.15                 # rad/s
GRAVITY = 1500.0            # px/s^2 (screen y down)
MIN_SPEED, MAX_SPEED = 650.0, 1500.0
HZ = 240                    # physics steps per second (8 per video frame)
SIM_SECONDS = 12.8          # race length after release
WIN_WINDOW = (6.8, 9.0)     # seconds after release
CLEAR_MARGIN = 0.5
MIN_NEAR_MISSES = 2


@dataclass
class Run:
    seed: int
    positions: np.ndarray            # (steps+1, n, 2)
    ring_angle: np.ndarray           # (steps+1,)
    escapes: dict                    # ball index -> escape time (s)
    impacts: list                    # (time, ball, strength 0..1, x)
    near_misses: int
    escape_speed: dict = field(default_factory=dict)

    @property
    def order(self):
        return sorted(self.escapes, key=self.escapes.get)

    @property
    def winner(self):
        return self.order[0] if self.escapes else None


def _ring(space):
    body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
    body.position = CENTER
    body.angular_velocity = SPIN
    space.add(body)
    n = 72
    start = GAP / 2
    span = 2 * math.pi - GAP
    pts = [(RADIUS * math.cos(start + span * i / n), RADIUS * math.sin(start + span * i / n)) for i in range(n + 1)]
    for a, b in zip(pts, pts[1:]):
        seg = pymunk.Segment(body, a, b, 8)
        seg.elasticity, seg.friction = 1.0, 0.0
        seg.filter = pymunk.ShapeFilter(categories=0b10)
        space.add(seg)
    return body


def simulate(seed, n=6, seconds=SIM_SECONDS):
    rng = random.Random(seed)
    space = pymunk.Space()
    space.gravity = (0, GRAVITY)
    space.iterations = 20
    ring = _ring(space)
    balls = []
    placed = []
    while len(placed) < n:
        r = rng.uniform(0, RADIUS - BALL_R * 2.2)
        a = rng.uniform(0, 2 * math.pi)
        p = (CENTER[0] + r * math.cos(a), CENTER[1] + r * math.sin(a))
        if all(math.dist(p, q) > BALL_R * 2.3 for q in placed):
            placed.append(p)
    for p in placed:
        body = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BALL_R))
        body.position = p
        ang = rng.uniform(0, 2 * math.pi)
        speed = rng.uniform(MIN_SPEED, MIN_SPEED * 1.4)
        body.velocity = (speed * math.cos(ang), speed * math.sin(ang))
        shape = pymunk.Circle(body, BALL_R)
        shape.elasticity, shape.friction = 1.0, 0.0
        shape.filter = pymunk.ShapeFilter(categories=0b01, mask=0b11)
        space.add(body, shape)
        balls.append((body, shape))
    steps = int(seconds * HZ)
    dt = 1 / HZ
    pos = np.zeros((steps + 1, n, 2))
    ang = np.zeros(steps + 1)
    pos[0] = [b.position for b, _ in balls]
    escapes, speeds, impacts = {}, {}, []
    near, in_gap = 0, [False] * n
    last_impact = [-1.0] * n
    prev_v = [b.velocity for b, _ in balls]
    for step in range(1, steps + 1):
        space.step(dt)
        t = step * dt
        for i, (body, shape) in enumerate(balls):
            v = body.velocity
            if i not in escapes:
                speed = v.length
                if speed < MIN_SPEED and speed > 0:
                    body.velocity = v * (MIN_SPEED / speed)   # keep the race lively (no settling)
                elif speed > MAX_SPEED:
                    body.velocity = v * (MAX_SPEED / speed)
                dv = (body.velocity - prev_v[i]).length
                if dv > 300 and t - last_impact[i] > 0.06:
                    impacts.append((t, i, min(1.0, dv / 1800), body.position.x))
                    last_impact[i] = t
                rel = body.position - CENTER
                d = rel.length
                if d > RADIUS + BALL_R * 0.6:
                    escapes[i] = t
                    speeds[i] = body.velocity.length
                    shape.filter = pymunk.ShapeFilter(categories=0b01, mask=0)   # fall away freely
                else:
                    # Near miss: ball touches the rim while the gap is within one gap-width of it.
                    gap_dir = ring.angle % (2 * math.pi)
                    off = (math.atan2(rel.y, rel.x) - gap_dir + math.pi) % (2 * math.pi) - math.pi
                    close = d > RADIUS - BALL_R * 1.6 and GAP / 2 < abs(off) < GAP * 1.5
                    if close and not in_gap[i]:
                        near += 1 if not escapes else 0
                    in_gap[i] = close
            prev_v[i] = body.velocity
        pos[step] = [b.position for b, _ in balls]
        ang[step] = ring.angle
    return Run(seed, pos, ang, escapes, impacts, near, speeds)


def good(run):
    if run.winner is None:
        return False
    t1 = run.escapes[run.winner]
    if not WIN_WINDOW[0] <= t1 <= WIN_WINDOW[1]:
        return False
    if len(run.order) > 1 and run.escapes[run.order[1]] - t1 < CLEAR_MARGIN:
        return False
    return run.near_misses >= MIN_NEAR_MISSES


def choose(base_seed, tries=400):
    """First seed at or after base_seed whose natural outcome passes the pacing checks."""
    for k in range(tries):
        run = simulate(base_seed + k)
        if good(run):
            return run
    raise RuntimeError(f'No seed with good pacing in {tries} tries from {base_seed}')
