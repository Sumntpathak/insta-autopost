"""Publish the dated Asia Desk edition through the shared carousel publisher."""
import datetime as dt
import json
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path[:0] = [str(REPO / "news-pilot"), str(REPO / "reels")]
import pilot
import campaign

class AsiaMeta(campaign.Meta):
    def ready(self, container):
        for delay in (20, 45, 90, None):
            try:
                return super().ready(container)
            except RuntimeError as error:
                if delay is None or str(error) not in (
                    f"Meta HTTP 403 on {container}", f"Meta HTTP 429 on {container}"
                ):
                    raise
                time.sleep(delay)

def stage(_item, output):
    slides = sorted((ROOT / "slides").glob("*.jpg"))
    if len(slides) != 8:
        raise RuntimeError("Expected cover and seven verified stories")
    output.mkdir(parents=True, exist_ok=True)
    for slide in slides:
        shutil.copyfile(slide, output / f"{data['id']}-{slide.name}")

def main():
    key = data["id"]
    if dt.datetime.now(campaign.IST).date().isoformat() != data["date"]:
        raise RuntimeError("The edition date is stale")
    campaign.Meta = AsiaMeta
    pilot.DATE = data["date"]
    pilot.TAG = "asia-desk-" + data["date"]
    pilot.ROOT = ROOT
    pilot.render = stage
    state = campaign.read_state()
    record = state["posts"].get(key, {})
    meta = AsiaMeta()
    if meta.check_account()["username"].lower() != "shipstack_":
        raise RuntimeError("Unexpected Instagram account")
    title = "Asia in Seven Headlines | 20 November 2026"
    if record.get("status") == "published":
        print(f"ASIA_CONFIRMED {key} {record['media_id']}", flush=True)
        return
    recent = meta.call(f"{meta.ig_id}/media", {
        "fields": "id,caption,timestamp,permalink", "limit": 100
    }).get("data", [])
    matches = [post for post in recent if post.get("caption", "").startswith(title)]
    if len(matches) > 1:
        raise RuntimeError("Multiple matching editions require reconciliation")
    if matches:
        post = matches[0]
        state["posts"][key] = dict(record, id=key, date=data["date"], scene="asia-desk",
            status="published", media_id=post["id"], permalink=post.get("permalink"),
            published_at=post["timestamp"], caption=post.get("caption"))
        campaign.persist(state)
        print(f"ASIA_CONFIRMED {key} {post['id']}", flush=True)
        return
    if record:
        container = record["container_id"]
        status = meta.call(container, {"fields": "status_code"}).get("status_code")
        if status != "FINISHED":
            raise RuntimeError(f"Existing parent requires reconciliation: {status}")
        media = meta.call(f"{meta.ig_id}/media_publish", {"creation_id": container}, "POST")["id"]
        record.update(status="published", media_id=media,
                      published_at=dt.datetime.now(campaign.IST).isoformat())
        campaign.persist(state)
    else:
        pilot.publish({
            "id": key, "headline": title,
            "deck": "Space, diplomacy, science and politics across seven newspapers.",
            "slides": [["", "Times are local to each publisher. AI editorial illustrations."]],
            "sources": [story["url"] for story in data["stories"]],
        })
    record = campaign.read_state()["posts"].get(key, {})
    if record.get("status") != "published" or not record.get("media_id"):
        raise RuntimeError("Publication is unconfirmed")
    details = meta.call(record["media_id"], {"fields": "id,permalink"})
    print(f"ASIA_CONFIRMED {key} {details['id']} {details.get('permalink', '')}", flush=True)

data = json.loads((ROOT / "edition.json").read_text())
if __name__ == "__main__":
    main()
