# Insta autopost (free)
GitHub posts one carousel a day from `schedule.json` to Instagram (+ Facebook Page) at ~7 PM IST.

## Add more days
Put slides in `images/` (JPEG only, 1080x1350) and add an entry to `schedule.json`:
{"date": "2026-11-14", "id": "T11", "images": ["images/T11_slide1.jpg", ...], "caption": "..."}
Max 10 images per carousel. Already-posted ids are tracked in `posted.json`, so nothing double-posts.

## Post one right now
Actions tab -> Daily Instagram post -> Run workflow -> type an id (e.g. T01).

## Test without posting
Actions tab -> Daily Instagram post -> Run workflow -> tick **dry_run**. It checks the token
and that every scheduled image URL is reachable, and publishes nothing.

## Secrets (never commit these)
Settings -> Secrets and variables -> Actions:
- `META_TOKEN`: Instagram Login token (`IG...`) or a Facebook Page token (`EAA...`).
- `IG_USER_ID`: Instagram account id.
- `FB_PAGE_ID` (optional): only works with a Facebook Page token.

Instagram Login tokens expire after ~60 days. Refresh before then and update the
`META_TOKEN` secret, or posting stops.
