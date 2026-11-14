"""Publish the Brain Break manifest to the existing ShipStack Instagram account."""
import json
from pathlib import Path
import subprocess
import time

import publish

class BrainBreakMeta(publish.campaign.Meta):
    def ready(self, container):
        # A status read is safe to retry. The actual publish stays journaled.
        for delay in (25, 50, None):
            try:
                return super().ready(container)
            except RuntimeError as error:
                if delay is None or str(error) not in (
                    f"Meta HTTP 403 on {container}", f"Meta HTTP 429 on {container}"
                ):
                    raise
                print(f"Retrying container status in {delay}s", flush=True)
                time.sleep(delay)

def main():
    entries = publish.items()
    meta = BrainBreakMeta()
    account = meta.check_account()["username"]
    print(f"Publishing to @{account}", flush=True)
    tag = json.loads(publish.MANIFEST.read_text())["batch_id"]
    if subprocess.run(["gh", "release", "view", tag], capture_output=True).returncode:
        subprocess.run([
            "gh", "release", "create", tag, "--target", "main", "--latest=false",
            "--title", "ShipStack Brain Break editions",
            "--notes", "Nine original visual puzzles for ShipStack.",
        ], check=True)

    for item in entries:
        recorded = publish.campaign.read_state()["posts"].get(item["id"], {})
        if recorded.get("status") == "published":
            continue
        record = publish.publish_one(item, Path("output") / (item["id"] + ".mp4"), meta)
        if record.get("status") != "published":
            raise RuntimeError(f"Publication must be reconciled for {item['id']}")
        if item != entries[-1]:
            time.sleep(35)

    records = publish.campaign.read_state()["posts"]
    confirmed = sum(records.get(item["id"], {}).get("status") == "published" for item in entries)
    print(f"BRAIN_BREAK_CONFIRMED {confirmed}/{len(entries)}", flush=True)
    if confirmed != len(entries):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
