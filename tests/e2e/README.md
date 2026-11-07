# `tests/e2e/` — the L1 end-to-end battery (Rev 2)

The battery that drives the built artifact through the declared entry points of
`docs/L1/e2e-surface.md` §3. Authored at L1 under `docs/L1/battery.md`; the harness module
owns the path and may support it, but may not rewrite it (`docs/L1/module-map.md` §5).

Run it from the repository root, with the project venv:

```
.venv/bin/python -m unittest discover -s tests/e2e -t .
```

`tests/e2e/__init__.py` exists so that `-t .` can import the start directory as
`tests.e2e`; there is no `tests/__init__.py`, and none is needed. It is also this battery's
write root hook: `unittest` loads no conftest at all, so the package init points
`PYPOKER_CHECKPOINT_ROOT` — the one ambient override `training.layout` reads on every call —
at a private `pypoker-battery-checkpoints-*` directory before any case module is imported, and
removes it when the process exits. `pytest` reaches the same root through `tests/conftest.py`,
and the two hooks are idempotent (the first records the root in `PYPOKER_BATTERY_ROOT`, which
`src/` never reads, and the second declines), so **both documented runners are safe** and
neither writes into the repository's `checkpoints/` (`docs/L1/battery.md` §2,
`docs/L3/harness/layout.md` §5, `docs/L2/training/write-root.md` §4). The battery imports
nothing beyond the standard library and the six declared packages, so it stays collectable
under either runner (`docs/L1/battery.md` §2).

Every case is red before implementation exists. Each one reaches its first declared
entry point through `_surface`, so an absent surface is one clear
`SurfaceAbsent: surface absent: ...` failure in the case that needed it — never a
collection error, and never an error thrown by the battery itself.

## Files and families

Rev 2 replaced the head-to-head opponent with the bounded round-robin league (D-16):
`evaluation` declares eleven entry points and the map forty-nine (`e2e-surface.md` §3.4,
§4). The families below are the sixteen of `battery.md` §3, in its order.

| File | Family | What it holds | Cases |
|---|---|---|---|
| `_surface.py` | — | `sys.path` plumbing for `src/`, the six package imports, the invented seeds and hand counts, the tolerant readers the whole battery shares, the one shared table, and the base case | — |
| `_records.py` | — | the `records.md` readers FAM-6..FAM-16 assert through (version §7, pool §8, cell §9, matrix §10, rating §11, run record §12), the container-agnostic matrix doctorers, the process-wide scratch area the shared pool needs, and the version/table fixtures | — |
| `test_fam01_surface.py` | FAM-1 | one case per entry point, all 49, in `e2e-surface.md` §3 order | 49 |
| `test_fam02_invariance.py` | FAM-2 | the D-2 game, the D-3 action vocabulary and the information set, identical across the ladder | 11 |
| `test_fam03_ladder.py` | FAM-3 | six rungs in brief §2's order; every adjacent and intra-rung pair; the one frozen pool both arms of R4, R5 and R6 declare and record | 18 |
| `test_fam04_seeds.py` | FAM-4 | the seed contract of `protocol.md` §2 and §4 with the pool in the reproducible tuple | 13 |
| `test_fam05_baselines.py` | FAM-5 | `random`, `always-call`, `oracle` as checkable rules (D-6, ASM-4) | 8 |
| `test_fam06_pool.py` | FAM-6 | the bound M, the pinned baselines, `offer`'s eviction from an unfrozen window, a frozen pool holding still, R1's three-baseline pool, and the membership's deterministic id | 12 |
| `test_fam07_scheduler.py` | FAM-7 | one cell at a time: hand accounting, seat alternation, both directions from one set of hands, and the drawn opponent | 9 |
| `test_fam08_matrix.py` | FAM-8 | membership, K(K−1)/2 cells, one hand count, the baseline cells, and the three refusals | 9 |
| `test_fam09_rating.py` | FAM-9 | one value and a 95% interval per member, Bradley-Terry, the baselines' zero anchor, the bounded member | 8 |
| `test_fam10_tables.py` | FAM-10 | the two budgets and their cell sizes, the live table's arithmetic, and the cost record | 5 |
| `test_fam11_report.py` | FAM-11 | the seven evidence families, a named refusal for each missing one, R1's pool row and the single-variant axis row | 12 |
| `test_fam12_checkpoints.py` | FAM-12 | the M-retained-snapshots-plus-final-model rule, the decision boundary, the retained window, and the shipped index | 6 |
| `test_fam13_parity.py` | FAM-13 | R1 against R2 on identical work, the recorded cost of both, and the driver's own clock (D-7) | 6 |
| `test_fam14_harness.py` | FAM-14 | `drive`, `fixtures`, `factory`, `seam`, `expect` and `timings` as support, not substitute | 11 |
| `test_fam15_custom.py` | FAM-15 | the battery's own seventh rung, its declared membership and the invented pool, run and reported as data | 5 |
| `test_fam16_blind.py` | FAM-16 | the 37 blind instances of §5 below | 37 |

219 cases: FAM-1 49, FAM-2 11, FAM-3 18, FAM-4 13, FAM-5 8, FAM-6 12, FAM-7 9,
FAM-8 9, FAM-9 8, FAM-10 5, FAM-11 12, FAM-12 6, FAM-13 6, FAM-14 11, FAM-15 5, FAM-16 37.

This directory is the harness's *consumer*, not its implementation: the `50 + 10×N` line
ceiling of `docs/L1/module-map.md` §4 applies to the harness's own files, and
`docs/L1/battery.md` §5 leaves it to `strata-lint` (never asserted by a battery).

## Cost

`evaluation.matrix` is the battery's most expensive observable: the declared surface fixes
a cell at the live budget's 120 hands, so the smallest table the surface allows is K = 4
(the three pinned baselines plus one variant) and 6 cells — 720 hands. `_surface` builds
one baselines-plus-one-variant table and its rating once per process and shares them
(`shared_league`), and FAM-16 builds one invented-membership table the same way. Everything
else the battery plays stays in the tens of hands per case (`battery.md` §2), and the
timing cases assert that a cost record carries the hands counted and a per-hand cost or its
reciprocal throughput — read by what the keys name, never by a literal spelling — and never
that a wall clock was beaten (ASM-15).

## Invented instances

`docs/L1/battery.md` §4 requires, for each of the 37 `general` rows of `e2e-surface.md` §5,
an instance that appears in no design document. The battery's own vocabulary:

- seeds `6174`, `271828`, `90210`, `5150`, `131`, `4711`, `8086`, `314159`, `424242`,
  `99991` and the table seeds `40961`, `7817` — the protocol's seed set is `0, 1, 2`;
- cell sizes `23` and `14` hands, and single cells of `37` and `11` hands — the league's
  cells are 120 live and 1,500 full (`league.md` §6);
- a training budget of `250` and `60` hands per variant per seed — the live budget is
  1,000 and the shipped one 200,000 (`ladder.md` §6);
- learner widths `61`, `96` and `48` at depths `2`, `3` and `4` — the ladder fixes a
  parameter budget, not these sizes (ASM-10);
- the encoding/equity sample count `257` (`engine.equity` takes a count, the design fixes
  none);
- the versions `kestrel`, `bramble`, `thistle`, `quarry`, `marlin`, `osprey`, `nimbus`,
  each a real checkpoint the case writes with `agents.save`, carrying an invented rung,
  variant, seed, training step, hands trained and the predecessor it descends from, in the
  record shape of `records.md` §7;
- a seventh rung `R7` (`_surface.custom_rung`) whose axis, variant names
  `deep-sparse`/`wide-sparse`, hyperparameters, sample budget, seed set, pool id and
  declared membership are the battery's own, written to `ladder.md` §3's schema — the
  membership declaration of `records.md` §8 included, which is how a custom league reaches
  the loop as data — and the unregistered name `R7-bottleneck`;
- the seam labels `echo-legal` and `seeded-legal` — a seam takes **any label**, because
  its contract is the policy protocol and not the label, with `recording` and `synthetic`
  the documented behaviours (`e2e-surface.md` §3.6, `records.md` §14) — and the observed
  values the battery invents for a **discovered** expectation kind: the expectation kinds
  are the harness's own set and are read off `harness.fixtures()`, so no kind is invented
  here (D-13, D-15).

## The 37 blind instances

| Case | `general` entry point (the subject) | The invented instance |
|---|---|---|
| FAM-16.1 | `engine.new_hand` | seed 424242, with 99991 as the contrast |
| FAM-16.2 | `engine.readout` | the first decision at seed 99991 |
| FAM-16.3 | `engine.legal_actions` | the first decision at seed 131, every descriptor applied |
| FAM-16.4 | `engine.apply_action` | the first action of seed 4711's hand |
| FAM-16.5 | `engine.is_terminal` | a hand at seed 90210 played out within 200 decisions |
| FAM-16.6 | `engine.payoffs` | the completed hand at seed 6174 |
| FAM-16.7 | `engine.play_hand` | seed 5150, a 61-wide learner against the oracle at seed 314159 |
| FAM-16.8 | `engine.equity` | 257 samples at seed 90210, with 97 as the contrast |
| FAM-16.9 | `features.encode` | the readout at seed 99991 |
| FAM-16.10 | `features.legal_indices` | the first two decisions at seed 131 |
| FAM-16.11 | `features.decode_action` | seed 4711's legal indices |
| FAM-16.12 | `agents.build_learner` | 61 wide, 2 deep, seed 424242 |
| FAM-16.13 | `agents.param_count` | 61 wide against 96 wide at depth 2, seed 424242 |
| FAM-16.14 | `agents.act` | 61 wide at seed 99991 on seed 5150's decisions |
| FAM-16.15 | `agents.learn` | 61 wide at seed 131 on seed 90210's transitions |
| FAM-16.16 | `agents.save` | 61 wide at seed 424242 into `fam16-16-wide61-d2.ckpt` |
| FAM-16.17 | `agents.load` | the same invented checkpoint, restored and compared |
| FAM-16.18 | `agents.as_policy` | 61 wide at seed 314159 playing seed 8086 |
| FAM-16.19 | `evaluation.build_pool` | four invented versions (`kestrel`, `bramble`, `thistle`, `quarry`) at M = 5 |
| FAM-16.20 | `evaluation.pool_members` | the `kestrel`/`bramble` membership read back, versions in lineage order |
| FAM-16.21 | `evaluation.offer` | a sixth version (`osprey`) offered into the unfrozen `kestrel`..`marlin` window |
| FAM-16.22 | `evaluation.opponent` | three invented versions, eight invented seeds |
| FAM-16.23 | `evaluation.match` | 23 hands at table seed 40961, a 61-wide learner against the oracle |
| FAM-16.24 | `evaluation.matrix` | the battery's own membership: `kestrel` plus one invented variant, K = 5 |
| FAM-16.25 | `evaluation.rating` | the fitted rating of that invented table |
| FAM-16.26 | `evaluation.policy_from` | the 61-wide checkpoint at seed 8086, played on seed 4711 |
| FAM-16.27 | `evaluation.report` | R7's report over the invented table, run at seed 6174 for 60 hands |
| FAM-16.28 | `training.rung` | the unregistered name `R7-bottleneck` |
| FAM-16.29 | `training.run` | the seventh rung at seed 131 for 60 hands |
| FAM-16.30 | `training.fairness` | the seventh rung's own `deep-sparse` / `wide-sparse` pair |
| FAM-16.31 | `training.checkpoints` | the shipped index read against the battery's own `kestrel`/`bramble` artefacts, and the shipped set confined to the repository |
| FAM-16.32 | `harness.drive` | the case `fam16-32-blind`, a seed 424242 hand |
| FAM-16.33 | `harness.fixtures` | a scratch file `fam16-33-invented.txt` the fixture must host |
| FAM-16.34 | `harness.factory` | a 48-wide, 4-deep learner at seed 99991 |
| FAM-16.35 | `harness.seam` | the invented labels `echo-legal` and `seeded-legal`, on seed 314159's hand |
| FAM-16.36 | `harness.expect` | an invented observed value, judged under a kind `fixtures()` lists; an invented kind refused by name |
| FAM-16.37 | `harness.timings` | the clock of a seed 90210 case driven through the driver |

The twelve `fixed` rows are exempt (`battery.md` §4): the game of D-2, the three baselines
of D-6, the six rungs of brief §2, the league of D-16, the enumerations (encodings, backends,
action vocabulary), the device list and the protocol have one instance each, and it is the
project's own. `features.observation_spec` is one of the twelve because an encoder exists
only by one of the two declared encodings, so no invented instance of it can be built
through the surface (`e2e-surface.md` §5); it is tested in FAM-1 and FAM-2, not blinded.

## Freedoms the cases leave to the implementation

Where `docs/L1` fixes a contract but not a spelling, a case asserts the contract through a
tolerant reader rather than a word this battery invented:

- an evidence family is recognised by its `protocol.md` §1 name, with `-`, `_` and spaces
  treated alike (`_surface.has_family`);
- a refusal may raise or return a failure record, and its class is free
  (`_surface.refusal_text`); a league refusal must name what it refused, and the reader
  accepts any wording that names the family, the pool rule or the member;
- a record's nesting is free: a cell is read through `records.md` §9's own keys
  (`_records.cell_*`), a matrix through §10's (`_records.matrix_*`), a rating through §11's
  (`_records.rating_*`), a pool through §8's (`_records.pool_*`); keys are matched with
  hyphens, underscores and spaces alike;
- a `members` or `cells` container may be a sequence or a mapping, so a case that doctors a
  table to see it refused goes through `_records.drop_matrix_member`,
  `_records.rename_matrix_member` and `_records.set_declared` — written against the
  container it finds, never against position zero, which a mapping does not have;
- the direction container may be a sequence or a mapping keyed by member, and a seat split
  may be keyed by seat or by button (`_surface.cell_directions`, `_surface.seat_split`);
- a pool's id is read from the pool record, from an `id` inside a pool-shaped mapping, or
  from a plain `pool: "<id>"`; a member's id is never taken for the pool's
  (`_surface.pool_identity`, `_records.pool_id`);
- the league may declare M under `m`, `max_versions`, `window size` or any key naming the
  bound, and the cell count for a membership as a callable, a mapping keyed by K, or an
  explicit row (`_surface.bound_numbers`, `_records.cells_for`);
- a table seed is read from a key naming it, else from a bare seed key;
- a run record's `checkpoints` entry is read on its own — the retained snapshots plus the
  final model per variant per seed (`records.md` §12) — and never by walking the record,
  where a pool member's own `path` would be counted twice (`_records.checkpoint_paths_of`);
  the count is asserted relative to M and to the run's own variant × seed pairs
  (`_records.checkpoint_span`), never to one instance's literal number;
- a cost record is read structurally: the hands counted, the seconds per hand, the
  throughput and the wall clock are recognised by what their keys name, so
  `seconds_per_hand` and `hands_per_second` — the snake_case these documents use — read as
  the per-hand cost and its reciprocal (`_records.timing_facts`); no case asserts that a
  wall clock was beaten (ASM-15);
- the action vocabulary may be a sequence, a mapping keyed by name, or a mapping keyed by
  the indices themselves; keys and values are read alike (`_surface.action_vocabulary`);
- a seam takes any label — its contract is the policy protocol, not the label — while an
  expectation kind is discovered from `harness.fixtures()` and never invented, so `expect`
  is handed an invented *observed value* for a listed kind, an unlisted kind is asserted to
  be a named failure, and a seam's label is the battery's own (`e2e-surface.md` §3.6,
  `records.md` §14);
- a matrix's `table` label and a pool record's `frozen` flag are **required** keys
  (`records.md` §10, §8) and are read as values — the label is `live` or `full`, the flag
  is a boolean — never by a substring;
- a member's 95% interval is read as the unordered pair whose extent contains the value,
  because `records.md` §11 fixes neither the bounds' key names nor the order they are
  stated in (`_records.rating_interval`): a record that states its bounds high-first is
  the same interval and must not be read inverted;
- an index's listed paths are read **as listed**, duplicates included
  (`_surface.checkpoint_path_listing`), so "lists no artefact twice" is judged against the
  listing the implementation returned; the de-duplicating reader
  (`_surface.checkpoint_paths`) answers questions about artefacts and is never the judge
  of a listing;
- a driver result reports a pass or a named failure in its own words
  (`_surface.verdict`);
- a learner spec carries the four names `e2e-surface.md` §3.3 gives — `backend`,
  `architecture`, `sizes`, `seed` — with the settings `ladder.md` §3 declares
  (`_surface.SurfaceCase.learner_spec`);
- a transition list for `agents.learn` carries both observations, the chosen index, the
  reward, the terminal flag and both legal masks (`_surface.SurfaceCase.transitions`).
