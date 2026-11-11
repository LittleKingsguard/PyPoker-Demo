# features — the game shape, and its part of this module

- **Layer:** L2 · **Module:** `features` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-10
- **Owner of this file:** the shape as this module's own data (§1), the per-shape amount normalisers (§2),
  the per-shape action vocabulary (§3), the index and the mask (§4), what the shape does not move, with the
  capacity's own document pointed at (§5), and the refusals and the join it owes (§6) (D-29, D-33, `shapes.md` §2,
  §8, `seats.md` §3, `sizing.md` §5, ASM-42, ASM-44)
- **Ceiling:** 155 lines. At the ceiling, split by owner — never append

## 1. The shape is this module's data, and one table is its whole statement

A shape is a declared row of `engine.game_shapes()` — the seats, blinds, stack, chips in play, bet
structure, action vocabulary, head width, amount normalisers and history capacity of one game — and
`fixed-limit-20` is first and the **default** (`shapes.md` §2, §8, D-29, D-33). This module needs six things
from a row: the descriptors **in that shape's index order**, the five amount normalisers, the bucket edges the
token encoding resolves an amount to, the **history block's capacity** — the number of action slots the block
declares, which is also its refusal threshold — the **seat count**, which is the width of both per-seat blocks,
and the **token vocabulary** those blocks need (`shapes.md` §8, `seats.md` §3, ASM-42, ASM-44).

`features` imports no other project module (`module-map.md` §2, D-13), so the row is **restated once** in
`src/features/declarations.py`'s shape table, under the same names and the same five normaliser keys
`engine` publishes, and nothing else in the module writes a divisor, a bucket edge, a capacity, a seat count or
a mode down: every block's `params` is read from that row, beside the module's own id constants. The two
catalogues are held equal by the **join** battery, not by an import — the same way this module restates the
descriptor spelling instead of importing it (`encodings.md` §5, `vocabulary.md` §1, D-13).

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

| Normaliser | `fixed-limit-20` — the default (ASM-6) | `no-limit-100` (D-29) | `six-seat-no-limit-100` (D-33) | What it scales |
|---|---|---|---|---|
| `stack` | 20 | 100 | 100 | one seat's stack |
| `pot` | 40 | 200 | **600** | the pot |
| `to_call` | 20 | 100 | 100 | the amount to call |
| `amount` | 4 | 100 | 100 | the bet size in force — the big bet on one shape, the minimum legal raise-to on the others |
| `count` | 4 | 50 | 50 | the bet-or-raise actions made this street: the cap on one shape, the stack's bound on the others |

The fixed-limit column is today's table exactly, so the default shape's encoding reproduces today's
observation **byte for byte** — that is a gated invariant and not a description (`shapes.md` §5). The second
column is why the table is the shape's at all: a divisor of 40 on a 200-chip game is not a normalisation but a
clip, and the count of 4 would saturate on a shape whose stack allows fifty raises (`sizing.md` §5, D-25). The
third column is the second's at six seats with **one value moved**: the pot divides by the 600 chips in play,
because the seats change the total and not the stack, and a divisor of 200 on a six-seat pot is a clip rather
than a normalisation (`seats.md` §2, `sizing.md` §5, ASM-39). Rejected: one table fitted to the larger game for
all three, which would move every fixed-limit observation and with it every shipped checkpoint's input block
(`sizing.md` §5, `shapes.md` §5).

The dense encoding divides by these five; the token encoding does not use them at all, because it
resolves each amount to a bucket id whose edges are the shape's too — the same row's second half
(`card-tokens.md` §4, `sizing.md` §5).

## 3. The per-shape action vocabulary

| Index | `fixed-limit-20` | `no-limit-100` | `six-seat-no-limit-100` |
|---|---|---|---|
| 0 | `fold` | `fold` | `fold` |
| 1 | `check-call` | `check-call` | `check-call` |
| 2 | `raise` | `raise-quarter` | `raise-quarter` |
| 3 | — | `raise-half` | `raise-half` |
| 4 | — | `raise-all-in` | `raise-all-in` |
| 5 | — | `raise-minimum` | `raise-minimum` |

The third column is the second's, index for index: **a seat count adds no descriptor**, because six seats change
the price of aggression — a bluff must buy five folds — and not the actions a seat may take (`seats.md` §2, D-33,
`shapes.md` §2). The second shape's four raise descriptors partition the legal integer interval between the
minimum legal raise-to and the all-in, each resolving to its own band's maximum, and a band with no legal amount
in it is **empty and masked out**, never collapsed onto its neighbour (`sizing.md` §2). The order is the
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
on the default shape, 0 to 5 on the two uncapped ones. An index outside the shape's vocabulary is refused
naming it, the shape and that shape's vocabulary; a non-integer, a `bool` included, is refused as before
(`surface.md` §9).

## 5. The capacity is the shape's, and what the shape does not move

**Moved to `capacity.md`** (§1–§5): the history block's capacity is the **shape's** — 24 slots on the default
shape, 66 on `no-limit-100` and 98 on `six-seat-no-limit-100`, each derived from its own game's betting — and it
is the block's refusal threshold as well as its width, so a longer history is refused naming the field, the
capacity and the count and never truncated (`shapes.md` §8, `seats.md` §2, ASM-42, ASM-44, `capacity.md` §1–§3).

**What the shape does not move** stays here, because it is this module's whole invariance (`shapes.md` §8,
`sizing.md` §5): five things are the encoding's on every shape — the nine carried fields, the block order, the
card ids, the street ids and the pad. What a shape moves is the divisor table (§2), the bucket edges
(`card-tokens.md` §4), the capacity, the **seat count** with both per-seat blocks' widths and modes, and the
**token vocabulary** those blocks need — 96 ids on the two-seat rows, 102 on the six-seat one, whose seat block
emits ids 96–101 above every id the other rows use, so no existing id is renamed (`seats.md` §3, ASM-44).
`observation_spec` therefore still returns its six keys and **no seventh**: four of them are shape-invariant and
`shape` and `vocabulary` are the shape's own, so the record still names no shape, no normaliser and no capacity.
The head width stays `agents`': 3 by default and 6 on the two uncapped rows, so `param_count` follows the shape
there while this module counts nothing (`sizing.md` §6, ASM-10, ASM-44).

## 6. The refusals, and the join this module owes

A shape name outside the catalogue is refused by the refusing entry point — the message names the entry
point, the rejected value and the **declared names** — and is never defaulted; `build_encoder` refuses an
unknown encoding name before it looks at the shape, so the two refusals cannot trade places
(`surface.md` §1, §4, D-13).

The join is three assertions in the integration battery, and they are the whole of how the restatement of §1
stays true:

- for every shape `engine.game_shapes()` declares, this module's row carries **the same descriptors in the
  same index order** and **the same five normalisers** — so `features.action_space(shape=...)` and
  `engine.game_shapes()[shape]["actions"]` cannot disagree, and neither can the divisors;
- an encoder built for a shape encodes that shape's own `engine.readout` to the declared shape and dtype,
  and `decode_action`'s descriptor is one `engine.apply_action` accepts in that shape's vocabulary
  (`e2e-surface.md` §2, §3.2);
- the shape's **`history` capacity is the engine's own row value**, because `engine.game_shapes()` publishes
  that key now: this module restates it and the join compares the two, so the refusal threshold cannot drift
  from the capacity the catalogue declares (`shapes.md` §2, §8, ASM-42, D-13).

The seat count is the fourth statement and it is joined the same way: `engine.game_shapes()[shape]["seats"]` and
this module's row must agree, because it is the width of both per-seat blocks in both encodings and the bound the
`seat` fact's index is refused against (`seats.md` §3, ASM-44).
