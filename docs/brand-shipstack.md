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

## 3. Visual identity (extends `reels/shipstack/brand.py`)

Keep the existing system and make it stricter, so every post is recognisable without the handle:
- **Colours:** paper white `#FFFFFF`, ink `#0D1117`, one accent indigo `#4F46E5`. No other accent.
- **Type:** Instrument Serif for headlines, Inter for body, JetBrains Mono for code and numbers.
- **News card (1080×1350):** top-left tag in indigo (`AI`, `AUTOMATION`, `DEALS`), a headline of at most 12 words,
  a one-line deck, a thin rule, then the source strip (`Source: Reuters · 19 Nov`). The mark is small and fixed in one corner.
- **Skill card/reel:** the skill's name as a verb phrase ("Automate your weekly report"), three numbered steps,
  one before-and-after result, and a "Save this" footer.
- **Simulations:** keep the Arena look. Always end on the result with the handle visible.
- **Rule:** never more than two type sizes on a card, and never a face or logo that is not ours or licensed.

## 4. Voice

Short, plain and specific. Numbers over adjectives. No hype words ("insane", "game-changer"), no clickbait that
the post doesn't pay off.
- Hook (line 1): the claim or the question, under 12 words.
- Body: what happened or what to do, in 2–3 lines.
- Close: one action. "Save this for later." or "Send this to someone who still does this by hand."

## 5. Series (names people can follow)

| Series | What | Cadence |
|---|---|---|
| **ShipStack Brief** | Verified AI and tech news card | 4 a day |
| **Skill of the Day** | One reusable workflow, 3 steps | 4 a day |
| **Pick One** | Balloon, ring and string simulations | 3 a day |
| **Lab** | Physics and maths, the signature original | 1 a day |

Each series has a fixed name, tag and layout, so a viewer knows what they are getting before reading.

## 6. Credibility rules (the "make people believe it" part)

1. **Every news card names its source and date.** No source, no post.
2. **Only `verified: true` items publish** (the news pipeline already enforces this field).
3. **Corrections are public.** If a fact is wrong, post a correction and pin it for 24 hours.
4. **No invented claims.** No fake numbers, fake testimonials, fake screenshots or follower counts.
5. **Credit images and clips.** Use licensed or original media, and show the credit on the card.
6. **Skills must be tested.** Each skill has been run once, and the result in the post is what really happened.
7. **Disclose AI.** If a visual is AI-generated, say so in the caption.

## 7. What changes first (in order)

1. Apply the new name, bio, link, highlights and three pinned posts.
2. Redesign the news card to the layout in section 3 (the existing `news-single/render.py` is the base).
3. Write the first 20 skills and queue them under "Skill of the Day".
4. Retire the carousels in their current form (average 0.6 likes) and the lowest-performing simulation formats.
5. Re-measure after 7 days, using saves and shares per reach once insights are available.
