# The exploration floor replicates: +11.30 and +12.92 chips/hand, all six runs clear zero

D-125's ε 0.60 result on seeds 1 and 2, both arms (same mask, card model, league; 5,000 train + 2,000 **greedy** hands;
D-14).

| arm | seed 0 | seed 1 | seed 2 | **mean** | 95 % CI (t, df 2) | card-dep |
|---|---|---|---|---|---|---|
| **base** | +11.81 ±5.03 | +12.67 ±5.75 | +9.44 ±3.97 | **+11.30** | **[+7.15, +15.46]** | 4 / 5 / 4 of 5 |
| **+ opponent model** | +10.49 ±4.24 | +14.44 ±6.25 | +13.84 ±4.85 | **+12.92** | **[+7.64, +18.21]** | 3 / 3 / 3 of 5 |

**Every one of the six runs clears zero on its own interval.** Against the fold baseline's **−0.60** and the earlier
break-even product runs (**+1.8 ±8.8**, D-105), this is a different regime: **+11.3 to +12.9 chips/hand, replicated.**

## What is now established

1. **The exploration floor is the mechanism.** Same representation, same pooler, same league — ε 0.05 gave +3.68 and a
   fold-99.7 % collapse; ε 0.60 gives **+11.30 to +12.92** and a **mixed** repertoire (fold 33–65 %, call 25–74 %,
   shoves 3–10 %). D-72 predicted exactly this.
2. **The opponent model is not harmful once the learner is not corner-locked** — the arm carrying it is **+1.62 chips
   better** on average, with intervals overlapping. D-123/D-124's "it destroys the policy" is a property of the
   collapsed learner, not of the model.
3. **Card-dependence replicates** in all six runs (3–5 of 5 distinct decisions on the loaded-deal suite) — against seven
   earlier experiments in which every policy played one action for every hand.

## What is **not** established

**That the play is ordered by strength.** The loaded-deal tables show card-dependence without monotonicity — one seed
raises `72o` twice while folding `22`, another shoves `AA` and calls `72o`. **D-116's monotonicity test is still owed**,
and it is the difference between "reads cards" and "plays well".

**Caveats:** the probe's learner, not the product's; 5,000 hands; one league of three checkpoints plus a caller; the
greedy evaluation makes the score a property of the learned policy rather than of exploration noise, but it is still a
score against *this* league.
