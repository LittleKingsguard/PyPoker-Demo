# features — the shape's action vocabulary

- **Owner:** `action_space`, `legal_indices`, `decode_action` — the three names that carry the action
  axis: one shape's vocabulary, a decision's legal indices, and an index read back as a descriptor
- **Rev:** 3 · **Date:** 2026-11-10
- **Ceiling:** 135 lines. At the ceiling, split by owner — never append

## 1. The vocabulary is the shape's, in the shape's own index order

| Index | `fixed-limit-20` — the default (D-2, ASM-6) | `no-limit-100` (D-27, D-29) | `six-seat-no-limit-100` (D-33) |
|---|---|---|---|
| 0 | `fold` — give up the hand | the same | the same |
| 1 | `check-call` — check when `to_call` is 0, otherwise call it | the same | the same |
| 2 | `raise` — the engine's minimum legal completion for that decision, unique in this shape | `raise-quarter` — the highest amount in the first quarter of the legal raise interval | the same |
| 3 | — | `raise-half` — the highest amount in the second quarter of the legal raise interval | the same |
| 4 | — | `raise-all-in` — the largest legal raise-to amount, the all-in | the same |
| 5 | — | `raise-minimum` — the minimum legal raise-to amount | the same |

The order is the shape's declared order, and on the two uncapped rows it is deliberately **not monotone in
amount**: the all-in is index 4 and the minimum index 5. A seat count adds no descriptor, so the six-seat row's six
indices are the second row's index for index (`docs/L1/seats.md` §2–§3, D-33). The tie-break among equal masked
values returns the **smallest masked index**, so an order that followed the amount would make a tie read as a
preference for the cheapest size (`sizing.md` §3, `docs/L3/agents/rule.md` §5). No rung varies the vocabulary — the
ladder holds one game (`ladder.md` §4) — and the shape is data this module restates, never one it imports (§3).

The descriptors are the project's shared spelling — the same `str`s `engine.apply_action` accepts,
`readout["legal"]` carries and `engine.legal_actions` returns in that shape's order
(`docs/L3/engine/actions.md` §1); this module does not import that module to compare them, and FAM-2.10,
FAM-2.11 and FAM-19 are the check that the two sides agree (`battery.md` §3, D-13). All three vocabularies
share `fold` and `check-call`, and no raise descriptor carries an amount — `engine` resolves one
(`sizing.md` §2).

## 2. `action_space(*, shape=None)` — one shape's declaration

    def action_space(*, shape=None) -> dict        # keyword-only; §4's arity reason, surface.md §7

    default: {0: {"name": "fold"}, 1: {"name": "check-call"},
              2: {"name": "raise", "completion": "the engine's minimum legal completion for the decision"}}
    the two uncapped rows, the same six, index for index:
              {0: {"name": "fold"}, 1: {"name": "check-call"},
               2: {"name": "raise-quarter", "band": "the highest amount in the first quarter of the legal raise interval"},
               3: {"name": "raise-half",   "band": "the highest amount in the second quarter of the legal raise interval"},
               4: {"name": "raise-all-in", "band": "the largest legal raise-to amount, the all-in"},
               5: {"name": "raise-minimum", "band": "the minimum legal raise-to amount"}}

No shape argument is the **default** shape — absence, never a defaulting of a name: a name the catalogue does
not carry is refused naming it, the entry point and the declared names (`shapes.md` §2, `errors.md` §3). Keys
are the shape's own indices; a raise's record adds `completion` or `band`, verbatim from `_RESOLUTIONS` (§1).

**The hard constraint: the only integers anywhere in this record are the shape's own indices** — `0`, `1`
and `2` for the default shape, `0`–`5` on the two uncapped rows (`guardrails.md` G6). The L1 battery's reader
(`tests/e2e/_surface.action_vocabulary`) folds keys, values and all-digit strings into the vocabulary it
reports, so an amount here reads as a chip count (FAM-2.9); a digit *inside* prose escapes it, so the unit
rule is stricter — no digit in any string — and the record stays plain data a report may quote.

## 3. `legal_indices(legal_actions)` — one decision's indices

    def legal_indices(legal_actions: Sequence[str]) -> tuple[int, ...]     # no shape, and needs none

    refuse unless the argument is a Sequence, not a str/bytes, and not a set or mapping  # InvalidActionList
    refuse if it is empty                                      # a decision has at least one action
    for each descriptor, refuse unless it is a declared descriptor, naming it       # UnknownAction
    return tuple(DESCRIPTOR_INDEX[d] for d in legal_actions)     # POSITION-ALIGNED, never reordered

`DESCRIPTOR_INDEX` is built once in `vocabulary.py` from every declared shape's row and is **total over
every descriptor a decision can carry**: a descriptor's index is its position in the shape that declares
it, the three vocabularies share their first two entries, and a decision's legal set is one shape's
vocabulary — so one table serves every decision (`docs/L2/features/shapes.md` §3, §4, ASM-44).

| Descriptor | `fixed-limit-20` | `no-limit-100` | `six-seat-no-limit-100` |
|---|---|---|---|
| `fold`, `check-call` | 0, 1 | 0, 1 | 0, 1 |
| `raise` | 2 | — | — |
| `raise-quarter`, `raise-half`, `raise-all-in`, `raise-minimum` | — | 2, 3, 4, 5 | 2, 3, 4, 5 |

The result is **position-aligned with the argument**: the i-th index is the i-th descriptor's index
(`surface.md` §8). It is one index per descriptor and — for an argument in the engine's order, which is the
shape's — ascending and distinct, a consequence of the alignment and never a step: nothing is sorted,
de-duplicated or decided, so an argument out of the engine's order yields its indices in that order
(`("raise-minimum", "check-call")` is `(5, 1)`), and `chosen_index` reads it positionally (FAM-2.11).

A **masked-out band is the normal case** on the six-descriptor shape: a band with no legal amount is absent
from `engine.legal_actions` and therefore absent from the mask, never collapsed onto a neighbour
(`sizing.md` §2) — `("check-call", "raise-minimum")` gives `(1, 5)`, the full vocabulary gives
`(0, 1, 2, 3, 4, 5)`, and the default shape's `{1, 2}` is the same fact one shape over.

Refusals, each naming what was violated: a value that is not a sequence of descriptors (a `str`, never a
descriptor list, `bytes`, a `set`, a mapping, an iterator, `None`); an empty sequence, because a live
decision always has at least one legal action (`docs/L3/engine/stepping.md` §1); and a descriptor **not
declared by any shape**, with that descriptor and the seven declared ones in the message (`'call'`,
`'Fold'`, `0`, `'raise-to-4'`). A descriptor the other shape declares is accepted — it has an index — so a
`'raise-half'` is never refused here and the caller's decision is the one that decides. The test is gated on
`str` first, so a foreign type's equality protocol cannot talk its way in, and no fold is substituted for an
unknown action (`surface.md` §8, `errors.md` §1, D-2); legality is the engine's to decide (`surface.md` §9).

## 4. `decode_action(index, *, shape=None)` — an index, one descriptor

    def decode_action(index: int, *, shape=None) -> str       # keyword-only, §2's arity reason

    refuse unless index is an Integral and not a bool, naming what was passed   # InvalidActionIndex
    refuse unless 0 <= index < len(the shape's vocabulary)                      # InvalidActionIndex
    return the shape's vocabulary[index]            # a plain str, equal by value, stable in text

The shape decides **how many indices exist** — `0–2` by default, `0–5` on the two uncapped rows (`shapes.md` §2,
D-33) — because an index decodes to a descriptor `engine.apply_action` accepts only in the vocabulary that
declared it. An index outside it is refused **naming it, the shape and that shape's vocabulary**:
`decode_action(index, shape): the index must be one of (0, 1, 2) on the shape 'fixed-limit-20', whose
vocabulary is ('fold', 'check-call', 'raise'), got 3`; a non-integer is refused on the word "integer"
before any shape is consulted (`'1'`, `1.0`, `None`, a `bool` — a flag is not an index, `README.md` §4).

**Why `shape` is keyword-only, on all three names.** The pre-existing arity cases pin each name's positional
arity, and a keyword-only optional adds the shape without moving any of them, so no case is weakened to
admit another shape (D-11, `shapes.md` §5): `build_encoder(name, *, shape=None)`, `action_space(*,
shape=None)`, `decode_action(index, *, shape=None)` — while the other four names take no shape (§3).

## 5. What is not a descriptor and what is not an index

A descriptor is exactly one of the declared `str` values: not an index, not a differently-cased spelling
(`"Fold"`), not a synonym (`"call"`, `"bet"`), not `None`, not a pair carrying an amount. An index is a
plain integer in the shape's range, **and what it denotes is shape-dependent** — index 2 is `raise` on
`fixed-limit-20` and `raise-quarter` on the two uncapped rows — so a caller storing one stores the shape beside it
(§4, `docs/L3/engine/actions.md` §3).

## 6. What the unit battery may assert

Every assertion below is one case per row. `action_space()` declares exactly `0, 1, 2` and names `fold` /
`check-call` / `raise` in order; `action_space(shape="no-limit-100")` and `shape="six-seat-no-limit-100"` each declare
exactly `0`–`5` and name the same six in the declared — not the ascending-amount — order; each record holds no integer
outside its own indices, no digit in any string, and the rows' records are unequal.
`legal_indices(("fold", "check-call", "raise"))` is `(0, 1, 2)`, `("check-call", "raise-minimum")` is `(1, 5)`, the
six in order are `(0, 1, 2, 3, 4, 5)` and `("raise", "raise-quarter")` is `(2, 2)` — one index per descriptor,
positionally, never sorted; an empty sequence, a `str`, a `set` and an undeclared descriptor each refuse with the
offending value named. `decode_action(i)` round-trips `legal_indices` for every index of its shape and is a plain
`str`; a non-integer and a `bool` refuse on the word "integer", `3` by default and `6` on each uncapped row refuse
naming the shape and its vocabulary; an unknown shape name refuses on all three names.
