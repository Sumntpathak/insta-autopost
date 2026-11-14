"""Create the ShipStack Gold Vault color editions from the original Blender render."""
import colorsys
import json
import tempfile
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
THEMES = [
    ("JADE", 0, "80dbc6"),
    ("SAPPHIRE", 54, "9ebcff"),
    ("AMETHYST", 121, "d5aaff"),
    ("RUBY", 177, "ff9bb4"),
    ("COPPER", -149, "ffab86"),
    ("EMERALD", -63, "97ec9f"),
    ("GLACIER", 21, "a4e7ff"),
    ("ORCHID", 148, "f4afee"),
    ("LIME", -92, "d3ef9e"),
    ("BRONZE", -120, "f8ce8c"),
]
BATCH = "shipstack-gold-vault-2026-11-14"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def entry(index, name):
    return {
        "id": f"GOLD-VAULT-20261114-{index + 1:02}",
        "scene": "gold-vault",
        "variant": index,
        "seconds": 15,
        "caption": (
            f"Gold Vault · {name.title()} Edition\n"
            "Follow the gold ball through eleven swaps. Lock in your cup before the reveal.\n\n"
            "#ShipStack #GoldVault #CupChallenge"
        ),
    }

def write_lut(path, rotation):
    size = 33
    with path.open("w") as cube:
        cube.write(f"LUT_3D_SIZE {size}\n")
        for blue in range(size):
            for green in range(size):
                for red in range(size):
                    rgb = tuple(v / (size - 1) for v in (red, green, blue))
                    hue, saturation, value = colorsys.rgb_to_hsv(*rgb)
                    degrees = hue * 360
                    # Retain gold and neutrals, including the target and reveal.
                    weight = min(1, max(0, (degrees - 82) / 39),
                                 max(0, (300 - degrees) / 55),
                                 max(0, (saturation - .08) / .17))
                    rotated = (hue + rotation * weight / 360) % 1
                    color = colorsys.hsv_to_rgb(rotated, saturation, value)
                    cube.write(" ".join(f"{channel:.6f}" for channel in color) + "\n")


def render(index, output):
    name, rotation, accent = THEMES[index]
    item = entry(index, name)
    output.mkdir(parents=True, exist_ok=True)
    path = output / (item["id"] + ".mp4")
    # Rotate the teal/blue palette while keeping the gold target recognizable.
    filters = [
        "scale=1080:1920:flags=lanczos", "setsar=1",
        f"drawtext=fontfile={FONT}:text='{name} EDITION':"
        f"fontcolor=0x{accent}:fontsize=27:x=(w-tw)/2:y=128",
        f"drawtext=fontfile={FONT}:text='@shipstack_':fontcolor=white@0.85:"
        "fontsize=24:x=(w-tw)/2:y=83",
        "tpad=stop_mode=clone:stop_duration=3",
    ]
    with tempfile.TemporaryDirectory() as work:
        lut = Path(work) / "palette.cube"
        write_lut(lut, rotation)
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-threads", "2", "-filter_threads", "2", "-i", str(HERE / "source.mp4"),
            "-vf", ",".join([f"lut3d=file={lut}", *filters]), "-af", "apad", "-t", "15",
            "-c:v", "libx264", "-threads", "3", "-preset", "fast", "-crf", "19",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart", str(path),
        ], check=True)
    subprocess.run([sys.executable, str(HERE.parent / "verify.py"), str(path)], check=True)
    path.with_suffix(".mp4.json").write_text(json.dumps({
        key: item[key] for key in ("scene", "variant", "seconds")
    }))
    if index == 0:
        entries = [entry(i, theme[0]) for i, theme in enumerate(THEMES)]
        (output / "manifest.json").write_text(json.dumps({
            "batch_id": BATCH, "enabled": True, "count": len(entries), "items": entries,
        }, indent=2))

if __name__ == "__main__":
    render(int(sys.argv[1]), Path(sys.argv[2]))
