"""The sides a cell plays: a member policy, `policy_from`, `opponent` and `_side`
(`docs/L3/evaluation/scheduler.md` §5-§5.1, `surface.md` §2, §8, §12).

A **policy** is a callable taking ``(readout, legal_actions)`` and returning one
descriptor from ``legal_actions``; this module calls policies and imports none
(`surface.md` §2).  A side is resolved once, before any hand is played, to
``(id, policy, params, unlabelled, rule)``: a baseline is built at the seed the caller
fixes, a version member is built from the two facts its own checkpoint records -- the seed
and the encoding name -- and an opaque callable handed in from outside is named for its
position and its capacity is recorded as an unmeasured ``0`` (`scheduler.md` §5, ASM-10).

The **rule** travels with the side: a policy built from a learner carries the catalogue
member its learner was built under, so a cell can say which two estimators met, and a
baseline or an opaque callable carries none (`e2e-surface.md` §2, `rules.md` §7, D-19).
A member **record** that declares a `rule` is compared with the rule its policy carries
and a disagreement is refused naming the member and both values (`scheduler.md` §5,
ASM-20).

`policy_from` reads **exactly** two facts from the checkpoint's own container and nothing
else: the seed and the encoding name.  The learner, its parameters and its rule stay
`agents.load`'s and `agents.as_policy`'s -- the rule a member reports is the one the
policy `as_policy` built carries, which is the rule the file records (ASM-20, `rules.md`
§6, G20).  No seed is ever substituted for a missing one, and no seed is a digest of a
path.  A recorded encoding name is checked by **building** it -- `features.build_encoder`
is the granted arrow and no encoding catalogue is read (`scheduler.md` §5.1,
`module-map.md` §2).
"""

import hashlib
import json
import numbers
import os
import zipfile
from collections.abc import Mapping

import agents
import features

from .errors import (
    CheckpointRecordMissing,
    CheckpointUnreadable,
    InvalidPool,
    InvalidSeed,
    MemberInvalid,
    MemberUnloadable,
    RuleMismatch,
    UnknownEncoding,
)
from .pool import Pool, _rule
from .seeds import _draw_index

#: The deepest a recorded fact is looked for in one JSON document (`scheduler.md` §5.1).
_MAX_DEPTH = 8


class _MemberPolicy:
    """One member as a policy: its id, its measured capacity, the callable and its rule.

    A pool and a policy are opaque values a caller only passes back (`surface.md` §1);
    this carries the member's id and parameter count so a cell can name it and report its
    capacity, and the catalogue member its learner was built under, so a cell records
    which estimator it met (`scheduler.md` §4-§5, `rules.md` §7).
    """

    __slots__ = ("member_id", "params", "policy", "unlabelled", "learning_rule")

    def __init__(self, member_id, params, policy, unlabelled=False, learning_rule=None):
        self.member_id = member_id
        self.params = int(params)
        self.policy = policy
        self.unlabelled = bool(unlabelled)
        self.learning_rule = learning_rule

    def __call__(self, readout, legal_actions):
        return self.policy(readout, legal_actions)

    def __repr__(self):
        return "_MemberPolicy(member_id=%r, params=%r, learning_rule=%r)" % (
            self.member_id,
            self.params,
            self.learning_rule,
        )


def _token(text):
    """A key reduced to its letters and digits (`scheduler.md` §5.1's normalized form)."""
    return "".join(ch for ch in str(text).lower() if ch.isalnum())


def _is_int(value):
    """An integer, a NumPy integer included, but never a `bool` (`errors.md` §5)."""
    return isinstance(value, numbers.Integral) and not isinstance(value, bool)


# ---------------------------------------------------------------------------
# The two facts a checkpoint records, and the reader that finds them (§5.1)
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
    """The recorded seed and encoding-name candidates, or `CheckpointRecordMissing` (§5.1).

    A plain zip of `metadata.json` and `parameters.npy` is the container established
    empirically; the walk tolerates names it did not observe, matching a key by its
    normalized form (exactly `seed` / `encoding`, then by suffix), depth-first in
    document order to depth 8.  Nothing else is read.  The encoding names come back as
    the walk collected them, in document order, because the name is checked by building
    it and not by a catalogue (`scheduler.md` §5.1).
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
    return found_seed[0], tuple(encodings)


def _built_encoder(names, entry, where, path):
    """The encoder the recorded names build, and the name it accepted (§5.1, §6).

    The candidates the walk collected are offered to `features.build_encoder` in the
    order they were collected and the first name it accepts is the encoder -- building it
    is the only test a recorded name passes, so no catalogue is read (`module-map.md`
    §2).  A name `features.build_encoder` refuses is this module's own `UnknownEncoding`;
    when none is accepted the message names the first candidate.
    """
    for name in names:
        try:
            return name, features.build_encoder(name)
        except Exception:
            continue
    raise UnknownEncoding(
        "%s(%s): the checkpoint %r records the encoding %r, and features.build_encoder "
        "refuses that name" % (entry, where, path, names[0])
    )


def _checkpoint_policy(member_id, path, entry, where):
    """One member policy, built at the seed and the encoding its container records.

    The order is path, facts, name, load (`scheduler.md` §6): the two facts are read
    first, the encoder is built for the first recorded name `features.build_encoder`
    accepts, `agents.load` restores the learner (its refusal propagated unchanged) and
    `agents.as_policy` makes the decision policy.  The one catch this module declares is
    the encoder's: a recorded name `build_encoder` refuses and `as_policy`'s refusal of
    the encoder that name builds are both re-raised as `UnknownEncoding` (§5.1).
    """
    seed, encodings = _checkpoint_facts(path, entry, where)
    encoding, encoder = _built_encoder(encodings, entry, where, path)
    learner = agents.load(None, path)
    try:
        policy = agents.as_policy(learner, encoder, seed)
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
    )


def _member_policy(record, entry, label=None, what="played", noun="member"):
    """A `records.md` §7 version record as a policy: `policy_from`'s own builder (§5).

    A record that declares a `rule` is held to it: the policy is built from the
    checkpoint, and a rule that disagrees with the one the policy carries is refused
    naming the member and both values (`scheduler.md` §5, `records.md` §7, D-19).  A
    record declaring none is admitted -- the container decides, and the rule the policy
    reports is the rule the file records.
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
    return policy


def _artefact_id(path):
    """The bare-artefact id `policy_from` gives a path: one checkpoint, one member id."""
    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
    return "ckpt-" + digest


# ---------------------------------------------------------------------------
# `policy_from` (`surface.md` §12)
# ---------------------------------------------------------------------------
def policy_from(path):
    """A checkpoint as a policy in evaluation mode, at the seed its container records.

    The learner is never trained, never updated and never frozen from its exploration;
    it holds the state the checkpoint holds, so it decides as its learner decided
    (`surface.md` §12, ASM-5).  It plays no hand and moves no stream.
    """
    return _checkpoint_policy(_artefact_id(path), path, "policy_from", "path")


# ---------------------------------------------------------------------------
# `opponent` (`surface.md` §8)
# ---------------------------------------------------------------------------
def opponent(pool, seed):
    """One pool member drawn by ``seed % n``, as a policy (`surface.md` §8, `pool.md` §7).

    A baseline is built at the caller's seed and a version at the seed its checkpoint
    records, so one pool and one seed draw one opponent that answers one decision one
    way.  A drawn version carrying no `path` is refused, naming the member.
    """
    if not isinstance(pool, Pool):
        raise InvalidPool(
            "opponent(pool): the argument must be a pool from build_pool or offer, got %s"
            % (type(pool).__name__,)
        )
    if not _is_int(seed):
        raise InvalidSeed("opponent(seed): the seed must be an integer, got %r" % (seed,))
    index = _draw_index(seed, len(pool.members))
    member = pool.members[index]
    if member.get("baseline"):
        return agents.build_baseline(member["id"], int(seed))
    return _member_policy(
        member, "opponent", what="an opponent", noun="drawn member"
    )


# ---------------------------------------------------------------------------
# `_side` (`scheduler.md` §5)
# ---------------------------------------------------------------------------
def _side(value, label, entry, seed=None, position=1):
    """One side of a cell, resolved to ``(id, policy, params, unlabelled, rule)`` (§5).

    A baseline name is built at ``seed`` and declares no rule; a `records.md` §7 version
    record is built from its checkpoint's recorded facts and carries the rule the policy
    its file records reports; a `_MemberPolicy` this module built carries its own id, its
    capacity and its rule; and any other callable is named ``policy-<position>`` with an
    unmeasured ``0`` and whatever rule its own ``learning_rule`` carries, which is none for
    an opaque callable (`surface.md` §2, `rules.md` §7, ASM-10, D-19).
    """
    if isinstance(value, _MemberPolicy):
        return (
            value.member_id,
            value,
            value.params,
            value.unlabelled,
            value.learning_rule,
        )
    if isinstance(value, str):
        if value in agents.baselines():
            if seed is None:
                raise MemberInvalid(
                    "%s(%s): a baseline side needs the seed the cell is played at (%r)"
                    % (entry, label, value)
                )
            return (value, agents.build_baseline(value, int(seed)), 0, False, None)
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
        return (member_id, policy, policy.params, False, policy.learning_rule)
    if callable(value):
        return (
            "policy-%d" % position,
            value,
            0,
            True,
            getattr(value, "learning_rule", None),
        )
    raise MemberInvalid(
        "%s(%s): the side must be a policy, a version record or one of %r, got %r"
        % (entry, label, tuple(agents.baselines()), value)
    )
