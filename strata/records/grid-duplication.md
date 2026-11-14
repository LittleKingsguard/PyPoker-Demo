# The grid ran twice, and both passes agree · reconciliation 2026-11-08

Two concurrent L1 passes ran the same 12-cell grid on the same pool, seeds and budget — L0's scheduling
error: the corrected brief was launched before the earlier pass had stopped (D-64). Both returned `PASS`
with different summary numbers, so the artefacts were reconciled before either set was published (D-14).

## They agree at seed level

Seed 0 of `net-masked-flat`:

| pass | decisions | raise-minimum | check-call |
|---|---|---|---|
| earlier | 3,935 | 61.7 % | 38.35 % |
| later | 3,934 | 61.5 % | 38.5 % |

Both match the pre-change record, as they must (D-6): the encoder's output is **provably identical** before and
after the change on real readouts — all four shape × encoding combinations, maximum difference **0.0**,
checked by importing the pre-change package from `git archive 0e030e1` — and the dense backend was
untouched, only the token path gaining the `tanh` squash.

## Why the summaries differed

One pass **pooled census shares across seeds whose policies differ**: seed 0 raise-minimum 61.5 %,
seed 1 raise-all-in 57.9 % with 39.1 % folding, seed 2 check-call 100 %. A pooled census of three different
attractors is not a policy — the trap `attractor-sweep.md` recorded, re-learned here.

They also differ on the band refusals: three `LearningDiverged` in one pass, two in the other, and the
later pass reports both completing on an identical retry — an intermittency, not a cell property.

## What stands

**The utility is the only axis that revives the trunk.** Every `net-chips` cell is a constant function (0
active units in the second hidden layer, one score vector over hundreds to thousands of observations,
‖hidden‖ 0.00 against a bias of 10–57); every `stack-shortfall` cell is alive (19–25 active units per layer,
distinct score vectors equal to distinct observations). The encoding modulates only where a trunk lives;
`double-q` and `reveal-counterfactual` sit inside the seed spread.

**Per-seed tables are the form of record; pooled census shares are not.** The duplication cost two grids of
compute, not a wrong conclusion.
