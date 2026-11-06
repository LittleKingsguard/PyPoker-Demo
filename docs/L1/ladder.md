# PyPoker-Demo — L1 rung ladder as configuration

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-05
- **Covers:** brief §2's six rungs and the budgets L1 fixes for them (D-3, ASM-8)
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append

## 1. A rung is a configuration, not a script

There is one rollout driver (`engine.play_hand`), one encoding factory (`features.build_encoder`), one learner family (`agents.build_learner`), one training loop (`training.run`), one league (`evaluation.league`) and one evidence contract (`evaluation.protocol`). A rung is a row of data in `training.rungs()`, and its variants are configurations of that same machinery (D-3). The order of brief §2 is fixed and is never rearranged without an L0 decision (D-2, D-3).

What this buys, and it is the point of the design: no rung can drift into its own copy of the loop, so a rung-to-rung difference is attributable to the configuration and to nothing else (D-3), and a seventh configuration can be run without new code (`battery.md` §3 FAM-15).

## 2. The rung registry

Each rung trains and is evaluated against one frozen pool: the last M versions of the rung it inherits plus the three baselines, held identical for both arms of a pair (D-16, ASM-16, `league.md` §2).

| Rung | The axis it varies | Variants | Primary (the lineage) | Carried from | The pool it trains against |
|---|---|---|---|---|---|
| R1 | naive numeric encoding, hand-rolled NumPy (D-7) | `naive-numeric` | `naive-numeric` | — | the three baselines only: R1 is the first rung and the window is empty (D-16) |
| R2 | the same model in PyTorch, for the speed difference (D-7) | `naive-numeric-torch` | `naive-numeric-torch` | R1 primary | R1's last M snapshots plus the baselines |
| R3 | card tokenisation into a learned embedding | `card-tokens` | `card-tokens` | R2 primary | R2's last M snapshots plus the baselines |
| R4 | width against depth, one budget | `wide`, `deep` | `deep` | R3 primary | R3's last M snapshots plus the baselines, frozen for both arms |
| R5 | dense against sparse connectivity, one budget | `dense`, `sparse` | `dense` | R4 primary | R4's last M snapshots plus the baselines, frozen for both arms |
| R6 | a residual path against none, at R5's depth | `residual`, `plain` | `residual` | R5 primary | R5's last M snapshots plus the baselines, frozen for both arms |

R4, R5 and R6 each carry a pair, because a rung named for a technique proves nothing on a curve alone
(ASM-9, D-6): the pair is the control for the axis, and `plain` in R6 is the same stack without the
residual path (`strata/records/residual-stream-research.md`, D-3). The **primary** variant is the one
the next rung inherits, and it is the variant whose row the next rung's table carries (D-16). The
single-variant rungs are R1, R2 and R3.

## 3. The configuration schema

One rung configuration is a mapping; `training.rung(name)` resolves it, and `training.run` accepts either a rung name or a configuration written to this same schema, which is how the blind instance of `training.run` is expressed.

| Key | Meaning |
|---|---|
| `name`, `axis` | the rung's name and the one thing it varies, both from §2 |
| `carried_from`, `primary` | the previous rung's primary variant, and the variant the next rung inherits |
| `variants` | one or two variant entries |
| `pool` | the frozen pool the variants train and are evaluated against: its lineage, M, and the id every arm's run record must carry — and, for a configuration that is not in the registry, the membership declaration itself, which is how a custom league reaches the loop as data (D-16, ASM-16, `records.md` §8) |
| variant `backend` | `numpy` for R1, `torch` from R2 on (D-7) |
| variant `encoding` | `flat-numeric` for R1/R2, `card-tokens` for R3–R6 (D-3) |
| variant `architecture` | the kind — naive stack, token embedding, wide, deep, sparse, residual, plain — with its width, depth, sparsity and residual settings (D-3) |
| variant `learning_rule` | fixed for the whole ladder: masked Q-learning over the three-index vocabulary (ASM-7) |
| variant `hyper` | learning rate, exploration schedule, batch size, target update interval — identical within a comparison pair (ASM-7) |
| variant `param_budget`, `samples`, `seeds`, `device` | the budgets and the seed set of §6 |
| variant `snapshot_every` | how many hands between two snapshots that feed the rolling window (ASM-18) |
| variant `table` | the table budget this variant's row is measured at, `live` or `full` (`league.md` §6) |

## 4. What a comparison holds constant

`training.fairness(a, b)` reports this list, and the battery asserts it for every adjacent pair and every intra-rung pair (D-3, ASM-8, ASM-10):

- the game configuration from `engine.game_config` — identical for every rung (D-2);
- the three-index action vocabulary from `features.action_space` (D-2);
- the readout facts of `e2e-surface.md` §2 — the information set, identical for every encoding (D-3);
- the reward: the seat's net chip delta for the completed hand, delivered at the terminal decision, with no shaping (ASM-12);
- the learning rule and every hyperparameter above, the optimiser family, and the exploration schedule (ASM-7);
- the sample budget, counted in hands, and the parameter budget within ±2% as measured by `agents.param_count` (ASM-8, ASM-10);
- the frozen pool: the same pool id, the same members and the same window, recorded by both arms' run records (D-16, ASM-16);
- the seed set, and the table budget with its hand count per cell and its seat alternation (D-16);
- the checkpoint policy and the device policy (ASM-5, D-8).

The one thing that differs is the pair's declared axis, and `fairness` returns the axis it found. A pair that differs on anything else is not a reportable comparison (D-3, D-6).

## 5. R1 against R2 is a speed comparison

D-7 recreates the naive rung in PyTorch to measure the speed difference on identical work, so R1 and R2 declare the same encoding, the same model shapes, the same update rule and the same sample order, and differ only in `backend`. Their evidence is throughput and wall-clock per hand from `training.run`'s record and `harness.timings` (D-7, D-8), plus a same-work check: both variants must choose the same actions on the same seeded hands. R2 still reports the table its pool yields, because every rung does (D-16) — the report labels that pair as a parity comparison, and a parity row that shows a large skill difference is a defect, not a finding.

## 6. Budgets

| Quantity | Live run | Shipped checkpoint run |
|---|---|---|
| Hands per variant per seed | 1,000 | 200,000 (**no such run ships yet** — what ships is R1 at the live 1,000) |
| Seeds | the three of `protocol.md` §2 | the same three |
| Snapshots per run | 10, at equal intervals (`snapshot_every` = budget ÷ 10), of which the pool retains the last M (ASM-18) | the same rule |
| Table budget, hands per cell | `live`: 120 (ASM-14) | `full`: 1,500 (ASM-14) |
| Parameter budget per comparison pair | 10,000 ±2% | 10,000 ±2% (ASM-10) |

The live budget is what keeps a rung at a few minutes in a talk (D-8); the long runs are what show that training time
matters (D-8, ASM-5). The shipped set today is R1's, from a live-budget run — 1,000 hands per variant per seed — so its
curves are the learning signal of a run that had not converged, and no long-run checkpoint exists yet to compare it
against. Both budgets use the same protocol and the same table membership, so the difference between them is the sample
count and the cell size and nothing else (D-6, D-16). The measured risk that pure-Python `pokerkit` dominates the wall
clock is C-C2's, and it is answered by the sample-matched budget: the comparison stays fair if the engine is slow, and
only the clock pays (ASM-15, ASM-21).

## 7. Notebooks (D-5)

- One notebook per rung, in `notebooks/`, named for its rung: `r1-naive-numpy.ipynb`, `r2-naive-torch.ipynb`, `r3-card-embeddings.ipynb`, `r4-wide-and-deep.ipynb`, `r5-dense-and-sparse.ipynb`, `r6-residual.ipynb`. `training` owns the path.
- **What ships now: one of the six.** `notebooks/r1-naive-numpy.ipynb` exists and runs the R1 rung end to end. The other five are not written yet — do not go looking for them in the tree — and each follows the R1 notebook's pattern exactly: the same imports, the same ordered steps (the rung, a run, the pool it trained against, the device, the checkpoints, the live table, the rating, the shipped `full` table, the report, the curves), read off that rung's own name. A notebook is written when its rung has something to narrate, and none of the five is a different design (D-5, brief §1).
- A notebook is the talk's narrative: markdown for the story, and cells that call the declared entry points of `training` and `evaluation` only — the rung, a run, the pool it trained against, the device in use, the shipped checkpoints, the league table read at the `live` budget, the rating, the shipped `full` table, the report, and a plot of the curves the report already contains (D-5, D-16).
- A notebook may import `training`, `evaluation`, `matplotlib` and the standard library. It may not import `engine`, `features`, `agents` or `harness`, may not import from `src/`, and may not carry a loop over hands, a model, an encoder, a metric, a match, or a copy of any module's code (D-5).
- A notebook that needs something the surface does not expose has found an L2 or L1 defect and returns as an `ADJUDICATION` (modules.md §3, D-12); inlining the missing piece is the one thing D-5 forbids.
