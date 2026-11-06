"""The two declarations and the league's constants
(`docs/L3/evaluation/declarations.md`, `surface.md` §3-§4).

`protocol()` is the evidence contract a report is judged against and `league()` the
league's parameters; both are `fixed` rows -- neither takes an argument, both are
rebuilt on every call and equal on two calls, and neither plays a hand, reads a file or
moves Python's global `random` stream.  The numbers are `docs/L1/league.md` §5-§6's and
no others (ASM-14, ASM-21).

`M`, `BASELINES`, `TABLE_SEED`, `TABLES`, `FAMILIES`, `HEADER_ITEMS`, `RATING` and
`cell_count` live here (`README.md` §4) and are *not* package-level surface names
(`e2e-surface.md` §1, D-12).
"""

import numbers
from collections.abc import Mapping

import agents

from .errors import InvalidMembership

#: M, the window's bound: a pool holds at most this many versions plus the three
#: pinned baselines (`league.md` §2, ASM-14).
M = 5

#: The three pinned baselines, in `agents.baselines()`'s order (D-6, `agents/surface.md`
#: §11); a baseline's id is its name (`pool.md` §2 step 5).
BASELINES = tuple(agents.baselines())

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
#: in `protocol()` and in `league()` (`declarations.md` §2.2, ASM-17).
RATING = {
    "method": "Bradley-Terry",
    "confidence": 0.95,
    "anchor": "the three baselines' mean fixed at 0",
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
    """The league's parameters: M, the baselines, the two budgets, `cell_count`, the seed.

    One mapping read under exactly six keys, in `declarations.md` §4's order.  It carries
    **no per-hand cost figure**: ASM-21 ratifies the measured cost and supersedes
    ASM-15's 40 ms bound, so what this declares is the budget's arithmetic on K and
    nothing a stopwatch produced -- a measured cost lives in a run record's `timings`
    and in the shipped artefact's cost block (`tables.md` §5, G19).
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
        "tables": tables,
        "cell_count": cell_count,
        "table_seed": TABLE_SEED,
        "rating": dict(RATING),
    }
