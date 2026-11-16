# Attention on the flat one-hot: works early, plateaus lower, then degrades · measured 2026-11-08

D-96 asked whether the attention mechanism can run on the **one-hot flat encoding** instead of learned card
embeddings. It can: each slot's 17-dim one-hot is projected by `Linear(17→50)`, a positional embedding is added, and
the same two-layer five-head attention, masked mean and head follow. 55,847 parameters against 57,597 for the token
version; same data, split and optimiser (D-14).

| epochs | **one-hot + attention** | tokens + attention | lead |
|---|---|---|---|
| 20 | 23.69 % | 25.13 % | tokens +1.4 |
| 40 | 28.77 % | 27.31 % | one-hot +1.5 |
| **60** | **29.32 %** | 28.14 % | one-hot +1.2 |
| 80 | **29.43 %** (peak) | 30.58 % | tokens +1.2 |
| 120 | 29.09 % | 32.37 % | tokens +3.3 |
| 160 | 27.46 % | 34.04 % | tokens +6.6 |
| 200 | **27.08 %** | 34.09 % | tokens +7.0 |
| 400 | — | **40.0 %** | — |

## The answer, in two parts

**Yes — attention transfers to the one-hot encoding, and early on it is competitive**: at 40–60 epochs it is
**slightly ahead** of the token version (29.3 against 28.1), so the attention mechanism does not require a learned
embedding to work.

**But it does not scale with training the way the token version does** (D-85): it **peaks at 29.4 % around epoch 80
and then declines to 27.1 % by 200**, while the token version climbs through the same window (28.1 → 34.1) and reaches 40.0 %
at 400. So the learned embedding buys **late-training capacity**: 52 free vectors that can move independently, against
a projection that must share its weights across all seven positions.

## What that means for the deck

The architecture's contribution is **attention plus positions**, worth +12.8 points over a positional mean (D-89), and
it can be demonstrated on the flat encoding with no embedding at all. The **learned card embedding** is what keeps the
model improving past ~30 % — which is the honest form of the "tokenise the cards" claim: it is not needed for the
mechanism, it is needed for the ceiling.

**Caveat (D-85):** the one-hot arm ran to 200 epochs and was **declining** at the end, so its 27.1 % is a settled
decline rather than an unfinished climb — the opposite of every other curve in this line.
