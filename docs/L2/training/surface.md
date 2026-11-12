# training — the callable surface

- **Layer:** L2 · **Module:** `training` · **Unit:** phase1 · **Rev:** 13 · **Date:** 2026-11-11
- **Owner of this file:** the surface — the six module-level names of `src/training/`, each with its argument
  contract, its returned record, its refusals and its determinism (D-12, `e2e-surface.md` §1, §3.5)
- **Rev 3:** §4's `checkpoints` row states where a run writes and how it spells a written path (`write-root.md`, split out
  because this file reached its ceiling). **Rev 4:** §6's probe rule is the sibling `devices.md`. **Rev 5:** §4's and §5's
  refusals include the declarations a run would discard (`declarations.md` §1–§4). **Rev 7:** the rule reaches §4's `pool` row and §7 (D-19). **Rev 8:** D-20 reaches §4's `pool`, `variants` and `rules` rows, §5's seventh axis, §7's index entry and `declarations.md`'s utility check — `utility.md`. **Rev 9:** D-21 reaches §1's granted calls, §3.1's id, §4's `pool` row, refusals and `baselines` block — the pinned set read off the catalogue's flag, and one row per baseline the pool holds. **Rev 10:** D-29 reaches §1's granted calls (`agents.as_policy` at `exploration="off"`), §4's `game` and `greedy` rows with the `UnknownShape` and `GreedyPassRefused` refusals, §4.1's shape-aware header and §5's `shape` constant — the pass is `greedy.md`'s, the bound `declarations.md` §5's (D-29, ASM-38, D-28). **Rev 11:** D-33's third shape reaches §1's restated tables, §4's `game` row and §4.2 — three names, three descriptor counts and three history capacities, the seat rotation `index % seats`, the shape's own record bound, and no table row from a shape whose seat count is not two (`seats.md` §2–§5, `shapes.md` §8, ASM-42, ASM-43, D-33). **Rev 12:** D-36 reaches §4's `greedy` row and §4's refusals — a **budget is never refused for the pass**: a run above the pass's 2,000-hand bound completes, and its pass plays a 2,000-hand **sample of the run's own hands**, the run's first `hands` hands at the run's seed, so `budget`, `hands` and `seed` state the sample exactly and a third party replays it; a **pass request** above the bound is still `GreedyPassRefused`, naming the count and the bound (`sizing.md` §4, `records.md` §15, `greedy.md` §1, §4, ASM-38). **Rev 13:** D-43 reaches §4's `variants` and sets rows and §5's eighth axis — a variant may declare a `counterfactual` member of the **third** catalogue, the run forwards it only when it is named and records it in the `variants` row and the `counterfactuals` set **only** when it is not the catalogue's first, so a run declaring nothing writes neither and its record keeps the shape a capture took; the member is an axis a pair may differ on and never a held setting (`counterfactual.md` §6, §9, `declarations.md` §4, D-43)
- **Ceiling:** 225 lines. At the ceiling, split by owner — never append

## 1. Rules that hold of every entry point

Each of the six names is a module-level name of the `training` package, and nothing below one of them is
contract (`e2e-surface.md` §1, brief §5). Six rules are shared and are stated here once (D-12, D-13):

- The six are fixed: L2 refines types, record keys, defaults and error classes and never adds, removes or renames
  an entry point (D-12, `e2e-surface.md` §1, `modules.md` §3).
- An invalid argument is refused by raising an error that names the violated contract; no entry point coerces a
  value, substitutes an undeclared default, swallows an error or returns part of a record (`e2e-surface.md` §2).
- This module never claims a result and never chooses the pool's membership: it declares the lineage it inherits
  and freezes the pool that lineage yields (`module-map.md` §3, D-16, ASM-16).
- No entry point plays a cell, fits a rating or assembles a report: the six call
  `evaluation.protocol|league|build_pool|pool_members|opponent`,
  `agents.build_learner|act|learn|save|learners`, plus `agents.as_policy` at
  `exploration="off"` for the one decision stream a run retains (`greedy.md` §1–§2, D-29, ASM-38),
  `features.build_encoder|encode|observation_spec|legal_indices|decode_action` and
  `engine.game_config|new_hand|play_hand|payoffs`, and no call outside those four lists (`module-map.md` §2, D-13). The
  pinned baselines are `evaluation.league()`'s `baselines` — the catalogue's `anchor: True` members — read through a
  granted call, so this module copies no literal set of three and builds no baseline policy (`folders.md` §4, ASM-32, D-21).
  `engine.game_config` and `features.decode_action` take the **run's own shape**, and `game_shapes` and
  `features.action_space` are granted to nobody: the three declared shapes' names, order, descriptor counts and history
  capacities are restated in `src/training/declarations.py` and joined to the catalogues by `tests/integration/training/`
  (§4.2, `shapes.md` §2, §8, ASM-42, D-33).
- The global `random` stream is moved by dealing and nothing else: every deal goes through `engine.new_hand`, the
  project's single seeding point, and no call here seeds or advances it (ASM-2, `protocol.md` §4).
- Every returned value is plain data — a mapping, a sequence of names or a path — so no record returned here
  exposes a learner, an encoder, a policy or a pool (`e2e-surface.md` §1, D-1). A record carries the keys
  `records.md` marks **required** and, beyond them, only this module's own keys (`records.md` §1, D-13).

Its one job is the registry plus the one loop every rung configures (`module-map.md` §1, D-3); the rest is `loop.md`'s.

## 2. `rungs` — the registry (`fixed` row), and §3 `rung` — one resolved configuration (`general` row)

**Both are `resolve.md` §2–§3's**, split out at this file's ceiling with the numbering kept: `rungs()`'s content and
order, `rung(name)`'s arguments, returned configuration, refusals and determinism, and §3.1's one rule about a pool's
id — that a rung's declared id *is* the digest of the membership, that a configuration in no registry carries its own,
and that the shape is not in the digest (`ladder.md` §2–§3, `records.md` §8, ASM-32, D-29). No registry row declares a
`game`: every rung is the catalogue's first shape and a configuration naming another reaches the same loop through `run`
(`shapes.md` §1, §3, D-29).

## 4. `run` — the one loop's record (`general` row)

- **Signature:** `run(rung, seeds=None, budget=None, device=None)`.
- **Arguments:**
  - `rung` — a rung name, **or** a configuration written to `ladder.md` §3's schema; the second form is how a
    configuration in no registry reaches the same loop and is the whole of D-3's claim (D-3, `ladder.md` §1).
  - `seeds` — the seed set, a non-empty sequence of distinct integers; omitted, it is the resolved
    configuration's declared `seeds` (the three of `protocol.md` §2).
  - `budget` — hands per variant per seed, a positive integer; omitted, the configuration's declared `samples`.
  - `device` — a name `devices()` lists; omitted, that catalogue's `default` (D-8).
  - `game` — not an argument: the **shape** is the configuration's own `game` key (`records.md` §2), read at the
    configuration and then at its first entry, absence meaning the catalogue's first shape (`shapes.md` §3, D-29).
  - An omitted argument *is* the declared value and the record states what was used; there is no other default
    (`records.md` §12, `e2e-surface.md` §2).
- **Returns:** `records.md` §12's run record, read under the keys below.
- **Behaviour:** it runs the one loop of `loop.md` §3 — freeze the pool, then per variant and per seed train,
  snapshot and save — and returns what happened; it measures no cell, fits no rating and states no table
  position (D-3, D-16, `module-map.md` §3). A run on the six-seat shape is complete and is **not** reportable: its
  curves, pool, ten snapshots, final model and `greedy` block are written, and no matrix, rating or report can be
  produced from it, because the pairwise instrument refuses a shape whose seat count is not two (`seats.md` §5, D-33).
- **Refusals:** an unknown rung name; a configuration missing a key the run reads from `ladder.md` §3; a variant
  count other than one or two (D-3, `ladder.md` §2); a `backend`, `encoding` or `architecture.kind` that
  `agents.learners()` and `features.encodings()` do not declare (D-3, `agents/surface.md` §3, `features/surface.md` §3);
  a seed set that is empty, repeats a seed or holds a non-integer (ASM-2); a budget that is not a positive integer or
  is below ten hands (ASM-18, `ladder.md` §6); a device `devices()` does not list (D-8); a `pool` declaration
  `evaluation.build_pool` refuses (`m` above M, a bad chain, an uncatalogued baseline name) — surfaced, never repaired
  (`e2e-surface.md` §2, ASM-32, D-21); a `game` outside the declared shapes is `UnknownShape` naming it and both names
  at either level (`shapes.md` §2, D-29); **no run is refused for a budget** — one above 2,000 hands completes and its
  pass samples the run's own first 2,000 — while the pass's own bounds are `greedy.md` §4's: a **pass request** that is
  not a positive integer or exceeds 2,000 is `GreedyPassRefused` naming it and the bound, and the shape's record bound is
  refused as the pass accumulates (`records.md` §15, ASM-38, ASM-42, D-36); and a `hyper`, `learning_rule` or
  `snapshot_every` the run would discard, and a pair declaring two values for one held setting (ASM-7).
- **Determinism:** one `(configuration, seed set, budget, pool membership)` gives one record twice — the same
  curves, the same pool id and the same checkpoint paths — because the deal seeds are a function of the run
  seed and the hand index, the learner's generator is seeded from the run seed, and the pool is frozen before
  the first hand(`e2e-surface.md` §2, `protocol.md` §4, `loop.md` §3, FAM-4); another seed set or membership differs.

The run record's keys (`records.md` §12's **required** set, D-19's rule set included):

| Key | Content |
|---|---|
| `rung` | the rung name, or an unregistered configuration's own `name` (`records.md` §12, `ladder.md` §3) |
| `game` | the **shape** the run played: the configuration's `game`, or the catalogue's first shape when it names none — so a record names a shape it measured and `evaluation.report` can hold a run, a pool and a matrix to one (`records.md` §12, `shapes.md` §3, `protocol.md` §1, D-29) — save that a shape whose **seat count is not two** is refused by `evaluation.match`, `matrix`, `rating` and `report`, and this module calls none of them, so only a two-seat shape's record becomes a table row (`seats.md` §5, D-22, D-33) |
| `greedy` | `records.md` §15's pass, keyed per variant and per seed exactly as `curves` is: `mode` (`off`), `seed`, `hands`, `net_chips` and the ordered `decisions` — **the one decision stream a run retains**, since a log of the behaviour policy is the defect D-28 records as fatal. `hands` is the **sample's** count and not the run's budget: the budget when it is at most 2,000 hands and 2,000 otherwise, the sample being the run's own **first `hands` hands** at the run's seed, so the record's own `budget`, `hands` and `seed` state it exactly and a third party replays it hand for hand (D-36, `sizing.md` §4, §7, ASM-38, `greedy.md` §1–§3) |
| `curves` | per variant and per seed: the sample axis (the snapshot steps), at least one learning signal from `agents.learn` — its `td_error` — and the spread across seeds, zero when the set holds one seed (`protocol.md` §1, D-6, `loop.md` §3); the spread is one array per variant and point, repeated in each of that variant's seed entries and never a per-seed measurement (`curves.md` §4, `evidence.md` §4) |
| `pool` | the frozen pool trained against: `id` (the configuration's declared id, so both arms of a pair carry one), `m`, `frozen`, `game` — the one shape the pool is on (`records.md` §8) — the ordered members with lineage and the pool's **pinned** baselines (the anchor three, then any folder the declaration named) — the `records.md` §8 record `pool_members` returned, under a nested key, beside the declared id — and `rules` and `utilities`, the distinct rules and utilities those version members declare (`records.md` §8, §12, `rules.md` §7, `utility.md` §3, D-16, ASM-16, ASM-32, D-19, D-20, D-21) |
| `checkpoints` | per variant and per seed: the retained snapshots — the last M of the ten — and that pair's final model, as the paths `agents.save` wrote, each spelled **repository-relative** with POSIX separators when the artefact is inside the repository root and **unchanged** when it is outside, because a run may be pointed at another write root (`docs/L3/training/checkpoints.md` §2, `protocol.md` §5, `write-root.md` §1, §5); the five earlier snapshots are intra-run and are not named (ASM-18) |
| `seeds`, `budget`, `device` | what the run actually used, after the defaults above (D-6, `protocol.md` §2, §6) |
| `params` | per variant, the declared parameter budget and its ±2% bound (ASM-10): a run measures no capacity, because `agents.param_count` is not among the four `agents` calls this module is granted (`module-map.md` §2, `records.md` §12) |
| `table` | the configuration's declared table budget the variant's row is measured at, `live` or `full`; a configuration that declares none is recorded at `live`, the budget a talk produces (`ladder.md` §3, `league.md` §6) |
| `timings` | the cost record: hands played, wall clock, seconds per hand and the throughput, per variant and per seed — the facts `harness.timings` reports, measured by the run itself because no `harness` edge reaches this module (`records.md` §12, `e2e-surface.md` §3.6, D-7, ASM-15) |
| `variants` | this module's own: each variant's backend, encoding, architecture, **its learning rule and its utility**, its `counterfactual` member **only when it is not the catalogue's first**, declared samples and the snapshot interval it used (`records.md` §12, `rules.md` §7, `utility.md` §3, `counterfactual.md` §6, D-20, D-43) |
| `rules`, `utilities` | the two sets the run declared and trained, so a configuration whose two arms name two estimators or two objectives says so (`records.md` §12, `rules.md` §7, `utility.md` §3, D-19, D-20) — and, on the third axis, the `counterfactuals` set, present **only when at least one variant declares a member that is not the catalogue's first** (`counterfactual.md` §6, §9, D-43) |

### 4.1 The three further keys a complete report needs (Rev 2, measured)

`evaluation.report` judges a record against **seven** families, each a key of that record, and the battery withholds
each in turn (`battery.md` §3 FAM-11.2–11.8). A run is the only producer of three of them, and states them beside the
keys above without claiming what it did not measure (D-6):

- `header` — `protocol.md` §1's nine items, all from granted calls or this record: the game (`game_config` of the **run's
  own shape**), the vocabulary (`decode_action` over that shape's indices — three or six), the **declared** parameter
  budget per variant and the baselines' declared `0`, the
  sample budget, the cell size `evaluation.league` declares for this `table`, the seed set, the table seed, the device
  and the checkpoint paths, spelled as the record's own `checkpoints` key spells them (`write-root.md` §5). D-5 forbids
  a notebook importing `engine` or `features` (`ladder.md` §7), so this is the only route by which the game and the
  vocabulary reach a report; a declared budget is not the capacity a cell records (ASM-10, `records.md` §9). The nine
  items do not grow: the shape is the record's top-level `game`, and the report's own tenth key is `evaluation`'s
  (`report.md` §2, `shapes.md` §6, D-29).- `baselines` — one declared row per baseline the frozen pool **actually holds**, read off `pool_members`' own members and
  never a count of three: `pinned: true`, `measured: false`, the league's cell size for each, and a declared `0` for each of
  those names in the `header`'s parameter counts — the rows are the matrix's to fill and a run plays no cell (D-16, `protocol.md` §3, ASM-32, D-21).
- `axis row` — `n/a, single variant` for a one-variant rung, explicit and never a blank; a two-variant rung omits it. `matrix` and `rating` are the caller's to attach.

### 4.2 The vocabularies a run checks against (Rev 6, Rev 10)

A `backend`, `encoding` or `architecture.kind` is refused against **this module's own declaration** of the two
backends, two encodings and seven kinds (`loop.md` §2, `docs/L3/agents/architecture.md` §1): `features.encodings()` is
not among the calls `module-map.md` §2 grants, so a run names the offending value and `features.build_encoder` and
`agents.build_learner` remain the authority, refusing it in turn. A `learning_rule` and a `utility` are the
exceptions: `agents.learners()` **is** granted, so the catalogue either is refused against is the one that call publishes (`declarations.md` §2, `utility.md` §1).

A `game` is refused against a **third restated table**, for the same reason: `engine.game_shapes()` is granted to
nobody and `features.action_space` is not this module's (`module-map.md` §2), so `src/training/declarations.py`
declares the **three** shapes' names in the catalogue's order, the first as the default, each one's descriptor count and
each one's history capacity — a capacity being the catalogue row's — and `tests/integration/training/` holds those
tables equal, name by name, count by count and capacity by capacity, to `engine.game_shapes()` and
`features.action_space`. Every descriptor a run reports comes back from `features.decode_action(index, shape=...)`, so
the table carries a count and never a spelling, and a seat count is in none of them (`shapes.md` §2, §4, §8, `seats.md`
§2–§3, `sizing.md` §3, ASM-42, ASM-44, D-13, D-29, D-33).

## 5. `fairness` — what a pair holds constant (`general` row)

- **Signature:** `fairness(left, right)`.
- **Arguments:** two resolved rung configurations, or two variant entries (`e2e-surface.md` §3.5). A mapping
  carrying `variants` is a configuration; one carrying `architecture` and no `variants` is an entry, and its
  name is `records.md` §2's (D-3, `records.md` §2). A rung *name* is not a configuration — `rung` resolves it
  first. Two sides of different kinds are refused, and so is anything else, naming what was expected.
- **Returns:** one mapping read under these keys (D-3, `ladder.md` §4):
  - `pair` — the two sides by name: a configuration's `primary` variant, because the primary is the lineage the
    next rung inherits, or an entry's own `name` (`ladder.md` §2, D-16).
  - `axis` — `{of, differs, declared}`: the axis the pair is named for, the field names that differ, and the axis the
    configuration carrying it declares, quoted from `ladder.md` §2's `axis` key. For two configurations, `of` is read
    from the **later** one's declared axis — the rung that varies against the lineage — so a pair whose two primaries
    declare one stack still names the axis the rung is for; for two entries it is the one axis the difference falls
    in, and a pair that differs on nothing reports `differs: []` and invents no axis (D-3, `ladder.md` §2, D-6).
  - `constants` — the `ladder.md` §4 list under the key names of `loop.md` §4, the **sets** of rules and of utilities
    the two sides declare, never one side's, and a `reward` row stating each side's utility's reward (`rules.md` §8,
    `utility.md` §5, D-19, D-20) — and **no row** for the counterfactual member, which is an axis a pair differs on and
    never a constant (`counterfactual.md` §6, D-43). Its first row is `shape`, the one shape both sides name, which is
    what its `game` and `action vocabulary` rows read and what makes a pair of two shapes no pair (`shapes.md` §1–§2, §6, `loop.md` §4, D-29).
  - `pool` — `m`, `frozen`, the catalogue's `baselines` either side's pool holds (the anchors in every pool, plus any declared
    folder), each arm's declared `id`, `same` (the one id both declare, or `None`), and, for the parity pair, the membership the same-work check is played against (ASM-16, ASM-32, `loop.md` §4, D-21).
- **The eight axes.** A pair is compared on exactly these dimensions; the architecture *kind* contributes only
  through the representation family it consumes, because `dense`, `deep` and `residual` are one stack under
  different settings (`agents/surface.md` §3, D-3). The eighth, `counterfactual`, is an axis and never a held setting (`counterfactual.md` §6, D-43):

| Axis | The compared value |
|---|---|
| `backend` | variant `backend` (D-7) |
| `encoding` | variant `encoding`, together with the `observation` family of `architecture.kind` (D-3) |
| `architecture` | architecture `width` and `depth` (D-3) |
| `connectivity` | architecture `sparsity` (D-3) |
| `residual` | architecture `residual` (D-3) |
| `rule` | variant `learning_rule` — an axis a pair may differ on, since D-19 makes the estimator a parameter (`rules.md` §8, D-19) |
| `utility` | variant `utility` — the seventh axis, and its token **and** field are one word, unlike `rule`/`learning_rule` (`utility.md` §5, `utilities.md` §8, D-20); the eighth, `counterfactual`, is a `variants` row's member on the same terms, and it is an axis a pair may differ on and never one of §4's held settings (`counterfactual.md` §6, `declarations.md` §4, D-43) |

- **A differing pair is refused when its differences are not one axis**, naming every axis it differs on, because the
  one thing a reportable comparison may differ on is the axis it declares (D-3, D-6, `ladder.md` §4). A pair of two
  variants declaring different pools is refused too, naming both, because both arms of a pair train against one frozen
  pool (ASM-16, `ladder.md` §4); and one whose two sides name **two shapes** is refused first, naming both shapes,
  because a shape is a property of a configuration and never a rung's axis (`shapes.md` §1, §6, D-29).

### 5.1 The axis rule the matched capacities force (Rev 2, measured)

`architecture` — width and depth — is compared **only between two sides that agree on the representation family and on
`sparsity`**. Where they differ on either, the width is the capacity match's compensation and belongs to the axis that
caused it: ASM-10 requires a `sparse` arm wider than its dense mate, its trunk term `D·(k + W)` shrinking with `s`, and a
token encoding to sit at a different width than a 203-wide dense one. Counting that width again would refuse R2–R3
(`encoding` and `architecture`) and R5's own pair (`architecture` and `connectivity`) — both rungs the ladder exists to
report (`docs/L3/agents/architecture.md` §5). With this rule the eight reportable pairs differ on one axis exactly:
R1–R2 `backend`; R2–R3 `encoding`; R3–R4 and R4–R5 on nothing, the later rung's declared axis still being the axis it is
for; R5–R6 `residual`; R4's, R5's and R6's own pairs `architecture`, `connectivity`, `residual`.

- **Refusals:** a side that is neither a configuration nor a variant entry; two sides of different kinds; a
  configuration missing a key the comparison reads; more than one differing axis, naming them; two variants of one
  configuration declaring different pool ids (D-3, ASM-16), or different `hyper` blocks — a constant one side only
  declares is no constant (`declarations.md` §3, ASM-7); a differing `learning_rule`, `utility` or `counterfactual` is the pair's axis instead (D-19, D-20, D-43).
- **Determinism:** one pair gives one record, and `fairness` plays no hand, builds no learner, writes nothing
  and moves no stream (D-3, ASM-2, `battery.md` §3 FAM-3, FAM-15). It reports what it holds and what differs;
  it never asserts that a pair is fair, because a non-reportable pair never gets that far (D-3, D-6, `rules.md` §8).

## 6. `devices` — what this platform offers (`fixed` row)

- **Signature:** `devices()`.
- **Arguments:** none: the platform is not a parameter (D-8).
- **Returns:** one mapping read under these keys — `available`, the device names `run` accepts, and always containing
  `cpu`; `default`, the one a run uses when none is named; and `gpu`, whether the platform exposes one, its name and the
  reason it is unavailable (D-8, `protocol.md` §6).
- **Rules:** `cpu` is always available and every rung and both table budgets run on it (D-8, ASM-15); a reachable GPU adds
  no name to `available`, which names what `run` accepts and never what the machine has (`docs/L1/gpu.md` §3, D-8). The
  probe, the operation it measures and the vocabulary `gpu.reason` carries are the sibling `devices.md` §1–§2 (Rev 4).
- **Refusals:** none; it has no argument.
- **Determinism:** two calls on one platform agree, and the answer depends on the platform and not on the caller;
  a run records the device it used, so a GPU run and a CPU run are never confused (D-8, `protocol.md` §6).

## 7. `checkpoints` — the shipped index (`general` row)

- **Signature and arguments:** `checkpoints()`, with no argument: the shipped set is the repository's (`protocol.md` §5).
- **Returns:** the shipped index — per rung, variant and seed that variant's final model, and per rung the retained versions of
  the window its successor inherits — where every entry is a `records.md` §7 version record and therefore carries the **rule** it
  was trained under and the **utility** it was trained on (R1's live run ships; its rule is `masked-q-learning` and its containers are read as `net-chips`, `rules.md` §6, `utility.md` §4, ASM-5, D-19, D-20). Every path is an artefact
  inside the repository that `evaluation.policy_from` loads, and every artefact appears once (`protocol.md` §5, `records.md` §7).
- **Behaviour:** declared data over `checkpoints/`, never a directory scan, so a scratch file the battery wrote is not a shipped artefact and is never listed (`battery.md` §3 FAM-12, FAM-16).
- **Refusals:** none. An artefact the index names and the repository does not carry is a defect of the shipped set, not a silent omission — the index is not filtered to what happens to be on disk (`records.md` §12).
- **Determinism and ordering:** two calls return equal listings in one declared order, and no artefact is listed twice, because a final model and the window's retained versions never share a file (ASM-18).
