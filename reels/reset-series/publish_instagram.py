"""Publish Reset Series reels through the campaign journal."""
import json
from pathlib import Path
import subprocess
import time

import publish

def main():
    items = publish.items()
    meta = publish.campaign.Meta()
    username = meta.check_account()["username"]
    if username.lower() != "shipstack_":
        raise RuntimeError(f"Unexpected Instagram account @{username}")
    tag = json.loads(publish.MANIFEST.read_text())["batch_id"]
    if subprocess.run(["gh", "release", "view", tag], capture_output=True).returncode:
        subprocess.run([
            "gh", "release", "create", tag, "--target", "main", "--latest=false",
            "--title", "ShipStack Reset Series", "--notes", "Ten supplied Reset Series reels.",
        ], check=True)
    for index, item in enumerate(items):
        previous = publish.campaign.read_state()["posts"].get(item["id"], {})
        if previous.get("status") == "published":
            continue
        record = publish.publish_one(item, Path("output") / (item["id"] + ".mp4"), meta)
        if record.get("status") != "published":
            raise RuntimeError(f"Publication needs reconciliation for {item['id']}")
        if index < len(items) - 1:
            time.sleep(40)
    print(f"RESET_SERIES_CONFIRMED {len(items)}/{len(items)}", flush=True)

if __name__ == "__main__":
    main()
