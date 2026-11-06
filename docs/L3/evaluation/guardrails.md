# evaluation — L4 guardrails

- **Owner:** one numbered note per risk this design identified, in the order they bite, each naming its rule and the
  test that catches it
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** all of `README.md`, `declarations.md`, `pool.md`, `scheduler.md`, `matrix.md`, `rating.md`,
  `tables.md`, `report.md`, `errors.md`

The unit battery's files and case ids are contract — one file per document, `test_declarations.py` (`EVL-1.k`) through
`test_guardrails.py` (`EVL-11.k`), the prefixes fixed and **not** contiguous (8 and 10 are unused, and `README.md` has
no file of its own because its rules are G1's). Each note is a place where a plausible implementation breaks a contract
the unit battery (`tests/evaluation/`) or the L1 battery (`tests/e2e/`) asserts, and a note's **Unverified** clause names
what no case drives.

## G1 — Eleven names, and `__all__` in the L1 order
`src/evaluation/__init__.py` exports exactly the eleven names of `README.md` §3 in that order and no twelfth — not
`Pool`, not `EvaluationError`, not `TABLE_SEED` (`e2e-surface.md` §1, D-12), one home per rule.
Caught by: `test_declarations.py::EVL-1.1`, `test_guardrails.py::EVL-11.g1`, FAM-1.27–1.37.
## G2 — The pool id is that digest and no other
`"pool-" + sha256("\n".join(ordered ids)).hexdigest()[:16]`, ids in `pool_members`'s order, a single `"\n"` between
them and no trailing separator, `m`/`frozen`/every other member field excluded (`pool.md` §4). A digest over the
member records, a `repr` of a tuple, or `hash()` (process-salted) is red.
Caught by: `test_pool.py::EVL-2.4` (the exact string, recomputed in the case), `::EVL-2.5`, FAM-6.8, FAM-6.9.
## G3 — The baselines come first, pinned, with the id that is their name
`build_pool` prepends `random`, `always-call`, `oracle` in `agents.baselines()`'s order, each `{"id": <name>,
"baseline": True, "pinned": True, "params": 0}`, and `offer` never evicts one (`pool.md` §2, §6). A baseline id of
`baseline:random` breaks `rating`'s anchor lookup, which compares ids (`rating.md` §2). A version declared **under one of
those three names** is `MemberDuplicate`, refused by `build_pool` naming the member: the membership would carry one id
twice (`pool.md` §2, `errors.md` §4).
Caught by: `test_pool.py::EVL-2.2`, `::EVL-2.9`, `::EVL-2.10`, FAM-6.2, FAM-6.5, FAM-6.7.
## G4 — The lineage order is the links, not the declaration's order
`_lineage_order` follows `lineage == id` from a start, refuses two members descending from one (`LineageConflict`)
and a chain reaching no start (`LineageCycle`), and concatenates chains in the order their starts were declared
(`pool.md` §3). Sorting by `step`, by `samples` or by the declaration's order passes FAM-6.3 by accident — the
battery's `version_chain` declares in lineage order — and fails `EVL-2.6`, which declares a chain shuffled.
Caught by: `test_pool.py::EVL-2.6`, `::EVL-2.7`, `::EVL-2.8`, FAM-6.3, FAM-6.4, FAM-16.20.
## G5 — A rich declaration is windowed, never refused; `frozen` is a flag
A declaration holding more than `m` versions keeps its last `m`; `m` above `league()["m"]` is refused and `m` ≤ M is
not; `frozen` must be a boolean and is stored, not interpreted (`pool.md` §2).
Caught by: `test_pool.py::EVL-2.3`, `::EVL-2.10`, FAM-6.3, FAM-6.11.
## G6 — `offer` drops the oldest and nothing else, and returns a new pool
The offered version joins the head, the oldest leaves when the window is full, the baselines stay, the argument pool is
unchanged and the id is recomputed (`pool.md` §6). Mutating the argument, or evicting by `samples` rather than by
window position, is red.
Caught by: `test_pool.py::EVL-2.11`, `::EVL-2.12`, FAM-6.6, FAM-16.21.
## G7 — `pool_members` returns §8's record, and the version records verbatim
`{"id", "m", "frozen", "members"}`, freshly built per call, each version the `records.md` §7 record the declaration
carried — `id`, `path`, `rung`, `variant`, `seed`, `step`, `samples`, `lineage` untouched (`pool.md` §5). A member
rebuilt with invented keys, or a read-back that is the internal tuple itself, is red: `EVL-2.13` edits the record and
asks again.
Caught by: `test_pool.py::EVL-2.13`, `::EVL-2.14`, FAM-6.10, FAM-6.11.
## G8 — Every seed is a derivation, and it is `scheduler.md` §3's
Four tagged functions, `int.from_bytes(sha256(...).digest()[:8], "big") % (2 ** 31)`, the parts joined by `\x1f` after
the tag, and a fifth derivation that is a modulo (`_draw_index`). `seed + i`, `random.Random(seed)`, a module-level
counter, a digest of a checkpoint path, or a call to `random.seed` anywhere in `src/evaluation/` is red — and the last is
red twice, because the global stream belongs to `engine.new_hand` (ASM-2).
Caught by: `test_scheduler.py::EVL-3.1`, `::EVL-3.2`, `test_rating.py::EVL-5.7`, `test_matrix.py::EVL-4.10` (a pool
version member played at the seed its checkpoint records, never a table- or path-derived one),
`test_guardrails.py::EVL-11.g8` (a clean interpreter: the nine entry points that play nothing leave `random.random()`
unchanged, while `match` and `matrix` move the stream only through `engine.new_hand`), FAM-7.5.
## G9 — Seats alternate, and `seat_split` carries two counts
Hand `i` gives seat 0 to `left` when `i` is even (`scheduler.md` §2); `seat_split` is keyed `seat 0`/`seat 1` and its
two values sum to `hands` and differ by at most one. A `button`/`big blind` pair, or a split of one number, is red —
the battery's reader collects the scalars under a seat- or button-named key and needs two.
Caught by: `test_scheduler.py::EVL-3.3`, `::EVL-3.4`, FAM-7.2.
## G10 — A hand's class is the sign of its net delta, and the directions are exact mirrors
`> 0` win, `< 0` loss, `== 0` tie, read from `play_hand`'s `payoffs[0]`/`payoffs[1]` (`scheduler.md` §4); the two means
are exact negations because both are one integer total over the same `hands`. A delta derived from `stacks`, or a mean
per seat rather than per member, is red.
Caught by: `test_scheduler.py::EVL-3.5`, `::EVL-3.6`, FAM-7.1, FAM-7.3, FAM-7.4.
## G11 — `params` is two integers, and `unlabelled` names the unmeasured zeros
`params` holds one plain `int` per member, position-aligned with `members`; a variant handed in as an opaque policy
gets `0` **and** its id in `unlabelled` — at the cell (`scheduler.md` §4) and at the table (`matrix.md` §5) — so a
reader tells a measured zero from an unmeasured one (ASM-10). A dict, a member record with more numbers in it, or an
invented count for an opaque policy is red.
Caught by: `test_scheduler.py::EVL-3.7`, `test_matrix.py::EVL-4.5`, FAM-7.6, FAM-16.24.
## G12 — The membership order and the pair enumeration are both fixed
`members` is the pool's members then `variant-1`, `variant-2` (`matrix.md` §1), and `cells` is `(0,1) (0,2) …
(0,K−1) (1,2) …`, `K(K−1)/2` of them, one per unordered pair (`matrix.md` §2). A `variant-N` label taken from the
policy, a pair listed twice, or cells ordered by outcome is red. A membership that is not distinct — a pool member named
`variant-1` beside that slot — is `MemberDuplicate`, refused before a checkpoint is loaded or a cell played (`matrix.md` §7).
Caught by: `test_matrix.py::EVL-4.1`, `::EVL-4.2`, `::EVL-4.8`, FAM-8.1, FAM-8.2, FAM-16.24.
## G13 — Every cell is played at the table's one hand count
`hands_per_cell` comes from `league()["tables"][table]` — 120 or 1500 — and **every** cell gets it, the three baseline
cells included (`matrix.md` §6). A cheaper cell for a baseline, or a hand count derived from a wall clock, is red
(`league.md` §3, ASM-15).
Caught by: `test_matrix.py::EVL-4.3`, `::EVL-4.4`, FAM-8.3, FAM-8.4, FAM-10.2.
## G14 — The matrix record's keys, and a table seed no argument supplies
`members`, `cells`, `hands_per_cell`, `table_seed`, `table`, then `pool`, `member_records`, `unlabelled`, `cell_count`
(`matrix.md` §5); `table_seed` is `declarations.TABLE_SEED` and `matrix` takes no seed (`matrix.md` §3); `table` is the
label **as a value**, never a substring. A second seed argument, a per-call seed, or `pool` holding the pool record
instead of its id, is red.
Caught by: `test_matrix.py::EVL-4.5`, `::EVL-4.6`, FAM-8.5, FAM-16.24.
## G15 — The anchor is applied every iteration, so the baselines' mean is exactly 0
The shift of `rating.md` §3 step 4 runs inside the loop, not once at the end; the likelihood is shift-invariant, so a
missing re-centring costs nothing in likelihood and everything in meaning. A mean of `0.04` is red. The one exception
is `rating.md` §3's pinned anchoring baseline, where the pin is taken last and so displaces the mean it was applied
after — that table's fit still converges and only the mean it states is not 0.
Caught by: `test_rating.py::EVL-5.2`, FAM-9.4, FAM-16.25. **Unverified**: that pinned-baseline table, which no case drives.
## G16 — Refuse exactly what the contract refuses, with §3's grammar
Every refusal of `errors.md` §2–§4 and no other, raised before the first cell is played, the first checkpoint loaded
or the first value fitted (`errors.md` §1, §5). Both directions fail: too few, where a `KeyError` escapes instead of
`PoolDeclarationInvalid`; too many, where a valid instance — a rich declaration, a `path`-less member, a hand-built
matrix, an explicit `n/a` family — is refused.
Caught by: `test_errors.py::EVL-9.1`–`EVL-9.11` (9.10 the too-many direction, 9.11 a NumPy seed), `test_pool.py::EVL-2.16`,
`test_scheduler.py::EVL-3.9`, `test_matrix.py::EVL-4.8`, `::EVL-4.9`, `test_rating.py::EVL-5.8`, `test_report.py::EVL-7.4`, FAM-8.7–8.9, FAM-11.2–11.8.
## G17 — The bound is ±10, and it never breaks the interval open
A member that won everything has no finite maximum-likelihood value; step 4 pins it at `BOUND = 10.0` (and a member
that lost everything at `−BOUND`), `bound_applied` and that member's own `bounded` are `True`, and the widened interval
still contains the value (`rating.md` §3–§4; `bound` is written **after** `bound_applied`, so a `rating_flag(read,
"bound")` reader finds the flag first). Returning `inf`, clipping the interval instead of widening it, or pinning a
member before the anchor's shift — which would leave `BOUND` minus the baselines' mean in the record — is red.
Caught by: `test_rating.py::EVL-5.5`, `::EVL-5.6`, FAM-9.6.
## G18 — The bootstrap resamples hands, 200 times, from the table seed
`RESAMPLES = 200`, one `multinomial(hands, p)` per cell per replicate in `cells` order, the refit from `θ = 0`, the
2.5/97.5 percentiles interpolated as `rating.md` §4 states, the value widened into the interval, and the generator
seeded from `_bootstrap_seed(matrix["table_seed"])` — no global stream, no cell-level resampling.
Caught by: `test_rating.py::EVL-5.7`, `::EVL-5.6`, FAM-9.2, FAM-9.7.
## G19 — The shipped artefact is evidence, and nothing reads it
`tables/league-full.json` with `schema`, `table`, `pool`, `matrix`, `rating`, `provenance`, `cost` (`tables.md` §3),
written by `evaluation.tables`' `__main__` and **never** by an entry point; the cost block carries `measured: true`
with `hands`, `seconds_per_hand` and `device: "cpu"`, while `league()` keeps carrying ASM-15's bound (`tables.md` §5).
An entry point that opens the file, or a `league()` reporting a measured number, is red. **Unverified**: no L1 case
reads the artefact (FAM-10.1 and FAM-10.3 assert the league's budgets and cell count only), so `EVL-6.*` is it.
Caught by: `test_tables.py::EVL-6.1`–`EVL-6.5`, `test_guardrails.py::EVL-11.g19`.
## G20 — `policy_from` reads exactly two recorded facts, and substitutes no seed
The seed and the encoding name come from the checkpoint's own container — `metadata.json`'s top-level `"seed"` and
`"representation"` → `"encoding"` — located by `_checkpoint_facts`' tolerant walk (`scheduler.md` §5.1), and nothing
else is read: the learner, its parameters and its rule stay `agents.load`'s (`surface.md` §12, `README.md` §3). Member
and bare path are built alike — `agents.as_policy(learner, encoder, seed)` at that recorded seed, over the encoder
`features.build_encoder` builds for the recorded name and for no other name. A path digest (`_artefact_seed`), a
table-derived seed, or a **catalogue read** (`features.encodings()` is not a granted arrow, `README.md` §5) is red:
there is no fallback, and a container recording no seed is `CheckpointRecordMissing`, refused rather than patched.
Caught by: `test_scheduler.py::EVL-3.8`, `::EVL-3.15` (the recorded-fact rule and its refusals, a name no `build_encoder`
accepts included), `test_guardrails.py::EVL-11.g20` (no path digest anywhere in `seeds.py`), FAM-12.3 and FAM-16.26 —
both **expected green**, because the policy now answers what `agents.act` answers at the learner's own seed.
## G21 — `report` copies and never invents
Each of the seven families is copied by value from the record under the name `protocol()` spells — `axis row`
included — and the report adds none: R1's pool row is the baselines it had, a single-variant rung's axis row stays the
string `n/a, single variant`, and `seeds`, `table`, `table seed` and `device` travel beside them (`report.md` §2, §4).
Filling an absent family, wrapping `n/a` into a record, or sorting members by rating is red.
Caught by: `test_report.py::EVL-7.1`–`EVL-7.3`, FAM-11.1, FAM-11.9–11.11, FAM-16.27.
## G22 — Run every battery

    .venv/bin/python -m pytest tests/evaluation -q                                  # this design's unit battery
    .venv/bin/python -m pytest tests/integration/evaluation -q                      # the join battery
    .venv/bin/python -m pytest tests/e2e -q                                         # the L1 battery, read-only
    .venv/bin/python -m unittest discover -s tests/e2e -t .                          # the L1 census

`tests/e2e/` is read-only here: a case that disagrees with this design is a finding against the design or the case, never a file to edit (`battery.md` §2, `strata/examiner.md` §5).
