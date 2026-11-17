# Figures for the deck

Eight SVGs plus a demo-data pack, generated from the project's records. **Nothing here is invented** — every number
carries a decision-row provenance in `manifest.json` and `demo-data.json`.

## How to use them in the single-file deck

The deck is one self-contained `index.html` (D-118) with **no network dependency**, so a figure must be **inlined**, not
linked:

- **Inline the SVG markup**: open the `.svg`, paste its `<svg>…</svg>` element into the slide. The files are 9–17 KB and
  already use `transparent` backgrounds, so they sit on the felt without a plate behind them.
- **Palette**: designed for a dark card — gold `#d9a441`, emerald `#4fbf8b`, crimson `#d4553f`, slate `#8a8378`,
  sky `#6fa8dc`, text `#f2e8d5`. If the deck's palette differs, re-run the generator with edited colours rather than
  recolouring by hand.
- **Regenerate**: `python figures/make_figures.py` (matplotlib 3.11.2 is in `.venv`). Edit the values in the script — they
  are annotated with the decision row each block comes from.

## The figures

| file | what it shows | row |
|---|---|---|
| `signal-by-street.svg` | how much of a six-way outcome the cards explain: 2.4 % preflop → 52.8 % river | D-83, D-86, D-93 |
| `representation-ladder.svg` | five encodings on one target; attention + positions wins at 40 % | D-84…D-96 |
| `card-model-convergence.svg` | the curve that showed every early figure was a snapshot | D-85, D-93 |
| `battery-error.svg` | 40 % pooled variance beside **2.7 % predicted for a 91.8 % hand** | D-91, D-94, D-95 |
| `chips-ladder.svg` | the exploration floor: fold-everything → **+11.3 / +12.9 chips per hand** | D-72, D-105, D-125, D-126 |
| `trunk-health.svg` | a network with **0 of 50 units alive** under the 600-scale reward | D-60, D-67, D-108 |
| `monotonicity.svg` | reads cards, does not rank them — suited junk shoved while a small pair folds | D-116, D-127 |
| `padding.svg` | **88 % of the input was the token for "nothing here"** | D-78, D-79, D-110 |
| `network-dead.svg` | the network under the 600-scale reward: **0 of 50 units firing**, both hidden layers | D-60, D-67, D-108 |
| `network-live.svg` | the same network with the normalised reward: **23 and 24 of 50 firing**, densely wired | D-67, D-108 |
| `network-compare.svg` | the two side by side, for one slide | D-108 |

## Demo data

`demo-data.json` holds the same numbers as structured blocks (chips with CIs, the street ladder, the battery, trunk
health, the monotonicity ladder, the policy's behaviour on extreme hands, the opponent-model comparison, the padding
split) so a slide can build a table or animate a value without re-deriving anything.

## Suggested slide pairings

1. **"The signal arrives with the board"** → `signal-by-street`, with the preflop 2.4 % as the punchline.
2. **"Every representation, measured"** → `representation-ladder` (+ `card-model-convergence` beside it to make the
   snapshot point).
3. **"The aggregate lied"** → `battery-error` alone, large.
4. **"What fixed it"** → `chips-ladder`, then `trunk-health` and `padding` as the two defects it took to get there.
5. **"What it still cannot do"** → `monotonicity`, closing the talk on an honest limit.

`network-compare.svg` works as the *cause* slide before `chips-ladder`: the dead trunk is why the earlier policy could
not use any input, and the exploration floor is why it could not escape once it could.

## Regenerating the network diagrams

`python figures/make_network.py` — it reads the parameters straight out of the two checkpoints
(`.probe/dead/dead-ckpt/...` and `/tmp/foldloop/high/...`), measures each unit's firing rate on 300 real observations,
and draws hollow rings for dead units, lit nodes for firing ones, with edges only between units that fire. The counts in
the caption are the measured ones, printed by the script.
