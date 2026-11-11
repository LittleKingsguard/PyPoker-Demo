"""Plumbing and invented readouts for the `features` unit battery (D-11).

This module is test support, not part of any subsystem.  It does four things:

* it puts the repository's ``src/`` on ``sys.path`` and imports the declared
  ``features`` package **lazily**, so that "the surface is absent" is one clean
  ``SurfaceAbsent`` failure in each case that needed it and never a collection
  error -- ``src/features/`` is written by L4 and the whole battery must stay
  collectable while it does not exist (``docs/L1/battery.md`` §1, §2);
* it drives the seven entry points of ``docs/L2/features/surface.md`` §3-§9 and
  nothing below them: no ``src/features/`` submodule, helper, private name,
  ``Encoder`` class or error class is ever touched (``docs/L3/features/README.md``
  §3, D-12);
* it holds the **invented readouts** the battery encodes.  A readout is a plain
  mapping the battery builds itself: this battery imports neither ``engine`` nor
  ``pokerkit``, because it tests this module in isolation and the battery that
  drives real engine readouts is a different layer's (D-13).  The invented values
  are the writer's own; only the value *shapes* and the design's fixed numbers
  (block offsets and widths, slot order, token ids, bucket edges, the card
  spelling and the history grammar) appear below, because a case asserts them;
* it holds tolerant readers for what the design leaves free (how a refusal's
  message is spelled, how an encoder is stored), so a case asserts the contract
  and never an implementation's private spelling.

The numbers below are the design's: ``docs/L3/features/flat-numeric.md`` §2-§5,
``docs/L3/features/card-tokens.md`` §2-§6, ``docs/L3/features/encoder.md`` §3-§6,
``docs/L3/features/vocabulary.md`` §1-§4.  Nothing here is an invented constant
except the readout *contents* (cards, chips, history entries and streets), and
those are marked as such.
"""

from __future__ import annotations

import copy
import importlib
import json
import numbers as _numbers
import os
import random
import subprocess
import sys
import unittest
from collections.abc import Mapping

import numpy

# --------------------------------------------------------------------------
# The declared surface (docs/L2/features/surface.md §1, layout.md §2)
# --------------------------------------------------------------------------
NINE = (
    "encodings",
    "build_encoder",
    "observation_spec",
    "encode",
    "action_space",
    "legal_indices",
    "decode_action",
)

# The readout's eleven facts, exactly (docs/L2/features/encodings.md §2, README.md §4,
# ASM-30), and the nine of them an observation carries -- neither `legal` nor D-21's
# `hand_class` is carried (D-21, ASM-30).
FACTS = (
    "street",
    "seat",
    "hole",
    "board",
    "stacks",
    "pot",
    "to_call",
    "limit",
    "history",
    "legal",
    "hand_class",
)
FIELDS = tuple(fact for fact in FACTS if fact not in ("legal", "hand_class"))
SPEC_KEYS = ("representation", "kind", "fields", "shape", "dtype", "vocabulary")

STREETS = ("preflop", "flop", "turn", "river")
ACTIONS = ("fold", "check-call", "raise")

# The card spelling (ASM-E1, features/README.md §4) and the two alphabets.
RANKS = "23456789TJQKA"
SUITS = "cdhs"
BOARD_SIZES = (0, 3, 4, 5)

# The two encodings, in the ladder's order (encodings.md §1, ladder.md §2).
FLAT = "flat-numeric"
TOKENS = "card-tokens"
ENCODINGS = (FLAT, TOKENS)

# What each encoding declares: representation, kind, shape, dtype, vocabulary
# (encodings.md §1, surface.md §5).  ``shape`` is the **default** shape's -- the record
# an encoder built with no shape declares, and the width a kind's declared observation
# size stays at (shapes.md §8, ASM-44); ``DECLARED_BY_SHAPE`` below carries the other two
# rows' pairs.
DECLARED = {

    FLAT: {
        "kind": "dense-numeric",
        "shape": (203,),
        "dtype": "float32",
        "vocabulary": None,
    },
    TOKENS: {
        "kind": "token-sequence",
        "shape": (40,),
        "dtype": "int32",
        "vocabulary": 96,
    },
}

# The two block tables on the **default** shape: (field, offset, width), in the spec's
# `fields` order (flat-numeric.md §2, card-tokens.md §2, encoder.md §4).  The eight blocks
# before the history are one table on the two-seat shapes; the history's offset is theirs
# and its width is `HISTORY_SLOT_WIDTH * CAPACITY[shape]` (dense) or `CAPACITY[shape]`
# (token) (shapes.md §8, ASM-42).  `FLAT_BLOCKS_BY_SHAPE` / `TOKEN_BLOCKS_BY_SHAPE` below
# carry all three rows, and `flat_blocks` / `token_blocks` derive them from the arithmetic
# `capacity.md` §2 states (ASM-42, ASM-44).
FLAT_BLOCKS = (
    ("street", 0, 4),
    ("seat", 4, 2),
    ("hole", 6, 34),
    ("board", 40, 85),
    ("stacks", 125, 2),
    ("pot", 127, 1),
    ("to_call", 128, 1),
    ("limit", 129, 2),
    ("history", 131, 72),
)
TOKEN_BLOCKS = (
    ("street", 0, 1),
    ("seat", 1, 2),
    ("hole", 3, 2),
    ("board", 5, 5),
    ("stacks", 10, 2),
    ("pot", 12, 1),
    ("to_call", 13, 1),
    ("limit", 14, 2),
    ("history", 16, 24),
)
FLAT_WIDTH = 203
TOKEN_WIDTH = 40
CARD_SLOT = 17          # 13 ranks + 4 suits (flat-numeric.md §3)
RANK_WIDTH = 13
HISTORY_SLOTS = 24      # the default shape's capacity: 24 slots of 3, or 24 tokens
HISTORY_SLOT_WIDTH = 3
VOCABULARY = 96         # ids 0-95 (card-tokens.md §6)

# The history block's capacity is the **shape's** (shapes.md §8, ASM-42): it is both the
# number of action slots the block declares and the refusal threshold, so the three
# declared shapes have three capacities and three pairs of widths.  The 127 dense slots
# and the 12 tokens that **no seat count touches** are the encoding's and do not move;
# the `seat` and the `stacks` blocks are one slot per seat, so the slots before the
# history are `127 + 2 x seats` and `12 + 2 x seats`, and the blocks that follow them are
# 3 x capacity and capacity (flat-numeric.md §2, §5; card-tokens.md §2, §5, seats.md §3,
# capacity.md §2, ASM-42, ASM-44):
#     131 + 3 x 24 = 203   and  16 + 24 = 40    on `fixed-limit-20` -- today's layout
#     131 + 3 x 66 = 329   and  16 + 66 = 82    on `no-limit-100`
#     139 + 3 x 98 = 433   and  24 + 98 = 122   on `six-seat-no-limit-100`
DEFAULT_SHAPE = "fixed-limit-20"
SECOND_SHAPE = "no-limit-100"
THIRD_SHAPE = "six-seat-no-limit-100"
SHAPES = (DEFAULT_SHAPE, SECOND_SHAPE)
ALL_SHAPES = SHAPES + (THIRD_SHAPE,)
CAPACITY = {DEFAULT_SHAPE: 24, SECOND_SHAPE: 66, THIRD_SHAPE: 98}
DECLARED_BY_SHAPE = {
    DEFAULT_SHAPE: {FLAT: (203,), TOKENS: (40,)},
    SECOND_SHAPE: {FLAT: (329,), TOKENS: (82,)},
    THIRD_SHAPE: {FLAT: (433,), TOKENS: (122,)},
}
# The seat count is the width of both per-seat blocks in both encodings, and the token
# vocabulary is the shape's: 96 ids on the two-seat rows, 102 on the six-seat one, whose
# seat block emits ids 96-101 above every id the other rows use (seats.md §2-§3,
# capacity.md §2, §4, ASM-44).
SEATS = {DEFAULT_SHAPE: 2, SECOND_SHAPE: 2, THIRD_SHAPE: 6}
VOCABULARY_BY_SHAPE = {DEFAULT_SHAPE: 96, SECOND_SHAPE: 96, THIRD_SHAPE: 102}
# The two two-seat rows' slots before the history -- the numbers `SHAPES`' cases use, kept
# because one shape's capacity is not another's while these do not move between the rows.
FIXED_FLAT_SLOTS = 131  # the two-seat rows' dense slots before the history: 4+2+34+85+2+1+1+2
FIXED_TOKEN_SLOTS = 16  # the two-seat rows' tokens before the history: 1+2+2+5+2+1+1+2
# The slots before the history that **no seat count touches** (street, hole, board, pot,
# to_call, limit) -- 127 dense and 12 token on all three rows (capacity.md §2, ASM-44).
SEAT_INVARIANT_FLAT_SLOTS = 127
SEAT_INVARIANT_TOKEN_SLOTS = 12


# -- the arithmetic `capacity.md` §2 states, one reading of it per encoding ----------
def seats_of(shape=DEFAULT_SHAPE):
    """The shape's seat count: the width of both per-seat blocks (seats.md §3)."""
    return SEATS[shape]


def capacity_of(shape=DEFAULT_SHAPE):
    """The shape's history capacity: the block's width and its refusal threshold."""
    return CAPACITY[shape]


def flat_slots_before_history(shape=DEFAULT_SHAPE):
    """`127 + 2 x seats`: 131 on the two-seat rows and 139 on the six-seat one."""
    return SEAT_INVARIANT_FLAT_SLOTS + 2 * seats_of(shape)


def token_slots_before_history(shape=DEFAULT_SHAPE):
    """`12 + 2 x seats`: 16 on the two-seat rows and 24 on the six-seat one."""
    return SEAT_INVARIANT_TOKEN_SLOTS + 2 * seats_of(shape)


def flat_width(shape=DEFAULT_SHAPE):
    """`127 + 2 x seats + 3 x capacity` -- 203, 329 and 433 (capacity.md §2)."""
    return flat_slots_before_history(shape) + HISTORY_SLOT_WIDTH * capacity_of(shape)


def token_width(shape=DEFAULT_SHAPE):
    """`12 + 2 x seats + capacity` -- 40, 82 and 122 (capacity.md §2)."""
    return token_slots_before_history(shape) + capacity_of(shape)


def _table(rows):
    """One block table, each offset the sum of the widths before it."""
    blocks = []
    offset = 0
    for field, width in rows:
        blocks.append((field, offset, width))
        offset += width
    return tuple(blocks)


def flat_blocks(shape=DEFAULT_SHAPE):
    """One shape's dense block table, `(field, offset, width)` (flat-numeric.md §2)."""
    seats = seats_of(shape)
    return _table((
        ("street", 4),
        ("seat", seats),
        ("hole", 34),
        ("board", 85),
        ("stacks", seats),
        ("pot", 1),
        ("to_call", 1),
        ("limit", 2),
        ("history", HISTORY_SLOT_WIDTH * capacity_of(shape)),
    ))


def token_blocks(shape=DEFAULT_SHAPE):
    """One shape's token block table, `(field, offset, count)` (card-tokens.md §2)."""
    seats = seats_of(shape)
    return _table((
        ("street", 1),
        ("seat", seats),
        ("hole", 2),
        ("board", 5),
        ("stacks", seats),
        ("pot", 1),
        ("to_call", 1),
        ("limit", 2),
        ("history", capacity_of(shape)),
    ))


FLAT_BLOCKS_BY_SHAPE = {shape: flat_blocks(shape) for shape in ALL_SHAPES}
TOKEN_BLOCKS_BY_SHAPE = {shape: token_blocks(shape) for shape in ALL_SHAPES}
SECOND_FLAT_BLOCKS = FLAT_BLOCKS_BY_SHAPE[SECOND_SHAPE]
SECOND_TOKEN_BLOCKS = TOKEN_BLOCKS_BY_SHAPE[SECOND_SHAPE]
THIRD_FLAT_BLOCKS = FLAT_BLOCKS_BY_SHAPE[THIRD_SHAPE]
THIRD_TOKEN_BLOCKS = TOKEN_BLOCKS_BY_SHAPE[THIRD_SHAPE]


# The pad and the id maps (card-tokens.md §3, §5, §6).
PAD = 0
STREET_IDS = {"preflop": 53, "flop": 54, "turn": 55, "river": 56}
SEAT_INDEX_BASE = 57    # 57 + index, so 57 seat 0 and 58 seat 1
SEAT_FLAG_BASE = 59     # 59 + flag, so 59 no button and 60 the button
SEAT_TOKEN_BASE = 96    # 96 + the seat slot: the six-seat row's own six seat ids
SIX_SEAT_SEAT_IDS = tuple(range(SEAT_TOKEN_BASE, SEAT_TOKEN_BASE + SEATS[THIRD_SHAPE]))
HISTORY_IDS = {"fold": 93, "check-call": 94, "raise": 95}

# The verb map: a history entry's fourth token decides its action index
# (flat-numeric.md §5, guardrail G13).
HISTORY_VERBS = {"folds": 0, "checks": 1, "calls": 1, "raises": 2}

# The five bucket ladders, as (upper bound, id) pairs read from the top; the last
# bound is unbounded and each ladder is total (card-tokens.md §4).  `LADDERS` is the
# **default** shape's; the uncapped row re-edges all five for a 100-chip stack and a
# 200-chip game, and the six-seat row keeps four of them -- a stack is bounded by 100,
# the amount in force by 100 and the count by 50 -- and re-edges the pot for its 600
# chips in play (card-tokens.md §4, seats.md §2, capacity.md §2, sizing.md §5):
#     pot 12, 24, 48, 96, 192, 300, 450 -- exactly three times `no-limit-100`'s
LADDERS = {
    "to_call": (
        (0, 61), (1, 62), (2, 63), (3, 64), (4, 65), (6, 66), (10, 67), (None, 68),
    ),
    "pot": (
        (3, 69), (5, 70), (8, 71), (12, 72), (16, 73), (24, 74), (32, 75), (None, 76),
    ),
    "stacks": (
        (1, 77), (3, 78), (5, 79), (8, 80), (11, 81), (14, 82), (17, 83), (None, 84),
    ),
    "bet": (
        (1, 85), (2, 86), (4, 87), (None, 88),
    ),
    "raises": (
        (0, 89), (1, 90), (2, 91), (None, 92),
    ),
}
SECOND_LADDERS = {
    "to_call": (
        (0, 61), (1, 62), (2, 63), (3, 64), (5, 65), (10, 66), (25, 67), (None, 68),
    ),
    "pot": (
        (4, 69), (8, 70), (16, 71), (32, 72), (64, 73), (100, 74), (150, 75), (None, 76),
    ),
    "stacks": (
        (5, 77), (10, 78), (20, 79), (40, 80), (60, 81), (80, 82), (95, 83), (None, 84),
    ),
    "bet": (
        (5, 85), (10, 86), (25, 87), (None, 88),
    ),
    "raises": (
        (0, 89), (2, 90), (5, 91), (None, 92),
    ),
}
SIX_SEAT_LADDERS = {
    "to_call": SECOND_LADDERS["to_call"],
    "pot": (
        (12, 69), (24, 70), (48, 71), (96, 72), (192, 73), (300, 74), (450, 75),
        (None, 76),
    ),
    "stacks": SECOND_LADDERS["stacks"],
    "bet": SECOND_LADDERS["bet"],
    "raises": SECOND_LADDERS["raises"],
}
LADDERS_BY_SHAPE = {
    DEFAULT_SHAPE: LADDERS,
    SECOND_SHAPE: SECOND_LADDERS,
    THIRD_SHAPE: SIX_SEAT_LADDERS,
}

# The modules `import features` must leave absent (layout.md §3, guardrail G12).
BOUNDARY = ("pokerkit", "torch", "engine", "agents", "evaluation", "training", "harness")


class SurfaceAbsent(AssertionError):
    """The declared `features` surface is absent, or a name of it is missing.

    It subclasses ``AssertionError`` so that the case that needed the surface
    records one clear *failure* naming what is missing, never an error inside
    this battery (``docs/L1/battery.md`` §1, §2).
    """


# --------------------------------------------------------------------------
# Import-path plumbing (the pattern of tests/engine/_engine_support.py)
# --------------------------------------------------------------------------
def repo_root():
    """The repository root: this file lives at ``<root>/tests/features/...``."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def src_dir():
    return os.path.join(repo_root(), "src")


def _ensure_src():
    src = src_dir()
    if src not in sys.path:
        sys.path.insert(0, src)


def module():
    """The declared ``features`` package, or one clear ``SurfaceAbsent``."""
    _ensure_src()
    try:
        return importlib.import_module("features")
    except Exception as exc:  # not importable yet, or broken on import
        raise SurfaceAbsent(
            "surface absent: the declared module 'features' is not importable from %s "
            "(%s: %s)" % (src_dir(), type(exc).__name__, exc)
        ) from exc


def ep(name):
    """One of the seven declared entry points, or one clear ``SurfaceAbsent``."""
    package = module()
    try:
        return getattr(package, name)
    except AttributeError:
        raise SurfaceAbsent(
            "surface absent: features.%s is not declared (layout.md §2)" % (name,)
        ) from None


def all_names():
    """``features.__all__``, the declared surface, or one clear ``SurfaceAbsent``."""
    package = module()
    declared = getattr(package, "__all__", None)
    if declared is None:
        raise SurfaceAbsent(
            "surface absent: features.__all__ is not declared (layout.md §2, guardrail G14)"
        )
    return tuple(declared)


def import_boundary_report():
    """Import ``features`` in a fresh interpreter and report what that import did.

    This is the verifiable form of ``layout.md`` §3: the in-process
    ``sys.modules`` is already polluted by whatever else the session imported --
    in a whole-tree run ``tests/e2e`` imports ``features`` before this battery --
    so the boundary is decided where it is observable: in a child interpreter
    that imports ``features`` itself, reads ``sys.modules`` and prints one JSON
    record holding ``imported`` (the import succeeded), ``added`` (the module
    names it added), ``present`` (the forbidden names still in ``sys.modules``)
    and ``all`` (``features.__all__``, read in the child).

    The child is a separate process on purpose: no case here measures the
    delta of *this* process's ``sys.modules``, because that delta is the import
    order of whatever else pytest collected and says nothing about ``features``.
    """
    _ensure_src()
    script = (
        "import json, sys\n"
        "sys.path.insert(0, %r)\n"
        "before = set(sys.modules)\n"
        "import features\n"
        "print(json.dumps({\n"
        "    'imported': 'features' in sys.modules,\n"
        "    'added': sorted(set(sys.modules) - before),\n"
        "    'present': sorted(name for name in %r if name in sys.modules),\n"
        "    'all': [name if isinstance(name, str) else repr(name)\n"
        "            for name in getattr(features, '__all__', [])],\n"
        "}))\n"
    ) % (src_dir(), list(BOUNDARY))
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repo_root(),
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise SurfaceAbsent(
            "surface absent: 'import features' fails in a fresh interpreter (%s)"
            % (completed.stderr.strip() or completed.stdout.strip(),)
        )
    return json.loads(completed.stdout.strip().splitlines()[-1])


# --------------------------------------------------------------------------
# Small readers.  A case asserts the contract through these instead of through
# a spelling this battery made up.
# --------------------------------------------------------------------------
def is_number(value):
    """A real number the battery reads as a quantity (booleans excluded)."""
    return isinstance(value, _numbers.Number) and not isinstance(value, (bool, complex))


def is_integer(value):
    """An integer, in the sense the index and chip-count contracts mean (bools out)."""
    return isinstance(value, _numbers.Integral) and not isinstance(value, bool)


def is_mapping(value):
    return isinstance(value, Mapping)


def floats(observation):
    """Every value of an observation as a plain float, in slot order."""
    return [float(value) for value in numpy.asarray(observation).reshape(-1).tolist()]


def ints(observation):
    """Every value of an observation as a plain int, in slot order."""
    return [int(value) for value in numpy.asarray(observation).reshape(-1).tolist()]


def plain_data_problem(value):
    """Why ``value`` is not plain data, or ``None`` when it is.

    ``encoder.md`` §3 makes every value in a spec record a ``str``, an ``int``, a
    ``tuple`` of those or ``None``, because the record is quoted in a report's
    header family.  A numpy dtype object (``guardrails.md`` G11) and a set are the
    two spellings a caller would then have to guess at.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return "a bool, which is not a spec value"
    if isinstance(value, str):
        return None
    if is_integer(value):
        return None
    if isinstance(value, tuple):
        for inner in value:
            problem = plain_data_problem(inner)
            if problem is not None:
                return "a tuple holding %s" % (problem,)
        return None
    if isinstance(value, (set, frozenset)):
        return "a set, whose order is not stable across processes (guardrails.md G11)"
    if isinstance(value, Mapping):
        return "a nested mapping, which the six-key record does not declare"
    name = type(value).__name__
    if "dtype" in name.lower():
        return "a numpy dtype object (%s), not the plain str 'float32' (guardrails.md G11)" % (
            name,
        )
    return "a %s, which is not plain data" % (name,)


def numbers(value, _depth=0):
    """Every number inside an observable value, in traversal order (keys excluded)."""
    if _depth > 20:
        return []
    if is_number(value):
        return [value]
    found = []
    if isinstance(value, Mapping):
        for inner in value.values():
            found.extend(numbers(inner, _depth + 1))
    elif isinstance(value, (list, tuple, set, frozenset)):
        for inner in value:
            found.extend(numbers(inner, _depth + 1))
    return found


def flatten_text(value, _depth=0):
    """Every key and every leaf of an observable value, as one lowercase string."""
    parts = []

    def walk(obj, depth):
        if depth > 20:
            return
        if isinstance(obj, Mapping):
            for key, inner in obj.items():
                parts.append(str(key))
                walk(inner, depth + 1)
        elif isinstance(obj, (list, tuple, set, frozenset)):
            for inner in obj:
                walk(inner, depth + 1)
        elif obj is not None:
            parts.append(str(obj))

    walk(value, 0)
    return " ".join(parts).lower()


def strings(value, _depth=0):
    """Every string inside an observable value, keys included, in traversal order.

    ``action_space``'s record is quoted in a report's header, so its *prose* is a
    value like any other: this reader is how the digit rule of ``guardrails.md``
    G6 reaches a key's text as well as a leaf's.
    """
    if _depth > 20:
        return []
    if isinstance(value, str):
        return [value]
    found = []
    if isinstance(value, Mapping):
        for key, inner in value.items():
            if isinstance(key, str):
                found.append(key)
            found.extend(strings(inner, _depth + 1))
    elif isinstance(value, (list, tuple, set, frozenset)):
        for inner in value:
            found.extend(strings(inner, _depth + 1))
    return found


def action_vocabulary(space):
    """The indices a declared action vocabulary names, read from keys as well as values.

    The same *weaker* reading ``tests/e2e/_surface.action_vocabulary`` does, so
    that this battery's FAM-2.9 assertion is that battery's assertion: every
    integer found in a key or a value, and every all-digit string, is folded into
    the set (``battery.md`` §3 FAM-2.9, ``vocabulary.md`` §2).

    It is deliberately not the whole rule: a digit *inside* prose -- a
    ``"raise to 4"`` -- escapes this reader, which is why the case that calls it
    also asserts :func:`strings`' no-digit rule (``vocabulary.md`` §2,
    ``guardrails.md`` G6).
    """
    found = set()

    def add(value):
        if is_integer(value):
            found.add(int(value))
        elif isinstance(value, str) and value.strip().isdigit():
            found.add(int(value.strip()))

    def walk(value, depth):
        if depth > 8:
            return
        if isinstance(value, Mapping):
            for key, inner in value.items():
                add(key)
                walk(inner, depth + 1)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for inner in value:
                walk(inner, depth + 1)
        else:
            add(value)

    walk(space, 0)
    return found


# --------------------------------------------------------------------------
# The card map, one reading shared by both encodings (README.md §4,
# flat-numeric.md §3, card-tokens.md §3)
# --------------------------------------------------------------------------
def rank_index(card):
    """The rank's slot inside the 13-wide rank one-hot: ``"2"`` is 0, ``"A"`` is 12."""
    return RANKS.index(card[0])


def suit_index(card):
    """The suit's slot inside the 4-wide suit one-hot: ``"c"`` is 0, ``"s"`` is 3."""
    return SUITS.index(card[1])


def card_id(card):
    """The card's token id: ``1 + 4 * rank_index + suit_index``, so ``"2c"`` is 1."""
    return 1 + 4 * rank_index(card) + suit_index(card)


def all_cards():
    """All 52 cards in id order (rank-major, suit-minor)."""
    return tuple(rank + suit for rank in RANKS for suit in SUITS)


def card_slot(card):
    """The 17 values one dealt card sets inside one dense card slot."""
    values = [0.0] * CARD_SLOT
    values[rank_index(card)] = 1.0
    values[RANK_WIDTH + suit_index(card)] = 1.0
    return values


def street_onehot(street):
    """The 4 values the dense street block holds for one street."""
    values = [0.0] * len(STREETS)
    values[STREETS.index(street)] = 1.0
    return values


def bucket(ladder, value):
    """The id the named ladder gives one non-negative integer."""
    for bound, ident in LADDERS[ladder]:
        if bound is None or value <= bound:
            return ident
    raise AssertionError("the %s ladder has no bound for %r" % (ladder, value))


def ladder_ids(ladder):
    """The ids the named ladder can emit, in ascending order."""
    return sorted({ident for _bound, ident in LADDERS[ladder]})


def bucket_on(shape, ladder, value):
    """The id one named ladder gives one non-negative integer on one declared shape.

    The ids do not move between shapes -- only the edges do -- so a case reads a
    six-seat pot, a six-seat stack or an amount to call on the row that declares it
    (card-tokens.md §4, capacity.md §2, ASM-44).
    """
    for bound, ident in LADDERS_BY_SHAPE[shape][ladder]:
        if bound is None or value <= bound:
            return ident
    raise AssertionError(
        "the %r ladder of %r has no bound for %r" % (ladder, shape, value)
    )


# --------------------------------------------------------------------------
# The history, read as one action index per entry (flat-numeric.md §5,
# card-tokens.md §5, guardrail G13)
# --------------------------------------------------------------------------
def history_action(entry):
    """The action index a history entry denotes, read off ASM-E2's fourth token."""
    tokens = entry.split()
    return HISTORY_VERBS[tokens[3]]


def history_block(history, slots=HISTORY_SLOTS):
    """The ``3 * slots`` dense values the history block holds: one per applied action.

    ``slots`` is the shape's capacity, so a case that walks a longer history on the
    second shape reads the same rule at that shape's length (shapes.md §8, ASM-42).
    """
    values = [0.0] * (slots * HISTORY_SLOT_WIDTH)
    for position, entry in enumerate(history):
        values[HISTORY_SLOT_WIDTH * position + history_action(entry)] = 1.0
    return values


def history_tokens(history, slots=HISTORY_SLOTS):
    """The ``slots`` token ids the history block holds, and the pad past the end."""
    values = [PAD] * slots
    for position, entry in enumerate(history):
        values[position] = HISTORY_IDS[ACTIONS[history_action(entry)]]
    return values



# --------------------------------------------------------------------------
# Invented readouts.  The cards, chips, streets and entries are the writer's own
# (battery.md §4, D-15): only their *shapes* are the contract's.  A default
# readout follows its street and holds plausible facts, but the defaults only
# have to be *shaped* like readouts, because a case overrides one fact at a time
# and the combination need not be one the engine could have produced: a flop
# default given seat=(1, False), a preflop readout whose to_call is 1 while the
# big blind acts, a stacks/pot pair that no deal would leave behind.  That is
# deliberate: `encode` must accept any readout whose carried facts are
# representable, one whose `pot + sum(stacks)` is not 40 included -- that
# invariant is the engine's, and re-checking it here would be a second source of
# truth (errors.md §4, flat-numeric.md §6, readout.md §2).  A case that needs an
# unrepresentable value builds a valid readout and overrides the one fact with
# :func:`with_facts`.
# --------------------------------------------------------------------------
STREET_DEFAULTS = {
    "preflop": {"pot": 3, "stacks": (19, 18), "to_call": 1, "limit": (2, 0)},
    "flop": {"pot": 6, "stacks": (17, 17), "to_call": 0, "limit": (2, 0)},
    "turn": {"pot": 10, "stacks": (15, 15), "to_call": 0, "limit": (4, 0)},
    "river": {"pot": 14, "stacks": (13, 13), "to_call": 0, "limit": (4, 1)},
}
BOARD_OF_STREET = {
    "preflop": (),
    "flop": ("Jh", "7c", "2d"),
    "turn": ("Jh", "7c", "2d", "Ks"),
    "river": ("Jh", "7c", "2d", "Ks", "3h"),
}
# A history whose sorted order is not its own order, so a writer that sorts it is
# visible (guardrails.md G4).
UNSORTED_HISTORY = (
    "flop seat 1 raises to 4",
    "flop seat 0 raises to 6",
    "preflop seat 0 folds",
)
_HISTORY_FORMS = (
    "preflop seat 0 folds",
    "flop seat 1 checks",
    "turn seat 0 calls 2",
    "river seat 1 raises to 4",
)


def history_entries(count):
    """``count`` entries of the four documented forms, cycling through them."""
    return [_HISTORY_FORMS[position % len(_HISTORY_FORMS)] for position in range(count)]


def readout(street="preflop", seat=(0, True), hole=("Td", "2c"), board=None,
            stacks=None, pot=None, to_call=None, limit=None, history=None,
            legal=None, hand_class=None, extra=None):
    """One invented readout: the eleven facts, as a fresh plain mapping.

    The defaults follow the street, so an untouched default is a plausible
    readout -- but only its *shape* is contracted, and an override can leave a
    combination the engine would not produce (see the note above).  A case that
    needs an *unrepresentable* value builds a valid readout and overrides the one
    fact with :func:`with_facts`.  `hand_class` defaults to `None`, the fact's value
    before the flop, and no encoding carries it (ASM-30, D-21).
    """
    base = STREET_DEFAULTS.get(street, STREET_DEFAULTS["preflop"])
    if board is None:
        board = BOARD_OF_STREET.get(street, ())
    if stacks is None:
        stacks = base["stacks"]
    if pot is None:
        pot = base["pot"]
    if to_call is None:
        to_call = base["to_call"]
    if limit is None:
        limit = base["limit"]
    if legal is None:
        legal = ACTIONS if to_call > 0 else ACTIONS[1:]
    record = {
        "street": street,
        "seat": tuple(seat),
        "hole": tuple(hole),
        "board": tuple(board),
        "stacks": tuple(stacks),
        "pot": pot,
        "to_call": to_call,
        "limit": tuple(limit),
        "history": list(history) if history is not None else [],
        "legal": tuple(legal),
        "hand_class": hand_class,
    }
    if extra:
        record.update(extra)
    return record


def with_facts(record, **changes):
    """A copy of ``record`` with the named facts replaced."""
    out = dict(record)
    out.update(changes)
    return out


#: The six-seat row's invented stacks: one entry per seat, in seat order.  The values
#: are the writer's own; only their *shape* -- six entries, never two -- is the
#: contract's (``seats.md`` §3, ``readout.md`` §2, ASM-28, ASM-44).
SIX_SEAT_STACKS = (100, 92, 84, 76, 68, 60)


def six_seat_readout(street="preflop", seat=(0, True), hole=("Td", "2c"), board=None,
                     stacks=None, pot=None, to_call=None, limit=None, history=None,
                     legal=None, hand_class=None, extra=None):
    """One invented **six-seat** readout: six stacks in seat order, a seat index in 0-5.

    A two-seat invented readout carries two stacks, and it must never reach a six-seat
    encoder except in the refusal case (`seats.md` §3, ASM-44): a case over the third
    row builds its readout here, so the per-seat facts are the row's own width.
    """
    if stacks is None:
        stacks = SIX_SEAT_STACKS
    return readout(street=street, seat=seat, hole=hole, board=board, stacks=stacks,
                   pot=pot, to_call=to_call, limit=limit, history=history, legal=legal,
                   hand_class=hand_class, extra=extra)


def shaped_readout(shape, **facts):
    """One invented readout whose two per-seat facts are of ``shape``'s seat count.

    ``stacks`` defaults to the shape's own count -- six on `six-seat-no-limit-100` and
    two on the two-seat rows -- so a loop over all three rows never hands a two-stack
    readout to a six-seat encoder by accident (`seats.md` §3, ASM-44).
    """
    if shape == THIRD_SHAPE:
        return six_seat_readout(**facts)
    return readout(**facts)


def without(record, *keys):
    """A copy of ``record`` with the named facts removed."""
    out = dict(record)
    for key in keys:
        out.pop(key, None)
    return out


def deep(record):
    """A deep copy of a readout, for the untouched-argument comparison."""
    return copy.deepcopy(record)


# --------------------------------------------------------------------------
# Stream state, for the purity cases (guardrails.md G5, ASM-2)
# --------------------------------------------------------------------------
def random_state():
    """The global `random` stream's state."""
    return random.getstate()


def numpy_state():
    """The global `numpy.random` stream's state, as plain comparable data."""
    state = numpy.random.get_state()
    return (state[0], state[1].tobytes(), int(state[2]), float(state[3]), state[4])


# --------------------------------------------------------------------------
# The seven names, fetched once
# --------------------------------------------------------------------------
class Surface:
    """The seven declared entry points of ``features``, fetched by name.

    A case starts with ``surface()``, so a missing package is one clean
    ``SurfaceAbsent`` failure before any assertion runs.
    """

    __slots__ = NINE

    def __init__(self):
        for name in NINE:
            setattr(self, name, ep(name))

    # -- the calls a case is written in ------------------------------------
    def encoder(self, name=FLAT):
        return self.build_encoder(name)

    def spec(self, name=FLAT):
        return self.observation_spec(self.encoder(name))

    def encode_with(self, name, record):
        return self.encode(self.encoder(name), record)

    def flat(self, record):
        return self.encode_with(FLAT, record)

    def tokens(self, record):
        return self.encode_with(TOKENS, record)


# --------------------------------------------------------------------------
# The base case
# --------------------------------------------------------------------------
class FeaturesCase(unittest.TestCase):
    """One battery case; every declared surface is reached through :func:`ep`."""

    def ep(self, name):
        return ep(name)

    def surface(self):
        return Surface()

    # -- the calls a case is written in -------------------------------------
    def encoder(self, name=FLAT):
        return ep("build_encoder")(name)

    def spec(self, name=FLAT):
        return ep("observation_spec")(self.encoder(name))

    def encode(self, name, record):
        return ep("encode")(self.encoder(name), record)

    def flat(self, record):
        return self.encode(FLAT, record)

    def tokens(self, record):
        return self.encode(TOKENS, record)

    def action_space(self):
        return ep("action_space")()

    def legal_indices(self, descriptors):
        return ep("legal_indices")(descriptors)

    def decode(self, index):
        return ep("decode_action")(index)

    # -- observations --------------------------------------------------------
    def shape_of(self, observation):
        """An observation's shape, as a tuple of plain ints."""
        self.assertTrue(
            hasattr(observation, "shape"),
            "encode must return a numpy array carrying a shape (encodings.md §3-§4)",
        )
        return tuple(int(value) for value in observation.shape)

    def assert_floats(self, got, expected, where):
        """One dense block (or vector) equals the values the design fixes.

        The comparison is to within float32's own resolution -- a value the design
        divides in float64 and ``encode`` writes as ``float32`` differs in the seventh
        decimal -- and still far tighter than a wrong divisor, a wrong offset or a
        missed one-hot, each of which differs by a whole fraction.
        """
        self.assertEqual(
            len(got), len(expected),
            "%s: %d slots, expected %d" % (where, len(got), len(expected)),
        )
        for position, (actual, wanted) in enumerate(zip(got, expected)):
            self.assertAlmostEqual(
                actual, wanted, delta=1e-5,
                msg="%s, slot %d: %r, the design fixes %r" % (where, position, actual, wanted),
            )

    def assert_ints(self, got, expected, where):
        """One token block (or vector) equals the ids the design fixes."""
        self.assertEqual(
            list(got), list(expected),
            "%s: %r, the design fixes %r" % (where, list(got), list(expected)),
        )

    # -- refusals -----------------------------------------------------------
    def refusal(self, fn, *args):
        """Call an entry point that must refuse, and return the raised error.

        The battery asserts that a refusal *happens*, that its message names the
        violated contract, and that it is not one of this battery's own failures
        -- never that it is an instance of a particular class
        (``docs/L3/features/errors.md`` §2: the classes are not surface).
        """
        try:
            fn(*args)
        except SurfaceAbsent:
            raise
        except Exception as exc:  # the refusal the contract asks for
            self.assertTrue(
                str(exc).strip(),
                "%s(%r) refused without a message naming the violated contract "
                "(errors.md §3)" % (getattr(fn, "__name__", fn), args),
            )
            return exc
        self.fail(
            "%s(%r) was accepted, and the contract refuses it (errors.md §3, §4)"
            % (getattr(fn, "__name__", fn), args)
        )

    def assert_names(self, exc, *words):
        """The refusal's message names the violated contract, in the words the design uses.

        ``errors.md`` §3 fixes the message's content, not its prose: the entry
        point's own name, the argument's or field's name, and the offending value
        where the canonical message prints it.  The match is a plain substring
        match, so it pins the *words* and not a sentence.
        """
        text = str(exc)
        for word in words:
            self.assertIn(
                str(word), text,
                "the refusal must name %r in the message it raises (errors.md §3): %r"
                % (str(word), text),
            )

    def refuses(self, fn, *args, words=()):
        """A call the contract refuses: it raises, and its message names the contract."""
        exc = self.refusal(fn, *args)
        self.assert_names(exc, *words)
        return exc


if __name__ == "__main__":  # pragma: no cover - support module, not a case file
    unittest.main()
