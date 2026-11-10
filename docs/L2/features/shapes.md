# features — the game shape, and its part of this module

- **Layer:** L2 · **Module:** `features` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-09
- **Owner of this file:** the shape as this module's own data (§1), the per-shape amount normalisers (§2),
  the per-shape action vocabulary (§3), the index and the mask (§4), what the shape does not move (§5), and
  the refusals and the join it owes (§6) (D-29, `shapes.md` §2, `sizing.md` §5)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append

## 1. The shape is this module's data, and one table is its whole statement

A shape is a declared row of `engine.game_shapes()` — the seats, blinds, stack, chips in play, bet
structure, action vocabulary, head width and amount normalisers of one game — and `fixed-limit-20` is
first and the **default** (`shapes.md` §2, D-29). This module needs three things from a row: the
descriptors **in that shape's index order**, the five amount normalisers, and — its own and no other
module's — the bucket edges the token encoding resolves an amount to.

`features` imports no other project module (`module-map.md` §2, D-13), so the row is **restated once** in
`src/features/declarations.py`'s shape table, under the same two names and the same five normaliser keys
`engine` publishes, and nothing else in the module writes a divisor or a bucket edge down: every block's
`params` is read from that row. The two catalogues are held equal by the **join** battery, not by an
import — the same way this module restates the descriptor spelling instead of importing it
(`encodings.md` §5, `vocabulary.md` §1, D-13).

Absence of a shape is the **default** shape and is not a defaulting of a name; a name outside the
catalogue is refused naming it and the declared names, never substituted (`shapes.md` §2, §3, D-13).

**Three of the seven names take the shape, as an optional keyword** (`surface.md` §4, §7, §9):

    build_encoder(name, *, shape=None)   action_space(*, shape=None)   decode_action(index, *, shape=None)

The other four take none: the shape is the encoder's once it is built, so `encode` reads it from the
value it is given, and neither `encodings`, `observation_spec` nor `legal_indices` needs it at all (§4,
§5). It is a **keyword-only** optional because the arity cases that already hold of these names pin each
one's positional arguments, and no existing case may be weakened (`battery.md` §5, D-11): a keyword-only
optional adds the shape while every positional call in the tree keeps meaning exactly what it meant, and
that is also why no caller changes.

## 2. The per-shape amount normalisers — the divisor table

The five normalisers are the shape's, and they are the only divisors either encoding applies:

| Normaliser | `fixed-limit-20` — the default (ASM-6) | `no-limit-100` (D-29) | What it scales |
|---|---|---|---|
| `stack` | 20 | 100 | one seat's stack |
| `pot` | 40 | 200 | the pot |
| `to_call` | 20 | 100 | the amount to call |
| `amount` | 4 | 100 | the bet size in force — the big bet on one shape, the minimum legal raise-to on the other |
| `count` | 4 | 50 | the bet-or-raise actions made this street: the cap on one shape, the stack's bound on the other |

The fixed-limit column is today's table exactly, so the default shape's encoding reproduces today's
observation **byte for byte** — that is a gated invariant and not a description (`shapes.md` §5). The
second column is why the table is the shape's at all: a divisor of 40 on a 200-chip game is not a
normalisation but a clip, and the count of 4 would saturate on a shape whose stack allows fifty raises
(`sizing.md` §5, D-25). Rejected: one table fitted to the larger game for both, which would move every
fixed-limit observation and with it every shipped checkpoint's input block (`sizing.md` §5, `shapes.md`
§5).

The dense encoding divides by these five; the token encoding does not use them at all, because it
resolves each amount to a bucket id whose edges are the shape's too — the same row's second half
(`card-tokens.md` §4, `sizing.md` §5).

## 3. The per-shape action vocabulary

| Index | `fixed-limit-20` | `no-limit-100` |
|---|---|---|
| 0 | `fold` | `fold` |
| 1 | `check-call` | `check-call` |
| 2 | `raise` | `raise-quarter` |
| 3 | — | `raise-half` |
| 4 | — | `raise-all-in` |
| 5 | — | `raise-minimum` |

The second shape's four raise descriptors partition the legal integer interval between the minimum legal
raise-to and the all-in, each resolving to its own band's maximum, and a band with no legal amount in it
is **empty and masked out**, never collapsed onto its neighbour (`sizing.md` §2). The order is the
measurement's — the measured price order, worst first — and it is **deliberately not monotone in
amount**: the all-in sits at 4 and the minimum raise at 5, so no reader, no test and no tie-break can read
an index as a size, and a tie resolves toward a worse-priced band rather than toward the best one
(`sizing.md` §3).

A descriptor still carries no amount and stays hand-independent, so one index denotes one descriptor on one
shape at every decision of that shape (`surface.md` §2). `action_space` publishes the shape's descriptors
in exactly this order, and `engine.legal_actions` returns a decision's legal subset in the same order
(`surface.md` §7, `sizing.md` §3).

## 4. The index is the shape's, and the mask stays positional

`legal_indices` takes **no shape** and needs none: a descriptor's index is its position in the shape that
declares it, and the two vocabularies share their first two entries, so one descriptor→index table is
total over every descriptor a decision can carry. The rule is unchanged — the i-th index is the i-th
descriptor's, nothing is sorted and nothing is de-duplicated — and it now covers a six-descriptor
vocabulary and a decision whose legal set has masked bands out:

    ("check-call", "raise-minimum")                      -> (1, 5)
    ("fold", "check-call", "raise-quarter", "raise-half",
     "raise-all-in", "raise-minimum")                    -> (0, 1, 2, 3, 4, 5)

A masked-out band is simply absent from the argument, because a decision's legal set is whatever
`engine.legal_actions` returned; the mask names no legality of its own (`surface.md` §8).

`decode_action` **does** take the shape, because an index alone cannot say how many indices exist: 0 to 2
on the default shape, 0 to 5 on the other. An index outside the shape's vocabulary is refused naming it,
the shape and that shape's vocabulary; a non-integer, a `bool` included, is refused as before
(`surface.md` §9).

## 5. What the shape does not move

`sizing.md` §5 pins the invariance, and this module is where it is visible: both encodings keep their
**slot counts** (203 dense slots, 40 tokens), every block width, their dtypes, the token **vocabulary of
96 ids**, the nine carried fields, the 24 history slots of 3 kinds, the card ids, the street and seat ids
and the pad. What moves is only the divisor table (§2) and the bucket edges (`card-tokens.md` §4).

Two consequences, both deliberate:

- `observation_spec` returns its six keys and **no seventh**, and names no shape: the six values are
  shape-invariant, so a record that named a shape or a normaliser would be a key every caller would have
  to branch on for no information the shape-invariant part does not already give (D-3, `sizing.md` §5).
  An encoder's shape is its provenance, and its effect is read in `encode`'s values;
- the head width is `agents`' and not this module's: 3 on the default shape and 6 on the other, so
  `param_count` follows the shape there and this module counts nothing (`sizing.md` §6, ASM-10).

**One invariance does not survive the second shape, and it is named here rather than smoothed over.** The
history block is 24 slots on both shapes, and its capacity is the default shape's bound: ASM-6's cap of four
bet-or-raise actions a street makes a fixed-limit hand at most 23 applied actions. The no-cap shape declares
no cap, and a *legal* hand there holds far more — measured, a minimum-raise hand on `no-limit-100` applies
50 actions, so the decision whose readout carries 25 entries is refused by `encode` in both encodings,
exactly as the design's own rule requires (a refusal, never a truncation — `flat-numeric.md` §5). The block
may not be widened here: `sizing.md` §5 fixes the slot count and ASM-39 refuses a per-shape layout, so the
gap is an L1 question returned as an `ADJUDICATION` — whether the second shape declares a second layout, a
bound on its hand, or a documented refusal — and this module implements the declared block meanwhile.

## 6. The refusals, and the join this module owes

A shape name outside the catalogue is refused by the refusing entry point — the message names the entry
point, the rejected value and the **declared names** — and is never defaulted; `build_encoder` refuses an
unknown encoding name before it looks at the shape, so the two refusals cannot trade places
(`surface.md` §1, §4, D-13).

The join is two assertions in the integration battery, and they are the whole of how the restatement of §1
stays true:

- for every shape `engine.game_shapes()` declares, this module's row carries **the same descriptors in the
  same index order** and **the same five normalisers** — so `features.action_space(shape=...)` and
  `engine.game_shapes()[shape]["actions"]` cannot disagree, and neither can the divisors;
- an encoder built for a shape encodes that shape's own `engine.readout` to the declared shape and dtype,
  and `decode_action`'s descriptor is one `engine.apply_action` accepts in that shape's vocabulary
  (`e2e-surface.md` §2, §3.2).
