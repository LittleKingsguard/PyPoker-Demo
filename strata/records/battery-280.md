# Battery at epoch 280: exact at the poles, badly compressed between them · 2026-11-08

The extremes battery (D-91) re-scored against the **epoch-280** checkpoint of the long run — identified by its
held-out figures matching that row exactly (35.21 / 13.70 / 44.66 / 47.08 %), so the label is measured, not assumed
(D-14).

| scenario | **MC truth** | model | error |
|---|---|---|---|
| quad aces | **100.00 %** | **99.95 %** | **−0.05** |
| nut flush | **100.00 %** | **99.91 %** | **−0.09** |
| ace-high straight | **97.77 %** | 46.66 % | **−51.11** |
| trip aces | **91.84 %** | 69.80 % | −22.04 |
| pair of kings, dry board | **45.07 %** | **4.24 %** | **−40.83** |
| 2-3 · 2-7 junk (no pair/draw) · 2-3 all-high | **0.00–0.02 %** | 0.00–0.77 % | ≤ 0.75 |

**Mean |error| 14.4 points; 22.8 in the strong region; 0.26 at the floor.** All eight states were verified for the
property they claim (no flush, no straight) before scoring.
## What the extra epochs changed

| scenario | epoch 60 (D-91) | **epoch 280** |
|---|---|---|
| quad aces | 93.55 | **99.95** |
| nut flush | 99.67 | **99.91** |
| ace-high straight | 63.94 | **46.66** (worse) |
| trip aces | 70.60 | 69.80 |
| pair of kings, dry | 12.01 | **4.24** (worse) |
| the junk hands | 0.01–0.20 | 0.00–0.77 |

**The model converged toward the poles:** the two unbeatable hands are now within a tenth of a point, the junk floor
is exact — and the hands in between **got worse**, with a dry pair of kings at 4 % against a true 45 %.
## What that means

The supervised target is **binary**, and in a six-way pot a non-nut strong hand wins a minority of showdowns while a
nut hand wins them all. Cross-entropy on that label drives the **poles** to their exact values — pure positives and
pure negatives are common — and leaves the middle compressed, which is exactly what a 22.8-point error beside a
0.26-point error looks like (D-94).

**The verdict is the same as on the shallow model, and sharper:** the model knows what a lock looks like and what a
hopeless hand looks like, and not what a *good but beatable* hand is worth. The fix to test next is a **continuous
target** (Monte-Carlo equity per sample) in place of the binary outcome, which gives the middle of the range a signal.
