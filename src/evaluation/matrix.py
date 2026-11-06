"""The pairwise matrix: `matrix` (`docs/L3/evaluation/matrix.md`).

`matrix(pool, variants, table)` plays one round robin over **the frozen pool's members
plus the rung's variants**: ``K = |pool| + V`` with `V` one or two, so `K` is 4 for R1, 9
for a one-variant rung with a full window and 10 for a two-variant rung (`league.md` §3).
The membership is the pool's order and then `variant-1`, `variant-2` by argument
position, whatever a variant carries; the cells are exactly the `K(K-1)/2` unordered
pairs, enumerated lexicographically by membership position and played in that order, one
to completion before the next begins (`matrix.md` §1-§2).

`matrix` takes no seed: the table seed is `declarations.TABLE_SEED`, and both derivations
come from it through `seeds.py`'s one digest -- a cell's seed from the table seed and the
pair, a baseline's policy seed from the table seed and its position.  A version member is
built at the seed its **checkpoint** records, because one checkpoint is one player
(`matrix.md` §3-§4, G14).  A membership is **distinct**: an id the table would carry twice
is `MemberDuplicate` before a member policy exists (`matrix.md` §1, §7).
"""

from .declarations import TABLE_SEED, TABLES, TABLE_BUDGETS
from .errors import (
    InvalidPool,
    MemberDuplicate,
    PoolNotFrozen,
    UnknownTable,
    VariantCountInvalid,
    VariantInvalid,
)
from .policy import _MemberPolicy, _side
from .pool import Pool, pool_members
from .scheduler import _play_cell
from .seeds import _cell_seed, _member_seed


def _pairs(k):
    """The ``K(K-1)/2`` unordered pairs, lexicographically (`matrix.md` §2, G12)."""
    for i in range(k):
        for j in range(i + 1, k):
            yield (i, j)


def _variant_list(variants):
    """The rung's variant policies, one or two (`matrix.md` §7, `ladder.md` §2)."""
    if (
        isinstance(variants, (str, bytes))
        or not hasattr(variants, "__len__")
        or not hasattr(variants, "__iter__")
    ):
        raise VariantCountInvalid(
            "matrix(variants): the variant count must be 1 or 2, got %r" % (variants,)
        )
    ordered = list(variants)
    if len(ordered) not in (1, 2):
        raise VariantCountInvalid(
            "matrix(variants): the variant count must be 1 or 2, got %d" % (len(ordered),)
        )
    return ordered


def _membership(pool, variants):
    """The ordered membership, its records and the resolved side of every member (§1, §4).

    The pool's members come first, in `pool_members`'s order -- each resolved once and
    reused for every cell it appears in, so one member is one player throughout a table --
    and then the variants, named by the slot they were handed in.  The ids are fixed
    before any policy is built, so a membership naming one id twice is refused before a
    checkpoint is touched (`matrix.md` §1, §7).
    """
    record = pool_members(pool)
    ids = [member["id"] for member in record["members"]]
    ids.extend("variant-%d" % (offset + 1,) for offset in range(len(variants)))
    # `matrix.md` §7's guard: a cell pairs two **distinct** members, so an id the
    # membership carries twice -- a declared version named `variant-1` colliding with the
    # first variant's slot label -- is refused before a member policy exists.
    seen = set()
    for name in ids:
        if name in seen:
            raise MemberDuplicate(
                "matrix(members): %r is the id of two members of the table, and a cell "
                "pairs two distinct members" % (name,)
            )
        seen.add(name)

    member_records = []
    sides = []
    for position, member in enumerate(record["members"]):
        name = member["id"]
        if member.get("baseline"):
            side = _side(
                name, name, "matrix", seed=_member_seed(TABLE_SEED, position)
            )
            member_records.append(
                {"id": name, "baseline": True, "pinned": True, "params": 0}
            )
        else:
            side = _side(dict(member), None, "matrix", position=position + 1)
            member_records.append(dict(member))
        sides.append(side)
    for offset, variant in enumerate(variants):
        name = "variant-%d" % (offset + 1,)
        if isinstance(variant, _MemberPolicy):
            side = (name, variant, variant.params, variant.unlabelled)
            member_records.append(
                {
                    "id": name,
                    "params": int(variant.params),
                    "unlabelled": bool(variant.unlabelled),
                }
            )
        else:
            side = (name, variant, 0, True)
            member_records.append({"id": name, "params": 0, "unlabelled": True})
        sides.append(side)
    return tuple(ids), tuple(member_records), tuple(sides)


def matrix(pool, variants, table):
    """One `records.md` §10 matrix at one budget over one frozen pool (`surface.md` §10).

    Every refusal is raised before the first cell is played -- an unfrozen pool is
    reported before a single checkpoint is touched, a membership naming one id twice is
    refused before a member policy is built, and a table over a version whose recorded
    facts are missing is refused before a hand is dealt (`matrix.md` §1, §7).  The
    matrix is reported raw: both directions of every cell, its counts, its chip deltas and
    its seat split, and it is never reduced to a ranking (`league.md` §3).
    """
    if not isinstance(pool, Pool):
        raise InvalidPool(
            "matrix(pool): the argument must be a pool from build_pool or offer, got %s"
            % (type(pool).__name__,)
        )
    if not pool.frozen:
        raise PoolNotFrozen(
            "matrix(pool): the pool is not frozen, and a pool does not change while it "
            "is tabled"
        )
    if not isinstance(table, str) or table not in TABLE_BUDGETS:
        raise UnknownTable(
            "matrix(table): the table label must be 'live' or 'full', got %r" % (table,)
        )
    policies = _variant_list(variants)
    for offset, variant in enumerate(policies):
        if not callable(variant):
            raise VariantInvalid(
                "matrix(variant %d): the variant must be a policy in the sense of "
                "surface.md §2, got %r" % (offset + 1, variant)
            )

    hands = int(TABLES[table]["hands_per_cell"])
    ids, member_records, sides = _membership(pool, policies)
    cells = []
    for i, j in _pairs(len(ids)):
        cell_seed = _cell_seed(TABLE_SEED, i, j)
        cells.append(_play_cell(sides[i], sides[j], hands, cell_seed))

    unlabelled = tuple(side[0] for side in sides if side[3])
    return {
        "members": tuple(ids),
        "cells": tuple(cells),
        "hands_per_cell": hands,
        "table_seed": TABLE_SEED,
        "table": table,
        "pool": pool.id,
        "member_records": tuple(member_records),
        "unlabelled": unlabelled,
        "cell_count": len(ids) * (len(ids) - 1) // 2,
    }
