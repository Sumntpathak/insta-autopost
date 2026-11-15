# ShipStack global content team

Nine coordinated roles run through one journal and one publishing queue. The target is **100 posts total per UTC day across Instagram and Facebook**, for seven live days: **700 deliveries**, not 1,400. Scheduling does not bypass Meta limits or make this chat a continuously running agent.

Positioning: **smart tools and sharper thinking for a global audience of creators and young professionals**. Launch language is plain English. Cover Asia-Pacific (including India), Europe, Africa, the Middle East and the Americas with evenly spread UTC slots; this is time-zone coverage, not a claim to reach every person or language.

## Operating team

| Role | Deliverable | Why it exists |
|---|---|---|
| CEO / growth lead | Daily priorities and keep/improve/stop review | Keeps audience and advertiser fit coherent |
| Analytics agent | Historical inventory, daily metrics, coverage and next-day allocation | Turns real outcomes into measurable decisions |
| News researcher | Primary-source headlines, dates and URLs | Finds fresh, relevant material |
| Editor / search specialist | Original global-English copy, searchable titles and captions | Makes the content useful and discoverable |
| Carousel designer | Clear-glass 4:5 JPEGs | Produces consistent, readable feed content |
| 3D motion director | Brain-game MP4s with original music | Gives ShipStack a recognizable entertainment format |
| Quality reviewer | Pass/hold and reasons | Stops unsupported, stale or unreadable posts |
| Publishing operator | Due-slot delivery and durable results | Coordinates both platforms and retries safely |
| Community agent | Contextual eligible replies and review queue | Responds without duplicate loops or unsolicited DMs |

Role instructions and source references are in `agents/`. These are implemented workers and instructions, not nine separately deployed persistent AI personas. GitHub role templates were evaluated for fit; their advertised success targets are not evidence of ShipStack performance. The existing local/Pillow/Blender engine is retained; Remotion skills are a reference, not a newly installed rendering dependency.

## Seven-day experiment

- Days 1–2: 50 Instagram + 50 Facebook deliveries each day.
- After 48 live hours: compare pilot posts at least 24 hours old. Require at least five measured posts per platform with reach >=100 before adjusting on median shares/reach. Limit a daily allocation change to ten slots and retain at least thirty slots per platform. Freeze each day's allocation when it begins.
- Proposed format budget: 40 reels, 35 carousels, 25 single images. Those are targets, not prewritten or already published assets. A carousel counts as one delivery. Posting the same asset to two platforms counts as two deliveries.
- Format adjustments also wait for mature samples, compare share rates within each platform and move at most five slots per day while keeping at least ten of each format. A missing comparable sample leaves the mix unchanged.
- Spread 100 slots at 864-second intervals over each UTC day. The existing GitHub Actions workflow checks the queue every ten minutes and can process up to six due items. GitHub can delay/skip scheduled jobs, so this is not an exact-time SLA. Items more than two hours late are not dumped into the feed.
- Fresh news is capped at twenty daily items. Missing verified news is not replaced with invented headlines. The optional editorial worker can create source-backed evergreen content. Production shortfalls are reported, not counted as successes.
- Day 7: report reliability, quality holds, actual output, platform/format performance, audience-country coverage where exposed, follows where exposed, render/model costs where measured, and sponsorship readiness. Do not claim that a week proves long-term growth or revenue.

## What is implemented

`planner.py` generates the 700 destination slots. `runner.py` coordinates research, drafting, quality checks, rendering, public asset hosting, account checks, publication and journaling. Instagram and Facebook have separate credentials/adapters. Existing legacy schedules hand over only while the enabled seven-day pilot is actually active; prior histories are preserved.

`analytics.py` follows media pagination beyond the old 100-item cap, collects supported post counters, attempts audience and follower counts, and writes a CEO review. A successful account check is not proof that media processing, insights, comments or messaging scopes work. The latest observed legacy reel failure was HTTP 403 during container status polling, after media creation. Its root cause has not been established.

Each baseline also exports a readable `ceo-review.md` and `historical-metrics.csv` with missing values left blank. These reports stay in workflow artifacts, not in the public source tree.

Facebook Reels have separate post and video IDs. The collector also reads video-level counters and watch time where available. Facebook unique media viewers remain a separately labeled audience measure; three-second video viewers are not presented as reach. Empty audience-demographic responses are marked unavailable.

`editor.py` optionally uses the OpenAI Responses API for drafting and a separate model verification call. It needs an API key and a Responses-compatible model configured by the operator. The small seed editorial library alone is insufficient for a full 100/day pilot. Model checks reduce risk but do not guarantee factual correctness; failed source fetches and reviews hold the item. No paid model calls were made during local development.

## Commands

```bash
python -m pip install 'Pillow>=11,<14'
python -m unittest discover -s team/tests -v
python -m team.cli plan                      # 700 proposed destination slots, no posting
python -m team.cli status
python -m team.cli check                     # read-only account and IG quota checks
python -m team.cli baseline                  # API-returned history + CEO report
python -m team.cli preview                   # inspect due briefs; may use configured editorial model
python -m team.cli cycle --live              # processes due slots only after enable + activation
python -m team.cli community
```

## Connect and launch

The repository already uses `META_TOKEN`, `IG_USER_ID`, `FB_PAGE_TOKEN` and `FB_PAGE_ID`. The new workflow reuses those secrets; it does not read or print their values. Optional editorial generation needs `OPENAI_API_KEY` as an Actions secret and `SHIPSTACK_MODEL` as an Actions variable. Model usage may incur charges on that API account. Existing credentials cannot be assumed to include insights, comments or messaging permissions.

The new workflow runs tests, a readiness check, a 700-slot planning artifact and the historical review when this integration reaches `main`. It does not start the pilot automatically. Scheduled work stays idle while disabled or outside the pilot window.

Before launch: resolve account/container permission problems, verify media publication on both destinations, verify editorial capacity and comment permissions, and review `readiness.json` and `ceo-review.json`. Then commit `enabled: true` in `team/config.json` and run **ShipStack global content team → activate** with a future ISO timestamp such as `2026-12-01T00:00:00+00:00`. The example is not a selected start date. Activation checks account identity and quota and preserves the existing state. To pause, commit `enabled: false`.

News/source access and optional API credentials are real runtime dependencies. A held item, unavailable metric or exhausted quota remains visible. A plan with 700 slots does not mean 700 publishable assets exist or 700 posts were delivered.

## Community and inbox

The scheduled worker polls comments on rotating batches of newly published pilot posts, with per-comment deduplication. This is not an immediate guarantee of coverage for every historic post or comment. Unsupported-language, sensitive and uncertain comments are held; no generic answer is invented.

User-initiated incoming messages use the separate signed webhook app in `webhook.py`. GitHub Actions cannot host a public webhook. Deploy the WSGI app and worker on an HTTPS host with a shared persistent private volume, install `gunicorn`, register the callback in the Meta app and grant messaging scopes. Configure `META_APP_SECRET`, `META_WEBHOOK_VERIFY_TOKEN` and `SHIPSTACK_INBOX_DB`, plus the platform credentials. Use the enabled/activated pilot configuration on that service. It is written but not deployed or subscribed by this change.

```bash
gunicorn --bind 0.0.0.0:8080 team.webhook:application
python -m team.webhook
```

The webhook verifies signatures, deduplicates message IDs, ignores echoes, checks destination identity, and sends supported template replies only to incoming messages within 24 hours. Processed message bodies are erased; reviewable/uncertain messages stay on private storage for operator review. Configure retention and encrypted storage on the host. The private inbox is excluded from Git and workflow artifacts. Likes/follows alone never trigger DMs. Human-agent exceptions are not used for automation. No brand outreach, paid ads, mass subscription messages or unsolicited promotions are enabled.

## Research references

- [Agency Agents](https://github.com/msitarzewski/agency-agents): role candidates; selected original files are linked in `agents/`.
- [Marketing Skills](https://github.com/coreyhaines31/marketingskills): alternative social/content/analytics reference set identified during research, not installed.
- [Meta content publishing](https://developers.facebook.com/documentation/instagram-platform/content-publishing): account requirements, containers, quota checks and carousel publishing. Check the live quota; scheduling does not bypass it.
- [Meta insights reference](https://developers.facebook.com/docs/graph-api/reference/shadow-ig-user/insights/): metrics are permission-, account-, age- and format-dependent.
- [Instagram webhooks](https://developers.facebook.com/docs/graph-api/webhooks/getting-started/webhooks-for-instagram/): comment and messaging integrations need their own app configuration.
- [Meta system cards](https://ai.meta.com/blog/how-ai-powers-experiences-facebook-instagram-system-cards/): Instagram has separate ranking surfaces; a website SEO prompt is not a universal Instagram growth strategy.
- [OpenAI Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create): optional structured drafting and model review.
