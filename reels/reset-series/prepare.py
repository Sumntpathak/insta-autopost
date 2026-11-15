"""Render and validate the supplied Reset Series clips."""
import json
import os
from pathlib import Path
import subprocess
import sys

from reset_series import REELS, make, timeline

CAPTIONS = {
    "focus": "Can you track the gold dot through all three levels?",
    "eye2": "Follow the gold dot through diagonals, a zigzag and a spiral.",
    "box": "Follow the square through two rounds of box breathing.",
    "sleep": "Follow the circle through two rounds of 4-7-8 breathing.",
    "sigh": "Two inhales and a long exhale. Follow the circle for three rounds.",
    "neck": "Take a desk break with four gentle movements.",
    "unclench": "Take a moment to relax your jaw, shoulders and hands.",
    "ground": "Pause and notice five things you can see, then work down through your senses.",
    "soft": "Keep your eyes on the dot and notice the edges of the screen.",
    "posture": "Take a seated break and follow four posture cues.",
}

def entry(key):
    keys = list(CAPTIONS)
    _, _, seconds = timeline(REELS[key])
    return {
        "id": f"RESET-20261115-{keys.index(key)+1:02d}",
        "scene": key,
        "variant": 0,
        "seconds": seconds,
        "caption": CAPTIONS[key] + "\n\nSave this for your next break.\n\n#ShipStack #ResetSeries",
    }

def render(key):
    item = entry(key)
    make(key, 30, False)
    clip = Path(f"reset_{key}.mp4")
    info = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(clip)
    ]))
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    audio = next(s for s in info["streams"] if s["codec_type"] == "audio")
    if (video["width"], video["height"], video["codec_name"], video["avg_frame_rate"],
            audio["codec_name"]) != (1080, 1920, "h264", "30/1", "aac"):
        raise RuntimeError(f"Invalid video or audio profile for {key}")
    if abs(float(info["format"]["duration"]) - item["seconds"]) > 0.15:
        raise RuntimeError(f"Unexpected duration for {key}")
    clip.rename(item["id"] + ".mp4")
    Path(item["id"] + ".mp4.json").write_text(json.dumps({
        k: item[k] for k in ("scene", "variant", "seconds")
    }))
    if key == next(iter(CAPTIONS)):
        Path("manifest.json").write_text(json.dumps({
            "batch_id": "shipstack-reset-2026-11-15",
            "enabled": True,
            "count": len(CAPTIONS),
            "items": [entry(k) for k in CAPTIONS],
        }, indent=2))

if __name__ == "__main__":
    out = Path("output")
    out.mkdir(exist_ok=True)
    os.chdir(out)
    for key in sys.argv[1:] or CAPTIONS:
        render(key)
