"""Publish the reviewed Asia pilot using the repository's carousel journal."""
import json
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "news-pilot"))
import pilot
import campaign

class AsiaMeta(campaign.Meta):
    def ready(self, container):
        for delay in (20, 45, 90, None):
            try:
                return super().ready(container)
            except RuntimeError as error:
                if delay is None or str(error) not in (
                    f'Meta HTTP 403 on {container}', f'Meta HTTP 429 on {container}',
                ):
                    raise
                time.sleep(delay)

campaign.Meta = AsiaMeta

data = json.loads((ROOT / "edition.json").read_text())
key = data["id"]

def stage(_item, output):
    slides = sorted((ROOT / "slides").glob("*.jpg"))
    if len(slides) != 8:
        raise RuntimeError("Expected the cover and seven story slides")
    output.mkdir(parents=True, exist_ok=True)
    for slide in slides:
        shutil.copyfile(slide, output / f"{key}-{slide.name}")

pilot.DATE = data["date"]
pilot.TAG = "asia-desk-" + data["date"]
pilot.ROOT = ROOT
pilot.render = stage
pilot.publish({
    "id": key,
    "headline": "Asia in Seven Headlines | 15 November 2026",
    "deck": "Seven newspapers across Asia in one 24-hour briefing.",
    "slides": [["", "Story times are given in each publisher’s local time. Artwork is AI-generated editorial illustration."]],
    "sources": [s["url"] for s in data["stories"]],
})
