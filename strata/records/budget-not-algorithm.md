# The difference was the training budget, not the algorithm — D-103 withdrawn · measured 2026-11-08

D-103 concluded that the product's learner "changes nothing" with the strength input, on the evidence of a
**5,000-hand** run where both arms folded every hand. The probe's advantage (+1.61) had been measured at **15,000**
hands. This runs the product at the **same 15,000 hands**, same league, same seed, `net-chips` (D-14).

| arm | budget | chips/hand | census |
|---|---|---|---|
| **control** (obs 122, v4) | **15,000** | **+3.46 ± 7.16** | check-call 83 %, raise-quarter 17 % |
| **strength + seeded** (obs 123, v6) | **15,000** | **+3.46 ± 7.16** | check-call 83 %, raise-quarter 17 % |
| control | 5,000 | −0.60 ± 0.04 | fold 100 % |
| strength + seeded | 5,000 | −0.60 ± 0.04 | fold 100 % |

**The two 15,000-hand arms are distinct runs** — different containers (md5 `dddf95e5…` against `e58ddf57…`), different
observation widths (122 against 123) — and they behave identically, which is a result about the *input*, not a bug.

## Two corrections, both mine

1. **D-103 is withdrawn.** The product does **not** "fold every hand with the strength input": at the probe's own
   15,000-hand budget it learns a **calling policy worth +3.46 ± 7.16 chips/hand against the league**, where 5,000
   hands gave −0.60. The collapse I reported was **an under-trained learner**, not a structural difference.
2. **The probe's +1.61 is inside the product's interval** (±7.16), so **the probe has no demonstrated advantage over
   the product at equal budget** — my "probe +1.9, product −0.6" comparison mixed two budgets and cannot be quoted.

## What survives from D-103

Only this: **the strength input and the seeded embeddings do not change the product's behaviour**, at either budget,
in six runs. That is now measured at 5,000 hands (seeds 0–2) and 15,000 hands (seed 0, both arms), with distinct
containers and identical decisions.

And the utility was excluded separately: `net-chips` and `stack-shortfall` both give fold 100 % at 5,000 hands.

## What the earlier probe results still mean

D-99 (+11.6 against scripted opponents, three seeds) and D-101 (+2.5 against the league, two of three seeds) stand as
probe measurements at 15,000 hands. What does **not** stand is any claim that they beat the product: at equal budget
the product reaches **+3.46 ± 7.16** against the same league, and the two are indistinguishable.

**The honest summary line: the card representation helps a policy that has enough training, and beyond that the
project has no measurement showing the probe's machinery is better than the product's.**
