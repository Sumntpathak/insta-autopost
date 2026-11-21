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
   least 60 minutes between them (calendar: 6/day; the rest is headroom for the news agent).
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
| `reels/shipstack/calendar.json` | **The month plan**: 180 slots (date, IST time, format, episode). Edit freely; `"paused": true` stops it. |
| `reels/shipstack/schedule.py` | Calendar generator (`make`) and due-slot finder (`plan`). |
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
| `shipstack-schedule.yml` | every 5 min | yes, when a calendar slot is due | **Unattended month plan**: render → verify → host → guarded publish of the due slot. |
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

## The month calendar (hands-off posting)

- `reels/shipstack/calendar.json` holds 30 days × 6 slots (IST): 08:10 physics (Lab Nº 01/02
  alternating), 10:40 balloon, 13:10 country battle, 16:10 ring escape, 19:10 balloon,
  21:40 country battle. Every slot has its own episode, so every race/setup is different.
- `shipstack-schedule.yml` runs every 5 minutes on the default branch and posts the due slot (slots missed by more than 2 h are skipped).
- Regenerate for the next month: `python -m reels.shipstack.schedule make --start YYYY-MM-DD --days 30`.
- Stop: set `"paused": true` in the calendar (or disable the workflow in the Actions tab).
- Tech news (5/day) is posted by a separate agent; the guard leaves room for it.

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

## Handoff (21 Nov 2026)

State of play for whoever picks this up next. Details are in the git log and the PRs.

- **Branch:** `claude/epic-johnson-swuv6r` is merged into `main` (PRs #5–#8). Work on a new branch and open a PR for each change.
- **Launch:** logo Reel + Story (17:19 IST, 20 Nov) and DSA #0001 (18:27 IST, 20 Nov) are live. Their journal keys are `LAUNCH-2026-11-*` in `reels/state.json`. The third launch post, news, is **on hold**: `launch/posts.json` marks it `ready: false`, because no fresh story has been verified against its source yet. The Anthropic IPO card was already posted on 19 Nov, so do not reuse it.
- **Launch override:** `--override-daily-cap` was approved for the launch posts only. It is recorded in the journal. Do not use it for other posts.
- **Open decision:** the owner has not yet decided on posting volume. The profile audit recommends 1–2 posts/day. The calendar currently runs 6/day, and the external news agent (`daily_publisher.py`, run from the owner's laptop) runs about 20/day outside the guard and journal. Do not change the volume without asking.
- **Still to do in the Instagram app (the API cannot):** set the category to Digital creator, update the name and bio, pin three posts, create the highlights, and fix the cover on the "We ship" Reel.
- **Renders:** Arena reels get a `#NN` badge (`reels/shipstack/badge.py`). Every reel sets `thumb_offset` (`THUMB_MS` in `publish.py`), enforced by a test. News cards are drawn by `news_renderer.render_pubity_card`, which now uses the dark Studio card.
- **Tools:** the Studio, Arena and film renders need `libegl1` and `signalflow` (see Run locally).
