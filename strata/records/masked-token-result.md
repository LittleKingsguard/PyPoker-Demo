# With the mask: the first token model that notices its cards, weakly · measured 2026-11-08

D-79's fix applied — padding masked out of **both** the pool and the gradient scatter — and rerun over the same
three arms, `stack-shortfall`, `card-tokens`, 5,000 hands × seed 0, six seats (D-14).

| arm | fold | pad row movement | card-row movement | card-sensitive? |
|---|---|---|---|---|
| **mask** (mask + mean over real) | **93.1 %** | **0.0 exactly** | 1.17 × 10⁻⁴ | **no** — every hand folds |
| **mask + `no-squash`** | **89.5 %** | **0.0 exactly** | 1.33 × 10⁻⁴ | **yes, weakly** — see below |
| mask + `sum-pool` | **diverged** past the 1e6 band | — | — | — |

**The mask works as designed**: the padding row moves **exactly zero** in both surviving arms, against 8.4× the
card rows' movement without it (D-78).

## The card sensitivity, stated narrowly

`mask + no-squash`, five hole sets, one dry board, both seatings:

| hole | opening seat | big-blind seat |
|---|---|---|
| AA · KQs · 22 · 87s | raise-quarter / **raise-half** | raise-quarter / raise-half |
| **72o** | raise-quarter / **raise-quarter** | raise-quarter / raise-half |

- **Opening seat: two distinct sequences** — 72o is separated from the four stronger hands, on the flop.
- **Big-blind seat: one sequence** — all five hands played identically.

So this is the **first token model in the project to distinguish a hand at all** (D-71, D-73 and the whole of
D-52/56/67 were unanimous card-blind), and it is a narrow signal: **it separates only the weakest hand, only on one
street, only in the seating where folding is legal.** Everything stronger is treated alike.

## Why the narrowness makes sense

The two changes needed to produce even that much were **both** necessary: the mask alone leaves every hand folding,
`no-squash` alone changes the constant without discriminating (D-77). The card rows still move only
**1.3 × 10⁻⁴** against a row scale of 0.55 — 0.02 % — because a card is addressed once or twice per decision and a
hand thousands of times over a run.

So the result is: **the representation can carry card information once the padding stops dominating it, and the
learner is still far from using it.** That is a real advance on an unanimous null, and it is not a card-aware agent.
