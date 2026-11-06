# features — `flat-numeric`, the dense encoding

- **Owner:** the dense encoding — its block order, the slot order inside each block, the card→slot
  map it shares with the token encoding, the amount normalisers, the history slot, and the arithmetic
  that sums to 203
- **Ceiling:** 140 lines. At the ceiling, split by owner — never append

## 1. What one observation is

One `flat-numeric` observation is a `float32` `numpy.ndarray` of shape `(203,)`: one fixed-width block
per carried field, concatenated in `fields` order (`encoder.md` §3.1), and no id, no index and no pad —
every slot is a number a learner can read directly. `kind` is `"dense-numeric"` and `vocabulary` is
`None` (`encodings.md` §1, §3).

The width is fixed by L2 and is not this document's to revisit: `encodings.md` §3 fixes all nine block
widths. What L3 fixes is the **order** of the blocks, the **slot order inside** a block, and the
**derivation** that turns a value into a number.

## 2. The block table, and the arithmetic that reaches 203

| # | `field` | `offset` | `width` | writer | `reads` | what it writes |
|---|---|---|---|---|---|---|
| 1 | `street` | 0 | 4 | `street-onehot` | `(street,)` | one-hot over preflop, flop, turn, river |
| 2 | `seat` | 4 | 2 | `seat-index` | `(seat,)` | the acting seat's index, the button flag |
| 3 | `hole` | 6 | 34 | `card-onehot`, 2 slots | `(hole,)` | two card slots of 17, in `hole`'s order |
| 4 | `board` | 40 | 85 | `card-onehot`, 5 slots | `(board,)` | five card slots of 17; an undealt slot is zeros |
| 5 | `stacks` | 125 | 2 | `stacks-scaled`, ÷20 | `(stacks, seat)` | the acting seat's stack, then the other's |
| 6 | `pot` | 127 | 1 | `amount-scaled`, ÷40 | `(pot,)` | the pot |
| 7 | `to_call` | 128 | 1 | `amount-scaled`, ÷20 | `(to_call,)` | the amount to call |
| 8 | `limit` | 129 | 2 | `limit-scaled`, ÷4 ÷3 | `(limit,)` | the bet size in force, the raises this street |
| 9 | `history` | 131 | 72 | `history-onehot`, 24 slots | `(history,)` | 24 slots of 3, one per applied action |

The widths sum to the declared shape, and each offset is the sum of the widths before it:

    4 + 2 + 34 + 85 + 2 + 1 + 1 + 2 + 72 = 203
    34 = 2 × 17,   85 = 5 × 17,   72 = 24 × 3,   17 = 13 + 4
    offsets: 0, 4, 6, 40, 125, 127, 128, 129, 131          (131 + 72 = 203)

The block order is the field order (`encoder.md` §3.1) — the same nine facts in the same order as the
token encoding, so a reader who knows one knows the other. Rejected: history first, or the cards first.
Both put one order behind a fact set the project declares once, and neither buys anything a dense vector
can use — a position in a dense vector is not a thing a model reads as an order.

## 3. The card slot map — 17 = 13 ranks + 4 suits

A card slot is 17 wide: `[0..12]` is the rank one-hot, `[13..16]` the suit one-hot. Within the block,
card slot `k` starts at `offset + 17 * k`. A card spelled `"<rank><suit>"` sets exactly two slots:

    rank_index = "23456789TJQKA".index(<rank>)   # "2" -> 0, ..., "T" -> 8, ..., "A" -> 12
    suit_index = "cdhs".index(<suit>)            # "c" -> 0, "d" -> 1, "h" -> 2, "s" -> 3
    slot offset + 17 * k + rank_index      = 1.0
    slot offset + 17 * k + 13 + suit_index = 1.0

`"Td"` therefore sets `offset + 17k + 8` and `offset + 17k + 14`. Both alphabets are ASM-E1's own and
in their own order (`README.md` §4), so **one** map serves both encodings: the same `rank_index` and
`suit_index` give the token id `1 + 4 * rank_index + suit_index` (`card-tokens.md` §3). `cards.py` holds
that one reading.

`hole` writes `hole[0]` into card slot 0 and `hole[1]` into card slot 1 — the readout's own order, never
sorted (a sort would be a second spelling of the deal, D-3). `board` writes `board[i]` into card slot `i`
for `i < len(board)`; card slots `len(board)..4` stay all-zero, which is what "not yet dealt" is.

## 4. The amount derivations

Every amount is divided by a fixed divisor and written as a `float32` in `[0, 1]`. Fixed divisors, never
a range fitted from data:

| Value | Divisor | Range it takes | Reaches |
|---|---|---|---|
| a stack | 20 — the chips a hand begins with | 0–20 | 0.0–1.0 |
| the pot | 40 — the chips a hand begins with | 3–40 | 0.075–1.0 |
| `to_call` | 20 | 0–20 | 0.0–1.0 |
| the bet size in force | 4 — the big bet | 2 or 4 | 0.5 or 1.0 |
| the raises this street | 3 — the raise cap less the opening bet | 0–3 | 0.0–1.0 |

Rejected: min-max scaling over the values a run happens to see (it would make the encoding a function
of the data, not of the readout, so two runs of one seed would differ — ASM-2, `surface.md` §6), and
clipping at 1.0 (a clip is a silent substitution, and the divisors above make it unnecessary: no valid
readout exceeds its divisor).

`stacks` is the one block that reads a second fact: `reads` is `("stacks", "seat")` and the slots are
`[stacks[i] / 20, stacks[1 - i] / 20]` with `i` the acting seat's index — L2's *the acting seat's stack,
then the other's* (`encodings.md` §3). `seat` is `[float(i), 1.0 if button else 0.0]`; note that slot 0
of the `seat` block is legitimately `0.0` for seat 0, which is a value and not a pad.

## 5. The history block

The history is 24 slots of 3, one slot per applied action, oldest first:

    for j, entry in enumerate(history):
        slot 131 + 3 * j + action_of_entry(entry) = 1.0      # history.py; the verb map below
    slots 131 + 3 * j for j >= len(history) stay all-zero

`action_of_entry` (one helper in `history.py`, `layout.md` §1) reads ASM-E2's grammar and returns the
vocabulary index of the action that was applied: `folds` → 0, `checks` → 1, `calls` → 1, `raises` → 2 —
the vocabulary's own order (`vocabulary.md` §1). It refuses an entry that is not one of the four forms,
naming the entry (`errors.md` §3), because a fifth form is a spelling this design cannot read and
guessing would silently mislabel an action. The entry's street, seat and amount are not carried: the
street is its own block, the seat is its own block, and the amount of a past action is not a fact the
readout carries anywhere else, so carrying it here would add a tenth fact (`encodings.md` §2).

24 slots is enough and needs no truncation rule: the raise cap of ASM-6 makes a hand at most
`3 × 6 + 5 = 23` applied actions (`encodings.md` §3). The refusal threshold is therefore **24**, the
block's capacity, and not 23, the hand's maximum: a 24-entry history is representable (no hand produces
one) and is accepted, and a 25th entry is refused rather than truncated — a truncation would silently
drop the fact that broke the rule.

## 6. What is refused, and what is not

Refused, each naming the field (and, for a card, the card too — `errors.md` §3): a `street` outside the
four; a `seat` that is not `(index, flag)` with an index in `0, 1` and a real `bool` flag; a `hole` that
is not exactly two cards; a card whose spelling is not a rank from `"23456789TJQKA"` followed by a suit
from `"cdhs"`; a `board` longer than five; a `stacks`, `pot`, `to_call` or `limit` entry that is not a
non-negative integer (`numpy` integers are fine; a `bool` is not a chip count); a `limit` that is not two
integers; a `history` that is not a sequence of at most 24 entries of the documented grammar.

Every one of those checks is **gated on the type first** — a `street` must be a `str` before it is
compared against the four, a card must be a `str` before its characters are read, a history amount must
be ASCII digits — so no value of a foreign type reaches an equality protocol it defines for itself (a
one-element `numpy` array compares equal to a string, and a multi-element one raises `ValueError` from
`bool()`). The refusal, never a leaked `ValueError`, is what `errors.md` §1 asks for.

**Not** refused: the same card twice in `hole` or `board` (a slot carries whatever the deal put there);
`hole` equal to a `board` card (that is the deal's business, not the encoding's); a readout whose
`pot + sum(stacks)` is not 40 (that is the engine's invariant, `readout.md` §2, and re-checking it here
would be a second source of truth); an extra key in the readout, `legal` included (`surface.md` §6); a
`history` shorter than 24 (that is the normal case); any chip count at all, because there is no bucket
to fall outside of.

## 7. What the unit battery may assert

The declared shape and dtype; that `encode` returns a fresh `float32` array of `(203,)` twice for one
readout; that the nine blocks sit at the offsets of §2 and that their widths sum to 203; that the
street and history blocks are one-hots (exactly one `1.0` per live action, a whole-zero slot past the
end); that an undealt board slot is all-zero; that `hole`'s card slots mark exactly the rank and suit of
each card and nothing else; that the `history` block is the **last** 72 slots; that the readout is
untouched and that no random state moved; and that each refusal of §6 happens with the field named.
