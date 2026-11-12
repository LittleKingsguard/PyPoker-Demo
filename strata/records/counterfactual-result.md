# The revealed counterfactual: folding appears, at one seed of two · measured 2026-11-07

Built as D-43 authorised — the reveal recorded post-hand, the counterfactual resolved from it, one
quantity, all legal actions — and measured at the configuration the user named: **six seats**, mixed pool
`pool-8386c3ef83ae48b2` (three anchors, D-21's three folders, a trained six-seat raiser), 20,000 hands per
seed, seeds 0 and 1, the two arms differing in the `counterfactual` key alone (D-14).

| seed | arm | decisions (tie-excluded) | fold | check-call | quarter | minimum | chips/hand [95 %] |
|---|---|---|---|---|---|---|---|
| 0 | `none` | 4,529 | **0.00 %** | 100.00 % | 0 | 0 | −5.04 [−11.97, +1.89] |
| 0 | `reveal-counterfactual` | 4,530 | **0.00 %** | 100.00 % | 0 | 0 | −5.29 [−12.21, +1.64] |
| 1 | `none` | 3,742 | **0.00 %** | 41.37 % | 52.57 % | 6.07 % | +3.19 [−4.16, +10.53] |
| 1 | `reveal-counterfactual` | 3,862 | **40.01 %** | 0 | 0 | 59.99 % | −0.76 [−3.41, +1.90] |

## The verdict, by the criterion pinned before the run

**FAIL.** Seed 1 passes all three conjuncts — 40.01 % fold against 0.00 %, a **+40.0-point** gap no share
interval can explain — and **seed 0 fails conjunct 1**: its member arm folds 0 of 4,530 decisions against
the pinned 5.0 % floor. Both seeds were pinned, so a pair verdict requires both.

**Plainly: the counterfactual produces folding where the existing rule produces none — but only at one of
two seeds.** At seed 1 it folds 40 % and drops the raise bands entirely; at seed 0 it folds nothing and
check-calls everything, exactly as the baseline does.

## What the measurement does and does not show

- **It is the mechanism working, not a chip effect**: the two arms' chip intervals overlap at both seeds,
  so chips neither confirm nor deny; the difference is behavioural, which is what was asked for.
- **The signal reaches about a quarter of the decisions it could**: 11,282 of 40,008 training transitions
  at seed 0 and 10,677 of 39,530 at seed 1 were resolved by a five-card showdown. Hands without one fall
  back to the ordinary target by D-40's rule, so three quarters of the learning is unchanged.
- **Neither run diverged** (largest |td_error| 104.8 / 92.6 baseline, 97.5 / 91.3 member).
- **The seed dependence is the attractor lottery**, recorded before (`attractor-sweep.md`) and exactly why
  the criterion was pinned per seed.

## What would settle it

More seeds, not a different threshold: the question is now the **probability** that this member reaches
the folding attractor, and two seeds cannot answer it. Seeds 2–6 at the same configuration would put the
first estimate on it, at the cost this run already paid per seed.
