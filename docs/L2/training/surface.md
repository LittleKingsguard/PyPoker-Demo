# training — the callable surface

- **Layer:** L2 · **Module:** `training` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-05
- **Owner of this file:** the surface — the six module-level names of `src/training/`, each with its argument
  contract, its returned record, its refusals and its determinism (D-12, `e2e-surface.md` §1, §3.5)
- **Ceiling:** 225 lines. At the ceiling, split by owner — never append

## 1. Rules that hold of every entry point

Each of the six names is a module-level name of the `training` package, and nothing below one of them is
contract (`e2e-surface.md` §1, brief §5). Six rules are shared and are stated here once (D-12, D-13):

- The six are fixed: L2 refines types, record keys, defaults and error classes and never adds, removes or
  renames an entry point (D-12, `e2e-surface.md` §1, `modules.md` §3).
- An invalid argument is refused by raising an error that names the violated contract; no entry point coerces
  a value, substitutes a default it did not declare, swallows an error or returns part of a record
  (`e2e-surface.md` §2).
- This module never claims a result and never chooses the pool's membership: it declares the lineage it
  inherits and freezes the pool that lineage yields (`module-map.md` §3, D-16, ASM-16).
- No entry point plays a cell, fits a rating or assembles a report: the six call
  `evaluation.protocol|league|build_pool|pool_members|opponent`, `agents.build_learner|act|learn|save`,
  `features.build_encoder|encode|observation_spec|legal_indices|decode_action` and
  `engine.game_config|new_hand|play_hand|payoffs`, and no call outside those four lists (`module-map.md` §2, D-13).
- The global `random` stream is moved by dealing and nothing else: every deal goes through `engine.new_hand`,
  the project's single seeding point, and no call here seeds or advances it (ASM-2, `protocol.md` §4,
  `engine/surface.md` §4).
- Every returned value is plain data — a mapping, a sequence of names or a path — so no record returned here
  exposes a learner, an encoder, a policy or a pool (`e2e-surface.md` §1, D-1). A record carries the keys
  `records.md` marks **required** and, beyond them, only this module's own keys, which no caller may depend on
  (`records.md` §1, D-13).

The module's one job is the rung registry plus the one training loop every rung is a configuration of
(`module-map.md` §1, D-3). The loop itself, the registry's content, the budgets, the notebooks and the
checkpoints are `loop.md`'s.

## 2. `rungs` — the registry (`fixed` row)

- **Signature:** `rungs()`.
- **Arguments:** none: the six rungs are brief §2's, so no parameter can vary them (`e2e-surface.md` §3.5, D-3).
- **Returns:** one mapping keyed by the six rung names in brief §2's order — `R1`, `R2`, `R3`, `R4`, `R5`,
  `R6` — each value the resolved configuration §3 returns, so the registry is read one way and not two
  (`ladder.md` §2, D-3).
- **Refusals:** none; it has no argument.
- **Determinism and ordering:** two calls return equal records in that order, and the order is never rearranged
  without an L0 decision (D-2, D-3, `ladder.md` §2). The registry's content — each rung's axis, variants,
  primary, `carried_from` and pool — is `loop.md` §1's table and is data, not a code path (D-3).

## 3. `rung` — one resolved configuration (`general` row)

- **Signature:** `rung(name)`.
- **Arguments:** one rung name, a string, one of the six `rungs()` declares.
- **Returns:** one resolved configuration in `ladder.md` §3's schema — `name`, `axis`, `carried_from`
  (`None` for R1, the previous rung's primary variant for R2–R6), `primary`, `variants` (one or two
  `records.md` §2 entries) and `pool` — plus this module's own keys, which `loop.md` §2 lists. The `pool` entry
  is the declaration `run` freezes: the inherited `lineage`, the bound `m`, `frozen`, the `members` (the
  version window, `records.md` §7 records in lineage order) and the `id` every arm's run record carries
  (`ladder.md` §3, `records.md` §8).
- **Behaviour:** resolving is not training: it builds no learner, plays no hand and writes nothing (D-3). The
  window is read from the shipped index §7 returns, and a lineage checkpoint the repository does not carry
  leaves the window short, so the pool holds the baselines and whatever versions are present
  (`protocol.md` §5, `league.md` §2).
- **Refusals:** a name the registry does not carry, naming it — and never resolving it as a configuration,
  because a configuration reaches the loop through `run` and through no other entry point (`e2e-surface.md` §2,
  `ladder.md` §3, `battery.md` §3 FAM-15, FAM-16).
- **Determinism:** one name resolves one configuration. The declared `pool.id` is the id the run record will
  carry, because it is the read-back `id` of the membership through `evaluation.pool_members`
  (`ladder.md` §3, `records.md` §8, `evaluation/surface.md` §6).

## 4. `run` — the one loop's record (`general` row)

- **Signature:** `run(rung, seeds=None, budget=None, device=None)`.
- **Arguments:**
  - `rung` — a rung name, **or** a configuration written to `ladder.md` §3's schema; the second form is how a
    configuration in no registry reaches the same loop and is the whole of D-3's claim (D-3, `ladder.md` §1).
  - `seeds` — the seed set, a non-empty sequence of distinct integers; omitted, it is the resolved
    configuration's declared `seeds` (the three of `protocol.md` §2).
  - `budget` — hands per variant per seed, a positive integer; omitted, the configuration's declared `samples`.
  - `device` — a name `devices()` lists; omitted, that catalogue's `default` (D-8).
  - An omitted argument *is* the declared value and the record states what was used; there is no other default
    (`records.md` §12, `e2e-surface.md` §2).
- **Returns:** `records.md` §12's run record, read under the keys below.
- **Behaviour:** it runs the one loop of `loop.md` §3 — freeze the pool, then per variant and per seed train,
  snapshot and save — and returns what happened; it measures no cell, fits no rating and states no table
  position (D-3, D-16, `module-map.md` §3).
- **Refusals:** an unknown rung name, naming it; a configuration missing one of `ladder.md` §3's keys the run
  reads, naming the key; a variant count other than one or two, naming it (D-3, `ladder.md` §2); a `backend`,
  `encoding` or `architecture.kind` that `agents.learners()` and `features.encodings()` do not declare, naming
  it (D-3, `agents/surface.md` §3, `features/surface.md` §3); a seed set that is empty, repeats a seed or holds
  a non-integer (ASM-2); a budget that is not a positive integer, or one below ten hands, because ten equally
  spaced snapshots need ten hands (ASM-18, `ladder.md` §6); a device `devices()` does not list, naming it
  (D-8); a `pool` declaration `evaluation.build_pool` refuses, surfaced by name and never repaired
  (`e2e-surface.md` §2, `module-map.md` §2).
- **Determinism:** one `(configuration, seed set, budget, pool membership)` gives one record twice — the same
  curves, the same pool id and the same checkpoint paths — because the deal seeds are a function of the run
  seed and the hand index, the learner's generator is seeded from the run seed, and the pool is frozen before
  the first hand (`e2e-surface.md` §2, `protocol.md` §4, `loop.md` §3, `battery.md` §3 FAM-4). A different seed
  set or a different membership gives a different record (FAM-4.8, FAM-4.9).

The run record's keys (`records.md` §12's **required** set is exactly these ten):

| Key | Content |
|---|---|
| `rung` | the rung name, or an unregistered configuration's own `name` (`records.md` §12, `ladder.md` §3) |
| `curves` | per variant and per seed: the sample axis (the snapshot steps), at least one learning signal from `agents.learn` — its `td_error` — and the spread across seeds, zero when the set holds one seed (`protocol.md` §1, D-6, `loop.md` §3) |
| `pool` | the frozen pool trained against: `id` (the configuration's declared id, so both arms of a pair carry one), `m`, `frozen`, the ordered members with lineage and the three pinned baselines — the `records.md` §8 record `pool_members` returned, under a nested key, beside the declared id (D-16, ASM-16, `records.md` §8) |
| `checkpoints` | per variant and per seed: the retained snapshots — the last M of the ten — and that pair's final model, as the paths `agents.save` wrote; the five earlier snapshots are intra-run and are not named (ASM-18, `protocol.md` §5) |
| `seeds`, `budget`, `device` | what the run actually used, after the defaults above (D-6, `protocol.md` §2, §6) |
| `params` | per variant, the declared parameter budget and its ±2% bound (ASM-10): a run measures no capacity, because `agents.param_count` is not among the four `agents` calls this module is granted (`module-map.md` §2, `records.md` §12) |
| `table` | the configuration's declared table budget the variant's row is measured at, `live` or `full`; a configuration that declares none is recorded at `live`, the budget a talk produces (`ladder.md` §3, `league.md` §6) |
| `timings` | the cost record: hands played, wall clock, seconds per hand and the throughput, per variant and per seed — the facts `harness.timings` reports, measured by the run itself because no `harness` edge reaches this module (`records.md` §12, `e2e-surface.md` §3.6, D-7, ASM-15) |
| `variants` | this module's own: each variant's backend, encoding, architecture, declared samples and the snapshot interval it used |

## 5. `fairness` — what a pair holds constant (`general` row)

- **Signature:** `fairness(left, right)`.
- **Arguments:** two resolved rung configurations, or two variant entries (`e2e-surface.md` §3.5). A mapping
  carrying `variants` is a configuration; one carrying `architecture` and no `variants` is an entry, and its
  name is `records.md` §2's (D-3, `records.md` §2). A rung *name* is not a configuration — `rung` resolves it
  first (`e2e-surface.md` §3.5). Two sides of different kinds are refused, and so is anything else, naming
  what was expected.
- **Returns:** one mapping read under these keys (D-3, `ladder.md` §4):
  - `pair` — the two sides by name: a configuration's `primary` variant, because the primary is the lineage the
    next rung inherits, or an entry's own `name` (`ladder.md` §2, D-16).
  - `axis` — `{of, differs, declared}`: the axis the pair is named for, the field names that differ, and the axis the
    configuration carrying it declares, quoted from `ladder.md` §2's `axis` key. For two configurations, `of` is read
    from the **later** one's declared axis — the rung that varies against the lineage — so a pair whose two primaries
    declare one stack still names the axis the rung is for; for two entries it is the one axis the difference falls
    in, and a pair that differs on nothing reports `differs: []` and invents no axis (D-3, `ladder.md` §2, D-6).
  - `constants` — the `ladder.md` §4 list under the key names of `loop.md` §4.
  - `pool` — `m`, `frozen`, the three `baselines`, each arm's declared `id`, `same` (the one id both declare,
    or `None`), and, for the parity pair, the membership the same-work check is played against
    (D-16, ASM-16, `loop.md` §4).
- **The five axes.** A pair is compared on exactly these dimensions; the architecture *kind* contributes only
  through the representation family it consumes, because `dense`, `deep` and `residual` are one stack under
  different settings (`agents/surface.md` §3, D-3):

| Axis | The compared value |
|---|---|
| `backend` | variant `backend` (D-7) |
| `encoding` | variant `encoding`, together with the `observation` family of `architecture.kind` (D-3) |
| `architecture` | architecture `width` and `depth` (D-3) |
| `connectivity` | architecture `sparsity` (D-3) |
| `residual` | architecture `residual` (D-3) |

- **A differing pair is refused when its differences are not one axis**, naming every axis it differs on, because the
  one thing a reportable comparison may differ on is the axis it declares (D-3, D-6, `ladder.md` §4). A pair of two
  variants declaring different pools is refused too, naming both, because both arms of a pair train against one frozen
  pool (ASM-16, `ladder.md` §4).
- **Refusals:** a side that is neither a configuration nor a variant entry, naming it; two sides of different kinds; a
  configuration missing a key the comparison reads, naming it; more than one differing axis, naming them; two variants
  of one configuration declaring different pool ids (D-3, ASM-16).
- **Determinism:** one pair gives one record, and `fairness` plays no hand, builds no learner, writes nothing
  and moves no stream (D-3, ASM-2, `battery.md` §3 FAM-3, FAM-15). It reports what it holds and what differs;
  it never asserts that a pair is fair, because a non-reportable pair never gets that far (D-3, D-6).

## 6. `devices` — what this platform offers (`fixed` row)

- **Signature:** `devices()`.
- **Arguments:** none: the platform is not a parameter (D-8).
- **Returns:** one mapping read under these keys — `available`, the device names `run` accepts and always
  containing `cpu`; `default`, the one a run uses when none is named; and `gpu`, whether the platform exposes
  one and the name it goes by, with the reason it is unavailable where the sandbox denies it (D-8,
  `protocol.md` §6).
- **Rules:** `cpu` is always available and every rung and both table budgets run on it (D-8, ASM-15). A GPU is
  reported available only when the device actually opens: a run started by this workflow is CPU-bound because
  the file sandbox denies the device nodes, and a GPU run is the user's, started outside it (D-8,
  `strata/platform.md`, `protocol.md` §6).
- **Refusals:** none; it has no argument.
- **Determinism:** two calls on one platform agree, and the answer depends on the platform and not on the
  caller; a run records the device it used, so a GPU run and a CPU run are never confused (D-8,
  `protocol.md` §6).

## 7. `checkpoints` — the shipped index (`general` row)

- **Signature:** `checkpoints()`.
- **Arguments:** none: the shipped set is the repository's (`protocol.md` §5).
- **Returns:** the shipped index — a mapping naming, per rung and variant and seed, that variant's final model,
  and per rung the retained versions of the window its successor inherits. Every path it names is an artefact
  inside the repository that `evaluation.policy_from` loads, and every artefact appears once
  (`protocol.md` §5, `records.md` §7, `evaluation/surface.md` §12). What ships and how the window is declared
  is `loop.md` §7.
- **Behaviour:** the index is declared data over `checkpoints/`, never a directory scan, so a scratch file the
  battery wrote is not a shipped artefact and is never listed (`protocol.md` §5, `battery.md` §3 FAM-12,
  FAM-16).
- **Refusals:** none; it has no argument. An artefact the index names and the repository does not carry is a
  defect of the shipped set, not a silent omission — the index is not filtered to what happens to be on disk
  (`protocol.md` §5, `records.md` §12).
- **Determinism and ordering:** two calls return equal listings in one declared order, and no artefact is
  listed twice, because a variant's final model and the window's retained versions never share a file
  (ASM-18, `protocol.md` §5, `battery.md` §3 FAM-12).
