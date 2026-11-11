"""One `encode`, one writer loop, two writer families (encoder.md §5, guardrails.md G1).

Both encodings are written by the loop in `encode`: it reads the encoder's
declaration, zeroes a fresh array of the declared shape and dtype, and calls the
writer each block names for the slice that block occupies.  Nothing in the loop names
an encoding -- the only per-encoding data are the block tables of
`declarations.py` and the writer tags they name -- so a rung-to-rung difference stays
attributable to the representation and to nothing else (D-3, README.md §5 rule 2).

A writer is a pure function of the values its block declares it reads.  It returns
exactly the block's width, refuses a value it cannot represent instead of clamping,
defaulting or substituting, and returns a fresh sequence (encoder.md §5 rule 2).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from numbers import Integral

import numpy

from . import cards, history
from .encoder import require_encoder
from .errors import InvalidReadout

# The one pad of the token encoding: an undealt board slot and a history token past
# the end.  No other block may emit it, and it is not a bucket (card-tokens.md §3).
PAD = 0


# --------------------------------------------------------------------------
# The refusals one block's value can need, each naming the field it read
# (errors.md §3).  A rule lives here once and both encodings reach it.
# --------------------------------------------------------------------------
def _is_count(value):
    """Whether a value is a chip count, a seat index or an action index.

    A `numpy` integer is an `Integral` and is accepted; a `bool` is not a count, and
    the project's house rule refuses it in all three places (errors.md §4).
    """
    return isinstance(value, Integral) and not isinstance(value, bool)


def _is_sequence(value):
    """Whether a value is a sequence of facts, and not the `str` that is also one."""
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))


def _street(value, streets):
    """The street's index in the declared order, or the refusal (flat-numeric.md §6)."""
    # Gated on `str` first: no foreign type's equality protocol reaches the four
    # (flat-numeric.md §6, errors.md §1).
    if isinstance(value, str) and value in streets:
        return streets.index(value)
    raise InvalidReadout(
        "encode(readout): 'street' must be one of %r, got %r" % (streets, value)
    )


def _seat(value, seats):
    """The ``(index, button flag)`` of a seat, or the refusal (flat-numeric.md §6).

    The index is bounded by the **shape's** seat count, which the block's ``params``
    carry, so a six-seat row accepts 0 to 5 and a two-seat row still accepts exactly the
    four values it always did (`seats.md` §3, ASM-44).
    """
    if _is_sequence(value) and len(value) == 2:
        index, flag = value[0], value[1]
        if _is_count(index) and 0 <= index < seats and isinstance(flag, bool):
            return int(index), flag
    raise InvalidReadout(
        "encode(readout): 'seat' must be a seat index in %r and a bool button flag, "
        "got %r" % (tuple(range(seats)), value)
    )


def _cards(value, field, capacity, exact):
    """The cards of a card block, or the refusal (flat-numeric.md §3, §6).

    `hole` is exactly its two cards -- a decision always has two -- and `board` is at
    most its five, with every slot past the deal left zero or pad.  A duplicated card
    is not refused: a slot carries whatever the deal put there (errors.md §4).
    """
    count = len(value) if _is_sequence(value) else None
    if count is not None:
        # `hole` fills its block exactly; `board` may be short, and not yet dealt.
        holds = (count == capacity) if exact else (count <= capacity)
        if holds:
            return value
    if exact:
        raise InvalidReadout(
            "encode(readout): %r must be exactly two cards, got %r" % (field, value)
        )
    seen = value if count is None else count
    raise InvalidReadout(
        "encode(readout): %r must be at most five cards, got %r" % (field, seen)
    )


def _count(value, field):
    """One non-negative integer chip count, or the refusal (errors.md §3, §4)."""
    if _is_count(value) and value >= 0:
        return int(value)
    raise InvalidReadout(
        "encode(readout): %r must be a non-negative integer, got %r" % (field, value)
    )


def _counts(value, field, count=2):
    """``count`` non-negative integer chip counts, or the refusal (errors.md §3, §4).

    ``count`` is the block's width, which is the shape's seat count for both per-seat
    blocks and two for the ``limit`` pair -- so a six-seat row refuses a two-entry
    ``stacks`` and a two-seat row refuses a six-entry one (`seats.md` §3, ASM-44).
    """
    if _is_sequence(value) and len(value) == count:
        counts = tuple(value)
        if all(_is_count(entry) and entry >= 0 for entry in counts):
            return tuple(int(entry) for entry in counts)
    raise InvalidReadout(
        "encode(readout): %r must be %d non-negative integers, got %r"
        % (field, count, value)
    )


def _entries(value, field, capacity):
    """The entries of the history block, or the refusal (flat-numeric.md §5)."""
    count = len(value) if _is_sequence(value) else None
    if count is not None and count <= capacity:
        return value
    seen = value if count is None else count
    raise InvalidReadout(
        "encode(readout): %r must be at most %d entries, got %r" % (field, capacity, seen)
    )


def _bucket(value, ladder):
    """The id one ladder gives a non-negative integer (card-tokens.md §4).

    Every ladder ends with an unbounded bound, so each is total over the non-negative
    integers and no amount is ever unrepresentable: the last bound is the catch-all.
    """
    for bound, ident in ladder[:-1]:
        if value <= bound:
            return ident
    return ladder[-1][1]


# --------------------------------------------------------------------------
# The closed set of block writers the block tables name (encoder.md §4, §5)
# --------------------------------------------------------------------------
def _street_onehot(readout, reads, params):
    """A one-hot over the declared streets (flat-numeric.md §2)."""
    streets = params
    values = [0.0] * len(streets)
    values[_street(readout[reads[0]], streets)] = 1.0
    return values


def _street_id(readout, reads, params):
    """The street's own id: 53 preflop through 56 river (card-tokens.md §3)."""
    streets, base = params
    return [base + _street(readout[reads[0]], streets)]


def _seat_index(readout, reads, params):
    """The acting seat's index and its button flag, or its one-hot over the seats.

    `params` carries the shape row's **declared mode** and its seat count
    (`declarations.py`): `index-flag` writes the index then the button flag -- the pair the
    two-seat rows have always carried, which is the acting seat's one-hot over the two
    seats read in reverse because the declared button seat is seat 0 -- and `one-hot`
    writes one slot per seat with the acting seat's set (`seats.md` §3, flat-numeric.md §4,
    ASM-44).
    """
    mode, seats = params
    index, flag = _seat(readout[reads[0]], seats)
    if mode == "index-flag":
        return [float(index), 1.0 if flag else 0.0]
    values = [0.0] * seats
    values[index] = 1.0
    return values


def _seat_ids(readout, reads, params):
    """The acting seat's own ids: 57 + index then 59 + flag, or 96 + the seat slot.

    `params` carries the shape row's declared mode, its seat count and the three id bases.
    `index-flag` is the two-seat rows' pair, unchanged; `one-hot` writes **one slot per
    seat** holding that seat's own id and the pad everywhere else, over ids 96-101, which
    sit above every id the other rows use, so no existing id is renamed and no two blocks
    of one observation can emit one id (`seats.md` §3, card-tokens.md §3, ASM-44).
    """
    mode, seats, index_base, flag_base, token_base = params
    index, flag = _seat(readout[reads[0]], seats)
    if mode == "index-flag":
        return [index_base + index, flag_base + (1 if flag else 0)]
    values = [PAD] * seats
    values[index] = token_base + index
    return values


def _card_onehot(readout, reads, params):
    """Card slots of 17, an undealt board slot all-zero (flat-numeric.md §3)."""
    capacity, exact = params
    field = reads[0]
    dealt = _cards(readout[field], field, capacity, exact)
    values = []
    for card in dealt:
        values.extend(cards.card_slot(card, field))
    values.extend([0.0] * (cards.CARD_SLOT * (capacity - len(dealt))))
    return values


def _card_ids(readout, reads, params):
    """One card id per dealt card, the pad past the deal (card-tokens.md §3)."""
    capacity, exact = params
    field = reads[0]
    dealt = _cards(readout[field], field, capacity, exact)
    values = [cards.card_id(card, field) for card in dealt]
    values.extend([PAD] * (capacity - len(dealt)))
    return values


def _stacks_scaled(readout, reads, params):
    """One stack slot per seat, each over the shape's fixed divisor.

    `params` carries the shape's stack normaliser, its **declared stacks order** and its
    seat count: `actor-first` writes the acting seat's stack then the other's -- the order
    the two-seat rows have always had, and the one mode that reads a second fact -- and
    `seat-order` writes one slot per seat in seat order (`seats.md` §3, flat-numeric.md §4,
    encoder.md §4, ASM-44).
    """
    divisor, order, seats = params
    stacks = _counts(readout[reads[0]], reads[0], seats)
    if order == "actor-first":
        seat, _flag = _seat(readout[reads[1]], seats)
        return [stacks[seat] / divisor, stacks[1 - seat] / divisor]
    return [amount / divisor for amount in stacks]


def _amount_scaled(readout, reads, params):
    """One amount over its fixed divisor (flat-numeric.md §4)."""
    field = reads[0]
    return [_count(readout[field], field) / params]


def _limit_scaled(readout, reads, params):
    """The bet size in force, then the bet-or-raise actions this street (flat-numeric.md §4)."""
    bet_divisor, raise_divisor = params
    field = reads[0]
    bet, raises = _counts(readout[field], field)
    return [bet / bet_divisor, raises / raise_divisor]


def _stacks_buckets(readout, reads, params):
    """One bucket per seat's stack, in the readout's seat order (card-tokens.md §4).

    `params` carries the shape's stacks ladder and its seat count, so the block declares one
    token per seat on every shape and reads one fact: the token encoding's stack order is
    the readout's on all three rows (`seats.md` §3, ASM-44).
    """
    ladder, seats = params
    field = reads[0]
    return [_bucket(amount, ladder)
            for amount in _counts(readout[field], field, seats)]


def _amount_bucket(readout, reads, params):
    """One bucket of one amount (card-tokens.md §4)."""
    field = reads[0]
    return [_bucket(_count(readout[field], field), params)]


def _limit_ids(readout, reads, params):
    """The bet size's bucket, then the bet-or-raise action count's (card-tokens.md §4)."""
    bet_ladder, raise_ladder = params
    field = reads[0]
    bet, raises = _counts(readout[field], field)
    return [_bucket(bet, bet_ladder), _bucket(raises, raise_ladder)]


def _history_onehot(readout, reads, params):
    """The shape's slots of 3, one per applied action, oldest first (flat-numeric.md §5).

    `params` carries the shape's capacity and the slot's three-way width, so the block's
    length and its refusal threshold are the shape row's and no writer holds either
    (shapes.md §8, ASM-42).
    """
    slots, slot_width = params
    field = reads[0]
    entries = _entries(readout[field], field, slots)
    values = [0.0] * (slots * slot_width)
    for position, entry in enumerate(entries):
        values[slot_width * position + history.action_of_entry(entry)] = 1.0
    return values


def _history_ids(readout, reads, params):
    """One id per applied action, the pad past the end (card-tokens.md §5).

    `params` carries the shape's capacity and the three action-kind ids, so the block's
    length and its refusal threshold are the shape row's, and the ids do not move between
    shapes (shapes.md §8, ASM-42, ASM-44).
    """
    slots, ids = params
    field = reads[0]
    entries = _entries(readout[field], field, slots)
    values = [ids[history.action_of_entry(entry)] for entry in entries]
    values.extend([PAD] * (slots - len(entries)))
    return values


# The closed set: every writer tag a block table may name, and no tag outside it.
WRITERS = {
    "street-onehot": _street_onehot,
    "seat-index": _seat_index,
    "card-onehot": _card_onehot,
    "stacks-scaled": _stacks_scaled,
    "amount-scaled": _amount_scaled,
    "limit-scaled": _limit_scaled,
    "history-onehot": _history_onehot,
    "street-id": _street_id,
    "seat-ids": _seat_ids,
    "card-ids": _card_ids,
    "stacks-buckets": _stacks_buckets,
    "amount-bucket": _amount_bucket,
    "limit-ids": _limit_ids,
    "history-ids": _history_ids,
}


def encode(encoder, readout):
    """One readout, one observation: a fresh array of the declared shape and dtype.

    The readout is refused as a whole (not a mapping) and field by field (a carried
    fact it is missing) before the first write, and a key the encoding does not carry
    -- `legal` above all -- is ignored and never refused (surface.md §6,
    guardrails.md G9).
    """
    declaration = require_encoder(encoder, "encode")._declaration
    if not isinstance(readout, Mapping):
        raise InvalidReadout(
            "encode(readout): the readout must be a mapping with the nine carried "
            "facts, got %s" % type(readout).__name__
        )
    for field in declaration["fields"]:
        if field not in readout:
            raise InvalidReadout(
                "encode(readout): the readout is missing %r, which this encoding carries"
                % (field,)
            )
    out = numpy.zeros(declaration["shape"], dtype=declaration["dtype"])
    for _field, offset, width, writer, reads, params in declaration["blocks"]:
        out[offset : offset + width] = WRITERS[writer](readout, reads, params)
    return out
