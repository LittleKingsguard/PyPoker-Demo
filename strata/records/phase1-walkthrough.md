# phase1 walkthrough — blind documentation pass (D-14) · run 1, 2026-11-05

Runner: a fresh agent that never saw the build, staged at `/tmp/walkthrough-root` with a docs copy
and the six packages importable. Scenarios: 12, L0-authored from the docs and brief. Verdict:
**STALE** — the documented route (import → live R1 run → 4-member/6-cell live table → BT rating →
12-key report) works end to end, but shipped claims are contradicted by the artifact.

## Findings that are real defects (routed)

| Finding | Owning layer | Route |
|---|---|---|
| `docs/L1/league.md` §8: "a version that outranks a baseline has shown it beats that rule" — falsified by the shipped table (R1 ranks +0.410 while losing 51–63 to `always-call` and 56–58 to `oracle`) | L1 | L1 doc fix |
| `docs/L1/league.md` §7 and ASM-15 still state a 40 ms/hand bound; measured 0.105–0.130 s/hand (ASM-21 in the brief supersedes it) | L1 | L1 doc fix |
| `docs/L1/battery.md` §2: "the venv carries no `pytest`" — it carries 9.2.0 | L1 | L1 doc fix |
| `docs/L1/module-map.md` §5 and `README.md` claim a root `README.md` that does not exist | L1 | L1 doc fix + L0 authors the README |
| `docs/L3/evaluation/tables.md` §2: "no module that produces checkpoints exists yet" — `training` exists and indexes 18 artefacts | L3 | L1 routes down |
| `docs/L3/training/curves.md` §5 says spread is per seed; the shipped evidence file carries it at variant level | L3 | L1 routes down |
| `checkpoints/evidence/r1-live.json` records absolute `/media/...` checkpoint paths and is named by no document | L2/L4 (`training`) | L1 routes down |
| The shipped full table's `variant-1` is an untrained model (seed 31415) while the live table's `variant-1` is the trained seed-0 final — one member id, two different players, no doc warns | L2 (`evaluation`) | L1 routes down |
| No document states how to get started: dependencies, environment, the run mode, or a shell command for `training.run` (the package has no `__main__`) | L1 | L1 doc fix |
| Only 1 of the 6 notebooks `ladder.md` §7 names exists | L1 | L1 doc fix (scope note) |

## Findings discounted as staging artifacts (not defects)

The first run staged a copy of `docs/` plus the packages, but omitted `modules.json`, the shipped
`.ckpt` set, and the test batteries, and renamed `.venv` to `venv`. Four reported issues — "no
`modules.json`", "none of the 18 checkpoints ship", "no test suite ships", and the `.venv`/`venv`
path mismatch — follow from that staging, not from the project. They are recorded here so the next
run is judged against a faithful root, and the staging is corrected rather than the docs.

## Next

Routed to the owning layers; a second run follows against a root staged as a listener would clone
it (docs, packages, batteries, notebooks, tables, checkpoints, packaging, README — no git history
and no `strata/` design root). A unit is recommended as ready only on a `PASS` (D-14).
