# Folding, reproducibly: the risk-averse utility at six seats · measured 2026-11-08

D-49's combined run at the reduced length: six seats, 100-chip stacks, the mixed pool
`pool-8386c3ef83ae48b2` (three anchors, D-21's three folders, a trained six-seat raiser), **15,000 hands ×
seeds 0, 1, 2**, ties excluded (D-14). Two arms, one key apart:

| arm | seed | decisions | fold | raise | check-call | chips/hand [95 %] |
|---|---|---|---|---|---|---|
| **counterfactual + shortfall** | 0 | 2,483 | **74.71 %** | 13 % min | 9 % | −1.839 [−3.30, −0.38] |
| " | 1 | 2,383 | **77.97 %** | 5 % min | 10 % | −1.064 [−2.79, +0.66] |
| " | 2 | 2,374 | **77.46 %** | 9 % min | 6 % | −1.484 [−3.34, +0.37] |
| **shortfall only (control)** | 0 / 1 / 2 | 2,386 / 2,201 / 2,386 | **78.33 / 87.01 / 77.58 %** | 7 % half | — | −1.922 / −0.480 / −1.188 |

Wall clock 7,983 s and 7,893 s (**4.4 h** for both arms).
## The finding: the utility is decisive, the counterfactual adds nothing

**Both arms fold at every seed, 74–87 %** — and the control arm, which has the counterfactual switched
off, folds *more*. So the reproducible folding comes from **`stack-shortfall` (D-20)**, not from
`reveal-counterfactual`.

That is attributable: same pool id, same shape, same seeds.

| arm on the same pool and shape | fold |
|---|---|
| `net-chips`, 20,000 hands, seeds 0–1 | **0.00 % / 0.00 %** (D-44) |
| `net-chips`, 1,000 hands, five seeds | **0 %** (D-34) |
| `stack-shortfall`, 15,000 hands, seeds 0–2 | **78.3 / 87.0 / 77.6 %** |

So the six-seat configuration that folds reproducibly is **risk-averse utility + a mixed pool**, and the
counterfactual is not required for it. The D-44 result stands as recorded (40 % at one seed of two), but
the mechanism that makes folding **reliable** is the utility.
## What it does not show

- **Folding 77–87 % is not profitable here** (D-6): chips/hand are −0.48 to −1.92 and two of six intervals
  reach above zero, so heavy folding is a *behaviour*, not yet a *win*.
- **Seat count dominates the utility's effect**: two seats gave 0.82–3.48 % (D-48), six give 77–87 %.
- **No criterion was pinned** (D-49), so this is a measurement and not a verdict.
