"""The fitted rating: `rating` (`docs/L3/evaluation/rating.md`).

The rating is Bradley-Terry, fitted over the matrix's cells on each cell's win/tie/loss
counts with **a tie counted as half a win to each side** (ASM-17, D-16).  It is anchored
by the three baselines, whose mean value is fixed at 0, so every value reads as a
distance from the only fixed standard in the table; each member carries a 95% interval
from a hand-level bootstrap seeded from the table seed; and a member with no finite
maximum-likelihood value is held at the bound rather than reported as an infinity
(`rating.md` §1-§5).

It is fitted over **one shape's cells**: a rating reads as a distance from the baselines
*in that game*, so two shapes' ratings are not on one scale and are never tabulated
together.  The matrix's own `game` and each cell's are read **tolerantly** -- an absent one
reads as the default, which is what keeps every table and every rating already recorded
ratable -- and a matrix whose cells name more than one shape, or whose own `game` is not
the shape its cells name, is refused naming the shapes (`rating.md` §1, §6, `shape.md` §3).
The shape enters the fit in **no other way**: the arithmetic reads counts and never a game
parameter, a rule or a utility.

It is a statement about the table's named members on this game at this cell size and
**never a claim of poker skill** (`league.md` §8, D-16).  It plays no hand, reads no file
and leaves Python's global `random` stream where it found it: the bootstrap draws from
its own NumPy generator (`rating.md` §4, `surface.md` §1).

**A rating is fitted over pairs, so a table on a shape with more than two seats is
refused** naming the shape and its seat count, after the record's one shape is resolved
and before a value is fitted (`docs/L1/seats.md` §5, `league.md` §4, D-22, D-33).  The
count comes from `engine.game_config` and never from a literal; the two-seat shapes are
unaffected and every rating they produce today is the rating they produce after it
(`seats.md` §5, D-33).
"""

import math
import numbers
from collections.abc import Mapping

from numpy.random import PCG64, Generator

from .declarations import BASELINES, DEFAULT_SHAPE, RATING, require_pairwise, require_shape
from .errors import (
    CellCountMismatch,
    DuplicatePair,
    ForeignMember,
    InvalidMatrix,
    MissingBaseline,
    MissingMatrixKey,
    ShapeMismatch,
    UnevenCell,
)
from .seeds import _bootstrap_seed

#: The largest ``|theta|`` the fit may return, in log-strength (a 22,026:1 win ratio).
BOUND = 10.0

#: The largest ``|delta theta|`` a step may move and still count as converged.
TOLERANCE = 1e-10

#: The cap; reaching it is what ``converged`` false means.
MAX_ITERATIONS = 10_000

#: The bootstrap's replicates, one multinomial draw per cell for each (`rating.md` §4).
RESAMPLES = 200

#: The interval's two percentile levels (`rating.md` §4).
LOWER_PERCENTILE = 2.5
UPPER_PERCENTILE = 97.5


def _token(text):
    """A key reduced to its letters and digits."""
    return "".join(ch for ch in str(text).lower() if ch.isalnum())


def _is_int(value):
    """An integer, a NumPy integer included, but never a `bool` (`errors.md` §5)."""
    return isinstance(value, numbers.Integral) and not isinstance(value, bool)


# ---------------------------------------------------------------------------
# Reading the record: a matrix that is not a table is refused (`rating.md` §6)
# ---------------------------------------------------------------------------
def _member_ids(raw, entry):
    """The ordered member ids of a matrix's `members` container, whatever holds them."""
    if isinstance(raw, Mapping):
        entries = list(raw.values())
    elif isinstance(raw, (str, bytes)) or not hasattr(raw, "__iter__"):
        raise InvalidMatrix(
            "%s(members): the membership must be a sequence or a mapping a reader can "
            "walk, got %r" % (entry, raw)
        )
    else:
        entries = list(raw)
    ids = []
    for entry_value in entries:
        if isinstance(entry_value, str):
            ids.append(entry_value)
        elif isinstance(entry_value, Mapping):
            found = None
            for key, value in entry_value.items():
                if _token(key) in ("id", "memberid", "member", "name") and isinstance(
                    value, str
                ):
                    found = value
                    break
            if found is None:
                raise InvalidMatrix(
                    "%s(members): a member entry names its id at its own record, got %r"
                    % (entry, entry_value)
                )
            ids.append(found)
        else:
            raise InvalidMatrix(
                "%s(members): a member is named by an id string or a record carrying "
                "one, got %r" % (entry, entry_value)
            )
    return tuple(ids)


def _cells(raw, entry):
    """The matrix's cells, in the order the record states them."""
    if isinstance(raw, Mapping):
        return list(raw.values())
    if isinstance(raw, (str, bytes)) or not hasattr(raw, "__iter__"):
        raise InvalidMatrix(
            "%s(cells): the cells must be a sequence or a mapping a reader can walk, "
            "got %r" % (entry, raw)
        )
    return list(raw)


def _cell_pair(cell, entry, index):
    """One cell's two member ids, in the cell's own order (`rating.md` §2)."""
    if not isinstance(cell, Mapping) or "members" not in cell:
        raise InvalidMatrix(
            "%s(cells): cell %d must be a records.md §9 record carrying its pair, got %r"
            % (entry, index, cell)
        )
    return _member_ids(cell["members"], entry)


def _direction(cell, offset, entry, index):
    """One direction record of a cell, position-aligned with the cell's pair (§2)."""
    directions = cell.get("directions")
    pair = _member_ids(cell["members"], entry)
    if isinstance(directions, Mapping):
        keyed = [directions.get(name) for name in pair]
        if all(isinstance(value, Mapping) for value in keyed):
            return keyed[offset]
        entries = list(directions.values())
    elif directions is None or isinstance(directions, (str, bytes)):
        entries = []
    else:
        entries = list(directions)
    if len(entries) != 2 or not isinstance(entries[offset], Mapping):
        raise InvalidMatrix(
            "%s(cells): cell %d reports one direction per member of its pair, got %r"
            % (entry, index, directions)
        )
    return entries[offset]


def _counts(direction, entry, index):
    """A direction's ``(wins, ties, losses)`` as plain numbers (`records.md` §9)."""
    values = []
    for key in ("wins", "ties", "losses"):
        value = direction.get(key)
        if not isinstance(value, numbers.Real) or isinstance(value, bool):
            raise InvalidMatrix(
                "%s(cells): cell %d reports its %s as a count, got %r"
                % (entry, index, key, value)
            )
        values.append(value)
    return tuple(values)


def _table_facts(matrix, entry):
    """Read a matrix record as a table, refusing what is not one (`rating.md` §6).

    The checks are `rating`'s own and `report` reuses them verbatim, so a refusal names the
    violated rule -- `cells`, `seats`, `hands`, `pair`, the missing baseline or the shapes
    -- and nothing is fitted or assembled when one fires.  The record's `game` is read here
    and carried out beside its other four own facts: it is the one shape whose cells the fit
    is over (`rating.md` §1, §5, `shape.md` §4), and its seat count is read off
    `engine.game_config` and held to the pairwise instrument's (`docs/L1/seats.md` §5, D-33).
    """
    if not isinstance(matrix, Mapping):
        raise InvalidMatrix(
            "%s(matrix): the argument must be a matrix record, got %s"
            % (entry, type(matrix).__name__)
        )
    for key in ("members", "cells", "hands_per_cell", "table_seed", "table"):
        if key not in matrix:
            raise MissingMatrixKey(
                "%s(matrix): the matrix is missing the required key %r" % (entry, key)
            )

    members = _member_ids(matrix["members"], entry)
    cells = _cells(matrix["cells"], entry)
    size = len(members)
    expected = size * (size - 1) // 2
    if len(cells) != expected:
        raise CellCountMismatch(
            "%s(cells): %d cells are not the %d pairs of a %d-member membership"
            % (entry, len(cells), expected, size)
        )

    pairs = []
    seen = set()
    for index, cell in enumerate(cells):
        pair = _cell_pair(cell, entry, index)
        if len(pair) != 2:
            raise InvalidMatrix(
                "%s(cells): a cell is one unordered pair of members, got %r"
                % (entry, pair)
            )
        key = frozenset(pair)
        if key in seen:
            raise DuplicatePair(
                "%s(cells): the pair %r appears in two cells" % (entry, tuple(pair))
            )
        seen.add(key)
        pairs.append((pair, cell))

    known = set(members)
    for pair, _cell in pairs:
        for name in pair:
            if name not in known:
                raise ForeignMember(
                    "%s(cells): the cell %r names %r, which is not a member"
                    % (entry, tuple(pair), name)
                )

    hands_per_cell = matrix["hands_per_cell"]
    if not _is_int(hands_per_cell):
        raise InvalidMatrix(
            "%s(hands_per_cell): the matrix declares one integer hand count for every "
            "cell, got %r" % (entry, hands_per_cell)
        )
    hands_per_cell = int(hands_per_cell)
    for pair, cell in pairs:
        hands = cell.get("hands")
        if not _is_int(hands):
            raise InvalidMatrix(
                "%s(cells): the cell %r reports the hands it played, got %r"
                % (entry, tuple(pair), hands)
            )
        if int(hands) != hands_per_cell:
            raise UnevenCell(
                "%s(cells): the cell %r plays %d hands and the matrix declares %d"
                % (entry, tuple(pair), int(hands), hands_per_cell)
            )

    for name in BASELINES:
        if name not in known:
            raise MissingBaseline(
                "%s(members): the membership holds no %r baseline, and the three "
                "baselines are the anchor" % (entry, name)
            )

    table_seed = matrix["table_seed"]
    if not _is_int(table_seed):
        raise InvalidMatrix(
            "%s(table_seed): the table seed is one recorded integer, got %r"
            % (entry, table_seed)
        )

    # One table is one shape's: the matrix's own `game` and each cell's are read
    # tolerantly -- an absent one is the default, which keeps every table already recorded
    # ratable -- and two shapes among the cells, or a **declared** `game` its cells
    # contradict, is refused naming the shapes (`rating.md` §1, §6, `shape.md` §2-§3,
    # `docs/L1/shapes.md` §6).
    declared_game = None
    if "game" in matrix:
        declared_game = require_shape(matrix["game"], entry, "matrix")
    cell_shapes = []
    for _pair, cell in pairs:
        game = DEFAULT_SHAPE
        if isinstance(cell, Mapping) and "game" in cell:
            game = require_shape(cell["game"], entry, "cells")
        if game not in cell_shapes:
            cell_shapes.append(game)
    if len(cell_shapes) > 1:
        raise ShapeMismatch(
            "%s(cells): the cells record the shapes %r and %r, and a rating is fitted over "
            "one shape's cells" % (entry, cell_shapes[0], cell_shapes[1])
        )
    game = cell_shapes[0] if cell_shapes else DEFAULT_SHAPE
    if declared_game is not None and declared_game != game:
        raise ShapeMismatch(
            "%s(matrix): the matrix records the shape %r and its cells the shape %r, and a "
            "rating is fitted over one shape's cells" % (entry, declared_game, game)
        )

    facts = []
    for index, (pair, cell) in enumerate(pairs):
        first = _direction(cell, 0, entry, index)
        second = _direction(cell, 1, entry, index)
        facts.append(
            {
                "pair": pair,
                "hands": int(cell["hands"]),
                "first": _counts(first, entry, index),
                "second": _counts(second, entry, index),
            }
        )
    # A rating is fitted over **pairs**, so a table on a shape whose seat count is above
    # the instrument's is refused here, after the shapes are resolved and before a value is
    # fitted, naming the shape and its seat count -- the same refusal `report` reaches
    # through this reader, so the two entry points refuse one contract one way
    # (`docs/L1/seats.md` §5, `league.md` §4, D-22, D-33).
    require_pairwise(game, entry, "cells")
    return {
        "members": members,
        "cells": facts,
        "hands_per_cell": hands_per_cell,
        "table_seed": int(table_seed),
        "table": matrix["table"],
        "game": game,
    }


def _terms(members, cells):
    """Each cell as ``(i, j, w_ij, w_ji, n_ij)`` with a tie a half-win a side (§2)."""
    position = {name: index for index, name in enumerate(members)}
    terms = []
    for cell in cells:
        first, second = cell["pair"]
        w_first = cell["first"][0] + cell["first"][1] / 2.0
        w_second = cell["second"][0] + cell["second"][1] / 2.0
        terms.append(
            (
                position[first],
                position[second],
                float(w_first),
                float(w_second),
                float(w_first + w_second),
            )
        )
    return terms


# ---------------------------------------------------------------------------
# The solver (`rating.md` §3)
# ---------------------------------------------------------------------------
def _fit(size, terms, anchor):
    """Hunter's minorise-maximise iteration, with the anchor and the bound (§3, G15, G17).

    One iteration, in §3's order: the MM increment for every member with a win mass, its
    addition, the ``+-BOUND`` clamp, then the anchor's shift **and, after it, the two ends
    pinned** -- a member that won nothing at ``-BOUND``, one with no losses and no ties at
    ``+BOUND`` -- and then the convergence test.  The pin is taken after the shift, so the
    value the record carries is the bound itself.
    """
    wins = [0.0] * size
    totals = [0.0] * size
    for i, j, w_i, w_j, n in terms:
        wins[i] += w_i
        wins[j] += w_j
        totals[i] += n
        totals[j] += n

    theta = [0.0] * size
    bounded = [False] * size
    bound_applied = False
    converged = False
    iterations = 0
    count = len(anchor)

    for step in range(1, MAX_ITERATIONS + 1):
        iterations = step
        previous = list(theta)

        expected = [0.0] * size
        for i, j, _w_i, _w_j, n in terms:
            strength_i = math.exp(theta[i])
            strength_j = math.exp(theta[j])
            total = strength_i + strength_j
            if total > 0.0:
                expected[i] += n * strength_i / total
                expected[j] += n * strength_j / total

        for index in range(size):
            if wins[index] > 0.0 and expected[index] > 0.0:
                theta[index] += math.log(wins[index]) - math.log(expected[index])

        for index in range(size):
            if theta[index] > BOUND:
                theta[index] = BOUND
                bounded[index] = True
                bound_applied = True
            elif theta[index] < -BOUND:
                theta[index] = -BOUND
                bounded[index] = True
                bound_applied = True

        shift = sum(theta[index] for index in anchor) / count if count else 0.0
        if shift:
            for index in range(size):
                theta[index] -= shift

        for index in range(size):
            if wins[index] == 0.0:
                theta[index] = -BOUND
                bounded[index] = True
                bound_applied = True
            elif wins[index] >= totals[index]:
                theta[index] = BOUND
                bounded[index] = True
                bound_applied = True

        if max(abs(theta[index] - previous[index]) for index in range(size)) <= TOLERANCE:
            converged = True
            break

    return {
        "theta": theta,
        "bound_applied": bound_applied,
        "converged": converged,
        "iterations": iterations,
        "bounded": bounded,
    }


# ---------------------------------------------------------------------------
# The bootstrap (`rating.md` §4)
# ---------------------------------------------------------------------------
def _percentile(ordered, level):
    """One linearly interpolated order statistic of ``RESAMPLES`` sorted values (§4)."""
    size = len(ordered)
    position = (size - 1) * level / 100.0
    index = int(math.floor(position))
    fraction = position - index
    following = min(index + 1, size - 1)
    return ordered[index] + fraction * (ordered[following] - ordered[index])


def _resample(size, terms, cells, generator, anchor):
    """`RESAMPLES` hand-level replicates, one multinomial draw per cell each (§4, G18).

    The cells are visited in the matrix's `cells` order and each contributes one
    three-category draw from its direction 0; the replicate's masses are
    ``counts[0] + counts[1] / 2`` for the first member and ``hands`` minus that for the
    second, because direction 1 is the mirror of direction 0.  Every replicate is fitted
    from ``theta = 0`` with the same anchor and the same bound.
    """
    replicates = [[] for _ in range(size)]
    for _ in range(RESAMPLES):
        resampled = []
        for (i, j, _w_i, _w_j, _n), cell in zip(terms, cells):
            hands = cell["hands"]
            raw = cell["first"]
            proportions = [float(value) for value in raw]
            total = sum(proportions)
            if total > 0.0:
                proportions = [value / total for value in proportions]
            else:
                proportions = [1.0 / 3.0] * 3
            counts = generator.multinomial(hands, proportions)
            first = float(counts[0]) + float(counts[1]) / 2.0
            second = float(hands) - first
            resampled.append((i, j, first, second, first + second))
        fitted = _fit(size, resampled, anchor)
        for index in range(size):
            replicates[index].append(fitted["theta"][index])
    return replicates


# ---------------------------------------------------------------------------
# `rating` (`surface.md` §11)
# ---------------------------------------------------------------------------
def rating(matrix):
    """The fitted rating of one matrix record (`surface.md` §11, `rating.md` §5).

    One value and a 95% interval per member, the method, the anchor, the bound flag, the
    bootstrap's seed, the fit's convergence and -- this module's own keys -- the bound,
    the tolerance, the steps it took, its resample count and the table it was fitted
    over.  A hand-built table is rated as readily as a played one: the record is checked
    and never repaired (`rating.md` §1, §6).
    """
    facts = _table_facts(matrix, "rating")
    members = facts["members"]
    cells = facts["cells"]
    size = len(members)
    terms = _terms(members, cells)
    anchor = [index for index, name in enumerate(members) if name in BASELINES]

    fitted = _fit(size, terms, anchor)
    theta = fitted["theta"]
    bounded = fitted["bounded"]

    bootstrap_seed = _bootstrap_seed(facts["table_seed"])
    generator = Generator(PCG64(bootstrap_seed))
    replicates = _resample(size, terms, cells, generator, anchor)

    hands = int(facts["hands_per_cell"]) * (size - 1)
    values = {}
    for index, name in enumerate(members):
        ordered = sorted(replicates[index])
        lower = _percentile(ordered, LOWER_PERCENTILE)
        upper = _percentile(ordered, UPPER_PERCENTILE)
        value = float(theta[index])
        if lower > value:
            lower = value
        if upper < value:
            upper = value
        values[name] = {
            "value": value,
            "interval": (float(lower), float(upper)),
            "hands": hands,
            "bounded": bool(bounded[index]),
        }

    return {
        "values": values,
        "method": RATING["method"],
        "anchor": RATING["anchor"],
        "bound_applied": bool(fitted["bound_applied"]),
        "bootstrap_seed": bootstrap_seed,
        "converged": bool(fitted["converged"]),
        "bound": float(BOUND),
        "tolerance": float(TOLERANCE),
        "iterations": int(fitted["iterations"]),
        "resamples": int(RESAMPLES),
        # This module's own key, `records.md` §11 requiring none: the one shape whose cells
        # it fitted, so two shapes' ratings are never tabulated together (`rating.md` §5,
        # `shape.md` §4, `docs/L1/shapes.md` §6).
        "game": facts["game"],
        "hands_per_cell": int(facts["hands_per_cell"]),
        "members": tuple(members),
        "table_seed": int(facts["table_seed"]),
        "table": facts["table"],
    }
