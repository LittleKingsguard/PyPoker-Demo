# Counterfactual regret as a learning signal: measured · 2026-11-07

The instruction: reward folding by the counterfactual regret the reveal exposes. Two design facts came
out of testing it, then two measurements (D-39).
## The signal must be estimated for the arm *not* taken

First attempt — compute it at **fold decisions only** — produced **zero** updates (D-6), because the learner
never folds: the signal exists only where the action is already taken, so a learner that never folds
never learns that folding is right. The true regret form estimates the **unchosen** arm at **every**
decision where calling is legal, so the signal exists from the first hand.

The estimate uses the reveal the user named (D-6): the engine knows the opponent's hole cards, and the
unseen board is sampled (30 runouts), giving `v_call = p·(pot − committed) − (1−p)·(committed + to_call)` and
`v_fold = −committed`, with `p` the equity of our hand against theirs over the sampled boards.
## Measurements (tabular learner, two-seat no-limit, 100-chip stacks, 12,000 hands)

| opponent | arm | fold | call | pot-size | chips/hand |
|---|---|---|---|---|---|
| **D-21 folder** | baseline | 0 % | 23 % | **35 %** | **−2.89** |
| " | counterfactual | 0 % | 62 % | **2 %** | **+3.49** |
| **tight aggressor** | baseline | **100 %** | 0 % | 0 % | +0.75 |
| " | counterfactual | 18 % | 70 % | 5 % | +0.73 |
## What it establishes

1. **The value correction works** (D-6). Against the folder it is worth **+6.4 chips/hand** and removes
   over-betting entirely (pot-size 35 % → 2 %) — the overestimation D-38 named as the zero-fold rate's
   cause. It is the first signal in the project that *repairs an estimator* rather than changing the
   game, and the effect is large.
2. **It is not a fold generator** (D-6). Against the raiser the baseline already folded 100 %; the
   counterfactual traded most of that for calling at the same EV (+0.73 against +0.75), because against
   an opponent that folds most hands, folding and calling are near-equivalent. The honest product
   expectation is **calibration, not more folding** — and "the learner never folds" remains a property
   of the pool, not of this signal.
3. The two findings are complementary: the counterfactual fixes the estimator, and a pool that makes
   folding correct is still what would make folding appear.

Caveats (D-6): probe-level, tabular value on a coarse state, one opponent per cell, 30 equity samples per
decision, and the counterfactual target is mixed into the TD update at a fixed rate rather than derived
as a regret — a hybrid the gate must judge before it reaches the product.
