# How the current model performs against the league · measured 2026-11-08

The best policy the project has: the product's learner at **15,000 hands**, six seats, `card-tokens`,
`token-embedding` 50×2, `net-chips`, against the league (folder / 50-50 raiser / 83 % raiser / caller), seeds 0–2,
2,000 greedy hands each (D-14).

| seed | chips/hand | behaviour |
|---|---|---|
| 0 | +3.46 ±7.16 | call 83 %, raise 17 % |
| 1 | −2.25 ±7.01 | call 100 % |
| 2 | +4.26 ±7.18 | call 100 % |
| **mean** | **+1.82 · sd 3.55 · 95 % CI ±8.81** | call-dominant |

**The interval [−6.99, +10.63] includes zero**, so the honest single statement is: **the model cannot be distinguished
from break-even against this league at this budget.**

## The reference bar — the league's own members, same mix

| player | chips/hand |
|---|---|
| the folder (folds 100 %) | **−0.60 ±0.04** |
| **the 50-50 raiser** | **+2.24 ±3.33** |
| the 83 % raiser | +1.31 ±8.27 |
| **our trained model** | **+1.82 ±8.81** |

**Our model is statistically indistinguishable from the league's best member** (+1.82 against +2.24, intervals
overlapping over their whole span) and is **not** a breakaway: the seed-to-seed spread (−2.25 to +4.26) is **larger
than any difference between our model and the league's best**.

## What the behaviour says

All three seeds end **call-dominant** (83–100 % `check-call`), which is what this mix rewards — the folder surrenders
blinds and the caller never folds, so cheap calling is the exploit. That is the same lesson D-99/D-101 produced: **the
policy finds the cheap exploit, not a strong strategy.**

## What would make this answer stronger

More seeds (three give ±8.8; six roughly halve it); a stronger league through the product's own pool machinery; and
the head-to-head Bradley–Terry instrument (D-21) rather than a chip mean against a fixed mix.
