# Did the tokens converge? Not at 12 epochs — they plateaued at 96 % of flat · 2026-11-08

D-84 compared the representations at 12 epochs. This traces both to 40 epochs on the same data and split, reporting
held-out MSE, the variance explained, and — for the token path — how far the **embedding** moved each epoch (D-14).

**Flat one-hot: converged by epoch 16.** R² 1.94 % (ep 4) → 2.30 % (ep 8) → **2.45 % peak (ep 16)**, then stationary
at 2.41–2.44 % with changes of ±0.00004. The later epochs are noise, not improvement.

**Tokens: still moving at 12, plateau by ~32.**

| epoch | R² | change | embedding movement |
|---|---|---|---|
| 2 | 1.67 % | −0.00047 | 0.077 |
| 12 | 2.07 % | −0.00001 | 0.026 |
| 20 | 2.26 % | −0.00003 | 0.023 |
| **32** | **2.34 %** | +0.00002 | 0.013 |
| 40 | 2.32 % — flat | +0.00005 | 0.015 |

**At 12 epochs the tokens were still improving** — R² rose from 2.07 % to 2.34 % over the next twenty epochs while the
embedding kept moving — and they converge at **~2.34 %, about 96 % of flat's 2.45 %**, after roughly twice the epochs.

## The correction this forces

**D-84's "88 % of flat" was a 12-epoch snapshot** (D-6); converged, the figure is **96 %** and the residual gap is
**0.11 points of variance** — a small, real representational difference, not a failure. The token encoding needs **~2×
the training** to reach it, which is the quantitative form of "an embedding has more to learn than a one-hot".

The argument is unchanged in direction and stronger in size (D-84): the token representation reaches within 4 % of the flat
one's explanatory power **on a task where learning succeeds**, so the policy's card-blindness was never an
embedding-capacity limit.

## Method note

A single-epoch-count comparison would have reported the token path as **12 % worse** than it is. Quoting a trained
model without a convergence trace is the same class of error as quoting a behavioural difference from the live budget
(D-82): a snapshot mistaken for a ceiling.
