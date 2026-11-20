# ShipStack brand system (v1, 20 Nov 2026)

Goal: be instantly recognisable and trusted, the way big curated pages are, without copying anyone.
What big pages actually do well: one clear promise, one repeatable look, a fast and steady cadence,
and credit for their sources. Trust is earned by being right and showing the source every time,
not by looking big.

## 1. Promise and positioning

**ShipStack: the AI and automation briefing you can save.**
Three words for the account: **Know. Save. Ship.**
- Know: verified AI and tech news, one line at a time.
- Save: a reusable skill or workflow in every skills post.
- Ship: proof it works, shown by real builds and the simulations the account is known for.

Why this: the current bio ("You dream it. We code it", DMs for web and apps) sells agency work, while the
feed shows balloon and ball simulations. A visitor can't tell what the account is, so they don't follow.

## 2. Profile (apply in the app; the API cannot edit these)

- **Name field:** `ShipStack | AI & Automation` (searchable keywords go in the name field).
- **Bio:**
  ```
  AI & automation, made simple.
  🔖 Daily skills worth saving
  📰 Verified AI news, always sourced
  ⚡ Built with code, not stock footage
  ```
- **Link:** one page that explains the account and links the best skills.
- **Highlights:** Start here · Skills · News · Simulations.
- **Pinned posts (3):** a "Start here" post, the best skill, the best simulation.

## 3. Visual identity: ShipStack Studio (`reels/shipstack/studio/`)

One design for all three series, so nothing is redesigned per post. Every post is a page in the same
developer workspace:
- **Header:** `>_` mark, then a file-path breadcrumb naming the series and episode
  (`shipstack / news / 19-nov`, `shipstack / automation / #0001`, `shipstack / dsa / #0001`), then the series tag.
- **Surface:** editor dark `#0D1117`, panels `#161B22`, borders `#30363D`, text `#E6EDF3`, meta `#8B949E`.
- **One accent:** cyan `#22D3EE` for the key phrase, highlights and the logo. Series tags: News red,
  AI Automation violet, DSA green (outline pills, always top-right).
- **Type:** Inter (headlines 800, body 500–600) and JetBrains Mono (breadcrumb, labels, code).
- **Footer:** one call to action on the left, `@shipstack_` on the right.

| Series | Template | Input needed per post |
|---|---|---|
| News | `cards.news()` 1080×1350 | headline, deck, source, date, photo + credit |
| AI Automation | `cards.automation()` 1080×1350 | title, 3 steps, result, tools |
| DSA (1200-problem series) | `dsa.render()` reel 1080×1920, 15 s | a solution function + a spec in `studio/problems.py` |

The DSA reel shows the real code, a moving line highlight, the array with gliding pointers, a watch panel
that flashes changed variables, one-line narration, and an end card with the return value, complexity and
the next episode. The trace comes from actually running the code, so it can't show a wrong step.

## 4. Voice

Short, plain and specific. Numbers over adjectives. No hype words, no clickbait the post doesn't pay off.
- Hook (line 1): the claim or the question, under 12 words.
- Body: what happened or what to do, in 2–3 lines.
- Close: one action. "Save this for later." or "Follow for the next problem."

## 5. Series

| Series | What | Cadence (12/day cap) |
|---|---|---|
| **News** | Verified AI and tech news, sourced | 4 a day |
| **AI Automation** | One reusable workflow, 3 steps, tested | 4 a day |
| **DSA** | One famous problem per episode, debugged line by line | 4 a day |

## 6. Credibility rules

1. Every news post names its source and date. No source, no post.
2. Only `verified: true` news items publish.
3. Corrections are public and pinned for 24 hours.
4. No invented claims, numbers, testimonials or screenshots.
5. Images are licensed or original and credited; AI-generated images are labelled.
6. Automation workflows are run once before posting; the result shown is what really happened.
7. DSA problems are described in our own words, with our own code (no copied problem statements).
