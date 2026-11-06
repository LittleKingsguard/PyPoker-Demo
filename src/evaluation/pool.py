"""The bounded pool: `Pool`, `build_pool`, `pool_members` and `offer`
(`docs/L3/evaluation/pool.md`).

A pool is one ordered member list plus its bound, its frozen flag and its id -- both the
opposition the training loop samples and a table's rows and columns (D-16).  It is
opaque: a caller only passes it back to `pool_members`, `offer`, `opponent` and `matrix`
(`surface.md` §1).  Nothing here caches, registers or mutates: `offer` returns a new
pool and leaves its argument unchanged.

The baselines come first, in `agents.baselines()`'s order, each pinned with the `params`
of `0` the catalogue declares; then the version window, oldest to newest, ordered by the
lineage links and windowed to its last `m` (`pool.md` §2-§3).  The id is
``"pool-" + sha256("\\n".join(ordered ids)).hexdigest()[:16]`` and is a function of the
ordered member ids and of nothing else (`pool.md` §4).
"""

import hashlib
import numbers
import os
from collections.abc import Mapping

from .declarations import BASELINES, M
from .errors import (
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
)

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
# The id digest (`pool.md` §4)
# ---------------------------------------------------------------------------
def _pool_id(ids):
    """`"pool-" + sha256("\\n".join(ids)).hexdigest()[:16]` (`pool.md` §4, G2).

    The ordered member ids exactly as their records spell them, joined by a single
    ``"\\n"`` with no trailing separator; `m`, `frozen` and every other member field are
    excluded, so a corrected seed or step does not rename the pool.
    """
    payload = "\n".join(ids).encode("utf-8")
    return "pool-" + hashlib.sha256(payload).hexdigest()[:16]


# ---------------------------------------------------------------------------
# The lineage order (`pool.md` §3)
# ---------------------------------------------------------------------------
def _lineage_order(members):
    """The declaration's versions, oldest first, following `lineage == id` (§3, G4).

    One chain per link: two records carrying one id are refused (`MemberDuplicate`),
    two members descending from one are refused (`LineageConflict`), and a chain that
    reaches no start is refused (`LineageCycle`).  The chains are concatenated in the
    order their starts were declared, each oldest to newest.
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
    lineage_of = {}
    for position, member in enumerate(members):
        lineage = member["lineage"]
        lineage_of[member["id"]] = lineage
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

    order = []
    visited = set()
    for start in starts:
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
            order.append(dict(member))
            following = successors.get(member["id"])
            position = following

    if len(order) != len(members):
        for member in members:
            if member["id"] not in visited:
                raise LineageCycle(
                    "build_pool(member %r): the lineage order reaches no start, because "
                    "the chain through %r closes on itself"
                    % (member["id"], member["id"])
                )
    return order


# ---------------------------------------------------------------------------
# One member, as `records.md` §7 declares a version
# ---------------------------------------------------------------------------
def _text(record, key, label, entry="build_pool"):
    """One of a member's two declaring fields: `id` or `lineage` (§2 item 1, §8)."""
    if key not in record:
        raise MemberInvalid(
            "%s(member %r): the member is missing the required key %r"
            % (entry, label, key)
        )
    value = record[key]
    if not isinstance(value, str) or not value or "\n" in value or "\r" in value:
        raise MemberInvalid(
            "%s(member %r): the %s must be a non-empty string without a "
            "newline, got %r" % (entry, label, key, value)
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

    The declaration's three keys are all required; `m` may be tighter than the league's
    M and never wider; the versions are ordered by their lineage links and windowed to
    their last `m`; the three baselines are added first, pinned, and the id is
    computed.  A declaration richer than the bound is windowed, never refused
    (`errors.md` §5).  A declared `id` that is one of the three pinned baselines' names
    is refused, because the baselines are prepended here and the membership would then
    carry that id twice (`pool.md` §2 item 1, §8).
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
    records = [_check_member(record, position) for position, record in enumerate(declared)]
    # A version declared under a pinned baseline's name: the baselines are prepended
    # below, so the membership would name that id twice (`pool.md` §2 item 1, §8).
    for member in records:
        if member["id"] in BASELINES:
            raise MemberDuplicate(
                "build_pool(member %r): %r is one of the three pinned baselines' names, "
                "and a pool names one member once" % (member["id"], member["id"])
            )
    for member in records:
        _check_path(member)

    ordered = _lineage_order(records)
    window = ordered[-bound:] if len(ordered) > bound else ordered

    members = tuple(_baseline_member(name) for name in BASELINES) + tuple(window)
    ids = [member["id"] for member in members]
    return Pool(_pool_id(ids), bound, frozen, members)


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


def pool_members(pool):
    """`records.md` §8's pool record, freshly built on every call (§6, `pool.md` §5).

    A caller that edits the returned record changes nothing, and a frozen pool's
    read-back does not change while it is used -- which is how a pair's parity is read.
    """
    _require_pool(pool, "pool_members")
    return {
        "id": pool.id,
        "m": pool.m,
        "frozen": bool(pool.frozen),
        "members": tuple(dict(member) for member in pool.members),
    }


# ---------------------------------------------------------------------------
# `offer` (`surface.md` §7)
# ---------------------------------------------------------------------------
def offer(pool, version):
    """The pool advanced by one version: the window rolls, the baselines stay (§7).

    The version joins the window at its head, the oldest version leaves when the window
    already holds `m`, and the id is recomputed; the argument pool is unchanged.  A
    frozen pool, a version already a member and a version whose lineage does not extend
    the window's newest are refused (`pool.md` §6).
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

    versions = [member for member in pool.members if not member.get("baseline")]
    if versions:
        newest = versions[-1]["id"]
        if offered["lineage"] != newest:
            raise LineageNotExtended(
                "offer(version %r): its lineage %r is not the window's newest member %r"
                % (offered["id"], offered["lineage"], newest)
            )

    window = versions + [offered]
    if len(window) > pool.m:
        window = window[-pool.m:]
    members = tuple(_baseline_member(name) for name in BASELINES) + tuple(window)
    ids = [member["id"] for member in members]
    return Pool(_pool_id(ids), pool.m, pool.frozen, members)
