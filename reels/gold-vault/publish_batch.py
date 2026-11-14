"""Publish the Gold Vault manifest to the existing ShipStack Instagram account."""
import json
from pathlib import Path
import subprocess
import time

import publish

def main():
    entries = publish.items()
    meta = publish.campaign.Meta()
    account = meta.check_account()["username"]
    print(f"Publishing to @{account}", flush=True)
    tag = json.loads(publish.MANIFEST.read_text())["batch_id"]
    if subprocess.run(["gh", "release", "view", tag], capture_output=True).returncode:
        subprocess.run([
            "gh", "release", "create", tag, "--target", "main", "--latest=false",
            "--title", "ShipStack Gold Vault editions",
            "--notes", "Ten color editions of the original Gold Vault Blender animation.",
        ], check=True)

    for item in entries:
        recorded = publish.campaign.read_state()["posts"].get(item["id"], {})
        if recorded.get("status") == "published":
            continue
        record = publish.publish_one(item, Path("output") / (item["id"] + ".mp4"), meta)
        if record.get("status") != "published":
            raise RuntimeError(f"Publication must be reconciled for {item['id']}")
        if item != entries[-1]:
            time.sleep(20)

    records = publish.campaign.read_state()["posts"]
    confirmed = sum(records.get(item["id"], {}).get("status") == "published" for item in entries)
    print(f"GOLD_VAULT_CONFIRMED {confirmed}/{len(entries)}", flush=True)
    if confirmed != len(entries):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
