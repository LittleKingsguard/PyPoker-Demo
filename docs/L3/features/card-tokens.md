# features — `card-tokens`, the token encoding

- **Owner:** the token encoding — its token order, the card→id map it shares with the dense encoding, the shape's
  bucket edges of the five bucketed blocks, the two per-seat blocks' declared modes and the shape's token
  vocabulary, the pad's spelling, and the arithmetic that reaches 40, 82 and 122 tokens
- **Rev:** 4 · **Date:** 2026-11-10
- **Ceiling:** 175 lines. At the ceiling, split by owner — never append

## 1. What one observation is

One `card-tokens` observation is an `int32` `numpy.ndarray` — `(40,)` on `fixed-limit-20`, `(82,)` on `no-limit-100` and
`(122,)` on `six-seat-no-limit-100`: one token id per carried occurrence of a fact, which a learned embedding turns into
a vector from R3 on (`ladder.md` §2). `kind` is `"token-sequence"`, ids run `0 … vocabulary − 1`, and `0` is the pad.

The **vocabulary is the shape's own** — `96` on the two two-seat rows and `102` on the six-seat one — and so is the
history block's count (`encodings.md` §4, `capacity.md` §1–§2, ASM-42, ASM-44). What L3 fixes is the **order** of the
tokens, the **id each value gets inside** its range, the **bucket edges** and the pad beyond id `0`; a row moves those
edges, that block's length and its `seat` ids, while the twelve seat-invariant tokens, the card map and the pad never
move (`sizing.md` §5, ASM-44).

## 2. The token table, and the arithmetic that reaches 40, 82 and 122

| # | `field` | `offset` — two / six seats | tokens | writer | `reads` | ids it emits |
|---|---|---|---|---|---|---|
| 1 | `street` | 0 / 0 | 1 | `street-id` | `(street,)` | 53–56 |
| 2 | `seat` | 1 / 1 | `seats` — 2 / 6 | `seat-ids`, the row's mode (§3) | `(seat,)` | 57–60, or 96–101 at six seats |
| 3 | `hole` | 3 / 7 | 2 | `card-ids`, 2 | `(hole,)` | 1–52, never the pad |
| 4 | `board` | 5 / 9 | 5 | `card-ids`, 5 | `(board,)` | 1–52, pad `0` for an undealt slot |
| 5 | `stacks` | 10 / 14 | `seats` — 2 / 6 | `stacks-buckets` | `(stacks,)` | 77–84 |
| 6 | `pot` | 12 / 20 | 1 | `amount-bucket`, §4 | `(pot,)` | 69–76 |
| 7 | `to_call` | 13 / 21 | 1 | `amount-bucket`, §4 | `(to_call,)` | 61–68 |
| 8 | `limit` | 14 / 22 | 2 | `limit-ids` | `(limit,)` | 85–88, 89–92 |
| 9 | `history` | 16 / 24 | the capacity — 24 / 66 / 98 | `history-ids` | `(history,)` | 93–95, pad `0` past the end |

The token counts sum to the declared shape, and each offset is the sum of the counts before it. The counts no seat
count touches are twelve — `street` 1, `hole` 2, `board` 5, `to_call` 1, `pot` 1, `limit` 2 — and the two per-seat
blocks add `2 × seats`, so the history block starts at `12 + 2 × 2 = 16` at two seats and `12 + 2 × 6 = 24` at six:

    1, 2, 2, 5, 2, 1, 1, 2  -- two seats; the two per-seat counts become 6 each at six seats
    16 + 24 = 40  on fixed-limit-20     16 + 66 = 82  on no-limit-100     24 + 98 = 122  on the six-seat row
    offsets: 0, 1, 3, 5, 10, 12, 13, 14, 16      -- two seats
             0, 1, 7, 9, 14, 20, 21, 22, 24      -- six seats: 12 + 2 × 6 = 24 before the history

The order is the field order, exactly as the dense encoding's is (`encoder.md` §3.1, `README.md` §5): the same nine facts
in the same order in both representations, the history last and therefore the one block that varies in length
(`shapes.md` §8). Rejected: L2's §4 table order (cards first, then the street) — one fact set with two orders.

## 3. Cards, streets, seats and the pad

**A card is `1 + 4 * rank_index + suit_index`**, with the two indices of `flat-numeric.md` §3 and the two alphabets
of ASM-E1. Rank-major, suit-minor:

    2c 2d 2h 2s = 1 2 3 4     …     As = 52
    1 + 4 * 12 + 3 = 52

Rejected: suit-major (`1 + 13 * suit + rank`). Rank-major keeps a hand's ranks contiguous in id space (`2c..2s` are four
neighbouring ids), the shape the dense encoding's 13-wide rank one-hot already has — one map, both encodings.

**A street is `53 + street_index`**: `preflop` 53, `flop` 54, `turn` 55, `river` 56 — the readout's own order (`readout.md` §2).

**A seat is `seats` tokens, and the two modes are declared data of one existing writer.** Under `index-flag`, on both
two-seat rows, token 1 is `57 + index` (`57` seat 0, `58` seat 1) and token 2 is `59 + flag` (`59` no button, `60` the
button): such a row produces only `(57, 60)` and `(58, 59)`, the declared button being seat 0, while all four ids exist
because the readout's `seat` type admits them. Under `one-hot`, on the six-seat row, the acting seat's slot holds
`96 + index` and every other slot the pad `0`, so the block emits ids **96–101**, above every id the two-seat rows use —
their top id is 95 (`docs/L1/seats.md` §3, ASM-44). Rejected: one combined id for the pair.

**The pad is `0`**, and only two blocks emit it: a `board` slot at or past `len(board)` ("not yet dealt") and a
`history` token at or past `len(history)` ("no action") — plus, on a `one-hot` row, the `seat` block's non-acting
slots — while `hole` never pads, since a decision always has two cards. No other block may emit `0`, and the pad is
**not** a bucket: `to_call`'s zero has its own id, `61` (`encodings.md` §4). Rejected: a pad of `96` or of `-1` (an id
outside the vocabulary, or a negative index into an embedding table).

## 4. The bucket ladders — the shape's, over the same ids

Five blocks resolve a quantity to one id. Each ladder is a list of `(upper bound, id)` pairs read from the top, the last
bound unbounded, and **each ladder is total over the non-negative integers** — no amount is unrepresentable and `encode`
refuses only a non-integer, never a magnitude (`errors.md` §4). A row re-edges the same ids of each bucketed block; no id
and no vocabulary entry moves (`sizing.md` §5, `shapes.md` §8, ASM-44). A cell reads *the default row's range →
`no-limit-100`'s → the six-seat row's*, with `=` where the last two agree.

| ids | `to_call`: default → no-limit → six seats | `pot`: default → no-limit → six seats | `stacks`: default → no-limit → six seats |
|---|---|---|---|
| 61 · 69 · 77 | 0 — its own id, never the pad → 0 = | 0–3 → 0–4 → 0–12 | 0–1 → 0–5 = |
| 62 · 70 · 78 | 1 = | 4–5 → 5–8 → 13–24 | 2–3 → 6–10 = |
| 63 · 71 · 79 | 2 = | 6–8 → 9–16 → 25–48 | 4–5 → 11–20 = |
| 64 · 72 · 80 | 3 = | 9–12 → 17–32 → 49–96 | 6–8 → 21–40 = |
| 65 · 73 · 81 | 4 → 4–5 = | 13–16 → 33–64 → 97–192 | 9–11 → 41–60 = |
| 66 · 74 · 82 | 5–6 → 6–10 = | 17–24 → 65–100 → 193–300 | 12–14 → 61–80 = |
| 67 · 75 · 83 | 7–10 → 11–25 = | 25–32 → 101–150 → 301–450 | 15–17 → 81–95 = |
| 68 · 76 · 84 | 11 or more → 26 or more = | 33 or more → 151 or more → 451 or more | 18 or more → 96 or more = |

`to_call` is fine at the bottom because the boundary between checking and folding is `0`; `pot`'s first bound holds the
default row's opening pot of 3, the second row's of 4 and the six-seat row's of 12; and `stacks` carries one token per
seat, **in the readout's seat order** (`stacks[0]` … `stacks[seats − 1]`), which is one fact on every row.

**The six-seat row's `pot` ladder is re-edged for 600 chips, exactly three times `no-limit-100`'s** — `12, 24, 48, 96,
192, 300, 450`, the ratio of the two games' chips in play — because a divisor of 200 on a six-seat pot is a clip and not
a normalisation (`sizing.md` §5, ASM-39, `docs/L1/seats.md` §2). Its `to_call`, `stacks`, `amount` and `count` ladders
are `no-limit-100`'s, because a 100-chip stack, the blinds and the minimum bet are the same at six seats.

Rejected for `stacks`: the dense encoding's `actor-first` order, which would read a second fact (`seat`) for no gain —
the acting seat is already tokens 1 and 2 — and put the two encodings' stack orders in disagreement (`encodings.md` §3).

`limit`, token 1 (the amount in force, ids 85–88) and token 2 (the bet-or-raise actions made this street, ids
89–92), re-edged per row and unchanged in id:

| ids | the amount in force: default → no-limit → six seats | the count: default → no-limit → six seats |
|---|---|---|
| 85 · 89 | 0–1, below the small bet → 0–5 = | 0 → 0 = |
| 86 · 90 | 2, the small bet → 6–10 = | 1 → 1–2 = |
| 87 · 91 | 3–4, the big bet or just below it → 11–25 = | 2 → 3–5 = |
| 88 · 92 | 5 or more → 26 or more = | 3 or more → 6 or more = |

ASM-6's cap is four bet-or-raise actions a street on the default row — post-flop the opening bet plus three raises,
pre-flop four raises after the posted blind — so `92` catches 3, 4 and any excess and the ladder stays total. The two
uncapped rows have no cap: their count is bounded by the stack and normalised by ÷50 (`flat-numeric.md` §4).

## 5. The history block

The capacity's tokens, oldest first, one per applied action, and the pad past the end — 24 tokens from 16 to 39 on the
default row, 66 from 16 to 81 on `no-limit-100`, and 98 from 24 to 121 on `six-seat-no-limit-100`:

    for j, entry in enumerate(history):
        token <16 at two seats, 24 at six> + j = HISTORY_ID[action_of_entry(entry)]    # 93 fold, 94 check-call, 95 raise
    tokens <16, 24> + j for j >= len(history) stay 0                                   # the pad

`action_of_entry` is one helper read off ASM-E2's grammar, shared with the dense encoding (`flat-numeric.md` §5,
`layout.md` §1); the entry's street, seat and amount are not carried, for the reasons `flat-numeric.md` §5 gives. The
kind is **not** a vocabulary index: the rows declare three and six action descriptors and this block is three wide on
every one, so a `raises` entry is id `95` whatever band the engine resolved it to (`sizing.md` §5, ASM-39).

How many tokens the block declares is the row's, and the **vocabulary does not follow it**: the same three ids `93`–`95`
and the same pad `0` on all three rows, so the wider block emits no new id (`capacity.md` §1–§3). The count is the
block's **refusal threshold** too — a history of exactly the capacity encodes, one entry more is refused naming the
field, the capacity and the count, measured as `'history' must be at most 98 entries, got 99` on the six-seat row.

## 6. The vocabulary is 96 or 102, and nothing may leave it

    pad 1 (id 0) + cards 52 (1–52) + streets 4 (53–56) + seat 4 (57–60) + to_call 8 (61–68)
      + pot 8 (69–76) + stacks 8 (77–84) + bet size 4 (85–88) + bet-or-raise 4 (89–92)
      + history 3 (93–95)  =  96 ids, 0–95   -- the two-seat rows

`observation_spec`'s `vocabulary` declares `96` on the two two-seat rows and `102` on the six-seat one, and `agents` sizes
an embedding table from it (`encodings.md` §6). The six-seat row adds **six seat ids, `96`–`101`, one per seat slot**, so
its vocabulary is `102` = `0`–`101` and no existing id is renamed (`capacity.md` §4, `docs/L1/seats.md` §3, ASM-44).

The ten ranges above are disjoint and cover `0`–`95` with no gap and no overlap, so the count is their lengths' sum, and
**every id an observation can carry is inside its row's vocabulary**: `card-ids` emits `1–52` or `0`, every bucketed
block its own range, the history `93`–`95` or `0`, and the `one-hot` `seat` block `96`–`101` or `0`.

## 7. What is refused, and what is not

Refused, each naming the field (and, for a card, the card too — `errors.md` §3): a `street` outside the four (there is no
id for a fifth); a `seat` that is not `(index, flag)` with an index in `0 .. seats − 1` and a real `bool` flag (ids 57–60
are exactly four and 96–101 exactly six); a `hole` that is not exactly two cards; a card whose spelling is not a rank
from `"23456789TJQKA"` followed by a suit from `"cdhs"` (ids 1–52 are exactly 52 cards); a `board` longer than five; a
`stacks` that is not `seats` non-negative integers, two or six; a `pot`, `to_call` or `limit` entry that is not a
non-negative integer (`numpy` integers are fine; a `bool` is not a chip count); a `history` that is not a sequence of at
most the row's capacity — 24, 66 or 98 — entries of the documented grammar (`capacity.md` §1, §3, ASM-44).

**Not** refused: the same card twice (two ids, two slots); a `board` of one or two cards (representable, and the
deal does not produce one); any magnitude of any amount, because every ladder is total (§4); an extra key in the
readout, `legal` included; a `history` shorter than the capacity.

## 8. What the unit battery may assert

The declared shape and dtype on all three rows — `(40,)`, `(82,)` and `(122,)`, the counts §2 derives; that `encode`
returns a fresh array twice for one readout; that the blocks sit at the offsets of §2 and the history block ends the
observation; that every emitted id is below the row's own vocabulary — `0–95` at two seats, `0–101` at six; that a card
id is in `1–52`, `"2c"` being `1` and `"As"` `52`; that a `board` slot past `len(board)` and a history token past
`len(history)` are `0`, and that a `to_call` of `0` is `61`; that the history block is the **last** capacity tokens —
24, 66 or 98 — emitting `93`–`95` and the pad and no fourth id; that the `seat` block emits `57`–`60` at two seats and
`96`–`101` with the pad at six; that each ladder is monotone and total on its own id range, walked once per row; that
the readout is untouched, no random state moved, and each refusal of §7 names the field (`capacity.md` §1–§4).
