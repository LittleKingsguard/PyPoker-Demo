# Reveal-only counterfactual at a six-seat mixed table · measured 2026-11-07

The design as the user scoped it: use counterfactual regret for all actions **only where the cards are
revealed into public knowledge** (a showdown), and the previous reward scaling everywhere else; and
train at multi-seat tables with **mixed pools of folders, raisers and callers**, since a two-player game
cannot reward folding (D-40).
## Implementation

Six-seat no-limit, blinds 1/2, 100-chip stacks, the learner in a random seat, the other five cycling
through a folder, a caller and a raiser. At a decision the counterfactual uses the reveal — the final
board and every showdown hand are public — so

`v_fold = −committed`, and `v_call = (pot − committed)` if our hand wins the showdown, else
`−(committed + to_call)` — both **exact**, not sampled. Every hand ending without a showdown falls back to the ordinary net-chip
reward, as before.
## Result (tabular learner, 8,000 training hands, 1,200 greedy)

| arm | fold | call | min | pot | all-in | chips/hand | cf updates | showdowns |
|---|---|---|---|---|---|---|---|---|
| baseline, net chips | **87 %** | 3 % | 5 % | 3 % | 2 % | +0.362 | 0 | 0 |
| reveal-only counterfactual | **87 %** | 5 % | 7 % | 0 % | 2 % | +0.297 | **19,889** | 7,978 |
## The finding that matters

**At six seats with a mixed pool, the tabular learner folds 87 % — folding appears.** The product's
six-seat run folded **0 %** on the same kind of table. Same game, same pool shape, same seat rotation;
the difference is the learner. That confirms D-38 from the other direction: the zero-fold rate is the
estimator's overestimation, not the pool and not the game.

The counterfactual signal, correctly scoped, **changed almost nothing here** — the learner already folds,
so there is little to repair and chips move inside noise. Its product value is specifically to repair an
estimator that overestimates the calling arm, which the earlier two-player probe showed it does
(+6.4 chips/hand).
## The honest limitation of reveal-only

One revealed board gives **one sample** per decision: `v_call` is a win or a loss, not an expectation.
19,889 updates across 7,978 showdowns is a high-variance signal, which is why it barely moved a learner
that was already correct. Averaging over the opponents' possible holdings would lower the variance but
would stop using the reveal, so the trade is between "public information, one sample" and "privileged
information, many samples" — the first is the user's instruction and the second was D-39's probe.
