# The card model: design and performance · 2026-11-08
A supervised **six-way equity estimator**: given the cards a player can see, predict P(win at showdown) against five
opponents. It replaces the policy task's credit-assignment problem with a directly learnable target, and it is the
best-performing card model in the project.
## Architecture — 57,597 parameters
```
card ids (7 slots: hole1, hole2, board1-5;  0 = not yet dealt)
  Embedding(53 -> 50) 2,650  +  PositionalEmbedding(7 -> 50) 350
  2 x [ MultiheadAttention(5 heads, d=50) 10,200 + LayerNorm
        FFN 50->96->50 9,746 + LayerNorm ]
  masked mean over dealt slots only
  Linear(50->96) -> ReLU -> Linear(96->96) -> ReLU -> Linear(96->1) -> Sigmoid   14,305
```
Design choices, each measured rather than assumed: **positions** are worth **+2.2 points**, because attention and
mean-pooling are both permutation-invariant (D-89); **attention** adds a further **+12.8**, since positions alone
reach 15.3 % (D-89); the **padding mask** is exact because 89 % of the project's full observation is padding and its
pad row absorbed the learning (D-78/D-79); there is **no squash**, which costs a third of the signal (D-77, D-87);
and the **seven fixed slots** make the zero-id plus mask *be* the "unknown board" signal (D-86).
Trained on 40,000 random six-way deals → **720,000 samples** (6 seats × 3 street views of one showdown), 85/15 split,
target 1.0 win / 1/n tie / 0.0 loss, cross-entropy, Adam 1e-3, batch 4,096.
## Performance — variance of the win/lose outcome explained
| known cards | R² | representation | params | R² |
|---|---|---|---|---|
| 2 (preflop) | **2.4 %** | tokens + mean pool | 16,955 | 13.1 % |
| 5 (flop) | **17.4 %** | tokens + positions + mean | 17,305 | 15.3 % |
| 6 (turn) | **30.6 %** | flat one-hot | 20,929 | 20.4 % |
| 7 (river) | **36.3 %** | **positions + attention** | **57,597** | **28.1 %** |
| pooled | **28.1 %** | | | |
## For the presentation
- **Say**: cards explain **2.4 %** of a six-way outcome preflop and **36 %** at the river — the signal arrives with
  the board — and the sequence model reads it **38 % better** than a flat encoding once relations between cards are
  expressible.
- **Say**: it is **calibrated**, not merely ordered — predicted deciles track empirical win rates at every street
  (river 1.1 → 61.6 %).
- **Do not say** it is a poker agent: no legal mask, no action head, and its target integrates over **random**
  opponents rather than the league's folders and raisers.
- **Do not say** these are ceilings: the attention model was still gaining **+1.3 points per twenty epochs** at 120,
  so 32.4 % is a **lower bound** and a longer run is in flight (D-85's rule — the curve, never the point).
