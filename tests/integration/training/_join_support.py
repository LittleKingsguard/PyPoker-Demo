"""Join plumbing and invented instances for the `training` integration battery.

This module is test support, not a subsystem (brief §5, `module-map.md` §5).  It
does four things and nothing else:

* it puts ``<repo>/src`` on ``sys.path`` and imports ``training`` and the four
  modules it consumes -- ``evaluation``, ``agents``, ``features`` and ``engine`` --
  lazily, so a missing surface is one ``SurfaceAbsent`` failure in the case that
  needed it and never a collection error (`battery.md` §2);
* it holds the battery's *invented instances* -- two run seeds, a budget, a
  second budget, two learner seeds, an episode seed with its two baseline seeds, a
  replay seed and a hand index, a cell size, a cell seed, a table seed and a
  variant label of the writer's own -- none of which appears in a design document
  or in `tests/e2e/` (`docs/L1/battery.md` §4, D-15).  No learner, encoder, pool,
  checkpoint, cell, matrix or rating is fabricated: every one is produced by the
  module that owns it -- `agents.build_learner`, `features.build_encoder`,
  `training.run`, `evaluation.build_pool`, `evaluation.match`, `evaluation.rating`
  -- because a join judged through a hand-written record would judge nothing
  (`docs/L1/protocol.md` §5, D-16).  The single exception is the matrix and the
  rating of join 7, whose provenance `evaluation.rating` explicitly does not
  check (`docs/L2/evaluation/surface.md` §11, `records.md` §10), and which exist
  so that one case can hand `evaluation.report` a run record without playing a
  120-hand cell (`docs/L2/evaluation/league.md` §5, ASM-15);
* it holds the *eight joins* `docs/L1/battery.md` §5 calls the invariants a
  single module cannot check about itself, as they bear on this module's edge:

      TRNJ-1  training x engine      a run's hands are the engine's hands
      TRNJ-2  training x features    the encoder a variant names is the one it used
      TRNJ-3  training x agents      the learning signal is `agents.learn`'s
      TRNJ-4  training x evaluation  the pool the loop trains against is the pool
                                     `build_pool`/`pool_members` measure and
                                     `opponent` draws from
      TRNJ-5  the lineage join       R2's declared window is R1's retained window
      TRNJ-6  the checkpoint join    a run's final model loads as a league member
      TRNJ-7  the report join        a run's record is the record `report` wants
      TRNJ-8  determinism, ASM-2     one tuple gives one record; only dealing
                                     moves the global `random` stream

* it holds tolerant readers for the shapes a record leaves free -- the seed key
  of a per-seed sub-record, a pool member's pinned flag, a baseline's declared row,
  a header item's spelling -- plus the module-level fixtures the battery shares:
  one small R1 run, one R2 run whose pool carries a version window, one R4 run
  with a variant pair, a repeat of the R1 tuple and one run at another seed, one
  run of the catalogue's third shape whose pool holds five members, one
  real episode with its transitions, the two backends' learners, and the hand-built
  matrix with its fitted rating.  A run is this battery's expensive observable, so
  each is built once per process and shared (`docs/L2/training/loop.md` §3,
  `docs/L1/battery.md` §2); every run stays at ten to twelve hands per variant per
  seed.

Three more of `training`'s declared names are read as contract beside
``seeds._deal_seed`` and ``episode._transitions`` below: ``declarations.SHAPE_HISTORY``
and ``declarations.greedy_decisions(shape)`` -- the restated per-shape history capacity
and the pass bound that is 1,000 x it, which `module-map.md` §2 leaves the module to
restate because it is granted no `engine.game_shapes` (`shapes.md` §8, ASM-42) -- and
``episode._seat``, the `index mod seats` rotation `docs/L3/training/episode.md` §1 and
`seats.md` §4 fix and `docs/L3/training/README.md` §4 makes contract
(`docs/L1/battery.md` §5, ASM-43, D-13, D-33).

The first two private `training` names are re-imported here and used as contract, exactly
as `docs/L3/training/seeds.md` §2 and `docs/L3/training/episode.md` §3 mark them
("contract for `tests/training/`"): ``seeds._deal_seed``/``_opponent_seed``, the
derivation that makes hand *i* of a run a function of its seed and its index, and
``episode._transitions``, the one place an episode becomes a batch.  A join that
needs to ask "is the seed the run dealt at the seed the derivation names?" or
"does the batch a hand produces carry the engine's terminal chip delta?" cannot
ask it through a single entry point, and inventing a second derivation here would
assert this module's arithmetic instead of the record's (`docs/L1/battery.md` §5).

Nothing here reaches past an entry point of `e2e-surface.md` §3.5 or of the four
consumed surfaces (`docs/L2/evaluation/surface.md`, `docs/L2/agents/surface.md`,
`docs/L2/features/surface.md`, `docs/L2/engine/surface.md`).  Each case module
loads this file under the private name ``training_join_support``: the
repository's integration batteries share the file name ``_join_support.py``, and a
plain import would let one battery's helpers stand in for another's when two test
directories are collected in one process.
"""

from __future__ import annotations

import copy
import importlib
import itertools
import json
import math
import numbers
import os
import random
import shutil
import sys
import tempfile
import unittest
from collections.abc import Mapping

# --------------------------------------------------------------------------
# The five packages, imported lazily.
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
# docs/ carries them and `tests/e2e/` uses none of them (`docs/L1/battery.md` §4,
# D-15).  The one budget a document does carry -- the run's hands per variant per
# seed -- appears below only as the two invented budgets the battery runs at, and
# the parameter budget of 10,000 is read back out of a configuration's own
# declaration (`docs/L3/training/registry.md` §4) rather than repeated here.
# --------------------------------------------------------------------------
RUN_SEED = 4103                # the battery's run seeds, invented
RUN_SEED_OTHER = 8807
RUN_BUDGET = 12                # hands per variant per seed, invented (10..40)
PAIR_BUDGET = 10
LEARNER_SEED_OFFSET = 101      # a second learner seed's offset, invented
EPISODE_SEED = 777001          # one real episode's deal seed, invented
EPISODE_BASELINE_A = 5         # that episode's two policies' seeds, invented
EPISODE_BASELINE_B = 7
REPLAY_SEED = 90211            # a readout a policy answers, invented
REPLAY_INDEX = 3               # a hand index whose deal is replayed, invented
DRAW_STEP = 7                  # walks a pool's membership by DRAW_STEP * n + k
CELL_HANDS = 6                 # the hand-built table's cell size, invented
CELL_SEED = 55103              # its one real cell's seed, invented
TABLE_SEED = 84017             # its table seed, invented
VARIANT_LABEL = "variant-invented-7"   # a member outside the pool, invented
SNAPSHOT_POINTS = 10           # ASM-18's ten snapshot intervals (`curves.md` §2)
UTILITY_SEED = 4409            # D-20's run's two seeds, invented
UTILITY_SEED_OTHER = 4410
UTILITY_BUDGET = 10            # its hands per variant per seed, invented
UTILITY_RUNG = "rung-invented-utility-9"        # its rung label, invented
UTILITY_LEFT = "chips-arm-invented-9"           # its two arms' names, invented
UTILITY_RIGHT = "shortfall-arm-invented-9"
UTILITY_POOL = "pool-invented-utility-9"        # the pool id it declares, invented
COUNTERFACTUAL_RUNG = "rung-invented-counterfactual-11"   # D-43's run's invented labels
COUNTERFACTUAL_VARIANT = "member-arm-invented-11"
COUNTERFACTUAL_POOL = "pool-invented-counterfactual-11"
COUNTERFACTUAL_SEED = 4411                      # its one seed, invented
SHOWDOWN_SEED = 4412                           # D-43's showdown hand's deal seed, invented
SIX_SEAT_RUNG = "rung-invented-shape-12"        # the third shape's invented labels
SIX_SEAT_POOL = "pool-invented-shape-12"


# --------------------------------------------------------------------------
# The small call vocabulary: one wrapper per entry point driven.
# --------------------------------------------------------------------------
def rungs():
    return mod("training").rungs()


def rung(name):
    return mod("training").rung(name)


def run(spec, seeds=None, budget=None, device=None):
    return mod("training").run(spec, seeds=seeds, budget=budget, device=device)


def fairness(left, right):
    return mod("training").fairness(left, right)


def devices():
    return mod("training").devices()


def checkpoints():
    return mod("training").checkpoints()


def deal_seed(seed, index):
    """`seeds._deal_seed` -- the seed `engine.play_hand` is called with (`seeds.md` §2)."""
    return mod("training.seeds")._deal_seed(seed, index)


def opponent_seed(seed, index):
    """`seeds._opponent_seed` -- the seed `evaluation.opponent` is called with."""
    return mod("training.seeds")._opponent_seed(seed, index)


def transitions(episode, seat, encoder):
    """`episode._transitions` -- one episode's batch for one seat (`episode.md` §3)."""
    return list(mod("training.episode")._transitions(episode, seat, encoder))


def transitions_under(episode, seat, encoder, utility):
    """`episode._transitions(..., utility)` -- the same batch on one utility's reward.

    The utility is the catalogue member the variant is trained on, and the transition step
    is the one place it is applied (`episode.md` §3, `reward.md` §1-§3, D-20).  D-43's
    resolution is transformed by the same function, so a case reads both utilities through
    this door and holds the two arithmetics side by side (`counterfactual.md` §4, D-43).
    """
    return list(
        mod("training.episode")._transitions(episode, seat, encoder, utility)
    )


def descriptor_count(shape=None):
    """`A`, one declared shape's descriptor count, read off `features.action_space` (§6).

    The battery may ask the catalogue directly, so the length of that shape's action space is
    the number a resolution must carry -- three on the default shape, six on either uncapped
    one -- and no literal is written down here (`sizing.md` §3, §6, `shapes.md` §2, D-13).
    """
    return len(mod("features").action_space(shape=shape))


def protocol():
    return mod("evaluation").protocol()


def league():
    return mod("evaluation").league()


def build_pool(declaration):
    return mod("evaluation").build_pool(declaration)


def pool_members(pool):
    return mod("evaluation").pool_members(pool)


def offer(pool, version):
    return mod("evaluation").offer(pool, version)


def opponent(pool, seed):
    return mod("evaluation").opponent(pool, seed)


def draw(pool, seed, count):
    """`evaluation.opponent(pool, seed, count)`: `count` distinct members, in draw order.

    Drawn **without replacement** from the frozen pool and reproducible from
    `(seed, membership)`, so a hand's opponents are distinct policies and two calls at one
    seed over one pool agree (`seats.md` §4, `league.md` §2, ASM-43, D-33).
    """
    return tuple(mod("evaluation").opponent(pool, seed, count))


def match(left, right, hands, seed):
    return mod("evaluation").match(left, right, hands, seed)


def rating(matrix_record):
    return mod("evaluation").rating(matrix_record)


def policy_from(path):
    return mod("evaluation").policy_from(path)


def report(rung_name, record, matrix_record, rating_record):
    return mod("evaluation").report(rung_name, record, matrix_record, rating_record)


def baselines():
    return mod("agents").baselines()


def learners():
    return mod("agents").learners()


def build_learner(spec):
    return mod("agents").build_learner(spec)


def param_count(learner):
    return mod("agents").param_count(learner)


def act(learner, observation, legal_mask):
    return mod("agents").act(learner, observation, legal_mask)


def learn(learner, batch):
    return mod("agents").learn(learner, batch)


def load(spec, path):
    return mod("agents").load(spec, path)


def build_baseline(name, seed):
    return mod("agents").build_baseline(name, seed)


def build_encoder(name, shape=None):
    """`features.build_encoder(name, shape=...)`: one shape's encoder (`features/surface.md` §4).

    The shape is an optional keyword-only argument whose absence is the default shape, so a
    caller that names none gets the encoder it always got and a six-seat learner takes its
    input width from the third row's encoder (`shapes.md` §8, ASM-44, D-29, D-33).
    """
    return mod("features").build_encoder(name, shape=shape)


def observation_spec(encoder):
    return mod("features").observation_spec(encoder)


def encode(encoder, readout_record):
    return mod("features").encode(encoder, readout_record)


def legal_indices(legal_actions):
    return tuple(mod("features").legal_indices(list(legal_actions)))


def decode_action(index):
    return mod("features").decode_action(index)


def game_config():
    return mod("engine").game_config()


def game_shapes():
    """The declared shape catalogue, default first (`shapes.md` §2, D-29)."""
    return mod("engine").game_shapes()


def shape_names():
    """The declared shape names, in the catalogue's order -- default first."""
    return tuple(str(name) for name in game_shapes())


def shaped_game_config(shape=None):
    """`engine.game_config(shape)`: one shape's parameters (`engine/surface.md` §3)."""
    return mod("engine").game_config(shape)


def action_space(shape=None):
    """`features.action_space(shape=...)`: one shape's vocabulary (`features/surface.md` §7)."""
    return mod("features").action_space(shape=shape)


def shaped_decode_action(index, shape=None):
    """`features.decode_action(index, shape=...)`: one index in one vocabulary."""
    return mod("features").decode_action(index, shape=shape)


def declared_shapes():
    """`training.declarations`' restated catalogue: `SHAPE_NAMES`, `SHAPE_ACTIONS`.

    Read as contract the way `seeds._deal_seed` is (`_join_support.py`'s module docstring):
    the module restates the two declared shapes' names and descriptor counts because
    `module-map.md` §2 grants it neither `engine.game_shapes` nor `features.action_space`,
    and this join is the one check that the restatement is the catalogue's (`D-13`,
    `shapes.md` §4).
    """
    declarations = importlib.import_module("training.declarations")
    return declarations.SHAPE_NAMES, declarations.SHAPE_ACTIONS


def declared_history():
    """`training.declarations`' restated per-shape history capacities: `SHAPE_HISTORY`.

    The counterpart of :func:`declared_shapes` for the number `shapes.md` §8 derives from
    each shape's own betting: `module-map.md` §2 grants this module no `engine.game_shapes`,
    so each capacity is restated as `SHAPE_ACTIONS` is, and this join is what holds the
    restatement to the catalogue row's own `history` (`shapes.md` §8, ASM-42, D-13, D-33).
    """
    declarations = importlib.import_module("training.declarations")
    return declarations.SHAPE_HISTORY


def declared_greedy_bound(shape=None):
    """`declarations.greedy_decisions(shape)`: one shape's greedy record bound.

    One thousand decision records per slot of the shape's history capacity — 24,000 at the
    default shape, 66,000 and 98,000 on the uncapped ones — so the pass's bound follows the
    run's own shape rather than a constant, and the default shape's 24,000 did not widen
    (`records.md` §15, `shapes.md` §8, ASM-38, ASM-42, D-33).
    """
    declarations = importlib.import_module("training.declarations")
    return int(declarations.greedy_decisions(shape))


def retained():
    """`declarations.RETAINED`: ASM-18's five snapshots one pair retains (`checkpoints.md` §3)."""
    declarations = importlib.import_module("training.declarations")
    return int(declarations.RETAINED)


def third_shape():
    """The catalogue's third declared shape: the six-seat row (`seats.md` §2, D-33)."""
    return shape_names()[2]


def shape_history(name):
    """One shape's published `history` capacity, read off `engine.game_shapes()`.

    The catalogue row carries it and `engine.game_config`'s fifteen keys do not, so this is
    the published value a restatement is held to (`shapes.md` §8, ASM-42, engine/surface.md
    §3).
    """
    return int(game_shapes()[str(name)]["history"])


def folders():
    """The catalogue's **folding** baselines — its `anchor: False` members — in its order.

    The counterpart of :func:`baseline_names` for D-21's folders: a folder is a pool member
    only when a membership declaration names it, so a pool holds the three anchors of D-6
    plus the folders declared and nothing else (`records.md` §8, `fairness.md` §5, ASM-32,
    D-21, D-33).
    """
    declared = baselines()
    return [
        str(name)
        for name, record in declared.items()
        if isinstance(record, dict) and not record.get("anchor")
    ]


def seat_of_hand(index, shape=None):
    """`episode._seat`: the seat the learner plays in hand `index` (`seats.md` §4, ASM-43).

    `_seat` is contract for this module's battery (`docs/L3/training/README.md` §4,
    `docs/L3/training/episode.md` §1) and takes its modulus from
    `engine.game_config(shape)["seats"]`, so the rotation a case reads here is the run's own
    shape's and no literal `2` or `6` is written down as the game's (ASM-44, D-33).
    """
    return int(mod("training.episode")._seat(int(index), shape))


def no_limit_configuration():
    """The registry's R1 entry, declared on the catalogue's second shape.

    A configuration in no design document (`docs/L1/battery.md` §4, D-15): R1's own
    variant entry, unchanged, under a label of this battery's and with `records.md` §2's
    `game` naming the second declared shape — so the run is the same loop on another game
    and the record is the same record on another shape (`shapes.md` §1, §3, D-29).  It
    declares an empty window and the battery's own seed and budget.
    """
    if "no-limit-config" not in _SHARED:
        template = clone(variant_entry(rung("R1"), "naive-numeric"))
        template["samples"] = RUN_BUDGET
        template["seeds"] = [RUN_SEED]
        template["snapshot_every"] = max(1, RUN_BUDGET // 10)
        _SHARED["no-limit-config"] = {
            "name": "rung-invented-shape-11",
            "axis": "the game shape, which is never a rung's axis",
            "carried_from": None,
            "primary": "naive-numeric",
            "game": shape_names()[1],
            "variants": [template],
            "pool": {
                "id": "pool-invented-shape-11",
                "lineage": None,
                "m": 5,
                "frozen": True,
                "members": [],
            },
            "seeds": [RUN_SEED],
            "samples": RUN_BUDGET,
            "device": "cpu",
            "snapshot_every": max(1, RUN_BUDGET // 10),
        }
    return clone(_SHARED["no-limit-config"])


def no_limit_run():
    """One run of that configuration: the second shape, trained end to end."""
    if "no-limit" not in _SHARED:
        _SHARED["no-limit"] = {
            "record": run(no_limit_configuration(), seeds=[RUN_SEED], budget=RUN_BUDGET)
        }
    return _SHARED["no-limit"]["record"]


def six_seat_configuration_with(members):
    """The third shape's invented configuration, its pool declaring `members` folders.

    A configuration in no design document (`docs/L1/battery.md` §4, D-15): R1's own variant
    entry, unchanged, under a label of this battery's and with `records.md` §2's `game`
    naming the catalogue's third shape — so the run is the same loop on a six-seat game and
    the record is the same record (`shapes.md` §1, §3, `seats.md` §2, D-33).  The pool
    declaration names the folders it is handed, so the frozen pool holds D-6's three
    anchors plus them: five members for two folders, which is the least a six-seat hand's
    draw of `seats - 1` opponents can be satisfied from, and four for one, which is a draw
    the membership cannot supply (`records.md` §8, `seats.md` §4, ASM-32, ASM-43, D-21).
    """
    template = clone(variant_entry(rung("R1"), "naive-numeric"))
    template["samples"] = RUN_BUDGET
    template["seeds"] = [RUN_SEED]
    template["snapshot_every"] = max(1, RUN_BUDGET // 10)
    return {
        "name": SIX_SEAT_RUNG,
        "axis": "the game shape, which is never a rung's axis",
        "carried_from": None,
        "primary": "naive-numeric",
        "game": third_shape(),
        "variants": [template],
        "pool": {
            "id": SIX_SEAT_POOL,
            "lineage": None,
            "m": 5,
            "frozen": True,
            "members": [],
            "baselines": [str(name) for name in members],
        },
        "seeds": [RUN_SEED],
        "samples": RUN_BUDGET,
        "device": "cpu",
        "snapshot_every": max(1, RUN_BUDGET // 10),
    }


def six_seat_configuration():
    """The same configuration with two folders declared: a pool of exactly five members."""
    return six_seat_configuration_with(folders()[:2])


def six_seat_run():
    """One run of it, built once per process: the third shape, trained end to end.

    Twelve hands per variant at one invented seed, so the curve closes with ten points at a
    one-hand interval, the record retains ASM-18's five snapshots plus the final model, and
    the pass is the same twelve hands replayed — the run is this battery's expensive
    observable, so it is shared (`curves.md` §2, `checkpoints.md` §3, `sizing.md` §4,
    `docs/L1/battery.md` §2, D-33).
    """
    if "six-seat" not in _SHARED:
        _SHARED["six-seat"] = {
            "record": run(six_seat_configuration(), seeds=[RUN_SEED], budget=RUN_BUDGET)
        }
    return _SHARED["six-seat"]["record"]


def greedy_block(record, variant, seed):
    """One variant × seed's `records.md` §15 block (`greedy.md` §2)."""
    block = record.get("greedy")
    if not isinstance(block, Mapping):
        raise AssertionError("the run record carries no `greedy` block: %r" % (sorted(record),))
    per_variant = block.get(str(variant))
    if not isinstance(per_variant, Mapping):
        raise AssertionError("the pass carries no block for %r: %r" % (variant, sorted(block)))
    seed_block = per_variant.get(seed_key(seed))
    if not isinstance(seed_block, Mapping):
        raise AssertionError(
            "the pass carries no block for %r at seed %r: %r"
            % (variant, seed, sorted(per_variant))
        )
    return seed_block


def decisions_of_block(block):
    """One block's ordered decision records (`records.md` §15)."""
    decisions = block.get("decisions")
    if not isinstance(decisions, (list, tuple)):
        raise AssertionError("a greedy block carries `decisions` as a sequence: %r" % (block,))
    return list(decisions)


def new_hand(seed):
    return mod("engine").new_hand(seed)


def readout(hand):
    return mod("engine").readout(hand)


def legal_actions(hand):
    return mod("engine").legal_actions(hand)


def payoffs(hand):
    return mod("engine").payoffs(hand)


def play_hand(seed, seat0_policy, seat1_policy):
    return mod("engine").play_hand(seed, seat0_policy, seat1_policy)


# --------------------------------------------------------------------------
# Tolerant readers.  A case asserts the contract, never a spelling of its own.
# --------------------------------------------------------------------------
def seed_key(seed):
    """The seed as the per-seed sub-records key it: a decimal string (`loop.md` §4)."""
    return str(int(seed))


def resolve(path):
    """One declared path as a filesystem path.

    The shipped index, and a run record whose artefact is inside the repository,
    carry the repository-relative spelling (`docs/L3/training/checkpoints.md` §2), so
    a reader resolves it against the repository root, which is where the battery runs
    (`docs/L1/battery.md` §2).  A record whose artefact is outside it -- a battery's
    run writes under the session's temporary write root -- carries the absolute path
    `agents.save` was handed unchanged (`docs/L2/training/write-root.md` §5).  Any
    absolute path, a caller's own checkpoint or one a case wrote into its scratch
    root, is taken as it stands.
    """
    text = str(path)
    if os.path.isabs(text):
        return os.path.abspath(text)
    return os.path.abspath(os.path.join(ROOT, text))


def canonical(record):
    """One record compared by value, whatever container a design chose."""
    return json.dumps(record, sort_keys=True, default=str)


def clone(record):
    return copy.deepcopy(record)


def token(text):
    return "".join(ch for ch in str(text).lower() if ch.isalnum())


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


def finite(value):
    return (
        isinstance(value, numbers.Real)
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def rung_order():
    """The six rung names in `rungs()`'s own order (`ladder.md` §2, D-2)."""
    return [str(name) for name in rungs()]


def variants_of(configuration):
    return list(configuration["variants"])


def variant_entry(configuration, name):
    for entry in variants_of(configuration):
        if str(entry["name"]) == str(name):
            return entry
    raise AssertionError(
        "the configuration %r declares no variant %r"
        % (configuration.get("name"), name)
    )


def pool_declaration_of(configuration):
    """A resolved configuration's pool entry (`registry.md` §3)."""
    return configuration["pool"]


def pool_of(record):
    """The pool record a run record carries (`loop.md` §3)."""
    return record["pool"]


def pool_member_ids(pool_record):
    return [str(member["id"]) for member in pool_record["members"]]


def is_baseline(member):
    """Whether a `records.md` §8 member is one of the pinned baselines."""
    if member.get("pinned") or member.get("baseline"):
        return True
    return str(member.get("id")) in set(baseline_names())


def baseline_names():
    """The catalogue's pinned baselines — its `anchor: True` members (`fairness.md` §5,
    ASM-32, D-21)."""
    declared = baselines()
    found = [
        str(name)
        for name, record in declared.items()
        if isinstance(record, dict) and record.get("anchor")
    ]
    return found or [str(name) for name in declared]


def catalogue_names():
    """The catalogue's six baseline names, in its order (D-21)."""
    return [str(name) for name in baselines()]


def utility_names():
    """The utilities `agents.learners()` publishes, in its declared order (`utilities.md` §2).

    The catalogue is the only vocabulary a `utility` is judged against, so a case reads the
    two members from that call and never restates a name (D-20, `utilities.md` §2, §5).
    """
    published = learners()["utilities"]
    return [str(name) for name in published]


def policy_utility(policy):
    """The utility a policy carries, or `None` (`e2e-surface.md` §2, `utilities.md` §6).

    `agents.as_policy` and `evaluation.policy_from` build a policy that names the utility
    the file it came from records, so a table can name each member's objective even when no
    other record of it exists yet (D-20, `utilities.md` §6, §7).
    """
    return getattr(policy, "utility", None)


def container_counterfactual(path):
    """The counterfactual member a checkpoint records, read off the loaded learner (§6).

    `agents.load` restores the learner a container holds, and a learner carries the name of
    the catalogue member its targets came from, so a case reads a version's training targets
    off the artefact itself and never off the record that claims them
    (`counterfactual.md` §6, `records.md` §7, D-43).  It is the learner and not the policy
    that is asked, because the pairwise instrument's member policy is `evaluation`'s and this
    pass is not the one that names the member there (`counterfactual.md` §6's scope bound,
    D-33, D-43).
    """
    return getattr(load(None, path), "counterfactual", None)


def counterfactual_names():
    """The counterfactual catalogue `agents.learners()` publishes, in its declared order.

    The third catalogue of `counterfactual.md` §6, read from the call and never restated:
    its first member is the default a spec naming none is built under (`D-43`).
    """
    published = learners()["counterfactuals"]
    return [str(name) for name in published]


def baseline_members(pool_record):
    return [m for m in pool_record["members"] if is_baseline(m)]


def version_members(pool_record):
    return [m for m in pool_record["members"] if not is_baseline(m)]


def curve_of(record, variant, seed):
    return record["curves"][str(variant)][seed_key(seed)]


def timings_of(record, variant, seed):
    return record["timings"][str(variant)][seed_key(seed)]


def checkpoints_of(record, variant, seed):
    return record["checkpoints"][str(variant)][seed_key(seed)]


def params_of(record, variant):
    return record["params"][str(variant)]


def declared_param_budget(configuration, variant):
    """A variant entry's declared `param_budget` (`records.md` §2, ASM-10)."""
    return int(variant_entry(configuration, variant)["param_budget"])


def band(budget):
    """The ±2% band a declared parameter budget states (`surface.md` §4, ASM-10)."""
    return 0.98 * float(budget), 1.02 * float(budget)


def entries():
    return list(checkpoints()["entries"])


def index_ids():
    return [str(entry["id"]) for entry in entries()]


def family_names():
    return [str(name) for name in protocol()["families"]]


def header_items():
    return [str(item) for item in protocol()["header"]]


def live_cell_size():
    return int(league()["tables"]["live"]["hands_per_cell"])


def baseline_rows(record):
    """A run record's `baselines` family -- the three declared rows (`surface.md` §4.1)."""
    declared = record["baselines"]
    if isinstance(declared, Mapping):
        for key, value in declared.items():
            if token(key) in ("rows", "baselines", "members"):
                return list(value)
        raise AssertionError(
            "the `baselines` family carries no rows: %r" % (declared,)
        )
    return list(declared)


def axis_row(record):
    return str(record["axis row"])


def header_of(record):
    return record["header"]


def statistic(statistics, name):
    """One key of `agents.learn`'s record (`agents/surface.md` §7)."""
    if isinstance(statistics, Mapping) and name in statistics:
        return statistics[name]
    return _lookup(statistics, (name,), "agents.learn's %r statistic" % (name,))


def same_descriptor(left, right):
    """Two descriptors compared by value (`docs/L2/engine/surface.md` §2)."""
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
        "the descriptor %r is not one of legal_actions %r" % (descriptor, actions)
    )


def action_index(result):
    """The chosen index out of `agents.act`'s return (`records.md` §6)."""
    if isinstance(result, int) and not isinstance(result, bool):
        return int(result)
    if isinstance(result, Mapping):
        for key, value in result.items():
            if any(part in str(key).lower()
                   for part in ("action", "index", "choice")):
                if isinstance(value, int) and not isinstance(value, bool):
                    return int(value)
    raise AssertionError(
        "cannot read an action index out of agents.act's return: %r" % (result,)
    )


def episode_payoffs(episode):
    """The episode's per-seat net chips (`records.md` §5, ASM-12)."""
    declared = _lookup(episode, ("payoffs", "payoff", "returns"),
                       "an episode record's payoffs")
    if not isinstance(declared, Mapping):
        raise AssertionError("the episode's payoffs are not a mapping: %r"
                             % (declared,))
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


def episode_decisions(episode):
    return list(_lookup(episode, ("decisions", "decision"),
                        "an episode record's decisions"))


def episode_seed(episode):
    return _lookup(episode, ("seed",), "an episode record's seed")


def readout_at(seed):
    """One real readout and its legal descriptors, from the engine's deal at `seed`."""
    hand = new_hand(seed)
    return readout(hand), legal_actions(hand)


def stream_after_deal(seed):
    """The global stream's state after `engine.new_hand(seed)` dealt one hand.

    `new_hand` is the project's single seeding point, so the state it leaves is a
    function of its seed alone (`docs/L2/engine/surface.md` §4, ASM-2); the
    caller's stream is restored, so reading it moves nothing.
    """
    before = random.getstate()
    try:
        new_hand(seed)
        return random.getstate()
    finally:
        random.setstate(before)


def caller(readout_record, legal):
    """Check/call when legal, else the smallest legal index; no randomness."""
    indices = list(legal_indices(legal))
    index = 1 if 1 in indices else indices[0]
    return decode_action(index)


def hand_cell(member_a, member_b, hands, wins, ties):
    """One `records.md` §9 cell, both directions the same hands seen from a seat.

    Used only for the members no cell is played for: the pair whose real cell the
    battery plays through `evaluation.match` keeps that record (`records.md` §9,
    `docs/L2/evaluation/surface.md` §9), and `evaluation.rating` accepts the rest
    because what it checks is the record and not its provenance
    (`docs/L2/evaluation/surface.md` §11).
    """
    losses = int(hands) - int(wins) - int(ties)
    if losses < 0:
        raise AssertionError(
            "a hand-built cell cannot have negative losses: %r/%r over %r hands"
            % (wins, ties, hands)
        )
    split_a = {"seat 0": (int(hands) + 1) // 2, "seat 1": int(hands) // 2}
    split_b = {"seat 0": int(hands) // 2, "seat 1": (int(hands) + 1) // 2}
    return {
        "members": [member_a, member_b],
        "hands": int(hands),
        "directions": [
            {"wins": int(wins), "ties": int(ties), "losses": losses,
             "mean_chip_delta": 0.0, "seat_split": split_a},
            {"wins": losses, "ties": int(ties), "losses": int(wins),
             "mean_chip_delta": 0.0, "seat_split": split_b},
        ],
        "params": [0, 0],
        "seed": 0,
    }


# --------------------------------------------------------------------------
# The module-level fixtures, built once per process.
# --------------------------------------------------------------------------
_SHARED = {}


def _run_observed(spec, budget, key):
    """One run, with the global stream sampled immediately around the call."""
    before = random.getstate()
    record = run(spec, seeds=[RUN_SEED], budget=budget)
    after = random.getstate()
    _SHARED[key] = {"record": record, "before": before, "after": after}
    return _SHARED[key]


def _run_at(spec, seed, budget, key):
    before = random.getstate()
    record = run(spec, seeds=[seed], budget=budget)
    after = random.getstate()
    _SHARED[key] = {"record": record, "before": before, "after": after}
    return _SHARED[key]


def small_run():
    """The battery's one-variant run: R1 at an invented seed and budget."""
    if "small" not in _SHARED:
        _run_observed("R1", RUN_BUDGET, "small")
    return _SHARED["small"]["record"]


def small_run_stream():
    """What the R1 run did to the global stream, sampled at build time."""
    small_run()
    return _SHARED["small"]


def window_run():
    """R2's run: its pool is R1's retained window (`loop.md` §1 step 2)."""
    if "window" not in _SHARED:
        _run_observed("R2", PAIR_BUDGET, "window")
    return _SHARED["window"]["record"]


def pair_run():
    """R4's run: the rung's own two-variant pair (`registry.md` §1)."""
    if "pair" not in _SHARED:
        _run_observed("R4", PAIR_BUDGET, "pair")
    return _SHARED["pair"]["record"]


def repeat_run():
    """A second run of the R1 tuple, built from the same `(config, seed, budget)`."""
    if "repeat" not in _SHARED:
        _run_observed("R1", RUN_BUDGET, "repeat")
    return _SHARED["repeat"]["record"]


def repeat_run_stream():
    """What the repeat run did to the global stream, sampled at build time."""
    repeat_run()
    return _SHARED["repeat"]


def other_seed_run():
    """R1's run at another invented seed (`surface.md` §4, FAM-4.8)."""
    if "other" not in _SHARED:
        _run_at("R1", RUN_SEED_OTHER, RUN_BUDGET, "other")
    return _SHARED["other"]["record"]


def two_utility_configuration():
    """A two-variant configuration whose arms declare the two catalogue utilities (D-20).

    A configuration in no design document (`docs/L1/battery.md` §4, D-15), written to
    `records.md` §2's shape: the registry's own R1 entry, declared twice under two variant
    names, with only the `utility` differing — one backend, one encoding, one
    architecture, one rule, one `hyper`, one seed set and one budget — so the two arms are
    one capacity trained on two rewards (`utilities.md` §3, §7, D-20). The utilities are
    read from `agents.learners()`, so no member name is restated here.
    """
    first_utility, second_utility = utility_names()[:2]
    template = clone(variant_entry(rung("R1"), "naive-numeric"))
    template["samples"] = UTILITY_BUDGET
    template["snapshot_every"] = max(1, UTILITY_BUDGET // SNAPSHOT_POINTS)
    left = clone(template)
    left["name"] = UTILITY_LEFT
    left["utility"] = first_utility
    right = clone(template)
    right["name"] = UTILITY_RIGHT
    right["utility"] = second_utility
    return {
        "name": UTILITY_RUNG,
        "axis": "the utility, at one architecture",
        "carried_from": None,
        "primary": UTILITY_LEFT,
        "variants": [left, right],
        "pool": {
            "id": UTILITY_POOL,
            "lineage": None,
            "m": 5,
            "frozen": True,
            "members": [],
        },
        "seeds": [UTILITY_SEED, UTILITY_SEED_OTHER],
        "samples": UTILITY_BUDGET,
        "param_budget": int(template["param_budget"]),
        "table": "live",
        "device": "cpu",
        "snapshot_every": max(1, UTILITY_BUDGET // SNAPSHOT_POINTS),
    }


def two_utility_run():
    """One run of it, built once per process: two arms, two rewards, one run record.

    Both variants are trained — D-20 makes the objective a parameter a variant names — so
    the record is the observable that says so: a curve, a final model and a utility per
    arm (`utilities.md` §7, `records.md` §12, `docs/L3/training/loop.md` §1 step 3).
    """
    if "utility" not in _SHARED:
        _SHARED["utility"] = run(
            two_utility_configuration(),
            seeds=[UTILITY_SEED, UTILITY_SEED_OTHER],
            budget=UTILITY_BUDGET,
        )
    return _SHARED["utility"]


def counterfactual_configuration():
    """A one-variant configuration declaring the catalogue's **second** counterfactual member.

    The registry's own R1 entry, declared on the invented budget and seed with one key added
    — the member `counterfactual.md` §6 puts second, read from `agents.learners()` and never
    restated — so the run is the registry's own arm on every other axis and the only
    difference is what its learner takes its training targets from (`counterfactual.md` §6,
    `records.md` §12, `docs/L1/battery.md` §4, D-43).
    """
    template = clone(variant_entry(rung("R1"), "naive-numeric"))
    template["samples"] = UTILITY_BUDGET
    template["snapshot_every"] = max(1, UTILITY_BUDGET // SNAPSHOT_POINTS)
    template["name"] = COUNTERFACTUAL_VARIANT
    template["counterfactual"] = counterfactual_names()[1]
    return {
        "name": COUNTERFACTUAL_RUNG,
        "axis": "the counterfactual member, at one architecture",
        "carried_from": None,
        "primary": COUNTERFACTUAL_VARIANT,
        "variants": [template],
        "pool": {
            "id": COUNTERFACTUAL_POOL,
            "lineage": None,
            "m": 5,
            "frozen": True,
            "members": [],
        },
        "seeds": [COUNTERFACTUAL_SEED],
        "samples": UTILITY_BUDGET,
        "param_budget": int(template["param_budget"]),
        "table": "live",
        "device": "cpu",
        "snapshot_every": max(1, UTILITY_BUDGET // SNAPSHOT_POINTS),
    }


def counterfactual_run():
    """One run of it, built once per process: one arm, one member, one run record.

    The record is the observable this join reads — a `variants` row naming the member and a
    `counterfactuals` set holding it — and the container beside it is the artefact a table
    would name, so the member reaches a pool only through a file that records it
    (`counterfactual.md` §6, `records.md` §7, §12, D-43).
    """
    if "counterfactual" not in _SHARED:
        _SHARED["counterfactual"] = run(counterfactual_configuration())
    return _SHARED["counterfactual"]


def episode():
    """One real episode: two declared baselines playing one seeded hand."""
    if "episode" not in _SHARED:
        _SHARED["episode"] = play_hand(
            EPISODE_SEED,
            build_baseline("always-call", EPISODE_BASELINE_A),
            build_baseline("random", EPISODE_BASELINE_B),
        )
    return _SHARED["episode"]


def showdown_episode():
    """One real episode two always-call baselines play to a river showdown.

    The hand D-43's resolution is observable on: nobody folds, so two seats show and the
    reveal resolves every decision of it (`counterfactual.md` §4, `episode.md` §5).  It is
    the battery's own invented seed and two fresh baseline objects, built once per process
    because a baseline is stateful (`battery.md` §4, `docs/L3/training/episode.md` §1).
    """
    if "showdown" not in _SHARED:
        _SHARED["showdown"] = play_hand(
            SHOWDOWN_SEED,
            build_baseline("always-call", EPISODE_BASELINE_A),
            build_baseline("always-call", EPISODE_BASELINE_B),
        )
    return _SHARED["showdown"]


def flat_encoder():
    """The encoder a run's own record names for its variant (`loop.md` §1 step 3)."""
    if "encoder" not in _SHARED:
        entry = variant_entry(rung("R1"), "naive-numeric")
        _SHARED["encoder"] = build_encoder(entry["encoding"])
    return _SHARED["encoder"]


def acting_seat():
    """A seat the battery's episode gives at least one decision (`episode.md` §3)."""
    if "acting_seat" not in _SHARED:
        encoder = flat_encoder()
        chosen = None
        for seat in (0, 1):
            if transitions(episode(), seat, encoder):
                chosen = seat
                break
        if chosen is None:
            raise AssertionError(
                "the battery's episode must give at least one seat a decision; it "
                "gives neither (docs/L3/training/episode.md §3, records.md §5)"
            )
        _SHARED["acting_seat"] = chosen
    return _SHARED["acting_seat"]


def batch():
    """The transitions `_transitions` builds from the battery's one real episode."""
    if "batch" not in _SHARED:
        _SHARED["batch"] = transitions(episode(), acting_seat(), flat_encoder())
    return _SHARED["batch"]


def learner_spec(entry, seed, encoder):
    """A learner spec built exactly as the loop builds it (`loop.md` §1 step 3)."""
    return {
        "backend": entry["backend"],
        "architecture": copy.deepcopy(dict(entry["architecture"])),
        "seed": int(seed),
        "encoder": encoder,
    }


def parity_entries():
    """The registry's own R1 and R2 variants: one architecture, two backends.

    R1 and R2 declare one architecture key for key, one encoding and one update
    rule and differ only in `backend` (`registry.md` §1, `docs/L1/ladder.md` §5,
    D-7), so these two entries are the parity pair's two arms.
    """
    return (variant_entry(rung("R1"), "naive-numeric"),
            variant_entry(rung("R2"), "naive-numeric-torch"))


def parity_learners():
    """Two fresh learners from those entries at one seed, and a second seed's.

    A learner is mutable -- `agents.learn` moves its state (`agents/surface.md`
    §7) -- so every case builds the learners it trains; nothing here is shared
    across cases.
    """
    encoder = flat_encoder()
    r1, r2 = parity_entries()
    return {
        "numpy": build_learner(learner_spec(r1, RUN_SEED, encoder)),
        "torch": build_learner(learner_spec(r2, RUN_SEED, encoder)),
        "other_seed": build_learner(
            learner_spec(r1, RUN_SEED + LEARNER_SEED_OFFSET, encoder)
        ),
        "same_seed_again": build_learner(learner_spec(r1, RUN_SEED, encoder)),
        "r1_entry": r1,
        "r2_entry": r2,
        "encoder": encoder,
    }


def decisions(learner, batch_transitions):
    """The indices one learner chooses over a batch's own observations."""
    return tuple(
        action_index(act(learner, item["observation"], item["legal"]))
        for item in batch_transitions
    )


def matrix_and_rating():
    """The hand-built table of join 7 and the rating fitted to it.

    `evaluation.report` requires a matrix and a rating beside the record's seven
    families (`docs/L2/evaluation/surface.md` §13), and `evaluation.matrix` takes
    a *table budget* whose live cell is 120 hands (`docs/L1/league.md` §6,
    ASM-14) -- far more than a join battery may spend.  So the table is the
    pool's membership plus one declared variant label, one pair of it is played
    for real through `evaluation.match`, and the rest are `records.md` §9 records
    at the same hand count, which `evaluation.rating` accepts because what it
    checks is the record and not its provenance (`docs/L2/evaluation/surface.md`
    §11, `records.md` §10).
    """
    if "matrix" not in _SHARED:
        pool_record = pool_of(small_run())
        members = [str(member["id"]) for member in baseline_members(pool_record)]
        members.append(VARIANT_LABEL)
        real = match(members[0], members[1], CELL_HANDS, CELL_SEED)
        cells = []
        for i, j in itertools.combinations(range(len(members)), 2):
            if {members[i], members[j]} == {members[0], members[1]}:
                cells.append(clone(real))
            else:
                cells.append(hand_cell(members[i], members[j], CELL_HANDS,
                                       CELL_HANDS // 2, 0))
        matrix_record = {
            "members": members,
            "cells": cells,
            "hands_per_cell": CELL_HANDS,
            "table_seed": TABLE_SEED,
            "table": "live",
        }
        _SHARED["matrix"] = matrix_record
        _SHARED["rating"] = rating(matrix_record)
    return _SHARED["matrix"], _SHARED["rating"]


def report_record():
    """A run record with a matrix and a rating attached (`records.md` §13)."""
    matrix_record, rating_record = matrix_and_rating()
    record = clone(small_run())
    record["matrix"] = clone(matrix_record)
    record["rating"] = clone(rating_record)
    return record


# --------------------------------------------------------------------------
# The base case: a scratch root, a refusal reader and the stream readers.
# --------------------------------------------------------------------------
class JoinCase(unittest.TestCase):
    """The base every case extends: a scratch root and the join's readers."""

    def setUp(self):
        self._scratch = None

    def scratch(self):
        if self._scratch is None:
            self._scratch = tempfile.mkdtemp(prefix="training-join-case-")
            self.addCleanup(shutil.rmtree, self._scratch, True)
        return self._scratch

    def assert_refusal(self, entry, groups, call, note=""):
        """Require `call` to be refused, naming the entry point and every group.

        The exception class is tolerated: `docs/L3/training/errors.md` §2 leaves the
        hierarchy below the base class, while §3 fixes the message grammar -- the
        entry point by its module path and the offending value named.  Each group
        is one spelling or a tuple of alternative spellings, one of which must
        appear in the message.
        """
        try:
            result = call()
        except SurfaceAbsent:
            raise
        except Exception as exc:  # noqa: BLE001 - the class is the design's freedom
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
            if not any(str(alternative).lower() in lowered
                       for alternative in alternatives):
                self.fail(
                    "%s: the refusal must name one of %r; the message was %r"
                    % (note or entry, alternatives, message)
                )
        return message

    def assert_stream_unchanged(self, call, what):
        """Require `call` to leave `random.getstate()` exactly as it found it.

        The stream is restored afterwards, so one case's finding never moves the
        stream a later case deals from (`docs/L2/training/surface.md` §1, ASM-2).
        """
        before = random.getstate()
        try:
            result = call()
        finally:
            after = random.getstate()
            random.setstate(before)
        self.assertEqual(
            after,
            before,
            "%s deals no hand and must leave the global `random` stream exactly as "
            "it found it (docs/L2/training/surface.md §1, ASM-2)" % (what,),
        )
        return result

    def assert_stream_at_last_deal(self, state_after, seed, index, what):
        """Require the stream to stand where the last hand's deal left it.

        A run moves the global stream only through `engine.new_hand`
        (`docs/L2/training/surface.md` §1, `docs/L3/training/seeds.md` §1, ASM-2),
        so after a pass it is where hand `index` at run seed `seed` left it.
        """
        self.assertEqual(
            state_after,
            stream_after_deal(deal_seed(seed, index)),
            "%s must move the global `random` stream only through "
            "`engine.new_hand`, so it must stand where the last hand's deal -- hand "
            "%r of run seed %r -- left it (docs/L2/training/surface.md §1, ASM-2)"
            % (what, index, seed),
        )

    def assert_descriptor_in(self, legal, descriptor, note=""):
        self.assertTrue(
            any(same_descriptor(descriptor, candidate) for candidate in legal),
            "%s: the chosen descriptor %r must be one of legal_actions %r"
            % (note, descriptor, list(legal)),
        )

    def assert_finite(self, value, what, citation):
        self.assertTrue(
            finite(value),
            "%s must be one finite number (%s); it is %r" % (what, citation, value),
        )
        return float(value)
