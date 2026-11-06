# training — the shipped R1 evidence file, as an integration fact

- **Layer:** L2 · **Module:** `training` · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-06
- **Owner of this file:** the one shipped evidence artefact under `checkpoints/` — that it exists and what it is not
  (§1), which of its blocks are this module's own record and which a caller attaches (§2), the spelling rule its paths
  obey (§3), the two curve layouts it and a run record carry (§4), and what no caller may do with it (§5) (D-8, D-12,
  D-16, `protocol.md` §5, `records.md` §12–§13)
- **Ceiling:** 85 lines. At the ceiling, split by owner — never append
- **Reads:** `docs/L1/protocol.md` §5, `league.md` §8, `records.md` §12–§13, `module-map.md` §3, §5; at this module's own
  design `docs/L3/training/evidence.md` §1–§7, `checkpoints.md` §2, §4–§5, `loop.md` §3–§4, `curves.md` §4–§5

## 1. The file, and its status

**`checkpoints/evidence/r1-live.json`** ships in the repository as `training`'s record of the R1 live run: that run's
run record, the pool it trained against, its four-member/six-cell `live` table, the Bradley-Terry rating over that
table, its twelve-family report and the shipped checkpoint index (`protocol.md` §5, `docs/L1/league.md` §8, ASM-18).

It is **evidence and not an interface**. It is not one of the six entry points, it is not a returned record, and no
entry point reads it or writes it — the one writer is `scripts/regenerate-evidence.py`, a script outside every module's
paths — a committed file an entry point consulted would make a talk's result depend on something that was written once
and never re-measured (D-8, D-12, `surface.md` §1, `protocol.md` §5, `docs/L3/training/evidence.md` §6). A D-5 notebook
reads it with `json` and plots from it; nothing else reads it at all (`loop.md` §6, D-5).

Its shape is seventeen top-level keys, and they are all evidence: `stages`, `errors`, `rungs`, `devices`, `run`,
`run_wall_clock_seconds`, `run_hands`, `pool_versions`, `pool_record`, `r2_pool`, `matrix`, `rating`,
`report_families`, `report`, `index_summary`, `index_missing`, and last `provenance` — the build the file came from
(`docs/L3/training/evidence.md` §2). Their content, and the module design's status for each of them, are `evidence.md`
§2, §6 and §7 there. This document fixes only the three facts at the integration edge: which blocks are this module's
record (§2), how its paths are spelled (§3), and which layouts its curves may take (§4) (`records.md` §13, `surface.md` §4).

## 2. Which blocks are this module's record, and which a caller attaches

The bundle's `run` block **is** the record `run` returns — `records.md` §12's ten required keys plus this module's own
`variants`, `header`, `baselines` and `axis row` (`surface.md` §4, §4.1) — with two differences that belong to the
job: `curves` is reshaped as §4 says, and `matrix` and `rating` are **attached by the caller**, because a run measures
no cell and fits no rating (`module-map.md` §3, `records.md` §13, `surface.md` §4.1).

The remaining blocks are the job's, not an entry point's: `stages`, `errors`, `run_wall_clock_seconds`, `run_hands`,
`pool_versions`, `pool_record`, `r2_pool`, `matrix`, `rating`, `report_families`, `report`, plus `rungs`, `devices`,
`index_summary` and `index_missing`, which are `rungs()`, `devices()` and `checkpoints()` read once and copied, and
`provenance`, which the producer writes and no entry point returns (`surface.md` §2, §6, §7, `evidence.md` §2, §6).

## 3. The paths it carries are repository-relative

Every path in `run.checkpoints`, `run.header.checkpoints` and `report.header.checkpoints` is **repository-relative**
with POSIX separators — `checkpoints/R1/naive-numeric/seed-0/final.ckpt` — and that is what `run` records: `agents.save`
is handed an absolute path and writes it, and the record carries `layout._relative` of it (`surface.md` §4,
`checkpoints.md` §2, `protocol.md` §5).

The reason is the surface's, not a preference: a record that named one machine's home directory cannot travel with the
repository or be read on another machine, and evidence that reproduces only where it was made is not evidence a third
party can re-run (D-6, D-8, `protocol.md` §2, §5). The index spells the same artefact the same way, so one artefact has
one spelling across the index and the record and no listing names it twice (`surface.md` §7, FAM-12.6); and this module
resolves a declared path through `layout._resolve` from the repository root, never from the caller's working directory,
and hands `evaluation.build_pool` the resolved records (`layout._resolved`) while keeping `_relative`'s spelling in every
record it returns — so a pool's membership and the record's spelling do not depend on where a talk was started
(`checkpoints.md` §2, `registry.md` §3, `evaluation/surface.md` §5).

## 4. The two curve layouts

`curves.md` §4 fixes the statistic: one array per variant and point, the max minus min of the seeds' signals at that
index. Two layouts carry it, and both are in use — a reader holding either file must be able to recognise the other
(`records.md` §12, FAM-4.8):

- a **run record** keys it per seed — `curves[variant][str(seed)] = {samples, td_error, spread}` — with the variant's
  one spread array repeated in each seed's entry: a convenience, and not a per-seed measurement (`surface.md` §4,
  `curves.md` §5);
- this **bundle** hoists it — `curves[variant] = {samples, seeds: {str(seed): {samples, td_error}}, spread}` — once
  per variant beside a `seeds` mapping, and no seed entry carries a `spread` of its own (`evidence.md` §4).

Neither layout makes the spread a property of one seed, and in this shipped file the stored array **is** the max minus
the min of the three series beside it at every point — `evidence.md` (L3) §3 records the check to twelve places — so a
reader may quote it and recompute it (`curves.md` §4, FAM-4.8).

## 5. What no caller may do with it

- **Read a result out of it.** It is one run at one budget on one game; a version's worth is a table position
  `evaluation` measures (`module-map.md` §3, D-6, D-16).
- **Write it.** No entry point writes under `checkpoints/evidence/`, and a talk that needs to record something writes
  its own file (`surface.md` §1, D-12).
- **Treat the two files that name `variant-1` as one member.** This bundle's `variant-1` is the trained seed-0 final;
  `tables/league-full.json`'s is an untrained learner at its recipe seed, and the two are never compared
  (`docs/L1/league.md` §8, D-16).
- **Depend on any key of it.** Every key is evidence; a key a talk needs is a defect in the six entry points and
  returns as an adjudication (`surface.md` §1, `README.md` §3, D-12).
