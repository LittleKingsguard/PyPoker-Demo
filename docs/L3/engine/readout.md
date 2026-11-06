# engine — the ten facts

- **Owner:** `readout(hand)` — the information set of D-3: each fact’s derivation, its type, the one card spelling, and what the readout may never expose
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append

## 1. `readout(hand)`

    def readout(hand: Hand) -> dict[str, object]

It refuses a handle that is not a `Hand` and a hand that is over — a hand with no acting seat has no
readout, and there is no "who would act next" to invent (`L2 surface.md` §5). It draws no
randomness, mutates nothing, and returns a **fresh** mapping each call whose lists are copies, so a
caller cannot reach back into the handle through what it was handed.

The acting seat is `seat_of(state.actor_index)` (`hand.md` §3). Both the seat and the hand’s street
come from the state; the module keeps no notion of "whose turn" of its own.

## 2. The ten keys — exactly these, and how each is derived

The mapping has these ten keys and no others (`e2e-surface.md` §2, `L2 environment.md` §2). "Seat
order" below always means engine seat order, `0` = button (`hand.md` §3).

| Key | Type | Derivation |
|---|---|---|
| `street` | `str` | `STREETS[state.street_index]` where `STREETS = ("preflop", "flop", "turn", "river")`. **Not** `streets.index(state.street)`: the turn and river `Street` values are equal by value, so `.index()` answers 2 on the river too and the river would never be named (`platform.md` §3) |
| `seat` | `tuple[int, bool]` | `(seat, seat == 0)` — the acting seat’s index **first**, then whether it holds the button. The button is always seat 0 in this game, so the flag is `seat == 0`; it is carried as a fact, not implied, because `records.md` §5 and the encoder read it |
| `hole` | `tuple[str, str]` | the acting seat’s two cards, `tuple(card_spelling(c) for c in state.hole_cards[player_index(seat)])`, in `pokerkit`’s own order |
| `board` | `tuple[str, ...]` | `tuple(card_spelling(c) for c in state.get_board_cards(0))`, length 0, 3, 4 or 5. **Not** `state.board_cards[0]`: `board_cards` is one row per *dealing operation*, so its row 0 is a single card on the flop (`platform.md` §2) |
| `stacks` | `tuple[int, int]` | `tuple(state.stacks[player_index(s)] for s in (0, 1))` — chips behind, in seat order |
| `pot` | `int` | `state.total_pot_amount` — **includes** the current street’s outstanding bets (`state.py:2601-2606`), so `pot + sum(stacks) == 40` at every decision |
| `to_call` | `int` | `state.checking_or_calling_amount` — 0 when the actor may check, else `min(actor_stack, max_bets - actor_bet)`, so it is never more than the actor’s stack and a call for less is bounded |
| `limit` | `tuple[int, int]` | `(state.street.min_completion_betting_or_raising_amount, state.completion_betting_or_raising_count)` — the fixed bet size in force (2 on the pre-flop and flop, 4 on the turn and river) and the raises made so far this street |
| `history` | `list[str]` | a **new list** of the handle’s applied actions, oldest first, and the empty list `[]` before the first one (`advance.md` §2) |
| `legal` | `tuple[str, ...]` | `legal_actions(hand)` — the same tuple the entry point returns, same value and same order (`stepping.md` §1) |

Two shapes are deliberate and must not be "tidied":

- `history` is a **`list`**, because the empty history is asserted equal to `[]` at the edge
  (FAM-16.2); a tuple would read `()` and fail there.
- `board` is a **tuple** and may be empty; only its length is asserted, never its container.

## 3. The one card spelling

`card_spelling(card)` is `repr(card)`: a two-character string, rank first from
`"23456789TJQKA"`, suit second from `"cdhs"` — `"As"`, `"Td"`, `"2c"`, `"Kh"`. Examples from the
library’s own deck: `Deck.STANDARD[:6]` spells as `2c 2d 2h 2s 3c 3d`.

A card is therefore a plain `str` in `hole`, in `board` and anywhere else a card is written. It
compares by value, hashes, sorts, prints stably, and needs no library to be understood — which is
what `features` needs: `features` may import `engine`’s surface and nothing below it, and it must
**not** import `pokerkit` (`module-map.md` §3, `e2e-surface.md` §2, D-3). A `pokerkit.Card` in a
readout would force every encoder to depend on the engine’s dependency, and would make the spelling
of a card a question each encoder answered for itself — the exact "second spelling of the deal" that
`features/encodings.md` forbids.

The card value never appears as a `pokerkit` object anywhere: the translation is at this one place,
so a record is plain data. (`repr`, not `str`: `str(Card)` prints `TWO OF CLUBS (2c)`.)

## 4. What the readout may never expose (D-3)

The facts are closed. The mapping never carries, in any form:

- the non-acting seat’s hole cards — `hole` is the *acting* seat’s only;
- the undealt deck, its order, or a board card the hand has not revealed — `board` is the cards
  already dealt to board `0` (`get_board_cards(0)`), and nothing else of the deck is read;
- a rung, an encoding, a learner, an opponent, a seed or an episode count;
- an eleventh key, since the invariance family compares the key set exactly (`battery.md` §3 FAM-2).

`legal` and `history` are in the set because §2 puts them there; nothing else is added "for
convenience". A `readout`-shaped helper that wants to report the pot odds, the number of outs, or
"whose turn it is next" is a defect: that is an encoding, and encoding is `features`’ work (D-3,
`module-map.md` §3).

## 5. What the battery may assert of the facts

Driving only `new_hand`, `readout` and `legal_actions`: the key set is exactly the ten; the first
decision of any seed reads `street == "preflop"`, `pot == 3`, `sum(stacks) == 37`,
`stacks == (19, 18)`, `to_call == 1`, `seat == (0, True)`, `len(hole) == 2`, `len(board) == 0`,
`history == []`; at every decision `pot + sum(stacks) == 40`; `len(board)` is always one of
0, 3, 4, 5; the spellings in `hole` and `board` are two characters from the two declared alphabets;
`readout(hand)["legal"] == legal_actions(hand)`; `readout` refuses a hand that is over; and two reads
of one hand are equal while a read of the handle before a step is unchanged after it.
