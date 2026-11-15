# The off-policy correction breaks the fold loop but not the card-blindness · measured 2026-11-08

D-72 found the fold-pinning is a data-starvation loop and named two remedies. This runs the second one: the
`reveal-counterfactual` member, which prices the actions the agent did **not** take. Same configuration, same
pool, same 5,000 hands × seeds 0–1, six seats, token encoding, `net-chips-normalised`; arms differ in one key
(D-14).
## It works on the loop

| arm | fold | check-call | raise-minimum | decisions |
|---|---|---|---|---|
| **masked-Q** (control) | **93.1 %** | 4 % | 3 % | 4,229 |
| **`reveal-counterfactual`** | **29.6 %** | 68 % | 2 % | 6,643 |

The fold share falls by **63 points** and the decision count rises 57 % — the agent plays on, so the samples that
price playing on now arrive. D-72's mechanism is confirmed by a second, independent remedy.
## It does not fix the card-blindness

The loaded-deal probe — the same dry board, the same seat, three hole sets, both seeds:

| arm | seed | AA | 72o | KQs | card-dependent? |
|---|---|---|---|---|---|
| control | 0, 1 | fold | fold | fold | **no** |
| counterfactual | 0 | check-call | check-call | check-call | **no** |
| counterfactual | 1 | fold | fold | fold | **no** |

**The counterfactual changes which constant the model picks; it does not make it pick by its cards.** Seed 0
calls everything, seed 1 folds everything, aces and seven-deuce alike.
## What this isolates

Three remedies have now been tried against the same failure and they separate cleanly:

| remedy | moves the mode? | moves card-dependence? |
|---|---|---|
| reward scale (D-67) | yes — revived the trunk | no |
| exploration floor (D-72) | yes — 92.9 % → 0.0 % | untested on the probe |
| **off-policy counterfactual** | **yes — 93.1 % → 29.6 %** | **no** |

So the failure has **two layers**: a control layer — which action the policy settles on — that all three remedies
move, and a **discrimination layer** — whether the decision depends on the hole cards — that none has. Only the
flat encodings are card-dependent (D-71).
