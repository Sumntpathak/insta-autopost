"""Daily Dispatcher & Automated Publisher for @shipstack_

Reads daily_schedule.json (assembled each morning) and handles
the hands-off publishing of all 25 posts throughout the day.

Runs either:
1. As a background daemon: python daily_publisher.py --daemon
2. On-demand or via Windows Task Scheduler every 30-35 mins: python daily_publisher.py
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

TOKEN = os.environ.get("META_TOKEN", "").strip()
IG_ID = os.environ.get("IG_USER_ID", "").strip()
API = "https://graph.instagram.com/v23.0" if TOKEN.startswith("IG") else "https://graph.facebook.com/v23.0"


def call_api(path, data=None, method="POST"):
    q = urllib.parse.urlencode(data or {})
    url = f"{API}/{path}" + (f"?{q}" if method == "GET" and q else "")
    req = urllib.request.Request(
        url,
        data=None if method == "GET" else q.encode(),
        method=method,
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.load(resp)


def wait_container_ready(container_id, max_attempts=36, delay_sec=5):
    for _ in range(max_attempts):
        status = call_api(container_id, {"fields": "status_code"}, "GET").get("status_code")
        if status == "FINISHED":
            return True
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Container {container_id} failed with status {status}")
        time.sleep(delay_sec)
    raise RuntimeError(f"Container {container_id} timed out waiting for ready status")


def publish_item(item, dry_run=False):
    print(f"\nPublishing slot {item['slot']} ({item['category'].upper()}): {item['id']}...")
    print(f"Title: {item['title']}")
    
    if dry_run:
        print("[DRY-RUN] Simulating publish. Item validated successfully.")
        return "dry_run_id_123"

    if not TOKEN or not IG_ID:
        raise RuntimeError("META_TOKEN or IG_USER_ID is missing in .env")

    # 1. Create Media Container
    if item["is_reel"]:
        payload = {
            "media_type": "REELS",
            "video_url": item["media_url"],
            "caption": item["caption"],
            "share_to_feed": "true"
        }
    else:
        payload = {
            "image_url": item["media_url"],
            "caption": item["caption"]
        }

    res_container = call_api(f"{IG_ID}/media", payload)
    container_id = res_container["id"]
    print(f"  Container created: {container_id}. Waiting for processing...")
    
    wait_container_ready(container_id)
    print(f"  Container ready. Publishing...")

    # 2. Publish Container
    res_pub = call_api(f"{IG_ID}/media_publish", {"creation_id": container_id})
    media_id = res_pub["id"]
    print(f"  [SUCCESS] Published live to Instagram as Media ID: {media_id}")
    return media_id


def process_queue(dry_run=False):
    queue_file = ROOT / "daily_schedule.json"
    if not queue_file.exists():
        print(f"No active queue found at {queue_file}. Run morning_pipeline.py first.")
        return 0

    schedule = json.loads(queue_file.read_text(encoding="utf-8"))
    now = dt.datetime.now(IST)
    
    due_items = []
    for item in schedule:
        if item.get("status") == "published":
            continue
        item_dt = dt.datetime.fromisoformat(item["scheduled_datetime"])
        if item_dt <= now:
            due_items.append(item)

    if not due_items:
        next_items = [i for i in schedule if i.get("status") != "published"]
        if next_items:
            print(f"Nothing due right now. Next slot: {next_items[0]['id']} at {next_items[0]['scheduled_time']} IST.")
        else:
            print("All 25 posts for today have been published!")
        return 0

    # Publish oldest due item
    target = due_items[0]
    try:
        media_id = publish_item(target, dry_run=dry_run)
        if not dry_run:
            target["status"] = "published"
            target["published_at"] = now.isoformat()
            target["instagram_media_id"] = media_id
            queue_file.write_text(json.dumps(schedule, indent=2), encoding="utf-8")
            
            # Append to posted.json
            posted_file = ROOT / "posted.json"
            posted = json.loads(posted_file.read_text(encoding="utf-8")) if posted_file.exists() else []
            posted.append({
                "id": target["id"],
                "category": target["category"],
                "date": target["date"],
                "slot_time": target["scheduled_time"],
                "posted_at": now.isoformat(),
                "instagram": media_id
            })
            posted_file.write_text(json.dumps(posted, indent=2), encoding="utf-8")
            print(f"[OK] Journal updated in posted.json and daily_schedule.json.")
        return 1
    except Exception as e:
        print(f"[ERROR] Failed publishing {target['id']}: {e}")
        return 0


def run_daemon(interval_sec=60, dry_run=False):
    print("=" * 60)
    print("ShipStack Daily Automated Publisher Daemon")
    print("Monitoring daily_schedule.json across active hours (09:30 - 23:30 IST)")
    print("Checking queue every 60 seconds. Press Ctrl+C to stop.")
    print("=" * 60)
    while True:
        try:
            process_queue(dry_run=dry_run)
            time.sleep(interval_sec)
        except KeyboardInterrupt:
            print("\nPublisher daemon stopped.")
            break
        except Exception as e:
            print(f"Unexpected error in publisher loop: {e}")
            time.sleep(30)


def main():
    parser = argparse.ArgumentParser(description="ShipStack Daily Automated Post Dispatcher")
    parser.add_argument("--dry-run", action="store_true", help="Simulate publish without Meta API calls")
    parser.add_argument("--daemon", action="store_true", help="Run continuously as background daemon")
    parser.add_argument("--interval", type=int, default=60, help="Daemon polling interval in seconds")
    args = parser.parse_args()

    if args.daemon:
        run_daemon(interval_sec=args.interval, dry_run=args.dry_run)
    else:
        process_queue(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
