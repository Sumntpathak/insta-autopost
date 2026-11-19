import datetime as dt, json, os, time, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
QUEUE=ROOT/"news-batch/queue.json"
JOURNAL=ROOT/"news-batch/journal.json"
TOKEN=os.environ["META_TOKEN"]; IG_ID=os.environ["IG_USER_ID"]
REPO=os.environ.get("GITHUB_REPOSITORY","Sumntpathak/insta-autopost"); REF=os.environ.get("GITHUB_REF_NAME","main")
def api(path,data=None,method="POST"):
    q=urllib.parse.urlencode(data or {})
    url="https://graph.facebook.com/v23.0/"+path+("?" + q if method=="GET" and q else "")
    req=urllib.request.Request(url,data=None if method=="GET" else q.encode(),method=method,headers={"Authorization":"Bearer "+TOKEN})
    with urllib.request.urlopen(req,timeout=60) as r: return json.load(r)
def main():
    q=json.loads(QUEUE.read_text()); journal=json.loads(JOURNAL.read_text()) if JOURNAL.exists() else []
    for item in q["items"]:
        if not(item["verified"] and item["approved"]): continue
        if any(x["id"]==item["id"] for x in journal): continue
        p=ROOT/item["image"]
        assert p.is_file() and p.suffix.lower()==".jpg"
        with Image.open(p) as im: assert im.size==(1080,1350)
        url=f"https://raw.githubusercontent.com/{REPO}/{REF}/{item['image']}"
        media=api(f"{IG_ID}/media",{"image_url":url,"caption":item["hook"]+"\\n\\nSource and context in the caption.\\n\\n#ShipStack #News"})["id"]
        for _ in range(36):
            s=api(media,{"fields":"status_code"},"GET").get("status_code")
            if s=="FINISHED": break
            if s in ("ERROR","EXPIRED"): raise RuntimeError(f"{item['id']}: {s}")
            time.sleep(5)
        published=api(f"{IG_ID}/media_publish",{"creation_id":media})["id"]
        journal.append({"id":item["id"],"media_id":published,"published_at":dt.datetime.now(dt.timezone.utc).isoformat()})
        JOURNAL.write_text(json.dumps(journal,indent=2)+"\\n")
        time.sleep(q["pause_seconds"])
if __name__=="__main__": main()
