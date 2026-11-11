# RCA: why the learner folds 0 of ~15,000 decisions · 2026-11-07

The claim to test: folding is correct preflop against raisers and is never chosen, so this is an
algorithm failure rather than a game bias. Four candidates were separated by experiment (D-14).

## Eliminated

1. **The reward.** A tabular Q-learner with the *same* terminal chip payoff — no counterfactual, no
   shaping — folds **100 %** against a tight aggressor and profits (+0.75 chips/hand).
2. **The hand-strength fact.** The same learner with the strength band removed from its state (street ×
   facing-a-bet only) also folds **100 %**: no encoding carrying `hand_class` is not the obstacle.
3. **The pool.** A two-seat no-limit learner trained with a trained raiser in the pool folds **0 of
   12,856** greedy decisions.
4. **The budget.** With the 2,000-hand run cap lifted (D-37), the same learner at **20,000 hands per
   seed** — pool `pool-9de92cd385722546`, three anchors, three folders, the trained raiser — gave **0
   folds in 17,181 greedy decisions**, and 0 in the **8,725** of them where `fold` sat in the legal
   mask. Twenty times the budget, the same 14,766-parameter learner, folding available on 51 % of
   decisions: nothing changed.

## What that leaves

The zero-fold rate is **the max operator's overestimation** (D-38): the calling arm's value is inflated by a
`max` that is taken over values estimated from the same samples, so a certain small loss (folding)
always looks worse than an optimistically valued call. That is the classical failure of masked
Q-learning (D-19) and it explains every observation above, including why a tabular learner with eight states
does not suffer it — its estimates converge before the optimism can dominate.

**Double-Q is the experiment** (D-19, D-38): already catalogued and implemented, never yet trained
against this question. It decouples selection from evaluation, which removes exactly this bias.

## What this does not say

Two honesty limits, both stated by the run (D-6): it is one run at two seeds, and the seeds collapsed onto
*different* non-fold attractors (90.6 % raise-quarter against 98.2 % raise-minimum), so the invariant
measured is "never fold", not "always raise a particular size". And the census describes a 2,000-hand
sample of each run's own hands, not 20,000 hands played greedily.
