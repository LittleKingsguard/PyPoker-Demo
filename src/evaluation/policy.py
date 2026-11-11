"""The sides a cell plays: a member policy, `policy_from`, `opponent` and `_side`
(`docs/L3/evaluation/scheduler.md` §5-§5.1, `surface.md` §2, §8, §12).

A **policy** is a callable taking ``(readout, legal_actions)`` and returning one
descriptor from ``legal_actions``; this module calls policies and imports none
(`surface.md` §2).  A side is resolved once, before any hand is played, to
``(id, policy, params, unlabelled, rule, utility, game)``: a baseline is built at the seed
the caller fixes, a version member is built from the **three** facts its own checkpoint
records -- the seed, the encoding name and the shape -- and an opaque callable handed in
from outside is named for its position and its capacity is recorded as an unmeasured ``0``
(`scheduler.md` §5, ASM-10).

The two **catalogue members** travel with the side: a policy built from a learner carries
the rule its learner was built under and the utility whose reward it was trained on, so a
cell can say which two estimators and which two objectives met, and a baseline or an
opaque callable carries neither (`e2e-surface.md` §2, `rules.md` §7, `utilities.md` §7,
D-19, D-20).  The **shape** travels with it too, and a **baseline** carries none: a
baseline is shape-silent, so it plays whatever shape the hands are dealt on (`shape.md`
§4).  A member **record** that declares a `rule`, a `utility` or a `game` is compared with
the member its policy carries and a disagreement is refused naming the member and both
values (`scheduler.md` §5, ASM-20, `shape.md` §3).

`policy_from` reads **exactly** three facts from the checkpoint's own container and nothing
else: the seed, the encoding name and the shape.  The learner, its parameters, its rule and
its utility stay `agents.load`'s and `agents.as_policy`'s -- the members a member reports
are the ones the policy `agents.as_policy` built carries, which are the ones the file
records (ASM-20, `rules.md` §6, `utilities.md` §6, G20).  No seed is ever substituted for a
missing one, and no seed is a digest of a path.  A recorded encoding name is checked by
**building** it for the recorded shape -- `features.build_encoder` is the granted arrow and
no encoding catalogue is read (`scheduler.md` §5.1, `module-map.md` §2).

`policy_from`'s second argument is the **exploration mode**: `schedule` is today's keyed
draw and `off` is the masked maximum and the tie-break alone, with no generator drawn from,
so a census computed over it is a function of the model and not of a seed (`shape.md` §5,
`docs/L1/sizing.md` §4, D-29).

`opponent`'s third argument is the **draw count** and its absence is today's call: one
policy for one training hand.  Named, it draws that many **distinct** pool members without
replacement, in the draw's order, which is what seats five opponents in a six-seat hand;
a pool holding fewer is refused naming both counts (`docs/L1/seats.md` §4, `league.md` §2,
ASM-43).  Both arms build a drawn **baseline** for the pool's own shape, so a six-seat
pool's `fold-large-bet` reads 100 and its oracle is asked a six-way question
(`seats.md` §2, §6, ASM-31, D-33).
"""

import hashlib
import json
import numbers
import os
import zipfile
from collections.abc import Mapping

import agents
import features

from .declarations import (
    EXPLORATION_DEFAULT,
    require_exploration,
    require_shape,
)
from .errors import (
    CheckpointRecordMissing,
    CheckpointUnreadable,
    DrawExceedsMembership,
    InvalidDrawCount,
    InvalidPool,
    InvalidSeed,
    MemberInvalid,
    MemberUnloadable,
    RuleMismatch,
    ShapeMismatch,
    UnknownEncoding,
    UtilityMismatch,
)
from .pool import Pool, _rule, _utility
from .seeds import _draw_index, _draw_order

#: The deepest a recorded fact is looked for in one JSON document (`scheduler.md` §5.1).
_MAX_DEPTH = 8


class _MemberPolicy:
    """One member as a policy: its id, its capacity, the callable, its rule, utility and shape.

    A pool and a policy are opaque values a caller only passes back (`surface.md` §1);
    this carries the member's id and parameter count so a cell can name it and report its
    capacity, the catalogue member its learner was built under, so a cell records which
    estimator it met, the catalogue member whose reward it was trained on, so the same cell
    records which objective it met, and the **shape** its container records, so a cell says
    which game it was played on (`scheduler.md` §4-§5, `rules.md` §7, `utilities.md` §7,
    `shape.md` §4, D-19, D-20, D-29).
    """

    __slots__ = (
        "member_id",
        "params",
        "policy",
        "unlabelled",
        "learning_rule",
        "utility",
        "game",
    )

    def __init__(
        self,
        member_id,
        params,
        policy,
        unlabelled=False,
        learning_rule=None,
        utility=None,
        game=None,
    ):
        self.member_id = member_id
        self.params = int(params)
        self.policy = policy
        self.unlabelled = bool(unlabelled)
        self.learning_rule = learning_rule
        self.utility = utility
        # The shape whose vocabulary this member's descriptor is decoded in: the one its
        # container records, or `None` for a value this module did not build from a file
        # (`shape.md` §4, `scheduler.md` §5).
        self.game = game

    def __call__(self, readout, legal_actions):
        return self.policy(readout, legal_actions)

    def __repr__(self):
        return "_MemberPolicy(member_id=%r, params=%r, learning_rule=%r, utility=%r, game=%r)" % (
            self.member_id,
            self.params,
            self.learning_rule,
            self.utility,
            self.game,
        )


def _token(text):
    """A key reduced to its letters and digits (`scheduler.md` §5.1's normalized form)."""
    return "".join(ch for ch in str(text).lower() if ch.isalnum())


def _is_int(value):
    """An integer, a NumPy integer included, but never a `bool` (`errors.md` §5)."""
    return isinstance(value, numbers.Integral) and not isinstance(value, bool)


# ---------------------------------------------------------------------------
# The three facts a checkpoint records, and the reader that finds them (§5.1)
# ---------------------------------------------------------------------------
def _read_documents(path, entry, where):
    """Every JSON document a checkpoint's container holds, in `namelist()` order."""
    try:
        archive = zipfile.ZipFile(path, "r")
    except Exception:
        raise CheckpointUnreadable(
            "%s(%s): %r names no readable file, or no readable zip"
            % (entry, where, path)
        )
    documents = []
    try:
        for name in archive.namelist():
            if not os.path.basename(name).lower().endswith(".json"):
                continue
            try:
                payload = archive.read(name)
            except Exception:
                continue
            try:
                documents.append(json.loads(payload.decode("utf-8")))
            except Exception:
                continue
    finally:
        archive.close()
    return documents


def _checkpoint_facts(path, entry, where):
    """The recorded seed, encoding-name and shape candidates, or `CheckpointRecordMissing`.

    A plain zip of `metadata.json` and `parameters.npy` is the container established
    empirically; the walk tolerates names it did not observe, matching a key by its
    normalized form (exactly `seed` / `encoding`, then by suffix), depth-first in document
    order to depth 8.  The **shape** is matched by that form being **exactly `game`** with
    a string value -- never by suffix, so a key that merely ends in `game` cannot move a
    member to another shape -- and an absent one is `DEFAULT_SHAPE`, which is what keeps
    the 18 shipped version-1 containers loadable (`scheduler.md` §5.1, `shape.md` §2,
    `docs/L1/shapes.md` §3, §5).  The encoding names come back as the walk collected them,
    in document order, because the name is checked by building it and not by a catalogue.
    """
    if not isinstance(path, str) and not isinstance(path, os.PathLike):
        raise CheckpointUnreadable(
            "%s(%s): %r names no readable file, or no readable zip"
            % (entry, where, path)
        )
    readable = False
    try:
        readable = os.path.isfile(path) and os.access(path, os.R_OK)
    except OSError:
        readable = False
    if not readable:
        raise CheckpointUnreadable(
            "%s(%s): %r names no readable file, or no readable zip"
            % (entry, where, path)
        )

    documents = _read_documents(path, entry, where)

    found_seed = []
    encodings = []
    shapes = []

    def walk(value, depth):
        if depth > _MAX_DEPTH:
            return
        if isinstance(value, Mapping):
            for key, inner in value.items():
                name = _token(key)
                if (name == "seed" or name.endswith("seed")) and _is_int(inner):
                    found_seed.append(int(inner))
                elif (name == "encoding" or name.endswith("encoding")) and isinstance(
                    inner, str
                ):
                    encodings.append(inner)
                elif name == "game" and isinstance(inner, str):
                    # The shape is matched by its form being **exactly** `game`: a suffix
                    # match would let `game_config` or `endgame` move a member to another
                    # shape (`scheduler.md` §5.1, `shape.md` §2).
                    shapes.append(inner)
                walk(inner, depth + 1)
        elif isinstance(value, (list, tuple)):
            for inner in value:
                walk(inner, depth + 1)

    for document in documents:
        walk(document, 0)

    if not found_seed:
        raise CheckpointRecordMissing(
            "%s(%s): the checkpoint %r records no seed, and no seed is ever "
            "substituted for a missing one" % (entry, where, path)
        )
    if not encodings:
        raise CheckpointRecordMissing(
            "%s(%s): the checkpoint %r records no encoding name, and no encoder is ever "
            "substituted for a missing one" % (entry, where, path)
        )
    # Absent reads as the default shape; a name the catalogue does not carry is refused
    # naming the path, the name and the declared names, and is never defaulted
    # (`shape.md` §2-§3, `scheduler.md` §5.1, §6).
    game = require_shape(shapes[0] if shapes else None, entry, where)
    return found_seed[0], tuple(encodings), game


def _built_encoder(names, game, entry, where, path):
    """The encoder the recorded names build **for the recorded shape**, and the name it took.

    The candidates the walk collected are offered to `features.build_encoder` in the order
    they were collected -- as `features.build_encoder(name, shape=game)`, since a
    descriptor decodes only in the vocabulary that declared it -- and the first name it
    accepts is the encoder; building it is the only test a recorded name passes, so no
    catalogue is read (`module-map.md` §2, `shape.md` §4).  A name
    `features.build_encoder` refuses is this module's own `UnknownEncoding`; when none is
    accepted the message names the first candidate and the shape it was built for.
    """
    for name in names:
        try:
            return name, features.build_encoder(name, shape=game)
        except Exception:
            continue
    raise UnknownEncoding(
        "%s(%s): the checkpoint %r records the encoding %r for the shape %r, and "
        "features.build_encoder refuses that name"
        % (entry, where, path, names[0], game)
    )


def _checkpoint_policy(member_id, path, entry, where, exploration=EXPLORATION_DEFAULT):
    """One member policy, built at the seed, encoding and shape its container records.

    The order is path, facts, name, load (`scheduler.md` §6): the three recorded facts are
    read first, the encoder is built for the first recorded name `features.build_encoder`
    accepts **and for the recorded shape**, `agents.load` restores the learner (its refusal
    propagated unchanged) and `agents.as_policy` makes the decision policy at the
    exploration mode it was handed.  The one catch this module declares is the encoder's: a
    recorded name `build_encoder` refuses and `as_policy`'s refusal of the encoder that name
    builds are both re-raised as `UnknownEncoding` (§5.1).  The shape is the container's and
    travels on the returned policy, so a cell can say which game it was played on
    (`shape.md` §4, D-29).
    """
    seed, encodings, game = _checkpoint_facts(path, entry, where)
    encoding, encoder = _built_encoder(encodings, game, entry, where, path)
    learner = agents.load(None, path)
    try:
        policy = agents.as_policy(learner, encoder, seed, exploration)
    except Exception as exc:
        raise UnknownEncoding(
            "%s(%s): the checkpoint %r records the encoding %r, and agents.as_policy "
            "refused the encoder that name builds (%s)"
            % (entry, where, path, encoding, exc)
        ) from exc
    return _MemberPolicy(
        member_id,
        agents.param_count(learner),
        policy,
        # The rule the file records, reported by the policy `agents.as_policy` built:
        # playback is rule-free, so the built policy is the witness (`rules.md` §6, D-19).
        learning_rule=getattr(policy, "learning_rule", None),
        # ... and the utility it records, on the same terms: playback is utility-free
        # too, so the policy is again the only witness (`utilities.md` §6, §7, D-20).
        utility=getattr(policy, "utility", None),
        # ... and the shape its container records, read by the walk because a container's
        # shape has no attribute to read it back from (`scheduler.md` §5.1, `shape.md` §4).
        game=game,
    )


def _member_policy(record, entry, label=None, what="played", noun="member"):
    """A `records.md` §7 version record as a policy: `policy_from`'s own builder (§5).

    A record that declares a `rule` is held to it, one that declares a `utility` is held
    to that too, and one that declares a `game` is held to the shape its container records:
    the policy is built from the checkpoint, and a value that disagrees with the one the
    policy carries is refused naming the member and both values -- `ShapeMismatch` for the
    shape on exactly the rule's and the utility's terms, after the load and before a hand
    (`scheduler.md` §5, `records.md` §7, `rules.md` §6, `utilities.md` §6, `shape.md` §3,
    D-19, D-20, D-29).  A record declaring none of the three is admitted -- the container
    decides, and the members the policy reports are the members the file records -- while
    an uncatalogued `game` is `UnknownShape`, refused with the cheap checks because it
    needs no load (`shape.md` §2).
    """
    member_id = record.get("id")
    if member_id is not None and (not isinstance(member_id, str) or not member_id):
        member_id = None
    subject = "member %r" % (member_id,) if member_id else (label or "member")
    if label and member_id and label != member_id:
        where = "%s, %s" % (label, subject)
    else:
        where = subject
    declared = _rule(record, where, entry, required=False)
    declared_utility = _utility(record, where, entry, required=False)
    # The declared shape is read before the load -- an uncatalogued name needs no
    # checkpoint -- and held to the container's afterwards (`scheduler.md` §5-§6,
    # `shape.md` §2-§3).
    declared_game = require_shape(record.get("game"), entry, where)
    path = record.get("path")
    if not path:
        raise MemberUnloadable(
            "%s(%s): the %s carries no path, so it cannot be %s"
            % (entry, where, noun, what)
        )
    policy = _checkpoint_policy(member_id or label or "member", path, entry, where)
    if declared is not None and policy.learning_rule != declared:
        raise RuleMismatch(
            "%s(%s): the member records the rule %r and its checkpoint %r records %r, "
            "and a member is trained under one rule"
            % (entry, where, declared, path, policy.learning_rule)
        )
    if declared_utility is not None and policy.utility != declared_utility:
        raise UtilityMismatch(
            "%s(%s): the member records the utility %r and its checkpoint %r records "
            "%r, and a member is trained under one objective"
            % (entry, where, declared_utility, path, policy.utility)
        )
    if policy.game != declared_game:
        raise ShapeMismatch(
            "%s(%s): the member records the shape %r and its checkpoint %r records %r, "
            "and a member is played on one shape"
            % (entry, where, declared_game, path, policy.game)
        )
    return policy


def _artefact_id(path):
    """The bare-artefact id `policy_from` gives a path: one checkpoint, one member id."""
    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
    return "ckpt-" + digest


# ---------------------------------------------------------------------------
# `policy_from` (`surface.md` §12)
# ---------------------------------------------------------------------------
def policy_from(path, exploration=EXPLORATION_DEFAULT):
    """A checkpoint as a policy in evaluation mode, at the seed its container records.

    The learner is never trained, never updated and never frozen from its exploration;
    it holds the state the checkpoint holds, so it decides as its learner decided
    (`surface.md` §12, ASM-5).  It plays no hand and moves no stream.

    The optional second argument is the **exploration mode**, whose absence is today's
    behaviour: `schedule` is the keyed draw of the exploration schedule `agents.as_policy`
    makes, and `off` is the masked maximum and the tie-break alone, with no generator
    drawn from -- so at `off` two policies at two seeds decide identically and the answer
    is a function of the model and not of a seed (`shape.md` §5, `docs/L1/sizing.md` §4,
    D-29).  A mode outside the two is `UnknownExploration` naming it and both modes,
    refused before a checkpoint is touched (`scheduler.md` §6).
    """
    mode = require_exploration(exploration, "policy_from")
    return _checkpoint_policy(
        _artefact_id(path), path, "policy_from", "path", mode
    )


# ---------------------------------------------------------------------------
# `opponent` (`surface.md` §8)
# ---------------------------------------------------------------------------
def _drawn(pool, member, seed):
    """One drawn member as a policy: a baseline of the **pool's** shape, or a version policy.

    A baseline is `agents.build_baseline(name, seed, pool.game)`: the pool's one shape is
    passed on, so `fold-large-bet` reads **that** shape's starting stack -- 100 on the
    six-seat row, so "half the stack" is 50 -- and the oracle prices a readout whose
    `stacks` carry that shape's seats (`seats.md` §2, §4, §6, ASM-31, D-33).  On the
    default shape the named shape and the absent one are one policy, so a two-argument
    draw is today's draw (`shape.md` §2, `seats.md` §6).  A version is the member policy
    its own container records, whose shape the record is held to (`pool.md` §7,
    `shape.md` §3-§4).
    """
    if member.get("baseline"):
        return agents.build_baseline(member["id"], int(seed), pool.game)
    return _member_policy(member, "opponent", what="an opponent", noun="drawn member")


def opponent(pool, seed, count=None):
    """One pool member drawn by ``seed % n``, or ``count`` distinct members in draw order.

    **Without a count** it is today's call, unchanged: one policy drawn from the pool's
    ordered membership by the seed, a baseline at the caller's seed and a version at the
    seed its checkpoint records, so one pool and one seed draw one opponent that answers
    one decision one way (`surface.md` §8, `pool.md` §7).

    **With a count** it returns **that many distinct members**, drawn **without
    replacement** from the frozen pool, in the draw's order: the first is the member the
    uncounted draw names and the rest follow in `seeds._draw_order`'s keyed order, so the
    draw is reproducible from `(seed, membership)` and is a function of the pool's own
    ordered membership (`seats.md` §4, `league.md` §2, ASM-43).  A six-seat hand therefore
    seats five opponents and never one member twice (`seats.md` §4, D-33).  A pool holding
    fewer members than the draw is **refused naming both counts**, because a substitute
    seat would be an opponent the membership does not carry (`records.md` §8, ASM-43).
    """
    if not isinstance(pool, Pool):
        raise InvalidPool(
            "opponent(pool): the argument must be a pool from build_pool or offer, got %s"
            % (type(pool).__name__,)
        )
    if not _is_int(seed):
        raise InvalidSeed("opponent(seed): the seed must be an integer, got %r" % (seed,))
    size = len(pool.members)
    if count is None:
        return _drawn(pool, pool.members[_draw_index(seed, size)], seed)
    if not _is_int(count) or int(count) < 1:
        raise InvalidDrawCount(
            "opponent(count): the draw count must be a positive integer, got %r" % (count,)
        )
    wanted = int(count)
    if wanted > size:
        raise DrawExceedsMembership(
            "opponent(count): the draw asks for %d distinct members and the pool holds %d, "
            "and a draw is without replacement because a substitute seat would be an "
            "opponent the membership does not carry" % (wanted, size)
        )
    return tuple(
        _drawn(pool, pool.members[position], seed)
        for position in _draw_order(seed, size)[:wanted]
    )


# ---------------------------------------------------------------------------
# `_side` (`scheduler.md` §5)
# ---------------------------------------------------------------------------
def _side(value, label, entry, seed=None, position=1):
    """One side of a cell, resolved to ``(id, policy, params, unlabelled, rule, utility, game)``.

    Seven elements, and every reader of a side unpacks seven (`scheduler.md` §5, G30).  A
    baseline name is built at ``seed``, declares neither catalogue member and names **no**
    shape -- a baseline is shape-silent (`shape.md` §4); a `records.md` §7 version record is
    built from its checkpoint's recorded facts and carries the rule, the utility and the
    shape the policy its file records reports; a `_MemberPolicy` this module built carries
    its own id, its capacity, both catalogue members and its container's shape; and any
    other callable is named ``policy-<position>`` with an unmeasured ``0`` and whatever
    ``learning_rule``, ``utility`` and ``game`` it carries itself, which is none of the
    three for an opaque callable (`surface.md` §2, `rules.md` §7, `utilities.md` §7,
    `shape.md` §3-§4, ASM-10, D-19, D-20, D-29).
    """
    if isinstance(value, _MemberPolicy):
        return (
            value.member_id,
            value,
            value.params,
            value.unlabelled,
            value.learning_rule,
            value.utility,
            value.game,
        )
    if isinstance(value, str):
        if value in agents.baselines():
            if seed is None:
                raise MemberInvalid(
                    "%s(%s): a baseline side needs the seed the cell is played at (%r)"
                    % (entry, label, value)
                )
            # A baseline names no shape: it answers whatever readout it is handed, so the
            # side is shape-silent (`shape.md` §4, `scheduler.md` §5).
            return (
                value,
                agents.build_baseline(value, int(seed)),
                0,
                False,
                None,
                None,
                None,
            )
        raise MemberInvalid(
            "%s(%s): the side must be a policy, a version record or one of %r, got %r"
            % (entry, label, tuple(agents.baselines()), value)
        )
    if isinstance(value, Mapping):
        member_id = value.get("id")
        if not isinstance(member_id, str) or not member_id:
            raise MemberInvalid(
                "%s(%s): the side is a version record and is missing the required key "
                "'id'" % (entry, label)
            )
        policy = _member_policy(dict(value), entry, label=label, what="played")
        return (
            member_id,
            policy,
            policy.params,
            False,
            policy.learning_rule,
            policy.utility,
            policy.game,
        )
    if callable(value):
        # An opaque callable names whatever its own `game` says and `None` for a plain
        # function; a name the catalogue does not carry is `UnknownShape`, never carried
        # into a cell (`shape.md` §2-§3, `scheduler.md` §5).
        game = getattr(value, "game", None)
        if game is not None:
            game = require_shape(game, entry, label)
        return (
            "policy-%d" % position,
            value,
            0,
            True,
            getattr(value, "learning_rule", None),
            getattr(value, "utility", None),
            game,
        )
    raise MemberInvalid(
        "%s(%s): the side must be a policy, a version record or one of %r, got %r"
        % (entry, label, tuple(agents.baselines()), value)
    )
