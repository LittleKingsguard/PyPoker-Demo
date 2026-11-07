# training — the shipped evidence bundle

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-06
- **Owner:** the one shipped evidence artefact under `checkpoints/evidence/` — what it is and is not (§1), its seventeen
  top-level keys (§2), the measurement it holds (§3), the two curve layouts inside it (§4), the block that is a
  declared budget and not a count (§5), how it is produced (§6), and what it is not (§7)
- **Ceiling:** 165 lines. At the ceiling, split by owner — never append
- **Read with:** `curves.md` §4, `checkpoints.md` §2, §4–§5, `loop.md` §3–§4, `registry.md` §3, `errors.md` §4

## 1. The file, and what it is

One file: **`checkpoints/evidence/r1-live.json`** — UTF-8 JSON, one object, the R1 live run's whole evidence, written
once, offline, and committed (`docs/L1/protocol.md` §5, `docs/L1/league.md` §8). It lives under the tree this module
owns, beside the checkpoints it names (`module-map.md` §5, `protocol.md` §5).

It is **evidence and not an interface**: no entry point reads it or writes it, it is none of the six module-level
names `__init__.py` exports, and no caller may depend on a key of it (`README.md` §3, D-12). It is the second of the two
shipped artefacts that are not interfaces — the other, `tables/league-full.json`, is `evaluation`'s and is documented
in `docs/L3/evaluation/tables.md` §3–§5 — and the two are never confused: that one is a `full` table over one
membership, this one a `live` table plus the run that produced the member it was played with (`league.md` §8, D-8, D-16).

Every path inside it is a **repository-relative** spelling, POSIX separators, resolved from the repository root
(`checkpoints.md` §2): a record that named one machine's home directory could not travel with the repository or be read
on another machine, and evidence that reproduces only where it was made is not evidence (`protocol.md` §2, §5, D-8).

## 2. The seventeen top-level keys

| Key | Content |
|---|---|
| `stages` | the wall clock of each stage of the job — `run_R1_live`, `build_pool`, `matrix_live`, `rating`, `report` — each `{"seconds": <float>}` (`records.md` §12, ASM-15) |
| `errors` | the stages that raised, named with their exception; `[]` means every stage completed (`errors.md` §2) |
| `rungs` | `rungs()`'s six resolved configurations, copied once: each rung's `axis`, `primary`, `carried_from`, `variants` and `pool`, plus the resolved `seeds`, `samples`, `param_budget`, `table`, `device` and `snapshot_every` (`registry.md` §1–§2) |
| `devices` | `training.devices()`'s record of the platform the job ran on, **as that build's probe answered it** — the shipped file's `gpu.reason` is the superseded read-only probe's sentence and is evidence of that run, not of today's probe (`devices.md` §1–§2, D-8) |
| `run` | the run record of `records.md` §12 plus this module's own `variants`, `header`, `baselines` and `axis row`, with `matrix` and `rating` attached beside them (`loop.md` §3–§4, `surface.md` §4.1) |
| `run_wall_clock_seconds` | the run's own cost: the sum of its per-seed `timings` wall clocks, and never `stages.run_R1_live`, which times the call (`loop.md` §4, ASM-15) |
| `run_hands` | the hands trained: the seed set's size × hands per variant per seed (`protocol.md` §2, ASM-8) |
| `pool_versions` | the version members of the pool the run trained against, and no baseline — empty for R1, which inherits no lineage (`records.md` §8, `registry.md` §3) |
| `pool_record` | the pool record `evaluation.pool_members` returned for that pool: `id`, `m`, `frozen` and the three pinned baselines (`records.md` §8, ASM-16) |
| `r2_pool` | the pool `R2`'s declaration carries: its `id` and its fifteen retained version members, read from `rung("R2")` (§3, `registry.md` §3) |
| `matrix` | `records.md` §10's matrix over that pool plus the run's primary variant, at the `live` budget (`records.md` §10, `league.md` §6) |
| `rating` | `records.md` §11's Bradley-Terry rating over that matrix (`records.md` §11, `league.md` §5) |
| `report_families` | the twelve family names `evaluation.report` assembled, sorted, and none added (`protocol.md` §1, `records.md` §13) |
| `report` | `report`'s record key for key: the twelve families of `protocol.md` §1, `matrix` and `rating` included (`records.md` §13) |
| `index_summary` | `checkpoints()` read once: `shipped`, `pending`, the entry count and whether every entry's file exists (`checkpoints.md` §4–§5) |
| `index_missing` | the entries `checkpoints()` names that the repository does not carry; `[]` is the shipped set being complete (`checkpoints.md` §5, FAM-12.5) |
| `provenance` | the build the file came from, readable from the file alone: `producer`, `recipe`, `generated_utc`, `source_digest` (sha256, covered set, recipe, `file_count`, `files`), `git` (`commit`, `working_tree_dirty`), `versions` (python, numpy, pokerkit), `environment` (`PYTHONHASHSEED`), `device` and the `entry_points` called; `"unavailable"` where git cannot answer (§3, §6) |

## 3. What the shipped file holds

The measurement is the file's, and a reader takes it from there rather than from any prose (`protocol.md` §2): every figure below is **one generation's** — commit `1d3342b4476c0461d6fe548bcbf94f148248ffcd`, `generated_utc` `2026-11-07T01:13:38Z` — and a regeneration moves every one, so a reader of a later build reads the file and not this page.

- **The run**: seeds `0, 1, 2` at 1,000 hands per variant per seed — 3,000 hands in `run_wall_clock_seconds`
  339.9341840699781 s, the seeds' sum and never the call's, at 0.11764519330603071, 0.10976475726295029 and
  0.11252423350099706 s per hand for seeds 0, 1 and 2; `run.curves["naive-numeric"]` is the axis `100 … 1,000` with
  the three seeds' `td_error` series and the one spread (`run.timings`, `curves.md` §2–§4, ASM-21, ASM-8).
- **The stages**: `run_R1_live` 339.935722988972 s, `build_pool` 1.1361960787326097e-05 s, `matrix_live` 108.53024961898336 s
  over those 720 hands (0.1507 s/hand), `rating` 0.01256761298282072 s, `report` 0.0001083450042642653 s, `errors` `[]` (`records.md` §12, ASM-15).
- **The pool**: `pool-bcbea031cb617939`, `m` 5, `frozen`, the three pinned baselines and no version — R1 inherits no
  lineage and trains against `league.md` §2's baselines-only pool, so `pool_versions` `[]` (`records.md` §8, `registry.md` §3).
- **The table**: four members — `random`, `always-call`, `oracle`, `variant-1` — six cells at 120 hands each, seats
  alternating 60/60 in every cell, table seed `20261105` (`records.md` §10, `league.md` §6, D-16). Its widest cell is
  `random`–`variant-1` 9/0/111 against the mirror's 111/0/9 (−4.833333333333333 / +4.833333333333333). `variant-1` is
  the trained seed-0 final model of `naive-numeric`, loaded by `evaluation.policy_from`; it is **not** the untrained
  learner `tables/league-full.json` names by the same id (L1 `league.md` §8).
- **The rating**: Bradley-Terry, anchored on the three baselines' mean at zero, 360 hands per member, converged in 29
  iterations over 200 bootstrap resamples at `bootstrap_seed` 1609833776 (`records.md` §11, ASM-17): `random`
  −0.32883650535109454 [−0.48104125475526555, −0.17045670560387302], `always-call` 0.18572816494167615
  [0.039323780873805045, 0.3477999350799521], `oracle` 0.14310834040941836 [0.0026486280426915336, 0.27859514028563104],
  `variant-1` 0.5182078734126888 [0.3445550910139468, 0.7087477222264041].
- **The report and the index**: twelve families, the count `protocol.md` §1 fixes; eighteen entries (`shipped`
  `["R1"]`, `pending` `R2 … R6`), all on disk — `all_exist` true, `index_missing` `[]` (`checkpoints.md` §4–§5, FAM-12.5).
- **`r2_pool` holds R2's fifteen versions, and the regeneration closed that defect**: `pool-adc21204b5fef725` over
  `R1/naive-numeric/seed-{0,1,2}/step-{0600,0700,0800,0900,1000}`, because `registry._window` resolves a declared path
  through `layout._resolve` from the repository root (`checkpoints.md` §2, `registry.md` §3, `protocol.md` §5).
- **The `spread` array is the statistic**: at all ten points it is the max minus the min of that variant's three
  `td_error` series to twelve places (largest absolute gap 0.0), so it is quotable as a run record's repetition (`curves.md` §4, FAM-4.8).
- **`provenance` is the file's own record of the build it came from**: producer `scripts/regenerate-evidence.py`,
  recipe `docs/L3/training/evidence.md §6`, `generated_utc` `2026-11-07T01:13:38Z`, `source_digest` sha256
  `9089ef9f802744381426cb183e1353425393e468e2a46b2fc481b992758bc955`, 54 files (`src/**/*.py`, `pyproject.toml`),
  `git` `1d3342b4476c0461d6fe548bcbf94f148248ffcd` with the tree dirty, python 3.12.3 / numpy 2.5.4 / pokerkit 0.7.7,
  `environment` `{"PYTHONHASHSEED": "0"}`, `device` `cpu` and the eleven entry points called — so whether the file is
  current is read from the file (§6, `protocol.md` §5).

## 4. The two curve layouts, stated once here

`curves.md` §4 fixes the statistic — one array per variant and per point, the **max minus min** of the seeds' signals
at that index — and two layouts store it. Both were observed, and this document is where they are told apart so that a
reader holding one file knows what the other looks like (`records.md` §12, `protocol.md` §1):

- **The run record repeats it**: `run.curves[variant][str(seed)] = {"samples": [...], "td_error": [...],
  "spread": [...]}` — three entries per variant, the same spread array in each, which is a convenience for a reader
  holding one seed and **not** a per-seed measurement (`loop.md` §4, `curves.md` §5, FAM-4.8).
- **This bundle hoists it**: `run.curves[variant] = {"samples": [...], "seeds": {"0": {"samples", "td_error"}, …},
  "spread": [...]}` — the axis and the one spread at variant level, the three per-seed signals under `seeds`, and
  **no `spread` key inside a seed's entry**. `report.curves` repeats that same variant-level layout, because the
  report's family is this document's `curves` block verbatim (`records.md` §13, `league.md` §5).

The layouts are one set of numbers and here either is a *view* of the same array: §3 records that the stored array is
the max minus the min of its own three series at every point, so a reader may quote it as a run record repeats it
(`curves.md` §4, FAM-4.8).

## 5. `10000` in the header and `10119` in a cell: one is declared, the other measured

The file carries both figures and they do not contradict each other, because they are two different quantities:

- **`run.header["parameter counts"]` is the declared parameter budget**, per variant, plus the `variant-<position>`
  alias `_header` writes for the table the record will be reported against, and a declared `0` for each of the three
  baselines. It is `10000` for `naive-numeric` and `10000` for `variant-1`, because a run reads a declaration and
  measures no capacity — `agents.param_count` is not among the four `agents` calls this module is granted
  (`surface.md` §4.1, ASM-10, `module-map.md` §2).
- **A matrix cell's `params` is a measured count**, `agents.param_count` of the member the cell played
  (`records.md` §9). The trained `naive-numeric` final of seed 0 measures **10,119** — 1.19% above the declared budget
  and inside the declared ±2% band of 9,800–10,200 that `agents.param_count` matches a comparison pair on (ASM-10).

So the header states the budget the ladder declares and the cell states what the built learner holds; one number in both
places would claim a measurement the run never made (`records.md` §12, `surface.md` §4).

## 6. How the producer rebuilds it, and what a reader re-derives

**`scripts/regenerate-evidence.py` produces this file**, from the repository root, as one command:
`PYTHONHASHSEED=0 .venv/bin/python scripts/regenerate-evidence.py`. It is a script and not a module because `scripts/`
is claimed by no module (`module-map.md` §5): it drives two of them — `training.run`, `training.checkpoints` and then
`evaluation`'s pool, matrix, rating and report — a set no module in `module-map.md` §2 is granted (D-12, D-13). Shipping
it leaves this bundle no interface: it calls only the eleven declared entry points of `e2e-surface.md` §3, writes that
one file, and no entry point reads it (§1). It refuses an unpinned interpreter, or a `PYPOKER_CHECKPOINT_ROOT` set.

The recipe it performs, in the order §2's keys are written:

1. `record = training.run("R1")` — three seeds, 1,000 hands per variant per seed, `cpu`, from the repository root
   (`surface.md` §4, `loop.md` §5). Its `timings` are the run's cost and its `checkpoints` the six artefacts per pair.
2. `pool = evaluation.build_pool({"members": [], "m": 5, "frozen": True})`, then
   `pool_record = evaluation.pool_members(pool)` — R1's declaration (`registry.md` §3, `records.md` §8).
3. `member = evaluation.policy_from(record["checkpoints"]["naive-numeric"]["0"]["final"])` — the trained seed-0 final;
   the **relative** path resolves from the repository root (`evaluation/surface.md` §12, `checkpoints.md` §2).
4. `matrix = evaluation.matrix(pool, [member], "live")` — four members, six cells, 120 hands, seat alternation; the
   variant slot is named `variant-1` by the matrix and not by the file (`records.md` §10, `matrix.md` §5).
5. `rating = evaluation.rating(matrix)` (`records.md` §11).
6. `record["matrix"] = matrix`, `record["rating"] = rating`, then `report = evaluation.report("R1", record, matrix,
   rating)` — `matrix` and `rating`, the two families a caller attaches to those the record carries (`records.md` §13).
7. Hoist the curves to §4's layout, then write §2's seventeen keys — `rungs()`, `devices()` and `rung("R2")` read once
   beside the record, the index from `checkpoints()`, and `provenance` last (`loop.md` §4, `checkpoints.md` §4).

**Reproduction was measured, and it spares a reader the run.** With `PYTHONHASHSEED=0` the `matrix`, the `rating` and
the `report` replay identically in a fresh process from the shipped seed-0 final — `pool_record`, `matrix`, `rating`,
`report` and `report_families` all compared equal; three processes of a 250-hand run at seeds 0, 1, 2 gave identical
curves and the same pool id; and two full pinned regenerations gave identical curves, checkpoints, matrix, rating,
report, `rungs` and `r2_pool`. `report`, `pool_record` and `index_summary` also reproduce from the file's own blocks:
the matrix, rating and index re-derive without a run, and the curves and `timings` are what one costs (`ASM-21`, `protocol.md` §2).

**The pin is a condition, not a convenience.** `engine.equity`'s sampled estimator is not a function of `(readout, seed,
samples)` across processes, because its sampling universe is ordered by a set whose iteration order follows Python's
per-process string-hash seed. Measured here: one live cell read 57/3/60 in one process and 58/3/59 in another, and two
60-hand runs of one `(configuration, seed set, budget)` differed in their last two curve points; with the pin, four
processes agreed exactly. `oracle` compares that estimate against the pot odds, so an unpinned interpreter moves the
`oracle` cells and a run's curves with them — hence the refusal and `provenance.environment` (§3). The defect is
`engine`'s and `agents`', unfixed here; a regeneration replaces the whole file, and nothing in it is corrected by
editing the JSON (`protocol.md` §5, D-8).

## 7. What it is not

It is not a cache: nothing loads it and no run consults it (`§1`, `protocol.md` §5). It is not a claim of poker skill:
it names four members of one small game at one cell size, and its rating is a statement about those four and no others
(D-16, `docs/L1/league.md` §8). It is not a surface: no key of it is contract, no notebook writes it, and a key that a
talk needs is a defect in the six entry points and returns as an adjudication (`README.md` §3, D-12).
