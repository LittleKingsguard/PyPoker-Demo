# features — `card-tokens`, the token encoding

- **Owner:** the token encoding — its token order, the card→id map it shares with the dense encoding,
  the bucket edges of the five bucketed blocks, the pad's spelling, and the arithmetic that sums to 40
  tokens over 96 ids
- **Ceiling:** 175 lines. At the ceiling, split by owner — never append

## 1. What one observation is

One `card-tokens` observation is an `int32` `numpy.ndarray` of shape `(40,)`: one token id per carried
occurrence of a fact, which a learned embedding turns into a vector from R3 on (`ladder.md` §2). `kind`
is `"token-sequence"`, `vocabulary` is `96`, and the ids are `0`–`95` — id `0` is the pad and nothing
else (`encodings.md` §4).

The token counts and the id ranges are L2's and are not revisited here: `encodings.md` §4 fixes every
one of them. What L3 fixes is the **order** of the tokens, the **id each value receives inside** its
range, the **bucket edges**, and the pad's spelling beyond id `0`.

## 2. The token table, and the arithmetic that reaches 40

| # | `field` | `offset` | tokens | writer | `reads` | ids it emits |
|---|---|---|---|---|---|---|
| 1 | `street` | 0 | 1 | `street-id` | `(street,)` | 53–56 |
| 2 | `seat` | 1 | 2 | `seat-ids` | `(seat,)` | 57–60 |
| 3 | `hole` | 3 | 2 | `card-ids`, 2 | `(hole,)` | 1–52, never the pad |
| 4 | `board` | 5 | 5 | `card-ids`, 5 | `(board,)` | 1–52, pad `0` for an undealt slot |
| 5 | `stacks` | 10 | 2 | `stacks-buckets` | `(stacks,)` | 77–84 |
| 6 | `pot` | 12 | 1 | `amount-bucket`, §4 | `(pot,)` | 69–76 |
| 7 | `to_call` | 13 | 1 | `amount-bucket`, §4 | `(to_call,)` | 61–68 |
| 8 | `limit` | 14 | 2 | `limit-ids` | `(limit,)` | 85–88, 89–92 |
| 9 | `history` | 16 | 24 | `history-ids` | `(history,)` | 93–95, pad `0` past the end |

The token counts sum to the declared shape, and each offset is the sum of the counts before it:

    1 + 2 + 2 + 5 + 2 + 1 + 1 + 2 + 24 = 40
    offsets: 0, 1, 3, 5, 10, 12, 13, 14, 16                  (16 + 24 = 40)

The order is the field order, exactly as the dense encoding's is (`encoder.md` §3.1, `README.md` §5):
the same nine facts in the same order in both representations, with the history last in both — the block
that varies in length is the one at the end. Rejected: L2's §4 table order for this encoding (cards
first, then the street). It would give one fact set two orders and put the variable-length block
somewhere different in each representation, for no gain: a token position is not a fact a model reads as
an order, it is a slot an embedding index is looked up by.

## 3. Cards, streets, seats and the pad

**A card is `1 + 4 * rank_index + suit_index`**, with the two indices of `flat-numeric.md` §3 and the
two alphabets of ASM-E1. Rank-major, suit-minor:

    2c 2d 2h 2s = 1 2 3 4     …     As = 52
    1 + 4 * 12 + 3 = 52

Rejected: suit-major (`1 + 13 * suit + rank`). Rank-major keeps a hand's ranks contiguous in id space
(`2c..2s` are four neighbouring ids, and the thirteen ids of one suit are not), which is the shape the
dense encoding's 13-wide rank one-hot already has — so one map, one mental model, both encodings.

**A street is `53 + street_index`**: `preflop` 53, `flop` 54, `turn` 55, `river` 56 — the readout's own
order (`readout.md` §2).

**A seat is two tokens and four ids**: token 1 is `57 + index` (`57` seat 0, `58` seat 1), token 2 is
`59 + flag` (`59` no button, `60` the button). The fixed game produces only `(57, 60)` — the button is
always seat 0 — and `(58, 59)`; the other two ids exist because the readout's `seat` type admits them and
this encoding is a function of the **value**, not of the game. Rejected: one combined id for the pair
(it would carry two facts in one token, and L2 fixes two tokens and four ids).

**The pad is `0`**, and only two blocks emit it: a `board` slot at or past `len(board)` ("not yet
dealt") and a `history` token at or past `len(history)` ("no action"). `hole` never pads — a decision
always has two cards. No other block may ever emit `0`, and the pad is **not** a bucket: `to_call`'s
zero has its own id, `61` (`encodings.md` §4). Rejected: a pad of `96` or of `-1` (an id outside the
declared vocabulary, or a negative index into an embedding table).

## 4. The bucket ladders

Five blocks resolve a quantity to one id. Each ladder is a list of `(upper bound, id)` pairs read from
the top, the last bound is unbounded, and **each ladder is total over the non-negative integers** — so no
amount is ever unrepresentable and `encode` refuses only a value that is not a non-negative integer, never
a magnitude (`errors.md` §4).

`to_call`, ids 61–68 — fine at the bottom because the boundary between checking and folding is `0`:

| id | the amount to call |
|---|---|
| 61 | 0 — its own id, and never the pad |
| 62 | 1 |
| 63 | 2 |
| 64 | 3 |
| 65 | 4 |
| 66 | 5–6 |
| 67 | 7–10 |
| 68 | 11 or more |

`pot`, ids 69–76 — the first bound holds the opening pot of 3 (`readout.md` §5), the rest roughly doubles:

| id | the pot | id | the pot |
|---|---|---|---|
| 69 | 0–3 | 73 | 13–16 |
| 70 | 4–5 | 74 | 17–24 |
| 71 | 6–8 | 75 | 25–32 |
| 72 | 9–12 | 76 | 33 or more |

`stacks`, ids 77–84 — one token per seat, **in the readout's seat order** (`stacks[0]` then `stacks[1]`):

| id | one seat's stack | id | one seat's stack |
|---|---|---|---|
| 77 | 0–1 | 81 | 9–11 |
| 78 | 2–3 | 82 | 12–14 |
| 79 | 4–5 | 83 | 15–17 |
| 80 | 6–8 | 84 | 18 or more |

Rejected for `stacks`: the dense encoding's acting-seat-first order. It would make this block read a
second fact (`seat`) for no gain — the acting seat is already carried by tokens 1 and 2 — and it would
put the two encodings' stack orders in disagreement for no reader's benefit. The dense encoding cannot
make that choice: L2 fixes its slot order (`encodings.md` §3).

`limit`, token 1 — the bet size in force, ids 85–88: `85` a size below the small bet (0–1), `86` the
small bet `2` (preflop and flop), `87` the big bet `4` or a size just below it (3–4, the turn and river),
`88` a size above the big bet (5 or more).

`limit`, token 2 — the raises made this street, ids 89–92: `89` none, `90` one, `91` two, `92` three or
more (the ASM-6 cap is three raises after the opening bet, so `92` is the cap and any excess).

## 5. The history block

24 tokens, oldest first, one per applied action, and the pad past the end:

    for j, entry in enumerate(history):
        token 16 + j = HISTORY_ID[action_of_entry(entry)]     # 93 fold, 94 check-call, 95 raise
    tokens 16 + j for j >= len(history) stay 0                # the pad

`action_of_entry` is one helper read off ASM-E2's grammar, shared with the dense encoding
(`flat-numeric.md` §5, `layout.md` §1). The entry's street, seat and amount are not carried, for the
reasons `flat-numeric.md` §5 gives: they are other blocks, or not facts of the readout at all.

## 6. The vocabulary is 96, and nothing may leave it

    pad 1 (id 0) + cards 52 (1–52) + streets 4 (53–56) + seat 4 (57–60) + to_call 8 (61–68)
      + pot 8 (69–76) + stacks 8 (77–84) + bet size 4 (85–88) + raises 4 (89–92)
      + history 3 (93–95)  =  96 ids, 0–95

`observation_spec`'s `vocabulary` declares `96` and `agents` sizes an embedding table from it
(`encodings.md` §6). The ten ranges above are disjoint and cover `0`–`95` with no gap and no overlap, so
the count is their lengths' sum. **Every id an observation can carry is in `0–95`**: `card-ids` emits
`1–52` or `0`, every bucketed block emits exactly its own range, and the history emits `93–95` or `0`.

## 7. What is refused, and what is not

Refused, each naming the field (and, for a card, the card too — `errors.md` §3): a `street` outside the four (there is no id for a fifth
street); a `seat` that is not `(index, flag)` with an index in `0, 1` and a real `bool` flag (ids 57–60
are exactly four); a `hole` that is not exactly two cards; a card whose spelling is not a rank from
`"23456789TJQKA"` followed by a suit from `"cdhs"` (ids 1–52 are exactly 52 cards); a `board` longer than
five; a `stacks`, `pot`, `to_call` or `limit` entry that is not a non-negative integer (`numpy` integers
are fine; a `bool` is not a chip count); a `history` that is not a sequence of at most 24 entries of the
documented grammar.

**Not** refused: the same card twice (two ids, two slots); a `board` of one or two cards (representable —
one card and four pads — and the deal does not produce one, so refusing it would be a refusal the
contract does not have); any magnitude of any amount, because every ladder is total (§4); an extra key in
the readout, `legal` included; a `history` shorter than 24.

## 8. What the unit battery may assert

The declared shape `(40,)` and dtype `int32`; that `encode` returns a fresh array twice for one readout;
that the nine blocks sit at the offsets of §2 and their counts sum to 40; that every emitted id is in
`0–95`; that a card id is in `1–52` and that `"2c"` is `1` and `"As"` is `52`; that a `board` slot past
`len(board)` and a history token past `len(history)` are `0`; that a `to_call` of `0` is `61` and not
`0`; that the history block is the **last** 24 tokens; that each bucket ladder is monotone and total on
its own id range by walking it through the public `encode` at its edges and beyond them; that the readout
is untouched and no random state moved; and that each refusal of §7 happens with the field named.
