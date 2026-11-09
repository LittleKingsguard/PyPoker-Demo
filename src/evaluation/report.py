"""The per-rung report: `report` (`docs/L3/evaluation/report.md`).

`report(rung_name, record, matrix, rating)` judges the run record -- the record with the
seven evidence families of `protocol.md` §1 attached -- against `protocol()`'s
declaration and returns one record carrying them, with the rung, the seeds, the table
budget, the table seed and the device beside them so a third party can re-run what it
describes (D-6, `protocol.md` §2).

Each family is copied by value from the record under the name `protocol()` spells --
`axis row`'s space included -- and the report adds none: an absent family is refused by
name, never filled in (`report.md` §3-§4).  The two facts a report completes are the pool
family's `rules` and its `utilities`: the population the report's table was measured over
is those rules and those utilities plus the rung's variants', and the pool family states
both (`e2e-surface.md` §3.4, `utilities.md` §7, §9, D-19, D-20).  A report is assembled
from records alone: it plays no hand, reads no file, moves no stream and never edits the
record it is handed.
"""

from collections.abc import Mapping

from .declarations import BASELINES, FAMILIES, HEADER_ITEMS
from .errors import (
    HeaderIncomplete,
    InvalidArgument,
    MembershipMismatch,
    MissingBaseline,
    MissingFamily,
    RatingMismatch,
)
from .rating import _member_ids, _table_facts, _token


def _families_present(record):
    """Every evidence family ``record`` carries, keyed by `protocol()`'s own spelling.

    A family is present when the record carries a key whose letters-and-digits token
    equals the family's **and** that key's value is not `None`: an explicit ``n/a`` value
    -- a string, an empty container, a record of ``n/a`` rows -- satisfies a family,
    while a missing key or a `None` value is refused (`report.md` §3 item 1, D-6).
    """
    present = {}
    for name in FAMILIES:
        wanted = _token(name)
        for key, value in record.items():
            if _token(key) == wanted and value is not None:
                present[name] = value
                break
    return present


def _header_value(header, item):
    """One header item's value, under the tolerant spelling of `declarations.md` §2.1."""
    wanted = _token(item)
    for key, value in header.items():
        name = _token(key)
        if name and (name == wanted or wanted in name or name in wanted):
            return value
    return None


def _header_ok(header):
    """The first of the nine header items the header lacks, or `None` (`report.md` §3)."""
    if not isinstance(header, Mapping):
        return HEADER_ITEMS[0]
    names = [name for name in (_token(key) for key in header) if name]
    for item in HEADER_ITEMS:
        wanted = _token(item)
        if not any(wanted == name or wanted in name or name in wanted for name in names):
            return item
    return None


def _pool_ids(pool_value):
    """The member ids a `records.md` §8 pool record names, in its own order."""
    if isinstance(pool_value, Mapping) and "members" in pool_value:
        return _member_ids(pool_value["members"], "report")
    return ()


def _membership_ok(pool_value, matrix_members):
    """The matrix's membership must be the pool's plus at most the rung's variants.

    Every pool member must be a row and a column, the three baselines must be present by
    id, and at most two members may lie outside the pool -- those two are the rung's
    variants (`report.md` §3 item 3, `league.md` §3).
    """
    named = set(matrix_members)
    pool_ids = _pool_ids(pool_value)
    for name in pool_ids:
        if name not in named:
            raise MembershipMismatch(
                "report(pool): the matrix does not name the pool's member %r" % (name,)
            )
    for name in BASELINES:
        if name not in named:
            raise MissingBaseline(
                "report(members): the membership holds no %r baseline, and the three "
                "baselines are the anchor" % (name,)
            )
    inside = set(pool_ids)
    outside = [name for name in matrix_members if name not in inside]
    if len(outside) > 2:
        raise MembershipMismatch(
            "report(matrix): %r is not a member of the pool the report names"
            % (outside[2],)
        )


def _rating_names(rating_value):
    """The member ids a rating record's `values` names, in the record's order."""
    if not isinstance(rating_value, Mapping):
        raise InvalidArgument(
            "report(rating): the rating must be a records.md §11 mapping, got %s"
            % (type(rating_value).__name__,)
        )
    if "values" not in rating_value:
        raise RatingMismatch(
            "report(rating): the rating carries no 'values', so it names no member"
        )
    raw = rating_value["values"]
    if isinstance(raw, Mapping):
        return [str(key) for key in raw]
    return list(_member_ids(raw, "report"))


def _rating_identity(rating_value, matrix_members):
    """`rating["values"]` must name exactly the matrix's members (`report.md` §3 item 4)."""
    names = _rating_names(rating_value)
    named = set(names)
    wanted = set(matrix_members)
    for name in names:
        if name not in wanted:
            raise RatingMismatch(
                "report(rating): the rating names %r and the matrix does not" % (name,)
            )
    for name in matrix_members:
        if name not in named:
            raise RatingMismatch(
                "report(rating): the matrix names %r and the rating does not" % (name,)
            )


def _measured_population(matrix_value):
    """The distinct rules the table's members declared, sorted (`records.md` §10, D-19).

    A matrix this module built carries `population`; a hand-built one may carry `rules` or
    neither, so the readers below take what the record states, in that order, and infer
    nothing a record does not say (`errors.md` §5, `rating.md` §1).
    """
    if not isinstance(matrix_value, Mapping):
        return ()

    def names_of(value):
        found = []
        if isinstance(value, Mapping):
            for inner in value.values():
                if isinstance(inner, str):
                    found.append(inner)
        elif isinstance(value, str):
            found.append(value)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for item in value:
                if isinstance(item, str):
                    found.append(item)
                elif isinstance(item, Mapping):
                    name = item.get("rule", item.get("learning_rule"))
                    if isinstance(name, str):
                        found.append(name)
        return found

    found = names_of(matrix_value.get("population"))
    if not found:
        found = names_of(matrix_value.get("rules"))
    if not found:
        found = names_of(matrix_value.get("member_records"))
    distinct = []
    for name in found:
        if name not in distinct:
            distinct.append(name)
    return tuple(sorted(distinct))


def _measured_utility_population(matrix_value):
    """The distinct utilities the table's members declared, sorted (§10, D-20).

    The utility side of :func:`_measured_population`, read the same way: the record's own
    `utility_population` first, then its per-member `utilities`, then its member records,
    and nothing invented for a record that states none (`errors.md` §5, `utilities.md`
    §7, §9).
    """
    if not isinstance(matrix_value, Mapping):
        return ()

    def names_of(value):
        found = []
        if isinstance(value, Mapping):
            for inner in value.values():
                if isinstance(inner, str):
                    found.append(inner)
        elif isinstance(value, str):
            found.append(value)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for item in value:
                if isinstance(item, str):
                    found.append(item)
                elif isinstance(item, Mapping):
                    name = item.get("utility")
                    if isinstance(name, str):
                        found.append(name)
        return found

    found = names_of(matrix_value.get("utility_population"))
    if not found:
        found = names_of(matrix_value.get("utilities"))
    if not found:
        found = names_of(matrix_value.get("member_records"))
    distinct = []
    for name in found:
        if name not in distinct:
            distinct.append(name)
    return tuple(sorted(distinct))


def _pool_family(pool_value, population, utility_population=()):
    """The pool family, its `rules` and `utilities` completed to the population the table measured.

    A pool record carries the rules and the utilities its own version members declare
    (`records.md` §8), and a report's pool family additionally states the two populations
    the report's table was measured over -- those members plus the rung's variants', the
    members a table holds outside the pool (`e2e-surface.md` §3.4's `report` row,
    `report.md` §2, `utilities.md` §7, §9, D-19, D-20).  Nothing is added when the family
    already names a population, and the value handed in is never edited (`report.md` §4).
    """
    if not isinstance(pool_value, Mapping) or "members" not in pool_value:
        return pool_value
    family = dict(pool_value)
    for key, wanted in (("rules", population), ("utilities", utility_population)):
        own = family.get(key)
        declared = []
        if isinstance(own, (list, tuple)):
            declared = [name for name in own if isinstance(name, str)]
        missing = [name for name in wanted if name not in declared]
        if missing:
            family[key] = tuple(declared) + tuple(missing)
    if family == pool_value:
        return pool_value
    return family


def report(rung_name, record, matrix, rating):
    """The complete per-rung report (`surface.md` §13, `records.md` §13).

    The seven families come first as presence, then the matrix is judged as a table
    (reusing `rating.md` §6's checks verbatim), then its membership against the report's
    pool family, then the rating's member identity, then the header's nine items -- each
    refused by name before anything is assembled.
    """
    if not isinstance(rung_name, str):
        raise InvalidArgument(
            "report(rung): the rung name must be a string, got %r" % (rung_name,)
        )
    if not isinstance(record, Mapping):
        raise InvalidArgument(
            "report(record): the run record must be a mapping, got %s"
            % (type(record).__name__,)
        )

    families = _families_present(record)
    for name in FAMILIES:
        if name not in families:
            raise MissingFamily(
                "report(record): the record carries no evidence family %r" % (name,)
            )

    facts = _table_facts(matrix, "report")
    matrix_members = facts["members"]
    _membership_ok(families["pool"], matrix_members)
    _rating_identity(rating, matrix_members)

    header = families["header"]
    missing_item = _header_ok(header)
    if missing_item is not None:
        raise HeaderIncomplete(
            "report(header): the header is missing the required item %r"
            % (missing_item,)
        )

    seeds = record.get("seeds")
    if seeds is None:
        seeds = _header_value(header, "seeds")
    population = _measured_population(matrix)
    utility_population = _measured_utility_population(matrix)
    assembled = {
        "rung": rung_name,
        "seeds": tuple(seeds) if isinstance(seeds, (list, tuple)) else seeds,
        "table": facts["table"],
        "table seed": facts["table_seed"],
        "device": _header_value(header, "device"),
    }
    for name in FAMILIES:
        if name == "matrix":
            assembled[name] = matrix
        elif name == "rating":
            assembled[name] = rating
        elif name == "pool":
            assembled[name] = _pool_family(
                families[name], population, utility_population
            )
        else:
            assembled[name] = families[name]
    return assembled
