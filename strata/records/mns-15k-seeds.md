# The token flicker does not survive the budget: three seeds, one constant each · measured 2026-11-08

D-80's masked-no-squash arm was the first token model to separate a hand at all — 72o from AA, KQs, 22 and 87s at
the opening seat — measured at 5,000 hands × seed 0. This reruns it at **15,000 hands × seeds 0, 1, 2**, fixed rate,
`stack-shortfall`, six seats, padding masked out of pool and scatter, squash dropped (D-14).

| seed | fold (census) | opening seat: distinct sequences of 5 hands | big-blind seat |
|---|---|---|---|
| 0 | 88.6 % | **1 / 5** — everything `raise-quarter` | **1 / 5** |
| 1 | 86.5 % | **1 / 5** — everything `raise-half` | **1 / 5** |
| 2 | 90.3 % | **1 / 5** — everything `check-call` | **1 / 5** |

**Every seed gives every hand the same decision, in both seatings.** AA, KQs, 22, 87s and 72o offsuit are played
identically by all three models; what differs between seeds is **which constant** — quarter, half, call.

## What this settles

**The 5,000-hand flicker was a transient, not a capability.** At three times the budget the pinning reasserts
completely and the card separation disappears — so D-80's finding must be read as *"a short-budget perturbation
moved the constant once"*, not as the token encoding beginning to read its hand. The correction is recorded, and the
token encoding's card-blindness is now measured at **5,000 and 15,000 hands, three seeds, two seatings, five hole
sets, with the padding masked and the squash dropped**: one action for everything.

## Why more hands erase rather than build

The mask and the squash-removal do what they were meant to — the padding row stops absorbing the learning, the card
rows move 9.5× further (D-78) — but a card is still addressed once or twice per decision, so 15,000 hands move a card
row by ~10⁻⁴ against a row scale of 0.55. Meanwhile the **exploration ramp decays to 0.05** and the fold/raise
attractor is what the value estimates converge on, so the longer run converges *harder* onto the constant, and the
short run's noise is exactly what produced the one flicker.

**The lesson is the one this project keeps re-learning**: a behavioural difference measured at the live budget must be
re-measured at a longer one before it is called a capability. D-23's rule about quoting band-plus-pointer exists for
this reason, and here it is again, at 5,000 versus 15,000 hands.
