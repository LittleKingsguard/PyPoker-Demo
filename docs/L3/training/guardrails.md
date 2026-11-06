# training — L4 guardrails

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-05
- **Owner:** one numbered note per risk this design identified, in the order they bite, each naming its rule and the test that
  catches it
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append
- **Read with:** all of `README.md`, `registry.md`, `loop.md`, `seeds.md`, `episode.md`, `curves.md`, `checkpoints.md`,
  `fairness.md`, `devices.md`, `errors.md`

The unit battery's files are contract: `tests/training/test_registry.py` (`TRN-1.k`), `test_loop.py` (`TRN-2.k`),
`test_seeds.py` (`TRN-3.k`), `test_episode.py` (`TRN-4.k`), `test_curves.py` (`TRN-5.k`), `test_checkpoints.py` (`TRN-6.k`),
`test_fairness.py` (`TRN-7.k`), `test_devices.py` (`TRN-8.k`), `test_errors.py` (`TRN-9.k`); the join battery is
`tests/integration/training/test_run_record.py` (`TRN-I1.k`), `test_index.py` (`TRN-I2.k`), `test_fairness_joins.py`
(`TRN-I3.k`). Each note below names the case that fails if the rule is broken.
## G1 — Fourteen files, and six names in `__init__.py`
`src/training/__init__.py` exports the six names of `README.md` §3 in that order and no seventh — not `RUNGS`, not
`TrainingError`, not `_Curve` (`e2e-surface.md` §1, D-12). One concern per file (`README.md` §4).
Caught by: `test_registry.py::TRN-1.1`, FAM-1.38–FAM-1.43.
## G2 — The registry is nine literals and the ±2% arithmetic is the point
`RUNGS` holds exactly `registry.md` §1's nine rows — backends, encodings, kinds, 36/2, 50/2, 62/1, 62/2 at 0.5, 50/2 at
residual, and the counts 10,119 / 10,053 / 10,047 / 10,109. A width "rounded" to 60, a `sparse` at width 50, or a `wide` declared
at depth 2 leaves ASM-10's band and FAM-3.15 fails on the pair, not on a curve.
Caught by: `test_registry.py::TRN-1.2` (each row's four settings and its count), FAM-3.15, FAM-13.3.
## G3 — The pool entry filters by readability, and the id is the read-back
`_window` drops every declared version whose `path` names no readable file, `build_pool` is called on the filtered declaration,
and `id` is `pool_members`' read-back. Hard-coding a pool id, or declaring a window without filtering it, makes a resolved rung
name a version it cannot load and fails the run at step 2 (`registry.md` §3, `protocol.md` §5).
Caught by: `test_registry.py::TRN-1.3`, `TRN-1.4`, FAM-3.17, FAM-16.31.
## G4 — The snapshot interval is `budget // 10`, not the declared `snapshot_every`
The declared 100 is the *declared* budget's interval and is recorded in the record's `variants`; the interval a run uses is
`budget // 10`. Honouring the declared value at 250 hands writes two snapshots, names three artefacts and fails FAM-12.4's
five-version window; at 60 hands it writes none.
Caught by: `test_curves.py::TRN-5.1`, `test_loop.py::TRN-2.1` (a 250-hand run writes ten and names six), FAM-12.1, FAM-12.4.
## G5 — Six artefacts named per variant × seed, never eleven
The record names the last M = 5 snapshots plus `final.ckpt`. `tests/e2e/_records.py`'s `checkpoint_span` allows at most
`pairs × (M + 1)`, which is exactly 6 for one pair and 12 for the custom two-variant rung: naming the ten plus the final is 11 and
fails both families (`checkpoints.md` §3).
Caught by: `test_checkpoints.py::TRN-6.1`, FAM-12.1, FAM-15.1, FAM-16.29.
## G6 — The record's keys, and the nesting each reader assumes
`curves` is variant → seed → `{samples, td_error, spread}`; `checkpoints` is variant → seed → `{snapshots, final}`; `timings` is
variant → seed → `{hands, wall_clock_seconds, seconds_per_hand, hands_per_second}`. The four timing keys are read by what they
name — `hands` as the hands, `seconds_per_hand` as the per-hand cost, `hands_per_second` as the throughput — so renaming them to
`perf`, `t` or `rate` loses the D-7 evidence reader (`loop.md` §4, `records.md` §12).
Caught by: `test_loop.py::TRN-2.2`–`TRN-2.4`, FAM-13.5.
## G7 — A transition's `action` is an index, and a terminal transition carries its own mask
`legal_indices` is position-aligned, so the index is the descriptor's position in `legal`; passing the descriptor itself, or the
raw episode `action` field, is refused by `agents.learn` on its first call. The terminal transition repeats its own
`next_observation`/`next_legal`, because it has no successor and an empty mask is illegal (`episode.md` §3–§4).
Caught by: `test_episode.py::TRN-4.2`, `TRN-4.3`.
## G8 — One pool id per record, and it is the declared one
The record's `pool.id` is the configuration's declared id and the read-back digest id is carried nowhere. Two ids in one
two-variant record makes `pool_identity` see two pools and fails FAM-3.18; dropping the declared id fails FAM-15.2.
Caught by: `test_loop.py::TRN-2.5`, FAM-3.18, FAM-15.2.
## G9 — The seed payload, byte for byte
`b"pypoker-training/" + domain + b"/v1" + b"\x1f" + seed + b"\x1f" + index`, the first eight bytes big-endian, modulo `2**63`. A
`hash()` instead of `sha256` is process-salted, a missing separator collides `(1, 23)` with `(12, 3)`, and `seed + i` makes every
rung at one seed play identical hands (`seeds.md` §2).
Caught by: `test_seeds.py::TRN-3.1`–`TRN-3.3`, FAM-4.3, FAM-4.8.
## G10 — A hand with no learner decision makes no `learn` call
When the opponent on the button folds preflop before the big blind acts, that seat's list is empty: no update, no signal, no
error. Calling `learn` with `[]` is a refusal, and inventing a zero-reward transition is a shaped reward (`episode.md` §3,
`loop.md` §1 step 6).
Caught by: `test_episode.py::TRN-4.4`, `test_curves.py::TRN-5.3`.
## G11 — The index is declared, never scanned
`_entries()` reads `SHIPPED_FINALS` and `SHIPPED_WINDOWS`; no entry point calls `os.listdir` or `os.walk`. A scan lists the
battery's own scratch checkpoints, and FAM-16.31's `carried` assertion names exactly those.
Caught by: `test_index.py::TRN-I1.1` (a scratch file in `checkpoints/` is not listed), FAM-16.31.
## G12 — Each artefact is listed exactly once
`checkpoint_path_listing` counts listings, repeats included: one list of entries, no second copy of any path, and `shipped` holds
rung names rather than paths. A window that also names a pair's `final.ckpt`, or a "finals" list beside the entries, fails on the
first repeat (`checkpoints.md` §4).
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
`features.encodings` are not this module's to call. Dropping them fails FAM-3.14's token scan; reading `action_space()` breaks
D-13's boundary (`fairness.md` §4).
Caught by: `test_fairness.py::TRN-7.4`, FAM-3.14, FAM-13.3.
## G16 — A refusal names the offending value, and nothing is wrapped
Every message has the four parts of `errors.md` §3 and the value in it: FAM-15.5 and FAM-16.28 compare the unknown rung's token to
the message. `features`', `agents`' and `evaluation`'s refusals propagate unchanged — a `try/except` around `build_learner` that
re-raises a `TrainingError` hides which module owns the catalogue.
Caught by: `test_errors.py::TRN-9.1`–`TRN-9.3`, FAM-15.5, FAM-16.28.
## G17 — Seats alternate by swapping the two policies
`play_hand(seed, seat0, seat1)` gives seat 0 the button in every hand, so the learner's seat is `i % 2` and the arms swap. Giving
the learner seat 0 in every hand makes half of each curve positional and R1's and R2's deals unequal — the parity pair's two arms
would then differ on something that is not the backend (`episode.md` §1, FAM-13.4).
Caught by: `test_episode.py::TRN-4.5`, FAM-13.4.
## G18 — `devices()` probes the nodes, and asks a backend only after one opens (Rev 2)
`os.open` on `/dev/kfd` and `/dev/dri/renderD128`, closing the handle after; a `PermissionError` is `"PERMISSION"`, a missing node
`"ABSENT"`. **Measured:** both nodes open on this host while `torch` reports no usable device, so the node test alone would report a
GPU the workflow cannot use; the probe therefore asks the backend once, after a node opened, and reports its refusal as the reason
(`devices.md` §2). No `torch` import happens on a platform without the nodes, and none at module scope.
Caught by: `test_devices.py::TRN-8.1`, `TRN-8.2`, FAM-1.42.
## G19 — `rung()` and `fairness()` are pure
Resolving builds a pool and reads it back; it deals no hand, builds no learner, writes no file and moves no stream. A cached
build that writes a scratch pool file, or a `fairness` that imports a learner to compare capacities, breaks D-3 and FAM-3.17's
repeated resolution.
Caught by: `test_registry.py::TRN-1.5`, `test_fairness.py::TRN-7.5`.
## G20 — A run writes into `checkpoints/`, and that is intended
`run` writes its snapshots and its final model under `checkpoints/<rung>/<variant>/seed-<seed>/`, so a battery run at seed 6174
adds files there and a run at the declared budget and seed set rewrites the shipped ones with the same content. That is the design
(every checkpoint is a run's artefact, `module-map.md` §5); what is forbidden is the index listing them without a declaration
(G11, G13).
Caught by: `test_index.py::TRN-I1.2`, FAM-16.31.
