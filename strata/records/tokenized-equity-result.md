# The token path learns equity: the policy failure was credit assignment · 2026-11-08

D-83's supervised task through the **token architecture**: two card ids (`1 + 4·rank + suit`) → embedding
(53 × 50) → mean over the two real rows → 64-64 trunk → sigmoid, same data, split, optimizer and epochs (D-14).
**No padding is involved** — the mean is over the two real tokens — so this isolates the embedding from D-79's
padding pathology.

| representation | held-out MSE | R² over constant | AA (empirical 52.2) | QQ (39.8) |
|---|---|---|---|---|
| **flat one-hot (34)** | **0.13004** | **2.41 %** | **44.7** | **36.6** |
| **tokens, no squash** | 0.13042 | **2.13 %** — 88 % of flat | 40.9 | 30.6 |
| tokens + squash | 0.13094 | 1.73 % | **32.8** | 23.9 |

Calibration tracks the diagonal in all three (tokens: deciles 10.8 → 27.9 %), and the hand ordering is correct.

## What this settles

**The token representation can learn poker equity from cards** — 88 % of the flat model's explanatory power, correct
ordering, calibration intact. So the token path's inability to read its hand in the policy runs (D-52, D-56, D-67,
D-71, D-73, D-77, D-82) is **not a representational limit on card information**: it is the
**credit-assignment problem** of the policy task, which a supervised target removes.

**Two secondary findings:** the **squash costs a third** of the explanatory power (2.13 → 1.73 %, aces 40.9 → 32.8),
confirming D-77's `no-squash` remedy on a task where learning succeeds; and **the padding pathology was an
implementation bug, not a token property** — with two real tokens and no padding the same embedding learns, so
D-79's 89 %-padding pool was starving it.

## The two-layer picture, completed

| layer | what it constrains | evidence |
|---|---|---|
| representation | **not** the binding limit — tokens learn equity at 88 % of flat | this record |
| credit assignment | the policy never learned card-dependence under any reward/exploration/estimator change | D-67, D-72, D-73, D-77, D-81, D-82 |
| information ceiling | even a perfect equity model explains **2.4 %** of a six-way outcome | D-83 |

The project's negative results are one problem, not three: **a small learnable signal, delivered by a credit
assignment method too weak to extract it** — and the supervised estimate the user proposed is precisely the fix.
