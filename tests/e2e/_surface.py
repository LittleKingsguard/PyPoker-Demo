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

# One architecture, two rules: the size both learners of a rule pair are built at, so a
# rule swap is one axis and no capacity moves with it (rules.md §3, ASM-10, D-19).
RULE_WIDTH = 53
RULE_DEPTH = 3

# The fixed league's own numbers (league.md §2, §6; ASM-14).  A pool declaration and
# a league assertion use these because a pool's bound and a table's cell size belong
# to the one league of D-16 and are not the battery's to invent.
LEAGUE_BOUND = 5
LIVE_CELL_HANDS = 120
FULL_CELL_HANDS = 1500

FLAT = "flat-numeric"
TOKENS = "card-tokens"

# The baseline catalogue `protocol.md` §3 publishes, in catalogue order: D-6's three fixed
# rules first, then D-21's three simple folders (`e2e-surface.md` §3.3, D-6, D-21).  A case
# about the *catalogue* reads all six; a case about a pool's pinned membership, a matrix's
# baseline rows or the rating's anchor reads :data:`ANCHOR_BASELINES`, because the three of
# D-6 are the only ones pinned by every pool and zeroed by the fit (`protocol.md` §3,
# `records.md` §8, §11, ASM-32).
BASELINES = (
    "random",
    "always-call",
    "oracle",
    "fold-no-pair-or-face",
    "fold-no-pair-or-better",
    "fold-large-bet",
)

# The catalogue's `anchor: True` members — D-6's three fixed rules.  They are pinned in
# every pool whether a declaration names them or not, and they are the rating's anchor; a
# folding baseline is never one (`protocol.md` §3, `league.md` §2, §5, ASM-32).
ANCHOR_BASELINES = BASELINES[:3]

# D-21's three folding baselines, in catalogue order: members and table rows only when a
# configuration's membership declaration names them, and never the anchor (D-21,
# `folders.md` §2, §4).
FOLDER_BASELINES = BASELINES[3:]

# One invented baseline name the catalogue does **not** carry, for the refusals
# `agents.build_baseline` and `evaluation.build_pool` owe a name outside it
# (`folders.md` §2, `records.md` §8, `protocol.md` §3).  It is the battery's own; no
# document in `docs/L1/` carries it (`battery.md` §4).
UNKNOWN_BASELINE = "always-raise-battery"

# The rank alphabet of the one card spelling (`docs/L3/engine/readout.md` §3) and the
# ranks D-21 pins as face cards, J, Q, K **or A** (`folders.md` §2, ASM-30).  A folder case
# recomputes its rule from the readout's own spellings through these two, so the case
# holds no copy of a rank.
RANKS = "23456789TJQKA"
FACE_RANKS = ("J", "Q", "K", "A")

# The invented seeds a folder case drives its hands at: one hand per (opponent, seat, seed)
# (`folders.md` §2, §6, `battery.md` §4).
FOLDER_SEEDS = (SEED_A, SEED_B, SEED_C, SEED_D, SEED_E, SEED_F, SEED_G, SEED_H)

# The learning-rule catalogue `rules.md` §2 publishes: two members, the first of which is
# the declared default of §4.  A case that needs "one architecture, two rules" reads the
# names here; the catalogue itself is always read off `agents.learners()`, because the
# names it publishes are its own (`rules.md` §2, D-19).
RULE_DEFAULT = "masked-q-learning"
RULE_SECOND = "double-q-learning"
RULES = (RULE_DEFAULT, RULE_SECOND)

# The utility catalogue `utilities.md` §2 publishes: two members, the first of which is
# the declared default of §5.  A case that needs "one architecture, two utilities" reads
# the names here; the catalogue itself is always read off `agents.learners()`, because the
# names it publishes are its own (`utilities.md` §2, D-20).
UTILITY_DEFAULT = "net-chips"
UTILITY_SECOND = "stack-shortfall"
UTILITIES = (UTILITY_DEFAULT, UTILITY_SECOND)

# Two invented utility names the catalogue does not carry: the battery's own, one for a
# learner spec and a `load` spec, one for a variant entry (`utilities.md` §5: a name
# outside the catalogue is refused where it is declared, by name, and never mapped onto
# the default).
UNKNOWN_UTILITY = "tournament-payout-battery"
UNKNOWN_ENTRY_UTILITY = "chips-per-hour-battery"

# One architecture, two utilities: the size both learners of a utility pair are built at,
# so a utility swap is one axis and no capacity moves with it (`utilities.md` §3, ASM-10,
# D-20).
UTILITY_WIDTH = 47
UTILITY_DEPTH = 3

# The seven evidence families of protocol.md §1, under the design's own names.
FAMILIES = ("curves", "pool", "matrix", "rating", "baselines", "axis row", "header")

# The readout facts of `e2e-surface.md` §2 — the information set D-3 holds fixed across
# the ladder.  Eleven keys: D-21 added the eleventh, `hand_class`, a **derived** fact (the
# class of the acting seat's best five-card hand of hole plus board, `None` before the
# flop) that no encoding carries (`folders.md` §3, ASM-30, D-21).
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
    "hand_class",
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


def readout_fact(readout, key):
    """One readout fact, or a clear failure naming the fact the readout does not carry.

    ``e2e-surface.md`` §2 makes the readout's keys exactly the eleven facts, so a fact a
    case needs and the readout lacks is an **absent surface name** and not a
    ``KeyError`` thrown from inside the battery: the case that needed it fails with what
    is missing, and the battery itself stays sound (``battery.md`` §1, D-11).
    """
    if not is_mapping(readout):
        raise AssertionError(
            "engine.readout must return a mapping in the sense of e2e-surface.md §2; it "
            "returned %r" % (type(readout).__name__,)
        )
    if key not in readout:
        raise SurfaceAbsent(
            "surface absent: engine.readout does not carry the %r fact of "
            "e2e-surface.md §2 (it carries %r)"
            % (key, sorted(str(name) for name in readout))
        )
    return readout[key]


def seat_of(readout):
    """The acting seat's index, read off the readout's ``seat`` fact.

    ``e2e-surface.md`` §2 makes the fact "the acting seat, and whether it is the button" —
    a pair whose first entry is the index — and ``seat_of`` reads that index so a case can
    give one seat a policy and the other seat another (``folders.md`` §2).
    """
    seat = readout_fact(readout, "seat")
    if isinstance(seat, (list, tuple)) and seat:
        return int(seat[0])
    if is_count(seat):
        return int(seat)
    values = numbers(seat)
    if values:
        return int(values[0])
    raise AssertionError(
        "the readout's `seat` fact must name the acting seat; it gave %r" % (seat,)
    )


def card_rank(spelling):
    """The rank character of the one card spelling (`docs/L3/engine/readout.md` §3).

    A card is two characters, rank first, from ``RANKS``; a case that recomputes a
    folder's rank test reads the rank here and never spells a card of its own second time
    (``folders.md`` §2, ASM-30).
    """
    text = str(spelling)
    if not text or text[0] not in RANKS:
        raise AssertionError(
            "engine's card spelling is two characters, rank first from %r; the readout "
            "gave %r (`docs/L3/engine/readout.md` §3)" % (RANKS, spelling)
        )
    return text[0]


def starting_stack(config):
    """The starting stack `engine.game_config()` declares, read tolerantly.

    ``e2e-surface.md`` §3.1 fixes the game's stacks as 20 and leaves the declaration's key
    spelling to the implementation, so the number is read by what its key names —
    ``starting_stack``, ``starting stacks``, a ``stacks`` pair — and never spelled here
    (``folders.md`` §2, ASM-31).
    """
    found = []
    if is_mapping(config):
        for key, value in config.items():
            if "stack" in _family_token(key):
                found.extend(numbers(value))
    candidates = [
        int(number) for number in found
        if _is_number(number) and float(number).is_integer() and number > 0
    ]
    if not candidates:
        raise AssertionError(
            "engine.game_config() must declare the fixed game's starting stack "
            "(e2e-surface.md §3.1); it declared %r" % (config,)
        )
    return max(candidates)


def folder_rule_folds(name, readout, stack):
    """Whether D-21's rule for the folder ``name`` folds at this readout, recomputed.

    The predicate is derived from the readout's own facts — the rank characters of the two
    hole spellings, ``hand_class``, and the declared starting stack — so a case that
    compares it with the decision the folder actually made catches a folder that folded
    one decision early or late, on the wrong street, or on the wrong comparison
    (``folders.md`` §2, §3, D-21).

    Legality is **not** part of the predicate: ``folders.md`` §2 makes a folder fold only
    where folding is legal, and a case checks that half separately (ASM-31).
    """
    street = str(readout_fact(readout, "street")).strip().lower()
    if name == "fold-no-pair-or-face":
        # Pre-flop only: unpaired hole cards and neither card a face card
        # (J, Q, K or A).  From the flop onward it never folds (D-21, folders.md §2).
        if street != "preflop":
            return False
        ranks = [card_rank(card) for card in readout_fact(readout, "hole")]
        return (
            len(ranks) == 2
            and ranks[0] != ranks[1]
            and not (set(ranks) & set(FACE_RANKS))
        )
    if name == "fold-no-pair-or-better":
        # Flop, turn and river only: a high-card-only best five (hand_class 0).  Before
        # the flop `hand_class` is `None` and there is no five-card hand to judge
        # (folders.md §3, ASM-30).
        if street == "preflop":
            return False
        return readout_fact(readout, "hand_class") == 0
    if name == "fold-large-bet":
        # Any street: a call worth more than half the declared starting stack
        # (D-21, folders.md §2, ASM-31).
        return 2 * int(readout_fact(readout, "to_call")) > int(stack)
    raise AssertionError(
        "%r is not one of D-21's three folders %r" % (name, FOLDER_BASELINES)
    )


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


def index_entries(index):
    """The per-artefact entries of the shipped checkpoint index.

    ``training.checkpoints()`` is the index over the shipped set — each artefact with the
    rung variant that produced it and the rule and the utility it was trained under
    (``protocol.md`` §5, ``e2e-surface.md`` §3.5) — and the container of its entries is the
    implementation's freedom: a sequence of entries or a mapping keyed by the artefact.
    Returns ``[]`` when the index names none, so a case that needs entries fails with its
    own message and never inside this reader (``battery.md`` §2).

    The reader is what a case needs to make a claim about **one entry at a time**:
    :func:`find_values` over the whole record answers "does the index name a rule
    anywhere", which the index's own ``windows`` block answers whether or not any entry
    carries one.  This one yields the entries themselves, in the order the index lists
    them, so an entry that dropped a required key is the entry the assertion is about.
    """
    container = None
    if isinstance(index, Mapping):
        for key, value in index.items():
            if _family_token(key) in ("entries", "entry", "artefacts", "artifacts"):
                container = value
                break
    if container is None:
        found = find_values(index, "entries")
        container = found[0] if found else None
    if container is None:
        return []
    if isinstance(container, Mapping):
        container = list(container.values())
    return [entry for entry in (container or ()) if isinstance(entry, Mapping)]


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


def _baseline_name(record):
    """The catalogue name one baseline record states of itself, or ``None``."""
    if not is_mapping(record):
        return None
    for key, value in record.items():
        token = _family_token(key)
        if token in ("name", "baseline", "id", "member") and isinstance(value, str):
            return value
    for key, value in record.items():
        if "name" in _family_token(key) and isinstance(value, str):
            return value
    return None


def baseline_catalogue(declared):
    """The baseline catalogue ``agents.baselines()`` publishes, as ordered pairs.

    ``protocol.md`` §3 makes the catalogue **six** members in catalogue order, each
    carrying its rule, its ``params: 0`` and its ``anchor`` flag — true for D-6's three,
    false for D-21's folders (`e2e-surface.md` §3.3, ASM-32, D-21).  The container's shape
    is the implementation's freedom: a mapping keyed by baseline name with a record per
    name, or the sequence of records.  Either is read one member per name, so a case
    asserts the *catalogue* and never a container this battery made up.

    Returns ``[(name, record), ...]`` in the order the catalogue declares them, which is
    the order the pool's pinned baselines and the matrix's rows follow (`records.md` §8).
    """
    pairs = []
    if is_mapping(declared):
        items = list(declared.items())
        if items and all(is_mapping(value) for _key, value in items):
            for key, record in items:
                pairs.append((_baseline_name(record) or str(key), record))
            return pairs
        for key, value in items:
            if _family_token(key) in ("baselines", "catalogue", "records", "members",
                                      "names"):
                return baseline_catalogue(value)
    elif isinstance(declared, (list, tuple)):
        for item in declared:
            if is_mapping(item):
                pairs.append((_baseline_name(item), item))
            elif isinstance(item, str):
                pairs.append((item, {}))
    if not pairs:
        raise AssertionError(
            "agents.baselines() publishes the six-member catalogue of protocol.md §3, each "
            "member with its rule, its `params` and its `anchor` flag (e2e-surface.md "
            "§3.3, D-6, D-21); it published %r" % (declared,)
        )
    return pairs


def baseline_catalogue_names(declared):
    """The catalogue's member names, in the order it declares them (``protocol.md`` §3)."""
    return [name for name, _record in baseline_catalogue(declared)]


def rule_catalogue(declared):
    """The learning-rule catalogue ``agents.learners()`` publishes, as ordered pairs.

    ``rules.md`` §2 makes ``learners()`` publish ``learning_rules``: exactly two rules,
    in order, each with its **name** and the **target it aims at**, and its first member
    is the declared default of §4.  The key's spelling is the design's; what the battery
    asserts is that the catalogue exists, that it holds more than one member, and that
    each member is a mapping naming its own rule — never the key order of the whole
    ``learners()`` record, which is the implementation's own (``battery.md`` §2).

    Returns ``[(name, member), ...]`` in the order the catalogue declares, so a case can
    read the first member — the default — without spelling a name of its own.
    """
    if not isinstance(declared, Mapping):
        raise AssertionError(
            "agents.learners() must return a mapping in the sense of e2e-surface.md §3.3; "
            "it returned %r" % (type(declared).__name__,)
        )
    found = None
    for key, value in declared.items():
        token = _family_token(key)
        if "rule" not in token:
            continue
        if isinstance(value, Mapping):
            found = value
            break
    if found is None:
        raise AssertionError(
            "agents.learners() publishes the learning-rule catalogue — the two rules of "
            "rules.md §2, each with its name and its target, under a key naming the rules "
            "(e2e-surface.md §3.3, §2 'Learning rule'): it publishes %r"
            % (sorted(str(key) for key in declared),)
        )
    pairs = []
    for key, value in found.items():
        # A member that states its own name in a mapping is read as it is; a catalogue
        # that lists only names is read as one member per name, so the *catalogue* is
        # still asserted rather than the container's shape.
        pairs.append((str(key), value if isinstance(value, Mapping) else {"name": str(key)}))
    return pairs


def rule_names(declared):
    """The catalogue's member names, in the order it declares them (``rules.md`` §2)."""
    return [name for name, _member in rule_catalogue(declared)]


def member_rule(member):
    """The rule name one catalogue member carries, or ``None``."""
    if not isinstance(member, Mapping):
        return None
    for key, value in member.items():
        token = _family_token(key)
        if token in ("name", "rule", "learningrule", "id") and isinstance(value, str):
            return value
    for key, value in member.items():
        if "name" in _family_token(key) and isinstance(value, str):
            return value
    return None


def member_target(member):
    """The target one catalogue member aims at, under whatever key declares it.

    ``rules.md`` §2 states each rule's target — the masked maximum of the target copy,
    or the online parameters' argmax read off the target copy — and leaves the spelling
    of the field to the implementation, so the field is read by what it names.
    """
    if not isinstance(member, Mapping):
        return None
    for key, value in member.items():
        token = _family_token(key)
        if "target" in token or token in ("aim", "aims", "bootstrap", "updates", "formula"):
            if isinstance(value, (str, Mapping, list, tuple)) and value:
                return value
    return None


def utility_catalogue(declared):
    """The utility catalogue ``agents.learners()`` publishes, as ordered pairs.

    ``utilities.md`` §2 makes ``learners()`` publish the utility catalogue: more than one
    member, in order, each with its **name** and the **reward it delivers**, and its first
    member is the declared default of §5.  The key's spelling is the design's; what the
    battery asserts is that the catalogue exists, that it holds more than one member, and
    that each member is a mapping naming its own utility — never the key order of the
    whole ``learners()`` record, which is the implementation's own (``battery.md`` §2).

    The mirror of :func:`rule_catalogue`, and read under the same rule: the catalogue is
    the value published under a key whose letters contain ``util``.  Returns
    ``[(name, member), ...]`` in the order the catalogue declares, so a case can read the
    first member — the default — without spelling a name of its own.
    """
    if not isinstance(declared, Mapping):
        raise AssertionError(
            "agents.learners() must return a mapping in the sense of e2e-surface.md §3.3; "
            "it returned %r" % (type(declared).__name__,)
        )
    found = None
    for key, value in declared.items():
        if "util" not in _family_token(key):
            continue
        if isinstance(value, Mapping):
            found = value
            break
        if isinstance(value, (list, tuple)) and value:
            # A catalogue written as a sequence of members is the same catalogue: each
            # member states its own name, so the pairs are read off the members.
            found = list(value)
            break
    if found is None:
        raise AssertionError(
            "agents.learners() publishes the utility catalogue — the members of "
            "utilities.md §2, each with its name and the reward it delivers, under a key "
            "naming the utilities (e2e-surface.md §3.3, §2 'Utility', D-20): it publishes "
            "%r" % (sorted(str(key) for key in declared),)
        )
    pairs = []
    keyed = isinstance(found, Mapping)
    for key, value in (found.items() if keyed else enumerate(found)):
        if isinstance(value, Mapping):
            pairs.append((str(key), value))
            continue
        # A catalogue that lists only names is read as one member per name, so the
        # *catalogue* is still asserted rather than the container's shape: a mapping keyed
        # by name says the name in its key, a sequence says it in the entry.
        name = str(key) if keyed else str(value)
        pairs.append((str(name), {"name": str(name)}))
    return pairs


def utility_names(declared):
    """The catalogue's member names, in the order it declares them (``utilities.md`` §2)."""
    return [name for name, _member in utility_catalogue(declared)]


def member_utility(member):
    """The utility name one catalogue member carries, or ``None``."""
    if not isinstance(member, Mapping):
        return None
    for key, value in member.items():
        token = _family_token(key)
        if token in ("name", "utility", "id") and isinstance(value, str):
            return value
    for key, value in member.items():
        if "name" in _family_token(key) and isinstance(value, str):
            return value
    return None


def member_reward(member):
    """The reward one catalogue member states, under whatever key declares it.

    ``utilities.md`` §2 states each utility's reward — ``net-chip-delta`` for
    ``net-chips``, ``squared-stack-shortfall-delta`` for ``stack-shortfall`` — as a stable
    token, and leaves the spelling of the field to the implementation, so the field is
    read by what it names.
    """
    if not isinstance(member, Mapping):
        return None
    for key, value in member.items():
        token = _family_token(key)
        if "reward" in token or token in ("payoff", "payment", "terminal", "score"):
            if isinstance(value, (str, Mapping, list, tuple)) and value:
                return value
    return None


def member_normaliser(member):
    """The normaliser one catalogue member states, under whatever key declares it.

    ``utilities.md`` §2 makes every member carry ``name``, the ``reward`` it delivers and
    the ``normaliser`` that reward is divided by, and leaves the spelling of the field to
    the implementation — a token such as ``U(s_0)`` or the number itself — so the field is
    read by what it names and never by one word this battery made up.
    """
    if not isinstance(member, Mapping):
        return None
    for key, value in member.items():
        token = _family_token(key)
        if "normalis" in token or "normaliz" in token or token in ("divisor",
                                                                  "denominator"):
            if isinstance(value, (str, Mapping, list, tuple)) and value:
                return value
            if value and _is_number(value):
                return value
    return None


# --------------------------------------------------------------------------
# The utility a record names (records.md §7, §8, §9, §10, §12; utilities.md §6, §7)
#
# D-20 puts one fact in five records, exactly as D-19 does for the rule: a version carries
# `utility`, a pool record the `utilities` its version members declare, a cell one utility
# per member, a matrix one per member plus the `utility_population` they make up, and a run
# record each variant's utility plus the run's `utilities` set.  The readers below are the
# utility side of the rule readers in `_records.py`, kept here because this module may not
# change that one: the fact is the catalogue name, or `None` for a baseline that declares
# none.
# --------------------------------------------------------------------------
def declared_field(record, what, *names):
    """One required field of a record, under whichever of ``names`` spells it."""
    if not isinstance(record, Mapping):
        raise AssertionError(
            "%s must be a mapping in the sense of records.md §1; it is a %r"
            % (what, type(record).__name__)
        )
    wanted = {_family_token(name) for name in names}
    for key, value in record.items():
        if _family_token(key) in wanted:
            return value
    raise AssertionError(
        "%s carries the required key %r — records.md §1 makes a required key part of the "
        "surface — and it carries %r"
        % (what, names[0], sorted(str(key) for key in record))
    )


def utilities_of(value):
    """Every ``(member id, utility)`` pair a utilities-shaped container states, in order.

    A container may be keyed by member — a cell's and a matrix's ``utilities`` — or be the
    list of names a pool record or a run record states — the distinct utilities, no member
    attached.  Both shapes are read here, and a member whose utility is a baseline's
    ``None`` keeps its place, because "which objectives met" is an answer a cell gives and
    "one of them declares none" is part of it (``records.md`` §9, §10, D-20).
    """
    out = []
    if isinstance(value, Mapping):
        for key, inner in value.items():
            if isinstance(inner, Mapping):
                name = None
                for field in ("utility", "name", "id", "member"):
                    candidate = inner.get(field)
                    if isinstance(candidate, str):
                        name = candidate
                        break
                out.append((str(key), name))
            elif inner is None or isinstance(inner, (str, bytes)):
                out.append((str(key), None if inner is None else str(inner)))
            else:
                out.append((str(key), None))
        return out
    if isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            if isinstance(item, Mapping):
                name = None
                for field in ("utility", "name", "value"):
                    candidate = item.get(field)
                    if isinstance(candidate, str):
                        name = candidate
                        break
                member = None
                for field in ("member", "id", "variant"):
                    candidate = item.get(field)
                    if isinstance(candidate, str):
                        member = candidate
                        break
                out.append((member, name))
            elif item is None or isinstance(item, (str, bytes)):
                out.append((None, None if item is None else str(item)))
            else:
                out.append((None, None))
        return out
    if isinstance(value, (str, bytes)):
        return [(None, str(value))]
    return out


def utility_names_of(value):
    """The distinct utility names a utilities-shaped container states, in first-seen order."""
    seen = []
    for _member, utility in utilities_of(value):
        if utility is not None and utility not in seen:
            seen.append(utility)
    return seen


def version_utility(member):
    """The ``utility`` a version member declares — a **required** key of ``records.md`` §7."""
    return declared_field(member, "a version member of the pool (records.md §7)", "utility")


def index_entry_rule(entry):
    """The ``rule`` one entry of the shipped checkpoint index names — **required** by §7.

    ``records.md`` §1 makes a key marked **required** one the e2e battery asserts, and §7
    marks a version record's ``rule`` so; ``training.checkpoints()``'s ``entries`` are
    version records, extended with ``kind`` (``e2e-surface.md`` §3.5, ``protocol.md`` §5).
    The rule is therefore read **on each entry** and never off the index's separate
    ``windows`` block, which names the same rule whether or not any entry carries one.

    The counterpart, on the same entries, of the ``utility`` field FAM-18.6 reads
    (``utilities.md`` §6, D-19, D-20).
    """
    return declared_field(
        entry,
        "an entry of the shipped checkpoint index (protocol.md §5, e2e-surface.md §3.5)",
        "rule",
    )


def pool_utilities(row):
    """The ``utilities`` a pool record declares — a **required** key of ``records.md`` §8.

    The key is the plural ``utilities`` and nothing else: §8 requires the *set* a pool's
    version members declare, so a record carrying a singular ``utility`` has declared no
    such key at all and a case fails with its own message rather than reading one member's
    name where the population belongs (``records.md`` §8, ``utilities.md`` §7).
    """
    return declared_field(row, "a pool record (records.md §8)", "utilities")


def cell_utilities(cell):
    """The ``utilities`` a cell declares — a **required** key of ``records.md`` §9.

    §9 requires each member's utility **by id** under the plural key; a singular ``utility``
    is a different declaration and is not read here (``records.md`` §9, ``utilities.md``
    §9).
    """
    return declared_field(cell, "a cell record (records.md §9)", "utilities")


def matrix_utilities(matrix):
    """The ``utilities`` a matrix declares — a **required** key of ``records.md`` §10.

    The plural key, as for a cell: §10 requires each member's utility by id, beside the
    ``utility_population`` they make up (``records.md`` §10, ``utilities.md`` §9).
    """
    return declared_field(matrix, "a matrix record (records.md §10)", "utilities")


def matrix_utility_population(matrix):
    """The ``utility_population`` a matrix declares — a **required** key of §10."""
    return declared_field(
        matrix,
        "a matrix record (records.md §10)",
        "utility_population",
    )


def run_utilities(record):
    """The ``utilities`` set a run record declares — a **required** key of §12.

    The plural key, as for a pool record: §12 requires the *set* of utilities the run
    declared and trained, and a singular ``utility`` is not that key (``records.md`` §12,
    ``utilities.md`` §7).
    """
    return declared_field(record, "a run record (records.md §12)", "utilities")


def variant_utility(entry):
    """The ``utility`` one variant entry of a run record names (§12, D-20)."""
    return declared_field(
        entry, "a variant entry of a run record (records.md §12)", "utility"
    )


def variant_curves(curves, name):
    """The curve body one variant's own name reaches in a curves family, or ``None``.

    ``records.md`` §12 makes the curves family *per variant per seed*, so a curve belongs
    to a variant and the family says which: as a mapping keyed by the variant's name, as
    an entry carrying its own name, or as a one-key mapping keyed by that name.  A reader
    that cannot attribute a curve to a variant cannot compare two arms' curves at all, and
    the case that needs the comparison says so rather than comparing two arbitrary halves
    (`battery.md` §1: a case that cannot fail is a defect).
    """
    wanted = _family_token(name)
    name_tokens = {"name", "variant", "arm", "member", "model", "label", "id"}

    def own_name(entry):
        for key, value in entry.items():
            if _family_token(key) in name_tokens and isinstance(value, str):
                return value
        return None

    def matched(entry):
        if not isinstance(entry, Mapping):
            return False
        stated = own_name(entry)
        if stated is not None:
            return _family_token(stated) == wanted
        if len(entry) == 1:
            key = next(iter(entry))
            return (_family_token(key) == wanted
                    and isinstance(entry[key], (Mapping, list, tuple)))
        return False

    def body(entry):
        if own_name(entry) is None and len(entry) == 1:
            return next(iter(entry.values()))
        return entry

    def walk(value, depth):
        if depth > 12:
            return None
        if isinstance(value, Mapping):
            for key, inner in value.items():
                if _family_token(key) == wanted and isinstance(inner, (Mapping, list, tuple)):
                    return inner
            if matched(value):
                return body(value)
            for inner in value.values():
                found = walk(inner, depth + 1)
                if found is not None:
                    return found
        elif isinstance(value, (list, tuple)):
            for inner in value:
                if matched(inner):
                    return body(inner)
            for inner in value:
                found = walk(inner, depth + 1)
                if found is not None:
                    return found
        return None

    return walk(curves, 0)


def family_value(record, family):
    """The value a record carries under the design's own family name, or ``None``.

    The mirror of :func:`has_family`: ``report`` copies each evidence family by value
    under ``protocol.md`` §1's spelling, and a case that asserts *inside* one family —
    the pool row's rules, the axis row's text — reads that family's value and not the
    flattened whole record.
    """
    wanted = _family_token(family)
    if isinstance(record, Mapping):
        for key, value in record.items():
            if _family_token(key) == wanted:
                return value
    return None


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
            # `records.md` §7 makes a version member's `rule` required (D-19); the tag
            # table carries none, so the catalogue's declared default is the rule these
            # invented versions name, which is what a record without a rule reads as.
            "rule": spec.get("rule") or RULE_DEFAULT,
            # And its `utility`, required on the same terms (records.md §7, D-20).
            "utility": spec.get("utility") or UTILITY_DEFAULT,
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
    # The hyperparameters a run will honour are the module's six declared ones, and a
    # `hyper` block that names another value is a declaration the run refuses (ASM-7):
    # this configuration therefore declares none, so the invented axis is the only thing
    # it varies and no key of it is a value the run would ignore.
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
                # `records.md` §2: a variant entry's `learning_rule` is one of the
                # catalogue's members — the name the catalogue publishes, never a prefix
                # of it (rules.md §2, D-19).
                "learning_rule": RULE_DEFAULT,
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
                "learning_rule": RULE_DEFAULT,
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


def shared_rule_league(case):
    """One table in which **two rules meet**, built once per process and shared.

    The heterogeneous table D-19 exists for: the frozen pool a run trained against (the
    three baselines alone, ``league.md`` §2) plus the rung's **two** variants, one trained
    under each catalogue rule.  Its membership is the smallest one that holds two
    policies of two rules — K = 5, so ten cells at the live 120 hands (``league.md`` §4,
    §6) — and it is built once and shared, because the league is deterministic from its
    membership and its table seed (ASM-2) and no second case should pay for the same
    table (``battery.md`` §2).

    The two variant policies are two learners of **one architecture** at one seed each,
    so the only thing that differs between them is the rule they were built under — which
    is what makes the table's `rules` and `population` evidence about estimators rather
    than about capacity (``rules.md`` §3, §7).  The fixture holds no scratch path, so it
    outlives the case that built it.
    """
    if "rule_league" in _SHARED:
        return _SHARED["rule_league"]
    pool = case.baselines_pool()
    masked = case.rule_policy(RULE_DEFAULT, seed=SEED_I)
    doubled = case.rule_policy(RULE_SECOND, seed=SEED_J)
    matrix = case.ep("evaluation", "matrix")(pool, [masked, doubled], "live")
    rating = case.ep("evaluation", "rating")(matrix)
    value = {
        "pool": pool,
        "members": case.members(pool),
        "masked": masked,
        "doubled": doubled,
        "variants": [masked, doubled],
        "rules": [RULE_DEFAULT, RULE_SECOND],
        "matrix": matrix,
        "rating": rating,
    }
    _SHARED["rule_league"] = value
    return value


def shared_utility_league(case):
    """One table in which **two utilities meet**, built once per process and shared.

    The heterogeneous table D-20 exists for: the frozen pool a run trained against (the
    three baselines alone, ``league.md`` §2) plus the rung's **two** variants, one trained
    under each catalogue utility.  Its membership is the smallest one that holds two
    policies of two utilities — K = 5, so ten cells at the live 120 hands (``league.md``
    §4, §6) — and it is built once and shared, because the league is deterministic from
    its membership and its table seed (ASM-2) and no second case should pay for the same
    table (``battery.md`` §2).

    The two variant policies are two learners of **one architecture**, so the only thing
    that differs between them is the utility their model's reward was defined by — which
    is what makes the table's `utilities` and `utility_population` evidence about
    objectives rather than about capacity (``utilities.md`` §3, §7, ASM-10).  The fixture
    holds no scratch path, so it outlives the case that built it.
    """
    if "utility_league" in _SHARED:
        return _SHARED["utility_league"]
    pool = case.baselines_pool()
    chips = case.utility_policy(UTILITY_DEFAULT, seed=SEED_I)
    shortfall = case.utility_policy(UTILITY_SECOND, seed=SEED_J)
    matrix = case.ep("evaluation", "matrix")(pool, [chips, shortfall], "live")
    rating = case.ep("evaluation", "rating")(matrix)
    value = {
        "pool": pool,
        "members": case.members(pool),
        "chips": chips,
        "shortfall": shortfall,
        "variants": [chips, shortfall],
        "utilities": [UTILITY_DEFAULT, UTILITY_SECOND],
        "matrix": matrix,
        "rating": rating,
    }
    _SHARED["utility_league"] = value
    return value


def shared_folder_league(case):
    """One table over a pool that **declares D-21's three folders**, built once.

    The membership a configuration that declares the folders tables: the flagged three,
    the three folders the declaration names, and the rung's one variant — K = 7, so 21
    cells at the live budget's 120 hands (``league.md`` §4, §6, ASM-33, D-21).  It is the
    smallest table whose pool holds the folders, and it is built once and shared by the
    two facts that need it — the matrix's arithmetic over that membership (FAM-8) and the
    rating's anchor on a table that holds folders (FAM-9) — because the league is
    deterministic from its membership and its table seed (ASM-2) and no second case should
    pay for the same table (``battery.md`` §2).

    Its one variant is a learner in evaluation mode, so the table's trained column is the
    battery's own variant and never an anchor (D-16).
    """
    if "folder_league" in _SHARED:
        return _SHARED["folder_league"]
    pool = case.folders_pool()
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
    _SHARED["folder_league"] = value
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
                     kind=None, sparsity=0.0, residual=False, learning_rule=None,
                     utility=None):
        """The battery's learner spec: the four names §3.3 gives, plus the settings.

        ``docs/L1/e2e-surface.md`` §3.3 declares ``backend, architecture, sizes,
        seed``; ``docs/L1/ladder.md`` §3 declares width, depth, sparsity and residual
        as the architecture's settings.  How those are nested is the implementation's
        freedom, so the battery passes both the declared architecture descriptor and
        the declared ``sizes`` and asks only that a learner comes back.

        ``learning_rule`` is ``records.md`` §3's optional rule: a spec that names one is
        built under it, and a spec that names none — every caller before FAM-17 — is
        built under the catalogue's first member, which is the declared default
        (``rules.md`` §4).  The key is added only when a case names a rule, so a caller
        that does not care about rules passes exactly the spec it passed before (D-19).

        ``utility`` is the same optional selection on D-20's axis: a spec that names one
        is built under it, and a spec that names none is built under the catalogue's
        first member, ``net-chips`` (``utilities.md`` §5, ``records.md`` §3).  The key is
        added only when a case names a utility, for the same reason.
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
        spec = {
            "backend": backend,
            "architecture": architecture,
            "sizes": {"width": width, "depth": depth},
            "seed": seed,
        }
        if learning_rule is not None:
            spec["learning_rule"] = learning_rule
        if utility is not None:
            spec["utility"] = utility
        return spec

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
                # `records.md` §2 makes a variant entry's `learning_rule` the rule its
                # learner is trained under, so a learner built from an entry is built
                # under that entry's rule and under no other (D-19).
                learning_rule=variant_setting(variant, "learning_rule"),
                # ... and D-20's `utility` is the second axis of the same entry: a variant
                # that names one is trained on that utility's reward (utilities.md §5, §7).
                utility=variant_setting(variant, "utility"),
            )
        )

    def rule_learner(self, rule, seed=SEED_I, width=RULE_WIDTH, depth=RULE_DEPTH):
        """A learner built under one catalogue rule (``rules.md`` §2, ``records.md`` §3)."""
        return self.ep("agents", "build_learner")(
            self.learner_spec(width=width, depth=depth, seed=seed, learning_rule=rule)
        )

    def rule_policy(self, rule, seed=SEED_I, width=RULE_WIDTH, depth=RULE_DEPTH):
        """One learner under ``rule`` as a policy, on the encoder this battery uses."""
        learner = self.rule_learner(rule, seed=seed, width=width, depth=depth)
        return self.ep("agents", "as_policy")(learner, self.encoder(), seed)

    def utility_learner(self, utility, seed=SEED_I, width=UTILITY_WIDTH,
                        depth=UTILITY_DEPTH):
        """A learner built under one catalogue utility (``utilities.md`` §2, §5)."""
        return self.ep("agents", "build_learner")(
            self.learner_spec(width=width, depth=depth, seed=seed, utility=utility)
        )

    def utility_policy(self, utility, seed=SEED_I, width=UTILITY_WIDTH,
                       depth=UTILITY_DEPTH):
        """One learner under ``utility`` as a policy, on the encoder this battery uses."""
        learner = self.utility_learner(utility, seed=seed, width=width, depth=depth)
        return self.ep("agents", "as_policy")(learner, self.encoder(), seed)

    def two_rule_rung(self, seeds=(SEED_A, SEED_B), members=(), bound=None,
                      pool_id="pool-r9-dual-rule"):
        """The battery's own two-rule configuration: one architecture, two rules.

        It appears in no design document: its name, its axis, its two variant names, its
        width and depth, its seed set, its pool id and the membership declaration it
        carries are the battery's own (``battery.md`` §4).  What it declares is exactly
        what D-19 makes legal and nothing else — two variant entries that agree on
        ``backend``, ``encoding``, ``architecture``, ``param_budget``, ``samples``,
        ``seeds`` and ``device`` and differ on ``learning_rule`` alone — so a run of it
        must train **both** variants, one under each rule (``rules.md`` §7, D-19).
        ``hyper`` is left undeclared and not varied: the six hyperparameters are one
        declaration for both rules, so a rule swap moves no budget with it (§2, ASM-7).

        The pool is the baselines alone — the cheapest window the surface allows, and the
        one R1 declares — because a case that only needs the loop to train two rules pays
        for no version it does not read (``battery.md`` §2).  ``members`` lets a case hand
        it a real checkpoint it built, when the run's own pool record is read back.
        """
        if bound is None:
            bound = LEAGUE_BOUND
        kind = self.architecture_kind("naive")
        architecture = {
            "kind": kind,
            "width": RULE_WIDTH,
            "depth": RULE_DEPTH,
            "sparsity": 0.0,
            "residual": False,
        }
        variants = []
        for name, rule in (("masked-arm", RULE_DEFAULT), ("double-arm", RULE_SECOND)):
            variants.append(
                {
                    "name": name,
                    "backend": "numpy",
                    "encoding": FLAT,
                    "architecture": dict(architecture),
                    "learning_rule": rule,
                    "param_budget": 10000,
                    "samples": BUDGET_TINY,
                    "seeds": list(seeds),
                    "device": "cpu",
                    "table": "live",
                }
            )
        return {
            "name": "R9-dual-rule",
            "axis": "the learning rule at one architecture",
            "carried_from": "residual",
            "primary": "masked-arm",
            "pool": {
                "id": pool_id,
                "lineage": "R6 residual",
                "m": bound,
                "frozen": True,
                "members": [dict(member) for member in members],
            },
            "variants": variants,
        }

    def two_utility_rung(self, seeds=(SEED_A, SEED_B), members=(), bound=None,
                         pool_id="pool-r11-dual-utility"):
        """The battery's own two-utility configuration: one architecture, two utilities.

        The sibling of :meth:`two_rule_rung` on D-20's axis.  It appears in no design
        document: its name, its two variant names, its width and depth, its seed set, its
        pool id and the membership declaration it carries are the battery's own
        (``battery.md`` §4).  What it declares is exactly what D-20 makes legal and nothing
        else — two variant entries that agree on ``backend``, ``encoding``,
        ``architecture``, ``learning_rule``, ``hyper``, ``param_budget``, ``samples``,
        ``seeds`` and ``device`` and differ on ``utility`` alone — so a run of it must
        train **both** variants, one on each catalogue utility's reward
        (``utilities.md`` §3, §7, D-20).

        The pool is the baselines alone, as in the two-rule rung: a case that only needs
        the loop to train two utilities pays for no version it does not read
        (``battery.md`` §2).  ``members`` lets a case hand it a real checkpoint it built.
        """
        if bound is None:
            bound = LEAGUE_BOUND
        kind = self.architecture_kind("naive")
        architecture = {
            "kind": kind,
            "width": UTILITY_WIDTH,
            "depth": UTILITY_DEPTH,
            "sparsity": 0.0,
            "residual": False,
        }
        variants = []
        for name, utility in (("chips-arm", UTILITY_DEFAULT),
                              ("shortfall-arm", UTILITY_SECOND)):
            variants.append(
                {
                    "name": name,
                    "backend": "numpy",
                    "encoding": FLAT,
                    "architecture": dict(architecture),
                    "learning_rule": RULE_DEFAULT,
                    "utility": utility,
                    "param_budget": 10000,
                    "samples": BUDGET_TINY,
                    "seeds": list(seeds),
                    "device": "cpu",
                    "table": "live",
                }
            )
        return {
            "name": "R11-dual-utility",
            "axis": "the utility at one architecture",
            "carried_from": "residual",
            "primary": "chips-arm",
            "pool": {
                "id": pool_id,
                "lineage": "R6 residual",
                "m": bound,
                "frozen": True,
                "members": [dict(member) for member in members],
            },
            "variants": variants,
        }

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

    def seated_walk(self, seed=SEED_A, policies=None, limit=240):
        """Drive one hand with **one policy per seat**, through the engine's entry points.

        ``policies`` maps a seat index to the policy that plays it; the acting seat is the
        readout's own ``seat`` fact (``e2e-surface.md`` §2), so one seat can hold a folder
        while the other holds the opponent it is measured against — which is how D-21's
        folders are driven on real decisions (``folders.md`` §2, §6).  Returns
        ``[(seat, readout, legal, action, index)]`` for each decision until the hand is
        terminal.
        """
        engine = self.mod("engine")
        if policies is None:
            policies = {"default": self.baseline("always-call", SEED_D)}
        hand = engine.new_hand(seed)
        walk = []
        while len(walk) < limit and not engine.is_terminal(hand):
            readout = engine.readout(hand)
            legal = engine.legal_actions(hand)
            seat = seat_of(readout)
            policy = policies[seat] if seat in policies else policies["default"]
            action = policy(readout, legal)
            walk.append((seat, readout, legal, action, self.chosen_index(legal, action)))
            hand = engine.apply_action(hand, action)
        return walk

    def folder_walk(self, folder, opponent, seed=SEED_A, seat=0):
        """Every decision one folder makes in one hand, as ``seat``'s policy.

        The folder is built through ``agents.build_baseline`` and every other seat is
        played by ``opponent``'s baseline, so the hand is a real one and the decisions
        returned are the folder's own (``folders.md`` §2, §6).  ``opponent`` is a
        catalogue name: ``always-call`` for the ordinary walks, ``random`` where a case
        needs an opponent that bets, because a folder can fold only where folding is legal
        and a check is not a fold (``folders.md`` §2, ASM-31).

        Returns ``[(readout, legal, action, index)]``, in the order the folder decided.
        """
        policies = {
            seat: self.baseline(folder, SEED_D),
            "default": self.baseline(opponent, SEED_G),
        }
        return [
            (readout, legal, action, index)
            for decided_seat, readout, legal, action, index in self.seated_walk(seed, policies)
            if decided_seat == seat
        ]

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
    def version(self, tag, width=None, depth=None, rule=None, utility=None):
        """One invented version, in the record shape ``records.md`` §7 pins.

        ``e2e-surface.md`` §2 makes a version "a checkpoint of a run, carrying an id,
        the lineage it came from and its path"; ``records.md`` §7 fixes the keys — id,
        path, rung, variant, seed, step, samples and lineage — and D-19 adds ``rule``,
        the catalogue member the version was trained under, which the version's own
        container must agree with.  The checkpoint is written by ``agents.save`` at a
        minimal budget, so no case depends on a shipped artifact (``battery.md`` §2);
        the tag, the lineage values, the samples and the file name are the battery's
        own.  ``width``/``depth`` let a case make two versions differ in capacity, which
        is how a cell's parameter counts become evidence that two memberships were not
        the same pool.  ``rule`` is the rule the learner is built under *and* the rule
        the record declares, so the pair is written consistently unless a case doctors
        the record deliberately.

        ``utility`` is D-20's second required member field on the same terms: the learner
        is built under ``utility`` — so the container records it — and the record declares
        it, defaulting to the catalogue's first member as ``rule`` does, so every caller
        that predates the catalogue keeps the version it built before
        (``utilities.md`` §5, §6, §7).
        """
        spec = VERSIONS[tag]
        if width is None:
            width = VERSION_WIDTH
        if depth is None:
            depth = VERSION_DEPTH
        if rule is None:
            rule = RULE_DEFAULT
        if utility is None:
            utility = UTILITY_DEFAULT
        path = os.path.join(self.scratch(), "version-%s.pt" % tag)
        learner = self.learner(width=width, depth=depth, seed=spec["seed"],
                               learning_rule=rule, utility=utility)
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
            "rule": rule,
            "utility": utility,
        }

    def membership(self, tags=("kestrel",), frozen=True, width=None, depth=None,
                   rule=None, utility=None, baselines=()):
        """An invented pool declaration, in the shape ``records.md`` §8 pins.

        A declaration is ``members`` (the versions, by id and lineage), ``m`` (the
        bound) and ``frozen``; the bound is the league's fixed M, because a pool's bound
        belongs to the one league of D-16 and is not the battery's to choose
        (``league.md`` §2).  ``utility`` is handed to each version, so a membership can
        declare a family trained on one utility's reward (``records.md`` §7, D-20).

        ``baselines`` is §8's **optional** key — the catalogue names a configuration
        admits beyond the flagged three, which is how D-21's folders join a membership
        (``records.md`` §8, ASM-32, D-21).  It is omitted when empty, so a declaration
        that names no folder is exactly the declaration this battery declared before
        D-21 and keeps the membership and the id it had.
        """
        declaration = {
            "members": [self.version(tag, width, depth, rule, utility) for tag in tags],
            "m": LEAGUE_BOUND,
            "frozen": bool(frozen),
        }
        if baselines:
            declaration["baselines"] = list(baselines)
        return declaration

    def pool(self, tags=("kestrel",), frozen=True, width=None, depth=None, rule=None,
             utility=None, baselines=()):
        """A pool through ``evaluation.build_pool`` (``e2e-surface.md`` §3.4).

        ``tags`` is either the invented version tags to declare, or a ready declaration
        in the shape ``records.md`` §8 pins (``members``, ``m``, ``frozen``, and the
        optional ``baselines`` this battery's own declarations add) — a case that brings
        its own lineage, its own snapshots, its own bound or its own declared folders
        hands the declaration over rather than a list of tags, and both routes reach
        ``build_pool`` with a declaration and never with a tag list read back out of one.
        """
        declaration = (
            tags if is_mapping(tags)
            else self.membership(tags, frozen, width, depth, rule, utility, baselines)
        )
        return self.ep("evaluation", "build_pool")(declaration)

    def folders_pool(self):
        """The pool a configuration that declares D-21's three folders builds.

        The flagged three are members whether a declaration names them or not, and the
        declared folders join pinned after them, so this pool is six members and no
        version (``records.md`` §8, `league.md` §2, ASM-32, D-21).
        """
        return self.pool(tags=(), frozen=True, baselines=FOLDER_BASELINES)

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
                # `records.md` §7 marks a version member's rule required (D-19); this row
                # declares the catalogue's default, which is the rule an invented version
                # of the battery's own tag table is trained under (rules.md §4).
                "rule": spec.get("rule") or RULE_DEFAULT,
                # D-20's second required member field, declared on the same terms
                # (records.md §7, §8; utilities.md §5).
                "utility": spec.get("utility") or UTILITY_DEFAULT,
            })
        members += [{"id": name, "baseline": True, "pinned": True}
                    for name in ANCHOR_BASELINES]
        identifier = "pool-" + ("-".join(tags) if tags else "baselines")
        return {"id": identifier, "m": LEAGUE_BOUND, "frozen": True, "members": members}

    def header_family(self, seeds=(SEED_A,), budget=BUDGET_TINY, device="cpu",
                      cell_hands=LIVE_CELL_HANDS, table_seed=None, record=None):
        """The header family: everything a third party needs to re-run the table.

        ``protocol.md`` §1: the game configuration, the action vocabulary, the
        parameter counts of every member, the sample budget, the cell size, the seed
        set, the table seed, the device and the checkpoint paths.
        """
        counts = {name: 0 for name in ANCHOR_BASELINES}
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
            # `protocol.md` §1: every baseline row of the catalogue **the run's
            # configuration declares** inside the matrix — always D-6's three, and D-21's
            # folders only where a membership declaration names them.  The records the
            # battery completes here declare no folder, so their row list is the flagged
            # three (`records.md` §8, ASM-32, D-21).
            record["baselines"] = {
                "rows": [{"member": name, "hand count": cell_hands}
                         for name in ANCHOR_BASELINES]
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
