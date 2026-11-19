"""Morning Multi-Agent Pipeline for @shipstack_

Runs every morning (09:00 AM IST) on your laptop:
1. News Agent: Gathers & renders 15 Pubity-style 1080x1350 single-image news posts + full captions.
2. Physics Agent: Renders 5 Physics reels (episodes 1-5).
3. Ball Agent: Renders 5 Ball game reels (Ring Escape, Balloon Pop, String Battle).
4. Host & Scheduler Agent:
   - Uploads videos to GitHub Release (shipstack-YYYY-MM) for public Meta ingestion.
   - Commits and pushes news images to Git for raw public URLs.
   - Assembles 25 scheduled timeslots (09:30 to 23:30 IST, spaced ~35 mins apart) into daily_schedule.json.

Once this finishes in ~10-12 minutes, you are free for the day!
"""
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Ensure dotenv and repo defaults
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

os.environ.setdefault("GITHUB_REPOSITORY", "Sumntpathak/insta-autopost")
os.environ.setdefault("GITHUB_REF_NAME", "main")

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

import news_curator
from reels.shipstack.publish import CAPTIONS, caption as get_caption


def render_reel(format_name, episode, out_path):
    cmd = [
        sys.executable, "-m", "reels.shipstack",
        "--format", format_name,
        "--episode", str(episode),
        "--out", str(out_path)
    ]
    res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to render {format_name}: {res.stderr}")
    # Verify MP4
    v_res = subprocess.run([sys.executable, str(ROOT / "reels" / "verify.py"), str(out_path)], cwd=str(ROOT), capture_output=True, text=True)
    if v_res.returncode != 0:
        raise RuntimeError(f"Verification failed for {out_path}: {v_res.stderr}")
    return out_path


def build_morning_package(date_str=None):
    if not date_str:
        date_str = dt.datetime.now(IST).strftime("%Y-%m-%d")
        
    print("=" * 65)
    print(f"SHIPSTACK MORNING MULTI-AGENT PIPELINE: {date_str}")
    print("Goal: Build 25 daily posts (15 News + 5 Physics + 5 Ball Reels)")
    print("=" * 65)
    
    # -------------------------------------------------------------
    # 1. NEWS AGENT: 15 Pubity-style single-image news posts
    # -------------------------------------------------------------
    print("\n[Agent 1: News & Editorial Researcher]")
    news_items = news_curator.generate_daily_news(date_str=date_str, target_count=15)
    print(f"[OK] 15 Pubity-style single-image news cards rendered.")
    
    # Commit and push news images to Git so raw URLs are public for Instagram
    print("Pusing news images to GitHub for public Meta URLs...")
    subprocess.run(["git", "add", f"images/daily/{date_str}"], cwd=str(ROOT))
    subprocess.run(["git", "commit", "-m", f"Add news graphics for {date_str}"], cwd=str(ROOT), capture_output=True)
    subprocess.run(["git", "pull", "--rebase", "-q"], cwd=str(ROOT), capture_output=True)
    subprocess.run(["git", "push"], cwd=str(ROOT), capture_output=True)
    
    repo = os.environ.get("GITHUB_REPOSITORY", "Sumntpathak/insta-autopost")
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    raw_base = f"https://raw.githubusercontent.com/{repo}/{branch}/"

    for n in news_items:
        n["public_url"] = raw_base + n["image"]

    # -------------------------------------------------------------
    # 2. PHYSICS AGENT: 5 Physics Reels
    # -------------------------------------------------------------
    print("\n[Agent 2: 3D Motion & Physics Director (5 Physics Reels)]")
    physics_items = []
    out_dir = ROOT / "reels" / "out" / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Interleave Lab & physics simulations
    physics_specs = [
        ("strings", 101, "Physics String Dynamics · Country Battle"),
        ("balloon", 201, "Elastic Collision & Stress Inflation"),
        ("ring", 301, "Centrifugal Ring Escape Simulation"),
        ("strings", 102, "Chaotic Boundary Cutting Dynamics"),
        ("balloon", 202, "Multi-Particle Slow-Motion Pop Physics"),
    ]
    
    for idx, (fmt, ep, title) in enumerate(physics_specs, 1):
        reel_file = out_dir / f"physics-{idx:02d}-{fmt}-ep{ep}.mp4"
        print(f"  Rendering Physics {idx}/5: {fmt} (ep {ep})...")
        render_reel(fmt, ep, reel_file)
        
        cap = CAPTIONS.get(fmt) or get_caption(fmt, ep)
        physics_items.append({
            "id": f"PHYSICS-{date_str}-{idx:02d}",
            "type": "physics_reel",
            "format": fmt,
            "episode": ep,
            "title": title,
            "file": str(reel_file),
            "caption": cap or f"Physics simulation · @shipstack_\n#physics #simulation #science #satisfying"
        })
    print("[OK] 5 Physics reels rendered and verified.")

    # -------------------------------------------------------------
    # 3. BALL AGENT: 5 Ball Game Reels
    # -------------------------------------------------------------
    print("\n[Agent 3: Ball Games & Arena Director (5 Ball Reels)]")
    ball_items = []
    ball_specs = [
        ("ring", 401, "Pick A Ball: Who Escapes First?"),
        ("balloon", 501, "Pick A Balloon: Who Pops First?"),
        ("strings", 601, "Country Ball Battle: Who Survives?"),
        ("ring", 402, "Ring Escape: Narrow 4.1% Rim Gap"),
        ("balloon", 502, "Balloon Pop Finale (Slow-Mo)"),
    ]
    
    for idx, (fmt, ep, title) in enumerate(ball_specs, 1):
        reel_file = out_dir / f"ball-{idx:02d}-{fmt}-ep{ep}.mp4"
        print(f"  Rendering Ball Game {idx}/5: {fmt} (ep {ep})...")
        render_reel(fmt, ep, reel_file)
        
        cap = CAPTIONS.get(fmt) or get_caption(fmt, ep)
        ball_items.append({
            "id": f"BALL-{date_str}-{idx:02d}",
            "type": "ball_reel",
            "format": fmt,
            "episode": ep,
            "title": title,
            "file": str(reel_file),
            "caption": cap or f"Pick one before you watch! · @shipstack_\n#physics #simulation #pickone #satisfying"
        })
    print("[OK] 5 Ball reels rendered and verified.")

    # -------------------------------------------------------------
    # 4. HOSTING & SCHEDULING AGENT: Upload Reels & Assemble Queue
    # -------------------------------------------------------------
    print("\n[Agent 4: Publishing Operator & Scheduler]")
    tag = f"shipstack-{date_str[:7]}"
    subprocess.run(["gh", "release", "create", tag, "--title", f"ShipStack {tag}", "--latest=false"], cwd=str(ROOT), capture_output=True)
    
    # Upload video reels
    all_reels = physics_items + ball_items
    for r in all_reels:
        fname = Path(r["file"]).name
        print(f"  Uploading {fname} to GitHub release {tag}...")
        subprocess.run(["gh", "release", "upload", tag, r["file"], "--clobber"], cwd=str(ROOT), capture_output=True)
        r["public_url"] = f"https://github.com/{repo}/releases/download/{tag}/{fname}"

    # Smoothly interleave all 25 posts
    # Plan: 25 slots from 09:30 AM to 23:30 PM (every 35 mins)
    start_hour, start_min = 9, 30
    combined_posts = []
    
    # Interleaving pattern: N, P, N, B, N, N, P, N, B, N, N, P, N, B, N, N, P, N, B, N, N, P, N, B, N
    pattern = [
        ("news", news_items[0]),
        ("physics", physics_items[0]),
        ("news", news_items[1]),
        ("ball", ball_items[0]),
        ("news", news_items[2]),
        ("news", news_items[3]),
        ("physics", physics_items[1]),
        ("news", news_items[4]),
        ("ball", ball_items[1]),
        ("news", news_items[5]),
        ("news", news_items[6]),
        ("physics", physics_items[2]),
        ("news", news_items[7]),
        ("ball", ball_items[2]),
        ("news", news_items[8]),
        ("news", news_items[9]),
        ("physics", physics_items[3]),
        ("news", news_items[10]),
        ("ball", ball_items[3]),
        ("news", news_items[11]),
        ("news", news_items[12]),
        ("physics", physics_items[4]),
        ("news", news_items[13]),
        ("ball", ball_items[4]),
        ("news", news_items[14]),
    ]
    
    current_time = dt.datetime.strptime(f"{date_str} {start_hour:02d}:{start_min:02d}", "%Y-%m-%d %H:%M").replace(tzinfo=IST)
    
    for slot_idx, (cat, item) in enumerate(pattern, 1):
        slot_time_str = current_time.strftime("%H:%M")
        combined_posts.append({
            "slot": slot_idx,
            "scheduled_time": slot_time_str,
            "scheduled_datetime": current_time.isoformat(),
            "date": date_str,
            "category": cat,
            "id": item["id"],
            "title": item.get("headline") or item.get("title"),
            "is_reel": cat in ("physics", "ball"),
            "media_url": item["public_url"],
            "caption": item["caption"],
            "status": "pending"
        })
        current_time += dt.timedelta(minutes=35)

    queue_file = ROOT / "daily_schedule.json"
    queue_file.write_text(json.dumps(combined_posts, indent=2), encoding="utf-8")
    
    print("\n" + "=" * 65)
    print("SUCCESS: 25 DAILY POSTS GENERATED, HOSTED & QUEUED!")
    print(f"Schedule File: {queue_file}")
    print(f"Active Window: 09:30 IST to 23:30 IST (every 35 mins)")
    print("Breakdown: 15 News (Pubity single-image) + 5 Physics Reels + 5 Ball Reels")
    print("You are now free for the day! The local publisher will deliver each due post.")
    print("=" * 65)
    return combined_posts


if __name__ == "__main__":
    build_morning_package()
