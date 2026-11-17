# With the mask the policy finally reads its cards — and plays worse · measured 2026-11-08

The masked pooler (D-114) at `net-chips-normalised`, 15,000 hands, six seats, against the league, seed 0, measured
beside the unmasked arms of D-109 (D-14). Pre-mask and post-mask are different eras; the comparison is what the change
was for, not a matched-budget claim.

| arm | pooler | chips/hand | census | card-dependence | showdown |
|---|---|---|---|---|---|
| control | unmasked | **−0.600 ±0.04** | fold 100 % | 1/5 | 0.0 % |
| control | **masked** | **−4.05 ±0.48** | fold 90 %, raise 9 % | **1/5** | 0.0 % |
| strength | unmasked | −9.97 ±0.88 | fold 83 %, raise-half 15 % | — | 0.0 % |
| **strength** | **masked** | **−1.70 ±0.24** | fold 86 %, raise-min 13 % | **2/5** | 0.0 % |

## What the mask did

**It ended the degenerate corner.** Unmasked, the control folded **100 %** of everything; masked, it folds 90 % and
raises 9 % — the policy's actions now vary **within** a run, which no earlier product run managed.

**And with the strength input it produces the first card-dependence in the product**: on the loaded-deal suite,
**`AA`, `KQs`, `22` and `87s` raise-minimum while `72o` folds** — 2 of 5 distinct decisions, against 1 of 5 for every
pre-mask checkpoint and for the masked control.

## What it did not do

**It did not produce skill.** Both masked arms **lose more than folding did** (−4.05 and −1.70 against −0.60), and both
still reach the showdown in **0.0 %** of hands. The strength arm's card-dependence is a **threshold, not a ranking**: it
raises `AA` and `22` alike and only distinguishes the worst hand — which is consistent with the card model's measured
shape (a lock detector that is 89 points wrong on near-locks, D-95), and with the league punishing raises (D-106).

## The honest reading

The pooler was **a** blocker, and removing it was necessary: the input channel now works, demonstrably, for the first
time. What remains is a **different** problem — the policy's fold/raise choice is not ranked by strength, and against a
league containing raisers the aggressive side of its range costs more than the passive side. **The next measurement is
whether the card-dependence survives seeds** — one seed, one arm, 2/5 distinct is a first sighting, not a result, and
this project has been burned by exactly that (D-82's flicker, withdrawn at 15,000 hands).
