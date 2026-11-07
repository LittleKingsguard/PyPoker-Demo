"""The one declaration table both encodings are rows of (encoder.md §4).

`ENCODINGS` is the only place an encoding is declared: its name, the six spec keys
and a **block table** whose widths sum to the declared shape.  A block record is a
6-tuple ``(field, offset, width, writer, reads, params)`` -- the field it writes, the
first slot it writes, how many slots, the tag of the writer `encode.py` calls, the
readout keys that writer reads, and the writer's own constants.

The offsets are **derived** from the widths (``offset[i] = offset[i-1] + width[i-1]``,
and the shape is their sum), so the table is the single source `encode` walks and a
hard-coded offset cannot drift from it (encoder.md §4, guardrails.md G3).  A third
encoding would be a third row here, never a third module (D-3, guardrails.md G1).
"""

from __future__ import annotations

from .cards import CARD_SLOT

# The nine facts an observation carries, in the readout's own order less `legal`
# (encoder.md §3.1).  This tuple is also the block order of both encodings.
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

# The five bucket ladders of the token encoding, as (upper bound, id) pairs read in
# order; the last bound is unbounded, so each ladder is total over the non-negative
# integers and no amount is ever unrepresentable (card-tokens.md §4).
TO_CALL_LADDER = ((0, 61), (1, 62), (2, 63), (3, 64), (4, 65), (6, 66), (10, 67), (None, 68))
POT_LADDER = ((3, 69), (5, 70), (8, 71), (12, 72), (16, 73), (24, 74), (32, 75), (None, 76))
STACK_LADDER = ((1, 77), (3, 78), (5, 79), (8, 80), (11, 81), (14, 82), (17, 83), (None, 84))
BET_LADDER = ((1, 85), (2, 86), (4, 87), (None, 88))
RAISE_LADDER = ((0, 89), (1, 90), (2, 91), (None, 92))

STREET_ID_BASE = 53          # 53 + street index, so preflop is 53 (card-tokens.md §3)
SEAT_INDEX_BASE = 57         # 57 + seat index
SEAT_FLAG_BASE = 59          # 59 + button flag
HISTORY_IDS = (93, 94, 95)   # the action indices: fold, check-call, raise

HISTORY_SLOTS = 24           # the block's capacity, and the refusal threshold
HISTORY_SLOT_WIDTH = 3       # one slot per action kind in the dense encoding

STACK_DIVISOR = 20           # the chips a seat begins a hand with
POT_DIVISOR = 40             # the chips a hand begins with
TO_CALL_DIVISOR = 20
BET_DIVISOR = 4              # the big bet
RAISE_DIVISOR = 4            # the cap of bet-or-raise actions a street (ASM-6)


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
# seat's stack, then the other's (flat-numeric.md §4, encoder.md §4).
_FLAT_BLOCKS = _table((
    ("street", len(STREETS), "street-onehot", ("street",), STREETS),
    ("seat", 2, "seat-index", ("seat",), None),
    ("hole", 2 * CARD_SLOT, "card-onehot", ("hole",), (2, True)),
    ("board", 5 * CARD_SLOT, "card-onehot", ("board",), (5, False)),
    ("stacks", 2, "stacks-scaled", ("stacks", "seat"), STACK_DIVISOR),
    ("pot", 1, "amount-scaled", ("pot",), POT_DIVISOR),
    ("to_call", 1, "amount-scaled", ("to_call",), TO_CALL_DIVISOR),
    ("limit", 2, "limit-scaled", ("limit",), (BET_DIVISOR, RAISE_DIVISOR)),
    ("history", HISTORY_SLOTS * HISTORY_SLOT_WIDTH, "history-onehot", ("history",),
     (HISTORY_SLOTS, HISTORY_SLOT_WIDTH)),
))

# card-tokens: one street token, two seat tokens, two and five card tokens, two
# stack tokens, the pot, the amount to call, the limit pair, and 24 history tokens
# -- 1 + 2 + 2 + 5 + 2 + 1 + 1 + 2 + 24 = 40 over 96 ids (card-tokens.md §2, §6).
_TOKEN_BLOCKS = _table((
    ("street", 1, "street-id", ("street",), (STREETS, STREET_ID_BASE)),
    ("seat", 2, "seat-ids", ("seat",), (SEAT_INDEX_BASE, SEAT_FLAG_BASE)),
    ("hole", 2, "card-ids", ("hole",), (2, True)),
    ("board", 5, "card-ids", ("board",), (5, False)),
    ("stacks", 2, "stacks-buckets", ("stacks",), STACK_LADDER),
    ("pot", 1, "amount-bucket", ("pot",), POT_LADDER),
    ("to_call", 1, "amount-bucket", ("to_call",), TO_CALL_LADDER),
    ("limit", 2, "limit-ids", ("limit",), (BET_LADDER, RAISE_LADDER)),
    ("history", HISTORY_SLOTS, "history-ids", ("history",), (HISTORY_SLOTS, HISTORY_IDS)),
))

# The declared encodings, in the ladder's order: `flat-numeric` then `card-tokens`
# (ladder.md §2, surface.md §3).  Each row is the six spec keys plus its block table.
ENCODINGS = {
    "flat-numeric": {
        "representation": "flat-numeric",
        "kind": "dense-numeric",
        "fields": FIELDS,
        "shape": _shape(_FLAT_BLOCKS),
        "dtype": "float32",
        "vocabulary": None,
        "blocks": _FLAT_BLOCKS,
    },
    "card-tokens": {
        "representation": "card-tokens",
        "kind": "token-sequence",
        "fields": FIELDS,
        "shape": _shape(_TOKEN_BLOCKS),
        "dtype": "int32",
        "vocabulary": 96,
        "blocks": _TOKEN_BLOCKS,
    },
}
