# ShipStack 25 Daily Posts Local Setup & Workflow Guide

Automated daily production and publishing for **@shipstack_**:
- **15 News posts** (Single 1080x1350 Pubity-style card with full story, key highlights, and source in the caption)
- **5 Physics reels** (1080x1920 60fps Lab animations: Brachistochrone, Pi Monte Carlo, Pendulums)
- **5 Ball reels** (1080x1920 60fps Arena games: Ring Escape, Balloon Pop, String Battle)
- **Total:** **25 posts per day** (fitting Meta's Instagram API daily ceiling).

---

## 1. Morning Workflow (09:00 AM IST)

Every morning at **09:00 AM IST**, the multi-agent builder runs:
1. **News Agent:** Scrapes top tech/AI/science feeds and renders 15 Pubity-style 1080x1350 cards.
2. **Physics Agent:** Renders 5 verified 60fps physics reels.
3. **Ball Agent:** Renders 5 verified 60fps ball game reels.
4. **Publisher Agent:** Pre-hosts videos on GitHub Releases, commits news images, and generates [`daily_schedule.json`](daily_schedule.json) with 25 slots from 09:30 AM to 11:30 PM (every 35 minutes).

**Run manually anytime:**
```powershell
python morning_pipeline.py
# OR
.\run-local.ps1 morning
```
*(Takes ~10–12 minutes total on your laptop CPU. Once finished, you are free for the day!)*

---

## 2. Automated Daily Delivery (09:30 AM – 11:30 PM IST)

During active hours, the dispatcher automatically sends the next due post every 35 minutes.

**Run as background loop:**
```powershell
python daily_publisher.py --daemon
# OR
.\run-local.ps1 dispatch --daemon
```

**Test with dry-run (simulation):**
```powershell
python daily_publisher.py --dry-run
```

---

## 3. Windows Task Scheduler Automation (Unattended)

To make everything happen automatically every day without touching anything:

```powershell
.\setup-windows-task.ps1
```

This creates:
- **`ShipStack-MorningPipeline`**: Starts at **09:00 AM IST** daily to build all 25 posts.
- **`ShipStack-Dispatcher`**: Runs **every 35 minutes** to publish the next due item to Instagram.

To uninstall:
```powershell
.\setup-windows-task.ps1 -Uninstall
```
