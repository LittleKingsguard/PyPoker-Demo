# evaluation — module design (L3)

- **Layer:** L3 · **Module:** `evaluation` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-05 · **Rev 2:** a recorded
  encoding name is checked by `build_encoder`, never by the catalogue (§5); a membership names its members once (§7, §8)
- **Realises:** `docs/L2/evaluation/surface.md` (the eleven entry points: arguments, records, refusals, determinism) and
  `docs/L2/evaluation/league.md` (the pool, the scheduler, the matrix, the rating, the two tables, the seven evidence
  families, the edge's contracts)
- **Reads:** `docs/L1/e2e-surface.md` §1, §2, §3.4, §5, `records.md` §1, §7–§13, `league.md` §1–§8,
  `protocol.md` §1–§6, `ladder.md` §2, §3, §6, `module-map.md` §2, §3, §5, `assumptions.md` (ASM-2, ASM-4,
  ASM-10, ASM-14–ASM-19), `battery.md` §2–§5, `strata/decisions.md` (D-1, D-8, D-12, D-13, D-16),
  `strata/platform.md`; at the consumed edge `docs/L2/agents/surface.md` §1, §5, §9–§12, `learner.md` §4–§5,
  §8, `docs/L2/features/surface.md` §3–§9, `docs/L2/engine/surface.md` §1, §4, §9, §10
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append
- **Implements:** `src/evaluation/` and the one shipped artefact `tables/league-full.json` (written by L4, never by L3).
  `tests/evaluation/` is this design's unit battery and `tests/integration/evaluation/` its join battery; the L1 battery's
  share is `test_fam06_pool.py`–`test_fam11_report.py`, `test_fam01_surface.py` (FAM-1.27–1.37) and `test_fam16_blind.py`

## 1. What this module is

`evaluation` **is** the league (D-16): a bounded rolling pool of the model's last M = 5 versions plus the three
pinned baselines, the scheduler that plays one cell at a time, the pairwise matrix of a membership, the
Bradley-Terry rating fitted over it with hand-level bootstrap intervals, the two table budgets (`live`, `full`)
and the complete per-rung report. The same pool is the training opposition and the evaluation opposition
(`module-map.md` §6, ASM-19). It measures: it never trains, never edits a curve, never chooses a pool's membership.

## 2. The documents, one per owner

| Document | Owns | What it fixes |
|---|---|---|
| `declarations.md` | `protocol()`, `league()` | the two declarations key by key and in order; the seven families with their refusal words; the nine header items; `cell_count`; the table seed; the two budget rows |
| `pool.md` | `build_pool`, `pool_members`, `offer`, `opponent` | the `Pool` value, the **lineage order** (§3), windowing to `m`, the **id digest** (§4), the read-back (§5), `offer`'s eviction (§6), the draw (§7) |
| `scheduler.md` | `match`, `policy_from` | seat alternation, the **per-hand seeds** (§3), win/tie/loss from net chips, the seat split, zero-sum, how a side becomes a policy and the **two facts a checkpoint records** (§5–§5.1), refusals |
| `matrix.md` | `matrix` | membership order, the **pair enumeration**, the **per-cell and per-member seeds** (§3), how each member's policy is built (§4), the record (§5), the budgets (§6) |
| `rating.md` | `rating` | the **Bradley-Terry solver**, its tolerance and **bound** (§2–§3), the anchor, the **bootstrap** (§4), the record (§5) |
| `tables.md` | the two budgets and the artefact | the budget arithmetic (§1), `tables/league-full.json`'s name and **schema** (§3), its provenance and cost block (§5) |
| `report.md` | `report` | the seven families and their order, the report record, the refusal grammar, the membership rule, what a report never does |
| `errors.md` | refusals | the class hierarchy, the message grammar, and the canonical message per refusal |
| `guardrails.md` | L4 | one numbered note per risk this design identified, in the order they bite, each naming its test |

## 3. The eleven names

`src/evaluation/__init__.py` exports exactly the eleven entry points of `e2e-surface.md` §3.4, in that order,
declares them in `__all__`, and adds, removes and renames none (D-12):

    protocol()                                -> Mapping     # the evidence contract
    league()                                  -> Mapping     # the league's parameters; carries cell_count
    build_pool(declaration)                   -> Pool        # opaque
    pool_members(pool)                        -> Mapping     # records.md §8's pool record
    offer(pool, version)                      -> Pool        # a new pool; the argument is unchanged
    opponent(pool, seed)                      -> callable    # a policy, for one training hand
    match(left, right, hands, seed)           -> Mapping     # one records.md §9 cell
    matrix(pool, variants, table)             -> Mapping     # records.md §10's matrix
    rating(matrix)                            -> Mapping     # records.md §11's rating
    policy_from(path)                         -> callable    # a policy, evaluation mode
    report(rung_name, record, matrix, rating) -> Mapping     # the per-rung report

`Pool`, `_MemberPolicy`, `EvaluationError` and its thirty-three subclasses, `seeds.py`'s five derivations and every
helper below an entry point are **not** surface (`e2e-surface.md` §1, `surface.md` §1). A pool and a policy are opaque;
a policy this module builds carries its member's id and parameter count, and no record returned here exposes either.

## 4. The layout of `src/evaluation/`

    __init__.py      the eleven entry points, `__all__`, and nothing else (§3)
    errors.py        EvaluationError and its subclasses (errors.md §2)
    declarations.py  M, BASELINES, TABLE_SEED, TABLES, FAMILIES, HEADER_ITEMS, RATING, protocol(), league(), cell_count()
    seeds.py         _seed, _hand_seed, _cell_seed, _member_seed, _bootstrap_seed, _draw_index
    pool.py          Pool, build_pool, pool_members, offer, _lineage_order, _pool_id (pool.md)
    policy.py        _MemberPolicy, _member_policy, _checkpoint_policy, _checkpoint_facts, _built_encoder, policy_from,
                     opponent, _side (§3, scheduler.md §5–§5.1)
    scheduler.py     _play_cell, match (scheduler.md)
    matrix.py        matrix, _membership, _pairs (matrix.md)
    rating.py        BOUND, TOLERANCE, MAX_ITERATIONS, RESAMPLES, _fit, _resample, rating (rating.md)
    report.py        report, _families_present, _membership_ok, _header_ok (report.md)
    tables.py        SHIPPED_PATH, VARIANT_SEED, _build_document, _cost_block, _write_document, and `__main__` (tables.md)

Eleven files, one concern each; a twelfth needs a document here saying what it owns. The private names above are contract for `tests/evaluation/`, which imports them; their bodies stay L4's.

## 5. The import boundary, and the one stream this module never touches

`evaluation` imports `numpy`, the standard library (`hashlib`, `json`, `numbers`, `os`, `time`, `zipfile`, `collections.abc`,
`typing`) and only the granted calls: `agents.baselines`, `build_baseline`, `as_policy`, `load`, `param_count`;
`features.build_encoder`, `encode`; `engine.play_hand` (`module-map.md` §2). Never `pokerkit`, `torch`, `training`, `harness`
or a `tests/` helper; never `agents.act` or `learn`; never `features.encodings()`, the catalogue this module is not granted —
a recorded encoding name is checked by **building** it (`scheduler.md` §5.1). One carve-out: `tables.py`'s offline
`__main__` also calls `agents.build_learner` for the artefact's variant (`league.md` §7, `tables.md` §2) — that call
belongs to the offline producer and to no entry point, and no talk makes it. `numpy` serves one thing, the bootstrap's
generator (rating.md §4); the global `random` stream is never seeded or drawn from here (ASM-2).

## 6. Facts inherited from `engine`, `features` and `agents`, and not re-derived

- `engine.play_hand(seed, seat0, seat1)` deals at that seed, drives the hand out and returns `records.md` §5's episode record, whose `payoffs` sum to zero; seat 0 holds the button and posts the small blind (`engine/surface.md` §4, §10), so a cell alternates seats by swapping the two policies it hands over.
- A policy is `callable(readout, legal_actions)` returning one descriptor of `legal_actions`; an illegal descriptor is `engine`'s refusal and is never caught or repaired here (D-2, `e2e-surface.md` §2).
- `agents.baselines()` names `random`, `always-call`, `oracle`, each with `params` `0`; `agents.build_baseline(name, seed)` returns a policy that never learns and whose state advances nowhere (`agents/surface.md` §11–§12, `learner.md` §5). A baseline's id is its name.
- `agents.load(None, path)` restores a member from its path alone; `agents.param_count(learner)` is its capacity; `agents.as_policy(learner, encoder, seed)` returns the snapshot policy a cell plays, and at the learner's own seed it decides as `act` does (`agents/surface.md` §9–§10, ASM-5).
- `features.build_encoder(name)` takes `flat-numeric` then `card-tokens`, and `agents.as_policy` refuses an encoder whose kind or size contradicts the learner's (`features/surface.md` §3–§5): the recorded name is the encoder built for it, and a name it refuses is `UnknownEncoding` (`scheduler.md` §5.1).

## 7. The decisions this design fixed, each with the alternative it rejected (D-1)

| # | Decision | Why | Rejected alternative |
|---|---|---|---|
| 1 | pool id = `"pool-" + sha256("\n".join(ordered ids)).hexdigest()[:16]` (pool.md §4) | it must change when and only when the ordered membership does (`records.md` §8) | digesting whole member records, which would rename a pool when a seed or step was corrected |
| 2 | per-hand seed = `sha256` of a fixed `(cell seed, index)` payload (scheduler.md §3) | a cell is reproduced from its seed alone and nothing draws on the global stream | `seed + i`, which correlates consecutive hands and collides across cells |
| 3 | per-member seed: `_member_seed(table seed, position)`, for **the three baselines only**; a version is built at the seed its checkpoint records, read with its encoding name from the container (matrix.md §3–§4, scheduler.md §5.1) | a table's baselines are that table's, and one checkpoint is one player | a table-derived or path-derived version seed, which would make one checkpoint two players and fail FAM-12.3, FAM-16.26 |
| 4 | lineage order: link by `lineage == id`, chains ordered by their start's declaration position (pool.md §3) | the declaration's own data orders the window, and one chain is the common case | ordering by the start's `step`, which would need a key the surface does not refuse for |
| 5 | Bradley-Terry by Hunter's MM iteration, tolerance `1e-10`, cap 10,000, bound `±10` (rating.md §2–§3) | closed-form updates need no learning rate and no gradient tuning | Newton/IRLS, which inverts a matrix per iteration for the same answer |
| 6 | bootstrap: 200 per-cell multinomial resamples, seeded from the table seed, 2.5/97.5 percentiles widened to hold the value (rating.md §4) | the hand is the unit of evidence and a cell's counts are its hand outcomes | resampling cells, which resamples the membership instead of the measurement |
| 7 | eleven files, one concern each (§4); the artefact at `tables/league-full.json` (tables.md §3) | one home per rule; the file is evidence and no entry point reads it | a twelfth entry point for the file, which D-12 forbids |
| 8 | 34 error classes under `EvaluationError` — one base and thirty-three subclasses, one per refusal family (errors.md §2) | a caller catches this module's refusals, never a `KeyError` from a bug | one class with a message, which no caller can route on |

## 8. Decisions a later module must not re-derive

1. **A member is named by id, never by rank** (`protocol.md` §1, `records.md` §7); a baseline's id is its name.
2. **The pool's id is a function of the ordered member ids and nothing else** (pool.md §4).
3. **Every seed this module derives is a derivation, never a draw**, and a member's policy seed is the one its own checkpoint records; no stream is seeded or read here (§5, scheduler.md §5.1).
4. **One cell at a time, seats alternating, both directions from one set of hands** (scheduler.md §2).
5. **A table's membership is the pool's members, then `variant-1`, `variant-2`** (matrix.md §1).
6. **The anchor is re-applied every iteration**, so the three baselines' mean is exactly 0 — except on `rating.md` §3's one pinned-baseline table, where the pin is taken last and so displaces the mean it was applied after (rating.md §3).
7. **The bound sizes a table; a measured cost is recorded only where it was measured** (tables.md §5).
8. **Nothing here reduces a matrix to a ranking, and no rating is a claim of poker skill** (`league.md` §4, D-16).
9. **A membership names its members once**: a version may not take one of the three baselines' names, and a table refuses a membership that is not distinct (pool.md §2, matrix.md §7).
