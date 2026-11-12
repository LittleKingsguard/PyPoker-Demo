"""Join plumbing and invented instances for the `evaluation` integration battery.

This module is test support, not a subsystem (brief §5, `module-map.md` §5).  It
does four things and nothing else:

* it puts ``<repo>/src`` on ``sys.path`` and imports ``evaluation``, ``agents``,
  ``features`` and ``engine`` lazily, so a missing surface is one ``SurfaceAbsent``
  failure in the case that needed it and never a collection error
  (`battery.md` §2);
* it holds the battery's *invented instances* — version ids, a lineage chain,
  checkpoint names, learner seeds, a variant seed, deal seeds, hand counts, a
  hand-built table seed and a membership of the writer's own — none of which
  appears in a design document or in `tests/e2e/` (`docs/L1/battery.md` §4,
  D-15, `docs/L1/e2e-surface.md` §5).  A learner, an encoder, a checkpoint, a
  pool, a policy, a cell, a matrix and a rating are never fabricated: every one
  is produced by the module that owns it — `agents.build_learner` + `agents.save`,
  `features.build_encoder`, `evaluation.build_pool`, `agents.build_baseline`,
  `evaluation.match`, `evaluation.matrix`, `evaluation.rating` — because a join
  judged through a hand-written record would judge nothing (`docs/L1/protocol.md`
  §5, D-16);
* it holds *tolerant readers* for the shapes the records leave free: the rating's
  per-member entry and its interval (`docs/L1/records.md` §11, `docs/L3/evaluation/
  rating.md` §5, §7), a cell's two directions (`records.md` §9, `docs/L3/evaluation/
  scheduler.md` §8), a policy's descriptor and `agents.act`'s chosen index, and a
  readout's seat fact.  A case asserts the contract through these readers instead
  of inventing a spelling of its own;
* it holds the small call vocabulary the cases are written in — one wrapper per
  entry point `evaluation` publishes and per granted call of the three modules it
  consumes (`module-map.md` §2) — plus the module-level fixtures the battery
  shares: the invented checkpoint, the invented frozen pool, the invented variant
  policy and **one** real `live` matrix with its rating.  A `live` matrix at the
  league's 120 hands a cell is this battery's one expensive observable, so it is
  built once per process and shared (`docs/L2/evaluation/league.md` §5, ASM-15);
  every `match` in the battery stays at a dozen hands or fewer.

Nothing here reaches past an entry point of `e2e-surface.md` §3.4 or of the three
consumed surfaces (`docs/L2/engine/surface.md`, `docs/L2/features/surface.md`,
`docs/L2/agents/surface.md`).  Each case module loads this file under the private
name ``evaluation_join_support``: the repository's integration batteries share the
file name ``_join_support.py``, and a plain import would let one battery's helpers
stand in for another's when two test directories are collected in one process.
"""

from __future__ import annotations

import atexit
import copy
import hashlib
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
from collections.abc import Mapping, Sequence

# --------------------------------------------------------------------------
# The four packages, imported lazily.
# --------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SRC = os.path.join(ROOT, "src")
SHIPPED_PATH = os.path.join(ROOT, "tables", "league-full.json")
SHIPPED_SCHEMA = "pypoker-evaluation-league-table/1"
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
# docs/ carries them and `tests/e2e/` uses none of them (docs/L1/battery.md §4,
# D-15).  The league's own numbers — M = 5, the table seed 20261105, the cell
# sizes 120 and 1500 — appear below only where a case reads them out of a
# published declaration or builds the one shared live table, never as a stand-in
# for an invented instance (`docs/L2/evaluation/surface.md` §4, `declarations.md`
# §6).
# --------------------------------------------------------------------------
CHECKPOINT_SEED = 58391        # learner seeds, invented
CHECKPOINT_SEED_B = 52861
CHECKPOINT_SEED_C = 46103
CHECKPOINT_SEED_D = 33907
CHECKPOINT_SEED_E = 90733
CHECKPOINT_SEED_F = 27739
VARIANT_SEED = 66413           # the shared variant policy's seed, invented
MATCH_SEED = 62077             # cell seeds, invented
MATCH_SEED_OTHER = 71549
REPLAY_SEED = 80231
HAND_BUILT_TABLE_SEED = 84673  # a hand-built table's own seed, invented
DRAW_MULTIPLE = 7919           # seeds for a drawn member: seed % n == position

WIDTH_A = 27                   # widths and depths, invented (small: 21-31, 1-2)
WIDTH_B = 31
DEPTH_A = 2
DEPTH_B = 1
DEFAULT_ENCODING = "flat-numeric"
DEFAULT_KIND = "naive-stack"

HANDS_DOZEN = 12               # hand counts, invented (the league's are 120/1500)
HANDS_TEN = 10
HANDS_NINE = 9
HANDS_SEVEN = 7
HANDS_FOUR = 4
HANDS_TWO = 2

VERSION_A = "version-goshawk"  # version ids, invented
VERSION_B = "version-dunlin"
VERSION_C = "version-plover"
VERSION_D = "version-wigeon"
VERSION_E = "version-snipe"
VERSION_F = "version-curlew"
FOREIGN_MEMBER = "version-outsider-6389"
START_LABEL = "R9/start"       # a rung start label, invented
RUNG = "R9"                    # an unregistered rung label, invented
VARIANT_LABEL = "flat-narrow"
STEP = 40                      # a snapshot step and a hands-trained count, invented
SAMPLES = 840
SAMPLE_BUDGET = 840

CHECKPOINT_A = "evaluation-join-goshawk.ckpt"   # checkpoint file names, invented
CHECKPOINT_B = "evaluation-join-dunlin.ckpt"
CHECKPOINT_C = "evaluation-join-plover.ckpt"
CHECKPOINT_D = "evaluation-join-wigeon.ckpt"
CHECKPOINT_E = "evaluation-join-snipe.ckpt"
CHECKPOINT_F = "evaluation-join-curlew.ckpt"
CHECKPOINT_MISSING = "evaluation-join-absent.ckpt"

#: The learning-rule catalogue's two members, by the names this battery asserts against
#: (`rules.md` §2, D-19).  The catalogue itself is always read off `agents.learners()`,
#: which a case checks, so no copy of it lives in the module under test.
DEFAULT_RULE = "masked-q-learning"
OTHER_RULE = "double-q-learning"
RULES = (DEFAULT_RULE, OTHER_RULE)

#: The utility catalogue's two members, on the same terms (`utilities.md` §2, D-20): the
#: names this battery asserts against, with the catalogue itself always read off
#: `agents.learners()`.
DEFAULT_UTILITY = "net-chips"
OTHER_UTILITY = "stack-shortfall"
UTILITIES = (DEFAULT_UTILITY, OTHER_UTILITY)

#: The counterfactual catalogue's two members, on the same terms (`counterfactual.md` §2, §6,
#: D-43): the names this battery asserts against, with the third catalogue itself always read
#: off `agents.learners()`.  `none` is its first member and the declared default -- the rule's
#: own target, unchanged -- and a member trained under it carries no container field and
#: appends nothing to a pool's id.
DEFAULT_COUNTERFACTUAL = "none"
OTHER_COUNTERFACTUAL = "reveal-counterfactual"
COUNTERFACTUALS = (DEFAULT_COUNTERFACTUAL, OTHER_COUNTERFACTUAL)

HAND_BUILT_MEMBERS = (
    "random",
    "always-call",
    "oracle",
    "version-goshawk",
)
HAND_BUILT_COUNTS = (
    (3, 0, HANDS_SEVEN - 3),   # random vs always-call: wins, ties, losses
    (2, 0, HANDS_SEVEN - 2),   # random vs oracle
    (2, 1, HANDS_SEVEN - 3),   # random vs the version
    (3, 0, HANDS_SEVEN - 3),   # always-call vs oracle
    (3, 0, HANDS_SEVEN - 3),   # always-call vs the version
    (2, 1, HANDS_SEVEN - 3),   # oracle vs the version
)


# --------------------------------------------------------------------------
# The small call vocabulary: one wrapper per published entry point.
# --------------------------------------------------------------------------
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


def matrix(pool, variants, table):
    return mod("evaluation").matrix(pool, variants, table)


def rating(matrix_record):
    return mod("evaluation").rating(matrix_record)


def policy_from(path, exploration="schedule"):
    """`evaluation.policy_from(path, exploration)` -- the mode is D-29's second argument.

    `docs/L2/evaluation/surface.md` §12 and `docs/L3/evaluation/shape.md` §5 declare the
    optional mode, `schedule` being its absence, so this wrapper names it explicitly and
    a case can hand over `off` (`sizing.md` §4, D-29).
    """
    return mod("evaluation").policy_from(path, exploration)


def report(rung_name, record, matrix_record, rating_record):
    return mod("evaluation").report(rung_name, record, matrix_record, rating_record)


def baselines():
    return mod("agents").baselines()


def declared_params(name):
    """The `params` count `agents.baselines()` declares for one baseline."""
    declared = baselines()[str(name)]
    value = _lookup(declared, ("params", "parameter", "count"),
                    "a baseline catalogue entry's params")
    return int(value)


def unlabelled_of(cell):
    """The ids whose `params` is an unmeasured zero (`scheduler.md` §4)."""
    try:
        declared = _lookup(cell, ("unlabelled", "unlabeled"),
                           "a cell record's unlabelled ids")
    except AssertionError:
        return set()
    return {str(member) for member in declared}


def build_baseline(name, seed):
    return mod("agents").build_baseline(name, seed)


def as_policy(learner, encoder, seed, exploration="schedule"):
    """`agents.as_policy(learner, encoder, seed, exploration)` (`agents/surface.md` §9)."""
    return mod("agents").as_policy(learner, encoder, seed, exploration)


def load(spec, path):
    return mod("agents").load(spec, path)


def declared_constant(module_name, attribute):
    """One named constant of a package under test, read for a restatement a case compares.

    `docs/L3/evaluation/shape.md` §1 gives the **join** battery the duty of holding
    `declarations.py`'s `SHAPE_NAMES` equal, in that order, to the names
    `engine.game_shapes()` publishes, and `EXPLORATION_MODES` equal to the modes
    `agents.as_policy` accepts -- so this is the one place a battery reads a module
    constant rather than an entry point, and `README.md` §4 declares those constants
    contract for it (`shape.md` §1, D-29).
    """
    module = mod(module_name)
    if not hasattr(module, attribute):
        raise AssertionError(
            "%s.%s is not declared, and shape.md §1 names it the restatement this join "
            "battery holds equal to the catalogue" % (module_name, attribute)
        )
    return getattr(module, attribute)


def act(learner, observation, legal_mask):
    return mod("agents").act(learner, observation, legal_mask)


def decision_as_act(learner, encoder, readout_record, legal):
    """The index `agents.act` chooses on `features.encode`'s observation.

    A member policy must decide as its learner does on the same readout
    (`docs/L2/agents/surface.md` §10, `docs/L1/protocol.md` §5), and the
    observation and the mask are the encoding's and the vocabulary's
    (`docs/L2/features/surface.md` §6, §8).
    """
    observation = encode(encoder, readout_record)
    mask = legal_indices(legal)
    return action_index(act(learner, observation, mask))


def param_count(learner):
    return mod("agents").param_count(learner)


def build_learner(spec):
    return mod("agents").build_learner(spec)


def save(learner, path):
    return mod("agents").save(learner, path)


def learners():
    return mod("agents").learners()


def build_encoder(name, shape=None):
    """`features.build_encoder(name, shape=...)` -- the shape is a **keyword** (§4-§5).

    An encoder carries the shape it was built for, because the second game shape changes
    the divisor and bucket tables of both encodings (`docs/L2/features/surface.md`
    §3-§5, `docs/L3/evaluation/shape.md` §4).  Absent, the declared default is built,
    which is what every caller that names no shape keeps (`docs/L1/shapes.md` §3).
    """
    return mod("features").build_encoder(name, shape=shape)


def encodings():
    return mod("features").encodings()


def observation_spec(encoder):
    return mod("features").observation_spec(encoder)


def encode(encoder, readout):
    return mod("features").encode(encoder, readout)


def legal_indices(legal_actions):
    return tuple(mod("features").legal_indices(legal_actions))


def decode_action(index, shape=None):
    """`features.decode_action(index, shape=...)`: an index decodes in one vocabulary.

    `docs/L2/features/surface.md` §9 and `docs/L3/evaluation/shape.md` §4: the shape
    decides how many indices there are and which descriptor each denotes, so a member of
    the second shape decodes its descriptor in that shape's vocabulary and never in the
    default one's.
    """
    return mod("features").decode_action(index, shape=shape)


def action_space():
    return mod("features").action_space()


def new_hand(seed, shape=None):
    """`engine.new_hand(seed, shape)` -- the project's single seeding point (`surface.md` §4)."""
    return mod("engine").new_hand(seed, shape)


def game_shapes():
    """`engine.game_shapes()` -- the catalogue, default first (`engine/surface.md` §12)."""
    return mod("engine").game_shapes()


def game_config(shape=None):
    """`engine.game_config(shape)` (`engine/surface.md` §3)."""
    return mod("engine").game_config(shape)


def readout(hand):
    return mod("engine").readout(hand)


def legal_actions(hand):
    return mod("engine").legal_actions(hand)


def play_hand(seed, seat0_policy, seat1_policy):
    return mod("engine").play_hand(seed, seat0_policy, seat1_policy)


def is_terminal(hand):
    return mod("engine").is_terminal(hand)


def apply_action(hand, descriptor):
    return mod("engine").apply_action(hand, descriptor)


# --------------------------------------------------------------------------
# Caller-side policies and decisions over real hands (`e2e-surface.md` §2).
# --------------------------------------------------------------------------
def caller(readout_record, legal):
    """Check/call when legal, else the smallest legal index; no randomness."""
    indices = list(legal_indices(legal))
    index = 1 if 1 in indices else indices[0]
    return decode_action(index)


def decisions_of(seed, policy, limit=200, shape=None):
    """The `(readout, legal actions)` pairs of one hand driven by `policy`.

    `shape` is the hand's game, absent meaning the default: a decision's readout, its
    legal descriptors and the mask built from them are one shape's (`engine/surface.md`
    §4-§6, `features/surface.md` §8, `shapes.md` §4).
    """
    hand = new_hand(seed, shape)
    out = []
    steps = 0
    while not is_terminal(hand) and steps < limit:
        facts = readout(hand)
        legal = legal_actions(hand)
        out.append((facts, legal))
        hand = apply_action(hand, policy(facts, legal))
        steps += 1
    return out


def decision_signature(policy, decisions):
    """A policy's answers to a fixed list of decisions, for comparing two policies."""
    return tuple(
        descriptor_index(legal, policy(facts, legal))
        for facts, legal in decisions
    )


# --------------------------------------------------------------------------
# The catalogue-derived pairing: each architecture kind consumes the
# representation family `features.encodings()` declares for its encoding
# (docs/L2/agents/surface.md §3, docs/L2/features/surface.md §3).
# --------------------------------------------------------------------------
def encoding_for(kind):
    catalogue = learners()["architectures"]
    if kind not in catalogue:
        raise AssertionError(
            "agents.learners() declares no %r architecture kind; it declares %r"
            % (kind, sorted(catalogue))
        )
    family = catalogue[kind]["observation"]
    declared = [name for name, spec in encodings().items() if spec.get("kind") == family]
    if len(declared) != 1:
        raise AssertionError(
            "features.encodings() must declare exactly one encoding of the %r family "
            "the kind %r consumes; it declared %r" % (family, kind, declared)
        )
    return declared[0]


# --------------------------------------------------------------------------
# The pinned derivations (docs/L3/evaluation/scheduler.md §3, matrix.md §3).
#
# These five are the one place this module makes a *derivation* contract, and
# `docs/L3/evaluation/` pins them: one seed and one position give one result on
# any host, whatever was played before (`scheduler.md` §7).  A case re-derives a
# hand's seed, a cell's seed, a baseline's policy seed, the rating's bootstrap
# seed and a pool's id from these functions and compares the module's record
# against them; it never reaches into the module for the private names.
# --------------------------------------------------------------------------
def _digest(tag, *parts):
    payload = tag + b"\x1f" + b"\x1f".join(str(p).encode("utf-8") for p in parts)
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % (2 ** 31)


def hand_seed(seed, index):
    """The seed of one hand of a cell (`scheduler.md` §3)."""
    return _digest(b"pypoker-evaluation/hand/v1", seed, index)


def cell_seed(table_seed, i, j):
    """The seed of one cell, from the table seed and the pair's positions."""
    return _digest(b"pypoker-evaluation/cell/v1", table_seed, i, j)


def member_seed(table_seed, position):
    """A baseline member's policy seed, from the table seed and its position."""
    return _digest(b"pypoker-evaluation/member/v1", table_seed, position)


def bootstrap_seed(table_seed):
    """The rating's bootstrap seed, from the table's seed (`rating.md` §4)."""
    return _digest(b"pypoker-evaluation/bootstrap/v1", table_seed)


def draw_order(seed, size):
    """The counted draw's order: `size` positions, first `seed % size`, then the digest.

    `docs/L3/evaluation/seats.md` §2 and `docs/L2/evaluation/seats.md` §2 fix the
    derivation: the first position is `_draw_index(seed, n) == seed % n` -- the member the
    uncounted draw names -- and the remaining positions ascend by
    ``_digest(b"pypoker-evaluation/draw/v1", seed, position)``, ties broken by position, so
    the result is a permutation of ``0 .. size-1`` and a draw is without replacement
    (`docs/L1/seats.md` §4, `league.md` §2, ASM-43).  Re-derived here, never imported: a
    case compares the module's draw against this and not against itself.
    """
    count = int(size)
    first = int(seed) % count
    rest = [position for position in range(count) if position != first]
    rest.sort(
        key=lambda position: (
            _digest(b"pypoker-evaluation/draw/v1", seed, position),
            position,
        )
    )
    return (first,) + tuple(rest)


def pool_id(members):
    """A pool's id: one line per member, a baseline's id alone and a version's with its members.

    `docs/L3/evaluation/families.md` §4, ASM-27, D-20 and D-43: the payload is a baseline's
    id alone and a version's `id`, ``\\x1f``, then its `rule`, ``\\x1f``, then its
    `utility`, then ``\\x1f`` and its `counterfactual` **only when** the record carries one
    that is not the catalogue's first, `none` -- so a member trained under `none`, or one
    whose record names no such key, contributes exactly the line it contributed before the
    third catalogue existed, and every shipped id stays as it was (`docs/L1/
    counterfactual.md` §6, §9, D-43).  One line per member, joined by one ``\\n``; SHA-256,
    truncated to sixteen hex characters and prefixed `pool-`.  A sequence of bare ids is
    read as a baselines-only membership, which is what a caller holding only names can
    mean.
    """
    lines = []
    for member in members:
        if isinstance(member, Mapping):
            if member.get("baseline"):
                lines.append(str(member["id"]))
            else:
                line = "%s\x1f%s\x1f%s" % (
                    member["id"], member["rule"], member["utility"]
                )
                declared = member.get("counterfactual")
                if isinstance(declared, str) and declared != DEFAULT_COUNTERFACTUAL:
                    line = "%s\x1f%s" % (line, declared)
                lines.append(line)
        else:
            lines.append(str(member))
    payload = "\n".join(lines).encode("utf-8")
    return "pool-" + hashlib.sha256(payload).hexdigest()[:16]


# --------------------------------------------------------------------------
# The module-level fixtures, built once per process.
# --------------------------------------------------------------------------
_SHARED = {}


def scratch_root():
    """One scratch root for the fixtures, removed when the process ends."""
    if "root" not in _SHARED:
        root = tempfile.mkdtemp(prefix="evaluation-join-")
        atexit.register(shutil.rmtree, root, True)
        _SHARED["root"] = root
    return _SHARED["root"]


def checkpoint(name=CHECKPOINT_A, seed=CHECKPOINT_SEED, width=WIDTH_A, depth=DEPTH_A,
               kind=DEFAULT_KIND, rule=None, utility=None):
    """A real checkpoint: `agents.build_learner` then `agents.save`.

    `rule` is the catalogue member the learner is built under, and the container records
    it: `rules.md` §6 makes a checkpoint's `learning_rule` a required field of the format
    (D-19).  `utility` is the catalogue member whose reward the learner is trained on,
    and the container records that too: `utilities.md` §6 makes `utility` a required
    field of the same container (D-20).  A caller naming none gets each catalogue's first
    member, the declared default, so every caller that predates D-20 keeps the checkpoint
    it wrote before.
    """
    key = ("checkpoint", name, utility)
    if key not in _SHARED:
        encoder = build_encoder(encoding_for(kind))
        spec = {
            "backend": "numpy",
            "architecture": {"kind": kind, "width": width, "depth": depth},
            "seed": seed,
            "encoder": encoder,
        }
        if rule is not None:
            spec["learning_rule"] = rule
        if utility is not None:
            spec["utility"] = utility
        learner = build_learner(spec)
        suffix = "" if utility is None else "-" + "".join(
            ch for ch in str(utility).lower() if ch.isalnum()
        )
        path = save(learner, os.path.join(scratch_root(), name + suffix))
        _SHARED[key] = {
            "path": path,
            "learner": learner,
            "encoder": encoder,
            "params": param_count(learner),
            "seed": seed,
            "rule": rule,
            "utility": utility,
        }
    return _SHARED[key]


def version(member_id, lineage, checkpoint_name=CHECKPOINT_A, seed=CHECKPOINT_SEED,
            width=WIDTH_A, depth=DEPTH_A, step=STEP, samples=SAMPLES,
            utility=DEFAULT_UTILITY):
    """One `records.md` §7 version record carrying a real checkpoint's path.

    The checkpoint is built under the utility the record declares, so the pair the record
    states is the pair its container records: a member whose `utility` disagreed with its
    file is refused where it is played (`utilities.md` §6, §7, ASM-20, D-20).  The
    catalogue's first member is the declared default of `utilities.md` §5, which is what
    a learner built without one records, so a case naming the default needs no second
    file.
    """
    info = checkpoint(
        checkpoint_name,
        seed,
        width,
        depth,
        utility=None if utility == DEFAULT_UTILITY else utility,
    )
    return {
        "id": member_id,
        "path": info["path"],
        "rung": RUNG,
        "variant": VARIANT_LABEL,
        "seed": info["seed"],
        "step": step,
        "samples": samples,
        "lineage": lineage,
        # `records.md` §7 makes a version member's rule required (D-19); the checkpoint
        # this record names was built without a `learning_rule`, so it records the
        # catalogue's first member, which is the declared default of `rules.md` §4.
        "rule": DEFAULT_RULE,
        # ... and its `utility` on the same terms (D-20): the record declares the one the
        # checkpoint it names was built under, and the container agrees (`utilities.md`
        # §6, §7).
        "utility": utility,
    }


def bare_version(member_id, lineage, step=STEP, samples=SAMPLES, seed=CHECKPOINT_SEED,
                 rule=DEFAULT_RULE, utility=DEFAULT_UTILITY):
    """One `records.md` §7 version record with no `path`: admitted, not loadable."""
    return {
        "id": member_id,
        "lineage": lineage,
        "rung": RUNG,
        "variant": VARIANT_LABEL,
        "seed": seed,
        "step": step,
        "samples": samples,
        "rule": rule,
        "utility": utility,
    }


def variant_policy():
    """The rung's one variant: a real policy, already built (`matrix.md` §4)."""
    if "variant" not in _SHARED:
        encoder = build_encoder(DEFAULT_ENCODING)
        learner = build_learner(
            {
                "backend": "numpy",
                "architecture": {"kind": DEFAULT_KIND, "width": WIDTH_B,
                                 "depth": DEPTH_B},
                "seed": VARIANT_SEED,
                "encoder": encoder,
            }
        )
        _SHARED["variant"] = as_policy(learner, encoder, VARIANT_SEED)
        _SHARED["variant_learner"] = learner
        _SHARED["variant_encoder"] = encoder
    return _SHARED["variant"]


def shared_pool():
    """One frozen pool: the three baselines and one invented version."""
    if "pool" not in _SHARED:
        _SHARED["pool"] = build_pool(
            {
                "members": [version(VERSION_A, START_LABEL)],
                "m": league()["m"],
                "frozen": True,
            }
        )
    return _SHARED["pool"]


def shared_matrix():
    """The battery's one real `live` matrix, built once and shared.

    The stream is observed around the call and kept, so a case can assert that
    the table moved it and left it where the last hand's deal left it
    (`docs/L2/evaluation/surface.md` §1, `docs/L2/engine/surface.md` §4).
    """
    if "matrix" not in _SHARED:
        pool = shared_pool()
        variant = variant_policy()
        before = random.getstate()
        record = matrix(pool, [variant], "live")
        after = random.getstate()
        _SHARED["matrix"] = record
        _SHARED["matrix_stream"] = {"before": before, "after": after,
                                    "moved": before != after}
    return _SHARED["matrix"]


def matrix_stream():
    """What the shared matrix did to the global stream, observed at build time."""
    shared_matrix()
    return _SHARED["matrix_stream"]


def shared_rating():
    if "rating" not in _SHARED:
        _SHARED["rating"] = rating(shared_matrix())
    return _SHARED["rating"]


def shared_pool_record():
    return pool_members(shared_pool())


def header_record(matrix_record=None, pool_record=None):
    """`protocol.md` §1's nine header items, as one record (`declarations.md` §2.1)."""
    matrix_record = matrix_record or shared_matrix()
    pool_record = pool_record or shared_pool_record()
    return {
        "game": game_config(),
        "action space": action_space(),
        "parameter counts": parameter_counts(matrix_record),
        "sample budget": SAMPLE_BUDGET,
        "cell size": matrix_record["hands_per_cell"],
        "seeds": protocol()["seeds"],
        "table seed": matrix_record["table_seed"],
        "device": "cpu",
        "checkpoints": [str(member.get("path")) for member in pool_record["members"]
                        if member.get("path")],
    }


def parameter_counts(matrix_record):
    """Every member's measured count, read off the cells' own `params` key.

    `records.md` §9 makes `params` a cell's required key, position-aligned with
    its `members`, so a table records every member's count without a reader
    depending on one of the module's own keys (`records.md` §1, D-13).
    """
    out = {}
    for cell in matrix_record["cells"]:
        for member, count in zip(cell_members(cell), cell["params"]):
            out.setdefault(str(member), int(count))
    return out


def baseline_rows(matrix_record):
    """The three baseline rows inside the table, at the table's one hand count."""
    names = [str(name) for name in protocol()["baselines"]]
    return {
        "rows": [
            {"id": name, "hands": matrix_record["hands_per_cell"]}
            for name in names
        ]
    }


def run_record(matrix_record=None, rating_record=None, pool_record=None):
    """A complete hand-built run record with the seven families attached.

    `records.md` §12's run keys are present, and so are `protocol.md` §1's seven
    evidence families (`records.md` §13): a family is data here, never a value
    this module invents, because `training` produces the run
    (`docs/L2/evaluation/league.md` §7).
    """
    matrix_record = matrix_record or shared_matrix()
    rating_record = rating_record or rating(matrix_record)
    pool_record = pool_record or shared_pool_record()
    record = {
        "rung": RUNG,
        "seeds": protocol()["seeds"],
        "budget": SAMPLE_BUDGET,
        "device": "cpu",
        "params": parameter_counts(matrix_record),
        "table": matrix_record["table"],
        "timings": {"hands": SAMPLES, "seconds_per_hand": 0.0125},
        "checkpoints": [version(VERSION_A, START_LABEL)["path"]],
    }
    record["curves"] = {
        VARIANT_LABEL: {
            "samples": [0, SAMPLES // 2, SAMPLES],
            "signal": [0.42, 0.19, 0.11],
            "spread": 0.07,
        }
    }
    record["pool"] = pool_record
    record["matrix"] = matrix_record
    record["rating"] = rating_record
    record["baselines"] = baseline_rows(matrix_record)
    record["axis row"] = "n/a, single variant"
    record["header"] = header_record(matrix_record)
    return record


# --------------------------------------------------------------------------
# Hand-built records for `rating` and `report` (the cheap cases).
# --------------------------------------------------------------------------
def hand_cell(member_a, member_b, hands, wins, ties):
    """One `records.md` §9 cell, both directions the same hands seen from a seat."""
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


def hand_matrix(members, counts, hands_per_cell, table_seed):
    """A sound `records.md` §10 table: one cell per unordered pair, in order."""
    ids = [str(member) for member in members]
    pairs = list(itertools.combinations(range(len(ids)), 2))
    if len(counts) != len(pairs):
        raise AssertionError(
            "a hand-built table of %d members needs %d count triples, got %d"
            % (len(ids), len(pairs), len(counts))
        )
    cells = []
    for (i, j), (wins, ties, _losses) in zip(pairs, counts):
        cells.append(hand_cell(ids[i], ids[j], hands_per_cell, wins, ties))
    return {
        "members": ids,
        "cells": cells,
        "hands_per_cell": int(hands_per_cell),
        "table_seed": int(table_seed),
        "table": "live",
    }


def hand_built_matrix():
    """This battery's own four-member table, at an invented cell size and seed."""
    return hand_matrix(
        HAND_BUILT_MEMBERS, HAND_BUILT_COUNTS, HANDS_SEVEN, HAND_BUILT_TABLE_SEED
    )


def hand_built_pool_record(members=None):
    """A §8 pool record whose members are the given ids, baselines first."""
    ids = list(members or HAND_BUILT_MEMBERS)
    declared = []
    names = [str(name) for name in protocol()["baselines"]]
    for index, member_id in enumerate(ids):
        if member_id in names:
            declared.append({"id": member_id, "baseline": True, "pinned": True,
                             "params": 0})
        else:
            declared.append(bare_version(member_id, START_LABEL))
    return {
        "id": pool_id(declared),
        "m": league()["m"],
        "frozen": True,
        "members": declared,
        "rules": tuple(
            dict.fromkeys(
                record["rule"] for record in declared if not record.get("baseline")
            )
        ),
    }


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


def canonical(record):
    """One record compared by value, whatever container a design chose."""
    return json.dumps(record, sort_keys=True, default=str)


def clone(record):
    return copy.deepcopy(record)


def names_of(pool_record):
    """The ordered member ids of a `records.md` §8 pool record."""
    return [str(member["id"]) for member in pool_record["members"]]


def members_of(pool_record):
    """The ordered members of a `records.md` §8 pool record — the digest's own input.

    `docs/L3/evaluation/families.md` §4 makes the id a function of one line per member, a
    version's rule included, so a case that recomputes the id hands over the records and
    not their names (ASM-27).
    """
    return [dict(member) for member in pool_record["members"]]


def pool_rules(pool_record):
    """The `rules` a pool record declares — a **required** key of `records.md` §8."""
    if "rules" not in pool_record:
        raise AssertionError(
            "a pool record carries `rules`, the distinct rules its version members declare "
            "(records.md §8, D-19): %r" % (sorted(str(key) for key in pool_record),)
        )
    return tuple(pool_record["rules"])


def pool_utilities(pool_record):
    """The `utilities` a pool record declares — a **required** key of `records.md` §8 (D-20)."""
    if "utilities" not in pool_record:
        raise AssertionError(
            "a pool record carries `utilities`, the distinct utilities its version members "
            "declare (records.md §8, utilities.md §7, D-20): %r"
            % (sorted(str(key) for key in pool_record),)
        )
    return tuple(pool_record["utilities"])


def member_utility(pool_record, member_id):
    """One version member's `utility` out of a pool record (`records.md` §7, D-20)."""
    member = member_record(pool_record, member_id)
    if "utility" not in member:
        raise AssertionError(
            "a version member carries `utility`, the objective it was trained on "
            "(records.md §7, utilities.md §6, D-20): %r" % (member,)
        )
    return str(member["utility"])


def member_record(pool_record, member_id):
    for member in pool_record["members"]:
        if str(member["id"]) == str(member_id):
            return member
    raise AssertionError(
        "the pool record %r holds no member %r" % (pool_record, member_id)
    )


def matrix_members(matrix_record):
    """The ordered membership of a `records.md` §10 matrix record."""
    return [str(member) for member in matrix_record["members"]]


def cell_members(cell):
    return [str(member) for member in cell["members"]]


def cell_by_pair(matrix_record, member_a, member_b):
    """The one cell of the unordered pair, read from the record itself."""
    wanted = {str(member_a), str(member_b)}
    found = [
        cell for cell in matrix_record["cells"]
        if {str(m) for m in cell["members"]} == wanted
    ]
    if len(found) != 1:
        raise AssertionError(
            "the table must carry exactly one cell for the pair (%r, %r); it "
            "carries %d (records.md §9, docs/L1/league.md §4)"
            % (member_a, member_b, len(found))
        )
    return found[0]


def pair_of(cell):
    return tuple(cell_members(cell))


def direction_for(cell, member_id):
    """One member's side of a cell (`records.md` §9, `scheduler.md` §8)."""
    members = cell_members(cell)
    directions = cell["directions"]
    if isinstance(directions, Mapping):
        for key, value in directions.items():
            if str(key) == str(member_id):
                return value
        raise AssertionError(
            "the cell's directions name no member %r: %r" % (member_id, directions)
        )
    if str(member_id) not in members:
        raise AssertionError(
            "the cell %r holds no member %r" % (members, member_id)
        )
    return directions[members.index(str(member_id))]


def counts_of(direction):
    """A direction's win/tie/loss counts (`records.md` §9)."""
    return (
        int(_lookup(direction, ("wins", "win"), "a direction's wins")),
        int(_lookup(direction, ("ties", "tie", "draws"), "a direction's ties")),
        int(_lookup(direction, ("losses", "loss", "loses"), "a direction's losses")),
    )


def mean_delta_of(direction):
    """A direction's mean chip delta per hand (`records.md` §9)."""
    value = _lookup(direction, ("mean_chip_delta", "mean", "chip", "delta"),
                    "a direction's mean chip delta")
    if not isinstance(value, numbers.Real) or isinstance(value, bool):
        raise AssertionError("a direction's mean chip delta must be one number: %r"
                             % (value,))
    return float(value)


def seat_split_of(direction):
    """A direction's two seat counts, seat 0 (the button) then seat 1."""
    declared = _lookup(direction, ("seat_split", "split", "seats"),
                       "a direction's seat split")
    if isinstance(declared, Mapping):
        out = {}
        for key, value in declared.items():
            token = "".join(ch for ch in str(key).lower() if ch.isalnum())
            if token.endswith("0") or token in ("button", "smallblind", "sb"):
                out[0] = int(value)
            elif token.endswith("1") or token in ("bigblind", "bb"):
                out[1] = int(value)
        if 0 in out and 1 in out:
            return out[0], out[1]
        raise AssertionError(
            "a seat split must name the hands each seat held, seat 0 and seat 1: %r"
            % (declared,)
        )
    counts = [int(value) for value in declared]
    if len(counts) != 2:
        raise AssertionError(
            "a seat split must be two counts: %r" % (declared,)
        )
    return counts[0], counts[1]


def rating_values(rating_record):
    """One entry per member, keyed by member id (`records.md` §11)."""
    declared = rating_record["values"]
    if isinstance(declared, Mapping):
        return {str(member): entry for member, entry in declared.items()}
    out = {}
    for entry in declared:
        member = _lookup(entry, ("member", "id", "name"), "a rating entry's member")
        out[str(member)] = entry
    return out


def rating_names(rating_record):
    return list(rating_values(rating_record))


def entry_value(entry):
    value = _lookup(entry, ("value", "rating", "theta", "strength", "score"),
                    "a rating entry's value")
    if not isinstance(value, numbers.Real) or isinstance(value, bool):
        raise AssertionError("a rating entry's value must be one number: %r"
                             % (value,))
    return float(value)


def entry_interval(entry):
    declared = _lookup(entry, ("interval", "bounds", "confidence", "ci"),
                       "a rating entry's interval")
    if isinstance(declared, Mapping):
        lower = _lookup(declared, ("lower", "low", "min", "bottom", "lo"),
                        "an interval's lower bound")
        upper = _lookup(declared, ("upper", "high", "max", "top", "hi"),
                        "an interval's upper bound")
        return float(lower), float(upper)
    bounds = [float(value) for value in declared]
    if len(bounds) != 2:
        raise AssertionError(
            "a rating interval must be two bounds: %r" % (declared,)
        )
    return bounds[0], bounds[1]


def entry_hands(entry):
    value = _lookup(entry, ("hands", "samples", "evidence"), "a rating entry's hands")
    return int(value)


def entry_bounded(entry):
    try:
        return bool(_lookup(entry, ("bounded",), "a rating entry's bounded flag"))
    except AssertionError:
        return None


def family_of(report_record, name):
    """One evidence family out of a report, by the name `protocol()` spells."""
    wanted = token(name)
    for key, value in report_record.items():
        if token(key) == wanted:
            return value
    raise AssertionError(
        "the report carries no evidence family %r; it carries %r"
        % (name, sorted(str(key) for key in report_record))
    )


def token(text):
    return "".join(ch for ch in str(text).lower() if ch.isalnum())


def family_names():
    return [str(name) for name in protocol()["families"]]


def family_refusal(name):
    return str(protocol()["families"][name]["refusal"])


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
            if any(part in str(key).lower() for part in ("action", "index", "move",
                                                         "choice")):
                if isinstance(value, int) and not isinstance(value, bool):
                    return int(value)
    raise AssertionError(
        "cannot read an action index out of agents.act's return: %r" % (result,)
    )


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


def seat_fact(readout_record):
    """`(seat index, is button)` out of a readout's `seat` fact."""
    value = readout_record["seat"]
    if isinstance(value, Mapping):
        index = _lookup(value, ("seat", "index", "number"),
                        "a readout's seat index")
        button = _lookup(value, ("button", "is_button", "button?"),
                         "a readout's button flag")
        return int(index), bool(button)
    if isinstance(value, (tuple, list)):
        numbers = [item for item in value
                   if isinstance(item, int) and not isinstance(item, bool)]
        if len(numbers) != 1:
            raise AssertionError("cannot read a seat index out of %r" % (value,))
        return int(numbers[0]), bool(any(item is True for item in value))
    if isinstance(value, int) and not isinstance(value, bool):
        return int(value), False
    raise AssertionError("cannot read a seat out of a readout: %r" % (readout_record,))


def episode_payoffs(episode):
    """The episode's per-seat net chips (`records.md` §5)."""
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


def decision_readout(decision):
    return _lookup(decision, ("readout", "facts"), "a decision record's readout")


def decision_seat(decision):
    return seat_fact(decision_readout(decision))


def matrix_cell_count(matrix_record):
    """The cells a table actually carries."""
    return len(list(matrix_record["cells"]))


def cell_count(members):
    """K(K−1)/2, the number of unordered pairs (`league()`'s callable)."""
    size = len(list(members))
    return size * (size - 1) // 2


def table_label(matrix_record):
    return str(matrix_record["table"])


def finite(value):
    return (
        isinstance(value, numbers.Real)
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def stream_after_deal(seed):
    """The global stream's state after `engine.new_hand(seed)` dealt one hand.

    `new_hand` is the project's single seeding point, so the state it leaves is
    a function of its seed alone (`docs/L2/engine/surface.md` §4, ASM-2); the
    caller's stream is restored, so reading it moves nothing.
    """
    before = random.getstate()
    try:
        new_hand(seed)
        return random.getstate()
    finally:
        random.setstate(before)


def last_cell_hand_seed(matrix_record, table_seed, hands_per_cell):
    """The seed of the last hand of the last cell of a table (`matrix.md` §2)."""
    members = matrix_members(matrix_record)
    i, j = len(members) - 2, len(members) - 1
    return hand_seed(cell_seed(table_seed, i, j), int(hands_per_cell) - 1)


def renamed_matrix(matrix_record, member_id, new_id):
    """A real table with one member renamed, membership and cells together.

    The record stays a table (same K, one cell per pair, the baselines present):
    what changes is that the pool family no longer names every member of it, so
    `report`'s membership rule is the one that must refuse
    (`docs/L3/evaluation/report.md` §3 item 3).
    """
    out = {key: copy.deepcopy(value) for key, value in matrix_record.items()}
    out["members"] = [new_id if str(member) == str(member_id) else member
                      for member in out["members"]]
    cells = []
    for cell in out["cells"]:
        rebuilt = {key: copy.deepcopy(value) for key, value in cell.items()}
        rebuilt["members"] = [new_id if str(member) == str(member_id) else member
                              for member in rebuilt["members"]]
        cells.append(rebuilt)
    out["cells"] = cells
    return out


# --------------------------------------------------------------------------
# The base case: a scratch directory and the battery's two readers.
# --------------------------------------------------------------------------
class JoinCase(unittest.TestCase):
    """The base every case extends: a scratch root and the join's two readers."""

    def setUp(self):
        self._scratch = None

    def scratch(self):
        if self._scratch is None:
            self._scratch = tempfile.mkdtemp(prefix="evaluation-join-case-")
            self.addCleanup(shutil.rmtree, self._scratch, True)
        return self._scratch

    def checkpoint_path(self, name=CHECKPOINT_A):
        return os.path.join(self.scratch(), name)

    def assert_refusal(self, entry, groups, call, note=""):
        """Require `call` to be refused, naming the entry point and every group.

        The exception class is tolerated: `docs/L3/evaluation/errors.md` §2 leaves
        the hierarchy to L3, while §3 fixes the message grammar and `tests/e2e/`'s
        readers accept any wording that names the family, the rule or the member.
        Each group is one spelling or a tuple of alternative spellings, one of
        which must appear in the message.
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
        stream a later case deals from (`docs/L2/evaluation/surface.md` §1, ASM-2).
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
            "%s plays nothing and must leave the global `random` stream exactly as "
            "it found it (docs/L2/evaluation/surface.md §1, ASM-2)" % (what,),
        )
        return result

    def assert_stream_at_last_deal(self, state_after, seed, what):
        """Require the stream to stand where one `engine.new_hand(seed)` left it.

        Play moves the global stream only through the project's single seeding
        point (`docs/L2/evaluation/surface.md` §1, `docs/L2/engine/surface.md` §4,
        ASM-2), so after a cell or a table the stream is where the last hand's
        deal left it — and nowhere else.
        """
        self.assertEqual(
            state_after,
            stream_after_deal(seed),
            "%s must move the global `random` stream only through "
            "`engine.new_hand`, so it must stand where the last hand's deal at seed "
            "%r left it (docs/L2/evaluation/surface.md §1, ASM-2)"
            % (what, seed),
        )

    def assert_descriptor_in(self, legal, descriptor, note=""):
        self.assertTrue(
            any(same_descriptor(descriptor, candidate) for candidate in legal),
            "%s: the chosen descriptor %r must be one of legal_actions %r"
            % (note, descriptor, list(legal)),
        )

    def assert_descriptor_made_by_features(self, legal, descriptor, note=""):
        """The descriptor must be the one `features.decode_action` makes.

        `docs/L2/features/surface.md` §9 and `docs/L2/engine/surface.md` §2 fix
        the three-index vocabulary's spelling, and `decode_action` maps an index
        back to the descriptor the engine applies.
        """
        index = descriptor_index(legal, descriptor)
        self.assertEqual(
            decode_action(index),
            descriptor,
            "%s: the descriptor a policy returns must be the one "
            "features.decode_action builds from its index "
            "(docs/L2/features/surface.md §9)" % (note,),
        )
        return index
