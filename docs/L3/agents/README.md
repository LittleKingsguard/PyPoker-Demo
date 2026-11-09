# agents — module design (L3)

- **Layer:** L3 · **Module:** `agents` · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-09
- **Realises:** `docs/L2/agents/surface.md` (the ten entry points, their arguments, returns and refusals) and
  `docs/L2/agents/learner.md` (both catalogues and the one contract each one's members answer, the edges)
- **Reads:** `docs/L1/e2e-surface.md` §1–§3.3, §5, `records.md` §2–§4, §6, §7, §9, `ladder.md` §2, §3, §5, §6,
  `protocol.md` §3–§5, `rules.md` §1–§8, `utilities.md` §2–§7, `folders.md` §2–§4, `assumptions.md` (ASM-2, ASM-4, ASM-5,
  ASM-7, ASM-10, ASM-12, ASM-18, ASM-25, ASM-28, ASM-30, ASM-31, ASM-32), `battery.md` §3–§4, `strata/decisions.md` (D-1,
  D-2, D-3, D-6, D-7, D-11, D-12, D-13, D-16, D-19, D-20, D-21), `strata/platform.md`, `docs/L2/features/surface.md` §1,
  §5, §6, §8, §9, `docs/L2/engine/surface.md` §2, §11, `docs/L3/features/README.md` §4–§5 (inherited, never code).
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append
- **Implements:** `src/agents/` (written by L4, never by L3). `tests/agents/` is this design's unit battery;
  `tests/e2e/`'s `test_fam01_surface.py` (FAM-1.17–1.26), `test_fam05_baselines.py`, `test_fam12_checkpoints.py`,
  `test_fam13_parity.py`, `test_fam18_utilities.py` and `test_fam16_blind.py` are the L1 battery's share for it

## 1. What this module is

`agents` is everything that chooses or learns an action: one learner family, the catalogue of two learning rules and
the catalogue of two terminal-reward utilities a spec selects from, and the six fixed baselines — D-6's three, which
anchor the rating, and D-21's three folders (`module-map.md` §1, D-6, D-19, D-20, D-21, ASM-7). It acts, learns, saves,
restores and hands out policies; it never deals a hand, decides legality, encodes an observation, measures a match or
writes a report (D-2, D-3, D-6, `surface.md` §1, `learner.md` §6–§8). The **sets** of rules and of utilities, the
vocabulary and the readout facts are fixed for the ladder, so a rung difference is no axis's (D-3, ASM-7, ASM-28, `rules.md` §8, `utility.md` §1).

## 2. The documents, one per owner

| Document | Owner of that question | What it fixes |
|---|---|---|
| `rule.md` | the catalogue of two rules | each rule's target, the contract they share, the mask, where the terminal reward enters, the semi-gradient step and the batch order; the exploration schedule and the **keyed draw**; the **tie-break**; what `learners()` declares and what `learn` returns (D-19, ASM-7, ASM-12) |
| `utility.md` | the catalogue of two utilities | each utility's `reward` and `normaliser`, the declared default, the one contract both answer, the arithmetic's four scores, where the transform is applied and where it is not, what a learner and a policy carry, and the `UnknownUtility` refusal (D-20, ASM-12, ASM-28) |
| `architecture.md` | the seven kinds | each kind's layer stack, how `width`/`depth`/`sparsity`/`residual` are read, the **one initialisation order**, the **parameter formula**, and the sizing contract (D-3, ASM-10) |
| `backends.md` | the R1↔R2 axis | NumPy at R1 and PyTorch from R2 on, what the swap may not change, the decision-parity mechanism and its tolerance, the dtype, the lazy `torch` import (D-7) |
| `checkpoint.md` | a version | what a restore recovers, the **exact bytes** of the container, format version 3 and the three version rules, the `utility` field written beside `learning_rule`, and `save`/`load`'s refusals (D-16, ASM-5, ASM-18, D-19, D-20) |
| `restore.md` | a restore's promise | the loss-free equality stated testably, why the file must carry more than the parameters, where the promise is asserted by a case, and what is left to L4 (D-16, ASM-5, ASM-20) |
| `baselines.md` | the six fixed rules | `random`'s keyed uniform draw, `always-call`'s procedure, `oracle`'s pot-odds inequality at **257** samples, the three folders' predicates under one legality rule, the blindness, the `baselines()` record and the `anchor` flag that keeps the rating's scale (D-6, ASM-4, ASM-31, ASM-32, D-21) |
| `errors.md` | refusals | the hierarchy, the message grammar, the canonical message per refusal of `surface.md` §4–§12, and what is deliberately *not* refused |
| `guardrails.md` | L4 | one numbered note per risk this design identified, in the order they bite, each naming the test that catches it |

## 3. The ten names

`src/agents/__init__.py` exports exactly the ten entry points of `e2e-surface.md` §3.3, in that order, and
adds, removes and renames none (D-12):

    learners()                             -> Mapping
    build_learner(spec)                    -> Learner        # opaque
    param_count(learner)                   -> int
    act(learner, observation, legal_mask)  -> Mapping        # "action" is a plain int
    learn(learner, transitions)            -> Mapping        # td_error, transitions
    save(learner, path)                    -> str
    load(spec, path)                       -> Learner
    as_policy(learner, encoder, seed)      -> callable
    baselines()                            -> Mapping
    build_baseline(name, seed)             -> callable

`Learner`, the error classes, the kind table, both catalogues, the hyper-declarations, the parameter layout, the keyed
draw and every helper below an entry point are **not** surface, and the rules holding of all ten — no coercion, no
substituted default, no swallowed error, no global `random` (ASM-2) — are L2's (`surface.md` §1, brief §5).

## 4. The layout of `src/agents/`

    __init__.py       the ten entry points, `__all__`, and nothing else (§3)
    errors.py         AgentsError and its eighteen subclasses (errors.md §2)
    declarations.py   BACKENDS, ARCHITECTURES, LEARNING_RULES, UTILITIES, KINDS, HYPER — the one catalogue (§5)
    model.py          the kinds' stacks, the parameter formula, the initialisation order (arch. §2–§5)
    rule.py           epsilon, the keyed draw, the tie-break, the TD aim, the semi-gradient step (rule.md)
    numpy_backend.py  the forward and backward arithmetic in NumPy (backends.md §2)
    torch_backend.py  the same arithmetic in PyTorch, and the only `import torch` in the project (§6)
    learner.py        Learner, build_learner, param_count, act, learn (rule.md, architecture.md)
    checkpoint.py     save, load, the zip container and its metadata (checkpoint.md §2–§3)
    policy.py         as_policy and the frozen snapshot (rule.md §7)
    baselines.py      baselines, build_baseline, the six rules and the anchor set (baselines.md §1–§9)

Eleven files, one concern each, and a twelfth needs a document here saying what it owns; `src/agents/` holds no
test, no fixture and no data file, the catalogue being code and the kinds its rows. The names `rule.md` §8 fixes in
`rule.py`, `model.py` and `checkpoint.py` are contract for `tests/agents/` — L4 implements those spellings.

## 5. The catalogue `learners()` publishes

Five keys, in this order: `backends`, `architectures`, `learning_rules`, `utilities`, `hyper` (`surface.md` §3, D-19,
D-20). `backends` is keyed `numpy` then `torch`, each value `{"name": <backend>}` — a record whose only string value is
the name. `architectures` is keyed by the seven kinds of `architecture.md` §1, each value carrying `name`,
`observation` and `observation_size`. `learning_rules` and `utilities` are keyed by their catalogues' members in
`rules.md` §2's and `utility.md` §2's order — `name` and `target` for a rule, `name`, `reward` and `normaliser` for a
utility (D-19, D-20) — and `hyper` is the six fixed declarations both catalogues consume (`rule.md` §6). The record is
plain data, equal on two calls, never the copy a fairness check audits (`ladder.md` §3, §4).

## 6. The import boundary — a hard rule

`agents` imports `numpy`, the Python standard library, the five granted `features` calls (`encode`,
`observation_spec`, `action_space`, `legal_indices`, `decode_action`) and the granted `engine` calls — `equity` for
the oracle, `game_config` for `fold-large-bet`, each imported inside the policy that needs it (`module-map.md` §2,
ASM-31). Never `pokerkit`; never `evaluation`, `training` or `harness`; never a `tests/` helper; never `build_encoder`,
the encoder always arriving from the caller (D-13). `torch` is imported inside `torch_backend.py` and nowhere else
(`backends.md` §4), so `import agents` leaves `torch` and `pokerkit` absent from `sys.modules`.

## 7. Facts inherited from `engine` and `features`, and not re-derived

- `observation_spec` fixes the family, size and dtype: `dense-numeric` at `(203,)` `float32` with
  `vocabulary None`, and `token-sequence` at `(40,)` `int32` with `vocabulary 96` (`features/surface.md` §5,
  `docs/L3/features/README.md` §4). A learner records them and copies no width out of a document (D-3).
- The mask is `legal_indices`' ascending, distinct, non-empty sequence, and a chosen index is one of its members;
  the policy's descriptor is `decode_action` of it — `"fold"`, `"check-call"`, `"raise"` (`features/surface.md` §8–§9).
- A readout is the eleven facts: `seat` a pair, `hole` two cards, `board` 0/3/4/5 cards, `stacks`/`limit` pairs,
  `pot`/`to_call` ints, `history` entries, `legal` descriptors, and `hand_class` `None` or an integer 0–8 — D-21's
  derived fact, which no encoding carries (`docs/L3/features/README.md` §4, ASM-30).
- `equity(decision_or_readout, seed, samples)` returns a float in `[0, 1]`, accepts a readout and repeats for one
  decision, seed and count (`engine/surface.md` §11) — the oracle's only `engine` call (`learner.md` §7).

## 8. Decisions a later module must not re-derive

1. **One rule set, one utility set, one vocabulary, one fact set** (ASM-7, ASM-28, D-19, D-20): a rung changes the
   representation or the architecture only; no hyperparameter is a per-learner argument, and a pair may differ on the
   rule or the utility at one capacity, each catalogue's members holding the same trainable parameters (ASM-10).
2. **An answer depends on the state and the decision, not on call order**: the key is a function of seed,
   observation and mask, the schedule advances only inside `learn`, a policy's state advances nowhere.
3. **The tie-break is total and backend-independent**: the smallest masked index within `1e-9` relative of
   the masked maximum (`rule.md` §5, `backends.md` §3).
4. **One initialisation order**, worked by NumPy for both backends: He-normal weights, zero biases (arch §4).
5. **The parameter count is one formula**; the target copy, the masks and the schedule are excluded (ASM-10).
6. **A checkpoint is a zip of two members**, written through an open file handle (`checkpoint.md` §2).
