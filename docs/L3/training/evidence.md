# training — the shipped evidence bundle

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-05
- **Owner:** the one shipped evidence artefact under `checkpoints/evidence/` — what it is and is not (§1), its sixteen
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

## 2. The sixteen top-level keys

| Key | Content |
|---|---|
| `stages` | the wall clock of each stage of the job — `run_R1_live`, `build_pool`, `matrix_live`, `rating`, `report` — each `{"seconds": <float>}` (`records.md` §12, ASM-15) |
| `errors` | the stages that raised, named with their exception; `[]` means every stage completed (`errors.md` §2) |
| `rungs` | one entry per rung in brief §2's order — its `axis`, `primary`, `carried_from` and the pool it declares — as the job transcribed the six rows: a compact spelling of the registry and **not** `rungs()`'s resolved configuration key for key (§3, `registry.md` §1–§2) |
| `devices` | `training.devices()`'s record of the platform the job ran on (`devices.md` §1, D-8) |
| `run` | the run record of `records.md` §12 plus this module's own `variants`, `header`, `baselines` and `axis row`, with `matrix` and `rating` attached beside them (`loop.md` §3–§4, `surface.md` §4.1) |
| `run_wall_clock_seconds` | the run's own cost: the sum of its per-seed `timings` wall clocks, and never `stages.run_R1_live`, which times the call (`loop.md` §4, ASM-15) |
| `run_hands` | the hands trained: the seed set's size × hands per variant per seed (`protocol.md` §2, ASM-8) |
| `pool_versions` | the version members of the pool the run trained against, and no baseline — empty for R1, which inherits no lineage (`records.md` §8, `registry.md` §3) |
| `pool_record` | the pool record `evaluation.pool_members` returned for that pool: `id`, `m`, `frozen` and the three pinned baselines (`records.md` §8, ASM-16) |
| `r2_pool` | the pool `R2`'s declaration carried when the job ran: its `id` and its version members — §3 records what the shipped file holds here and why |
| `matrix` | `records.md` §10's matrix over that pool plus the run's primary variant, at the `live` budget (`records.md` §10, `league.md` §6) |
| `rating` | `records.md` §11's Bradley-Terry rating over that matrix (`records.md` §11, `league.md` §5) |
| `report_families` | the twelve family names `evaluation.report` assembled, sorted, and none added (`protocol.md` §1, `records.md` §13) |
| `report` | `report`'s record key for key: the twelve families of `protocol.md` §1, `matrix` and `rating` included (`records.md` §13) |
| `index_summary` | `checkpoints()` read once: `shipped`, `pending`, the entry count and whether every entry's file exists (`checkpoints.md` §4–§5) |
| `index_missing` | the entries `checkpoints()` names that the repository does not carry; `[]` is the shipped set being complete (`checkpoints.md` §5, FAM-12.5) |

## 3. What the shipped file holds, and the blocks that no longer match it

The measurement is the file's, and a reader takes it from there rather than from any prose (`protocol.md` §2):

- **The run**: seeds `0, 1, 2` at 1,000 hands per variant per seed — 3,000 hands in 340.5 s, measured 0.120, 0.105 and
  0.116 s per hand at seeds 0, 1 and 2 (`run.timings`, ASM-21, ASM-8). `run.curves["naive-numeric"]` is the axis
  `100 … 1,000` with the three seeds' `td_error` series and the one spread — the series are the run's, the spread is
  the stale array §3's fourth bullet records (`curves.md` §2–§4).
- **The pool**: `pool-bcbea031cb617939`, `m` 5, `frozen`, the three pinned baselines and no version, because R1
  inherits no lineage and trains against `league.md` §2's baselines-only pool (`records.md` §8, `registry.md` §3).
- **The table**: four members — `random`, `always-call`, `oracle`, `variant-1` — six cells at 120 hands each, seats
  alternating 60/60 in every cell, table seed `20261105` (`records.md` §10, `league.md` §6, D-16). `variant-1` is the
  trained seed-0 final model of `naive-numeric`, loaded by `evaluation.policy_from`; it is **not** the untrained
  learner `tables/league-full.json` names by the same id (L1 `league.md` §8).
- **The rating**: Bradley-Terry, anchored on the three baselines' mean at zero, 360 hands per member, `variant-1` at
  +0.410 with the 95% interval [0.236, 0.606], converged in 27 iterations over 200 bootstrap resamples
  (`records.md` §11, ASM-17).
- **The report and the index**: twelve families, the count `protocol.md` §1 fixes; and eighteen shipped artefacts
  (`shipped` `["R1"]`, `pending` `R2 … R6`) with every one of them on disk (`checkpoints.md` §5, FAM-12.5).
- **Three blocks the shipped file spells differently from today's code, none of them a measurement**: `run.params[V]`
  is `{"budget": 10000, "tolerance": 0.02}` where a run now writes `{budget, lower, upper}` — one band, spelled as
  its fraction there and as its two edges here (§5, `loop.md` §3); each `timings[V][seed]` entry carries the `device`
  it was measured on, this module's own key beside `records.md` §12's four required facts (`records.md` §1, §12); and
  `rungs` is a transcription of the six rows — the axis texts worded as `registry.md` §1 first declared them, each
  pool entry carrying `versions` and a `rung variant` lineage — where `rungs()` returns a resolved configuration key
  for key (`registry.md` §2, §1). A regeneration writes all three in today's spelling and changes no measurement.
- **`r2_pool` is empty in the shipped file, and that is a recorded defect, not a fact about R1's lineage**:
  `{"id": "pool-bcbea031cb617939", "versions": []}` is the *baselines-only* digest, which is R1's pool and not R2's,
  because the job's window test was a path test against the process's working directory and the repository's
  relative spellings did not resolve there. `registry._window` now resolves a declared path through `layout._resolve`
  against the repository root (`checkpoints.md` §2, `registry.md` §3), so `training.rung("R2")` reports the fifteen
  retained `naive-numeric` versions whatever directory it is called from; the shipped block predates that and is
  corrected by the next run of §6, never by editing it (`protocol.md` §5, D-16).
- **The shipped `spread` array is stale, and it is the one number here a reader must not quote.** It is not the max
  minus min of the three `td_error` series it sits beside: at all ten points it is 0.408–0.446 of the recomputed value
  (point 0, `0.018227…` recorded against `0.044066…` recomputed), it matches no pairwise difference of those series, and
  it is not a scalar multiple of the envelope — so it was computed over a series this file does not carry, before
  `curves._spread` fixed the statistic (`curves.md` §4). A reader takes the three series as the run's signal and
  recomputes the spread, or regenerates by §6; this array is never quoted as the statistic and never compared against a
  run record's repetition of its own (`protocol.md` §2, FAM-4.8).

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

The two layouts are one set of numbers, and in a record either one is a *view* of the same array — but not in this shipped
file: §3 records that its stored array no longer reproduces as the statistic of its own three series, so a reader who
needs the number recomputes it from the series and never reads the array here as a run record's repetition
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

## 6. How it is produced, and what an offline run does to reproduce it

**No shipped code produces this file.** The job spans two modules — it drives `training.run` and
`training.checkpoints` and then `evaluation`'s pool, matrix, rating and report — and no module in `module-map.md` §2
is granted that set, so the driver belongs to neither and is not one of the six entry points (D-12, D-13). The recipe
is therefore the producer, and it is one command's worth of calls in this order:

1. `record = training.run("R1")` — three seeds, 1,000 hands per variant per seed, `cpu`, from the repository root
   (`surface.md` §4, `loop.md` §5). Its `timings` are the run's cost and its `checkpoints` the six artefacts per pair.
2. `pool = evaluation.build_pool({"members": [], "m": 5, "frozen": True})`, then
   `pool_record = evaluation.pool_members(pool)` — R1's declaration (`registry.md` §3, `records.md` §8).
3. `member = evaluation.policy_from(record["checkpoints"]["naive-numeric"]["0"]["final"])` — the trained seed-0 final,
   loaded at the seed and encoding its container records; the **relative** path resolves from the repository root
   (`evaluation/surface.md` §12, `checkpoints.md` §2).
4. `matrix = evaluation.matrix(pool, [member], "live")` — four members, six cells, 120 hands, seat alternation; the
   variant slot is named `variant-1` by the matrix and not by the file (`records.md` §10, `matrix.md` §5).
5. `rating = evaluation.rating(matrix)` (`records.md` §11).
6. `record["matrix"] = matrix`, `record["rating"] = rating`, then `report = evaluation.report("R1", record, matrix,
   rating)` — the record carries the five families the run produced and these two are the ones a caller attaches
   (`records.md` §13, `surface.md` §4.1).
7. Reshape the curves to §4's layout, then write §2's sixteen keys: `run_wall_clock_seconds` is the sum of the record's
   per-seed wall clocks, `run_hands` the hands trained, `pool_versions` the run pool's non-baseline members, `r2_pool`
   and `index_summary` read from `rung("R2")` and `checkpoints()` (`loop.md` §4, `checkpoints.md` §4).

This is prose, not a shipped module, for the reason D-13 gives. It is verified where verification needs no run: `report`
reproduces the file's `report` key for key from the file's own `run`, `matrix` and `rating`; `pool_record` and
`index_summary` reproduce theirs; every path in the three path-bearing blocks resolves to a file under the repository
root — `r2_pool` does not, for §3's reason. Stage 1 is the one call not re-derived: re-running 3,000 hands costs the run,
and the figures it would print are the file's own `run.timings` (`ASM-21`, `protocol.md` §2). A regeneration replaces the
whole file, and nothing in it is corrected by editing the JSON (`protocol.md` §5, D-8).

## 7. What it is not

It is not a cache: nothing loads it and no run consults it (`§1`, `protocol.md` §5). It is not a claim of poker skill:
it names four members of one small game at one cell size, and its rating is a statement about those four and no others
(D-16, `docs/L1/league.md` §8). It is not a surface: no key of it is contract, no notebook writes it, and a key that a
talk needs is a defect in the six entry points and returns as an adjudication (`README.md` §3, D-12).
