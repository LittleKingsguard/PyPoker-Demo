# features — the history block's capacity, and it is the shape's

- **Layer:** L2 · **Module:** `features` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-10
- **Owner of this file:** the history block's capacity — that it is the **shape's** and not the encoding's, how it
  is derived from a shape's own betting at two seats and at six, the widths and the seat count that follow from it
  in each encoding, and the refusal it is the threshold of (`shapes.md` §8, `seats.md` §2, ASM-42, ASM-44, D-33)
- **Split from:** `shapes.md` §5, whose section of that name is now a pointer here (ASM-24)
- **Ceiling:** 90 lines. At the ceiling, split by owner — never append

## 1. Why the capacity is the shape's, and what it is derived from

`no-limit-100` declares no bet cap, so a legal hand there applies far more actions than a fixed-limit hand: a bet
or raise advances the street's level by at least the minimum bet of 2, and every seat commits that level on every
street it plays. Measured, a minimum-raise no-limit hand applies 50 actions, and a pool that seated one trained
no-limit model had its encoder refuse a decision at 25 entries — because the 24 slots the block declared were the
**fixed-limit cap's** bound and not that game's (`shapes.md` §8, D-33, D-32).

So a shape declares its own capacity, derived from its own betting rather than chosen (`shapes.md` §8, ASM-42):
the levels a bet-or-raise can reach, summed over the four streets, are at most the chips in play divided by the
seats, and each seat also takes at most two non-bet actions a street. `no-limit-100` gives 200 ÷ 4 = 50 raises plus
4 × 2 × 2 = 16 = **66**; `six-seat-no-limit-100` gives 600 ÷ 12 = 50 plus 4 × 6 × 2 = 48 = **98**; and
`fixed-limit-20` keeps **24**, the number its cap gives. The capacity is **also the block's refusal threshold**: a
history of exactly the capacity encodes, and one entry more is refused naming the field, the capacity and the
count — never truncated (`shapes.md` §8, `seats.md` §2, ASM-42, `sizing.md` §5).

## 2. The widths that follow

The capacity is shape data and the widths follow from it. The 127 dense slots and the 12 tokens that **no seat count
touches** are the encoding's and do not move between shapes; the `seat` and `stacks` blocks are one slot per seat, so
the slots before the history are `127 + 2 × seats` dense and `12 + 2 × seats` tokens (`shapes.md` §8, `seats.md` §3,
ASM-44, `encodings.md` §3–§4):

| Quantity | `fixed-limit-20` — the default | `no-limit-100` | `six-seat-no-limit-100` |
|---|---|---|---|
| seats, and the `seat` and `stacks` block widths — `seats` each | 2, 2 and 2 | 2, 2 and 2 | **6, 6 and 6** |
| history capacity — the block's slots, and its refusal threshold | **24** | **66** | **98** |
| slots before the history — `127 + 2 × seats` | 131 | 131 | **139** |
| `flat-numeric` history width — `3 × capacity` | 72 | 198 | 294 |
| `flat-numeric` observation — `127 + 2 × seats + 3 × capacity` | **203** | **329** | **433** |
| tokens before the history — `12 + 2 × seats` | 16 | 16 | **24** |
| `card-tokens` observation — `12 + 2 × seats + capacity` | **40** | **82** | **122** |
| `card-tokens` vocabulary — the shape's own | **96** | **96** | **102**, six seat ids above the other rows' top |
| `param_count` at `W = 36`, `D = 2` — input + trunk + `A·W + A` | 10,119 | 14,766 | 18,510 |

Rejected: one capacity for every shape, which is the 24 slots that overflowed at 25 against a raiser; and
coarsening the block into aggregated entries, which keeps the width and throws away the resolution the price lives
in (`strata/decisions.md` D-33, D-32). Also rejected: truncating to the most recent 24, a silently different
observation and what the refusal exists to prevent (`sizing.md` §5).

## 3. The refusal, and where the number lives

`encode` accepts a history of at most the shape's capacity and refuses one entry more, naming the field, the
capacity and the count (`errors.md` §3, `flat-numeric.md` §6, `card-tokens.md` §7). The capacity is **one row
value**: it lives in the row beside that row's seat count, five normalisers and five ladders, both block tables
derive their history width from it and the writer `params` carry it (`shapes.md` §8, ASM-42, `guardrails.md` G16).

## 4. What the seat count moves, and what stays the encoding's

Five things are the encoding's on every shape: the nine carried fields, the block order, the card ids, the street
ids and the pad. What the shape moves is the divisor table (`shapes.md` §2), the bucket edges (`card-tokens.md` §4),
this capacity, the **seat count** — which widens the `seat` and `stacks` blocks to one slot per seat in both
encodings — and the **token vocabulary** those blocks need (`seats.md` §3, ASM-44).

- `observation_spec` still returns its six keys and **no seventh**: four are shape-invariant, and `shape` and
  `vocabulary` are the shape's own, so the record names no shape, no normaliser and no capacity. A kind's declared
  observation size stays the **default** row's — `(203,)` dense and `(40,)` over 96 ids (`surface.md` §5, ASM-44);
- the six-seat row's seat ids are `96`–`101`, one per seat slot, above every id the two-seat rows use, so its
  vocabulary is `102` and no existing id is renamed: the two-seat rows keep `96`, and no two blocks of one
  observation can emit one id (`seats.md` §3, `card-tokens.md` §6, ASM-44).

## 5. What is joined now, and what is still arithmetic

The capacity is the engine's too: `engine.game_shapes()` publishes a `history` key on every row — 24, 66 and 98 —
so this module restates it and the integration battery compares the two statements rather than reading the number
out of `shapes.md` §8. The seat count is joined the same way: `seats` reads 2, 2 and 6 (`shapes.md` §8, ASM-44, D-13).

**The 14,766 is now a reading.** `agents.build_learner` takes a non-default shape's input width from the encoder it
is handed, so a spec naming `no-limit-100` beside that shape's 329-wide encoder builds and `agents.param_count`
measures **14,766** — 329·36 + 36 input, 2·(36² + 36) trunk, 6·36 + 6 head. A spec naming **no** shape is still
refused at 203, and that is D-13's identity rule: absence reads as the default shape, where 203 is the size. The
default shape's **10,119** is unchanged and measured (`shapes.md` §8, ASM-40).

**The 18,510 is arithmetic, not a reading.** `agents` does not yet carry `six-seat-no-limit-100` among its shape
names, so no learner can be built there and `agents.param_count` cannot read it: 433·36 + 36 input, 2·(36² + 36)
trunk and 6·36 + 6 head is `shapes.md` §8's arithmetic until that module declares the third name, the head its six
descriptors make and a vocabulary of 102 (`seats.md` §3, ASM-40, ASM-44).

L3 owns everything below the entry point — which block holds the slots, the history block's slot order, the three
action-kind ids it emits and the writer that reads the capacity from the row: `docs/L3/features/flat-numeric.md` §5,
`docs/L3/features/card-tokens.md` §5 (`guardrails.md` G16, D-1).
