# agents — L4 guardrails

- **Owner:** one numbered note per risk this design identified, in the order they bite, each naming its rule and test
- **Ceiling:** 165 lines. At the ceiling, split by owner — never append
- **Read with:** all of `README.md`, `rule.md`, `utility.md`, `architecture.md`, `backends.md`, `checkpoint.md`,
  `restore.md`, `baselines.md`, `errors.md`

Each note is a place where a plausible implementation breaks a contract the unit battery (`tests/agents/`, cases
`AGT-<family>.<k>`) or the L1 battery (`tests/e2e/`) asserts; a note's **Unverified** clause names what no case drives.

## G1 — Ten names, and `__all__` in the L1 order

`src/agents/__init__.py` exports exactly the ten names of `README.md` §3 in that order and no eleventh — not
`Learner`, not `AgentsError`, not `KINDS`, not either catalogue (`e2e-surface.md` §1, D-12, `features/layout.md` §2).

Caught by: `test_surface.py::test_agt1_2_all_is_exactly_the_ten_in_the_l1_order`,
`test_guardrails.py::test_agt11_g1_all_is_the_ten_names_in_order`, FAM-1.17–1.26.

## G2 — `act` returns a plain Python `int`, in a mapping

`action` is `int(index)`, never `numpy.int64` and never a `bool`, in a mapping (`records.md` §6, `surface.md` §6). The
L1 reader `S.action_index` in `tests/e2e/_surface.py` accepts only a plain `int`, so a numpy scalar reports a bad return.

Caught by: `test_act.py::test_agt5_1_the_action_is_a_plain_int_in_a_mapping`,
`test_guardrails.py::test_agt11_g2_the_action_is_a_plain_int`, FAM-1.20, FAM-12.2, FAM-16.14.

## G3 — The exploration is keyed by the decision, not by a stream

`act` derives `u` and `v` from §4's payload each call through `rule.py`'s `_decision_key(seed, family, observation, mask)`
(`rule.md` §8), consuming no generator and keeping no counter, so FAM-12.2 would flap if a call advanced anything.

Caught by: `test_act.py::test_agt5_4_two_calls_at_one_decision_agree` and
`test_guardrails.py::test_agt11_g3_two_calls_at_one_decision_agree`, FAM-16.17.

## G4 — One initialisation order, drawn by NumPy for both backends

`architecture.md` §4's five steps, from `numpy.random.Generator(numpy.random.PCG64(seed))`, He-normal weights and
zero biases. The torch backend **copies** them (`torch.from_numpy(...).clone()` — `from_numpy` shares memory) and
never draws its own with `torch.randn`.

Caught by: `test_guardrails.py::test_agt11_g4_both_backends_answer_one_decision_alike` and `::test_agt11_g4b_both_backends_start_from_one_draw`,
plus `test_param_count.py::test_agt4_3` and the kind axes AGT-13.1–13.3 with `test_backends.py` AGT-14.1–14.3.

## G5 — The tie-break is the tolerance rule, never a bare `argmax`

`rule.md` §5: the masked maximum, then the smallest masked index within `1e-9 × max(1, |best|)`. A bare `argmax`
over three values lets the backend's last bits decide, and a `numpy.argmax`-style maximum is not defined on the mask.

Caught by: FAM-13.4, `test_rule.py::test_agt12_3_the_tie_break_is_the_tolerance_rule` (near-tie triples through
`_tie_break(values, mask)`) and, only for membership, `test_act.py::test_agt5_2` — a fresh learner explores at `1.0`.

## G6 — `torch` is imported lazily, and nothing touches a GPU

`import torch` lives in `torch_backend.py` at build time and nowhere else; no module-level torch import, no torch
type in a signature, no `.to("cuda")`, no `torch.cuda.*`; `import agents` leaves `torch` and `pokerkit` out of
`sys.modules` (`README.md` §6, `backends.md` §4, `strata/platform.md`).

Caught by: `test_guardrails.py::test_agt11_g6_the_numpy_path_never_imports_torch_or_pokerkit` (a clean interpreter,
after a numpy build, `act`, `save` and `load`) and `test_guardrails.py::test_agt11_g6b_a_torch_learner_runs_on_the_cpu_without_a_device`.

## G7 — `learn` consumes the caller's order, one step per transition

No sampling, shuffling, dedup, replay or second pass, and no refusal of a batch whose length differs from
`batch_size` (32) — the battery hands six transitions (`rule.md` §3, `ladder.md` §5).

Caught by: `test_learn.py::test_agt6_4_the_batch_order_is_the_callers`,
`test_guardrails.py::test_agt11_g7_a_six_transition_batch_is_consumed`, FAM-1.21, FAM-16.15.

## G8 — `td_error` and `transitions` are plain and finite

`td_error` a plain `float`, the batch's mean absolute TD error; `transitions` a plain `int`, the records consumed;
nothing else in the mapping (`rule.md` §3, `surface.md` §7).

Caught by: `test_learn.py::test_agt6_1_the_statistics_are_the_two_declared_keys` and
`test_guardrails.py::test_agt11_g8_the_statistics_are_plain_and_finite`, FAM-16.15.

## G9 — The target copy, the counter, and which estimate reads which

`q'` is read from the target copy, refreshed only when the consumed-transition counter reaches
`target_update_interval` (200), then reset; reading `q'` online, or refreshing per batch, changes the rule. Under
`double-q-learning` the index is chosen from the **online** parameters' values at `s'` and the value read at that index
from the **target copy**: taking the index from the copy, or the value from the online parameters, is a different rule.

Caught by: `test_learn.py::test_agt6_2_the_signal_is_real`, `test_agt6_3_a_terminal_reward_is_the_target` and AGT-6.8
(the two targets on one transition), `test_guardrails.py::test_agt11_g9_the_target_is_unmoved_within_one_step`,
AGT-11.g9b and AGT-11.g9c (`_read_metadata`'s `target.counter`: `0` fresh, `0` again at `target_update_interval`).
**Unverified**: nothing — every clause here has a case.

## G10 — `param_count` is one formula, excludes buffers, and returns a plain `int`

`architecture.md` §5's formula is `model.py`'s `_param_count_for(kind, width, depth, sparsity)`, so a case compares
against it, not a magic number; `S.is_count` accepts a `numpy.int64`, so only the unit battery catches a numpy count.

Caught by: `test_param_count.py::test_agt4_1_the_count_is_a_plain_positive_int` and
`test_guardrails.py::test_agt11_g10_param_count_is_one_formula`, FAM-13.3, FAM-16.12, FAM-16.13.

## G11 — `save` writes exactly the caller's path, through an open handle

`checkpoint.md` §2: `open(path, "wb")`, then a `zipfile.ZipFile` on that handle, members `metadata.json` and
`parameters.npy`, `ZIP_STORED`; never `numpy.savez`, never `os.makedirs`; the return is the caller's path, a `str`.

Caught by: `test_checkpoint.py::test_agt7_1_save_writes_exactly_the_path_it_was_handed` and
`test_guardrails.py::test_agt11_g11_save_writes_exactly_the_callers_path`, FAM-1.22, FAM-16.16, FAM-16.26.

## G12 — The checkpoint carries the seed, the position, the target copy, the masks, the rule and the utility

`checkpoint.md` §1–§2.1: a file with only the parameters restores a learner that decides differently as soon as any
exploration is in play, `as_policy` needing the recorded seed and `act` the position. A version-3 file **requires**
`learning_rule` and `utility`, a version-2 one the rule alone, a version-1 one neither and is read as both defaults;
an older file recording a field its version forbids is refused by name (`checkpoint.md` §3, `utility.md` §3, D-20).

Caught by: `test_checkpoint.py::test_agt7_2_the_round_trip_keeps_the_decision`, `test_guardrails.py::test_agt11_g12_a_checkpoint_carries_the_seed_and_the_position`,
`test_checkpoint.py` AGT-7.14 (rule and utility recorded), AGT-7.15 (a version-1 container read as the two defaults), FAM-12.2.

## G13 — `load` compares the enumerated keys and nothing else

`backend`, kind, `seed`, `learning_rule` and `utility` when the spec names one, and the encoder's representation and
size when the spec carries one. **Not** width or depth (a spec may name its kind bare), never `sizes`; other extra keys
are ignored (`checkpoint.md` §3, `surface.md` §9).

Caught by: `test_checkpoint.py::test_agt7_5_a_disagreeing_spec_is_refused_naming_the_key` and
`test_guardrails.py::test_agt11_g13_load_compares_only_the_enumerated_keys`, FAM-1.23, FAM-12.2.

## G14 — Refuse exactly what the contract refuses, before writing anything

Every refusal of `errors.md` §2–§3 and no other, each checked before the first mutation, copy and file handle
(`errors.md` §4). Both directions fail: too few — a `KeyError` escapes for an `InvalidSpec`; too many — a valid instance
is refused.

Caught by: AGT-11.g14b (`a_refused_batch_leaves_the_learner_as_it_was`), AGT-3.3–3.11 (`test_build_learner.py`),
`test_act.py::test_agt5_5_the_refusals`, `test_learn.py::test_agt6_5_the_refusals`, AGT-7.5–7.7 (`test_checkpoint.py`),
`test_policy.py::test_agt8_6_the_refusals`, AGT-9.2–9.3 (`test_baselines.py`), `test_param_count.py::test_agt4_6_a_baseline_is_refused`;
the not-refused side by AGT-11.g14 and `test_agt3_12_an_extra_spec_key_is_ignored`; FAM-16.12, FAM-16.30.

## G15 — The baselines: three names, keyed draws, 257, and no fold

`baselines()` keyed `random`, `always-call`, `oracle` in that order, each with `name`, `rule` and `params: 0`, the
oracle also `equity_samples: 257`; `random`'s draw keyed by the decision; `oracle`'s `engine.equity(readout, seed,
257)` and `odds = 0.0` when `pot + to_call == 0`; `always-call` never index 0 (`baselines.md` §2–§6).

Caught by: `test_baselines.py::test_agt9_1_the_catalogue_is_the_three_in_order`,
`test_guardrails.py::test_agt11_g15_the_oracle_declares_257_samples`, and `test_baselines.py` AGT-9.4–9.7, FAM-5.1–5.8.

## G16 — `as_policy` snapshots, and its policy never leaves `legal_actions`

The snapshot is a copy of the parameters, the position and the encoder, and a later `learn` must not change a policy
already built; the policy returns `features.decode_action(index)` of a member of `legal_indices` (`rule.md` §7, `surface.md` §10).

Caught by: `test_policy.py::test_agt8_4_a_policy_is_a_snapshot` and
`test_guardrails.py::test_agt11_g16_a_policy_is_a_snapshot_and_stays_legal`, FAM-16.18, FAM-12.3.

## G17 — The utility is carried here and computed elsewhere

`checkpoint.md` §2.1 writes `utility` immediately after `learning_rule`, a version-3 container requires it and an older
one refuses it (`checkpoint.md` §3, `utility.md` §3, D-20); `learn`'s terminal branch stays `target = record["reward"]`,
the transform being `training`'s (`utility.md` §4, §6), and `as_policy` carries `utility` beside `learning_rule` (§7).
Caught by: `test_utility.py` AGT-15.3, AGT-15.9, `test_checkpoint.py` AGT-7.14, AGT-7.15, FAM-18.4, FAM-18.6, FAM-18.11.
**Unverified**: nothing — AGT-15.1–15.9 and FAM-18 drive every clause here.

## G18 — Run both batteries

    .venv/bin/python -m pytest tests/agents -q       # this design's unit battery
    .venv/bin/python -m pytest tests/e2e -q          # the L1 battery, FAM-18 included

`tests/e2e/` is read-only: a disagreeing case is a finding against the design, not a file to edit (`battery.md` §2).
