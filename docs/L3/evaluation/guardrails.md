# evaluation — L4 guardrails

- **Owner:** one numbered note per risk this design identified, in the order they bite, each naming its rule and the
  test that catches it
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Rev 6:** D-29's second shape — G7, G20, G21 and G30 re-issued (the read-back's `game`, the three recorded facts, the header's tenth key, the seven-element side), and G31–G36 added for the risks the shape introduces · **Rev 7:** D-33's seat count — G8 re-issued for the sixth derivation and the counted draw, G16 for the three refusals and the read-not-copied seat count, G31 for the three declared names, and G36 for the deal's one shape on a six-seat hand (`seats.md` §1–§5, `shape.md` §1, D-33)
- **Read with:** all of `README.md`, `declarations.md`, `shape.md`, `seats.md`, `pool.md`, `families.md`, `utility.md`, `scheduler.md`,
  `matrix.md`, `rating.md`, `tables.md`, `report.md`, `errors.md`

The unit battery's files and case ids are contract — one file per document, `test_declarations.py` (`EVL-1.k`) through `test_guardrails.py` (`EVL-11.k`), the prefixes fixed and **not** contiguous (8 and 10 are unused, `README.md` has no file of its own because its rules are G1's, and `test_utility.py` (`EVL-14.k`) and `test_seats.py` (`EVL-15.k`) take the prefixes after it for `utility.md` and `seats.md`). Each note is a place where a plausible implementation breaks a contract the unit battery (`tests/evaluation/`) or the L1 battery (`tests/e2e/`) asserts; a note's **Unverified** clause names what no case drives.
## G1 — Eleven names, and `__all__` in the L1 order
`src/evaluation/__init__.py` exports exactly the eleven names of `README.md` §3 in that order and no twelfth — not `Pool`, not `EvaluationError`, not `TABLE_SEED` (`e2e-surface.md` §1, D-12).
Caught by: `test_declarations.py::EVL-1.1`, `test_guardrails.py::EVL-11.g1`, FAM-1.27–1.37.
## G2 — The pool id is that digest and no other, one line per member
`"pool-" + sha256(payload).hexdigest()[:16]`, one line per member in `pool_members`'s order joined by a single `"\n"` with no trailing separator: a **baseline** contributes its `id` alone, a **version** its `id`, `"\x1f"`, its `rule`, `"\x1f"` and its `utility` (`families.md` §4, `utility.md` §3, ASM-27, D-20). A digest over the member records, over ids alone, over ids and rules without the utility, a `repr` of a tuple, or `hash()` (process-salted) is red.
Caught by: `test_pool.py::EVL-2.4` (the exact string, recomputed in the case), `::EVL-2.5`, FAM-6.8, FAM-6.9, FAM-18.11.
## G3 — The baselines come first, pinned, with the id that is their name
`build_pool` prepends `random`, `always-call`, `oracle` in `agents.baselines()`'s order, each `{"id": <name>, "baseline": True, "pinned": True, "params": 0}`, and `offer` never evicts one (`pool.md` §2, §6). A baseline id of `baseline:random` breaks `rating`'s anchor lookup, which compares ids (`rating.md` §2). A version declared **under one of those three names** is `MemberDuplicate` (`pool.md` §2, `errors.md` §4).
Caught by: `test_pool.py::EVL-2.2`, `::EVL-2.9`, `::EVL-2.10`, FAM-6.2, FAM-6.5, FAM-6.7.
## G4 — The window is the lineage links, grouped into families, not the declaration's order
Each **family** is one chain — a start whose `lineage` is no declared `id`, then each member whose `lineage` is its predecessor's `id` — the chains concatenated in their starts' declaration order, each oldest to newest (`families.md` §1–§2); two members descending from one (`LineageConflict`) and a chain reaching no start (`LineageCycle`) are refused. Sorting by `step`, by `samples` or by the declaration's order passes FAM-6.3 by accident and fails `EVL-2.6`, which declares a chain shuffled.
Caught by: `test_pool.py::EVL-2.6`, `::EVL-2.7`, `::EVL-2.8`, FAM-6.3, FAM-6.4, FAM-16.20.
## G5 — A rich declaration is windowed, never refused; `frozen` is a flag
A declaration holding more than `m` versions keeps `m` of them under `families.md` §3's rule; `m` above `league()["m"]` is refused and `m` ≤ M is not; `frozen` must be a boolean and is stored, not interpreted (`pool.md` §2).
Caught by: `test_pool.py::EVL-2.3`, `::EVL-2.10`, FAM-6.3, FAM-6.11.
## G6 — `offer` extends one family, evicts fair-share, and returns a new pool
The offered version joins the family whose **newest** member it names, or opens a new family on a label no member carries; a full window evicts the oldest member of the family that holds the most, ties to the earlier family (`families.md` §3, §5); the baselines stay, the argument pool is unchanged and the id is recomputed (`pool.md` §1, `families.md` §4). Mutating the argument, evicting by `samples` instead of by window position, or evicting oldest-first across the concatenation, is red.
Caught by: `test_pool.py::EVL-2.11`, `::EVL-2.12`, FAM-6.6, FAM-16.21.
## G7 — `pool_members` returns §8's record, with `game`, `rules` and `utilities`, and the version records verbatim
`{"id", "m", "frozen", "game", "members", "rules", "utilities"}`, freshly built per call (`pool.md` §5, `utility.md` §3, `shape.md` §4): `game` is **required** and names the one shape the pool is on — an absent declaration key reads as the default, and a read-back that omits the key, or reads it off a member instead of the pool, is red; `members` is the baselines then the window, each version the `records.md` §7 record the declaration carried with its `rule`, its `utility` and its `game` untouched — all three the declaration's own, nothing filled in — `rules` the **distinct** rules those versions declare **in the window's order**, and `utilities` their counterpart; both are the empty tuple for R1's pool, never `(None,)`. A read-back that is the internal tuple itself, or one whose `rules` is a set or a sorted list, is red: `EVL-2.13` edits the record and asks again.
Caught by: `test_pool.py::EVL-2.13`, `::EVL-2.14`, FAM-6.10, FAM-6.11, FAM-18.11.
## G8 — Every seed is a derivation, and it is `scheduler.md` §3's
Four tagged functions, `int.from_bytes(sha256(...).digest()[:8], "big") % (2 ** 31)`, the parts joined by `\x1f` after the tag; a fifth derivation that is a modulo (`_draw_index`); and a sixth, `_draw_order(seed, n)`, which returns a permutation of `0..n-1` from a fifth tag (`_DRAW_TAG`) with `_draw_index(seed, n)` first and the rest ascending by `(_seed(_DRAW_TAG, seed, position), position)` — a counted draw of `k` from `n` is `k` **distinct** positions, and a `k > n` is refused rather than wrapped, padded or truncated (`seats.md` §2, ASM-43). `seed + i`, `random.Random(seed)`, a module-level counter, a digest of a checkpoint path, a resample in place of the permutation, or a call to `random.seed` anywhere in `src/evaluation/` is red — and the last is red twice, because the global stream belongs to `engine.new_hand` (ASM-2).
Caught by: `test_scheduler.py::EVL-3.1`, `::EVL-3.2`, `test_rating.py::EVL-5.7`, `test_matrix.py::EVL-4.10`, `test_guardrails.py::EVL-11.g8` (a clean interpreter: the nine entry points that play nothing leave `random.random()` unchanged), `test_seats.py::EVL-15.4`, `::EVL-15.5`, `::EVL-15.6`, FAM-7.5, FAM-21.
## G9 — Seats alternate, and `seat_split` carries two counts
Hand `i` gives seat 0 to `left` when `i` is even (`scheduler.md` §2); `seat_split` is keyed `seat 0`/`seat 1` and its two values sum to `hands` and differ by at most one. A `button`/`big blind` pair, or a split of one number, is red.
Caught by: `test_scheduler.py::EVL-3.3`, `::EVL-3.4`, FAM-7.2.
## G10 — A hand's class is the sign of its net delta, and the directions are exact mirrors
`> 0` win, `< 0` loss, `== 0` tie, read from `play_hand`'s `payoffs[0]`/`payoffs[1]` (`scheduler.md` §4); the two means are exact negations because both are one integer total over the same `hands`. A delta derived from `stacks`, or a mean per seat rather than per member, is red.
Caught by: `test_scheduler.py::EVL-3.5`, `::EVL-3.6`, FAM-7.1, FAM-7.3, FAM-7.4.
## G11 — `params` is two integers, `unlabelled` names the unmeasured zeros, and a rule is never invented
`params` holds one plain `int` per member, position-aligned with `members`; a variant handed in as an opaque policy gets `0` **and** its id in `unlabelled` — at the cell (`scheduler.md` §4) and at the table (`matrix.md` §5). Its `rules` entry is `None`, because an opaque policy's rule is whatever its own `learning_rule` says and nothing else: a `params` dict, or a rule or a count invented for a policy this module did not build, is red (ASM-10, `scheduler.md` §5).
Caught by: `test_scheduler.py::EVL-3.7`, `test_matrix.py::EVL-4.5`, FAM-7.6, FAM-16.24.
## G12 — The membership order and the pair enumeration are both fixed
`members` is the pool's members then `variant-1`, `variant-2` (`matrix.md` §1), and `cells` is `(0,1) (0,2) … (0,K−1) (1,2) …`, `K(K−1)/2` of them (`matrix.md` §2). A `variant-N` label taken from the policy, a pair listed twice, or cells ordered by outcome is red. A membership that is not distinct is `MemberDuplicate`, refused before a checkpoint is loaded (`matrix.md` §7).
Caught by: `test_matrix.py::EVL-4.1`, `::EVL-4.2`, `::EVL-4.8`, FAM-8.1, FAM-8.2, FAM-16.24.
## G13 — Every cell is played at the table's one hand count
`hands_per_cell` comes from `league()["tables"][table]` — 120 or 1500 — and **every** cell gets it, the three baseline cells included (`matrix.md` §6). A cheaper cell for a baseline, or a hand count derived from a wall clock, is red (`league.md` §3, ASM-15).
Caught by: `test_matrix.py::EVL-4.3`, `::EVL-4.4`, FAM-8.3, FAM-8.4, FAM-10.2.
## G14 — The matrix record's keys, in this order, its `game` required, and a table seed no argument supplies
`members`, `cells`, `rules`, `population`, `utilities`, `utility_population`, `hands_per_cell`, `table_seed`, `table`, then `game` (this module's own, **required**), `pool`, `member_records`, `unlabelled`, `cell_count` (`matrix.md` §5); `table_seed` is `declarations.TABLE_SEED` and `matrix` takes no seed (`matrix.md` §3); `table` is the label **as a value**, never a substring. A second seed argument, a per-call seed, a shape argument, `pool` holding the pool record instead of its id, a `game` inferred from a member rather than the pool's, or `population` sorted by insertion rather than lexically, is red.
Caught by: `test_matrix.py::EVL-4.5`, `::EVL-4.6`, FAM-8.5, FAM-16.24.
## G15 — The anchor is applied every iteration, so the baselines' mean is exactly 0
The shift of `rating.md` §3 step 4 runs inside the loop, not once at the end; the likelihood is shift-invariant, so a missing re-centring costs nothing in likelihood and everything in meaning. A mean of `0.04` is red. The one exception is `rating.md` §3's pinned anchoring baseline, where the pin is taken last and so displaces the mean it was applied after.
Caught by: `test_rating.py::EVL-5.2`, FAM-9.4, FAM-16.25. **Unverified**: that pinned-baseline table, which no case drives.
## G16 — Refuse exactly what the contract refuses, with §3's grammar
Every refusal of `errors.md` §2–§4 and no other, raised before the first cell is played, the first checkpoint loaded or the first value fitted (`errors.md` §1, §5) — `UnknownRule`, `UnknownUtility`, `RuleMismatch`, `UtilityMismatch`, `FamilyBoundExceeded`, `UnknownShape`, `ShapeMismatch`, `UnknownExploration`, `InvalidDrawCount`, `DrawExceedsMembership` and `SeatCountExceeded` included, and the mismatches the ones that must come **after** their load (`families.md` §6, `utility.md` §4, `shape.md` §3, `seats.md` §2–§3). Both directions fail: too few, where a `KeyError` escapes instead of `PoolDeclarationInvalid`; too many, where a valid instance — a rich declaration, a `path`-less member, a **bare §7 record** declaring no rule or no utility handed to `match`/`matrix`/`opponent`, a record naming **no** `game` (the default shape), a **six-seat pool, hand and greedy pass**, or a `count` of one (`opponent(pool, seed, 1)` is the uncounted draw's member) — is refused. **And a game parameter is read, never copied**: `seat_count` asks `engine.game_config`, `PAIRWISE_SEATS` names the **instrument's** arity and not a shape's row, and a literal `2` or `6` standing as a game's seat count in this package is red, while the two-seat shapes must pass every check untouched (`seats.md` §1, §3, `module-map.md` §2, D-13, D-33).
Caught by: `test_errors.py::EVL-9.1`–`EVL-9.11`, `test_pool.py::EVL-2.16`, `test_scheduler.py::EVL-3.9`, `test_matrix.py::EVL-4.8`, `::EVL-4.9`, `test_rating.py::EVL-5.8`, `test_report.py::EVL-7.4`, `test_seats.py::EVL-15.2`, `::EVL-15.3`, `::EVL-15.7`, `::EVL-15.8`, `::EVL-15.9`, FAM-8.7–8.9, FAM-11.2–11.8, FAM-18.11, FAM-21.
## G17 — The bound is ±10, and it never breaks the interval open
A member that won everything has no finite maximum-likelihood value; step 4 pins it at `BOUND = 10.0` (a member that lost everything at `−BOUND`), `bound_applied` and that member's `bounded` are `True`, and the widened interval still contains the value (`rating.md` §3–§4; `bound` is written **after** `bound_applied`). Returning `inf`, clipping the interval instead of widening it, or pinning a member before the anchor's shift, is red.
Caught by: `test_rating.py::EVL-5.5`, `::EVL-5.6`, FAM-9.6.
## G18 — The bootstrap resamples hands, 200 times, from the table seed
`RESAMPLES = 200`, one `multinomial(hands, p)` per cell per replicate in `cells` order, the refit from `θ = 0`, the 2.5/97.5 percentiles interpolated as `rating.md` §4 states, the value widened into the interval, and the generator seeded from `_bootstrap_seed(matrix["table_seed"])` — no global stream, no cell-level resampling.
Caught by: `test_rating.py::EVL-5.7`, `::EVL-5.6`, FAM-9.2, FAM-9.7.
## G19 — The shipped artefact is evidence, and nothing reads it
`tables/league-full.json` with `schema`, `table`, `pool`, `matrix`, `rating`, `provenance`, `cost` (`tables.md` §3), written by `evaluation.tables`' `__main__`, **never** by an entry point; its cost block carries `measured: true` with no ceiling (ASM-21), and `provenance.member_status` says which player each member is (`tables.md` §2, §5). An entry point that opens the file, or a `league()` carrying a per-hand number, is red; no L1 case reads it.
Caught by: `test_tables.py::EVL-6.1`–`EVL-6.6`, `test_guardrails.py::EVL-11.g19`.
## G20 — `policy_from` reads exactly three recorded facts, and the rule is the built policy's
The seed, the encoding name and the **shape** come from the checkpoint's own container (`scheduler.md` §5.1), and nothing else is read: the learner, its parameters and its **rule** stay `agents.load`'s — the rule reported is the `learning_rule` attribute of the policy `agents.as_policy` built, which is what the file records (`rules.md` §6, ASM-20). The encoder is built **for the recorded shape** — `features.build_encoder(name, shape=game)` — and the policy by `agents.as_policy(learner, encoder, seed, exploration)`. Member and bare path are built alike. A path digest, a table-derived seed, a **catalogue read**, a rule parsed out of `metadata.json` instead of taken from the policy, or an encoder built without the recorded shape, is red.
Caught by: `test_scheduler.py::EVL-3.8`, `::EVL-3.15`, `test_guardrails.py::EVL-11.g20`, FAM-12.3 and FAM-16.26.
## G21 — `report` copies and never invents, and the shape rides in the header family
Each of the seven families is copied by value from the record under the name `protocol()` spells — `axis row` included — and the report adds none, filling an absent family, wrapping `n/a` into a record, or sorting members by rating being red (`report.md` §2, §4). The pool family's `rules` **and** `utilities` are the two completed keys, written on the report's own copy and never into the argument (`report.md` §1–§2, `utility.md` §3, D-20) — and the header family's **tenth** key `shape` is the third, written beside the nine a record states while `HEADER_ITEMS` stays nine (`declarations.md` §2.1, `shape.md` §4). A report that adds a top-level `game`, or one whose header family lacks the resolved shape, is red.
Caught by: `test_report.py::EVL-7.1`–`EVL-7.3`, FAM-11.1, FAM-11.9–11.11, FAM-16.27, FAM-18.11.
## G22 — Run every battery
The census needs no guard: `tests/e2e/__init__.py` points the write root at a private temporary directory before any case, as `tests/conftest.py` does (`docs/L3/harness/layout.md` §5, `battery.md` §2).

    .venv/bin/python -m pytest tests/evaluation -q                                  # this design's unit battery
    .venv/bin/python -m pytest tests/integration/evaluation -q                      # the join battery
    .venv/bin/python -m pytest tests/e2e -q                                         # the L1 battery, read-only
    .venv/bin/python -m unittest discover -s tests/e2e -t .                          # the L1 census; safe unguarded only in this -t . form
`tests/e2e/` is read-only here: a case that disagrees with this design is a finding against the design or the case, never a file to edit (`battery.md` §2, `strata/examiner.md` §5).
## G23 — The digest carries each version's rule, not ids alone
A payload of ids alone lets **one member's rule contradict its neighbour's under one id**: `{A: masked-q, B: double-q}` and `{A: double-q, B: masked-q}` would digest alike, so a table could not say which population a rating was fitted over, and R1's pool and a two-estimator pool of the same ids would wear one id (`families.md` §4, ASM-27); leaving the utility out repeats the defect for the objective, which is D-20's amendment to the same rule (`utility.md` §3, D-20). It bites silently — the ids are right and only the certification is missing.
Caught by: `test_pool.py::EVL-2.4` (a pool's id recomputed from the rule-bearing payload), `::EVL-2.5` (two memberships differing only in a rule digest differently), FAM-6.8, FAM-6.9.
## G24 — Eviction is fair-share, so no family is emptied while another holds two
Oldest-first over the concatenated window (the rule before D-19) evicts the last member of a family whose chain is short, so the population the table claims to have measured loses an estimator it still names (`families.md` §3, ASM-26). It bites only when a second family exists, so a single-chain battery case passes it.
Caught by: `test_pool.py` (a window of two families at `m` keeps one member of each after an offer), FAM-6.6, FAM-16.21.
## G25 — `offer` accepts a second family's next snapshot
A lineage check written as "extend the window's newest version" — the rule before D-19 — refuses the snapshot that advances any family but one, so a heterogeneous pool can be declared and never roll (`families.md` §5, D-19's V-F4). It bites as a refusal of a valid instance, which is a defect in the over-refusal direction (`errors.md` §5).
Caught by: `test_pool.py` (an offer extending the second family's newest succeeds), `::EVL-2.11`, FAM-6.6.
## G26 — `policy_from` reports the rule the file records, not one this module chose
A `policy_from` that reports the catalogue's default, a rule inferred from the member record, or the rule parsed out of the container's JSON reports a rule the file does not record — and a version-1 container would then read as anything at all (`scheduler.md` §5.1, `rules.md` §6, ASM-20). It bites when a member's record and its file disagree: the module would confirm its own guess.
Caught by: `test_scheduler.py::EVL-3.8`, `::EVL-3.15`, `test_guardrails.py::EVL-11.g20`, FAM-16.26.
## G27 — `report` requires no new content item
A report that *requires* a rules item — a new family, a new header item, or a stricter `required` tuple — refuses a record another battery hand-builds, and a valid instance refused is as much a failure as a contract missed (`report.md` §1, §4, `errors.md` §5, D-19). It bites the L1 battery hardest, whose records predate the catalogue.
Caught by: `test_report.py::EVL-7.1`–`EVL-7.4`, `test_declarations.py` (the seven families' `required` tuples unchanged), FAM-11.1, FAM-11.9.
## G28 — `build_pool` refuses an uncatalogued rule; it never maps it onto the default
Mapping an unknown name onto the catalogue's first member — the tempting convenience, since a spec naming none is built under it — reports a member as trained under an estimator it was not, and the pool's `rules`, the matrix's `population` and the id would all certify the wrong population (`families.md` §6, `rules.md` §4, ASM-26). It bites for a typo, which is exactly the case a reader would want refused by name.
Caught by: `test_pool.py` (an uncatalogued `rule` raises `UnknownRule` naming the catalogue), `test_errors.py::EVL-9.4`, FAM-8.7.
## G29 — A version declaration that names no utility is refused by name, never read as the catalogue's first member
`build_pool` and `offer` refuse an omitted `utility` as a missing required key (`MemberInvalid`, naming the member and the key), because defaulting one reports a member as trained under an objective nobody declared — and the pool id, the record's `utilities` and the matrix's `utility_population` would all certify the wrong objective (`utility.md` §2, §4, `pool.md` §2, `records.md` §7, ASM-27, D-20). The reading that **stays** admitted is the bare §7 record handed to `match`, `matrix` or `opponent`, where the container is the witness (`utility.md` §2, `scheduler.md` §5). Mapping a *declared but uncatalogued* name onto the default stays red too (`utility.md` §4, `errors.md` §5).
Caught by: `test_utility.py::EVL-14.3` (the absent key is refused by name), `::EVL-14.6` (an offered version that names none is refused), `::EVL-14.13` (the bare record stays admitted), FAM-18.11.
## G30 — The side tuple is seven elements, and every reader unpacks seven
`_side` returns `(id, policy, params, unlabelled, rule, utility, game)`; `_play_cell` unpacks all seven, `_membership` reads
`side[4]`, `side[5]` and `side[6]` for its records' `rule`, `utility` and `game`, and `matrix._variant_shape` reads `side[6]` — so
a six-element side, or a cell whose `utilities` maps positionally instead of by member id, leaves one member's utility or one
member's shape on another (`scheduler.md` §5, `matrix.md` §4–§5, `utility.md` §3, `shape.md` §4, D-20, D-29).
Caught by: `test_scheduler.py::EVL-3.7`, `test_matrix.py::EVL-4.5`, FAM-7.6, FAM-18.10.
## G31 — The default shape is an **absence**, never a defaulting of a present name
An absent `game` reads as `SHAPE_NAMES[0]`; a `game` that is present and uncatalogued is `UnknownShape` **naming it and the declared
names** (`shape.md` §2–§3). The two failure modes are opposite and both bite: mapping an uncatalogued name onto the default, the
silent substitution `e2e-surface.md` §2 forbids, which would make a typo play the fixed game; and refusing an absent one, which would
make every record the repository already holds unreadable — the 18 shipped version-1 containers, `tables/league-full.json` and
`checkpoints/evidence/r1-live.json` among them (`docs/L1/shapes.md` §3, §5).
Caught by: `test_pool.py` (a pool built from a declaration naming no `game` reads back `fixed-limit-20`), `test_errors.py::EVL-9.4`
(an uncatalogued shape raises `UnknownShape` naming the declared three), `test_scheduler.py` (a version-1 container loads as the
default shape), FAM-19's shape cases.
## G32 — The pool id must not digest the shape
The payload is one line per member — a baseline's bare id, a version's `id`, `\x1f`, its `rule`, `\x1f`, its `utility` — and the
shape is **outside** it (`families.md` §4, `pool.md` §4, ASM-27): ASM-27's rule is that the id changes when and only when the
membership does, so a shape in the digest would rename a baselines-only pool that had not changed — R1's
`pool-bcbea031cb617939` and the file shipped beside it — and would make two pools of one membership on two shapes two ids, where
the design's point is that they are **one id and two tables** (`records.md` §8, `shape.md` §4, `tables.md` §3). It bites
silently: every id is still well formed and only the certification is wrong.
Caught by: `test_pool.py::EVL-2.4` (the exact string, recomputed from the rule-bearing payload), `::EVL-2.5`, FAM-6.8, FAM-6.9.
## G33 — A rating is one shape's, and two shapes' ratings are never tabulated together
`rating` reads the matrix's `game` and each cell's `game`, both tolerantly, and refuses a matrix whose cells name more than one
shape or whose own `game` is not the shape its cells name — naming the shapes — so no value is ever a distance measured in one
game and read in another (`rating.md` §1, §6, `shape.md` §3, `docs/L1/shapes.md` §6, ASM-17). The returned record carries the one
shape it fitted, and the arithmetic does not read it: a fit that took a shape as an input would be a different rating model, and
a fit that ignored the disagreement would tabulate two games on one scale.
Caught by: `test_rating.py` (a two-shape matrix raises `ShapeMismatch` naming both), `test_report.py` (the report's three-way
refusal), FAM-9's shape case, FAM-19.
## G34 — The `off` mode draws nothing and decides identically at two seeds
`policy_from(path, "off")` returns the masked maximum and the tie-break alone, and **no generator is drawn from**: two policies at two
seeds decide identically on one readout, and a case that patches the generator and asserts it was never called is the direct test
(`shape.md` §5, `scheduler.md` §7, `docs/L1/sizing.md` §4). Building the policy with the schedule's keyed draw and calling it
"greedy" — or reading the ε = 0.05 tail as nearly greedy — is red, because the census `docs/L1/sizing.md` §7 computes would then be a sample of the exploration schedule and not of the policy (D-28, D-29).
Caught by: `test_scheduler.py` (two seeds, one readout, identical answers under `off`; the generator untouched), FAM-12's mode
cases, FAM-19.
## G35 — A report requires no new content item of a record, the shape included
The header family's tenth key `shape` is written by the report onto its **own copy** of that family; `HEADER_ITEMS` keeps nine,
`protocol()["header"]` keeps nine, and no family's `required` tuple grows (`declarations.md` §2.1, §3, `report.md` §1–§4). A report
that *requires* a shape item — a tenth `HEADER_ITEMS` entry, a new family, a stricter `required` tuple — refuses a record another
battery hand-builds and every record already on disk, which is over-refusal and therefore a defect of its own (`errors.md` §5,
`shape.md` §2). It bites hardest on the L1 battery, whose records predate the shape.
Caught by: `test_report.py::EVL-7.1`–`EVL-7.4`, `test_declarations.py` (the seven families' `required` tuples and `HEADER_ITEMS` unchanged), FAM-11.1, FAM-11.9.
## G36 — A cell's hands are dealt on the cell's shape, handed to `play_hand` as its fourth argument
`_play_cell` calls `engine.play_hand(hand_seed, left_policy, right_policy, shape=game)` at **both** seat arrangements, `game` being the shape the cell is played on: the table's, from `pool_members(pool)["game"]`, when `matrix` supplies it, and `_cell_shape(...)`'s resolution at `match` (`scheduler.md` §1, §5, `matrix.md` §1, `shape.md` §4, D-29). A `play_hand` called without it deals the **default** shape, so a `no-limit-100` version member decodes its six-index vocabulary against a fixed-limit deal's three legal descriptors and `engine` refuses its descriptor (`InvalidAction`, naming it) before the cell can report anything: the cell's shape would then be a label on a deal it never shaped, and that cell unplayable. It bites **silently** for every default-shape cell, because `engine` reads an absent shape as `fixed-limit-20`: an absent argument and the default's own name deal identically, so no gated number moves and only a second-shape cell is red.
Caught by: `tests/integration/evaluation/test_join_shapes.py::JOIN-EVL-15.4` (a default-shape baseline opposite a `no-limit-100` member is played on that shape, its `game` saying so and every decision legal), FAM-19.
