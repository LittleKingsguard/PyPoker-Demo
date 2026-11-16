# Supervised equity with the board known: 2.4 % → 26 % of variance as the board arrives · 2026-11-08

D-83/D-84 taught the model equity from **hole cards alone**. This extends the supervised set to the community state:
every deal contributes three views — **flop (3 board cards), turn (4), river (5)** — the same showdown outcome seen at
three information states. 40,000 six-way deals → **720,000 samples** (240,000 per street), 119 one-hot inputs (2 hole
+ up to 5 board cards, unfilled board slots zero), 96-96 trunk, Adam 1e-3, 85/15 split, 60 epochs (D-14).

| known cards | variance explained (held-out) | calibration, predicted decile 1 → 10 |
|---|---|---|
| **2 (preflop, D-83)** | **2.4 %** | 10.8 → … → 28.3 |
| **5 (flop)** | **14.4 %** | 3.3 → 5.5 → 7.1 → 8.3 → 9.9 → 13.4 → 16.7 → 22.7 → 29.5 → **49.9** |
| **6 (turn)** | **20.9 %** | 2.0 → 3.5 → 5.1 → 6.4 → 8.3 → 12.7 → 15.7 → 22.9 → 33.8 → **56.3** |
| **7 (river)** | **26.0 %** | **1.1 → 2.1 → 3.5 → 5.3 → 7.5 → 11.6 → 15.8 → 22.9 → 36.6 → 61.6** |

**Every added board card multiplies the signal**: 2.4 % → 14.4 % → 20.9 % → 26.0 %, an **eleven-fold** rise from the
preflop view to the river. The calibration curve is monotone and close to the diagonal at every street, so the model
is not merely ordering hands — it is producing usable probabilities.

## The curve, not the point (D-85)

The river figure was still creeping at 60 epochs (25.11 → 25.72 → 25.98 over the last three checkpoints, +0.3–0.6 per
eight epochs), so **26.0 % is a lower bound** and the flop's 14.4 % is the least converged of the three.

## What it means for the project

**The card signal a decision has available depends on the street, and the spread is large.** Preflop — where every
learned policy in this project collapsed to one action — cards explain **2.4 %** of the outcome. By the river they
explain **26 %**. So the uniform preflop behaviour is not only a credit-assignment failure (D-84) but also the street
with the **least to learn from**, while the postflop streets — which the folding policies never reached — carry ten
times as much.

That is the strongest argument yet for the user's plan: **a supervised equity estimate is worth feeding in, and it is
worth feeding in most where the policy currently has least to go on.**
