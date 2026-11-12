"""Reject bad exports before making a publishing request."""
import json
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
    assert Fraction(video['avg_frame_rate']) == 30, 'Expected 30 FPS'
    assert int(video['nb_frames']) == 450, 'Expected 450 frames'
    assert any(s['codec_type'] == 'audio' and s['codec_name'] == 'aac' for s in info['streams']), 'Expected AAC audio track'
    print('Verified: 1080x1920, H.264/AAC, 15 seconds, 450 frames')


if __name__ == '__main__':
    verify(sys.argv[1])
