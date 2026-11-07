# PyPoker-Demo — L1 module map

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 4 · **Date:** 2026-11-08
- **Covers:** brief §2 (the rung ladder) and brief §3 (the league evaluation, D-16), Phase 1 only
- **Ceiling:** 110 lines. At the ceiling, split by owner — never append

## 1. The map

Six modules. Five carry Phase 1; the sixth is the harness the brief requires in the map (§5). The
league is not a seventh module: the pool is a set of opponents, which is `evaluation`'s subject, and
one owner is what keeps the training pool and the evaluation pool the same object (D-16, ASM-19).

| Module | Responsibility — one sentence | Endpoints |
|---|---|---|
| `engine` | the fixed game as a reinforcement-learning environment: hands, legality, readouts, reward, seeding, equity (D-2, ASM-2) | 9 |
| `features` | the observation and action encoding of a readout — the ladder's representation axis (D-3) | 7 |
| `agents` | everything that chooses or learns an action: one learner family, and the three fixed baselines (D-6, ASM-7) | 10 |
| `evaluation` | the league: the bounded pool, the match scheduler, the pairwise matrix, the fitted rating, the shipped tables, and the complete per-rung report (D-16) | 11 |
| `training` | the rung registry plus the one training loop every rung is a configuration of; the loop trains against the pool (D-3, D-16) | 6 |
| `harness` | test support whose consumers are test batteries (brief §5) | 6 |

Paths each module owns are declared in `modules.json` at the repository root; §5 states the rule.

## 2. Interactions

Calls go one way along the arrow; the direction is fixed so that no pair of modules is a cycle.

| From | To | Through | Why it may call |
|---|---|---|---|
| `training` | `evaluation` | `protocol`, `league`, `build_pool`, `pool_members`, `opponent` | the loop freezes one pool before it trains and draws every hand's opponent from it (D-16, ASM-16) |
| `training` | `agents` | `build_learner`, `act`, `learn`, `save` | the loop drives one learner (D-7) |
| `training` | `features` | `build_encoder`, `encode`, `observation_spec`, `legal_indices`, `decode_action` | the loop encodes readouts (D-3) |
| `training` | `engine` | `game_config`, `new_hand`, `play_hand`, `payoffs` | the loop needs hands (D-2) |
| `evaluation` | `agents` | `baselines`, `build_baseline`, `as_policy`, `load`, `param_count` | a table needs the three baselines as members, and each arm's parameter count (D-6, D-16) |
| `evaluation` | `features` | `build_encoder`, `encode` | a checkpoint becomes a policy only over an observation, so the league builds an encoder to load a member (D-16, D-3) |
| `evaluation` | `engine` | `new_hand`, `readout`, `legal_actions`, `play_hand`, `payoffs` | a cell is a run of hands (D-2, D-16) |
| `agents` | `features` | `encode`, `observation_spec`, `action_space`, `legal_indices`, `decode_action` | a learner consumes an observation and is sized by the encoding, and `as_policy` must encode the readouts its policy receives (D-3) |
| `agents` | `engine` | `readout`, `equity` | the oracle baseline reads pot and equity (ASM-4) |
| `features` | `engine` | the readout facts of `e2e-surface.md` §2 | an encoder encodes a readout (D-3) |
| `engine` | — | `pokerkit` only | the engine is the bottom of the map (D-1) |
| `harness` | any declared entry point | — | test support only, never a real subsystem (brief §5) |

Dependency order, which is the order of L2 integration returns:
`engine` → `features` → `agents` → `evaluation` → `training` → `harness`.

Notebooks of D-5 sit above `training` and `evaluation`; they import nothing else (`ladder.md` §7).

## 3. Boundaries

One job per module, and each "never" is what keeps the module independently testable.

- `engine` never imports another project module, never encodes an observation, never chooses an action and never records a result. It depends on `pokerkit` and the standard library (D-2, ASM-2).
- `features` never decides legality, never applies an action, never counts a parameter, and never learns which opponent it faces. It maps a readout to an observation and an index to an action (D-3).
- `agents` never deals a hand, never measures a match, never schedules an opponent and never writes a report. It acts and it learns (D-6, D-7).
- `evaluation` never trains and never edits a curve. It owns the pool, plays the cells and assembles evidence, and never reports a table whose members it cannot name or whose cells differ in hand count (D-16).
- `training` never claims a result and never chooses the pool's membership: it declares the lineage it inherits and freezes the pool that lineage yields (D-3, D-16).
- `harness` never re-implements, simplifies, or substitutes for a real subsystem; it calls the entry points this map declares and nothing else (brief §5, D-13).

## 4. Endpoints and the harness ceiling

`modules.json` declares, per module, its owned paths and its entry-point count `N`. The harness ceiling is `50 + 10×N` lines for that module's harness files, computed by `strata-lint` and never asserted by a harness author (brief §5): a harness over its ceiling means the surface is too large, not that the harness may grow. The declared counts are `engine` 9, `features` 7, `agents` 10, `evaluation` 11, `training` 6, `harness` 6 — 49 endpoints across the map.

The authoritative list of entry points per module is `e2e-surface.md` §3, and its row count must equal the `endpoints` value here for every module. `strata-lint` prints one ceiling per module, so no ceiling in this map is implicit.

## 5. Path ownership

- Each module owns `src/<module>/`, `tests/<module>/`, `docs/L2/<module>/` and `docs/L3/<module>/`, plus the shared artifact paths named below. No two modules claim one path, and `strata-lint` fails a duplicate claim (modules.md §4).
- Ownership is a path declaration for the diff-scope check, not authorship: L2 writes `docs/L2/<module>/`, L3 writes `docs/L3/<module>/`, L4 writes `src/<module>/` (D-13, modules.md §1).
- `training` additionally owns `notebooks/` (the one notebook per rung of D-5) and `checkpoints/` — the tree a run writes its ten snapshots and its final model per variant × seed under, and the one whose **shipped** set the repository carries: the retained window's last five per seed plus each seed's final, six per pair, 18 for R1's three seeds against the 33 such a run writes, and the pool is a view over that shipped window (`protocol.md` §5, D-16, ASM-18).
- `evaluation` additionally owns `tables/`, where the precomputed offline league table is shipped: the table is evidence, and the pool it was measured over lives in `checkpoints/` (D-16, D-8).
- `harness` additionally owns `tests/conftest.py`, `tests/e2e/`, `pyproject.toml` and the dependency lock file. The e2e battery in `tests/e2e/` is authored by the L1 test writer and is the harness's consumer, not its implementation: a harness agent may support it and may not rewrite it (brief §5, D-13).
- Layer-owned artifacts are outside module claims by construction: `docs/L1/` (including `getting-started.md`), `modules.json`, `LICENSE`, `README.md`, `.gitignore`, and `scripts/run-all-tests.sh`, the runner `battery.md` §2 names — `modules.json` claims no path under `scripts/`, so it is nobody's module. The diff-scope check of modules.md §4 therefore runs over changed paths inside module subtrees; a scaffolding change is not a module escape (modules.md §4, D-13).
- `README.md` at the repository root is L0's, written outside this map and owning no module: it is the front page a listener arrives on — what the demo is, how to install and run it, and what its numbers may and may not be read as — while `docs/L1/README.md` stays the design entry point and `docs/L1/getting-started.md` is this layer's newcomer route (Python version, dependencies, `PYTHONPATH=src`, one training run, one league table). Linking that route from the front page is L0's, as the page itself is (brief §5, D-1, D-14).
- The union of claims covers every path where module code, tests, notebooks, checkpoints and shipped tables will live.

## 6. Why the league stays inside `evaluation` (ASM-19)

The pool, the scheduler, the matrix and the rating are one mechanism: a member of the pool is an
opponent the loop samples, the same object is a column of the matrix, and the rating is a function of
that matrix (D-16). Splitting them across a seventh module would put the pool's membership under one
owner and its meaning under another, and would add an `evaluation` → `league` → `agents` hop in front
of the match loop that is `evaluation`'s own work (D-16, D-13). The rejected alternative is recorded
with ASM-19.

## 7. Deliberately absent from the map

No game-expansion module, no attention or opponent-modelling module, no multi-player seat handling and
no web UI: they are Phase 2 or later (D-4, D-9). No module is declared for work the brief does not
name, and no module carries a Phase 2 seam in anticipation (D-4).
