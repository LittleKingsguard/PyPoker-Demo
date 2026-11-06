# phase1 walkthrough — blind documentation pass (D-14) · run 2, 2026-11-05

Runner: a fresh agent, staged at `/tmp/wt2` as a listener's clone (source, tests, notebooks,
tables, shipped checkpoints, packaging, docs, README, the `strata/` record; no git history, venv
pre-populated). Scenarios: the same 12 as run 1, so the two are comparable. Verdict: **STALE** —
the documented route works end to end (install → import → live R1 run → 4-member/6-cell table →
rating → 12-key report → checkpoint decision), but several shipped claims are contradicted.

## Defects to repair (routed by owning layer)

| # | Finding | Owner |
|---|---|---|
| 1 | `notebooks/r1-naive-numpy.ipynb` **fails when launched as `README.md` §Quickstart and `docs/L1/ladder.md` §7 say to launch it**: the kernel cwd is `notebooks/`, and `evaluation.policy_from` resolves the record's repository-relative checkpoint path against the cwd, so the table cell raises `CheckpointUnreadable` after a 6-minute run has already succeeded | `training` (the notebook must resolve the repo root) |
| 2 | The shipped `checkpoints/evidence/r1-live.json` **does not reproduce on the current build**: a documented re-run gives curves differing from the first interval, a live table of `variant-1` +0.506 [0.290, 0.696] where the file records +0.410 [0.236, 0.606], and `random`–`variant-1` 111–9 where the file records 103–17. Determinism is not in question — three runs within the build were identical to the digit — so the evidence describes an earlier build | `training` (regenerate it, or record its provenance) |
| 3 | `docs/L3/training/guardrails.md` G20 claims a run at the declared budget and seed set "rewrites the shipped ones with the same content"; it rewrites them with different content (finding 2) | L3 |
| 4 | The live table measured **0.150 s/hand** (108.3 s for 720 hands), 14 % above the stated 0.105–0.132 band; the training run itself stayed inside it (0.108–0.117) | L1 cost rows |
| 5 | The documented batteries **write into the shipped `checkpoints/` tree** (`seed-4103`, `seed-8807`, `R2/`, `R4/`), which `battery.md` §2 calls self-sufficient and `checkpoints.md` §5 says cannot happen | `training` + `harness` (write to a temp root) |
| 6 | `training.run('R1')` silently overwrites the shipped checkpoints before the reader loads them — intended, but unmentioned where a newcomer is told to run it | L1 `getting-started.md` |
| 7 | The L1 route never says how the variant policy is obtained for `matrix(pool, [variant_policy], "live")`; only the notebook shows the sequence | L1 |
| 8 | A matrix cell **cannot be replayed** from the `seed` it records: `records.md` §9 calls it "the seed the cell was played at", but `matrix` seeds member policies from the table seed by position. Replaying the recorded seed gives 51/3/66, not the cell's 57/3/60 | L1 `records.md` §9 |
| 9 | No document states the working directory the notebook requires — the difference between it working and failing (finding 1) | L1 |

## Where run 2 is clean

Orientation, the fixed game's parameters, dependencies and setup, the battery run rule, the live
training command, the curves' reading, the live table's construction and two cells, the rating's
contract and the rank-versus-head-to-head rule (`league.md` §8 now explains the very case with its
numbers), the shipped full table's provenance (`member_status` marks `variant-1` untrained), the
claims and refusals, and a real decision from a shipped checkpoint. Run 1's staleness in those
areas is closed.

## Note on staging

Run 2 staged a listener's clone rather than the protocol's minimal root (docs + installed artifact
+ empty directory), because the scenario set asks a listener to run batteries and open a notebook.
Run 1's staging artifacts — missing `modules.json`, missing checkpoints, `.venv`/`venv` naming —
are therefore discounted, and the remaining findings are against the project, not the staging.

A unit is recommended as ready only on a `PASS`; this is a loop recommendation, not readiness (D-14).
