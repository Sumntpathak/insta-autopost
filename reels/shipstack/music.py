"""Background music per format. Tracks live in film/public/bgm (also used by the Remotion reels).

Provenance: audio supplied by the account owner; see film/public/bgm/README.md. Replace a file there to change a format's music.
"""
import subprocess
from pathlib import Path

BGM = Path(__file__).resolve().parents[2] / 'film' / 'public' / 'bgm'
# format -> (file, music volume). News uses the second track so it sounds different from the other formats.
MUSIC = {'automation': ('luminary.mp3', 0.5), 'dsa': ('luminary.mp3', 0.45), 'news': ('cod4.mp3', 0.4)}
TYPING_GAIN = 0.35        # automation reels: keyboard clicks sit under the music


def mix(video, fmt, seconds=15):
    """Mix the format's track under the existing audio of `video` (in place). Video stream is copied untouched."""
    name, vol = MUSIC[fmt]
    track = BGM / name
    out = Path(video).with_suffix('.music.mp4')
    graph = (f'[1:a]volume={vol},afade=t=in:d=0.5,afade=t=out:st={seconds - 1}:d=1,atrim=0:{seconds}[m];'
             f'[0:a][m]amix=inputs=2:duration=first:normalize=0[a]')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(video), '-stream_loop', '-1', '-i', str(track),
                    '-filter_complex', graph, '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-t', str(seconds), str(out)], check=True)
    out.replace(video)
