"""The registry: six rows resolved into six configurations (D-3, ladder.md §2, §3).

Resolving is not training: it builds no learner, plays no hand, writes nothing and moves
no stream. It does read the shipped window, because a rung's `pool` entry has to declare
the id the run record will carry, and that id is the read-back id of the membership the
repository actually carries (`docs/L2/training/surface.md` §3, protocol.md §5).
"""

import copy
import os

import evaluation

from . import declarations, errors, index

#: The six rung names, in brief §2's order: one read, one order (`rungs()`, D-2).
RUNG_NAMES = declarations.RUNG_NAMES


def _window(carried_from):
    """The version records of one primary variant's retained window that are present.

    A declared version the repository does not carry is not a member: the pool holds what
    is present and the record states the membership it used, because a pool never pretends
    a version it could not load (protocol.md §5, docs/L3/training/registry.md §3).
    """
    members = []
    for member in index._window_members(carried_from):
        path = member.get("path")
        if path and os.path.isfile(str(path)):
            members.append(dict(member))
    return members


def _pool_entry(name, carried_from):
    """One rung's `pool` entry: the id it trains under, its bound, and its membership."""
    del name  # the rung name is the entry's context, not one of its fields
    members = _window(carried_from) if carried_from else []
    built = evaluation.build_pool(
        {"members": members, "m": declarations.LEAGUE_M, "frozen": True}
    )
    record = evaluation.pool_members(built)
    return {
        "id": record["id"],
        "lineage": carried_from,
        "m": declarations.LEAGUE_M,
        "frozen": True,
        "members": members,
    }


def _configuration(name):
    """One rung name as `ladder.md` §3's resolved configuration."""
    row = declarations.ROWS[name]
    variants = copy.deepcopy(list(row["variants"]))
    for entry in variants:
        declarations.check_variant(entry, "rung %r" % (name,))
    return {
        "name": row["name"],
        "axis": row["axis"],
        "carried_from": row["carried_from"],
        "primary": row["primary"],
        "variants": variants,
        "pool": _pool_entry(row["name"], row["carried_from"]),
        "seeds": list(declarations.SEEDS),
        "samples": declarations.LIVE_BUDGET,
        "param_budget": declarations.PARAM_BUDGET,
        "table": declarations.TABLE,
        "device": declarations.DEVICE,
        "snapshot_every": declarations.LIVE_BUDGET // declarations.SNAPSHOTS,
    }


def rungs():
    """The six rung declarations, in brief §2's fixed order (D-2, D-3)."""
    return {name: rung(name) for name in declarations.RUNG_NAMES}


def rung(name):
    """One resolved configuration, or a refusal naming the rung the registry does not carry."""
    if not isinstance(name, str) or name not in declarations.ROWS:
        raise errors.UnknownRung(
            "training.rung refused the rung name %r: the registry carries %s"
            % (name, ", ".join(declarations.RUNG_NAMES))
        )
    return _configuration(name)
