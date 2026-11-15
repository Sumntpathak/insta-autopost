"""Publish Reset Series reels through the campaign journal."""
import datetime as dt
import json
from pathlib import Path
import subprocess
import time
from urllib.error import HTTPError

import publish

class ResetMeta(publish.campaign.Meta):
    def call(self, path, data=None, method="GET"):
        try:
            return super().call(path, data, method)
        except RuntimeError as error:
            upstream = error.__context__
            if isinstance(upstream, HTTPError):
                try:
                    details = json.load(upstream).get("error", {})
                except (ValueError, OSError):
                    details = {}
                codes = {k: details[k] for k in ("code", "error_subcode")
                         if isinstance(details.get(k), int)}
                print(f"Meta response codes: {codes}", flush=True)
            raise

def resume(meta, item, state, record):
    container = record["container_id"]
    status = meta.call(container, {"fields": "status_code"}).get("status_code")
    print(f"{item['id']} container status: {status}", flush=True)
    if status == "PUBLISHED":
        posts = meta.call(f"{meta.ig_id}/media", {
            "fields": "id,caption,timestamp", "limit": 30
        }).get("data", [])
        attempted = dt.datetime.fromisoformat(record["attempted_at"])
        matches = [post for post in posts if post.get("caption") == item["caption"]
                   and dt.datetime.fromisoformat(post["timestamp"]) >= attempted - dt.timedelta(seconds=10)]
        if len(matches) != 1:
            raise RuntimeError(f"Could not match published reel {item['id']}")
        media_id = matches[0]["id"]
    elif status == "FINISHED":
        media_id = meta.call(f"{meta.ig_id}/media_publish", {"creation_id": container}, "POST")["id"]
    else:
        raise RuntimeError(f"Cannot resume {item['id']} with container status {status}")
    record.update(status="published", media_id=media_id,
                  published_at=dt.datetime.now(publish.campaign.IST).isoformat())
    publish.campaign.persist(state)
    print(f"INSTAGRAM_PUBLISHED {item['id']} {media_id}", flush=True)
    return record

def main():
    items = publish.items()
    meta = ResetMeta()
    username = meta.check_account()["username"]
    if username.lower() != "shipstack_":
        raise RuntimeError(f"Unexpected Instagram account @{username}")
    try:
        quota = meta.call(f"{meta.ig_id}/content_publishing_limit", {"fields": "quota_usage,config"})
    except RuntimeError:
        quota = {}
    for row in quota.get("data", []):
        print(f"Instagram publish usage: {row.get('quota_usage')} / {row.get('config', {}).get('quota_total')}", flush=True)
    tag = json.loads(publish.MANIFEST.read_text())["batch_id"]
    if subprocess.run(["gh", "release", "view", tag], capture_output=True).returncode:
        subprocess.run([
            "gh", "release", "create", tag, "--target", "main", "--latest=false",
            "--title", "ShipStack Reset Series", "--notes", "Ten supplied Reset Series reels.",
        ], check=True)
    for index, item in enumerate(items):
        state = publish.campaign.read_state()
        previous = state["posts"].get(item["id"], {})
        if previous.get("status") == "published":
            continue
        if previous.get("status") == "publishing":
            record = resume(meta, item, state, previous)
        else:
            record = publish.publish_one(item, Path("output") / (item["id"] + ".mp4"), meta)
        if record.get("status") != "published":
            raise RuntimeError(f"Publication needs reconciliation for {item['id']}")
        if index < len(items) - 1:
            time.sleep(40)
    print(f"RESET_SERIES_CONFIRMED {len(items)}/{len(items)}", flush=True)

if __name__ == "__main__":
    main()
