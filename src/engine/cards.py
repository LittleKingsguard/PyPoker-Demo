"""The one spelling of a card (docs/L3/engine/readout.md §3).

A card is a two-character plain `str` — rank first from `RANKS`, suit second from
`SUITS`, as in `"As"`, `"Td"`, `"2c"`, `"Kh"` — and no `pokerkit` object ever leaves
this module (guardrails.md G3, e2e-surface.md §2).  `repr(Card)` is that spelling;
`str(Card)` is not (`str(Card)` prints `TWO OF CLUBS (2c)`).
"""

from __future__ import annotations

from pokerkit.utilities import Card

RANKS = "23456789TJQKA"
SUITS = "cdhs"


def card_spelling(card) -> str:
    """The two-character spelling of a `pokerkit` card (readout.md §3)."""
    return repr(card)


def parse_card(spelling: str) -> Card:
    """The card a two-character spelling names; the inverse of `card_spelling`."""
    return Card(spelling[0], spelling[1])


def is_card_spelling(value) -> bool:
    """Whether `value` is one card of the declared spelling (readout.md §3)."""
    return (
        isinstance(value, str)
        and len(value) == 2
        and value[0] in RANKS
        and value[1] in SUITS
    )
