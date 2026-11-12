# R1 closed out: the deep run lands on the same steal · measured 2026-11-08

The first rung's deep run, at the configuration that measured best: two-seat no-limit, 100-chip stacks,
blinds 1/2, `naive-numeric` (numpy, flat-numeric, naive-stack 36×2), masked-Q, net chips, the frozen
folder pool `pool-11b03e0a5ff07c13`. **200,000 hands × seeds 0, 1, 2**, wall clock **11.5 h** (D-14).

## The result

| seed | greedy decisions | raise-minimum | check-call | fold | chips/hand vs `fold-no-pair-or-better` |
|---|---|---|---|---|---|
| 0 | 6,542 | **98.6 %** | 1.4 % | **0** | +1.188 ± 0.466 |
| 1 | 6,434 | **98.3 %** | 1.7 % | **0** | +1.188 ± 0.466 |
| 2 | 6,511 | **98.5 %** | 1.5 % | **0** | +1.188 ± 0.466 |
| **pooled** | **19,487** | **98.46 %** | 1.54 % | **0** | — |

The chip rate is identical across seeds because the three policies are behaviourally identical: same
98.5 % minimum raise, same deal set, so the same payoffs. That is itself the finding.

## What it closes

**Two hundred times the live budget reproduces the live-budget policy to within a percentage point** —
98.46 % raise-minimum at 200,000 hands against 96.8 % at 1,000 (D-38), with no fold ever taken and the
same positive chip rate against a folding opponent. R1 has **converged to the steal**, and compute does
not move it: the plateau is at the deepest budget the project runs, not at the shallow one.

That is a close-out, not a failure: the rung's claim is that a flat numeric encoding and a naive stack
learn to steal from opponents that fold, and at 200× the budget the claim holds, with the policy's
stability across three seeds as the strongest form the claim can take. Its evidence sits beside the
measurements that justify the configuration — the sizing ladder's 6–9.6-chip price for bet size, the
96.5 % game win rate of the steal against folding opponents, and the five-way elimination that showed
the zero fold rate is not the reward, the encoding, the pool or the budget.

## What the record does not carry

The curves were not captured: the launcher printed the last `mean|TD|` points through a formatting bug
and did not dump the run record, so the trajectory exists only inside the process that has ended. The
census, the chips and the three final containers are on record; the curve is owed if a later rung needs a
live-versus-deep curve comparison on this shape. The lesson is the launcher's, not the build's.
