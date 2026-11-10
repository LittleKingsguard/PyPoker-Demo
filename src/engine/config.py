"""The declared game shapes, and `game_config` / `game_shapes` (docs/L3/engine/config.md).

The game is not one declaration for the whole project any more: `game_shapes()`
publishes the declared shapes **default first**, and the default's row is the fixed
game of ASM-6 — two seats, blinds 1 and 2, one blind level that never rises, starting
stacks of 20 chips, a small bet of 2, a big bet of 4 and a raise cap of 4 on a street
(docs/L2/engine/surface.md §3, ASM-6, D-29).

Nothing here is per-call state: every entry point of this module builds its mapping
fresh, so two calls are equal and a caller's edit of one cannot reach the next
(surface.md §3). A shape name outside the catalogue is refused naming it and the
declared names, and is never defaulted (D-13, D-29).
"""

from __future__ import annotations

from .errors import UnknownShape

# The four streets, in `pokerkit`'s `state.street_index` order (readout.md §2).  The
# street fact is `STREETS[state.street_index]`, never `streets.index(state.street)`:
# the turn and river `Street` values are equal by value (platform.md §3).
STREETS = ("preflop", "flop", "turn", "river")

# The default shape's own numbers, kept as names because `readout` reads the seat
# count and every caller reads the streets (readout.md §2).
SEAT_COUNT = 2
BUTTON_SEAT = 0
STARTING_STACK = 20
SMALL_BLIND = 1
BIG_BLIND = 2
SMALL_BET = 2
BIG_BET = 4
RAISE_CAP = 4
BLIND_LEVELS = 1

#: The first row of the catalogue, and what an absent shape reads as (shapes.md §3, D-29).
DEFAULT_SHAPE = "fixed-limit-20"

#: The declared shapes, in the catalogue's own order — default first (shapes.md §2).
#: A row is data: the seats, blinds, stack, chips in play, bet structure, bet sizes and
#: cap, the vocabulary in the shape's index order, the head width and the amount
#: normalisers of one game (shapes.md §2, sizing.md §3, §5, §6).
_SHAPE_ROWS = (
    {
        "name": "fixed-limit-20",
        "default": True,
        "seats": 2,
        "blinds": (1, 2),
        "starting_stack": 20,
        "chips_in_play": 40,
        "bet_structure": "fixed-limit",
        "small_bet": 2,
        "big_bet": 4,
        "raise_cap": 4,
        "actions": ("fold", "check-call", "raise"),
        "head_width": 3,
        "normalisers": {
            "stack": 20,
            "pot": 40,
            "to_call": 20,
            "amount": 4,
            "count": 4,
        },
    },
    {
        "name": "no-limit-100",
        "default": False,
        "seats": 2,
        "blinds": (1, 2),
        "starting_stack": 100,
        "chips_in_play": 200,
        "bet_structure": "no-limit",
        "small_bet": None,
        "big_bet": None,
        "raise_cap": None,
        "actions": (
            "fold",
            "check-call",
            "raise-quarter",
            "raise-half",
            "raise-all-in",
            "raise-minimum",
        ),
        "head_width": 6,
        "normalisers": {
            "stack": 100,
            "pot": 200,
            "to_call": 100,
            "amount": 100,
            "count": 50,
        },
    },
)

#: Each row's `game` name, which is the word `game_config` reports for it.
_GAME_OF = {
    "fixed-limit-20": "fixed-limit texas hold'em",
    "no-limit-100": "no-limit texas hold'em",
}


def shape_names() -> tuple[str, ...]:
    """Every declared shape name, in the catalogue's order — default first (shapes.md §2)."""
    return tuple(row["name"] for row in _SHAPE_ROWS)


def require_shape(shape, entry_point: str, argument: str = "shape") -> str:
    """The shape name `shape` denotes, or the refusal naming it and the declared names.

    `None` is the **default** shape and is not a defaulting of a name: absence and a
    name the catalogue does not carry are different facts, and only the first is legal
    (shapes.md §3, D-13).  A name outside the catalogue is refused, never substituted.
    """
    if shape is None:
        return DEFAULT_SHAPE
    for row in _SHAPE_ROWS:
        if isinstance(shape, str) and shape == row["name"]:
            return row["name"]
    raise UnknownShape(
        "%s(%s): %r is not one of the declared shapes %r, and a shape name is never "
        "defaulted (shapes.md §2, D-29)" % (entry_point, argument, shape, shape_names())
    )


def shape_row(shape=None) -> dict:
    """One declared row, as a fresh mapping (shapes.md §2).

    The nested values are rebuilt on every call, so a caller's edit of a returned row
    cannot reach the catalogue (surface.md §3).
    """
    name = require_shape(shape, "shape_row")
    for row in _SHAPE_ROWS:
        if row["name"] == name:
            return {
                "name": row["name"],
                "default": row["default"],
                "seats": row["seats"],
                "blinds": tuple(row["blinds"]),
                "starting_stack": row["starting_stack"],
                "chips_in_play": row["chips_in_play"],
                "bet_structure": row["bet_structure"],
                "small_bet": row["small_bet"],
                "big_bet": row["big_bet"],
                "raise_cap": row["raise_cap"],
                "actions": tuple(row["actions"]),
                "head_width": row["head_width"],
                "normalisers": dict(row["normalisers"]),
            }
    raise AssertionError("the catalogue carries no row for %r" % (name,))


def game_shapes() -> dict:
    """The declared shapes as an ordered mapping, default first (surface.md §12).

    The instance set is the declaration itself, so no caller can invent a shape here:
    the row is `fixed` (e2e-surface.md §5, shapes.md §2).
    """
    return {row["name"]: shape_row(row["name"]) for row in _SHAPE_ROWS}


def game_config(shape=None) -> dict:
    """The named shape's parameters as one mapping (surface.md §3).

    Called with no argument it returns the **default** shape's row, which is the mapping
    this entry point has always returned, byte for byte (ASM-6, shapes.md §2).  A named
    shape returns the same fifteen keys with the same value shapes, differing only in the
    values that shape declares: the no-cap shape has no fixed bet and no cap, so its
    `small_bet`, `big_bet`, `limit` and `raise_cap` are `None` (shapes.md §2, D-29).
    """
    name = require_shape(shape, "game_config")
    row = shape_row(name)
    return {
        "game": _GAME_OF[row["name"]],
        "seats": row["seats"],
        "player_count": row["seats"],
        "button_seat": BUTTON_SEAT,
        "blinds": tuple(row["blinds"]),
        "small_blind": row["blinds"][0],
        "big_blind": row["blinds"][1],
        "blind_levels": BLIND_LEVELS,
        "starting_stack": row["starting_stack"],
        "starting_stacks": tuple([row["starting_stack"]] * row["seats"]),
        "small_bet": row["small_bet"],
        "big_bet": row["big_bet"],
        "limit": (
            None
            if row["small_bet"] is None or row["big_bet"] is None
            else (row["small_bet"], row["big_bet"])
        ),
        "raise_cap": row["raise_cap"],
        "streets": STREETS,
    }
