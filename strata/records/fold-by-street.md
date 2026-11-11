# The learner never folds even when facing a bet on every preflop decision · 2026-11-07

D-34's census counted the learner's decisions against the six-member pool but not **which street** they
were on: the retained decision record carries no street. This measurement supplies it by replaying the
stage-3 learner (seed 2, exploration off) at a six-seat table against **five always-raisers**, so that
folding junk preflop — the case the user named — is unambiguously correct (D-14).

| street | decisions | actions | folded |
|---|---|---|---|
| preflop | **200** | check-call 62 %, raise-minimum 38 % | **0** |
| flop / turn / river | 0 | — | 0 |

**Every one of the 200 preflop decisions faced a bet, and the learner folded none of them.** It called or
min-raised into five raisers with whatever it held.

The absent post-flop rows are a property of this table, not of the learner: five always-raisers end the
hand preflop in an all-in war, so no post-flop decision arises here. The earlier pool-wide census
(`six-seat-result.md`) did contain post-flop decisions and also recorded zero folds.

## What this corrects

D-34 said six seats make folding *less* correct. That holds **post-flop**, where a six-way pot offers a
cheap price — and it does not hold **pre-flop facing a raise**, where a junk hand is a clear fold. So the
learner's 0 % fold rate is not the pool's answer after all; against raisers it declines a fold that is
correct, on every preflop decision it is offered.

## What it does not yet say

Which cause is responsible is untested, and they are separable: whether the learner lacked exposure (the
stage-3 pool's one trained raiser may rarely have raised, and two of five seeds diverged in training),
whether its value estimate cannot separate junk from playable hands at 1,000 hands, or whether the
representation cannot see the difference. A two-seat run against a raiser, where the earlier probe showed
a tabular learner folding 100 %, isolates the first: same reward, same opponent, one seat.
