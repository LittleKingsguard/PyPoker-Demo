# R2 deep run — 200,000 hands x 3 seeds, CPU · measured 2026-11-07

The shipped-run budget (200,000 hands per seed) on the PyTorch backend: **29,035 s (8.07 h)**, 600,000
hands, 0.0481–0.0487 s/hand — close to the 0.0451 the live pair predicted. Shipped R1 set untouched.

## The curve plateaus, it does not converge

Mean |TD error| per 20,000-hand interval, ten points per seed:

- seed 0: 3.08 2.90 3.20 3.04 3.00 3.13 3.00 3.15 3.09 3.13
- seed 1: 2.75 2.93 3.13 2.84 3.04 3.10 2.99 3.14 3.22 2.91
- seed 2: 3.08 3.05 3.09 2.99 3.15 3.10 3.15 3.02 3.19 3.00

Spread across seeds 0.03–0.33; the signal holds at ≈3.0 from the first interval to the last, over 200×
the live budget. `curves.md` §1 is why this is no verdict: a TD error has a noise floor set by payoff
variance, so a plateau fits both "converged to its floor" and "never learned". The table decides.

## The table says it did not get better

Live table, K = 4, 6 cells × 120 hands, 108.5 s, the same table seed as everything else:

| cell | result | chips/hand |
|---|---|---|
| `random` vs R2-deep | 11W/1T/**108L** | −4.533 to `random` |
| `always-call` vs R2-deep | **63W**/6T/51L | +0.817 to `always-call` |
| `oracle` vs R2-deep | **62W**/4T/54L | +1.333 to `oracle` |

Rating: R2-deep **+0.441 [0.250, 0.636]**, `always-call` +0.166, `oracle` +0.158, `random` −0.324.

Against the shipped live R1 (+0.531 [0.356, 0.722], 112–8 over `random`, 51–63 to `always-call`, 58–58
with `oracle`) the deep model is **indistinguishable and marginally worse**: a little more lost to the
oracle, slightly less to `random`. Intervals overlap; neither comparison is resolvable.

## What it means

**Training time is not this agent's lever.** 600,000 hands moved nothing that 3,000 had already
reached: it beats `random` decisively and loses to `always-call` and the `oracle`, exactly as the live
model did. D-8's premise — that pre-trained checkpoints demonstrate how much training time matters —
does not hold for R1/R2; the ladder's next variable must be representation or architecture, not scale.
Whether the rule or the capacity is the cause is a design question for a routed cycle (D-14).
