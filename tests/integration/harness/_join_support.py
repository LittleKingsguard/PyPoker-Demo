"""Join plumbing and invented instances for the `harness` integration battery.

This module is test support, not a subsystem (brief §5, `module-map.md` §5).  It does
three things and nothing else:

* it puts ``<repo>/src`` on ``sys.path`` and imports the six packages of the map lazily,
  so a missing surface is one ``SurfaceAbsent`` failure in the case that needed it and
  never a collection error (`battery.md` §2);
* it holds the battery's *invented instances* -- two deal seeds, a cell size and its
  seed, a learner seed and size, two baseline seeds, two seam labels, an undeclared
  factory kind, an undeclared expectation kind and the non-quantity means a cell-shaped
  value is composed with -- none of which appears in a design document or in
  `tests/e2e/` (`docs/L1/battery.md` §4, D-15).  No encoder, learner,
  baseline, hand, rung configuration or pool is fabricated here: every one is what
  ``harness.factory`` returns, which is the owning module's own object
  (`docs/L2/harness/surface.md` §4, D-13);
* it holds the *seven joins* `docs/L1/battery.md` §5 calls the invariants a single
  module cannot check about itself, as they bear on this module's edge:

      HRNJ-1  harness x the five modules   a driven case's steps are theirs: each step
                                           called once in order, a refusal an
                                           observation, the verdict `expect`'s
      HRNJ-2  harness x the owners         a factory builds the owner's own object,
                                           and the owner's refusal arrives unchanged
      HRNJ-3  harness x engine and agents  a seam is a policy of `e2e-surface.md` §2
                                           inside a real, zero-sum engine episode
      HRNJ-4  harness x records            the four kinds read what the modules really
                                           return, totally and deterministically
      HRNJ-5  harness x measured work      `timings()` is the cost the driver collected
      HRNJ-6  harness x the process        one scratch root, the protocol's seed, the
                                           device of D-8, the kind list of §6
      HRNJ-7  determinism, ASM-2           only dealing, and only through `factory`,
                                           moves the global `random` stream

It also holds tolerant readers for the shapes a record leaves free -- a decision's
``seat``, a pool member's pinned flag, a chosen index under `records.md` §6 -- plus the
expensive observables the battery shares: one pool, one cell, one episode, one encoder
and one readout, each built once per process and reused (`docs/L1/battery.md` §2).  A
cell here is eleven hands and a training budget is never run: the joins this battery
judges are joins, not measurements (ASM-15, D-6).

Nothing here reaches past a declared entry point: the six names of
``docs/L2/harness/surface.md`` §2-§7 and, at the consumed edge, `engine.play_hand`,
`readout`, `legal_actions`, `new_hand`, `apply_action`, `is_terminal`, `features.encode`,
`encode`, `legal_indices`, `decode_action`, `observation_spec`, `agents.build_learner`,
`param_count`, `act`, `as_policy`, `build_baseline`, `baselines`, `evaluation.build_pool`,
`pool_members`, `match`, `protocol` and `training.rung`, `fairness`, `devices`.  No
``_``-name of any package is imported, and the harness's own private names are never
touched: the surface is the six entry points and nothing below them (`docs/L2/harness/
README.md` §3, D-13).

Each case module loads this file under the private name ``harness_join_support``: the
repository's integration batteries share the file name ``_join_support.py``, and a plain
import would let one battery's helpers stand in for another's when two test directories
are collected in one process.
"""

from __future__ import annotations

import copy
import importlib
import json
import numbers
import os
import random
import sys
import unittest

# --------------------------------------------------------------------------
# The six packages, imported lazily.
# --------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

_MODULES = {}


class SurfaceAbsent(AssertionError):
    """One package this battery consumes is not importable at all."""


def mod(name):
    """The named package, imported on first use (one clear failure if absent)."""
    if name in _MODULES:
        return _MODULES[name]
    try:
        package = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - the failure is the finding, not the class
        raise SurfaceAbsent(
            "the %r package is not importable from %r (%s: %s); this join cannot be "
            "judged without it" % (name, SRC, type(exc).__name__, exc)
        ) from None
    _MODULES[name] = package
    return package


# --------------------------------------------------------------------------
# Invented instances.  These values are the test writer's own; no document in
# docs/ carries them and `tests/e2e/` uses none of them (`docs/L1/battery.md`
# §4, D-15).  The values a document *does* carry -- the protocol's seed 0, the
# device `cpu`, the four expectation kinds, the six factory kinds and R1's name --
# appear below because a case deliberately pins them (`surface.md` §3, §4, §6).
# --------------------------------------------------------------------------
DEAL_SEED = 613597          # the episode and the walk the seams answer, invented
DEAL_SEED_OTHER = 240713    # a second deal, so a step has two hands to play
MATCH_SEED = 550613         # the battery's one cell seed, invented
HANDS_SMALL = 11            # that cell's hand count, invented (the league's is 120)
LEARNER_SEED = 7307         # the invented learner spec's seed
WIDTH = 8                   # the invented learner's width
DEPTH = 2                   # the invented learner's depth
BASELINE_SEED = 613         # the seeded baseline's own seed, invented
BASELINE_SEED_OTHER = 977   # the other policy's seed, invented
SEAM_LABEL = "join-probe-alpha"      # a label in no design document, invented
SEAM_LABEL_CYCLE = "synthetic"       # the documented cyclic behaviour
SEAM_LABEL_RECORDING = "recording"   # the documented first-descriptor behaviour
ENCODING = "flat-numeric"   # R1's declared encoding (`ladder.md` §2) -- a fixed name
RUNG_NAME = "R1"            # the first declared rung -- a fixed name
RUNG_NEXT = "R2"
UNDECLARED_OBJECT = "deck-of-cards"       # a kind the map does not declare, invented
UNKNOWN_ENCODING = "join-probe-no-such-encoding"
UNKNOWN_KIND = "join-probe-no-such-expectation"
WALK_LIMIT = 30             # a walk is bounded; a hand that outlasts this is a defect

# The means a cell-shaped value is composed with when the battery needs one the kind cannot
# read as a quantity (`docs/L2/harness/surface.md` §6 reads a cell's deltas "from ... a cell
# record's two directions' `mean_chip_delta`").  Each pair is ``(label, first, second)``:
# a string, a `None`, and a boolean beside a number -- the boolean pair sums to zero under
# Python's arithmetic, which is why it is the one a reader that does not keep quantities
# only would pass.  The string is the test writer's own (`docs/L1/battery.md` §4, D-15).
UNREADABLE_MEANS = (
    ("a string mean", "join-probe-not-a-quantity", 0.0),
    ("a None mean", None, 0.0),
    ("a boolean mean beside a number", True, -1),
)

# The declarations of `docs/L2/harness/surface.md` this battery asserts: the four
# expectation kinds in §6's order (the first judges an episode record, H-1) and the six
# factory kinds of §4.  These are this module's declared vocabulary, not an instance a
# case invents (`e2e-surface.md` §3.6, `records.md` §14, D-13).
DECLARED_KINDS = ("zero-sum", "legal-choice", "counted", "refused")
DECLARED_OBJECTS = ("baseline", "encoder", "hand", "learner", "pool", "rung")

# `records.md` §5, §9 and §14: the **required** keys this battery reads.
EPISODE_KEYS = ("seed", "decisions", "payoffs")
DECISION_KEYS = ("seat", "readout", "legal", "action", "reward")
CELL_KEYS = ("members", "hands", "directions", "params", "seed")
DIRECTION_KEYS = ("wins", "ties", "losses", "mean_chip_delta", "seat_split")
DRIVER_KEYS = ("id", "steps", "expectations", "hands", "wall_clock_seconds",
               "verdict", "reason")
STEP_KEYS = ("index", "outcome", "refused", "seconds")
EXPECTATION_KEYS = ("kind", "step", "verdict", "reason")
TIMING_KEYS = ("hands", "wall_clock_seconds", "seconds_per_hand",
               "hands_per_second", "cases", "steps")
FIXTURE_KEYS = ("root", "seed", "device", "expectations")
VERDICT_KEYS = ("kind", "verdict", "reason")


# --------------------------------------------------------------------------
# The call vocabulary: one wrapper per declared entry point this battery drives.
# --------------------------------------------------------------------------
def drive(case):
    return mod("harness").drive(case)


def fixtures():
    return mod("harness").fixtures()


def factory(kind, options):
    return mod("harness").factory(kind, options)


def seam(label):
    return mod("harness").seam(label)


def expect(kind, observation):
    return mod("harness").expect(kind, observation)


def timings():
    return mod("harness").timings()


def new_hand(seed):
    return mod("engine").new_hand(seed)


def readout(hand):
    return mod("engine").readout(hand)


def legal_actions(hand):
    return mod("engine").legal_actions(hand)


def apply_action(hand, descriptor):
    return mod("engine").apply_action(hand, descriptor)


def is_terminal(hand):
    return mod("engine").is_terminal(hand)


def payoffs(hand):
    return mod("engine").payoffs(hand)


def play_hand(seed, seat0_policy, seat1_policy):
    return mod("engine").play_hand(seed, seat0_policy, seat1_policy)


def build_encoder(name):
    return mod("features").build_encoder(name)


def observation_spec(encoder):
    return mod("features").observation_spec(encoder)


def encode(encoder, readout_record):
    return mod("features").encode(encoder, readout_record)


def legal_indices(legal):
    return tuple(mod("features").legal_indices(list(legal)))


def decode_action(index):
    return mod("features").decode_action(index)


def build_learner(spec):
    return mod("agents").build_learner(spec)


def param_count(learner):
    return mod("agents").param_count(learner)


def act(learner, observation, legal_mask):
    return mod("agents").act(learner, observation, legal_mask)


def as_policy(learner, encoder, seed):
    return mod("agents").as_policy(learner, encoder, seed)


def build_baseline(name, seed):
    return mod("agents").build_baseline(name, seed)


def baselines():
    return mod("agents").baselines()


def build_pool(declaration):
    return mod("evaluation").build_pool(declaration)


def pool_members(pool):
    return mod("evaluation").pool_members(pool)


def match(left, right, hands, seed):
    return mod("evaluation").match(left, right, hands, seed)


def protocol():
    return mod("evaluation").protocol()


def rung(name):
    return mod("training").rung(name)


def fairness(left, right):
    return mod("training").fairness(left, right)


def devices():
    return mod("training").devices()


# --------------------------------------------------------------------------
# Tolerant readers.  A case asserts the contract, never a spelling of its own.
# --------------------------------------------------------------------------
def canon(value):
    """One record compared by value, whatever container a design chose."""
    return json.dumps(value, sort_keys=True, default=str)


def token(text):
    return "".join(ch for ch in str(text).lower() if ch.isalnum())


def as_plain(value):
    """One observation as plain data, so two of them compare by value.

    `features.encode` returns a NumPy array (`features/surface.md` §6), and an array is
    opaque to `==`; a battery compares the values it carries.
    """
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        return tolist()
    return value


def finite(value):
    return (
        isinstance(value, numbers.Real)
        and not isinstance(value, bool)
        and float(value) == float(value)
    )


def refusal_of(call):
    """What one call did: ``(False, None, value)`` or ``(True, class name, message)``.

    The exception class is tolerated: which class an owning module raises is its own
    freedom, and what a join asserts is that the refusal reached the caller named and
    unrepaired (`e2e-surface.md` §2, `docs/L2/harness/surface.md` §4).
    """
    try:
        return False, None, call()
    except SurfaceAbsent:
        raise
    except Exception as exc:  # noqa: BLE001 - the class is the owner's freedom
        return True, type(exc).__name__, str(exc)


def verdict_of(record):
    """The verdict one verdict or case-result record states (`surface.md` §6)."""
    if not isinstance(record, dict):
        return None
    return record.get("verdict")


def reason_of(record):
    if not isinstance(record, dict):
        return None
    return record.get("reason")


def chosen_index(decision):
    """The chosen index out of `agents.act`'s return (`records.md` §6)."""
    if isinstance(decision, int) and not isinstance(decision, bool):
        return int(decision)
    if isinstance(decision, dict):
        for key, value in decision.items():
            if any(part in str(key).lower() for part in ("action", "index", "choice")):
                if isinstance(value, int) and not isinstance(value, bool):
                    return int(value)
    raise AssertionError(
        "cannot read an action index out of agents.act's return: %r" % (decision,)
    )


def same_descriptor(left, right):
    """Two descriptors compared by value (`docs/L2/engine/surface.md` §2)."""
    try:
        return bool(left == right)
    except Exception:  # noqa: BLE001 - an exotic descriptor still prints stably
        return str(left) == str(right)


def seat_index(seat):
    """The seat number out of a record's ``seat``, which may carry the button too.

    `e2e-surface.md` §2 makes the readout's `seat` "the acting seat, and whether it is
    the button", so it is read positionally: the first entry of a sequence, or the
    number itself.
    """
    if isinstance(seat, (tuple, list)):
        if not seat:
            raise AssertionError("a decision's `seat` is empty: %r" % (seat,))
        seat = seat[0]
    if isinstance(seat, bool) or not isinstance(seat, int):
        raise AssertionError("a decision's `seat` carries no seat number: %r" % (seat,))
    return int(seat)


def pinned(member):
    """Whether a `records.md` §8 member is one of the three pinned baselines."""
    if not isinstance(member, dict):
        return False
    if member.get("pinned") or member.get("baseline"):
        return True
    return str(member.get("id")) in set(baseline_names())


def member_ids(pool_record):
    return [str(member["id"]) for member in pool_record["members"]]


def baseline_names():
    return [str(name) for name in baselines()]


def pool_declaration():
    """R1's own pool declaration, as `training.rung` resolves it.

    `training/surface.md` §3 makes a configuration's `pool` entry the declaration the
    run freezes -- the inherited lineage, the bound `m`, the frozen flag, the version
    window and the `id` every arm's run record carries -- so the battery reads a real
    declaration from the owner instead of writing one (`records.md` §8, ASM-16).
    """
    return rung(RUNG_NAME)["pool"]


def readout_and_legal(seed):
    """One real readout and its legal descriptors, from the engine's deal at `seed`."""
    hand = new_hand(seed)
    return readout(hand), tuple(legal_actions(hand))


def logged_calls(policy):
    """A seam's `calls` log, read as ``[(readout, legal, chosen), ...]``.

    `docs/L2/harness/surface.md` §5 makes the `calls` sequence contract -- "one record
    per call, in call order, holding the `readout` and the `legal_actions` it was handed
    and the descriptor it returned" -- while the keys of one entry are the design's own
    (`docs/L2/harness/README.md` §7).  So the entry is read by what its values are: the
    mapping it was handed, the descriptor set, and the descriptor it returned.
    """
    calls = getattr(policy, "calls", None)
    if calls is None:
        raise AssertionError(
            "a seam must record every call it answered, in a `calls` sequence on the "
            "returned policy (docs/L2/harness/surface.md §5, H-3): %r" % (policy,)
        )
    out = []
    for entry in calls:
        values = list(entry.values()) if isinstance(entry, dict) else list(entry)
        handed = None
        legal = None
        for value in values:
            if handed is None and isinstance(value, dict):
                handed = value
            elif (legal is None and isinstance(value, (tuple, list)) and value
                  and all(not isinstance(item, (dict, list, tuple)) for item in value)):
                legal = list(value)
        chosen = None
        if legal is not None:
            for value in values:
                if isinstance(value, (tuple, list)):
                    continue
                if any(same_descriptor(value, candidate) for candidate in legal):
                    chosen = value
                    break
        out.append((handed, legal, chosen))
    return out


def walk(seed, limit=WALK_LIMIT):
    """A real hand's decision sequence: ``[(readout, legal), ...]`` in played order.

    The hand is the engine's, advanced through `engine.apply_action` with its own last
    legal descriptor, so the sequence is one a policy would really be called over -- the
    shape a seam answers (`e2e-surface.md` §2).  Nothing is invented: the readouts and
    the legal sets are the engine's, and the hand is dealt at `seed` (ASM-2).
    """
    hand = new_hand(seed)
    decisions = []
    while not is_terminal(hand) and len(decisions) < limit:
        descriptor = tuple(legal_actions(hand))
        decisions.append((readout(hand), descriptor))
        hand = apply_action(hand, descriptor[-1])
    return decisions


def finished_hand(seed, limit=WALK_LIMIT):
    """One completed hand handle, played to its end by its own last legal descriptor.

    `engine.payoffs` takes a completed hand (`engine/surface.md` §9), so a battery that
    wants the engine's own per-seat mapping has to finish a hand through
    `engine.apply_action` -- and the hand it finishes is the engine's, dealt at `seed`
    (ASM-2).
    """
    hand = new_hand(seed)
    steps = 0
    while not is_terminal(hand) and steps < limit:
        hand = apply_action(hand, tuple(legal_actions(hand))[-1])
        steps += 1
    if not is_terminal(hand):
        raise AssertionError(
            "the battery's hand must end within %d decisions -- short stacks and the "
            "raise cap bound it, and a hand still running is a defect "
            "(docs/L2/engine/surface.md §8, ASM-6): seed %r" % (limit, seed)
        )
    return hand


def learner_spec(seed=LEARNER_SEED, width=WIDTH, depth=DEPTH):
    """One invented learner spec in `records.md` §3's shape.

    `architecture` is authoritative and carries the declared kind, so the learner is
    sized from the kind's `observation_size` -- the encoder-less build of
    `agents/surface.md` §4, which is the one a battery may assemble itself (`records.md`
    §3, D-3).
    """
    return {
        "backend": "numpy",
        "architecture": {"kind": "naive-stack", "width": int(width), "depth": int(depth)},
        "seed": int(seed),
    }


# --------------------------------------------------------------------------
# The module-level fixtures, built once per process and shared.
# --------------------------------------------------------------------------
_SHARED = {}


def shared_pool():
    """The pool `factory` builds from R1's own declaration (once per process)."""
    if "pool" not in _SHARED:
        _SHARED["pool"] = factory("pool", pool_declaration())
    return _SHARED["pool"]


def shared_cell():
    """One real cell: the two pinned baselines at the battery's hand count and seed."""
    if "cell" not in _SHARED:
        _SHARED["cell"] = match("always-call", "random", HANDS_SMALL, MATCH_SEED)
    return _SHARED["cell"]


def cell_shaped_like(first_mean, second_mean, cell=None):
    """A cell-shaped value carrying a real cell's own record and two given means.

    `docs/L2/harness/surface.md` §6 reads a cell's deltas "from ... a cell record's two
    directions' `mean_chip_delta`", and §2 lets a case judge a value it composed
    (FAM-14.10).  So the value is `evaluation.match`'s own cell -- the battery's shared
    one, or the record a step just played -- with nothing replaced but those two means:
    its keys, counts, `hands`, `members` and `seed` stay the league's, and the battery
    invents no cell record and no direction.
    """
    value = copy.deepcopy(shared_cell() if cell is None else cell)
    rows = value["directions"]
    rows[0]["mean_chip_delta"] = first_mean
    rows[1]["mean_chip_delta"] = second_mean
    return value


def shared_episode():
    """One real episode: two declared baselines playing one seeded hand."""
    if "episode" not in _SHARED:
        _SHARED["episode"] = play_hand(
            DEAL_SEED,
            build_baseline("always-call", BASELINE_SEED),
            build_baseline("random", BASELINE_SEED_OTHER),
        )
    return _SHARED["episode"]


def shared_walk():
    """The decision sequence of one real hand, built once and shared."""
    if "walk" not in _SHARED:
        _SHARED["walk"] = walk(DEAL_SEED)
    return _SHARED["walk"]


def shared_payoffs():
    """`engine.payoffs` of one completed hand, built once and shared."""
    if "payoffs" not in _SHARED:
        _SHARED["payoffs"] = payoffs(finished_hand(DEAL_SEED_OTHER))
    return _SHARED["payoffs"]


def shared_encoder():
    """The encoder `factory` builds from R1's declared encoding."""
    if "encoder" not in _SHARED:
        _SHARED["encoder"] = factory("encoder", ENCODING)
    return _SHARED["encoder"]


# --------------------------------------------------------------------------
# The base case: the readers every join uses.
# --------------------------------------------------------------------------
class JoinCase(unittest.TestCase):
    """The base every case extends: record readers and the refusal joins."""

    def assert_required_keys(self, record, keys, what, citation):
        """Require a returned record to carry the keys `records.md` marks required."""
        self.assertIsInstance(
            record, dict,
            "%s must be a plain mapping (%s): %r" % (what, citation, record),
        )
        for key in keys:
            self.assertIn(
                key, record,
                "%s must carry its required key %r (%s, records.md §1): %r"
                % (what, key, citation, sorted(record)),
            )

    def assert_refusal(self, call, tokens, note, citation):
        """Require `call` to be refused, naming the tokens the refusal must carry."""
        raised, klass, detail = refusal_of(call)
        self.assertTrue(
            raised,
            "%s: this call must be refused (%s), but it returned %r"
            % (note, citation, detail),
        )
        lowered = str(detail).lower()
        for group in tokens:
            alternatives = (group,) if isinstance(group, str) else tuple(group)
            if not any(str(alternative).lower() in lowered for alternative in alternatives):
                self.fail(
                    "%s: the refusal must name one of %r (%s); the message was %r"
                    % (note, alternatives, citation, detail),
                )
        return klass, detail

    def assert_same_refusal(self, through, direct, what, citation):
        """Require the refusal that reached `through` to be `direct`'s, unchanged.

        `docs/L2/harness/surface.md` §4: a factory "validates nothing about `options`"
        and "a refusal the owning entry point raises" surfaces "as it is, named and
        never repaired" (`e2e-surface.md` §2, D-13) -- so the class name and the message
        the owning entry point produces are the ones the caller must see.
        """
        raised_direct, class_direct, message_direct = refusal_of(direct)
        self.assertTrue(
            raised_direct,
            "%s: the owning entry point must refuse this argument, or there is no "
            "refusal for the factory to carry (%s)" % (what, citation),
        )
        raised_through, class_through, message_through = refusal_of(through)
        self.assertTrue(
            raised_through,
            "%s: the factory must pass the owner's refusal on rather than repair it "
            "(%s), but it returned %r" % (what, citation, message_through),
        )
        self.assertEqual(
            (class_direct, message_direct),
            (class_through, message_through),
            "%s: the refusal the factory surfaces must be the owning entry point's own "
            "-- same class, same message -- and never a second spelling of it (%s): "
            "%r against %r" % (what, citation, (class_through, message_through),
                               (class_direct, message_direct)),
        )
        return class_through, message_through

    def assert_descriptor_in(self, legal, descriptor, note, citation):
        self.assertTrue(
            any(same_descriptor(descriptor, candidate) for candidate in legal),
            "%s: the descriptor %r must be one of legal_actions %r (%s)"
            % (note, descriptor, list(legal), citation),
        )

    def assert_verdict(self, record, expected, what, citation):
        """Require one verdict record (or case result) to state `expected`."""
        self.assertIn(
            verdict_of(record), ("pass", "fail"),
            "%s must state `pass` or `fail` in `verdict` (%s): %r"
            % (what, citation, record),
        )
        self.assertEqual(
            verdict_of(record), expected,
            "%s must be %r (%s): %r" % (what, expected, citation, record),
        )
        if expected == "pass":
            self.assertIsNone(
                reason_of(record),
                "%s passes, so its `reason` is None: a pass that argued for a failure "
                "would not be a record (%s): %r" % (what, citation, record),
            )
        else:
            self.assertIsInstance(
                reason_of(record), str,
                "%s fails, so its `reason` is one sentence naming what failed (%s): %r"
                % (what, citation, record),
            )

    def assert_finite(self, value, what, citation):
        self.assertTrue(
            finite(value),
            "%s must be one finite number (%s); it is %r" % (what, citation, value),
        )
        return float(value)

