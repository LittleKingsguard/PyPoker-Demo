# PyPoker-Demo — getting started

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-06
- **Purpose:** the shortest route from an empty checkout to a trained rung and a league table, for a reader who has the repository and nothing else
- **Ceiling:** 70 lines. At the ceiling, split by owner — never append

## 1. What you need

- **Python 3.12** — `pyproject.toml` requires `>=3.12` and the shipped environment measured 3.12.3 (brief §4).
- **The runtime and the extras**: `pokerkit==0.7.7` (the game), `numpy==2.5.4` (the R1 backend), `torch==2.13.0` from R2 on, plus `matplotlib` and `pytest==9.2.0` — neither of those last two is a runtime dependency of the six packages, and a GPU is optional because a workflow-started run is CPU-bound while a GPU run is one the user starts (`pyproject.toml`, C-C5, brief §4, D-7, D-8).

## 2. Set it up

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[torch,notebooks,dev]"   # drop the torch extra for a CPU-only R1; .venv/ is never committed
```

## 3. How the packages are found, and where you stand

The six packages live in `src/` and are imported by their **bare names** — `import training` — so `src/` must be on the path
(brief §5): prefix a bare interpreter with `PYTHONPATH=src`, and a `pytest` run needs nothing because `pyproject.toml` sets
`pythonpath = ["src"]`. The commands below run from the repository root, except the notebook, which finds that root itself (`ladder.md` §7).

## 4. Run a training rung

`training.run` is the loop and the package ships no `__main__`, so a rung is driven from Python. R1 at its live budget —
1,000 hands per variant per seed at seeds 0, 1 and 2 — takes a few minutes on CPU at `league.md` §7's measured cost:

```sh
PYTHONPATH=src .venv/bin/python -c "import training; print(training.run('R1')['timings'])"
```

The call writes ten snapshots and a final model per variant per seed under `checkpoints/` and returns the record of
`records.md` §12 — curves, pool, checkpoints, seeds, budget, device and the measured cost per hand (D-3, ASM-18).

**It overwrites the set the repository ships.** At the declared seeds and budget it writes exactly the paths the shipped R1 models occupy — `checkpoints/R1/naive-numeric/seed-{0,1,2}/` — so running it before you load them replaces them; to leave the shipped set alone, point the run's write root elsewhere in the same command (`docs/L2/training/write-root.md` §3–§4):

```sh
PYPOKER_CHECKPOINT_ROOT=/tmp/pypoker-run PYTHONPATH=src .venv/bin/python -c "import training; print(training.run('R1')['checkpoints'])"
```

## 5. Run a league table

A **live** table is what a talk plays, one declared call per stage (`e2e-surface.md` §3.4): `evaluation.build_pool(...)` over that run's frozen membership with the three baselines added and pinned, `evaluation.matrix(pool, [variant_policy], "live")` at 120 hands a cell, then `evaluation.rating(matrix)` — six cells and ≈110 s at K = 4, at the measured 0.141–0.153 s/hand (`league.md` §7, ASM-21, ASM-14).

The **variant policy** is the rung's own trained model, named by the run record: `record["checkpoints"][variant][str(seed)]["final"]` is a repository-relative path — resolve it against the repository root first, because `policy_from` and `build_pool` read a path as the working directory spells it — then `evaluation.policy_from` loads it and `matrix` names it `variant-1` by the slot it was passed in (`records.md` §10, `e2e-surface.md` §3.4). `notebooks/r1-naive-numpy.ipynb` walks that route.

The **shipped full** table is precomputed offline and never regenerated during a talk (D-8, D-16):

```sh
PYTHONPATH=src .venv/bin/python -m evaluation.tables   # writes tables/league-full.json, ≈20 min at the measured cost
```

## 6. Run the batteries

```sh
scripts/run-all-tests.sh                    # every battery, one pytest run each
.venv/bin/python -m pytest tests/e2e -q     # just the L1 end-to-end battery
```

One battery per invocation is the supported form: a bare `pytest tests` cannot collect this tree, because sibling batteries reuse file basenames and each imports its own same-directory support module (`battery.md` §2). A battery writes nothing under the repository's `checkpoints/` — the session points the run's write root at a temporary directory (`battery.md` §2) — so a reader's tree is unchanged.
