# @shipstack_ 30-day growth plan (20 Nov – 19 Dec 2026)

Owner: the agent (acting as CEO). Day 1 starts 20 Nov, 13:00 IST.
Goal: grow reach, saves, shares and followers from a global audience, with minimal manual effort.
Fixed constraints: 12 posts a day maximum, at least 60 minutes between posts (`reels/guard.py`).

## 1. Straight answers on the two big ideas

**"Post 10 posts at the same time."** Not doing this. The repo's own history shows bursts:
median gap of 2 minutes, ten posts in ten minutes. Posts in a burst compete with each other for
the same first test audience, and reach on the burst days (13–14 Nov) collapsed afterward
(8, 21, 6, 0, 3, 2 posts/day). The version of the idea that works is **waves**: three posts
spread across a few hours (60+ min apart), four waves a day. Instagram sees steady, frequent,
varied activity instead of one spike.

**"No interaction from me at all."** Almost. The pipeline can run by itself, but three things need
you, once:
1. Merge the branch `claude/epic-johnson-swuv6r` into `main` (the scheduler only reads `main`).
2. Keep the `META_TOKEN` secret valid. Meta tokens expire; renew before the date in section 7.
3. Approve the first skills pack and news sources (section 4). After that I run on defaults.

**Global viewership data.** I can't see Meta from the build environment. The read-only workflows
`instagram-audience.yml` (country/age split) and Reel campaign mode `insights` produce that data.
Until they run, the timing and content mix below are hypotheses, and the plan changes at the
day-7 review.

## 2. Positioning

One line: **"AI and automation, made simple. Save the skill."**
- Lane A: AI and automation news people save (tools, launches, price changes).
- Lane B: Skills: one reusable workflow per post (prompts, automations, Claude workflows).
- Lane C: Satisfying simulations (Balloon Pop etc.) as the reach engine. It is the proven performer.
- Lane D: Lab (physics/maths) as the signature, original, authority content.

## 3. Daily rhythm: 12 posts, 4 waves (IST), tuned for a global audience

| Wave | IST | Audience it reaches | Posts |
|---|---|---|---|
| 1 | 06:30, 07:40, 08:50 | India morning, Gulf, Europe evening | news card, skill post, balloon reel |
| 2 | 12:30, 13:40, 14:50 | India lunch, Europe morning | skill post, news card, lab/strings reel |
| 3 | 18:30, 19:40, 20:50 | India evening, Europe afternoon, US East morning | news card, skill post, ring/balloon reel |
| 4 | 23:30, 00:40, 01:50 | US East evening, US West afternoon | skill post, news card, balloon reel |

Mix per day: 4 news cards, 4 skill posts, 3 simulation reels, 1 Lab reel. Slots are adjusted at day 7 from the
actual audience countries.

Rules for every post: a hook in the first line, one idea, a clear "Save this" or "Share with a friend"
call to action, no repeated topic within 24 hours, and a different episode/seed each time so nothing repeats.

## 4. Content sources (so nothing is invented)

- **News:** only verified items with a named source and link, rendered by `news-single/` into 1080×1350
  cards. Each card is checked for `verified: true` before it can publish.
- **Skills:** built from things we actually run, so each is true and demonstrable:
  - how this repo posts on a schedule with GitHub Actions
  - journaling before publishing, to avoid double posts
  - turning one source into carousel, reel and caption
  - prompt and Claude workflows for research, summarising and checking facts
  - "I automated X, here are the 3 steps"
  Format: hook, 3 steps, result, save call to action. Target library: 120 skills for the month.
- **Simulations and Lab:** already automated through `calendar.json` (Balloon Pop, Ring Escape, Country
  Strings, Lab Nº 01/02), one new episode each.

## 5. Weekly schedule

### Week 1 (20–26 Nov): baseline and reset
- Day 1: merge the branch, run `instagram-audience.yml` and the insights export, reconcile the 16 stuck
  `publishing` records, rebuild `calendar.json` for 12 slots/day.
- Days 1–7: run all four lanes in equal proportion. Do not change the mix yet.
- Day 7 review: rank lanes by saves + shares per reach and by watch time (`reels/insights_report.py`);
  check audience countries; adjust wave times.

### Week 2 (27 Nov – 3 Dec): double down
- Give the top two lanes about 60% of slots. Cut the bottom lane to 1 post a day.
- Start two named series with fixed days (for example "Skill of the Day" at the same time daily),
  because repetition builds a returning audience.
- Add a pinned post and a bio with one clear promise.

### Week 3 (4–10 Dec): depth
- Turn the best five skills into carousels (more saves) and the best reels into a follow-up series.
- Test one variable at a time: hook style, post length, posting time. Keep what wins.
- Run the second review; remove any format with below-median saves and shares.

### Week 4 (11–19 Dec): scale and hand over
- Raise volume only if saves, shares and reach per post held steady for two weeks.
  Move to 18 per day first; 50 per day only after that, and only if the guard and metrics allow it.
- Generate the next 30-day calendar and the final report: what worked, what didn't, what to change.

## 6. Daily operating routine (automatic)

1. Scheduler checks every 5 minutes; posts the due slot through the guard (gap, cap, journal).
2. 23:17 IST: insights snapshot and design report.
3. Failures: a slot missed by more than 2 hours is skipped, not posted late, and logged.
4. Weekly: the review above, and `calendar.json` is updated for the next 7 days.

## 7. Risks and what I'll watch

| Risk | Control |
|---|---|
| Reach drops from posting volume | Weekly reach-per-post check; fall back to 6/day if it falls for 3 days in a row |
| Repetitive content looks like spam | Unique episode per post; no topic repeats within 24 h; vary lanes in each wave |
| Wrong or unverified news | Only `verified: true` items with source and link publish |
| Token expiry | Renew `META_TOKEN` before it lapses; the daily check calls `check_account` |
| Stuck or double posts | Journal before publish; ambiguous states are reconciled by hand, never retried |
| Meta policy limits | Stay far below the 24-hour API limit (to be confirmed in the Meta docs) |
| Runner cost and time | Pre-render the heavy reels in nightly batches; news/skill cards render in seconds |

## 8. Success measures at day 30

- 12 posts a day delivered on 90%+ of days.
- Saves + shares per 1,000 reach up versus the week-1 baseline.
- Top three formats identified, and a documented plan for the next month.
- Follower growth, tracked per lane as follows per 1,000 reached.
