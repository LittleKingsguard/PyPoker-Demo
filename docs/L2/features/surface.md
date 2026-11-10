# features — the callable surface

- **Layer:** L2 · **Module:** `features` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-09
- **Owner of this file:** the surface — the seven module-level names of `src/features/`, each with its
  argument contract, its return, its refusals and its ordering (D-12, `e2e-surface.md` §1)
- **Ceiling:** 170 lines. At the ceiling, split by owner — never append

## 1. Rules that hold of every entry point

Each of the seven names is a module-level name of the `features` package, and nothing below one of them is
contract (`e2e-surface.md` §1, brief §5). Six rules are shared and are stated here once (D-12, D-13):

- The seven names are fixed: L2 refines types, record keys, defaults and error classes and never adds,
  removes or renames an entry point (D-12, `e2e-surface.md` §1).
- An invalid argument is refused by raising an error that names the violated contract — the refusing entry
  point and what it refused, its class free — and no entry point coerces a value, substitutes a default,
  swallows an error or returns part of a record (`e2e-surface.md` §2, D-12).
- No entry point draws randomness, seeds or advances the global `random` stream, and none takes a seed, so
  every name here is a function of its arguments alone (`e2e-surface.md` §2, ASM-2, `protocol.md` §4).
- **Three names take a game shape** — `build_encoder`, `action_space` and `decode_action` — as an optional
  **keyword** whose absence is the default shape, `fixed-limit-20`; the other four take none, because the
  shape is the encoder's once it is built (`shapes.md` §1, §5, D-29, `e2e-surface.md` §2).
- An encoder is an opaque value a caller only hands back to `observation_spec` and `encode`; no caller
  inspects, compares, serialises or rebuilds one (`e2e-surface.md` §1). Every other returned value is plain
  data — a mapping, a sequence of names or indices, or the observation array — because `action_space` is
  quoted in a report's header family beside `game_config` (`protocol.md` §1, `e2e-surface.md` §3.2).

## 2. The action vocabulary and the action descriptor

The vocabulary is the **shape's** — the fixed-limit shape declares three indices and the no-cap shape six,
in each shape's own declared order — and it is not a rung's (`e2e-surface.md` §2, `shapes.md` §3, D-29).
The default shape's three, which is what a caller naming no shape gets, are:

| Index | Action | What the descriptor denotes |
|---|---|---|
| 0 | fold | give up the hand |
| 1 | check/call | check when `to_call` is 0, otherwise call it |
| 2 | raise | the engine's minimum legal completion for that decision, unique in fixed-limit (`e2e-surface.md` §2, D-2) |

Five consequences bind both sides of this edge, and four of them hold on either shape (`e2e-surface.md` §2):

- a descriptor carries no amount, is hand-independent and compares by value, so one value denotes one index
  on one shape at every decision of that shape (`engine/surface.md` §2, `shapes.md` §4);
- the spelling is shared with `engine` and is fixed here: the descriptors are the shape's own names, and
  that round trip — `decode_action` returns one, `legal_indices` recognizes one — is the contract between
  the two modules (`e2e-surface.md` §3.2, D-13);
- `engine.legal_actions` returns a decision's descriptors in the shape's declared order, at most one per
  index, so its legal indices are distinct and ascending whenever the argument is the engine's order
  (`engine/surface.md` §2, §6, `sizing.md` §3);
- fold is absent where `to_call` is 0, because folding where checking is free is not an action of that
  decision (`engine/surface.md` §2, `battery.md` §3 FAM-16);
- a raise descriptor still carries no amount: `engine` resolves it — the minimum legal completion on the
  fixed-limit shape, a band's own maximum on the no-cap one — and `decode_action` never claims legality, so
  applying a decoded index that decision does not allow is the caller's violation, refused by
  `engine.apply_action` (`engine/surface.md` §7, `sizing.md` §2, D-2).

## 3. `encodings` — the declared encodings (`fixed` row)

- **Signature:** `encodings()`.
- **Arguments:** none: the encoding set is the ladder's, so there is no parameter by which it can be varied
  (D-3, `e2e-surface.md` §2). It takes no shape because a spec record does not depend on one (§5).
- **Returns:** a mapping keyed by the two encoding names — `flat-numeric` and `card-tokens` — each value the
  record `observation_spec` returns for that encoding (§5, `encodings.md` §1–§4); both names appear and no
  third encoding does (`ladder.md` §2, D-3). Two calls return equal records in the ladder's order, and the
  catalogue is plain data a report's header may quote (`protocol.md` §1).
- **Refusals:** none; it has no argument and nothing to vary (`e2e-surface.md` §3.2, D-3).

## 4. `build_encoder` — one encoder (`fixed` row)

- **Signature:** `build_encoder(name, *, shape=None)`.
- **Arguments:** `name`, one of the two names `encodings` declares — the encoding a variant entry names
  (`ladder.md` §3, `records.md` §2); and `shape`, the game shape's name, optional, whose absence is the
  default shape. No seed, no size and no rung (`ladder.md` §3, `e2e-surface.md` §3.2, D-29).
- **Returns:** an encoder — the opaque value `observation_spec` and `encode` take (§1) — for that encoding
  **on that shape**: the normalisers and bucket edges an observation is written with are the shape's, so an
  encoder is one encoding on one game (`shapes.md` §2, §5, `sizing.md` §5). It is the only way to obtain
  one, so every observation the ladder consumes came from a declared encoding (`e2e-surface.md` §5).
- **Refusals:** a name that is not one of the two, with that name in the error (`e2e-surface.md` §2, §5,
  `battery.md` §4); a shape name outside the catalogue, naming it and the declared names and never
  defaulted (`shapes.md` §2, §6).
- **Determinism:** two encoders built from one name and one shape declare equal specs and encode one
  readout to equal observations; building draws no randomness and keeps no state an observation could see
  (ASM-2).

## 5. `observation_spec` — what one observation is (`fixed` row)

- **Signature:** `observation_spec(encoder)`.
- **Arguments:** an encoder from `build_encoder` (`e2e-surface.md` §3.2).
- **Returns:** one mapping, read under **exactly these six keys — no seventh** (`shapes.md` §5):

| Key | Content |
|---|---|
| `representation` | **the encoding's own name** — `flat-numeric` or `card-tokens`; the invariance family reads it as that name (`e2e-surface.md` §2, `battery.md` §3 FAM-2 case FAM-2.6) |
| `kind` | the representation family: `dense-numeric` or `token-sequence` (`e2e-surface.md` §3.2) |
| `fields` | the readout facts the observation carries: the same nine names for both encodings, a subset of `engine.readout`'s eleven, `legal` and the derived `hand_class` excluded (`e2e-surface.md` §2, `encodings.md` §2, `folders.md` §3) |
| `shape` | a tuple of integers, one observation's shape: `(203,)` for `flat-numeric`, `(40,)` for `card-tokens` (`encodings.md` §3–§4) |
| `dtype` | the element type: `float32` for `flat-numeric`, `int32` for `card-tokens` (`encodings.md` §3–§4) |
| `vocabulary` | the number of distinct token ids a `card-tokens` observation can carry, `96`, and `null` for `flat-numeric`: a key this document adds to the record because `agents` sizes an embedding table from it, and the only one a caller depends on beyond the five above it (`module-map.md` §2, `records.md` §1) |

- **The six values are the same on both shapes**, which is `sizing.md` §5's invariance at this edge: the
  slot counts, block widths, dtype and token vocabulary do not move, so the record names no shape and no
  normaliser — an encoder's shape is read in `encode`'s values (`shapes.md` §5, D-29).
- **Refusals:** a value that is not an encoder this module built, naming that contract (`e2e-surface.md`
  §2). **Determinism:** one encoder declares one spec; two calls are equal and the spec depends on no
  readout, hand or seed (`e2e-surface.md` §2, ASM-2).

## 6. `encode` — one readout, one observation (`general` row)

- **Signature:** `encode(encoder, readout)`.
- **Arguments:** an encoder, and a readout in the shape `engine.readout` returns — the eleven facts, with
  `street`, `seat`, `hole`, `board`, `stacks`, `pot`, `to_call`, `limit`, `history`, `legal` and
  `hand_class` all present (`engine/environment.md` §2, `folders.md` §3).
- **Returns:** one observation — a NumPy array of the declared `shape` and `dtype` (`encodings.md` §3–§4).
  It carries the declared `fields` and nothing else, so no observation can show the other seat's cards or
  the undealt deck (`engine/environment.md` §2, D-3), and the divisors and bucket edges it applies are the
  encoder's shape's (`shapes.md` §2).
- **Refusals:** a value that is not an encoder; a readout missing a field this encoding carries; a carried
  field that cannot be represented, such as a `street` outside the four or a `hole` that is not two cards.
  Each names what was violated, and none is defaulted (`e2e-surface.md` §2, D-3). The two facts it does not
  carry — `legal` and `hand_class` — are ignored and not refused (`encodings.md` §2, `folders.md` §3).
  **Determinism:** one encoder and one readout give one observation value for value, and `encode` neither
  mutates its argument nor draws randomness (`battery.md` §3 FAM-16 case FAM-16.9, ASM-2).

## 7. `action_space` — one shape's vocabulary (`fixed` row)

- **Signature:** `action_space(*, shape=None)`.
- **Arguments:** `shape`, the game shape's name, optional: absence is the default shape, whose vocabulary is
  the three indices of §2, so a caller naming no shape gets the mapping this entry point has always
  returned, key for key and value for value (`shapes.md` §3, D-29).
- **Returns:** a mapping keyed by that shape's indices, each value a plain record carrying the action's
  `name` and, for a descriptor that resolves an amount, the resolution it denotes as prose: the fixed-limit
  `raise` says it denotes the engine's minimum legal completion (§2), and a sized band says which part of
  the legal raise interval it takes (`shapes.md` §3, `sizing.md` §2). The keys are in the shape's
  **declared** index order, deliberately not monotone in amount on the second shape (`sizing.md` §3). It is
  plain data, because a report's header quotes it (`protocol.md` §1), and the shape's indices are the only
  numbers in it: no bet size, no chip count, because the invariance family reads the vocabulary as the set
  of integers it finds anywhere in the record (`battery.md` §3 FAM-2 case FAM-2.9, `shapes.md` §3).
- **Refusals:** a shape name outside the catalogue, naming it and the declared names, never defaulted
  (`shapes.md` §6). **Ordering:** two calls with one shape return equal records in that shape's index order,
  and the mask `legal_indices` returns is read against exactly these indices (`battery.md` §3 FAM-2.9).

## 8. `legal_indices` — a decision's legal indices (`general` row)

- **Signature:** `legal_indices(legal_actions)`.
- **Arguments:** one decision's descriptors — `engine.legal_actions(hand)`, or the same sequence under
  `readout["legal"]`, which the engine makes the same in value and order (`engine/surface.md` §6). It takes
  **no shape**: the descriptors are the shape's own, and one's index is its position there (`shapes.md` §4).
- **Returns:** the indices of those actions, **position-aligned with the argument** — the i-th index is the
  i-th descriptor's — therefore one per descriptor, and distinct for any descriptor set a decision can
  produce, since §2 allows at most one descriptor per index. They are ascending whenever the argument is the
  engine's order; an out-of-order argument keeps its own order and is never sorted, and a band masked out at
  the decision is simply absent (`shapes.md` §4, `battery.md` §3 FAM-2 case FAM-2.11). The battery reads it
  positionally to turn a policy's chosen descriptor back into an index (`battery.md` §2).
- **Refusals:** an empty sequence, because a decision has at least one legal action and none has zero
  (`engine/surface.md` §6); a value that is not a sequence of descriptors; a descriptor outside the declared
  vocabulary, with that descriptor named; no fold is substituted for an unknown action (D-2,
  `e2e-surface.md` §2). **Determinism:** one descriptor sequence gives one index sequence, with no
  randomness and no state (`battery.md` §3 FAM-16 case FAM-16.10, ASM-2).

## 9. `decode_action` — an index, one descriptor (`general` row)

- **Signature:** `decode_action(index, *, shape=None)`.
- **Arguments:** one index of the named shape's vocabulary — 0 to 2 by default, 0 to 5 on the no-cap shape —
  and the shape, optional, whose absence is the default (`engine/surface.md` §2, `shapes.md` §4).
- **Returns:** the descriptor `engine.apply_action` accepts in that shape's vocabulary (§2), whose raise
  denotes that shape's resolution, and which is the round trip of §2 (`battery.md` §3 FAM-2.10, D-2).
- **Refusals:** an index outside the shape's vocabulary — naming it, the shape and that vocabulary — and a
  value that is not an integer, a `bool` included; neither is mapped to a default (`e2e-surface.md` §2,
  `shapes.md` §6, D-2), and one index on one shape gives one descriptor, stable in text across calls
  (`battery.md` §3 FAM-16 case FAM-16.11).
