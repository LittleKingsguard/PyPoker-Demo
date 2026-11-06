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
  real episode with its transitions, the two backends' learners, and the hand-built
  matrix with its fitted rating.  A run is this battery's expensive observable, so
  each is built once per process and shared (`docs/L2/training/loop.md` §3,
  `docs/L1/battery.md` §2); every run stays at ten to twelve hands per variant per
  seed.

Two private `training` names are re-imported here and used as contract, exactly as
`docs/L3/training/seeds.md` §2 and `docs/L3/training/episode.md` §3 mark them
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


def build_encoder(name):
    return mod("features").build_encoder(name)


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
    """Whether a `records.md` §8 member is one of the three pinned baselines."""
    if member.get("pinned") or member.get("baseline"):
        return True
    return str(member.get("id")) in set(baseline_names())


def baseline_names():
    return [str(name) for name in baselines()]


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


def episode():
    """One real episode: two declared baselines playing one seeded hand."""
    if "episode" not in _SHARED:
        _SHARED["episode"] = play_hand(
            EPISODE_SEED,
            build_baseline("always-call", EPISODE_BASELINE_A),
            build_baseline("random", EPISODE_BASELINE_B),
        )
    return _SHARED["episode"]


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
