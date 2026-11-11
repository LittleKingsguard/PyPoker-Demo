# training — L4 guardrails

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 14 · **Date:** 2026-11-11 · **Rev 9:** G23/G24 carry the utility axis, and G25 states where the reward is applied (D-20) · **Rev 10:** G26 carries the run's own shape and G27 the greedy pass, and G1/G5/G15/G21 are re-counted to fourteen files, fifteen constants and six pair settings (D-28, D-29, ASM-38) · **Rev 11:** G17 is re-issued as the shape's own rotation seated by `episode._hand`, and G26/G27 name every declared shape and the run's own shape's record bound (`seats.md` §2–§5, `shapes.md` §8, ASM-42, ASM-43, ASM-44, D-33) · **Rev 12:** G27 is re-issued for the **sampled** pass — the hand bound bounds the sample, no run is refused for its budget, and a pass request still is (D-36) · **Rev 13:** G20 points at `test_greedy_sample.py::TRNJ-13.1`, which measures its pinned-interpreter clause in a child pinned to `PYTHONHASHSEED=0` (D-36) · **Rev 14:** G27 also carries the request that is not a positive integer — refused before a hand is dealt — and names TRN-14.9 beside TRN-14.8's checkpoint-pinned prefix (D-36)
- **Owner:** one numbered note per risk this design identified, in the order they bite, each naming its rule and the test that
  catches it — Rev 4 adds G21 (the declaration refusals), Rev 5 G22 (the declared budget), Rev 6 G23 (the member forwarded and the
  record's sets), Rev 9 G25 (the one place a utility is applied), **Rev 10** G26/G27 (the shape forwarded whole, and the pass's
  bounds and its unreported `tie`) and **Rev 11** G17, G26 and G27 re-issued for the seat count and the shape's own record bound, and **Rev 12**
  G27 re-issued for the sampled pass (D-36)
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append
- **Read with:** all of `README.md`, `registry.md`, `loop.md`, `record.md`, `greedy.md`, `seeds.md`, `episode.md`, `reward.md`, `curves.md`, `checkpoints.md`,
  `fairness.md`, `devices.md`, `errors.md`

The unit battery's files are contract: `tests/training/test_registry.py` (`TRN-1.k`), `test_loop.py` (`TRN-2.k`),
`test_seeds.py` (`TRN-3.k`), `test_episode.py` (`TRN-4.k`), `test_curves.py` (`TRN-5.k`), `test_checkpoints.py` (`TRN-6.k`),
`test_fairness.py` (`TRN-7.k`), `test_devices.py` (`TRN-8.k`), `test_errors.py` (`TRN-9.k`); the join battery is
`tests/integration/training/test_run_record.py` (`TRNJ-1`–`4`, `TRNJ-7`–`8`), `test_fairness_joins.py` (`TRNJ-5`),
`test_index.py` (`TRNJ-6`) and `test_evidence.py` (`TRNJ-9`). Each note below names the case that fails if the rule is broken.
## G1 — Fourteen files, and six names in `__init__.py`
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
The record names the last M = 5 snapshots plus `final.ckpt`. `tests/e2e/_records.py`'s `checkpoint_span` allows at most `pairs × (M + 1)`, which is exactly 6 for one pair and 12 for the custom two-variant rung: naming the ten plus the final is 11 and fails both families, and the greedy pass reads `final.ckpt` and writes no seventh (`checkpoints.md` §3, `greedy.md` §1).
Caught by: `test_checkpoints.py::TRN-6.1`, FAM-12.1, FAM-15.1, FAM-16.29.
## G6 — The record's keys, and the nesting each reader assumes
`curves` is variant → seed → `{samples, td_error, spread}`; `checkpoints` is variant → seed → `{snapshots, final}`; `timings` is variant →
seed → `{hands, wall_clock_seconds, seconds_per_hand, hands_per_second}`. The four timing keys are read by what they name — `hands` as the
hands, `seconds_per_hand` as the cost, `hands_per_second` as the throughput — so renaming them loses the D-7 reader (`records.md` §12).
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
R5's `dense` (width 50, sparsity 0) against its `sparse` (width 62, sparsity 0.5) differs on `sparsity` alone; a rule that also compares width finds two axes, refuses the rung's own control, and fails FAM-3.12. R4's own pair is the converse: one family, one sparsity, so `width` *and* `depth` differ and the axis is `architecture` (`fairness.md` §2–§3).
Caught by: `test_fairness.py::TRN-7.1`–`TRN-7.3`, FAM-3.11, FAM-3.12, FAM-15.3.
## G15 — `constants` carries fifteen keys, `shape` first, and two of them declared here
The shape name, the game from `engine.game_config(shape)` and that shape's vocabulary from `declarations.vocabulary(shape)`; the readout facts as data, because `features.action_space` and `features.encodings` are not this module's to call. The rule and utility rows are `rules` and `utilities`, the **sets** the two sides declare, never a single value one side carries: dropping the vocabulary or reporting the default shape's for a pair on the second fails FAM-3.14, and reading `action_space()` breaks D-13's boundary (`rules.md` §8, `utilities.md` §8, `shapes.md` §2–§3, D-20, D-29).
Caught by: `test_fairness.py::TRN-7.4`, `test_shapes.py::TRN-13.6`, FAM-3.14, FAM-13.3, FAM-3.19.
## G16 — A refusal names the offending value, and nothing is wrapped
Every message has the four parts of `errors.md` §3 and the value in it: FAM-15.5 and FAM-16.28 compare the unknown rung's token to the message.
`features`', `agents`' and `evaluation`'s refusals propagate unchanged — a `try/except` re-raising one in a `TrainingError` hides the catalogue's owner.
Caught by: `test_errors.py::TRN-9.1`–`TRN-9.3`, FAM-15.5, FAM-16.28.
## G17 — The learner rotates through the shape's own seats, and `_hand` seats the hand
`episode._seats(shape)` reads `engine.game_config(shape)["seats"]` and `_seat(index, shape)` is `index mod seats`: on a two-seat shape that is the `i % 2` and the two positional policies swap exactly as before, and on a shape with more seats the learner holds each seat for one hand in `seats`. `episode._hand(pool, shape, seed, index, policy)` is the one place a hand is seated, for the loop and the pass alike, and it returns `(played, seat)` — one uncounted `evaluation.opponent` draw and the two positional policies on two seats, one `evaluation.opponent(pool, draw_seed, seats - 1)` draw of **distinct** members with the learner's policy inserted at `seat` and `play_hand(..., seats=(...))` on more (`episode.md` §1, `seats.md` §2–§4, ASM-43, ASM-44, D-33). Writing a `2` or a `6` down here, giving the learner one seat in every hand, or seating a policy twice makes a curve positional and R1's and R2's deals unequal, so the parity pair's two arms would differ on something that is not the backend (FAM-13.4).
Caught by: `test_episode.py::TRN-4.1` and `TRN-4.5` for the two-seat rotation and the successor chain, `test_shapes.py::TRN-13.11`–`TRN-13.12` for the rotation across six seats and the five-opponent draw's refusal boundary, `test_shape_join.py::TRNJ-11.7`–`TRNJ-11.8` for the same two facts at the catalogue's edge, and `test_fam21_seats.py::FAM-21.6`–`FAM-21.7` for the seating at the engine's own edge (`README.md` §4, `battery.md` §5).
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
`engine.equity`'s sampled estimate following the per-process hash seed (`protocol.md` §4, `evidence.md` §6); what is forbidden is the index
listing an artefact the design does not declare (G11, G13).
Caught by: `test_loop.py::TRN-2.7`, `test_checkpoints.py::TRN-6.5`, `test_checkpoints.py::TRN-6.9`, `test_run_record.py::TRNJ-8.1`, FAM-16.31, and — for the "one pinned interpreter's" clause itself — `test_greedy_sample.py::TRNJ-13.1`, which replays a 1,000-hand run in a child pinned to `PYTHONHASHSEED=0`, the pin that capture was taken under, and holds that child's whole summary to the capture field for field, so the project's own unpinned runner measures the pinned claim (`battery.md` §5, D-36).
## G21 — A declaration the run would discard is refused at resolve, never kept in silence
A `hyper` key and a `snapshot_every` — **at the configuration and at each entry** — are `IgnoredDeclaration` unless they equal that key's `HYPER` value and the **declared** samples ÷ 10; a `learning_rule` or a `utility` is refused only when the catalogue `agents.learners()` publishes does not carry it, a `game` only when `engine.game_shapes()` does not, which is `UnknownShape` and not this class; and two arms declaring two values for one of the **six** shared settings that reach the pair check are `PairDeclarationsDiffer`. Neither member is one of the six: a catalogued rule or utility is forwarded and trained, so refusing a second would restore the single-member clause D-19 retired, while a `game` **is** one of them, because a pair is on one shape. A configuration-level block is a declaration no entry can see, so leaving it unchecked drops it as silently as an entry's would be (ASM-7, ASM-18, D-19, D-20, `shapes.md` §1, §6, D-29).
Caught by: `test_errors.py::TRN-9.15`–`TRN-9.16`, `test_shapes.py::TRN-13.7`, `test_fairness.py::TRN-7.8`, FAM-17.9.
## G22 — A declared `param_budget` is validated where it is resolved, never coerced
A `param_budget` that is not a positive integer — `"abc"`, `12345.6`, `True`, `-5` — is `VariantSettingInvalid` naming the key, the level and the value, so `int()` never truncates a float, reads `True` as 1 or accepts a negative band: the `params` band is the resolved number ∓2% (`declarations.md` §2, ASM-10, `errors.md` §4).
Caught by: `test_errors.py::TRN-9.15`–`TRN-9.16`'s file; the contract's test writer pins every shape next.
## G23 — Both members are read and forwarded, and the record says which trained which curve (Rev 6, Rev 9)
A variant's `learning_rule` and its `utility` — else its configuration's copy, else nothing — go into the `agents.build_learner` spec; an entry
naming either passes no key and `agents` builds that catalogue's first, and this module never substitutes one. Both catalogues are read through
`agents.learners()`, never a private copy. `variants[i]` carries `learning_rule` and `utility`, and the record carries `rules` and `utilities`,
the distinct members in declaration order — `fairness` reports the same sets on the `rule` and `utility` axes (`utilities.md` §5, D-20).
Caught by: FAM-17.7–17.9 (`tests/e2e/test_fam17_rules.py`), FAM-18.7–18.9 (`tests/e2e/test_fam18_utilities.py`: 18.7 the run record's `utilities` set and each variant's `utility`), `tests/e2e/test_fam03_ladder.py::FAM-3.19`, FAM-18.10 (a cell's `utilities`, a matrix's `utilities` and its `utility_population`) and FAM-18.11 (a pool member's `utility`, the pool record's `utilities`, and the id that digests it).
## G24 — An index entry carries its `rule` and its `utility`, one of each per shipped run
An entry is a `records.md` §7 version record, so `rule` and `utility` are **required** beside `kind` (`checkpoints.md` §4, D-19, D-20):
`_snapshot_entry` and `_final_entry` read them from `SHIPPED_RULES` and `SHIPPED_UTILITIES`, the per-rung declarations beside `SHIPPED`, because no
default stands in for either and a rung added to `SHIPPED` names both in the same edit; without them the window a successor inherits cannot be certified
and the pool's id covers neither estimator nor objective (`records.md` §7, §8, ASM-27).
Caught by: `test_checkpoints.py::TRN-6.3`, `TRN-6.10`, `test_loop.py::TRN-2.16`, `test_index.py::TRNJ-6.4`, FAM-12.8 for the `rule` and FAM-18.6 for the `utility`.
## G25 — The utility is applied here, terminal-only, selected by reward token
`episode._transitions` re-expresses the **terminal** decision's reward as the variant's utility's number, selected by the token
`agents.learners()` publishes for that member — never by a member name copied into this module — and every other decision keeps `0.0`;
`learner.py`'s branches stay `target = record["reward"]`, so applying it inside `learn` or shaping an intermediate decision breaks D-20 (`reward.md` §1–§4, `utilities.md` §4, ASM-28). Caught by: `test_episode.py::TRN-4.9`–`TRN-4.13` — 4.9 the reward's four numbers, 4.10 the zero every non-terminal decision keeps, 4.11 the unshaped `net-chips` delta, 4.12 the chips-in-play guard and 4.13 the reward token that selects the arithmetic — and `test_shapes.py::TRN-13.3` for the guard reading the run's own total.
## G26 — One shape, resolved once, forwarded whole
`_game(configuration)` resolves the `game` at the configuration, else at its first variant entry, else `DEFAULT_SHAPE`, and refuses an uncatalogued name as `UnknownShape` naming it and **every declared name**. That one name reaches `features.build_encoder(..., shape=)`, `build_learner`'s `game`, `engine.play_hand(..., shape=)`, `episode._hand`'s seating, `_transitions(..., shape)`, `_learner_policy(..., shape)`, `_pool`'s declaration and `_header`'s `game`/`action space`, and it is never `engine.game_config()`'s default: a step that drops it trains or reports the default shape on a run that declared another, and a readout of one shape read against another is `ChipConservationBroken` rather than a silent rescale — the seats a hand is dealt with come from the same name and from no literal (`seats.md` §2–§3, ASM-44, `shapes.md` §2–§3, `loop.md` §1–§2, `episode.md` §1–§3, D-29).
Caught by: `test_shapes.py::TRN-13.1`–`TRN-13.7`, and the shape join of `tests/integration/training/`.
## G27 — The pass samples the run, runs after the save, inside both bounds, and reports no tie
`greedy._pass` is called with the finished learner, the run's shape, the run's seed and `greedy._sample(budget)` — the run's first `min(budget, 2,000)` hands — **after** `agents.save` of the final model, so the block is reproducible from the checkpoint the record names. The hand bound bounds the **sample and never the run**: the per-pair step asks for `_sample(budget)` and no bound is checked at resolve, so the shipped 200,000-hand budget trains and passes over 2,000 hands, while `_check_hands` still refuses a **pass request** above 2,000 naming the count asked for and the bound (D-36). A request that is not a positive integer — a `bool`, a float, a string, 0 or a negative — is refused by that same seam **before** a hand is dealt, naming the request as given and the contract `at least 1 hand and at most 2,000`, so a block's `hands` is always a positive integer equal to `len(net_chips)` and `int()` never truncates a float into an honest-looking count (`errors.md` §4, D-36). `_check_decisions` refuses the moment one more record would cross **the run's own shape's** record bound, `declarations.greedy_decisions(shape)` = 1,000 × `shape_history(shape)`: 24,000 at the default shape, 66,000 and 98,000 on the uncapped ones, the refusal naming the count, the bound, the shape and its capacity; neither clamps, and a pass of exactly a bound is inside it. The sample is `episode._hand`'s prefix, so a six-seat block rotates through six seats and a six-seat pass is refused beyond 98,000 (`seats.md` §4, `shapes.md` §8, ASM-42, ASM-43, D-33). `tie` is `False` on every decision because no granted exploration-off surface reports the flag, so a census must not divide by it and `sizing.md` §7's conjunct 7 is not computable from this block (`greedy.md` §2, §4, §6, `records.md` §15, ASM-38, D-28).
Caught by: `test_greedy.py::TRN-14.1`–`TRN-14.9` — `TRN-14.3` pins `hands` to `min(budget, 2,000)`, `TRN-14.5` drives the record bound of **all three** declared shapes and the pass-side hand refusal naming both counts, `TRN-14.8` measures the prefix hand for hand and holds a two-hand pass built from the run's own final checkpoint to that run's block prefix, `TRN-14.9` refuses 0, a negative, a float and a string by name before a hand is dealt, and `test_greedy_sample.py::TRNJ-13.1` holds a 1,000-hand run to its pre-change capture — `test_shapes.py::TRN-13.10`, `test_shape_join.py::TRNJ-11.6` and `TRNJ-11.9` drive a six-seat pass end to end and assert that its record carries no matrix, and `test_default_baseline.py::TRNJ-12.1` holds a default-shape record to a capture taken before the third shape landed, so the absence reproduces today's value (`shapes.md` §5, `battery.md` §5, `README.md` §4). §6's limitation is a named `ADJUDICATION` rather than a case, because no case can observe a flag no granted call returns.
