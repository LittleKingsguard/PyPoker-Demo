# The encoding bites under the risk-averse utility · measured 2026-11-08

The sharper half of D-51's comparison: `R3 card-tokens` against `R1 flat-numeric`, six seats, 100-chip
stacks, the mixed pool `pool-8386c3ef83ae48b2`, **15,000 hands × seeds 0, 1, 2**, `stack-shortfall` on both
arms, ties excluded, the encoding the only variable (D-14). Wall clock 8,115 s and 8,314 s.

| arm | seed | decisions | fold | chips/hand [95 %] |
|---|---|---|---|---|
| flat-numeric | 0 / 1 / 2 | 2,386 / 2,201 / 2,386 | **78.33 / 87.01 / 77.58 %** | −1.922 / −0.480 / −1.188 ± 1.7–2.1 |
| **card-tokens** | 0 / 1 / 2 | 2,142 / 2,107 / 2,130 | **91.83 / 93.45 / 92.25 %** | −0.939 / −0.110 / −0.509 ± 0.05–0.81 |

## Two levers, in order of size

**The utility is the big one**, reproduced exactly: `net-chips` at six seats folds **0 %** (D-34, D-44,
D-52); `stack-shortfall` folds **78–93 %**.

**The encoding is the second, and here it finally separates** (D-6):

- **More folding at every seed**: 91.8 / 93.5 / 92.3 % against 78.3 / 87.0 / 77.6 % — a 5–15 point gap, and
  far steadier across seeds (the token arm varies 1.6 points, the flat arm 9.4).
- **Smaller losses at every seed**: −0.94 against −1.92, −0.11 against −0.48, −0.51 against −1.19.
- **Far tighter payoffs**: ±0.25, ±0.81, ±0.05 against ±1.70, ±1.47, ±2.05. A folder that folds 92 % of its
  decisions ends hands fast, and its outcome varies little.

## What it does not establish

- **Neither arm wins.** Every chip rate is negative, "less negative" is not a gain, and the arms' intervals
  still overlap at all three seeds, so no chip difference is resolvable.
- **Folding 92 % is a behaviour, not an edge** — plausibly a cheap way to lose slowly against a pool that
  bets.
- The effect is **conditional on the utility**: at `net-chips` the same comparison showed no chip
  difference at all (D-52), so the encoding needs a policy distribution to act on.

## Reading for the talk

Two factors on one table: **the reward decides what kind of agent it is** (stealer at 0 % folds, folder at
78–93 %), and **the encoding decides how hard and how consistently it folds** (78–87 % → 92–93 %, a third of
the variance). That is attributable, reproducible and the first encoding claim this project can make.
