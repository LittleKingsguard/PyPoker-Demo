# PyPoker-Demo — L1 rung ladder as configuration

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 10 · **Date:** 2026-11-09
- **Covers:** brief §2's six rungs and the budgets L1 fixes for them (D-3, ASM-8), the set of learning rules a rung declares (D-19), the utility its arms are trained under (D-20) and the folding baselines a configuration may add to its pool (D-21)
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append

## 1. A rung is a configuration, not a script

There is one rollout driver (`engine.play_hand`), one encoding factory (`features.build_encoder`), one learner family (`agents.build_learner`), one training loop (`training.run`), one league (`evaluation.league`) and one evidence contract (`evaluation.protocol`). A rung is a row of data in `training.rungs()`, and its variants are configurations of that same machinery (D-3). The order of brief §2 is fixed and is never rearranged without an L0 decision (D-2, D-3).

What this buys, and it is the point of the design: no rung can drift into its own copy of the loop, so a rung-to-rung difference is attributable to the configuration and to nothing else (D-3), and a seventh configuration can be run without new code (`battery.md` §3 FAM-15).

## 2. The rung registry

Each rung trains and is evaluated against one frozen pool: the last M versions of the rung it inherits plus the three anchor baselines, held identical for both arms of a pair (D-16, ASM-16, `league.md` §2). **The six rows below declare no folder of D-21**, so no rung's table membership, cells or rating moves with that decision; a configuration that declares the three folders is a custom one — the same machinery as data — and takes K = 12 or 13 and the cost `folders.md` §5 forecasts (ASM-33, `battery.md` §3 FAM-15, D-21).

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

**A rung's variants may be trained under different rules** (D-19): the six rungs declare
`masked-q-learning` on every variant today, so the *set* of rules a rung declares is one rule and the
ladder is unchanged. A rung declaring one variant per rule would instead train **both** variants, take
K = 10 on its table and double the hands it plays — that is D-19's own re-baseline and L0's decision,
not this page's (D-19, `rules.md` §7, §8).

## 3. The configuration schema

One rung configuration is a mapping; `training.rung(name)` resolves it, and `training.run` accepts either a rung name or a configuration written to this same schema, which is how the blind instance of `training.run` is expressed.

| Key | Meaning |
|---|---|
| `name`, `axis` | the rung's name and the one thing it varies, both from §2 |
| `carried_from`, `primary` | the previous rung's primary variant, and the variant the next rung inherits |
| `variants` | one or two variant entries |
| `pool` | the frozen pool the variants train and are evaluated against: its lineage, M, and the id every arm's run record must carry — and, for a configuration that is not in the registry, the membership declaration itself, which names any baseline beyond the three anchor ones it wants in the pool, and is how a custom league reaches the loop as data (D-16, ASM-16, `records.md` §8, ASM-32, D-21) |
| variant `backend` | `numpy` for R1, `torch` from R2 on (D-7) |
| variant `encoding` | `flat-numeric` for R1/R2, `card-tokens` for R3–R6 (D-3) |
| variant `architecture` | the kind — naive stack, token embedding, wide, deep, sparse, residual, plain — with its width, depth, sparsity and residual settings (D-3) |
| variant `learning_rule` | the rule this variant is **trained** under: one of the catalogue's members (`rules.md` §2, D-19), absent meaning the catalogue's first and declared so in `records.md` §2; two variants of one configuration may name two rules |
| variant `utility` | the utility this variant is **trained** under: one of the reward catalogue's members (`utilities.md` §2, D-20), absent meaning the catalogue's first, `net-chips`, and declared so in `records.md` §2; the six rows of §2 declare one utility for both arms of a pair |
| variant `hyper` | learning rate, exploration schedule, batch size, target update interval — one declaration per rule and identical within a comparison pair (ASM-7, D-19) |
| variant `param_budget`, `samples`, `seeds`, `device` | the budgets and the seed set of §6 |
| variant `snapshot_every` | how many hands between two snapshots that feed the rolling window (ASM-18) |
| variant `table` | the table budget this variant's row is measured at, `live` or `full` (`league.md` §6) |

## 4. What a comparison holds constant

`training.fairness(a, b)` reports this list, and the battery asserts it for every adjacent pair and every intra-rung pair (D-3, ASM-8, ASM-10):

- the game configuration from `engine.game_config` — identical for every rung, because every rung is one shape (D-2, D-29); a pair on two shapes is refused rather than reported, and a shape is a property of the configuration, so a shape is never a rung's axis (`shapes.md` §1, §6);
- the action vocabulary from `features.action_space` — the shape's own, three indices in the fixed-limit shape the six rungs share (D-2, D-29);
- the readout facts of `e2e-surface.md` §2 — the information set, identical for every encoding (D-3);
- the reward: the seat's net chip delta for the completed hand, delivered at the terminal decision, with no shaping (ASM-12), re-expressed by the utility both sides are trained under — the **set** of utilities the two sides declare, one utility for every rung of §2 (`utilities.md` §2, §8, D-20);
- the **set** of learning rules the two sides declare, with every hyperparameter above, the optimiser family, the exploration schedule and the discount — the set, not one rule, is what a rung holds constant, and a pair may differ on the rule itself when that is its declared axis (ASM-7, D-19, `rules.md` §8);
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
- **Where a notebook runs from.** `jupyter lab notebooks/r1-naive-numpy.ipynb` starts the kernel in `notebooks/`, so a notebook may not assume the repository root is the working directory: it finds the root itself (walking up for `pyproject.toml` and `src/`) and resolves every repository-relative path a record spells against that root before handing it back to `evaluation`, whose `policy_from` and `build_pool` read a path as the working directory spells it. The R1 notebook runs unchanged headless from `notebooks/` — `cd notebooks && PYTHONHASHSEED=0 ../.venv/bin/python -m jupyter nbconvert --to notebook --execute r1-naive-numpy.ipynb --output-dir /tmp/r1-notebook --ExecutePreprocessor.timeout=2400` — and at the repository root alike; the pin is only what makes its numbers comparable with the shipped evidence (D-5, `protocol.md` §4, `getting-started.md` §5).
- **Where a notebook writes.** The R1 notebook's run writes to `/tmp/pypoker-notebook-r1` by default, not to the shipped set: at the declared seeds and budget its run **writes** 33 paths — `checkpoints/R1/naive-numeric/seed-{0,1,2}/`, ten snapshots and a final model each — of which the **18 the repository ships** (that window's last five per seed, plus each seed's final model) are exactly the paths the shipped set occupies, so executing it as `README.md` §Quickstart showed rewrote all 18 shipped files in place — that build's payloads
identical, while on any other build it silently swaps the shipped models for different ones (`protocol.md` §5,
ASM-18) — and the fifteen earlier snapshots it also writes are intra-run and ship nothing, because a run's 33 are
its own to rewrite while the 18 are the set a reader protects (`protocol.md` §5, ASM-18). The notebook therefore sets the run's write root itself before it trains and says so in its opening markdown, exactly as `getting-started.md` §4 redirects the shell one-liner: `PYPOKER_CHECKPOINT_ROOT` names that root — the notebook honours one you set and otherwise supplies `/tmp/pypoker-notebook-r1`, and an absolute path to the shipped layout (`<repo>/checkpoints`) is how you overwrite it deliberately (`docs/L2/training/write-root.md` §3–§4, `getting-started.md` §4, ASM-18, D-8).
- A notebook that needs something the surface does not expose has found an L2 or L1 defect and returns as an `ADJUDICATION` (modules.md §3, D-12); inlining the missing piece is the one thing D-5 forbids.
