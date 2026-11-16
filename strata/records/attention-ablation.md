# Positions or attention? The ablation says attention does the heavy lifting · measured 2026-11-08

D-88 found attention + positional embeddings at **28.1 %**. This isolates the two: token embedding **+ positional
embedding + masked mean pool, no attention at all** — 17,305 parameters, same data, split and optimiser, run to
**180 epochs** so it is compared at convergence (D-85, D-14).

| variant | flop | turn | river | **overall** | at |
|---|---|---|---|---|---|
| tokens, mean, **no positions** | 8.8 % | 13.6 % | 16.8 % | **13.1 %** | 180 ep |
| tokens, mean, **+ positions** | 10.0 % | 15.4 % | 20.6 % | **15.3 %** | 180 ep |
| attention, **no positions** | 4.3 % | 14.9 % | 18.9 % | 12.7 % | 60 ep |
| **attention + positions** | 17.4 % | 30.6 % | 36.3 % | **28.1 %** | 60 ep, still rising |

## The decomposition

- **Positions alone add +2.2 points** (13.1 → 15.3, +17 %) — real, and concentrated on the later streets (river
  16.8 → 20.6), where knowing which card is the river matters.
- **Attention alone adds nothing** (D-6) (12.7 % against 13.1 %): with no positional signal it is permutation-invariant,
  exactly like the mean pool it replaced, and it cannot recover what it never sees.
- **Together they add +15.0 points over the plain mean** (13.1 → 28.1) — and **+12.8 points over the positional
  mean**, which is the attention layer's own contribution. **It nearly doubles the variance explained.**

## Why attention is worth that much

A positional mean can say *"the river is the 9♠ and I hold 9♥ 9♦"* but not **relate** them: pooling sums the slots
into one vector, so the fact that two of the seven cards **pair** is only representable as an accident of arithmetic.
Self-attention compares every slot with every other, so "the river paired my hole card" is directly expressible —
and that relation, not the position alone, is what most of the river's 36.3 % comes from.

## Caveats

- The attention figure is at **60 epochs and still rising** (28.01 → 28.14 over the last ten), so **28.1 % is a lower
  bound** and the +12.8 gap is if anything understated.
- The no-position attention run was also **unstable** (flop 10.5 % at epoch 20 falling to 4.3 % at 60), so its
  12.7 % is an average over a shaky trajectory rather than a settled value.
