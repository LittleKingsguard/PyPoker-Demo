"""Join plumbing and invented instances for the `agents` integration battery.

This module is test support, not a subsystem (brief §5, `module-map.md` §5).  It
does four things and nothing else:

* it puts ``<repo>/src`` on ``sys.path`` and imports ``engine``, ``features`` and
  ``agents`` lazily, so a missing surface is one ``SurfaceAbsent`` failure in the
  case that needed it and never a collection error (`battery.md` §2);
* it holds the battery's *invented instances* — deal seeds, learner seeds, widths,
  depths, a sparsity, hand counts, masks and invented checkpoint file names — none
  of which appears in a design document (`docs/L1/battery.md` §4, D-15).  An
  observation is never fabricated: every one is ``features.encode`` of a readout
  dealt by ``engine.new_hand``, because the consumed edge has one declared producer
  of an observation (`docs/L2/features/surface.md` §6) and an invented observation
  would judge nothing;
* it holds *tolerant readers* for the shapes the design leaves free: the index out
  of ``agents.act``'s return (`docs/L1/records.md` §6), a policy's descriptor
  compared by value, a decision record's fields, a reward and a seat out of an
  episode record (`records.md` §5), the two statistics of ``agents.learn``
  (`docs/L2/agents/surface.md` §7) and a finite-number check.  A case asserts the
  contract through these readers instead of inventing a spelling of its own;
* it holds the small call vocabulary the cases are written in — one wrapper per
  entry point the three modules publish, a decision walk, transition records over a
  played episode, a recording policy, and the two caller-side policies the
  baselines case needs.

Nothing here reaches past an entry point of `e2e-surface.md` §3.3 or of the two
consumed surfaces (`docs/L2/engine/surface.md`, `docs/L2/features/surface.md`).
Each case module loads this file under the private name ``agents_join_support``: the
repository's integration batteries share the file name ``_join_support.py``, and a
plain import would let one battery's helpers stand in for another's when two test
directories are collected in one process.
"""

from __future__ import annotations

import importlib
import math
import numbers
import os
import shutil
import sys
import tempfile
import unittest
from collections.abc import Mapping

# --------------------------------------------------------------------------
# The three packages, imported lazily.
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
# Invented instances.  These numbers are the test writer's own; no document in
# docs/ carries them (docs/L1/battery.md §4, D-15).  The protocol's own numbers
# appear below only where a case deliberately reads them out of a published
# catalogue (the oracle's equity sample count, the exploration schedule's
# `samples`), never as a literal.
# --------------------------------------------------------------------------
DEAL_DECISION_A = 74011      # deals the battery plays, invented
DEAL_DECISION_B = 31817
DEAL_DECISION_C = 90277
DEAL_POLICY_A = 55109
DEAL_POLICY_B = 68041
DEAL_REWARD_A = 12007
DEAL_REWARD_B = 93551
DEAL_TOKEN_A = 47209
DEAL_TOKEN_B = 13553
DEAL_CHECKPOINT_A = 24611
DEAL_CHECKPOINT_B = 37013
DEAL_SEED_A = 48109
DEAL_SEED_B = 59221
DEAL_ORACLE_A = 20024       # the two deals the oracle case plays in both seats
DEAL_ORACLE_B = 20047

LEARNER_SEED = 81349         # learner seeds, invented
LEARNER_SEED_OTHER = 26699
LEARNER_SEED_BLIND = 61027
POLICY_SEED = 40813
BASELINE_SEED = 35729
BASELINE_SEED_OTHER = 70241

WIDTH_ONE = 9                # widths and depths, invented (small: 8-24, 1-3)
WIDTH_TWO = 14
WIDTH_THREE = 23
DEPTH_ONE = 1
DEPTH_TWO = 2
DEPTH_THREE = 3
SPARSITY = 0.35

MASK_ONE = (1,)              # masks, invented
MASK_PAIR = (1, 2)
MASK_ALL = (0, 1, 2)

BATCH_LENGTH = 5             # a batch length, invented
HANDS_TWO = 2
HANDS_THREE = 3
STREAM_SEED_A = 9173         # seeds for the global `random` stream, invented
STREAM_SEED_B = 4621
STREAM_DRAWS = 8

CHECKPOINT_ALPHA = "join-invented-alpha.ckpt"   # checkpoint names, invented
CHECKPOINT_BETA = "join-invented-beta.pt"
CHECKPOINT_GAMMA = "join-invented-gamma.npz"
CHECKPOINT_MISSING = "join-invented-delta.ckpt"

REFUSAL_MASKS = ((), (0, 1, 1), (0, 3))          # masks a decision cannot produce


# --------------------------------------------------------------------------
# The small call vocabulary: one wrapper per published entry point.
# --------------------------------------------------------------------------
def learners():
    return mod("agents").learners()


def build_learner(spec):
    return mod("agents").build_learner(spec)


def param_count(learner):
    return mod("agents").param_count(learner)


def act(learner, observation, legal_mask):
    return mod("agents").act(learner, observation, legal_mask)


def learn(learner, transitions):
    return mod("agents").learn(learner, transitions)


def save(learner, path):
    return mod("agents").save(learner, path)


def load(spec, path):
    return mod("agents").load(spec, path)


def as_policy(learner, encoder, seed):
    return mod("agents").as_policy(learner, encoder, seed)


def baselines():
    return mod("agents").baselines()


def build_baseline(name, seed):
    return mod("agents").build_baseline(name, seed)


def build_encoder(name):
    return mod("features").build_encoder(name)


def observation_spec(encoder):
    return mod("features").observation_spec(encoder)


def encode(encoder, readout):
    return mod("features").encode(encoder, readout)


def legal_indices(legal_actions):
    return tuple(mod("features").legal_indices(legal_actions))


def decode_action(index):
    return mod("features").decode_action(index)


def encodings():
    return mod("features").encodings()


def action_space():
    return mod("features").action_space()


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


def equity(decision, seed, sample_count):
    return mod("engine").equity(decision, seed, sample_count)


# --------------------------------------------------------------------------
# The catalogue-derived pairing: each architecture kind's encoding is the one
# features declares for the representation family the kind consumes
# (docs/L2/agents/surface.md §3, docs/L2/features/surface.md §3).
# --------------------------------------------------------------------------
def encoding_for(kind):
    """The encoding name whose observation family the kind's catalogue entry names."""
    catalogue = learners()["architectures"]
    if kind not in catalogue:
        raise AssertionError(
            "agents.learners() declares no %r architecture kind; it declares %r"
            % (kind, sorted(catalogue))
        )
    family = catalogue[kind]["observation"]
    declared = [
        name
        for name, spec in encodings().items()
        if spec.get("kind") == family
    ]
    if len(declared) != 1:
        raise AssertionError(
            "features.encodings() must declare exactly one encoding of the %r family "
            "the kind %r consumes; it declared %r" % (family, kind, declared)
        )
    return declared[0]


def learner_spec(kind, width, depth, seed, backend="numpy", encoding=None, **settings):
    """One learner spec (`docs/L1/records.md` §3) sized from the kind's encoding."""
    architecture = {"kind": kind, "width": width, "depth": depth}
    architecture.update(settings)
    return {
        "backend": backend,
        "architecture": architecture,
        "seed": seed,
        "encoder": build_encoder(encoding or encoding_for(kind)),
    }


def learner(kind="naive-stack", width=WIDTH_TWO, depth=DEPTH_TWO, seed=LEARNER_SEED,
            backend="numpy", encoding=None, **settings):
    """A built learner, from the spec above through `agents.build_learner`."""
    return build_learner(
        learner_spec(kind, width, depth, seed, backend, encoding, **settings)
    )


def exploration_samples():
    """The sample count the exploration schedule anneals over (`surface.md` §3)."""
    schedule = _lookup(learners()["hyper"], ("exploration", "schedule", "epsilon"),
                       "learners()['hyper']'s exploration schedule")
    return int(_lookup(schedule, ("samples", "anneal", "decisions"),
                       "the exploration schedule's sample count"))


def oracle_samples():
    """The sample count `baselines()` declares for the oracle's equity query."""
    declared = _lookup(baselines()["oracle"], ("equity_samples", "samples"),
                       "the oracle baseline's declared sample count")
    return int(declared)


# --------------------------------------------------------------------------
# Tolerant readers.  A case asserts the contract, never a spelling of its own.
# --------------------------------------------------------------------------
def _lookup(mapping, needles, what):
    if not isinstance(mapping, Mapping):
        raise AssertionError(
            "cannot read %s out of %r: it is not a mapping" % (what, mapping)
        )
    for key, value in mapping.items():
        lowered = str(key).lower()
        if any(needle in lowered for needle in needles):
            return value
    raise AssertionError(
        "cannot read %s out of %r: no key carries any of %r"
        % (what, mapping, tuple(needles))
    )


def action_index(result):
    """The chosen index out of `agents.act`'s return (`records.md` §6)."""
    if isinstance(result, int) and not isinstance(result, bool):
        return int(result)
    if isinstance(result, (tuple, list)):
        for value in result:
            if isinstance(value, int) and not isinstance(value, bool):
                return int(value)
    if isinstance(result, Mapping):
        for key, value in result.items():
            if any(part in str(key).lower() for part in ("action", "index", "move", "choice")):
                if isinstance(value, int) and not isinstance(value, bool):
                    return int(value)
    raise AssertionError(
        "cannot read an action index out of agents.act's return: %r" % (result,)
    )


def same_descriptor(left, right):
    """Two action descriptors compared by value (`engine/surface.md` §2)."""
    try:
        return bool(left == right)
    except Exception:  # noqa: BLE001 - an exotic descriptor still prints stably
        return str(left) == str(right)


def descriptor_index(legal, descriptor):
    """The vocabulary index of `descriptor` in `legal`, position-aligned."""
    actions = list(legal)
    indices = list(legal_indices(actions))
    for position, candidate in enumerate(actions):
        if same_descriptor(candidate, descriptor):
            return indices[position]
    raise AssertionError(
        "the descriptor %r is not one of legal_actions %r"
        % (descriptor, actions)
    )


def episode_seed(record):
    return _lookup(record, ("seed",), "an episode record's seed")


def episode_decisions(record):
    return list(_lookup(record, ("decisions", "decision"), "an episode record's decisions"))


def decision_readout(decision):
    return _lookup(decision, ("readout", "facts"), "a decision record's readout")


def decision_legal(decision):
    return _lookup(decision, ("legal", "actions"), "a decision record's legal actions")


def decision_action(decision):
    return _lookup(decision, ("action", "choice", "descriptor"),
                   "a decision record's chosen action")


def decision_reward(decision):
    return _lookup(decision, ("reward", "payoff", "return"),
                   "a decision record's reward")


def decision_seat(decision):
    """The acting seat out of a decision record, tolerant of the seat's spelling."""
    value = _lookup(decision, ("seat", "player"), "a decision record's seat")
    if isinstance(value, Mapping):
        value = _lookup(value, ("index", "seat", "number", "id"), "a seat record")
    if isinstance(value, (tuple, list)):
        for item in value:
            if isinstance(item, int) and not isinstance(item, bool):
                return int(item)
        raise AssertionError("cannot read a seat index out of %r" % (decision,))
    if isinstance(value, int) and not isinstance(value, bool):
        return int(value)
    raise AssertionError("cannot read a seat index out of %r" % (decision,))


def episode_payoffs(record):
    """The episode record's per-seat payoffs, keyed by integer seat."""
    declared = _lookup(record, ("payoffs", "payoff", "returns"),
                       "an episode record's payoffs")
    if not isinstance(declared, Mapping):
        raise AssertionError("the episode's payoffs are not a mapping: %r" % (declared,))
    out = {}
    for key, value in declared.items():
        try:
            seat = int(key)
        except (TypeError, ValueError):
            raise AssertionError(
                "an episode payoff is keyed by a seat, and %r is not one" % (key,)
            )
        out[seat] = float(value)
    return out


def payoff_sum(record):
    return sum(episode_payoffs(record).values())


def td_error(statistics):
    """The finite learning signal out of `agents.learn`'s return (`surface.md` §7)."""
    value = _lookup(statistics, ("td_error", "td-error", "td", "error", "loss"),
                    "learn's td_error statistic")
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise AssertionError(
            "learn's td_error must be one number, got %r" % (value,)
        )
    number = float(value)
    if not math.isfinite(number):
        raise AssertionError("learn's td_error must be finite, got %r" % (number,))
    return number


def transitions_consumed(statistics):
    """The transition count out of `agents.learn`'s return (`surface.md` §7)."""
    value = _lookup(statistics, ("transitions", "transition", "consumed", "count"),
                    "learn's transitions statistic")
    if isinstance(value, bool) or not isinstance(value, int):
        raise AssertionError(
            "learn's transitions must be one integer, got %r" % (value,)
        )
    return int(value)


def finite(value):
    return (
        isinstance(value, numbers.Real)
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


# --------------------------------------------------------------------------
# Caller-side policies and the recording policy (`e2e-surface.md` §2).
# --------------------------------------------------------------------------
def caller(readout_facts, legal):
    """Check/call when legal, else the smallest legal index; no randomness."""
    indices = list(legal_indices(legal))
    index = 1 if 1 in indices else indices[0]
    return decode_action(index)


def raiser(readout_facts, legal):
    """Raise when legal, else check/call: the oracle case's aggressive opponent."""
    indices = list(legal_indices(legal))
    index = 2 if 2 in indices else (1 if 1 in indices else indices[0])
    return decode_action(index)


def recording(policy):
    """A policy of the protocol that records every call it is handed.

    A wrapper is a policy in the sense of `e2e-surface.md` §2: it takes the readout
    and the legal descriptors, delegates to the policy under judgement, and returns
    that policy's answer unchanged.
    """
    calls = []

    def wrapped(readout_facts, legal):
        chosen = policy(readout_facts, legal)
        calls.append((readout_facts, legal, chosen))
        return chosen

    wrapped.calls = calls
    return wrapped


# --------------------------------------------------------------------------
# Decisions and transitions over real hands.
# --------------------------------------------------------------------------
def decision(seed):
    """One real decision: ``(hand, readout, legal, observation, mask)`` at a deal."""
    hand = new_hand(seed)
    facts = readout(hand)
    legal = legal_actions(hand)
    return hand, facts, legal, encode(build_encoder(encoding_for("naive-stack")), facts), \
        legal_indices(legal)


def walk(seed, policy, limit=200):
    """Drive one hand to its end through the declared engine entry points.

    Returns ``[(hand, readout, legal, descriptor, index)]`` for every decision, the
    policy being one of `e2e-surface.md` §2's.
    """
    hand = new_hand(seed)
    steps = 0
    out = []
    while not is_terminal(hand) and steps < limit:
        facts = readout(hand)
        legal = legal_actions(hand)
        chosen = policy(facts, legal)
        out.append((hand, facts, legal, chosen, descriptor_index(legal, chosen)))
        hand = apply_action(hand, chosen)
        steps += 1
    return out


def observations(seed, policy, encoder, limit=200):
    """The observations and masks of one driven hand, for a decision comparison."""
    encoder = encoder or build_encoder(encoding_for("naive-stack"))
    return [
        (encode(encoder, facts), legal_indices(legal))
        for _hand, facts, legal, _chosen, _index in walk(seed, policy, limit)
    ]


def seat_transitions(record, seat, encoder):
    """Transition records for one seat of a played episode (`records.md` §4).

    The record carries the two encoded observations, the chosen index, the reward of
    ASM-12 at that seat's terminal decision and zero elsewhere, the terminal flag
    and the two legal index sequences (`records.md` §4, `surface.md` §7).
    """
    decisions = [d for d in episode_decisions(record) if decision_seat(d) == seat]
    if not decisions:
        raise AssertionError(
            "the episode records no decision for seat %r, so no transition batch can "
            "be built for it: %r" % (seat, record)
        )
    rewards = episode_payoffs(record)
    out = []
    for position, held in enumerate(decisions):
        last = position == len(decisions) - 1
        successor = held if last else decisions[position + 1]
        out.append(
            {
                "observation": encode(encoder, decision_readout(held)),
                "next_observation": encode(encoder, decision_readout(successor)),
                "action": descriptor_index(decision_legal(held), decision_action(held)),
                "reward": rewards[seat] if last else 0.0,
                "terminal": last,
                "legal": list(legal_indices(decision_legal(held))),
                "next_legal": list(legal_indices(decision_legal(successor))),
            }
        )
    return out


def tiled(records, length):
    """A batch of `length` transitions drawn from real records in order.

    `learn` consumes the caller's batch in the caller's order and neither samples nor
    dedups it (`surface.md` §7, `ladder.md` §5), so a longer batch built from real
    records is a legal batch and is how a case anneals the schedule without playing
    hundreds of hands.
    """
    if not records:
        raise AssertionError("cannot tile an empty transition sequence")
    return [dict(records[position % len(records)]) for position in range(length)]


# --------------------------------------------------------------------------
# The base case: a scratch directory and the refusal reader.
# --------------------------------------------------------------------------
class JoinCase(unittest.TestCase):
    """The base every case extends: a scratch root and two contract readers."""

    def setUp(self):
        self._scratch = None

    def scratch(self):
        if self._scratch is None:
            self._scratch = tempfile.mkdtemp(prefix="agents-join-")
            self.addCleanup(shutil.rmtree, self._scratch, True)
        return self._scratch

    def checkpoint_path(self, name=CHECKPOINT_ALPHA):
        return os.path.join(self.scratch(), name)

    def assert_refusal(self, entry, groups, call, note=""):
        """Require `call` to be refused, naming the entry point and every group.

        The exception class is tolerated: `docs/L3/agents/errors.md` §2 leaves it to
        L3, while §3 fixes the message grammar.  Each group is one spelling or a
        tuple of alternative spellings, one of which must appear in the message.
        """
        try:
            result = call()
        except SurfaceAbsent:
            raise
        except Exception as exc:  # noqa: BLE001 - the class is L3's freedom
            message = str(exc)
        else:
            self.fail(
                "%s: %s must refuse this call, but it returned %r"
                % (note or entry, entry, result)
            )
        lowered = message.lower()
        self.assertIn(
            entry.lower(),
            lowered,
            "%s: the refusal must name the entry point %r; the message was %r"
            % (note or entry, entry, message),
        )
        for group in groups:
            alternatives = (group,) if isinstance(group, str) else tuple(group)
            if not any(str(alternative).lower() in lowered for alternative in alternatives):
                self.fail(
                    "%s: the refusal must name one of %r; the message was %r"
                    % (note or entry, alternatives, message)
                )
        return message

    def assert_index_in(self, index, mask, note=""):
        self.assertIn(
            index,
            set(mask),
            "%s: the chosen index %r must be a member of the decision's mask %r"
            % (note, index, mask),
        )

    def assert_descriptor_in(self, legal, descriptor, note=""):
        self.assertTrue(
            any(same_descriptor(descriptor, candidate) for candidate in legal),
            "%s: the chosen descriptor %r must be one of legal_actions %r"
            % (note, descriptor, list(legal)),
        )
