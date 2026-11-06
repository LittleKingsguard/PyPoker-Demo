# evaluation — the two budgets and the shipped table

- **Owner:** the two table budgets and the one artefact that ships — the arithmetic (§1), what can honestly be
  measured today (§2), the file's name and **schema** (§3), how it is produced (§4), its provenance and cost block
  (§5), and what changes when `training` ships snapshot lineages (§6) (`league.md` §5–§7, `module-map.md` §5, D-8)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `matrix.md` §5–§6, `rating.md` §5, `declarations.md` §4, `guardrails.md` G19

## 1. The arithmetic

One membership, two cell sizes: `live` and `full` differ in `hands_per_cell` and in nothing else (`league.md` §5,
ASM-14). A table plays `cell_count(K) × hands_per_cell` hands, so the whole budget is arithmetic on K:

| K | Membership | Cells = K(K−1)/2 | `live` (120/cell) | `full` (1,500/cell) |
|---|---|---|---|---|
| 4 | the three baselines + one variant — R1, and every table this repository can build today (§2) | 6 | 720 | 9,000 |
| 9 | a full window (8 members: 3 baselines + M = 5 versions) + one variant | 36 | 4,320 | 54,000 |
| 10 | a full window + two variants (R4, R5, R6) | 45 | 5,400 | 67,500 |

The K = 9 and K = 10 columns are `league()`'s declared `hands_played` (`declarations.md` §4.1) and what a rung with a
full window costs; the K = 4 column is the smallest the surface allows and the only one this repository can build before
`training` exists (§2). At ASM-15's bound of 40 ms a hand, K = 4 full is about six minutes of CPU and K = 10 full under
an hour — the bound sizes the table, and no case asserts that a wall clock was beaten (ASM-15).

## 2. What ships today, and what it may never pretend

The members of a table are a frozen pool plus the rung's variants, and **no module that produces checkpoints exists
yet**: `training` and `checkpoints/` are not built, so the repository ships no version checkpoint (`docs/L1/protocol.md`
§5, `module-map.md` §7). The shipped table therefore names a membership the module can build **and measure today**:

- the **three pinned baselines** — a frozen pool whose declaration is `{"members": [], "m": 5, "frozen": True}`, which
  is R1's pool (`league.md` §2);
- **one variant member**, `variant-1`, built deterministically from its own recipe, which §5 records — a
  learner from `agents.build_learner` at the rung's declared backend, encoding and architecture, made a policy by
  `features.build_encoder` and `agents.as_policy` at the module's own constant `VARIANT_SEED = 31415` (`scheduler.md` §3,
  `matrix.md` §4). It is **not** `_member_seed`'s: that digest derives the three baselines' seeds and nothing else, and a
  variant handed to `matrix` is a policy already built (`matrix.md` §4). That call belongs to the **offline producer and to
  no entry point**, and `docs/L2/evaluation/league.md` §7 admits it explicitly: the job stands where `training` stands,
  because a rung's variants are `training`'s to hand `matrix`, and until `training` ships snapshot lineages the producer
  builds its one variant at the recipe the artefact records (`league.md` §7, `module-map.md` §2). No talk makes it and no
  surface call reaches it (`README.md` §5).

`K = 4`, `6` cells, `9,000` hands at the `full` budget. It is a real table of four real members at one hand count,
and it says in its own provenance which membership it is. It **never** names a version it could not load: no
member id, path or lineage in the file refers to a checkpoint that is not on disk (`protocol.md` §5). A table whose
only model member is an untrained learner is weak evidence, and the file says so — the untrained policy is declared
by its recipe, not dressed up as a trained one. It is also **not** `protocol.md` §5's shipped checkpoint pool: that
pool is `training`'s to retain and ship, and this file's `membership_kind` says which of the two it is (§6).

## 3. The file, and its schema

One file, at the module's own path (`module-map.md` §5, ASM-11): **`tables/league-full.json`** — UTF-8 JSON, one
object, its keys in this order:

| Key | Content |
|---|---|
| `schema` | the `str` `pypoker-evaluation-league-table/1` — the format's name and version, so a reader can refuse a different one |
| `table` | `full` — the budget this table was measured at, repeated from the matrix (`records.md` §10) |
| `pool` | `records.md` §8's pool record the table was measured over: `id`, `m`, `frozen`, `members` (§2) |
| `matrix` | `records.md` §10's matrix record, exactly as `matrix` returned it (`matrix.md` §5) |
| `rating` | `records.md` §11's rating record, exactly as `rating` returned it (`rating.md` §5) |
| `provenance` | §5's first block: what produced it, from what membership, by which recipe |
| `cost` | §5's second block: the measured cost of that run |

`pool`, `matrix` and `rating` are the three records unchanged — the file adds no member, no cell and no value, so a
reader can compare the file's matrix against its own `matrix` call record for record (`league.md` §5). Every key of
those three records is a `str`, so JSON carries them without a rename: the file is a faithful dump, not a
translation.

## 4. How it is produced

The file is written by `src/evaluation/tables.py`, and **no entry point reads or writes it**: D-12 forbids a twelfth
surface and `league.md` §5 makes the file evidence rather than an interface. The producer is that module's
`__main__`, so the recipe is one command and not a notebook that knows the schema:

    PYTHONPATH=src .venv/bin/python -m evaluation.tables        # writes tables/league-full.json

It calls `build_pool` with §2's declaration, `matrix(pool, [variant], "full")` and `rating(matrix)`, and then
`_build_document` / `_cost_block` / `_write_document` — the private functions that hold the schema of §3 and §5, whose
target is the module constant `SHIPPED_PATH = "tables/league-full.json"`, so the file's path and shape have one home
(`README.md` §4). It times the `matrix` call with `time.perf_counter` and counts the hands it played, which is what
§5's cost block records. It is run offline, once, and the result is committed; a talk's live table is played by the
talk and never written to this path (`league.md` §5, D-8). **Unverified**: no unit case drives the producer itself —
writing the artefact needs a real 9,000-hand `full` table and a write under `tables/`, which is not the unit battery's
cost — so `EVL-6.*` checks the file this design ships and its schema, never the command that built it
(`guardrails.md` G19).

## 5. The provenance and cost blocks

    "provenance": {
      "module": "evaluation",
      "entry_points": ["build_pool", "matrix", "rating"],
      "schema": "pypoker-evaluation-league-table/1",
      "table_seed": 20261105,
      "budget": "full",
      "hands_per_cell": 1500,
      "cell_count": 6,
      "hands_played": 9000,
      "membership_kind": "baselines+variant",
      "members": ["random", "always-call", "oracle", "variant-1"],
      "variants": [{"id": "variant-1", "backend": "numpy", "encoding": "flat-numeric",
                    "architecture": {"kind": "naive-stack", "width": 96, "depth": 2},
                    "seed": 31415, "params": <agents.param_count>}],
      "pool": {"id": "<the pool record's id>", "m": 5, "frozen": true}
    }

    "cost": {"hands": 9000, "seconds_per_hand": <float>, "hands_per_second": <float>,
             "wall_clock_seconds": <float>, "device": "cpu",
             "per_hand_ceiling_seconds": 0.04, "measured": true}

- `variants` is the **recipe** a third party needs to rebuild the same membership: the backend, the encoding name,
  the architecture kind and its settings, the seed the policy was built at — the module's own `VARIANT_SEED`, never a
  table-derived one — and the parameter count `param_count` measured, so the file names a member whose capacity is a
  measurement and not a claim (ASM-10, `records.md` §2). It is the recipe of a learner `agents.build_learner` built in the
  offline job, and that call is the producer's own and no entry point's (`league.md` §7, §2 above). This is the
  producer's own measurement, and it does not contradict the matrix block's `params` `0` for that member with its id in
  `unlabelled`: the matrix was handed a policy already built and measures no capacity (`matrix.md` §5). The
  architecture's `width`/`depth` are copied from the rung configuration the job was handed; this module chooses neither.
- `cost` is a **measurement**: the hands the run played, the seconds per hand, their reciprocal and the wall clock, taken
  around the `matrix` call on the device that ran it — `cpu`, because a workflow-started run cannot reach the GPU
  (`strata/platform.md`, D-8). `measured: true` says these were observed; `per_hand_ceiling_seconds` is ASM-15's
  **bound**, carried beside them so the two are never confused.
- No entry point ever returns a measured cost. `league()` keeps carrying ASM-15's `0.04` bound and never a
  measurement (`declarations.md` §4.1); a run's own measured figures live in its run record's `timings`
  (`records.md` §12).

## 6. What changes when `training` ships lineages

When `training` produces snapshot lineages and `checkpoints/` holds them, the **same file** is regenerated with the
rung's frozen pool instead of §2's empty declaration, and exactly these fields change:

- `membership_kind` becomes `pool+variant`, `pool.members` gains the M = 5 version records with their ids and
  lineages (`records.md` §7), and `members` grows to `K = 9` or `K = 10` (`matrix.md` §1);
- `cell_count` becomes 36 or 45 and `hands_played` 54,000 or 67,500 at the `full` budget (§1), with
  `hands_per_cell` staying 1,500 — the budget never changes, only the membership does (`league.md` §5);
- the `matrix` and `rating` records grow with them: 36 or 45 cells and one rating entry per member, the three
  baselines' mean still 0 (`rating.md` §2);
- `cost` reports the new hand count and the new measured seconds per hand — the same keys, new numbers;
- `schema` **does not change**: the shape of the document is the same, so a reader written against version 1 keeps
  working when the membership grows.

Nothing else in the file moves, and no entry point learns about it: the growth is a content change in evidence, not a
surface change (D-8, D-12).

## 7. What the file is not

It is not a cache — nothing loads it, and a `matrix` call never consults it (`league.md` §5). It is not a claim
about the rung that produced its variant: it names one membership, at one cell size, on this game, and the rating
inside it is a statement about those four members and no others (D-16, `league.md` §8). It carries no curve, no
report and no timing the module did not measure.
