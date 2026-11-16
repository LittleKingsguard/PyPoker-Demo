# The card model: what to say, and what each ingredient is worth · 2026-11-08
## What each ingredient contributes (all measured)

| ingredient | worth | evidence |
|---|---|---|
| **positions** | **+2.2 points** | attention and mean-pooling are both permutation-invariant (D-89) |
| **attention** | **+12.8 points** | positions without attention reach 15.3 % (D-89) |
| **learned card embedding** | mechanism **not** needed, ceiling **needed**: one-hot + attention reaches 29.4 % then declines, tokens climb to 40.0 % (D-96) | |
| **more training** | **+7.6 points** from 120 to 360 epochs, moving the late streets while the flop stalls at 17.7 % (D-93) | |
## The caveat that must travel with the headline

**At convergence the pooled R² rose to 40 % while the battery's mean error rose to 24 points** (D-95): the model
predicts **2.7 % for trip aces whose true equity is 91.8 %**, and is accurate only at the poles — because the training
target is **binary**, cross-entropy pushes each non-nut hand to an extreme and lets the average absorb the error.
Quote the 40 % with that sentence, or quote neither.
## For the presentation
- **Say**: cards explain **2.4 %** of a six-way outcome preflop and **52.8 %** at the river — the signal arrives with the
  board — and **attention plus positions** reads it **38 % better** than a flat encoding, because it can express
  *"the river paired my hole card"* as a relation rather than an accident of pooling.
- **Say**: the **learned embedding** is what keeps it improving past 30 % — the mechanism works without it, the ceiling
  does not (D-96).
- **Say**: an **aggregate can hide a local collapse** — 40 % pooled beside an 89-point error on a near-lock (D-95).
- **Do not say** it is a poker agent: no legal mask, no action head, target integrates over **random** opponents.
- **Do not say** these are ceilings without the convergence curve — every figure here now has one (D-85).
