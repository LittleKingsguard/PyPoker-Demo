# training — module design (L3)

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-05
- **Owner:** the module — what it is, the document map, the six names, the layout of `src/training/`, the import boundary, the facts it inherits, and the decisions a later module must not re-derive
- **Realises:** `docs/L2/training/surface.md` (the six entry points) and `docs/L2/training/loop.md` (the registry as data, the one loop, what a comparison holds constant, budgets, the checkpoints, the contracts at this edge)
- **Reads:** `docs/L1/e2e-surface.md` §1, §2, §3.5, §5, `records.md` §1–§5, §7–§8, §12, `ladder.md` §1–§6, `protocol.md` §1–§6, `league.md` §1–§7, `module-map.md` §1–§5, `assumptions.md` (ASM-2, ASM-5, ASM-7–ASM-10, ASM-12, ASM-14, ASM-16, ASM-18),
  `battery.md` §2–§5, `strata/decisions.md` (D-2, D-3, D-5, D-7, D-8, D-16), `strata/brief.md` §2–§5, `strata/platform.md`; at the
  consumed edge `docs/L2/evaluation/surface.md` §3–§8, §12, `evaluation/league.md` §1–§6, `docs/L2/agents/surface.md` §3–§8,
  §3–§9 of `features/surface.md`, §3–§10 of `engine/surface.md`
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append
- **Read with:** `registry.md` (§1), `loop.md` (§2, §4), `seeds.md` (§3), `episode.md` (§5), `curves.md` (§6), `checkpoints.md`
  (§7), `fairness.md` (§8), `devices.md` (§9), `errors.md` (§10), `guardrails.md`
- **Implements:** `src/training/`, `notebooks/` and `checkpoints/`, written by L4 and never by L3; `tests/training/` is the unit
  battery and `tests/integration/training/` the join battery; the L1 battery's share is `test_fam03_ladder.py`, `test_fam04_seeds.py`,
  `test_fam12_checkpoints.py`, `test_fam13_parity.py`, `test_fam15_custom.py`, `test_fam16_blind.py` (FAM-16.28–16.31) and
  `test_fam01_surface.py` (FAM-1.38–1.43)

## 1. What this module is

`training` **is** the rung registry plus the one training loop every rung is a configuration of (D-3): it declares the
lineage it inherits, freezes the pool that lineage yields before a variant trains, draws each hand's opponent from that
pool, plays the hands through `engine` on an observation from `features` and a decision and update from `agents`, and
returns the run record (`module-map.md` §1, §3, D-16). It claims no result, measures no cell, fits no rating and never
chooses the membership (D-16, ASM-16), so a rung-to-rung difference belongs to the configuration and to nothing else and a
seventh configuration runs without new code (D-3, FAM-15). Its other two owned paths are data: `notebooks/`, one thin notebook
per rung calling declared entry points only (D-5, `ladder.md` §7), and `checkpoints/`, the shipped models and the
intra-run snapshots the pool is a view over (`module-map.md` §5, ASM-18).

## 2. The documents, one per owner

| Document | Owns | What it fixes |
|---|---|---|
| `registry.md` | `rungs()`, `rung()` | the six rows as literal data (§1), the resolved configuration key by key (§2), the pool entry and the read-back id (§3), the parameter arithmetic (§4) |
| `loop.md` | `run()` | the nine steps (§1), `_train_variant_seed` (§2), the run record key by key (§3), the defaults (§5), refusals (§6), determinism (§7) |
| `seeds.md` | the derivations | the `sha256` payload for the deal and opponent seed (§2), both arms on one deal (§3), the learner seed (§4) |
| `episode.md` | one episode → transitions | `_seat` (§1), decision ordering and the terminal flag (§3), `reward`, `next_legal` (§4), the batch (§5) |
| `curves.md` | the ten points | the axis (§2), the signal (§3), the spread (§4), the curve record (§5) |
| `checkpoints.md` | the artefacts and the index | the layout and names (§1–§2), the ten snapshots and the retained five (§3), `checkpoints()` (§4), what ships (§5) |
| `evidence.md` | the shipped evidence file | `checkpoints/evidence/r1-live.json`: its status (§1), its sixteen keys (§2), the measurement it holds and the two blocks it spells differently from a run today (§3), the two curve layouts (§4), declared budget against measured count (§5), the producer recipe (§6), what it is not (§7) |
| `fairness.md` | `fairness()` | the two argument shapes (§1), the five axes and their matching rule (§2), the eight reportable pairs (§3), `constants` (§4), the pool report (§5) |
| `devices.md` | `devices()` | the record (§1), the probe (§2), what a run records (§3) |
| `errors.md` | refusals | the classes (§2), the message grammar (§3), one canonical message per refusal (§4) |
| `guardrails.md` | L4 | one numbered note per risk, in the order they bite, each naming the test that catches it |

## 3. The six names

`src/training/__init__.py` exports exactly the six entry points of `e2e-surface.md` §3.5 in that order, declares them in
`__all__`, and adds, removes and renames none (D-12):

    rungs()                                          -> Mapping  # the six resolved configurations, brief §2's order
    rung(name)                                       -> Mapping  # one resolved configuration, or UnknownRung
    run(rung, seeds=None, budget=None, device=None)  -> Mapping  # records.md §12's record plus `variants`
    fairness(left, right)                            -> Mapping  # {pair, axis, constants, pool}
    devices()                                        -> Mapping  # {available, default, gpu}
    checkpoints()                                    -> Mapping  # {entries, shipped}

`RUNGS`, `HYPER`, `_Curve`, `TrainingError` and its subclasses and every `_`-name stay below an entry point and are **not**
surface (`surface.md` §1); no returned record exposes a learner, an encoder, a policy or a pool (D-1).

## 4. The layout of `src/training/` (D9)

    __init__.py     the six entry points, __all__, and nothing else (§3)
    errors.py       TrainingError and its subclasses (errors.md §2)
    declarations.py SEEDS, LIVE_BUDGET, PARAM_BUDGET, HYPER, LEARNING_RULE, TABLE, DEVICE, RETAINED, SNAPSHOTS, RUNGS
    registry.py     rungs(), rung(), _configuration(), _pool_entry(), _window(), RUNG_NAMES (registry.md)
    seeds.py        _derive(), _deal_seed(), _opponent_seed() (seeds.md)
    policies.py     _learner_policy() (episode.md §2)
    episode.py      _seat(), _transitions() (episode.md)
    curves.py       _Curve, _axis(), _spread() (curves.md)
    loop.py         run(), _train_variant_seed(), _timings(), _record() (loop.md)
    fairness.py     fairness(), _sides(), _axis(), _constants() (fairness.md)
    devices.py      devices(), _gpu() (devices.md)
    layout.py       ROOT, _final_path(), _snapshot_path(), _relative(), _resolve(), _resolved() (checkpoints.md §1)
    index.py        checkpoints(), SHIPPED_FINALS, SHIPPED_WINDOWS, _entries() (checkpoints.md §4)

`RETAINED` is M = 5 and `SNAPSHOTS` is 10 — ASM-18's two numbers, in one place. Fourteen files, one concern each, and the
private names in `declarations.py`, `registry.py`, `seeds.py`, `episode.py`, `curves.py`, `layout.py`, `index.py` and
`fairness.py` are contract for `tests/training/`.

## 5. The import boundary (D10)

`training` imports the standard library (`hashlib`, `json`, `math`, `os`, `statistics`, `time`, `collections.abc`,
`typing`) and exactly the granted calls (`module-map.md` §2, D-13):

    evaluation  protocol, league, build_pool, pool_members, opponent  — never match, matrix, rating, report, offer, policy_from
    agents      build_learner, act, learn, save                       — never as_policy, load, param_count, baselines, learners
    features    build_encoder, encode, observation_spec, legal_indices, decode_action  — never encodings(), action_space()
    engine      game_config, new_hand, play_hand, payoffs             — never readout, legal_actions, apply_action, is_terminal

Never `harness`, never `pokerkit`, and no numerical library at module scope: the one conditional import in the module is `devices.py`'s backend probe, which imports `torch` **only after** a GPU device node has opened, once per process, and reports the backend's own refusal as the reason the GPU is unavailable (`devices.md` §2, Rev 2, measured). The learner's side of a hand is a policy **assembled here** from `features.encode` + `features.legal_indices` + `agents.act` + `features.decode_action`, because `agents.as_policy` is not this module's to call (`episode.md` §2). `math`/`statistics` serve the curve (`curves.md` §3), and no call here seeds or advances the global `random` stream; only dealing moves it (ASM-2).

## 6. Facts inherited from the four modules this one calls

- `engine.play_hand(seed, seat0, seat1)` deals at that seed and returns `records.md` §5's episode record; seat 0 holds the button in **every** hand, so seats alternate by swapping the policies (ASM-12, `engine/surface.md` §4, §10, `league.md` §3).
- `features.legal_indices` is **position-aligned** with its argument, so a chosen descriptor becomes its vocabulary index by
  position and no second legality channel is invented; `agents.act` returns a mapping whose `action` is the chosen index;
  `agents.learn` consumes the caller's order and returns `td_error`, the mean absolute TD error (`agents/surface.md` §6, §7,
  `features/surface.md` §8, §9).
- `agents.save` writes exactly the path given and invents no directory; `evaluation.build_pool` freezes one declaration and `pool_members` reads back `id`, `m`, `frozen` and the ordered members with the three baselines (`evaluation/surface.md` §5).

## 7. The decisions this design fixed, each with the alternative it rejected

| # | Decision | Why | Rejected alternative |
|---|---|---|---|
| 1 | the six rows are one literal table in `declarations.py` (registry.md §1) | a rung is data, so no rung drifts into a copy of the loop (D-3, FAM-15) | a function per rung, which is six loops under one name |
| 2 | the snapshot interval is `budget // 10` at the budget the run was given (loop.md §2) | ASM-18 wants ten equally spaced snapshots at **any** budget, and the battery runs 60 and 250 | the declared `snapshot_every`, which yields two snapshots at 250 hands (FAM-12.4) |
| 3 | deal and opponent seeds are a `sha256` derivation of `(seed, hand index)` (seeds.md §2) | both arms must play the same hands, and no stream may be drawn on (ASM-2, ASM-16) | `seed + i`, which correlates adjacent hands and collides across rungs |
| 4 | the learner's side is a policy assembled from `encode`/`legal_indices`/`act`/`decode_action` (episode.md §2) | `as_policy` is not granted here (`module-map.md` §2) | calling `agents.as_policy`, a sixth `agents` call |
| 5 | the run record's `pool.id` is the **declared** id; the read-back digest is never carried (loop.md §3) | one id per record proves both arms held one pool (FAM-3.18, ASM-16) | carrying both, which makes a record declare two pools |
| 6 | the index is declared data in `index.py`, one listing per artefact (checkpoints.md §4) | never a directory scan, so a scratch file is not a shipped artefact (FAM-16.31) | `os.walk`, which lists the battery's own scratch files |
| 7 | `fairness` compares `architecture` only when family and `sparsity` agree (fairness.md §2) | a capacity match is the *compensation* for another axis (ASM-10) | comparing width always, which refuses R5's pair on two axes (FAM-3.12) |
| 8 | a path is **written** absolute and **recorded** repository-relative, and read back through `layout._resolve` from the repository root (checkpoints.md §2) | a record that names one machine's home directory cannot travel with the tree or be read elsewhere, and `protocol.md` §5 makes the record portable (D-8, D-6) | absolute paths in the record, which is what the shipped evidence bundle first carried, so nothing but the machine that made it could read it |

## 8. Decisions a later module must not re-derive

1. **A rung is a row of data and `run` is the only path into the loop**; `rung(name)` never resolves a configuration (D-3).
2. **The interval is `budget // 10` and every seed is a `hashlib` derivation of `(seed, index)`, never a draw** (seeds.md §2).
3. **A transition's `action` is an index, and a terminal transition carries its own `next_legal`** (episode.md §3–§4).
4. **The record names the retained five and the final model, and carries one pool id: the declared one** (loop.md §3).
