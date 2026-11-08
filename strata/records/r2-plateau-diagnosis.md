# Why R1/R2 stall at "beats random, loses to the callers" · measured 2026-11-07

Framing (user): if `always-call` is the stronger degenerate strategy the learner should at least reach
it. It reaches the *other* one — always-raise — worse than calling everywhere it was measured (D-14).

## What the trained policies do

Action census over ~560 decisions each, both seats (deep R2 = 200,000 hands; shipped R1 = 1,000):
**raise 80–89 %, check-call 10–20 %, fold 1 %** — the calling core learned, plus a raise habit (D-14).

## The raise habit is a mistake, not an adaptation

The same policy against a twin forced to call wherever calling is legal (it differs only in not raising):

- vs the R1 ancestor (its training pool): −1.423 learned, −0.693 forced to call — **worse by 0.730**.
- vs `always-call`: −0.163 learned, −0.100 forced to call — **raising is worse by 0.063**.

Against `always-call` the twin reproduces the baseline exactly (137/11/152) — the control: the twin
*is* `always-call`. The learner is not adapting to its pool; it leaves money on the table in both,
most of all against the ancestors it trained on (D-16).

## Neither capacity, nor time, nor hyperparameters

- **Time**: 200,000 hands × 3 seeds gave the same table as 3,000 (`r2-deep.md`); **capacity**: width
  36 and width 120 (163 KB vs 864 KB of parameters) converge to the *same greedy policy*.
- **Hyperparameters**: unsweepable — a configuration's `hyper` block is **silently ignored** (`grep
  hyper src/training/loop.py` → nothing), so four sweep configs gave byte-identical results because
  they were the same model. A key a run ignores and never refuses is a defect (D-14).

## Conclusion

The bottleneck is the **estimator**, not the representation: max-operator Q-learning on a terminal
reward varying by ±20 chips, resolving an action-value difference of ~0.06–0.7 chips. The max of three
noisy estimates is biased upward and takes whichever drew positive noise; more hands do not shrink
that bias, which is why 600,000 hands moved nothing (D-6).

For the ladder, one learning rule is held across R1–R6 so a rung isolates representation (D-3); if
the rule is the bottleneck, R3–R6 compare representations under a biased estimator. The rule wants
changing — Double Q, Monte-Carlo or n-step returns, reward normalisation — which re-baselines every
artefact (D-14).
