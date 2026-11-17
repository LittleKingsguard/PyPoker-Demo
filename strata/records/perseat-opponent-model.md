# Per-seat history transforms the opponent model — the table-level target was the bias · 2026-11-08

The user's diagnosis: at a six-player table any *given* opponent folds often, but "all opponents fold" is rare, so a
table-level target averages those into a fold-heavy marginal. Measured per-seat (the history filtered to the acting
seat) and with identity, 400 self-play hands per opponent (D-14).

**The training class mix confirms the bias and its cure:** the table-level set was **95.9 % calls** (D-121); the per-seat
set is **33.9 % fold / 50.4 % call / 15.7 % raise**.

| model | accuracy | balanced accuracy | folder | raiser-50-50 | raiser-83 | `fold-no-pair-or-face` |
|---|---|---|---|---|---|---|
| table-level (D-121) | — | — | lift **−0.135** | 0.000 | **−0.423** | −0.028 |
| **per-seat, no identity** | 0.702 | **0.730** | **+0.166** | **+0.127** | −0.013 | −0.212 |
| **per-seat + identity** | **0.814** | **0.821** | **+0.278** | 0.000 | **+0.064** | 0.000 |

## What changed

1. **It predicts raises now.** Table-level predicted **0 %** raises against a member that raises 36 % of the time;
   per-seat predicts 22–39 % and reaches **raise recall 0.62** (no identity) and **1.00** (with identity).
2. **The fold bias is gone.** Predictions track each member's own mix (`folder` 71/1/28 predicted against 70/1/28
   actual, with identity) instead of an 83–100 % fold default.
3. **Identity is worth a lot on top**: accuracy 0.702 → **0.814**, balanced 0.730 → **0.821**, and it removes the false
   raises against the scripted folder (39 % → 0 %).

## Limits

759 held-out rows, 400 hands per opponent, four opponents, self-play only — a directional result, not a calibrated
estimator. `fold-large-bet` and `fold-no-pair-or-better` were not in this run. But the previous record's conclusion —
that the model had learned its population's marginal — is now explained and fixed: **the target was wrong, not the
architecture.**

**Consequence for the integration test**: the frozen artefact used in D-119 was trained on the biased table-level target,
which is why its output was near-constant and why it destroyed the policy. A per-seat, identity-conditioned artefact is
the version worth wiring in.
