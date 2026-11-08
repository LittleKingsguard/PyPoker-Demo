# agents — module design (L3)

- **Layer:** L3 · **Module:** `agents` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-09
- **Realises:** `docs/L2/agents/surface.md` (the ten entry points, their arguments, returns and refusals)
  and `docs/L2/agents/learner.md` (the rule catalogue and the one contract its members answer, the R1↔R2
  backend axis, the parameter budget, a version as a checkpoint, the three baselines, the edges)
- **Reads:** `docs/L1/e2e-surface.md` §1–§3.3, §5, `records.md` §2–§4, §6, §7, §9, `ladder.md` §2, §3, §5,
  §6, `protocol.md` §3–§5, `rules.md` §1–§8, `assumptions.md` (ASM-2, ASM-4, ASM-5, ASM-7, ASM-10, ASM-12,
  ASM-18, ASM-25), `battery.md` §3–§4, `strata/decisions.md` (D-1, D-2, D-3, D-6, D-7, D-11, D-12, D-13,
  D-16, D-19), `strata/platform.md`, `docs/L2/features/surface.md` §1, §5, §6, §8, §9,
  `docs/L2/engine/surface.md` §2, §11, `docs/L3/features/README.md` §4–§5 (inherited fact, never code).
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append
- **Implements:** `src/agents/` (written by L4, never by L3). `tests/agents/` is this design's unit battery;
  `tests/e2e/`'s `test_fam01_surface.py` (FAM-1.17–1.26), `test_fam05_baselines.py`, `test_fam12_checkpoints.py`
  (FAM-12.2), `test_fam13_parity.py` and `test_fam16_blind.py` are the L1 battery's share for it

## 1. What this module is

`agents` is everything that chooses or learns an action: one learner family, the catalogue of two learning rules a spec
selects from, and the three fixed baselines (`module-map.md` §1, D-6, D-19, ASM-7). It acts, learns, saves, restores and
hands out policies; it never deals a hand, decides legality, encodes an observation, measures a match or writes a report
(D-2, D-3, D-6, `surface.md` §1, `learner.md` §6–§8). The **set** of rules, the reward, the vocabulary and the readout
facts are fixed for the ladder, so a rung difference is never a rule's (D-3, ASM-7, ASM-12, `rules.md` §8).

## 2. The documents, one per owner

| Document | Owner of that question | What it fixes |
|---|---|---|
| `rule.md` | the catalogue of two rules | each rule's target, the contract they share, the mask, the reward, the semi-gradient step and the batch order; the exploration schedule and the **keyed draw**; the **tie-break**; what `learners()` declares and what `learn` returns (D-19, ASM-7, ASM-12) |
| `architecture.md` | the seven kinds | each kind's layer stack, how `width`/`depth`/`sparsity`/`residual` are read, the **one initialisation order**, the **parameter formula**, and the sizing contract (D-3, ASM-10) |
| `backends.md` | the R1↔R2 axis | NumPy at R1 and PyTorch from R2 on, what the swap may not change, the decision-parity mechanism and its tolerance, the dtype, the lazy `torch` import (D-7) |
| `checkpoint.md` | a version | what a restore recovers, the **exact bytes** of the container, the format version and the rule a version-1 file is read as, and `save`/`load`'s refusals (D-16, ASM-5, ASM-18, D-19) |
| `baselines.md` | the three fixed rules | `random`'s keyed uniform draw, `always-call`'s procedure, `oracle`'s pot-odds inequality at **257** samples, the blindness, the `baselines()` record (D-6, ASM-4) |
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

`Learner`, `AgentsError` and its subclasses, the kind table, the rule catalogue, the hyper-declarations, the
parameter layout, the keyed draw and every helper below an entry point are **not** surface (`e2e-surface.md` §1,
`surface.md` §1, brief §5). Every rule that holds of all ten — no coercion, no substituted default, no swallowed
error, no partial record, no global `random` (ASM-2), an invalid argument refused by name — is L2's, not restated here.

## 4. The layout of `src/agents/`

    __init__.py       the ten entry points, `__all__`, and nothing else (§3)
    errors.py         AgentsError and its seventeen subclasses (errors.md §2)
    declarations.py   BACKENDS, ARCHITECTURES, LEARNING_RULES, HYPER, KINDS — the one catalogue (§5)
    model.py          the kinds' stacks, the parameter formula, the initialisation order (arch. §2–§5)
    rule.py           epsilon, the keyed draw, the tie-break, the TD aim, the semi-gradient step (rule.md)
    numpy_backend.py  the forward and backward arithmetic in NumPy (backends.md §2)
    torch_backend.py  the same arithmetic in PyTorch, and the only `import torch` in the project (§6)
    learner.py        Learner, build_learner, param_count, act, learn (rule.md, architecture.md)
    checkpoint.py     save, load, the zip container and its metadata (checkpoint.md §2–§3)
    policy.py         as_policy and the frozen snapshot (rule.md §7)
    baselines.py      baselines, build_baseline, the three rules (baselines.md §1–§4)

Eleven files, one concern each; a twelfth needs a document here saying what it owns. `src/agents/` holds no
test, no fixture and no data file: the catalogue is code, and the kinds are its rows. The names `rule.md` §8
fixes in `rule.py`, `model.py` and `checkpoint.py` are contract for `tests/agents/` — L4 implements those spellings.

## 5. The catalogue `learners()` publishes

Four keys, in this order: `backends`, `architectures`, `learning_rules`, `hyper` (`surface.md` §3, D-19).
`backends` is keyed `numpy` then `torch`, each value `{"name": <backend>}` — a record whose only string
value is the name, so no prose can be read as one. `architectures` is keyed by the seven kinds in the order
`naive-stack`, `token-embedding`, `wide`, `deep`, `sparse`, `residual`, `plain`, each value carrying `name`,
`observation` and `observation_size` (203 for `naive-stack`, 96 for the six token kinds). `learning_rules` is keyed by
the two catalogue members in `rules.md` §2's order, each value a record of `name` and the `target` it aims at; `hyper`
is the six fixed declarations both rules consume (`rule.md` §6). The record is plain data, equal on two calls, never
the copy a fairness check audits (`ladder.md` §3, §4).

## 6. The import boundary — a hard rule

`agents` imports `numpy`, the Python standard library (`hashlib`, `io`, `json`, `numbers`, `os`, `zipfile`,
`collections.abc`, `typing`), the five granted `features` calls (`encode`, `observation_spec`,
`action_space`, `legal_indices`, `decode_action`) and the one `engine` call `equity` (`learner.md` §5–§7,
`module-map.md` §2). Never `pokerkit`; never `evaluation`, `training` or `harness`; never a `tests/` helper;
never `build_encoder`, the encoder always arriving from the caller (D-13, `module-map.md` §2). `torch` is
imported **inside** `torch_backend.py` when a torch learner is built and nowhere else (`backends.md` §4), so
`import agents` must leave `torch` and `pokerkit` absent from `sys.modules`.

## 7. Facts inherited from `engine` and `features`, and not re-derived

- `observation_spec` fixes the family, size and dtype: `dense-numeric` at `(203,)` `float32` with
  `vocabulary None`, and `token-sequence` at `(40,)` `int32` with `vocabulary 96` (`features/surface.md` §5,
  `docs/L3/features/README.md` §4). A learner records them and copies no width out of a document (D-3).
- The mask is `legal_indices`' ascending, distinct, non-empty sequence, and a chosen index is one of its members;
  the policy's descriptor is `decode_action` of it — `"fold"`, `"check-call"`, `"raise"` (`features/surface.md` §8–§9).
- A readout is the ten facts: `seat` a pair, `hole` two cards, `board` 0/3/4/5 cards, `stacks`/`limit` pairs,
  `pot`/`to_call` ints, `history` entries, `legal` descriptors (`docs/L3/features/README.md` §4).
- `equity(decision_or_readout, seed, samples)` returns a float in `[0, 1]`, accepts a readout and repeats for one
  decision, seed and count (`engine/surface.md` §11) — the oracle's only `engine` call (`learner.md` §7).

## 8. Decisions a later module must not re-derive

1. **One rule set, one reward, one vocabulary, one fact set** (ASM-7, ASM-12, D-19): a rung changes the
   representation or the architecture and nothing else; no hyperparameter is a per-learner argument, and a pair may
   differ on the rule at one capacity because both rules hold the same trainable parameters (ASM-10, D-19).
2. **An answer depends on the state and the decision, not on call order**: the key is a function of seed,
   observation and mask, the schedule advances only inside `learn`, a policy's state advances nowhere.
3. **The tie-break is total and backend-independent**: the smallest masked index within `1e-9` relative of
   the masked maximum (`rule.md` §5, `backends.md` §3).
4. **One initialisation order**, worked by NumPy for both backends: He-normal weights, zero biases (arch §4).
5. **The parameter count is one formula**; the target copy, the masks and the schedule are excluded (ASM-10).
6. **A checkpoint is a zip of two members**, written through an open file handle (`checkpoint.md` §2).
