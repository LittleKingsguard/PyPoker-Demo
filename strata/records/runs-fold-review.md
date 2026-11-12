# Every run, and which ones did *not* converge to never-fold · review 2026-11-08

Which runs ended with a policy that folds, against the dominant pattern of never folding. Product runs are
`training.run` records; probes are disposable scripts, listed separately because their fold rate is a
property of a hand-written tabular learner, not of the build (D-6).
## Product runs — one exception in twelve

| run | configuration | budget | fold decisions |
|---|---|---|---|
| R1 live (five seeds) | two-seat NL, folders pool | 1,000 × 5 | **0 / 15,906** |
| R1 deep (`pool-11b03e0a5ff07c13`) | two-seat NL, folders pool | 200,000 × 3 | **0 / 19,487** |
| R2 deep (fixed-limit) | two-seat FL, folders pool | 200,000 × 3 | **0** |
| R1 + raiser in pool | two-seat NL, raiser pool | 20,000 × 2 | **0 / 17,181** |
| Double-Q + raiser pool | two-seat NL, raiser pool | 20,000 × 2 | **0 / 21,858** |
| raiser pool, live budget | two-seat NL, raiser pool | 1,000 × 3 | **0 / 12,856** |
| six seats, stage-3 | six-seat NL, folders + raiser | 1,000 × 5 | **0 / 15,127** |
| counterfactual, seed 0 | six-seat NL, mixed pool | 20,000 | **0 / 4,530** |
| counterfactual, seed 1 | six-seat NL, mixed pool | 20,000 | **1,545 / 3,862 (40.01 %)** |
| counterfactual control, seed 1 | same, member `none` | 20,000 | **0 / 3,742** |
| counterfactual seeds 2–6 | six-seat NL, mixed pool | 20,000 | **diverged**, no verdict |

**The one exception is the reveal-counterfactual member at seed 1**: 1,545 folds of 3,862 decisions
(40.01 %), against its own control arm at 0.00 % on the same pool, seeds and budget. Every other product
run — two game shapes, three seat counts, four pools, two rules, four budgets, and the member itself at
seed 0 — folded **not once**.
## Probe runs — the control, and they fold

| probe | configuration | fold share |
|---|---|---|
| tabular Q vs a tight aggressor (with and without strength in its state) | **100 %** both |
| six-seat mixed table (net chips and counterfactual arms) | **87 %** both |
## What the pattern says

Folding is **reachable** — four probe configurations reach it, and the product reaches it once — but under
the shipped learner it appears in **one run of twelve**, and in that run **only at one seed of two**. The
member's seed 0 and its own control at seed 1 both sit at zero, so the effect is real where it appears and
not reproducible across seeds at the shipped budget: the attractor lottery of `attractor-sweep.md`, now
with its first exception rather than an absence.
