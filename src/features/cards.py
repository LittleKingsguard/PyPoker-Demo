"""ASM-E1's card spelling, read once for both encodings (flat-numeric.md §3).

A card is a two-character plain `str`: a rank first from `"23456789TJQKA"`, a suit
second from `"cdhs"`.  This module **parses** that spelling; it never imports the
library that produced it, and one reading of it gives both the dense card slot and
the token id (README.md §4, layout.md §3, guardrails.md G12).
"""

from __future__ import annotations

from .errors import InvalidReadout

RANKS = "23456789TJQKA"
SUITS = "cdhs"

# One dense card slot: a 13-wide rank one-hot, then a 4-wide suit one-hot
# (flat-numeric.md §3).  Derived from the two alphabets, never written down twice.
RANK_WIDTH = len(RANKS)
CARD_SLOT = RANK_WIDTH + len(SUITS)


def parse_card(card, field):
    """The ``(rank index, suit index)`` of one card, or the refusal (flat-numeric.md §3).

    The refusal names the block that held the card and the card itself, because a
    misspelt card is the one value a readout can carry that has no spelling at all
    (errors.md §3).
    """
    if (
        isinstance(card, str)
        and len(card) == 2
        and card[0] in RANKS
        and card[1] in SUITS
    ):
        return RANKS.index(card[0]), SUITS.index(card[1])
    raise InvalidReadout(
        "encode(readout): %r must hold cards, and %r is not one: a rank from %r then a "
        "suit from %r" % (field, card, RANKS, SUITS)
    )


def card_slot(card, field):
    """The 17 values one dealt card sets inside one dense card slot."""
    rank_index, suit_index = parse_card(card, field)
    values = [0.0] * CARD_SLOT
    values[rank_index] = 1.0
    values[RANK_WIDTH + suit_index] = 1.0
    return values


def card_id(card, field):
    """The card's token id: ``1 + 4 * rank index + suit index``, so ``"2c"`` is 1."""
    rank_index, suit_index = parse_card(card, field)
    return 1 + len(SUITS) * rank_index + suit_index
