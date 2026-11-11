"""Support for the L2 integration battery of the ``features`` module (D-11, D-13).

The battery drives the seven entry points of ``docs/L2/features/surface.md`` (Rev 1)
and ``docs/L2/features/encodings.md`` (Rev 1) **at the module join**: every readout a
case encodes is a real readout of the built ``engine`` — ``engine.new_hand`` then
``engine.readout`` — and every descriptor a case applies was decoded by ``features``
and handed to ``engine.apply_action``.  A case therefore asserts the contract the two
modules exchange and never a shape the battery built for itself
(``docs/L1/battery.md`` §2, §5, D-13).

This module holds what the cases share and nothing else:

* the ``src/`` import path, so the battery runs standalone and needs no ``conftest.py``
  (the ``harness`` module owns that file);
* the battery's **invented instances** — the seeds, the undeclared encoding name, the
  invented descriptor, the invented history entry and the invented readout key below
  appear in no design document (D-15, ``docs/L1/battery.md`` §4), so each ``general``
  row of ``docs/L1/e2e-surface.md`` §5.2 carries an instance of the writer's own;
* tolerant readers for what the design leaves free — a descriptor's spelling, a
  fact's container, a refusal's error class — so a case asserts the contract and never
  a spelling this battery invented (``docs/L1/e2e-surface.md`` §2), and one strict
  reader for what §1 fixes: a refusal's **message** names the entry point and what was
  violated, so an internal lookup error does not pass as this module's named refusal
  (``docs/L2/features/surface.md`` §1);
* the **far-end mutation** that proves one carried fact reaches the observation
  (§``far_end_changes``), and the small vocabulary of calls the cases are written in.

It reads ``features`` through its seven names and ``engine`` through ``new_hand``,
``readout``, ``legal_actions``, ``apply_action`` and ``is_terminal``, and it reaches
below neither (``docs/L2/features/README.md`` §3, ``docs/L2/engine/surface.md`` §1).
Nothing here names an ``src/features/`` submodule, a private constant, a block offset,
a bucket edge, a card id or an error class: those are ``tests/features/``'s subject
(``docs/L3/features/README.md`` §3, §5, D-11).

The file is named ``_join_support`` rather than ``_support`` on purpose: pytest's
prepend mode puts this directory on ``sys.path``, and ``tests/integration/engine/``
already owns a top-level ``_support`` module, so a shared name would make one battery
import the other's plumbing when both directories are collected in one session.
"""

from __future__ import annotations

import importlib
import numbers as _numbers
import os
import re
import sys
import unittest
from collections.abc import Mapping

import numpy

# ---------------------------------------------------------------------------
# The declared surface, by name (surface.md §1, layout.md §2 of L3)
# ---------------------------------------------------------------------------
FEATURES = "features"
ENGINE = "engine"

ENTRY_POINTS = (
    "encodings",
    "build_encoder",
    "observation_spec",
    "encode",
    "action_space",
    "legal_indices",
    "decode_action",
)

# encodings.md §1-§4, surface.md §5: the two declared encodings, and the six keys of
# the spec record each one is declared by.
ENCODING_NAMES = ("flat-numeric", "card-tokens")
SPEC_KEYS = ("representation", "kind", "fields", "shape", "dtype", "vocabulary")
KINDS = {"flat-numeric": "dense-numeric", "card-tokens": "token-sequence"}

# The **default** shape's declared widths: the pair a no-shape encoder declares, and the
# width a kind's declared observation size stays at (shapes.md §8, ASM-44).
SHAPES = {"flat-numeric": (203,), "card-tokens": (40,)}

# The three declared shapes, and each one's two widths.  The 127 dense slots and the 12
# tokens that no seat count touches are the encoding's; the `seat` and `stacks` blocks are
# one slot per seat, so the slots before the history are `127 + 2 x seats` and
# `12 + 2 x seats`, and the block that follows them is 3 x the shape's capacity (dense) or
# the capacity itself (token).  So 131 + 3 x 24 = 203 and 16 + 24 = 40 on
# `fixed-limit-20`, 131 + 3 x 66 = 329 and 16 + 66 = 82 on `no-limit-100`, and
# 139 + 3 x 98 = 433 and 24 + 98 = 122 on `six-seat-no-limit-100` (capacity.md §2,
# shapes.md §8, seats.md §3, ASM-42, ASM-44).  `engine.game_shapes()` now publishes
# `seats` and `history` on every row, so a case derives those widths from the engine's own
# catalogue (`dense_width` / `token_width`) and this table is only the battery's second
# statement of the same arithmetic (D-13).
DEFAULT_SHAPE = "fixed-limit-20"
SECOND_SHAPE = "no-limit-100"
THIRD_SHAPE = "six-seat-no-limit-100"
SHAPE_NAMES = (DEFAULT_SHAPE, SECOND_SHAPE, THIRD_SHAPE)
CAPACITY = {DEFAULT_SHAPE: 24, SECOND_SHAPE: 66, THIRD_SHAPE: 98}
SEATS = {DEFAULT_SHAPE: 2, SECOND_SHAPE: 2, THIRD_SHAPE: 6}
SHAPES_BY_CATALOGUE = {
    DEFAULT_SHAPE: {"flat-numeric": (203,), "card-tokens": (40,)},
    SECOND_SHAPE: {"flat-numeric": (329,), "card-tokens": (82,)},
    THIRD_SHAPE: {"flat-numeric": (433,), "card-tokens": (122,)},
}
DTYPES = {"flat-numeric": "float32", "card-tokens": "int32"}
VOCABULARIES = {"flat-numeric": None, "card-tokens": 96}
# The token vocabulary is the shape's: 96 ids on the two-seat rows and 102 on the
# six-seat one, whose seat block emits six ids of its own above every id the other rows
# use (card-tokens.md §6, seats.md §3, capacity.md §4, ASM-44).
TOKEN_VOCABULARY = {DEFAULT_SHAPE: 96, SECOND_SHAPE: 96, THIRD_SHAPE: 102}
SEAT_TOKEN_BASE = 96
SIX_SEAT_SEAT_IDS = tuple(range(SEAT_TOKEN_BASE, SEAT_TOKEN_BASE + SEATS[THIRD_SHAPE]))
#: The dense and token slots before the history that no seat count touches (capacity.md
#: §2, ASM-44).
SEAT_INVARIANT_DENSE_SLOTS = 127
SEAT_INVARIANT_TOKEN_SLOTS = 12


def dense_width(row):
    """`127 + 2 x seats + 3 x history` from one `engine.game_shapes()` row.

    The engine publishes both numbers this module restates -- `seats` and `history` --
    so a case can compute the width the row implies and compare it with the width the
    encoder declares, instead of restating a capacity the engine did not publish
    (capacity.md §2, §5, shapes.md §2, §8, ASM-42, D-13).
    """
    return (SEAT_INVARIANT_DENSE_SLOTS + 2 * int(row["seats"])
            + 3 * int(row["history"]))


def token_width(row):
    """`12 + 2 x seats + history` from one `engine.game_shapes()` row (capacity.md §2)."""
    return (SEAT_INVARIANT_TOKEN_SLOTS + 2 * int(row["seats"])
            + int(row["history"]))



# environment.md §2 (engine): the readout's closed eleven facts, in the declared order,
# and the nine an observation carries — the eleven less `legal` and less D-21's
# `hand_class`, which no encoding carries (encodings.md §2, ASM-30, D-21).
READOUT_FACTS = (
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
CARRIED_FACTS = tuple(
    fact for fact in READOUT_FACTS if fact not in ("legal", "hand_class")
)

# surface.md §2: the three-index vocabulary, and the spelling both modules share.
ACTION_INDICES = (0, 1, 2)
ACTION_NAMES = ("fold", "check-call", "raise")

# environment.md §2 (engine): the four streets and the board each one reveals.
BOARD_LENGTH = {"preflop": 0, "flop": 3, "turn": 4, "river": 5}

# ---------------------------------------------------------------------------
# The battery's invented instances (D-15, battery.md §4)
# ---------------------------------------------------------------------------
# None of these seeds, names or entries appears in docs/L1, docs/L2 or docs/L3, and
# none is one of the seeds tests/e2e/_surface.py uses; they are the writer's own,
# invented from the declared surface alone.  Each drives one `general` row of
# e2e-surface.md §5.2: encode, legal_indices and decode_action.
SEED_ENCODE = 20483          # the `encode` row's instance
SEED_MASK = 61879            # the `legal_indices` row's instance
SEED_DECODE = 73391          # the `decode_action` row's instance
SEED_PARITY = 51229          # the deal R1's and R2's runs both play (D-7)
SEED_SAMPLE = 30671          # the second walk the samples are gathered from
SAMPLE_SEEDS = (SEED_ENCODE, SEED_SAMPLE)

UNDECLARED_ENCODING = "quantised-bucket"   # names no declared encoding
UNDECLARED_DESCRIPTOR = "double-down"      # names no vocabulary action
INVENTED_ENTRY = "preflop seat 0 teleports"  # outside the history grammar
INVENTED_KEY = "table_mood"                # a readout key the encoding does not carry

# The two policies the battery walks a hand with: continue (check or call) and take
# the last legal action (raise wherever raising is legal).
CHECK_CALL = "check-call"
RAISE = "raise"

# surface.md §8 (engine): a hand that has not ended after 200 decisions is a defect.
DECISION_BOUND = 200


# ---------------------------------------------------------------------------
# Import-path plumbing: the battery runs without a conftest
# ---------------------------------------------------------------------------
def repo_root():
    """The repository root: this file is ``<root>/tests/integration/features/``."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(os.path.dirname(here)))


def src_dir():
    return os.path.join(repo_root(), "src")


_CACHE = {}


def module(name):
    """One of the two packages, or a failure naming the absent surface."""
    package = _CACHE.get(name)
    if package is None:
        src = src_dir()
        if src not in sys.path:
            sys.path.insert(0, src)
        try:
            package = importlib.import_module(name)
        except Exception as exc:  # not importable yet, or broken on import
            raise AssertionError(
                "surface absent: the declared module %r is not importable from %s "
                "(%s: %s)" % (name, src, type(exc).__name__, exc)
            ) from exc
        _CACHE[name] = package
    return package


def entry(name, entry_point):
    """One declared entry point of one package, or a failure naming the missing name."""
    package = module(name)
    try:
        return getattr(package, entry_point)
    except AttributeError:
        raise AssertionError(
            "surface absent: %s.%s is not a module-level name of the package "
            "(surface.md §1)" % (name, entry_point)
        ) from None


# ---------------------------------------------------------------------------
# Tolerant readers for the shapes the design leaves free
# ---------------------------------------------------------------------------
def is_number(value):
    return isinstance(value, _numbers.Number) and not isinstance(value, (bool, complex))


def is_count(value):
    """Whether a value is an integer (a ``bool`` is not a count, nor an index)."""
    return isinstance(value, _numbers.Integral) and not isinstance(value, bool)


def is_mapping(value):
    return isinstance(value, Mapping)


def is_indexable(value):
    """Whether a value is an ordered, indexable sequence (not a string or a set)."""
    if isinstance(value, (str, bytes, set, frozenset)):
        return False
    return hasattr(value, "__len__") and hasattr(value, "__getitem__")


def is_array(value):
    """Whether a value is one numpy array — the observation of an encoding."""
    return isinstance(value, numpy.ndarray)


def numbers_in(obj, _depth=0):
    """Every number in an observable value, in traversal order (``bool`` excluded)."""
    if _depth > 24:
        return []
    if isinstance(obj, bool):
        return []
    if is_number(obj):
        return [obj]
    if isinstance(obj, Mapping):
        out = []
        for value in obj.values():
            out.extend(numbers_in(value, _depth + 1))
        return out
    if isinstance(obj, (list, tuple, set, frozenset)):
        out = []
        for value in obj:
            out.extend(numbers_in(value, _depth + 1))
        return out
    return []


def integers_in(obj, _depth=0):
    """Every integer anywhere in a value, **mapping keys included** (``bool`` excluded).

    ``action_space``'s three indices are the record's keys, so a reader that walked
    values alone would find no integer at all.  The vocabulary is "the set of integers
    it finds anywhere in the record" (``battery.md`` §3 FAM-2 case FAM-2.9,
    ``surface.md`` §7), which is this function.
    """
    if _depth > 24:
        return []
    if isinstance(obj, bool):
        return []
    if is_count(obj):
        return [int(obj)]
    if is_number(obj):
        return []
    if isinstance(obj, Mapping):
        out = []
        for key, value in obj.items():
            out.extend(integers_in(key, _depth + 1))
            out.extend(integers_in(value, _depth + 1))
        return out
    if isinstance(obj, (list, tuple, set, frozenset)):
        out = []
        for value in obj:
            out.extend(integers_in(value, _depth + 1))
        return out
    return []


def strings_in(obj, _depth=0):
    """Every string in an observable value, in traversal order."""
    if _depth > 24:
        return []
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, bytes):
        return []
    if isinstance(obj, Mapping):
        out = []
        for value in obj.values():
            out.extend(strings_in(value, _depth + 1))
        return out
    if isinstance(obj, (list, tuple, set, frozenset)):
        out = []
        for value in obj:
            out.extend(strings_in(value, _depth + 1))
        return out
    return []


def flatten_text(obj, _depth=0):
    """Every key and every leaf of an observable value, as one lowercase string."""
    parts = []

    def walk(value, depth):
        if depth > 24:
            return
        if isinstance(value, Mapping):
            for key, inner in value.items():
                parts.append(str(key))
                walk(inner, depth + 1)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for inner in value:
                walk(inner, depth + 1)
        else:
            parts.append(str(value))

    walk(obj, _depth)
    return " ".join(parts).lower()


def token(value):
    """A value reduced to its letters and digits: ``check-call`` == ``check call``."""
    return "".join(ch for ch in flatten_text(value) if ch.isalnum())


def mentions(text, word):
    """Whether ``word`` appears in ``text`` as a standalone token.

    Used to read a refusal's message: ``surface.md`` §1 requires the message to name
    the violated contract, so the entry point's name has to read as that name — the
    word ``encode`` inside ``encode(readout): ...`` — and never as a substring some
    other word happens to carry.  Case-insensitive, and blind to punctuation, because
    the message's wording is the implementation's (``docs/L1/e2e-surface.md`` §2).
    """
    pattern = r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape("%s" % (word,))
    return re.search(pattern, "%s" % (text,), re.IGNORECASE) is not None


def canonical(obj, _depth=0):
    """A hashable, order-stable canonical form of an observable value.

    Used to compare two returned records without assuming how they are nested, and to
    compare a readout against a snapshot taken before a call.
    """
    if _depth > 24:
        return ("deep", str(obj))
    if obj is None or isinstance(obj, (bool, int, float, str, bytes)):
        return obj
    if isinstance(obj, Mapping):
        return tuple(
            sorted((str(key), canonical(value, _depth + 1)) for key, value in obj.items())
        )
    if isinstance(obj, (list, tuple)):
        return tuple(canonical(value, _depth + 1) for value in obj)
    if isinstance(obj, (set, frozenset)):
        return tuple(sorted((canonical(value, _depth + 1) for value in obj), key=repr))
    if hasattr(obj, "tolist"):
        try:
            return canonical(obj.tolist(), _depth + 1)
        except Exception:
            pass
    if hasattr(obj, "__len__") and hasattr(obj, "__getitem__"):
        try:
            return tuple(canonical(obj[i], _depth + 1) for i in range(len(obj)))
        except Exception:
            pass
    return ("object", type(obj).__name__, str(obj))


def is_plain(value, _depth=0):
    """Whether a returned value is plain data a report's header may quote.

    surface.md §1: every returned value is plain data except the opaque encoder — a
    mapping, a sequence of names or indices, or the observation array itself.
    """
    if _depth > 12:
        return False
    if value is None or isinstance(value, (bool, int, float, str)):
        return True
    if isinstance(value, Mapping):
        return all(
            isinstance(key, (str, int)) and is_plain(inner, _depth + 1)
            for key, inner in value.items()
        )
    if isinstance(value, (list, tuple)):
        return all(is_plain(inner, _depth + 1) for inner in value)
    return False


def seat_fact(value):
    """The acting seat's index and its button flag, from the readout's ``seat`` fact.

    environment.md §2 (engine) fixes the content and leaves the container free, so a
    tuple, a list or a mapping all read here.
    """
    numbers = numbers_in(value)
    flags = [item for item in _bools_in(value)]
    if not numbers or not flags:
        raise AssertionError(
            "the readout's seat fact must carry the acting seat's index and whether it "
            "holds the button (engine/environment.md §2); got %r" % (value,)
        )
    return int(numbers[0]), flags[0]


def _bools_in(obj, _depth=0):
    if _depth > 24:
        return []
    if isinstance(obj, bool):
        return [obj]
    if isinstance(obj, Mapping):
        out = []
        for value in obj.values():
            out.extend(_bools_in(value, _depth + 1))
        return out
    if isinstance(obj, (list, tuple, set, frozenset)):
        out = []
        for value in obj:
            out.extend(_bools_in(value, _depth + 1))
        return out
    return []


def descriptor_kind(descriptor):
    """Which vocabulary action a descriptor names, read from its stable text.

    surface.md §2 fixes the three actions and the engine's descriptors print stably,
    so the text is the one spelling a battery reads without reaching below an entry
    point.  ``None`` when the text names none of the three.
    """
    text = flatten_text(descriptor)
    if "fold" in text:
        return "fold"
    if "raise" in text or "bet" in text:
        return "raise"
    if "call" in text or "check" in text:
        return "check-call"
    return None


def descriptors(legal, what):
    """An ordered descriptor sequence, as a list, or a failure naming it."""
    if not is_indexable(legal):
        raise AssertionError(
            "%s must be an ordered, indexable sequence of descriptors "
            "(engine/surface.md §6); got %r" % (what, legal)
        )
    return [legal[position] for position in range(len(legal))]


def pick_descriptor(legal, kind):
    """One descriptor of a policy's own choosing, taken from the engine's sequence."""
    sequence = descriptors(legal, "a decision's legal descriptors")
    for descriptor in sequence:
        if descriptor_kind(descriptor) == kind:
            return descriptor
    return sequence[-1]


def same_observation(left, right):
    """Whether two observations are one observation value for value."""
    if not is_array(left) or not is_array(right):
        return False
    if tuple(left.shape) != tuple(right.shape):
        return False
    return bool(numpy.array_equal(left, right))


def all_finite(observation):
    """Whether every element of one observation is a finite number.

    ``flat-numeric`` divides and keeps the magnitude instead of bucketing it, so every
    element it emits is a finite number a dense layer can multiply
    (``encodings.md`` §3).
    """
    if not is_array(observation):
        return False
    try:
        return bool(numpy.isfinite(observation).all())
    except TypeError:  # not a numeric dtype at all
        return False


# ---------------------------------------------------------------------------
# The cards, and the far-end mutations one carried fact at a time
# ---------------------------------------------------------------------------
def card_pool(readouts):
    """Every card the battery has actually seen, in the engine's own spelling.

    The battery never writes a card itself: a card's spelling is the engine's
    (``engine/environment.md`` §2, ``docs/L3/engine/readout.md`` §3), so a replacement
    card is taken from a real readout and this battery invents none.
    """
    pool = []
    for readout in readouts:
        for card in tuple(readout["hole"]) + tuple(readout["board"]):
            if card not in pool:
                pool.append(card)
    return pool


def spare_card(readout, pool):
    """One real card that is neither on this readout's board nor in its hole."""
    visible = set(token(card) for card in tuple(readout["hole"]) + tuple(readout["board"]))
    for card in pool:
        if token(card) not in visible:
            return card
    raise AssertionError(
        "the battery needs one card that is on neither the board nor in the hole; the "
        "walk saw %d distinct cards, all of them visible at %r" % (len(pool), readout)
    )


def far_end_changes(readout, pool, references):
    """The one-fact changes of FAM-2.10, fact by fact.

    Each carried fact is moved to the **far end of its own declared range** — the pot
    to the other end of the 40 chips a hand begins with, the amount to call to zero or
    well past the small blind, the stacks to one seat holding all of them, the bet size
    to the other of the two fixed sizes, the history from empty to a real entry or the
    other way — and the observation must change.  A change at the far end is what an
    encoding cannot hide: a bucketing coarse enough to map the bottom of a range and
    its top to one id would leave the ids that encoding declares unreachable
    (``encodings.md`` §1–§4), and no fact would be carried at all.

    A card is replaced by a real card the walk has seen and this readout does not show
    (:func:`spare_card`), never by a card the battery spells.  Nothing here encodes a
    block offset, a slot index, a bucket edge or a card id: the values are drawn from
    the readout and from the engine's own declared ranges, so a case built on this
    helper asserts that a fact is carried and never how it is spelled
    (``docs/L1/battery.md`` §2, D-11).
    """
    changes = {}

    # `street`: one of the four, and never the one it already is.
    changes["street"] = "river" if readout["street"] != "river" else "preflop"

    # `seat`: the other seat, with the other button flag.
    index, button = seat_fact(readout["seat"])
    changes["seat"] = (1 - index, not button)

    # `hole`: the same second card, one different first card.
    changes["hole"] = (spare_card(readout, pool), tuple(readout["hole"])[1])

    # `board`: one different revealed card, or three real cards where none is dealt.
    board = tuple(readout["board"])
    if board:
        changes["board"] = (spare_card(readout, pool),) + board[1:]
    else:
        changes["board"] = tuple(_first_board(references, 3))

    # `stacks`: one seat holds every chip behind, the other none.
    total = sum(int(value) for value in readout["stacks"])
    changes["stacks"] = (0, total) if int(readout["stacks"][0]) != 0 else (total, 0)

    # `pot`: the far end of the 40 chips a hand begins with.
    changes["pot"] = 0 if int(readout["pot"]) > 20 else 40

    # `to_call`: free, or the twenty chips a seat begins a hand with.
    changes["to_call"] = 0 if int(readout["to_call"]) else 20

    # `limit`: the other bet size in force, and the other raise count.
    bet, raises = int(readout["limit"][0]), int(readout["limit"][1])
    changes["limit"] = (4 if bet == 2 else 2, 0 if raises else 1)

    # `history`: the empty list, or one real entry the walk really made.
    changes["history"] = [] if readout["history"] else list(_first_history(readout, references))

    return changes


def _first_board(references, length):
    for readout in references:
        if len(tuple(readout["board"])) == length:
            return tuple(readout["board"])
    raise AssertionError(
        "the battery needs a real %d-card board to move an undealt board to; the "
        "samples hold boards of length %r"
        % (length, sorted({len(tuple(readout["board"])) for readout in references}))
    )


def _first_history(readout, references):
    """One real history entry, taken from a readout whose street this one shares."""
    for other in references:
        if other["history"] and readout["street"] == other["street"]:
            return list(other["history"])[:1]
    for other in references:
        if other["history"]:
            return list(other["history"])[:1]
    raise AssertionError(
        "the battery needs one real history entry to move an empty history to; no "
        "sampled readout carries one"
    )


class Step:
    """One decision of a walked hand: its handle, its facts, and its legal set."""

    __slots__ = ("hand", "readout", "legal")

    def __init__(self, hand, readout, legal):
        self.hand = hand
        self.readout = readout
        self.legal = legal


# ---------------------------------------------------------------------------
# The base case the battery is written on
# ---------------------------------------------------------------------------
class JoinCase(unittest.TestCase):
    """One battery case, written in the seven names and the engine's five calls."""

    # -- the seven names of `features` -------------------------------------
    def ep(self, name):
        """One entry point of the module under test."""
        return entry(FEATURES, name)

    def encodings(self):
        return self.ep("encodings")()

    def build_encoder(self, name):
        return self.ep("build_encoder")(name)

    def encoder(self, name):
        """One encoder, from the only entry point that builds one (surface.md §4)."""
        return self.build_encoder(name)

    def observation_spec(self, encoder):
        return self.ep("observation_spec")(encoder)

    def spec(self, name):
        """The spec record of one declared encoding, read through both entry points."""
        return self.observation_spec(self.encoder(name))

    def encode(self, encoder, readout):
        return self.ep("encode")(encoder, readout)

    def action_space(self):
        return self.ep("action_space")()

    def legal_indices(self, legal):
        return self.ep("legal_indices")(legal)

    def decode_action(self, index):
        return self.ep("decode_action")(index)

    # -- the engine's side of the join -------------------------------------
    def new_hand(self, seed):
        return entry(ENGINE, "new_hand")(seed)

    def readout(self, hand):
        return entry(ENGINE, "readout")(hand)

    def legal_actions(self, hand):
        return entry(ENGINE, "legal_actions")(hand)

    def apply_action(self, hand, action):
        return entry(ENGINE, "apply_action")(hand, action)

    def is_terminal(self, hand):
        return entry(ENGINE, "is_terminal")(hand)

    # -- walks -------------------------------------------------------------
    def walk(self, seed, kind=CHECK_CALL, limit=DECISION_BOUND):
        """Drive one real hand to its end, taking the descriptor ``kind`` names.

        Returns the decisions as :class:`Step` values — each carrying the handle it was
        read at, which the engine leaves unchanged when a step is applied — and the
        final handle.  A policy's choice is taken from the engine's own descriptors, so
        a walk never depends on the module this battery judges.
        """
        hand = self.new_hand(seed)
        steps = []
        while len(steps) < limit and not self.is_terminal(hand):
            readout = self.readout(hand)
            legal = self.legal_actions(hand)
            steps.append(Step(hand, readout, legal))
            hand = self.apply_action(hand, pick_descriptor(legal, kind))
        return steps, hand

    def walks(self):
        """The walks the samples are gathered from, cached for one case."""
        cached = getattr(self, "_walks", None)
        if cached is None:
            cached = []
            for seed in SAMPLE_SEEDS:
                for kind in (CHECK_CALL, RAISE):
                    cached.append(self.walk(seed, kind))
            self._walks = cached
        return cached

    def samples(self):
        """Real readouts at every board length and history state the game produces."""
        cached = getattr(self, "_samples", None)
        if cached is None:
            cached = [step.readout for steps, _hand in self.walks() for step in steps]
            self._samples = cached
        return cached

    def by_street(self):
        """The first sampled readout of each street, keyed by the street name."""
        found = {}
        for readout in self.samples():
            found.setdefault(readout["street"], readout)
        return found

    # -- observations ------------------------------------------------------
    def declared_shape(self, spec):
        shape = spec["shape"]
        if not is_indexable(shape):
            raise AssertionError(
                "the spec's shape must be a tuple of integers (surface.md §5); got %r"
                % (shape,)
            )
        return tuple(int(value) for value in shape)

    def assert_observation(self, encoding, spec, observation):
        """Assert one observation is the one array the spec declares (surface.md §6)."""
        self.assertTrue(
            is_array(observation),
            "%r must encode to one numpy array (surface.md §6); got %r"
            % (encoding, type(observation).__name__),
        )
        shape = self.declared_shape(spec)
        self.assertEqual(
            tuple(observation.shape),
            shape,
            "%r returned a %r observation, and its spec declares %r "
            "(surface.md §5, §6)" % (encoding, tuple(observation.shape), shape),
        )
        self.assertEqual(
            observation.dtype,
            numpy.dtype(str(spec["dtype"])),
            "%r returned a %r observation, and its spec declares dtype %r "
            "(surface.md §5, §6)" % (encoding, observation.dtype, spec["dtype"]),
        )

    # -- refusals ----------------------------------------------------------
    def refusal(self, call, what):
        """The exception ``call`` was refused by, or a failure if it returned.

        surface.md §1: an invalid argument is refused by an error, and no entry point
        coerces a value, substitutes a default, swallows an error or returns part of a
        record.  The class is free (``docs/L1/e2e-surface.md`` §2), so only the refusal
        itself is asserted here.
        """
        try:
            returned = call()
        except Exception as exc:  # the refusal itself
            return exc
        self.fail(
            "%s must be refused, not accepted (surface.md §1); it returned %r"
            % (what, returned)
        )

    def assert_refused(self, call, what, words=()):
        """Assert ``call`` is refused by an error that names the violated contract.

        surface.md §1: an invalid argument is refused by raising an error that names
        the violated contract, and no entry point coerces a value, substitutes a
        default, swallows an error or returns part of a record.  The error's class is
        free (``docs/L1/e2e-surface.md`` §2), so only the refusal and its text are
        asserted.
        """
        exc = self.refusal(call, what)
        text = "%s: %s" % (type(exc).__name__, exc)
        if words and not any(word.lower() in text.lower() for word in words):
            self.fail(
                "%s must be refused by an error that names the violated contract "
                "(surface.md §1); it raised %s" % (what, text)
            )
        return exc

    def assert_named_refusal(self, call, entry_point, what, words=()):
        """Assert ``call`` is refused by a message naming the entry point and the violation.

        ``docs/L2/features/surface.md`` §1 and §6–§9 fix more than "an error was
        raised": the refusal names the violated contract — *which* entry point refused
        and *what* it refused — so a case about a named refusal is not satisfied by an
        internal lookup error that happens to repeat the argument's text.  Only the
        message is read, never the type: the class stays free
        (``docs/L1/e2e-surface.md`` §2).

        ``entry_point`` is one of the seven declared names and ``words`` are the parts
        of the violation the caller's contract states, so nothing below an entry point
        is named here.
        """
        exc = self.refusal(call, what)
        message = "%s" % (exc,)
        text = "%s: %s" % (type(exc).__name__, message)
        absent = [
            word for word in (entry_point,) + tuple(words) if not mentions(message, word)
        ]
        if absent:
            self.fail(
                "%s must be refused by an error whose message names the violated "
                "contract: the entry point %r and what was violated, %r (surface.md §1); "
                "it raised %s"
                % (what, entry_point, ", ".join(repr(word) for word in absent), text)
            )
        return exc
