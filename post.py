"""Publishes the next due carousel from schedule.json to Instagram (+ optional Facebook Page).

Twice-daily slots (IST): morning 08:30, evening 19:00. Each run posts at most ONE item:
the oldest scheduled slot that is due and not yet in posted.json. So if GitHub skips a
scheduled run, nothing is lost; the next run catches up.
"""
import json, os, sys, time, datetime, urllib.request, urllib.parse, urllib.error

TOKEN = os.environ["META_TOKEN"].strip()    # long-lived token, stored as a GitHub Actions secret
# "IG..." tokens come from Instagram Login and only work on graph.instagram.com;
# Facebook Login / Page tokens ("EAA...") use graph.facebook.com.
API = "https://graph.instagram.com/v23.0" if TOKEN.startswith("IG") else "https://graph.facebook.com/v23.0"
DRY_RUN = os.environ.get("DRY_RUN", "").lower() == "true"
IG_ID = os.environ["IG_USER_ID"]            # Instagram account id
PAGE_ID = os.environ.get("FB_PAGE_ID", "")  # optional: also post to Facebook Page (needs a Page token)
REPO = os.environ["GITHUB_REPOSITORY"]      # set automatically by GitHub
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/"

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
SLOT_TIME = {"morning": (8, 30), "evening": (19, 0)}


def call(path, data=None, method="POST"):
    data = dict(data or {}, access_token=TOKEN)
    q = urllib.parse.urlencode(data)
    url = f"{API}/{path}" + (f"?{q}" if method == "GET" else "")
    req = urllib.request.Request(url, data=None if method == "GET" else q.encode(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"API error on {path}: {e.read().decode()}")


def wait_ready(container_id):
    for _ in range(36):
        status = call(container_id, {"fields": "status_code"}, "GET").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            sys.exit(f"container {container_id} failed with status {status}")
        time.sleep(5)
    sys.exit(f"container {container_id} not ready after 3 minutes")


def post_instagram(urls, caption):
    kids = [call(f"{IG_ID}/media", {"image_url": u, "is_carousel_item": "true"})["id"] for u in urls]
    for kid in kids:
        wait_ready(kid)
    box = call(f"{IG_ID}/media", {"media_type": "CAROUSEL", "children": ",".join(kids), "caption": caption})["id"]
    wait_ready(box)
    return call(f"{IG_ID}/media_publish", {"creation_id": box})["id"]


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
    me = call("me", {"fields": "username,account_type"}, "GET")
    print(f"Token OK for @{me.get('username')} ({me.get('account_type')}) via {API}")
    bad = []
    for item in schedule:
        for p in item["images"]:
            req = urllib.request.Request(RAW + p, method="HEAD")
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    ok = r.status == 200
            except urllib.error.HTTPError:
                ok = False
            if not ok:
                bad.append(RAW + p)
    due = [i["id"] for i in schedule if slot_dt(i) <= now]
    print(f"{len(schedule)} scheduled posts, {sum(len(i['images']) for i in schedule)} images checked, {len(bad)} unreachable")
    print(f"next slots: " + ", ".join(f"{i['id']}@{i['date']} {i['slot']}" for i in schedule[:4]))
    print(f"already due now: {due[:10]}")
    if bad:
        sys.exit("unreachable images:\n" + "\n".join(bad[:20]))


def main():
    now = datetime.datetime.now(IST)
    schedule = sorted(load("schedule.json"), key=slot_dt)
    if DRY_RUN:
        return dry_run(schedule, now)
    posted = load("posted.json")
    done = {p["id"] for p in posted}
    force = os.environ.get("POST_ID", "").strip()
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
    rec = {"id": item["id"], "date": now.date().isoformat(), "slot": item.get("slot"),
           "posted_at": now.isoformat(timespec="minutes"), "instagram": post_instagram(urls, item["caption"])}
    posted.append(rec)
    save_posted(posted)  # record immediately so a later failure can never cause a double post
    if PAGE_ID:
        rec["facebook"] = post_facebook(urls, item["caption"])
        save_posted(posted)
    print("Posted", rec)
    behind = len(candidates) - 1
    if behind > 0 and not force:
        print(f"{behind} more due slot(s) waiting; they will go out on the next runs")


if __name__ == "__main__":
    main()
