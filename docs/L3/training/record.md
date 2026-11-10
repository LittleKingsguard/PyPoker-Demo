# training — the run record, key by key

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-09 · **Rev 1** carries `loop.md` §3's key-by-key table and `loop.md` §4's sub-records out of a file at its ceiling, and adds the two keys D-29 writes — `game` and `greedy` — with the header's and the pool block's shape rows (`records.md` §12, §15, `shapes.md` §3, D-28, D-29)
- **Owner:** `_record()` and `_header()` — the record key by key (§1), the sub-records in the shape their readers expect (§2), the two keys D-29 adds and the rows that repeat the shape (§3), what is left to L4 (§4). `loop.md` §3 and §4 keep their numbers as pointers into this file, because tests cite them; nothing here is a second claim — every sentence of §1 and §2 is one of those two sections', moved, and §3 is the shape's own statement
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `loop.md` §1 steps 2 and 8–9, §2, §3, §4, §6, `checkpoints.md` §2–§3, `curves.md` §5, `greedy.md` §1–§2, `registry.md` §1–§3, `errors.md` §4, `records.md` §8, §12, §15

## 1. The record, key by key (moved from `loop.md` §3)

`records.md` §12's thirteen **required** keys — `variants` among them, and `rules` and `utilities` since D-19 and D-20 — plus the two D-29 adds, `game` and `greedy`, which §12 makes required of a record this build writes, and then this module's own evidence keys, `header`, `baselines` and `axis row` (`surface.md` §4, `utilities.md` §7, `records.md` §12, §15, D-29):

| Key | Content |
|---|---|
| `rung` | the rung name, or the unregistered configuration's own `name` (`records.md` §12) |
| `game` | the shape the run played — the configuration's `game`, else the default (`shapes.md` §3, §3 below, D-29) |
| `greedy` | variant → seed → `records.md` §15's block — the pass, and the only decision stream a run retains (`greedy.md` §1–§2, ASM-38, D-28) |
| `curves` | variant → seed → `{samples, td_error, spread}` — the ten snapshot steps, the mean absolute `td_error` of each interval, the spread across seeds (`curves.md` §5) |
| `pool` | `{id, lineage, m, frozen, game, members, rules, utilities}`: the **declared** id, the read-back `m`, `frozen` and ordered members — the pool's **pinned** baselines first (the anchor three, then any declared folder), then the version window — the one shape the pool is on, and `rules` and `utilities`, the distinct rules and utilities those version members declare (`records.md` §8, §12, `registry.md` §3, ASM-32, D-19, D-20, D-21, D-29) |
| `checkpoints` | variant → seed → `{snapshots: [<the retained five paths>], final: <that pair's final model>}`, each path `layout._relative` of what `agents.save` was handed: repository-relative with POSIX separators inside the repository root and **unchanged — absolute — outside it** (`checkpoints.md` §2, `write-root.md` §5) |
| `seeds` | the seed set the run used, after `loop.md` §5's default |
| `budget` | the hands per variant per seed the run used, after `loop.md` §5's default |
| `device` | the device the run used, after `loop.md` §5's default (`protocol.md` §6, D-8) |
| `params` | variant → `{budget: 10000, lower: 9800.0, upper: 10200.0}` — the declared budget and its ±2% bound: the entry's `param_budget`, else the configuration's, else `declarations.PARAM_BUDGET`, validated at `loop.md` §1 step 1 (`loop.md` §6); a run measures no capacity (`surface.md` §4, ASM-10) |
| `table` | the declared table budget, `live` or `full`; a configuration declaring none is recorded at `live` (`league.md` §6, `loop.md` §2) |
| `timings` | variant → seed → `{hands, wall_clock_seconds, seconds_per_hand, hands_per_second}` (§2, `records.md` §12) |
| `variants` | the list of `{name, backend, encoding, architecture, learning_rule, utility, samples, snapshot_every}` — the entry's declaration, **the rule and the utility the variant was actually built under**, and the interval the run used (§2, D-19, D-20) |
| `rules` | the distinct rules the run declared and trained, in declaration order: one name for a ladder rung, two for a configuration whose arms name two estimators (`records.md` §12, `rules.md` §7, D-19) |
| `utilities` | the same set on D-20's axis: the distinct utilities the run declared and trained, in declaration order, read through `_trained_utility` — one for a ladder rung, two for a configuration whose arms name two (`records.md` §12, `utilities.md` §7, D-20) |

**One id per record, and it is the declared one** (D3, stated in `loop.md` §3): `pool.id` is `config["pool"]["id"]` — for a registry rung the read-back id of the membership, for a custom configuration its own `"pool-r7"`-style id — and the read-back digest id is **not** carried anywhere in the record, because `tests/e2e/_surface.py`'s `pool_identity` reads every `id` a record declares and two ids in one two-variant record fail FAM-3.18 (ASM-16).

## 2. The sub-records, in the shape their readers expect (moved from `loop.md` §4)

- `curves[V][str(seed)] = {"samples": [...], "td_error": [...], "spread": [...]}` — three ten-element lists: the axis, the signal and the across-seed spread repeated at each of that variant's seeds because it is one fact about it (`curves.md` §5).
- `checkpoints[V][str(seed)] = {"snapshots": [five paths], "final": <one path>}` — the retained last M = 5 of the ten the pair wrote and that pair's final model, six artefacts and never eleven (`checkpoints.md` §3, `write-root.md` §5); `_records.py`'s `checkpoint_paths_of` reads this key alone. **The pass adds nothing here**: it reads the final model and writes no path, so this block is what it was before D-29 (`checkpoints.md` §3, `greedy.md` §1).
- `params[V] = {"budget": 10000, "lower": 9800.0, "upper": 10200.0}` — declared, never measured: the entry's `param_budget`, else the configuration's, else 10,000, with `lower`/`upper` that number ∓2% (`module-map.md` §2, ASM-10).
- `timings[V][str(seed)] = {"hands": budget, "wall_clock_seconds": ..., "seconds_per_hand": ..., "hands_per_second": ...}` — the facts `harness.timings` reports; the four key names are deliberate, because the battery's `timing_facts` classifies a key by what it names (`e2e-surface.md` §3.6, ASM-15, FAM-13.5).
- `variants[i] = {name, backend, encoding, architecture, learning_rule, utility, samples, snapshot_every}` — `architecture` the entry's record copied verbatim, `samples` its declared budget (the run's hands when the entry declares none), `snapshot_every` the interval the run used, and `learning_rule`/`utility` **the member of each axis the learner was built under**: the entry's, else its configuration's, else the catalogue's first, which is what `agents` built when the entry named neither (`rules.md` §4, `utilities.md` §5, D-19, D-20).
- `rules = [<one rule per distinct estimator trained>]` and `utilities = [<one utility per distinct objective trained>]` — the sets the per-variant rows name, in declaration order and deduped, so `records.md` §12's `rules` and `utilities` are read off the record itself; `pool.rules` and `pool.utilities` are the same sets for the opposition, off the members' own fields (`records.md` §8, §12, `rules.md` §7, `utilities.md` §7, D-19, D-20).
- `baselines` and `header` — `_pool_baselines(pool_record)` reads the baseline ids the frozen pool **actually holds** off its own members, so `baselines["rows"]` is one `{member, hand count, pinned: True, measured: False}` row per baseline the pool holds — the anchor three and any declared folder, in the pool's order — and the header's `parameter counts` carry a declared `0` for each of those names: no count here is a hard-coded three (`records.md` §8, `protocol.md` §3, ASM-32, D-21, `evaluation/surface.md` §13).

## 3. The two keys D-29 adds, and the rows that repeat the shape

**`game` is one name, and the record never names a shape it did not measure.** The value is `declarations.require_game`'s answer for the configuration's `game`, else its first variant entry's, else the catalogue's first shape — so a record already on disk that carries no `game` reads as the default shape, exactly as a version-1 container's absent rule reads as the catalogue's first (`records.md` §12, `shapes.md` §3, `loop.md` §1 step 1, D-19, D-29).

**`greedy` is one block per variant per seed, keyed as `curves` is.** `_record` receives the pass's blocks from `loop.run` and writes them through unchanged, so the record carries `mode`, `seed`, `hands`, `net_chips` and the ordered `decisions` for every pair the run trained and nothing that is not the pass (`records.md` §12, §15, `greedy.md` §2, D-28).

**`pool.game` repeats the shape, because a pool record requires it.** `records.md` §8 makes `game` a field of a pool record, so the block carries the read-back value and falls back to the record's own name only if an owner returned none — a run never reports a pool on a shape the run is not on (`records.md` §8, `shapes.md` §3, D-29).

**The `header` is the run's shape's, and its nine items do not grow.** `_header(configuration, table, hands, seed_set, device, checkpoints, interval, baselines, shape=None)` returns `game` = `engine.game_config(shape)` and `action space` = `declarations.vocabulary(shape)` — three descriptors on the fixed-limit shape and six on the no-cap one, in the shape's declared order — so the header is the only route by which a D-5 notebook sees which game its curves are about (`protocol.md` §1, `shapes.md` §2–§3, `sizing.md` §3, `loop.md` §7, `ladder.md` §7, D-5, D-29). Its keys are `game`, `action space`, `parameter counts`, `sample budget`, `cell size`, `seeds`, `table seed`, `device`, `checkpoints` and `snapshot interval`; the shape is the `game` row's own identity and the record's top-level `game`, never a tenth item, and `evaluation.report`'s own tenth key stays `evaluation`'s (`report.md` §2, `shapes.md` §6, D-29). `declarations.vocabulary` reads each descriptor through the granted `features.decode_action(index, shape=...)`, because `features.action_space` is not among this module's five granted `features` calls (`module-map.md` §2, `features/surface.md` §7, §9, D-13).

## 4. What is left to L4

Whether `_record` builds the mapping literal or assembles it, the order its keys are written in (a record's key order is no reader's contract), whether `pool.game` is read back or echoed, and whether `_header` takes the shape positionally or by keyword — its `shape` argument is contract for `tests/training/` (`README.md` §4), as are `_record`'s two new trailing arguments, `shape=None` and `greedy_block=None`, which `loop.run` passes positionally and which a unit case may omit to get the empty `greedy` block and the default shape.

Not L4's: §1's keys and the one-id rule, §2's sub-record shapes and the four `timings` key names, the two keys D-29 adds and the three rows that repeat the shape, the header's nine items and its `game`/`action space` rows, and `evaluation.report`'s tenth key staying the report's (`guardrails.md` G6, G8, G23, `loop.md` §8).
