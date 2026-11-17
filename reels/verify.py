"""Reject bad exports before making a publishing request."""
import json
import re
import subprocess
import sys
from fractions import Fraction


def verify(path):
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                                               '-show_format', '-of', 'json', path]))
    video = next(s for s in info['streams'] if s['codec_type'] == 'video')
    assert video['codec_name'] == 'h264', 'Expected H.264'
    assert video['width'] == 1080 and video['height'] == 1920, 'Expected 1080x1920'
    assert abs(float(info['format']['duration']) - 15) < 0.1, 'Expected 15 seconds'
    fps = Fraction(video['avg_frame_rate'])
    assert fps in (30, 60), 'Expected 30 or 60 FPS'
    assert int(video['nb_frames']) == 15 * fps, f'Expected {15 * fps} frames'
    assert any(s['codec_type'] == 'audio' and s['codec_name'] == 'aac' for s in info['streams']), 'Expected AAC audio track'
    audio = subprocess.run(['ffmpeg', '-v', 'info', '-i', str(path), '-vn', '-af', 'volumedetect', '-f', 'null', '-'], capture_output=True, text=True, check=True)
    match = re.search(r'mean_volume: (-?[0-9.]+) dB', audio.stderr)
    assert match and float(match.group(1)) > -40, 'Audio must contain audible music, not silence'
    print(f'Verified: 1080x1920, H.264/AAC, 15 seconds, {15 * fps} frames at {fps} fps, audible music')


if __name__ == '__main__':
    verify(sys.argv[1])
