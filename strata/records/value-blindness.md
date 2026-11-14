# What the models actually score: constant vectors, not weighted choices · measured 2026-11-08

The question: do the never-folding models *zero* the fold, or merely **outweigh** it? Neither. The learner
is an argmax over six values (a Q-vector), so there is no probability weighting to read — and the
measurement shows the never-folding models **emit one constant vector regardless of their input** (D-14).

Replaying each model at six seats against a table that produces varied decisions (a folder pair and a
caller, so pots stay small and all four streets appear), recording the encoded observation and the six
scores at every decision:

| model | decisions | distinct observations | **distinct score vectors** | actions chosen |
|---|---|---|---|---|
| token + net-chips s0 | 480 | 477 | **1** | raise-half 480 |
| token + net-chips s1 | 480 | 477 | **1** | check-call 480 |
| token + net-chips s2 | 480 | 477 | **1** | check-call 480 |
| flat + net-chips s0 | 480 | 477 | **1** | raise-minimum 480 |
| token + shortfall s0…s6 (7 models) | 120 each | 117 | **115** | fold 120 each |
| flat + shortfall s0 | 178 | 175 | **175** | fold 95, quarter 29, half 24, call 12, min 10, all-in 8 |

## What the numbers say

1. **The net-chip models are state-blind** (D-6). 477 different observations — different cards, streets, pots — map
   to **one** score vector. Their "policy" is a constant function: the same six numbers in every situation,
   so the same action always wins. `fold` is not zeroed and not outcompeted; the model is simply not reading
   its input. Its constant vector on this table is `[−8.650, −2.618, −1.625, −1.056, −1.191, −1.154]`, so
   fold sits 6.03 below the call and 7.59 below the best raise — a *constant* margin, hand after hand.
2. **The token+shortfall models do read their input** (D-6) — 115 distinct vectors from 117 observations — but the
   spread is tiny (sd 0.001–0.004) and `fold` wins by a margin of ≈0.013 over the call. Here fold is
   genuinely *outweighed*, by a hair, in every case.
3. **Only the flat+shortfall model is both state-dependent and mixed** (D-6): 175 vectors from 175 observations and
   a spread of actions (fold 53 %, raises 40 %, call 7 %), which is the one genuinely varied policy measured.

## Why this reframes the project

"Never folds" was never a preference (D-59). For the net-chip models it is **a collapsed network**: the same
constant vector in every state, which is also why three seeds produced identical payoffs, why the inference
test's matches between same-family models came out at 0.026 chips, and why every census showed a single
dominant action. The utility does not merely change *what* the model prefers — it changes **whether the
model learns to depend on its input at all**, and only the flat encoding under the risk-averse utility
produces a policy with real state dependence.
