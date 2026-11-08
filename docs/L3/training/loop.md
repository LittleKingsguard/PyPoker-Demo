# training — the one loop

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-08
- **Owner:** `run()` — the nine steps every rung is a configuration of (§1), the per-pair pass (§2), the run record key by key
  (§3), the sub-records it carries (§4), the arguments and their defaults (§5), the refusals (§6), determinism (§7); Rev 2 refuses
  the declarations the run would not use, at §1 step 1, and reports the configuration's declared `param_budget` (§3–§4)
- **Ceiling:** 190 lines. At the ceiling, split by owner — never append
- **Read with:** `registry.md` §1–§3, `seeds.md` §2–§4, `episode.md` §1–§5, `curves.md` §5, `checkpoints.md` §3–§4,
  `devices.md` §3, `errors.md` §4

## 1. The nine steps (D3)

One pass of `run`, in this order, for any configuration — a registry rung or one written to `ladder.md` §3 and in no design
document (`loop.md` §3, FAM-15.1). Steps 3–8 repeat per variant and per seed; steps 1, 2 and 9 happen once.

1. **Resolve, refusing what the run would discard.** A string goes through `rung(name)` (`registry.md` §5). A mapping is a
   configuration and is used as it stands, refused in this order and always naming the key or the value it saw: the shape and the
   keys it reads (`name`, `variants`, `pool`, `seeds`, `samples`, `device`, `table`) and then the seed set's and budget's values
   (§5, `surface.md` §4); then each entry's declared `backend`, `encoding` and `architecture` (`check_variant`); then the three
   declarations a run would not use — each entry's `hyper` keys, its `learning_rule`, and the `snapshot_every` declared at either
   level (§2) — and, for a two-entry configuration, the eight settings both arms must share; then the pool, at step 2. The `name`
   is what the record's `rung` carries, and no step after this one sees a configuration this one refused.
2. **Freeze the pool before the first hand.** The declaration is `{"members": <config["pool"]["members"] filtered to versions
   whose `path` names a readable file>, "m": config["pool"]["m"], "frozen": config["pool"]["frozen"]}`; it goes to
   `evaluation.build_pool` and `evaluation.pool_members` reads the membership back. The pool is frozen for the whole run: no
   snapshot of this run enters it, and rolling is `evaluation.offer` between runs (D-16, ASM-16, `registry.md` §3).
3. **Build the variant.** `features.build_encoder(entry["encoding"])`, then `features.observation_spec(encoder)` as the
   cross-check: `spec["representation"]` must equal the entry's `encoding`, or the run refuses naming both (`surface.md` §4,
   `features/surface.md` §5). Per seed, `agents.build_learner({"backend", "architecture", "seed", "encoder"})` with the run's
   seed as the learner's own seed (ASM-2, `agents/surface.md` §4, `protocol.md` §4).
4. **Seed the work, not the arm.** Hand *i* of a run at `seed` is dealt at `_deal_seed(seed, i)` and draws its opponent at
   `_opponent_seed(seed, i)`, both of which are functions of the run seed and *i* alone (`seeds.md` §2). The opponent is
   `evaluation.opponent(pool, `_opponent_seed(seed, i)`)` (`evaluation/surface.md` §8, ASM-16).
5. **Play the hand through `engine`.** The learner's seat is `_seat(i)` (`episode.md` §1). The learner's policy is
   `_learner_policy(learner, encoder)` (`episode.md` §2); seats alternate by swapping the two arguments, because seat 0 holds
   the button in every hand (`engine/surface.md` §4, D-2). The call is `engine.play_hand(deal_seed, seat0, seat1)`.
6. **Learn once per hand.** The episode's decisions for the learner's own seat become `records.md` §4 transitions and go to
   `agents.learn` as one batch, in the caller's order, neither sampled nor shuffled (`episode.md` §5, ASM-7). Its `td_error` is
   the hand's learning signal (`curves.md` §3). **A hand in which the learner's seat never acted produces no batch and no
   update** — `learn` refuses an empty sequence — and contributes no signal (`agents/rule.md` §3).
7. **Snapshot every interval.** After hand *i* with `(i + 1) % interval == 0`, and at most ten times, the run makes the
   pair's directory and calls `agents.save(learner, layout._write_path(layout._snapshot_path(...)))`, keeping the path it
   returns (`checkpoints.md` §2, `write-root.md` §1, §5). The interval is `budget // 10`; §2 says why it is not the declared
   `snapshot_every`.
8. **Write the final model.** After the last hand, `agents.save(learner, layout._write_path(layout._final_path(...)))` writes
   `final.ckpt` for that pair (`checkpoints.md` §2, ASM-18), and the pair's curve closes with the spread across seeds
   (`curves.md` §4). The naming helper names the *declared* layout; `_write_path` re-roots it at the write root, and the
   record spells both through `layout._relative`, unchanged (`write-root.md` §2, §5, §6).
9. **Assemble the record.** `_record(...)` returns §3's mapping and nothing beyond it: a run claims no table position and
   fits no rating (`module-map.md` §3, `records.md` §13, `surface.md` §4).

**The nine steps are the same for R1 and for a configuration in no registry**; only the data differs, and that is the whole of
D-3 (`ladder.md` §1, FAM-15, FAM-16.29). No step is conditional on a rung name, and no step reads `RUNGS`.

## 2. One variant × one seed: `_train_variant_seed`

`_train_variant_seed(config, entry, seed, budget, device) -> (curve, checkpoints, timing)` runs steps 3–8 for one pair and
returns three plain records; it is the only place a learner exists (`loop.py`, `README.md` §4). Three rules of its own:

- **The interval is `budget // 10`, not the declared `snapshot_every`.** ASM-18 fixes ten equally spaced snapshots, and a run's
  budget is not the configuration's declared one: the battery runs 60 and 250 hands (`battery.md` §2). At 250 hands a declared
  100 would write two snapshots, name two retained ones and leave FAM-12.4's five-version window unobservable; at `budget //
  10` it writes exactly ten, the last at `10 × interval ≤ budget` (`curves.md` §2). The declared value is **recorded**, in §4's
  `variants` row, and a run at the declared budget reproduces it exactly (1000 ÷ 10 = 100).
- **The pass is sequential and single-threaded**: one hand at a time, because one global `random` stream deals every hand and
  concurrency is not available (`protocol.md` §4, ASM-2). No hand is buffered, replayed or reordered.
- **The timing is measured, not asserted**: `_timings(start, hands)` reads `time.perf_counter()` around the pair's hands and
  returns §4's four facts; a run never claims a wall clock was beaten (`records.md` §12, ASM-15, FAM-13.5).

**The declaration the run would discard is refused, and nothing else changes (Rev 2).** At §1 step 1, and after the shape checks
above, the resolve step refuses an entry's `learning_rule` that is not `declarations.LEARNING_RULE`, a `hyper` key whose value is
not that key's `declarations.HYPER` value — or a key `HYPER` does not carry — and a `snapshot_every` at either level that is not
the **declared** samples ÷ 10, all as `IgnoredDeclaration`; and two arms declaring two values for one of the eight settings the
pair must share as `PairDeclarationsDiffer`, naming the key and both values. The `snapshot_every` check is skipped when no `samples`
is declared anywhere, because the run refuses that absence on its own (§5), and it is never measured against the `budget` argument:
a caller overriding `budget` trips nothing. A setting an entry leaves absent — or spells `None`, the way `_declared` already
reads one — is no claim and is accepted, and a `hyper` that is not a mapping names no key and is no claim either. The learner is
still built from `declarations.HYPER`, the interval is still `budget // 10`, and the seeds, the pool and the order of the loop are
untouched (`declarations.md` §2–§4, `errors.md` §4, ASM-7).
**The comparison is by declaration, not by shape.** `seeds` compares as a sequence (a list and a tuple of the same integers are one
declaration), and two `hyper` blocks differ when a key **both** of them name carries two values — a key only one side names is no
claim, the way the `hyper` check above reads one. The checks above already fix `learning_rule`, `hyper` and `snapshot_every`, so the
pair check does the work for the settings §2 leaves open: `samples`, `seeds`, `device`, `table` and `param_budget` (`declarations.md` §4).

Every write in the pass goes through `os.makedirs(parent, exist_ok=True)` before `agents.save`, because `save` invents no
directory and refuses a path whose parent is missing (`agents/surface.md` §8, `checkpoints.md` §2). The parent is made
**under the write root**, `layout._write_root()` — `CHECKPOINT_ROOT` unless the ambient `PYPOKER_CHECKPOINT_ROOT` names
another root — and both artefacts are handed to `save` through `layout._write_path`, so a battery's run writes a temporary
tree and the shipped one is untouched (`write-root.md` §1, §3, §4, §6).

## 3. The run record, key by key (D3)

`records.md` §12's ten **required** keys, plus this module's own `variants` (`surface.md` §4, `records.md` §1):

| Key | Content |
|---|---|
| `rung` | the rung name, or the unregistered configuration's own `name` (`records.md` §12) |
| `curves` | variant → seed → `{samples, td_error, spread}` — the ten snapshot steps, the mean absolute `td_error` of each interval, the spread across seeds (`curves.md` §5) |
| `pool` | `{id, m, frozen, members}`: the **declared** id, the read-back `m` and `frozen`, and the read-back members in order — the three pinned baselines first, then the version window (`records.md` §8, `registry.md` §3) |
| `checkpoints` | variant → seed → `{snapshots: [<the retained five paths>], final: <that pair's final model>}`, each path `layout._relative` of what `agents.save` was handed: repository-relative with POSIX separators when the artefact is inside the repository root, and **unchanged — absolute — when it is outside it**, because a run may be pointed at another write root (`checkpoints.md` §2, `write-root.md` §5) |
| `seeds` | the seed set the run used, after §5's default |
| `budget` | the hands per variant per seed the run used, after §5's default |
| `device` | the device the run used, after §5's default (`protocol.md` §6, D-8) |
| `params` | variant → `{budget: 10000, lower: 9800.0, upper: 10200.0}` — the declared parameter budget and its ±2% bound: the entry's own `param_budget`, else the configuration's, else `declarations.PARAM_BUDGET`, and the band is that number ±2%; a run measures no capacity (`surface.md` §4, ASM-10, `declarations.md` §2) |
| `table` | the declared table budget, `live` or `full`; a configuration declaring none is recorded at `live` (`league.md` §6, `loop.md` §2) |
| `timings` | variant → seed → `{hands, wall_clock_seconds, seconds_per_hand, hands_per_second}` (§4, `records.md` §12) |
| `variants` | the list of `{name, backend, encoding, architecture, samples, snapshot_every}` — the entry's declaration and the interval the run actually used (§4) |

**One id per record, and it is the declared one** (D3): `pool.id` is `config["pool"]["id"]` — for a registry rung the read-back id
of the membership, for a custom configuration its own `"pool-r7"`-style id — and the read-back pool's own digest id is **not**
carried anywhere in the record, because `tests/e2e/_surface.py`'s `pool_identity` reads every `id` a record declares and a
two-variant record showing two ids fails FAM-3.18 (`loop.md` §2, ASM-16).

## 4. The sub-records, in the shape their readers expect

- `curves[V][str(seed)] = {"samples": [...], "td_error": [...], "spread": [...]}` — three ten-element lists, the axis and the
  signal per seed and the across-seed spread repeated at each of that variant's seeds because it is one fact about the variant
  (`curves.md` §5). The keys are the variant name and the seed as a decimal string.
- `checkpoints[V][str(seed)] = {"snapshots": [five paths], "final": <one path>}` — the retained last M = 5 of the ten the pair
  wrote and that pair's final model, six artefacts and never the five earlier snapshots (`checkpoints.md` §3). Each path is
  `layout._relative` of what `agents.save` was handed: repository-relative when the artefact is inside the repository root and
  unchanged when it is outside, which is why `layout._resolve` reads an inside path back from the repository root and an
  outside one as it stands (`checkpoints.md` §2, `write-root.md` §5). `tests/e2e/_records.py`'s `checkpoint_paths_of` reads
  this key on its own, so a pool member's `path` is never counted here.
- `params[V] = {"budget": 10000, "lower": 9800.0, "upper": 10200.0}` — declared, never measured: `budget` is the entry's
  `param_budget`, else the configuration's, else 10,000, and `lower`/`upper` are that number ∓2%, so a caller declaring 12,000 reads
  11760.0 and 12240.0; what the record reports and what `agents.build_learner` is built with are two things, and no capacity is
  measured here (`agents.param_count` is not among the four `agents` calls this module may make, `module-map.md` §2, `surface.md`
  §4, `declarations.md` §2).
- `timings[V][str(seed)] = {"hands": budget, "wall_clock_seconds": ..., "seconds_per_hand": ..., "hands_per_second": ...}` —
  the facts `harness.timings` reports, measured here because no `harness` edge reaches this module (`e2e-surface.md` §3.6,
  ASM-15). The four key names are deliberate: the battery's `timing_facts` classifies a key by what it names, so `hands`,
  `seconds_per_hand` and `hands_per_second` are read as the hands, the per-hand cost and the throughput (FAM-13.5).
- `variants[i] = {name, backend, encoding, architecture, samples, snapshot_every}` where `samples` is the entry's declared
  budget and `snapshot_every` is the interval the run used. `architecture` is the entry's record copied verbatim, so the record
  shows the four settings the run was built from (`records.md` §2).

## 5. The arguments, and what an omitted one means (D3)

`run(rung, seeds=None, budget=None, device=None)` (`surface.md` §4):

- `seeds` omitted → the configuration's own `seeds`, else its first variant entry's `seeds`; a configuration carrying neither is
  `ConfigurationInvalid` naming `seeds`. The record states the set used.
- `budget` omitted → the configuration's `samples`, else its first variant entry's `samples`, else `LIVE_BUDGET` is **not**
  substituted: a configuration carrying none is refused naming `samples` (`e2e-surface.md` §2, D-12).
- `device` omitted → the configuration's `device`, else `devices()["default"]`, which is `"cpu"` (`devices.md` §1). A named
  device must be one `devices()["available"]` lists, or the run refuses naming it (D-8).
- `snapshot_every` and `table` are read from the configuration and are never arguments: the interval is `budget // 10` (§2) and
  a missing `table` is recorded as `live`.

## 6. The refusals of this document

This module's own refusals raise a `TrainingError` subclass with the offending value in the message (`errors.md` §2–§4), before
the first hand is dealt and before anything is written — a refused run leaves no artefact and no snapshot (`e2e-surface.md` §2).
The two rows marked *the owner's class* and *the pool's own class* are the called modules' refusals, propagated unchanged.

| Refusal | When |
|---|---|
| `UnknownRung` | `rung` is a string `RUNG_NAMES` does not carry — named (`registry.md` §5, FAM-15.5) |
| `ConfigurationInvalid` | a configuration missing a key the run reads, or one that is not a mapping — the key is named (§1, §5) |
| `VariantCountInvalid` | `variants` holds zero, three or more entries; one or two only (`ladder.md` §2, `surface.md` §4) |
| `VariantSettingInvalid` | a setting the run reads has the wrong shape: `backend` or `encoding` is not a string, `architecture` is not a mapping, `width`/`depth` is not a positive integer, or `sparsity` is outside `[0, 1]` — the field and its value are named (`records.md` §2, `ladder.md` §3) |
| *(the owner's class)* | a `backend`, an `encoding` or an `architecture.kind` the owning module does not declare is refused by **that** module, at §1 step 3: `features.build_encoder` for the encoding and `agents.build_learner` for the backend and the kind, whose message names the value. Those catalogues are not among the granted calls, so this module does not read them and does not re-wrap the refusal (`module-map.md` §2, `features/surface.md` §4, `agents/surface.md` §4) |
| `MissingConfigurationKey` | a configuration carrying none of the places §5 looks for `seeds`, `samples` or `device` — the key is named (§5) |
| `InvalidSeeds` | the seed set is empty, repeats a seed, or holds a non-integer (ASM-2, `surface.md` §4) |
| `InvalidBudget` | `budget` is not a positive integer, or is below ten hands — ten equally spaced snapshots need ten hands (`surface.md` §4, ASM-18) |
| `UnknownDevice` | a named `device` that `devices()["available"]` does not list, named (D-8, `devices.md` §1) |
| `IgnoredDeclaration` | a declaration the run would not use, raised after every shape check above and before the pool: an entry's `learning_rule` that is not `declarations.LEARNING_RULE`, a `hyper` key whose value is not that key's `declarations.HYPER` value (an unknown key included), or a `snapshot_every` at either level that is not the **declared** samples ÷ 10 — naming the entry, the configuration, the key, the value declared and the value in force (`declarations.md` §2–§3, ASM-7, ASM-18) |
| `PairDeclarationsDiffer` | a two-entry configuration whose arms declare two values for one of `learning_rule`, `hyper`, `samples`, `seeds`, `device`, `snapshot_every`, `table` or `param_budget` — a key only one arm declares is no claim, and the message names the key and both values (`declarations.md` §4, ASM-8, ASM-16) |
| *(the pool's own class)* | `build_pool`'s or `pool_members`' refusal — an `m` above the league's M, a member lacking `id` or `lineage`, a bad chain — propagates unchanged in `evaluation`'s class and is **never repaired** (`surface.md` §4, `evaluation/surface.md` §5) |

## 7. Determinism

One `(configuration, seed set, budget, pool membership)` gives one record twice: the same curves, the same pool id and the same
checkpoint paths (`surface.md` §4, FAM-4.7). Three facts carry it: the deal and opponent seeds are derivations of `(seed, i)`
(`seeds.md` §2), the learner's own generator is seeded from the run seed (`agents/architecture.md` §4), and the pool is frozen
before the first hand so the opponent draw depends on the membership and the seed alone (`registry.md` §3, ASM-16). A different
seed set gives different curves (FAM-4.8) and a different membership a different pool id (FAM-4.9). The **timings** are the one
field that differs between two runs of one tuple, which is why FAM-4.7 compares curves and pool ids and never the whole record.

## 8. What is left to L4

The loop's control structure, whether the per-pair pass is a generator or a list, how the snapshot count is tracked, the name and
shape of the resolve step's declaration checks — one reader per declaration, or one per pass — and every private name other than
`_train_variant_seed`, `_timings` and `_record`, whose signatures are contract for `tests/training/` (`README.md` §4). Not L4's:
§1's order, the nine steps' content, the `budget // 10` interval, the record's eleven keys and their nesting, the one-id rule, the
four timing key names, the order §1 step 1 refuses in and the four message texts (`guardrails.md` G4–G8, G21, `errors.md` §4).
