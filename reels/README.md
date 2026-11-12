# 30-day physics reel trial for @shipstack_

This is a bounded experiment, not a promise of reach. Target: **10 unique 15-second
1080×1920, 30 FPS reels/day for 30 days (300 slots)**. GitHub schedule delays, failed
renders, API outages or account restrictions can mean fewer successful posts.
Missed days are not dumped into the next day. At most one due clip goes out per run.

## Source and variety

The five simulations in `vendor/` are upstream Matter.js examples (whitespace normalized) from
https://github.com/liabru/matter-js/tree/0.20.0/examples (MIT; notice in vendor/LICENSE).
Matter.js is pinned to 0.20.0. We reuse ballPool, newtonsCradle, avalanche,
restitution and chains. The adapter seeds each slot independently, rotates palettes,
varies gravity/initial velocities, recycles escaped balls and re-energizes free-body
scenes. These are variations of five scenes, **not 300 separate templates**. The
rotating-paddle scene from the original reference is not included in this pack.
No downloaded Instagram footage, third-party watermark, or unlicensed music is used.
AAC is a silent compatibility track. The physics and scene definitions are upstream;
the small custom layer handles styling, export, scheduling and publishing.

## Start / preview / insights

After merging, Actions → **Physics reels — 30-day trial** → Run workflow:

- `preview`: render and validate a sample; download the MP4 artifact. No post.
- `check`: verify the existing Meta credentials resolve to @shipstack_. No post.
- `insights`: export the most recent 100 Instagram media and available metrics,
  including older carousels. Download `insights.json` from the run artifact.
- `start`: initialize tomorrow in IST, or set `start_date` (YYYY-MM-DD). It refuses
  to reset an initialized campaign. No immediate post.
- `post`: publish one due slot. Automatic runs check every half-hour, at :07/:37.

The first automatic run validates the account, initializes the campaign for the next
IST day, and exports baseline insights. It never restarts an expired campaign.
`start` can alternatively initialize a chosen future date before that first run. Ten slots (IST):
07:00, 08:40, 10:20, 12:00, 13:40, 15:20, 17:00, 18:40, 20:20, 22:00.
Scheduled runs publish shortly after a slot, not precisely at the slot minute.
The existing carousel job pauses during the active trial and resumes afterward.
All publishing jobs share the same concurrency group.

## Credentials and hosting

Uses the existing GitHub secrets `META_TOKEN` and `IG_USER_ID`. No new secrets.
The token must permit content publishing; insights require the corresponding
Instagram insights permissions. A successful historical carousel run does not prove
Reels or insights permissions. The account check blocks publishing to a different
username. This pipeline intentionally publishes only Instagram reels, not Facebook.

Rendered MP4s are public GitHub Release assets, not committed to git. This requires
the repository to remain public and Actions contents:write. Expect 300 renders and
300 retained assets over a full campaign, plus runner/artifact storage usage; review
your GitHub plan's usage. The publisher verifies asset availability and waits for
Meta video processing. Reports and preview artifacts expire after their retention
period; download reports if you want to retain the entire experiment.

## Reliability / recovery

`state.json` records the slot, seed, scene and Instagram media/container ID. It is
pushed **before** calling `media_publish`, then updated on success. If an API timeout
makes the result uncertain, the slot stays `publishing` and is not automatically
retried. Inspect the container/account before resolving that entry; deleting it can
duplicate an already published Reel. An asset left by a failed render/upload can be
replaced safely because no publish attempt has been journaled yet. Do not change
slot/scene configuration during an active trial. To stop early, disable this workflow
in Actions (and disable the carousel workflow too if all posting should stop).

No secrets are printed or stored in reports. Local runs that publish require a
writable authenticated git checkout because journal push failures block publishing.

## Evaluate weekly

First export baseline insights. Compare reels at similar ages (e.g. 48 hours), by
scene: reach, views, saves/reach and shares/reach. The report keeps unsupported or
unauthorized metrics missing rather than treating them as zero. Daily 23:17 IST
snapshots cover the latest 100 media, not the whole month in a single report.
Non-follower reach, watch-time and follows may need Instagram's Insights screenshots;
they are not inferred from total reach. There is no automatic content optimization
or guarantee of new viewers. After seven days, keep the formats that show results
rather than increasing volume alone. Baseline insights cannot be read from GitHub
secrets by the assistant; run `insights` and share the artifact here.

## Local verification

```sh
npm ci --prefix reels
python -m unittest discover -s reels/tests -v
node reels/render.mjs avalanche 123 reels/out/preview.mp4
python reels/verify.py reels/out/preview.mp4
```

Requires Node 22+, Python 3.12+, ffmpeg/ffprobe. No browser is required.
