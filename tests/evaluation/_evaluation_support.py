"""Shared support for the `evaluation` unit battery.

Puts `<repo>/src` on `sys.path`, imports the `evaluation` package **lazily inside a
helper** (so an absent `src/evaluation/` is one clean red case per contract and never
a collection error), and holds this battery's invented instances, its tolerant
readers, its hand-built records and the base `unittest.TestCase` every case derives
from.

Everything asserted by the battery is stated in `docs/L3/evaluation/` (the design this
battery pins) and `docs/L2/evaluation/surface.md` (the callable contract), with the
record keys of `docs/L1/records.md` §7-§13 and the numbers of `docs/L1/protocol.md`
§1-§3, `docs/L1/league.md` §2-§6 and `docs/L1/e2e-surface.md` §2, §3.4. The modules
this module calls -- `agents`, `features`, `engine` -- are implemented, so the
battery builds real learners, real checkpoints and real readouts through their
declared entry points and never reads their source (`docs/L2/agents/surface.md`,
`docs/L2/features/surface.md`, `docs/L2/engine/surface.md`).

Three conventions keep this battery honest:

* **The surface is absent, not broken.** `evaluation()` raises `SurfaceAbsent`, an
  `AssertionError`, so every case of the battery fails as one self-explaining
  "surface absent" failure while `src/evaluation/` does not exist
  (`strata/examiner.md` §2-§3). Nothing below a support helper is imported at module
  import time; the invented fixtures are data and the real ones are built inside a
  case.
* **A freedom is read, a pinned spelling is asserted.** Where `docs/L3/evaluation/`
  leaves a shape free -- the container of `cells`, `members` and rating `values`, the
  nesting of `directions`, the bounds' key names and order -- a reader here reads it
  tolerantly (`matrix_member_ids`, `matrix_cells`, `cell_directions`,
  `rating_entries`, `rating_interval`). Where the design pins a name or a number --
  the eleven entry points, the seven family names (`axis row` included), the nine
  header items, the pool digest, the five seed derivations, `BOUND`, `TOLERANCE`,
  `RESAMPLES`, the two budgets -- a case asserts it exactly.
* **Cost discipline.** `matrix` plays `K(K-1)/2 x 120` hands, and the pinned `oracle`
  baseline asks `engine.equity` at every decision, so one real `live` matrix costs
  about a minute and a half on CPU. This battery therefore builds exactly three, once
  each, cached in `_REAL_MATRICES` and shared by every case that needs one: `k4`
  (the three baselines and one labelled `variant-1`), `k5` (two variants, the
  second an opaque callable) and `k6` (the three baselines, one real version member
  read from a checkpoint, and one labelled `variant-1` -- the one table that plays
  `matrix.md` §4's version row, `policy._member_policy(record)` at the seed its
  checkpoint records). Every other matrix in the battery is hand-built in
  `records.md` §10's shape, which is what `rating` and `report` are specified to
  accept (`rating.md` §1, `report.md` §2).

The invented instances below appear in no design document: the seed set, the hand
counts, the membership ids, the lineage start, the hand-built matrix's table seed and
the version ids are this battery's own (`battery.md` §4, D-15), and no case reuses a
design example or a `tests/e2e/` instance.
"""

import atexit
import hashlib
import importlib
import json
import numbers
import os
import random
import shutil
import sys
import tempfile
import unittest
import zipfile
from collections.abc import Mapping
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
SRC_ROOT = os.path.join(REPO_ROOT, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

# ---------------------------------------------------------------------------
# The declared surface (surface.md §1-§13, README.md §3, e2e-surface.md §3.4)
# ---------------------------------------------------------------------------

#: The eleven entry points, in the L1 order (`e2e-surface.md` §3.4, `README.md` §3).
ELEVEN_NAMES = (
    "protocol",
    "league",
    "build_pool",
    "pool_members",
    "offer",
    "opponent",
    "match",
    "matrix",
    "rating",
    "policy_from",
    "report",
)

#: The seven evidence families, in `protocol.md` §1's order (`declarations.md` §3).
FAMILIES = ("curves", "pool", "matrix", "rating", "baselines", "axis row", "header")

#: The nine header items, in `declarations.md` §2.1's order.
HEADER_ITEMS = (
    "game",
    "action space",
    "parameter counts",
    "sample budget",
    "cell size",
    "seeds",
    "table seed",
    "device",
    "checkpoints",
)

#: The three pinned baselines, in `agents.baselines()`'s order (`agents/surface.md` §11).
BASELINES = ("random", "always-call", "oracle")

#: The two table budgets, in `declarations.md` §4.1's order.
BUDGETS = ("live", "full")

#: The fixed seed set (`protocol.md` §2).
SEED_SET = (0, 1, 2)

#: The five seed derivations' tags, exactly as `scheduler.md` §3 spells them.
HAND_TAG = b"pypoker-evaluation/hand/v1"
CELL_TAG = b"pypoker-evaluation/cell/v1"
MEMBER_TAG = b"pypoker-evaluation/member/v1"
BOOTSTRAP_TAG = b"pypoker-evaluation/bootstrap/v1"

#: The rating's anchor sentence (`declarations.md` §2.2, `rating.md` §5).
ANCHOR = "the three baselines' mean fixed at 0"

#: R1's explicit axis row (`protocol.md` §1, `report.md` §1).
AXIS_ROW = "n/a, single variant"

# ---------------------------------------------------------------------------
# Invented instances -- none of these numbers or names is in a design document
# ---------------------------------------------------------------------------

LEARNER_SEED = 202641
OTHER_LEARNER_SEED = 202642
MATCH_SEED = 31337
OTHER_MATCH_SEED = 77
MATCH_HANDS = 12
ODD_HANDS = 13
ALT_HANDS = 9
OPPONENT_SEEDS = tuple(range(550101, 550108))
PROBE_HAND_SEEDS = (5501, 5502, 5503, 5504, 5505, 5506, 5507, 5508)

#: The bound a tight pool declaration may carry below the league's M.
POOL_M = 3

#: The five invented version ids and the start label their first member descends from.
VERSION_IDS = (
    "version-heron-5501",
    "version-otter-5502",
    "version-pika-5503",
    "version-lark-5504",
    "version-marmot-5505",
    "version-tern-5506",
    "version-quill-5507",
)
START_LABEL = "own-start-5500"

#: The hand-built matrices' own table seed and cell size (`records.md` §10; `rating`
#: re-judges no `table` label and reads the hand count off the record, `rating.md` §6).
TABLE_SEED_HAND = 771113
HANDS_PER_CELL = 120

#: The invented configuration label an unregistered rung carries (`ladder.md` §1).
RUNG_NAME = "R7-heron-ladder"


class SurfaceAbsent(AssertionError):
    """`src/evaluation/` or one of the eleven entry points is missing.

    Every case that cannot find the package fails with this message rather than a
    collection error, which is what keeps the battery red for the right reason before
    `src/evaluation/` exists (`strata/examiner.md` §2-§3).
    """


_EVALUATION = None


def evaluation():
    """Return the `evaluation` package, or raise `SurfaceAbsent`."""
    global _EVALUATION
    if _EVALUATION is not None:
        return _EVALUATION
    try:
        import evaluation as package
    except SurfaceAbsent:
        raise
    except Exception as exc:  # absent package, or absent on sys.path
        raise SurfaceAbsent(
            "src/evaluation/ is not importable, so the eleven entry points cannot be "
            "driven (%s: %s)" % (type(exc).__name__, exc)
        )
    missing = [name for name in ELEVEN_NAMES if not hasattr(package, name)]
    if missing:
        raise SurfaceAbsent(
            "the evaluation package is missing entry point(s): " + ", ".join(missing)
        )
    _EVALUATION = package
    return package


_FEATURES = None


def features():
    """The `features` package, read only through its declared surface (`features/surface.md`)."""
    global _FEATURES
    if _FEATURES is None:
        import features as package

        _FEATURES = package
    return _FEATURES


_ENGINE = None


def engine():
    """The `engine` package, read only through its declared surface (`engine/surface.md`)."""
    global _ENGINE
    if _ENGINE is None:
        import engine as package

        _ENGINE = package
    return _ENGINE


_AGENTS = None


def agents():
    """The `agents` package, read only through its declared surface (`agents/surface.md`)."""
    global _AGENTS
    if _AGENTS is None:
        import agents as package

        _AGENTS = package
    return _AGENTS


def flat_encoder():
    """The `flat-numeric` encoder the caller owns (`learner.md` §6)."""
    return features().build_encoder("flat-numeric")


def token_encoder():
    """The `card-tokens` encoder the caller owns (`learner.md` §6)."""
    return features().build_encoder("card-tokens")


def declared_internal(module_name, attribute):
    """One private name `README.md` §4 declares contract for `tests/evaluation/`.

    `README.md` §4 lists the module layout and names the private spellings this
    battery imports -- `seeds.py`'s five derivations, `rating.py`'s four constants,
    `tables.py`'s two -- so those are contract here and nothing else below an entry
    point is (`e2e-surface.md` §1). A missing one is a missing surface.
    """
    evaluation()
    try:
        module = importlib.import_module("evaluation." + module_name)
    except SurfaceAbsent:
        raise
    except Exception as exc:
        raise SurfaceAbsent(
            "src/evaluation/%s.py is not importable, so %s.%s (README.md §4) cannot be "
            "driven (%s: %s)" % (module_name, module_name, attribute, type(exc).__name__, exc)
        )
    if not hasattr(module, attribute):
        raise SurfaceAbsent(
            "evaluation.%s.%s is not declared, and README.md §4 fixes it as contract for "
            "this battery" % (module_name, attribute)
        )
    return getattr(module, attribute)


_ERRORS_MODULE = None


def errors_module():
    """The `evaluation.errors` module, imported lazily, or `SurfaceAbsent`.

    `errors.md` §2 fixes the module's path and `README.md` §4 declares the hierarchy
    contract for this battery; the import lives here so the battery reaches nothing
    under `src/evaluation/` except through this support module's lazy loaders.
    """
    global _ERRORS_MODULE
    if _ERRORS_MODULE is None:
        evaluation()
        try:
            import evaluation.errors as module
        except Exception as exc:
            raise SurfaceAbsent(
                "src/evaluation/errors.py is not importable, so the hierarchy of "
                "errors.md §2 cannot be asserted (%s: %s)" % (type(exc).__name__, exc)
            )
        _ERRORS_MODULE = module
    return _ERRORS_MODULE


_ERROR_ROOT = None


def refusal_class():
    """`evaluation.errors.EvaluationError`, the root `errors.md` §2 declares.

    `errors.md` §2 fixes both the module path (`src/evaluation/errors.py`) and the
    root's name, and `README.md` §4 declares the class hierarchy contract for this
    battery: a caller catches `EvaluationError` to know that *this* module refused it,
    so a refusal that arrives as a `TypeError`, a `KeyError` or an `engine` error
    escapes that catch (`errors.md` §1-§2). The thirty-three subclasses are asserted
    in `test_errors.py` alone and never elsewhere (`errors.md` §2's closing rule).
    """
    global _ERROR_ROOT
    if _ERROR_ROOT is None:
        module = errors_module()
        root = getattr(module, "EvaluationError", None)
        if not isinstance(root, type) or not issubclass(root, Exception):
            raise SurfaceAbsent(
                "evaluation.errors.EvaluationError is not an exception class, and "
                "errors.md §2 declares it the base of every refusal of this module"
            )
        _ERROR_ROOT = root
    return _ERROR_ROOT


# ---------------------------------------------------------------------------
# The five seed derivations, recomputed from scheduler.md §3
# ---------------------------------------------------------------------------
def expected_seed(tag, *parts):
    """`scheduler.md` §3's one digest: the tag and the parts joined by ``\\x1f``.

    A case recomputes the derivation here rather than trusting the implementation's
    own helper, so a `seed + i`, a `random.Random(seed)` or a `hash()` fails loudly
    (`scheduler.md` §3, `guardrails.md` G8).
    """
    payload = tag + b"\x1f" + b"\x1f".join(str(part).encode("utf-8") for part in parts)
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % (2 ** 31)


def hand_seed(seed, index):
    """`seeds._hand_seed(seed, index)` (`scheduler.md` §3)."""
    return expected_seed(HAND_TAG, seed, index)


def cell_seed(table_seed, i, j):
    """`seeds._cell_seed(table_seed, i, j)` (`scheduler.md` §3)."""
    return expected_seed(CELL_TAG, table_seed, i, j)


def member_seed(table_seed, position):
    """`seeds._member_seed(table_seed, position)` (`scheduler.md` §3)."""
    return expected_seed(MEMBER_TAG, table_seed, position)


def bootstrap_seed(table_seed):
    """`seeds._bootstrap_seed(table_seed)` (`scheduler.md` §3, `rating.md` §4)."""
    return expected_seed(BOOTSTRAP_TAG, table_seed)


def draw_index(seed, size):
    """`seeds._draw_index(seed, size) = seed % size` (`scheduler.md` §3, `pool.md` §7)."""
    return seed % size


def pool_digest(ids):
    """`pool.md` §4's id: the ordered ids joined by one ``\\n``, SHA-256, 16 hex, prefixed.

    Recomputed in the case so a digest over member records, a `repr` or a salted
    `hash()` is red (`guardrails.md` G2).
    """
    payload = "\n".join(ids).encode("utf-8")
    return "pool-" + hashlib.sha256(payload).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Tolerant readers: the shapes `docs/L3/evaluation/` leaves free
# ---------------------------------------------------------------------------
def token(text):
    """A name reduced to its letters and digits (`declarations.md` §2.1's presence rule)."""
    return "".join(ch for ch in str(text).lower() if ch.isalnum())


def member_id(value):
    """One member's id: a pool member's record or a bare id (`records.md` §8, §10)."""
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        for key, inner in value.items():
            if token(key) in ("id", "memberid", "member", "name") and isinstance(inner, str):
                return inner
    raise AssertionError(
        "a member names its id at its own record (`records.md` §7-§10): %r" % (value,)
    )


def pool_member_ids(record):
    """A pool record's member ids, the three baselines first (`records.md` §8)."""
    return tuple(member_id(entry) for entry in record["members"])


def matrix_member_ids(matrix):
    """A matrix record's membership ids, in order (`matrix.md` §1).

    `matrix.md` §8 frees the container -- "a sequence or a mapping a reader can walk"
    -- so the reader accepts either and never pins the type.
    """
    raw = matrix["members"]
    entries = list(raw.values()) if isinstance(raw, Mapping) else list(raw)
    return tuple(member_id(entry) for entry in entries)


def matrix_cells(matrix):
    """A matrix record's cells, in the order the record states them (`matrix.md` §2, §8)."""
    raw = matrix["cells"]
    return list(raw.values()) if isinstance(raw, Mapping) else list(raw)


def member_ids_of_cell(cell):
    """One cell's pair, in the cell's own order (`rating.md` §2, `records.md` §9)."""
    return tuple(member_id(entry) for entry in cell["members"])


def cell_directions(cell):
    """One cell's two directions, position-aligned with the cell's own pair.

    `scheduler.md` §8 frees the container and whether a direction is "one mapping per
    member or keyed by member", so a mapping keyed by the cell's member ids is read in
    the cell's order and a sequence is read as given.
    """
    value = cell["directions"]
    ids = member_ids_of_cell(cell)
    if isinstance(value, Mapping):
        keyed = [value[name] for name in ids if name in value]
        if len(keyed) == len(ids):
            return keyed
        entries = list(value.values())
        if len(entries) == len(ids):
            return entries
        raise AssertionError(
            "a cell reports one direction per member of its pair (`records.md` §9, "
            "`scheduler.md` §4): %r" % (value,)
        )
    entries = list(value)
    if len(entries) != len(ids):
        raise AssertionError(
            "a cell reports one direction per member of its pair (`records.md` §9): %r"
            % (value,)
        )
    return entries


def direction_values(direction, where="a cell's direction"):
    """A direction's five required facts (`records.md` §9, `scheduler.md` §4)."""
    if not isinstance(direction, Mapping):
        raise AssertionError("%s must be a mapping (`records.md` §9): %r" % (where, direction))
    missing = [
        key
        for key in ("wins", "ties", "losses", "mean_chip_delta", "seat_split")
        if key not in direction
    ]
    if missing:
        raise AssertionError(
            "%s is missing the required key(s) %r (`records.md` §9, `scheduler.md` §4): %r"
            % (where, tuple(missing), direction)
        )
    return direction


def count(value, what):
    """A plain integer count -- a NumPy integer is a count, a `bool` is not.

    `errors.md` §5 refuses no NumPy integer for a count, while a flag is never a count
    (`scheduler.md` §6, `errors.md` §5).
    """
    if isinstance(value, bool) or not isinstance(value, numbers.Integral):
        raise AssertionError("%s must be an integer, got %r (%s)" % (what, value, type(value).__name__))
    return int(value)


def finite_float(value, what):
    """A finite number read as a `float` (`records.md` §11, `scheduler.md` §4)."""
    import math

    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise AssertionError("%s must be a number, got %r (%s)" % (what, value, type(value).__name__))
    number = float(value)
    if not math.isfinite(number):
        raise AssertionError("%s must be finite, got %r" % (what, number))
    return number


def seat_split_counts(split, where="a direction's seat_split"):
    """A seat split's two hand counts, as ``(seat 0, seat 1)`` (`scheduler.md` §2).

    `scheduler.md` §2 fixes the rule -- two counts, keyed by the engine's seat order,
    summing to the cell's hands -- and names the spelling `seat 0`/`seat 1`. A case
    that asserts the spelling itself (EVL-3.3) checks the key tokens; this reader only
    needs the two counts, and reads a button-named pair as the same two seats.
    """
    if not isinstance(split, Mapping):
        raise AssertionError("%s must be a mapping (`scheduler.md` §2): %r" % (where, split))
    seat0 = seat1 = None
    for key, value in split.items():
        name = token(key)
        if "seat0" in name or name in ("button", "btn", "smallblind", "sb"):
            seat0 = count(value, "%s (seat 0)" % where)
        elif "seat1" in name or name in ("bigblind", "bb"):
            seat1 = count(value, "%s (seat 1)" % where)
    if seat0 is None or seat1 is None:
        raise AssertionError(
            "%s carries two counts, one per engine seat (`scheduler.md` §2): %r"
            % (where, split)
        )
    return seat0, seat1


def direction_counts(direction, where="a cell's direction"):
    """``(wins, ties, losses, mean_chip_delta)`` of one direction."""
    values = direction_values(direction, where)
    return (
        count(values["wins"], "%s wins" % where),
        count(values["ties"], "%s ties" % where),
        count(values["losses"], "%s losses" % where),
        finite_float(values["mean_chip_delta"], "%s mean_chip_delta" % where),
    )


def params_of(cell, where="a cell"):
    """A cell's parameter counts: one integer per member, position-aligned (`scheduler.md` §4).

    `guardrails.md` G11 makes a dict red, so a mapping is a failure and not a shape to
    read tolerantly.
    """
    raw = cell["params"]
    if isinstance(raw, Mapping):
        raise AssertionError(
            "%s carries one integer per member, position-aligned with members, not a "
            "mapping keyed by member (`scheduler.md` §4, G11): %r" % (where, raw)
        )
    if isinstance(raw, (str, bytes)) or not isinstance(raw, (list, tuple)):
        raise AssertionError(
            "%s carries one integer per member (`scheduler.md` §4): %r" % (where, raw)
        )
    return [count(value, "%s params entry" % where) for value in raw]


def unlabelled_of(container):
    """The ids whose capacity is unmeasured (`scheduler.md` §4, `matrix.md` §5)."""
    raw = container.get("unlabelled") or ()
    return tuple(member_id(entry) for entry in raw)


def family_token_matches(key, name):
    """Whether a record key spells an evidence family (`report.md` §3's tolerance)."""
    return token(key) == token(name)


def family_present(record, name):
    """Whether a record carries a family under the design's letters-and-digits token."""
    if not isinstance(record, Mapping):
        return False
    return any(
        family_token_matches(key, name) and value is not None
        for key, value in record.items()
    )


def family_value(record, name):
    """The value a record carries for a family, under its token-equal key."""
    for key, value in record.items():
        if family_token_matches(key, name) and value is not None:
            return value
    return None


def rating_entries(rating):
    """A rating record's per-member entries, keyed by member id (`records.md` §11).

    `rating.md` §7 frees the container -- "a mapping keyed by member id (this design's
    choice) or a sequence of entries each carrying its member's id" -- so both are
    read here.
    """
    raw = rating["values"]
    out = {}
    if isinstance(raw, Mapping):
        for key, entry in raw.items():
            out[str(key)] = entry
        return out
    for entry in raw:
        out[member_id(entry)] = entry
    return out


def rating_entry(entries, member, where="the rating"):
    """One member's entry, or a failure naming the member (`records.md` §11)."""
    if member not in entries:
        raise AssertionError(
            "%s carries one entry per matrix member, and has none for %r "
            "(records.md §11): %r" % (where, member, sorted(entries))
        )
    return entries[member]


def interval_bounds(entry, where="a rating entry"):
    """A rating entry's 95% interval as ``(smaller, larger)`` (`records.md` §11).

    `records.md` §11 fixes neither the bounds' key names nor the order they are stated
    in, so the extent is read and never "bound one then bound two" (`rating.md` §5).
    """
    raw = entry["interval"]
    if isinstance(raw, Mapping):
        values = [finite_float(value, "%s interval bound" % where) for value in raw.values()]
    elif isinstance(raw, (list, tuple)):
        values = [finite_float(value, "%s interval bound" % where) for value in raw]
    else:
        raise AssertionError(
            "%s carries a 95%% interval, two bounds (%s): %r" % (where, "records.md §11", raw)
        )
    if len(values) != 2:
        raise AssertionError(
            "%s carries two interval bounds (`records.md` §11): %r" % (where, raw)
        )
    return min(values), max(values)


def entry_value(entry, where="a rating entry"):
    """A rating entry's fitted value (`records.md` §11)."""
    return finite_float(entry["value"], "%s value" % where)


def entry_hands(entry, where="a rating entry"):
    """The hands behind one entry (`records.md` §11, `rating.md` §5)."""
    return count(entry["hands"], "%s hands" % where)


def entry_bounded(entry, where="a rating entry"):
    """Whether the fit bounded this member (`records.md` §11, `rating.md` §5)."""
    value = entry["bounded"]
    if not isinstance(value, (bool, numbers.Integral)) or isinstance(value, float):
        raise AssertionError("%s bounded flag must be a boolean: %r" % (where, value))
    return bool(value)


def bool_flag(value, what):
    """A boolean flag read from a record (`records.md` §11, `report.md` §2)."""
    if isinstance(value, bool):
        return value
    if isinstance(value, numbers.Integral) and not isinstance(value, bool) and int(value) in (0, 1):
        return bool(value)
    raise AssertionError("%s must be a boolean, got %r (%s)" % (what, value, type(value).__name__))


# ---------------------------------------------------------------------------
# Invented members, declarations and pools (records.md §7-§8)
# ---------------------------------------------------------------------------
def version_record(
    member_id_value,
    lineage,
    path=None,
    seed=LEARNER_SEED,
    step=0,
    samples=0,
    rung=RUNG_NAME,
    variant="heron",
):
    """One `records.md` §7 version record, with the `path` only when the battery has one.

    `records.md` §7 marks `id` and `path` required, while `docs/L2/evaluation/surface.md`
    §5 admits a declared member without a `path` and lets `matrix`/`opponent` refuse it
    when it must be a policy. A record built here without a path is that admitted
    version and nothing else.
    """
    record = {
        "id": member_id_value,
        "rung": rung,
        "variant": variant,
        "seed": seed,
        "step": step,
        "samples": samples,
        "lineage": lineage,
    }
    if path is not None:
        record["path"] = path
    return record


def version_chain(ids, start=START_LABEL, paths=None):
    """A single lineage chain, oldest first, declared in lineage order.

    The first member descends from `start`, the i-th from the (i-1)-th, which is how a
    rung's snapshots are declared (`pool.md` §3, `records.md` §7).
    """
    records = []
    for index, member in enumerate(ids):
        lineage = start if index == 0 else ids[index - 1]
        path = None if paths is None else paths[index]
        records.append(
            version_record(
                member,
                lineage,
                path=path,
                seed=LEARNER_SEED + index,
                step=100 * (index + 1),
                samples=1200 * (index + 1),
            )
        )
    return records


def declaration(members=(), m=POOL_M, frozen=True):
    """One `records.md` §8 declaration: the three required keys and nothing else."""
    return {"members": list(members), "m": m, "frozen": frozen}


def baseline_member(name):
    """One pinned baseline member (`pool.md` §2 step 5, `matrix.md` §5)."""
    return {"id": name, "baseline": True, "pinned": True, "params": 0}


def baseline_members():
    """The three baselines in `agents.baselines()`'s order (`pool.md` §2)."""
    return [baseline_member(name) for name in BASELINES]


def pool_record(members=(), m=5, frozen=True, identity=None):
    """A hand-built `records.md` §8 pool record: baselines first, then the versions.

    `report` reads its `pool` family as this shape (`report.md` §2, `surface.md` §13),
    and a hand-built one keeps the report cases free of `build_pool`'s cost and of its
    own defects (`errors.md` §1: a report is assembled from records alone).
    """
    ordered = baseline_members() + [dict(entry) for entry in members]
    ids = [member_id(entry) for entry in ordered]
    return {
        "id": identity or pool_digest(ids),
        "m": m,
        "frozen": frozen,
        "members": tuple(ordered),
    }


# ---------------------------------------------------------------------------
# Hand-built cells, matrices and ratings (records.md §9-§11)
# ---------------------------------------------------------------------------
def direction(wins, ties, losses, hands=HANDS_PER_CELL, seat0=None, mean=0.0):
    """One direction record with the five facts `records.md` §9 requires."""
    if seat0 is None:
        seat0 = (hands + 1) // 2
    return {
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "mean_chip_delta": mean,
        "seat_split": {"seat 0": seat0, "seat 1": hands - seat0},
    }


def cell_record(left, right, left_wins, ties, hands=HANDS_PER_CELL, seed=TABLE_SEED_HAND, mean=0.0):
    """One cell record of the pair (left, right), both directions mirroring (records.md §9)."""
    left_losses = hands - left_wins - ties
    return {
        "members": (left, right),
        "hands": hands,
        "directions": (
            direction(left_wins, ties, left_losses, hands, (hands + 1) // 2, mean),
            direction(left_losses, ties, left_wins, hands, hands // 2, -mean),
        ),
        "params": (0, 0),
        "seed": seed,
    }


def hand_matrix(
    results,
    members=None,
    hands=HANDS_PER_CELL,
    table_seed=TABLE_SEED_HAND,
    table="live",
):
    """A complete hand-built matrix in `records.md` §10's shape (`rating.md` §1).

    `results(left, right)` returns that pair's `(left_wins, ties)`; the cells are
    enumerated lexicographically by membership position, as `matrix.md` §2 fixes, so
    `rating` sees one cell per unordered pair and a full table.
    """
    membership = list(members if members is not None else tuple(BASELINES) + ("variant-1",))
    cells = []
    for i in range(len(membership)):
        for j in range(i + 1, len(membership)):
            left, right = membership[i], membership[j]
            wins, ties = results(left, right)
            cells.append(cell_record(left, right, wins, ties, hands=hands, seed=table_seed))
    return {
        "members": tuple(membership),
        "cells": tuple(cells),
        "hands_per_cell": hands,
        "table_seed": table_seed,
        "table": table,
    }


def all_ties(left, right):
    """Every hand of every cell is a tie: the fit's closed form is 0 for every member."""
    return 0, HANDS_PER_CELL


def balanced(left, right):
    """The same record for every pair, so every member's win mass is the same."""
    return HANDS_PER_CELL // 2, 20


def champion_won_everything(left, right):
    """`variant-1` won every hand of its three cells; the baselines tie one another."""
    if "variant-1" in (left, right):
        return (HANDS_PER_CELL, 0) if left == "variant-1" else (0, 0)
    return 0, HANDS_PER_CELL


def champion_lost_everything(left, right):
    """`variant-1` lost every hand of its three cells; the baselines tie one another."""
    if "variant-1" in (left, right):
        return (0, 0) if left == "variant-1" else (HANDS_PER_CELL, 0)
    return 0, HANDS_PER_CELL


def lopsided(left, right):
    """`variant-1` wins more than it loses in every cell (`rating.md` §2's ordering)."""
    if "variant-1" in (left, right):
        return (80, 10) if left == "variant-1" else (30, 10)
    return 50, 20


def rating_entry_record(value=0.0, half_width=0.5, hands=None, bounded=False):
    """One `records.md` §11 entry: a value, its interval and the hands behind it."""
    if hands is None:
        hands = HANDS_PER_CELL * 3
    return {
        "value": float(value),
        "interval": (float(value) - float(half_width), float(value) + float(half_width)),
        "hands": int(hands),
        "bounded": bool(bounded),
    }


def rating_record(matrix, entries=None, converged=True, bound_applied=False):
    """A hand-built `records.md` §11 rating over one matrix record (`report.md` §2)."""
    members = matrix_member_ids(matrix)
    hands = count(matrix["hands_per_cell"], "a hand-built matrix's hands_per_cell") * (len(members) - 1)
    if entries is None:
        entries = {member: rating_entry_record(hands=hands) for member in members}
    return {
        "values": {member: entries[member] for member in members},
        "method": "Bradley-Terry",
        "anchor": ANCHOR,
        "bound_applied": bool(bound_applied),
        "bootstrap_seed": bootstrap_seed(matrix["table_seed"]),
        "converged": bool(converged),
        "hands_per_cell": matrix["hands_per_cell"],
        "members": tuple(members),
        "table_seed": matrix["table_seed"],
        "table": matrix["table"],
    }


# ---------------------------------------------------------------------------
# The run record a report is handed (records.md §12-§13, protocol.md §1)
# ---------------------------------------------------------------------------
def curves_family(variant="variant-1"):
    """The `curves` family: per variant, per seed, an axis, a signal and a spread.

    The shape is the run record's own (`records.md` §12); `report` copies it by value
    and never reads inside it (`report.md` §2, §4).
    """
    rows = []
    for index, seed in enumerate(SEED_SET):
        rows.append(
            {
                "variant": variant,
                "seed": seed,
                "samples": (0, 400, 800, 1200),
                "signal": (1.0 - 0.1 * index, 0.7, 0.55, 0.5 + 0.02 * index),
                "spread": 0.01 * (index + 1),
            }
        )
    return rows


def baselines_family(matrix):
    """The `baselines` family: the three baseline rows at the table's one hand count."""
    hands = count(matrix["hands_per_cell"], "the matrix's hands_per_cell")
    return {
        "rows": tuple(
            {"id": name, "baseline": True, "params": 0, "hands": hands} for name in BASELINES
        )
    }


def header_record(device="cpu", table_seed=TABLE_SEED_HAND, cell=HANDS_PER_CELL, seeds=SEED_SET):
    """The `header` family: the nine items `declarations.md` §2.1 names, as keys."""
    return {
        "game": {
            "seats": 2,
            "blinds": (1, 2),
            "stacks": 20,
            "small bet": 2,
            "big bet": 4,
            "raise cap": 4,
        },
        "action space": {"0": "fold", "1": "check-call", "2": "raise"},
        "parameter counts": {name: 0 for name in BASELINES},
        "sample budget": 1200,
        "cell size": cell,
        "seeds": tuple(seeds),
        "table seed": table_seed,
        "device": device,
        "checkpoints": (),
    }


def run_record(matrix, rating, pool=None, rung=RUNG_NAME, families=None, drop=(), extra=None):
    """One assembled run record in `records.md` §12-§13's shape, with all seven families.

    `training` does not exist, so the record is data here: `report` is promised a record
    with the families attached and reads nothing else (`surface.md` §13, `records.md`
    §13). `families` overrides a family, `drop` removes one and `extra` adds a key, which
    is how the absence and tolerance cases are built.
    """
    record = {
        "rung": rung,
        "curves": curves_family(),
        "pool": pool_record() if pool is None else pool,
        "matrix": matrix,
        "rating": rating,
        "baselines": baselines_family(matrix),
        "axis row": AXIS_ROW,
        "header": header_record(table_seed=matrix["table_seed"], cell=matrix["hands_per_cell"]),
        "checkpoints": (),
        "seeds": tuple(SEED_SET),
        "budget": "live",
        "device": "cpu",
        "params": {"variant-1": 0},
        "table": matrix["table"],
        "timings": {"hands": len(matrix_cells(matrix)) * matrix["hands_per_cell"], "device": "cpu"},
    }
    if families:
        record.update(families)
    for name in drop:
        record.pop(name, None)
    if extra:
        record.update(extra)
    return record


def report_inputs(matrix=None, rating=None, pool=None):
    """``(rung_name, record, matrix, rating)`` for a complete, consistent report."""
    matrix = matrix if matrix is not None else hand_matrix(balanced)
    rating = rating if rating is not None else rating_record(matrix)
    record = run_record(matrix, rating, pool=pool)
    return RUNG_NAME, record, matrix, rating


# ---------------------------------------------------------------------------
# Invented policies: the opaque callables `surface.md` §2 names policy-1, policy-2
# ---------------------------------------------------------------------------
def first_legal(readout, legal_actions):
    """A policy returning the first legal descriptor -- fold where folding is legal."""
    return legal_actions[0]


def last_legal(readout, legal_actions):
    """A policy returning the last legal descriptor."""
    return legal_actions[-1]


def prefers(index):
    """A policy preferring one vocabulary index, built through `features.decode_action`."""

    def policy(readout, legal_actions):
        wanted = features().decode_action(index)
        for descriptor in legal_actions:
            if descriptor == wanted:
                return descriptor
        return legal_actions[0]

    return policy


def illegal_policy(readout, legal_actions):
    """A policy returning a descriptor outside `legal_actions` -- a contract violation.

    `engine` refuses it and `evaluation` neither catches nor repairs it
    (`surface.md` §9, `engine/surface.md` §10, D-2).
    """
    return "not-an-action-descriptor"


# ---------------------------------------------------------------------------
# Real learners, checkpoints and readouts, built through the declared entry points
# ---------------------------------------------------------------------------
_SCRATCH = []


def scratch_root():
    """A temporary directory outside the repository, removed at interpreter exit."""
    if not _SCRATCH:
        folder = tempfile.mkdtemp(prefix="evaluation-unit-")
        atexit.register(shutil.rmtree, folder, True)
        _SCRATCH.append(folder)
    return _SCRATCH[0]


_CHECKPOINTS = {}


def checkpoint(name="member", seed=LEARNER_SEED, encoding="flat-numeric", kind="naive-stack", width=4, depth=1, backend="numpy"):
    """A real checkpoint saved by `agents.save`, cached per class of spec.

    The learner is built through `agents.build_learner` and saved through
    `agents.save`; the checkpoint's own container records the seed and the encoding
    name that `policy_from` must read (`scheduler.md` §5.1, `surface.md` §12).
    """
    key = (name, seed, encoding, kind, width, depth, backend)
    if key not in _CHECKPOINTS:
        encoder = features().build_encoder(encoding)
        spec = {
            "backend": backend,
            "architecture": {"kind": kind, "width": width, "depth": depth},
            "seed": seed,
            "encoder": encoder,
        }
        learner = agents().build_learner(spec)
        path = os.path.join(scratch_root(), name + "-%d.ckpt" % seed)
        agents().save(learner, path)
        _CHECKPOINTS[key] = {
            "name": name,
            "path": path,
            "learner": learner,
            "encoder": encoder,
            "encoding": encoding,
            "kind": kind,
            "seed": seed,
            "params": agents().param_count(learner),
        }
    return _CHECKPOINTS[key]


def member_policy_checkpoint():
    """The checkpoint a labelled (`_MemberPolicy`) variant is built from."""
    return checkpoint(name="member")


def other_checkpoint():
    """A second checkpoint at a different learner seed, for the "two players" cases."""
    return checkpoint(name="other", seed=OTHER_LEARNER_SEED)


def chosen_action(learner, encoder, readout):
    """The descriptor `agents.act` chooses on one readout (`agents/surface.md` §6)."""
    mask = tuple(features().legal_indices(readout["legal"]))
    observation = features().encode(encoder, readout)
    record = agents().act(learner, observation, mask)
    return features().decode_action(record["action"])


def write_zip(path, members):
    """Write one stored zip of ``{name: bytes}`` -- the checkpoint container's shape.

    `scheduler.md` §5.1 established the container empirically: a plain zip whose
    `metadata.json` records the seed and the encoding name. A case that must provoke a
    recorded-facts refusal writes its own zip here, because no entry point writes a
    checkpoint that lies about its facts.
    """
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)


def checkpoint_without_seed(name="no-seed"):
    """A readable checkpoint zip whose `metadata.json` records no seed at all."""
    path = os.path.join(scratch_root(), name + ".ckpt")
    if not os.path.exists(path):
        write_zip(
            path,
            {
                "metadata.json": json.dumps(
                    {"format": "pypoker-agents-checkpoint", "representation": {"encoding": "flat-numeric"}}
                ).encode("utf-8"),
                "parameters.npy": b"\x93NUMPY-not-a-real-array",
            },
        )
    return path


def checkpoint_with_unknown_encoding(name="bogus-encoding"):
    """A checkpoint zip recording a seed and an encoding name `features.build_encoder` refuses."""
    path = os.path.join(scratch_root(), name + ".ckpt")
    if not os.path.exists(path):
        write_zip(
            path,
            {
                "metadata.json": json.dumps(
                    {"seed": LEARNER_SEED, "representation": {"encoding": "bogus-encoding"}}
                ).encode("utf-8"),
                "parameters.npy": b"\x93NUMPY-not-a-real-array",
            },
        )
    return path


def checkpoint_without_facts(name="no-facts"):
    """A readable zip carrying no JSON member at all, so no fact is recorded."""
    path = os.path.join(scratch_root(), name + ".ckpt")
    if not os.path.exists(path):
        write_zip(path, {"parameters.npy": b"\x93NUMPY-not-a-real-array"})
    return path


def file_that_is_not_a_checkpoint(name="plain-text"):
    """A readable file that is not a zip, so it is no checkpoint (`scheduler.md` §6)."""
    path = os.path.join(scratch_root(), name + ".ckpt")
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("this path is a file and not a checkpoint\n")
    return path


_PROBES = {}


def probe_readouts(count=4):
    """`count` real readouts from invented hands, with their legal descriptors and masks.

    One readout is one decision the policies of this battery answer; the hands are dealt
    once per process and cached, because `engine.new_hand` moves the global stream and a
    case that compares the stream's state must do so after this call
    (`engine/surface.md` §4, ASM-2).
    """
    if "rows" not in _PROBES:
        eng = engine()
        feats = features()
        rows = []
        for seed in PROBE_HAND_SEEDS:
            hand = eng.new_hand(seed)
            readout = eng.readout(hand)
            rows.append(
                {
                    "seed": seed,
                    "readout": readout,
                    "legal": tuple(readout["legal"]),
                    "mask": tuple(feats.legal_indices(readout["legal"])),
                }
            )
        _PROBES["rows"] = rows
    return [dict(row) for row in _PROBES["rows"][:count]]


def policy_answers(policy, count=4):
    """One policy's answers on the battery's probe decisions."""
    answers = []
    for row in probe_readouts(count):
        answers.append(policy(row["readout"], row["legal"]))
    return answers


# ---------------------------------------------------------------------------
# The three shared real matrices (cost discipline: built once, shared by every case)
# ---------------------------------------------------------------------------
_REAL_MATRICES = {}
_REAL_RATINGS = {}
_REAL_POOLS = {}


def version_pool_member():
    """The one real `records.md` §7 version member the shared `k6` pool declares.

    Its `path` is the battery's own checkpoint (`checkpoint(name="member")`), so the
    member is the learner `policy_from` restores; its `id` and `lineage` are the
    battery's invented values (`VERSION_IDS[0]`, `START_LABEL`). `matrix.md` §4's
    version row is played from this record, and §5's `member_records` carries it back
    verbatim -- the `path` included.
    """
    return version_record(
        VERSION_IDS[0], START_LABEL, path=member_policy_checkpoint()["path"]
    )


def shared_pool(key="k4"):
    """The frozen pool one shared matrix is played over, cached per key (`matrix.md` §1).

    `k4` and `k5` are played over the frozen **baselines-only** pool; `k6` is played
    over a frozen pool whose window holds one real version member
    (`version_pool_member`), so its membership is the three baselines, that version,
    then the variant slot -- K = 5, and the version is a *pool member* and not a
    variant (`matrix.md` §1, §4). One pool per key, so no case rebuilds one to read it.
    """
    if key not in _REAL_POOLS:
        package = evaluation()
        if key == "k6":
            _REAL_POOLS[key] = package.build_pool(
                declaration(members=[version_pool_member()], m=POOL_M, frozen=True)
            )
        else:
            _REAL_POOLS[key] = package.build_pool(
                declaration(members=(), m=5, frozen=True)
            )
    return _REAL_POOLS[key]


def _variants_for(key):
    """The variant list of one shared matrix: a labelled member policy, and maybe a bare one."""
    evaluation()
    labelled = evaluation().policy_from(member_policy_checkpoint()["path"])
    if key == "k4":
        return [labelled]
    if key == "k5":
        return [labelled, first_legal]
    if key == "k6":
        return [labelled]
    raise AssertionError(
        "the battery shares three matrices, k4, k5 and k6, and no other: %r" % (key,)
    )


def shared_matrix(key="k4"):
    """One real `live` matrix over one frozen shared pool, cached per key.

    The three shared matrices are the smallest legal memberships this surface can build
    (`tables.md` §2): `k4` is the three pinned baselines and one variant (`matrix.md`
    §1's R1 shape), `k5` adds a second, opaque variant so the slot naming and the
    unlabelled zero are exercised, and `k6` is played over a pool whose window holds
    one real version member (`shared_pool`), so `matrix.md` §4's version row -- a
    version played by `policy._member_policy(record)` at the seed its checkpoint
    records -- is driven through `matrix` itself. A `live` cell is 120 hands and every
    cell pairing the pinned `oracle` asks `engine.equity` at each decision
    (`agents/learner.md` §5), so each matrix is built exactly once
    (`guardrails.md` G13, ASM-15); a case reads it again and never rebuilds it.
    """
    if key not in _REAL_MATRICES:
        _REAL_MATRICES[key] = evaluation().matrix(
            shared_pool(key), _variants_for(key), "live"
        )
    return _REAL_MATRICES[key]


def shared_rating(key="k4"):
    """The rating fitted once to one shared matrix, cached beside it (`rating.md` §4)."""
    if key not in _REAL_RATINGS:
        _REAL_RATINGS[key] = evaluation().rating(shared_matrix(key))
    return _REAL_RATINGS[key]


# ---------------------------------------------------------------------------
# Assertions shared by the battery
# ---------------------------------------------------------------------------
def no_file_reads(what="this entry point"):
    """A context manager that fails if anything opens or unzips a file inside it.

    `report` "plays no hand, moves no stream and reads no file" (`surface.md` §13,
    `report.md` §4), `rating` "plays no hand, reads no file" (`rating.md` §1) and no
    entry point reads the shipped artefact (`tables.md` §4, `guardrails.md` G19), so a
    call made inside this block must not touch the filesystem.
    """
    return _PatchedReads(what)


class _PatchedReads:
    """`no_file_reads`' implementation: patch `open`, `zipfile.ZipFile` and `io.open`."""

    def __init__(self, what):
        self._what = what
        self._patches = []

    def __enter__(self):
        def refused(description):
            def deny(*args, **kwargs):
                raise AssertionError(
                    "%s read a file (%s), and a report is assembled from records alone "
                    "(surface.md §13, report.md §4, tables.md §4): %r"
                    % (self._what, description, args[:1])
                )

            return deny

        self._patches = [
            mock.patch("builtins.open", refused("open")),
            mock.patch("zipfile.ZipFile", refused("zipfile.ZipFile")),
            mock.patch("io.open", refused("io.open")),
        ]
        for patch in self._patches:
            patch.start()
        return self

    def __exit__(self, exc_type, exc, traceback):
        for patch in reversed(self._patches):
            patch.stop()
        return False


class EvaluationCase(unittest.TestCase):
    """Base case: the package, the invented fixtures, the shared tables and the refusals."""

    @classmethod
    def setUpClass(cls):
        """A per-class fixture cache, filled lazily inside a case.

        Nothing is built here: an absent `src/evaluation/` must still be one clean
        `SurfaceAbsent` failure per contract and never a setup error (`examiner.md` §2).
        """
        super().setUpClass()
        cls._fixtures = {}

    def evaluation(self):
        return evaluation()

    def features(self):
        return features()

    def engine(self):
        return engine()

    def agents(self):
        return agents()

    def tempdir(self):
        """A temporary directory outside the repository tree, removed after the case."""
        folder = tempfile.mkdtemp(prefix="evaluation-case-")
        self.addCleanup(shutil.rmtree, folder, True)
        return folder

    def frozen_pool(self, members=(), m=POOL_M):
        return self.evaluation().build_pool(declaration(members=members, m=m, frozen=True))

    def open_pool(self, members=(), m=POOL_M):
        return self.evaluation().build_pool(declaration(members=members, m=m, frozen=False))

    def pool_members(self, pool):
        return self.evaluation().pool_members(pool)

    def members_of(self, pool):
        return pool_member_ids(self.pool_members(pool))

    def shared_pool(self, key="k4"):
        return shared_pool(key)

    def shared_matrix(self, key="k4"):
        return shared_matrix(key)

    def shared_rating(self, key="k4"):
        return shared_rating(key)

    def checkpoint(self, name="member", **kwargs):
        return checkpoint(name=name, **kwargs)

    def stream_state(self):
        """The global `random` stream's state, which only the deal may move (`surface.md` §1)."""
        return random.getstate()

    def assert_stream_unchanged(self, before, what):
        self.assertEqual(
            before,
            random.getstate(),
            "%s plays no hand and leaves Python's global random stream where it found "
            "it (surface.md §1, ASM-2)" % what,
        )

    def assert_refused(self, fn, *args, entry, groups=(), label=""):
        """Assert a refusal: the call raises and the message names `entry` and each group.

        `groups` is a tuple of alternatives-tuples: every group must have one member the
        message contains. The exception class is tolerated here (`errors.md` §2's closing
        rule: a battery asserts the behaviour, not the class).
        """
        where = label or entry
        try:
            value = fn(*args)
        except SurfaceAbsent:
            raise
        except Exception as exc:
            message = str(exc)
            self.assertTrue(
                message.strip(),
                "%s was refused with an empty message (%s), and a refusal names the "
                "violated contract (errors.md §3)" % (where, type(exc).__name__),
            )
            lowered = message.lower()
            self.assertIn(
                entry.lower(),
                lowered,
                "%s was refused without naming %r: %r (errors.md §3)" % (where, entry, message),
            )
            for group in groups:
                if not any(candidate.lower() in lowered for candidate in group):
                    self.fail(
                        "%s was refused without naming any of %r: %r (errors.md §3)"
                        % (where, tuple(group), message)
                    )
        else:
            self.fail("%s accepted %r, which the contract refuses" % (where, value))

    def assert_evaluation_refusal(self, fn, *args, entry, groups=(), label=""):
        """Assert the refusal is this module's **own**, naming `entry` and each group.

        `errors.md` §1-§2: a refusal must be catchable as `EvaluationError`, so a
        `TypeError` from a mistyped record key, a `KeyError` or a NumPy error is an
        internal decision leaking as a crash and is red here.
        """
        where = label or entry
        root = refusal_class()
        try:
            value = fn(*args)
        except SurfaceAbsent:
            raise
        except Exception as exc:
            self.assertIsInstance(
                exc,
                root,
                "%s was refused with %s, which is not this module's own refusal (%s), so "
                "a caller catching EvaluationError would miss it: %r (errors.md §1-§2)"
                % (where, type(exc).__name__, root.__name__, exc),
            )
            self.assert_refused_like(exc, entry, groups, where)
        else:
            self.fail("%s accepted %r, which the contract refuses" % (where, value))

    def assert_refused_like(self, exc, entry, groups, where):
        """The message half of a refusal assertion (`errors.md` §3)."""
        message = str(exc)
        self.assertTrue(
            message.strip(),
            "%s was refused with an empty message (%s) (errors.md §3)"
            % (where, type(exc).__name__),
        )
        lowered = message.lower()
        self.assertIn(
            entry.lower(),
            lowered,
            "%s was refused without naming %r: %r (errors.md §3)" % (where, entry, message),
        )
        for group in groups:
            if not any(candidate.lower() in lowered for candidate in group):
                self.fail(
                    "%s was refused without naming any of %r: %r (errors.md §3)"
                    % (where, tuple(group), message)
                )

    def assert_plain_counts(self, values, hands, what):
        """A direction's wins, ties and losses account for every hand (`league.md` §2)."""
        wins, ties, losses, _mean = values
        self.assertEqual(
            wins + ties + losses,
            hands,
            "%s must account for every hand it played: wins + ties + losses = hands "
            "(records.md §9, league.md §2, FAM-7.1), got %d + %d + %d for %d hands"
            % (what, wins, ties, losses, hands),
        )
