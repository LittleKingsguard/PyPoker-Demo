# What the 108 padding tokens are for · measured 2026-11-08

D-78 found the token embedding's learning goes almost entirely to the padding row. This states what the padding
is: **pre-allocated capacity for the worst case**, because the observation is a fixed-width sequence (D-14).

From the shape's own declaration — `1 + seats + 2 + 5 + seats + 1 + 1 + 2 = 12 + 2 × seats`, then the history
block:

| segment | six seats | what it holds |
|---|---|---|
| street · seat block | 1 · 6 | the street id; the acting seat's id (96–101) |
| hole · board | 2 · 5 | the acting seat's two cards (no other seat's, D-43); the dealt board |
| stacks | 6 | one bucket id per seat |
| `pot` · `to_call` · `limit` | 1 · 1 · 2 | the amount facts |
| **subtotal** | **24** | |
| **history** | **98** | one id per applied action, sized for the **longest legal hand** at this shape |
| **total** | **122** | |

Measured on a preflop decision, block by block: **14 tokens real, 108 pad 0 — 89 %.** The history block is the
bulk (98 slots, **zero** entries preflop, a handful even in a long hand) and the board's five slots are empty until
cards are dealt; everything before the history is essentially all real.

**The padding is not waste in principle** (D-6): a fixed-width tensor is what a feed-forward trunk needs — every
decision on every street must produce the same shape — so the width fits the worst case and the rest must be
filled. That is ordinary sequence practice, and its standard companion is a **mask**: pool and learn over the real
positions only.

**What went wrong is the missing mask, not the width.** The token path pools `rows.mean(dim=0)` over all 122
positions and scatters the gradient to all 108 pad positions, so **89 % of the trunk's input is one constant
vector** and the pad row absorbs most of the learning signal — exactly the per-row asymmetry D-78 measured (pad
row 8.4×, card rows 0.01°).

**The fix is the mask**: keep the fixed 122 tokens, exclude pads from pool and scatter. The `masked-both` probe is
that change and moved card rows 9.5× — still only 0.02 % of their scale at 5,000 hands, the second, separate limit
D-78 recorded.
