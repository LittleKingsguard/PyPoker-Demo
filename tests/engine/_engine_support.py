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

The values the *contract* fixes (the ten fact names, the four street names, the
three descriptors, the two card alphabets, the 200-decision bound) appear here
because a case asserts them.  Every seed and every sample count below is the
writer's own invention: no seed or sample count here is an example instance of
the design documents (the equity examples of ``docs/L3/engine/equity.md`` §4
included) or a seed, step or budget of ``tests/e2e``.
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
# The declared surface (docs/L2/engine/surface.md §1, layout.md §2)
# --------------------------------------------------------------------------
NINE = (
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

# The ten facts, exactly (docs/L2/engine/environment.md §2, readout.md §2).
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


# --------------------------------------------------------------------------
# Policies.  A policy is a callable taking ``(readout, legal)`` and returning a
# member of ``legal`` (docs/L1/e2e-surface.md §2); these are the battery's own,
# the engine knows none of them by name (episode.md §4).
# --------------------------------------------------------------------------
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
