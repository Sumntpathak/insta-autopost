"""Publishes the next due carousel from schedule.json to Instagram (+ optional Facebook Page).

Twice-daily slots (IST): morning 08:30, evening 19:00. Each run posts at most ONE item:
the oldest scheduled slot that is due and not yet in posted.json. So if GitHub skips a
scheduled run, nothing is lost; the next run catches up.
"""
import json, os, sys, time, datetime, urllib.request, urllib.parse, urllib.error
from pathlib import Path

# Automatically load local .env if available
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

# Default repository attributes if not set in environment
os.environ.setdefault("GITHUB_REPOSITORY", "Sumntpathak/insta-autopost")
os.environ.setdefault("GITHUB_REF_NAME", "main")

TOKEN = os.environ.get("META_TOKEN", "").strip()    # long-lived token, stored in .env or GitHub Actions secret
if not TOKEN:
    sys.exit("Error: META_TOKEN environment variable is not set. Please set it in .env file.")
# "IG..." tokens come from Instagram Login and only work on graph.instagram.com;
# Facebook Login / Page tokens ("EAA...") use graph.facebook.com.
API = "https://graph.instagram.com/v23.0" if TOKEN.startswith("IG") else "https://graph.facebook.com/v23.0"
DRY_RUN = os.environ.get("DRY_RUN", "").lower() == "true"
IG_ID = os.environ.get("IG_USER_ID", "").strip()            # Instagram account id
if not IG_ID:
    sys.exit("Error: IG_USER_ID environment variable is not set. Please set it in .env file.")
PAGE_ID = os.environ.get("FB_PAGE_ID", "")  # optional: also post to Facebook Page (needs a Page token)
REPO = os.environ["GITHUB_REPOSITORY"]      # set automatically by GitHub or defaulted above
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/"

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
SLOT_TIME = {"morning": (8, 30), "evening": (19, 0)}


class APIError(Exception):
    """Meta answered with an HTTP error: the request definitely did not succeed."""


def call(path, data=None, method="POST"):
    # The token travels in a header, never in a URL that proxies or logs could keep.
    q = urllib.parse.urlencode(data or {})
    url = f"{API}/{path}" + (f"?{q}" if method == "GET" and q else "")
    req = urllib.request.Request(url, data=None if method == "GET" else q.encode(), method=method,
                                 headers={"Authorization": f"Bearer {TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        # Keep Meta's error code/message for debugging, but never echo the raw body.
        try:
            err = json.loads(e.read().decode()).get("error", {})
        except ValueError:
            err = {}
        detail = f"{err.get('type', '')} {err.get('code', '')}: {err.get('message', '')}".replace(TOKEN, "***")
        raise APIError(f"Meta HTTP {e.code} on {path}: {detail.strip()}") from None


def wait_ready(container_id):
    for _ in range(36):
        status = call(container_id, {"fields": "status_code"}, "GET").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise APIError(f"container {container_id} failed with status {status}")
        time.sleep(5)
    raise APIError(f"container {container_id} not ready after 3 minutes")


def prepare_instagram(urls, caption):
    """Upload and process the carousel. Nothing is visible on the account yet."""
    kids = [call(f"{IG_ID}/media", {"image_url": u, "is_carousel_item": "true"})["id"] for u in urls]
    for kid in kids:
        wait_ready(kid)
    box = call(f"{IG_ID}/media", {"media_type": "CAROUSEL", "children": ",".join(kids), "caption": caption})["id"]
    wait_ready(box)
    return box


def post_facebook(urls, caption):
    ids = [call(f"{PAGE_ID}/photos", {"url": u, "published": "false"})["id"] for u in urls]
    data = {"message": caption}
    for i, pid in enumerate(ids):
        data[f"attached_media[{i}]"] = json.dumps({"media_fbid": pid})
    return call(f"{PAGE_ID}/feed", data)["id"]


def slot_dt(item):
    h, m = SLOT_TIME[item.get("slot", "evening")]
    d = datetime.date.fromisoformat(item["date"])
    return datetime.datetime(d.year, d.month, d.day, h, m, tzinfo=IST)


def load(name):
    with open(name, encoding="utf-8") as f:
        return json.load(f)


def save_posted(posted):
    with open("posted.json", "w", encoding="utf-8") as f:
        json.dump(posted, f, indent=2)


def dry_run(schedule, now):
    fields = "username,account_type" if TOKEN.startswith("IG") else "id,name"
    me = call("me", {"fields": fields}, "GET")
    name_str = me.get("username") or me.get("name")
    print(f"Token OK for {name_str} via {API}")
    bad = []
    for item in schedule:
        for p in item["images"]:
            req = urllib.request.Request(RAW + p, method="HEAD")
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    ok = r.status == 200
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
                ok = False
            if not ok:
                bad.append(RAW + p)
    due = [i["id"] for i in schedule if slot_dt(i) <= now]
    print(f"{len(schedule)} scheduled posts, {sum(len(i['images']) for i in schedule)} images checked, {len(bad)} unreachable")
    print(f"next slots: " + ", ".join(f"{i['id']}@{i['date']} {i['slot']}" for i in schedule[:4]))
    print(f"already due now: {due[:10]}")
    if bad:
        sys.exit("unreachable images:\n" + "\n".join(bad[:20]))


def publish(item, urls, posted, now):
    """Journal before the irreversible call, so an ambiguous failure can never re-post.

    - Upload/processing errors happen before anything is public: nothing is recorded, the
      next run retries.
    - media_publish is journalled first as "publishing" with its container id. A definite
      HTTP error removes the entry (safe to retry); a timeout or dropped connection keeps it,
      so the slot is skipped until someone reconciles the container by hand.
    """
    try:
        box = prepare_instagram(urls, item["caption"])
    except APIError as e:
        sys.exit(f"{item['id']}: not published, will retry next run ({e})")
    rec = {"id": item["id"], "date": now.date().isoformat(), "slot": item.get("slot"),
           "posted_at": now.isoformat(timespec="minutes"), "status": "publishing", "container_id": box}
    posted.append(rec)
    save_posted(posted)
    try:
        rec["instagram"] = call(f"{IG_ID}/media_publish", {"creation_id": box})["id"]
    except APIError as e:
        posted.remove(rec)
        save_posted(posted)
        sys.exit(f"{item['id']}: Meta rejected publish, will retry next run ({e})")
    except Exception as e:  # timeout / connection reset: the post may be live
        sys.exit(f"{item['id']}: publish outcome unknown ({type(e).__name__}); "
                 f"kept as 'publishing' with container {box}. Check the account before clearing it.")
    rec["status"] = "published"
    save_posted(posted)
    if PAGE_ID:
        try:
            rec["facebook"] = post_facebook(urls, item["caption"])
        except APIError as e:
            rec["facebook_error"] = str(e)  # visible in posted.json for a manual retry
        save_posted(posted)
    print("Posted", rec)
    return rec


def main():
    from team.active import active as team_active
    if team_active():
        print('Global ShipStack team owns publishing during the pilot.'); return
    now = datetime.datetime.now(IST)
    schedule = sorted(load("schedule.json"), key=slot_dt)
    if DRY_RUN:
        return dry_run(schedule, now)
    posted = load("posted.json")
    done = {p["id"] for p in posted}
    force = os.environ.get("POST_ID", "").strip()
    if force in done:
        print(f"{force} already posted, skipping"); return
    if force:
        candidates = [i for i in schedule if i["id"] == force]
        if not candidates:
            sys.exit(f"{force} is not in schedule.json")
    else:
        candidates = [i for i in schedule if slot_dt(i) <= now and i["id"] not in done]
    if not candidates:
        print("Nothing due right now."); return
    item = candidates[0]
    if item["id"] in done:
        print(f"{item['id']} already posted, skipping"); return
    urls = [RAW + p for p in item["images"]]
    publish(item, urls, posted, now)
    behind = len(candidates) - 1
    if behind > 0 and not force:
        print(f"{behind} more due slot(s) waiting; they will go out on the next runs")


if __name__ == "__main__":
    try:
        main()
    except APIError as e:
        sys.exit(str(e))
