"""
SHIPSTACK RESET SERIES - 10 guided follow-along reels (1080x1920, sound)
Same look and structure as EYE RESET: hook -> numbered steps with progress bar -> SAVE card.

Reels:
  eye2      EYE RESET 2       diagonals, zigzag, spiral, blinks, far focus
  box       BOX BREATHING     4-4-4-4 square breathing, 2 rounds
  sleep     4-7-8 SLEEP       sleep breathing, 2 rounds
  sigh      CALM IN 30s       physiological sigh, 3 rounds
  focus     FOCUS TEST        keep eyes on the dot while distractions fly in
  neck      NECK RESET        turns, nods, ear to shoulder, shoulder rolls
  unclench  UNCLENCH          body scan: forehead, jaw, shoulders, hands, belly
  ground    5-4-3-2-1         grounding for overthinking
  soft      SOFT FOCUS        panoramic vision eye relaxation
  posture   POSTURE RESET     sit tall, chin back, shoulders back

Requires: pip install pygame numpy  (+ ffmpeg)
Usage:
  python reset_series.py                 # render all 10
  python reset_series.py box sleep       # render chosen ones
  python reset_series.py --fps 60        # smoother (slower render)
  python reset_series.py --preview       # also save a preview sheet per reel
"""
import os, sys, math, random, wave, argparse, subprocess
os.environ["SDL_VIDEODRIVER"] = "dummy"
import numpy as np
import pygame

W, H = 1080, 1920
CX, CY, AX, AY = 540, 1000, 380, 420
GOLD, PEACH, WHITE = (243, 200, 120), (246, 170, 120), (238, 240, 245)
DIM, GUIDE, BG = (130, 136, 150), (44, 48, 60), (14, 16, 22)
RED = (255, 110, 110)
HOOK_T, END_LEN = 2.6, 3.6

def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k
def shade(c, k): return tuple(int(lerp(BG[i], c[i], k)) for i in range(3))

# ======================= shared drawing context =======================
class Ctx:
    def __init__(self):
        pygame.font.init()
        path = pygame.font.match_font("dejavusans", bold=True)
        self.f = {k: pygame.font.Font(path, v) for k, v in dict(
            brand=24, title=84, step=40, hint=36, hook=66, big=220, mid=110,
            cta=60, small=34, tiny=26).items()}
        self.bg = self._background()
        self.glow = self._glow(110, (150, 110, 45))
        self.glow_big = self._glow(300, (90, 66, 28))
        self.state = {}

    def _background(self):
        g = np.linspace(0, 1, H)[:, None]
        col = (np.array(BG) * (1 - g) + np.array((6, 7, 10)) * g)[:, None, :].repeat(W, 1)
        yy, xx = np.mgrid[0:H, 0:W]
        spot = np.clip(1 - np.hypot((xx - CX) / 560, (yy - CY) / 700), 0, 1) ** 2 * 14
        col = np.clip(col + spot[..., None] * np.array([.8, .9, 1.2]), 0, 255).astype(np.uint8)
        return pygame.surfarray.make_surface(col.swapaxes(0, 1))

    def _glow(self, r, color):
        yy, xx = np.mgrid[-r:r, -r:r]
        f = np.clip(1 - np.hypot(xx, yy) / r, 0, 1) ** 2.4
        return pygame.surfarray.make_surface((f[..., None] * np.array(color)).astype(np.uint8).swapaxes(0, 1))

    def spaced(self, s, font, color, sp):
        imgs = [self.f[font].render(c, True, color) for c in s]
        out = pygame.Surface((max(1, sum(i.get_width() for i in imgs) + sp * (len(s) - 1)),
                              self.f[font].get_height()), pygame.SRCALPHA)
        x = 0
        for i in imgs: out.blit(i, (x, 0)); x += i.get_width() + sp
        return out

    def blit(self, s, img, c, alpha=255):
        if alpha < 255: img = img.copy(); img.set_alpha(max(0, int(alpha)))
        s.blit(img, img.get_rect(center=(int(c[0]), int(c[1]))))

    def text(self, s, txt, font, color, c, alpha=255):
        self.blit(s, self.f[font].render(txt, True, color), c, alpha)

    def add_glow(self, s, x, y, big=False):
        g = self.glow_big if big else self.glow
        s.blit(g, g.get_rect(center=(int(x), int(y))), special_flags=pygame.BLEND_RGB_ADD)

    def dot(self, s, x, y, key="dot", r=34):
        tr = self.state.setdefault(key, [])
        tr.append((x, y)); del tr[:-16]
        for j, (tx, ty) in enumerate(tr[:-1]):
            k = j / len(tr)
            pygame.draw.circle(s, shade(GOLD, k * .5), (int(tx), int(ty)), int(10 + 20 * k))
        self.add_glow(s, x, y)
        pygame.draw.circle(s, GOLD, (int(x), int(y)), r)
        pygame.draw.circle(s, WHITE, (int(x) - r // 3, int(y) - r // 3), max(4, r // 4))

    def guide(self, s, fn, d):
        for k in range(0, 241, 4):
            x, y = fn(d * k / 240, d)
            pygame.draw.circle(s, GUIDE, (int(x), int(y)), 3)

# ======================= step builders =======================
def path_step(name, dur, fn, hint="Head still. Move only your eyes."):
    def draw(s, u, d, C):
        C.guide(s, fn, d)
        C.dot(s, *fn(u, d))
        C.text(s, hint, "hint", DIM, (540, 1560))
    cues = lambda d: [(k + .5, 440, .3, .06, 14) for k in range(int(d))]
    return dict(name=name, dur=dur, draw=draw, cues=cues)

def draw_eye(s, openness, cx=CX, cy=CY, w=320):
    h = max(4, 150 * openness)
    top = [(cx - w / 2 + w * k / 40, cy - h / 2 * math.sin(math.pi * k / 40)) for k in range(41)]
    bot = [(cx - w / 2 + w * k / 40, cy + h / 2 * math.sin(math.pi * k / 40)) for k in range(41)]
    if openness > .15:
        clip = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(clip, (*GOLD, 255), top + bot[::-1])
        pupil = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.circle(pupil, (*GOLD, 255), (cx, cy), 48)
        pygame.draw.circle(pupil, (*BG, 255), (cx, cy), 20)
        pupil.blit(clip, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        s.blit(pupil, (0, 0))
    pygame.draw.lines(s, WHITE, False, top, 6)
    pygame.draw.lines(s, WHITE, False, bot, 6)

def blink_step(dur=4):
    def draw(s, u, d, C):
        ph = u % 1.0
        draw_eye(s, 1 - math.sin(math.pi * min(1, ph / .6)) if ph < .6 else 1)
        C.text(s, f"Blink slowly \u00b7 {min(int(d), int(u) + 1)}/{int(d)}", "cta", GOLD, (540, 1300))
    return dict(name="SLOW BLINKS", dur=dur, draw=draw,
                cues=lambda d: [(k + .4, 523, .8, .12, 5) for k in range(int(d))])

def far_step(dur=5):
    def draw(s, u, d, C):
        n = int(d) - int(u)
        C.text(s, str(n), "big", GOLD, (540, 1000), 255 * (1 - (u % 1) * .6))
        C.text(s, "Look at something", "hint", WHITE, (540, 1260))
        C.text(s, "at least 20 feet (6 m) away", "hint", WHITE, (540, 1310))
    return dict(name="LOOK FAR AWAY", dur=dur, draw=draw,
                cues=lambda d: [(k + .3, 392, .4, .1, 9) for k in range(int(d))])

def breath_scale(phases, u):
    """phases: [(label, dur, target)] -> (label, scale, seconds in phase, phase dur)"""
    s0, t0 = 0.0, 0.0
    for label, d, tgt in phases:
        if u < t0 + d:
            k = (u - t0) / d
            return label, lerp(s0, tgt, ease(k)), u - t0, d
        s0, t0 = tgt, t0 + d
    return phases[-1][0], phases[-1][2], phases[-1][1], phases[-1][1]

def breath_cues(phases):
    def cues(d):
        out, t0 = [], 0
        for label, pd, tgt in phases:
            f = 523 if "IN" in label.upper() or "SIP" in label.upper() else (392 if "EX" in label.upper() else 659)
            out.append((t0 + .02, f, 1.4, .16, 3))
            out += [(t0 + k, 330, .2, .03, 18) for k in range(1, int(pd))]
            t0 += pd
        return out
    return cues

def draw_breath_circle(s, C, scale, label, secs, rmin=110, rmax=380, cy=CY, count=True):
    r = int(rmin + (rmax - rmin) * scale)
    C.add_glow(s, CX, cy, big=True)
    pygame.draw.circle(s, shade(GOLD, .16 + .12 * scale), (CX, cy), r)
    pygame.draw.circle(s, GOLD, (CX, cy), r, 5)
    if count:
        C.text(s, str(int(secs) + 1), "mid", WHITE, (CX, cy - 10))
    C.blit(s, C.spaced(label, "step", GOLD, 6), (CX, cy + max(r, 150) + 70))

def breath_step(name, phases, rmin=110, rmax=380):
    dur = sum(p[1] for p in phases)
    def draw(s, u, d, C):
        label, sc, secs, _ = breath_scale(phases, u)
        draw_breath_circle(s, C, sc, label, secs, rmin, rmax)
    return dict(name=name, dur=dur, draw=draw, cues=breath_cues(phases))

def box_step(name):
    phases = [("INHALE", 4, 1), ("HOLD", 4, 1), ("EXHALE", 4, 0), ("HOLD", 4, 0)]
    L, T, R, B = CX - 330, CY - 330, CX + 330, CY + 330
    corners = [(L, B), (L, T), (R, T), (R, B), (L, B)]
    def draw(s, u, d, C):
        pygame.draw.rect(s, GUIDE, (L, T, R - L, B - T), 4, border_radius=6)
        label, sc, secs, _ = breath_scale(phases, u)
        i = min(3, int(u // 4)); k = ease((u - 4 * i) / 4)
        a, b = corners[i], corners[i + 1]
        pygame.draw.line(s, shade(GOLD, .6), a, (lerp(a[0], b[0], k), lerp(a[1], b[1], k)), 6)
        r = int(70 + 150 * sc)
        pygame.draw.circle(s, shade(GOLD, .16 + .12 * sc), (CX, CY), r)
        pygame.draw.circle(s, GOLD, (CX, CY), r, 4)
        C.text(s, str(int(secs) + 1), "mid", WHITE, (CX, CY - 8))
        C.dot(s, lerp(a[0], b[0], k), lerp(a[1], b[1], k))
        side = [((L - 60, CY), 90), ((CX, T - 55), 0), ((R + 60, CY), -90), ((CX, B + 55), 0)]
        for j, ((px, py), rot) in enumerate(side):
            img = C.spaced(phases[j][0], "tiny", GOLD if j == i else DIM, 5)
            C.blit(s, pygame.transform.rotate(img, rot), (px, py))
    return dict(name=name, dur=16, draw=draw, cues=breath_cues(phases))

# ---------- focus test ----------
DISTRACT = ["1 new message", "LOOK HERE", "notification", "50% OFF", "someone liked", "breaking news",
            "your mom called", "battery 5%", "new follower", "trending now"]
def focus_step(name, dur, level, t_offset):
    rng = random.Random(level)
    arrows = [(rng.uniform(0, dur), rng.uniform(560, 1500), rng.choice(DISTRACT), rng.choice([-1, 1]))
              for _ in range(0 if level == 1 else 7 if level == 2 else 12)]
    pops = [(rng.uniform(0, dur - .8), rng.uniform(220, 860), rng.choice([620, 1400]), rng.choice(DISTRACT))
            for _ in range(0 if level < 3 else 7)]
    total = 20
    def draw(s, u, d, C):
        left = total - (t_offset + u)
        pygame.draw.circle(s, GUIDE, (CX, CY), 120, 6)
        frac = max(0, left / total)
        pygame.draw.arc(s, GOLD, (CX - 120, CY - 120, 240, 240), math.pi / 2, math.pi / 2 + 2 * math.pi * frac, 7)
        C.dot(s, CX, CY)
        C.text(s, f"{max(0, math.ceil(left))}s", "cta", WHITE, (CX, CY + 200))
        for ft, y, lbl, sgn in arrows:
            k = (u - ft) / 1.1
            if 0 <= k <= 1:
                x = lerp(1200, -200, k) if sgn < 0 else lerp(-200, 1200, k)
                pygame.draw.line(s, WHITE, (x, y), (x + 80 * -sgn, y), 4)
                tip = [(x + 16 * sgn, y), (x, y - 10), (x, y + 10)]
                pygame.draw.polygon(s, WHITE, tip)
                C.text(s, lbl, "tiny", DIM, (x - 40 * sgn, y - 26))
        for ft, x, y, lbl in pops:
            if 0 <= u - ft < .8:
                rect = pygame.Rect(0, 0, 360, 96); rect.center = (x, y)
                pygame.draw.rect(s, (34, 38, 48), rect, border_radius=22)
                pygame.draw.rect(s, RED if "battery" in lbl else GOLD, rect, 3, border_radius=22)
                C.text(s, lbl, "small", WHITE, rect.center)
        msg = ["Easy so far\u2026", "Don\u2019t look at them", "Most people fail here"][level - 1]
        C.text(s, msg, "hint", DIM, (540, 1600))
    cues = lambda d: [(k + .05, 440, .25, .06, 14) for k in range(int(d))] + \
                     [(a[0], 880, .15, .05, 25) for a in arrows] + [(p[0], 1046, .2, .08, 20) for p in pops]
    return dict(name=name, dur=dur, draw=draw, cues=cues)

# ---------- neck reset ----------
def draw_neck_figure(s, turn=0.0, nod=0.0, tilt=0.0, shrug=0.0):
    base = (540, 1080)
    sh_y = 1160 - 40 * shrug
    pygame.draw.line(s, WHITE, (540, 1080), (540, sh_y), 10)
    pygame.draw.line(s, WHITE, (340, sh_y + 10), (740, sh_y + 10), 10)
    for sx in (340, 740):
        pygame.draw.circle(s, WHITE, (sx, int(sh_y + 10)), 5)
        pygame.draw.line(s, WHITE, (sx, sh_y + 10), (sx + (-30 if sx < 540 else 30), 1500), 10)
    pygame.draw.line(s, WHITE, (540, sh_y + 10), (540, 1500), 10)
    a = math.radians(tilt)
    def rot(x, y):
        dx, dy = x - base[0], y - base[1]
        return (base[0] + dx * math.cos(a) - dy * math.sin(a), base[1] + dx * math.sin(a) + dy * math.cos(a))
    hc = rot(540, 930)
    pygame.draw.circle(s, WHITE, (int(hc[0]), int(hc[1])), 112, 7)
    fx, fy = 46 * turn, 34 * nod
    for ex in (-40, 40):
        e = rot(540 + ex + fx, 915 + fy)
        pygame.draw.circle(s, GOLD, (int(e[0]), int(e[1])), 11)
    n1, n2 = rot(540 + fx * 1.25, 930 + fy), rot(540 + fx * 1.25 + 8 * turn, 960 + fy)
    pygame.draw.line(s, GOLD, n1, n2, 6)

def neck_step(name, dur, mode):
    def draw(s, u, d, C):
        w = 2 * math.pi * u / 4
        if mode == "turn":
            draw_neck_figure(s, turn=math.sin(w)); C.dot(s, CX + 330 * math.sin(w), 760, r=22)
        elif mode == "nod":
            draw_neck_figure(s, nod=math.sin(w)); C.dot(s, CX + 300, CY - 90 + 180 * math.sin(w), r=22)
        elif mode == "tilt":
            draw_neck_figure(s, tilt=28 * math.sin(2 * math.pi * u / 5))
        else:
            sh = .5 - .5 * math.cos(2 * math.pi * u / 3)
            draw_neck_figure(s, shrug=sh)
            for sx in (340, 740):
                pygame.draw.arc(s, shade(GOLD, .7), (sx - 50, 1080, 100, 100), 0, 2 * math.pi * ((u / 3) % 1), 4)
        C.text(s, "Slow & gentle. Stop if anything hurts.", "hint", DIM, (540, 1600))
    period = 3 if mode == "roll" else 4 if mode in ("turn", "nod") else 5
    cues = lambda d: [(k * period / 2 + .1, 440, .4, .06, 8) for k in range(int(2 * d / period))]
    return dict(name=name, dur=dur, draw=draw, cues=cues)

# ---------- unclench body scan ----------
def draw_standing(s, shoulder_up=1.0, hands_open=0.0, jaw_open=0.0, belly=0.0):
    hy = 680; sy = 840 - 45 * shoulder_up
    pygame.draw.circle(s, WHITE, (540, hy), 84, 7)
    mw = 30; my = hy + 38
    pygame.draw.line(s, WHITE, (540 - mw, my), (540 + mw, my), 5) if jaw_open < .5 else \
        pygame.draw.ellipse(s, WHITE, (540 - 22, my - 8, 44, 18), 4)
    for ex in (-30, 30): pygame.draw.circle(s, WHITE, (540 + ex, hy - 8), 7)
    pygame.draw.line(s, WHITE, (540, hy + 84), (540, 1180), 10)
    pygame.draw.line(s, WHITE, (380, sy), (700, sy), 10)
    pygame.draw.line(s, WHITE, (540, hy + 84), (540, sy), 10)
    for sx, dx in ((380, -1), (700, 1)):
        hand = (sx + 40 * dx, 1200)
        pygame.draw.line(s, WHITE, (sx, sy), hand, 10)
        if hands_open < .5: pygame.draw.circle(s, WHITE, hand, 22)
        else:
            pygame.draw.circle(s, WHITE, hand, 22, 5)
            for fi in range(-2, 3):
                pygame.draw.line(s, WHITE, (hand[0] + fi * 9, hand[1] + 18), (hand[0] + fi * 12, hand[1] + 48), 4)
    for fx in (-1, 1):
        pygame.draw.line(s, WHITE, (540, 1180), (540 + 100 * fx, 1560), 10)
    if belly > 0:
        r = int(40 + 50 * belly)
        pygame.draw.circle(s, shade(GOLD, .5), (540, 1060), r, 4)

def unclench_step(name, dur, part):
    order = ["forehead", "jaw", "shoulders", "hands", "belly"]
    idx = order.index(part)
    spots = dict(forehead=[(540, 630)], jaw=[(540, 722)], shoulders=[(380, 800), (700, 800)],
                 hands=[(340, 1200), (740, 1200)], belly=[(540, 1060)])
    def draw(s, u, d, C):
        k = ease(u / 2.5)
        su = 1 - (k if idx == 2 else (1 if idx > 2 else 0))
        ho = (k if idx == 3 else (1 if idx > 3 else 0))
        jo = 1 if idx == 1 and u > .8 else 0
        bel = .5 - .5 * math.cos(2 * math.pi * u / 4) if idx == 4 else 0
        for (x, y) in spots[part]:
            C.add_glow(s, x, y)
        draw_standing(s, su, ho, jo, bel)
        hints = ["Let the skin between your eyebrows go", "Let your teeth come apart",
                 "Let them fall away from your ears", "Open your fingers, let them hang", "Slow breath into your stomach"]
        C.text(s, hints[idx], "hint", WHITE, (540, 1640))
    return dict(name=name, dur=dur, draw=draw, cues=lambda d: [(1.2, 392, 1.5, .08, 3)])

# ---------- 5-4-3-2-1 grounding ----------
def ground_step(n, sense, dur):
    def draw(s, u, d, C):
        C.text(s, str(n), "big", GOLD, (540, 960))
        lit = min(n, int(u / ((d - .6) / n)) + 1)
        for j in range(n):
            a = -math.pi / 2 + 2 * math.pi * j / n
            x, y = CX + 300 * math.cos(a), 960 + 300 * math.sin(a)
            if j < lit:
                C.add_glow(s, x, y); pygame.draw.circle(s, GOLD, (int(x), int(y)), 22)
            else:
                pygame.draw.circle(s, GUIDE, (int(x), int(y)), 22, 4)
        C.text(s, f"things you can {sense}" if n > 1 else f"thing you can {sense}", "cta", WHITE, (540, 1380))
        C.text(s, "Name each one in your head", "hint", DIM, (540, 1460))
    step = lambda d: [(j * (d - .6) / n + .05, 523 + 40 * j, .5, .1, 7) for j in range(n)]
    return dict(name=f"{n} \u00b7 {sense.upper()}", dur=dur, draw=draw, cues=step)

# ---------- soft focus ----------
def soft_step(name, dur, stage):
    marks = [(70, CY), (1010, CY), (540, 600), (540, 1460)]
    def draw(s, u, d, C):
        maxr = [200, 470, 520, 520][stage]
        for j in range(5):
            k = ((u * (.35 if stage == 3 else .55)) + j / 5) % 1
            pygame.draw.circle(s, shade(GOLD, .5 * (1 - k)), (CX, CY), int(60 + maxr * k), 3)
        if stage >= 1:
            for j, (x, y) in enumerate(marks):
                if j < 2 or stage >= 2:
                    pul = .6 + .4 * math.sin(u * 4 + j)
                    pygame.draw.circle(s, shade(GOLD, pul), (x, y), 16)
        C.dot(s, CX, CY, r=30)
        msg = ["Keep your eyes on the dot", "Notice the left and right edges", "Now the top and bottom too",
               "Relax your jaw and forehead"][stage]
        C.text(s, msg, "hint", WHITE, (540, 1660))
    return dict(name=name, dur=dur, draw=draw, cues=lambda d: [(k + .5, 330, .6, .05, 6) for k in range(0, int(d), 2)])

# ---------- posture ----------
def draw_seated(s, p, c, sb, col=WHITE, width=10):
    pel = (480, 1250)
    top = (lerp(560, 470, p), lerp(960, 920, p))
    mid = (lerp(420, 455, p), 1090)
    pts = []
    for k in range(21):
        t = k / 20
        pts.append(((1 - t) ** 2 * pel[0] + 2 * (1 - t) * t * mid[0] + t * t * top[0],
                    (1 - t) ** 2 * pel[1] + 2 * (1 - t) * t * mid[1] + t * t * top[1]))
    pygame.draw.lines(s, col, False, pts, width)
    sh = (top[0] + lerp(30, -5, sb), top[1] + 25)
    head = (top[0] + lerp(85, 5, c) * (1 if p > 0 else 1), top[1] - lerp(70, 95, c))
    pygame.draw.line(s, col, top, head, width)
    pygame.draw.circle(s, col, (int(head[0]), int(head[1] - 45)), 55, 7)
    elbow = (sh[0] + 30, sh[1] + 150)
    pygame.draw.line(s, col, sh, elbow, width); pygame.draw.line(s, col, elbow, (elbow[0] + 140, elbow[1] - 10), width)
    pygame.draw.line(s, col, pel, (680, 1262), width); pygame.draw.line(s, col, (680, 1262), (690, 1470), width)

def posture_step(name, dur, stage):
    def draw(s, u, d, C):
        pygame.draw.line(s, GUIDE, (400, 1290), (640, 1290), 8)
        pygame.draw.line(s, GUIDE, (400, 1290), (380, 900), 8)
        pygame.draw.line(s, GUIDE, (420, 1290), (420, 1480), 6); pygame.draw.line(s, GUIDE, (620, 1290), (620, 1480), 6)
        pygame.draw.line(s, GUIDE, (720, 1100), (1000, 1100), 8)
        k = ease(u / 2.5)
        p = k if stage == 0 else 1
        c = 0 if stage == 0 else (k if stage == 1 else 1)
        sb = 0 if stage < 2 else (k if stage == 2 else 1)
        if stage == 3:
            draw_seated(s, 0, 0, 0, col=GUIDE, width=6)
        draw_seated(s, p, c, sb)
        if stage == 3:
            n = int(d) - int(u)
            C.text(s, str(n), "mid", GOLD, (850, 760))
            C.text(s, "Breathe. Hold it.", "hint", WHITE, (540, 1640))
        else:
            C.text(s, ["Grow tall from the top of your head", "Slide your chin straight back",
                       "Squeeze shoulder blades, then drop"][stage], "hint", WHITE, (540, 1640))
    return dict(name=name, dur=dur, draw=draw,
                cues=lambda d: [(.1, 523, 1.2, .1, 4)] + ([(k + .3, 392, .4, .08, 9) for k in range(int(d))] if stage == 3 else []))

# ======================= the 10 reels =======================
def eye2_paths():
    w = 2 * math.pi / 2
    return [
        path_step("DIAGONAL \u2197", 5, lambda u, d: (CX + AX * math.sin(w * u), CY - AY * .8 * math.sin(w * u))),
        path_step("DIAGONAL \u2196", 5, lambda u, d: (CX - AX * math.sin(w * u), CY - AY * .8 * math.sin(w * u))),
        path_step("ZIGZAG", 6, lambda u, d: (CX + AX * math.sin(2 * math.pi * u / 1.25), CY + AY * math.sin(2 * math.pi * u / d))),
        path_step("SPIRAL", 6, lambda u, d: (CX + AX * .9 * math.sin(math.pi * u / d) * math.sin(2 * math.pi * u / 1.5),
                                            CY - AX * .9 * math.sin(math.pi * u / d) * math.cos(2 * math.pi * u / 1.5))),
        blink_step(4), far_step(5)]

SIGH = [("INHALE", 2, .75), ("+ ONE MORE SIP", 1, 1.0), ("LONG EXHALE", 6, 0.0)]
SLEEP = [("INHALE \u00b7 NOSE", 4, 1), ("HOLD", 7, 1), ("EXHALE \u00b7 MOUTH", 8, 0)]

REELS = {
    "eye2": dict(title="EYE RESET 2", hook=["Part 2.", "Your screen eyes", "asked for this"],
                 hint="Follow the gold dot \u2192", steps=eye2_paths(),
                 save="Do it every 20 min of screen time", share=["Send to someone who", "needs a screen break"]),
    "box": dict(title="BOX BREATHING", hook=["Stressed?", "Breathe with", "the square"],
                hint="Inhale as the dot climbs \u2191", steps=[box_step("ROUND 1"), box_step("ROUND 2")],
                save="Use it before any stressful moment", share=["Send to someone who", "needs to calm down"]),
    "sleep": dict(title="4-7-8 SLEEP", hook=["Can\u2019t sleep?", "Do this", "lying in bed"],
                  hint="Breathe with the circle", steps=[breath_step("ROUND 1", SLEEP), breath_step("ROUND 2", SLEEP)],
                  save="Do 4 rounds tonight in bed", share=["Send to someone who", "can\u2019t sleep"]),
    "sigh": dict(title="CALM IN 30s", hook=["The fastest way", "to calm down", "(30 seconds)"],
                 hint="Two inhales, one long exhale", steps=[breath_step(f"ROUND {i}", SIGH) for i in (1, 2, 3)],
                 save="Use it when stress hits", share=["Send to someone who", "overthinks everything"]),
    "focus": dict(title="FOCUS TEST", hook=["Can you keep your", "eyes on the dot", "for 20 seconds?"],
                  hint="Most people fail level 3",
                  steps=[focus_step("LEVEL 1", 6, 1, 0), focus_step("LEVEL 2", 7, 2, 6), focus_step("LEVEL 3", 7, 3, 13)],
                  end_big="DID YOU MAKE IT?", save="Comment YES or NO \u2193",
                  share=["Send to a friend who", "can\u2019t focus for 5 seconds"]),
    "neck": dict(title="NECK RESET", hook=["Your neck after", "a day at", "the desk"],
                 hint="Follow with your head, slowly",
                 steps=[neck_step("TURN LEFT \u2194 RIGHT", 8, "turn"), neck_step("LOOK UP \u2195 DOWN", 8, "nod"),
                        neck_step("EAR TO SHOULDER", 10, "tilt"), neck_step("SHOULDER ROLLS", 6, "roll")],
                 save="Do it every hour at your desk", share=["Send to someone who", "works at a desk all day"]),
    "unclench": dict(title="UNCLENCH", hook=["You\u2019re tense", "right now and", "don\u2019t know it"],
                     hint="Follow each step",
                     steps=[unclench_step("FOREHEAD", 4, "forehead"), unclench_step("JAW", 4, "jaw"),
                            unclench_step("SHOULDERS", 5, "shoulders"), unclench_step("HANDS", 4, "hands"),
                            unclench_step("BELLY", 6, "belly")],
                     save="Do it whenever you feel tight", share=["Send to someone", "who carries stress"]),
    "ground": dict(title="5-4-3-2-1", hook=["Overthinking?", "Do this", "right now"],
                   hint="Look around you",
                   steps=[ground_step(5, "see", 6), ground_step(4, "touch", 5), ground_step(3, "hear", 5),
                          ground_step(2, "smell", 4), ground_step(1, "taste", 3)],
                   save="Use it when your mind races", share=["Send to someone", "who overthinks"]),
    "soft": dict(title="SOFT FOCUS", hook=["Relax your eyes", "in 20 seconds"],
                 hint="Keep your eyes on the dot",
                 steps=[soft_step("EYES ON THE DOT", 5, 0), soft_step("WIDEN YOUR VIEW", 6, 1),
                        soft_step("SEE EVERYTHING", 6, 2), soft_step("SOFTEN", 6, 3)],
                 save="Do it after long screen sessions", share=["Send to someone with", "tired screen eyes"]),
    "posture": dict(title="POSTURE RESET", hook=["You\u2019re slouching", "right now"],
                    hint="Copy him \u2192",
                    steps=[posture_step("SIT TALL", 6, 0), posture_step("CHIN BACK", 6, 1),
                           posture_step("SHOULDERS BACK", 6, 2), posture_step("HOLD \u00b7 BREATHE", 5, 3)],
                    save="Check your posture every hour", share=["Send to someone who", "is slouching right now"]),
}

# ======================= timeline, audio, render =======================
def timeline(reel):
    t, out = HOOK_T, []
    for st in reel["steps"]:
        out.append((t, t + st["dur"], st)); t += st["dur"]
    return out, t, t + END_LEN

def build_audio(reel, path, sr=44100):
    tl, end_t, dur = timeline(reel)
    n = int(dur * sr); x = np.arange(n) / sr
    au = np.zeros(n + 2 * sr)
    pad = sum(np.sin(2 * np.pi * f * x) for f in (110, 165, 220, 277)) * .05
    au[:n] += pad * np.minimum(1, x / 2) * np.minimum(1, (dur - x) / 2) * (1 + .2 * np.sin(2 * np.pi * x / 6))
    def tone(t0, f, ln, v, k):
        m = int(ln * sr); xx = np.arange(m) / sr
        i = int(t0 * sr)
        if i >= len(au): return
        au[i:i + m] += (np.sin(2 * np.pi * f * xx) * np.exp(-xx * k) * v)[:len(au) - i]
    for a, b, st in tl:
        for j, f in enumerate((659, 880)): tone(a + .1 * j, f, 1.2, .14, 4)
        for (o, f, ln, v, k) in st.get("cues", lambda d: [])(st["dur"]):
            tone(a + o, f, ln, v, k)
    for j, f in enumerate((523, 659, 784, 1047)): tone(end_t + .08 * j, f, 2, .2, 2.5)
    au = au[:n] / np.abs(au[:n]).max() * .85
    with wave.open(path, "wb") as fh:
        fh.setnchannels(1); fh.setsampwidth(2); fh.setframerate(sr)
        fh.writeframes((au * 32767).astype(np.int16).tobytes())

def render(reel, C, fps):
    tl, end_t, dur = timeline(reel)
    title = C.spaced(reel["title"], "title", PEACH, 14)
    brand = C.spaced("SHIPSTACK", "brand", (150, 155, 168), 8)
    s = pygame.Surface((W, H))
    nseg = len(tl); seg_w = min(150, (900 - 14 * (nseg - 1)) / nseg)
    prev = None
    for fr in range(int(dur * fps)):
        t = fr / fps
        s.blit(C.bg, (0, 0))
        C.blit(s, brand, (540, 190)); C.blit(s, title, (540, 270))
        x0 = 540 - (nseg * (seg_w + 14) - 14) / 2
        for i, (a, b, st) in enumerate(tl):
            xx = x0 + i * (seg_w + 14)
            pygame.draw.rect(s, GUIDE, (xx, 350, seg_w, 8), border_radius=4)
            k = max(0, min(1, (t - a) / (b - a)))
            if k > 0: pygame.draw.rect(s, GOLD, (xx, 350, max(8, seg_w * k), 8), border_radius=4)
        cur = next((i for i, (a, b, _) in enumerate(tl) if a <= t < b), None)
        if cur != prev: C.state.clear(); prev = cur
        if t < HOOK_T:
            a = 255 * min(1, t * 4, (HOOK_T - t) * 4)
            for i, line in enumerate(reel["hook"]):
                C.text(s, line, "hook", GOLD if i == len(reel["hook"]) - 1 else WHITE, (540, 600 + i * 82), a)
            C.text(s, reel["hint"], "hint", GOLD, (540, 1420), a)
            C.add_glow(s, CX, CY + 120)
            pygame.draw.circle(s, GOLD, (CX, CY + 120), int(34 * (1 + .15 * math.sin(t * 6))))
        elif cur is not None:
            a, b, st = tl[cur]
            al = 255 * min(1, (t - a) * 4)
            C.text(s, f"{cur + 1}/{nseg}", "small", DIM, (540, 420), al)
            C.blit(s, C.spaced(st["name"], "step", WHITE, 6), (540, 475), al)
            st["draw"](s, t - a, b - a, C)
        else:
            k = ease((t - end_t) / .5)
            C.add_glow(s, 540, 760)
            if "end_big" not in reel:
                pts = [(-45, -70), (45, -70), (45, 70), (0, 35), (-45, 70)]
                pygame.draw.polygon(s, GOLD, [(540 + px, 760 + py * k) for px, py in pts])
                big = "SAVE THIS"
            else:
                pygame.draw.circle(s, GOLD, (540, 760), int(34 * k))
                big = reel["end_big"]
            C.blit(s, C.spaced(big, "title" if len(big) < 12 else "cta", GOLD, 10), (540, 950), 255 * k)
            C.text(s, reel["save"], "small", WHITE, (540, 1050), 255 * k)
            if t > end_t + .8:
                kk = 255 * ease((t - end_t - .8) / .4)
                for i, line in enumerate(reel["share"]):
                    C.text(s, line, "small", DIM, (540, 1250 + 50 * i), kk)
        yield t, s

def make(key, fps, preview):
    reel = REELS[key]; C = Ctx()
    _, end_t, dur = timeline(reel)
    wav, out = f"tmp_{key}.wav", f"reset_{key}.mp4"
    build_audio(reel, wav)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-i", wav, "-c:v", "libx264",
                           "-threads", "2", "-movflags", "+faststart", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac",
                           "-b:a", "160k", "-shortest", out], stdin=subprocess.PIPE)
    tl, _, _ = timeline(reel)
    marks = [1.3] + [(a + b) / 2 for a, b, _ in tl] + [end_t + 2]
    mframes = {int(m * fps) for m in marks}
    shots = []
    for fr, (t, surf) in enumerate(render(reel, C, fps)):
        ff.stdin.write(pygame.image.tobytes(surf, "RGB"))
        if preview and fr in mframes: shots.append(pygame.transform.smoothscale(surf, (216, 384)))
    ff.stdin.close()
    if ff.wait():
        raise RuntimeError("FFmpeg failed")
    os.remove(wav)
    if shots:
        sheet = pygame.Surface((226 * len(shots) + 10, 404)); sheet.fill((225, 228, 235))
        for k, sh in enumerate(shots): sheet.blit(sh, (10 + k * 226, 10))
        pygame.image.save(sheet, f"preview_{key}.png")
    print(f"saved {out} ({dur:.1f}s)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("reels", nargs="*", default=list(REELS))
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    for key in a.reels: make(key, a.fps, a.preview)
