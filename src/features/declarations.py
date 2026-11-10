"""The one declaration table both encodings are rows of (encoder.md §4).

`ENCODING_NAMES` fixes the ladder's two encodings and the order they are declared
in.  A **shape row** (`SHAPE_ROWS`, default first) is the part of this module that
the game shape varies, and it is the module's **single** statement of it: the
descriptors in the shape's own index order, the five amount normalisers, and the
five bucket ladders of the token encoding (shapes.md §2, sizing.md §3, §5).  A
**declaration** is one encoding on one shape: the six spec keys plus a **block
table** whose widths sum to the declared shape.

A block record is a 6-tuple ``(field, offset, width, writer, reads, params)`` -- the
field it writes, the first slot it writes, how many slots, the tag of the writer
`encode.py` calls, the readout keys that writer reads, and the writer's own
constants.

The offsets are **derived** from the widths (``offset[i] = offset[i-1] + width[i-1]``,
and the shape is their sum), so the table is the single source `encode` walks and a
hard-coded offset cannot drift from it (encoder.md §4, guardrails.md G3).  A third
encoding would be a third *name* here, never a third module (D-3, guardrails.md G1).

The normalisers and the descriptors are **restated, not imported**: this module
imports no other project module (layout.md §3, guardrails.md G12), so the values a
shape declares are the same values `engine.game_shapes()` publishes, and the join
battery is what holds the two statements equal (shapes.md §2, D-13).  Nothing else
in the module writes a divisor or a bucket edge down: every block's `params` is read
from the shape's row here.
"""

from __future__ import annotations

from .cards import CARD_SLOT
from .errors import UnknownEncoding, UnknownShape

# The nine facts an observation carries, in the readout's own order less `legal` and the
# derived `hand_class` (encoder.md §3.1, ASM-30); it is also both encodings' block order.
FIELDS = (
    "street",
    "seat",
    "hole",
    "board",
    "stacks",
    "pot",
    "to_call",
    "limit",
    "history",
)

# The four streets, in the readout's own order (readout.md §2).
STREETS = ("preflop", "flop", "turn", "river")

STREET_ID_BASE = 53          # 53 + street index, so preflop is 53 (card-tokens.md §3)
SEAT_INDEX_BASE = 57         # 57 + seat index
SEAT_FLAG_BASE = 59          # 59 + button flag
HISTORY_IDS = (93, 94, 95)   # the three action *kinds*: fold, check-call, raise

HISTORY_SLOTS = 24           # the block's capacity, and the refusal threshold
HISTORY_SLOT_WIDTH = 3       # one slot per action kind in the dense encoding

#: The first row of the catalogue, and what an absent shape reads as (shapes.md §3).
DEFAULT_SHAPE = "fixed-limit-20"

#: The two declared encodings, in the ladder's order (ladder.md §2, surface.md §3).
ENCODING_NAMES = ("flat-numeric", "card-tokens")

#: What each encoding declares beyond its block table: the representation family, the
#: dtype and the token-id cardinality.  All three are **the same on every shape** -- the
#: slot counts, the block widths and the token vocabulary do not move (sizing.md §5).
_ENCODING_ROWS = {
    "flat-numeric": {
        "representation": "flat-numeric",
        "kind": "dense-numeric",
        "dtype": "float32",
        "vocabulary": None,
    },
    "card-tokens": {
        "representation": "card-tokens",
        "kind": "token-sequence",
        "dtype": "int32",
        "vocabulary": 96,
    },
}

# The five bucket ladders of the token encoding, as (upper bound, id) pairs read in
# order; the last bound is unbounded, so each ladder is total over the non-negative
# integers and no amount is ever unrepresentable (card-tokens.md §4).
#
# `fixed-limit-20`: the edges of ASM-6's 20-chip game, and what the encoding has always
# carried -- stack ÷20, pot ÷40, `to_call` ÷20, the bet size ÷4 and the count ÷4
# (flat-numeric.md §4, card-tokens.md §4).
_FIXED_LIMIT_LADDERS = {
    "to_call": ((0, 61), (1, 62), (2, 63), (3, 64), (4, 65), (6, 66), (10, 67), (None, 68)),
    "pot": ((3, 69), (5, 70), (8, 71), (12, 72), (16, 73), (24, 74), (32, 75), (None, 76)),
    "stacks": ((1, 77), (3, 78), (5, 79), (8, 80), (11, 81), (14, 82), (17, 83), (None, 84)),
    "amount": ((1, 85), (2, 86), (4, 87), (None, 88)),
    "count": ((0, 89), (1, 90), (2, 91), (None, 92)),
}

# `no-limit-100`: the same ten ids per block, re-edged for a 100-chip stack and a
# 200-chip game -- a divisor of 40 on a 200-chip pot is a clip, not a normalisation
# (sizing.md §5, ASM-39).
_NO_LIMIT_LADDERS = {
    "to_call": ((0, 61), (1, 62), (2, 63), (3, 64), (5, 65), (10, 66), (25, 67), (None, 68)),
    "pot": ((4, 69), (8, 70), (16, 71), (32, 72), (64, 73), (100, 74), (150, 75), (None, 76)),
    "stacks": ((5, 77), (10, 78), (20, 79), (40, 80), (60, 81), (80, 82), (95, 83), (None, 84)),
    "amount": ((5, 85), (10, 86), (25, 87), (None, 88)),
    "count": ((0, 89), (2, 90), (5, 91), (None, 92)),
}

#: The descriptor spellings a shape may declare, and the note `action_space`'s record
#: carries for each beyond its `name`: the fixed-limit `raise` resolves to the minimum
#: legal completion, and a sized band resolves to its own band's maximum (vocabulary.md
#: §2, sizing.md §2).  Prose, never a number: no string in the record contains a digit
#: (vocabulary.md §2, guardrails.md G6).
_RESOLUTIONS = {
    "raise": (
        "completion",
        "the engine's minimum legal completion for the decision",
    ),
    "raise-minimum": ("band", "the minimum legal raise-to amount"),
    "raise-quarter": (
        "band",
        "the highest amount in the first quarter of the legal raise interval",
    ),
    "raise-half": (
        "band",
        "the highest amount in the second quarter of the legal raise interval",
    ),
    "raise-all-in": ("band", "the largest legal raise-to amount, the all-in"),
}

#: The declared shapes, in the catalogue's own order -- default first (shapes.md §2).
#: A row is data: the vocabulary in the shape's index order, the amount normalisers under
#: the same five key names `engine.game_shapes()` publishes, and the bucket ladders
#: (shapes.md §2, sizing.md §3, §5).
SHAPE_ROWS = {
    "fixed-limit-20": {
        "default": True,
        "actions": ("fold", "check-call", "raise"),
        "normalisers": {"stack": 20, "pot": 40, "to_call": 20, "amount": 4, "count": 4},
        "ladders": _FIXED_LIMIT_LADDERS,
    },
    "no-limit-100": {
        "default": False,
        "actions": (
            "fold",
            "check-call",
            "raise-quarter",
            "raise-half",
            "raise-all-in",
            "raise-minimum",
        ),
        "normalisers": {
            "stack": 100,
            "pot": 200,
            "to_call": 100,
            "amount": 100,
            "count": 50,
        },
        "ladders": _NO_LIMIT_LADDERS,
    },
}


def _table(rows):
    """One encoding's block records, each offset the sum of the widths before it."""
    blocks = []
    offset = 0
    for field, width, writer, reads, params in rows:
        blocks.append((field, offset, width, writer, reads, params))
        offset += width
    return tuple(blocks)


def _shape(blocks):
    """One observation's shape: the sum of the block widths, and nothing else."""
    return (sum(block[2] for block in blocks),)


# flat-numeric: four street slots, two seat slots, two and five card slots of 17,
# two stacks, the pot, the amount to call, the limit pair, and 24 history slots of 3
# -- 4 + 2 + 34 + 85 + 2 + 1 + 1 + 2 + 72 = 203 (flat-numeric.md §2).
# `stacks` is the one dense block that reads a second fact: its slots are the acting
# seat's stack, then the other's (flat-numeric.md §4, encoder.md §4).  The five amount
# params are the shape's normalisers and nothing else (flat-numeric.md §4).
def _flat_blocks(row):
    """The dense encoding's block table on one shape (flat-numeric.md §2)."""
    normalisers = row["normalisers"]
    return _table((
        ("street", len(STREETS), "street-onehot", ("street",), STREETS),
        ("seat", 2, "seat-index", ("seat",), None),
        ("hole", 2 * CARD_SLOT, "card-onehot", ("hole",), (2, True)),
        ("board", 5 * CARD_SLOT, "card-onehot", ("board",), (5, False)),
        ("stacks", 2, "stacks-scaled", ("stacks", "seat"), normalisers["stack"]),
        ("pot", 1, "amount-scaled", ("pot",), normalisers["pot"]),
        ("to_call", 1, "amount-scaled", ("to_call",), normalisers["to_call"]),
        ("limit", 2, "limit-scaled", ("limit",),
         (normalisers["amount"], normalisers["count"])),
        ("history", HISTORY_SLOTS * HISTORY_SLOT_WIDTH, "history-onehot", ("history",),
         (HISTORY_SLOTS, HISTORY_SLOT_WIDTH)),
    ))


# card-tokens: one street token, two seat tokens, two and five card tokens, two
# stack tokens, the pot, the amount to call, the limit pair, and 24 history tokens
# -- 1 + 2 + 2 + 5 + 2 + 1 + 1 + 2 + 24 = 40 over 96 ids (card-tokens.md §2, §6).
# The five ladders are the shape's and the ids they emit do not move between shapes
# (card-tokens.md §4).
def _token_blocks(row):
    """The token encoding's block table on one shape (card-tokens.md §2)."""
    ladders = row["ladders"]
    return _table((
        ("street", 1, "street-id", ("street",), (STREETS, STREET_ID_BASE)),
        ("seat", 2, "seat-ids", ("seat",), (SEAT_INDEX_BASE, SEAT_FLAG_BASE)),
        ("hole", 2, "card-ids", ("hole",), (2, True)),
        ("board", 5, "card-ids", ("board",), (5, False)),
        ("stacks", 2, "stacks-buckets", ("stacks",), ladders["stacks"]),
        ("pot", 1, "amount-bucket", ("pot",), ladders["pot"]),
        ("to_call", 1, "amount-bucket", ("to_call",), ladders["to_call"]),
        ("limit", 2, "limit-ids", ("limit",),
         (ladders["amount"], ladders["count"])),
        ("history", HISTORY_SLOTS, "history-ids", ("history",),
         (HISTORY_SLOTS, HISTORY_IDS)),
    ))


def shape_names():
    """Every declared shape name, in the catalogue's order -- default first (shapes.md §2)."""
    return tuple(SHAPE_ROWS)


def require_shape(shape, entry_point, argument="shape"):
    """The shape name `shape` denotes, or the refusal naming it and the declared names.

    `None` is the **default** shape and is not a defaulting of a name: absence and a name
    the catalogue does not carry are different facts, and only the first is legal
    (shapes.md §3, D-13).  A name outside the catalogue is refused, never substituted.
    """
    if shape is None:
        return DEFAULT_SHAPE
    for name in SHAPE_ROWS:
        if isinstance(shape, str) and shape == name:
            return name
    raise UnknownShape(
        "%s(%s): %r is not one of the declared shapes %r, and a shape name is never "
        "defaulted (shapes.md §2, D-29)" % (entry_point, argument, shape, shape_names())
    )


def shape_row(shape=None, entry_point="shape_row"):
    """One declared row, as a fresh mapping (shapes.md §2)."""
    name = require_shape(shape, entry_point)
    row = SHAPE_ROWS[name]
    return {
        "name": name,
        "default": row["default"],
        "actions": tuple(row["actions"]),
        "normalisers": dict(row["normalisers"]),
        "ladders": {key: tuple(value) for key, value in row["ladders"].items()},
    }


def shape_rows(shape=None, entry_point="shape_rows"):
    """The catalogue, default first, as fresh rows (shapes.md §2).

    The instance set is the declaration itself, so no caller can invent a shape here.
    """
    if shape is not None:
        return (shape_row(shape, entry_point),)
    return tuple(shape_row(name, entry_point) for name in SHAPE_ROWS)


def require_encoding(name, entry_point, argument="name"):
    """The encoding name, or the refusal naming it and the two declared encodings."""
    for declared in ENCODING_NAMES:
        if isinstance(name, str) and name == declared:
            return declared
    raise UnknownEncoding(
        "%s(%s): the encoding must be one of %r, got %r"
        % (entry_point, argument, ENCODING_NAMES, name)
    )


def declaration(name, shape=None, entry_point="build_encoder"):
    """One encoding on one shape: the six spec keys plus its block table (encoder.md §4).

    Built fresh on every call, so a caller's edit of a returned table cannot reach the
    next caller's (surface.md §1, guardrails.md G11).
    """
    encoding = require_encoding(name, entry_point)
    row = shape_row(shape, entry_point)
    blocks = _flat_blocks(row) if encoding == "flat-numeric" else _token_blocks(row)
    record = {
        "representation": _ENCODING_ROWS[encoding]["representation"],
        "kind": _ENCODING_ROWS[encoding]["kind"],
        "fields": FIELDS,
        "shape": _shape(blocks),
        "dtype": _ENCODING_ROWS[encoding]["dtype"],
        "vocabulary": _ENCODING_ROWS[encoding]["vocabulary"],
        "blocks": blocks,
    }
    return record


def spec(name, shape=None, entry_point="build_encoder"):
    """The six-key spec record of one encoding on one shape (encoder.md §3).

    The six values are the shape-invariant part of a declaration: the slot counts, the
    block widths, the dtype and the token vocabulary are the same on every shape, so
    this record does not name the shape it was built for (sizing.md §5, encoder.md §3).
    """
    record = declaration(name, shape, entry_point)
    return {
        "representation": record["representation"],
        "kind": record["kind"],
        "fields": record["fields"],
        "shape": record["shape"],
        "dtype": record["dtype"],
        "vocabulary": record["vocabulary"],
    }


def catalogue():
    """The two declared encodings' spec records on the default shape (surface.md §3)."""
    return {name: spec(name) for name in ENCODING_NAMES}
