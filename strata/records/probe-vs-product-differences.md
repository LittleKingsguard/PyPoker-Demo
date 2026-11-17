# What actually differs between the probe and the product — enumerated, and two candidates refuted

D-103 found the product folding every hand where the probe did not. This enumerates every difference between the two
and records which have been **tested** (D-14).

## The differences, in the order they could plausibly matter

| # | difference | probe | product | status |
|---|---|---|---|---|
| 1 | **training budget** | 15,000 hands | **5,000 hands** | **untested at equal budget when I first reported it** — my own comparison error |
| 2 | **target** | Monte-Carlo: every decision of the hand gets the hand's payoff | one-step TD bootstrap per transition | untested |
| 3 | **update batching** | one batched step per hand | one semi-gradient step per transition | untested |
| 4 | **utility** | net chips (`payoffs / 600`) | `stack-shortfall` in the first run | **tested and refuted**: with `net-chips` the product still folds 100 % |
| 5 | **card input** | the supervised model's **masked** pooled 50-dim representation + probability | 123 token ids with seeded rows through the product's **unmasked** mean pool | **tested in the probe**: diluting the representation the way the product's pooler does moved fold from 87 % to 91 % and chips from −1.10 to −0.81 — a **direction** consistent with dilution hurting, not a significant effect |
| 6 | exploration schedule | ε 1.0 → 0.05 over the first half | the product's own ramp → 0.05 | untested |
| 7 | head | 64-64 over 56 inputs, 6 outputs | `token-embedding` 50×2 over 123 ids | untested |

## Two candidates eliminated, and one number that had to be corrected

**The utility is not the cause** — `net-chips` and `stack-shortfall` both give **fold 100 %, −0.600**, with and without
the strength input, on the same seed.

**The representation is not sufficient on its own** — the probe's masked-pool arm and its product-like unmasked-pool arm
differ in the expected direction (87 % vs 91 % fold; −1.10 vs −0.81 chips) but not significantly at 5,000 hands
(intervals ±2.2 and ±0.04).

**And the comparison I reported was unfair to the probe**: at **5,000** hands the probe's own Monte-Carlo arm scores
**−1.10 ± 2.16** — no advantage at all — while its D-101 result of **+1.61 ± 2.56** was at **15,000** hands against a
**5,000**-hand product run. So the headline "probe +1.9, product −0.6" mixed two budgets, and the correct statement
until an equal-budget run exists is: **at 5,000 hands neither configuration beats the fold baseline reliably.**

## The comparison that decides it

The product at **15,000 hands**, same league, same seed, `net-chips`, both arms — now running. If it stays at −0.600
the difference is **structural** (target/bootstrapping); if it moves, the difference was **budget**, and D-103's
conclusion must be withdrawn.
