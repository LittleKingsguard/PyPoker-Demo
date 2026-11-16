# Annealing from a hot start: no rescue, and it erases the token flicker · measured 2026-11-08

D-81's pass: the learning rate scheduled from **3 × 10⁻² down to the declared 10⁻³** geometrically over the first
60 % of 5,000 hands (verified in the run: `rate 3.00e-02 -> 1.00e-03 over 5000 steps`), applied to the flat
baseline and to the token frontier (mask + `no-squash`), both at `stack-shortfall`, six seats, seed 0 (D-14).

| arm | fold share | fixed-rate reference | card-dependent? |
|---|---|---|---|
| **flat** | **91.3 %** | 78–87 % | **yes** — 2/5 distinct at the opening seat, 3/5 at big-blind |
| **tokens** (mask + no-squash) | **90.8 %** | 89.5 % | **no** — 1/5 in both seatings |

## What the hot start did

**Nothing good, on either arm.** It raised the fold share on both (+13 points for flat against its fixed-rate
record, +1.3 for tokens) and it **destroyed the one card-sensitivity the project had produced**: with a fixed rate
the masked-no-squash token arm separated 72o from the four stronger hands at the opening seat (D-80); under
annealing **all five hands are identical at both seats**.

## And the discrimination it left is not sound play

The annealed flat model is card-dependent but not sensible: at the opening seat it **folds AA**, shoves all-in with
KQs, folds 22, 87s and 72o. At big-blind it gives three distinct sequences across the five hands. So it reads the
cards, and what it reads them as is wrong — which is a reminder that "card-dependent" is a necessary condition for
a poker agent and nowhere near a sufficient one.

## Why a hot start plausibly hurts here

D-65 established the usable window for `lr × reward-scale`; a 30× hotter start takes the first few hundred updates
well above it on the risk-averse utility's larger values, moves the parameters a long way before the exploration
ramp has produced any diversity of experience, and lands the learner in the same attractor the annealed end cannot
leave. The schedule ends at the rate that has already been shown, on its own, to pin the policy to fold (D-72).

**Conclusion:** annealing is not the missing mechanism. The pinning is the exploration loop (D-72) and the
discrimination is the representation (D-79/D-80); a schedule over the learning rate touches neither.
