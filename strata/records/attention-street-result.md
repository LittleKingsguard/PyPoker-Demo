# Attention is the fix: 28.1 % of variance, beating the flat encoding · measured 2026-11-08

D-87 found the masked-mean token path at **65 %** of the flat encoding on the three-street task because a mean pool is
permutation-invariant and a board is not. This replaces the pool with **self-attention over the 7 slots** (hole 1,
hole 2, board 1–5), 2 layers, 5 heads, 50-wide, LayerNorm + feed-forward, masked mean of the transformed rows, and —
for the decisive variant — **learned positional embeddings added by slot index**. 57,597 parameters, same data, split
and optimiser, 60 epochs (D-14).

| representation | flop | turn | river | **overall** |
|---|---|---|---|---|
| tokens, masked mean (D-87) | 8.8 % | 13.6 % | 16.8 % | 13.1 % |
| **flat one-hot (D-86)** | 14.4 % | 20.9 % | 26.0 % | 20.4 % |
| **attention + positional** | **17.4 %** | **30.6 %** | **36.3 %** | **28.1 %** |
| attention, **no** positional | 4.3 % | 14.9 % | 18.9 % | 12.7 % |

## Three findings in one table

1. **Attention with positions beats the flat encoding by 38 %** (28.1 against 20.4 % overall) and wins on every
   street — most at the turn (**30.6 against 20.9**) and the river (**36.3 against 26.0**), which is where slot
   identity matters most.
2. **Position is the whole fix.** The same attention *without* positional embeddings scores **12.7 %** — the mean-pool
   level, and unstable (flop 10.5 % at epoch 20 falling to 4.3 % at 60). Attention alone is permutation-invariant
   too; **attention plus positions** is what carries the information.
3. **The flat encoding was not the ceiling** — it was the best *simple* representation, and a sequence model with
   positions clears it by a wide margin.

## Convergence caveat (D-85)

Still creeping at 60 epochs (28.01 → 28.14 over the last ten), so **28.1 % is a lower bound**; the turn and river
figures are still rising and would gain from more epochs.

## What this settles for the plan

The supervised module should be **attention with positional embeddings over the card slots**. It is now the strongest
representation measured in this project — 28.1 % of six-way outcome variance explained, against 26 % for the best
flat street model, 16.8 % for the best mean-pool token model and 2.4 % for preflop cards alone — and it makes the
user's original intuition concrete: **the board is a sequence, and a sequence model is what reads it.**
