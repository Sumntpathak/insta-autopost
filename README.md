# @shipstack_ autopost (free)

GitHub Actions posts a **6-slide system-design carousel twice a day** to Instagram:
**08:37 IST** (morning slot) and **19:07 IST** (evening slot), from `schedule.json`.

Each post: 1 hook + diagram, 2 desi story analogy (kahani mein -> tech mein),
3 the trap (red), 4 the fix (green), 5 interview cheat sheet (save trigger),
6 A/B question + follow (comment/share trigger). Blueprint "SYSTEM DESIGN · 0NN" series look.

## How posting works
- Each run publishes **one** item: the oldest scheduled slot that is due and not in `posted.json`.
  If GitHub skips a run, the next run catches up, so nothing is lost or double-posted.
- `posted.json` is committed back after every post.

## Make more posts
```bash
cd generator && npm install
# add posts to data/posts.json (schema: src/lib/types.ts)
node validate.mjs                       # layout + content checks
node render.mjs S061 S062               # -> ../images/S061_1.jpg ... _6.jpg (1080x1350 JPEG)
node schedule.mjs 2026-12-04 morning    # rebuilds ../schedule.json (skip ids already posted)
```

## Post one right now
Actions -> Instagram autopost -> Run workflow -> type an unpublished ID from `schedule.json`.

## Test without posting
Actions -> Instagram autopost -> Run workflow -> tick **dry_run**. It checks the token and that
every scheduled image URL is reachable, and publishes nothing.

## Secrets (never commit these)
Settings -> Secrets and variables -> Actions:
- `META_TOKEN`: Instagram Login token (`IG...`) or a Facebook Page token (`EAA...`).
- `IG_USER_ID`: Instagram account id.
- `FB_PAGE_ID` (optional): only works with a Facebook Page token.

Instagram Login tokens expire after ~60 days. Refresh before then and update the
`META_TOKEN` secret, or posting stops.

Published carousel images and the retired v1 archive are available in Git history. `posted.json` keeps the carousel publication record.

## Pythonic Life Reel collection

The [Pythonic Life integration](reels/pythonic/README.md) adapts five MIT-licensed
formats to 15-second portrait reels: Ring Escape, Balloon Pop, Last Ball Standing,
Crumbling Floor and Marble Race. Music and collision sounds are synthesized by
the upstream scripts. Existing Instagram post history and the 30-day window remain.

Completed one-off batches are recorded in `reels/state.json`. Their release assets remain available under GitHub Releases.