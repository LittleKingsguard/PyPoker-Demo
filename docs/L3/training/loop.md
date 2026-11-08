# training — the one loop

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 6 · **Date:** 2026-11-09 · **Rev 6** states that five of a pair's seven shared settings — not seven — reach `PairDeclarationsDiffer` (§2, §6)
- **Owner:** `run()` — the nine steps every rung is a configuration of (§1), the per-pair pass (§2), the run record key by key
  (§3), the sub-records it carries (§4), the arguments and their defaults (§5), the refusals (§6), determinism (§7); Rev 2 refuses
  the declarations a run would not use and reports the declared `param_budget` (§3–§4); Rev 3 reads the `hyper` block and the
  `learning_rule` at either level; **Rev 4** forwards a variant's rule into `agents.build_learner` and records it per variant and as
  the run's `rules` set (§1 step 3, §3–§4); **Rev 5** adds `rules` to the record's `pool` block, off its version members (D-19)
- **Ceiling:** 190 lines. At the ceiling, split by owner — never append
- **Read with:** `registry.md` §1–§3, `seeds.md` §2–§4, `episode.md` §1–§5, `curves.md` §5, `checkpoints.md` §3–§4,
  `devices.md` §3, `errors.md` §4

## 1. The nine steps (D3)

One pass of `run`, in this order, for any configuration — a registry rung or one written to `ladder.md` §3 and in no design
document (`loop.md` §3, FAM-15.1). Steps 3–8 repeat per variant and per seed; steps 1, 2 and 9 happen once.

1. **Resolve, refusing what the run would discard.** A string goes through `rung(name)` (`registry.md` §5). A mapping is used as it
   stands, refused in this order and always naming the key or the value it saw: the shape and the keys it reads (`name`, `variants`,
   `pool`, `seeds`, `samples`, `device`, `table`) and then the seed set's and budget's values (§5, `surface.md` §4); each entry's
   declared `backend`, `encoding` and `architecture` (`check_variant`); every declared `param_budget` that is not a positive integer
   (`VariantSettingInvalid`, §6); the declarations a run would not use — the `hyper` block's keys, a `learning_rule` the catalogue
   `agents.learners()` publishes does not carry, and the `snapshot_every` of either level, each at the configuration and at each
   entry (§2) — and, for two entries, the **five** settings both arms must share that reach this step (§6); then the pool, at step 2. The
   `name` is what the record's `rung` carries, and no step after this one sees a configuration this one refused.
2. **Freeze the pool before the first hand.** The declaration is `{"members": <config["pool"]["members"] filtered to versions
   whose `path` names a readable file>, "m": config["pool"]["m"], "frozen": config["pool"]["frozen"]}`; it goes to
   `evaluation.build_pool` and `evaluation.pool_members` reads the membership back. The pool is frozen for the whole run: no
   snapshot of this run enters it, and rolling is `evaluation.offer` between runs (D-16, ASM-16, `registry.md` §3).
3. **Build the variant under the rule it declares.** `features.build_encoder(entry["encoding"])`, then
   `features.observation_spec(encoder)` as the cross-check: `spec["representation"]` must equal the entry's `encoding`, or the run
   refuses naming both (`surface.md` §4, `features/surface.md` §5). Per seed, `agents.build_learner({"backend", "architecture",
   "seed", "encoder"})` with the run's seed as the learner's own seed, plus `"learning_rule"` when the entry — else its
   configuration — names one; a variant naming none passes nothing and `agents` builds the catalogue's first, so the spec is a
   declaration and never a rule this module substituted (ASM-2, D-19, `agents/surface.md` §4, `protocol.md` §4, `declarations.md` §1).
4. **Seed the work, not the arm.** Hand *i* of a run at `seed` is dealt at `_deal_seed(seed, i)` and draws its opponent at
   `_opponent_seed(seed, i)`, both functions of the run seed and *i* alone (`seeds.md` §2). The opponent is
   `evaluation.opponent(pool, `_opponent_seed(seed, i)`)` (`evaluation/surface.md` §8, ASM-16).
5. **Play the hand through `engine`.** The learner's seat is `_seat(i)` (`episode.md` §1) and its policy is
   `_learner_policy(learner, encoder)` (`episode.md` §2); seats alternate by swapping the two arguments, because seat 0 holds the
   button in every hand (`engine/surface.md` §4, D-2). The call is `engine.play_hand(deal_seed, seat0, seat1)`.
6. **Learn once per hand.** The episode's decisions for the learner's own seat become `records.md` §4 transitions and go to
   `agents.learn` as one batch, in the caller's order, neither sampled nor shuffled (`episode.md` §5, ASM-7). Its `td_error` is the
   hand's learning signal (`curves.md` §3). **A hand in which the learner's seat never acted produces no batch and no update** —
   `learn` refuses an empty sequence — and contributes no signal (`agents/rule.md` §3).
7. **Snapshot every interval.** After hand *i* with `(i + 1) % interval == 0`, and at most ten times, the run makes the pair's
   directory and calls `agents.save(learner, layout._write_path(layout._snapshot_path(...)))`, keeping the path it returns
   (`checkpoints.md` §2, `write-root.md` §1, §5). The interval is `budget // 10`; §2 says why it is not the declared `snapshot_every`.
8. **Write the final model.** After the last hand, `agents.save(learner, layout._write_path(layout._final_path(...)))` writes
   `final.ckpt` for that pair (`checkpoints.md` §2, ASM-18), and the pair's curve closes with the spread across seeds (`curves.md` §4).
   The naming helper names the *declared* layout; `_write_path` re-roots it at the write root, and the record spells both through
   `layout._relative`, unchanged (`write-root.md` §2, §5, §6).
9. **Assemble the record.** `_record(...)` returns §3's mapping and nothing beyond it: a run claims no table position and fits no
   rating (`module-map.md` §3, `records.md` §13, `surface.md` §4).

**The nine steps are the same for R1 and for a configuration in no registry**; only the data differs, and that is the whole of D-3
(`ladder.md` §1, FAM-15, FAM-16.29). No step is conditional on a rung name, and no step reads `RUNGS`.

## 2. One variant × one seed: `_train_variant_seed`

`_train_variant_seed(config, entry, seed, budget, device) -> (curve, checkpoints, timing)` runs steps 3–8 for one pair and returns
three plain records; it is the only place a learner exists (`loop.py`, `README.md` §4). Three rules of its own:

- **The interval is `budget // 10`, not the declared `snapshot_every`.** ASM-18 fixes ten equally spaced snapshots, and a run's budget
  is not the configuration's declared one: the battery runs 60 and 250 hands (`battery.md` §2). At 250 hands a declared 100 would write
  two snapshots and leave FAM-12.4's five-version window unobservable; at `budget // 10` it writes exactly ten, the last at
  `10 × interval ≤ budget` (`curves.md` §2). The declared value is **recorded**, in §4's `variants` row.
- **The pass is sequential and single-threaded**: one hand at a time, because one global `random` stream deals every hand and
  concurrency is not available (`protocol.md` §4, ASM-2). No hand is buffered, replayed or reordered.
- **The timing is measured, not asserted**: `_timings(start, hands)` reads `time.perf_counter()` around the pair's hands and returns
  §4's four facts; a run never claims a wall clock was beaten (`records.md` §12, ASM-15, FAM-13.5).

**The declaration a run would discard is refused; a catalogued rule is not a discard (Rev 4).** At §1 step 1 the resolve step
refuses, as `IgnoredDeclaration`, a `learning_rule` the catalogue `declarations.learning_rules()` reads from `agents.learners()` does not
carry, a `hyper` key whose value is not that key's `declarations.HYPER` value (a key `HYPER` does not carry included), and a
`snapshot_every` that is not the **declared** samples ÷ 10 — each at the configuration and at each entry, and a configuration-level
refusal names the configuration and no entry, because such a block sits where no entry can see it. Two arms declaring two values for one
of the **five** settings that reach the pair check are `PairDeclarationsDiffer`, naming the key and both values; a catalogued rule is not one
of them, so two arms may declare two rules and both are trained (D-19, `rules.md` §2, §8). Every declared `param_budget` that is not a
positive integer is `VariantSettingInvalid` (§6), so the `params` band is computed from a validated number and never from an `int()` of a
string or a truncated float. The `snapshot_every` check is skipped when no `samples` is declared anywhere, and it is never measured
against `budget`, so a caller overriding `budget` trips nothing. An absent setting — or one spelled `None` — is no claim and is accepted,
and a `hyper` that is not a mapping names no key: the learner is still built from `declarations.HYPER` and the interval is still
`budget // 10` (`declarations.md` §2–§4, ASM-7, ASM-10).
**The comparison is by declaration, not by shape.** `seeds` compares as a sequence (a list and a tuple of the same integers are one
declaration), and two `hyper` blocks differ when a key **both** name carries two values; the checks above fix `hyper` and
`snapshot_every`, so the pair check covers `samples`, `seeds`, `device`, `table` and `param_budget` (`declarations.md` §4).

Every write in the pass goes through `os.makedirs(parent, exist_ok=True)` before `agents.save`, because `save` invents no directory and
refuses a path whose parent is missing (`agents/surface.md` §8, `checkpoints.md` §2). The parent is made **under the write root**,
`layout._write_root()` — `CHECKPOINT_ROOT` unless the ambient `PYPOKER_CHECKPOINT_ROOT` names another root — and both artefacts are
handed to `save` through `layout._write_path`, so a battery's run writes a temporary tree and the shipped one is untouched
(`write-root.md` §1, §3, §4, §6).

## 3. The run record, key by key (D3)

`records.md` §12's eleven **required** keys — `rules` among them since D-19 — plus this module's own `variants` (`surface.md` §4):

| Key | Content |
|---|---|
| `rung` | the rung name, or the unregistered configuration's own `name` (`records.md` §12) |
| `curves` | variant → seed → `{samples, td_error, spread}` — the ten snapshot steps, the mean absolute `td_error` of each interval, the spread across seeds (`curves.md` §5) |
| `pool` | `{id, lineage, m, frozen, members, rules}`: the **declared** id, the read-back `m`, `frozen` and ordered members — the three pinned baselines first, then the version window — and `rules`, the distinct rules those version members declare (`records.md` §8, §12, `registry.md` §3, D-19) |
| `checkpoints` | variant → seed → `{snapshots: [<the retained five paths>], final: <that pair's final model>}`, each path `layout._relative` of what `agents.save` was handed: repository-relative with POSIX separators inside the repository root and **unchanged — absolute — outside it** (`checkpoints.md` §2, `write-root.md` §5) |
| `seeds` | the seed set the run used, after §5's default |
| `budget` | the hands per variant per seed the run used, after §5's default |
| `device` | the device the run used, after §5's default (`protocol.md` §6, D-8) |
| `params` | variant → `{budget: 10000, lower: 9800.0, upper: 10200.0}` — the declared budget and its ±2% bound: the entry's `param_budget`, else the configuration's, else `declarations.PARAM_BUDGET`, validated at §1 step 1 (§6); a run measures no capacity (`surface.md` §4, ASM-10) |
| `table` | the declared table budget, `live` or `full`; a configuration declaring none is recorded at `live` (`league.md` §6, `loop.md` §2) |
| `timings` | variant → seed → `{hands, wall_clock_seconds, seconds_per_hand, hands_per_second}` (§4, `records.md` §12) |
| `variants` | the list of `{name, backend, encoding, architecture, learning_rule, samples, snapshot_every}` — the entry's declaration, **the rule the variant was actually built under** and the interval the run used (§4) |
| `rules` | the distinct rules the run declared and trained, in declaration order: one name for a ladder rung, two for a configuration whose arms name two estimators (`records.md` §12, `rules.md` §7, D-19) |

**One id per record, and it is the declared one** (D3): `pool.id` is `config["pool"]["id"]` — for a registry rung the read-back id of
the membership, for a custom configuration its own `"pool-r7"`-style id — and the read-back pool's own digest id is **not** carried
anywhere in the record, because `tests/e2e/_surface.py`'s `pool_identity` reads every `id` a record declares and a two-variant record
showing two ids fails FAM-3.18 (`loop.md` §2, ASM-16).

## 4. The sub-records, in the shape their readers expect

- `curves[V][str(seed)] = {"samples": [...], "td_error": [...], "spread": [...]}` — three ten-element lists: the axis, the signal and the
  across-seed spread repeated at each of that variant's seeds because it is one fact about it (`curves.md` §5); the keys are the variant name and `str(seed)`.
- `checkpoints[V][str(seed)] = {"snapshots": [five paths], "final": <one path>}` — the retained last M = 5 of the ten the pair wrote
  and that pair's final model, six artefacts and never the five earlier snapshots (`checkpoints.md` §3), each path `layout._relative`
  of what `agents.save` was handed (`checkpoints.md` §2, `write-root.md` §5); `_records.py`'s `checkpoint_paths_of` reads this key alone.
- `params[V] = {"budget": 10000, "lower": 9800.0, "upper": 10200.0}` — declared, never measured: `budget` is the entry's
  `param_budget`, else the configuration's, else 10,000, and `lower`/`upper` are that number ∓2%, so a caller declaring 12,000 reads
  11760.0 and 12240.0; no capacity is measured here (`agents.param_count` is not granted, `module-map.md` §2, ASM-10).
- `timings[V][str(seed)] = {"hands": budget, "wall_clock_seconds": ..., "seconds_per_hand": ..., "hands_per_second": ...}` — the facts
  `harness.timings` reports, measured here because no `harness` edge reaches this module (`e2e-surface.md` §3.6, ASM-15). The four key
  names are deliberate: the battery's `timing_facts` classifies a key by what it names (FAM-13.5).
- `variants[i] = {name, backend, encoding, architecture, learning_rule, samples, snapshot_every}` — `architecture` is the entry's record
  copied verbatim, `samples` its declared budget (the run's hands when the entry declares none), `snapshot_every` the interval the run
  used, and `learning_rule` **the rule the learner was built under**: the entry's, else the configuration's copy, else the catalogue's
  first, which is what `agents` built when the entry named none, so a reader rebuilds the learner the curve came from (`rules.md` §4, D-19).
- `rules = [<one rule per distinct estimator the run trained>]` — the set the per-variant rows name, in declaration order and deduped, so
  `records.md` §12's `rules` is read off the record itself; `pool.rules` is the same set for the opposition, read off the members'
  own `rule` fields (`records.md` §8, §12, `rules.md` §7, D-19).

## 5. The arguments, and what an omitted one means (D3)

`run(rung, seeds=None, budget=None, device=None)` (`surface.md` §4):

- `seeds` omitted → the configuration's own `seeds`, else its first variant entry's `seeds`; a configuration carrying neither is
  `ConfigurationInvalid` naming `seeds`. The record states the set used.
- `budget` omitted → the configuration's `samples`, else its first variant entry's `samples`, else `LIVE_BUDGET` is **not**
  substituted: a configuration carrying none is refused naming `samples` (`e2e-surface.md` §2, D-12).
- `device` omitted → the configuration's `device`, else `devices()["default"]`, which is `"cpu"`; a named device must be one
  `devices()["available"]` lists, or the run refuses naming it (`devices.md` §1, D-8).
- `snapshot_every` and `table` are read from the configuration and are never arguments: the interval is `budget // 10` (§2) and
  a missing `table` is recorded as `live`. `learning_rule` is read from the declaration too and is never an argument.

## 6. The refusals of this document

This module's own refusals raise a `TrainingError` subclass with the offending value in the message (`errors.md` §2–§4), before
the first hand is dealt and before anything is written — a refused run leaves no artefact and no snapshot (`e2e-surface.md` §2).
The two rows marked *the owner's class* and *the pool's own class* are the called modules' refusals, propagated unchanged.

| Refusal | When |
|---|---|
| `UnknownRung` | `rung` is a string `RUNG_NAMES` does not carry — named (`registry.md` §5, FAM-15.5) |
| `ConfigurationInvalid` | a configuration missing a key the run reads, or one that is not a mapping — the key is named (§1, §5) |
| `VariantCountInvalid` | `variants` holds zero, three or more entries; one or two only (`ladder.md` §2, `surface.md` §4) |
| `VariantSettingInvalid` | a setting the run reads has the wrong shape: `backend` or `encoding` is not a string, `architecture` is not a mapping, `width`/`depth` is not a positive integer, `sparsity` is outside `[0, 1]`, or a declared `param_budget` — at the configuration or at an entry — is not a positive integer — the field, its level and its value are named (`records.md` §2, `ladder.md` §3, ASM-10) |
| *(the owner's class)* | a `backend`, an `encoding`, an `architecture.kind` or a `learning_rule` the owning module does not declare is refused by **that** module, at §1 step 3: `features.build_encoder` for the encoding and `agents.build_learner` for the backend, the kind and the rule, whose message names the value; this module reads no such catalogue except the rule catalogue `learners()` publishes, and re-wraps none (`module-map.md` §2, `features/surface.md` §4, `agents/surface.md` §4) |
| `MissingConfigurationKey` | a configuration carrying none of the places §5 looks for `seeds`, `samples` or `device` — the key is named (§5) |
| `InvalidSeeds` | the seed set is empty, repeats a seed, or holds a non-integer (ASM-2, `surface.md` §4) |
| `InvalidBudget` | `budget` is not a positive integer, or is below ten hands — ten equally spaced snapshots need ten hands (`surface.md` §4, ASM-18) |
| `UnknownDevice` | a named `device` that `devices()["available"]` does not list, named (D-8, `devices.md` §1) |
| `IgnoredDeclaration` | a declaration the run would not use, raised after every shape check above and before the pool: a `learning_rule` the catalogue `agents.learners()` publishes does not carry, a `hyper` key whose value is not that key's `declarations.HYPER` value (an unknown key included), and a `snapshot_every` at either level that is not the **declared** samples ÷ 10 — each **at the configuration and at each entry**, naming the level, the key, the rule or value declared and the catalogue or value the run uses (`declarations.md` §2–§3, `rules.md` §2, D-19, ASM-18) |
| `PairDeclarationsDiffer` | a two-entry configuration whose arms declare two values for one of `samples`, `seeds`, `device`, `table` or `param_budget` — **five** of the seven settings a pair shares, because `hyper` and `snapshot_every` are refused earlier and per arm by `IgnoredDeclaration` and the pair class is unreachable for them: two arms cannot differ on a `hyper` value or an interval without one arm disagreeing with the declaration in force, and the `hyper`, rule and interval checks run before the pair check — a key only one arm declares is no claim, and the message names the key and both values. `learning_rule` is **not** among them: two arms may declare two rules, which is the pair's `rule` axis (`declarations.md` §2, §4, `rules.md` §8, ASM-8, ASM-16) |
| *(the pool's own class)* | `build_pool`'s or `pool_members`' refusal — an `m` above the league's M, a member lacking `id` or `lineage`, a bad chain — propagates unchanged in `evaluation`'s class and is **never repaired** (`surface.md` §4, `evaluation/surface.md` §5) |

## 7. Determinism

One `(configuration, seed set, budget, pool membership)` gives one record twice: the same curves, the same pool id, the same
checkpoint paths and the same rules (`surface.md` §4, FAM-4.7), because a variant's rule is a declaration and not a draw. Three facts
carry it: the deal and opponent seeds are derivations of `(seed, i)` (`seeds.md` §2), the learner's generator is seeded from the run seed
(`agents/architecture.md` §4), and the pool is frozen before the first hand so the opponent draw depends on the membership and the seed
alone (`registry.md` §3, ASM-16). A different seed set gives different curves (FAM-4.8), a different membership a different pool id
(FAM-4.9); the **timings** are the one field that differs between two runs of one tuple (`surface.md` §4).

## 8. What is left to L4

The loop's control structure, whether the per-pair pass is a generator or a list, how the snapshot count is tracked, the name and shape
of the resolve step's declaration checks, how a variant's rule is resolved from its entry and its configuration, and where the
`param_budget` validation sits (at step 1 and inside `_param_budget`); and every private name other than `_train_variant_seed`,
`_timings` and `_record`, whose signatures are contract for `tests/training/` (`README.md` §4). Not L4's: §1's order, the nine steps'
content, the `budget // 10` interval, the record's twelve keys and their nesting, the one-id rule, the rule forwarded and built under, the
four timing key names, the order §1 step 1 refuses in and the message texts (`guardrails.md` G21–G23).
