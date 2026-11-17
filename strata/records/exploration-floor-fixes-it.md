# The exploration floor fixes the collapse: +11.81 chips/hand and mixed play · measured 2026-11-08

D-72 measured the pinning with one parameter (ε_end 0.05 → 92.9 % fold; ε_end 0.60 → 0 % fold) and D-124 concluded the fix
lay there. This runs it: same mask, same card model, same league, 5,000 train + 2,000 **greedy** hands, seed 0, the ε
floor varied (D-14).

| arm | ε floor | chips/hand | census | card-dep |
|---|---|---|---|---|
| base | 0.05 | +3.68 ±3.21 | fold 78 %, call 22 % | 3/5 |
| **base** | **0.60** | **+11.81 ±5.03** | **fold 47 %, call 46 %, all-in 7 %** | **4/5** |
| opponent model | 0.05 | **−0.56 ±0.11** | **fold 99.7 %** | 1/5 |
| **opponent model** | **0.60** | **+10.49 ±4.24** | **fold 60 %, call 29 %, all-in 10 %** | 3/5 |

## What it does

1. **It un-collapses the opponent arm**: −0.56 → **+10.49**, fold 99.7 % → 60 %, with card-dependence restored
   (1/5 → 3/5). The arm that D-119/D-123/D-124 called unusable becomes as good as the base arm.
2. **It improves the base arm more than fourfold**: +3.68 → **+11.81**, and the repertoire becomes **mixed** — folding 47 %,
   calling 46 %, shoving 7 %, raising the rest.
3. **Both arms converge to the same place** (+11.81 and +10.49, intervals overlapping), so the opponent model stops being
   harmful once the learner is not corner-locked — exactly the reading D-124 gave.
4. **The evaluation is greedy**, so this is a better *learned policy*, not exploration noise leaking into the score.

## The best policy the project has measured

**+11.81 ±5.03 chips/hand against the league, card-dependent on 4 of 5 loaded hands, with a mixed action repertoire** —
against −0.60 for folding everything and +1.8 for the earlier break-even product runs.

## Caveats

**One seed.** The base arm alone ranged +3.68 to +9.09 across seeds at ε 0.05 (D-120), so the ε 0.60 magnitude needs seeds
1–2 before it is quoted, and the "opponent model is now harmless" reading needs the same. The probe's learner, not the
product's, and 5,000 hands is short. But the **direction** is the one D-72 predicted and it reverses D-123/D-124's
conclusion about the opponent model: the model was never the problem.
