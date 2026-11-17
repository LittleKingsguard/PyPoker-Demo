# The trained model never folds — it goes to the reveal with every hand · measured 2026-11-08

Does the trained policy call everything down, or fold when raised into on a bad hand? Measured on the 15,000-hand
product learner (`net-chips`, seed 0) against **three** opponent sets (D-14).

| opponents | hands | reached the reveal | folds |
|---|---|---|---|
| the league (folder / 50-50 raiser / 83 % raiser / caller) | 2,000 | **100.0 %** | **0** |
| **five copies of the 20 %-all-in raiser** | 1,200 | **100.0 %** | **0** |
| five copies of the scripted oracle | 1,200 | **100.0 %** | **0** |

**Zero folds in 4,400 hands.** Every hand the model played went to showdown.

## Not even with a bad hand facing an all-in

Conditioned on **facing a bet**, bucketed by the supervised model's own strength estimate:

| strength at the decision | decisions facing a bet | folded |
|---|---|---|
| **weak (< 0.10)** | **2,261** | **0 (0.0 %)** |
| mid (0.10 – 0.25) | 897 | 0 (0.0 %) |
| strong (≥ 0.25) | 1,642 | 0 (0.0 %) |

It calls all-in with the weakest hands the card model can score at the same rate as with its strongest.

## The shape this makes

The policy has only two observed states, and they are the two corners of the action simplex: **fold 100 %** at 5,000
hands (D-104), **fold 0 % / call ≥ 83 %** at 15,000 (here). **It never learns a selective fold rule.**

That is D-72's fold-pinning seen from the other side: the value spread between fold and its alternatives (+0.0157) is
smaller than the exploration noise, so whichever corner the early updates reach, the ramp to ε = 0.05 locks in.

## What it costs

Against the league it is **break-even** (D-105: +1.82 ±8.81), and against strong opponents it pays off every made hand,
because it can only win by showing down the best hand. **A policy that never folds cannot bluff and cannot be bluffed
out** — the exact behaviour the project's bonus goal was about.
