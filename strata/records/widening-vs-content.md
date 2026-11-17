# It is the opponent model's content, not the extra width · measured 2026-11-08

D-123 concluded that "three extra dimensions, whatever they contain, move this learner into the fold corner". That was
an untested hypothesis; this tests it with three arms that differ **only** in what the three extra dimensions hold
(mask, card model, league, 5,000 + 2,000 hands, seed 0, D-14).

| arm | dim | extra dimensions hold | chips/hand | census | card-dep |
|---|---|---|---|---|---|
| base | 56 | — | +3.68 ±3.22 | fold 78 %, call 22 % | 3/5 |
| **+ constant** | 59 | three zeros | **+2.71 ±2.03** | fold 92 %, call 8 % | 3/5 |
| **+ noise** | 59 | three irrelevant but **varying** values | **+8.52 ±3.42** | fold 78 %, call 22 % | 4/5 |
| **+ opponent model** | 59 | the per-seat artefact's three action probabilities | **−0.56 ±0.11** | **fold 99.7 %** | 1/5 |

## The hypothesis is refuted

**Widening the input is harmless**: three constant dimensions cost 1 chip (+2.71) and three *varying* dimensions are the
best arm measured (+8.52). So it is **not** the extra width, and it is **not** the perturbation of the input space.

**It is specifically what the opponent model carries** (D-124). Its three probabilities are near-constant *within* a run — the
league is three fixed policies, so the model emits three nearly-fixed vectors — and that makes them a **table-identity
signal**. Handed that, the policy can learn "against these raisers, fold", and since folding is never punished harder than
the blind while raising into raisers is, the fold corner becomes the reachable optimum: **99.7 % fold, −0.56**.

## What this means (D-124)

- The opponent model is **not** unusable because it is inaccurate, and **not** because it widens the input. It is
  unusable because **as an identity signal it makes the degenerate policy profitable-looking** on this league.
- That is a statement about the **league** (D-124), not about opponent modelling: a pool containing raisers rewards folding, and
  any input that identifies the pool hands the learner the exploit — "always fold" — in three numbers.
- The fix is on the **learner/pool** side: an exploration floor that keeps the aggressive actions sampled (D-72's
  ε_end 0.60 → 0 % fold), or a pool where folding is not free.

## Caveat

One seed per arm; the base arm itself ranges +3.68 to +9.09 across seeds (D-120), so the **magnitudes** are not
established — but the **collapse is categorical** (99.7 % fold against 78 %), and it appears in exactly the arm that
carries the identity-like signal.
