# The encoding separates cleanly on seven seeds · measured 2026-11-08

D-54's hardening run: `R3 card-tokens` against `R1 flat-numeric`, six seats, no-limit, 100-chip stacks, the
mixed pool `pool-8386c3ef83ae48b2`, `stack-shortfall` on both arms, **15,000 hands × seeds 0–6**, ties
excluded, the encoding the only variable (D-14). Seeds 0–2 are D-53's; 3–6 are this run (wall 11,916 s and
10,708 s).

| arm | seeds 0–6 fold % | mean | sd | range |
|---|---|---|---|---|
| flat-numeric | 78.33 · 87.01 · 77.58 · 76.99 · 70.69 · 81.21 · 70.87 | **77.53 %** | **5.71** | 70.69–87.01 |
| **card-tokens** | 91.83 · 93.45 · 92.25 · 91.02 · 93.01 · 94.82 · 92.82 | **92.74 %** | **1.22** | 91.02–94.82 |

## The separation, and why it is the strongest claim in the project

- **The arms' ranges do not overlap**: the *lowest* token seed (91.02 %) sits **4.01 points above** the
  *highest* flat seed (87.01 %).
- **Every seed favours the token encoding**, by 6.4 to 22.3 points, mean **+15.22 pp** (sd 5.48).
- **The token arm is also far steadier**: sd 1.22 against 5.71 — a fifth of the spread — and its chips are
  consistently less negative (−0.48 to −0.63 per hand) with intervals two to three times tighter than the
  flat arm's.

Seven seeds is enough to say this **is not seed selection**: the hypothesis D-54 set out to falsify — that
D-53's 92–93 % was seeds 0–2 — is falsified. Seeds 3–6 alone give 91.02 / 93.01 / 94.82 / 92.82, and the
flat arm on those same seeds gives 76.99 / 70.69 / 81.21 / 70.87.

## What it still does not establish

- **Neither arm wins**: every chip rate is negative, so this is a difference between two losing policies,
  and the arms' chip intervals still overlap within each seed.
- **The effect is conditional on the utility** (D-52): under `net-chips` the same encoding comparison
  produced no chip difference at all, so the encoding needs a policy distribution to act on.
- **Folding 92.7 % is a behaviour**, not a demonstrated edge — plausibly a cheap way to lose slowly.

## The claim the talk can make

With the utility held fixed and the encoding as the only variable, over seven seeds: **tokenising the cards
makes the agent fold 15 points more, with a fifth of the variance, and no seed reverses it.** That is
attributable, reproducible and falsification-tested — the first claim in this project that is all three.
