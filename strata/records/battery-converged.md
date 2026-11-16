# At convergence the aggregate metric improved and the calibration collapsed · measured 2026-11-08

The extremes battery scored against the **converged 400-epoch** model (weights saved and verified this time), beside
the same battery at 60 and 280 epochs (D-91, D-94). Same eight states, same Monte-Carlo truth (D-14).

| model | pooled R² | quad aces (100) | nut flush (100) | **straight (97.8)** | **trip aces (91.8)** | **KK dry (45.1)** | junk (0–0.02) | mean abs err |
|---|---|---|---|---|---|---|---|---|
| **60 ep** | 28.1 % | 93.55 | 99.67 | **63.94** | **70.60** | **12.01** | 0.01–0.20 | **11.90** |
| **280 ep** | 35.2 % | 99.95 | 99.91 | **46.66** | **69.80** | **4.24** | 0.00–0.77 | 14.36 |
| **400 ep** | **40.0 %** | 99.66 | 99.65 | **11.21** | **2.71** | 28.03 | 0.00–0.38 | **24.22** |

## The two curves move in opposite directions

**Pooled variance explained rises 28.1 % → 35.2 % → 40.0 %** while **mean absolute error on the battery rises
11.9 → 14.4 → 24.2 points.** At convergence the model predicts:

- **2.71 %** for trip aces whose true equity is **91.84 %** — a **89-point** error on a near-lock;
- **11.21 %** for an ace-high straight whose true equity is **97.77 %** — an **86-point** error;
- ~100 % for the two *unbeatable* hands and ~0 % for junk, i.e. it has become a **threshold detector of locks**, not an
  estimator of equity.

## Why both are true at once

The training target is **binary**, and the pooled R² rewards getting the *bulk* of the distribution right — most
samples are mid-range hands whose labels are near the 1/6 base rate. A model can improve pooled squared error while
its **conditional** predictions for particular hands collapse toward 0 or 1, because a binary label gives every
non-nut hand a mixture of wins and losses that cross-entropy resolves by pushing the output to an extreme and letting
the *average* absorb the error.

**The battery catches what the aggregate cannot**: identical R² improvements coexisting with a 89-point regression on
a specific near-lock. Every claim in this project that used an aggregate deserves the same check, and the ones without
one should be read as provisional.

## The fix this makes obvious

**Train on a continuous target** — Monte-Carlo equity per sample, exactly the quantity the battery uses as truth —
instead of a binary outcome. A continuous target forces the model to regress the *conditional probability* rather than
classify the majority outcome, and it is the one change the battery has specifically earned.
