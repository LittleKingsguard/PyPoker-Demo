"""The pairwise matrix: `matrix` (`docs/L3/evaluation/matrix.md`).

`matrix(pool, variants, table)` plays one round robin over **the frozen pool's members
plus the rung's variants**: ``K = |pool| + V`` with `V` one or two, so `K` is 4 for R1, 9
for a one-variant rung with a full window and 10 for a two-variant rung (`league.md` §3).
The membership is the pool's order and then `variant-1`, `variant-2` by argument
position, whatever a variant carries; the cells are exactly the `K(K-1)/2` unordered
pairs, enumerated lexicographically by membership position and played in that order, one
to completion before the next begins (`matrix.md` §1-§2).

**The table's shape is the pool's**, and `matrix` takes no shape argument: the pool carries
the one shape every member of it plays, so the table is played on that shape -- every hand
of every cell dealt on it through ``_play_cell`` -- and its record states it.  A variant may
name that shape or none -- naming **another** one is refused naming the variant's slot and
both shapes, because a table is measured on one shape and no row of it is a second game
(`matrix.md` §1, §4-§5, `shape.md` §3-§4, `docs/L1/shapes.md` §6).

`matrix` takes no seed: the table seed is `declarations.TABLE_SEED`, and both derivations
come from it through `seeds.py`'s one digest -- a cell's seed from the table seed and the
pair, a baseline's policy seed from the table seed and its position.  A version member is
built at the seed its **checkpoint** records, because one checkpoint is one player
(`matrix.md` §3-§4, G14).  A membership is **distinct**: an id the table would carry twice
is `MemberDuplicate` before a member policy exists (`matrix.md` §1, §7).

Every member carries its rule, its utility and its shape, so the record carries `rules`,
`utilities` and `game` -- each member's rule and utility by its id, `None` for a baseline
-- and `population` and `utility_population`, the distinct rules and the distinct utilities
those members declared, sorted: the two populations this table measured (`matrix.md` §5,
`records.md` §10, D-19, D-20).

**A matrix is two seats'.**  A cell is a pair and the rating is fitted over pairs, so
`matrix` refuses a pool on a shape whose seat count is above the instrument's, naming the
shape and its seat count, before a variant is looked at and before a checkpoint is touched
(`docs/L1/seats.md` §5, `league.md` §4, D-22, D-33).  The seat count is `engine.game_config`'s
and never a literal, and the two-seat shapes pass untouched, so no cell, matrix, rating or
report they produce today moves (`seats.md` §5, D-33).
"""

from .declarations import (
    TABLE_SEED,
    TABLES,
    TABLE_BUDGETS,
    require_pairwise,
    require_shape,
)
from .errors import (
    InvalidPool,
    MemberDuplicate,
    PoolNotFrozen,
    ShapeMismatch,
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


def _variant_shape(variant, slot, shape, entry="matrix"):
    """A variant's own `game`, held to the table's shape (`matrix.md` §1, §7).

    A variant is the rung's own policy, so it **may** name the table's shape or none: one
    that names none -- an opaque callable, a `_MemberPolicy` built for a run that named no
    shape -- is shape-silent and plays the pool's shape.  Naming **another** one is
    `ShapeMismatch`, naming the variant's slot (`variant-1`, `variant-2`) and both shapes,
    because a table is measured on one shape; a name the catalogue does not carry is
    `UnknownShape` naming the slot, the name and the declared names (`shape.md` §2-§3,
    `matrix.md` §7, `docs/L1/shapes.md` §6).
    """
    declared = getattr(variant, "game", None)
    if declared is None:
        return None
    game = require_shape(declared, entry, slot)
    if game != shape:
        raise ShapeMismatch(
            "%s(%s): the variant records the shape %r and the table is %r"
            % (entry, slot, game, shape)
        )
    return game


def _membership(pool, variants, shape):
    """The ordered membership, its records and the resolved side of every member (§1, §4).

    The pool's members come first, in `pool_members`'s order -- each resolved once and
    reused for every cell it appears in, so one member is one player throughout a table --
    and then the variants, named by the slot they were handed in.  Each member's record
    carries the rule, the utility and the shape its policy carries, so the table says which
    estimators, which objectives and which game its rows are (`matrix.md` §5,
    `records.md` §10, D-19, D-20, `shape.md` §4).  A variant of another shape is refused
    first (`ShapeMismatch`, §7), then the ids are fixed before any policy is built, so a
    membership naming one id twice is refused before a checkpoint is touched (§1, §7).
    """
    slots = ["variant-%d" % (offset + 1,) for offset in range(len(variants))]
    variant_games = []
    for slot, variant in zip(slots, variants):
        variant_games.append(_variant_shape(variant, slot, shape))

    record = pool_members(pool)
    ids = [member["id"] for member in record["members"]]
    ids.extend(slots)
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
            # A baseline is shape-silent: its `game` is `None`, and its rule and utility
            # are `None` too, being a fixed policy (`matrix.md` §5, `shape.md` §4).
            member_records.append(
                {
                    "id": name,
                    "baseline": True,
                    "pinned": True,
                    "params": 0,
                    "rule": side[4],
                    "utility": side[5],
                    "game": side[6],
                }
            )
        else:
            side = _side(dict(member), None, "matrix", position=position + 1)
            member_records.append(
                dict(member, rule=side[4], utility=side[5], game=side[6])
            )
        sides.append(side)
    for offset, variant in enumerate(variants):
        name = slots[offset]
        game = variant_games[offset]
        if isinstance(variant, _MemberPolicy):
            side = (
                name,
                variant,
                variant.params,
                variant.unlabelled,
                variant.learning_rule,
                variant.utility,
                game,
            )
            member_records.append(
                {
                    "id": name,
                    "params": int(variant.params),
                    "unlabelled": bool(variant.unlabelled),
                    "rule": variant.learning_rule,
                    "utility": variant.utility,
                    "game": game,
                }
            )
        else:
            side = (
                name,
                variant,
                0,
                True,
                getattr(variant, "learning_rule", None),
                getattr(variant, "utility", None),
                game,
            )
            member_records.append(
                {
                    "id": name,
                    "params": 0,
                    "unlabelled": True,
                    "rule": side[4],
                    "utility": side[5],
                    "game": game,
                }
            )
        sides.append(side)
    return tuple(ids), tuple(member_records), tuple(sides)


def matrix(pool, variants, table):
    """One `records.md` §10 matrix at one budget over one frozen pool (`surface.md` §10).

    Every refusal is raised before the first cell is played -- an unfrozen pool is
    reported before a single checkpoint is touched, a pool on a shape with more seats than
    a pair has before a variant is looked at, a variant of another shape before a row
    exists, a membership naming one id twice before a member policy is built, and a table
    over a version whose recorded facts are missing before a hand is dealt (`matrix.md`
    §1, §7, `docs/L1/seats.md` §5, D-33).  The matrix is reported raw: both directions of
    every cell, its counts, its chip deltas and its seat split, and it is never reduced to
    a ranking (`league.md` §3).  Its shape is the **pool's** and it takes no shape argument
    (`matrix.md` §1, §3).
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
    # The table's shape is the pool's: the one shape every member of it plays, which the
    # pool record states (`matrix.md` §1, §5, `pool.md` §5, `shape.md` §4).  A shape whose
    # seat count is not the instrument's is refused **here**, before a variant is looked
    # at and before a single checkpoint is touched, because a cell is a pair and a
    # six-way hand is a placement for which no permutation model is designed
    # (`docs/L1/seats.md` §5, `league.md` §4, D-22, D-33).
    shape = pool_members(pool)["game"]
    require_pairwise(shape, "matrix", "pool")
    policies = _variant_list(variants)
    for offset, variant in enumerate(policies):
        if not callable(variant):
            raise VariantInvalid(
                "matrix(variant %d): the variant must be a policy in the sense of "
                "surface.md §2, got %r" % (offset + 1, variant)
            )

    # The table's shape is the pool's, and it was resolved and held to the instrument's
    # seat count above: `_membership` builds the rows on it (`matrix.md` §1, §5).
    hands = int(TABLES[table]["hands_per_cell"])
    ids, member_records, sides = _membership(pool, policies, shape)
    cells = []
    for i, j in _pairs(len(ids)):
        cell_seed = _cell_seed(TABLE_SEED, i, j)
        # Every cell is played -- and every hand of it dealt -- on the table's one shape,
        # which `_play_cell` hands to `engine.play_hand`, so no row of a table is a second
        # game (`matrix.md` §1, §4-§5, `shape.md` §4).
        cells.append(_play_cell(sides[i], sides[j], hands, cell_seed, shape))

    unlabelled = tuple(side[0] for side in sides if side[3])
    rules = {side[0]: side[4] for side in sides}
    population = tuple(sorted({rule for rule in rules.values() if rule is not None}))
    utilities = {side[0]: side[5] for side in sides}
    utility_population = tuple(
        sorted({utility for utility in utilities.values() if utility is not None})
    )
    return {
        "members": tuple(ids),
        "cells": tuple(cells),
        "rules": rules,
        "population": population,
        "utilities": utilities,
        "utility_population": utility_population,
        "hands_per_cell": hands,
        "table_seed": TABLE_SEED,
        "table": table,
        # This module's own key, **required** of what `matrix` returns: the one shape the
        # table was played on, so no reader infers it (`matrix.md` §5, `shape.md` §4).
        "game": shape,
        "pool": pool.id,
        "member_records": tuple(member_records),
        "unlabelled": unlabelled,
        "cell_count": len(ids) * (len(ids) - 1) // 2,
    }
