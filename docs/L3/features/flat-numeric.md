# features — `flat-numeric`, the dense encoding

- **Owner:** the dense encoding — its block order, the slot order inside each block, the card→slot
  map it shares with the token encoding, the shape's amount normalisers, the history slot, and the
  arithmetic that sums to 203
- **Rev:** 2 · **Date:** 2026-11-09
- **Ceiling:** 140 lines. At the ceiling, split by owner — never append

## 1. What one observation is

One `flat-numeric` observation is a `float32` `numpy.ndarray` of shape `(203,)`: one fixed-width block
per carried field, concatenated in `fields` order (`encoder.md` §3.1), and no id, no index and no pad —
every slot is a number a learner can read directly. `kind` is `"dense-numeric"` and `vocabulary` is
`None` (`encodings.md` §1, §3).

The width is fixed by L2 and is not this document's to revisit: `encodings.md` §3 fixes all nine block
widths. What L3 fixes is the **order** of the blocks, the **slot order inside** a block, and the
**derivation** that turns a value into a number. The second declared shape moves the last of those only:
block order, widths, offsets and slot orders are the same on both shapes, and §4's divisor table is the one
thing here that is the shape's (`sizing.md` §5, `docs/L2/features/shapes.md` §2).

## 2. The block table, and the arithmetic that reaches 203

| # | `field` | `offset` | `width` | writer | `reads` | what it writes |
|---|---|---|---|---|---|---|
| 1 | `street` | 0 | 4 | `street-onehot` | `(street,)` | one-hot over preflop, flop, turn, river |
| 2 | `seat` | 4 | 2 | `seat-index` | `(seat,)` | the acting seat's index, the button flag |
| 3 | `hole` | 6 | 34 | `card-onehot`, 2 slots | `(hole,)` | two card slots of 17, in `hole`'s order |
| 4 | `board` | 40 | 85 | `card-onehot`, 5 slots | `(board,)` | five card slots of 17; an undealt slot is zeros |
| 5 | `stacks` | 125 | 2 | `stacks-scaled`, the shape's stack divisor (§4) | `(stacks, seat)` | the acting seat's stack, then the other's |
| 6 | `pot` | 127 | 1 | `amount-scaled`, the shape's pot divisor (§4) | `(pot,)` | the pot |
| 7 | `to_call` | 128 | 1 | `amount-scaled`, the shape's `to_call` divisor (§4) | `(to_call,)` | the amount to call |
| 8 | `limit` | 129 | 2 | `limit-scaled`, the shape's amount and count divisors (§4) | `(limit,)` | the bet size in force, the bet-or-raise actions this street |
| 9 | `history` | 131 | 72 | `history-onehot`, 24 slots | `(history,)` | 24 slots of 3, one per applied action |

The widths sum to the declared shape, and each offset is the sum of the widths before it:

    4 + 2 + 34 + 85 + 2 + 1 + 1 + 2 + 72 = 203
    34 = 2 × 17,   85 = 5 × 17,   72 = 24 × 3,   17 = 13 + 4
    offsets: 0, 4, 6, 40, 125, 127, 128, 129, 131          (131 + 72 = 203)

The block order is the field order (`encoder.md` §3.1) — the same nine facts in the same order as the
token encoding, so a reader who knows one knows the other, and one order serves both representations.

## 3. The card slot map — 17 = 13 ranks + 4 suits

A card slot is 17 wide: `[0..12]` is the rank one-hot, `[13..16]` the suit one-hot — the same 17 on both
shapes, since no shape touches this map. Within the block, card slot `k` starts at `offset + 17 * k`, and a
card spelled `"<rank><suit>"` sets exactly two slots:

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

## 4. The amount derivations — the shape's divisor table

Every amount is divided by **the shape's** declared divisor and written as a `float32` in `[0, 1]` — fixed
divisors, never a range fitted from data, each that value's own maximum in that shape (`sizing.md` §5):

| Value | `fixed-limit-20` — the default (ASM-6) | `no-limit-100` (D-27, D-29) |
|---|---|---|
| a stack | ÷20 — the chips a hand begins with | ÷100 — the same, at the shape's total |
| the pot | ÷40 — the chips a hand begins with | ÷200 |
| `to_call` | ÷20 | ÷100 |
| the amount in force | ÷4 — the big bet, so 2 → 0.5 and 4 → 1.0 | ÷100 — the minimum legal raise-to, up to the stack |
| the bet-or-raise actions this street | ÷4 — the cap of ASM-6, and the count's own maximum | ÷50 — the most such actions a street can produce |

The five numbers are **the shape row's**, not the encoding's: a divisor of 40 on a 200-chip game is a clip
rather than a normalisation (`sizing.md` §5, ASM-39, `guardrails.md` G16). The widths, the offsets and the
slot orders of §2, §3 and §5 do not move between shapes — only this table does.

Rejected: min-max scaling over the values a run happens to see (it would make the encoding a function
of the data, not of the readout, so two runs of one seed would differ — ASM-2, `surface.md` §6), and
clipping at 1.0 (a clip is a silent substitution, and the divisors above make it unnecessary: no valid
readout exceeds its divisor).

`stacks` is the one block that reads a second fact: `reads` is `("stacks", "seat")` and the slots are
`[stacks[i] / s, stacks[1 - i] / s]` with `i` the acting seat's index and `s` the shape's stack divisor —
L2's *the acting seat's stack, then the other's* (`encodings.md` §3). `seat` is `[float(i), 1.0 if button
else 0.0]`; slot 0 is legitimately `0.0` for seat 0, which is a value and not a pad.

## 5. The history block

The history is 24 slots of 3, one slot per applied action, oldest first:

    for j, entry in enumerate(history):
        slot 131 + 3 * j + action_of_entry(entry) = 1.0      # history.py; the verb map below
    slots 131 + 3 * j for j >= len(history) stay all-zero

`action_of_entry` (one helper in `history.py`, `layout.md` §1) reads ASM-E2's grammar and returns the
**kind** of the action applied: `folds` → 0, `checks` → 1, `calls` → 1, `raises` → 2 — the history slot's
own three-way width, and not a vocabulary index: this block is three wide on both shapes, because a past
bet's size is not a fact the learner is given (`sizing.md` §5, ASM-39). It refuses an entry that is not one
of the four forms, naming it (`errors.md` §3). The entry's street, seat and amount are not carried: they are
other blocks, or not facts of the readout at all (`encodings.md` §2).

24 slots is enough and needs no truncation rule on the default shape: ASM-6's cap of four bet-or-raise
actions a street makes a hand at most `3 × 6 + 5 = 23` applied actions (`encodings.md` §3). The capacity is
the block's, not a shape's: **24** entries are accepted, and a 25th is refused rather than truncated.

## 6. What is refused, and what is not

Refused, each naming the field (and, for a card, the card too — `errors.md` §3): a `street` outside the
four; a `seat` that is not `(index, flag)` with an index in `0, 1` and a real `bool` flag; a `hole` that
is not exactly two cards; a card whose spelling is not a rank from `"23456789TJQKA"` followed by a suit
from `"cdhs"`; a `board` longer than five; a `stacks`, `pot`, `to_call` or `limit` entry that is not a
non-negative integer (`numpy` integers are fine; a `bool` is not a chip count); a `limit` that is not two
integers; a `history` that is not a sequence of at most 24 entries of the documented grammar.

Every one of those checks is **gated on the type first** — a `street` must be a `str` before it is compared
against the four, a card must be a `str` before its characters are read, a history amount must be ASCII
digits — so no foreign type reaches an equality protocol it defines for itself (a one-element `numpy` array
compares equal to a string, a multi-element one raises `ValueError`). The refusal, never a leaked
`ValueError`, is what `errors.md` §1 asks for, and no shape adds or removes one.

**Not** refused: the same card twice in `hole` or `board` (a slot carries whatever the deal put there);
`hole` equal to a `board` card (the deal's business); a readout whose `pot + sum(stacks)` is not the shape's
chips in play, 40 or 200 by shape (`readout.md` §2 — re-checking it here would be a second source of truth);
an extra key in the readout, `legal` included (`surface.md` §6); a `history` shorter than 24 (the normal
case); any chip count at all — there is no bucket to miss.

## 7. What the unit battery may assert

The declared shape and dtype on both shapes; that `encode` returns a fresh `float32` array of `(203,)` twice
for one readout; that the nine blocks sit at the offsets of §2 and their widths sum to 203, on the default
shape and again on `build_encoder(name, shape="no-limit-100")`, whose only difference is §4's divisors; that
the street and history blocks are one-hots (exactly one `1.0` per live action, a whole-zero slot past the
end); that an undealt board slot is all-zero; that `hole`'s card slots mark exactly the rank and suit of each
card and nothing else; that the `history` block is the **last** 72 slots; that the readout is untouched, no
random state moved, and each refusal of §6 happens with the field named.
