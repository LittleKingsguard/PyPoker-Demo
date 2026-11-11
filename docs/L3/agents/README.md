# agents — module design (L3)

- **Layer:** L3 · **Module:** `agents` · **Unit:** phase1 · **Rev:** 6 · **Date:** 2026-11-10
- **Realises:** `docs/L2/agents/surface.md` (the ten entry points, their arguments, returns and refusals) and
  `docs/L2/agents/learner.md` (both catalogues and the one contract each one's members answer, the edges)
- **Reads:** `docs/L1/e2e-surface.md` §1–§3.3, §5, `shapes.md` §8, `records.md` §2–§4, §6, §7, §9, `ladder.md` §2, §3, §5,
  §6, `protocol.md` §3–§5, `rules.md` §1–§8, `utilities.md` §2–§7, `folders.md` §2–§4, `assumptions.md` (ASM-2, ASM-4,
  ASM-5, ASM-7, ASM-10, ASM-12, ASM-18, ASM-25, ASM-28, ASM-30, ASM-31, ASM-32, ASM-42, ASM-44), `battery.md` §3–§4,
  `strata/decisions.md` (D-1, D-2, D-3, D-6, D-7, D-11, D-12, D-13, D-16, D-19, D-20, D-21, D-33), `strata/platform.md`,
  `docs/L2/features/surface.md` §1, §5, §6, §8, §9 and `capacity.md`, `docs/L2/engine/surface.md` §2, §11.
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append
- **Implements:** `src/agents/` (written by L4, never by L3). `tests/agents/` is this design's unit battery, and
  `tests/e2e/`'s FAM-1, FAM-5, FAM-12, FAM-13, FAM-16 and FAM-18 files are the L1 battery's share for it.

## 1. What this module is

`agents` is everything that chooses or learns an action: one learner family, the catalogue of two learning rules and the
catalogue of two terminal-reward utilities a spec selects from, the three declared game shapes a spec selects between, and
the six fixed baselines — D-6's three, which anchor the rating, and D-21's three folders (`module-map.md` §1, D-6, D-19,
D-20, D-21, D-29, D-33, ASM-7). It acts, learns, saves, restores and hands out policies; it never deals a hand, decides
legality, encodes an observation, measures a match or writes a report (D-2, D-3, `learner.md` §6–§8). The **sets** of rules
and utilities, the shape catalogue, the vocabulary and the readout facts are fixed for the ladder (D-3, ASM-7, `rules.md` §8).

## 2. The documents, one per owner

| Document | Owner of that question | What it fixes |
|---|---|---|
| `rule.md` | the catalogue of two rules | each rule's target, the contract they share, the mask, where the terminal reward enters, the semi-gradient step and the batch order; the two **divergence guards** that sit in that order (`divergence.md` §2); the exploration schedule and the **keyed draw**; the **tie-break**; what `learners()` declares and what `learn` returns (D-19, ASM-7, ASM-12) |
| `utility.md` | the catalogue of two utilities | each utility's `reward` and `normaliser`, the declared default, the one contract both answer, the arithmetic's four scores, where the transform is applied and where it is not, what a learner and a policy carry, and the `UnknownUtility` refusal (D-20, ASM-12, ASM-28) |
| `architecture.md` | the seven kinds | each kind's layer stack, how `width`/`depth`/`sparsity`/`residual` are read, the **one initialisation order**, the **parameter formula**, and the sizing contract (D-3, ASM-10) |
| `backends.md` | the R1↔R2 axis | NumPy at R1 and PyTorch from R2 on, what the swap may not change, the decision-parity mechanism and its tolerance, the dtype, the lazy `torch` import (D-7) |
| `checkpoint.md` | a version | what a restore recovers, the **exact bytes** of the container, format **3** for a default-shape learner and **4** with a `game` field for any other declared shape, the four version rules, the `utility` field written beside `learning_rule`, and `save`/`load`'s refusals (D-16, ASM-5, ASM-18, D-19, D-20, ASM-40) |
| `shapes.md` | the game shape | the catalogue restated in `declarations.py` with each row's seat count and why `A` is **read** off `features.action_space`, the head `W → A` and the layout's `actions` field, the `A`-index decision space, `decide`/`decide_greedy` and the `tie` flag, the two exploration modes, format 4 and the `game` field (D-29, D-33, ASM-37, ASM-40) |
| `restore.md` | a restore's promise | the loss-free equality stated testably, why the file must carry more than the parameters, where the promise is asserted by a case, and what is left to L4 (D-16, ASM-5, ASM-20) |
| `baselines.md` | the six fixed rules | `random`'s keyed uniform draw, `always-call`'s procedure, `oracle`'s pot-odds inequality at **257** samples, the three folders' predicates under one legality rule, the blindness, the `baselines()` record and the `anchor` flag that keeps the rating's scale (D-6, ASM-4, ASM-31, ASM-32, D-21) |
| `errors.md` | refusals | the hierarchy, the message grammar, the canonical message per refusal of `surface.md` §4–§12 and of `divergence.md`'s, and what is deliberately *not* refused — the learner's own divergence being `divergence.md`'s: its twenty-first class, its sites and guards, its four messages (D-19, D-20) |
| `guardrails.md` | L4 | one numbered note per risk this design identified, in the order they bite, each naming the test that catches it |

## 3. The ten names

`src/agents/__init__.py` exports exactly the ten entry points of `e2e-surface.md` §3.3, in that order, and
adds, removes and renames none (D-12):

    learners()                             -> Mapping
    build_learner(spec)                    -> Learner        # opaque
    param_count(learner)                   -> int
    act(learner, observation, legal_mask)  -> Mapping        # "action" a plain int, "tie" a plain bool
    learn(learner, transitions)            -> Mapping        # td_error, transitions
    save(learner, path)                    -> str
    load(spec, path)                       -> Learner
    as_policy(learner, encoder, seed, exploration="schedule") -> callable
    baselines()                            -> Mapping
    build_baseline(name, seed, shape=None) -> callable        # the declared shape the policy decides in

`Learner`, the error classes, the kind table, the shape names, both catalogues, the hyper-declarations, the parameter
layout, the keyed draw and every helper below an entry point are **not** surface, and the rules holding of all ten — no
coercion, no substituted default, no swallowed error, no global `random` (ASM-2) — are L2's (`surface.md` §1, brief §5).

## 4. The layout of `src/agents/`

    __init__.py       the ten entry points, `__all__`, and nothing else (§3)
    errors.py         AgentsError and its twenty-one subclasses (errors.md §2, divergence.md §1)
    declarations.py   the catalogues, the shape names and seat counts, the exploration modes and `sized_by_kind`, with
                      their refusals (§5, shapes.md §1, §6)
    model.py          the kinds' stacks, the parameter formula, the initialisation order (arch. §2–§5)
    rule.py           epsilon, the keyed draw, the tie-break, the TD aim, the step, both guards (rule.md, divergence.md)
    numpy_backend.py  the forward and backward arithmetic in NumPy (backends.md §2)
    torch_backend.py  the same arithmetic in PyTorch, and the only `import torch` in the project (§6)
    learner.py        Learner, build_learner, param_count, act, learn, both guards (rule.md, architecture.md)
    checkpoint.py     save, load, the zip container and its metadata (checkpoint.md §2–§3)
    policy.py         as_policy and the frozen snapshot (rule.md §7)
    baselines.py      baselines, build_baseline, the six rules and the anchor set (baselines.md §1–§9)

Eleven files, one concern each, and a twelfth needs a document here saying what it owns; `src/agents/` holds no test, no
fixture and no data file. The names `rule.md` §8 fixes in `rule.py`, `model.py` and `checkpoint.py` are contract for
`tests/agents/` — L4 implements those spellings, and the shape's fields ride through them (`shapes.md` §2).

## 5. The catalogue `learners()` publishes

Five keys, in this order: `backends`, `architectures`, `learning_rules`, `utilities`, `hyper` (`surface.md` §3, D-19,
D-20). `backends` is keyed `numpy` then `torch`, each value `{"name": <backend>}`. `architectures` is keyed by the seven
kinds of `architecture.md` §1, each value carrying `name`, `observation` and `observation_size` — the **default shape's**
size, 203 and 96, so a learner on another shape takes its width from that shape's encoder (`shapes.md` §8, ASM-44);
`learning_rules` and `utilities` by their catalogues' members in `rules.md` §2's and `utility.md` §2's order (D-19, D-20);
`hyper` is the six fixed declarations both catalogues consume (`rule.md` §6). The record is plain data, equal on two calls,
never the copy a fairness check audits (`ladder.md` §3, §4). **No shape key is added** (`shapes.md` §1, §4).

## 6. The import boundary — a hard rule

`agents` imports `numpy`, the Python standard library, the five granted `features` calls (`encode`, `observation_spec`,
`action_space`, `legal_indices`, `decode_action`) and the granted `engine` calls — `equity` for the oracle, `game_config`
for `fold-large-bet`, each imported inside the policy that needs it (`module-map.md` §2, ASM-31). Never `pokerkit`, never
`evaluation`, `training` or `harness`, never `build_encoder` (D-13), and `torch` only inside `torch_backend.py`
(`backends.md` §4): `import agents` leaves `torch` and `pokerkit` absent from `sys.modules`.

## 7. Facts inherited from `engine` and `features`, and not re-derived

- `observation_spec` fixes the family, size and dtype **on the shape its encoder was built for**: `dense-numeric`
  `float32` at `(203,)`, `(329,)` and `(433,)`, `token-sequence` `int32` at `(40,)`, `(82,)` and `(122,)` with `vocabulary`
  96 on the two-seat rows and 102 at six seats, recorded and copied from no document (`shapes.md` §8, `seats.md` §4, ASM-44, D-3).
- The mask is `legal_indices`' ascending, distinct, non-empty sequence, and a chosen index is one of its members in
  `0 .. A−1`; the policy's descriptor is `decode_action` of it **in the learner's shape** (`shapes.md` §3).
- A readout is the eleven facts: `seat` a pair of index and button flag, `hole` two cards, `board` 0/3/4/5 cards, `stacks` one
  entry per seat, `limit`, `pot`/`to_call` ints, `history`, `legal` and `hand_class` 0–8 or `None` (ASM-30, `seats.md` §2).
- `equity(decision_or_readout, seed, samples)` returns a float in `[0, 1]`, accepts a readout and repeats for one
  decision, seed and count (`engine/surface.md` §11) — the oracle's only `engine` call (`learner.md` §7).

## 8. Decisions a later module must not re-derive

1. **One rule set, one utility set, one shape catalogue, one vocabulary** (ASM-7, ASM-28, D-19, D-20, D-29, D-33): a rung
   changes the representation or the architecture only, and a pair may differ on the rule or the utility at one capacity.
2. **An answer depends on the state and the decision, not on call order**: the key is a function of seed,
   observation and mask, the schedule advances only inside `learn`, a policy's state advances nowhere.
3. **The tie-break is total and backend-independent**: the smallest masked index within `1e-9` relative of the masked
   maximum, in the **shape's** declared order (`rule.md` §5, `backends.md` §3, `shapes.md` §3).
4. **One initialisation order**, worked by NumPy for both backends: He-normal weights, zero biases (arch §4).
5. **The count is one formula and the shape's numbers are read, never written**: `I·W` over the learner's own input width
   (203, 329 or 433) plus `A·W + A` at its head, the target copy and masks excluded; `SHAPE_NAMES` and `SHAPE_SEATS` restate
   the names and seat counts only, and no backend carries a `3` (`shapes.md` §1–§2, §8, `seats.md` §1, ASM-40, ASM-44, D-33).
6. **A checkpoint is a zip of two members**, written through an open file handle (`checkpoint.md` §2).
