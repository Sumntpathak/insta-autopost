# ShipStack Lab — editorial maths & physics reels

Each reel follows one teaching structure in 15 seconds:

1. **Question** (frame 1 already shows the headline and the figure — it is the hook)
2. **Live calculation** (the figure moves; equation + table update from the real computation)
3. **Answer** (one conclusion line, computed — never hard-coded)
4. **The rule** (`THE RULE · SAVE THIS`: headline, dek and equation swap to the takeaway)

Every number on screen comes from the simulation or calculation that drives the picture.

## Files

| File | Role |
|---|---|
| `__main__.py` | `python -m reels.shipstack.lab --reel <key>`; the `REELS` registry. |
| `style.py` | Palette, fonts, canvas/units (`P()` pixel→Manim, `fs()` cap height). |
| `layout.py` | **The page grid.** Fixed slots: masthead, headline (2 lines), dek, figure box, rule, equation, table, conclusion. Never place text by eye. |
| `figure.py` | skia raster figure for thousands of particles (drawn 1:1 into the figure box). |
| `sound.py` | SignalFlow voices (pluck, chord, pad) + `Timeline` placed from simulation events. |
| `pipeline.py` | Manim render + audio mux → MP4; `Clocked.timed()` keeps every reel at exactly 15 s. |
| `brachistochrone.py` | Nº 01 — straight vs cycloid (physics from `reels/experiments/track_race.py`). |
| `montecarlo_pi.py` | Nº 02 — Monte Carlo π, 20,000 dots, fixed seed. |

Fonts and palette live in `reels/shipstack/brand.py` and `reels/shipstack/fonts/` (SIL OFL).

## Design system

- Page: white `#FFFFFF`; ink `#0D1117`; muted `#667085`; hairlines `#E4E7EC`;
  one accent, indigo `#4F46E5` (the answer, the winner, the italic headline word).
- Type: headline Instrument Serif (84 px cap) with one `<i>accent</i>` word; kicker Inter
  SemiBold caps; numbers/equations LaTeX; handle JetBrains Mono.
- No cards, boxes or borders. Separate blocks with `layout.hairline()` and space only.
- Left/right edges are `layout.LEFT_X` / `layout.RIGHT_X` for everything, including figures
  (`layout.fit()` scales geometry to fill the figure box).
- No countdowns; the race/process starts within ~1 s.

## Add a new reel (checklist)

1. Copy `montecarlo_pi.py` (raster figure) or `brachistochrone.py` (vector figure).
2. Use only `layout` helpers: `masthead`, `headline`, `dek`, figure box, `hairline`,
   `equation`, `Table`, `conclusion`, `kicker_only`.
3. Drive everything from one `ValueTracker` clock; compute values, don't type them.
4. Build the soundtrack from the same event times (`sound.Timeline`).
5. Register it in `lab/__main__.REELS` and `reels/shipstack/__main__.FORMATS`, add its caption to
   `reels/shipstack/publish.CAPTIONS`, and add the key to the `reel` options in
   `.github/workflows/shipstack-reel.yml`.
6. Check alignment with `--grid`, then `python reels/verify.py` on the output.
7. Facts in headlines/deks/captions must be verifiable; prefer conclusions computed live.
