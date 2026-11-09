# PyPoker-Demo — getting started

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 6 · **Date:** 2026-11-08
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

**It overwrites the set the repository ships.** At the declared seeds and budget a run **writes** 33 artefacts — ten snapshots and a final model per variant per seed — and the **18 the repository ships** are exactly the paths the shipped R1 models occupy in `checkpoints/R1/naive-numeric/seed-{0,1,2}/` (the retained window's last five per seed plus each seed's final; the other fifteen are intra-run snapshots the repository does not carry, so a run rewrites them freely and only the 18 are the set a reader protects), so running it before you load them replaces them; to leave the shipped set alone, point the run's write root elsewhere in the same command (`protocol.md` §5, `docs/L2/training/write-root.md` §3–§4):

```sh
PYPOKER_CHECKPOINT_ROOT=/tmp/pypoker-run PYTHONPATH=src .venv/bin/python -c "import training; print(training.run('R1')['checkpoints'])"
```

## 5. Run a league table

A **live** table is what a talk plays, one declared call per stage (`e2e-surface.md` §3.4): `evaluation.build_pool(...)` over that run's frozen membership with the three anchor baselines added and pinned — a declaration that names D-21's folding baselines holds them too, which takes K and the table's cost to `folders.md` §5, ASM-33 — `evaluation.matrix(pool, [variant_policy], "live")` at 120 hands a cell, then `evaluation.rating(matrix)` — six cells and ≈110 s at K = 4, at the measured 0.141–0.153 s/hand (`league.md` §7, ASM-21, ASM-14).

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

One battery per invocation is the supported form: a bare `pytest tests` cannot collect this tree, because sibling batteries reuse file basenames and each imports its own same-directory support module (`battery.md` §2). **A battery writes nothing under the repository's `checkpoints/`, whichever runner runs it**: each runner loads a hook that points the run's write root — `PYPOKER_CHECKPOINT_ROOT` — at a private temporary directory before any case runs and removes it at exit, so `pytest tests/e2e` and the `unittest` census (spelled with its `-t .`, which is what makes discovery import the battery's package) alike leave your tree exactly as they found it (`battery.md` §2, D-8). Only a run you start deliberately writes the shipped layout (§4).

## 7. If you have a GPU

A GPU is optional and nothing above uses one: every rung trains and evaluates on CPU, which is the supported path and where the shipped evidence was produced (D-8, `protocol.md` §6). An agent cannot run the GPU path — the file sandbox denies read-write opens under `/dev`, not a driver and not a permissions fault — and the code is CPU-only regardless, so `run` refuses any device but `cpu` (D-17). `gpu.md` states all three plainly, gives the commands that verify the card with this venv from your own shell, and reports the measured PyTorch-versus-NumPy difference — roughly 2.5× on identical work, the pair's own seconds in `strata/records/r2-speed.md` — with the two commands that re-measure it on your machine (D-17, D-7, D-8, ASM-21). What those commands cost you is a forecast and not a figure read off any build: both rungs run 3,000 hands, so at the measured band expect about 5–6 minutes for R1 and about 2–2.5 minutes for R2, and read your own recorded `timings` for the number that applies (D-17, ASM-21, ASM-23).
