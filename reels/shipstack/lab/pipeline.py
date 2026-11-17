"""Shared render pipeline for Lab reels: Manim video + SignalFlow audio -> verified MP4."""
import subprocess
import tempfile
from pathlib import Path

from . import style as S


def render(scene_cls, out, soundtrack, name, grid=False):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        S.setup(tmp, name)
        scene = scene_cls()
        scene.grid = grid
        scene.render()
        video = Path(scene.renderer.file_writer.movie_file_path)
        wav = Path(tmp) / 'audio.wav'
        soundtrack(wav)
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(video), '-i', str(wav),
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(S.FPS),
                        '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-frames:v', str(S.FPS * S.SECONDS),
                        '-t', str(S.SECONDS), '-movflags', '+faststart', str(out)], check=True)
    return out


class Clocked:
    """Mixin: play() that tracks elapsed time so every reel ends at exactly SECONDS."""
    spent = 0.0

    def timed(self, *anims, run_time, rate_func=None):
        kw = {'run_time': run_time}
        if rate_func is not None:
            kw['rate_func'] = rate_func
        self.play(*anims, **kw)
        self.spent += run_time

    def finish(self):
        if getattr(self, 'grid', False):
            from .layout import grid_overlay
            self.add(grid_overlay())
        self.wait(S.SECONDS - self.spent)
