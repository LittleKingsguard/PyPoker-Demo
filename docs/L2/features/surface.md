# features — the callable surface

- **Layer:** L2 · **Module:** `features` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-05
- **Owner of this file:** the surface — the seven module-level names of `src/features/`, each with its
  argument contract, its return, its refusals and its ordering (D-12, `e2e-surface.md` §1)
- **Ceiling:** 170 lines. At the ceiling, split by owner — never append

## 1. Rules that hold of every entry point

Each of the seven names is a module-level name of the `features` package, and nothing below one of them is
contract (`e2e-surface.md` §1, brief §5). Five rules are shared and are stated here once (D-12, D-13):

- The seven names are fixed: L2 refines types, record keys, defaults and error classes and never adds,
  removes or renames an entry point (D-12, `e2e-surface.md` §1).
- An invalid argument is refused by raising an error that names the violated contract — the refusing entry
  point and what it refused, its class free — and no entry point coerces a value, substitutes a default,
  swallows an error or returns part of a record (`e2e-surface.md` §2, D-12).
- No entry point draws randomness, seeds or advances the global `random` stream, and none takes a seed, so
  every name here is a function of its arguments alone (`e2e-surface.md` §2, ASM-2, `protocol.md` §4).
- An encoder is an opaque value a caller only hands back to `observation_spec` and `encode`; no caller
  inspects, compares, serialises or rebuilds one, because nothing below an entry point is surface
  (`e2e-surface.md` §1).
- Every other returned value is plain data — a mapping, a sequence of names or indices, or the observation
  array — because `action_space` is quoted in a report's header family beside `game_config`
  (`protocol.md` §1, `e2e-surface.md` §3.2).

This module never decides legality, never applies an action, never counts a parameter and never learns
which opponent it faces (`module-map.md` §3, D-2). Its whole view of the game is `engine.readout`'s
eleven facts, of which it carries nine and reads as data (`module-map.md` §2, `engine/environment.md` §6).

## 2. The action vocabulary and the action descriptor

The vocabulary is the game's and not a rung's, and it has three indices (`e2e-surface.md` §2, D-2):

| Index | Action | What the descriptor denotes |
|---|---|---|
| 0 | fold | give up the hand |
| 1 | check/call | check when `to_call` is 0, otherwise call it |
| 2 | raise | the engine's minimum legal completion for that decision, unique in fixed-limit (`e2e-surface.md` §2, D-2) |

Five consequences bind both sides of this edge (`e2e-surface.md` §2, D-3):

- a descriptor carries no amount, is hand-independent and compares by value, so one value denotes one
  index at every decision and `decode_action` can build it from an index alone (`engine/surface.md` §2);
- the vocabulary's spelling is shared with `engine` and is fixed here: `"fold"`, `"check-call"` and
  `"raise"` — the names `action_space` declares. `decode_action` returns one of them, `legal_indices`
  recognizes one, and that round trip is the contract between the two modules (`e2e-surface.md` §3.2,
  D-13);
- `engine.legal_actions` returns a decision's descriptors in ascending vocabulary index — fold, then
  check/call, then raise — with at most one entry per index, so a decision's legal indices are ascending
  and distinct (`engine/surface.md` §2, §6);
- fold is absent where `to_call` is 0, because folding where checking is free is not an action of that
  decision (`engine/surface.md` §2, `battery.md` §3 FAM-16);
- `decode_action` never claims legality: it sees no decision, so applying a decoded descriptor whose index
  that decision does not allow is the caller's contract violation and `engine.apply_action` refuses it
  (`engine/surface.md` §7, D-2). The authoritative legality channel is `legal_indices`; the descriptor
  itself is hand-independent (`engine/surface.md` §2), and the engine's fixed seat roles make one index
  denote one action whatever the hand (`engine/surface.md` §4).

## 3. `encodings` — the declared encodings (`fixed` row)

- **Signature:** `encodings()`.
- **Arguments:** none: the encoding set is the ladder's, so there is no parameter by which it can be varied
  (D-3, `e2e-surface.md` §2).
- **Returns:** a mapping keyed by the two encoding names — `flat-numeric` and `card-tokens` — each value
  the record `observation_spec` returns for that encoding (§5, `encodings.md` §1–§4). Both names appear and
  no third encoding does (`ladder.md` §2, D-3).
- **Refusals:** none; it has no argument and nothing to vary (`e2e-surface.md` §3.2, D-3).
- **Determinism and ordering:** two calls return equal records, written in the ladder's order,
  `flat-numeric` then `card-tokens`, and the catalogue is plain data a report's header may quote
  (`ladder.md` §2, `protocol.md` §1).

## 4. `build_encoder` — one encoder (`fixed` row)

- **Signature:** `build_encoder(name)`.
- **Arguments:** `name`, one of the two names `encodings` declares — the encoding a variant entry names
  (`ladder.md` §3, `records.md` §2). No seed, no size and no rung, because a representation is not a model
  (D-3, `e2e-surface.md` §3.2).
- **Returns:** an encoder — the opaque value `observation_spec` and `encode` take (§1). It is the only way
  to obtain one, so every observation the ladder consumes came from a declared encoding
  (`e2e-surface.md` §5).
- **Refusals:** a name that is not one of the two, with that name in the error, because an encoder exists
  only by a declared encoding (`e2e-surface.md` §2, §5, `battery.md` §4).
- **Determinism:** two encoders built from one name declare equal specs and encode one readout to equal
  observations; building draws no randomness and keeps no state that an observation could see (ASM-2).

## 5. `observation_spec` — what one observation is (`fixed` row)

- **Signature:** `observation_spec(encoder)`.
- **Arguments:** an encoder from `build_encoder` (`e2e-surface.md` §3.2).
- **Returns:** one mapping, read under these keys:

| Key | Content |
|---|---|
| `representation` | **the encoding's own name** — `flat-numeric` or `card-tokens`; the invariance family reads it as that name (`e2e-surface.md` §2, `battery.md` §3 FAM-2 case FAM-2.6) |
| `kind` | the representation family: `dense-numeric` or `token-sequence` (`e2e-surface.md` §3.2) |
| `fields` | the readout facts the observation carries: the same nine names for both encodings, a subset of `engine.readout`'s eleven, `legal` and the derived `hand_class` excluded (`e2e-surface.md` §2, `encodings.md` §2, `folders.md` §3) |
| `shape` | a tuple of integers, one observation's shape: `(203,)` for `flat-numeric`, `(40,)` for `card-tokens` (`encodings.md` §3–§4) |
| `dtype` | the element type: `float32` for `flat-numeric`, `int32` for `card-tokens` (`encodings.md` §3–§4) |
| `vocabulary` | the number of distinct token ids a `card-tokens` observation can carry, `96`, and `null` for `flat-numeric`: a key this document adds to the two encodings' record because `agents` sizes an embedding table from it, and the only one a caller depends on beyond the five keys above it (`module-map.md` §2, `e2e-surface.md` §2, `records.md` §1) |

- **Refusals:** a value that is not an encoder this module built, naming that contract
  (`e2e-surface.md` §2).
- **Determinism:** one encoder declares one spec; two calls are equal and the spec depends on no readout,
  hand or seed (`e2e-surface.md` §2, ASM-2).

## 6. `encode` — one readout, one observation (`general` row)

- **Signature:** `encode(encoder, readout)`.
- **Arguments:** an encoder, and a readout in the shape `engine.readout` returns — the eleven facts, with
  `street`, `seat`, `hole`, `board`, `stacks`, `pot`, `to_call`, `limit`, `history`, `legal` and
  `hand_class` all present (`engine/environment.md` §2, `e2e-surface.md` §2, `folders.md` §3).
- **Returns:** one observation — a NumPy array of the declared `shape` and `dtype` (`encodings.md` §3–§4).
  It carries the declared `fields` and nothing else, and in particular nothing the readout withholds, so no
  observation can show the other seat's cards or the undealt deck (`engine/environment.md` §2, D-3).
- **Refusals:** a value that is not an encoder; a readout missing a field this encoding carries; a carried
  field that cannot be represented, such as a `street` outside the four or a `hole` that is not two cards.
  Each names what was violated, and none is defaulted (`e2e-surface.md` §2, D-3). The two facts it does not
  carry — `legal` and `hand_class` — are ignored and not refused (`encodings.md` §2, `folders.md` §3).
- **Determinism:** one encoder and one readout give one observation value for value, and `encode` neither
  mutates its argument nor draws randomness (`battery.md` §3 FAM-16 case FAM-16.9, ASM-2).

## 7. `action_space` — the three-index vocabulary (`fixed` row)

- **Signature:** `action_space()`.
- **Arguments:** none: the vocabulary is the game's, so there is no parameter by which it can be varied
  (`e2e-surface.md` §2, D-2).
- **Returns:** a mapping keyed by the indices `0`, `1` and `2`, each value a plain record carrying the
  action's `name` (`fold`, `check-call`, `raise`) and, for the raise, the resolution that it denotes the
  engine's minimum legal completion (§2). It is plain data, because the report's header quotes it
  (`protocol.md` §1), and the three indices are the only numbers in it — no bet size, no chip count —
  because the invariance family reads the vocabulary as the set of integers it finds anywhere in the
  record, where a stray `4` would make it `{0, 1, 2, 4}` (`battery.md` §3 FAM-2 case FAM-2.9).
- **Refusals:** none; it has no argument (`e2e-surface.md` §3.2, D-2).
- **Determinism and ordering:** two calls return equal records in ascending index order, and the mask
  `legal_indices` returns is read against exactly these three indices (`battery.md` §3 FAM-2 case FAM-2.9).

## 8. `legal_indices` — a decision's legal indices (`general` row)

- **Signature:** `legal_indices(legal_actions)`.
- **Arguments:** one decision's descriptors — `engine.legal_actions(hand)`, or the same sequence under
  `readout["legal"]`, which the engine makes the same in value and order (`engine/surface.md` §6).
- **Returns:** the indices of those actions, **position-aligned with the argument** — the i-th index is the
  vocabulary index of the i-th descriptor — therefore one per descriptor, and distinct for any descriptor
  set a decision can produce, since §2 allows at most one descriptor per index; and ascending whenever the
  argument is in the engine's order, which is the vocabulary's (§2, `battery.md` §3 FAM-2 case FAM-2.11,
  `e2e-surface.md` §2). An out-of-order argument keeps its own order and is never sorted. The battery reads
  it positionally to turn a policy's chosen descriptor back into an index, so the alignment is contract
  (`tests/e2e/_surface.py` `chosen_index`, `battery.md` §2).
- **Refusals:** an empty sequence, because a decision has at least one legal action and none has zero
  (`engine/surface.md` §6); a value that is not a sequence of descriptors; a descriptor outside the
  three-index vocabulary, with that descriptor named. No fold is substituted for an unknown action (D-2,
  `e2e-surface.md` §2).
- **Determinism:** one descriptor sequence gives one index sequence, with no randomness and no state
  (`battery.md` §3 FAM-16 case FAM-16.10, ASM-2).

## 9. `decode_action` — an index, one descriptor (`general` row)

- **Signature:** `decode_action(index)`.
- **Arguments:** one of the three indices and nothing else, because a descriptor is hand-independent and
  carries no amount (`engine/surface.md` §2, `e2e-surface.md` §2).
- **Returns:** the descriptor `engine.apply_action` accepts — the shared spelling of §2, whose raise
  denotes the minimum legal completion of whatever decision it is applied to (`e2e-surface.md` §2, D-2). It
  is accepted wherever that index is legal at the decision it is applied to, which is the round trip of §2
  (`battery.md` §3 FAM-2 case FAM-2.10).
- **Refusals:** an index outside `{0, 1, 2}`, and a value that is not an integer, a `bool` included; each
  names the violated contract, and an unknown action is never mapped to a default (`e2e-surface.md` §2, D-2).
- **Determinism:** one index gives one descriptor, equal by value and stable in text across calls
  (`engine/surface.md` §2, `battery.md` §3 FAM-16 case FAM-16.11).
