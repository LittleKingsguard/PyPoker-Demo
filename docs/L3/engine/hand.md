# engine — the hand

- **Owner:** the hand’s data structure and its wrapper over a `pokerkit` state: the handle, `new_hand` (the project’s single seeding point), the **seat mapping**, and the two entry points that are a pure function of a finished or running hand (`is_terminal`, `payoffs`)
- **Ceiling:** 178 lines — raised from 118 for the third seat count: the general seat map and the three derived sources it rests on, the six-seat instance's table, the six-seat first-decision check beside the two existing ones, and `payoffs` as one entry per seat. At the ceiling, split by owner — never append

## 1. The value

    class Hand:                    # src/engine/hand.py — NOT surface
        _state: pokerkit.state.State
        _history: tuple[str, ...]  # one entry per applied action, oldest first (history.md §1)
        _shape: str                # the canonical name of the shape it was dealt from (config.md §1)

A `Hand` is an **opaque handle**: no public attribute, no mapping access, no iterator, no `__eq__`
(identity equality only), and a constant `__repr__` such as `<engine.Hand>`. A caller only ever
passes it back; nothing in it is surface (`e2e-surface.md` §1).

The module keeps **no state of its own**: the whole state of a hand lives in its handle, so two
handles are independent and a hand dealt earlier is unaffected by a hand dealt later (`L2
environment.md` §1, ASM-2). No module-level cache, no "current hand", no registry.

Internally a `Hand` is exactly three things — the state, the public history and the shape’s name — and
everything a readout needs is derived from the state on demand: a cache would be a second source of
truth that a `deepcopy` could desynchronise.

The **shape lives in the handle** and nowhere else: `readout`, `legal_actions`, `apply_action` and
`advance` need its vocabulary or its bet structure, and none of them may take a shape beside a hand,
because a second argument could name a different game from the deal that was made (`surface.md` §1,
`shapes.md` §3). The third field is that canonical name, and a step copies it forward (`advance.md` §1).

The third field is also what fixes the hand’s **seat count**, because the count is shape data: it is
that row’s `seats`, read through `seat_count(hand._shape)`, so one handle names its game, its
vocabulary and how many entries its `stacks`, its `payoffs` and its seating have (`seats.md` §2–§4,
ASM-44). Nothing below this module divides by two, and no entry point takes a seat count beside a hand
(`config.md` §1, `shapes.md` §2).

## 2. `new_hand(seed, shape=None)`

    def new_hand(seed: int, shape=None) -> Hand

    validate_seed(seed)                      # not an int, or a bool — errors.md, InvalidSeed
    name = require_shape(shape, "new_hand")  # a name outside the catalogue — config.md §1, UnknownShape
    row = shape_row(name)                    # the row is read BEFORE the seed (guardrails.md G14)
    random.seed(seed)                       # THE single seeding point of the project (ASM-2)
    return Hand(create_state(row), (), name)

Both refusals happen **before** `random.seed`, so a refused call cannot move the stream and neither
depends on the other. `create_state(row)` picks the library class from the row’s `bet_structure`
(`config.md` §2), hands it the row’s seat count as `player_count` and the row’s `blind_vector` as
`raw_blinds_or_straddles`, and builds both arguments from the row alone:

    blind_vector(row) = tuple(row["blinds"]) + (0,) * (row["seats"] - 2)   # §3

    "fixed-limit" -> FixedLimitTexasHoldem.create_state(
                         AUTOMATIONS, True, 0, blind_vector(row),
                         row["small_bet"], row["big_bet"], row["starting_stack"], row["seats"])
    "no-limit"    -> NoLimitTexasHoldem.create_state(
                         AUTOMATIONS, True, 0, blind_vector(row),
                         row["blinds"][1], row["starting_stack"], row["seats"])

For a two-seat row `blind_vector` is `(1, 2)` with no padding, which is the argument this module has
always handed `pokerkit`, so the fixed row’s call and the two-seat no-cap row’s call are the ones they
always were (`shapes.md` §5). A six-seat row hands the library six entries of which two are non-zero,
which is what seats six players rather than two (`seats.md` §2).

Why this is enough: `pokerkit` shuffles the deck inside `create_state` (`state.py:1241`,
`shuffle(self.deck_cards)`, `from random import shuffle`), so seeding the global stream immediately
before creation fixes the **whole** deck order, and every later card comes from that order — a step
consumes a few incidental draws (`platform.md` §4) but cannot change the deal, and `advance` hands
them back (`advance.md` §1). The **shape does not move that order**: the seed is set, then the state
its row declares is created, so a default-shape deal is unchanged card for card (`shapes.md` §5, D-29).

`bool` is refused although `bool` is an `int` subclass: a recorded seed is an integer, and `True` as
a seed is a defect a test can see (`protocol.md` §2).

`AUTOMATIONS` is the module’s constant: `ANTE_POSTING, BET_COLLECTION, BLIND_OR_STRADDLE_POSTING,
CARD_BURNING, HOLE_DEALING, BOARD_DEALING, HOLE_CARDS_SHOWING_OR_MUCKING, HAND_KILLING,
CHIPS_PUSHING, CHIPS_PULLING`. It is what makes the *betting decisions* the only manual operations:
hole cards exist from the first decision on, and each street’s board cards are dealt automatically as
the previous street’s betting closes (`strata/platform.md`).

## 3. The seat map — the single most dangerous detail

The map is no longer heads-up’s own: it is the seat count’s, derived from `pokerkit` 0.7.7’s own
arithmetic (`.venv/lib/python3.12/site-packages/pokerkit/state.py`) and not from a table of two.

- `get_effective_blind_or_straddle` (`state.py:3325-3345`) reads `abs(self.blinds_or_straddles[not
  player_index])` **only** when `player_count == 2`, and `abs(self.blinds_or_straddles[player_index])`
  otherwise. For more than two players the vector is therefore one blind per player index, and the
  pair `(1, 2)` padded with zeros gives player 0 the small blind 1 and player 1 the big blind 2 —
  engine seats 1 and 2 under the map below (`seats.md` §2).
- `_begin_betting` (`state.py:4190-4212`) sets `max_bet_index` to the player maximising
  `(self.bets[i] * sign(blinds_or_straddles[i]), i)` — with the vector reversed first when
  `player_count == 2` (`state.py:4203-4204`) — and then `opener_index = (max_bet_index + 1) %
  player_count`.
- `collect_bets` zeroes every bet when a street’s bets are collected (`state.py:3266-3267`), and the
  next street opens after that collection (`_end_dealing` → `_begin_betting`, `state.py:3621-3627`).
- So on every street after the pre-flop every `bets[i]` is 0, the key reduces to `(0, i)`, the maximum
  is the **last** player index, and the opener is player 0 — for **every** player count.

The seat that acts **last** post-flop is the button, and it is player `player_count - 1`. Engine seat 0
holds the button on every shape (`L2 environment.md` §1), so engine seat `s` is player
`(s - 1) mod seats`:

    SEAT_TO_PLAYER = (1, 0)                  # the two-seat instance, = seat_map(2)
    seat_map(seats)          = ((s - 1) % seats for s in range(seats))
    player_index(seat, seats) = (seat - 1) % seats        # helpers, not surface
    seat_of(index, seats)     = (index + 1) % seats

Measured on the six-seat row (blinds `(1, 2, 0, 0, 0, 0)`, stacks 100, minimum bet 2): `actor_index`
is 2 at the first decision, the pre-flop order of acting players is `[2, 3, 4, 5, 0, 1]`, and the flop,
turn and river order is `[0, 1, 2, 3, 4, 5]` — `seat_map(6)` is therefore `(5, 0, 1, 2, 3, 4)`:

| Engine seat | `pokerkit` player | Posts | Acts |
|---|---|---|---|
| 0 | 5 | — | last post-flop, fourth of six pre-flop — **the button** |
| 1 | 0 | 1 | first post-flop, fifth pre-flop — the small blind |
| 2 | 1 | 2 | last pre-flop — the big blind |
| 3 | 2 | — | first pre-flop, second post-flop — under the gun |
| 4 | 3 | — | second pre-flop — the hijack |
| 5 | 4 | — | third pre-flop — the cutoff |

The **two-seat instance** is that same formula at `seats = 2`, which is the map this module already
had: `seat_map(2) = (1, 0)`, `player_index(seat) = 1 - seat`, `seat_of(index) = 1 - index`, and
`blind_vector` is `(1, 2)` with no padding. The library then reverses the pair itself
(`state.py:3336-3339`, `:4203-4204`), so player 1 posts the 1, player 0 posts the 2 and acts first on
the flop, turn and river — and **the two-seat deal is unchanged, card for card**, because the same
seed creates the same state with the same arguments (`shapes.md` §5, `seats.md` §3).

**Every** per-seat fact is translated exactly once, where it is read: `stacks`, `payoffs`, `hole`, the
readout’s `seat` fact, the acting seat of a decision, the seat a history entry names, and the policy
`play_hand` calls. No `pokerkit` index ever reaches a caller. Do not "simplify" this by passing
`(2, 1)` to `create_state`: the library reverses an already-reversed pair again and the button lands
back on the wrong seat (`guardrails.md` G2).

## 4. The first decision, as a check on the whole mapping

At any seed the **default shape’s** first decision must read: `street == "preflop"`, `pot == 3`,
`stacks == (19, 18)`, `to_call == 1`, `seat == (0, True)`, `len(hole) == 2`, `board == ()`,
`history == []`. If a build reads `stacks == (18, 19)` or `seat == (1, False)`, the seat map is
inverted and nothing else in the module can be trusted (`readout.md` §2).

The **two-seat no-cap row’s** own first decision carries the same seating and its own numbers:
`pot == 3`, `stacks == (99, 98)`, `to_call == 1`, `seat == (0, True)`, `limit == (2, 0)`, `board == ()`
— differing only where the row differs (`config.md` §6, `shapes.md` §2).

The **six-seat row’s** first decision is the check on the general map, and it is the same at every
seed because the blinds are posted before the deal matters: `street == "preflop"`, `pot == 3`,
`stacks == (100, 99, 98, 100, 100, 100)` in seat order, `to_call == 2`, `seat == (3, False)`,
`limit == (2, 0)`, `board == ()`, `history == []`, `hand_class is None` — the small blind of 1 sits in
seat 1’s stack and the big blind of 2 in seat 2’s, and the first seat to act is under the gun, not the
button (`seats.md` §2–§3, ASM-44).

Conservation, asserted at every decision: `pot + sum(stacks)` is the row’s chips in play — 40 in the
default shape, 200 in the two-seat no-cap one and 600 on the six-seat one (6 × 100) — because
committed chips sit in the pot and never in a stack (`L2 environment.md` §1, `config.md` §4), and
`state.total_pot_amount` includes the current street’s outstanding bets (`state.py:2601-2606`).
Measured through a whole six-seat hand of 24 decisions: no violation.

## 5. `is_terminal` and `payoffs`

    def is_terminal(hand: Hand) -> bool          # bool(), never a truthy object
    def payoffs(hand: Hand) -> dict[int, int]    # one entry per seat — engine seat order

`is_terminal` is `bool(not state.status)` and refuses only a value that is not a `Hand`: every handle
states whether it is over, a freshly dealt one included (`L2 surface.md` §8). The e2e edge asserts
`assertIsInstance(..., bool)`.

`payoffs` refuses a handle that is still running (`L2 surface.md` §9) and maps
`{seat: state.payoffs[player_index(seat, seats)]}` over the hand’s **own** seat count — the net chip
delta `stack - starting_stack` (`state.py:1095-1103`) — so it holds exactly one number per seat of the
shape it was dealt from, six on `six-seat-no-limit-100` and two elsewhere, summing to zero, keyed by
seat and carrying no total (`seats.md` §3, `e2e-surface.md` §3.1). A split is a zero payoff and is
legal (ASM-12). Measured: `{0: -2, 1: -2, 2: -2, 3: 10, 4: -2, 5: -2}` for one six-seat
always-check-call hand, six entries summing to zero.
