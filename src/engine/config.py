"""The fixed game's constants and `game_config` (docs/L3/engine/layout.md §1).

The game is one declaration for the whole project: two seats, blinds 1 and 2, one
blind level that never rises, starting stacks of 20 chips, a small bet of 2, a big
bet of 4 and a raise cap of 4 on a street (docs/L2/engine/surface.md §3, ASM-6, D-2).
Nothing here is per-call state: `game_config` builds its mapping fresh, so two calls
are equal and a caller's edit of one cannot reach the next (surface.md §3).
"""

from __future__ import annotations

# The four streets, in `pokerkit`'s `state.street_index` order (readout.md §2).  The
# street fact is `STREETS[state.street_index]`, never `streets.index(state.street)`:
# the turn and river `Street` values are equal by value (platform.md §3).
STREETS = ("preflop", "flop", "turn", "river")

SEAT_COUNT = 2
BUTTON_SEAT = 0
STARTING_STACK = 20
SMALL_BLIND = 1
BIG_BLIND = 2
SMALL_BET = 2
BIG_BET = 4
RAISE_CAP = 4
BLIND_LEVELS = 1


def game_config() -> dict:
    """The fixed game as one mapping, stated in numbers (surface.md §3).

    Refuses nothing, takes no argument, and carries no seed, hand or rung, so the
    ladder has one game object for its whole length (D-2, D-3).
    """
    return {
        "game": "fixed-limit texas hold'em",
        "seats": SEAT_COUNT,
        "player_count": SEAT_COUNT,
        "button_seat": BUTTON_SEAT,
        "blinds": (SMALL_BLIND, BIG_BLIND),
        "small_blind": SMALL_BLIND,
        "big_blind": BIG_BLIND,
        "blind_levels": BLIND_LEVELS,
        "starting_stack": STARTING_STACK,
        "starting_stacks": (STARTING_STACK, STARTING_STACK),
        "small_bet": SMALL_BET,
        "big_bet": BIG_BET,
        "limit": (SMALL_BET, BIG_BET),
        "raise_cap": RAISE_CAP,
        "streets": STREETS,
    }
