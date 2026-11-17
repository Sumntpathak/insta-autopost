# ShipStack quality experiment v1

Status: experimental branch only. No publishing or changes to main.

## Verified baseline (2026-11-17)
- `reels/render.mjs`: Matter.js simulation, Canvas renderer, 30 FPS, 450 frames.
- `reels/soundtrack.mjs`: original 48 kHz stereo procedural soundtrack, collision-triggered tones, 15 seconds.
- `reels/verify.py`: H.264, AAC, 1080×1920, 15 s, 30 FPS, audible-audio validation.
- `.github/workflows/reels.yml`: 10-minute scheduled checks and insights workflow. Publishing has side effects and must not be used for experiment validation.

## Decision
Keep existing renderer and soundtrack as baseline. Do not introduce heavyweight Manim or SignalFlow into the production workflow until isolated benchmarks prove added value.

## Experiment A: math challenge
- Produce an original 15-second 9:16 challenge: predict which of two competing paths reaches the target first.
- 0–2 s: strong question and two clearly distinct candidates.
- 2–12 s: deterministic simulation with a readable progress indicator.
- 12–15 s: reveal and explanation, with no misleading claim.
- Export H.264/AAC, 1080×1920, 30 FPS, exactly 450 frames.

## Experiment B: reactive audio
- Capture event times from the simulation rather than assigning random impact timing.
- Map event strength to note velocity and timbre; cap simultaneous events and apply a minimum 100 ms separation to avoid noise.
- Keep loudness consistent and retain existing audio verification.
- Evaluate SignalFlow only if existing synthesizer cannot deliver this.

## Experiment C: measurement
- Record post ID, publish time, format, creative version, views, reach, likes, comments, shares, saves, follows and watch-time metrics *when the API provides them*.
- Never invent missing API metrics. Track 24-hour and 72-hour snapshots when available.
- Compare shares/reach, follows/reach and watch time, not only raw views.
- No Instagram API write calls during analytics experiments.

## Acceptance criteria
1. Preview generated and passes `reels/verify.py`.
2. Original source and dependencies documented, including license review.
3. No workflow changes to `main`, no publish calls, no changes to `reels/state.json`.
4. Preview reviewed before any production merge or Instagram post.

## Immediate next steps
1. Implement an isolated renderer under `reels/experiments/`.
2. Run deterministic rendering and ffprobe verification in a nonpublishing test workflow.
3. Inspect preview and tune audio.
4. Prepare analytics comparison and review results before rollout.
