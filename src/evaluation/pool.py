"""The bounded pool: `Pool`, `build_pool`, `pool_members` and `offer`
(`docs/L3/evaluation/pool.md`, `docs/L3/evaluation/families.md`).

A pool is one ordered member list plus its bound, its frozen flag and its id -- both the
opposition the training loop samples and a table's rows and columns (D-16).  It is
opaque: a caller only passes it back to `pool_members`, `offer`, `opponent` and `matrix`
(`surface.md` §1).  Nothing here caches, registers or mutates: `offer` returns a new
pool and leaves its argument unchanged.

The baselines come first, each pinned with the `params` of `0` the catalogue declares:
the **flagged three** of `agents.baselines()` -- the catalogue's `anchor: True` members --
in the catalogue's order, and then, only when the declaration's optional `baselines` key
names them, D-21's folders, still in the catalogue's order.  Every one of them is pinned
and never evicted, because eviction is the version window's (D-16, ASM-32, `records.md`
§8, D-21).  Then comes the version window, grouped into **families** -- one lineage chain
each, every member of it declaring one rule -- listed contiguously oldest to newest, the
families in the order they entered the window (`families.md` §1-§3, ASM-26).  The window
is bounded by `m`, and a full window evicts fair-share: the member that leaves is the
oldest of the family that currently holds the most (`families.md` §3).

Every version member declares its `rule` and its `utility`, the catalogue members it was
trained under, read from `agents.learners()`'s two catalogues through the granted arrow
and never from a copy of the names (`rules.md` §2, §4, `utilities.md` §2, §5, D-19,
D-20).  The id is
``"pool-" + sha256(payload).hexdigest()[:16]`` where the payload is one line per member --
a baseline's id alone, a version's `id`, ``\\x1f``, then its `rule`, ``\\x1f``, then its
`utility` -- so a baselines-only pool keeps the id it had and two pools of one membership
under two estimators or two objectives do not wear one id (`families.md` §4, ASM-27).
A declaration that names no folder therefore digests exactly as it did before D-21.
"""

import hashlib
import numbers
import os
from collections.abc import Mapping

import agents

from .declarations import BASELINES, CATALOGUE, M
from .errors import (
    FamilyBoundExceeded,
    InvalidPool,
    LineageConflict,
    LineageCycle,
    MemberDuplicate,
    MemberInvalid,
    MemberUnloadable,
    PoolBoundInvalid,
    PoolDeclarationInvalid,
    PoolFrozen,
    LineageNotExtended,
    RuleMismatch,
    UnknownBaseline,
    UnknownRule,
    UnknownUtility,
    UtilityMismatch,
)

#: The digest's field separator: a version's line carries its id, this, its rule, this,
#: then its utility, and no field may contain it (`families.md` §4, ASM-27).
SEPARATOR = "\x1f"


class Pool:
    """One pool: its id, its bound, its frozen flag and its ordered members.

    Immutable in use -- `offer` builds a new one -- and opaque: no record returned here
    exposes it, and a caller only hands it back (`pool.md` §1, `surface.md` §1).
    """

    __slots__ = ("id", "m", "frozen", "members")

    def __init__(self, pool_id, m, frozen, members):
        self.id = pool_id
        self.m = m
        self.frozen = frozen
        self.members = members

    def __repr__(self):
        return "Pool(id=%r, m=%r, frozen=%r, members=%r)" % (
            self.id,
            self.m,
            self.frozen,
            tuple(member.get("id") for member in self.members),
        )


# ---------------------------------------------------------------------------
# The two catalogues, through the granted arrow (`rules.md` §2, `utilities.md` §2)
# ---------------------------------------------------------------------------
def _catalogue():
    """`agents.learners()`'s learning-rule catalogue, its member names in declared order.

    The names are read here and never copied into this module: a copy would be a second
    catalogue that drifts from the one a learner spec selects from (`rules.md` §4,
    `module-map.md` §2, D-19).
    """
    declared = agents.learners()
    catalogue = declared.get("learning_rules") if isinstance(declared, Mapping) else None
    if isinstance(catalogue, Mapping):
        return tuple(str(name) for name in catalogue)
    return ()


def _utility_catalogue():
    """`agents.learners()`'s utility catalogue, its member names in declared order.

    The utility side of :func:`_catalogue`, on the same terms: read through the granted
    arrow on every call and never restated here, so a name this module accepts is a
    name `agents.build_learner` accepts (`utilities.md` §2, §5, `module-map.md` §2,
    D-20).
    """
    declared = agents.learners()
    catalogue = declared.get("utilities") if isinstance(declared, Mapping) else None
    if isinstance(catalogue, Mapping):
        return tuple(str(name) for name in catalogue)
    return ()


# ---------------------------------------------------------------------------
# The pinned baselines of one membership (`records.md` §8, ASM-32, D-21)
# ---------------------------------------------------------------------------
def _declared_baselines(declaration):
    """The catalogue names a declaration admits beyond the pinned set (`records.md` §8).

    The optional `baselines` key is a sequence of catalogue names; absent, `None` or
    empty means the flagged three and nothing else, so a pool built from such a
    declaration keeps the membership, the order and the id it has today.  A name outside
    the catalogue is refused **by name**, because a membership that named a rule which
    does not exist would be a table row this module could not build; naming a pinned
    anchor is accepted and adds nothing, the three being members whether a declaration
    names them or not (ASM-32, D-21, `errors.md` §4).
    """
    declared = declaration.get("baselines")
    if declared is None:
        return ()
    if isinstance(declared, (str, bytes)) or not hasattr(declared, "__iter__"):
        raise PoolDeclarationInvalid(
            "build_pool(baselines): the declared baselines must be a sequence of the "
            "catalogue's names %r, got %r" % (CATALOGUE, declared)
        )
    names = []
    for name in declared:
        if not isinstance(name, str) or name not in CATALOGUE:
            raise UnknownBaseline(
                "build_pool(baselines): the baseline %r is not one of the catalogue's %r"
                % (name, CATALOGUE)
            )
        if name not in names:
            names.append(name)
    return tuple(names)


def _pinned(declared):
    """The pinned baseline ids: the flagged three first, then the declared folders.

    Both are in `agents.baselines()`'s order, so a pool's first members are the
    catalogue's order and never the declaration's, and no baseline is ever evicted
    (`records.md` §8, `league.md` §2, ASM-32, ASM-33, D-21).
    """
    admitted = set(declared) - set(BASELINES)
    return tuple(BASELINES) + tuple(name for name in CATALOGUE if name in admitted)


# ---------------------------------------------------------------------------
# The id digest (`families.md` §4, ASM-27)
# ---------------------------------------------------------------------------
def _member_line(member):
    """One member's line of the digest payload: a baseline's id alone, a version's, its rule and its utility."""
    if member.get("baseline"):
        return member["id"]
    return "%s%s%s%s%s" % (
        member["id"],
        SEPARATOR,
        member["rule"],
        SEPARATOR,
        member["utility"],
    )


def _pool_id(members):
    """`"pool-" + sha256(payload).hexdigest()[:16]` over the ordered member lines.

    One line per member, in the pool's order: a baseline contributes its id alone and a
    version contributes its id, ``\\x1f``, then its `rule`, ``\\x1f``, then its
    `utility`; lines joined by one ``"\\n"`` with no trailing separator.  `m`, `frozen`
    and every other member field stay outside it, so a corrected seed or step does not
    rename the pool, and a baselines-only pool digests exactly as it did before either
    catalogue existed (`families.md` §4, ASM-27, D-19, D-20).
    """
    payload = "\n".join(_member_line(member) for member in members).encode("utf-8")
    return "pool-" + hashlib.sha256(payload).hexdigest()[:16]


# ---------------------------------------------------------------------------
# The families and the ordered window (`families.md` §1-§3, ASM-26)
# ---------------------------------------------------------------------------
def _families(members):
    """The declaration's versions grouped into families, oldest first, in entry order.

    A family is one lineage chain: its label is the start its first member names, and all
    its members declare one rule **and one utility** (§1).  Two records carrying one id are
    refused (`MemberDuplicate`), two members descending from one are refused
    (`LineageConflict`), a chain that reaches no start is refused (`LineageCycle`), a chain
    whose members declare two rules is refused naming the member and both rules
    (`RuleMismatch`), and a chain whose members declare two utilities is refused on the
    same terms (`UtilityMismatch`, D-20).  The families are ordered by the position of
    each one's start in the declaration, which is what makes "the order they entered the
    window" a declared fact (§2).
    """
    index = {}
    for position, member in enumerate(members):
        member_id = member["id"]
        if member_id in index:
            raise MemberDuplicate(
                "build_pool(member %r): %r appears in two member records, and a pool "
                "names one member once" % (member_id, member_id)
            )
        index[member_id] = position

    successors = {}
    for position, member in enumerate(members):
        lineage = member["lineage"]
        if lineage in index:
            if lineage in successors:
                earlier = members[successors[lineage]]["id"]
                raise LineageConflict(
                    "build_pool(member %r): %r is the lineage of two members, %r and "
                    "%r, so the window would have two successors for one link"
                    % (member["id"], lineage, earlier, member["id"])
                )
            successors[lineage] = position

    starts = [
        position
        for position, member in enumerate(members)
        if member["lineage"] not in index
    ]

    families = []
    visited = set()
    for start in starts:
        chain = []
        position = start
        while position is not None:
            member = members[position]
            if member["id"] in visited:
                raise LineageCycle(
                    "build_pool(member %r): the lineage order reaches no start, because "
                    "the chain through %r closes on itself"
                    % (member["id"], member["id"])
                )
            visited.add(member["id"])
            chain.append(dict(member))
            position = successors.get(member["id"])
        families.append(
            {
                "label": chain[0]["lineage"],
                "rule": chain[0]["rule"],
                "utility": chain[0]["utility"],
                "members": chain,
            }
        )

    if len(visited) != len(members):
        for member in members:
            if member["id"] not in visited:
                raise LineageCycle(
                    "build_pool(member %r): the lineage order reaches no start, because "
                    "the chain through %r closes on itself"
                    % (member["id"], member["id"])
                )

    for family in families:
        for member in family["members"]:
            if member["rule"] != family["rule"]:
                raise RuleMismatch(
                    "build_pool(member %r): the rule %r is not the rule %r of the family "
                    "it extends, whose start is %r"
                    % (
                        member["id"],
                        member["rule"],
                        family["rule"],
                        family["label"],
                    )
                )
            if member["utility"] != family["utility"]:
                raise UtilityMismatch(
                    "build_pool(member %r): the utility %r is not the utility %r of the "
                    "family it extends, whose start is %r"
                    % (
                        member["id"],
                        member["utility"],
                        family["utility"],
                        family["label"],
                    )
                )
    return families


def _window_families(versions):
    """A window's versions grouped into contiguous chains, oldest first (§2 step 2).

    The window is written as each family's members contiguously, oldest to newest, the
    families in the order they entered -- so a member whose lineage is not its
    predecessor's id begins a new family, and the grouping needs nothing but the records.
    """
    families = []
    for member in versions:
        if families and member["lineage"] == families[-1][-1]["id"]:
            families[-1].append(member)
        else:
            families.append([member])
    return families


def _evict(chains):
    """Evict fair-share: the oldest member of the family that holds the most (§3).

    Ties are broken by which family's oldest member is the older, which -- the families
    being listed in entry order, oldest first -- is the earlier family.  The family that
    holds the most has at least two members whenever an eviction is due, so this never
    empties a family while another holds two or more (§3, ASM-26).
    """
    largest = 0
    for index in range(1, len(chains)):
        if len(chains[index]) > len(chains[largest]):
            largest = index
    chains[largest].pop(0)
    return chains


def _window(families, bound, entry):
    """The ordered version window of a declaration, windowed to ``bound`` (§3).

    A declaration holding more families than the bound is refused by name, because
    windowing could not keep one member of each; a richer declaration of a number of
    families the bound allows is windowed by the eviction rule `offer` uses, so one
    family's chain behaves exactly as the last ``m`` of that chain did before the
    catalogue existed (§3, `pool.md` §2 step 4).
    """
    if len(families) > bound:
        raise FamilyBoundExceeded(
            "%s(m): the declaration holds %d families, and a window of %d cannot keep one "
            "member of each" % (entry, len(families), bound)
        )
    chains = [list(family["members"]) for family in families]
    while sum(len(chain) for chain in chains) > bound:
        _evict(chains)
    return [member for chain in chains for member in chain]


# ---------------------------------------------------------------------------
# One member, as `records.md` §7 declares a version
# ---------------------------------------------------------------------------
def _text(record, key, label, entry="build_pool"):
    """One of a member's declaring fields: `id`, `lineage` or `rule` (§2 item 1, §8)."""
    if key not in record:
        raise MemberInvalid(
            "%s(member %r): the member is missing the required key %r"
            % (entry, label, key)
        )
    value = record[key]
    if (
        not isinstance(value, str)
        or not value
        or "\n" in value
        or "\r" in value
        or SEPARATOR in value
    ):
        raise MemberInvalid(
            "%s(member %r): the %s must be a non-empty string without a newline or the "
            "digest's separator, got %r" % (entry, label, key, value)
        )
    return value


def _rule(record, where, entry, required=True):
    """A version member's `rule`, checked against the catalogue (`rules.md` §4, D-19).

    A record that declares none is refused as a missing key when ``required`` and read as
    declaring none otherwise -- which is what an entry point handed a bare §7 record sees.
    A name the catalogue does not carry is refused by name, and never mapped onto the
    declared default (`rules.md` §4, ASM-26).
    """
    if "rule" not in record:
        if not required:
            return None
        raise MemberInvalid(
            "%s(%s): the member is missing the required key 'rule'" % (entry, where)
        )
    value = record["rule"]
    if (
        not isinstance(value, str)
        or not value
        or "\n" in value
        or "\r" in value
        or SEPARATOR in value
    ):
        raise MemberInvalid(
            "%s(%s): the rule must be a non-empty string without a newline or the "
            "digest's separator, got %r" % (entry, where, value)
        )
    catalogue = _catalogue()
    if value not in catalogue:
        raise UnknownRule(
            "%s(%s): the rule %r is not one of the catalogue's %r"
            % (entry, where, value, catalogue)
        )
    return value


def _utility(record, where, entry, required=True):
    """A version member's `utility`, checked against the catalogue (`utilities.md` §5, D-20).

    A record that declares none is refused as a missing key when ``required`` -- the
    version declaration of a membership (`build_pool`) and of an offered version
    (`offer`), where the pool must certify what its member was trained under and is the
    only witness of it -- and read as declaring none otherwise, which is what a bare §7
    record handed to an entry point sees (`policy.py`'s `_member_policy`), the checkpoint
    being the witness there.  The declared default speaks for a variant entry and a
    learner spec only, never for a pool member (`utilities.md` §5, `records.md` §7,
    D-20).  A name the catalogue does not carry is refused by name, and never mapped onto
    the declared default (`utilities.md` §5, ASM-26).
    """
    if "utility" not in record:
        if not required:
            return None
        raise MemberInvalid(
            "%s(%s): the member is missing the required key 'utility'" % (entry, where)
        )
    value = record["utility"]
    if (
        not isinstance(value, str)
        or not value
        or "\n" in value
        or "\r" in value
        or SEPARATOR in value
    ):
        raise MemberInvalid(
            "%s(%s): the utility must be a non-empty string without a newline or the "
            "digest's separator, got %r" % (entry, where, value)
        )
    catalogue = _utility_catalogue()
    if value not in catalogue:
        raise UnknownUtility(
            "%s(%s): the utility %r is not one of the catalogue's %r"
            % (entry, where, value, catalogue)
        )
    return value


def _check_member(record, position):
    """Validate one declared member's shape and return a copy of it (§2, §8)."""
    if not isinstance(record, Mapping):
        raise MemberInvalid(
            "build_pool(member %d): the member must be a mapping in the sense of "
            "records.md §7, got %r" % (position, record)
        )
    label = record.get("id")
    if not isinstance(label, str) or not label:
        label = "member %d" % position
    member = dict(record)
    member["id"] = _text(member, "id", label)
    member["lineage"] = _text(member, "lineage", member["id"])
    return member


def _check_path(member):
    """A declared `path` must name a readable file (`protocol.md` §5, `surface.md` §5)."""
    path = member.get("path")
    if path is None:
        return
    readable = isinstance(path, str) or isinstance(path, os.PathLike)
    if readable:
        try:
            readable = os.path.isfile(path) and os.access(path, os.R_OK)
        except OSError:
            readable = False
    if not readable:
        raise MemberUnloadable(
            "build_pool(member %r): the path %r names no readable file"
            % (member["id"], path)
        )


# ---------------------------------------------------------------------------
# `build_pool` (`surface.md` §5)
# ---------------------------------------------------------------------------
def build_pool(declaration):
    """One pool from one `records.md` §8 declaration (§5, `pool.md` §2).

    The declaration's three keys are all required and its optional `baselines` key names
    the catalogue baselines it admits beyond the flagged three; `m` may be tighter than
    the league's M and never wider; every version member declares its `rule` and its
    `utility`, each refused by name when the catalogue does not carry it and the `utility`
    refused by name when it is absent too, the pool being the only witness of the objective
    a member was trained under; the versions are grouped into families and ordered by
    their lineage links; the window is bounded to `m` by the fair-share eviction rule;
    the pinned baselines are added first -- the flagged three and then any declared
    folder, in the catalogue's order -- and the id is computed.  A declaration richer than
    the bound is windowed, never refused, unless it holds more families than the bound
    allows (`errors.md` §5).  A declared `id` that is one of the pinned baselines' names
    is refused, because the baselines are prepended here and the membership would then
    carry that id twice (`pool.md` §2 item 1, §8, ASM-32, D-21).
    """
    if not isinstance(declaration, Mapping):
        raise PoolDeclarationInvalid(
            "build_pool(declaration): the declaration must be a mapping, got %s"
            % (type(declaration).__name__,)
        )
    for key in ("members", "m", "frozen"):
        if key not in declaration:
            raise PoolDeclarationInvalid(
                "build_pool(declaration): the declaration is missing the required key %r"
                % (key,)
            )

    bound = declaration["m"]
    if isinstance(bound, bool) or not isinstance(bound, numbers.Integral):
        raise PoolBoundInvalid(
            "build_pool(m): the bound must be a positive integer no larger than the "
            "league's %d, got %r" % (M, bound)
        )
    bound = int(bound)
    if bound < 1 or bound > M:
        raise PoolBoundInvalid(
            "build_pool(m): the bound must be a positive integer no larger than the "
            "league's %d, got %r" % (M, declaration["m"])
        )

    frozen = declaration["frozen"]
    if not isinstance(frozen, bool) and not (
        type(frozen).__name__ in ("bool_", "bool8", "bool")
    ):
        raise PoolDeclarationInvalid(
            "build_pool(frozen): the frozen flag must be a boolean, got %r" % (frozen,)
        )
    frozen = bool(frozen)

    declared = declaration["members"]
    if isinstance(declared, (str, bytes)) or not hasattr(declared, "__iter__"):
        raise PoolDeclarationInvalid(
            "build_pool(members): the members entry must be a sequence of member "
            "records, got %r" % (declared,)
        )
    # The pinned set this declaration admits beyond the flagged three: read first, so a
    # name the catalogue does not carry is refused before a version is checked
    # (`records.md` §8, ASM-32, D-21).
    pinned = _pinned(_declared_baselines(declaration))
    records = [_check_member(record, position) for position, record in enumerate(declared)]
    # A version declared under a pinned baseline's name: the baselines are prepended
    # below, so the membership would name that id twice (`pool.md` §2 item 1, §8).
    for member in records:
        if member["id"] in pinned:
            raise MemberDuplicate(
                "build_pool(member %r): %r is one of the pinned baselines' names, and a "
                "pool names one member once" % (member["id"], member["id"])
            )
    for member in records:
        _check_path(member)
    for member in records:
        member["rule"] = _rule(member, "member %r" % (member["id"],), "build_pool")
    # Every version member declares the `utility` it was trained under, and one that names
    # none is refused by name, never read as the declared default: the pool is the
    # container that must certify it (`records.md` §7, §8, `utilities.md` §5, D-20).
    for member in records:
        member["utility"] = _utility(
            member, "member %r" % (member["id"],), "build_pool"
        )

    families = _families(records)
    window = _window(families, bound, "build_pool")

    members = tuple(_baseline_member(name) for name in pinned) + tuple(window)
    return Pool(_pool_id(members), bound, frozen, members)


def _baseline_member(name):
    """One pinned baseline member: its id is its name (`pool.md` §2 step 5, G3)."""
    return {"id": name, "baseline": True, "pinned": True, "params": 0}


# ---------------------------------------------------------------------------
# `pool_members` (`surface.md` §6)
# ---------------------------------------------------------------------------
def _require_pool(pool, entry):
    """The argument must be a pool this module built (`surface.md` §6, `errors.md` §2)."""
    if not isinstance(pool, Pool):
        raise InvalidPool(
            "%s(pool): the argument must be a pool from build_pool or offer, got %s"
            % (entry, type(pool).__name__)
        )


def _pool_rules(members):
    """The distinct rules the version members declare, in the window's order (§5).

    A baseline declares none -- it is a fixed rule, not a trained estimator -- so an
    empty tuple is R1's answer and the pool record's `rules` is the population a table
    over it measured (`records.md` §8, ASM-27).
    """
    seen = []
    for member in members:
        if member.get("baseline"):
            continue
        rule = member.get("rule")
        if isinstance(rule, str) and rule not in seen:
            seen.append(rule)
    return tuple(seen)


def _pool_utilities(members):
    """The distinct utilities the version members declare, in the window's order (§5).

    The utility side of :func:`_pool_rules`: a baseline declares none, so an empty tuple
    is R1's answer and the pool record's `utilities` is the objective population a table
    over it measured (`records.md` §8, `utilities.md` §7, ASM-27, D-20).
    """
    seen = []
    for member in members:
        if member.get("baseline"):
            continue
        utility = member.get("utility")
        if isinstance(utility, str) and utility not in seen:
            seen.append(utility)
    return tuple(seen)


def pool_members(pool):
    """`records.md` §8's pool record, freshly built on every call (§6, `pool.md` §5).

    A caller that edits the returned record changes nothing, and a frozen pool's
    read-back does not change while it is used -- which is how a pair's parity is read.
    `rules` and `utilities` are the two populations its version members declare.
    """
    _require_pool(pool, "pool_members")
    return {
        "id": pool.id,
        "m": pool.m,
        "frozen": bool(pool.frozen),
        "members": tuple(dict(member) for member in pool.members),
        "rules": _pool_rules(pool.members),
        "utilities": _pool_utilities(pool.members),
    }


# ---------------------------------------------------------------------------
# `offer` (`surface.md` §7)
# ---------------------------------------------------------------------------
def offer(pool, version):
    """The pool advanced by one version: one family rolls, the baselines stay (§7).

    The offered version extends exactly one family -- its lineage must be that family's
    **newest member**, or a label no member carries, which opens a new family
    (`families.md` §5, ASM-26).  A lineage naming a member that is not its family's newest
    would fork the chain and is refused; a version whose rule or whose utility differs from
    the family it extends is refused; a version that names no `utility` is refused as a
    missing required key, as a declared member's is; and a full window evicts fair-share, so
    no family is emptied while another holds two or more.  Opening the (m+1)th family is
    refused by name rather than emptying one.  The argument pool is unchanged (`pool.md`
    §6).
    """
    _require_pool(pool, "offer")
    if pool.frozen:
        raise PoolFrozen(
            "offer(pool): the pool is frozen and a frozen membership does not change "
            "while it is used"
        )
    if not isinstance(version, Mapping):
        raise MemberInvalid(
            "offer(version): the version must be a mapping in the sense of records.md "
            "§7, got %r" % (version,)
        )
    label = version.get("id")
    if not isinstance(label, str) or not label:
        label = "version"
    offered = dict(version)
    offered["id"] = _text(offered, "id", label, entry="offer")
    offered["lineage"] = _text(offered, "lineage", offered["id"], entry="offer")

    existing = [member["id"] for member in pool.members]
    if offered["id"] in existing:
        raise MemberDuplicate(
            "offer(version %r): %r is already a member of the pool"
            % (offered["id"], offered["id"])
        )
    offered["rule"] = _rule(
        offered, "version %r" % (offered["id"],), "offer"
    )
    # An offered version declares the `utility` it was trained under, as a declared member
    # does: one that names none is refused by name, never read as the declared default, so
    # every member of a pool carries the objective it was trained on and the id can certify
    # it (`utilities.md` §5, §6, ASM-27, D-20).
    offered["utility"] = _utility(
        offered, "version %r" % (offered["id"],), "offer"
    )

    versions = [dict(member) for member in pool.members if not member.get("baseline")]
    chains = _window_families(versions)
    target = None
    for index, chain in enumerate(chains):
        if chain[-1]["id"] == offered["lineage"]:
            target = index
            break
    if target is None:
        for chain in chains:
            for member in chain:
                if member["id"] == offered["lineage"]:
                    raise LineageNotExtended(
                        "offer(version %r): its lineage %r is not the newest member of its "
                        "family, which is %r"
                        % (offered["id"], offered["lineage"], chain[-1]["id"])
                    )
        if len(chains) + 1 > pool.m:
            raise FamilyBoundExceeded(
                "offer(version %r): the pool holds %d families under a bound of %d, so a "
                "new family would leave another without a member"
                % (offered["id"], len(chains), pool.m)
            )
        chains.append([offered])
    else:
        family_rule = chains[target][0].get("rule")
        if family_rule is not None and family_rule != offered["rule"]:
            raise RuleMismatch(
                "offer(version %r): the rule %r is not the rule %r of the family it "
                "extends, whose newest member is %r"
                % (
                    offered["id"],
                    offered["rule"],
                    family_rule,
                    chains[target][-1]["id"],
                )
            )
        family_utility = chains[target][0].get("utility")
        if family_utility is not None and family_utility != offered["utility"]:
            raise UtilityMismatch(
                "offer(version %r): the utility %r is not the utility %r of the family "
                "it extends, whose newest member is %r"
                % (
                    offered["id"],
                    offered["utility"],
                    family_utility,
                    chains[target][-1]["id"],
                )
            )
        chains[target].append(offered)

    while sum(len(chain) for chain in chains) > pool.m:
        _evict(chains)
    window = [member for chain in chains for member in chain]
    # The pool's pinned baselines are read back off its own members -- the flagged three
    # always, plus whatever folder its declaration admitted, in the catalogue's order --
    # so an offer rolls the version window and leaves every baseline exactly where it was
    # (`pool.md` §6, ASM-16, ASM-32, D-21).
    pinned = _pinned(
        [member["id"] for member in pool.members if member.get("baseline")]
    )
    members = tuple(_baseline_member(name) for name in pinned) + tuple(window)
    return Pool(_pool_id(members), pool.m, pool.frozen, members)
