# ShipStack scheduler (Cloudflare Worker)

GitHub's own `schedule:` cron was throttled to a few runs a day, so posts were missed. A Cloudflare cron trigger is reliable.
This Worker runs every 5 minutes, reads `reels/shipstack/calendar.json` and `reels/state.json` from the public repo, and **only when a
slot is due and no calendar run is already queued or running** it dispatches `.github/workflows/shipstack-calendar.yml`.
Rendering and posting stay in GitHub Actions (they need ffmpeg and Remotion). The workflow re-checks the slot and enforces the
posting guard (60 min gap, 12/day, journal first), so a duplicate dispatch can never double-post.

## Deploy (once, about 5 minutes; free Cloudflare plan is enough)
1. GitHub → Settings → Developer settings → Fine-grained tokens → new token: **only this repository**, permission **Actions: Read and write**
   (Metadata: read is added automatically). Copy it once; do not paste it into chat or commit it.
2. In a terminal:
   ```bash
   cd worker && npm install
   npx wrangler login
   npx wrangler secret put GITHUB_TOKEN     # paste the token when prompted
   npx wrangler deploy
   ```
3. Check: open `https://shipstack-scheduler.<your-subdomain>.workers.dev/status` (shows `due` and `paused`, dispatches nothing) and
   `npx wrangler tail` to watch the 5-minute ticks (`idle`, `busy` or `dispatched`).

## Stop
Set `"paused": true` in `reels/shipstack/calendar.json`, or `npx wrangler delete`.

## Test (no network, no token)
```bash
cd worker && node --test test/plan.test.mjs
```
