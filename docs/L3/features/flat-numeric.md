# features — `flat-numeric`, the dense encoding

- **Owner:** the dense encoding — its block order, the slot order inside each block, the card→slot map it shares
  with the token encoding, the shape's amount normalisers and both per-seat blocks' declared modes, the history
  slot and the shape's capacity behind it, and the arithmetic that reaches 203, 329 and 433
- **Rev:** 4 · **Date:** 2026-11-10
- **Ceiling:** 140 lines. At the ceiling, split by owner — never append

## 1. What one observation is

One `flat-numeric` observation is a `float32` `numpy.ndarray` — `(203,)` on `fixed-limit-20`, `(329,)` on
`no-limit-100` and `(433,)` on `six-seat-no-limit-100`: one fixed-width block per carried field, concatenated in
`fields` order (`encoder.md` §3.1), and no id, no index and no pad — every slot is a number a learner reads directly.
`kind` is `"dense-numeric"` and `vocabulary` is `None` on every row (`encodings.md` §1, §3).

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

**The literal 131 does not hold on the six-seat row.** The slots no seat count touches are 127 — `4 + 34 + 85 + 1 + 1 + 2`:
street, hole, board, pot, `to_call` and `limit` — and the two per-seat blocks add `2 × seats`, so the history block
starts at `127 + 2 × 2 = 131` at two seats and `127 + 2 × 6 = 139` at six. Each offset is the sum of the widths before
it and the widths sum to the declared shape: `131 + 3 × 24 = 203`, `131 + 3 × 66 = 329`, `139 + 3 × 98 = 433` (`capacity.md` §2, ASM-44).

    0, 4, 6, 40, 125, 127, 128, 129, 131          -- two seats: 127 + 2 × 2 = 131 slots before the history
    0, 4, 10, 44, 129, 135, 136, 137, 139         -- six seats: 127 + 2 × 6 = 139 slots before the history

The block order is the field order (`encoder.md` §3.1) — the same nine facts in the same order as the token encoding,
so a reader who knows one knows the other and one order serves both representations.

## 3. The card slot map — 17 = 13 ranks + 4 suits

A card slot is 17 wide: `[0..12]` is the rank one-hot, `[13..16]` the suit one-hot — the same 17 on every row, since
no shape touches this map. Card slot `k` starts at `offset + 17 * k`, and a card spelled `"<rank><suit>"` sets two
slots:

    rank_index = "23456789TJQKA".index(<rank>)   # "2" -> 0, ..., "T" -> 8, ..., "A" -> 12
    suit_index = "cdhs".index(<suit>)            # "c" -> 0, "d" -> 1, "h" -> 2, "s" -> 3
    slot offset + 17 * k + rank_index      = 1.0
    slot offset + 17 * k + 13 + suit_index = 1.0

`"Td"` therefore sets `offset + 17k + 8` and `offset + 17k + 14`. Both alphabets are ASM-E1's own and in their own
order (`README.md` §4), so **one** map serves both encodings: the same `rank_index` and `suit_index` give the token id
`1 + 4 * rank_index + suit_index` (`card-tokens.md` §3), and `cards.py` holds that one reading. `hole` writes
`hole[0]` into slot 0 and `hole[1]` into slot 1 — the readout's own order, never sorted (a sort would be a second
spelling of the deal, D-3); `board` writes `board[i]` into slot `i` for `i < len(board)` and leaves the rest all-zero,
which is what "not yet dealt" is.

## 4. The amount derivations, and both per-seat blocks' modes

Every amount is divided by **the shape's** declared divisor and written as a `float32` in `[0, 1]` — fixed divisors,
never a range fitted from data, each that value's own maximum in that shape (`sizing.md` §5):

| Value | `fixed-limit-20` — the default (ASM-6) | `no-limit-100` (D-27, D-29) | `six-seat-no-limit-100` (D-33) |
|---|---|---|---|
| a stack | ÷20 — the chips a hand begins with | ÷100 — the same, at the shape's total | ÷100, the two-seat row's |
| the pot | ÷40 — the chips a hand begins with | ÷200 | **÷600** — the chips in play at six seats |
| `to_call` | ÷20 | ÷100 | ÷100 |
| the amount in force | ÷4 — the big bet, so 2 → 0.5 and 4 → 1.0 | ÷100 — the minimum legal raise-to, up to the stack | ÷100 |
| the bet-or-raise actions this street | ÷4 — the cap of ASM-6, and the count's own maximum | ÷50 — the most such actions a street can produce | ÷50 |

The five numbers are **the shape row's**, not the encoding's: a divisor of 40 on a 200-chip game is a clip rather than
a normalisation, and the six-seat row moves the pot's alone, because six seats change the chips in play and not the
stack (`sizing.md` §5, ASM-39, `docs/L1/seats.md` §2, `guardrails.md` G16). Six widths, the offsets and the slot orders
of §2, §3 and §5 do not move between rows — only this table, both per-seat widths and the history capacity do
(`shapes.md` §8, ASM-42, ASM-44). Rejected: min-max scaling over the values a run happens to see (it would make the
encoding a function of the data and not of the readout — ASM-2, `surface.md` §6), and clipping at 1.0 (a clip is a
silent substitution, and the divisors above make it unnecessary: no valid readout exceeds its divisor).

**Both per-seat blocks are the shape's, and each is one writer with two declared modes — never a third writer.** `seat`
is `[float(i), 1.0 if button else 0.0]` under `index-flag`: the declared button seat is seat 0 on every row, so that
pair is the acting seat's one-hot over the two seats read in reverse — seat 0 writes `[0, 1]`, seat 1 `[1, 0]` — which
is why the default shape's observations do not move; under `one-hot` it is one slot per seat, `1.0` at the acting
index, and slot 0 is legitimately `0.0` for seat 0, a value and not a pad. `stacks` reads a second fact only under
`actor-first`, where `reads` is `("stacks", "seat")` and the slots are `[stacks[i] / s, stacks[1 - i] / s]` with `s` the
row's stack divisor; under `seat-order` it reads `("stacks",)` and writes one slot per seat (`encodings.md` §3, ASM-44).

## 5. The history block

The history is the row's slots of 3, one slot per applied action, oldest first — 24 slots from 131 to 202 on the
default row, 66 from 131 to 328 on `no-limit-100`, and 98 from 139 to 432 on `six-seat-no-limit-100`:

    for j, entry in enumerate(history):
        slot <131 at two seats, 139 at six> + 3 * j + action_of_entry(entry) = 1.0    # the verb map below
    slots <131, 139> + 3 * j for j >= len(history) stay all-zero

`action_of_entry` (one helper in `history.py`, `layout.md` §1) reads ASM-E2's grammar and returns the **kind** of the
action applied: `folds` → 0, `checks` → 1, `calls` → 1, `raises` → 2 — the history slot's own three-way width, and not
a vocabulary index: this block is three wide on every row, because a past bet's size is not a fact the learner is
given (`sizing.md` §5, ASM-39). It refuses an entry that is not one of the four forms, naming it; the entry's street,
seat and amount are not carried, since they are other blocks or not facts of the readout at all (`errors.md` §3).

How many slots the block declares is **the shape's**, and it is the block's refusal threshold as well as its length:
24 entries encode on `fixed-limit-20`, 66 on `no-limit-100` and 98 on `six-seat-no-limit-100`, and one entry more is
refused rather than truncated, naming the field, the capacity and the count. The writer reads that number from the
shape row's `params`, so no second code path holds it (`shapes.md` §8, ASM-42, `docs/L2/features/capacity.md` §1, §3).

## 6. What is refused, and what is not

Refused, each naming the field (and, for a card, the card too — `errors.md` §3): a `street` outside the four; a `seat`
that is not `(index, flag)` with an index in `0 .. seats − 1` and a real `bool` flag; a `hole` that is not exactly two
cards; a card whose spelling is not a rank from `"23456789TJQKA"` followed by a suit from `"cdhs"`; a `board` longer
than five; a `stacks` that is not `seats` non-negative integers, two or six, naming the field and the count; a `pot`,
`to_call` or `limit` entry that is not a non-negative integer (`numpy` integers are fine; a `bool` is not a chip
count); a `limit` that is not two integers; a `history` that is not a sequence of at most the row's capacity — 24, 66
or 98 — entries of the documented grammar (`capacity.md` §1, §3, ASM-44).

Every one of those checks is **gated on the type first** — a `street` must be a `str` before it is compared against the
four, a card must be a `str` before its characters are read, a history amount must be ASCII digits — so no foreign type
reaches an equality protocol it defines for itself (a one-element `numpy` array compares equal to a string, a
multi-element one raises `ValueError`). The refusal, never a leaked `ValueError`, is what `errors.md` §1 asks for.

**Not** refused: the same card twice in `hole` or `board` (a slot carries whatever the deal put there); `hole` equal to
a `board` card; a readout whose `pot + sum(stacks)` is not the shape's chips in play — 40, 200 or 600 by row
(`readout.md` §2, re-checking which would be a second source of truth); an extra key in the readout, `legal` included
(`surface.md` §6); a `history` shorter than the capacity; any chip count at all.

## 7. What the unit battery may assert

The declared shape and dtype on all three rows — `(203,)`, `(329,)` and `(433,)`, the widths §2 derives; that `encode`
returns a fresh `float32` array of that shape twice for one readout; that the blocks sit at the offsets of §2 and the
history block — one-hots, one `1.0` per live action, a whole-zero slot past the end — ends the observation on each row,
whose only other differences are §4's divisors, both per-seat widths and their modes; that an undealt board slot is
all-zero and each hole card marks its rank and suit; that the `history` block is the **last** `3 × capacity` slots;
that 24 entries encode on the default row, 66 on the second and 98 on the six-seat one, and one more is refused on each;
that the readout is untouched, no random state moved, and each refusal of §6 names the field (`capacity.md` §1–§3).
