"""Episode badge for Arena reels, so consecutive covers on the grid never look like re-uploads.

The grid shows the centre 3:4 of a reel (y 240..1680 of 1920), which crops off the small 'Nº' line in
the Arena masthead. This burns a large '#12' pill next to the title, inside that area, for the whole
clip (the cover frame can be any moment). Audio, size, fps and frame count are unchanged.
"""
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import brand

BOX = (812, 262)          # top-left of the pill, right of the Arena title row
INK = brand.ACCENT        # Arena accent


def badge_png(episode, path):
    font = ImageFont.truetype(str(brand.FONTS / 'GeistMono-Variable.ttf'), 60)
    font.set_variation_by_axes([800])
    text = f'#{episode:02d}'
    l, t, r, b = ImageDraw.Draw(Image.new('RGBA', (1, 1))).textbbox((0, 0), text, font=font)
    w, h = (r - l) + 56, 92
    im = Image.new('RGBA', (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), radius=h, fill=INK)
    big = ImageFont.truetype(str(brand.FONTS / 'GeistMono-Variable.ttf'), 120)
    big.set_variation_by_axes([800])
    l, t, r, b = d.textbbox((0, 0), text, font=big)
    d.text(((w * 2 - (r - l)) / 2 - l, (h * 2 - (b - t)) / 2 - t), text, font=big, fill='white')
    im.resize((w, h), Image.Resampling.LANCZOS).save(path)
    return w


def apply(video, episode):
    """Burn the badge into `video` in place."""
    video = Path(video)
    with tempfile.TemporaryDirectory() as tmp:
        png, out = Path(tmp) / 'badge.png', Path(tmp) / 'out.mp4'
        w = badge_png(episode, png)
        x = min(BOX[0], 1080 - 64 - w)
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(video), '-i', str(png), '-filter_complex',
                        f'[0:v][1:v]overlay={x}:{BOX[1]}:format=auto,format=yuv420p[v]', '-map', '[v]', '-map', '0:a?',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-c:a', 'copy', '-movflags', '+faststart',
                        str(out)], check=True)
        out.replace(video)
    return video
