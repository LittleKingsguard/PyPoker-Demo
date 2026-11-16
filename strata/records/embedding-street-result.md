# Embeddings on the street task: 65 % of the flat encoding, and the mean pool is why · measured 2026-11-08

D-86's three-street supervised data — 720,000 samples over flop / turn / river views — run through the **token
architecture**: up to 7 card ids (`1 + 4·rank + suit`, pad 0 for an unknown board slot) → embedding (53 × 50) →
**masked mean** over the real rows → 96-96 trunk → sigmoid, 16,955 parameters, same split and optimiser, taken to
**180 epochs** so the comparison is at convergence and not a snapshot (D-85, D-14).

| representation | params | flop | turn | river | overall |
|---|---|---|---|---|---|
| **flat one-hot (119)** | 20,929 | **14.4 %** | **20.9 %** | **26.0 %** | **20.4 %** |
| **tokens, masked mean** | 16,955 | 8.8 % | 13.6 % | 16.8 % | **13.1 %** |
| tokens + squash (60 epochs) | 16,955 | 4.2 % | 4.6 % | 5.3 % | 4.7 % (still climbing) |

**The token path converges at 65 % of the flat encoding's explanatory power** (13.1 against 20.4 %), and the deficit
grows with the amount of state: flop 61 %, turn 65 %, river 65 %. On the *two-card* task the same architecture reached
**96 %** (D-84/D-85) — so something about the board is what it cannot represent.

## Why: the mean pool destroys position

`mean over rows` is **permutation-invariant**: `(As, Kd)` and `(Kd, As)` pool to the same vector, which is exactly
right for two hole cards — and exactly wrong for a board, where **which slot a card occupies carries information**.
The pooled vector cannot tell the turn from a flop card, cannot tell which board card is the river, and cannot express
"the river paired my hole card" differently from "a flop card did". The flat encoding hands the network that
information by construction: slot *i* is slot *i*.

So the token path's deficit here is **not** the embedding's capacity and **not** the squash alone — it is an
architectural mismatch between a **set** view and a **sequence** view of the board. The remedies that would fit:
positional embeddings added to each row, per-slot pools rather than one pool, or attention over the sequence.

## What it establishes

- **The squash costs most of the signal again**: 4.7 % against 13.1 % at equal epochs on the same architecture.
- **The 96 %-of-flat result was task-specific**: with two cards the pooling is harmless, so the earlier conclusion
  ("the embedding is not the limit") holds only where position does not matter — and a poker board is precisely where
  it does.
- **For any board-aware module the flat encoding is the right choice today**; a token path needs positional treatment
  before it can compete.
