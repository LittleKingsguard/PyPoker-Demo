# Double-Q at 20,000 hands: another zero · measured 2026-11-07

D-38 concluded that the max operator's overestimation explains the zero fold rate, and D-41 chose Double-Q
— catalogued since D-19, implemented, capacity-matched, never trained against this question — as the
cheap test of that conclusion. Run: two-seat no-limit, 100-chip stacks, 20,000 hands per seed, seeds 0 and
1, the raiser pool (three anchors, the two folders used by the RCA, and the trained raiser), `double-q-learning`.

| seed | decisions | fold | check-call | raise-minimum | folds legal |
|---|---|---|---|---|---|
| 0 | 11,015 | **0** | 2.0 % | 98.0 % | — |
| 1 | 10,843 | **0** | 2.0 % | 98.0 % | — |
| **pooled** | **21,858** | **0** | 2.0 % | 98.0 % | 14,046 |

Wall clock 2,947 s for the two seeds.

## What it settles

**Double-Q does not change the behaviour.** Twenty-two thousand decisions, folding legal in 14,046 of
them, and the policy is the same 98 % raise-minimum as masked-Q in that configuration — so the cheapest
classical repair for max-operator overestimation moves nothing.

That does not prove overestimation is absent — function approximation can bias value estimates in ways
Double-Q's decoupled selection does not remove — but it **removes the remedy D-38 named**, so the RCA's
attribution cannot be accepted as it stood.

## The elimination table, after five experiments

| candidate | verdict |
|---|---|
| the reward (folding read as a loss) | eliminated — a tabular learner with the same payoff folds 100 % |
| the missing `hand_class` fact | eliminated — folds 100 % with strength removed from its state |
| the pool's composition | eliminated — 0 folds with a trained raiser in the pool |
| the training budget | eliminated — 0 folds at 20,000 hands |
| **max-operator overestimation (Double-Q)** | **not repaired by its classical remedy** |

What remains is the **learner's representation and capacity**: an eight-state tabular learner folds 87 %
at a six-seat mixed table where a 14,766-parameter network folds 0 %, and no remedy applied to the
network's updates has changed that. The isolating experiment is at **matched configuration** — the same
six-seat mixed table, the product learner, 20,000 hands, possible since D-37 — and it is the next one
(D-42).
