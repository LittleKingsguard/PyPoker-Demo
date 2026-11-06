"""Surface plumbing and invented instances for the L1 end-to-end battery.

This module is test support, not a subsystem (brief §5, `module-map.md` §5).  It does
four things and nothing else:

* it puts the repository's ``src/`` on ``sys.path`` and imports the six declared
  packages on demand, so that a missing surface is one ``SurfaceAbsent`` failure in
  the case that needed it and never a collection error;
* it holds the *invented instances* the battery drives a ``general`` entry point with
  (seeds, hand counts, cell sizes, table seeds, versions with their lineages and
  checkpoints, membership declarations, a seventh rung configuration, learner specs,
  transition records).  None of these values appears in ``docs/L1/``; they are the
  battery's own, invented from ``docs/L1/e2e-surface.md`` alone (``battery.md`` §4,
  D-15);
* it holds tolerant readers for the shapes the design leaves free (a report's family
  key, a cell's rows, a seat split, a pool's id key, a record's nesting, an error's
  class).  A case asserts the contract through these readers instead of asserting a
  spelling this battery made up;
* it holds the league builders Rev 2 needs (D-16): a membership declaration with M
  and the frozen flag, a pool, its members, an advance by ``offer``, one ``match``
  cell, a ``matrix``, a ``rating``, and the run record completed with
  ``protocol.md`` §1's seven evidence families.

Nothing here reaches past an entry point of ``docs/L1/e2e-surface.md`` §3.  The one
expensive object the battery builds — the live matrix — is built once per process and
shared (:func:`shared_league`): the league is deterministic from its membership and its
table seed (ASM-2), so a second case would see the same table anyway, and a table of
K(K-1)/2 cells at 120 hands per cell is not something a dozen cases should each pay
for (``battery.md`` §2, ASM-14).
"""

from __future__ import annotations

import importlib
import numbers as _numbers
import os
import shutil
import sys
import tempfile
import unittest
from collections.abc import Mapping

MODULES = ("engine", "features", "agents", "evaluation", "training", "harness")

# --------------------------------------------------------------------------
# Invented instances.  These numbers are the test writer's own; no document in
# docs/L1/ carries them (battery.md §4, D-15).  The protocol's own numbers — the
# seed set 0, 1, 2, the 1,000-hand live budget, the 120- and 1,500-hand cells and
# M = 5 — appear below only where a case deliberately asserts the fixed protocol
# or the fixed league (e2e-surface.md §3.4, league.md §2, §6).
# --------------------------------------------------------------------------
SEED_A = 6174
SEED_B = 271828
SEED_C = 90210
SEED_D = 5150
SEED_E = 131
SEED_F = 4711
SEED_G = 8086
SEED_H = 314159
SEED_I = 424242
SEED_J = 99991
HANDS = 37             # a hand count, invented
HANDS_TINY = 11
CELL_HANDS = 23        # hands per cell, invented (the league's cells are 120 and 1,500)
CELL_HANDS_SMALL = 14
TABLE_SEED_A = 40961   # a table seed, invented
TABLE_SEED_B = 7817
BUDGET = 250           # hands per variant per seed, invented (live is 1,000)
BUDGET_TINY = 60
EQUITY_SAMPLES = 257
VERSION_WIDTH = 61     # the invented version's learner size
VERSION_DEPTH = 2

# The fixed league's own numbers (league.md §2, §6; ASM-14).  A pool declaration and
# a league assertion use these because a pool's bound and a table's cell size belong
# to the one league of D-16 and are not the battery's to invent.
LEAGUE_BOUND = 5
LIVE_CELL_HANDS = 120
FULL_CELL_HANDS = 1500

FLAT = "flat-numeric"
TOKENS = "card-tokens"
BASELINES = ("random", "always-call", "oracle")

# The seven evidence families of protocol.md §1, under the design's own names.
FAMILIES = ("curves", "pool", "matrix", "rating", "baselines", "axis row", "header")

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
# A checkpoint is a file whose name says so; `.gitignore` already declares the
# project's checkpoint suffixes, so the battery requires one of these and no
# particular nesting inside the run record.
CHECKPOINT_SUFFIXES = (".pt", ".pth", ".npz", ".ckpt", ".bin")

# The invented versions the battery's league cases roll over, written to the shape
# `docs/L1/records.md` §7 pins: an id, the checkpoint path, the rung, the variant, the
# seed, the training step, the hands trained and the lineage it descends from.  The
# tags, the seeds, the steps and the samples are the battery's own, and the checkpoint
# itself is written by `agents.save` in a scratch directory — a case that needs a
# checkpoint builds one at a minimal budget (battery.md §2).
VERSIONS = {
    "kestrel": {"seed": SEED_A, "step": 880, "samples": 640, "rung": "R3", "variant": TOKENS,
                "lineage": "R3/start"},
    "bramble": {"seed": SEED_B, "step": 1440, "samples": 800, "rung": "R3", "variant": TOKENS,
                "lineage": "version-kestrel"},
    "thistle": {"seed": SEED_C, "step": 2260, "samples": 960, "rung": "R4", "variant": "deep",
                "lineage": "version-bramble"},
    "quarry": {"seed": SEED_E, "step": 3181, "samples": 1120, "rung": "R4", "variant": "wide",
               "lineage": "version-thistle"},
    "marlin": {"seed": SEED_F, "step": 4093, "samples": 1280, "rung": "R5", "variant": "dense",
               "lineage": "version-quarry"},
}
VERSION_TAGS = tuple(VERSIONS)

# The rungs that declare a pair, and therefore owe one frozen pool to both arms
# (league.md §2, ASM-16).
TWO_VARIANT_RUNGS = ("R4", "R5", "R6")


class SurfaceAbsent(AssertionError):
    """A declared module, entry point or contract is absent.

    Subclasses ``AssertionError`` so that ``unittest`` records it as a failure of the
    case that needed the surface, not as an error in the battery itself.
    """


# --------------------------------------------------------------------------
# Import-path plumbing
# --------------------------------------------------------------------------
def is_count(value):
    """Whether a returned value is an integer count (NumPy integers included)."""
    return isinstance(value, _numbers.Integral) and not isinstance(value, bool)


def is_mapping(value):
    """Whether a returned value is a mapping in the sense of e2e-surface.md §2."""
    return isinstance(value, Mapping)


def is_flag(value):
    """Whether a returned value is a boolean flag.

    ``records.md`` §8 makes a pool record's ``frozen`` a required flag, and §11 asks the
    rating for recorded booleans; a NumPy scalar boolean is the same flag as a ``bool``
    and a case asserts the flag's value rather than a spelling of it.
    """
    return isinstance(value, bool) or type(value).__name__.lower() in ("bool", "bool_",
                                                                        "bool8")


def _is_number(value):
    """Whether a value is a real number the battery reads as a quantity."""
    return isinstance(value, _numbers.Number) and not isinstance(value, (bool, complex))


def repo_root():
    """The repository root: this file lives at ``<root>/tests/e2e/_surface.py``."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def src_dir():
    return os.path.join(repo_root(), "src")


def _ensure_src():
    src = src_dir()
    if src not in sys.path:
        sys.path.insert(0, src)


def module(name):
    """Import one of the six declared packages, or fail with one clear message."""
    _ensure_src()
    try:
        return importlib.import_module(name)
    except Exception as exc:  # ImportError, or a package that is not importable yet
        raise SurfaceAbsent(
            "surface absent: the declared module %r is not importable from %s (%s: %s)"
            % (name, src_dir(), type(exc).__name__, exc)
        ) from exc


def entry(module_name, name):
    """Return a declared entry point, or fail naming the missing one."""
    mod = module(module_name)
    try:
        return getattr(mod, name)
    except AttributeError:
        raise SurfaceAbsent(
            "surface absent: %s.%s is not declared" % (module_name, name)
        ) from None


# --------------------------------------------------------------------------
# Tolerant readers for shapes the design leaves free
# --------------------------------------------------------------------------
def canon(obj, _depth=0):
    """A hashable, order-stable canonical form of an observable value.

    Used to compare two returned records for equality without assuming how the
    records are nested.  Unknown objects fall back to their type and ``str``, so a
    comparison never raises.
    """
    if _depth > 24:
        return ("deep", str(obj))
    if obj is None or isinstance(obj, (bool, int, float, str, bytes)):
        return obj
    if isinstance(obj, Mapping):
        return tuple(sorted((str(k), canon(v, _depth + 1)) for k, v in obj.items()))
    if isinstance(obj, (list, tuple)):
        return tuple(canon(v, _depth + 1) for v in obj)
    if isinstance(obj, (set, frozenset)):
        return tuple(sorted((canon(v, _depth + 1) for v in obj), key=repr))
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

    def walk(o, depth):
        if depth > 24:
            return
        if isinstance(o, Mapping):
            for k, v in o.items():
                parts.append(str(k))
                walk(v, depth + 1)
        elif isinstance(o, (list, tuple, set, frozenset)):
            for v in o:
                walk(v, depth + 1)
        elif hasattr(o, "tolist") and not isinstance(o, (str, bytes)):
            try:
                walk(o.tolist(), depth + 1)
                return
            except Exception:
                parts.append(str(o))
        else:
            parts.append(str(o))

    walk(obj, 0)
    return " ".join(parts).lower()


def find_values(obj, needle, _depth=0):
    """Every value found under a mapping key containing ``needle``, recursively."""
    found = []
    if _depth > 24:
        return found
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            if needle.lower() in str(key).lower():
                found.append(value)
            found.extend(find_values(value, needle, _depth + 1))
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for value in obj:
            found.extend(find_values(value, needle, _depth + 1))
    return found


def numbers(obj, _depth=0):
    """Every number in an observable value, in traversal order."""
    out = []
    if _depth > 24:
        return out
    if _is_number(obj):
        return [obj]
    if isinstance(obj, Mapping):
        for value in obj.values():
            out.extend(numbers(value, _depth + 1))
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for value in obj:
            out.extend(numbers(value, _depth + 1))
    elif hasattr(obj, "tolist") and not isinstance(obj, (str, bytes)):
        try:
            out.extend(numbers(obj.tolist(), _depth + 1))
        except Exception:
            pass
    return out


def strings(obj, _depth=0):
    """Every plain string in an observable value, in traversal order."""
    out = []
    if _depth > 24:
        return out
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, bytes):
        return []
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            out.append(str(key))
            out.extend(strings(value, _depth + 1))
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for value in obj:
            out.extend(strings(value, _depth + 1))
    return out


def scalars(value):
    """Every number inside ``value``, however it is nested."""
    out = []
    if _is_number(value):
        return [value]
    if isinstance(value, Mapping):
        for inner in value.values():
            out.extend(scalars(inner))
    elif isinstance(value, (list, tuple, set, frozenset)):
        for inner in value:
            out.extend(scalars(inner))
    return out


def _texts(value):
    """Every string or integer inside ``value``, as strings."""
    if isinstance(value, bool) or value is None:
        return []
    if isinstance(value, (str, int)):
        return [str(value)]
    out = []
    if isinstance(value, Mapping):
        for inner in value.values():
            out.extend(_texts(inner))
    elif isinstance(value, (list, tuple, set, frozenset)):
        for inner in value:
            out.extend(_texts(inner))
    return out


def declared_numbers(obj, *names):
    """Numbers under any key whose letters-and-digits form is one of ``names``.

    ``e2e-surface.md`` §3.4 leaves the league's declaration container free, so a case
    reads a declared bound, cell size or table seed by the key that carries it rather
    than by a shape this battery made up.
    """
    tokens = {_family_token(name) for name in names}
    out = []

    def walk(value, depth):
        if depth > 24:
            return
        if isinstance(value, Mapping):
            for key, inner in value.items():
                if _family_token(key) in tokens:
                    out.extend(numbers(inner))
                walk(inner, depth + 1)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for inner in value:
                walk(inner, depth + 1)

    walk(obj, 0)
    return out


_BOUND_EXACT = (
    "m",
    "max",
    "bound",
    "bounds",
    "maxversions",
    "maxversion",
    "poolsize",
    "window",
    "capacity",
    "limit",
)
_BOUND_WORDS = ("bound", "window", "maxversion", "poolsize", "capacity", "poollimit")


def bound_numbers(obj):
    """Numbers an observable declares as the pool's bound M.

    ``league.md`` §2 fixes M = 5, ``e2e-surface.md`` §3.4 has the league declare it, and
    ``ladder.md`` §3 puts it in a rung's pool entry.  The reader accepts the key ``M``
    and any key whose letters name the bound — ``max_versions``, ``window size``,
    ``pool_bound``, ``capacity`` — because the design fixes the parameter and leaves the
    spelling to the implementation.
    """
    out = []

    def walk(value, depth):
        if depth > 24:
            return
        if isinstance(value, Mapping):
            for key, inner in value.items():
                token = _family_token(key)
                if token in _BOUND_EXACT or any(word in token for word in _BOUND_WORDS):
                    out.extend(numbers(inner))
                walk(inner, depth + 1)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for inner in value:
                walk(inner, depth + 1)

    walk(obj, 0)
    return out


def rows_with(obj, *needles):
    """Every mapping whose own keys name all of ``needles``, at any depth.

    A matching mapping is not searched again, so one row is never counted twice
    through a nested copy of itself.
    """
    wanted = tuple(needle.lower() for needle in needles)
    out = []

    def walk(value, depth):
        if depth > 24:
            return
        if isinstance(value, Mapping):
            names = " ".join(_family_token(key) for key in value)
            if all(needle in names for needle in wanted):
                out.append(value)
                return
            for inner in value.values():
                walk(inner, depth + 1)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for inner in value:
                walk(inner, depth + 1)

    walk(obj, 0)
    return out


def count_rows(obj):
    """The rows that report win, tie and loss counts — a cell's two directions.

    ``protocol.md`` §2 requires every cell to report wins, ties and losses, the mean
    chip delta per hand, the seat split and the hands played.  A row is recognised by
    its own keys, never by a nesting this battery invented.
    """
    return rows_with(obj, "win", "loss")


def cell_directions(cell):
    """The direction records of one cell, or the cell itself when it is one record."""
    rows = count_rows(cell)
    if rows:
        return rows
    return [cell] if is_mapping(cell) else []


def count_total(row, *names):
    """The total of the counts found under any of ``names`` (0 when none is found)."""
    return int(sum(declared_numbers(row, *names)))


def seat_split(obj):
    """The per-seat hand counts a cell reports, read tolerantly.

    ``league.md`` §3 and ``protocol.md`` §1 fix the contract: seats alternate, so each
    member holds the button for half the cell's hands, and the cell reports the split.
    A report may key it ``seat 0``/``seat 1``, a nested split mapping, or a ``button``
    pair; the reader takes the scalars under the first seat- or button-named key it
    meets and never counts a nesting twice.
    """
    found = []

    def walk(value, depth):
        if depth > 24:
            return
        if isinstance(value, Mapping):
            for key, inner in value.items():
                name = str(key).lower()
                if "seat" in name or "button" in name:
                    found.extend(scalars(inner))
                else:
                    walk(inner, depth + 1)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for inner in value:
                walk(inner, depth + 1)

    walk(obj, 0)
    return found


def is_pool_record(value):
    """Whether a mapping is a pool record: it carries members and its bound or frozen flag.

    ``records.md`` §8 makes a pool record ``id``, ``m``, ``frozen`` and ``members`` — the
    id at the record's own top level, not under a key spelling the word "pool" — so the
    id reader has to recognise the record's shape and not only its nesting.
    """
    if not isinstance(value, Mapping):
        return False
    tokens = {_family_token(key) for key in value}
    return "members" in tokens and bool(
        tokens & {"m", "bound", "bounds", "frozen", "maxversions", "poolsize", "window"}
    )


def pool_identity(obj):
    """The pool id (or ids) an observable value declares.

    ``league.md`` §2 makes a pool's id change when and only when its members do, and
    ``ladder.md`` §3 says a rung configuration's pool carries "the id every arm's run
    record must carry".  The reader accepts ``pool_id`` at any level, an ``id`` inside
    a pool-shaped mapping, and a plain ``pool: "<id>"``; a member's id is not taken
    for the pool's.
    """
    found = []

    def walk(value, depth, in_pool, in_member):
        if depth > 24:
            return
        if isinstance(value, Mapping):
            for key, inner in value.items():
                name = str(key).lower()
                token = _family_token(key)
                member_context = in_member or any(
                    part in token for part in ("member", "version", "baseline")
                )
                pool_context = in_pool or "pool" in name or is_pool_record(value)
                if not member_context:
                    if token in ("poolid", "poolkey", "poolidentity"):
                        found.extend(_texts(inner))
                    elif pool_context and token in ("id", "identifier", "name"):
                        found.extend(_texts(inner))
                    elif "pool" in name and isinstance(inner, (str, int)):
                        found.extend(_texts(inner))
                walk(inner, depth + 1, pool_context, member_context)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for inner in value:
                walk(inner, depth + 1, in_pool, in_member)

    walk(obj, 0, False, False)
    return found


def checkpoint_paths(obj):
    """The distinct checkpoint-shaped artefacts a record names, in first-seen order.

    This is the right reader for a question about artefacts — how many a run retained —
    and the wrong reader for a question about a *listing*: it has already removed a
    second mention, so a uniqueness assertion judged against it cannot see the defect
    it is about.  A case that asserts something about the listing itself uses
    :func:`checkpoint_path_listing` instead.
    """
    seen = []
    for text in strings(obj):
        lowered = text.lower()
        if lowered.endswith(CHECKPOINT_SUFFIXES) and text not in seen:
            seen.append(text)
    return seen


def checkpoint_path_listing(obj):
    """Every checkpoint-shaped path a record lists, **as listed**, duplicates included.

    ``training.checkpoints`` is an index over the shipped set (``protocol.md`` §5,
    ``e2e-surface.md`` §3.5), and "an index lists no artefact twice" is an assertion
    *about the listing*: it has to read the entries the implementation returned, in the
    order it returned them, with every repeat still in place.  Reading it through
    :func:`checkpoint_paths` — which de-duplicates — would erase the only evidence the
    assertion is about (``battery.md`` §2: a case that cannot fail is a defect).

    One entry of an index is one mapping (or one element of a sequence), and an entry
    that gives a path both as its key and as its value is one listing of that artefact;
    two entries that name the same artefact are two listings, which is what the assertion
    is looking for.  The container is free — a sequence, a mapping keyed by path, a
    mapping keyed by rung, variant or seed — so every nesting is walked.
    """

    def is_path(text):
        return str(text).lower().endswith(CHECKPOINT_SUFFIXES)

    listed = []

    def walk(value, depth, suppressed=()):
        if depth > 24:
            return
        if isinstance(value, Mapping):
            names = []
            for key, inner in value.items():
                candidates = (str(key),) if is_path(key) else ()
                if isinstance(inner, str) and is_path(inner):
                    candidates += (inner,)
                for candidate in candidates:
                    if candidate not in suppressed and candidate not in names:
                        names.append(candidate)
            listed.extend(names)
            for key, inner in value.items():
                if isinstance(inner, str):
                    continue
                child = suppressed + (str(key),) if is_path(key) else suppressed
                walk(inner, depth + 1, child)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for inner in value:
                if isinstance(inner, str):
                    if is_path(inner) and inner not in suppressed:
                        listed.append(inner)
                else:
                    walk(inner, depth + 1, suppressed)
        elif isinstance(value, str) and is_path(value) and value not in suppressed:
            listed.append(value)

    walk(obj, 0)
    return listed


def checkpoint_paths_of(record):
    """The checkpoint paths a record's own ``checkpoints`` entry names.

    ``records.md`` §12 makes that key *the retained snapshots plus the final model per
    variant per seed*, so it is read on its own and the rest of the record is not walked:
    a pool member is a version and carries a ``path`` too (``records.md`` §7), so a
    whole-record walk counts the same artefact twice and reads a snapshot the run did not
    retain.  Returns ``[]`` when the record names no such entry; a case that requires the
    entry asserts that itself.
    """
    if not isinstance(record, Mapping):
        return []
    for key, value in record.items():
        if _family_token(key) in ("checkpoints", "checkpoint"):
            return checkpoint_paths(value)
    return []


def action_vocabulary(space):
    """The indices a declared action vocabulary names, read from its keys as well as values.

    ``e2e-surface.md`` §2 fixes three indices — 0 fold, 1 check/call, 2 raise — and not
    the container: a vocabulary may be a sequence, a mapping keyed by name, or a mapping
    keyed by the indices themselves.  Reading only the values would miss the third shape
    and report an empty vocabulary.
    """
    found = set()

    def add(value):
        if is_count(value):
            found.add(int(value))
        elif isinstance(value, str) and value.strip().isdigit():
            found.add(int(value.strip()))

    def walk(value, depth):
        if depth > 8:
            return
        if isinstance(value, Mapping):
            for key, inner in value.items():
                add(key)
                walk(inner, depth + 1)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for inner in value:
                walk(inner, depth + 1)
        else:
            add(value)

    walk(space, 0)
    if not found and isinstance(space, (list, tuple)) and len(space) == 3:
        # A vocabulary written as three ordered entries — the words without an index of
        # their own — still fixes the three indices positionally, which is what §2 asks
        # for: three indices and no more.
        found = {0, 1, 2}
    return found


def _family_token(text):
    """A family name reduced to its letters and digits: ``axis row`` == ``axis_row``."""
    return "".join(ch for ch in str(text).lower() if ch.isalnum())


def has_family(record, family):
    """Whether ``record`` carries an evidence family under the design's own name.

    ``docs/L1/protocol.md`` §1 names the seven families ``curves``, ``pool``,
    ``matrix``, ``rating``, ``baselines``, ``axis row`` and ``header``.  The freedom
    left to the implementation is the spelling: hyphens, underscores and spaces are
    treated as the same separator here.
    """
    wanted = _family_token(family)
    for candidate in strings(record):
        if _family_token(candidate) == wanted:
            return True
    return False


def drop_family(record, family):
    """Remove one evidence family from a record, under the design's own name."""
    wanted = _family_token(family)
    for key in [key for key in record if _family_token(key) == wanted]:
        del record[key]
    return record


def verdict(result):
    """Read a pass/fail verdict out of a driver, expectation or case record.

    Returns ``True``, ``False`` or ``None`` (no verdict found).  The freedom left to
    the implementation is the record's spelling; the contract is that a driver and an
    expectation report one.
    """
    if isinstance(result, bool):
        return result
    if isinstance(result, Mapping):
        for key, value in result.items():
            name = str(key).lower()
            if any(t in name for t in ("pass", "ok", "success", "result", "verdict", "status")):
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    text = value.lower()
                    if any(w in text for w in ("fail", "error", "refus", "red")):
                        return False
                    if any(w in text for w in ("pass", "ok", "succ", "green", "true")):
                        return True
    text = flatten_text(result)
    if any(word in text for word in ("fail", "error", "refus")):
        return False
    if any(word in text for word in ("pass", "succ", "green", "ok")):
        return True
    return None


def expectation_kinds(fixtures):
    """The expectation kinds ``harness.fixtures()`` lists, in declared order.

    ``e2e-surface.md`` §3.6 and ``records.md`` §14 make the kind set the harness's own:
    ``harness.expect`` takes a kind ``fixtures`` listed, and an unknown kind is a named
    failure.  So the battery discovers the vocabulary here and invents an *observed
    value*, never a kind (D-13, D-15, ``battery.md`` §4).  The kinds sit under a key
    naming the expectations, and the container is the implementation's freedom — a list of
    kinds, a mapping from kind to what it judges, or a further ``kinds`` entry — so both a
    sequence's entries and a registry's own keys read as kinds, and a registry's
    descriptions do not.
    """
    found = []

    def collect(value):
        if isinstance(value, Mapping):
            nested = [
                key for key in value
                if "expect" in _family_token(key)
                or _family_token(key) in ("kind", "kinds", "expectation", "expectations")
            ]
            if nested:
                for key in nested:
                    collect(value[key])
                return
            for key in value:
                text = str(key).strip()
                if text and text not in found:
                    found.append(text)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for inner in value:
                collect(inner)
        elif isinstance(value, str):
            text = value.strip()
            if text and text not in found:
                found.append(text)

    def walk(value, depth):
        if depth > 8:
            return
        if isinstance(value, Mapping):
            for key, inner in value.items():
                if "expect" in _family_token(key):
                    collect(inner)
                else:
                    walk(inner, depth + 1)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for inner in value:
                walk(inner, depth + 1)

    walk(fixtures, 0)
    return found


def refusal_text(call):
    """Run ``call``; return the text of its refusal, or ``None`` if it returned.

    ``docs/L1/e2e-surface.md`` §2 lets a violated contract raise *or* refuse with a
    failure record; this reader accepts either edge and hands back what was said.
    """
    try:
        result = call()
    except SurfaceAbsent:
        raise
    except Exception as exc:
        return "%s: %s" % (type(exc).__name__, exc)
    if result is None:
        return "returned None"
    text = flatten_text(result)
    if any(word in text for word in ("fail", "refus", "missing", "incomplete", "error")):
        return text
    return None


# --------------------------------------------------------------------------
# The ladder's own declarations, read tolerantly
# --------------------------------------------------------------------------
RUNGS = ("R1", "R2", "R3", "R4", "R5", "R6")
VARIANTS = {
    "R1": ("naive-numeric",),
    "R2": ("naive-numeric-torch",),
    "R3": ("card-tokens",),
    "R4": ("wide", "deep"),
    "R5": ("dense", "sparse"),
    "R6": ("residual", "plain"),
}
PRIMARY = {
    "R1": "naive-numeric",
    "R2": "naive-numeric-torch",
    "R3": "card-tokens",
    "R4": "deep",
    "R5": "dense",
    "R6": "residual",
}


def rung_names(declared):
    """The rung names a ``training.rungs()`` declaration carries, in declaration order."""
    seen = []

    def walk(obj, depth):
        if depth > 8:
            return
        if isinstance(obj, Mapping):
            for key, value in obj.items():
                name = str(key).strip()
                if name in RUNGS and name not in seen:
                    seen.append(name)
                walk(value, depth + 1)
        elif isinstance(obj, (list, tuple)):
            for value in obj:
                walk(value, depth + 1)
        elif isinstance(obj, str):
            name = obj.strip()
            if name in RUNGS and name not in seen:
                seen.append(name)

    walk(declared, 0)
    return seen


def variant_entries(config):
    """The variant entries of a resolved rung configuration, in declaration order.

    A rung may declare its variants as a list of entries or as a mapping from variant
    name to entry; in the second case the name is folded into the entry here, so every
    reader below sees the same shape.
    """
    entries = []

    def named(inner, key):
        if "name" in inner and isinstance(inner["name"], str):
            return inner
        folded = dict(inner)
        folded.setdefault("name", str(key))
        return folded

    def walk(obj, depth):
        if depth > 8:
            return
        if isinstance(obj, Mapping):
            for key, value in obj.items():
                if "variant" in str(key).lower():
                    if isinstance(value, Mapping):
                        for inner_key, inner in value.items():
                            if isinstance(inner, Mapping):
                                entries.append(named(inner, inner_key))
                    elif isinstance(value, (list, tuple)):
                        for inner in value:
                            if isinstance(inner, Mapping) and len(inner) == 1:
                                inner_key, body = next(iter(inner.items()))
                                if isinstance(body, Mapping):
                                    entries.append(named(body, inner_key))
                                    continue
                            if isinstance(inner, Mapping):
                                entries.append(inner)
                else:
                    walk(value, depth + 1)
        elif isinstance(obj, (list, tuple)):
            for value in obj:
                walk(value, depth + 1)

    walk(config, 0)
    return entries


def variant_name(entry, index=0):
    """The name a variant entry declares."""
    if isinstance(entry, Mapping):
        for key in ("name", "variant", "id", "label"):
            if isinstance(entry.get(key), str):
                return entry[key]
        for key, value in entry.items():
            if isinstance(value, str) and "name" in str(key).lower():
                return value
    for text in strings(entry):
        if text.strip():
            return text
    return "variant-%d" % (index,)


def variant_setting(entry, key, default=None):
    """One declared setting of a variant entry (``architecture``, ``backend``, ...)."""
    if isinstance(entry, Mapping):
        for name, value in entry.items():
            if _family_token(name) == _family_token(key):
                return value
    return default


def axis_text(result):
    """What a ``training.fairness`` result says the pair differs on."""
    for needle in ("axis", "difference", "differs", "varies", "changed"):
        values = find_values(result, needle)
        if values:
            return flatten_text(values)
    return flatten_text(result)


def custom_membership(tags=("kestrel", "bramble")):
    """The membership the seventh rung's ``pool`` entry declares (``records.md`` §8).

    ``ladder.md`` §3 says a configuration that is not in the registry carries the
    membership declaration itself in its ``pool`` entry — that is how a custom league
    reaches the loop as data rather than as a script — and ``records.md`` §8 fixes the
    declaration's keys: ``members`` (the versions, by id and lineage), ``m`` and
    ``frozen``.  The tags, the lineage chain, the steps and the samples are the battery's
    own invention (``battery.md`` §4).
    """
    members = []
    for tag in tags:
        spec = VERSIONS[tag]
        members.append({
            "id": "version-%s" % tag,
            "lineage": spec["lineage"],
            "rung": spec["rung"],
            "variant": spec["variant"],
            "seed": spec["seed"],
            "step": spec["step"],
            "samples": spec["samples"],
        })
    return members


def custom_rung(pool_id="pool-r7", bound=None):
    """A seventh rung configuration, written to ``docs/L1/ladder.md`` §3's schema.

    It appears in no design document: the axis, the variant names, the architecture
    sizes, the hyperparameters, the sample budget, the pool id and the declared
    membership are the battery's own.  It varies one thing — depth against width at a
    sparse connectivity — using only the settings the ladder's schema declares, and it
    is a configuration rather than a registry entry, so ``training.run`` must take it as
    data.  The ``pool`` entry is the schema's: its lineage, its bound, the id every arm's
    record must carry, and — because this configuration is not in the registry — the
    membership declaration ``records.md`` §8 requires (``members``, ``m``, ``frozen``),
    which is how a custom league reaches the loop as data.  The bound is the fixed
    league's M, because a pool's bound belongs to the one league of D-16 and is not the
    battery's to choose (``league.md`` §2).
    """
    if bound is None:
        bound = LEAGUE_BOUND
    architecture_deep = {
        "kind": "deep",
        "width": 48,
        "depth": 4,
        "sparsity": 0.5,
        "residual": False,
    }
    architecture_wide = {
        "kind": "wide",
        "width": 96,
        "depth": 2,
        "sparsity": 0.5,
        "residual": False,
    }
    hyper = {
        "learning_rate": 0.0005,
        "batch_size": 32,
        "target_update_interval": 200,
        "exploration": "epsilon-greedy 1.00 -> 0.05",
    }
    return {
        "name": "R7",
        "axis": "depth-against-width at sparse connectivity",
        "carried_from": "residual",
        "primary": "deep-sparse",
        "pool": {
            "id": pool_id,
            "lineage": "R6 residual",
            "m": bound,
            "frozen": True,
            "members": custom_membership(),
        },
        "variants": [
            {
                "name": "deep-sparse",
                "backend": "torch",
                "encoding": TOKENS,
                "architecture": architecture_deep,
                "learning_rule": "masked-q",
                "hyper": dict(hyper),
                "param_budget": 10000,
                "samples": BUDGET,
                "seeds": [SEED_A, SEED_B],
                "device": "cpu",
            },
            {
                "name": "wide-sparse",
                "backend": "torch",
                "encoding": TOKENS,
                "architecture": architecture_wide,
                "learning_rule": "masked-q",
                "hyper": dict(hyper),
                "param_budget": 10000,
                "samples": BUDGET,
                "seeds": [SEED_A, SEED_B],
                "device": "cpu",
            },
        ],
    }


def custom_variant(name=None):
    """One variant entry of :func:`custom_rung`, by name (primary by default)."""
    variants = custom_rung()["variants"]
    if name is None:
        return variants[0]
    for variant in variants:
        if variant["name"] == name:
            return variant
    raise AssertionError("the battery's own seventh rung has no variant %r" % (name,))


# --------------------------------------------------------------------------
# The one expensive league object, built once per process
# --------------------------------------------------------------------------
_SHARED = {}


def shared_league(case):
    """One pool, one matrix and one rating, built once per process and shared.

    The matrix is the battery's most expensive observable: K(K-1)/2 cells at the live
    budget's 120 hands per cell (``league.md`` §6, ASM-14).  The league is
    deterministic from its membership and its table seed (ASM-2), so a second case
    would see the same table; building it once keeps the battery's own hands played
    cheap, as ``battery.md`` §2 requires.  The fixture holds no scratch path — its
    pool is the three pinned baselines (``league.md`` §2) and its variant member is a
    learner held in memory — so it outlives the case that built it.
    """
    if "league" in _SHARED:
        return _SHARED["league"]
    pool = case.baselines_pool()
    variant = case.variant_policy()
    matrix = case.ep("evaluation", "matrix")(pool, [variant], "live")
    rating = case.ep("evaluation", "rating")(matrix)
    value = {
        "pool": pool,
        "members": case.members(pool),
        "variant": variant,
        "matrix": matrix,
        "rating": rating,
    }
    _SHARED["league"] = value
    return value


# --------------------------------------------------------------------------
# The base case the battery is written on
# --------------------------------------------------------------------------
class SurfaceCase(unittest.TestCase):
    """One battery case.  Every declared surface is reached through :meth:`ep`."""

    # -- the surface -------------------------------------------------------
    def mod(self, name):
        return module(name)

    def ep(self, module_name, name):
        return entry(module_name, name)

    # -- the harness's own vocabulary --------------------------------------
    def expectation_kinds(self):
        """The expectation kinds the fixture lists, discovered and never invented.

        ``e2e-surface.md`` §3.6: ``harness.expect`` takes a kind ``fixtures()`` lists,
        so a case asks the fixture rather than fixing a kind of its own.
        """
        fixtures = self.ep("harness", "fixtures")()
        kinds = expectation_kinds(fixtures)
        self.assertTrue(
            kinds,
            "harness.fixtures() yields the expectation kinds harness.expect accepts, so a "
            "battery can invent an observed value and not a kind (e2e-surface §3.6, "
            "records.md §14): %r" % (fixtures,),
        )
        return kinds

    def an_expectation_kind(self):
        """One expectation kind the fixture lists."""
        return self.expectation_kinds()[0]

    # -- declared-object builders, all through declared entry points --------
    def encoder(self, representation=FLAT):
        return self.ep("features", "build_encoder")(representation)

    def architecture_kind(self, preference):
        """A kind string the implementation itself declared in ``agents.learners``."""
        declared = self.ep("agents", "learners")()
        names = [text for text in strings(declared) if text.strip()]
        for wanted in (preference, "naive", "flat", "plain"):
            for name in names:
                if wanted in name.lower():
                    return name
        if not names:
            raise AssertionError(
                "agents.learners() declared no architecture kind this battery can name: %r"
                % (declared,)
            )
        return names[0]

    def learner_spec(self, width=96, depth=3, seed=SEED_A, backend="numpy",
                     kind=None, sparsity=0.0, residual=False):
        """The battery's learner spec: the four names §3.3 gives, plus the settings.

        ``docs/L1/e2e-surface.md`` §3.3 declares ``backend, architecture, sizes,
        seed``; ``docs/L1/ladder.md`` §3 declares width, depth, sparsity and residual
        as the architecture's settings.  How those are nested is the implementation's
        freedom, so the battery passes both the declared architecture descriptor and
        the declared ``sizes`` and asks only that a learner comes back.
        """
        if kind is None:
            kind = self.architecture_kind("naive")
        architecture = {
            "kind": kind,
            "width": width,
            "depth": depth,
            "sparsity": sparsity,
            "residual": residual,
        }
        return {
            "backend": backend,
            "architecture": architecture,
            "sizes": {"width": width, "depth": depth},
            "seed": seed,
        }

    def learner(self, **kwargs):
        return self.ep("agents", "build_learner")(self.learner_spec(**kwargs))

    def variant_learner(self, variant, seed=SEED_A):
        """A learner built from one variant entry of a resolved rung configuration.

        The variant's declared ``backend`` and ``architecture`` (kind, width, depth,
        sparsity, residual — ``ladder.md`` §3) are handed to ``agents.build_learner``
        in the battery's learner spec.
        """
        architecture = variant_setting(variant, "architecture")
        kind, width, depth, sparsity, residual = None, 96, 3, 0.0, False
        if isinstance(architecture, Mapping):
            for key, value in architecture.items():
                token = _family_token(key)
                if token == "kind":
                    kind = value
                elif token == "width":
                    width = _as_int(value, width)
                elif token == "depth":
                    depth = _as_int(value, depth)
                elif token == "sparsity":
                    sparsity = value
                elif token == "residual":
                    residual = value
        elif isinstance(architecture, str):
            kind = architecture
        return self.ep("agents", "build_learner")(
            self.learner_spec(
                width=width,
                depth=depth,
                seed=seed,
                backend=variant_setting(variant, "backend") or "numpy",
                kind=kind,
                sparsity=sparsity,
                residual=residual,
            )
        )

    def policy(self, learner, encoder=None, seed=SEED_A):
        if encoder is None:
            encoder = self.encoder()
        return self.ep("agents", "as_policy")(learner, encoder, seed)

    def baseline(self, name="random", seed=SEED_D):
        return self.ep("agents", "build_baseline")(name, seed)

    def hand(self, seed=SEED_A):
        return self.ep("engine", "new_hand")(seed)

    def readout(self, hand):
        return self.ep("engine", "readout")(hand)

    def legal(self, hand):
        return self.ep("engine", "legal_actions")(hand)

    def play(self, seed=SEED_A, policy_a=None, policy_b=None):
        if policy_a is None:
            policy_a = self.baseline("always-call", SEED_D)
        if policy_b is None:
            policy_b = self.baseline("always-call", SEED_D)
        return self.ep("engine", "play_hand")(seed, policy_a, policy_b)

    # -- decisions ---------------------------------------------------------
    def chosen_index(self, legal, action):
        """The action vocabulary's index for a policy's descriptor.

        ``docs/L1/e2e-surface.md`` §2 fixes the vocabulary at three indices and
        ``features.legal_indices`` returns the legal indices of a decision; the case
        reads the chosen descriptor's index by its position in ``legal_actions``.
        """
        indices = list(self.ep("features", "legal_indices")(legal))
        for position, candidate in enumerate(legal):
            same = candidate is action
            if not same:
                try:
                    same = bool(candidate == action)
                except Exception:
                    same = False
            if same and position < len(indices):
                return indices[position]
        raise AssertionError(
            "the policy returned a descriptor that is not in legal_actions: %r (legal: %r)"
            % (action, legal)
        )

    def observation(self, encoder, readout):
        return self.ep("features", "encode")(encoder, readout)

    def mask(self, readout):
        return self.ep("features", "legal_indices")(readout["legal"])

    def act(self, learner, encoder, readout):
        return self.ep("agents", "act")(learner, self.observation(encoder, readout), self.mask(readout))

    def action_index(self, result):
        """The index out of ``agents.act``'s return (index plus the learner's record)."""
        if isinstance(result, int) and not isinstance(result, bool):
            return result
        if isinstance(result, (tuple, list)):
            for value in result:
                if isinstance(value, int) and not isinstance(value, bool):
                    return value
        if isinstance(result, Mapping):
            for key, value in result.items():
                if any(t in str(key).lower() for t in ("action", "index", "move", "choice")):
                    if isinstance(value, int) and not isinstance(value, bool):
                        return value
        raise AssertionError(
            "cannot read an action index out of agents.act's return: %r" % (result,)
        )

    def finished_hand(self, seed=SEED_A, limit=200):
        """Play one hand to its end through the declared engine entry points."""
        engine = self.mod("engine")
        hand = engine.new_hand(seed)
        policy = self.baseline("always-call", SEED_D)
        steps = 0
        while not engine.is_terminal(hand) and steps < limit:
            hand = engine.apply_action(hand, policy(engine.readout(hand), engine.legal_actions(hand)))
            steps += 1
        return hand

    def decision_walk(self, seed=SEED_A, policy=None, limit=200):
        """Drive one hand through the declared engine entry points.

        Returns ``[(hand, readout, legal, action, index)]`` for each decision until the
        hand is terminal.  Only ``new_hand``, ``readout``, ``legal_actions``,
        ``apply_action``, ``is_terminal`` and ``features.legal_indices`` are used.
        """
        engine = self.mod("engine")
        hand = engine.new_hand(seed)
        if policy is None:
            policy = self.baseline("always-call", SEED_D)
        walk = []
        while len(walk) < limit and not engine.is_terminal(hand):
            readout = engine.readout(hand)
            legal = engine.legal_actions(hand)
            action = policy(readout, legal)
            walk.append((hand, readout, legal, action, self.chosen_index(legal, action)))
            hand = engine.apply_action(hand, action)
        return walk

    def transitions(self, seed=SEED_C, limit=6):
        """Transition records for ``agents.learn``, built from a driven hand.

        The record's shape is the battery's invention; it carries the two encoded
        observations, the chosen index, the reward, the terminal flag and the two
        legal masks, which is the least a masked Q-learning update needs.
        """
        encoder = self.encoder()
        walk = self.decision_walk(seed, self.baseline("random", SEED_D), limit=limit)
        out = []
        for position, (_hand, readout, legal, _action, index) in enumerate(walk):
            terminal = position == len(walk) - 1
            next_readout = walk[position + 1][1] if not terminal else readout
            next_legal = walk[position + 1][2] if not terminal else legal
            out.append(
                {
                    "observation": self.observation(encoder, readout),
                    "action": index,
                    "reward": 0.0,
                    "next_observation": self.observation(encoder, next_readout),
                    "terminal": terminal,
                    "legal": list(self.ep("features", "legal_indices")(legal)),
                    "next_legal": list(self.ep("features", "legal_indices")(next_legal)),
                }
            )
        return out

    # -- the league (D-16) -------------------------------------------------
    def version(self, tag, width=None, depth=None):
        """One invented version, in the record shape ``records.md`` §7 pins.

        ``e2e-surface.md`` §2 makes a version "a checkpoint of a run, carrying an id,
        the lineage it came from and its path"; ``records.md`` §7 fixes the keys — id,
        path, rung, variant, seed, step, samples and lineage.  The checkpoint is written
        by ``agents.save`` at a minimal budget, so no case depends on a shipped artifact
        (``battery.md`` §2); the tag, the lineage values, the samples and the file name
        are the battery's own.  ``width``/``depth`` let a case make two versions differ
        in capacity, which is how a cell's parameter counts become evidence that two
        memberships were not the same pool.
        """
        spec = VERSIONS[tag]
        if width is None:
            width = VERSION_WIDTH
        if depth is None:
            depth = VERSION_DEPTH
        path = os.path.join(self.scratch(), "version-%s.pt" % tag)
        learner = self.learner(width=width, depth=depth, seed=spec["seed"])
        written = self.ep("agents", "save")(learner, path)
        if written:
            path = str(written)
        return {
            "id": "version-%s" % tag,
            "path": path,
            "rung": spec["rung"],
            "variant": spec["variant"],
            "seed": spec["seed"],
            "step": spec["step"],
            "samples": spec["samples"],
            "lineage": spec["lineage"],
        }

    def membership(self, tags=("kestrel",), frozen=True, width=None, depth=None):
        """An invented pool declaration, in the shape ``records.md`` §8 pins.

        A declaration is ``members`` (the versions, by id and lineage), ``m`` (the
        bound) and ``frozen``; the bound is the league's fixed M, because a pool's bound
        belongs to the one league of D-16 and is not the battery's to choose
        (``league.md`` §2).
        """
        return {
            "members": [self.version(tag, width, depth) for tag in tags],
            "m": LEAGUE_BOUND,
            "frozen": bool(frozen),
        }

    def pool(self, tags=("kestrel",), frozen=True, width=None, depth=None):
        """A pool through ``evaluation.build_pool`` (``e2e-surface.md`` §3.4).

        ``tags`` is either the invented version tags to declare, or a ready declaration
        in the shape ``records.md`` §8 pins (``members``, ``m``, ``frozen``) — a case that
        brings its own lineage, its own snapshots or its own bound hands the declaration
        over rather than a list of tags, and both routes reach ``build_pool`` with a
        declaration and never with a tag list read back out of one.
        """
        declaration = (
            tags if is_mapping(tags) else self.membership(tags, frozen, width, depth)
        )
        return self.ep("evaluation", "build_pool")(declaration)

    def baselines_pool(self):
        """The pool a first rung has: the three baselines and no version.

        ``league.md`` §2: R1 has no lineage, so its pool is the three baselines alone.
        """
        return self.pool(tags=(), frozen=True)

    def members(self, pool):
        """A pool's ordered members and its bound, through ``pool_members``."""
        return self.ep("evaluation", "pool_members")(pool)

    def opponent(self, pool, seed=SEED_G):
        """One policy drawn from the pool, through ``opponent`` (``league.md`` §3)."""
        return self.ep("evaluation", "opponent")(pool, seed)

    def member_policy(self, tag, width=None, depth=None):
        """A policy for one invented version: its checkpoint, loaded by ``policy_from``."""
        return self.ep("evaluation", "policy_from")(
            self.version(tag, width, depth)["path"]
        )

    def variant_policy(self, seed=SEED_H, width=VERSION_WIDTH, depth=VERSION_DEPTH):
        """One of a rung's variant members: a learner in evaluation mode (§2)."""
        return self.ep("agents", "as_policy")(
            self.learner(width=width, depth=depth, seed=seed), self.encoder(), seed
        )

    def match(self, left=None, right=None, hands=CELL_HANDS, seed=TABLE_SEED_A):
        """One cell through ``evaluation.match``.

        ``e2e-surface.md`` §3.4 gives it two policies or two members, a hand count and
        a seed; the defaults are two of the fixed baselines, which makes a cheap cell
        and a cell no model influences (``protocol.md`` §3).
        """
        if left is None:
            left = self.baseline("always-call", SEED_D)
        if right is None:
            right = self.baseline("random", SEED_F)
        return self.ep("evaluation", "match")(left, right, hands, seed)

    def matrix_of(self, pool=None, variants=None, budget="live"):
        """A table through ``evaluation.matrix`` (``league.md`` §4)."""
        if pool is None:
            pool = self.baselines_pool()
        if variants is None:
            variants = [self.variant_policy()]
        return self.ep("evaluation", "matrix")(pool, variants, budget)

    def rating_of(self, matrix):
        """The fitted rating of one matrix (``league.md`` §5)."""
        return self.ep("evaluation", "rating")(matrix)

    def report_of(self, rung_name, record, matrix, rating):
        """The per-rung report: rung, record, matrix, rating (``e2e-surface.md`` §3.4)."""
        return self.ep("evaluation", "report")(rung_name, record, matrix, rating)

    # -- evidence records --------------------------------------------------
    def run_record(self, rung_name="R1", seeds=(SEED_A,), budget=BUDGET_TINY, device="cpu"):
        """A run record through ``training.run`` at a minimal budget."""
        return self.ep("training", "run")(rung_name, list(seeds), budget, device)

    def curves_of(self, record):
        """The run record's curves family, or a clear failure (``protocol.md`` §1)."""
        values = find_values(record, "curve")
        if not values:
            keys = sorted(str(key) for key in record) if is_mapping(record) else record
            raise AssertionError(
                "training.run's record carries no curves family: %r" % (keys,)
            )
        return values

    def curves_family(self, budget=BUDGET_TINY, seeds=(SEED_A,)):
        """An invented curves family: a sample axis and one learning signal per seed.

        ``protocol.md`` §1 asks the family for the sample axis, at least one learning
        signal from ``agents.learn`` per variant per seed, and the spread across seeds.
        The numbers are the battery's own.
        """
        return {
            "samples": [0, budget // 2, budget],
            "seeds": list(seeds),
            "signal": {"mean": [-0.9, -0.55, -0.4], "spread": [0.0, 0.05, 0.04]},
        }

    def table_seed_of(self, matrix=None):
        """The table seed an observable records, tolerantly (``league.md`` §4).

        A matrix records the table seed it played at; the league declares one too.  The
        reader prefers a key that names the table seed and accepts a bare seed key,
        because which of the two is recorded is the implementation's freedom.
        """
        candidates = []
        if matrix is not None:
            candidates = declared_numbers(matrix, "tableseed") or declared_numbers(matrix, "seed")
        if not candidates:
            candidates = declared_numbers(self.ep("evaluation", "league")(), "tableseed", "seed")
        if not candidates:
            return TABLE_SEED_A
        return int(candidates[0])

    def pool_row(self, tags=(), pool=None):
        """The pool evidence family, in the pool-record shape of ``records.md`` §8.

        A pool record carries its id, its bound, its frozen flag and its ordered
        members; the three baselines are present and marked pinned.  For a first rung
        the member list is the three baselines and nothing else: ``league.md`` §2 says
        R1's pool is the baselines alone and the report says so instead of inventing a
        version (``protocol.md`` §1, ``records.md`` §13).
        """
        members = []
        for tag in tags:
            spec = VERSIONS[tag]
            members.append({
                "id": "version-%s" % tag,
                "path": "checkpoints/versions/version-%s.pt" % tag,
                "rung": spec["rung"],
                "variant": spec["variant"],
                "seed": spec["seed"],
                "step": spec["step"],
                "samples": spec["samples"],
                "lineage": spec["lineage"],
            })
        members += [{"id": name, "baseline": True, "pinned": True} for name in BASELINES]
        identifier = "pool-" + ("-".join(tags) if tags else "baselines")
        return {"id": identifier, "m": LEAGUE_BOUND, "frozen": True, "members": members}

    def header_family(self, seeds=(SEED_A,), budget=BUDGET_TINY, device="cpu",
                      cell_hands=LIVE_CELL_HANDS, table_seed=None, record=None):
        """The header family: everything a third party needs to re-run the table.

        ``protocol.md`` §1: the game configuration, the action vocabulary, the
        parameter counts of every member, the sample budget, the cell size, the seed
        set, the table seed, the device and the checkpoint paths.
        """
        counts = {name: 0 for name in BASELINES}
        counts["variant"] = VERSION_WIDTH
        return {
            "game": self.ep("engine", "game_config")(),
            "action space": self.ep("features", "action_space")(),
            "parameter counts": counts,
            "sample budget": budget,
            "cell size": cell_hands,
            "seeds": list(seeds),
            "table seed": table_seed if table_seed is not None else TABLE_SEED_A,
            "device": device,
            "checkpoints": checkpoint_paths_of(record) if record is not None else [],
        }

    def evidence_record(self, run_record, matrix=None, rating=None, pool_row=None,
                        include=FAMILIES, seeds=(SEED_A,), budget=BUDGET_TINY,
                        device="cpu", axis_row="n/a, single variant",
                        cell_hands=LIVE_CELL_HANDS):
        """A run record completed with the evidence families ``protocol.md`` §1 names.

        ``training`` produces the run record and ``evaluation`` measures the table; the
        record ``evaluation.report`` judges is the run's record with the measured
        families attached under the design's own names.  Which families are attached is
        the case's choice, which is how a case hands the report an incomplete record;
        the matrix and the rating are also passed to ``report`` as its own arguments,
        because ``e2e-surface.md`` §3.4 gives them to it directly.
        """
        if not is_mapping(run_record):
            raise AssertionError(
                "training.run must return a record mapping; got %r" % (type(run_record).__name__,)
            )
        record = dict(run_record)
        if "curves" in include:
            # The family is attached under the design's own name, whether the run record
            # already carried one under some nesting this battery cannot know or not.
            values = find_values(run_record, "curve")
            record["curves"] = values if values else [self.curves_family(budget, seeds)]
        if "pool" in include:
            record["pool"] = pool_row if pool_row is not None else self.pool_row(())
        if "matrix" in include and matrix is not None:
            record["matrix"] = matrix
        if "rating" in include and rating is not None:
            record["rating"] = rating
        if "baselines" in include:
            record["baselines"] = {
                "rows": [{"member": name, "hand count": cell_hands} for name in BASELINES]
            }
        if "axis row" in include:
            record["axis row"] = axis_row
        if "header" in include:
            record["header"] = self.header_family(
                seeds=seeds,
                budget=budget,
                device=device,
                cell_hands=cell_hands,
                table_seed=self.table_seed_of(matrix) if matrix is not None else None,
                record=run_record,
            )
        return record

    # -- scratch -----------------------------------------------------------
    def scratch(self):
        path = tempfile.mkdtemp(prefix="pypoker-e2e-")
        self.addCleanup(_rmtree, path)
        return path


def _rmtree(path):
    shutil.rmtree(path, ignore_errors=True)


def _as_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
