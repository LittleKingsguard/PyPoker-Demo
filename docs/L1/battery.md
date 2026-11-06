# PyPoker-Demo — L1 end-to-end battery

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 4 · **Date:** 2026-11-06
- **Covers:** what `tests/e2e/` must drive, and what "green" means before code exists (D-11)
- **Ceiling:** 100 lines. At the ceiling, split by owner — never append

## 1. What green means here

The examiner validates the battery before the code (D-11, `strata/examiner.md` §1). Every assertion below is red against absent code, which is the expected state of a design-stage battery: "red" is not the finding, and "completable" is (`strata/examiner.md` §3). This layer is green when the battery drives only declared surfaces, asserts observable outcomes, is satisfiable by some implementation, and covers the families of §3.

## 2. Rules the battery is written under

- It calls only the entry points of `e2e-surface.md` §3, through the `harness` module where support is needed, and reaches past no entry point (brief §5). The shapes it reads are `records.md`'s **required** keys and nothing beyond them (D-13).
- It asserts outcomes, never an internal call, an internal shape, or a restatement of an implementation (`strata/examiner.md` §2).
- It is network-free, CPU-only, self-sufficient and run from the repository root with the project venv. A case that needs a checkpoint or a pool builds one with a minimal budget; reading `training.checkpoints()` as an index is not a dependency on a shipped artefact, but asserting retention is done against a run the case builds itself (D-8, ASM-18).
- It imports nothing beyond the standard library and the declared entry points — `unittest` included, and no third-party package — so it adds no dependency to the audience's environment and runs under either runner (C-C5, D-8). The project venv does carry `pytest` 9.2.0 (the `dev` extra of `pyproject.toml`, not a battery dependency), and that is how the batteries are executed.
- **How the batteries are run.** One battery per invocation, from the repository root: `.venv/bin/python -m pytest tests/e2e -q` for this one, `.venv/bin/python -m pytest tests/<module> -q` for a module's, and `scripts/run-all-tests.sh` for all thirteen, which is what "run the tests" means. A bare `pytest tests` cannot collect this tree: sibling batteries reuse file basenames — `test_errors.py` in two, `test_seeds.py` in two, `test_episode.py` in two, `test_guardrails.py` in two — and each battery imports its own same-directory support module (`_evaluation_support.py`, `_join_support.py` and their kin), so the prepend import mode aborts with an import file mismatch while the importlib mode breaks those helper imports. Measured 2026-11-05: `.venv/bin/python -m pytest tests --collect-only -q` reports five such errors, one per duplicated basename (`scripts/run-all-tests.sh`, D-11).
- **Where a battery writes.** Nowhere under the repository's `checkpoints/`: `tests/conftest.py` points the run's write root — `PYPOKER_CHECKPOINT_ROOT`, which `training.layout` reads on every call — at a private temporary directory for the session and removes it at exit, so a battery that trains creates `seed-4103`, `R2/` or `R4/` in a temporary tree and the reader's shipped set is untouched (D-8, ASM-18, `docs/L2/training/write-root.md` §3–§4, `docs/L3/training/checkpoints.md` §5). A run a reader starts deliberately still writes the shipped layout; that is intended and `getting-started.md` §4 warns of it.
- No case is skipped or conditionally disabled. A case that cannot run is a finding against the test writer (D-11).
- League cases assert cell counts from K arithmetically, and where a table is actually played the case uses the smallest legal membership — the three baselines and one variant, K = 4, six cells — because `evaluation.matrix` takes a table budget rather than a hand count and the live cell is fixed at 120 hands (ASM-14). The battery proves the scheduler's arithmetic; the shipped table proves the cost.
- A timing case asserts that a cost record exists and carries hands and seconds per hand; it never asserts that a wall clock was beaten, which would be a flaky test and not a contract (ASM-15).
- Each case carries an id of the form `FAM-<n>.<k>`; the layer return cites them.

## 3. The case families

Sixteen families. FAM-6..FAM-10 are the league's own machinery, FAM-11 assembles them into the report, and FAM-12..FAM-16 carry the ladder, the harness and the blind instances (D-16).

| Family | What it drives | What it asserts |
|---|---|---|
| FAM-1 | every one of the 49 entry points at least once | the declared surface exists and is callable; a name that is absent is one finding per name (brief §5) |
| FAM-2 | `engine.game_config`, `features.action_space`, `features.observation_spec` for every rung | the game, the action vocabulary and the readout facts are identical across the ladder — the D-2 and D-3 invariance |
| FAM-3 | `training.rungs`, `training.rung`, `training.fairness` | six rungs in brief §2's order; each adjacent pair and each intra-rung pair differs on exactly one declared axis and is matched on budget and parameter count; both arms of R4, R5 and R6 name one frozen pool id (D-3, D-16, ASM-16) |
| FAM-4 | `engine.new_hand`, `engine.play_hand`, `training.run` | one seed, one configuration and one pool give identical outcomes twice; a different seed or a different pool differs; the seed set and the table seed appear in every record (ASM-2, D-16) |
| FAM-5 | `agents.baselines`, `agents.build_baseline`, `engine.equity` | the three baselines behave as `protocol.md` §3 states, including the oracle's pot-odds consistency and `always-call` never folding (D-6, ASM-4) |
| FAM-6 | `evaluation.league`, `build_pool`, `pool_members`, `offer` | a pool holds at most M versions and always the three baselines; the baselines are pinned and never evicted; `offer` drops the oldest evictable version and nothing else and changes the id; R1's pool is the three baselines alone; one declaration yields one ordered membership (D-16, ASM-14, ASM-16) |
| FAM-7 | `evaluation.match`, `evaluation.opponent` | one cell accounts for every hand it played; seats alternate and the split covers both seats; the two directions are the same hands and their chip deltas sum to zero; a cell plays the hand count it was given and carries both parameter counts and its seed; two cells are never interleaved; `opponent` returns a policy drawn from the pool (D-16, ASM-2) |
| FAM-8 | `evaluation.matrix` | membership is the pool plus the rung's variants; the cells are exactly K(K−1)/2 unordered pairs; every cell carries the table's one hand count, the three baseline cells included; a matrix with an unequal cell, a missing baseline or a foreign member is refused (D-16, ASM-14) |
| FAM-9 | `evaluation.rating` | one value and a 95% interval per matrix member, the method declared as Bradley-Terry, the anchor set so the three baselines' mean is 0, the hands behind each value reported, a member that won everything bounded rather than infinite, and the convergence and bootstrap seed recorded (D-16, ASM-17) |
| FAM-10 | `evaluation.league`, `evaluation.matrix`, `harness.timings` | both table budgets are declared with their cell sizes; the live table's hands played equal cells × hands per cell for the membership; the cell count for a membership is its pair count; the cost record carries hands and seconds per hand (D-16, D-8, ASM-14, ASM-15) |
| FAM-11 | `evaluation.report`, `evaluation.protocol` | a complete record yields a report carrying all seven families; a record missing curves, pool, matrix, rating, baselines, axis row or header is refused with that family named; R1's pool row is the three baselines it actually had and a single-variant rung's axis row is an explicit value; the report carries the seeds, the table seed and the device (D-6, D-16) |
| FAM-12 | `agents.save`, `agents.load`, `evaluation.policy_from`, `training.checkpoints`, `evaluation.offer` | a run writes ten snapshots and its final model and the retained window is the last M; the index carries each variant's final model and lists no artefact twice; a loaded checkpoint chooses the same action as its learner on the same readout (ASM-5, ASM-18, D-16) |
| FAM-13 | `training.run`, `harness.timings` | R1 and R2 declare the same encoding, shapes, update rule and budgets and differ only on the backend; they choose the same actions on the same seeded hands against the same opponents; both run records carry throughput — the D-7 speed evidence (D-7, D-8) |
| FAM-14 | `harness.drive`, `harness.fixtures`, `harness.factory`, `harness.seam`, `harness.expect`, `harness.timings` | a case runs through the driver from a pinned fixture, a factory builds only declared objects and refuses an undeclared one, a seam satisfies the policy protocol and produces a real episode, and `expect` yields a verdict — the harness is support, not a substitute (brief §5) |
| FAM-15 | a rung configuration and a pool membership that are in no design document | `training.run`, `evaluation.fairness` and `evaluation.build_pool` take them as data and the report covers them too, so a rung is a configuration and a league is not a script (D-3, D-16) |
| FAM-16 | the blind instances of §4 | one per `general` row of `e2e-surface.md` §5, with an instance invented by the test writer (D-15) |

## 4. The blind instances

`e2e-surface.md` §5 marks 37 rows `general`. For each, the battery carries at least one case whose subject is that row and whose instance — the seed, the configuration, the membership, the cell size, the hand count, the checkpoint, the case — appears in no design document (D-15). The test writer invents them from the declared surface; the L1 documents show no instance for a `general` row, which is what keeps the walkthrough blind (D-14, D-15).

The twelve `fixed` rows are exempt: their one instance is the project's own — the game of D-2, the two encodings of D-3, the baselines of D-6, the rungs of brief §2 and the league of D-16. `features.observation_spec` is one of them because an encoder exists only by a declared encoding, so no invented instance of it can be built through the surface (`e2e-surface.md` §5).

## 5. What the battery does not cover

Module-internal behaviour belongs to `tests/<module>/`, and the harness line ceiling belongs to `strata-lint` with the counts of `modules.json` (brief §5). The battery judges the map's joins — the invariants a single module cannot check about itself (D-3, D-16): that the pool the loop samples is the pool the table measures, that both arms of a pair held one pool, and that a table's rows are comparable because its cells were played at one hand count (D-16, ASM-16).

It also does not assert a table's *values*: no case requires a member to outrank a baseline, because that is what the run measures and not what the surface promises (D-6, D-16).
