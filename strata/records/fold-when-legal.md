# Why all nine token runs reported 55.3 %: they are the same policy · measured 2026-11-08

D-67 flagged that nine token runs — three estimators × three seeds — reported **exactly 55.3 %** fold, too exact
to be independent convergence. This resolves it (D-14).

**They are literally the same function.** Playing four token models (`masked`/`double-q`/`reveal-counterfactual`
× seeds 0 and 1) on one fixed table of 150 hands, every model chose fold at every decision and all six pairwise
comparisons of the action sequences were **identical**: different estimators, different seeds, one policy.

**And that policy is "fold when folding is legal".** On the census pool, folding is legal in **55.3 %** of the
learner's decisions — the same number the nine runs report — so the models fold *whenever they can*, and 55.3 % is
how often the pool offers the chance. Replayed directly, `norm-tok-s0` folds **120 of 120** legal folds.

**But they are not constant folders.** On a *different* table — two folders and a caller, no raiser — the same
models diverge:

| model | folded when legal | played on |
|---|---|---|
| `norm-tok-s0` (D-67) | **120 / 120 (100 %)** | 0 |
| `short-flat-s0` (D-56) | 88 / 120 (73.3 %) | 32 |
| `norm-flat-s0` (D-67) | 20 / 120 (16.7 %) | 100 |
| `short-tok-s0` (D-56) | **0 / 120 (0 %)** | 120 |

Behaviour **is** conditional on the opposition — the token+stack-shortfall model that folds 92.7 % on its own pool
folds not once against folders and a caller — but within one pool the token models agree exactly.

## What this changes

1. **The 55.3 % is not nine results.** It is one policy reported nine times, so the estimator axis's apparent
   agreement at tokens is one measurement, not three.
2. **The encoding comparison needs restating.** "Tokens fold 92.7 % against flat's 77.5 %" (D-56) reads better as
   a difference in **when the model is willing to fold at all**: tokens fold whenever the pool lets them, flat
   folds three times in four.
3. **Both claims must be re-measured on the other's table before either is presented** (D-6), because the
   direction reverses with the opposition.

The honest sentence is narrower than the one prepared: **the risk-averse utility makes the agent fold whenever
folding is legal against a betting pool, and the token encoding makes it do so more consistently — while against
an all-passive table the same models stop folding entirely.** Conditionality is the finding; the percentage is a
property of the opposition.
