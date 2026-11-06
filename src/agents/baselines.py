"""`baselines`, `build_baseline` and the three fixed rules (`baselines.md` §1-§6).

`random`, `always-call` and `oracle` are D-6's three fixed standards: none of them
learns from a match, none has a trainable parameter (`params: 0`), and none advances a
state, so each is a function of the decision it is handed.  `random`'s draw is keyed by
the decision (`baselines.md` §2) because a uniform draw over each decision's legal
indices cannot come from a stream position once the order of decisions is free.

`engine` is imported **inside** the oracle's policy and nowhere else: `engine`'s
modules hold `pokerkit` at module level, and an eager import would leak it into
`sys.modules` (`backends.md` §4, `README.md` §6).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from numbers import Integral, Real

import numpy

import features

from .errors import InvalidReadout, InvalidSeed, UnknownBaseline

NAMES = ("random", "always-call", "oracle")

#: The board sizes a decision declares: no public card, the flop, the turn, the river
#: (`README.md` §7).
BOARD_SIZES = (0, 3, 4, 5)

#: The oracle's pinned sample count: the count `baselines()` declares and the count
#: `build_baseline("oracle", seed)` queries, so a caller re-issues the same query
#: (`baselines.md` §5, ASM-4).
EQUITY_SAMPLES = 257

#: `baselines.md` §2's payload tag.
PAYLOAD = b"pypoker-agents/baseline-random/v1"

#: The facts the canonical spelling and the inequality read, in the readout's order.
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
)


def _record(name, rule):
    """One baseline's catalogue value (`baselines.md` §6)."""
    return {"name": name, "rule": rule, "params": 0}


def baselines():
    """The three fixed baselines, keyed in `random`, `always-call`, `oracle` order."""
    return {
        "random": _record(
            "random",
            "a uniform draw over the decision's legal indices, keyed by the decision "
            "and the baseline's seed",
        ),
        "always-call": _record(
            "always-call",
            "check/call whenever that is legal, never fold, and the minimum legal "
            "completion when raising is the only option",
        ),
        "oracle": dict(
            _record(
                "oracle",
                "check/call when the hand's equity is at least the pot odds "
                "to_call / (pot + to_call), and fold when that inequality fails and "
                "folding is legal",
            ),
            equity_samples=EQUITY_SAMPLES,
        ),
    }


def _malformed(fact, wanted, value):
    """The refusal of one readout fact that is not of the shape `baselines.md` §1 fixes."""
    return InvalidReadout(
        "policy(readout): the readout's %r must be %s, got %r" % (fact, wanted, value)
    )


def _entries(fact, value, wanted):
    """One readout fact that is a sequence of entries: never a string, never a mapping."""
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Iterable):
        raise _malformed(fact, wanted, value)
    return tuple(value)


def _pair(fact, wanted, value):
    """One readout fact that is a pair: two entries, and never a string or a mapping."""
    entries = _entries(fact, value, wanted)
    if len(entries) != 2:
        raise _malformed(fact, wanted, value)
    return entries


def _amounts(fact, wanted, value):
    """One readout fact that is a pair of numbers: two amounts, not spellings."""
    entries = _pair(fact, wanted, value)
    for entry in entries:
        if isinstance(entry, bool) or not isinstance(entry, Real):
            raise _malformed(fact, wanted, value)
    return entries


def _counted(fact, value):
    """One readout fact that is an integer: a flag, a float or a string is refused, never `int()`-ed."""
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise _malformed(fact, "an integer", value)
    return int(value)


def _cards(fact, wanted, sizes, value):
    """One readout fact that names a fixed number of cards: the count is checked, no card parsed."""
    cards = _entries(fact, value, wanted)
    if len(cards) not in sizes:
        raise _malformed(fact, wanted, len(cards))
    return cards


def _readout(value):
    """One readout mapping whose facts have the shapes `baselines.md` §1 fixes.

    A readout is the ten facts of `README.md` §7 or it is refused: a policy that
    defaulted a malformed fact would answer a decision nobody described, and an
    `int("3")` on the way to one would invent it (`surface.md` §1, `errors.md` §2-§3).
    Every shape is checked here, before any rule reads a fact, and as this module's
    own `InvalidReadout` named `policy(readout)`.  Nothing parses a card's spelling:
    the counts and the shapes are checked and the cards only counted, so no `engine`
    parser is imported to inspect one (`README.md` §6).
    """
    if not isinstance(value, Mapping):
        raise InvalidReadout(
            "policy(readout): the readout must be a mapping of the decision's facts, "
            "got %s" % type(value).__name__
        )
    for fact in FACTS:
        if fact not in value:
            raise InvalidReadout(
                "policy(readout): the readout is missing %r, which the rule needs"
                % (fact,)
            )
    pair = "a pair of a seat index and its button flag"
    seat = _pair("seat", pair, value["seat"])
    if isinstance(seat[0], bool) or not isinstance(seat[0], Integral):
        raise _malformed("seat", pair, value["seat"])
    _amounts("stacks", "one number per seat", value["stacks"])
    _amounts("limit", "a pair of numbers", value["limit"])
    _counted("pot", value["pot"])
    _counted("to_call", value["to_call"])
    hole = _cards("hole", "two cards", (2,), value["hole"])
    board = _cards("board", "0, 3, 4 or 5 cards", BOARD_SIZES, value["board"])
    _entries("history", value["history"], "a sequence of entries")
    seen = set()
    for card in hole + board:
        spelling = str(card)
        if spelling in seen:
            raise InvalidReadout(
                "policy(readout): the readout's 'hole' and 'board' must name distinct "
                "cards, got %r twice" % (spelling,)
            )
        seen.add(spelling)
    return value


def _indices(legal_actions):
    """The decision's legal indices, `features.legal_indices`' own sequence."""
    return tuple(int(index) for index in features.legal_indices(legal_actions))


def _canonical(readout, indices):
    """One decision as the one UTF-8 string `baselines.md` §2 canonicalises it to.

    The eight spellings, joined with `"|"`: the street, the seat as `"<index>:<0|1>"`,
    the hole and the board comma-joined, the stacks and the limit as their integers
    comma-joined, the pot and the amount to call as integers, the history's entries
    semicolon-joined, and the decision's legal indices comma-joined.  The readout has
    already been validated by `_readout`, so no fact is defaulted here.
    """
    seat = readout["seat"]
    stacks_and_limit = [int(amount) for amount in readout["stacks"]] + [
        int(amount) for amount in readout["limit"]
    ]
    pot_and_call = [int(readout["pot"]), int(readout["to_call"])]
    parts = (
        str(readout["street"]),
        "%d:%d" % (int(seat[0]), 1 if seat[1] else 0),
        ",".join(str(card) for card in readout["hole"]),
        ",".join(str(card) for card in readout["board"]),
        ",".join(str(amount) for amount in stacks_and_limit),
        ",".join(str(amount) for amount in pot_and_call),
        ";".join(str(entry) for entry in readout["history"]),
        ",".join(str(index) for index in indices),
    )
    return "|".join(parts)


def _random_index(readout, legal_actions, seed):
    """`baselines.md` §2: one index drawn uniformly from the decision's legal indices."""
    indices = _indices(legal_actions)
    text = _canonical(readout, indices)
    key = hashlib.sha256(
        PAYLOAD
        + b"\x1f"
        + str(int(seed)).encode("ascii")
        + b"\x1f"
        + text.encode("utf-8")
    ).digest()
    draw = numpy.random.Generator(
        numpy.random.PCG64(int.from_bytes(key[:16], "big"))
    ).random()
    return indices[min(int(draw * len(indices)), len(indices) - 1)]


def _always_call_index(legal_actions):
    """`baselines.md` §3: index 1 whenever it is legal, else index 2, never 0."""
    indices = _indices(legal_actions)
    if 1 in indices:
        return 1
    if 2 in indices:
        return 2
    return indices[0]


def _oracle_index(readout, legal_actions, seed):
    """`baselines.md` §4: call at or above the pot odds, fold below them, never raise."""
    indices = _indices(legal_actions)
    pot = int(readout["pot"])
    to_call = int(readout["to_call"])
    total = pot + to_call
    odds = float(to_call) / float(total) if total else 0.0
    try:
        import engine

        equity = float(engine.equity(readout, int(seed), EQUITY_SAMPLES))
    except Exception as error:
        # A refusal raised while a policy works is **this** module's, named
        # `policy(readout)`: `engine`'s own class would escape a caller's
        # `except AgentsError` (`errors.md` §2-§3).
        raise InvalidReadout(
            "policy(readout): the readout is not one engine.equity can price: %s"
            % (error,)
        ) from None
    if equity >= odds:
        if 1 in indices:
            return 1
        if 2 in indices:
            return 2
        return indices[0]
    if 0 in indices:
        return 0
    if 1 in indices:
        return 1
    return indices[-1]


class Baseline:
    """One fixed rule as a policy: a callable over `(readout, legal_actions)`."""

    _agents_baseline = True

    __slots__ = ("_name", "_seed")

    def __init__(self, name, seed):
        self._name = name
        self._seed = seed

    def __repr__(self):
        return "Baseline(%r, seed %d)" % (self._name, self._seed)

    def __call__(self, readout, legal_actions):
        """One descriptor from `legal_actions` for one readout (`surface.md` §12).

        The readout is validated for every baseline, `always-call` included: it reads
        no fact for its rule, and it still refuses a malformed one, because answering
        a decision nobody described would hide the caller's defect (`baselines.md` §1).
        """
        decision = _readout(readout)
        if self._name == "random":
            index = _random_index(decision, legal_actions, self._seed)
        elif self._name == "always-call":
            index = _always_call_index(legal_actions)
        else:
            index = _oracle_index(decision, legal_actions, self._seed)
        return features.decode_action(int(index))


def build_baseline(name, seed):
    """One baseline as a policy, or the refusal naming the name or the seed."""
    if not isinstance(name, str) or name not in NAMES:
        raise UnknownBaseline(
            "build_baseline(name): the name must be one of %r, got %r" % (NAMES, name)
        )
    if not isinstance(seed, Integral) or isinstance(seed, bool):
        raise InvalidSeed(
            "build_baseline(seed): the seed must be an integer, got %r" % (seed,)
        )
    return Baseline(name, int(seed))
