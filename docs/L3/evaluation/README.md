# evaluation — module design (L3)

- **Layer:** L3 · **Module:** `evaluation` · **Unit:** phase1 · **Rev:** 6 · **Date:** 2026-11-09 · **Rev 4:** D-20's utility beside
  D-19's rule — a member declares `utility`, a family holds one rule **and one utility**, the id digests both, and six records name
  the utility (`utility.md` §2–§4) · **Rev 5:** D-21's catalogue — `BASELINES` is its `anchor: True` set and `CATALOGUE` its six
  names, a declaration's `baselines` admits a folder after the three, `UnknownBaseline` refuses an uncatalogued one, and `league()`
  gains `catalogue` (`declarations.md` §2–§4, `pool.md` §2, `errors.md` §2) · **Rev 6:** D-29's second shape — `SHAPE_NAMES`,
  `DEFAULT_SHAPE` and `EXPLORATION_MODES` are restated at this edge (`shape.md` §1), a pool, a member, a cell, a matrix, a rating, a
  policy and a report each name **one** shape, `policy_from` gains the mode `off`, and the pool id does **not** digest the shape
  (`shape.md` §2–§5, `families.md` §4)
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append
- **Realises:** `docs/L2/evaluation/surface.md` (the eleven entry points; the shape, the policy and the member at this edge) and
  `docs/L2/evaluation/league.md` (the pool, scheduler, matrix, rating, the two tables, the seven families, the edge's contracts),
  with the rule at `docs/L2/evaluation/rules.md` and the four pool entry points at `docs/L2/evaluation/pool.md`
- **Reads:** `docs/L1/e2e-surface.md` §1, §2, §3.4, §5, `records.md` §1, §7–§13, `league.md` §1–§8, `protocol.md` §1–§6, `ladder.md`
  §2, §3, §6, `module-map.md` §2, §3, §5, `shapes.md` §2–§6, `sizing.md` §4–§6, `assumptions.md` (ASM-2, ASM-4, ASM-10, ASM-14–ASM-19,
  ASM-21, ASM-26, ASM-27), `battery.md` §2–§5; at the consumed edge `docs/L2/agents/surface.md` §1, §5, §9–§12, `learner.md` §4–§5,
  §8, `docs/L2/features/surface.md` §3–§9 and `docs/L2/evaluation/rules.md` §2–§6
- **Implements:** `src/evaluation/` and `tables/league-full.json` (written by L4, never by L3). `tests/evaluation/` is this design's
  unit battery, `tests/integration/evaluation/` its join battery, and the L1 battery's share is `test_fam06_pool.py`–
  `test_fam11_report.py`, `test_fam01_surface.py` (FAM-1.27–1.37) and `test_fam16_blind.py`

## 1. What this module is

`evaluation` **is** the league (D-16): a bounded rolling pool of the model's last M = 5 versions plus the pinned baselines — the catalogue's flagged three and any folder a declaration names — the scheduler that plays one cell at a time, the pairwise matrix of a membership, the Bradley-Terry rating fitted over it with hand-level bootstrap intervals, the two table budgets (`live`, `full`) and the complete per-rung report. The same pool is the training opposition and the evaluation opposition (`module-map.md` §6, ASM-19, ASM-32), and every object it hands back — a pool, a cell, a table, a rating, a policy, a report — is **one shape's**, declared or read as the default (`shape.md` §2, §4, D-29). It measures: it never trains, never edits a curve, never chooses a pool's membership.

## 2. The documents, one per owner

| Document | Owns | What it fixes |
|---|---|---|
| `declarations.md` | `protocol()`, `league()` | the two declarations key by key and in order — `league()`'s seven keys with `catalogue` among them; the seven families with their refusal words; the nine header items a **record** states, plus the `shape` key a **report** writes onto its own copy; `cell_count`; the table seed; the two budget rows (declarations.md §2.2, §4) |
| `shape.md` | the game **shape** at this edge | the catalogue restated in `declarations.py` and the join battery that holds it (§1), absence as the default and never a defaulting of a name (§2), the three refusals (§3), which record carries a shape and which must not (§4), the two exploration modes (§5) |
| `pool.md` | `build_pool`, `pool_members`, `offer`, `opponent` | the `Pool` value and its shape (§1), the declaration with its `game` key, the member's `game` and the baseline probe (§2), the read-back with `game`, `rules` and `utilities` (§5), `offer`'s shape refusal (§6), the draw (§7), the pool's refusals (§8), what is free (§9); §3, §4 and §6 keep a redirect |
| `families.md` | the version window's **families** | the grouping and the **ordered window** (§1–§2), the **fair-share eviction** and the (m+1)th-family refusal (§3), the **id digest** that certifies each version's rule and utility and **not** its shape (§4), `offer`'s rolling (§5), the refusals it adds (§6) |
| `utility.md` | the utility a member was trained under | the catalogue through the granted arrow (§1), a **required** `utility` refused by name where a version declaration names none — the default speaking only for a variant entry and a learner spec (§2), the records that name one (§3), the three disagreements and their refusals (§4), what is free (§5) |
| `scheduler.md` | `match`, `policy_from` | the cell's one shape (§1), seat alternation, the **per-hand seeds** (§3), win/tie/loss from net chips, the seat split, zero-sum, how a side becomes a policy, the shape a side names and the **seven-element side tuple** (§5), the **three facts a checkpoint records** (§5.1), refusals |
| `matrix.md` | `matrix` | membership order and the table's shape being the pool's (§1), the **pair enumeration**, the **per-cell and per-member seeds** (§3), how each member's policy is built (§4), the record with its required `game` (§5), the budgets (§6) |
| `rating.md` | `rating` | what is fitted: **one shape's** cells (§1), the **Bradley-Terry solver**, its tolerance and **bound** (§2–§3), the anchor, the **bootstrap** (§4), the record with its `game` (§5), the shape refusals (§6) |
| `tables.md` | the two budgets and the artefact | the budget arithmetic (§1), `tables/league-full.json`'s name and **schema** (§3), its provenance and cost block (§5) |
| `report.md` | `report` | the seven families and their order, the report record and its header's tenth key (§2), the refusal grammar and the three-way shape refusal's place in it (§3), the membership rule, what a report never does |
| `errors.md` | refusals | the class hierarchy, the message grammar, and the canonical message per refusal, the three shape classes included |
| `guardrails.md` | L4 | one numbered note per risk this design identified, in the order they bite, each naming its test |

## 3. The eleven names

`src/evaluation/__init__.py` exports exactly the eleven entry points of `e2e-surface.md` §3.4, in that order, declares them in `__all__`, and adds, removes and renames none (D-12):

    protocol()                                -> Mapping     # the evidence contract
    league()                                  -> Mapping     # the league's parameters; carries cell_count
    build_pool(declaration)                   -> Pool        # opaque; carries the one shape it is on
    pool_members(pool)                        -> Mapping     # records.md §8's pool record, `game` included
    offer(pool, version)                      -> Pool        # a new pool; the argument is unchanged
    opponent(pool, seed)                      -> callable    # a policy, for one training hand
    match(left, right, hands, seed)           -> Mapping     # one records.md §9 cell, with its `game`; no shape argument
    matrix(pool, variants, table)             -> Mapping     # records.md §10's matrix, its `game` required
    rating(matrix)                            -> Mapping     # records.md §11's rating, one shape's, with its `game`
    policy_from(path, exploration="schedule") -> callable    # a policy, evaluation mode; `off` is the greedy one
    report(rung_name, record, matrix, rating) -> Mapping     # the per-rung report; the header names the shape

`Pool`, `_MemberPolicy`, `EvaluationError` and its forty-two subclasses, `seeds.py`'s five derivations, `declarations.py`'s constants and every helper below an entry point are **not** surface (`e2e-surface.md` §1, `surface.md` §1). A pool and a policy are opaque; a policy this module builds carries its member's id, its parameter count, its rule, its utility and its shape, and no record returned here exposes the object itself (`shape.md` §4).

## 4. The layout of `src/evaluation/`

    __init__.py      the eleven entry points, `__all__`, and nothing else (§3)
    errors.py        EvaluationError and its subclasses (errors.md §2)
    declarations.py  M, BASELINES, CATALOGUE, SHAPE_NAMES, DEFAULT_SHAPE, EXPLORATION_MODES, EXPLORATION_DEFAULT, PROBE_SEED, TABLE_SEED, TABLES, FAMILIES, HEADER_ITEMS, RATING, protocol(), league(), cell_count() (shape.md §1)
    seeds.py         _seed, _hand_seed, _cell_seed, _member_seed, _bootstrap_seed, _draw_index
    pool.py          Pool, build_pool, pool_members, offer, _shape, _member_game, _probe_baseline, _families, _window_families, _evict, _window, _pool_id, _rule, _utility, _catalogue, _utility_catalogue, _declared_baselines, _pinned, _baseline_member, _pool_rules, _pool_utilities (pool.md, families.md, utility.md, shape.md)
    policy.py        _MemberPolicy (its `game` slot), _member_policy, _checkpoint_policy, _checkpoint_facts, _built_encoder, policy_from, opponent, _side (§3, scheduler.md §5–§5.1)
    scheduler.py     _play_cell, match (scheduler.md)
    matrix.py        matrix, _membership, _variant_shape, _pairs (matrix.md)
    rating.py        BOUND, TOLERANCE, MAX_ITERATIONS, RESAMPLES, _fit, _resample, rating (rating.md)
    report.py        report, _families_present, _membership_ok, _header_ok, _resolved_shape, _header_with_shape (report.md)
    tables.py        SHIPPED_PATH, VARIANT_SEED, _build_document, _member_status, _cost_block, _write_document, `__main__`

Eleven files, one concern each; a twelfth needs a document here saying what it owns. The private names above are contract for `tests/evaluation/`, which imports them; their bodies stay L4's.

## 5. The import boundary, and the one stream this module never touches

`evaluation` imports `numpy`, the standard library (`hashlib`, `json`, `numbers`, `os`, `time`, `zipfile`, `collections.abc`) and only the granted calls: `agents.baselines`, `build_baseline`, `as_policy`, `load`, `param_count`; `features.build_encoder` (with its shape as a keyword) and `encode`; and `engine.play_hand` (`module-map.md` §2). Never `pokerkit`, `torch`, `training`, `harness` or a `tests/` helper; never `agents.act` or `learn`; never `features.encodings()`, and **never `engine.game_shapes` or `engine.game_config`** — which is why the catalogue is restated (`shape.md` §1). A recorded encoding name is checked by **building** it for the recorded shape (`scheduler.md` §5.1). One carve-out: `tables.py`'s offline `__main__` also calls `agents.build_learner` for the artefact's variant (`league.md` §7, `tables.md` §2) — a call of the offline producer and of no entry point. `numpy` serves one thing, the bootstrap's generator (rating.md §4); the global `random` stream is never seeded or drawn from here (ASM-2).

## 6. Facts inherited from `engine`, `features` and `agents`, and not re-derived

- `engine.play_hand(seed, seat0, seat1, shape=None)` deals at that seed **and on that shape** — an absent shape is the default — drives the hand out and returns `records.md` §5's episode record, whose `payoffs` sum to zero; seat 0 holds the button and posts the small blind (`engine/surface.md` §4, §10), so a cell alternates seats by swapping the two policies it hands over. A cell hands over **its own** shape as that argument: its hands are dealt on the one shape its two sides name, never on a default its member's vocabulary does not fit (`scheduler.md` §1).
- A policy is `callable(readout, legal_actions)` returning one descriptor of `legal_actions`; an illegal descriptor is `engine`'s refusal and is never caught or repaired here (D-2, `e2e-surface.md` §2).
- `agents.baselines()` names the catalogue's **six** — `random`, `always-call`, `oracle`, `fold-no-pair-or-face`, `fold-no-pair-or-better`, `fold-large-bet` — each with `name`, `rule`, `params` `0` and an `anchor` flag true for the first three and false for the folders, and **no shape**: `agents.build_baseline(name, seed)` takes a name and a seed and no shape, so a baseline policy is **shape-silent** and every one of the six plays both declared shapes (`agents/surface.md` §11–§12, `learner.md` §5, `shape.md` §4, D-21).
- `agents.load(None, path)` restores a member from its path alone, and the restored learner's `.game` is its container's shape — the default shape where the container records none; a version-4 container carries `game` while the default shape still writes version 3 with no field, which is what keeps the 18 shipped version-1 containers loadable (`sizing.md` §6, `docs/L1/shapes.md` §3, §5). `agents.param_count` is that learner's capacity, which the shape's head width sets.
- `agents.as_policy(learner, encoder, seed, exploration="schedule")` accepts `exploration` in `("schedule", "off")` and refuses anything else **naming both modes**; at the learner's own seed it decides as `act` does and the policy it returns carries `learning_rule`, `utility` and `game` (`agents/surface.md` §9–§10, `sizing.md` §4, ASM-5, D-29). `agents.build_learner(spec)` takes an optional `game`.
- `features.build_encoder(name, shape=None)` takes the shape as a **keyword**, and `agents.as_policy` refuses an encoder whose kind or size contradicts the learner's (`features/surface.md` §3–§5): the recorded name is the encoder built for it **and for the recorded shape**, and a name it refuses is `UnknownEncoding` (`scheduler.md` §5.1).

## 7. The decisions this design fixed, each with the alternative it rejected (D-1)

| # | Decision | Why | Rejected alternative |
|---|---|---|---|
| 1 | pool id = `"pool-" + sha256("\n".join(one line per member)).hexdigest()[:16]`, a version's line carrying its `id`, `"\x1f"`, its `rule`, `"\x1f"` and its `utility` (families.md §4) | it must change when and only when the ordered membership does — a version's rule and utility included (`records.md` §8, ASM-27) | digesting ids alone, where one member's rule could contradict its neighbour's under one id |
| 2 | per-hand seed = `sha256` of a fixed `(cell seed, index)` payload (scheduler.md §3) | a cell is reproduced from its seed alone and nothing draws on the global stream | `seed + i`, which correlates consecutive hands and collides across cells |
| 3 | per-member seed: `_member_seed(table seed, position)`, for **the three baselines only**; a version is built at the seed its checkpoint records, read with its encoding name and its shape from the container (matrix.md §3–§4, scheduler.md §5.1) | a table's baselines are that table's, and one checkpoint is one player | a table-derived or path-derived version seed, which would make one checkpoint two players and fail FAM-12.3, FAM-16.26 |
| 4 | **families**: one lineage chain each, all its members under one rule **and one utility**, the chains ordered by each start's declaration position and the window evicting fair-share (families.md §1–§3) | the declaration's own data orders a heterogeneous window, and one rule per chain is what the pool must not lose (ASM-26) | ordering by the start's `step`, a key the surface does not refuse for |
| 5 | Bradley-Terry by Hunter's MM iteration, tolerance `1e-10`, cap 10,000, bound `±10` (rating.md §2–§3) | closed-form updates need no learning rate and no gradient tuning | Newton/IRLS, which inverts a matrix per iteration for the same answer |
| 6 | bootstrap: 200 per-cell multinomial resamples, seeded from the table seed, 2.5/97.5 percentiles widened to hold the value (rating.md §4) | the hand is the unit of evidence and a cell's counts are its hand outcomes | resampling cells, which resamples the membership instead of the measurement |
| 7 | eleven files, one concern each (§4); the artefact at `tables/league-full.json` (tables.md §3) | one home per rule; the file is evidence and no entry point reads it | a twelfth entry point for the file, which D-12 forbids |
| 8 | **43** error classes under `EvaluationError` — one base and forty-two subclasses, one per refusal family (errors.md §2) | a caller catches this module's refusals, never a `KeyError` from a bug | one class with a message, which no caller can route on |
| 9 | the **utility** is a catalogue member, held as the rule is: read through the granted arrow, refused by name where a version declaration names none — the default speaking only for a variant entry and a learner spec — and refused by name when uncatalogued (utility.md §1–§2) | D-20 makes the reward an axis, and a pool must be able to certify which objective each member was trained on (`records.md` §7, §8) | a scalar rescaling of the net chip delta, which changes no preference among equal-EV actions (D-20) |
| 10 | the shape is a **required field of every record that measures one** and **never a field of the pool's id**; two pools of one membership on two shapes share one id and are never one table (shape.md §4, families.md §4) | ASM-27 makes the id change when and only when the membership does, and a shape in the digest would rename every pool in the tree (`records.md` §8) | digesting the shape, which certifies it at the cost of renaming a baselines-only pool that has not changed |
| 11 | the catalogue is **restated** in `declarations.py` and held equal to `engine.game_shapes()` by the join battery (shape.md §1) | this module holds no arrow to the catalogue, so a restatement plus a join case is the only shape it can name without a twelfth entry point (`module-map.md` §2, D-12, D-13) | calling `engine.game_shapes()` through a widened arrow, which is L1's to grant; or inferring the shape from a policy, which makes one record depend on another |
| 12 | `off` is `policy_from`'s optional second argument — the masked maximum and the tie-break alone, **no generator drawn** (shape.md §5, scheduler.md §7) | the census `docs/L1/sizing.md` §7 requires reads a greedy policy, and 5 % forced draws from a six-descriptor mask would contaminate exactly the classes it counts (`docs/L1/sizing.md` §4) | reading the schedule's ε = 0.05 tail as "nearly greedy", which is not a greedy policy at all |
| 13 | each pinned baseline is **probed** once with `agents.build_baseline(name, PROBE_SEED)` — a construction only, whose firing set is empty under today's catalogue (pool.md §2) | a baseline the catalogue cannot construct must be refused by name rather than silently held unplayable, and a probe that played a hand would seed the global stream and break `build_pool`'s "plays nothing, moves no stream" (ASM-2) | probing by playing a hand at the pool's shape, which seeds the stream and is the only other way to learn whether a baseline can play it |

## 8. Decisions a later module must not re-derive

1. **A member is named by id, never by rank** (`protocol.md` §1, `records.md` §7); a baseline's id is its name.
2. **The pool's id is a function of the ordered member lines — a baseline's `id`, a version's `id`, `rule` and `utility` — and nothing else** (families.md §4, ASM-27); **the shape is not in it** (shape.md §4).
3. **Every seed this module derives is a derivation, never a draw**, and a member's policy seed is the one its own checkpoint records; no stream is seeded or read here (§5, scheduler.md §5.1), and **no shape moves a seed** (scheduler.md §3).
4. **One cell at a time, seats alternating, both directions from one set of hands** (scheduler.md §2) — and **one cell is played on one shape**: the one its two sides name, the default when neither does, and every hand of it is **dealt** on that shape (scheduler.md §1, §5).
5. **A table's membership is the pool's members, then `variant-1`, `variant-2`** (matrix.md §1), and **a table's shape is the pool's**, never an argument (matrix.md §1).
6. **The anchor is re-applied every iteration**, so the flagged three's mean is exactly 0 — never a folder D-21 adds — except on `rating.md` §3's one pinned-baseline table, where the pin is taken last and so displaces the mean it was applied after (rating.md §3, ASM-32); **a rating is one shape's** (rating.md §1, `docs/L1/shapes.md` §6).
7. **The budget is arithmetic on K, and a measured cost is recorded only where it was measured** (tables.md §1, §5, ASM-21); **nothing here reduces a matrix to a ranking, and no rating is a claim of poker skill** (`league.md` §4, D-16).
8. **A membership names its members once**: a version may not take one of the pool's pinned baseline names, and a table refuses a membership that is not distinct (pool.md §2, matrix.md §7, ASM-32).
9. **An absent `game` is the default shape, and a name the catalogue does not carry is refused by name** — two contracts, and nothing here defaulted a name (shape.md §2).
10. **A report writes the shape onto the header's own copy and requires no shape item of a record** (report.md §1–§4): `HEADER_ITEMS` keeps nine and every record on disk stays reportable.
