"""`baselines`, `build_baseline` and the six fixed rules (`baselines.md` §1-§9).

`random`, `always-call` and `oracle` are D-6's three fixed standards and the rating's
**anchor**; `fold-no-pair-or-face`, `fold-no-pair-or-better` and `fold-large-bet` are
D-21's three simple folders, which are members and table rows and never anchors.  None
of the six learns from a match, none has a trainable parameter (`params: 0`), and none
advances a state, so each is a function of the decision it is handed.  `random`'s draw is
keyed by the decision (`baselines.md` §2) because a uniform draw over each decision's
legal indices cannot come from a stream position once the order of decisions is free.

`engine` is imported **inside** a policy that needs it — the oracle's and
`fold-large-bet`'s — and nowhere else: `engine`'s modules hold `pokerkit` at module level,
and an eager import would leak it into `sys.modules` (`backends.md` §4, `README.md` §6).
A folder's rank is read off the one card spelling `engine` declares and never off a second
one; the starting stack is read from `engine.game_config` rather than copied (`folders.md`
§2, ASM-31, D-13, D-21).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from numbers import Integral, Real

import numpy

import features

from .errors import InvalidReadout, InvalidSeed, UnknownBaseline

#: The six catalogue names, in `protocol.md` §3's order: D-6's three first, then D-21's
#: three folders (`baselines.md` §6, D-21).
NAMES = (
    "random",
    "always-call",
    "oracle",
    "fold-no-pair-or-face",
    "fold-no-pair-or-better",
    "fold-large-bet",
)

#: The names that are the rating's anchor: the catalogue's `anchor: True` members, and
#: never a folder (`protocol.md` §3, ASM-32, D-21).  A catalogue record's flag is this
#: set's membership, so the declared flag and the anchor cannot drift.
ANCHORS = ("random", "always-call", "oracle")

#: The board sizes a decision declares: no public card, the flop, the turn, the river
#: (`README.md` §7).
BOARD_SIZES = (0, 3, 4, 5)

#: The oracle's pinned sample count: the count `baselines()` declares and the count
#: `build_baseline("oracle", seed)` queries, so a caller re-issues the same query
#: (`baselines.md` §5, ASM-4).
EQUITY_SAMPLES = 257

#: `baselines.md` §2's payload tag.
PAYLOAD = b"pypoker-agents/baseline-random/v1"

#: The rank alphabet of the one card spelling (`engine`'s `readout.md` §3): a card is two
#: characters, rank first.  `fold-no-pair-or-face` reads a rank off this spelling and adds
#: no second one (`folders.md` §2, `module-map.md` §2).
RANKS = "23456789TJQKA"

#: The ranks D-21 pins as face cards: J, Q, K **or A** (`folders.md` §2, D-21).
FACE_RANKS = frozenset("JQKA")

#: The declared spelling `features.action_space` publishes for the minimum legal raise-to,
#: and the only place this module names it: a decision's own descriptors are matched
#: against it and this module re-derives no vocabulary (`shapes.md` §3,
#: `features/surface.md` §7, `baselines.md` §3).
MINIMUM_RAISE = "raise-minimum"

#: The facts the canonical spelling, the inequality and the three folder rules read, in
#: the readout's order (`folders.md` §2, `surface.md` §11).
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
    "hand_class",
)


def _record(name, rule):
    """One baseline's catalogue value (`baselines.md` §6)."""
    return {
        "name": name,
        "rule": rule,
        "params": 0,
        "anchor": name in ANCHORS,
    }


def baselines():
    """The six fixed baselines, in `protocol.md` §3's order, each with its `anchor` flag."""
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
        "fold-no-pair-or-face": _record(
            "fold-no-pair-or-face",
            "before the flop, fold when the two hole cards are unpaired and neither "
            "card's rank is J, Q, K or A; check/call on every other decision",
        ),
        "fold-no-pair-or-better": _record(
            "fold-no-pair-or-better",
            "from the flop onward, fold when the best five-card hand of hole plus board "
            "is a high card only (hand_class 0); check/call before the flop",
        ),
        "fold-large-bet": _record(
            "fold-large-bet",
            "fold when the chips to call exceed half the declared starting stack — "
            "more than 10 of the declared 20 — on any street; check/call otherwise",
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


def _hand_class(value):
    """The readout's `hand_class`: `None` before the flop, or an integer 0-8 (ASM-30).

    A `bool`, a float, a string or an integer outside the nine classes is refused naming
    the fact, because a rule that read one would answer a decision nobody described; a
    missing `hand_class` is refused as a missing fact by :func:`_readout` itself
    (`folders.md` §2, §3, D-21).
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise _malformed("hand_class", "None or an integer 0-8", value)
    number = int(value)
    if not 0 <= number <= 8:
        raise _malformed("hand_class", "None or an integer 0-8", value)
    return number


def _rank(card):
    """One hole card's rank, read off the one declared spelling `engine` fixes (§3).

    A card is two characters, rank first from `"23456789TJQKA"`; anything else is refused
    as this module's own `policy(readout)` naming the fact, because a rank this module
    guessed would be a second spelling of the deal (`folders.md` §2, `module-map.md` §2,
    `engine/readout.md` §3).
    """
    spelling = card if isinstance(card, str) else None
    if spelling is None or len(spelling) != 2 or spelling[0] not in RANKS:
        raise _malformed(
            "hole", "the two-card spellings of engine's declared alphabet", card
        )
    return spelling[0]


def _readout(value):
    """One readout mapping whose facts have the shapes `baselines.md` §1 fixes.

    A readout is the eleven facts of `README.md` §7 or it is refused: a policy that
    defaulted a malformed fact would answer a decision nobody described, and an
    `int("3")` on the way to one would invent it (`surface.md` §1, `errors.md` §2-§3).
    Every shape is checked here, before any rule reads a fact, and as this module's
    own `InvalidReadout` named `policy(readout)`, `hand_class`'s `None`-or-0-8 rule
    included (`folders.md` §2, §3, ASM-30).  Nothing parses a card's spelling here:
    the counts and the shapes are checked and the cards only counted, so no `engine`
    parser is imported to inspect one (`README.md` §6); the one rule that reads a rank
    reads it through :func:`_rank`.
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
    _hand_class(value["hand_class"])
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


def _descriptor(legal_actions, index):
    """One chosen index as the `legal_actions` member at that index's own position.

    Every one of the six policies returns through this one function, so the lookup is
    implemented once and no baseline decodes an index in a shape's vocabulary
    (`baselines.md` §1-§2, `docs/L2/agents/baselines.md` §2).  The descriptor is the
    `legal_actions` member at the position the chosen index holds in
    `features.legal_indices`, never `legal_actions[index]`: a band masked out at the
    decision is absent from that sequence, so positions shift (`features/surface.md` §8
    fixes `legal_indices` as position-aligned, §9 makes `decode_action` shape-dependent,
    and a baseline carries no shape).  On the default shape the two readings agree,
    because the legal indices are `0, 1, 2` and their positions are `0, 1, 2`, so
    nothing at the default shape moves (`baselines.md` §1-§2, `features/surface.md` §8).
    """
    indices = _indices(legal_actions)
    return legal_actions[indices.index(int(index))]


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
    """`baselines.md` §3: index 1 whenever it is legal, else the minimum legal completion.

    With check/call unavailable the rule is the decision's **minimum legal completion**:
    the `raise-minimum` descriptor where `legal_actions` offers one, and otherwise index
    2, the first raise index every declared vocabulary carries.  `raise-minimum` is the
    declared spelling `features.action_space` publishes, which this module re-derives no
    vocabulary for: it recognises the decision's own descriptor and never decodes one, and
    a shape whose minimum carried another name would fall back to the first raise
    (`baselines.md` §3, `shapes.md` §3, `features/surface.md` §7).
    """
    indices = _indices(legal_actions)
    if 1 in indices:
        return 1
    for position, descriptor in enumerate(legal_actions):
        if descriptor == MINIMUM_RAISE:
            return indices[position]
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


def _continue_or_fold(indices, fold):
    """A folder's one legality rule: fold where folding is legal, else check/call (§7).

    Index `0` is taken only where `fold` is legal, index `1` whenever check/call is, and
    index `2` — the minimum legal completion — only where a raise is the sole legal
    action, because a raise-only decision is forced by the game and never chosen by the
    rule (ASM-31, `folders.md` §2).  An impossible mask holding none of the three gets its
    smallest index: legality outranks never-fold (D-2).
    """
    if fold and 0 in indices:
        return 0
    if 1 in indices:
        return 1
    if 2 in indices:
        return 2
    return indices[0]


def _fold_no_pair_or_face_index(readout, legal_actions):
    """`baselines.md` §7: pre-flop, fold unpaired hole cards with no J, Q, K or A."""
    indices = _indices(legal_actions)
    fold = False
    if readout["street"] == "preflop":
        first, second = readout["hole"]
        ranks = (_rank(first), _rank(second))
        fold = ranks[0] != ranks[1] and not (
            ranks[0] in FACE_RANKS or ranks[1] in FACE_RANKS
        )
    return _continue_or_fold(indices, fold)


def _fold_no_pair_or_better_index(readout, legal_actions):
    """`baselines.md` §7: from the flop, fold a high-card-only best five (§3's fact).

    `hand_class` is `None` before the flop, so `== 0` is the whole rule: it folds
    exactly on a high-card-only hand from the flop onward and never pre-flop (D-21).
    """
    indices = _indices(legal_actions)
    return _continue_or_fold(indices, readout["hand_class"] == 0)


def _fold_large_bet_index(readout, legal_actions):
    """`baselines.md` §7: fold when the call is more than half the starting stack.

    The stack is `engine.game_config()["starting_stack"]` read through the granted arrow
    on every decision, never a copied `20`: a game parameter lives once, in `engine`
    (ASM-31, `module-map.md` §2, D-13, D-21).
    """
    indices = _indices(legal_actions)
    to_call = int(readout["to_call"])
    try:
        import engine

        starting_stack = engine.game_config()["starting_stack"]
    except Exception as error:
        raise InvalidReadout(
            "policy(readout): the game's declared starting stack is not readable: %s"
            % (error,)
        ) from None
    return _continue_or_fold(indices, 2 * to_call > int(starting_stack))


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
        elif self._name == "oracle":
            index = _oracle_index(decision, legal_actions, self._seed)
        elif self._name == "fold-no-pair-or-face":
            index = _fold_no_pair_or_face_index(decision, legal_actions)
        elif self._name == "fold-no-pair-or-better":
            index = _fold_no_pair_or_better_index(decision, legal_actions)
        else:
            index = _fold_large_bet_index(decision, legal_actions)
        return _descriptor(legal_actions, index)


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
