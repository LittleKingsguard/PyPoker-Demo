# evaluation — the two budgets and the shipped table

- **Owner:** the two table budgets and the one artefact that ships — the arithmetic (§1), what ships and which
  player each member is (§2), the file's name and **schema** (§3), how it is produced (§4), its provenance and cost
  blocks (§5), the regeneration over a rung's frozen pool (§6), and what it is not (§7) (`league.md` §5–§7, D-8)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `matrix.md` §1, §5–§6, `rating.md` §5, `declarations.md` §4.1, `guardrails.md` G19

## 1. The arithmetic

One membership, two cell sizes: `live` and `full` differ in `hands_per_cell` and nothing else (`league.md` §5, ASM-14).
A table plays `cell_count(K) × hands_per_cell` hands, so the whole budget is arithmetic on K:

| K | Membership | Cells = K(K−1)/2 | `live` (120/cell) | `full` (1,500/cell) |
|---|---|---|---|---|
| 4 | the three baselines + one variant — R1's membership, and the one this file names (§2) | 6 | 720 | 9,000 |
| 9 | a full window (3 baselines + M = 5 versions) + one variant | 36 | 4,320 | 54,000 |
| 10 | a full window + two variants (R4, R5, R6) | 45 | 5,400 | 67,500 |

The K = 9 and K = 10 columns are `league()`'s declared `hands_played`; the K = 4 column is R1's, whose pool is the three pinned
baselines alone (`declarations.md` §4.1, `docs/L1/league.md` §2, §4). The per-hand cost is **measured, not bounded**: ASM-21
ratifies 0.105–0.153 s/hand on CPU, wide because the oracle decides it (0.255–0.315 s/hand in an oracle-bearing cell vs 0.002–0.004
without, in half a table's hands), so K = 4 `live` is ≈95–110 s (720 hands: 110.29 s = 0.1532 s/hand in the evidence bundle, 107.4 s
= 0.1491 in run 3) and `full` ≈20 min (this file's own `cost.wall_clock_seconds` still 1,191.37 s), a full window ≈10–12 minutes
live and ≈2 hours full (≈2¼–2¾ hours at the slowest measured rate), no case asserts a wall clock (ASM-21, `docs/L1/league.md` §7).

## 2. What ships, and which player each member is

The members of a table are a frozen pool plus the rung's variants (`docs/L1/protocol.md` §5, `module-map.md` §7).
`training` is implemented and green: `training.checkpoints()` returns an 18-entry shipped index — R1, three seeds ×
five retained snapshots plus a final model each, under `checkpoints/R1/naive-numeric/seed-{0,1,2}/` — and
`checkpoints/evidence/r1-live.json` records the R1 live run (ASM-18, `protocol.md` §5). This file names **R1's**
membership, and R1's pool is the baselines alone, so it is K = 4 (D-16, `league.md` §2):

- the **three pinned baselines** — a frozen pool declared as `{"members": [], "m": 5, "frozen": True}`, which is R1's
  pool (`league.md` §2);
- **one variant member**, `variant-1`, built deterministically from its own recipe, which §5 records — a learner from
  `agents.build_learner` at the rung's declared backend, encoding and architecture, made a policy by
  `features.build_encoder` and `agents.as_policy` at the module constant `VARIANT_SEED = 31415` (`scheduler.md` §3,
  `matrix.md` §4). It is **not** `_member_seed`'s: that digest derives the three baselines' seeds and nothing else,
  and a variant handed to `matrix` is a policy already built (`matrix.md` §4). The call belongs to the **offline
  producer and to no entry point**: a rung's variants are `training`'s to hand `matrix`, and a producer standing where
  `training` stands builds its own at the recipe the artefact records (`docs/L2/evaluation/league.md` §7).

`variant-1` **names a slot, not a player** (`matrix.md` §1), and two tables spend it on two different learners. This
file's is the producer's **untrained** learner at seed 31415 — flat-numeric NumPy, width 96, depth 2, 38,499
parameters, never a hand played — while a live table's is the rung's **trained** final model: the shipped R1 evidence
records the trained seed-0 final at 10,119 parameters with `unlabelled: false`
(`checkpoints/evidence/r1-live.json`, ASM-18). The two rows measure **two different players and are never compared**,
not even as one member at two cell sizes. The untrained row's capacity is the producer's own `param_count`
measurement; the matrix block's `params: 0` with that id in `unlabelled` means only that `matrix` was handed a policy
already built (`matrix.md` §5) — a statement about provenance, never about training — and §5's
`provenance.member_status` names which of the two every row is.

`K = 4`, `6` cells, `9,000` hands at the `full` budget: four real members at one hand count, whose provenance says
which membership it is and which player each member is. It **never** names a version it could not load — no id, path
or lineage refers to a checkpoint not on disk (`protocol.md` §5) — and a table whose only model member is untrained is
weak evidence, declared as such and never dressed up as trained: it is **not** `training`'s shipped pool (§6).

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
| `provenance` | §5's first block: what produced it, from what membership, by which recipe, and which player each member is |
| `cost` | §5's second block: the measured cost of that run |

`pool`, `matrix` and `rating` are the three records unchanged — the file adds no member, no cell and no value, so a
reader can compare the file's matrix against its own `matrix` call record for record (`league.md` §5). Every key of
those three is a `str`, so JSON carries them unrenamed: the file is a faithful dump, not a translation. `provenance`
is the producer's own block and the one home of membership-level facts — `member_status`, aligned with `members`.

## 4. How it is produced

The file is written by `src/evaluation/tables.py`, and **no entry point reads or writes it**: D-12 forbids a twelfth
surface and `league.md` §5 makes the file evidence. The producer is that module's `__main__`, so the recipe is one
command and not a notebook that knows the schema:

    PYTHONPATH=src .venv/bin/python -m evaluation.tables        # writes tables/league-full.json

It calls `build_pool` with §2's declaration, `matrix(pool, [variant], "full")` and `rating(matrix)`, then
`_build_document` / `_member_status` / `_cost_block` / `_write_document` — the private functions holding §3's and §5's
schema, whose target is `SHIPPED_PATH = "tables/league-full.json"`, so the file's path and shape have one home
(`README.md` §4). It times the `matrix` call with `time.perf_counter` and counts the hands it played, which is what
§5's cost block records, and it is run offline, once, with the result committed (`league.md` §5, D-8). **Unverified**:
no unit case drives the producer — that needs a real 9,000-hand table and a write under `tables/` — so `EVL-6.*`
checks the file this design ships and §5's schema, never the command (`guardrails.md` G19).

## 5. The provenance and cost blocks

    "provenance": {
      "module": "evaluation", "entry_points": ["build_pool", "matrix", "rating"],
      "schema": "pypoker-evaluation-league-table/1", "table_seed": 20261105, "budget": "full",
      "hands_per_cell": 1500, "cell_count": 6, "hands_played": 9000,
      "membership_kind": "baselines+variant",
      "members": ["random", "always-call", "oracle", "variant-1"],
      "member_status": [{"id": "random", "status": "baseline"}, {"id": "always-call", "status": "baseline"},
                        {"id": "oracle", "status": "baseline"}, {"id": "variant-1", "status": "untrained", "seed": 31415}],
      "variants": [{"id": "variant-1", "status": "untrained", "backend": "numpy", "encoding": "flat-numeric",
                    "architecture": {"kind": "naive-stack", "width": 96, "depth": 2}, "seed": 31415, "params": <agents.param_count>}],
      "pool": {"id": "<the pool record's id>", "m": 5, "frozen": true}
    }

    "cost": {"hands": 9000, "seconds_per_hand": <float>, "hands_per_second": <float>,
             "wall_clock_seconds": <float>, "device": "cpu", "measured": true}

- `member_status` is §2's distinction made machine-readable: one entry per id of `members`, in `members` order. A
  variant's entry is its recipe's `status` — `untrained` here — with its build seed; a pool version is a `checkpoint`;
  a pinned baseline is a `baseline` (D-16, ASM-18, §6).
- `variants` is the **recipe** a third party needs to rebuild the same membership: the backend, the encoding name,
  the architecture and its settings, the seed the policy was built at — the module's own `VARIANT_SEED`, never a
  table-derived one — the `status` of the learner it builds, and the measured `param_count`, so the file names a
  member whose capacity is a measurement and not a claim (ASM-10, `records.md` §2). It is one `agents.build_learner`
  built in the offline job, a call no entry point makes (`league.md` §7), so the matrix block's `params: 0` for that
  id in `unlabelled` is no contradiction (`matrix.md` §5).
- `cost` is a **measurement**: the hands played, the seconds per hand, their reciprocal and the wall clock, taken
  around the `matrix` call on the device that ran it — `cpu`, because a workflow-started run cannot reach the GPU
  (`strata/platform.md`, D-8). `measured: true` says these were observed, and it carries **no ceiling**: ASM-21
  ratifies the measurement and supersedes ASM-15's bound, so a `per_hand_ceiling_seconds` here would have no source,
  and `league()` carries no per-hand figure either (`declarations.md` §4.1, ASM-21).

## 6. What changes when the file is regenerated over a rung's frozen pool

`training` has shipped its lineages, so the recipe for a `pool+variant` file exists; the file does not — this one is
R1's, and R1 has no window to put in it (§1–§2). Regenerated over a rung whose pool retains R1's snapshots — R2's, by
construction — the **same file** changes exactly these fields:

- `membership_kind` becomes `pool+variant`, `pool.members` gains the M = 5 version records with their ids and
  lineages (`records.md` §7), and `members` grows to `K = 9` or `K = 10` (`matrix.md` §1);
- `member_status` gains a `checkpoint` row per version member, and the variant's row becomes `trained` with the seed
  its checkpoint records, because a matrix over `policy_from` policies was handed trained members (§5);
- `cell_count` becomes 36 or 45 and `hands_played` 54,000 or 67,500 at the `full` budget (§1), `hands_per_cell`
  staying 1,500 — the budget never changes, only the membership does (`league.md` §5);
- the `matrix` and `rating` records grow with them — a rating entry per member — and `cost` reports the new hand count and measured
  seconds per hand, the same keys and new numbers: ASM-21's 0.105–0.153 s/hand is a band because the oracle decides it, so the full
  window is ≈10–12 minutes live, ≈2 hours full (≈2¼–2¾ hours at the slowest measured rate) (`rating.md` §2, `docs/L1/league.md` §7);
- `schema` **does not change**: the shape of the document is the same, so a reader written against version 1 keeps
  working when the membership grows. Nothing else moves and no entry point learns about it (D-8, D-12).

## 7. What the file is not

It is not a cache — nothing loads it, and a `matrix` call never consults it (`league.md` §5) — and it claims nothing
beyond one membership at one cell size, with no curve, no report and no timing it did not measure (D-16, `league.md` §8, ASM-21).
