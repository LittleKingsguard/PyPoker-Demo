# Why the embedding learns at 0.3 %: a 122-fold gradient dilution · measured 2026-11-08

D-74 found the token embedding is still its initialization after 15,000 hands. This finds why, in the backward
pass itself (D-14).

**The mechanism, in one line of code.** `numpy_backend.py`:
`numpy.add.at(gathered, ids, (upstream / len(ids)) * slope)` — every addressed embedding row receives the upstream
gradient **divided by `len(ids)`**, the *whole* observation, padding included.

| quantity | six-seat token encoding | flat encoding |
|---|---|---|
| observation length | **122** (fixed) | 433 |
| positions carrying a real token | **14** | 433 |
| pooling denominator applied | **122** | — (none) |
| squash slope (bounded embedding) | **≤ 0.5** | — |
| **gradient a card row gets per appearance** | **≤ 1/122 × 0.5 ≈ 0.0041** of upstream | its own value |

**Only 14 of 122 positions are real, and each is still divided by 122.** The padding dilutes 8.7× for nothing,
and the reciprocal-122 dominates: a card row gets about **0.4 %** of a dense slot's gradient, and only when that
exact card appears.

**The arithmetic closes against the measurement.** `appearances × lr × upstream × 0.0041` at `lr = 1e-3`, upstream
of order `1e-2` (the normalised value scale) and hundreds to a couple of thousand appearances gives **order 1e-4**
— exactly the measured **max |Δ| 0.0004** against a row scale of 0.14. The 0.3 % is predicted, not accidental.

**Four remedies, cheapest first.** (1) Divide by the **real** token count or mask the padding out of the pool —
recovers 8.7× and is one line. (2) Drop the squash or widen the embedding scale — another ≤ 2×, and removes a
saturation risk. (3) Sum-pool instead of mean-pool — no denominator at all, at the cost of a count-dependent
input. (4) Use the flat encoding — no pooling, and the only card-aware encoding in the project (D-71).

**Consequence for every earlier encoding result.** The token encoding never had a fair test: its card
representation received **0.4 %** of the learning signal the flat encoding's did, for the whole of every run.
D-52, D-56, D-67, D-71 and D-73 are therefore statements about an **untrained embedding**, not about tokenisation
as an idea — the honest way to report them, and the reason the flat encoding is the project's only card-aware
agent.
