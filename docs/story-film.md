# "We Ship": the ShipStack story film

The first post of the relaunch: a 15-second animated reel that says who ShipStack is and what
the account posts from now on. Built in Remotion (`film/`), music composed in code (`film/music.py`).

## 1. Pitch

**Logline.** Everyone has an idea. Most people stop at "where do I start?". ShipStack is the
account that gets you from idea to shipped: AI news you can trust, automations you can copy, and
1,200 DSA problems debugged line by line.

**Why this film first.** The account has 22 followers and a feed of mixed experiments. A new visitor
needs one post that explains the new account in 15 seconds. Pinned to the top of the grid, it becomes
the trailer for everything after it.

**Tone.** Calm, confident, technical. A terminal, not a hype reel. No stock footage, no fake UI from
other platforms. Every frame uses the Studio design (Geist, dark editor, one cyan accent), so the film
looks exactly like the posts that follow it.

## 2. Screenplay (15 s, 30 fps, 450 frames, 120 BPM: 1 beat = 15 frames)

| # | Time | Frames | Picture | Words on screen | Sound |
|---|---|---|---|---|---|
| 1 | 0.0–2.0 s | 0–59 | Black editor. A terminal prompt types `$ ship my-idea`. A beat later the reply appears in red: `error: where do I start?` | (typed) | Soft pad, one key click per letter |
| 2 | 2.0–3.5 s | 60–104 | Hard cut to giant type, one word per beat: **Learn it.** **Build it.** **Ship it.** (the last in cyan) | Learn it. / Build it. / Ship it. | Kick on each word |
| 3 | 3.5–6.0 s | 105–179 | The logo builds: the hull rises, the `>` sail snaps in, the wordmark types `shipstack` and the cyan cursor blinks | shipstack_ | Bass drop at 4.0 s, arpeggio starts |
| 4a | 6.0–8.2 s | 180–244 | NEWS: a news card slides up; the key figure counts up | AI news. Verified. Every source shown. | Accent hit on the cut |
| 4b | 8.2–10.3 s | 245–309 | AI AUTOMATION: 01, 02, 03 tick in one per beat | Automations you can copy. | Accent hit |
| 4c | 10.3–12.5 s | 310–374 | DSA: code with the debugger highlight stepping down; episode counter rolls 0001 → 1200 | 1,200 DSA problems. Debugged line by line. | Accent hit |
| 5 | 12.5–15.0 s | 375–449 | End card: the logo, the three words, the handle | Know. Save. Ship. / Follow @shipstack_ | Final chord, ring out |

**Caption (post copy).**
```
We ship.

From today, ShipStack posts three things:
→ AI news, verified, every source shown
→ AI automations you can copy
→ 1,200 DSA problems, debugged line by line

Follow so you don't miss #0001.

#ai #automation #dsa #coding #leetcode #programming
```

## 3. Music (original, composed in code)

`film/music.py` writes `film/public/bgm.wav`, so there is nothing to license.
- 120 BPM, A minor, 15 s: pad (A–F–C–G), kick, sub bass, 16th-note arpeggio.
- **0–4 s:** pad only, a key click per typed letter, kicks on the three words.
- **4 s:** the drop: kick, bass and arpeggio together as the logo lands.
- **6.0 / 8.2 / 10.3 s:** a short accent hit on each series cut.
- **12.5 s:** the groove stops; the final A-minor chord rings out under the end card.

## 4. Built with the Remotion agent skills

The film follows Remotion's official agent skills (github.com/remotion-dev/skills, v4.0.545):
- every animation is an inline `interpolate()` with `Easing.spring` / `Easing.bezier`, using separate
  `translate` / `scale` properties, with `output: 'perceptual-scale'` on scale;
- all timing comes from `useVideoConfig().fps` (one beat = fps / 2 at 120 BPM);
- consecutive scenes are named `TransitionSeries.Sequence`s, with a custom slide-up presentation between
  the three series (scene lengths include the overlap, so the total stays 450 frames and cuts stay on the beat);
- music through `Audio` from `@remotion/media`; Geist loaded locally with `@remotion/fonts`;
- video layout rules: 80 px side / 100 px top-bottom safe area, headlines at least 84 px, supporting text at least 44 px.

## 4. Director's notes

- **Motion:** every entrance is a spring (no linear slides). Text enters 24 px below its rest
  position and settles; nothing bounces more than once.
- **Cuts land on beats.** Every scene boundary is a multiple of 15 frames.
- **Readability:** the largest words are at least 120 px; nothing important sits in the bottom
  320 px (Instagram's caption overlay) or the top 160 px.
- **One accent.** Cyan is used only for the word or number that matters in each shot.
- **First frame matters:** frame 0 already shows the prompt, so the auto-generated cover isn't black.
- **No fake platform UI** (no Instagram buttons, no verification badges, no X/Twitter chrome).

## 5. How we post it

1. **Before posting:** apply the new profile picture (`reels/shipstack/studio/samples/avatar-1080.png`),
   name `ShipStack | AI & Automation`, and the bio from `docs/brand-shipstack.md`.
2. **Archive the old grid** (in the app: ⋯ → Archive) so a visitor sees only the new identity.
   This hides posts; it does not delete them.
3. **Render and check:** `cd film && npm run music && npm run render`, then `python reels/verify.py film/out/shipstack-story.mp4`.
4. **Publish** through the guarded publisher (one post, the guard's 60-minute gap applies), with the
   caption above. Best slot: 19:10 IST (India evening, Europe afternoon).
5. **Pin it** to the top of the profile (in the app: ⋯ → Pin to your profile). The API can't pin.
6. **Next day:** start the three series at the planned cadence. DSA #0001 Two Sum goes first, because
   the film promises it.
7. **Measure** at 24 and 72 hours: views, average watch time, follows from the reel. If watch time is
   under 5 s, recut the opening (scene 1 is the risk).
