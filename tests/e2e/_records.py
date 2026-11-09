"""Record readers and league fixtures for FAM-6..FAM-16 of the rev-2 battery.

``_surface.py`` is the plumbing the whole battery shares: the six package imports, the
invented seeds and hand counts, and the base case.  This module adds the two things the
league families (FAM-6..FAM-16) need on top of it:

* tolerant readers for the record shapes ``docs/L1/records.md`` pins — a version
  (§7), a pool and its members (§8), a cell (§9), a matrix (§10) and a rating (§11).
  The contract is asserted, the nesting and the key spelling are not;
* a scratch area that outlives one case and a version builder, because a pool, a
  table or a run record is built once per process and shared with the cases after it
  (``battery.md`` §2: league cases are sized to the battery, not to the talk).  A
  case's own ``scratch()`` directory is deleted when that case ends, so a shared pool
  must not point into it.

Nothing here reaches past an entry point of ``docs/L1/e2e-surface.md`` §3.
"""

from __future__ import annotations

import atexit
import os
import shutil
import sys
import tempfile
from collections.abc import Mapping

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _surface as S  # noqa: E402


def tok(value):
    """A comparison token: lowercase, alphanumerics only."""
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


# ---------------------------------------------------------------------------
# A scratch area that outlives one case
# ---------------------------------------------------------------------------
_WORK = None


def work_dir():
    """A writable directory the battery owns for the whole process."""
    global _WORK
    if _WORK is None:
        _WORK = tempfile.mkdtemp(prefix="pypoker-league-")
        atexit.register(shutil.rmtree, _WORK, True)
    return _WORK


# ---------------------------------------------------------------------------
# Required keys, read tolerantly
# ---------------------------------------------------------------------------
def required(record, what, *names):
    """One required key of a record, or a failure naming the record and the key."""
    if not isinstance(record, Mapping):
        raise AssertionError(
            "%s must be a mapping in the sense of records.md §1; got %r"
            % (what, type(record).__name__)
        )
    for name in names:
        want = tok(name)
        for key in record:
            if tok(key) == want:
                return record[key]
    raise AssertionError(
        "%s is missing the required key %r (it carries %r)"
        % (what, names[0], sorted(str(key) for key in record))
    )


def numbers_under(record, *needles):
    """Every number under a key containing one of ``needles``, however nested."""
    found = []

    def walk(value):
        if isinstance(value, Mapping):
            for key, inner in value.items():
                name = str(key).lower()
                if any(needle in name for needle in needles):
                    found.extend(S.numbers(inner))
                else:
                    walk(inner)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for inner in value:
                walk(inner)

    walk(record)
    return found


def ids_of(value):
    """The member ids of a members-like container, in declared order."""
    if isinstance(value, Mapping):
        return [str(key) for key in value]
    if isinstance(value, (list, tuple, set, frozenset)):
        out = []
        for item in value:
            if isinstance(item, Mapping):
                for key in ("id", "name", "member", "version"):
                    inner = item.get(key)
                    if isinstance(inner, str):
                        out.append(inner)
                        break
                else:
                    out.append(str(S.canon(item)))
            else:
                out.append(str(item))
        return out
    return [str(value)]


# ---------------------------------------------------------------------------
# Version, pool (records.md §7, §8)
# ---------------------------------------------------------------------------
def make_version(case, name, seed=S.SEED_A, step=53, samples=S.BUDGET_TINY,
                 lineage="R6-residual-battery", rung="R7", variant="deep-sparse",
                 width=None, depth=None, rule=None, utility=None):
    """One version record of ``records.md`` §7, with a checkpoint the case really wrote.

    The battery builds a small learner through ``agents.build_learner``, saves it with
    ``agents.save`` into the process scratch area, and wraps the artefact as a version:
    an id, the path ``evaluation.policy_from`` loads, the rung and variant that
    produced it, the seed, the snapshot's step and the hands trained, the lineage it
    descends from, and — D-19's required key — the **rule** it was trained under, and —
    D-20's — the **utility** whose reward it was trained on.  Every one of those values
    is the battery's own.

    ``rule`` and ``utility`` default to the catalogues' first members, the declared
    defaults of ``rules.md`` §4 and ``utilities.md`` §5, so every caller that predates
    either catalogue keeps the version it built before; the learner is built under the
    rule and utility the record declares, so a version whose file and record disagreed
    would only exist where a case doctors it on purpose.
    """
    width = S.VERSION_WIDTH if width is None else width
    depth = S.VERSION_DEPTH if depth is None else depth
    rule = S.RULE_DEFAULT if rule is None else rule
    utility = S.UTILITY_DEFAULT if utility is None else utility
    spec = case.learner_spec(width=width, depth=depth, seed=seed, learning_rule=rule,
                             utility=utility)
    learner = case.ep("agents", "build_learner")(spec)
    target = os.path.join(work_dir(), "version-%s.pt" % (name,))
    written = case.ep("agents", "save")(learner, target)
    return {
        "id": "version-%s" % (name,),
        "path": str(written) if written else target,
        "rung": rung,
        "variant": variant,
        "seed": seed,
        "step": step,
        "samples": samples,
        "lineage": lineage,
        "rule": rule,
        "utility": utility,
    }


def version_chain(case, names, seed=S.SEED_A, step=53, rule=None, utility=None,
                  lineage_start="R6-residual-battery", rung="R7",
                  variant="deep-sparse"):
    """A lineage chain of version records, each descending from the one before it.

    ``lineage_start`` is the label the chain's first member descends from: a label no
    member of the pool carries, which is what makes this chain **one family** of a pool
    that holds several (``ASM-26``).  Two chains given two starts and two rules are two
    families, and that is how a case builds a heterogeneous window (D-19); a chain's
    members declare one utility for the same reason they declare one rule (D-20).
    """
    out = []
    previous = lineage_start
    for index, name in enumerate(names):
        out.append(
            make_version(
                case,
                name,
                seed=seed + index,
                step=step * (index + 1),
                samples=S.BUDGET_TINY * (index + 1),
                lineage=previous,
                rule=rule,
                utility=utility,
                rung=rung,
                variant=variant,
            )
        )
        previous = "version-%s" % (name,)
    return out


def next_version(case, name, newest, seed=None, later=37, rule=None, utility=None):
    """One version offered into a window: it sits at the head of the lineage order.

    ``records.md`` §7 makes a version's ``lineage`` the version it descends from, and
    ``league.md`` §2 rolls the window by lineage order, so a version offered into a
    window is newer than every member it joins: its lineage is the current newest
    member's id and its step is later than that member's.  Offering a version whose
    lineage points nowhere in the window would leave the window with no order to roll,
    which is what makes "the oldest evictable version is dropped" unobservable and the
    membership — and so the id — unchanged.  The tag, the seed and the increment are the
    battery's own.  ``rule`` and ``utility`` are what the version is trained under,
    defaulting to the newest member's own, because a family is one lineage chain under
    one rule and one utility (``ASM-26``, D-20).
    """
    step, samples = 53, S.BUDGET_TINY
    lineage = "R6-residual-battery"
    rung, variant = "R7", "deep-sparse"
    if isinstance(newest, Mapping):
        lineage = str(newest.get("id") or lineage)
        step = _as_int(newest.get("step"), 0) + later
        samples = _as_int(newest.get("samples"), 0) + S.BUDGET_TINY
        rung = newest.get("rung") or rung
        variant = newest.get("variant") or variant
        if rule is None:
            rule = newest.get("rule")
        if utility is None:
            utility = newest.get("utility")
    elif newest:
        lineage = str(newest)
    return make_version(
        case,
        name,
        seed=S.SEED_A if seed is None else seed,
        step=step,
        samples=samples,
        lineage=lineage,
        rung=rung,
        variant=variant,
        rule=rule,
        utility=utility,
    )


def pool_row_members(row):
    """A pool record's ordered members, or the sequence ``pool_members`` returned."""
    if isinstance(row, Mapping):
        value = required(row, "pool_members", "members", "member_list")
        return value
    return row


def member_ids(row):
    """The ids of a pool's ordered members."""
    return ids_of(pool_row_members(row))


def member_records(row):
    """A pool's members as records, where the surface returns records."""
    value = pool_row_members(row)
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, (list, tuple)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def pool_bound(row):
    """The bound M a pool record reports (§8)."""
    numbers = [number for number in S.bound_numbers(row) if float(number).is_integer()]
    return int(numbers[0]) if numbers else None


def pool_frozen(row):
    """The frozen flag a pool record reports — a **required** key of ``records.md`` §8.

    §8 makes a pool record ``id``, ``m``, ``frozen`` and ``members``, with ``frozen``
    required because it says whether the pool was frozen when it was used, which is how
    a pair's parity is read.  A caller reads the flag and its value, not a word that
    happens to contain it.
    """
    return required(row, "a pool record (records.md §8)", "frozen")


def pool_id(pool, row):
    """A pool's id, read off the pool record or its read-back (§8)."""
    for candidate in (pool, row):
        found = S.pool_identity(candidate)
        if found:
            return str(found[0])
    raise AssertionError(
        "neither build_pool's record nor pool_members names a pool id; records.md §8 "
        "requires one so two reports can compare a run with a table by the id alone"
    )


# ---------------------------------------------------------------------------
# The rule a record names (records.md §7, §8, §9, §10, §12; rules.md §4, §7)
#
# D-19 put one fact in five records: a version carries `rule`, a pool record the
# `rules` its version members declare, a cell one rule per member, a matrix one rule
# per member plus the `population` they make up, and a run record each variant's rule
# plus the run's `rules` set.  The fact is the same in all five, so the readers below
# share one walker: the container is the record's own, the fact is the catalogue name
# (or `None` for a baseline, which declares no rule).
# ---------------------------------------------------------------------------
def rule_of(entry):
    """The rule a record states for itself, under whatever key declares it, or ``None``."""
    if not isinstance(entry, Mapping):
        return None
    for key, value in entry.items():
        if "rule" in tok(key) and isinstance(value, str):
            return value
    return None


def rules_of(value):
    """Every ``(member id, rule)`` pair a rules-shaped container states, in its order.

    A container may be keyed by member — a cell's and a matrix's ``rules`` — or be the
    list of names a pool record or a run record states — the distinct rules, no member
    attached.  Both shapes are read here, and a member whose rule is a baseline's
    ``None`` keeps its place, because "which estimators met" is an answer a cell gives
    and "one of them declares none" is part of it (``records.md`` §9, §10).
    """
    out = []
    if isinstance(value, Mapping):
        for key, inner in value.items():
            if isinstance(inner, Mapping):
                out.append((str(key), rule_of(inner)))
            elif inner is None or isinstance(inner, (str, bytes)):
                out.append((str(key), None if inner is None else str(inner)))
            else:
                out.append((str(key), None))
        return out
    if isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            if isinstance(item, Mapping):
                name = None
                for field in ("id", "member", "name", "variant"):
                    candidate = item.get(field)
                    if isinstance(candidate, str):
                        name = candidate
                        break
                out.append((name, rule_of(item)))
            elif item is None or isinstance(item, (str, bytes)):
                out.append((None, None if item is None else str(item)))
            else:
                out.append((None, rule_of(item)))
        return out
    if isinstance(value, (str, bytes)):
        return [(None, str(value))]
    return out


def rule_names_of(value):
    """The distinct rule names a rules-shaped container states, in first-seen order."""
    seen = []
    for _member, rule in rules_of(value):
        if rule is not None and rule not in seen:
            seen.append(rule)
    return seen


def pool_rules(row):
    """The ``rules`` a pool record declares — a **required** key of ``records.md`` §8."""
    return required(row, "a pool record (records.md §8)", "rules")


def version_rule(member):
    """The ``rule`` a version member declares — a **required** key of ``records.md`` §7."""
    return required(member, "a version member of the pool (records.md §7)", "rule")


def cell_rules(cell):
    """The ``rules`` a cell declares — a **required** key of ``records.md`` §9."""
    return required(cell, "a cell record (records.md §9)", "rules")


def matrix_rules(matrix):
    """The ``rules`` a matrix declares — a **required** key of ``records.md`` §10."""
    return required(matrix, "a matrix record (records.md §10)", "rules")


def matrix_population(matrix):
    """The ``population`` a matrix declares — a **required** key of ``records.md`` §10."""
    return required(matrix, "a matrix record (records.md §10)", "population")


def run_rules(record):
    """The ``rules`` set a run record declares — a **required** key of ``records.md`` §12."""
    return required(record, "a run record (records.md §12)", "rules")


def variant_rule(entry):
    """The ``learning_rule`` one variant entry of a run record names (§12, D-19)."""
    return required(entry, "a variant entry of a run record (records.md §12)",
                    "learning_rule", "rule")


def version_members(row):
    """The ids of a pool's version members, i.e. all but the catalogue's baselines.

    The catalogue is six baselines since D-21 — the flagged three and the three folders —
    and a folder is a baseline member exactly as ``always-call`` is, so a folder id is
    never mistaken for a version's (`records.md` §8, ASM-32, D-21).
    """
    return [member for member in member_ids(row)
            if not any(tok(name) in tok(member) for name in S.BASELINES)]


def baseline_members(row):
    """The ids of a pool's fixed baselines — the flagged three and any declared folder."""
    return [member for member in member_ids(row)
            if any(tok(name) in tok(member) for name in S.BASELINES)]


def baseline_member(members, name):
    """The member id one baseline appears under, or ``None``."""
    for member in members:
        if tok(name) in tok(member):
            return member
    return None


# ---------------------------------------------------------------------------
# Cell (records.md §9)
# ---------------------------------------------------------------------------
def cell_members(cell):
    """The two member ids a cell pairs."""
    return ids_of(required(cell, "a cell record", "members"))


def cell_hands(cell):
    """The hands a cell played."""
    values = [int(number) for number in
              S.declared_numbers(cell, "hands", "hands_played", "hands played")
              if float(number).is_integer()]
    if not values:
        raise AssertionError(
            "a cell record reports the hands it played (records.md §9): %r" % (cell,)
        )
    return values[0]


def cell_seed(cell):
    """The seed a cell was played at."""
    values = S.declared_numbers(cell, "seed")
    if not values:
        raise AssertionError("a cell record reports its seed (records.md §9): %r" % (cell,))
    return int(values[0])


def cell_params(cell):
    """The two members' parameter counts."""
    values = numbers_under(cell, "param")
    return [int(round(number)) for number in values]


def direction_rows(cell):
    """The cell's direction records."""
    return S.cell_directions(cell)


def direction_counts(row):
    """``(wins, ties, losses)`` of one direction, read tolerantly."""
    return (
        S.count_total(row, "wins", "win", "won"),
        S.count_total(row, "ties", "tie", "draws", "draw"),
        S.count_total(row, "losses", "loss", "lost"),
    )


def direction_delta(row):
    """The mean chip delta per hand of one direction."""
    values = S.numbers(S.find_values(row, "delta"))
    if not values:
        values = S.numbers(S.find_values(row, "mean"))
    if not values:
        raise AssertionError(
            "a cell's direction reports the mean chip delta per hand (protocol.md §2): %r"
            % (row,)
        )
    return float(values[0])


def cell_deltas(cell):
    """The two directions' mean chip deltas, in declared order."""
    return [direction_delta(row) for row in direction_rows(cell)]


def seat_split(row):
    """The per-seat hand counts of one direction."""
    return [value for value in S.seat_split(row) if float(value).is_integer()]


# ---------------------------------------------------------------------------
# Matrix (records.md §10)
# ---------------------------------------------------------------------------
def matrix_members(matrix):
    """The ordered membership of a matrix record."""
    return ids_of(required(matrix, "a matrix record", "members"))


def matrix_cells(matrix):
    """Every cell of a matrix record, in declared order, whatever container holds them."""
    cells = required(matrix, "a matrix record", "cells", "cell_records")
    if isinstance(cells, Mapping):
        return list(cells.values())
    return list(cells)


def matrix_hands_per_cell(matrix):
    """The one hand count every cell was played at."""
    values = [int(number) for number in
              S.declared_numbers(matrix, "hands_per_cell", "hands per cell", "handcell",
                                 "cell_hands", "cell size")
              if float(number).is_integer()]
    if not values:
        raise AssertionError(
            "a matrix record reports the one hand count of every cell (records.md §10): %r"
            % (matrix,)
        )
    return values[0]


def matrix_table_seed(matrix):
    """The seed the table was played from."""
    values = S.declared_numbers(matrix, "table_seed", "table seed") or \
        S.declared_numbers(matrix, "seed")
    if not values:
        raise AssertionError(
            "a matrix record reports the table seed it was played from (records.md §10): %r"
            % (matrix,)
        )
    return int(values[0])


def matrix_table(matrix):
    """The table budget a matrix record names.

    ``records.md`` §10 marks the matrix's ``table`` label **required** — ``live`` or
    ``full`` — because the report's header repeats it and two tables are only comparable
    when a reader can tell which budget measured them (``league.md`` §6, D-16).  The key
    is read as a required key of the record, and its value is read as a value.
    """
    return required(matrix, "a matrix record (records.md §10)", "table")


def matrix_pair_count(matrix):
    """How many unordered pairs the matrix's membership has."""
    return len(matrix_members(matrix)) * (len(matrix_members(matrix)) - 1) // 2


# ---------------------------------------------------------------------------
# Matrix containers, doctored (records.md §10)
#
# §10 leaves the `members` and `cells` containers free: a sequence, or a mapping a
# reader can walk.  A case that damages a table to see it refused must therefore go
# through the container the record actually returned.  Indexing position zero or
# slice-assigning the container raises `KeyError`/`TypeError` on a mapping, and a
# battery may not throw on its own (battery.md §2), so every removal below is written
# against the container it finds.
# ---------------------------------------------------------------------------
def matrix_key(matrix, *names):
    """The actual key of a matrix record whose form is one of ``names``."""
    wanted = {S._family_token(name) for name in names}
    for key in (matrix if isinstance(matrix, Mapping) else ()):
        if S._family_token(key) in wanted:
            return key
    raise AssertionError(
        "a matrix record carries a %r container (records.md §10); it carries %r"
        % (names[0], sorted(str(key) for key in matrix)
           if isinstance(matrix, Mapping) else matrix)
    )


def member_entry_id(value):
    """The id one members-container entry names."""
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        for key in ("id", "name", "member", "version"):
            inner = value.get(key)
            if isinstance(inner, str):
                return inner
        found = ids_of(value)
        return found[0] if found else ""
    return str(value)


def cell_pair(cell):
    """The member ids a cell pairs, read without failing on a shape not invented here."""
    if isinstance(cell, Mapping):
        for key, value in cell.items():
            if tok(key) in ("members", "member", "pair", "players", "sides", "opponents"):
                return ids_of(value)
        return []
    return ids_of(cell)


def without(container, drop, drop_key=None):
    """A copy of a members- or cells-like container without the entries ``drop`` selects.

    A mapping container is filtered by its values and, when ``drop_key`` is given, by its
    keys too — a cells mapping may be keyed by the pair it holds.
    """
    if isinstance(container, Mapping):
        return {
            key: value for key, value in container.items()
            if not drop(value) and not (drop_key and drop_key(key))
        }
    return [value for value in container if not drop(value)]


def drop_matrix_member(matrix, member):
    """Remove one member and every cell that names it, whatever the containers are."""
    wanted = tok(member)
    members_key = matrix_key(matrix, "members")
    cells_key = matrix_key(matrix, "cells", "cell_records")
    matrix[members_key] = without(
        matrix[members_key], lambda value: wanted == tok(member_entry_id(value))
    )
    matrix[cells_key] = without(
        matrix[cells_key],
        lambda cell: any(wanted == tok(pair) for pair in cell_pair(cell)),
        drop_key=lambda key: wanted in tok(key),
    )
    return matrix


def rename_matrix_member(matrix, member, replacement):
    """Rename one member in the membership and in every cell that pairs it."""
    wanted = tok(member)
    members_key = matrix_key(matrix, "members")
    cells_key = matrix_key(matrix, "cells", "cell_records")

    def renamed_text(value):
        return replacement if isinstance(value, str) and tok(value) == wanted else value

    def renamed_entry(entry):
        if isinstance(entry, str):
            return renamed_text(entry)
        if isinstance(entry, Mapping):
            return {
                key: (renamed_text(value)
                      if tok(key) in ("id", "member", "name", "version") else value)
                for key, value in entry.items()
            }
        return entry

    members = matrix[members_key]
    if isinstance(members, Mapping):
        matrix[members_key] = {
            (replacement if tok(key) == wanted else key): renamed_entry(value)
            for key, value in members.items()
        }
    else:
        matrix[members_key] = [renamed_entry(entry) for entry in members]

    def doctor(cell):
        if not isinstance(cell, Mapping):
            return cell
        out = dict(cell)
        for key, value in cell.items():
            if tok(key) not in ("members", "member", "pair", "players", "sides",
                                "opponents"):
                continue
            if isinstance(value, Mapping):
                out[key] = {
                    (replacement if tok(inner_key) == wanted else inner_key): inner
                    for inner_key, inner in value.items()
                }
            else:
                out[key] = [renamed_entry(entry) for entry in value]
        return out

    cells = matrix[cells_key]
    if isinstance(cells, Mapping):
        matrix[cells_key] = {key: doctor(value) for key, value in cells.items()}
    else:
        matrix[cells_key] = [doctor(value) for value in cells]
    return matrix


def set_declared(record, value, *names):
    """Rewrite the one key of a record whose form is one of ``names``; ``False`` if none.

    A case that doctors a record mutates the key it finds rather than a spelling this
    battery invented, and a record without that key returns ``False`` so the case can
    fail with its own message instead of raising from the battery's body.
    """
    wanted = {S._family_token(name) for name in names}
    for key in list(record.keys()) if isinstance(record, Mapping) else ():
        if S._family_token(key) in wanted:
            record[key] = value
            return True
    return False


# ---------------------------------------------------------------------------
# Rating (records.md §11)
# ---------------------------------------------------------------------------
def rating_entries(rating):
    """One entry per matrix member: ``{member id: entry}``."""
    values = required(rating, "a rating record", "values", "ratings")
    out = {}
    if isinstance(values, Mapping):
        for key, value in values.items():
            out[str(key)] = value
        return out
    for item in values or ():
        if not isinstance(item, Mapping):
            raise AssertionError(
                "a rating entry carries a value, a 95%% interval and the hands behind "
                "it (records.md §11); got %r" % (type(item).__name__,)
            )
        key = None
        for name in ("id", "member", "name"):
            for inner_key, inner in item.items():
                if tok(inner_key) == name and isinstance(inner, str):
                    key = inner
                    break
            if key:
                break
        if not key:
            raise AssertionError("a rating entry names no member: %r" % (item,))
        out[key] = item
    return out


def rating_entry_count(rating):
    """How many entries a rating record **lists**, repeats included.

    ``records.md`` §11 makes ``values`` one entry per matrix member, and the reader above
    keys its result by member — so an entry listed twice would collapse into one and "one
    value each" would pass on its own defect.  A case that asserts the one-entry-per-member
    rule counts the listing itself as well (``battery.md`` §2: a case that cannot fail is a
    defect).
    """
    values = required(rating, "a rating record", "values", "ratings")
    try:
        return len(values)
    except TypeError:  # a one-pass container: read it once, as listed
        return len(rating_entries(rating))


def scalar_numbers_under(record, *needles):
    """Numbers a record gives directly under a key naming one of ``needles``.

    A key whose value is one number states that quantity; a key whose value is a
    container is descended into, so the numbers inside it are read under their own
    keys and never by their position in the container.  This is what keeps a reader
    from mistaking the first number of a nested record for the quantity the key names.
    """
    found = []

    def walk(value):
        if isinstance(value, Mapping):
            for key, inner in value.items():
                name = str(key).lower()
                token = tok(key)
                if S._is_number(inner) and any(needle in name or needle in token
                                               for needle in needles):
                    found.append(inner)
                else:
                    walk(inner)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for inner in value:
                walk(inner)

    walk(record)
    return found


# The words a rating entry can use for the two ends of its interval.  ``records.md``
# §11 fixes neither their names nor their order, so a reader must recognise the ends by
# what they say and then read the interval by its extent.
_INTERVAL_TOKENS = (
    "interval",
    "intervals",
    "confidence",
    "conf",
    "ci",
    "ci95",
    "bounds",
    "bound",
    "range",
    "percentile",
    "percentiles",
    "quantile",
    "quantiles",
    "lower",
    "upper",
    "low",
    "high",
    "min",
    "max",
)


def _names_interval(token):
    """Whether a key's form names one end of, or the whole of, a confidence interval."""
    if token in _INTERVAL_TOKENS:
        return True
    if "interval" in token or "confidence" in token:
        return True
    for side in ("lower", "upper", "low", "high", "min", "max"):
        if token.startswith(side) or token.endswith(side):
            return True
    return token.startswith("ci") and token[2:].isdigit()


def interval_numbers(entry):
    """Every number an entry states as a bound, in the order the entry states them."""
    found = []

    def walk(value):
        if isinstance(value, Mapping):
            for key, inner in value.items():
                if _names_interval(tok(key)):
                    found.extend(S.numbers(inner))
                else:
                    walk(inner)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for inner in value:
                walk(inner)

    walk(entry)
    return found


def rating_value(entry):
    """One entry's fitted value, read as a value and never as a container's first number."""
    values = scalar_numbers_under(entry, "value", "rating", "elo", "estimate", "strength")
    if not values:
        values = numbers_under(entry, "value", "rating", "elo", "estimate", "strength")
    if not values:
        raise AssertionError("a rating entry carries no fitted value (records.md §11): %r" % (entry,))
    return float(values[0])


def rating_interval(entry):
    """One entry's 95% interval as an unordered pair's extent: ``(smaller, larger)``.

    ``records.md`` §11 fixes neither the key names of the bounds nor the order they are
    stated in, so the interval is read by what it *is*: the pair of bounds whose extent
    is meant to contain the fitted value.  Reading the first number as the lower bound
    and the second as the upper would invert a conforming record that states its bounds
    high-first and fail a correct fit, which is ``battery.md`` §2's failure class (b).
    The extent is returned, so a case asserts that the value lies between the two — never
    that bound one precedes bound two.
    """
    values = interval_numbers(entry)
    if len(values) < 2:
        raise AssertionError(
            "a rating entry carries a 95%% interval — two bounds, under keys of the "
            "record's own naming and in either order (records.md §11): %r" % (entry,)
        )
    return min(values), max(values)


def rating_hands(entry):
    """The hands behind one entry, or ``None`` when the entry states none."""
    values = scalar_numbers_under(entry, "hands", "games", "observations", "samples")
    if not values:
        values = numbers_under(entry, "hands", "games", "observations", "samples")
    if values:
        return int(round(sum(values)))
    return None


def rating_flag(rating, *needles):
    """Whether a named flag of the rating record is set, read tolerantly."""
    for key, value in (rating.items() if isinstance(rating, Mapping) else ()):
        name = tok(key)
        if all(tok(needle) in name for needle in needles):
            return value
    return None


# ---------------------------------------------------------------------------
# The league declaration (evaluation.league)
# ---------------------------------------------------------------------------
def league_m(decl):
    """The pool bound M the league declares."""
    numbers = [number for number in S.bound_numbers(decl) if float(number).is_integer()]
    return int(numbers[0]) if numbers else None


def table_numbers(decl, table):
    """Every count the league declaration associates with one table budget."""
    wanted = tok(table)
    found = []

    def walk(value):
        if isinstance(value, Mapping):
            for key, inner in value.items():
                named = wanted in tok(key)
                if not named and isinstance(inner, Mapping):
                    named = any(isinstance(v, str) and tok(v) == wanted
                                for v in inner.values())
                if named:
                    found.extend(int(number) for number in S.numbers(inner)
                                 if float(number).is_integer())
                walk(inner)
        elif isinstance(value, (list, tuple)):
            for inner in value:
                walk(inner)

    walk(decl)
    return found


def cells_for(decl, k):
    """The league's cell count for a K-member membership, or ``None``."""
    for key, value in _items(decl):
        if callable(value) and ("cell" in tok(key) or "pair" in tok(key)):
            for args in ((k,), (list(range(k)),), ({"members": list(range(k))},)):
                try:
                    got = value(*args)
                except Exception:
                    continue
                numbers = [int(number) for number in S.numbers(got)
                           if float(number).is_integer()]
                if numbers:
                    return numbers[0]
    for key, value in _items(decl):
        if isinstance(value, Mapping):
            for inner_key, inner in value.items():
                if tok(inner_key) == str(k):
                    numbers = [int(number) for number in S.numbers(inner)
                               if float(number).is_integer()]
                    if numbers:
                        return numbers[0]
    return None


def _items(obj, _depth=0):
    if _depth > 8:
        return
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            yield key, value
            for item in _items(value, _depth + 1):
                yield item
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            for item in _items(value, _depth + 1):
                yield item


# ---------------------------------------------------------------------------
# Run record: the checkpoints family (records.md §12)
# ---------------------------------------------------------------------------
def checkpoint_paths_of(record):
    """The checkpoint paths a run record's own ``checkpoints`` entry names.

    ``records.md`` §12 makes that key *the retained snapshots plus the final model per
    variant per seed*, so it is read on its own and never by walking the whole record: a
    pool member is a version and carries a ``path`` too (``records.md`` §7), so a
    whole-record walk counts the same artefact twice and reads a snapshot the run did
    not retain.
    """
    entry = required(record, "a run record (records.md §12)", "checkpoints", "checkpoint")
    paths = S.checkpoint_paths(entry)
    if not paths:
        raise AssertionError(
            "a run record's checkpoints entry names the retained snapshots and the final "
            "model per variant per seed (records.md §12); it names no checkpoint: %r"
            % (entry,)
        )
    return paths


def checkpoint_span(m, variants=1, seeds=1):
    """The least and the most checkpoints a run record may name (``records.md`` §12).

    A run writes ten intra-run snapshots of which the pool's window retains the last M,
    plus its final model per variant per seed (``protocol.md`` §5, ASM-18).  So a run of
    ``variants`` × ``seeds`` pairs names at least its final models and at most M retained
    snapshots plus one final model for each pair — expressed relative to M and to the
    run's own pair count, never as a literal tied to one instance.
    """
    pairs = max(1, int(variants) * int(seeds))
    return pairs, pairs * (int(m) + 1)


# ---------------------------------------------------------------------------
# The cost record (e2e-surface.md §3.6, records.md §12)
# ---------------------------------------------------------------------------
def timing_facts(timings):
    """The hands, per-hand durations, throughputs and wall clocks a cost record carries.

    ``e2e-surface.md`` §3.6 names what ``harness.timings`` reports — the wall clock, the
    seconds per hand and the throughput the driver collected — and ``records.md`` §12
    puts that record in the run record, but neither fixes a key spelling.  A record keyed
    ``seconds_per_hand`` or ``hands_per_second`` — the snake_case these documents use
    throughout — says exactly what ``seconds per hand`` and ``hands per second`` say, so
    a key is classified by what it names and not by a literal substring.  The reader
    never asserts a bound on any value it returns.
    """
    facts = {"hands": [], "per_hand": [], "throughput": [], "clock": []}

    def classify(token):
        if "hand" in token and ("persecond" in token or "through" in token):
            return "throughput"
        if "perhand" in token or token in ("spth", "handseconds", "handtime",
                                           "secondsonehand", "timeperhand"):
            return "per_hand"
        if "hand" in token:
            return "hands"
        if "through" in token or "persecond" in token:
            return "throughput"
        if any(word in token for word in ("clock", "wall", "elapsed", "duration",
                                          "runtime", "second", "secs", "time")):
            return "clock"
        return None

    def walk(value, depth):
        if depth > 24:
            return
        if isinstance(value, Mapping):
            for key, inner in value.items():
                kind = classify(tok(key))
                if kind:
                    facts[kind].extend(S.numbers(inner))
                    # A flat mapping of numbers under a classified key is that one
                    # quantity's own record; descending into it would file the same
                    # number under a second kind.
                    if isinstance(inner, Mapping) and all(
                        not isinstance(item, (Mapping, list, tuple, set, frozenset))
                        for item in inner.values()
                    ):
                        continue
                walk(inner, depth + 1)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for inner in value:
                walk(inner, depth + 1)

    walk(timings, 0)
    return {kind: [float(number) for number in values] for kind, values in facts.items()}


def run_timings(record):
    """The cost record a run record carries (``records.md`` §12: ``timings``), or ``None``."""
    if not isinstance(record, Mapping):
        return None
    for key, value in record.items():
        if tok(key) in ("timings", "timing", "cost", "costs", "throughput"):
            return value
    for needle in ("timing", "cost", "throughput"):
        values = S.find_values(record, needle)
        if values:
            return values
    return None


# ---------------------------------------------------------------------------
# Episode and decision records (records.md §5)
# ---------------------------------------------------------------------------
def decision_records(episode):
    """The ordered decisions of an episode record, whatever container holds them.

    ``records.md`` §5 requires the ordered decisions; a record may carry them as a
    sequence or as a mapping whose entries are the decisions, and either way this reader
    hands back the decision mappings in declared order.
    """
    value = required(episode, "an episode record (records.md §5)", "decisions", "decision")
    entries = list(value.values()) if isinstance(value, Mapping) else list(value)
    out = []
    for entry in entries:
        if isinstance(entry, Mapping):
            out.append(entry)
        elif isinstance(entry, (list, tuple)):
            out.extend(item for item in entry if isinstance(item, Mapping))
    return out


def decision_seat(decision):
    """The seat a decision belongs to, as one comparable token."""
    value = required(decision, "a decision record (records.md §5)", "seat")
    numbers = S.numbers(value)
    if numbers:
        return int(numbers[0])
    return tok(S.flatten_text(value))


def decision_reward(decision):
    """The reward a decision carries (zero except at that seat's terminal decision)."""
    value = required(decision, "a decision record (records.md §5)", "reward")
    numbers = S.numbers(value)
    return float(numbers[0]) if numbers else 0.0


# ---------------------------------------------------------------------------
# A table in which one member won every cell it played
# ---------------------------------------------------------------------------
def bounded_matrix(hands=S.LIVE_CELL_HANDS):
    """A matrix record in which one invented member won every cell (ASM-17).

    Built by hand to ``records.md`` §10's shape: a real table cannot be asked to
    produce a member without a finite maximum-likelihood rating on demand, and the
    fit must bound such a member rather than report an infinite value.  Its members
    are the three **anchor** baselines of D-6 and one invented version, so the rating's
    anchor still exists and the record is a consistent table of K = 4 and six cells: a
    folding baseline is a member of a pool only where a declaration names it, and this
    declaration names none (`records.md` §8, §10, ASM-17, ASM-32, D-21).
    """
    champion = "version-nimbus"
    members = list(S.ANCHOR_BASELINES) + [champion]
    button = hands // 2

    def direction(wins, losses, delta, held, other):
        return {
            "wins": wins,
            "ties": hands - wins - losses,
            "losses": losses,
            "mean_chip_delta": delta,
            "seat_split": {"button": held, "big blind": other},
        }

    cells = []

    def cell(left, right, left_wins, left_delta):
        cells.append({
            "members": [left, right],
            "hands": hands,
            "directions": [
                direction(left_wins, hands - left_wins, left_delta, button,
                          hands - button),
                direction(hands - left_wins, left_wins, -left_delta,
                          hands - button, button),
            ],
            "params": [0, 0],
            "seed": S.TABLE_SEED_B,
        })

    cell("random", "always-call", hands // 2 + 8, 0.25)
    cell("random", "oracle", hands // 2 - 12, -0.75)
    cell("always-call", "oracle", hands // 2 - 3, -0.5)
    cell(champion, "random", hands, 2.0)
    cell(champion, "always-call", hands, 2.0)
    cell(champion, "oracle", hands, 2.0)
    return {
        "members": members,
        "cells": cells,
        "hands_per_cell": hands,
        "table_seed": S.TABLE_SEED_B,
        "table": "live",
    }


# ---------------------------------------------------------------------------
# A shared, invented membership and table
# ---------------------------------------------------------------------------
def invented_versions(case, names=("kestrel", "bramble")):
    """The battery's own version records, each backed by a checkpoint it wrote."""
    return version_chain(case, names)


def _as_int(value, default):
    """An integer out of a value the battery itself wrote, or ``default``.

    The fixture builders read numbers they wrote, so a malformed one is a battery bug and
    not a finding against the implementation; this keeps such a value from raising inside
    a case body, which ``battery.md`` §2 forbids.
    """
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default
