"""Join plumbing and invented instances for the `agents` integration battery.

This module is test support, not a subsystem (brief §5, `module-map.md` §5).  It
does four things and nothing else:

* it puts ``<repo>/src`` on ``sys.path`` and imports ``engine``, ``features`` and
  ``agents`` lazily, so a missing surface is one ``SurfaceAbsent`` failure in the
  case that needed it and never a collection error (`battery.md` §2);
* it holds the battery's *invented instances* — deal seeds, learner seeds, widths,
  depths, a sparsity, hand counts, masks, checkpoint file names, and the shape
  battery's own deals, seeds, widths, depths and container names — none of which
  appears in a design document (`docs/L1/battery.md` §4, D-15).  An observation is
  never fabricated: every one is ``features.encode`` of a readout dealt by
  ``engine.new_hand``, because the consumed edge has one declared producer of an
  observation (`docs/L2/features/surface.md` §6) and an invented observation would
  judge nothing.  The one exception is named at `flat_observation` and is used by
  the `tie` case alone, whose subject is the one input on which the flag is
  decidable (`docs/L2/agents/shapes.md` §3, `records.md` §6, §15);
* it holds *tolerant readers* for the shapes the design leaves free: the index out
  of ``agents.act``'s return (`docs/L1/records.md` §6) with the ``tie`` flag beside
  it (`records.md` §15), a policy's descriptor compared by value, a decision
  record's fields, a reward and a seat out of an episode record (`records.md` §5),
  the two statistics of ``agents.learn`` (`docs/L2/agents/surface.md` §7), the
  shape name and head width a learner carries (`docs/L2/agents/shapes.md` §2), a
  container's ``metadata.json`` (`docs/L3/agents/checkpoint.md` §2.1) and a
  finite-number check.  A case asserts the contract through these readers instead
  of inventing a spelling of its own;
* it holds the small call vocabulary the cases are written in — one wrapper per
  entry point the three modules publish, the three calls that take a declared shape
  as a keyword (`docs/L2/features/shapes.md` §1), a decision walk and a shaped one,
  transition records over a played episode, a recording policy, the caller-side
  policies the baselines and shape cases need, a container's metadata read and
  written, and the one internal the `off` mode stands aside.

Nothing here reaches past an entry point of `e2e-surface.md` §3.3 or of the two
consumed surfaces (`docs/L2/engine/surface.md`, `docs/L2/features/surface.md`).  The
one internal stood aside is ``agents.rule._draws``, which is the observable the `off`
mode's "no draw is taken" is stated against (`docs/L2/agents/shapes.md` §4), and it is
replaced for one block and restored before the block leaves.
Each case module loads this file under the private name ``agents_join_support``: the
repository's integration batteries share the file name ``_join_support.py``, and a
plain import would let one battery's helpers stand in for another's when two test
directories are collected in one process.
"""

from __future__ import annotations

import importlib
import json
import math
import numbers
import os
import shutil
import sys
import tempfile
import unittest
import zipfile
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
# The game-shape battery's own instances (`docs/L2/agents/shapes.md` §1-§5).
#
# The two shapes themselves are **not** invented: `docs/L1/battery.md` §4 exempts
# D-2's and D-29's declared games, so the names below are the catalogue's own and
# every case asserts that against `engine.game_shapes()` instead of trusting them.
# The deals, the learner seeds, the policy seeds, the width, the depth and the
# container names are the test writer's own (`docs/L1/battery.md` §4, D-15).
# --------------------------------------------------------------------------
SHAPE_DEFAULT = "fixed-limit-20"    # the catalogue's first row, read back below
SHAPE_SECOND = "no-limit-100"       # the second declared row (D-29)

#: A shape name no catalogue carries: this battery's own spelling, invented from the
#: catalogue's two (`docs/L1/battery.md` §4, D-15, `shapes.md` §1).
SHAPE_UNDECLARED = "join-invented-shape"

#: `as_policy`'s two declared exploration modes, and one value outside them
#: (`docs/L2/agents/shapes.md` §4).
EXPLORATION_MODES = ("schedule", "off")
EXPLORATION_UNDECLARED = "greedy"

DEAL_SHAPE_A = 63421                # deals the shape cases play, invented
DEAL_SHAPE_B = 71993
DEAL_SHAPE_C = 85703
LEARNER_SEED_SHAPE = 52919          # learner seeds and policy seeds, invented
LEARNER_SEED_SHAPE_OTHER = 68437
POLICY_SEED_SHAPE = 37139
POLICY_SEED_SHAPE_OTHER = 90571

WIDTH_SHAPE = 11                    # a width and a depth, invented (small: 8-24, 1-3)
DEPTH_SHAPE = 2

CHECKPOINT_SHAPE_ALPHA = "join-invented-shape-alpha.ckpt"   # container names, invented
CHECKPOINT_SHAPE_BETA = "join-invented-shape-beta.ckpt"
CHECKPOINT_SHAPE_GAMMA = "join-invented-shape-gamma.ckpt"

#: The tree's shipped containers, which a case reads and never writes
#: (`docs/L2/agents/shapes.md` §5, ASM-5, ASM-40).
SHIPPED_ROOT = os.path.join(ROOT, "checkpoints")

#: The container's members and the version its default-shape writer writes
#: (`docs/L3/agents/checkpoint.md` §2-§3).
METADATA_MEMBER = "metadata.json"
DEFAULT_FORMAT_VERSION = 3
GAME_FORMAT_VERSION = 4


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


def build_baseline(name, seed, shape=None):
    """One baseline as a policy, on one declared shape or on the default by absence.

    The third argument is D-33's optional shape (`docs/L2/agents/baselines.md` §2,
    `e2e-surface.md` §3.3, `docs/L1/seats.md` §6): absent, it is the default shape and the
    two-argument call this battery has always made, so no case below that passes two
    arguments moves (`shapes.md` §2, D-33).
    """
    return mod("agents").build_baseline(name, seed, shape=shape)


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
# The same vocabulary, over the declared shapes: the three `features` calls that
# take a shape as a **keyword-only** optional and the three `engine` calls that
# take one (`docs/L2/features/shapes.md` §1, `docs/L2/engine/surface.md` §3-§4, §10).
# --------------------------------------------------------------------------
def game_shapes():
    """`engine.game_shapes()`, the declared catalogue, default first (§12)."""
    return mod("engine").game_shapes()


def shape_names():
    """Every declared shape name, in the catalogue's own order, the default first."""
    return tuple(game_shapes())


def shape_row(shape=None):
    """One row of `engine.game_shapes()`, the default row when no name is given."""
    catalogue = game_shapes()
    name = shape_names()[0] if shape is None else shape
    if name not in catalogue:
        raise AssertionError(
            "engine.game_shapes() carries no row for %r; it declares %r"
            % (name, tuple(catalogue))
        )
    return catalogue[name]


def shaped_hand(seed, shape=None):
    """One real hand of one declared shape, through the engine's seeding point (§4)."""
    return mod("engine").new_hand(seed, shape=shape)


def shaped_play_hand(seed, seat0_policy, seat1_policy, shape=None):
    """One whole hand of one declared shape driven by two policies (§10)."""
    return mod("engine").play_hand(seed, seat0_policy, seat1_policy, shape=shape)


def shaped_encoder(name, shape=None):
    """One encoder, by encoding name, on one declared shape (features surface §4)."""
    return mod("features").build_encoder(name, shape=shape)


def shaped_action_space(shape=None):
    """One shape's vocabulary, in that shape's declared index order (§7)."""
    return mod("features").action_space(shape=shape)


def shaped_decode_action(index, shape=None):
    """One index decoded in one declared shape's vocabulary (§9)."""
    return mod("features").decode_action(index, shape=shape)


def as_policy_mode(learner, encoder, seed, exploration="schedule"):
    """One learner as a policy under one exploration mode (`docs/L2/agents/shapes.md` §4).

    The fourth argument is the mode the policy is built with: `schedule` is the keyed
    draw of `rule.md` §4 and `off` the masked maximum and the tie-break alone, where no
    generator is drawn from at all (`sizing.md` §4).
    """
    return mod("agents").as_policy(learner, encoder, seed, exploration=exploration)


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


def shaped_learner_spec(kind, width, depth, seed, game, backend="numpy",
                        encoding=None, **settings):
    """One learner spec naming the declared shape it decides in (`shapes.md` §1, §4).

    `game` is the spec's optional key (`docs/L2/agents/surface.md` §4): the shape whose
    head the learner is built on, and whose own encoder is supplied here so the
    representation's provenance is the shape the learner decides in (`sizing.md` §6).
    """
    architecture = {"kind": kind, "width": width, "depth": depth}
    architecture.update(settings)
    return {
        "backend": backend,
        "architecture": architecture,
        "seed": seed,
        "encoder": shaped_encoder(encoding or encoding_for(kind), game),
        "game": game,
    }


def shaped_learner(kind="naive-stack", width=WIDTH_SHAPE, depth=DEPTH_SHAPE,
                   seed=LEARNER_SEED_SHAPE, game=SHAPE_SECOND, backend="numpy",
                   encoding=None, **settings):
    """A built learner on one declared shape, through `agents.build_learner`."""
    return build_learner(
        shaped_learner_spec(kind, width, depth, seed, game, backend, encoding,
                            **settings)
    )


def declared_param_count(kind, width, depth, sparsity, actions, size=None):
    """`architecture.md` §5's sum arithmetic, from the kind's row, a shape's `A` and its `I`.

    The input block first (`I·W + W` for the dense family, `V·W` for a token one), then
    `D·(W² + W)` — `D·(k + W)` for `sparse`, `k = round((1 − s)·W²)` — then the head's
    `A·W + A` (`docs/L2/agents/shapes.md` §2, `docs/L3/agents/shapes.md` §2, `sizing.md`
    §6, ASM-40).  Nothing here is a copied count: the caller states the width, the depth,
    the sparsity and the shape's `A`, so the head's width is a parameter and never a
    literal of this battery's.

    `size` is `I` — or `V`, the token vocabulary — and `None` means the kind's declared
    `observation_size`, which is the **default** shape's and the only size an encoder-less
    build is ever given (`docs/L1/shapes.md` §8, ASM-44).  A caller on any other shape
    passes that shape's encoder's width or vocabulary out of
    `features.observation_spec`, because the input term is the shape's too: 329 dense over
    66 history slots on `no-limit-100` against the default's 203 over 24
    (`docs/L2/features/capacity.md` §2, ASM-44).
    """
    row = learners()["architectures"][kind]
    if size is None:
        size = int(row["observation_size"])
    dense = row["observation"] == "dense-numeric"
    layer_width = int(width)
    input_term = int(size) * layer_width + (layer_width if dense else 0)
    if kind == "sparse":
        kept = round((1.0 - float(sparsity)) * layer_width * layer_width)
        trunk_term = int(depth) * (kept + layer_width)
    else:
        trunk_term = int(depth) * (layer_width * layer_width + layer_width)
    return input_term + trunk_term + int(actions) * layer_width + int(actions)


def head_width(shape=None):
    """`A`, one shape's descriptor count, **read** off `features.action_space` (§1).

    This is the granted call the module's own `actions_for` makes and the only statement
    of the head's width: three on the default shape and six on the other, never a
    literal of a table's, a backend's or this battery's (`docs/L3/agents/shapes.md` §1,
    `sizing.md` §6, ASM-40).
    """
    return len(shaped_action_space(shape))


def shaped_input_size(kind, shape=None):
    """`I` — or `V` — the input width a learner of `kind` on `shape` is built at.

    Read off **that shape's** encoder, which is the one statement of it: a dense
    encoding's width is `observation_spec(...)["shape"][0]` and a token encoding's size
    is its `["vocabulary"]`, never its sequence length — 329 dense and a vocabulary of
    96 over an 82-long sequence on `no-limit-100`, against the default shape's 203 and 40
    (`docs/L1/shapes.md` §8, ASM-44, `docs/L2/agents/shapes.md` §2, `docs/L2/features/
    capacity.md` §2).  `shape=None` is the default shape's, which is the size the kind's
    declared `observation_size` names and the only one an encoder-less build is given.
    """
    spec = observation_spec(shaped_encoder(encoding_for(kind), shape))
    if spec["kind"] == "dense-numeric":
        return int(tuple(spec["shape"])[0])
    return int(spec["vocabulary"])


def exploration_samples():
    """The sample count the exploration schedule anneals over (`surface.md` §3)."""
    schedule = _lookup(learners()["hyper"], ("exploration", "schedule", "epsilon"),
                       "learners()['hyper']'s exploration schedule")
    return int(_lookup(schedule, ("samples", "anneal", "decisions"),
                       "the exploration schedule's sample count"))


def exploration_start():
    """The rate the exploration schedule starts at, which a fresh learner is at (`§3`)."""
    schedule = _lookup(learners()["hyper"], ("exploration", "schedule", "epsilon"),
                       "learners()['hyper']'s exploration schedule")
    return float(_lookup(schedule, ("start", "begin", "initial"),
                         "the exploration schedule's starting rate"))


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


def decision_record(result):
    """`agents.act`'s record as a mapping, refusing a bare index (`shapes.md` §3).

    `act` returns the decision record — the chosen index under `action` and the `tie`
    flag beside it — and not a bare index (`docs/L2/agents/surface.md` §6, `records.md`
    §6, §15), so a case that reads the flag requires the mapping.
    """
    if not isinstance(result, Mapping):
        raise AssertionError(
            "agents.act must return the decision record carrying `action` and `tie`, "
            "got %r" % (result,)
        )
    return result


def decision_tie(record):
    """The `tie` flag out of `agents.act`'s record, required to be a plain `bool` (§15).

    True exactly when the **greedy arm** decided the index and at least two masked
    values sat within the tolerance of the masked maximum — so the tie-break and not a
    strict maximum chose it — false on a one-element mask and false wherever the
    exploring arm drew the index (`docs/L2/agents/shapes.md` §3, `records.md` §6, §15,
    `docs/L3/agents/shapes.md` §3).
    """
    for key, value in decision_record(record).items():
        if "tie" in str(key).lower():
            if not isinstance(value, bool):
                raise AssertionError(
                    "act's `tie` must be a plain bool, got %r" % (value,)
                )
            return value
    raise AssertionError(
        "act's record carries no `tie` flag, so the tie-break is not observable "
        "(records.md §6, §15): %r" % (record,)
    )


def plain_action(record):
    """The `action` out of `agents.act`'s record, required to be a plain `int` (§6)."""
    for key, value in decision_record(record).items():
        if any(part in str(key).lower() for part in ("action", "index", "choice")):
            if isinstance(value, bool) or not isinstance(value, int):
                raise AssertionError(
                    "act's `action` must be a plain int, got %r" % (value,)
                )
            return int(value)
    raise AssertionError("act's record carries no `action`: %r" % (record,))


def learner_game(learner):
    """The declared shape a learner decides in (`docs/L2/agents/shapes.md` §2).

    "The learner carries the resolved `A` and its shape's name"; `act`, `learn`,
    `as_policy` and `save` read it and no arithmetic branches on it (`shapes.md` §2,
    `docs/L3/agents/shapes.md` §2, ASM-40).
    """
    game = getattr(learner, "game", None)
    if not isinstance(game, str):
        raise AssertionError(
            "a learner carries the declared shape it decides in, under `game` "
            "(shapes.md §2); got %r" % (game,)
        )
    return game


def learner_actions(learner):
    """`A`, the head width a learner was built with (`docs/L2/agents/shapes.md` §2)."""
    value = getattr(learner, "actions", None)
    if isinstance(value, bool) or not isinstance(value, int):
        raise AssertionError(
            "a learner carries the resolved `A` under `actions` (shapes.md §2); got %r"
            % (value,)
        )
    return int(value)


def flat_observation(encoder):
    """A zero observation of the encoder's declared shape and dtype (`architecture.md` §6).

    **This is the one observation in this battery that is not `features.encode` of a
    readout `engine` dealt**, and it is named here rather than hidden.  `act`'s masked
    values are not observable through any entry point (`docs/L2/agents/surface.md` §6,
    `docs/L3/agents/rule.md` §8), so the one input on which the `tie` flag is decidable
    from the record alone — a **flat** value vector, where the tie-break and not a
    strict maximum must have chosen and a one-element mask must report false — is
    reached by an observation whose every slot is zero, which no readout of either
    declared shape encodes to (`docs/L2/agents/shapes.md` §3, `records.md` §6, §15).
    The join's real hands are driven through `shaped_walk`, never through this.
    """
    import numpy

    spec = observation_spec(encoder)
    shape = tuple(spec["shape"])
    return numpy.zeros(shape, dtype=spec["dtype"])


def still_batch(observation, mask, length):
    """`length` transitions that leave every parameter as it was and advance the position.

    Over a zero observation at an unlearned head every value and every target is `0.0`,
    so the TD error is `0.0` and `rule.md` §3's step adds nothing while §4's position
    still advances by the batch's length.  That is the only way to hold a learner at the
    annealed rate without moving the values the tie-break reads, which is what the `tie`
    case needs (`docs/L2/agents/shapes.md` §3-§4, `docs/L2/agents/surface.md` §7).
    """
    members = [int(index) for index in mask]
    return [
        {
            "observation": observation,
            "next_observation": observation,
            "action": members[0],
            "reward": 0.0,
            "terminal": False,
            "legal": list(members),
            "next_legal": list(members),
        }
        for _ in range(int(length))
    ]


# --------------------------------------------------------------------------
# The container, read and rewritten at the join (`docs/L3/agents/checkpoint.md` §2-§3).
# --------------------------------------------------------------------------
def container_metadata(path):
    """The `metadata.json` object of the container at `path`, read and never written.

    A checkpoint is a zip of exactly two members, the metadata object and the parameter
    array (`docs/L3/agents/checkpoint.md` §2), so a case reads the first of them to
    check the version and the `game` a writer wrote — which no entry point reports
    (`docs/L2/agents/shapes.md` §5, §6).
    """
    try:
        with zipfile.ZipFile(path) as container:
            if METADATA_MEMBER not in container.namelist():
                raise AssertionError(
                    "the container at %r carries no %r member: %r"
                    % (path, METADATA_MEMBER, container.namelist())
                )
            data = container.read(METADATA_MEMBER)
    except zipfile.BadZipFile as error:
        raise AssertionError(
            "the container at %r is not a zip: %s" % (path, error)
        ) from None
    try:
        record = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        raise AssertionError(
            "the container at %r carries a %r that is not one JSON object: %s"
            % (path, METADATA_MEMBER, error)
        ) from None
    if not isinstance(record, Mapping):
        raise AssertionError(
            "the container at %r carries a %r that is not one object: %r"
            % (path, METADATA_MEMBER, record)
        )
    return record


def rewrite_container(source, destination, **changes):
    """Copy the container at `source` to `destination`, editing its metadata object.

    The refusals of `docs/L3/agents/checkpoint.md` §3 are stated over containers no
    writer of this module writes — a version-4 one naming the default shape among them —
    so the surgery is done on a copy in the case's scratch root and never on a path
    `save` wrote or on a shipped file (`docs/L2/agents/shapes.md` §5, `battery.md` §5).
    """
    with zipfile.ZipFile(source) as container:
        members = [(name, container.read(name)) for name in container.namelist()]
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_STORED) as written:
        for name, data in members:
            if name == METADATA_MEMBER:
                record = dict(container_metadata(source))
                record.update(changes)
                data = json.dumps(record).encode("utf-8")
            written.writestr(name, data)
    return destination


def shipped_containers(version=None):
    """Every container the tree ships under `<repo>/checkpoints`, in path order.

    Read-only: a case that loads one leaves it as it found it (`docs/L2/agents/shapes.md`
    §5, ASM-5, ASM-40).  `version` keeps only the containers whose own
    `format_version` is that one, so a case names the shipped version-1 set without
    spelling a path (`docs/L3/agents/checkpoint.md` §3).
    """
    found = []
    if not os.path.isdir(SHIPPED_ROOT):
        return found
    for base, _directories, files in os.walk(SHIPPED_ROOT):
        for name in files:
            if not name.endswith(".ckpt"):
                continue
            path = os.path.join(base, name)
            try:
                record = container_metadata(path)
            except AssertionError:
                continue
            if version is None or record.get("format_version") == version:
                found.append(path)
    return sorted(found)


def container_stamp(path):
    """A container's `(size, mtime_ns)`, so a case can show it was not rewritten."""
    status = os.stat(path)
    return (int(status.st_size), int(status.st_mtime_ns))


def rule_module():
    """`agents.rule`, the module `rule.md` §4-§5 puts the keyed draw in (`shapes.md` §4)."""
    return mod("agents.rule")


class draws_stood_aside:
    """`agents.rule._draws` replaced for one block and restored before the block leaves.

    The `off` mode's claim is that the draw is **not constructed at all**
    (`docs/L3/agents/shapes.md` §4, `sizing.md` §4), and the observable is the one
    internal `rule.md` §8 declares: under a stub that raises, a `schedule` policy
    refuses to decide and an `off` policy decides.  `__exit__` restores what was held,
    so a failing case leaves the module as it found it (`battery.md` §5).
    """

    def __init__(self):
        self._module = None
        self._held = None

    def __enter__(self):
        self._module = rule_module()
        self._held = self._module._draws

        def refuse(*arguments, **keywords):
            raise AssertionError(
                "rule._draws was called: an `off` policy constructs no generator and "
                "takes no draw (docs/L3/agents/shapes.md §4, sizing.md §4)"
            )

        self._module._draws = refuse
        return self

    def __exit__(self, kind, value, traceback):
        self._module._draws = self._held
        self._module = None
        self._held = None
        return False


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


def caller_in(shape):
    """Check/call when legal, else the smallest legal index, decoded in `shape`.

    The whole of a caller-side policy on a declared shape: it picks an index the mask
    holds and decodes it in **that shape's** vocabulary, which is what
    `features.decode_action(index, shape=...)` is for (`docs/L2/features/shapes.md`
    §3-§4, §9).  Its indices are the mask's own, never a descriptor of this battery's.
    """
    def policy(readout_facts, legal):
        indices = list(legal_indices(legal))
        index = 1 if 1 in indices else indices[0]
        return shaped_decode_action(index, shape)

    return policy


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


def shaped_walk(seed, shape, policy, limit=200):
    """Drive one real hand of one declared shape to its end, decision by decision.

    The shaped twin of `walk`: the hand is dealt through `engine.new_hand(seed,
    shape=...)` — the project's single seeding point on either shape
    (`docs/L2/engine/surface.md` §4) — and the decisions come back as
    ``[(hand, readout, legal, descriptor, index)]``, the descriptor being the engine's
    own and the index its position in that shape's vocabulary (`sizing.md` §3).
    """
    hand = shaped_hand(seed, shape)
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
