"""The two declarations and the league's constants
(`docs/L3/evaluation/declarations.md`, `surface.md` §3-§4).

`protocol()` is the evidence contract a report is judged against and `league()` the
league's parameters; both are `fixed` rows -- neither takes an argument, both are
rebuilt on every call and equal on two calls, and neither plays a hand, reads a file or
moves Python's global `random` stream.  The numbers are `docs/L1/league.md` §5-§6's and
no others (ASM-14, ASM-21).

`M`, `BASELINES`, `TABLE_SEED`, `TABLES`, `FAMILIES`, `HEADER_ITEMS`, `RATING` and
`cell_count` live here (`README.md` §4) and are *not* package-level surface names
(`e2e-surface.md` §1, D-12).  The game **shape**'s constants and the two validators this
edge reads a shape name and an exploration mode with live here too -- `SHAPE_NAMES`,
`DEFAULT_SHAPE`, `EXPLORATION_MODES`, `EXPLORATION_DEFAULT`, `PROBE_SEED`,
`require_shape` and `require_exploration` (`shape.md` §1-§2, §5, D-29).
"""

import numbers
from collections.abc import Mapping

import agents

from .errors import InvalidMembership, UnknownExploration, UnknownShape

#: M, the window's bound: a pool holds at most this many versions plus the catalogue's
#: pinned baselines (`league.md` §2, §4, ASM-14, ASM-33).
M = 5

#: The catalogue as `agents.baselines()` declares it: read once here, so the names below
#: and their `anchor` flags come from the catalogue and never from a copy of it
#: (`module-map.md` §2, D-13, ASM-32).
_DECLARED = agents.baselines()

#: The catalogue's six names, in `agents.baselines()`'s order (D-6, D-21,
#: `agents/surface.md` §11); a baseline's id is its name (`pool.md` §2 step 5).  This is
#: the names a membership declaration may add beyond the pinned set (`records.md` §8).
CATALOGUE = tuple(_DECLARED)

#: The pinned set: the catalogue's `anchor: True` members — the three baselines of D-6 —
#: read off the catalogue's own flag and never copied as a literal list.  They are
#: members of every pool, and they are the rating's anchor; a folding baseline D-21 adds
#: is neither (`protocol.md` §3, `league.md` §5, ASM-32, `folders.md` §4).
BASELINES = tuple(name for name in CATALOGUE if _DECLARED[name].get("anchor"))

#: The two declared game shapes' names, in the catalogue's order -- default first
#: (`docs/L1/shapes.md` §1-§2, `shape.md` §1, D-29).  Only the names and their order are
#: restated: `module-map.md` §2 grants this module neither `engine.game_shapes` nor
#: `engine.game_config`, so the arrow it holds is a cell's hands and nothing else (D-13).
#: The restatement is **deliberate and not a second catalogue**: the join battery
#: (`tests/integration/evaluation/`) holds `SHAPE_NAMES` equal, in that order, to the
#: names `engine.game_shapes()` publishes, and `EXPLORATION_MODES` equal to the set
#: `agents.as_policy` accepts -- the same restatement `agents` and `features` make at
#: their own edges, so a restatement that drifts is a red join case and never a silent
#: catalogue of its own (`shape.md` §1, `docs/L1/e2e-surface.md` §3.1).
SHAPE_NAMES = ("fixed-limit-20", "no-limit-100")

#: The declared default shape: what an **absent** `game` reads as, everywhere -- a pool
#: declaration, a member record, an offered version, a cell, a matrix, a rating, a
#: report's three records and a version-1-to-3 container alike (`shape.md` §2).  Absence
#: is the default and never a defaulting of a present name: a name the catalogue does not
#: carry is `UnknownShape` and is never mapped onto this (`shape.md` §2-§3).
DEFAULT_SHAPE = SHAPE_NAMES[0]

#: The two exploration modes `policy_from` accepts, the default first (`shape.md` §5):
#: `schedule` is the keyed draw of the exploration schedule `agents.as_policy` makes, and
#: `off` is the masked maximum and the tie-break alone, with **no generator drawn from**
#: (`docs/L1/sizing.md` §4, §7, D-29).
EXPLORATION_MODES = ("schedule", "off")

#: The default mode: absence is today's behaviour, so a caller that names none gets
#: exactly the policy it got before the argument existed (`shape.md` §5).
EXPLORATION_DEFAULT = EXPLORATION_MODES[0]

#: The seed a pinned baseline's probe is built at -- a **construction** only, with no hand
#: played, no file read and no stream moved (`pool.md` §2, ASM-2).
PROBE_SEED = 0

#: The league's one table seed -- the design revision's own date, so the number is
#: recognisable as the league's and is no battery instance (`declarations.md` §6).
TABLE_SEED = 20261105

#: `league()["tables"]`, keyed `live` then `full` (`declarations.md` §4.1).  Each row
#: carries the one hand count of every cell, the hands a table of K members plays and what
#: produces it -- and no per-hand cost figure at all.  ASM-21 ratifies the measured cost
#: (0.105-0.130 s/hand) and supersedes ASM-15's 40 ms bound, so a bound carried here would
#: be a number with no ratified source; a measured cost lives in a run record's `timings`
#: and in the shipped artefact's cost block (`declarations.md` §4.1, `tables.md` §5).
TABLES = {
    "live": {
        "hands_per_cell": 120,
        "hands_played": {4: 720, 9: 4320, 10: 5400},
        "produced_by": "the talk, on the fly",
    },
    "full": {
        "hands_per_cell": 1500,
        "hands_played": {4: 9000, 9: 54000, 10: 67500},
        "produced_by": "an offline job shipped under tables/",
    },
}

#: The seven evidence families, in `protocol.md` §1's order (`declarations.md` §3).
FAMILIES = ("curves", "pool", "matrix", "rating", "baselines", "axis row", "header")

#: The nine header items, in `declarations.md` §2.1's order (`protocol.md` §1).
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

#: The two table budgets, in `records.md` §10's order.
TABLE_BUDGETS = ("live", "full")

#: The fixed seed set (`protocol.md` §2).
SEED_SET = (0, 1, 2)

#: The rating row: the method, the interval's level and the anchor -- one value, equal
#: in `protocol()` and in `league()` (`declarations.md` §2.2, ASM-17).  The anchor names
#: the **flagged three** it zeroes the fit on, spelled from the catalogue's own pinned
#: set, so a reader is told which baselines the scale is relative to and a folder is
#: never among them (ASM-32, `folders.md` §4, D-21).
RATING = {
    "method": "Bradley-Terry",
    "confidence": 0.95,
    "anchor": "the mean of the three anchor baselines fixed at 0 — %s"
    % (", ".join(BASELINES),),
}

#: One record per family: the content items its value must carry and the exact word a
#: report refuses its absence with (`declarations.md` §3, D-6).
_FAMILY_RECORDS = {
    "curves": ("samples", "signal", "spread"),
    "pool": ("id", "m", "frozen", "members"),
    "matrix": ("members", "cells", "hands_per_cell", "table_seed", "table"),
    "rating": ("values", "method", "anchor", "bound_applied", "bootstrap_seed", "converged"),
    "baselines": ("rows",),
    "axis row": ("value",),
    "header": HEADER_ITEMS,
}


def require_shape(value, entry, argument="game"):
    """The shape name `value` denotes, or `UnknownShape` naming it and the declared names.

    `None` is the **default** shape, and that is the absence of a name rather than a
    defaulting of one: a field that says nothing is read as `DEFAULT_SHAPE`, while a name
    the restated catalogue does not carry -- a non-string included -- is refused naming
    the entry point, the field, the value and `SHAPE_NAMES`, and is never substituted
    (`shape.md` §2-§3, `errors.md` §3-§4, D-29, D-13).  Every entry point of this module
    that reads a `game` reads it through here, so the two contracts stay one rule.
    """
    if value is None:
        return DEFAULT_SHAPE
    for name in SHAPE_NAMES:
        if isinstance(value, str) and value == name:
            return name
    raise UnknownShape(
        "%s(%s): the shape %r is not one of the declared shapes %r"
        % (entry, argument, value, SHAPE_NAMES)
    )


def require_exploration(value, entry):
    """The exploration mode `value` names, or `UnknownExploration` naming both modes.

    There is no absence to read: `policy_from`'s second argument is the declared default
    `schedule` when the caller passes none, so a value outside the two modes is a value
    the caller wrote -- a non-string included -- and is refused naming the entry point,
    the mode and `EXPLORATION_MODES` (`shape.md` §5, `errors.md` §3-§4, D-29).
    """
    for mode in EXPLORATION_MODES:
        if isinstance(value, str) and value == mode:
            return mode
    raise UnknownExploration(
        "%s(exploration): the mode must be %r or %r, got %r"
        % (entry, EXPLORATION_MODES[0], EXPLORATION_MODES[1], value)
    )


def cell_count(value):
    """`K(K-1)/2` -- the cells a membership of `K` members has (`declarations.md` §5).

    Three shapes are accepted and the rest refused with `InvalidMembership`: an integer
    `K` of at least 2, a membership sequence, and a mapping carrying `members`.  A talk
    sizes its table before it plays one, so this is the one callable `league()` carries.
    """
    if isinstance(value, bool):
        raise InvalidMembership(
            "cell_count(K): the bound must be an integer of at least 2, a members "
            "mapping or a sequence, got %r" % (value,)
        )
    if isinstance(value, numbers.Integral):
        size = int(value)
    elif isinstance(value, (str, bytes)):
        raise InvalidMembership(
            "cell_count(K): the bound must be an integer of at least 2, a members "
            "mapping or a sequence, got %r" % (value,)
        )
    elif isinstance(value, Mapping):
        if "members" not in value:
            raise InvalidMembership(
                "cell_count(K): a members mapping must carry 'members', got %r" % (value,)
            )
        inner = value["members"]
        if isinstance(inner, (str, bytes)) or not hasattr(inner, "__len__"):
            raise InvalidMembership(
                "cell_count(K): the 'members' entry must be a sequence of members, got %r"
                % (inner,)
            )
        size = len(inner)
    elif isinstance(value, (list, tuple)) or (
        hasattr(value, "__len__") and hasattr(value, "__iter__")
    ):
        size = len(value)
    else:
        raise InvalidMembership(
            "cell_count(K): the bound must be an integer of at least 2, a members "
            "mapping or a sequence, got %r" % (value,)
        )
    if size < 2:
        raise InvalidMembership(
            "cell_count(K): the bound must be an integer of at least 2, a members "
            "mapping or a sequence, got %r" % (value,)
        )
    return size * (size - 1) // 2


def protocol():
    """The evidence contract: the seven families, the seeds, the header and the rest.

    One mapping read under exactly six keys, in `declarations.md` §2's order; plain
    data (except `league()`'s one callable), rebuilt on every call, playing nothing and
    moving no stream (`surface.md` §3).
    """
    families = {}
    for name in FAMILIES:
        families[name] = {
            "required": tuple(_FAMILY_RECORDS[name]),
            "refusal": name,
        }
    return {
        "families": families,
        "seeds": tuple(SEED_SET),
        "header": tuple(HEADER_ITEMS),
        "table_budgets": tuple(TABLE_BUDGETS),
        "baselines": tuple(BASELINES),
        "rating": dict(RATING),
    }


def league():
    """The league's parameters: M, the baselines, the catalogue, the budgets, `cell_count`.

    One mapping read under exactly seven keys, in `declarations.md` §4's order: `m`, the
    **pinned** `baselines` (the flagged three), `catalogue` (the six names a membership
    declaration may add beyond them), `tables`, `cell_count`, `table_seed` and `rating`.
    It carries **no per-hand cost figure**: ASM-21 ratifies the measured cost and
    supersedes ASM-15's 40 ms bound, so what this declares is the budget's arithmetic on K
    and nothing a stopwatch produced -- a measured cost lives in a run record's `timings`
    and in the shipped artefact's cost block (`tables.md` §5, G19, D-21).
    """
    tables = {}
    for budget in TABLE_BUDGETS:
        row = TABLES[budget]
        tables[budget] = {
            "hands_per_cell": int(row["hands_per_cell"]),
            "hands_played": dict(row["hands_played"]),
            "produced_by": row["produced_by"],
        }
    return {
        "m": M,
        "baselines": tuple(BASELINES),
        "catalogue": tuple(CATALOGUE),
        "tables": tables,
        "cell_count": cell_count,
        "table_seed": TABLE_SEED,
        "rating": dict(RATING),
    }
