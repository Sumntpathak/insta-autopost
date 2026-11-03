"""Posts today's carousel (from schedule.json) to Instagram + Facebook Page via the Graph API."""
import json, os, sys, time, datetime, urllib.request, urllib.parse

TOKEN = os.environ["META_TOKEN"].strip()    # long-lived token, stored as a GitHub Actions secret
# "IG..." tokens come from Instagram Login and only work on graph.instagram.com;
# Facebook Login / Page tokens ("EAA...") use graph.facebook.com.
API = "https://graph.instagram.com/v23.0" if TOKEN.startswith("IG") else "https://graph.facebook.com/v23.0"
DRY_RUN = os.environ.get("DRY_RUN", "").lower() == "true"
IG_ID = os.environ["IG_USER_ID"]            # Instagram business account id
PAGE_ID = os.environ.get("FB_PAGE_ID", "")  # optional: also post to Facebook Page
REPO = os.environ["GITHUB_REPOSITORY"]      # set automatically by GitHub
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/"

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

def post_instagram(urls, caption):
    kids = [call(f"{IG_ID}/media", {"image_url": u, "is_carousel_item": "true"})["id"] for u in urls]
    box = call(f"{IG_ID}/media", {"media_type": "CAROUSEL", "children": ",".join(kids), "caption": caption})["id"]
    for _ in range(30):
        if call(box, {"fields": "status_code"}, "GET").get("status_code") == "FINISHED":
            break
        time.sleep(5)
    return call(f"{IG_ID}/media_publish", {"creation_id": box})["id"]

def post_facebook(urls, caption):
    ids = [call(f"{PAGE_ID}/photos", {"url": u, "published": "false"})["id"] for u in urls]
    data = {"message": caption}
    for i, pid in enumerate(ids):
        data[f"attached_media[{i}]"] = json.dumps({"media_fbid": pid})
    return call(f"{PAGE_ID}/feed", data)["id"]

def dry_run(today):
    """Verify the token and every scheduled image URL without publishing anything."""
    me = call("me", {"fields": "username,account_type"}, "GET")
    print(f"Token OK for @{me.get('username')} ({me.get('account_type')}) via {API}")
    for item in json.load(open("schedule.json")):
        for p in item["images"]:
            req = urllib.request.Request(RAW + p, method="HEAD")
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    status = r.status
            except urllib.error.HTTPError as e:
                status = e.code
            if status != 200:
                sys.exit(f"Image not reachable ({status}): {RAW + p}")
        print(f"{item['id']} {item['date']}{' (today)' if item['date'] == today else ''}: {len(item['images'])} images reachable")

def main():
    today = (datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)).date().isoformat()  # IST
    if DRY_RUN:
        return dry_run(today)
    force = os.environ.get("POST_ID", "").strip()
    posted = json.load(open("posted.json"))
    done = {p["id"] for p in posted}
    for item in json.load(open("schedule.json")):
        if (force and item["id"] != force) or (not force and item["date"] != today):
            continue
        if item["id"] in done:
            print(f"{item['id']} already posted, skipping"); continue
        urls = [RAW + p for p in item["images"]]
        rec = {"id": item["id"], "date": today, "instagram": post_instagram(urls, item["caption"])}
        if PAGE_ID:
            rec["facebook"] = post_facebook(urls, item["caption"])
        posted.append(rec); print("Posted", rec)
    json.dump(posted, open("posted.json", "w"), indent=2)

if __name__ == "__main__":
    main()
