# features — `flat-numeric`, the dense encoding

- **Owner:** the dense encoding — its block order, the slot order inside each block, the card→slot map it shares
  with the token encoding, the shape's amount normalisers and both per-seat blocks' declared modes, the history
  slot and the shape's capacity behind it, the arithmetic that reaches 203, 329 and 433, and the bound every
  slot saturates at
- **Rev:** 5 · **Date:** 2026-11-10
- **Ceiling:** 140 lines. At the ceiling, split by owner — never append

## 1. What one observation is

One `flat-numeric` observation is a `float32` `numpy.ndarray` — `(203,)` on `fixed-limit-20`, `(329,)` on `no-limit-100` and
`(433,)` on `six-seat-no-limit-100`: one fixed-width block per carried field in `fields` order (`encoder.md` §3.1), no id, no
index and no pad; `kind` is `"dense-numeric"`, `vocabulary` is `None`, and every slot is in `[0, 1]` (`encodings.md` §1, §3, D-61).

Six widths are fixed by L2; two follow the seat count and the ninth is the history block's, `3 × the capacity`
(`shapes.md` §8, ASM-42). What L3 fixes is the **order** of the blocks, the **slot order inside** a block and the
**derivation** from a value to a number; a row moves only §4's table, both per-seat widths and that block (`capacity.md` §2).

## 2. The block table, and the arithmetic that reaches 203, 329 and 433

| # | `field` | `offset` — two / six seats | `width` | writer | `reads` | what it writes |
|---|---|---|---|---|---|---|
| 1 | `street` | 0 / 0 | 4 | `street-onehot` | `(street,)` | one-hot over preflop, flop, turn, river |
| 2 | `seat` | 4 / 4 | `seats` — 2 / 6 | `seat-index`, the row's mode (§4) | `(seat,)` | `index-flag`: the index, then the button flag; `one-hot`: one slot per seat |
| 3 | `hole` | 6 / 10 | 34 | `card-onehot`, 2 slots | `(hole,)` | two card slots of 17, in `hole`'s order |
| 4 | `board` | 40 / 44 | 85 | `card-onehot`, 5 slots | `(board,)` | five card slots of 17; an undealt slot is zeros |
| 5 | `stacks` | 125 / 129 | `seats` — 2 / 6 | `stacks-scaled`, the row's order and stack divisor (§4) | `(stacks, seat)` or `(stacks,)` | `actor-first`: the acting seat's stack, then the other's; `seat-order`: one per seat |
| 6 | `pot` | 127 / 135 | 1 | `amount-scaled`, the row's pot divisor (§4) | `(pot,)` | the pot |
| 7 | `to_call` | 128 / 136 | 1 | `amount-scaled`, the row's `to_call` divisor (§4) | `(to_call,)` | the amount to call |
| 8 | `limit` | 129 / 137 | 2 | `limit-scaled`, the row's amount and count divisors (§4) | `(limit,)` | the bet size in force, the bet-or-raise actions this street |
| 9 | `history` | 131 / 139 | `3 × capacity` — 72 / 198 / 294 | `history-onehot`, the row's slots | `(history,)` | one slot of 3 per applied action, oldest first |

**The literal 131 does not hold on the six-seat row.** The slots no seat count touches are 127 — `4 + 34 + 85 + 1 + 1 + 2` —
and the two per-seat blocks add `2 × seats`: `131 + 3 × 24 = 203`, `131 + 3 × 66 = 329`, `139 + 3 × 98 = 433` on the three
rows, each offset the sum of the widths before it (`capacity.md` §2, ASM-44). The block order is the field order
(`encoder.md` §3.1) — the same nine facts in the same order as the token encoding.

## 3. The card slot map — 17 = 13 ranks + 4 suits

A card slot is 17 wide: `[0..12]` is the rank one-hot, `[13..16]` the suit one-hot — the same 17 on every row, since
no shape touches this map. Card slot `k` starts at `offset + 17 * k`, and a card spelled `"<rank><suit>"` sets two slots:

    rank_index = "23456789TJQKA".index(<rank>)   # "2" -> 0, ..., "T" -> 8, ..., "A" -> 12
    suit_index = "cdhs".index(<suit>)            # "c" -> 0, "d" -> 1, "h" -> 2, "s" -> 3
    slot offset + 17 * k + rank_index      = 1.0
    slot offset + 17 * k + 13 + suit_index = 1.0

`"Td"` sets `offset + 17k + 8` and `offset + 17k + 14`. Both alphabets are ASM-E1's own and in their own order
(`README.md` §4), so **one** map serves both encodings: the same two indices give the token id `1 + 4 * rank_index + suit_index`
(`card-tokens.md` §3), and `cards.py` holds that one reading. `hole` writes `hole[0]` into slot 0 and `hole[1]` into slot 1 —
the readout's own order, never sorted (a sort would be a second spelling of the deal, D-3); `board` writes `board[i]` into
slot `i` for `i < len(board)` and leaves the rest all-zero, which is "not yet dealt".

## 4. The amount derivations, both per-seat blocks' modes, and the bound

Every slot's value is a **declared numerator over a declared denominator**, and every dense slot is in `[0, 1]`: a
scaled block's denominator is **the shape's** normaliser — fixed, never a range fitted from data — and a value above
the block's declared high **saturates at that high**, the clamp being the block's, never a run's, never silent
(`sizing.md` §5, D-61). The nine blocks, slot by slot:

| block | numerator | denominator: `fixed-limit-20` / `no-limit-100` / `six-seat` | bound |
|---|---|---|---|
| `street` (4) | the street's flag, one-hot | 1 | `exact` — `0.0` or `1.0` |
| `seat` (seats) | `index-flag`: the seat index, then the button flag; `one-hot`: the seat's flag | `seats − 1` = 1, then 1; 1 | `exact` |
| `hole` (34) | the card's rank and suit flags | 1 | `exact` |
| `board` (85) | the same, `0.0` at a slot past the deal | 1 | `exact` |
| `stacks` (seats) | the stack | 20 / 100 / 100 | `saturate` at 1.0 |
| `pot` (1) | the pot | 40 / 200 / 600 | `saturate` at 1.0 |
| `to_call` (1) | the amount to call | 20 / 100 / 100 | `saturate` at 1.0 |
| `limit` slot 0 | the amount in force | 4 / 100 / 100 | `saturate` at 1.0 |
| `limit` slot 1 | the bet-or-raise actions this street | 4 / 50 / 50 | `saturate` at 1.0 |
| `history` (3 × capacity) | the action kind's flag | 1 | `exact` |

The five divisors are **the shape row's**, not the encoding's: a divisor of 40 on a 200-chip game is a clip rather than a
normalisation, and the six-seat row moves the pot's alone, because six seats change the chips in play and not the stack
(`sizing.md` §5, ASM-39, `docs/L1/seats.md` §2, `guardrails.md` G16). A reachable value of exactly 1.0 is legal and not an
error — a six-seat `to_call` of 100, a fixed-limit bet of 4 — and the five scaled blocks saturate there while the four
`exact` ones cannot leave `{0.0, 1.0}` (D-61). Rejected: min-max scaling over the values a run happens to see (it would make
the encoding a function of the data, not of the readout — ASM-2, `surface.md` §6), and a *silent* clip (a clamp nobody
declared is a substitution; the declared high above is not one — D-61). Only §4's divisors, both per-seat widths and the
history capacity move between rows (`shapes.md` §8, ASM-42, ASM-44).

**Both per-seat blocks are the shape's, and each is one writer with two declared modes — never a third writer.** `seat`
is `[i / (seats − 1), 1.0 if button else 0.0]` under `index-flag`: the declared button seat is seat 0 on every row, so
that pair is the acting seat's one-hot over the two seats read in reverse — seat 0 writes `[0, 1]`, seat 1 `[1, 0]`,
`seats − 1` being 1 on both two-seat rows, so no emitted value moves — which is why the default shape's observations do
not move; under `one-hot` it is one slot per seat, `1.0` at the acting index, and slot 0 is legitimately `0.0` for seat
0, a value and not a pad. `stacks` reads a second fact only under `actor-first`, where `reads` is `("stacks", "seat")`
and the slots are `[stacks[i] / s, stacks[1 - i] / s]` with `s` the row's stack divisor; under `seat-order` it reads
`("stacks",)` and writes one slot per seat (`encodings.md` §3, ASM-44).

## 5. The history block

The history is the row's slots of 3, one slot per applied action, oldest first — 24 slots from 131 to 202 on the
default row, 66 from 131 to 328 on `no-limit-100`, and 98 from 139 to 432 on `six-seat-no-limit-100`:

    for j, entry in enumerate(history):
        slot <131 at two seats, 139 at six> + 3 * j + action_of_entry(entry) = 1.0    # the verb map below
    slots <131, 139> + 3 * j for j >= len(history) stay all-zero

`action_of_entry` (one helper in `history.py`, `layout.md` §1) reads ASM-E2's grammar and returns the **kind** of the
action applied: `folds` → 0, `checks` → 1, `calls` → 1, `raises` → 2 — the slot's own three-way width, not a vocabulary
index: the block is three wide on every row, because a past bet's size is not a fact the learner is given (`sizing.md`
§5, ASM-39). It refuses an entry that is not one of the four forms, naming it; the entry's street, seat and amount are
not carried, since they are other blocks or not facts of the readout at all (`errors.md` §3).

How many slots the block declares is **the shape's**, and it is the block's refusal threshold as well as its length: 24
entries encode on `fixed-limit-20`, 66 on `no-limit-100` and 98 on `six-seat-no-limit-100`, and one entry more is refused
rather than truncated, naming the field, the capacity and the count (`shapes.md` §8, ASM-42, `capacity.md` §1, §3).

## 6. What is refused, and what is not

Refused, each naming the field (and, for a card, the card too — `errors.md` §3): a `street` outside the four; a `seat` that
is not `(index, flag)` with an index in `0 .. seats − 1` and a real `bool` flag; a `hole` that is not exactly two cards; a
card not spelled as a rank from `"23456789TJQKA"` then a suit from `"cdhs"`; a `board` longer than five; a `stacks` that is
not `seats` non-negative integers; a `pot`, `to_call` or `limit` entry that is not a non-negative integer (`numpy` integers
are fine; a `bool` is not a chip count); a `limit` that is not two integers; a `history` longer than the row's capacity
(`capacity.md` §1, §3, ASM-44).

Every one of those checks is **gated on the type first** — a `street` must be a `str` before it is compared against the four,
a card a `str` before its characters are read, a history amount ASCII digits — so no foreign type reaches an equality protocol
it defines for itself (a one-element `numpy` array compares equal to a string, a multi-element one raises `ValueError`); the
refusal, never a leaked `ValueError`, is what `errors.md` §1 asks for.

**Not** refused: the same card twice in `hole` or `board`; `hole` equal to a `board` card; a readout whose `pot + sum(stacks)`
is not the shape's chips in play — 40, 200 or 600 by row (`readout.md` §2, re-checking which would be a second source of
truth); an extra key, `legal` included (`surface.md` §6); a `history` shorter than the capacity; and any chip count at all,
which saturates at its block's declared high and is never refused for its magnitude (§4, D-61).

## 7. What the unit battery may assert

The declared shape and dtype on all three rows — `(203,)`, `(329,)` and `(433,)`, the widths §2 derives; that `encode` returns
a fresh `float32` array of that shape twice for one readout; that the blocks sit at the offsets of §2 and the history block —
one-hots, one `1.0` per live action, a whole-zero slot past the end — ends the observation on each row, whose only other
differences are §4's divisors, both per-seat widths and their modes; that an undealt board slot is all-zero and each hole card
marks its rank and suit; that the `history` block is the **last** `3 × capacity` slots; that 24 entries encode on the default
row, 66 on the second and 98 on the six-seat one, and one more is refused on each; that every slot of every observation is in
`[0, 1]`, a scaled block's high exactly; and that the readout is untouched, no random state moved, and each refusal of §6
names the field (`capacity.md` §1–§4, D-61).
