# ShipStack Arena — ball races and country battles

Same editorial page as the Lab (masthead, two-line serif headline with an italic accent,
dek, hairlines), with a larger figure and a 3x2 live scoreboard. White page, 60 fps, 15 s.

| File | Role |
|---|---|
| `page.py` | skia page drawing on the `brand.ARENA` grid (`Page`, `Type`), 60 fps `Encoder`. |
| `ring_physics.py` | Ring Escape physics (pymunk) + pacing search: clear winner inside 6.8–9.0 s, ≥ 0.5 s margin, ≥ 2 near misses. |
| `ring.py` | Ring Escape reel: live rim-bounce board; the winner is held outside the gap at the reveal. |
| `balloon.py` | Balloon Pop: game logic adapted from the MIT Pythonic Life scene; close race with a late lead change; 0.4x slow-motion run-up (labelled); live inflation board. |
| `strings.py` | Country String Battle: game logic adapted from the user-supplied `string_battle.py`, tuned slower with bigger balls and denser strings so cuts read as a fight; knockouts every ~2 s remove the country with the fewest strings until one survives; near full-width ring; one-row flag board with OUT markers. |

Rules: every result is the simulation's real outcome (seed search only *chooses* a seed with
good pacing, it never edits results); no countdown at the start; text sits on grid slots;
the conclusion line auto-shrinks to the text column. Sound comes from `lab/sound.py`.

New game checklist: physics module (deterministic, seeded) → reel class with `frame(sec)` and
`soundtrack(path)` using `Page` → register in `reels/shipstack/__main__.py`, caption in
`reels/shipstack/publish.py`, option in `.github/workflows/shipstack-reel.yml` → add a test.
