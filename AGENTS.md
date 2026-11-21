# AGENTS.md — how to work in this repo

Automated publishing for the Instagram account **@shipstack_** (and its Facebook Page).
Read this first. It describes what runs, how to render and publish safely, and the rules
every change must keep.

## Golden rules (do not break)

1. **Never post as a side effect.** Every publishing workflow is manual (`workflow_dispatch`)
   or a guarded schedule. Editing a file must never trigger a post. Use dry runs to test.
2. **Journal before publish.** Write a `publishing` record (with the container id) to the
   state file and push it *before* calling `media_publish`. An ambiguous failure is never
   retried automatically; reconcile it by hand from the container id.
3. **Respect the posting plan.** `reels/guard.py` allows at most 12 posts per IST day with at
   least 60 minutes between them (calendar: 12/day, so no separate news agent may post).
   Do not post in bursts.
4. **Missing metrics stay missing.** Never write 0 for an unavailable insight.
5. **Secrets stay in GitHub Actions.** `META_TOKEN`, `IG_USER_ID`, `FB_PAGE_ID` are never
   committed, printed or put in URLs (send the token as a `Bearer` header).
6. **One publisher at a time.** Every publishing job uses `concurrency: group: autopost`.

## Map

| Path | What it is |
|---|---|
| `reels/shipstack/` | **ShipStack engines (current formats).** `python -m reels.shipstack --list`. |
| `reels/shipstack/brand.py` | Single source of truth: palette, fonts, page grids. |
| `reels/shipstack/lab/` | Lab: editorial maths/physics reels (Manim + LaTeX + SignalFlow). See its README. |
| `reels/shipstack/studio/` | **Studio: the one design for News, AI Automation and DSA.** `cards.py` (news/automation posts), `dsa.py` (debugger reels from `problems.py`). |
| `reels/shipstack/arena/` | Arena: Balloon Pop, Ring Escape and Country String Battle (skia, 60 fps). See its README. |
| `reels/shipstack/publish.py` | Guarded publisher for all formats (guard → container → journal → publish) and captions. |
| `reels/guard.py` | Posting plan rules (60 min gap, 12/day). |
| `reels/shipstack/calendar.json` | **The calendar**: 12 slots/day (date, IST time, format, episode `next`). Edit freely; `"paused": true` stops it. |
| `reels/shipstack/schedule.py` | Calendar generator (`make`), due-slot finder (`plan`) and episode resolver (`resolve`). |
| `worker/` | Cloudflare Worker: the scheduler. Cron every 5 min, dispatches the calendar workflow when a slot is due. See its README. |
| `reels/insights_report.py` | Joins the insights export with how each reel was made; ranks designs by shares+saves per reach and watch ratio. |
| `reels/campaign.py` | 30-day reel campaign planner/publisher, insights export (`insights` mode). |
| `reels/verify.py` | Hard gate: H.264/AAC, 1080×1920, 15 s, 30 or 60 fps (450/900 frames), audible audio. |
| `reels/experiments/track_race.py` | Verified brachistochrone physics (used by Lab Nº 01). |
| `reels/pythonic/` | Adapted MIT "Pythonic Life" race scenes (pick-a-ball formats). |
| `reels/state.json` | Journal of every reel publish attempt (all pipelines). |
| `post.py`, `schedule.json`, `posted.json` | Legacy carousel publisher and its journal. |
| `team/` | Multi-platform "team" pilot. **Disabled** (`team/config.json`). |
| `generator/` | Carousel image generator (Remotion; check its licence before commercial use). |

## Workflows (`.github/workflows/`)

| Workflow | Trigger | Posts? | Purpose |
|---|---|---|---|
| `shipstack-calendar.yml` | dispatched by the Cloudflare Worker (`worker/`) every 5 min, only when a slot is due | yes | **Unattended calendar**: render → verify → host → guarded publish of the due slot. |
| `shipstack-reel.yml` | manual | only if **publish** is ticked | Render → verify → preview artifact → (optional) guarded publish of any format (`lab01`, `lab02`, `ring`, `strings`, `balloon`, `dsa`). **Use this for new content.** |
| `shipstack-launch.yml` | manual | only if **publish** is ticked | One-time launch: carousel (logo animation + the three series) and Story from `reels/shipstack/launch/`, via `reels/shipstack/announce.py` (guard + live account check + journal). |
| `reels.yml` | every 10 min + 23:17 IST + manual | no while `reels/config.json` is paused (it is) | Old 30-day campaign, **paused** (replaced by the calendar); still runs the daily insights snapshot + design report. |
| `daily-post.yml` | 08:37 / 19:07 IST + manual | yes (carousels) | Legacy carousel slots from `schedule.json`. Skips while the reel campaign is active. |
| `reels-check.yml` | pull requests | no | Unit tests + preview renders. |
| `instagram-audience.yml`, `shipstack-facebook-insights.yml`, `facebook-check.yml` | manual | no | Read-only account/insight checks. |
| `shipstack-team.yml`, `shipstack-team-tests.yml` | schedule (idle while disabled) / PRs | only if the pilot is enabled | Team pilot. |

Old one-off batch workflows (dated `shipstack-2026111x-*`, flag battle, AI shorts, etc.) were
removed; they remain in git history if ever needed.

## Run locally

```bash
# System packages (Ubuntu/Debian)
sudo apt-get install -y ffmpeg libegl1 libpango1.0-dev libcairo2-dev pkg-config \
  texlive-latex-base texlive-latex-extra texlive-fonts-recommended dvisvgm cm-super
pip install -r reels/shipstack/requirements.txt pytest

python -m reels.shipstack --list                           # all formats
python -m reels.shipstack --format lab01 --out reels/out/lab01.mp4
python -m reels.shipstack --format ring --episode 3        # new episode = new race
python -m reels.shipstack --format strings --episode 2
python -m reels.shipstack.lab --reel lab01 --out /tmp/g.mp4 --grid   # Lab alignment overlay
python reels/verify.py reels/out/lab01.mp4                 # accepts 30 or 60 fps
python -m pytest -q reels/tests team/tests                 # all tests (no network)
```

## Publish a reel

GitHub → Actions → **ShipStack reel** → Run workflow → choose the format (and an episode
number for Arena formats).
- Leave **publish** off first: download the `reel-…` artifact and watch it.
- Run again with **publish** on. The job checks the posting plan, uploads the MP4 as a
  release asset, journals to `reels/state.json`, then publishes.

## The calendar (hands-off posting): 12 a day, three formats

- `reels/shipstack/calendar.json`: 12 slots/day (IST, 90 min apart): 06:30 news, 08:00 dsa, 09:30 automation, 11:00 news, 12:30 dsa,
  14:00 automation, 15:30 news, 17:00 dsa, 18:30 automation, 20:00 news, 21:30 dsa, 23:00 automation. 4 of each.
- Slots carry `"episode": "next"`. When a slot fires, `schedule.resolve()` picks the next unposted episode: DSA from `studio/problems*.py`
  (#1 went out at launch), automation from `film/src/automations.json`, news from `reels/shipstack/news_feed.py` (outlets' own RSS headlines,
  newest unused, source credited, URL journaled as `news_url`). If DSA/automation content runs out, that slot posts news instead; if no fresh
  news exists the slot is skipped, never padded with filler. A slot missed by more than 3 h is skipped.
- Music: `reels/shipstack/music.py` (tracks in `film/public/bgm/`, see its README): Luminary under automation + DSA, the other track under news.
  Typing clicks sit at 35% under the music.
- Timing: a Cloudflare Worker (`worker/`, cron every 5 min) reads the calendar + journal, and dispatches `shipstack-calendar.yml` only when a slot is due
  (GitHub's own cron was throttled to a few runs a day). The workflow posts the due slot (guard: 60 min gap, 12/day, journal first).
- Regenerate: `python -m reels.shipstack.schedule make --start YYYY-MM-DD --days 30 [--not-before ISO]`. Stop: `"paused": true` or disable the workflow.
- Content runway: add DSA problems (`studio/problems_more.py`) and automations (`film/src/automations.json`) before they run out (about 5 days
  of each at 4/day); the calendar keeps going on news meanwhile. The old Arena/Lab formats still render but are no longer scheduled.

## Measure

Actions → **Reel campaign** → mode `insights`. The run summary shows the design report
(`reels/insights_report.py`); the artifact contains `insights.json`. Lab reels are recorded
with `collection: shipstack-lab|shipstack-arena` and `scene: lab01|lab02|ring|strings|balloon`, so they
group separately.

## Adding work

- New Lab reel: follow `reels/shipstack/lab/README.md`; new Arena game: `reels/shipstack/arena/README.md`.
- Tech news is produced by a separate agent (not in this repo yet).
- Any new publisher must use `reels/guard.py`, journal before publish, and the `autopost`
  concurrency group, and must default to not posting.
- Run the tests before committing; add a test for every safety rule you touch.
