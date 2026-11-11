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

**The shape is the policy's, and it is optional.**  `build_baseline(name, seed, shape=None)`
takes the declared shape the policy decides in, absent meaning the default, and the policy
carries that shape's **name** and neither a `learning_rule` nor a `utility`: a baseline
still learns nothing and is trained on no reward (`e2e-surface.md` §2, §3.3, ASM-4, D-6,
D-21).  Two of the six rules need it and one of them for a reading rather than an
arithmetic: `fold-large-bet` folds when the call exceeds half the **shape's own** starting
stack, so the same policy folds at 51 chips on a hundred-chip six-seat table and at 11 on
the default shape's twenty, and the oracle's equity question is N-way on a shape with more
than two seats (`folders.md` §2, ASM-31, `seats.md` §2, §6, D-33).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from numbers import Integral, Real

import numpy

import features

from . import declarations
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
            "fold when the chips to call exceed half the shape's declared starting "
            "stack — more than 10 of the default shape's 20 — on any street; check/call "
            "otherwise",
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


def _seat_counts():
    """`one number per seat: the 2 or 6 entries the declared shapes carry`, as a refusal says it.

    The clause is derived from `declarations.SEAT_COUNTS` rather than typed out, so a
    fourth declared seat count cannot leave a message naming the old set (`errors.md` §3,
    `seats.md` §2-§3).
    """
    counts = declarations.SEAT_COUNTS
    return "one number per seat: the %s entries the declared shapes carry" % (
        " or ".join("%d" % (count,) for count in counts),
    )


def _seats(fact, value):
    """One readout fact that is one number per seat: as many entries as a declared shape's seats.

    `stacks` is one entry per seat in seat order, so its length **is** the decision's seat
    count -- the rule `engine.equity` reads the same fact by (`seats.md` §3, `engine/
    equity.md` §3).  Two lengths are declared, two seats on D-2's and D-29's rows and six
    on D-33's, so a sequence of any other length is a readout no declared shape produces
    and is refused naming the fact, the declared lengths and the value; a single entry
    that is not a number is refused the same way.  Nothing is parsed and nothing is
    truncated to two: the count is the shape's and never a literal of this module's
    validator (`shapes.md` §2, `seats.md` §2-§3, ASM-44).
    """
    wanted = _seat_counts()
    entries = _entries(fact, value, wanted)
    if len(entries) not in declarations.SEAT_COUNTS:
        raise _malformed(fact, wanted, value)
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
    reads it through :func:`_rank`.  The **seat count** is checked too, and only through
    `stacks`' own length: `stacks` is one entry per seat and `seat` indexes it, so a
    six-seat decision is as well-formed as a two-seat one and no other length is
    (`seats.md` §3, ASM-44).
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
    # The seat count is the shape's and it reaches this validator through the one fact
    # whose length is it, `stacks`: two entries on the two-seat rows and six on the
    # six-seat one, so an index in `0 .. seats − 1` is the range a decision of that shape
    # can name and no looser or tighter one is accepted (`seats.md` §3, ASM-44).
    seats = _seats("stacks", value["stacks"])
    if not 0 <= int(seat[0]) < len(seats):
        raise _malformed(
            "seat",
            "a seat index in 0..%d, one per entry of 'stacks'" % (len(seats) - 1,),
            value["seat"],
        )
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
    """`baselines.md` §4: call at or above the pot odds, fold below them, never raise.

    The equity question is asked with the readout it was handed, at the baseline's own
    seed and at the declared sample count, and `engine.equity` reads the **seat count**
    off that readout's `stacks` fact: a decision of a shape with more than two seats is
    answered N-way, against the other seats' uniformly random hands, so a six-seat
    readout is a six-way question and no argument here says how many opponents there are
    (`engine/equity.md` §3, `seats.md` §2, D-33).  That is why a policy built for a shape
    with more than two seats is an oracle at all: the shape decides whether this question
    is asked two-way or N-way, and the validator above is what lets the six-seat readout
    reach it (`e2e-surface.md` §3.1, §3.3, ASM-4, D-6).
    """
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


def _fold_large_bet_index(readout, legal_actions, shape):
    """`baselines.md` §9: fold when the call is more than half the shape's starting stack.

    The stack is `engine.game_config(shape)["starting_stack"]` read through the granted
    arrow on every decision, never a copied `20` and never a copied `100`: a game
    parameter lives once, in `engine`, and the shape is the one the policy was built for,
    so "half the stack" is 10 on the default shape's twenty chips and 50 on the
    six-seat row's hundred -- the same rule and the same code (`folders.md` §2, ASM-31,
    `module-map.md` §2, `seats.md` §2, §6, D-13, D-21, D-33).
    """
    indices = _indices(legal_actions)
    to_call = int(readout["to_call"])
    try:
        import engine

        starting_stack = engine.game_config(shape)["starting_stack"]
    except Exception as error:
        raise InvalidReadout(
            "policy(readout): the game's declared starting stack is not readable: %s"
            % (error,)
        ) from None
    return _continue_or_fold(indices, 2 * to_call > int(starting_stack))


class Baseline:
    """One fixed rule as a policy: a callable over `(readout, legal_actions)`.

    It carries the baseline's name, its seed and the **name of the declared shape it
    decides in** -- and nothing else: no `learning_rule` and no `utility`, because a
    baseline learns nothing and is trained on no reward, and no shape object, because a
    policy's state is its own and the shape is one string (`e2e-surface.md` §2, ASM-4,
    D-6, D-21, `seats.md` §6).
    """

    _agents_baseline = True

    __slots__ = ("_name", "_seed", "_shape")

    def __init__(self, name, seed, shape=None):
        self._name = name
        self._seed = seed
        self._shape = shape

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
            index = _fold_large_bet_index(decision, legal_actions, self._shape)
        return _descriptor(legal_actions, index)


def build_baseline(name, seed, shape=None):
    """One baseline as a policy, or the refusal naming the name, the seed or the shape.

    `shape` is the declared game the policy decides in and is **optional**: absent it is
    the default shape, which is what the two-seat fixed game's baselines were built as
    before the shape existed, so a two-argument call is today's call (`e2e-surface.md`
    §3.3, `shapes.md` §2, `seats.md` §6, D-33).  A name outside the catalogue is refused
    naming it and the declared names, never defaulted, as every other row of this surface
    that takes a shape refuses one (`shapes.md` §2, `seats.md` §6, D-13).
    """
    if not isinstance(name, str) or name not in NAMES:
        raise UnknownBaseline(
            "build_baseline(name): the name must be one of %r, got %r" % (NAMES, name)
        )
    if not isinstance(seed, Integral) or isinstance(seed, bool):
        raise InvalidSeed(
            "build_baseline(seed): the seed must be an integer, got %r" % (seed,)
        )
    return Baseline(name, int(seed), declarations.require_game(shape, "build_baseline"))
