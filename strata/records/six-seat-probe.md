# Does more seats make folding — and therefore bluffing — pay? Probe · 2026-11-07

Probe harness, pokerkit directly, no module changes, 500 hands per cell (D-14). **One row of this
probe is void**: my `folder-pair` policy compared `entry.label` to `0`, but the label is an enum
string (`"High card"`), so it never folded and its cells reproduced `always-call` exactly — verified by
counting folds (zero). The shipped `fold-no-pair-or-better` uses the engine's integer `hand_class` and
does fold (9.7 % vs `random`, measured in D-21), so the product is sound and the probe was wrong.

Valid evidence therefore rests on `folder-face` alone (preflop folding, which does fire):

| cell | raiser's chips/hand | the other seat |
|---|---|---|
| 2 seats: raiser vs caller | +0.11 ± 1.23 / −0.73 ± 1.22 | −0.11 / +0.73 |
| 2 seats: raiser vs **folder-face** | **−0.29 ± 0.93 / −0.91 ± 0.95** | +0.29 / +0.91 |
| 2 seats: folder-face vs caller | −0.10 ± 0.17 | +0.10 |
| 6 seats: raiser + 5 callers | −0.03 ± 2.73 | +1.96 ± 2.88 / −2.63 ± 2.51 |
| 6 seats: raiser + 5 folder-face | −1.89 ± 1.97 | +0.73 ± 1.81 / −1.40 ± 1.52 |

## What the numbers do and do not say

- **Directionally, aggression does worse against a folder** in both seed blocks — the raiser's chip
  result falls by 0.41 and 0.18 chips/hand against `folder-face` relative to a caller.
- **But it is not resolved**: the intervals are ±0.9 to ±1.2 and overlap, and the differences sit
  inside that noise. The honest statement is "slightly worse, unresolved", not "worse".
- **Six seats stays negative and noisier**: the raiser against five folders measures −1.89 ± 1.97,
  not better than against five callers, with a six-times wider interval — a six-way bluff needs five
  folds and the payoff does not cover it *by direction*, unresolved in magnitude.
- **Six seats destroys resolution regardless of premise**: two seats holding an *identical* policy
  measured +1.96 and −2.63 chips/hand — position, not strategy. Resolving a 0.3-chip edge at that
  variance needs ≈40,000 hands per cell, against 500 here and 120 in a live table.

## Disposition

The hypothesis "more simultaneous opponents make bluffing pay" is **not supported**: the one rule
that fires measures the raiser slightly worse against it, six seats does not improve that, and the
measurement power at six seats is unusable. D-23 records that six-player seating is not adopted for
Phase 1 (D-22) and that the untried lever with a mechanism behind it is the game's structure, not the
table's size (D-4, D-6).
