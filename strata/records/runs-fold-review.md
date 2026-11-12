# Every run, and which ones did *not* converge to never-fold · review 2026-11-08

Which runs ended with a policy that folds, against the dominant pattern of effectively never folding.
Product runs are `training.run` records; probes are disposable scripts whose fold rate belongs to a
hand-written tabular learner, not the build (D-6).
## Product runs — two exceptions in fourteen

| run | configuration | budget | fold decisions |
|---|---|---|---|
| R1 live (5 seeds) | two-seat NL, folders | 1,000 × 5 | **0 / 15,906** |
| R1 deep (`pool-11b03e0a5ff07c13`) | two-seat NL, folders | 200,000 × 3 | **0 / 19,487** |
| R1 + raiser in pool, and Double-Q in the same pool | two-seat NL, raiser | 20,000 × 2 | **0 / 17,181** and **0 / 21,858** |
| six seats, stage-3 | six-seat NL, folders + raiser | 1,000 × 5 | **0 / 15,127** |
| **net-chips control, 3 seeds** | two-seat NL, folders | 1,000 × 3 | **0.10 / 0.10 / 0.28 %** |
| **`stack-shortfall`, 3 seeds** | two-seat NL, folders | 1,000 × 3 | **0.82 / 3.33 / 3.48 %** |
| counterfactual, seed 0 | six-seat NL, mixed | 20,000 | **0 / 4,530** |
| **counterfactual, seed 1** | six-seat NL, mixed | 20,000 | **1,545 / 3,862 (40.01 %)** |
| counterfactual seeds 2–6 | six-seat NL, mixed | 20,000 | **diverged**, no verdict |

**Two runners break the pattern.** `stack-shortfall` folds at **all three seeds** (0.82 / 3.33 / 3.48 %
against net-chips' 0.10 / 0.10 / 0.28 % on the same pool) — small in absolute terms but **reproducible**.
The reveal-counterfactual folds much harder but at **one seed of two** (40.01 % against its own control's
0.00 %). Everything else folded effectively not at all, under 0.3 %.
## Probe runs — the control, and they fold

| probe | fold share |
|---|---|
| tabular Q vs a tight aggressor (with and without strength in its state) | **100 %** both |
| six-seat mixed table (net chips and counterfactual arms) | **87 %** both |
## What the pattern says

Folding is **reachable**, and the product reaches it in two places with opposite characters: the utility
axis **reliably but weakly**, the counterfactual **strongly but at one seed of two**. Neither establishes a
chip advantage — both arms' intervals overlap — and the utility's evidence stops at 1,000 hands while the
counterfactual's reaches 20,000, so the axes are not yet like-for-like (D-48).
