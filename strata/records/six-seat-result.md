# Six seats with folders *and* a raiser: zero folds in 15,127 decisions · 2026-11-07

D-33's test: five seeds, 1,000 hands each at the live budget, census read from the exploration-off pass,
pool `pool-a6d453658fad47a6` — three anchors, D-21's three folders and a trained six-seat raiser, seven
members, frozen (D-14).

| seed | decisions | fold | check-call | quarter | half | minimum |
|---|---|---|---|---|---|---|
| 0 | 4,790 | **0** | 100.00 % | 0 | 0 | 0 |
| 1 | 2,458 | **0** | 8.71 % | 0 | 0 | 91.29 % |
| 2 | 2,442 | **0** | 9.13 % | 0 | 0 | 90.87 % |
| 3 | 2,458 | **0** | 7.85 % | 0 | 0.08 % | 92.07 % |
| 4 | 2,979 | **0** | 12.08 % | 0 | 77.31 % | 10.61 % |
| **pooled** | **15,127** | **0** | 38.21 % | 0 | 15.24 % | 46.55 % |

**Folding never appeared — 0 of 15,127 decisions, though it was legal in 11,212 (74 %)** — and every chip
interval spans zero (pooled +0.03 [−4.45, 4.66]).
## Why the chain breaks at its middle step

The expectation was: the pool lacked raisers → put raisers in → folding becomes correct → the learner
folds. **Six seats make folding *less* correct, not more.** With six players the pot is ~6× the blinds
before any raise, so continuing is cheap in relative terms and almost no hand is bad enough to fold; the
raisers *enlarge* the pot being offered rather than narrowing the price. That is the arithmetic the
earlier multi-way probe measured ("a limped 6-way pot offers 1 to win 11"), and raisers do not overturn it.

The heads-up probe is the counter-example that locates the condition: against a tight aggressor a learner
folds **100 %** and profits (`fold-when-correct.md`). Folding is learnable where it is correct — and it is
correct with **few opponents, deep stacks and large relative bets**, the opposite of six seats.
## Findings to carry

1. **Two of five seeds diverged and were not refused** (curves of 4.4e79 and 1.4e41): `LearningDiverged`
   guards non-finite values only, and these are finite but astronomical. A finite-explosion guard is
   missing.
2. **The retained record carries no seat**, so the rotation added to control position cannot be verified
   from the artefacts.
3. **`engine.equity` is process-dependent** through pokerkit's set-ordered sampling deck (0.36 / 0.3925 /
   0.3675 at `PYTHONHASHSEED` 0 / 2 / 5), contradicting `docs/L3/engine/stream.md`; pre-existing.
4. The **collapse** holds in four of five seeds, and *which* descriptor collapses varies by seed — the
   attractor lottery again, now over three sizes.
