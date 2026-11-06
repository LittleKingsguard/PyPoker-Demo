"""Support for the L2 integration battery of the ``engine`` module.

The battery drives the nine entry points of ``docs/L2/engine/surface.md`` (Rev 2)
at the package's edge and reaches nothing below one of them.  This module holds
what every case shares and nothing else:

* the ``src/`` import path, so the battery runs standalone and needs no
  ``conftest.py`` (the ``harness`` module owns that file);
* the battery's *invented instances* — seeds, sample counts, hand counts and
  policy behaviours that appear in no design document (D-15, ``battery.md`` §4),
  so each ``general`` row carries an instance of the test writer's own;
* tolerant readers for what the design leaves free (a descriptor's spelling, a
  seat fact's container, a per-seat record's keys, a refusal's error class), so a
  case asserts the contract and never a spelling this battery invented;
* a base case with the small vocabulary of calls the cases are written in, and
  the plain callables that play the policies' side of the edge.

It imports ``engine`` and the standard library, and nothing else.
"""

from __future__ import annotations

import importlib
import numbers as _numbers
import os
import random
import sys
import unittest
from collections.abc import Mapping

# ---------------------------------------------------------------------------
# The declared surface, by name
# ---------------------------------------------------------------------------
ENGINE = "engine"

ENTRY_POINTS = (
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

# environment.md §2: the closed information set, in its declared order.
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
)

# records.md §5: the episode record's three required keys, and each decision's
# five required facts.
EPISODE_FACTS = ("seed", "decisions", "payoffs")
DECISION_FACTS = ("seat", "readout", "legal", "action", "reward")

# environment.md §2: the four street names and the board each one reveals.
STREETS = ("preflop", "flop", "turn", "river")
BOARD_LENGTH = {"preflop": 0, "flop": 3, "turn": 4, "river": 5}

# ASM-6's fixed game (surface.md §3).
STARTING_STACKS = 20
SMALL_BLIND = 1
BIG_BLIND = 2
SMALL_BET = 2
BIG_BET = 4
RAISE_CAP = 4

# surface.md §8: a hand that has not ended after 200 decisions is a defect.
DECISION_BOUND = 200

# ---------------------------------------------------------------------------
# The battery's invented instances (D-15, battery.md §4)
# ---------------------------------------------------------------------------
# None of these seeds, sample counts or hand counts is in docs/L1 or docs/L2;
# they are the test writer's own, invented from the declared surface alone.
SEED_A = 20251
SEED_B = 60617
SEED_C = 84123
SEED_D = 77103
SEED_E = 31417
SEED_F = 50021
SEED_G = 64007
SEED_H = 81233
SEED_I = 90917
SEED_J = 13337
SEED_K = 22273
SEED_L = 48017
SEED_M = 55049
SEED_N = 70571
SEED_O = 96001
SEED_P = 10501

SEED_DISTINCT = (SEED_A, SEED_B, SEED_C, SEED_D, SEED_E, SEED_F, SEED_G,
                 SEED_H, SEED_I, SEED_J, SEED_K, SEED_L, SEED_M)
# A sample of hands the battery scans for a split: the first seed is the one
# that pays a tie under the battery's own raise-always policy, and the rest of
# the range is the sample it falls back on.
SEED_SAMPLE = (70051,) + tuple(range(70001, 70065))
SAMPLES_COARSE = 83                            # a coarse sample count, invented
SAMPLES_ODD = 89
SAMPLES_FINE = 353
SAMPLES_HUGE = 97                              # the design documents' coarse count


class PolicyFailure(Exception):
    """The error the battery's own exploding policy raises (D-2: it propagates)."""


# ---------------------------------------------------------------------------
# Import-path plumbing: the battery runs without a conftest
# ---------------------------------------------------------------------------
def repo_root():
    """The repository root: this file is ``<root>/tests/integration/engine/``."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(os.path.dirname(here)))


def src_dir():
    return os.path.join(repo_root(), "src")


_ENGINE = None


def module():
    """The ``engine`` package, or a failure naming the absent surface."""
    global _ENGINE
    if _ENGINE is None:
        src = src_dir()
        if src not in sys.path:
            sys.path.insert(0, src)
        try:
            _ENGINE = importlib.import_module(ENGINE)
        except Exception as exc:  # not importable yet, or broken on import
            raise AssertionError(
                "surface absent: the declared module %r is not importable from %s "
                "(%s: %s)" % (ENGINE, src, type(exc).__name__, exc)
            ) from exc
    return _ENGINE


def entry(name):
    """One declared entry point, or a failure naming the missing name."""
    module()
    try:
        return getattr(_ENGINE, name)
    except AttributeError:
        raise AssertionError(
            "surface absent: engine.%s is not a module-level name of the package "
            "(surface.md §1)" % (name,)
        ) from None


# ---------------------------------------------------------------------------
# Tolerant readers for the shapes the design leaves free
# ---------------------------------------------------------------------------
def is_number(value):
    """Whether a returned value is a real number the battery reads as a quantity."""
    return isinstance(value, _numbers.Number) and not isinstance(value, (bool, complex))


def is_count(value):
    """Whether a value is an integer count (a ``bool`` is not a count)."""
    return isinstance(value, _numbers.Integral) and not isinstance(value, bool)


def is_mapping(value):
    return isinstance(value, Mapping)


def is_indexable(value):
    """Whether a value is an ordered, indexable sequence (not a string or a set)."""
    if isinstance(value, (str, bytes, set, frozenset)):
        return False
    return hasattr(value, "__len__") and hasattr(value, "__getitem__")


def token(name):
    """A key reduced to its letters and digits: ``check-call`` == ``check_call``."""
    return "".join(ch for ch in str(name).lower() if ch.isalnum())


def canon(obj, _depth=0):
    """A hashable, order-stable canonical form of an observable value.

    Used to compare two returned records without assuming how they are nested.
    An object the battery cannot read falls back to its type and ``str``, which is
    the spelling the design promises to keep stable (surface.md §2).
    """
    if _depth > 24:
        return ("deep", str(obj))
    if obj is None or isinstance(obj, (bool, int, float, str, bytes)):
        return obj
    if isinstance(obj, Mapping):
        return tuple(sorted((str(key), canon(value, _depth + 1)) for key, value in obj.items()))
    if isinstance(obj, (list, tuple)):
        return tuple(canon(value, _depth + 1) for value in obj)
    if isinstance(obj, (set, frozenset)):
        return tuple(sorted((canon(value, _depth + 1) for value in obj), key=repr))
    if hasattr(obj, "tolist"):
        try:
            return canon(obj.tolist(), _depth + 1)
        except Exception:
            pass
    if hasattr(obj, "__len__") and hasattr(obj, "__getitem__"):
        try:
            return tuple(canon(obj[i], _depth + 1) for i in range(len(obj)))
        except Exception:
            pass
    return ("object", type(obj).__name__, str(obj))


def flatten_text(obj):
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

    walk(obj, 0)
    return " ".join(parts).lower()


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


def bools_in(obj, _depth=0):
    """Every boolean in an observable value, in traversal order."""
    if _depth > 24:
        return []
    if isinstance(obj, bool):
        return [obj]
    if isinstance(obj, Mapping):
        out = []
        for value in obj.values():
            out.extend(bools_in(value, _depth + 1))
        return out
    if isinstance(obj, (list, tuple, set, frozenset)):
        out = []
        for value in obj:
            out.extend(bools_in(value, _depth + 1))
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


def contains_number(obj, target):
    """Whether a fact states ``target``, as a number or as digits in a string."""
    for value in numbers_in(obj):
        try:
            if float(value) == float(target):
                return True
        except (TypeError, ValueError):
            continue
    digits = str(int(target))
    for text in strings_in(obj):
        if digits in "".join(ch for ch in text if ch.isdigit() or ch == "."):
            return True
    return False


def one_number(value, what):
    """The single number a fact states, or a failure naming the fact."""
    values = numbers_in(value)
    if len(values) != 1:
        raise AssertionError(
            "%s must be one number (environment.md §2); got %r" % (what, value)
        )
    return values[0]


def count_list(value, what, count=2):
    """The numbers a fact states, in order, when it must state ``count`` of them."""
    values = numbers_in(value)
    if len(values) != count:
        raise AssertionError(
            "%s must state %d numbers in seat order (environment.md §2); got %r"
            % (what, count, value)
        )
    return values


def card_list(value, what):
    """The cards a fact holds, as a list, or a failure naming the fact."""
    if not is_indexable(value):
        raise AssertionError(
            "%s must be a sequence of cards (environment.md §2); got %r" % (what, value)
        )
    return [value[i] for i in range(len(value))]


def descriptor_kind(descriptor):
    """Which vocabulary action a descriptor names, read from its stable text.

    ``e2e-surface.md`` §2 fixes the three actions — ``fold``, ``check-call`` and
    ``raise`` — and leaves the spelling to the implementation; the descriptor
    prints stably (surface.md §2), so its text is the one spelling a battery can
    read without reaching below the entry point.  ``None`` when the text names
    none of the three.
    """
    text = flatten_text(descriptor)
    if "fold" in text:
        return "fold"
    if "raise" in text or "bet" in text:
        return "raise"
    if "call" in text or "check" in text:
        return "check-call"
    return None


def descriptor_list(value, what):
    """The descriptors of an indexable, ordered sequence, as a list."""
    if not is_indexable(value):
        raise AssertionError(
            "%s must be an ordered, indexable sequence of descriptors (surface.md §6); "
            "got %r" % (what, value)
        )
    return [value[i] for i in range(len(value))]


def same_descriptor(left, right):
    """Whether two descriptors are the one action, by value (surface.md §2)."""
    if left is right:
        return True
    try:
        return bool(left == right)
    except Exception:
        return False


def descriptors_equal(left, right):
    """Whether two descriptor sequences are equal in value and order."""
    left = descriptor_list(left, "the first descriptor sequence")
    right = descriptor_list(right, "the second descriptor sequence")
    if len(left) != len(right):
        return False
    return all(same_descriptor(a, b) for a, b in zip(left, right))


def seat_fact(value):
    """The acting seat a ``seat`` fact names: its index and its button flag.

    environment.md §2 fixes the content — the seat's index, 0 or 1, as the fact's
    first number, and a boolean saying whether it holds the button — and leaves
    the container free, so a tuple, a list or a mapping all read here.
    """
    numbers = numbers_in(value)
    flags = bools_in(value)
    if not numbers or not flags:
        raise AssertionError(
            "the seat fact must carry the acting seat's index and whether it holds the "
            "button (environment.md §2); got %r" % (value,)
        )
    index = int(numbers[0])
    return index, flags[0]


def _seat_index(key):
    """A per-seat record's key read as a seat index, or ``None``."""
    if is_count(key) and int(key) in (0, 1):
        return int(key)
    digits = "".join(ch for ch in str(key) if ch.isdigit())
    if digits in ("0", "1"):
        return int(digits)
    return None


def seat_keyed(record, what):
    """A per-seat record read as ``{seat index: value}``, or a failure naming it."""
    if not isinstance(record, Mapping):
        raise AssertionError(
            "%s must be a mapping keyed by seat (surface.md §9); got %r" % (what, record)
        )
    out = {}
    for key, value in record.items():
        index = _seat_index(key)
        if index is None:
            raise AssertionError(
                "%s must be keyed by seat and carry nothing else (surface.md §9); key %r "
                "names no seat (the record is %r)" % (what, key, record)
            )
        out[index] = value
    if sorted(out) != [0, 1]:
        raise AssertionError(
            "%s must carry exactly one entry per seat (surface.md §9); got %r"
            % (what, record)
        )
    return out


def required(record, what, name):
    """One required key of a record, read by its letters and digits."""
    if not isinstance(record, Mapping):
        raise AssertionError(
            "%s must be a mapping (records.md §1); got %r" % (what, record)
        )
    want = token(name)
    for key, value in record.items():
        if token(key) == want:
            return value
    raise AssertionError(
        "%s is missing the required key %r (it carries %r)"
        % (what, name, sorted(str(key) for key in record))
    )


def decision_list(episode):
    """The ordered decisions of an episode record, as a list of mappings."""
    decisions = required(episode, "the episode record of play_hand", "decisions")
    if not is_indexable(decisions):
        raise AssertionError(
            "the episode's decisions must be an ordered sequence (records.md §5); got %r"
            % (decisions,)
        )
    out = [decisions[i] for i in range(len(decisions))]
    for position, decision in enumerate(out):
        if not isinstance(decision, Mapping):
            raise AssertionError(
                "decision %d of the episode must be a mapping (records.md §5); got %r"
                % (position, decision)
            )
        for fact in DECISION_FACTS:
            required(decision, "decision %d of the episode" % position, fact)
    return out


def decision_fact(decision, name):
    return required(decision, "a decision of the episode", name)


def leaves(obj, _depth=0):
    """Every non-mapping, non-sequence leaf of an observable value."""
    if _depth > 24:
        return [obj]
    if isinstance(obj, Mapping):
        out = []
        for value in obj.values():
            out.extend(leaves(value, _depth + 1))
        return out
    if isinstance(obj, (list, tuple, set, frozenset)):
        out = []
        for value in obj:
            out.extend(leaves(value, _depth + 1))
        return out
    return [obj]


# ---------------------------------------------------------------------------
# Policies: the battery's own plain callables (e2e-surface.md §2)
# ---------------------------------------------------------------------------
def policy_arguments(args, kwargs):
    """The ``(readout, legal_actions)`` pair a policy is called with.

    ``e2e-surface.md`` §2 fixes the call as ``policy(readout, legal_actions)`` and
    not whether the engine passes the two by position or by name, so both read
    here and anything else is a protocol violation.
    """
    values = list(args) + list(kwargs.values())
    if len(values) != 2:
        raise AssertionError(
            "a policy is called as policy(readout, legal_actions) (e2e-surface.md §2); "
            "it was called with args=%r and kwargs=%r" % (args, tuple(kwargs))
        )
    mappings = [value for value in values if isinstance(value, Mapping)]
    if len(mappings) != 1:
        raise AssertionError(
            "a policy is called with the readout mapping and the legal descriptors "
            "(e2e-surface.md §2); it was called with %r" % (values,)
        )
    readout = mappings[0]
    legal = values[1] if values[0] is readout else values[0]
    return readout, legal


def choose_call(readout, legal):
    """A policy that always continues: the check/call descriptor when it is legal."""
    for descriptor in descriptor_list(legal, "legal_actions"):
        if descriptor_kind(descriptor) == "check-call":
            return descriptor
    for descriptor in descriptor_list(legal, "legal_actions"):
        if descriptor_kind(descriptor) != "fold":
            return descriptor
    return legal[0]


def choose_fold(readout, legal):
    """A policy that folds whenever folding is legal, and continues otherwise."""
    for descriptor in descriptor_list(legal, "legal_actions"):
        if descriptor_kind(descriptor) == "fold":
            return descriptor
    return choose_call(readout, legal)


def choose_raise(readout, legal):
    """A policy that raises whenever raising is legal, and continues otherwise."""
    for descriptor in descriptor_list(legal, "legal_actions"):
        if descriptor_kind(descriptor) == "raise":
            return descriptor
    return choose_call(readout, legal)


class PolicyProbe:
    """A policy that asserts the protocol at each call and records what it saw.

    It is a policy in the sense of ``e2e-surface.md`` §2: called with the readout
    and the legal descriptors, returning one member of that list.  It checks that
    the call carries exactly those two things, that the readout is the whole
    ten-fact mapping, and that the legal list it is handed is the readout's own
    ``legal`` fact, then hands back the descriptor its chooser names.
    """

    def __init__(self, chooser=choose_call, name="the battery's policy"):
        self.chooser = chooser
        self.name = name
        self.calls = []

    def __call__(self, *args, **kwargs):
        readout, legal = policy_arguments(args, kwargs)
        declared = set(token(key) for key in readout)
        expected = set(token(fact) for fact in READOUT_FACTS)
        if declared != expected:
            raise AssertionError(
                "%s was called with a mapping whose keys are not exactly the ten facts "
                "(environment.md §2): %r" % (self.name, sorted(str(key) for key in readout))
            )
        descriptors = descriptor_list(legal, "the legal descriptors a policy is called with")
        if not descriptors:
            raise AssertionError(
                "%s was called with an empty legal list (surface.md §6)" % (self.name,)
            )
        if not descriptors_equal(descriptors, readout["legal"]):
            raise AssertionError(
                "%s was called with a legal list that is not the readout's own legal fact "
                "(environment.md §2): %r against %r"
                % (self.name, descriptors, readout["legal"])
            )
        action = self.chooser(readout, legal)
        if not any(same_descriptor(descriptor, action) for descriptor in descriptors):
            raise AssertionError(
                "%s returned a descriptor outside the legal list: %r" % (self.name, action)
            )
        self.calls.append({"readout": readout, "legal": descriptors, "action": action})
        return action


class IllegalAnswer:
    """A policy whose answer is not a descriptor of the decision it was handed."""

    def __init__(self):
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        policy_arguments(args, kwargs)
        return "not-an-action-of-this-decision"


class FoldWhenFree:
    """A policy that answers a free decision with a fold descriptor.

    Folding where checking is free is not an action of that decision
    (surface.md §2), so the answer is a descriptor outside ``legal_actions`` even
    though it is a real descriptor of the game.  Used to prove that
    ``play_hand`` refuses an out-of-list answer rather than folding for the
    violator (surface.md §10).
    """

    def __init__(self, fold_descriptor):
        self.fold_descriptor = fold_descriptor
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        readout, legal = policy_arguments(args, kwargs)
        free = one_number(readout["to_call"], "the readout's to_call fact") == 0
        if free:
            return self.fold_descriptor
        return choose_call(readout, legal)


class ExplodingPolicy:
    """A policy that raises its own error at every call (surface.md §10)."""

    def __init__(self):
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        raise PolicyFailure("the battery's policy refuses to choose an action")


class Step:
    """One decision of a walked hand: the handle, its facts, and the action taken."""

    __slots__ = ("hand", "readout", "legal", "action")

    def __init__(self, hand, readout, legal, action):
        self.hand = hand
        self.readout = readout
        self.legal = legal
        self.action = action


# ---------------------------------------------------------------------------
# The base case the battery is written on
# ---------------------------------------------------------------------------
class EngineCase(unittest.TestCase):
    """One battery case, written in the nine entry points and nothing below them."""

    # -- the nine entry points ---------------------------------------------
    def ep(self, name):
        return entry(name)

    def game_config(self):
        return self.ep("game_config")()

    def new_hand(self, seed):
        return self.ep("new_hand")(seed)

    def readout(self, hand):
        return self.ep("readout")(hand)

    def legal_actions(self, hand):
        return self.ep("legal_actions")(hand)

    def apply_action(self, hand, action):
        return self.ep("apply_action")(hand, action)

    def is_terminal(self, hand):
        return self.ep("is_terminal")(hand)

    def payoffs(self, hand):
        return self.ep("payoffs")(hand)

    def play_hand(self, seed, seat0, seat1):
        return self.ep("play_hand")(seed, seat0, seat1)

    def equity(self, decision, seed, samples):
        return self.ep("equity")(decision, seed, samples)

    # -- walks -------------------------------------------------------------
    def walk(self, seed, chooser=None, limit=DECISION_BOUND):
        """Drive one hand to its end; returns its decisions and its final handle."""
        if chooser is None:
            chooser = choose_call
        hand = self.new_hand(seed)
        steps = []
        while len(steps) < limit and not self.is_terminal(hand):
            readout = self.readout(hand)
            legal = self.legal_actions(hand)
            action = chooser(readout, legal)
            steps.append(Step(hand, readout, legal, action))
            hand = self.apply_action(hand, action)
        return steps, hand

    def finished_hand(self, seed, chooser=None, limit=DECISION_BOUND):
        """One completed hand handle at ``seed``, played by the battery's policy."""
        steps, hand = self.walk(seed, chooser, limit)
        self.assertTrue(
            self.is_terminal(hand),
            "a hand must end within %d decisions (surface.md §8, ASM-6); seed %r took "
            "at least that many" % (limit, seed),
        )
        return hand

    # -- refusals ----------------------------------------------------------
    def assert_refused(self, call, what, words=()):
        """Assert ``call`` is refused by an error, never accepted and never swallowed.

        surface.md §1: an invalid argument is refused by raising an error that
        names the violated contract, and no entry point coerces a value,
        substitutes a default, swallows an error or returns part of a record.
        """
        try:
            returned = call()
        except Exception as exc:  # the refusal itself
            text = "%s: %s" % (type(exc).__name__, exc)
            if words and not any(word.lower() in text.lower() for word in words):
                self.fail(
                    "%s must be refused by an error that names the violated contract "
                    "(surface.md §1); it raised %s" % (what, text)
                )
            return exc
        self.fail(
            "%s must be refused, not accepted (surface.md §1); it returned %r"
            % (what, returned)
        )

    # -- the global stream -------------------------------------------------
    @staticmethod
    def stream():
        """The state of Python's global ``random``, the deal stream (ASM-2)."""
        return random.getstate()

    def assert_stream_unchanged(self, call, what):
        """Assert ``call`` hands the caller's deal stream back as it found it."""
        before = self.stream()
        result = call()
        after = self.stream()
        self.assertEqual(
            canon(before),
            canon(after),
            "%s must leave the global random stream as it found it (surface.md §1 rule 4)"
            % (what,),
        )
        return result

    # -- decisions ---------------------------------------------------------
    @staticmethod
    def free_decision(steps):
        """The first decision of a walked hand at which checking costs nothing."""
        for step in steps:
            if one_number(step.readout["to_call"], "the readout's to_call fact") == 0:
                return step
        raise AssertionError(
            "the battery needs a decision where to_call is 0; this walk has none"
        )

    @staticmethod
    def fold_descriptor(legal):
        """A fold descriptor, taken from a decision where folding is legal."""
        for descriptor in descriptor_list(legal, "legal_actions"):
            if descriptor_kind(descriptor) == "fold":
                return descriptor
        raise AssertionError(
            "facing the big blind, folding is legal: legal_actions is %r" % (legal,)
        )
