# phase1 walkthrough — blind documentation pass (D-14) · run 5, 2026-11-06

Runner: a fresh agent, staged at `/tmp/wt5` as a listener's clone. Scenarios: 13, unchanged across
all five runs. Verdict: **STALE**, and the remaining findings are bookkeeping — every one of the 13
steps completed from the documentation alone, every documented command worked as written, and the
runner verified the shipped tree byte-identical (34 files, sha256 unchanged) after **both** the
pytest battery and the `unittest` census. Substance is done; the docs disagree with the tree in
three places.

## Confirmed working (run 5)

Orientation and reading order; the fixed game's parameters; versions and imports; the battery run
rule (219 pytest, 219 census, 13 batteries green, five documented collection errors); a redirected
3,000-hand R1 run at 0.1051–0.1191 s/hand; curves and how to read them; a 720-hand live table in
109.3 s with two cells read; the rating (+0.518 [0.345, 0.709]) and its rank-versus-head-to-head
rule; the shipped full table's untrained membership and 0.1324 s/hand cost; the notebook headless
(exit 0, reproducing the shipped evidence); the claims and refusals; a decision from a shipped
checkpoint; and the whole GPU page, whose every command behaved as documented.

## Findings

| # | Finding | Owner | Disposition |
|---|---|---|---|
| F1 | `docs/L3/training/evidence.md` §2's `devices` row calls the bundle's `gpu.reason` "the superseded read-only probe's sentence"; the bundle now carries today's read-write sentence, because the evidence was regenerated after the probe was fixed | L3 training | routed |
| F2 | Three L2/L3 documents cite "walkthrough finding 5" and `docs/L1/README.md` cites run 4's findings, but the record they point at was run 3's and no run-4 record was ever written; `strata/walkthrough.md` §7 replaces the record every run, so a citation by run number cannot stay true | L0 (record) + L1/L2/L3 (citation form) | record replaced by this one; the citing documents move to citing the **subject** rather than a run's finding number |
| F3 | "Shipped" was stated two ways: the index names **18** artefacts (the retained five snapshots plus each seed's final) while the repository carried **33** `.ckpt` files (every snapshot), and `docs/L1/ladder.md` §7 called 33 "the shipped set's own" | L0 (tree) + L1/L3 (wording) | tree pruned to the index: 18 `.ckpt`, 0 unindexed, 0 missing, batteries green; the wording is routed |

## L0's own share

Both tree-side faults were mine. F3 is the visible one: I force-added every snapshot when first
committing the checkpoint set, which made the repository disagree with its own index and with
ASM-5's retention policy. Pruned to the 18 the index names, verified by walking `checkpoints/`
against `training.checkpoints()` — `index entries 18, missing 0, unindexed 0` — and by
`tests/training`, `tests/harness` and `tests/integration/training` (206 cases) afterwards.

The citation lesson is also now a rule: a document cites the *finding's subject*, never "finding n
of run k", because this file is replaced on every run (D-14, `strata/walkthrough.md` §7).

A unit is recommended as ready only on a `PASS`; this remains a loop recommendation, not readiness.
