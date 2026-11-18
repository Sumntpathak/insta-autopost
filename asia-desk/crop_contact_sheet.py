"""Crop a 4-column × 2-row Asia Desk contact sheet into eight portrait previews.

These are DESIGN PREVIEWS ONLY. Do not publish them as verified news.
Usage: python asia-desk/crop_contact_sheet.py contact-sheet.png
"""
from pathlib import Path
import argparse
from PIL import Image, ImageOps

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("contact_sheet", type=Path)
    parser.add_argument("--output", type=Path, default=Path("asia-desk/preview"))
    args = parser.parse_args()
    image = Image.open(args.contact_sheet).convert("RGB")
    width, height = image.size
    if width % 4 or height % 2:
        raise ValueError("Expected an exact 4x2 contact sheet")
    args.output.mkdir(parents=True, exist_ok=True)
    w, h = width // 4, height // 2
    for index in range(8):
        x, y = (index % 4) * w, (index // 4) * h
        tile = image.crop((x, y, x + w, y + h))
        tile = ImageOps.fit(tile, (1080, 1350), method=Image.Resampling.LANCZOS)
        path = args.output / f"slide_{index+1:02d}.jpg"
        tile.save(path, quality=92, optimize=True)
        print(path)

if __name__ == "__main__":
    main()
