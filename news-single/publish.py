"""Journaled single-image Instagram publisher for individually verified ShipStack news.
Requires a reviewed manifest and an already committed 1080x1350 JPG or PNG.
Never retries an ambiguous media_publish result automatically.
"""
import datetime as dt
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "news-single"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
TOKEN = os.environ.get("META_TOKEN", "").strip()
IG_ID = os.environ.get("IG_USER_ID", "").strip()
API = "https://graph.instagram.com/v23.0" if TOKEN.startswith("IG") else "https://graph.facebook.com/v23.0"
REPO = os.environ.get("GITHUB_REPOSITORY", "Sumntpathak/insta-autopost")
REF = os.environ.get("GITHUB_REF_NAME", "main")
JOURNAL = DIR / "journal.json"
MANIFEST = DIR / "sample.json"

def api(path, data=None, method="POST"):
    query = urllib.parse.urlencode(data or {})
    url = API + "/" + path + ("?" + query if method == "GET" and query else "")
    request = urllib.request.Request(url, data=None if method == "GET" else query.encode(),
        method=method, headers={"Authorization": "Bearer " + TOKEN})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            info = json.loads(error.read()).get("error", {})
            detail = str(info.get("message", ""))[:200].replace(TOKEN, "***")
        except Exception:
            detail = ""
        raise RuntimeError(f"Meta HTTP {error.code}: {detail}") from None

def save(records):
    JOURNAL.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")

def validate(item):
    today = dt.datetime.now(IST).date()
    assert item["id"].startswith("SHIPNEWS-"), "Invalid post id"
    assert dt.date.fromisoformat(item["date"]) == today, "Sample must be dated today (IST)"
    assert item.get("verified") is True, "Story requires explicit editorial verification"
    assert item.get("approved") is True, "Sample requires explicit approval"
    assert item["source_url"].startswith("https://"), "Original source URL required"
    assert len(item["headline"]) >= 15 and item["source"] and item["caption"], "Missing story fields"
    path = ROOT / item["image"]
    assert path.resolve().is_relative_to(DIR.resolve()), "Image must be in news-single/"
    assert path.is_file() and path.suffix.lower() in (".jpg", ".jpeg", ".png"), "Missing committed JPG/PNG"
    from PIL import Image
    with Image.open(path) as im:
        assert im.size == (1080, 1350), "Image must be 1080x1350"
    return path

def main():
    item = json.loads(MANIFEST.read_text())
    path = validate(item)
    records = json.loads(JOURNAL.read_text()) if JOURNAL.exists() else []
    if any(r["id"] == item["id"] for r in records):
        print("Already attempted/published; reconcile journal before any retry:", item["id"])
        return
    if os.environ.get("PUBLISH", "").lower() != "true":
        print("VALIDATED PREVIEW ONLY:", item["id"], path)
        return
    if not TOKEN or not IG_ID:
        raise RuntimeError("META_TOKEN and IG_USER_ID required")
    url = f"https://raw.githubusercontent.com/{REPO}/{REF}/{item['image']}"
    with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=30) as response:
        assert response.status == 200, "Public image URL unavailable"
    media = api(f"{IG_ID}/media", {"image_url": url, "caption": item["caption"]})["id"]
    for _ in range(36):
        state = api(media, {"fields": "status_code"}, "GET").get("status_code")
        if state == "FINISHED":
            break
        if state in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Meta media container {state}")
        time.sleep(5)
    else:
        raise RuntimeError("Image processing timeout; no publish attempted")
    rec = {"id": item["id"], "date": item["date"], "status": "publishing",
           "container_id": media, "source_url": item["source_url"],
           "attempted_at": dt.datetime.now(IST).isoformat()}
    records.append(rec)
    save(records)  # must persist this file even on a failed/uncertain publish
    try:
        rec["instagram_media_id"] = api(f"{IG_ID}/media_publish", {"creation_id": media})["id"]
    except Exception as error:
        rec["error"] = type(error).__name__
        save(records)
        raise RuntimeError("Publish outcome unconfirmed; reconcile container and account manually. Do not retry.") from None
    rec["status"] = "published"
    save(records)
    print("CONFIRMED Instagram media ID:", rec["instagram_media_id"])

if __name__ == "__main__":
    main()
