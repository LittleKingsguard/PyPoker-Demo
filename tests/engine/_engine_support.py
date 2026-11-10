"""Plumbing and invented instances for the `engine` unit battery (D-11).

This module is test support, not part of any subsystem.  It does three things:

* it puts the repository's ``src/`` on ``sys.path`` and imports the declared
  ``engine`` package **lazily**, so that "the surface is absent" is one clean
  ``SurfaceAbsent`` failure in each case that needed it and never a collection
  error -- ``src/engine/`` does not exist yet, and the whole battery must still
  be collectable (``docs/L1/battery.md`` §1, §2);
* it drives the nine entry points of ``docs/L2/engine/surface.md`` §1 and
  nothing below them: no ``src/engine/`` submodule, helper, private name or
  class is ever touched (``docs/L3/engine/README.md`` §3, D-12);
* it holds the battery's own invented instances -- seeds, sample counts, policy
  objects -- so that a case is not written around the one example a design
  document happens to use (``docs/L1/battery.md`` §4, D-15).

The values the *contract* fixes (the eleven fact names, the four street names, the
three descriptors, the two card alphabets, the 200-decision bound) appear here
because a case asserts them.  Every seed and every sample count below is the
writer's own invention: no seed or sample count here is an example instance of
the design documents (the equity examples of ``docs/L3/engine/equity.md`` §4
included) or a seed, step or budget of ``tests/e2e``.  The nine hand classes are
written out as the design's own numbered table rather than read off the library's
label order, and the nine deals of ``CLASS_DEALS`` are pinned card strings this
battery spells itself (ASM-30, D-21).
"""

from __future__ import annotations

import importlib
import numbers as _numbers
import os
import random
import sys
import unittest
from collections.abc import Mapping

# --------------------------------------------------------------------------
# The declared surface (docs/L2/engine/surface.md §1, §12, layout.md §2)
# --------------------------------------------------------------------------
# The ten entry points, in the order ``engine.__all__`` declares them: D-29 added
# `game_shapes`, the catalogue of the declared shapes, to what were nine (surface.md
# §12, shapes.md §2).  ENG-1.1 asserts each one is a callable module-level name and
# ENG-12.1 asserts this tuple *is* the package's ``__all__``.
NINE = (
    "game_shapes",
    "game_config",
    "new_hand",
    "readout",
    "legal_actions",
    "apply_action",
    "is_terminal",
    "payoffs",
    "play_hand",
    "equity",
)

# The eleven facts, exactly (docs/L2/engine/environment.md §2, readout.md §2): the ten
# of D-3 plus D-21's derived `hand_class` (ASM-30).
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

#: The nine hand classes, each with the integer the design declares for it -- 0 high card,
#: 1 one pair, 2 two pair, 3 three of a kind, 4 straight, 5 flush, 6 full house, 7 four of a
#: kind, 8 straight flush (docs/L1/e2e-surface.md §2, docs/L1/folders.md §3, ASM-30) --
#: written out here as literals.  This is the battery's own statement of the numbering and
#: is never read off `pokerkit.lookups.Label`'s declaration order, which is how the engine
#: builds its map: a library release that reordered or inserted a label must not move the
#: expectation with the implementation.
HAND_CLASS_TABLE = (
    ("high card", 0),
    ("one pair", 1),
    ("two pair", 2),
    ("three of a kind", 3),
    ("straight", 4),
    ("flush", 5),
    ("full house", 6),
    ("four of a kind", 7),
    ("straight flush", 8),
)

#: The nine integers, in the design's own order: 0 high card through 8 straight flush.
HAND_CLASSES = tuple(value for _name, value in HAND_CLASS_TABLE)

#: One real dealt hand per declared class, spelled as card strings with the class those
#: cards make.  Each entry is
#: ``(class name, seed, hole, board, the five cards that make the class)``: driving that
#: seed with :func:`always_call` reaches a post-flop decision whose ``hole`` and ``board``
#: are exactly these spellings, and those five cards are the hand of that class.  ENG-4.12
#: compares that readout's ``hand_class`` with ``HAND_CLASS_TABLE``'s literal, so the
#: declared numbering is falsified from cards this battery spells itself, without asking
#: the library what order it thinks the classes are in (ASM-30, D-21).  Eight of the nine
#: are river deals chosen so that the board alone would be a *different* class, which
#: makes a board-only evaluation visible; the high-card row is a flop deal, where the
#: board alone (three cards) is not even a hand, so a board-only evaluation reads
#: ``None`` against the declared 0.
#:
#: The card strings are pinned to the deal ``engine.new_hand(seed)`` produces today.  If
#: the library's deck order ever changed, the case fails loudly -- no decision of the walk
#: reads these cards -- instead of silently measuring other hands, and the table is
#: refreshed by driving a fresh seed, reading its cards and writing down the class it makes.
CLASS_DEALS = (
    ("high card", 3000001, ("2h", "7d"), ("9s", "8h", "Ts"),
     ("2h", "7d", "9s", "8h", "Ts")),
    ("one pair", 3100003, ("Jd", "9s"), ("5d", "2s", "6c", "8d", "9d"),
     ("9s", "9d", "Jd", "8d", "6c")),
    ("two pair", 3100004, ("2s", "2c"), ("8d", "8c", "3s", "7h", "5h"),
     ("8d", "8c", "2s", "2c", "7h")),
    ("three of a kind", 3100016, ("6d", "9s"), ("9c", "7s", "2c", "9d", "3d"),
     ("9s", "9c", "9d", "7s", "6d")),
    ("straight", 3100006, ("Ad", "Qd"), ("4s", "7s", "Jc", "Kc", "Ts"),
     ("Ad", "Kc", "Qd", "Jc", "Ts")),
    ("flush", 3100095, ("3c", "6c"), ("9d", "7c", "Ac", "9c", "Ad"),
     ("Ac", "9c", "7c", "6c", "3c")),
    ("full house", 3100001, ("9h", "8h"), ("8d", "Ah", "7c", "7s", "7h"),
     ("7c", "7s", "7h", "8h", "8d")),
    ("four of a kind", 3101628, ("7s", "Tc"), ("Td", "Ts", "Th", "Jh", "6h"),
     ("Tc", "Td", "Ts", "Th", "Jh")),
    ("straight flush", 3100595, ("Ks", "Qs"), ("Js", "Ts", "9s", "4s", "2h"),
     ("Ks", "Qs", "Js", "Ts", "9s")),
)

STREETS = ("preflop", "flop", "turn", "river")
ACTIONS = ("fold", "check-call", "raise")
RANKS = "23456789TJQKA"
SUITS = "cdhs"
BOARD_SIZES = (0, 3, 4, 5)
STREET_OF_SIZE = {0: "preflop", 3: "flop", 4: "turn", 5: "river"}

# The hand must end within this many applied actions (surface.md §8,
# guardrails.md G5).  Asserted as a count, never as a clock (battery.md §2).
MAX_DECISIONS = 200

# --------------------------------------------------------------------------
# The two declared shapes, spelled out (docs/L3/engine/config.md §1-§6,
# docs/L1/shapes.md §2).  These are the *declaration* and not a reading of it:
# a case asserts them against `game_shapes`, `game_config` and the deals, so the
# expectation cannot move with the implementation (D-29, D-30).
# --------------------------------------------------------------------------
#: The catalogue's own order: the default row first (surface.md §12).
DEFAULT_SHAPE = "fixed-limit-20"
NO_LIMIT_SHAPE = "no-limit-100"
SHAPE_NAMES = (DEFAULT_SHAPE, NO_LIMIT_SHAPE)

#: The thirteen keys of one catalogue row, in the order surface.md §12 states them.
ROW_KEYS = (
    "name",
    "default",
    "seats",
    "blinds",
    "starting_stack",
    "chips_in_play",
    "bet_structure",
    "small_bet",
    "big_bet",
    "raise_cap",
    "actions",
    "head_width",
    "normalisers",
)

#: The five normalisers every row declares, in config.md §4's order.
NORMALISER_KEYS = ("stack", "pot", "to_call", "amount", "count")

#: The fifteen keys `game_config` carries, in the order config.md §3 declares them.
CONFIG_KEYS = (
    "game",
    "seats",
    "player_count",
    "button_seat",
    "blinds",
    "small_blind",
    "big_blind",
    "blind_levels",
    "starting_stack",
    "starting_stacks",
    "small_bet",
    "big_bet",
    "limit",
    "raise_cap",
    "streets",
)

#: The two descriptors every declared shape carries, at indices 0 and 1 (actions.md §1).
BASES = ("fold", "check-call")

#: Each shape's vocabulary, in its own index order (config.md §2, §6).
FIXED_ACTIONS = ("fold", "check-call", "raise")
SIZED_ACTIONS = (
    "fold",
    "check-call",
    "raise-quarter",
    "raise-half",
    "raise-all-in",
    "raise-minimum",
)
SHAPE_ACTIONS = {DEFAULT_SHAPE: FIXED_ACTIONS, NO_LIMIT_SHAPE: SIZED_ACTIONS}

#: The four raise descriptors of a shape without a cap, in the declared index order --
#: the measured price order, worst first, which is deliberately **not** monotone in
#: amount: the all-in sits before the minimum (config.md §6, sizing.md §3).
SIZED_RAISES = ("raise-quarter", "raise-half", "raise-all-in", "raise-minimum")

#: The chips in play each row declares, and the stack it starts each seat with.
SHAPE_CHIPS_IN_PLAY = {DEFAULT_SHAPE: 40, NO_LIMIT_SHAPE: 200}
SHAPE_STARTING_STACK = {DEFAULT_SHAPE: 20, NO_LIMIT_SHAPE: 100}

# --------------------------------------------------------------------------
# Invented instances.  Every seed and sample count here is the battery's own,
# invented from the declared surface (D-15): none is an example instance of the
# design documents, and none is a seed, step or budget of the e2e battery.  The
# sample counts are deliberately neither the design's equity examples nor the
# e2e battery's counts.
# --------------------------------------------------------------------------
SEED_A = 20260101
SEED_B = 777
SEED_C = 4242424
SEED_D = 311
SEED_E = 5151
SEED_F = 60607
SEEDS = (
    SEED_A, SEED_B, SEED_C, SEED_D, SEED_E, SEED_F,
    1234567, 909091, 64037, 2718, 161803, 3141,
)
SAMPLES_COARSE = 149
SAMPLES_TINY = 11
SAMPLES_MID = 83

#: The second declared shape's own invented seeds (D-15, D-29).  None of them is a
#: seed of the design documents, of the seeds above, of `CLASS_DEALS` or of the e2e
#: battery: they were picked by the writer for this family alone, and the walks ENG-13
#: builds on them are pinned by the case that needs each one.
SHAPE_SEED_A = 880411
SHAPE_SEED_B = 5050505
SHAPE_SEED_C = 730211
SHAPE_SEED_D = 660133
SHAPE_SEED_E = 512345
SHAPE_SEEDS = (SHAPE_SEED_A, SHAPE_SEED_B, SHAPE_SEED_C, SHAPE_SEED_D, SHAPE_SEED_E)


class SurfaceAbsent(AssertionError):
    """The declared `engine` surface is absent, or a name of it is missing.

    It subclasses ``AssertionError`` so that the case that needed the surface
    records one clear *failure* naming what is missing, never an error inside
    this battery (``docs/L1/battery.md`` §1).
    """


# --------------------------------------------------------------------------
# Import-path plumbing (the pattern of tests/e2e/_surface.py)
# --------------------------------------------------------------------------
def repo_root():
    """The repository root: this file lives at ``<root>/tests/engine/...``."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def src_dir():
    return os.path.join(repo_root(), "src")


def _ensure_src():
    src = src_dir()
    if src not in sys.path:
        sys.path.insert(0, src)


def engine():
    """The declared ``engine`` package, or one clear ``SurfaceAbsent``."""
    _ensure_src()
    try:
        return importlib.import_module("engine")
    except SurfaceAbsent:
        raise
    except Exception as exc:  # not importable yet, or broken on import
        raise SurfaceAbsent(
            "surface absent: the declared module 'engine' is not importable from %s "
            "(%s: %s)" % (src_dir(), type(exc).__name__, exc)
        ) from exc


def ep(name):
    """One of the nine declared entry points, or one clear ``SurfaceAbsent``."""
    module = engine()
    try:
        return getattr(module, name)
    except AttributeError:
        raise SurfaceAbsent(
            "surface absent: engine.%s is not declared" % (name,)
        ) from None


# --------------------------------------------------------------------------
# Small readers.  A case asserts the contract through these instead of through
# a spelling this battery made up.
# --------------------------------------------------------------------------
def is_number(value):
    """A real number the battery reads as a quantity (booleans excluded)."""
    return isinstance(value, _numbers.Number) and not isinstance(value, (bool, complex))


def is_integer(value):
    """An integer, in the sense the seed contract means (bools excluded)."""
    return isinstance(value, _numbers.Integral) and not isinstance(value, bool)


def is_mapping(value):
    return isinstance(value, Mapping)


def numbers(value, _depth=0):
    """Every number inside an observable value, in traversal order."""
    out = []
    if _depth > 20:
        return out
    if is_number(value):
        return [value]
    if is_mapping(value):
        for inner in value.values():
            out.extend(numbers(inner, _depth + 1))
    elif isinstance(value, (list, tuple, set, frozenset)):
        for inner in value:
            out.extend(numbers(inner, _depth + 1))
    return out


def leaves(value, _depth=0):
    """Every non-container leaf of an observable value, as one text."""
    parts = []
    if _depth > 20:
        return " ".join(parts)
    if is_mapping(value):
        for key, inner in value.items():
            parts.append(str(key))
            parts.append(leaves(inner, _depth + 1))
    elif isinstance(value, (list, tuple, set, frozenset)):
        for inner in value:
            parts.append(leaves(inner, _depth + 1))
    else:
        parts.append(str(value))
    return " ".join(parts)


def card_spelling_ok(card):
    """Whether ``card`` is a two-character card of the declared spelling."""
    if not isinstance(card, str) or len(card) != 2:
        return False
    return card[0] in RANKS and card[1] in SUITS


def hand_class_of(hole, board):
    """The class of the best five-card hand of these spellings, from `pokerkit` itself.

    A **second, differently built witness for the derivation** -- that the fact is the best
    five-card hand of hole plus board and of nothing else -- checked over many real deals,
    so a class the engine derived from anything but those two facts fails
    (``docs/L3/engine/readout.md`` §2, ASM-30, D-21).  ``None`` while fewer than five cards
    are known, exactly as the fact is.

    It is **not** the authority for the nine integers: this function reads the library's own
    ``Label`` order, which is how the engine builds its map, so a reordered library would move
    both together.  The numbering is fixed independently by ``HAND_CLASS_TABLE`` and the
    explicit card strings of ``CLASS_DEALS``, which is what ENG-4.12 asserts.
    """
    from pokerkit.hands import StandardHighHand
    from pokerkit.lookups import Label
    from pokerkit.utilities import Card

    def cards(spellings):
        return [Card(spelling[0], spelling[1]) for spelling in spellings]

    best = StandardHighHand.from_game_or_none(cards(hole), cards(board))
    if best is None:
        return None
    return list(Label).index(best.entry.label)


# --------------------------------------------------------------------------
# The four raise bands, as the declaration states them (docs/L3/engine/config.md
# §5, docs/L1/sizing.md §2).  Written out here rather than read off the engine, so
# the expectation does not move with the implementation: a case computes the
# amount a descriptor must resolve to from that decision's own bounds, and never
# from the amount the engine happened to choose.
# --------------------------------------------------------------------------
def band_amount(descriptor, minimum, maximum):
    """The amount ``descriptor`` resolves to, or ``None`` for an empty band.

    With ``m`` the minimum legal raise-to, ``A`` the all-in raise-to and
    ``L = A - m`` (``config.md`` §5): ``raise-minimum`` owns ``{m}`` and resolves to
    ``m``; ``raise-quarter`` owns ``(m, m + L//4]``; ``raise-half`` owns
    ``(m + L//4, m + L//2]``; ``raise-all-in`` owns ``(m + L//2, A]`` -- each
    resolving to its own band's maximum.  A band holding no legal integer is
    **empty and masked out**, so ``None`` here means "this descriptor is absent
    from ``legal_actions`` at this decision", never "it bets its neighbour's
    amount" (``sizing.md`` §2).
    """
    span = maximum - minimum
    if descriptor == "raise-minimum":
        return minimum
    if descriptor == "raise-quarter":
        return minimum + span // 4 if span // 4 >= 1 else None
    if descriptor == "raise-half":
        return minimum + span // 2 if span // 2 > span // 4 else None
    if descriptor == "raise-all-in":
        return maximum if maximum > minimum + span // 2 else None
    raise AssertionError(
        "%r is not a raise descriptor of a shape without a cap (config.md §5)" % (descriptor,)
    )


def is_raise(descriptor):
    """Whether ``descriptor`` names a raise rather than one of the two bases."""
    return descriptor not in BASES


def raises_in(legal):
    """The raise descriptors of one decision's legal sequence, in the order given."""
    return tuple(descriptor for descriptor in legal if is_raise(descriptor))


# --------------------------------------------------------------------------
# Policies.  A policy is a callable taking ``(readout, legal)`` and returning a
# member of ``legal`` (docs/L1/e2e-surface.md §2); these are the battery's own,
# the engine knows none of them by name (episode.md §4).
# --------------------------------------------------------------------------
def band_walk(pattern):
    """A policy cycling ``pattern`` one descriptor per decision, falling back to a call.

    ``pattern`` is a tuple of descriptors read as the seat's own decision count modulo
    its length, so ``band_walk(("raise-minimum",))`` raises the minimum whenever a raise
    is legal and ``band_walk(("raise-quarter", "raise-half"))`` alternates them.  A
    descriptor the decision does not offer -- a band masked out because it is empty
    (``config.md`` §5) -- is replaced by ``check-call``, so a walk continues past it;
    the battery says which descriptors it expects where in the cases that read the
    resulting record, rather than here.

    Each seat gets its own closure, exactly as ``play_hand`` is called with two policy
    objects, so the count is one seat's decisions.  It draws no randomness, so a case
    built on it repeats (surface.md §10, ASM-2).
    """
    state = {"decision": 0}

    def policy(readout, legal):
        position = state["decision"]
        state["decision"] = position + 1
        want = pattern[position % len(pattern)]
        return want if want in legal else "check-call"

    return policy


def raise_to(entry):
    """The raise-to one applied raise reported, read from its history entry.

    A raise's entry reads ``"<street> seat <index> raises to <amount>"``
    (``docs/L3/engine/advance.md`` §2), and the amount is the total street bet level
    the step reached -- the resolution the engine chose for the descriptor and
    handed to the step (``actions.md`` §2, ``stepping.md`` §2).  It is how a case
    reads the resolution of a descriptor the record did not choose: the amount is
    what the engine reported, and the case compares it with the amount the
    declaration says that band owns.
    """
    text = str(entry)
    head, _, amount = text.rpartition(" ")
    if not head.endswith("raises to") or not amount.isdigit():
        raise AssertionError(
            "a raise's history entry reads '<street> seat <i> raises to <n>', got %r "
            "(advance.md §2)" % (entry,)
        )
    return int(amount)


def always_call(readout, legal):
    return "check-call"


def always_raise(readout, legal):
    return "raise" if "raise" in legal else "check-call"


def always_fold(readout, legal):
    return "fold" if "fold" in legal else "check-call"


def first_legal(readout, legal):
    return legal[0]


def last_legal(readout, legal):
    return legal[-1]


# --------------------------------------------------------------------------
# The base case
# --------------------------------------------------------------------------
class EngineCase(unittest.TestCase):
    """One battery case; every declared surface is reached through :func:`ep`."""

    # -- the nine entry points ---------------------------------------------
    def config(self):
        return ep("game_config")()

    def hand(self, seed=SEED_A):
        return ep("new_hand")(seed)

    def readout(self, hand):
        return ep("readout")(hand)

    def legal(self, hand):
        return ep("legal_actions")(hand)

    def step(self, hand, action):
        return ep("apply_action")(hand, action)

    def terminal(self, hand):
        return ep("is_terminal")(hand)

    def payoffs(self, hand):
        return ep("payoffs")(hand)

    def episode(self, seed=SEED_A, seat0_policy=None, seat1_policy=None):
        if seat0_policy is None:
            seat0_policy = always_call
        if seat1_policy is None:
            seat1_policy = always_call
        return ep("play_hand")(seed, seat0_policy, seat1_policy)

    def equity(self, decision, seed=SEED_A, samples=SAMPLES_COARSE):
        return ep("equity")(decision, seed, samples)

    # -- the declared shapes (surface.md §2, §12, config.md §1-§3) -----------
    def catalogue(self):
        """`game_shapes()`: the declared shapes as one ordered mapping (surface.md §12)."""
        return ep("game_shapes")()

    def shaped_hand(self, seed, shape):
        """`new_hand(seed, shape)`: one deal on the named shape (surface.md §4)."""
        return ep("new_hand")(seed, shape)

    def shaped_episode(self, seed, seat0_policy, seat1_policy, shape):
        """`play_hand(seed, p0, p1, shape)`: one episode on the named shape (surface.md §10)."""
        return ep("play_hand")(seed, seat0_policy, seat1_policy, shape)

    def replay(self, seed, shape, seat0_policy, seat1_policy, limit=MAX_DECISIONS):
        """Yield ``(hand, decision)`` pairs of one hand played out on ``shape``.

        The decisions are the episode record's; ``hand`` is the live handle at that
        decision's state, reached through ``new_hand`` and ``apply_action`` along the
        actions the record holds.  A case therefore reads a decision from the record --
        its bounds, its legal descriptors, its amount -- and steps from the handle the
        same walk reached (surface.md §10, episode.md §5).  The two policies are
        separate objects, exactly as ``play_hand`` is called with them, so a policy
        that counts its own decisions counts one seat's.
        """
        record = self.shaped_episode(seed, seat0_policy, seat1_policy, shape)
        hand = self.shaped_hand(seed, shape)
        for position, decision in enumerate(record["decisions"]):
            if position >= limit:
                self.fail(
                    "the hand at seed %r on %r has not ended after %d applied actions "
                    "(surface.md §8, guardrails.md G5)" % (seed, shape, limit)
                )
            yield hand, decision
            hand = self.step(hand, decision["action"])

    # -- driving ------------------------------------------------------------
    def drive(self, seed=SEED_A, policy=None, limit=MAX_DECISIONS):
        """Apply ``policy`` until the hand ends: the walk and the final hand.

        Returns ``(walk, last)`` where ``walk`` is a list of
        ``(readout, legal, action)`` before each applied action and ``last`` is
        the terminal handle.
        """
        if policy is None:
            policy = always_call
        hand = self.hand(seed)
        walk = []
        while not self.terminal(hand):
            if len(walk) >= limit:
                self.fail(
                    "the hand at seed %r has not ended after %d applied actions "
                    "(surface.md §8, guardrails.md G5): %r"
                    % (seed, limit, self.readout(hand))
                )
            readout = self.readout(hand)
            legal = self.legal(hand)
            action = policy(readout, legal)
            walk.append((readout, legal, action))
            hand = self.step(hand, action)
        return walk, hand

    def played_out(self, seed=SEED_A, policy=None, limit=MAX_DECISIONS):
        """The terminal handle of one played-out hand."""
        return self.drive(seed, policy, limit)[1]

    def decisions_of(self, walk):
        """The acting seat index of each decision in a walk."""
        return [entry[0]["seat"][0] for entry in walk]

    # -- refusals -----------------------------------------------------------
    def refusal(self, fn, *args):
        """Call an entry point that must refuse, and return the raised error.

        The battery asserts that a refusal *happens*, that its message names
        the violated contract, and that it is not one of this battery's own
        failures -- never that it is an instance of a particular class
        (``docs/L3/engine/errors.md`` §2, ``docs/L1/battery.md`` §2).
        """
        try:
            fn(*args)
        except SurfaceAbsent:
            raise
        except Exception as exc:  # the refusal the contract asks for
            self.assertTrue(
                str(exc).strip(),
                "%s(%r) refused without a message naming the violated contract "
                "(surface.md §1)" % (getattr(fn, "__name__", fn), args),
            )
            return exc
        self.fail(
            "%s(%r) was accepted, and the contract refuses it (surface.md §1)"
            % (getattr(fn, "__name__", fn), args)
        )

    def assert_mentions(self, exc, *words):
        """The refusal's message names the violated contract, tolerantly."""
        text = str(exc).lower()
        self.assertTrue(
            any(word.lower() in text for word in words),
            "the refusal must name the violated contract (%r), got %r"
            % (" or ".join(words), str(exc)),
        )

    def assert_untouched(self, hand, before):
        """A refused call left the handle at its own state (surface.md §1)."""
        self.assertEqual(
            self.readout(hand),
            before,
            "a refused call must leave the hand it was given at its own state "
            "(surface.md §1 rule 6)",
        )

    def assert_stream_untouched(self, fn, *args):
        """``fn(*args)`` leaves the global `random` stream byte-identical."""
        saved = random.getstate()
        result = fn(*args)
        self.assertEqual(
            random.getstate(),
            saved,
            "%s moved the global random stream, which only new_hand may seed "
            "(surface.md §1, stream.md §1)"
            % (getattr(fn, "__name__", fn),),
        )
        return result
