# training — the one loop

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 8 · **Date:** 2026-11-09 · **Rev 7** forwards a variant's `utility` to `agents.build_learner` and to the transition step, and records it per variant, per pool member and as the run's `utilities` set (§1 steps 3 and 6, §3–§4, D-20) · **Rev 8** forwards a `pool` entry's `baselines` and reads one `baselines` row per baseline the frozen pool holds (§1 step 2, §3–§4, D-21)
- **Owner:** `run()` — the nine steps every rung is a configuration of (§1), the per-pair pass (§2), the run record key by key
  (§3), the sub-records it carries (§4), the arguments and their defaults (§5), the refusals (§6), determinism (§7); Rev 2 refuses
  the declarations a run would not use and reports the declared `param_budget` (§3–§4); Rev 3 reads the `hyper` block and the
  `learning_rule` at either level; **Rev 4** forwards and records a variant's rule (§1 step 3, §3–§4); **Rev 5** adds `rules` to the
  record's `pool` block, off its version members (D-19)
- **Ceiling:** 190 lines. At the ceiling, split by owner — never append
- **Read with:** `registry.md` §1–§3, `seeds.md` §2–§4, `episode.md` §1–§6, `reward.md` §1–§5, `curves.md` §5, `checkpoints.md` §3–§4,
  `devices.md` §3, `errors.md` §4

## 1. The nine steps (D3)

One pass of `run`, in this order, for any configuration — a registry rung or one written to `ladder.md` §3 and in no design
document (`loop.md` §3, FAM-15.1). Steps 3–8 repeat per variant and per seed; steps 1, 2 and 9 happen once.

1. **Resolve, refusing what the run would discard.** A string goes through `rung(name)` (`registry.md` §5). A mapping is used as it
   stands, refused in this order and always naming the key or the value it saw: the shape and the keys it reads (`name`, `variants`,
   `pool`, `seeds`, `samples`, `device`, `table`) and then the seed set's and budget's values (§5, `surface.md` §4); each entry's
   `backend`, `encoding` and `architecture` (`check_variant`); every declared `param_budget` that is not a positive integer; the
   declarations a run would not use — the `hyper` keys, a `learning_rule` or a `utility` no catalogue `agents.learners()` publishes
   carries, and the `snapshot_every` of either level, each at both levels (§2) — and, for two entries, the **five** settings both arms
   must share (§6); then the pool, at step 2. No step after this one sees a configuration this one refused (`errors.md` §2).
2. **Freeze the pool before the first hand.** The declaration is `{"members": <config["pool"]["members"] filtered to versions
   whose `path` names a readable file>, "m": config["pool"]["m"], "frozen": config["pool"]["frozen"]}`, plus `"baselines"` — named catalogue
   baselines the configuration admits — when its `pool` entry declares one, forwarded as it stands and never defaulted here; it goes to
   `evaluation.build_pool` and `evaluation.pool_members` reads the membership back. No snapshot of this run enters it (D-16, ASM-16, ASM-32, `registry.md` §3, D-21).
3. **Build the variant under the rule and the utility it declares.** `features.build_encoder(entry["encoding"])`, then
   `features.observation_spec(encoder)` as the cross-check: `spec["representation"]` must equal the entry's `encoding`, or the run
   refuses naming both (`surface.md` §4, `features/surface.md` §5). Per seed, `agents.build_learner({"backend", "architecture",
   "seed", "encoder"})` with the run's seed as the learner's own seed, plus `"learning_rule"` and `"utility"` when the entry — else
   its configuration — names them; a variant naming either passes no key and `agents` builds that catalogue's first, so the spec is a
   declaration and never a member this module substituted (ASM-2, D-19, D-20, `agents/surface.md` §4, `protocol.md` §4).
4. **Seed the work, not the arm.** Hand *i* of a run at `seed` is dealt at `_deal_seed(seed, i)` and draws its opponent at
   `_opponent_seed(seed, i)`, both functions of the run seed and *i* alone (`seeds.md` §2). The opponent is
   `evaluation.opponent(pool, `_opponent_seed(seed, i)`)` (`evaluation/surface.md` §8, ASM-16).
5. **Play the hand through `engine`.** The learner's seat is `_seat(i)` (`episode.md` §1) and its policy is
   `_learner_policy(learner, encoder)` (`episode.md` §2); seats alternate by swapping the two arguments, because seat 0 holds the
   button in every hand (`engine/surface.md` §4, D-2). The call is `engine.play_hand(deal_seed, seat0, seat1)`.
6. **Learn once per hand.** The episode's decisions for the learner's own seat become `records.md` §4 transitions and go to
   `agents.learn` as one batch, in the caller's order, neither sampled nor shuffled (`episode.md` §5, ASM-7); the transition step is
   handed `_trained_utility(config, entry)`, the utility the variant is trained on, which is **the one place a utility is applied**
   (`episode.md` §3, `reward.md` §1, D-20). Its `td_error` is the hand's learning signal (`curves.md` §3). **A hand in which the
   learner's seat never acted produces no batch and no update** — `learn` refuses an empty sequence — and contributes no signal
   (`agents/rule.md` §3).
7. **Snapshot every interval.** After hand *i* with `(i + 1) % interval == 0`, and at most ten times, the run makes the pair's
   directory and calls `agents.save(learner, layout._write_path(layout._snapshot_path(...)))`, keeping the path it returns
   (`checkpoints.md` §2, `write-root.md` §1, §5). The interval is `budget // 10`; §2 says why it is not the declared `snapshot_every`.
8. **Write the final model.** After the last hand, `agents.save(learner, layout._write_path(layout._final_path(...)))` writes
   `final.ckpt` for that pair (`checkpoints.md` §2, ASM-18), and the pair's curve closes with the spread across seeds (`curves.md` §4);
   the helper names the *declared* layout, `_write_path` re-roots it and `layout._relative` spells it (`write-root.md` §2, §5, §6).
9. **Assemble the record.** `_record(...)` returns §3's mapping and nothing beyond it: a run claims no table position and fits no
   rating (`module-map.md` §3, `records.md` §13, `surface.md` §4).

**The nine steps are the same for R1 and for a configuration in no registry**; only the data differs, and that is the whole of D-3
(`ladder.md` §1, FAM-15, FAM-16.29). No step is conditional on a rung name, a rule or a utility, because all three are declarations a
configuration carries (`rules.md` §4, `utilities.md` §5, D-19, D-20).

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

**Both axes are resolved one way, and neither is substituted.** `_declared_rule` and `_declared_utility` read the entry's declaration
first, its configuration's second — a level declaring none, or `None`, is no claim and they return `None` — and `_trained_rule` and
`_trained_utility` fall back to the **catalogue's first** member of their axis, through `declarations.learning_rules()` and
`declarations.utilities()`, so a variant naming neither is trained under `masked-q-learning` on `net-chips` (`rules.md` §4, `utilities.md` §5, D-19, D-20).

**The declaration a run would discard is refused; a catalogued member is not (Rev 4, Rev 7).** At §1 step 1 a `learning_rule` or a
`utility` the catalogue `agents.learners()` publishes does not carry is `IgnoredDeclaration`, as a `hyper` key whose value is not that
key's `declarations.HYPER` value (an unknown key included) and a `snapshot_every` that is not the **declared** samples ÷ 10 is — each at
the configuration and at each entry, and both levels are named. Two arms declaring two values for one of the **five** settings that reach
the pair check are `PairDeclarationsDiffer`, naming the key and both values; a catalogued rule or utility is not one of them, so two arms
may declare two of either and both are trained (D-19, D-20, `rules.md` §8, `utilities.md` §8). A `param_budget` that is not a positive
integer is `VariantSettingInvalid`; an absent setting — or one spelled `None` — is no claim, and a `hyper` that is not a mapping names no
key (`declarations.md` §2–§4, ASM-7, ASM-10, ASM-18).
**The comparison is by declaration, not by shape.** `seeds` compares as a sequence, and two `hyper` blocks differ when a key **both**
name carries two values; with those two checks above, the pair check covers `samples`, `seeds`, `device`, `table`, `param_budget`
(`declarations.md` §4).

Every write in the pass goes through `os.makedirs(parent, exist_ok=True)` before `agents.save`, because `save` invents no directory and
refuses a path whose parent is missing (`agents/surface.md` §8, `checkpoints.md` §2). The parent is made **under the write root**,
`layout._write_root()` — `CHECKPOINT_ROOT` unless the ambient `PYPOKER_CHECKPOINT_ROOT` names another root — and both artefacts reach
`save` through `layout._write_path`, so a battery's run writes a temporary tree and the shipped one is untouched (`write-root.md` §6).

## 3. The run record, key by key (D3)

`records.md` §12's thirteen **required** keys — `variants` among them, and `rules` and `utilities` since D-19 and D-20 — and then this
module's own evidence keys, `header`, `baselines` and `axis row` (`surface.md` §4, `utilities.md` §7):
| Key | Content |
|---|---|
| `rung` | the rung name, or the unregistered configuration's own `name` (`records.md` §12) |
| `curves` | variant → seed → `{samples, td_error, spread}` — the ten snapshot steps, the mean absolute `td_error` of each interval, the spread across seeds (`curves.md` §5) |
| `pool` | `{id, lineage, m, frozen, members, rules, utilities}`: the **declared** id, the read-back `m`, `frozen` and ordered members — the pool's **pinned** baselines first (the anchor three, then any declared folder), then the version window — and `rules` and `utilities`, the distinct rules and utilities those version members declare (`records.md` §8, §12, `registry.md` §3, ASM-32, D-19, D-20, D-21) |
| `checkpoints` | variant → seed → `{snapshots: [<the retained five paths>], final: <that pair's final model>}`, each path `layout._relative` of what `agents.save` was handed: repository-relative with POSIX separators inside the repository root and **unchanged — absolute — outside it** (`checkpoints.md` §2, `write-root.md` §5) |
| `seeds` | the seed set the run used, after §5's default |
| `budget` | the hands per variant per seed the run used, after §5's default |
| `device` | the device the run used, after §5's default (`protocol.md` §6, D-8) |
| `params` | variant → `{budget: 10000, lower: 9800.0, upper: 10200.0}` — the declared budget and its ±2% bound: the entry's `param_budget`, else the configuration's, else `declarations.PARAM_BUDGET`, validated at §1 step 1 (§6); a run measures no capacity (`surface.md` §4, ASM-10) |
| `table` | the declared table budget, `live` or `full`; a configuration declaring none is recorded at `live` (`league.md` §6, `loop.md` §2) |
| `timings` | variant → seed → `{hands, wall_clock_seconds, seconds_per_hand, hands_per_second}` (§4, `records.md` §12) |
| `variants` | the list of `{name, backend, encoding, architecture, learning_rule, utility, samples, snapshot_every}` — the entry's declaration, **the rule and the utility the variant was actually built under**, and the interval the run used (§4, D-19, D-20) |
| `rules` | the distinct rules the run declared and trained, in declaration order: one name for a ladder rung, two for a configuration whose arms name two estimators (`records.md` §12, `rules.md` §7, D-19) |
| `utilities` | the same set on D-20's axis: the distinct utilities the run declared and trained, in declaration order, read through `_trained_utility` — one for a ladder rung, two for a configuration whose arms name two (`records.md` §12, `utilities.md` §7, D-20) |

**One id per record, and it is the declared one** (D3): `pool.id` is `config["pool"]["id"]` — for a registry rung the read-back id of
the membership, for a custom configuration its own `"pool-r7"`-style id — and the read-back digest id is **not** carried anywhere in the
record, because `tests/e2e/_surface.py`'s `pool_identity` reads every `id` a record declares and two ids in one two-variant record fail FAM-3.18 (ASM-16).

## 4. The sub-records, in the shape their readers expect

- `curves[V][str(seed)] = {"samples": [...], "td_error": [...], "spread": [...]}` — three ten-element lists: the axis, the signal and the across-seed spread repeated at each of that variant's seeds because it is one fact about it (`curves.md` §5).
- `checkpoints[V][str(seed)] = {"snapshots": [five paths], "final": <one path>}` — the retained last M = 5 of the ten the pair wrote
  and that pair's final model, six artefacts and never eleven (`checkpoints.md` §3, `write-root.md` §5); `_records.py`'s `checkpoint_paths_of` reads this key alone.
- `params[V] = {"budget": 10000, "lower": 9800.0, "upper": 10200.0}` — declared, never measured: the entry's `param_budget`, else the configuration's, else 10,000, with `lower`/`upper` that number ∓2% (`module-map.md` §2, ASM-10).
- `timings[V][str(seed)] = {"hands": budget, "wall_clock_seconds": ..., "seconds_per_hand": ..., "hands_per_second": ...}` — the facts
  `harness.timings` reports; the four key names are deliberate, because the battery's `timing_facts` classifies a key by what it names
  (`e2e-surface.md` §3.6, ASM-15, FAM-13.5).
- `variants[i] = {name, backend, encoding, architecture, learning_rule, utility, samples, snapshot_every}` — `architecture` the entry's
  record copied verbatim, `samples` its declared budget (the run's hands when the entry declares none), `snapshot_every` the interval the
  run used, and `learning_rule`/`utility` **the member of each axis the learner was built under**: the entry's, else its configuration's,
  else the catalogue's first, which is what `agents` built when the entry named neither (`rules.md` §4, `utilities.md` §5, D-19, D-20).
- `rules = [<one rule per distinct estimator trained>]` and `utilities = [<one utility per distinct objective trained>]` — the sets the
  per-variant rows name, in declaration order and deduped, so `records.md` §12's `rules` and `utilities` are read off the record itself;
  `pool.rules` and `pool.utilities` are the same sets for the opposition, off the members' own fields (`records.md` §8, §12, `rules.md` §7, `utilities.md` §7, D-19, D-20).
- `baselines` and `header` — `_pool_baselines(pool_record)` reads the baseline ids the frozen pool **actually holds** off its own members,
  so `baselines["rows"]` is one `{member, hand count, pinned: True, measured: False}` row per baseline the pool holds — the anchor three
  and any declared folder, in the pool's order — and the header's `parameter counts` carry a declared `0` for each of those names: no
  count here is a hard-coded three (`records.md` §8, `protocol.md` §3, ASM-32, D-21, `evaluation/surface.md` §13).

## 5. The arguments, and what an omitted one means (D3)

`run(rung, seeds=None, budget=None, device=None)` (`surface.md` §4):

- `seeds` omitted → the configuration's own `seeds`, else its first variant entry's `seeds`; a configuration carrying neither is `ConfigurationInvalid` naming `seeds`.
- `budget` omitted → the configuration's `samples`, else its first variant entry's `samples`, else `LIVE_BUDGET` is **not**
  substituted: a configuration carrying none is refused naming `samples` (`e2e-surface.md` §2, D-12).
- `device` omitted → the configuration's `device`, else `devices()["default"]`, which is `"cpu"`; a named device must be one
  `devices()["available"]` lists, or the run refuses naming it (`devices.md` §1, D-8).
- `snapshot_every` and `table` are read from the configuration and are never arguments: the interval is `budget // 10` (§2) and a
  missing `table` is recorded as `live`; `learning_rule`, `utility` and a `pool` entry's `baselines` are read from the declaration too (`utilities.md` §5, D-20, D-21).

## 6. The refusals of this document

This module's own refusals raise a `TrainingError` subclass naming the offending value (`errors.md` §2–§4), before the first hand is
dealt and before anything is written; the two rows marked *the owner's class* and *the pool's own class* propagate unchanged (`e2e-surface.md` §2).

| Refusal | When |
|---|---|
| `UnknownRung` | `rung` is a string `RUNG_NAMES` does not carry — named (`registry.md` §5, FAM-15.5) |
| `ConfigurationInvalid` | a configuration missing a key the run reads, or one that is not a mapping — the key is named (§1, §5) |
| `VariantCountInvalid` | `variants` holds zero, three or more entries; one or two only (`ladder.md` §2, `surface.md` §4) |
| `VariantSettingInvalid` | a setting the run reads has the wrong shape: `backend` or `encoding` is not a string, `architecture` is not a mapping, `width`/`depth` is not a positive integer, `sparsity` is outside `[0, 1]`, or a declared `param_budget` — at the configuration or at an entry — is not a positive integer — the field, its level and its value are named (`records.md` §2, `ladder.md` §3, ASM-10) |
| *(the owner's class)* | a `backend`, an `encoding`, an `architecture.kind`, a `learning_rule` or a `utility` the owning module does not declare is refused by **that** module, at §1 step 3: `features.build_encoder` for the encoding and `agents.build_learner` for the backend, the kind, the rule and the utility, whose message names the value; this module reads no such catalogue except the two `learners()` publishes, and re-wraps none (`module-map.md` §2, `features/surface.md` §4, `agents/surface.md` §4, D-20) |
| `MissingConfigurationKey` | a configuration carrying none of the places §5 looks for `seeds`, `samples` or `device` — the key is named (§5) |
| `InvalidSeeds` | the seed set is empty, repeats a seed, or holds a non-integer (ASM-2, `surface.md` §4) |
| `InvalidBudget` | `budget` is not a positive integer, or is below ten hands — ten equally spaced snapshots need ten hands (`surface.md` §4, ASM-18) |
| `UnknownDevice` | a named `device` that `devices()["available"]` does not list, named (D-8, `devices.md` §1) |
| `IgnoredDeclaration` | a declaration the run would not use, raised after every shape check above and before the pool: a `learning_rule` or a `utility` the catalogue `agents.learners()` publishes does not carry, a `hyper` key whose value is not that key's `declarations.HYPER` value (an unknown key included), and a `snapshot_every` at either level that is not the **declared** samples ÷ 10 — each **at the configuration and at each entry**, naming the level, the key, the member or value declared and the catalogue or value the run uses (`declarations.md` §2–§3, `rules.md` §2, `utilities.md` §2, D-19, D-20, ASM-18) |
| `PairDeclarationsDiffer` | a two-entry configuration whose arms declare two values for one of `samples`, `seeds`, `device`, `table` or `param_budget` — **five** of the seven settings a pair shares, because `hyper` and `snapshot_every` are refused earlier and per arm by `IgnoredDeclaration` and the pair class is unreachable for them: two arms cannot differ on a `hyper` value or an interval without one arm disagreeing with the declaration in force, and the `hyper`, member and interval checks run before the pair check — a key only one arm declares is no claim, and the message names the key and both values. `learning_rule` and `utility` are **not** among them: two arms may declare two of either, which are the pair's `rule` and `utility` axes (`declarations.md` §2, §4, `rules.md` §8, `utilities.md` §8, ASM-8, ASM-16) |
| `ChipConservationBroken` | a hand whose chips in play disagree with the stacks the game declares, or whose `U(s_0)` is `0` — raised by the transition step under `stack-shortfall`, naming the seed and both totals (`reward.md` §4, `errors.md` §2, ASM-6, D-20) |
| *(the pool's own class)* | `build_pool`'s or `pool_members`' refusal — an `m` above the league's M, a member lacking `id`, `lineage`, `rule` or `utility`, a bad chain — propagates unchanged in `evaluation`'s class and is **never repaired** (`surface.md` §4, `evaluation/surface.md` §5, ASM-27) |

## 7. Determinism

One `(configuration, seed set, budget, pool membership)` gives one record twice: the same curves, the same pool id, the same
checkpoint paths, and the same rules and utilities (`surface.md` §4, FAM-4.7), because each variant's rule and utility are
declarations and not draws. Three facts carry it: the deal and opponent seeds are derivations of `(seed, i)` (`seeds.md` §2), the
learner's generator is seeded from the run seed (`agents/architecture.md` §4), and the pool is frozen before the first hand so the
opponent draw depends on the membership alone (`registry.md` §3, ASM-16). A different seed set gives different curves (FAM-4.8), a
different membership a different pool id (FAM-4.9); the **timings** are the one field two runs of one tuple differ in (`surface.md` §4).

## 8. What is left to L4

The loop's control structure, whether the per-pair pass is a generator or a list, how the snapshot count is tracked, the name and shape
of the resolve step's declaration checks, how a variant's rule and utility are resolved from its entry and its configuration, and where
the `param_budget` validation sits (at step 1 and inside `_param_budget`); and every private name other than `_train_variant_seed`,
`_timings`, `_record` and `_pool_baselines`, whose signatures are contract for `tests/training/` (`README.md` §4). Not L4's: §1's order, the nine steps' content,
the `budget // 10` interval, the record's thirteen keys, the one-id rule, both members forwarded and built under, the four timing key names,
one `baselines` row per baseline the pool holds with its declared `0`, the order §1 step 1 refuses in and the message texts (`guardrails.md` G21–G23).
