# PyPoker-Demo — getting started

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 1 (new) · **Date:** 2026-11-05
- **Purpose:** the shortest route from an empty checkout to a trained rung and a league table, for a reader who has the repository and nothing else
- **Ceiling:** 70 lines. At the ceiling, split by owner — never append

## 1. What you need

- **Python 3.12** — `pyproject.toml` requires `>=3.12` and the shipped environment measured 3.12.3 (brief §4).
- **The runtime floor**: `pokerkit==0.7.7` (the game) and `numpy==2.5.4` (the R1 backend) (brief §4, D-2, D-7).
- **`torch==2.13.0`** for R2 and later — the second learner backend. A GPU is optional: a run started by the build workflow is CPU-bound, and a GPU run is one the user starts directly (D-7, D-8).
- **The extras**: `matplotlib` for the notebooks and `pytest==9.2.0` for the batteries. Neither is a runtime dependency of the six packages (`pyproject.toml`, C-C5).

## 2. Set it up

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[torch,notebooks,dev]"
```

Drop the `torch` extra for a CPU-only, no-PyTorch install that runs R1 alone. Nothing in `.venv/` is committed (D-8).

## 3. How the packages are found

The six packages live in `src/` and are imported by their **bare names** — `import training`, `import evaluation` — so
`src/` is the package root and must be on the path (brief §5):

- a bare interpreter: prefix the command with `PYTHONPATH=src`;
- a `pytest` run: nothing to do, because `pyproject.toml` sets `pythonpath = ["src"]`;
- `scripts/run-all-tests.sh` does that for you, and the e2e battery and the notebook each put `src/` on `sys.path` themselves.

## 4. Run a training rung

`training.run` is the loop, and the package ships no `__main__`, so a rung is driven from Python. R1 at its live budget —
1,000 hands per variant per seed at seeds 0, 1 and 2, a few minutes on CPU at the measured 0.105–0.132 s/hand (ASM-21):

```sh
PYTHONPATH=src .venv/bin/python -c "
import training
record = training.run('R1')
print(record['timings'])
"
```

The call writes ten snapshots and a final model per variant per seed under `checkpoints/` and returns the run record of
`records.md` §12 — curves, pool, checkpoints, seeds, budget, device and the measured cost per hand. `training.rungs()`
lists the six rungs and `training.rung('R4')` resolves one as data (D-3, ASM-18).

## 5. Run a league table

A **live** table is what a talk plays, one declared call per stage (`e2e-surface.md` §3.4): `evaluation.build_pool(...)`
over the frozen membership, `evaluation.matrix(pool, [variant_policy], "live")` at 120 hands a cell, then
`evaluation.rating(matrix)`. At K = 4 — the three baselines and one variant — that is six cells and ≈95 s (ASM-21, ASM-14).
`notebooks/r1-naive-numpy.ipynb` walks exactly that, ending in `evaluation.report(...)`.

The **shipped full** table is precomputed offline and never regenerated during a talk (D-8, D-16):

```sh
PYTHONPATH=src .venv/bin/python -m evaluation.tables   # writes tables/league-full.json, ≈20 min at the measured cost
```

## 6. Run the batteries

```sh
scripts/run-all-tests.sh                    # every battery, one pytest run each
.venv/bin/python -m pytest tests/e2e -q     # just the L1 end-to-end battery
```

One battery per invocation is the supported form: a bare `pytest tests` cannot collect this tree, because sibling
batteries reuse file basenames and each imports its own same-directory support module (`battery.md` §2).
