# A simplified model: can a network learn six-way win probability from cards? · 2026-11-08

D-83's task, run as a supervised probe: predict **P(win at a six-way showdown)** from **the two hole cards alone**,
learned from 150,000 random six-way deals (900,000 samples, base rate 1/6 = 0.1667), a 34-input one-hot (rank + suit
per card), 64-64 MLP, Adam 1e-3, 12 epochs, 85/15 split (D-14).

**It learns equity.** Held-out MSE **0.13004** against **0.13325** for the constant predictor "always 1/6" — **2.4 %
of the variance explained** — with the predicted/empirical curve tracking by decile (8–11 % predicted → 10.8 %
empirical; 20–24 % → 22.2 %) and the correct ordering across hands:

| hand | predicted | empirical | error |
|---|---|---|---|
| AA | 44.72 % | **52.23 %** | −7.5 |
| KK | 39.70 % | 41.49 % | −1.8 |
| QQ | 36.56 % | 39.79 % | −3.2 |
| KQs | 29.59 % | 29.83 % | **−0.2** |
| AKo | 32.01 % | 28.22 % | +3.8 |
| 87s | 18.48 % | 16.72 % | +1.8 |
| 22 | 12.84 % | 14.14 % | −1.3 |
| 72o | 10.41 % | 8.70 % | +1.7 |

Most hands land within one to three points; the worst is aces (7.5 under, the model compressing the top of the
range). **The network can estimate poker equity from cards** — the thing it never managed for the policy.

## And the same measurement sizes the original failure

**Card identity explains 2.4 % of the variance in a six-way win/lose outcome** (D-6). The board and five unknown
opponent hands account for the rest. That is the signal the value function was trying to bootstrap from — the same
structure that left the action values nearly equal (D-72) and the game "nearly a coin flip".

## On the plan the user proposed

Feeding this probability into the policy model is the **right next step and cheap** (D-83): it is a well-calibrated,
supervised estimate of exactly the quantity the value function estimates from noisy returns — the prior that credit
assignment lacked. Two caveats: it is **marginal over random opponents**, so it must be recomputed or conditioned for
a real pool; and its 2.4 % ceiling means it should sharpen the **ranking** of hands, not make decisions profitable by
itself.
