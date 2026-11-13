"""Render a close Balloon Pop race with a slow-motion finish."""
from bisect import bisect_right
from functools import lru_cache
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SCENE = 'pl-balloon-slow'
SEEDS = (14, 15, 22, 28, 30, 32, 43, 50, 51, 62)
POP_TIME = 12.4
SLOW_START = 10.6
SLOW_SPEED = 0.34
CENTERS = ((273, 484), (759, 484), (273, 879), (759, 879), (273, 1274), (759, 1274))
PALETTES = (
    ((255, 93, 132), (255, 183, 89), (250, 226, 113), (99, 238, 171), (98, 190, 255), (188, 147, 255)),
    ((241, 124, 255), (255, 121, 104), (255, 205, 106), (92, 226, 231), (136, 166, 255), (180, 239, 128)),
)
WHITE = (245, 249, 255)
MUTED = (161, 183, 206)


@lru_cache(maxsize=12)
def font(size):
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size)


def bounds(x, y, rx, ry=None):
    ry = rx if ry is None else ry
    return (x - rx, y - ry, x + rx, y + ry)


def blend(a, b, amount):
    return tuple(round(x + (y - x) * amount) for x, y in zip(a, b))


def backdrop():
    y, x = np.ogrid[-1:1:1920j, -1:1:1080j]
    halo = np.exp(-2.3 * (x * x + (y + .25) ** 2))
    pixels = np.stack([base + glow * halo for base, glow in ((6, 9), (11, 18), (22, 34))], axis=-1)
    image = Image.fromarray(pixels.astype(np.uint8))
    draw = ImageDraw.Draw(image)
    for y in range(285, 1530, 31):
        for x in range(48, 1040, 31):
            draw.ellipse(bounds(x, y, 1.5), fill=(27, 43, 67))
    draw.text((516, 167), 'PICK A BALLOON', font=font(79), fill=WHITE, anchor='mm')
    draw.text((516, 251), 'Which one pops first?', font=font(43), fill=MUTED, anchor='mm')
    return image


@lru_cache(maxsize=12)
def balloon_sprite(color):
    y, x = np.ogrid[-1:1:384j, -1:1:384j]
    distance = np.hypot(x, y)
    center = np.sqrt(np.maximum(0, 1 - distance ** 2))
    shine = np.exp(-((x + .40) ** 2 * 15 + (y + .47) ** 2 * 35))
    reflected = np.exp(-((x - .50) ** 2 * 10 + (y - .58) ** 2 * 17))
    rim = np.exp(-((distance - .965) * 21) ** 2)
    rgb = [
        14 + channel * (.24 + .19 * center + .14 * reflected + .48 * rim) + 123 * shine
        for channel in color
    ]
    alpha = np.clip((1 - distance) * 170, 0, 1) * 255
    return Image.fromarray(np.clip(np.stack([*rgb, alpha], axis=-1), 0, 255).astype(np.uint8))


class BalloonRace:
    def __init__(self, upstream, variant):
        if not 0 <= variant < len(SEEDS):
            raise ValueError('Unknown Balloon Pop variation')
        self.sim = upstream
        self.FPS = upstream.FPS
        self.SR = upstream.SR
        self.seed = SEEDS[variant]
        self.colors = PALETTES[variant % len(PALETTES)]
        frames, hits, self.winner, self.win = upstream.simulate(self.seed, 12.0)
        if self.winner is None:
            raise RuntimeError('Balloon Pop simulation has no winner')
        self.frames = np.asarray(frames)
        self.scale = .91
        self.hits = [[] for _ in CENTERS]
        for hit in hits:
            self.hits[hit[1]].append(hit)
        self.hit_times = [[hit[0] for hit in hits] for hits in self.hits]
        self.background = backdrop()
        self.slow_source = self.win - (POP_TIME - SLOW_START) * SLOW_SPEED
        rng = random.Random(self.seed)
        self.shards = [(math.tau * k / 28 + rng.uniform(-.12, .12),
                        rng.uniform(110, 250), rng.uniform(8, 24), rng.uniform(-8, 8))
                       for k in range(28)]

    def source_time(self, t):
        if t < SLOW_START:
            return t * self.slow_source / SLOW_START
        return min(self.win + .39, self.win + (t - POP_TIME) * SLOW_SPEED)

    def output_time(self, t):
        if t < self.slow_source:
            return t * SLOW_START / self.slow_source
        return POP_TIME + (t - self.win) / SLOW_SPEED

    def render(self, frame):
        t = frame / self.FPS
        source = self.source_time(t)
        popped = t >= POP_TIME
        pos = max(0, source * self.FPS - 1)
        index = int(pos)
        state = self.frames[index] + (self.frames[index + 1] - self.frames[index]) * (pos - index)
        image = self.background.copy()
        draw = ImageDraw.Draw(image)
        fade = min(.75, max(0, (t - POP_TIME) * 1.9))
        for k, ((cx, cy), (ball_x, ball_y, radius), accent) in enumerate(zip(CENTERS, state, self.colors)):
            dim = fade if k != self.winner else 0
            color = blend(accent, (56, 70, 89), dim)
            draw.rounded_rectangle((cx - 204, cy - 178, cx + 204, cy + 193), 36,
                                   fill=(10, 20, 34), outline=blend((42, 61, 88), accent, .28 * (1 - dim)), width=3)
            if popped and k == self.winner:
                self.burst(draw, cx, cy, color, t - POP_TIME)
                continue
            fraction = min(1, max(0, (radius - self.sim.R0) / (self.sim.RPOP - self.sim.R0)))
            hit_index = bisect_right(self.hit_times[k], source) - 1
            hit = self.hits[k][hit_index] if hit_index >= 0 else None
            age = source - hit[0] if hit else 1
            scale = self.scale
            r = radius * scale
            image_balloon = balloon_sprite(accent).resize((round(r * 2), round(r * 2)), Image.Resampling.BILINEAR)
            if dim:
                image_balloon.putalpha(image_balloon.getchannel('A').point(lambda value: round(value * (1 - dim))))
            draw.polygon(((cx, cy + r - 6), (cx - 10, cy + r + 10), (cx + 10, cy + r + 10)), fill=color)
            image.paste(image_balloon, (round(cx - r), round(cy - r)), image_balloon)
            draw.text((cx, cy), str(k + 1), font=font(105),
                      fill=blend((180, 196, 217), color, .47 + dim * .55),
                      stroke_width=2, stroke_fill=(19, 32, 51), anchor='mm')
            if hit and age < .1:
                direction = math.degrees(hit[3])
                draw.arc(bounds(cx, cy, r + 1), direction - 18, direction + 18,
                         fill=blend(color, WHITE, .93 * (1 - age * 8)), width=8)
            old_x, old_y = self.sim.CENT[k]
            x = cx + (ball_x - old_x) * scale
            y = cy + (ball_y - old_y) * scale
            draw.ellipse(bounds(x, y, self.sim.RB * scale), fill=blend((9, 19, 35), color, .18),
                         outline=blend(WHITE, color, dim), width=5)
            draw.ellipse(bounds(x - 5, y - 6, 4), fill=blend(WHITE, color, dim))
            draw.rounded_rectangle((cx - 121, cy + 168, cx + 63, cy + 176), 4, fill=(39, 58, 80))
            if fraction:
                draw.rounded_rectangle((cx - 121, cy + 168, cx - 121 + 184 * fraction, cy + 176), 4, fill=color)
            draw.text((cx + 138, cy + 172), f'{min(99, int(fraction * 100))}%', font=font(24),
                      fill=blend(WHITE, color, dim), anchor='rm')
        if popped:
            footer = f'BALLOON {self.winner + 1} POPPED FIRST'
            footer_color = self.colors[self.winner]
        elif t >= SLOW_START:
            footer = 'SLOW MOTION'
            footer_color = WHITE
        else:
            footer = 'Every hit makes it bigger'
            footer_color = MUTED
        draw.text((516, 1543), footer, font=font(42), fill=footer_color, anchor='mm')
        return np.asarray(image)

    def burst(self, draw, cx, cy, color, age):
        hit = self.hits[self.winner][-1]
        direction = hit[3]
        impact = (cx + math.cos(direction) * 146, cy + math.sin(direction) * 146)
        if age < .37:
            opacity = 1 - age / .37
            draw.ellipse(bounds(*impact, 15 + age * 140), outline=blend((10, 20, 34), WHITE, opacity),
                         width=max(1, round(8 * opacity)))
        if age < .91:
            for angle, speed, length, spin in self.shards:
                radius = 144 + speed * age
                x = cx + math.cos(angle) * radius
                y = cy + math.sin(angle) * radius + 145 * age ** 2
                if abs(x - cx) > 203 or abs(y - cy) > 178:
                    continue
                tilt = angle + spin * age
                dx, dy = length * math.cos(tilt), length * math.sin(tilt)
                shade = blend(color, WHITE, .4) if length > 18 else color
                draw.polygon(((x + dx, y + dy), (x - dy * .4, y + dx * .4),
                              (x - dx, y - dy), (x + dy * .4, y - dx * .4)),
                             fill=blend(shade, (10, 20, 34), age / .91))
        draw.text((cx, cy), 'POP!', font=font(103), fill=WHITE, stroke_width=4,
                  stroke_fill=blend((10, 20, 34), color, .45), anchor='mm')
        draw.text((cx, cy + 83), f'BALLOON {self.winner + 1}', font=font(31), fill=color, anchor='mm')

    def audio(self):
        mixer = self.sim.Mixer(15)
        mixer.beat(108, roots=(110, 130.81, 98, 146.83))
        mixer.mus *= .52
        last = -1.0
        for t, _, radius, _ in sorted(hit for hits in self.hits for hit in hits):
            output = self.output_time(t)
            if output - last < .065 or output >= POP_TIME - .055:
                continue
            tension = (radius - self.sim.R0) / (self.sim.RPOP - self.sim.R0)
            mixer.ping(output, 255 * 2 ** (1.35 * tension), .17)
            last = output
        mixer.whoosh(SLOW_START, POP_TIME - SLOW_START, .1, self.seed)
        mixer.pop(POP_TIME, 1.12)
        mixer.impact(POP_TIME, .65)
        mixer.chord(POP_TIME + .20, [440, 554.37, 659.25, 880], .075)
        return mixer.final()
