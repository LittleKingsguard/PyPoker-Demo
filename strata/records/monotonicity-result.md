# Monotonicity: the policy reads cards but does not rank them by strength · measured 2026-11-08

D-116's owed test, run on the best configuration (masked pooler, attn-60, league, **ε 0.60**, seed 0, base arm), 12
hole sets on a fixed board disjoint from every one of them, **preflop decisions only** — the board is unknown there, so the
decision sees exactly the hole cards — with true equity from 300-draw Monte Carlo (D-14).

| hand | true eq | action | | hand | true eq | action |
|---|---|---|---|---|---|---|
| 72o | 6.8 % | fold | | 87s | 19.3 % | call |
| 32o | 9.3 % | fold | | **KQo** | **22.8 %** | **all-in** |
| 82o | 10.6 % | fold | | AKo | 30.8 % | all-in |
| **72s** | **10.5 %** | **all-in** | | **QQ** | **41.1 %** | **call** |
| **43s** | **12.2 %** | **all-in** | | AA | 50.9 % | all-in |
| **22** | **12.3 %** | **fold** | | T9s | 25.2 % | call |

**12 violating pairs; not monotone.**

## What the ladder shows

- **It folds the three worst hands** (6.8, 9.3, 10.6 %) — the floor is real.
- **It raises all-in with 72s (10.5 %) and 43s (12.2 %) while folding 22 (12.3 %)** — a suited junk hand is played more
  aggressively than a pair, at the same equity.
- **QQ (41.1 %) gets a call while KQo (22.8 %) gets an all-in** — an inversion at the top of the range.

So the policy is keyed on **suitedness and shape**, not on strength: within the same equity it prefers suited junk to a
small pair, and it treats a big pair more passively than a big offsuit ace.

## What this settles

**Card-dependence and strength-ordering are different properties, and the project has the first without the second.**
Everything since the mask (D-115, D-119, D-125, D-126) established that the agent reads its cards; this establishes that
it does not rank them, and quantifies the gap: **12 monotonicity violations out of 66 pairs on a 12-hand ladder.**

That is the last measurement owed on the policy side, and it names the remaining work precisely: the learner uses card
information for *texture* (suited/paired/connected) and not for *equity*, which is what a Monte-Carlo target or the
card-model ranking as a direct input would change.
