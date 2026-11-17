# Three seeds: the base arm replicates, the bet-size advantage does not · measured 2026-11-08

D-119's four-arm test rerun on seeds 1 and 2 for the two positive arms (masked pooling, attn-60, league, 5,000 train +
2,000 greedy hands each; D-14).

| arm | seed 0 | seed 1 | seed 2 | **mean** | 95 % CI (t, df 2) | card-dep per seed |
|---|---|---|---|---|---|---|
| **base** (card + strength + facts) | +6.29 ±3.63 | +5.52 ±2.84 | +9.09 ±4.44 | **+6.97** | **[+2.29, +11.64]** | 2 / 3 / 4 of 5 |
| **+ `bet_size`** | +7.96 ±3.99 | +1.11 ±2.40 | +4.08 ±2.82 | +4.38 | [−4.15, +12.92] | 2 / 4 / 3 of 5 |

**Every base-arm seed clears zero on its own interval; `bet_size` seed 1 does not** ([−1.29, +3.50]).

## The correction this forces

**D-119's "the bet size is worth +1.7 chips/hand" was a one-seed difference and does not replicate.** Across three
seeds the **base arm is the better one by +2.59 chips/hand**, and it is the consistent one (sd 1.88 against 3.44). The
+1.7 was seed 0's luck, measured in exactly the way D-82's flicker was and dying the same death.

**What does replicate: card-dependence.** Both arms are card-dependent in **all three seeds** (2–4 distinct decisions out
of 5 on the loaded-deal suite) — the first replicated card-dependent policy in this project, after seven experiments in
which every policy played one action for every hand.

## Where this leaves the integrated test

| claim | status |
|---|---|
| masked pooling + card representation + strength beats the fold baseline against the league | **replicated**: +6.97 ±4.67, three of three seeds clear |
| card-dependence | **replicated**: 2–4 of 5 in every seed, both arms |
| `bet_size` helps | **not replicated** — one seed's difference, and the base arm is better on three |
| the opponent model helps | **refuted**: both arms carrying it collapsed to fold-100 % (D-119) |

**Still owed:** the same comparison on the product's learner (the probe's head is not the product's), and the
monotonicity test (D-116) on the base arm, whose card-dependence is real but has not been shown to be *ordered* by
strength.
