# Bet size has a large, resolvable price — measured with a verified ladder · 2026-11-07

No-limit heads-up, blinds 1/2, 100-chip stacks, five seed blocks × 600 paired hands, seats
alternating, the bettor's payoff taken in both seatings. The ladder is defined in **legal amounts** and
each rung was verified to choose different amounts: min-raise uses {2, 4}, 1× uses {4, 8, 24}, 2×
{8, 32, 60}, 4× {16, 84}, all-in {100} — so this measurement is not the earlier one, whose nominal pot
fractions collapsed onto the minimum raise (D-28).

Against D-21's folder, chips/hand and the paired difference from the minimum raise:

| rung | mean | paired vs min-raise |
|---|---|---|
| **min-raise** | **+0.68 ± 0.21** | — |
| 1 × (pot + to_call) | −8.89 ± 1.93 | **−9.57 ± 1.72** |
| 2 × | −7.77 ± 1.94 | −8.45 ± 1.73 |
| 4 × | −5.54 ± 1.97 | −6.22 ± 1.76 |
| all-in | −5.54 ± 2.72 | −6.22 ± 2.57 |

Against a caller every rung is the same, 1× through all-in measuring **+0.43 ± 3.57** and min-raise
+0.04 ± 0.36 — a caller never folds, so the size changes nothing.

## What it says

1. **Size has a price of 6–9.6 chips/hand** (D-6), resolvable at ±1.7–2.6, against the fixed-limit
   game where every action was EV-neutral to within noise. This is the signal the ladder never had.
2. **The minimum raise is best** — the only rung above zero.
3. **Among the large sizes, bigger is less bad** (1× worst at −8.89, 4× and all-in −5.54): the
   fold-equity counter-pressure is real, and a mid-size bet gets the worst of both — it folds out the
   hands that would call small and gets called by the hands that beat big. That non-monotonicity is a
   strategy worth learning, not noise: each paired interval clears.
4. **The gradient is folder-borne.** Against a caller it vanishes entirely, so a no-limit pool without
   folding opponents holds no price at all (D-26 required them in; D-21 provides them).

Caveats: one opponent type (a scripted folder), one stack depth (100), a scripted bettor rather than a
learner, and blinds 1/2 with a 2-chip minimum bet. It establishes the action space's price, not that a
learner finds the best rung — that is the question a build would exist to ask (D-28).
