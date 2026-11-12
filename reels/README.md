# Collision Circuit — 30-day Reel experiment

@shipstack_ targets ten 15-second 1080×1920 reels per day for thirty days. This is an
experiment, not a promise of reach. GitHub schedule delays and API failures can
reduce the achieved posting count. The first campaign began 12 November 2026.

## Visual and audio direction (v2)

The new renderer uses Matter.js 0.20.0 for collisions, with a portrait Canvas layout:
large circular arena, colored particle trails, multiplying balls, real counters,
and a direction reversal at ten seconds. Three variants: `spinner` (two paddles),
`orbit` (ring only), `splitter` (three paddles). Slot seeds vary colors and motion.
These are custom visual scenes using the existing physics engine, not unchanged
upstream demos. The v1 upstream examples remain in vendor/ with their MIT notice.

`Collision Circuit` is an original synthesized 128 BPM instrumental, eight bars in
fifteen seconds. It has kick, percussion, bass, harmony, plucks, collision pings and
a cue for the reversal. No third-party recorded music is bundled. The output is
normalized to -16 LUFS with a -1.5 dBTP target. This is embedded original audio, not
an Instagram music-library/trending-song selection. `verify.py` rejects silent
outputs as well as incorrect video dimensions, frame count and duration.

## Operation

Actions → **Physics reels — 30-day trial** → Run workflow:

- `preview`: render and verify a sample; download the artifact. Does not publish.
- `check`: verify credentials belong to @shipstack_.
- `insights`: export available metrics for the most recent 100 account media.
- `post`: publish one due slot from today, respecting the pause flag and journal.
- `start`: initialize an unused campaign (tomorrow IST by default, or start_date).
  It refuses to reset existing history.

Automatic publishing checks every half hour, at :07/:37. Ten slots in IST:
07:00, 08:40, 10:20, 12:00, 13:40, 15:20, 17:00, 18:40, 20:20, 22:00.
A push changing `reels/config.json` or `reels/trigger.json` also runs one due slot.
If no campaign is initialized, automatic mode initializes tomorrow first.
`paused: true` in config stops planning/publishing; insights and previews still work.
The pause does not clear posting history or shift the 30-day campaign end date.

Existing carousels pause during the campaign date window and resume afterward.
All publishing jobs share concurrency `autopost`. Missed days are not dumped into
the next day. At most ten slots per date, and one post per workflow run.

## Hosting and credentials

Uses existing secrets META_TOKEN and IG_USER_ID. Token permissions must allow
content publishing; insights need the account's insights permissions. These are
Instagram-only posts. The account username is checked before container creation.

Videos are public GitHub Release assets, not committed to source. This requires a
public repository and Actions contents:write. A full month entails 300 renders,
runner usage and retained MP4 assets. Reports/previews are workflow artifacts with
35-day retention; download snapshots to retain a full historical analysis.

## Reliability and measurement

The posting journal is pushed before media_publish and updated on success. An
ambiguous API timeout remains `publishing`; it is never retried automatically.
Inspect the Instagram account/container before resolving that entry. Deleting
uncertain entries could duplicate already published reels. Journal push failure
blocks publishing. Existing Instagram posts are not replaced or deleted.

Nightly snapshots at 23:17 IST report available views, reach, saves, shares, likes
and comments. Unsupported metrics remain missing, never zero. Reports cover the
latest 100 media, not all 300 campaign posts at once. Compare scenes at similar
post ages; non-follower reach, watch time and follows may require app Insights.
There is no automatic content optimizer or guarantee of new viewers.

## Local checks

Requires Node 22+, Python 3.12+, ffmpeg and ffprobe; no browser.

```sh
npm ci --prefix reels
python -m unittest discover -s reels/tests -v
node reels/render.mjs spinner 42 reels/out/preview.mp4
python reels/verify.py reels/out/preview.mp4
```
