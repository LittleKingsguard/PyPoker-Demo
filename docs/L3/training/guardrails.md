# training — L4 guardrails

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 8 · **Date:** 2026-11-09 · **Rev 8:** G21 counts the five shared settings that reach `PairDeclarationsDiffer`
- **Owner:** one numbered note per risk this design identified, in the order they bite, each naming its rule and the test that
  catches it — Rev 4 adds G21 (the declaration refusals), Rev 5 G22 (the declared budget), Rev 6 G21's catalogued-rule reading and
  G23 (the rule forwarded, and the record's `rules` set)
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append
- **Read with:** all of `README.md`, `registry.md`, `loop.md`, `seeds.md`, `episode.md`, `curves.md`, `checkpoints.md`,
  `fairness.md`, `devices.md`, `errors.md`

The unit battery's files are contract: `tests/training/test_registry.py` (`TRN-1.k`), `test_loop.py` (`TRN-2.k`),
`test_seeds.py` (`TRN-3.k`), `test_episode.py` (`TRN-4.k`), `test_curves.py` (`TRN-5.k`), `test_checkpoints.py` (`TRN-6.k`),
`test_fairness.py` (`TRN-7.k`), `test_devices.py` (`TRN-8.k`), `test_errors.py` (`TRN-9.k`); the join battery is
`tests/integration/training/test_run_record.py` (`TRNJ-1`–`4`, `TRNJ-7`–`8`), `test_fairness_joins.py` (`TRNJ-5`),
`test_index.py` (`TRNJ-6`) and `test_evidence.py` (`TRNJ-9`). Each note below names the case that fails if the rule is broken.
## G1 — Thirteen files, and six names in `__init__.py`
`src/training/__init__.py` exports the six names of `README.md` §3 in that order and no seventh — not `RUNGS`, not `TrainingError`, not `_Curve` — and one concern per file (`e2e-surface.md` §1, D-12, `README.md` §4).
Caught by: `test_registry.py::TRN-1.1`, FAM-1.38–FAM-1.43.
## G2 — The registry is nine literals and the ±2% arithmetic is the point
`RUNGS` holds exactly `registry.md` §1's nine rows — backends, encodings, kinds, 36/2, 50/2, 62/1, 62/2 at 0.5, 50/2 at residual, and the counts 10,119 / 10,053 / 10,047 / 10,109. A width "rounded" to 60, a `sparse` at width 50, or a `wide` declared at depth 2 leaves ASM-10's band and FAM-3.15 fails on the pair, not on a curve.
Caught by: `test_registry.py::TRN-1.2` (each row's four settings and its count), FAM-3.15, FAM-13.3.
## G3 — The pool entry filters by readability, and the id is the read-back
`_window` drops every declared version whose `path` names no readable file, `build_pool` is called on the filtered declaration, and `id` is `pool_members`' read-back. Hard-coding a pool id, or declaring a window without filtering it, makes a resolved rung name a version it cannot load and fails the run at step 2 (`registry.md` §3, `protocol.md` §5).
Caught by: `test_registry.py::TRN-1.3`, `TRN-1.4`, FAM-3.17, FAM-16.31.
## G4 — The snapshot interval is `budget // 10`, not the declared `snapshot_every`
The declared 100 is the *declared* budget's interval and is recorded in the record's `variants`; the interval a run uses is `budget // 10`. Honouring the declared value at 250 hands writes two snapshots, names three artefacts and fails FAM-12.4's five-version window; at 60 hands it writes none.
Caught by: `test_curves.py::TRN-5.1`, `test_loop.py::TRN-2.1` (a 250-hand run writes ten and names six), FAM-12.1, FAM-12.4.
## G5 — Six artefacts named per variant × seed, never eleven
The record names the last M = 5 snapshots plus `final.ckpt`. `tests/e2e/_records.py`'s `checkpoint_span` allows at most `pairs × (M + 1)`, which is exactly 6 for one pair and 12 for the custom two-variant rung: naming the ten plus the final is 11 and fails both families (`checkpoints.md` §3).
Caught by: `test_checkpoints.py::TRN-6.1`, FAM-12.1, FAM-15.1, FAM-16.29.
## G6 — The record's keys, and the nesting each reader assumes
`curves` is variant → seed → `{samples, td_error, spread}`; `checkpoints` is variant → seed → `{snapshots, final}`; `timings` is
variant → seed → `{hands, wall_clock_seconds, seconds_per_hand, hands_per_second}`. The four timing keys are read by what they
name — `hands` as the hands, `seconds_per_hand` as the per-hand cost, `hands_per_second` as the throughput — so renaming them to
`perf`, `t` or `rate` loses the D-7 evidence reader (`loop.md` §4, `records.md` §12).
Caught by: `test_loop.py::TRN-2.2`–`TRN-2.4`, FAM-13.5.
## G7 — A transition's `action` is an index, and a terminal transition carries its own mask
`legal_indices` is position-aligned, so the index is the descriptor's position in `legal`; passing the descriptor itself, or the raw episode `action` field, is refused by `agents.learn` on its first call. The terminal transition repeats its own `next_observation`/`next_legal`, because it has no successor and an empty mask is illegal (`episode.md` §3–§4).
Caught by: `test_episode.py::TRN-4.2`, `TRN-4.3`.
## G8 — One pool id per record, and it is the declared one
The record's `pool.id` is the configuration's declared id and the read-back digest id is carried nowhere. Two ids in one
two-variant record makes `pool_identity` see two pools and fails FAM-3.18; dropping the declared id fails FAM-15.2.
Caught by: `test_loop.py::TRN-2.5`, FAM-3.18, FAM-15.2.
## G9 — The seed payload, byte for byte
`b"pypoker-training/" + domain + b"/v1" + b"\x1f" + seed + b"\x1f" + index`, the first eight bytes big-endian, modulo `2**63`. A `hash()` instead of `sha256` is process-salted, a missing separator collides `(1, 23)` with `(12, 3)`, and `seed + i` makes every rung at one seed play identical hands (`seeds.md` §2).
Caught by: `test_seeds.py::TRN-3.1`–`TRN-3.3`, FAM-4.3, FAM-4.8.
## G10 — A hand with no learner decision makes no `learn` call
When the opponent on the button folds preflop before the big blind acts, that seat's list is empty: no update, no signal, no error. Calling `learn` with `[]` is a refusal, and inventing a zero-reward transition is a shaped reward (`episode.md` §3, `loop.md` §1 step 6).
Caught by: `test_episode.py::TRN-4.4`, `test_curves.py::TRN-5.3`.
## G11 — The index is declared, never scanned
`_entries()` reads `SHIPPED`, `SHIPPED_RULES`, `SHIPPED_FINALS` and `SHIPPED_WINDOWS`; no entry point calls `os.listdir` or `os.walk`. A scan lists the
battery's own scratch checkpoints, and FAM-16.31's `carried` assertion names exactly those.
Caught by: `test_index.py::TRN-I1.1` (a scratch file in `checkpoints/` is not listed), FAM-16.31.
## G12 — Each artefact is listed exactly once
`checkpoint_path_listing` counts listings, repeats included: one list of entries, no second copy of any path, and `shipped` holds rung names rather than paths. A window that also names a pair's `final.ckpt`, or a "finals" list beside the entries, fails on the first repeat (`checkpoints.md` §4).
Caught by: `test_checkpoints.py::TRN-6.2`, FAM-12.6.
## G13 — What ships, and no path for a run that does not exist
`shipped` is `["R1"]`: 3 seeds × 6 artefacts = 18 paths, each of which exists. R2–R6 contribute nothing until their runs exist.
Fabricating an R4 path to look complete fails the existence check; filtering the index by what is on disk instead is a scan (G11).
Caught by: `test_checkpoints.py::TRN-6.3`, FAM-12.5, FAM-16.31.
## G14 — `fairness` compares `architecture` only when family and `sparsity` agree
R5's `dense` (width 50, sparsity 0) against its `sparse` (width 62, sparsity 0.5) differs on `sparsity` alone; a rule that also
compares width finds two axes, refuses the rung's own control, and fails FAM-3.12. R4's own pair is the converse: one family, one
sparsity, so `width` *and* `depth` differ and the axis is `architecture` (`fairness.md` §2–§3).
Caught by: `test_fairness.py::TRN-7.1`–`TRN-7.3`, FAM-3.11, FAM-3.12, FAM-15.3.
## G15 — `constants` carries thirteen keys, two of them declared here
The game from `engine.game_config`; the action vocabulary and the readout facts as data, because `features.action_space` and
`features.encodings` are not this module's to call. The rule row is `rules`, the **set** the two sides declare, and never a single
value one side carries: dropping the vocabulary or the facts fails FAM-3.14's token scan, and reading `action_space()` breaks D-13's
boundary (`fairness.md` §4, `rules.md` §8, D-19).
Caught by: `test_fairness.py::TRN-7.4`, FAM-3.14, FAM-13.3, FAM-3.19.
## G16 — A refusal names the offending value, and nothing is wrapped
Every message has the four parts of `errors.md` §3 and the value in it: FAM-15.5 and FAM-16.28 compare the unknown rung's token to the message.
`features`', `agents`' and `evaluation`'s refusals propagate unchanged — a `try/except` re-raising one in a `TrainingError` hides the catalogue's owner.
Caught by: `test_errors.py::TRN-9.1`–`TRN-9.3`, FAM-15.5, FAM-16.28.
## G17 — Seats alternate by swapping the two policies
`play_hand(seed, seat0, seat1)` gives seat 0 the button in every hand, so the learner's seat is `i % 2` and the arms swap. Giving
the learner seat 0 in every hand makes half of each curve positional and R1's and R2's deals unequal — the parity pair's two arms
would then differ on something that is not the backend (`episode.md` §1, FAM-13.4).
Caught by: `test_episode.py::TRN-4.5`, FAM-13.4.
## G18 — `devices()` measures the **read-write** open, and asks a backend only after one succeeds (Rev 3)
`os.open(node, os.O_RDWR)` on `/dev/kfd` then `/dev/dri/renderD128`; a denial is followed by a control `O_RDONLY` open of the same node, separating
the sandbox's read-write split from a permissions fault. Every `False` names the node, the operation, `errno.errorcode` and its number, and which of
`devices.md` §2's five texts it is — **measured:** read-only opens succeed while read-write is denied `EACCES`; no `torch` import before the open.
Caught by: `test_devices.py::TRN-8.2`, `TRN-8.4`–`TRN-8.10`, FAM-1.42.
## G19 — `rung()` and `fairness()` are pure
Resolving builds a pool and reads it back; it deals no hand, builds no learner, writes no file and moves no stream. A cached build that writes a scratch pool file, or a `fairness` that imports a learner to compare capacities, breaks D-3 and FAM-3.17's repeated resolution.
Caught by: `test_registry.py::TRN-1.5`, `test_fairness.py::TRN-7.5`.
## G20 — A run writes under the write root; determinism is one build's, under the pin
`run` writes its ten snapshots and its final model under `layout._write_root()` — `checkpoints/` unless `PYPOKER_CHECKPOINT_ROOT` names another — so a
battery's private `mkdtemp` gains every artefact and `<repo>/checkpoints` gains none (`write-root.md` §1, §3, §4, `checkpoints.md` §5). A re-run guarantees
**one build's, one pinned interpreter's** result: with `PYTHONHASHSEED=0` the curves and the table reproduce as measured, unpinned they do not,
`engine.equity`'s sampled estimate following the per-process hash seed (`protocol.md` §4, `evidence.md` §6). `provenance` names the build a bundle came
from, so drift is attributable; what is forbidden is the index listing an artefact the design does not declare (G11, G13).
Caught by: `test_loop.py::TRN-2.7`, `test_checkpoints.py::TRN-6.5`, `test_checkpoints.py::TRN-6.9`, `test_run_record.py::TRNJ-8.1`, FAM-16.31.
## G21 — A declaration the run would discard is refused at resolve, never kept in silence
A `hyper` key and a `snapshot_every` — **at the configuration and at each entry** — are `IgnoredDeclaration` unless they equal that key's
`HYPER` value and the **declared** samples ÷ 10, and a `learning_rule` only when the catalogue `agents.learners()` publishes does not carry
it; two arms declaring two values for one of the **five** shared settings that reach the pair check are `PairDeclarationsDiffer`, naming key and values.
`learning_rule` is not one of the seven: a catalogued rule is forwarded and trained, so refusing a second rule would restore ASM-7's
single-rule clause D-19 retired. A configuration-level block is a declaration no entry can see, so leaving it unchecked drops it exactly as
an entry's would be. Silence is the plateau defect — four sweeps of one model looked like four results (ASM-7, ASM-18, D-19).
Caught by: `test_errors.py::TRN-9.15`–`TRN-9.16`, `test_fairness.py::TRN-7.8`, FAM-17.9, and the contract's test writer's next cases.
## G22 — A declared `param_budget` is validated where it is resolved, never coerced
A `param_budget` that is not a positive integer — `"abc"`, `12345.6`, `True`, `-5` — is `VariantSettingInvalid` naming the key, the level and the
value, so `int()` never truncates a float, reads `True` as 1 or accepts a negative band: the `params` band is the resolved number ∓2% (`declarations.md` §2, ASM-10, `errors.md` §4).
Caught by: `test_errors.py::TRN-9.15`–`TRN-9.16`'s file; the contract's test writer pins every shape next.
## G23 — The rule is read and forwarded, and the record says which estimator trained which curve (Rev 6)
A variant's `learning_rule` — else its configuration's copy, else nothing — goes into the `agents.build_learner` spec as
`"learning_rule"`, so the learner is built under the rule the entry names and an entry naming none passes nothing: `agents` builds the
catalogue's first, and this module never substitutes a rule of its own. The catalogue is read through `agents.learners()`, never a private
copy. `variants[i]` carries `learning_rule` (the rule it was **built** under) and the record carries `rules`, the distinct rules in
declaration order, which is `records.md` §12's required set; `fairness` reports the same set under `constants["rules"]` and the `rule` axis.
Caught by: FAM-17.7–17.9, `tests/e2e/test_fam03_ladder.py::FAM-3.19`, and the contract's test writer's cases for the record's `rules` set.
## G24 — An index entry carries its `rule`, one per shipped run
An entry is a `records.md` §7 version record, so `rule` is **required** beside `kind` (`checkpoints.md` §4, D-19): `_snapshot_entry` and
`_final_entry` read it from `SHIPPED_RULES`, the per-rung declaration beside `SHIPPED`, because no default stands in for one and a rung added
to `SHIPPED` names its rule in the same edit. Without it the retained window a successor inherits cannot be certified and the pool's id covers
no estimator (`records.md` §7, §8, `rules.md` §6, ASM-27).
Caught by: `test_checkpoints.py::TRN-6.3`, `TRN-6.10`, `test_loop.py::TRN-2.16`, `test_index.py::TRNJ-6.4`, FAM-12.8.
