# Battery: the model at the best and worst hands it can hold · measured 2026-11-08

A battery of **loaded states at the extremes**, each verified for the property it claims (no flush possible, no
straight possible), with ground truth from **20,000-draw Monte Carlo** over five random opponents, and scored against
the attention card model trained to 60 epochs (D-14).

| scenario | flush? | straight? | **MC truth** | model | error |
|---|---|---|---|---|---|
| quad aces | no | no | **100.00 %** | 93.55 % | −6.45 |
| nut flush (`As Qs` on `Js 9s 4s`) | — (that is the hand) | no | **100.00 %** | 99.67 % | −0.33 |
| ace-high straight (`As Kd` on `Qc Js Th`) | no | — (that is the hand) | **97.77 %** | 63.94 % | **−33.83** |
| trip aces (`As Ad` on `Ah Kd 7c 5s 2c`) | no | no | **91.84 %** | 70.60 % | **−21.24** |
| pair of kings, dry board | no | no | **45.07 %** | 12.01 % | **−33.06** |
| 2-3 offsuit, no pair, no draw | no | no | **0.00 %** | 0.01 % | **+0.01** |
| 2-7 offsuit, no pair, no draw | no | no | **0.00 %** | 0.08 % | +0.08 |
| 2-3 offsuit, all-high board | no | no | **0.02 %** | 0.20 % | +0.18 |

## What the battery finds: the ordering is right, the calibration is not

- **Rank correlation with the truth: ρ = 0.976** — the model orders the extremes almost perfectly (the only
  disagreement is trip aces against the straight, 6 points apart in truth).
- **Errors split sharply by region**: hands whose true equity is **< 1 %** carry a mean error of **0.09 points** —
  essentially exact. Hands above **40 %** carry a mean error of **19.0 points**, and the two worst misses are the
  ace-high straight (−33.8) and a dry pair of kings (−33.1).
- **The error is one-directional**: everything strong is **under-predicted**, i.e. the model compresses toward the
  mean of its training distribution. This is the same compression D-83 measured on aces preflop, now shown at the
  extremes of a known board.

**So an aggregate R² of ~28 % coexists with a 34-point error on a specific hand (D-6).** The R² says the model has learned
something; the battery says exactly where it is wrong — and that is the point of having both.

## Caveats

The model scored here trained for **60 epochs**; a longer run in flight would sharpen the absolute numbers. The
*shape* of the error — accurate at the floor, compressed at the top — is the property this battery exists to watch,
and it should be re-read once the longer run lands.
