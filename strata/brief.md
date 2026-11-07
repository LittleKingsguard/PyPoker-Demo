# PyPoker-Demo — design brief

- **Layer:** L0 · **Rev:** 1 · **Date:** 2026-11-05
- **Status:** ACTIVE — intake closed, Phase 1 design not yet started
- **Scope:** Phase 1 (technique ladder on one fixed game). Phase 2 and the bonus objective are
  planned, not designed (D-3, D-4, D-9)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append

## 0. Purpose

A demonstration tool accompanying a community tech talk about AI/ML techniques. It trains
poker-playing agents by reinforcement learning, starting from the most naive implementation and
adding depth rung by rung, borrowing the techniques the LLM space made familiar: card
tokenisation into embeddings, wide vs deep and dense vs sparse networks, residual streaming.
The card engine is `pokerkit` (D-1).

## 1. What the demo is

One notebook per rung, thin, importing the project's modules — the notebook is the talk's
per-rung narrative and never carries its own copy of the code (D-5). A live run of a rung is a
few minutes; pre-trained checkpoints from longer runs travel with the repo so the talk can show
that training time matters (D-8). A web UI is speculative and waits on progress (D-5).

## 2. Phase 1 — the technique ladder

Every rung plays the same game: heads-up fixed-limit Hold'em through `pokerkit` (D-2). The game
never changes across Phase 1, so a rung-to-rung difference belongs to the network (D-3). The
rungs the user named, in the order they were given:

| # | Rung | What changes |
|---|---|---|
| R1 | Naive numeric encoding | flat numeric conversion of card rank and suit; hand-rolled NumPy (D-7) |
| R2 | PyTorch recreation of R1 | the same naive model in PyTorch, to measure the speed difference (D-7) |
| R3 | Card tokenisation into embeddings | a card becomes a learned vector rather than a number |
| R4 | Width vs depth | the same budget spent wide and spent deep |
| R5 | Dense vs sparse | connectivity varied at a matched budget |
| R6 | Residual stream | each sublayer adds a delta to a carried representation vector instead of replacing it, so "do nothing" is the default — the residual-stream construction of the LLM literature (D-3; source `lizeman.github.io/llm-arch-kb/residual/residual-overview`) |

L1 fixes rung granularity, the per-rung parameter and sample budget, and what each rung must
hold constant so its comparison is fair. L1 does not reorder the ladder without an L0 decision
(D-2, D-3).

## 3. Evaluation protocol

Every rung reports its training curves and its place in a round-robin league (D-16): a bounded
rolling pool of the model's own last M versions, plus three fixed non-learning baselines —
random, always-call, and an oracle that only calls when pot odds justify it (D-6, ASM-4). The
agent learns against that pool, and the same pool is its evaluation opponent (D-16). Evidence is a
pairwise matrix plus a fitted rating (Elo or Bradley-Terry) with confidence intervals, because
poker payoffs need not be transitive (D-16). A small table is produced live in minutes; the full
table is precomputed offline and shipped (D-8, D-16). The three baselines sit inside the table at
the same hand count as every league cell — they are the only fixed standard, so they anchor every
claim (D-16). Seeds are fixed and recorded (ASM-2); matches run sequentially because one global
`random` stream deals every hand; and both arms of a two-variant rung train and evaluate against
an identical frozen pool (D-3, D-16). A rung is not progress on a curve alone (D-6), and a league
rank is not a claim of poker skill (D-16).

## 4. Environment

- The machine has an AMD Radeon RX 9070 XT (RDNA4) with ROCm 7.2.3 and a working
  `torch 2.13.0+rocm7.1`, plus 24 CPU threads and 62 GB RAM. The GPU is reachable only outside the
  DSH sandbox: a workflow-started run is CPU-bound, and a GPU run is one the user starts directly
  (D-8, `strata/platform.md`).
- Python 3.12.3, `uv` available, project dependencies isolated in a repository-local virtual
  environment (D-8).
- `pokerkit` 0.7.7 is MIT-licensed and requires Python ≥ 3.11; it ships no reinforcement-learning
  wrapper, no observation encoding and no seeding hook — those are this project's to build
  (`strata/platform.md`).

## 5. Layers and handoffs

L0 interviews, decides and reports; it designs no module and writes no implementation (D-1). L1
owns the module map and the end-to-end battery; L2 owns integration surfaces; L3 owns module
design; L4 implements in one shot (D-1). Every return carries the envelope of `strata/envelope.md`
(D-1, D-11, D-12). Module agents see one module only, and their writes are lint-confined to it
(D-13). No unit is reported ready without the blind documentation walkthrough (D-14). Intake
research precedes a design commitment and carries a source per claim (D-15).

The test harness — driver, fixtures, factories, mock seams — is ordinary code, not a per-layer
artifact (D-1). It enters the L1 module map as a module whose consumers are test batteries, and it
calls only the entry points that map declares: it never re-implements, simplifies or substitutes
for a real subsystem (D-13). Its line ceiling is `50 + 10×N`, where N is the endpoint count the
module declares, computed by `strata-lint` and never asserted by the harness author: exceeding it
means the surface is too large, not that the harness may grow (D-1).

## 6. Decisions in force

D-1 workflow · D-2 fixed game · D-3 technique axis · D-4 Phase 2 game expansion · D-5 notebooks
· D-6 evidence · D-7 NumPy then PyTorch · D-8 GPU plus checkpoints · D-9 attention deferred ·
D-10 intake gate · D-11 examiner · D-12 adjudication · D-13 module isolation · D-14 walkthrough
· D-15 research · D-16 the league opponent.

## 7. Open assumptions

- `ASM-1` — the fixed game is configured with short stacks and a single fixed blind level, so a
  hand ends in a handful of decisions and the ladder stays cheap to train (D-2). Rejected: deep
  stacks with multiple raise caps, which multiply the per-hand decision count for no gain in
  what Phase 1 is trying to show.
- `ASM-2` — reproducibility is obtained by seeding Python's global `random`, because `pokerkit`
  shuffles its deck with `random.shuffle` at state creation and exposes no seed parameter.
  Rejected: a project-owned dealer, which would duplicate the engine and take the deal away from
  the thing under test.
- `ASM-3` — the learning algorithm per rung is an L1 design decision (a tabular method for R1,
  and a value- or policy-based method from R2 on), recorded there with its own rejected
  alternative. Rejected: pinning one algorithm family for every rung, which would decide at L0
  what the ladder exists to compare.
- `ASM-4` — the oracle baseline decides with pot odds against hand equity obtained from
  `pokerkit`'s equity calculation, at each decision point. Rejected: an oracle distilled from a
  trained rung, which would no longer be a fixed baseline (D-6).
- `ASM-5` — checkpoints are retained as the league pool requires: intra-run snapshots feed the
  rolling window of the last M versions, and what ships is that pool plus each rung's final model
  (D-16). Rejected: shipping only one final checkpoint per rung, which leaves a league with no
  opponents and makes the table a claim the audience cannot reproduce.
- `ASM-13` — the pool size M, the hands per pairing and the match count are L1's parameters,
  recorded in its docs together with the cost they imply for a minutes-long live table and an
  offline full table (D-16, D-8). Rejected: fixing M here at a round number, which would settle
  the table's cost and its resolution before the engine's per-hand cost is measured.
- `ASM-14` — L1's league parameters and reading rules, recorded in `docs/L1/assumptions.md` and
  ratified here by reference: M = 5 versions with the baselines pinned, 120 hands per cell live
  and 1,500 full, Bradley-Terry with bootstrap intervals anchored on the baselines, ten snapshots
  per run, and `evaluation` reading a checkpoint's seed and encoding from its container (D-16).
- `ASM-21` — measured, and it supersedes the earlier 40 ms bound: the per-hand cost is **not one
  number** but 0.105–0.153 s on CPU, decided by what an artefact plays — an oracle-bearing cell
  costs 0.255–0.315 s/hand against 0.002–0.004 for an oracle-free one, and the oracle sits in half
  a table's hands. Measured: training 0.105–0.120, the shipped full table 0.1299–0.1324, the live
  table 0.1415–0.1532. Read at the live table's own rate: 720 hands at K=4 is ≈100–110 s, 4,320 at
  K=9 is ≈10–11 min, 5,400 at K=10 is ≈13–14 min; the full table at the shipped rate is ≈2 hours at
  K=9 and ≈2.5 at K=10. Every figure is a measurement recorded beside the
  artefact, never a claim (D-16, D-8). Rejected: a single scalar (40 ms, or 0.13 s), which reports
  a ten-minute table as under four minutes and hides that the oracle is the cost.

## 8. Non-goals at rev 1

- Phase 2 game expansion, the multi-round attention objective, and multi-player poker (D-4, D-9).
- A web UI, and any claim of superhuman or exploitative play: Phase 1 compares architectures on
  one small game, and says nothing beyond that (D-6).
- Any rung that changes two things at once, and any comparison without fixed seeds and matched
  budgets (D-3, D-6).
