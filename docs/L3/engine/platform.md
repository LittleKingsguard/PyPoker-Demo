# engine — the `pokerkit` facts this design measured

- **Owner:** the platform facts a design decision of this module rests on, measured against `pokerkit` 0.7.7 in this venv, and the three places where the received fact sheet was wrong
- **Ceiling:** 60 lines. At the ceiling, split by owner — never append
- **Status:** these are measurements, not design. Anything here that contradicts an inherited claim is a correction this module had to make, and is reported upward as such

## 1. Confirmed as stated

Created exactly as `hand.md` §2 says (`AUTOMATIONS`, `ante_trimming_status=True`, `raw_antes=0`,
`raw_blinds_or_straddles=(1, 2)`, `small_bet=2`, `big_bet=4`, `raw_starting_stacks=20`,
`player_count=2`), the first decision reads, in **`pokerkit` index order**:

    status        True          actor_index   1            total_pot_amount   3
    stacks        [18, 19]      bets          [2, 1]       checking_or_calling_amount  1
    street_index  0             board_cards   []           hole_cards          2 cards each
    can_fold      True          can_check_or_call True     can_complete_bet_or_raise_to True

So engine seat 0 (pokerkit player 1) posts 1, has 19 behind and acts first; seat 1 (player 0) posts 2,
has 18 behind, and acts first on the flop, turn and river — the seat map of `hand.md` §3 is confirmed
in both directions, as is `pot + sum(stacks) == 40` at every decision and `{0: -1, 1: 1}` for a
first-decision fold. `complete_bet_or_raise_to()` with no argument resolves to the minimum completion
(4 at the first decision of a 2/4 game with blinds 1/2), `can_complete_bet_or_raise_to()` turns False
at the fourth bet on a street, and `can_fold()` is False exactly when the actor’s bet already equals
the maximum bet. `repr(Card)` spells `2c 2d 2h 2s 3c 3d` for `Deck.STANDARD[:6]`. Lengths of a played
hand: 8 applied actions under always-check-or-call, 12 under always-raise-if-legal — both far under
the 200-decision bound.

## 2. Corrected — `state.board_cards` is not the board

`board_cards` is one row **per dealing operation**, not one row per board: after the flop it reads
`[['7h'], ['5d'], ['Jc']]`, and only `state.get_board_cards(0)` yields the three-card board
(`state.py:1660-1703`). An implementation that reads `board_cards[0]` reports a one-card board on the
flop and fails `L2 environment.md` §2’s "0, 3, 4 or 5 public cards" outright. `readout.md` §2 is
fixed accordingly.

## 3. Corrected — `streets.index(state.street)` cannot tell the turn from the river

The turn and the river `Street` values are **equal by value** (same flags, same board count, same
`big_bet`, same cap), so `.index()` returns `2` on the river as well and `STREETS[2]` names every river
decision "turn" — with a five-card board. The street is `STREETS[state.street_index]`
(`state.py:1129`, set at `_begin_dealing`, `state.py:3552-3555`). `readout.md` §2 is fixed accordingly.

## 4. Corrected — advancing a hand *does* draw from the global stream

`_begin_dealing` (`state.py:3546-3593`) evaluates `get_dealable_cards(None, False)` on every street
transition, and that path runs `shuffled(self.reserved_cards)` merely to obtain a length
(`state.py:2406-2411`). So a played hand consumes a handful of draws of Python’s global `random` —
measured 1 to 3 draws per hand, at the turn-to-river transitions, growing with the number of burned
and mucked cards. The **deal is unaffected** (the board comes from `deck_cards` in order, which was
fixed at creation, so injecting `random.random()` between steps leaves holes, board and payoffs
identical), but the statement "advanced later, the hand draws no randomness" is false as measured.
Consequence for this module: the advance is wrapped in the same save/seed/restore as `equity`, so that
`apply_action` still hands the caller’s stream back untouched as `L2 surface.md` §1, §7 require
(`advance.md` §1, `stream.md` §1).

## 5. Confirmed — `calculate_equities`

Repeats bit-exactly under a fixed seed, stays inside [0, 1], counts ties as their share, accepts an
empty board, and draws from the global `random` (`analysis.py:22,163,328`) with no generator argument,
which is what forces `equity`’s save/seed/restore (`stream.md` §1).
