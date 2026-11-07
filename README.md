# PyPoker-Demo

A technique ladder for poker-playing reinforcement learning, built as the demonstration tool for a
community tech talk about AI/ML methods.

One fixed game throughout. Each rung changes exactly one thing about how the agent represents the
game or how the network is built — from a flat numeric encoding of the cards up through learned
card embeddings, width/depth and dense/sparse comparisons, and a residual stream — so that a
rung-to-rung difference is attributable to that one change and not to the game or the learning
rule. The card engine is [PokerKit](https://github.com/uoftcprg/pokerkit).

## What it does

- **The game**: heads-up fixed-limit Texas Hold'em — two seats, blinds 1/2, one blind level,
  20-chip stacks, bets of 2 (preflop/flop) and 4 (turn/river), 4 raises per street.
- **The ladder**: R1 naive flat-numeric encoding (hand-rolled NumPy) · R2 the same model in PyTorch,
  to measure the speed difference · R3 cards as learned embeddings · R4 wide vs deep · R5 dense vs
  sparse · R6 residual stream vs plain stack. Every pair is matched to the same parameter budget.
- **The league**: agents train against a bounded round-robin pool of their own recent versions,
  and the same pool is the measuring instrument. Every table also contains three fixed,
  non-learning baselines — random, always-call, and an oracle that only calls when the pot odds
  justify it — at the same hand count as every league cell.
- **The evidence**: a pairwise matrix *and* a Bradley-Terry rating with confidence intervals. Both,
  because poker payoffs need not be transitive: in the shipped live table R1 ranks **top of the
  rating** while **losing** to `always-call` and only **drawing** `oracle` — which still takes chips
  off it per hand — its place earned by beating `random` almost every time. The matrix shows that;
  a rating alone would hide it. The exact figures live in `checkpoints/evidence/r1-live.json` and
  move whenever the table is regenerated, so this page states the shape of the result, not a number
  that would go stale.

## Quickstart

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[torch,notebooks,dev]"   # pokerkit, numpy, torch, matplotlib, pytest, jupyterlab
```

The core runtime is `pokerkit` and `numpy`; `torch` is the second learner backend used from R2 on,
and the notebook and test extras are separate so a reader who only wants the engine need not
install PyTorch.

Run the batteries (a bare `pytest tests` cannot collect this tree — see `scripts/run-all-tests.sh`):

```sh
scripts/run-all-tests.sh
```

Train the first rung at the live budget and get a run record back:

```sh
PYPOKER_CHECKPOINT_ROOT=/tmp/pypoker-run PYTHONHASHSEED=0 \
PYTHONPATH=src .venv/bin/python -c "import training; rec = training.run('R1')"
```

The `PYPOKER_CHECKPOINT_ROOT` redirect matters: without it this command **overwrites the 18
shipped checkpoints in `checkpoints/`** with a fresh run's models, which is fine if that is what you
meant and surprising if it is not. `PYTHONHASHSEED=0` pins the interpreter, because the oracle's
sampled equity estimate is ordered by a set whose iteration follows the hash seed, so an unpinned
process shifts the oracle cells. Both are explained in `docs/L1/getting-started.md` §4.

Play a rung against the fixed baselines and rate the result — the pattern the R1 notebook walks
through end to end:

```sh
jupyter lab notebooks/r1-naive-numpy.ipynb
```

### Using a GPU

This project trains on **CPU**, which is the supported path and the one the shipped evidence came
from. Moving R1's arithmetic from hand-rolled NumPy into PyTorch (rung R2) already bought roughly
**two and a half times** on identical work, so the interpreter, not the accelerator, was the
bottleneck at that point. The measured pair and the machine it was taken on are recorded in
`strata/records/r2-speed.md`; re-measure on yours rather than trusting a number from mine.

A GPU is not currently usable, for two separate reasons: a delegated agent cannot reach the card,
because the development sandbox denies read-write opens under `/dev` (not a driver or group
fault), and the PyTorch backend itself is CPU-only — `training.devices()` lists `cpu` alone and
`run(device="cuda")` refuses. `docs/L1/gpu.md` explains both, gives the commands that tell you
whether *your* card is usable with this project's interpreter, and states what a GPU-enabled path
would need.

## What the numbers mean — and what they do not

A rung is never reported as progress on a training curve alone. Each one carries curves, its place
in the league table, and its results against the three baselines.

The project explicitly does **not** claim poker skill, exploitative play, or superhuman strength.
It compares architectures on one small game. In particular:

- a league rank is a global fit across all cells and does **not** imply a head-to-head win;
- an untrained model's row in the shipped full table is not the trained rung's row, even when both
  carry the same member id;
- training time matters: the shipped R1 run is a live-budget run (1,000 hands per seed) whose
  learning signal had not converged, and **no long-budget run ships yet** — the 200,000-hand
  runs that would show the difference are the next thing to produce, not something you will
  find in `checkpoints/`.

## Layout

| Path | What it is |
|---|---|
| `src/engine` | the fixed game as a reinforcement-learning environment (PokerKit; one seeding point; readouts, legality, reward, equity) |
| `src/features` | observation and action encoding for the whole ladder, from one declaration table |
| `src/agents` | one masked-Q learning family, NumPy at R1 and PyTorch from R2, plus the three fixed baselines |
| `src/evaluation` | the league: pool, sequential match scheduler, matrix, Bradley-Terry rating, live and shipped tables, the report |
| `src/training` | the rung registry and the one loop that trains against the pool |
| `src/harness` | test support whose consumers are the batteries |
| `notebooks/` | one notebook per rung (D-5) — thin, importing the modules, never a copy of the code |
| `tables/` | the shipped full league table |
| `checkpoints/` | the shipped R1 checkpoint set and its evidence record |
| `docs/` | the layered design record: L1 module map and protocol, L2 integration surfaces, L3 module designs |
| `strata/` | the development workflow's own record: brief, decisions, platform facts, walkthrough |

## Reading order

`docs/L1/README.md` is the design entry point. `strata/brief.md` states what is being built and
`strata/decisions.md` records every decision and who made it. `strata/platform.md` holds the
measured facts about the machine the thing runs on — including that a workflow-started run is
CPU-bound and that the GPU is only reachable outside the development sandbox.

## Licence

MIT. See `LICENSE`.
