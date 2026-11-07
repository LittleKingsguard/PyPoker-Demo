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


def _seat(value):
    """The ``(index, button flag)`` of a seat, or the refusal (flat-numeric.md §6)."""
    if _is_sequence(value) and len(value) == 2:
        index, flag = value[0], value[1]
        if _is_count(index) and index in (0, 1) and isinstance(flag, bool):
            return int(index), flag
    raise InvalidReadout(
        "encode(readout): 'seat' must be a seat index 0 or 1 and a bool button flag, "
        "got %r" % (value,)
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


def _counts(value, field):
    """Two non-negative integer chip counts, or the refusal (errors.md §3, §4)."""
    if _is_sequence(value) and len(value) == 2:
        first, second = value[0], value[1]
        if _is_count(first) and _is_count(second) and first >= 0 and second >= 0:
            return int(first), int(second)
    raise InvalidReadout(
        "encode(readout): %r must be two non-negative integers, got %r" % (field, value)
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
    """The acting seat's index, then its button flag (flat-numeric.md §4)."""
    index, flag = _seat(readout[reads[0]])
    return [float(index), 1.0 if flag else 0.0]


def _seat_ids(readout, reads, params):
    """57 + index, then 59 + flag (card-tokens.md §3)."""
    index_base, flag_base = params
    index, flag = _seat(readout[reads[0]])
    return [index_base + index, flag_base + (1 if flag else 0)]


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
    """The acting seat's stack, then the other's, each over the fixed divisor.

    The one dense block that reads a second fact, and its `reads` says so
    (flat-numeric.md §4, encoder.md §4).
    """
    stacks = _counts(readout[reads[0]], reads[0])
    seat, _flag = _seat(readout[reads[1]])
    return [stacks[seat] / params, stacks[1 - seat] / params]


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
    """One bucket per seat's stack, in the readout's seat order (card-tokens.md §4)."""
    field = reads[0]
    return [_bucket(amount, params) for amount in _counts(readout[field], field)]


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
    """24 slots of 3, one per applied action, oldest first (flat-numeric.md §5)."""
    slots, slot_width = params
    field = reads[0]
    entries = _entries(readout[field], field, slots)
    values = [0.0] * (slots * slot_width)
    for position, entry in enumerate(entries):
        values[slot_width * position + history.action_of_entry(entry)] = 1.0
    return values


def _history_ids(readout, reads, params):
    """One id per applied action, the pad past the end (card-tokens.md §5)."""
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
