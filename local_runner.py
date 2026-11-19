"""Local Workflow Runner for @shipstack_ autopost

Replicates all GitHub Actions workflows locally:
- Carousel Autopost (daily-post.yml: 08:37 & 19:07 IST)
- Reel Calendar Autopost (shipstack-schedule.yml: every 30 min)
- Manual Reel Rendering & Publishing (shipstack-reel.yml)
- Asia Desk Publication (asia-desk.yml)
- Account & Token Verification (status / check)
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# Ensure defaults
os.environ.setdefault("GITHUB_REPOSITORY", "Sumntpathak/insta-autopost")
os.environ.setdefault("GITHUB_REF_NAME", "main")

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def get_token():
    token = os.environ.get("META_TOKEN", "").strip()
    if not token:
        print("ERROR: META_TOKEN is not set in .env or environment.", file=sys.stderr)
        print("Please edit .env and set your META_TOKEN.", file=sys.stderr)
        sys.exit(1)
    return token


def get_ig_id():
    ig_id = os.environ.get("IG_USER_ID", "").strip()
    if not ig_id:
        print("ERROR: IG_USER_ID is not set in .env or environment.", file=sys.stderr)
        print("Please edit .env and set your IG_USER_ID.", file=sys.stderr)
        sys.exit(1)
    return ig_id


def get_api_url(token):
    return "https://graph.instagram.com/v23.0" if token.startswith("IG") else "https://graph.facebook.com/v23.0"


def check_status():
    print("=" * 60)
    print("ShipStack Local Autopost - Status & Verification")
    print("=" * 60)
    
    token = os.environ.get("META_TOKEN", "").strip()
    ig_id = os.environ.get("IG_USER_ID", "").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "Sumntpathak/insta-autopost")
    
    print(f"Repository:        {repo}")
    print(f"Working Directory: {ROOT}")
    print(f"Local IST Time:    {dt.datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"META_TOKEN:        {'[CONFIGURED]' if token else '[MISSING in .env]'}")
    print(f"IG_USER_ID:        {ig_id if ig_id else '[MISSING in .env]'}")
    print(f"FB_PAGE_ID:        {os.environ.get('FB_PAGE_ID', '[NOT SET / OPTIONAL]')}")
    
    if not token or not ig_id:
        print("\n[!] Please fill in your META_TOKEN and IG_USER_ID in .env before running posting commands.")
        return False
    
    api = get_api_url(token)
    print(f"\nChecking Meta Graph API connectivity ({api})...")
    fields = "id,username,account_type" if token.startswith("IG") else "id,name"
    req = urllib.request.Request(
        f"{api}/me?fields={fields}",
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
            name_val = data.get('username') or data.get('name')
            print(f"[OK] Token valid for {name_val} (ID: {data.get('id')})")
    except urllib.error.HTTPError as e:
        print(f"[FAIL] Meta API returned HTTP {e.code}: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"[FAIL] Connection error: {e}")
        return False

    # Check token scopes/permissions if Facebook token
    if not token.startswith("IG"):
        try:
            req_perm = urllib.request.Request(
                f"{api}/me/permissions",
                headers={"Authorization": f"Bearer {token}"}
            )
            with urllib.request.urlopen(req_perm, timeout=15) as resp:
                perm_data = json.load(resp)
                granted = [p["permission"] for p in perm_data.get("data", []) if p.get("status") == "granted"]
                print(f"     Granted Permissions: {', '.join(granted)}")
                ig_needed = {"instagram_basic", "instagram_content_publish"}
                missing = ig_needed - set(granted)
                if missing:
                    print(f"     [!] WARNING: Missing Instagram publishing permission(s): {', '.join(missing)}")
                    print(f"         Generate a token with 'instagram_basic' and 'instagram_content_publish' in Meta Graph API Explorer.")
        except Exception as e:
            print(f"     Could not check permissions: {e}")

    # Check Instagram User ID
    req_ig = urllib.request.Request(
        f"{api}/{ig_id}?fields=id,username,name",
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req_ig, timeout=15) as resp:
            ig_data = json.load(resp)
            print(f"[OK] IG Account: @{ig_data.get('username', 'unknown')} (ID: {ig_data.get('id')})")
    except Exception as e:
        print(f"[WARN] Could not verify IG_USER_ID {ig_id}: {e}")

    # Check gh CLI
    try:
        gh_check = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
        if gh_check.returncode == 0:
            print("[OK] GitHub CLI is authenticated locally.")
        else:
            print("[WARN] GitHub CLI auth check failed. Releases upload may need 'gh auth login'.")
    except FileNotFoundError:
        print("[WARN] 'gh' CLI not found in PATH.")

    # Check state files
    posted_path = ROOT / "posted.json"
    if posted_path.exists():
        try:
            posted = json.loads(posted_path.read_text(encoding="utf-8"))
            print(f"[OK] posted.json loaded: {len(posted)} carousels logged.")
            if posted:
                last_p = posted[-1]
                print(f"     Last carousel: {last_p.get('id')} at {last_p.get('posted_at')}")
        except Exception as e:
            print(f"[WARN] Failed reading posted.json: {e}")

    state_path = ROOT / "reels" / "state.json"
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            posts = state.get("posts", {})
            print(f"[OK] reels/state.json loaded: {len(posts)} reel/news entries.")
            if posts:
                last_key = list(posts.keys())[-1]
                last_entry = posts[last_key]
                print(f"     Last entry: {last_key} ({last_entry.get('status')}) at {last_entry.get('published_at') or last_entry.get('attempted_at')}")
        except Exception as e:
            print(f"[WARN] Failed reading reels/state.json: {e}")

    print("=" * 60)
    return True


def run_carousel(dry_run=False, post_id=None):
    """Replicates .github/workflows/daily-post.yml"""
    print(f"\n--- Running Carousel Autopost (dry_run={dry_run}, post_id={post_id}) ---")
    get_token()
    get_ig_id()
    
    env = os.environ.copy()
    if dry_run:
        env["DRY_RUN"] = "true"
    if post_id:
        env["POST_ID"] = post_id
        
    cmd = [sys.executable, str(ROOT / "post.py")]
    res = subprocess.run(cmd, cwd=str(ROOT), env=env)
    if res.returncode != 0:
        print(f"[FAIL] post.py exited with code {res.returncode}")
        return False
    
    # Commit posted.json if updated
    if not dry_run:
        subprocess.run(["git", "add", "posted.json"], cwd=str(ROOT))
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(ROOT))
        if diff.returncode != 0:
            commit_msg = f"Log post {dt.datetime.now(IST).strftime('%Y-%m-%d %H:%M')}"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(ROOT))
            print(f"[OK] Committed updated posted.json. Pushing changes...")
            for attempt in range(1, 4):
                if subprocess.run(["git", "pull", "--rebase", "-q"], cwd=str(ROOT)).returncode == 0:
                    if subprocess.run(["git", "push"], cwd=str(ROOT)).returncode == 0:
                        print("[OK] Successfully pushed posted.json to remote.")
                        break
                print(f"Push attempt {attempt} failed, retrying...")
                time.sleep(attempt * 3)
    return True


def run_calendar_reel(dry_run=False):
    """Replicates .github/workflows/shipstack-schedule.yml"""
    print("\n--- Running ShipStack Month Calendar Reel Workflow ---")
    get_token()
    get_ig_id()
    
    # 1. Plan slot
    res = subprocess.run(
        [sys.executable, "-m", "reels.shipstack.schedule", "plan"],
        cwd=str(ROOT), capture_output=True, text=True
    )
    if res.returncode != 0:
        print(f"[FAIL] Schedule plan failed: {res.stderr}")
        return False
        
    output = res.stdout.strip()
    if not output:
        print("No slot due right now according to calendar.")
        return True
        
    try:
        slot = json.loads(output)
    except json.JSONDecodeError:
        print(f"Failed to parse plan output: {output}")
        return False
        
    print(f"[DUE] Slot found: {slot['id']} | Format: {slot['format']} | Episode: {slot['episode']} | Due at {slot['time']}")
    
    # 2. Check posting plan before rendering
    check_cmd = [
        sys.executable, "-m", "reels.shipstack.publish",
        "--reel", slot["format"],
        "--key", slot["id"],
        "--url", "https://example.invalid/check.mp4",
        "--dry-run"
    ]
    check_res = subprocess.run(check_cmd, cwd=str(ROOT))
    if check_res.returncode != 0:
        print(f"[BLOCKED] Posting plan check blocked this run.")
        return False
        
    if dry_run:
        print(f"[DRY-RUN] Verification complete for due slot {slot['id']}. Skipping render and publish.")
        return True
        
    # 3. Render and verify
    out_dir = ROOT / "reels" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = out_dir / "slot.mp4"
    named_mp4 = out_dir / f"{slot['id']}.mp4"
    
    print(f"\nRendering format {slot['format']} episode {slot['episode']}...")
    render_cmd = [
        sys.executable, "-m", "reels.shipstack",
        "--format", slot["format"],
        "--episode", str(slot["episode"]),
        "--out", str(out_mp4)
    ]
    render_res = subprocess.run(render_cmd, cwd=str(ROOT))
    if render_res.returncode != 0:
        print("[FAIL] Rendering failed.")
        return False
        
    verify_cmd = [sys.executable, str(ROOT / "reels" / "verify.py"), str(out_mp4)]
    if subprocess.run(verify_cmd, cwd=str(ROOT)).returncode != 0:
        print("[FAIL] Video verification failed.")
        return False
        
    import shutil
    shutil.copyfile(out_mp4, named_mp4)
    
    # 4. Host clip as a public release asset via GitHub CLI
    tag = f"shipstack-{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m')}"
    repo = os.environ.get("GITHUB_REPOSITORY", "Sumntpathak/insta-autopost")
    print(f"\nUploading {named_mp4.name} to GitHub Release {tag}...")
    
    # Create release if not exists
    subprocess.run(
        ["gh", "release", "create", tag, "--title", f"ShipStack reels {tag}", "--notes", "Rendered locally", "--latest=false"],
        cwd=str(ROOT), capture_output=True
    )
    # Upload asset
    up_res = subprocess.run(
        ["gh", "release", "upload", tag, str(named_mp4), "--clobber"],
        cwd=str(ROOT), capture_output=True, text=True
    )
    if up_res.returncode != 0:
        print(f"[FAIL] Failed to upload release asset: {up_res.stderr}")
        return False
        
    video_url = f"https://github.com/{repo}/releases/download/{tag}/{slot['id']}.mp4"
    print(f"[OK] Video hosted at: {video_url}")
    
    # Verify download URL is accessible
    try:
        req = urllib.request.Request(video_url, headers={"Range": "bytes=0-1023"})
        with urllib.request.urlopen(req, timeout=20) as r:
            if r.status not in (200, 206):
                print(f"[FAIL] Video asset URL responded with status {r.status}")
                return False
    except Exception as e:
        print(f"[FAIL] Could not verify public URL reachability: {e}")
        return False
        
    # 5. Publish
    print("\nPublishing reel to Instagram...")
    pub_cmd = [
        sys.executable, "-m", "reels.shipstack.publish",
        "--reel", slot["format"],
        "--episode", str(slot["episode"]),
        "--key", slot["id"],
        "--url", video_url
    ]
    pub_res = subprocess.run(pub_cmd, cwd=str(ROOT))
    if pub_res.returncode != 0:
        print("[FAIL] reels.shipstack.publish failed.")
        return False
        
    print(f"[SUCCESS] Slot {slot['id']} rendered, hosted, and published!")
    return True


def run_single_reel(format_name, episode=1, publish=False):
    """Replicates .github/workflows/shipstack-reel.yml"""
    print(f"\n--- Running Single Reel: format={format_name}, episode={episode}, publish={publish} ---")
    if publish:
        get_token()
        get_ig_id()
        
    out_dir = ROOT / "reels" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = out_dir / f"{format_name}-ep{episode}.mp4"
    
    print(f"Rendering {format_name} episode {episode} to {out_mp4}...")
    render_cmd = [
        sys.executable, "-m", "reels.shipstack",
        "--format", format_name,
        "--episode", str(episode),
        "--out", str(out_mp4)
    ]
    if subprocess.run(render_cmd, cwd=str(ROOT)).returncode != 0:
        print("[FAIL] Rendering failed.")
        return False
        
    if subprocess.run([sys.executable, str(ROOT / "reels" / "verify.py"), str(out_mp4)], cwd=str(ROOT)).returncode != 0:
        print("[FAIL] Verification failed.")
        return False
        
    print(f"[OK] Video ready and verified at: {out_mp4}")
    
    if not publish:
        print("[INFO] Publish flag was false. Video rendered and verified. Run with --publish to send to Instagram.")
        return True
        
    tag = f"shipstack-{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m')}"
    repo = os.environ.get("GITHUB_REPOSITORY", "Sumntpathak/insta-autopost")
    print(f"Uploading to GitHub release {tag}...")
    subprocess.run(["gh", "release", "create", tag, "--title", f"ShipStack reels {tag}", "--latest=false"], cwd=str(ROOT), capture_output=True)
    subprocess.run(["gh", "release", "upload", tag, str(out_mp4), "--clobber"], cwd=str(ROOT), check=True)
    video_url = f"https://github.com/{repo}/releases/download/{tag}/{out_mp4.name}"
    
    slot_key = f"{format_name}-{episode}-{int(time.time())}"
    pub_cmd = [
        sys.executable, "-m", "reels.shipstack.publish",
        "--reel", format_name,
        "--episode", str(episode),
        "--key", slot_key,
        "--url", video_url
    ]
    return subprocess.run(pub_cmd, cwd=str(ROOT)).returncode == 0


def run_asia_desk(publish=False):
    """Replicates .github/workflows/asia-desk.yml"""
    print(f"\n--- Running Asia Desk Workflow (publish={publish}) ---")
    if publish:
        get_token()
        get_ig_id()
    
    # Run structural validation
    val_script = """
import datetime, json, pathlib
root = pathlib.Path("asia-desk")
data = json.loads((root / "edition.json").read_text())
today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).date().isoformat()
print(f"Edition date: {data['date']}, Current date: {today}")
assert data["id"] == "ASIA-" + data["date"].replace("-", ""), "Edition ID/date mismatch"
stories = data["stories"]
assert len(stories) == 7, "Expected exactly seven verified stories"
urls = [s["url"] for s in stories]
assert len(set(urls)) == 7, "Duplicate source URLs"
for s in stories:
    assert s.get("headline") and s.get("source") and s.get("time"), "Missing attribution"
    assert s["url"].startswith("https://"), "Original HTTPS source required"
    assert s.get("verified") is True, "Every story must be manually/editorially verified"
slides = sorted((root / "slides").glob("*.jpg"))
assert len(slides) == 8, "Need eight publication-ready JPG slides"
print("Edition manifest and assets pass structural validation.")
"""
    val_res = subprocess.run([sys.executable, "-c", val_script], cwd=str(ROOT))
    if val_res.returncode != 0:
        print("[FAIL] Asia Desk validation failed.")
        return False
        
    if not publish:
        print("[OK] Asia Desk structural validation passed. Add --publish to publish.")
        return True
        
    pub_res = subprocess.run([sys.executable, "asia-desk/publish.py"], cwd=str(ROOT))
    if pub_res.returncode != 0:
        print("[FAIL] asia-desk/publish.py failed.")
        return False
        
    # Commit journal
    subprocess.run(["git", "add", "asia-desk", "news-pilot", "reels/state.json", "posted.json"], cwd=str(ROOT))
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(ROOT))
    if diff.returncode != 0:
        subprocess.run(["git", "commit", "-m", f"Publish Asia Desk {dt.datetime.now(IST).strftime('%Y-%m-%d')}"], cwd=str(ROOT))
        subprocess.run(["git", "pull", "--rebase", "-q"], cwd=str(ROOT))
        subprocess.run(["git", "push"], cwd=str(ROOT))
        print("[OK] Publishing journal saved and pushed.")
    return True


def run_daemon(poll_seconds=300):
    """Continuous local scheduler loop matching GitHub cron schedules."""
    print("=" * 60)
    print("ShipStack Local Autopost Daemon Started")
    print(f"Polling interval: {poll_seconds} seconds")
    print("Schedules monitored:")
    print("  - Carousels: 08:37 IST & 19:07 IST (post.py)")
    print("  - Month Calendar Reels: checked every 30 minutes")
    print("Press Ctrl+C to stop.")
    print("=" * 60)
    
    last_carousel_check = None
    last_calendar_check = 0
    
    while True:
        try:
            now = dt.datetime.now(IST)
            now_ts = time.time()
            current_minute = now.strftime("%Y-%m-%d %H:%M")
            
            # Check calendar reels every 30 minutes (1800s)
            if now_ts - last_calendar_check >= 1800:
                print(f"[{now.strftime('%H:%M:%S IST')}] Checking month calendar reels...")
                try:
                    run_calendar_reel(dry_run=False)
                except Exception as e:
                    print(f"Error in calendar reel job: {e}")
                last_calendar_check = now_ts
                
            # Check carousels at morning (08:37) and evening (19:07)
            time_str = now.strftime("%H:%M")
            if time_str in ("08:37", "19:07") and last_carousel_check != current_minute:
                print(f"[{now.strftime('%H:%M:%S IST')}] Scheduled carousel slot triggered: {time_str}")
                try:
                    run_carousel(dry_run=False)
                except Exception as e:
                    print(f"Error in carousel job: {e}")
                last_carousel_check = current_minute
                
            time.sleep(poll_seconds)
        except KeyboardInterrupt:
            print("\nDaemon stopped by user.")
            break
        except Exception as e:
            print(f"Unexpected loop exception: {e}")
            time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="Local Workflow Runner for @shipstack_ Instagram autopost")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # status / check
    subparsers.add_parser("status", help="Verify tokens, connectivity, account, and journal status")
    subparsers.add_parser("check", help="Alias for status")
    
    # carousel
    p_carousel = subparsers.add_parser("carousel", help="Publish due carousel (post.py)")
    p_carousel.add_argument("--dry-run", action="store_true", help="Verify token and image URLs without posting")
    p_carousel.add_argument("--post-id", type=str, default=None, help="Post specific carousel ID from schedule.json")
    
    # reel-calendar
    p_cal = subparsers.add_parser("reel-calendar", help="Check and publish due slot from calendar.json")
    p_cal.add_argument("--dry-run", action="store_true", help="Plan and check posting rules without rendering or posting")
    
    # reel-manual
    p_reel = subparsers.add_parser("reel", help="Render and optionally publish a specific reel format")
    p_reel.add_argument("--format", required=True, choices=["lab01", "lab02", "ring", "strings", "balloon"], help="Reel format")
    p_reel.add_argument("--episode", type=int, default=1, help="Episode number for seed / setup")
    p_reel.add_argument("--publish", action="store_true", help="Publish to Instagram after rendering and verifying")
    
    # asia-desk
    p_asia = subparsers.add_parser("asia-desk", help="Validate or publish current Asia Desk edition")
    p_asia.add_argument("--publish", action="store_true", help="Publish to Instagram")
    
    # daemon
    p_daemon = subparsers.add_parser("daemon", help="Run local scheduler daemon loop")
    p_daemon.add_argument("--poll", type=int, default=300, help="Polling interval in seconds (default: 300)")

    args = parser.parse_args()
    
    if not args.command or args.command in ("status", "check"):
        check_status()
    elif args.command == "carousel":
        run_carousel(dry_run=args.dry_run, post_id=args.post_id)
    elif args.command == "reel-calendar":
        run_calendar_reel(dry_run=args.dry_run)
    elif args.command == "reel":
        run_single_reel(format_name=args.format, episode=args.episode, publish=args.publish)
    elif args.command == "asia-desk":
        run_asia_desk(publish=args.publish)
    elif args.command == "daemon":
        run_daemon(poll_seconds=args.poll)


if __name__ == "__main__":
    main()
