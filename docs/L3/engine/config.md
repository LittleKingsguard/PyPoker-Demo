# engine — the declared shapes

- **Owner:** the shape question: the catalogue and its home in `config.py`, the three rows, the default and the refusal, the `history` capacity that is the row's and not `game_config`'s, `seat_count`, `game_config`'s fifteen keys, chips in play and the divisors, the four raise bands, the index order, and the state each row creates (D-29, D-30, D-33)
- **Ceiling:** 140 lines — raised from 95 for the third row: `six-seat-no-limit-100`, the `history` key that is the row's and not `game_config`'s, `seat_count`, and the sixth-seat numbers. At the ceiling, split by owner — never append

## 1. The catalogue, and its home

`config.py` owns the game's numbers. `_SHAPE_ROWS` is the catalogue, three row dicts default first;
`DEFAULT_SHAPE` names the first; `_GAME_OF` holds each row's `game` words; and `STREETS` with the
default row's constants keep their names, two of them read by `readout` (`surface.md` §3, §12).
`SEAT_COUNT = 2` stays as the **default** shape's seat count — the value an absent shape reads as —
and is not the game's seat count, which is each row's own (`seats.md` §2, ASM-44):

    shape_names() -> tuple[str, ...] | shape_row(shape=None) -> dict   # the names | one FRESH row
    require_shape(shape, entry_point, argument="shape") -> str   # the canonical name, or the refusal
    seat_count(shape=None) -> int   # the row's `seats`: the one place a caller learns the seat count
    game_shapes() -> dict   |   game_config(shape=None) -> dict   # {name: row} | the fifteen keys

`shape_row` rebuilds every nested value, so a caller's edit of a returned row cannot reach the
catalogue (`surface.md` §12). `require_shape` returns the canonical name and never invents one: `None` is
the **default** — absence, not a defaulted name — and a value the catalogue does not carry is refused by
`UnknownShape`, naming it and the declared names (`errors.md` §2, `shapes.md` §3, D-13) — so
`new_hand(seed, "no-limit-50")` is a refusal, never a 20-chip deal (`shapes.md` §5, D-29).

`seat_count(shape)` is the third read: `shape_row(shape)["seats"]`, so `seat_count()` is 2 and
`seat_count("six-seat-no-limit-100")` is 6, and no entry point below this one divides by two. It is what
`readout` sizes its `stacks` by, `payoffs` sizes its mapping by and `play_hand` seats policies by
(`readout.md` §2, `hand.md` §5, `episode.md` §1, `seats.md` §3–§4).

## 2. The three rows, and the state each creates

| Key | `fixed-limit-20` — the default | `no-limit-100` | `six-seat-no-limit-100` |
|---|---|---|---|
| `default`, `seats`, `blinds`, `bet_structure` | `True`, 2, `(1, 2)`, `"fixed-limit"` | `False`, 2, `(1, 2)`, `"no-limit"` | `False`, 6, `(1, 2)`, `"no-limit"` |
| `starting_stack`, `chips_in_play`, `small_bet`, `big_bet`, `raise_cap` | 20, 40, 2, 4, 4 | 100, 200, `None`, `None`, `None` | 100, 600, `None`, `None`, `None` |
| `actions` (index order, §6), `head_width` | `("fold", "check-call", "raise")`, 3 | `("fold", "check-call", "raise-quarter", "raise-half", "raise-all-in", "raise-minimum")`, 6 | the same six in the same index order, 6 |
| `normalisers` (§4) | 20, 40, 20, 4, 4 | 100, 200, 100, 100, 50 | 100, **600**, 100, 100, 50 |
| `history` — the block's capacity (§2.1) | 24 | 66 | **98** |

The third row is D-33's shape: the two-seat uncapped row's stack, blinds and divisors over six seats, so
the seat count adds no descriptor and no key and only the pot's divisor and the history capacity are the
total's (`seats.md` §2, `shapes.md` §8, D-33).

`create_state(row)` picks the class from `bet_structure`, and the default row's call is the one this
module has always made, so its deals are unchanged card for card (`shapes.md` §5). Both arguments that a
seat count moves are built from the row: its `seats` as `player_count`, and `blind_vector(row)` —
`tuple(row["blinds"]) + (0,) * (row["seats"] - 2)` — as the blinds (`hand.md` §3):

    "fixed-limit" -> FixedLimitTexasHoldem.create_state(AUTOMATIONS, True, 0, blinds, 2, 4, 20, 2)
    "no-limit"    -> NoLimitTexasHoldem.create_state(AUTOMATIONS, True, 0, blinds, min_bet, 100, 2)
    # six seats:   NoLimitTexasHoldem.create_state(AUTOMATIONS, True, 0, (1, 2, 0, 0, 0, 0), 2, 100, 6)
    # (automations, ante_trimming, antes, blinds, the bets — or min_bet = the big blind of 2 —, stacks, players)

### 2.1 `history` is the catalogue row's, and never `game_config`'s

The capacity of the history block is the shape's own, derived from its own betting rather than from the
fixed-limit cap: `no-limit-100` gives 200 ÷ 4 = 50 raises plus 4 × 2 × 2 = 16 = **66**,
`six-seat-no-limit-100` gives 600 ÷ 12 = 50 plus 4 × 6 × 2 = 48 = **98**, and `fixed-limit-20` keeps
**24**, its cap's own bound (`shapes.md` §8, ASM-42). The key is a **row's** and not `game_config`'s: the
fifteen keys below are a contract and carry no capacity, so a caller that wants it reads
`game_shapes()[name]["history"]` (`shapes.md` §2, ASM-44). This module declares the number and enforces
nothing: the block's width and its refusal are `features`' (`docs/L3/features`, D-13).

## 3. `game_config`'s fifteen keys

In this order, in every shape: `game`, `seats`, `player_count`, `button_seat`, `blinds`, `small_blind`,
`big_blind`, `blind_levels`, `starting_stack`, `starting_stacks`, `small_bet`, `big_bet`, `limit`,
`raise_cap`, `streets` — `player_count` being the row's `seats`, `starting_stacks` the tuple that row's
seat count makes, and `limit` its `(small_bet, big_bet)` (or `None` where it declares no fixed bet).
With **no argument** it returns, byte for byte, today's mapping — 20 chips, blinds 1 and 2, one blind
level, bets 2 and 4, cap 4, four streets (`surface.md` §3, ASM-6); `no-limit-100` returns the same keys
and value shapes with its own values — `game` `"no-limit texas hold'em"`, stacks 100, `None` for
`small_bet`, `big_bet`, `limit` and `raise_cap` (`surface.md` §3, D-29).

`six-seat-no-limit-100` returns the same fifteen keys again: `game` `"six-seat no-limit texas hold'em"`,
`seats` and `player_count` 6, `starting_stack` 100 with `starting_stacks` a six-tuple of 100, `blinds`
`(1, 2)`, and `None` for `small_bet`, `big_bet`, `limit` and `raise_cap` (`seats.md` §2, ASM-44). Measured:
all three mappings carry fifteen keys, the same fifteen, and none carries `history`.

## 4. Chips in play, and the divisors

`pot + sum(stacks)` is the row's `chips_in_play` at every decision — 40 in the default shape, 200 in the
two-seat no-cap one and 600 on the six-seat one, which is 6 × 100 — since committed chips sit in `pot`,
never in a stack (`environment.md` §1, ASM-6, `seats.md` §2).

| Normaliser | `fixed-limit-20` | `no-limit-100` | `six-seat-no-limit-100` | What it divides |
|---|---|---|---|---|
| `stack` | 20 | 100 | 100 | a starting stack, the largest `stacks` entry |
| `pot` | 40 | 200 | 600 | the chips in play, the largest `pot` |
| `to_call` | 20 | 100 | 100 | the largest call a seat can face |
| `amount` | 4 | 100 | 100 | the largest raise-to on the shape's own terms: a big bet, or a stack |
| `count` | 4 | 50 | 50 | the most bet-or-raise actions a street holds: the cap, or 100 ÷ 2 |

A divisor does not travel between rows: 40 on a 200-chip game returns two for a pot that filled the
stacks, so the fixed shape's pot divisor here is a **clip**, not a normalisation (`sizing.md` §5, D-25) —
and for the same reason the six-seat row's pot divides by the 600 in play, because a divisor of 200 on a
six-seat pot is a clip of exactly the same kind (`seats.md` §2). This module declares the five numbers and
applies none.

## 5. The four raise bands

`m` is the **minimum legal raise-to** and `A` the **largest**, the all-in raise-to, both from
`pokerkit`'s own completion amounts, with `L = A − m`. The bands partition the legal integer interval
`[m, A]`, each resolving to its own band's maximum (`sizing.md` §2):

| Descriptor | The amounts it owns | Resolves to | Legal iff |
|---|---|---|---|
| `raise-minimum` | `{m}` | `m` | a raise is legal at all |
| `raise-quarter` | `(m, m + L//4]` | `m + L//4` | `L//4 >= 1` |
| `raise-half` | `(m + L//4, m + L//2]` | `m + L//2` | `L//2 > L//4` |
| `raise-all-in` | `(m + L//2, A]` | `A` | `A > m + L//2` |

Disjoint and total, so every legal amount belongs to exactly one band; an empty band is **masked out,
never collapsed onto its neighbour** — at `L = 0` only `raise-minimum` is legal, at `L = 1` only it and
`raise-all-in` (`sizing.md` §2). The fixed row declares no band: its `raise` is the minimum completion.
The bands are a property of the interval, not of the seat count, so the six-seat row's are the two-seat
row's (`actions.md` §2).

## 6. The index order, and the no-cap facts

`fold` 0, `check-call` 1, `raise-quarter` 2, `raise-half` 3, `raise-all-in` 4, `raise-minimum` 5 — the
row's `actions` tuple read as an index order, the bases first in every shape. It is the **measured price
order, worst first** (`sizing.md` §3, D-29): a tie-break toward the smallest index resolves toward a
worse-priced band, so no tie manufactures a PASS; the order is **not monotone in amount**, so no index
reads as a size; and a verdict resting on the tie is recomputable without those decisions, the legal
subset keeping this order (`stepping.md` §1).

Measured: `NoLimitPokerMixin.max_completion_betting_or_raising_count` is `None`, `FixedLimitPokerMixin`'s
`4` — the cap is the library's per-class property, so a no-cap row bounds the count by its own stack.
Under `NO_LIMIT` `state.max_completion_betting_or_raising_to_amount` is `stacks[actor] + bets[actor]`,
under `FIXED_LIMIT` the minimum completion — so the fixed row's interval has `minimum == maximum` and
`L = 0`. At `no-limit-100`'s first decision: `pot` 3, `stacks` `(99, 98)`, `to_call` 1, `limit` `(2, 0)`,
`m` 4, `A` 100, `L` 96 — quarter 28, half 52, all-in 100; 8 decisions always-check-or-call, 2 all-in.
At `six-seat-no-limit-100`'s first decision the same amounts hold — `pot` 3, `to_call` 2, `limit`
`(2, 0)`, `m` 4, `A` 100, `L` 96, quarter 28, half 52, all-in 100 — because the blind level and the
stack are the same and only the number of stacks is not (`hand.md` §4, `seats.md` §2).
