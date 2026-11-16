# How different are the embeddings? The card rows barely move; the padding row is what moved · 2026-11-08

D-77 reported that `mean-real` moved the embedding **8.4×** further than the baseline. Measured per row, that is
**wrong**: the movement was the **padding row**, and the card rows are essentially unchanged (D-14).

| arm | padding row abs Δ | **card rows abs Δ, max** | card rows abs Δ, mean |
|---|---|---|---|
| **today** | 0.0056 | **1.2 × 10⁻⁵** | 2.1 × 10⁻⁶ |
| `mean-real` | 0.0468 (8.4×) | **7.7 × 10⁻⁵** (6.3×) | 1.4 × 10⁻⁵ |
| `no-squash` | 0.0179 (3.2×) | 1.8 × 10⁻⁵ (1.4×) | 1.1 × 10⁻⁶ |
| `masked-both` (probe) | **0.0 — exactly** | **1.2 × 10⁻⁴** (9.5×) | 1.6 × 10⁻⁵ |

## The card rows are the same vectors

Row-by-row cosine between the baseline and `mean-real`, for the 52 card rows:

**mean 1.000000, min 1.000000, max 1.000000** — the cards turn by a mean of **0.01 degrees**. The whole-table
cosine is 0.999928, and the whole of that 0.00007 comes from the padding row.

## Why, and what it means

The backward scatter is `add.at(gathered, ids, share)` over **every** addressed position — and 108 of an
observation's 122 positions are padding. Dividing by 14 rather than 122 raises every position's share 8.7×, so
the **padding row**, addressed 108 times per decision, absorbs 108 × share and moves 8.4× further; a card row,
addressed once or twice, moves 6.3× further **from an already negligible base**.

Only `masked-both` — padding excluded from the pool *and* from the scatter — makes the padding row move exactly
zero and the card rows move 9.5×. **And even that leaves a card row at 1.2 × 10⁻⁴ against an initial row scale of
0.55: two hundredths of a percent.**

## The correction this forces

**D-77's "the embedding now trains 8.4× faster" was a padding-row artefact**, and must be read as: the remedies
raise every row's gradient by the recovered factor, but a card row is addressed so rarely and so briefly that even
9.5× of almost nothing is almost nothing. The dilution D-75 diagnosed is real; the remedy is real; the **absolute**
learning on cards remains negligible, which is a second, independent reason a pooler with 108 padding positions
cannot learn card identity in 5,000–15,000 hands.

The answer to the question asked: **the `mean-real` embedding differs from the baseline in no card-relevant way.**
