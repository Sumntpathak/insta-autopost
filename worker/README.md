# ShipStack scheduler (Cloudflare Worker)

GitHub's own `schedule:` cron was throttled to a few runs a day, so posts were missed. A Cloudflare cron trigger is reliable.
This Worker runs every 5 minutes, reads `reels/shipstack/calendar.json` and `reels/state.json` from the public repo, and **only when a
slot is due and no calendar run is already queued or running** it dispatches `.github/workflows/shipstack-calendar.yml`.
Rendering and posting stay in GitHub Actions (they need ffmpeg and Remotion). The workflow re-checks the slot and enforces the
posting guard (60 min gap, 12/day, journal first), so a duplicate dispatch can never double-post.

## Deploy from GitHub (recommended: tokens stay in GitHub's encrypted secrets)
1. Add three repository secrets (Settings -> Secrets and variables -> Actions -> New repository secret):
   - `CLOUDFLARE_API_TOKEN`: Cloudflare -> My Profile -> API Tokens -> Create Token -> template **Edit Cloudflare Workers**.
   - `CLOUDFLARE_ACCOUNT_ID`: Cloudflare dashboard -> Workers & Pages -> right-hand side.
   - `SCHEDULER_GITHUB_TOKEN`: GitHub -> Settings -> Developer settings -> Fine-grained tokens: **only this repository**, **Actions: Read and write**.
2. Actions -> **Deploy scheduler (Cloudflare)** -> Run workflow. It checks the secrets, runs the Worker tests, deploys, and sets the Worker's `GH_TOKEN`.
3. Check: open `https://shipstack-scheduler.<your-subdomain>.workers.dev/status` (shows `due` and `paused`, dispatches nothing).

## Deploy by hand instead (once, about 5 minutes; free Cloudflare plan is enough)
```bash
cd worker && npm install
npx wrangler login
npx wrangler secret put GH_TOKEN     # paste the GitHub token when prompted
npx wrangler deploy
```
Watch the 5-minute ticks (`idle`, `busy` or `dispatched`) with `npx wrangler tail`. Never paste tokens into chat or commit them.

## Notes
- `/status` shows `hasToken` and the GitHub status code for the token (200 = accepted). If `hasToken` is false, add `GH_TOKEN` as a **Secret**
  (Cloudflare dashboard -> the Worker -> Settings -> Variables and Secrets, or the deploy workflow above).
- `keep_vars = true` in `wrangler.toml` stops a deploy from clearing variables added in the dashboard.

## Stop
Set `"paused": true` in `reels/shipstack/calendar.json`, or `npx wrangler delete`.

## Test (no network, no token)
```bash
cd worker && node --test test/plan.test.mjs
```
