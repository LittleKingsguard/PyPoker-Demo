"""`Learner`, `build_learner`, `param_count`, `act`, `learn`.

One learner family (`surface.md` §4-§7, `rule.md` §1-§3): a learner is built from one
spec, complete at construction, and it is opaque — a caller only passes it back.  The
sizing record it carries (`architecture.md` §6) is what `act`, `learn`, `as_policy`,
`save` and `load` check an argument against, and the schedule position is the only
state `learn` advances.

Every *validation* refusal is raised before the first mutation, so a refused batch
leaves the learner bit-identical (`errors.md` §1, §4).  The one exception is the
divergence refusal, which reports the state the steps before it left while the
position stays put (`divergence.md` §2, §4).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from numbers import Integral, Real

import numpy

import features

from . import declarations, model, rule
from .errors import (
    EncoderMismatch,
    InvalidBatch,
    InvalidEncoder,
    InvalidLearner,
    InvalidMask,
    InvalidObservation,
    InvalidSeed,
    InvalidSetting,
    InvalidSpec,
    LearningDiverged,
    UnknownArchitecture,
    UnknownBackend,
    UnknownCounterfactual,
    UnknownRule,
    UnknownUtility,
)

TRANSITION_KEYS = (
    "observation",
    "next_observation",
    "action",
    "reward",
    "terminal",
    "legal",
    "next_legal",
    "episode",
)


# --------------------------------------------------------------------------
# Readers and refusals shared by the entry points of this module
# --------------------------------------------------------------------------
def is_count(value):
    """Whether a value is an integer and not a flag (`errors.md` §4)."""
    return isinstance(value, Integral) and not isinstance(value, bool)


def _require_learner(value, entry):
    """The learner, or the refusal the entry point's contract states."""
    if isinstance(value, Learner):
        return value
    if getattr(value, "_agents_baseline", False) is True:
        raise InvalidLearner(
            "%s(learner): a baseline is not a learner, and its parameter count is the "
            "0 baselines() declares" % entry
        )
    raise InvalidLearner(
        "%s(learner): the argument must be a learner from build_learner, got %s"
        % (entry, type(value).__name__)
    )


def _integer(value, key, entry):
    """One required positive integer setting."""
    if not is_count(value) or int(value) < 1:
        raise InvalidSetting(
            "%s(spec): %r must be a positive integer, got %r" % (entry, key, value)
        )
    return int(value)


def _seed(value, entry, field="seed"):
    """One integer seed: a `numpy` integer is accepted, a flag is not (`errors.md` §3)."""
    if not is_count(value):
        raise InvalidSeed(
            "%s(%s): the seed must be an integer, got %r" % (entry, field, value)
        )
    return int(value)


def encoder_spec(value, entry, field="encoder", key="encoder"):
    """An encoder's `observation_spec`, or this module's refusal naming the key.

    The record is spelled as `errors.md` §3's table does it: the entry point, the
    record it was handed, the key at fault quoted, and the offending value.
    """
    try:
        return features.observation_spec(value)
    except Exception:
        raise InvalidEncoder(
            "%s(%s): %r must be an encoder from features.build_encoder, got %s"
            % (entry, field, key, type(value).__name__)
        ) from None


def encoder_size(spec):
    """The size an `observation_spec` sizes a learner by: its width, or its vocabulary."""
    if spec["kind"] == declarations.DENSE_FAMILY:
        return int(tuple(spec["shape"])[0])
    return int(spec["vocabulary"])


def encoder_side(spec):
    """`'card-tokens' (token-sequence, vocabulary 96)`, as a refusal names it."""
    if spec["kind"] == declarations.DENSE_FAMILY:
        return "'%s' (%s, width %d)" % (
            spec["representation"],
            spec["kind"],
            encoder_size(spec),
        )
    return "'%s' (%s, vocabulary %d)" % (
        spec["representation"],
        spec["kind"],
        encoder_size(spec),
    )


def kind_side(kind):
    """`'naive-stack' is dense-numeric at 203`, as a refusal names it."""
    row = declarations.kind_row(kind)
    return "'%s' is %s at %d" % (kind, row["observation"], row["observation_size"])


def learner_side(learner):
    """The learner half of an observation refusal, naming its family and its size."""
    if learner.shape is not None:
        return "%s %s %s" % (tuple(learner.shape), learner.dtype, learner.family)
    return "%s at %d" % (learner.family, learner.size)


def _observation(value, learner, entry, field):
    """One observation, validated against the learner's sizing record."""
    try:
        array = numpy.asarray(value)
    except Exception:
        raise InvalidObservation(
            "%s(%s): the observation must be an array of the learner's own family, got %s "
            "and the learner is %s"
            % (entry, field, type(value).__name__, learner_side(learner))
        ) from None
    if array.ndim != 1 or array.dtype.kind not in "iuf":
        raise InvalidObservation(
            "%s(%s): the observation is %s and the learner is %s"
            % (entry, field, _side(array, None), learner_side(learner))
        )
    family = (
        declarations.TOKEN_FAMILY
        if array.dtype.kind in "iu"
        else declarations.DENSE_FAMILY
    )
    description = _side(array, family)
    mismatch = family != learner.family
    if not mismatch:
        # A dense observation is as wide as the input block.  A token observation is a
        # sequence of positions, whose count only an encoder declares: a token learner's
        # size is the vocabulary (`architecture.md` §6).
        if learner.family == declarations.DENSE_FAMILY:
            mismatch = array.shape[0] != learner.size
        elif learner.shape is not None:
            mismatch = array.shape[0] != tuple(learner.shape)[0]
    if mismatch:
        raise InvalidObservation(
            "%s(%s): the observation is %s and the learner is %s"
            % (entry, field, description, learner_side(learner))
        )
    numeric = array.astype(numpy.float64)
    if not numpy.isfinite(numeric).all():
        raise InvalidObservation(
            "%s(%s): the observation is %s and holds a value that is not finite"
            % (entry, field, description)
        )
    if learner.dtype is not None and numpy.dtype(array.dtype) != numpy.dtype(learner.dtype):
        raise InvalidObservation(
            "%s(%s): the observation dtype is %s and the learner's encoding declares %s"
            % (entry, field, array.dtype, learner.dtype)
        )
    if family == declarations.TOKEN_FAMILY:
        lowest = int(array.min()) if array.size else 0
        highest = int(array.max()) if array.size else 0
        if lowest < 0 or highest >= learner.size:
            offending = lowest if lowest < 0 else highest
            raise InvalidObservation(
                "%s(%s): the observation is %s carrying the token id %d, which is "
                "outside the vocabulary 0..%d of the learner %s"
                % (
                    entry,
                    field,
                    description,
                    offending,
                    learner.size - 1,
                    learner_side(learner),
                )
            )
    return array


def _side(array, family):
    """`(203,) float32 dense-numeric`, or `(203,) float32` when the family is unknown."""
    if family is None:
        return "%s %s" % (tuple(array.shape), array.dtype)
    return "%s %s %s" % (tuple(array.shape), array.dtype, family)


def _mask(value, entry, field, held):
    """One legal mask: non-empty, distinct indices of the learner's shape's vocabulary.

    The index range is the **learner's shape's** — `0 .. A−1`, three indices on the
    default shape and six on the other, in that shape's declared order (`shapes.md` §3,
    `sizing.md` §3).  An observation alone cannot betray its shape, both declaring the
    same widths, dtype and token vocabulary, so the shape shows in the mask: an index
    outside the learner's vocabulary is refused naming the entry point, the learner's
    shape, that shape's range and the offending index, before any arithmetic and before
    the tie-break (`surface.md` §6–§7).
    """
    span = int(held.actions)
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Iterable):
        raise InvalidMask(
            "%s(%s): the mask must be non-empty, distinct indices of 0..%d on the shape "
            "%r, got %r" % (entry, field, span - 1, held.game, value)
        )
    items = []
    for item in value:
        if not is_count(item) or not 0 <= int(item) < span:
            raise InvalidMask(
                "%s(%s): the mask names the index %r, which is outside the index range "
                "0..%d of the shape %r the learner decides in, got %r"
                % (entry, field, item, span - 1, held.game, value)
            )
        items.append(int(item))
    if not items or len(set(items)) != len(items):
        raise InvalidMask(
            "%s(%s): the mask must be non-empty, distinct indices of 0..%d on the shape "
            "%r, got %r" % (entry, field, span - 1, held.game, value)
        )
    return tuple(sorted(items))


def learning_rule(value, entry):
    """One catalogue member's name, or the refusal (`rules.md` §2, §4, D-19).

    A learner learns under one of `learners()['learning_rules']`'s members, named by
    the catalogue's own spelling: a value that is not a string, or a string no member
    carries, is refused naming the value and the catalogue's names, and is never
    mapped onto the declared default — a silent substitution would train a model
    under a rule its spec does not name (`surface.md` §4, §9; `errors.md` §3).
    """
    if not isinstance(value, str) or value not in declarations.LEARNING_RULES:
        raise UnknownRule(
            "%s(spec): 'learning_rule' must be one of %r, got %r"
            % (entry, tuple(declarations.LEARNING_RULES), value)
        )
    return value


def utility(value, entry):
    """One utility catalogue member's name, or the refusal (`utilities.md` §2, §5, D-20).

    A learner is trained on the reward of one of `learners()['utilities']`'s members,
    named by the catalogue's own spelling: a value that is not a string, or a string no
    member carries, is refused naming the value and the catalogue's names, and is never
    mapped onto the declared default — a silent substitution would train a model on a
    reward its spec does not name (`surface.md` §4, §9; `errors.md` §3).
    """
    if not isinstance(value, str) or value not in declarations.UTILITIES:
        raise UnknownUtility(
            "%s(spec): 'utility' must be one of %r, got %r"
            % (entry, tuple(declarations.UTILITIES), value)
        )
    return value


def counterfactual(value, entry):
    """One counterfactual catalogue member's name, or the refusal (`counterfactual.md` §6, D-43).

    A learner takes its targets from one of `learners()['counterfactuals']`'s members,
    named by the catalogue's own spelling: a value that is not a string, or a string no
    member carries, is refused naming the value and the catalogue's names, and is never
    mapped onto the declared default.  It is not a rule and not a utility -- it is the
    axis that decides whether a residual is the rule's bootstrap or the transition's own
    whole-hand value -- and a silent substitution would train a model on targets its spec
    does not name (`counterfactual.md` §6, D-43; `errors.md` §3).
    """
    if not isinstance(value, str) or value not in declarations.COUNTERFACTUALS:
        raise UnknownCounterfactual(
            "%s(spec): 'counterfactual' must be one of %r, got %r"
            % (entry, tuple(declarations.COUNTERFACTUALS), value)
        )
    return value


def _backend(name):
    """The one module that performs this backend's arithmetic (`backends.md` §4).

    A name outside `learners()`'s two is refused and never mapped onto the torch
    module: the old fallback would let an undeclared backend import `torch` and be
    answered as a torch learner, which is a coercion of the caller's value and, on
    `load`'s path, of the file's (`surface.md` §1, §9; `checkpoint.md` §3;
    `README.md` §6).
    """
    if name not in declarations.BACKENDS:
        raise UnknownBackend(
            "build_learner(spec): the backend must be one of %r, got %r"
            % (declarations.BACKENDS, name)
        )
    if name == "numpy":
        from . import numpy_backend

        return numpy_backend
    from . import torch_backend

    return torch_backend


# --------------------------------------------------------------------------
# The learner
# --------------------------------------------------------------------------
class Learner:
    """One learner of the catalogue, complete at construction and opaque to a caller.

    It holds the backend's state — the online parameters, their target copy and the
    sparse masks — the sizing record a caller's arguments are checked against, the
    seed its exploration is keyed by, the catalogue member it learns under, the
    catalogue member whose reward its training target carries, the catalogue member it
    takes its targets from, the schedule position `learn` advances and the target
    copy's consumed-transition counter (`rule.md` §2-§4, `checkpoint.md` §1, D-19,
    D-20, D-43).  `counterfactual` is the catalogue member the learner takes its targets
    from — `none` being the rule's own bootstrap target, unchanged — read by `learn`
    alone and carried by every container it writes and by every policy `as_policy`
    builds; `act`, `param_count` and `as_policy`'s arithmetic are counterfactual-free
    (`counterfactual.md` §6, D-43).  `rule` and `counterfactual` are the only fields a
    learner's arithmetic reads and nothing else does: `act`, `param_count`,
    `as_policy` and the two checkpoints' members are rule-free; `utility` is read by no
    arithmetic here at all, because the reward is the caller's and the transform is
    `training`'s (`utilities.md` §4, `surface.md` §4-§7, D-19, D-20).

    `game` and `actions` are the shape it decides in and that shape's descriptor count
    `A` — the identity a container records and the width its head is built at.  They are
    read by `act` and `learn` (the index range), by `as_policy` (the vocabulary a
    descriptor is decoded in) and by `save` (the format version), and by no arithmetic
    that would branch on them (`shapes.md` §1–§3, §5, ASM-40).
    """

    __slots__ = (
        "backend_name",
        "backend",
        "layout",
        "state",
        "seed",
        "kind",
        "width",
        "depth",
        "sparsity",
        "residual",
        "family",
        "encoding",
        "size",
        "shape",
        "dtype",
        "rule",
        "utility",
        "counterfactual",
        "game",
        "actions",
        "position",
        "counter",
    )

    def __init__(
        self,
        backend_name,
        layout,
        state,
        seed,
        kind,
        width,
        depth,
        sparsity,
        residual,
        family,
        encoding,
        size,
        shape,
        dtype,
        rule,
        utility,
        position=0,
        counter=0,
        game=None,
        actions=None,
        counterfactual=None,
    ):
        self.backend_name = backend_name
        self.backend = _backend(backend_name)
        self.layout = layout
        self.state = state
        self.seed = seed
        self.kind = kind
        self.width = width
        self.depth = depth
        self.sparsity = sparsity
        self.residual = residual
        self.family = family
        self.encoding = encoding
        self.size = size
        self.shape = shape
        self.dtype = dtype
        self.rule = rule
        self.utility = utility
        # The catalogue member it takes its targets from: absent, the declared default,
        # which is the rule's own bootstrap target and today's arithmetic unchanged
        # (`counterfactual.md` §6, D-43).
        self.counterfactual = (
            declarations.DEFAULT_COUNTERFACTUAL if counterfactual is None else counterfactual
        )
        # The shape it decides in, and that shape's descriptor count: absent, the
        # declared default's -- a reading through `features.action_space`, never a
        # constant (`shapes.md` §1–§2, ASM-40).
        self.game = declarations.require_game(game, "Learner")
        self.actions = (
            declarations.actions_for(self.game) if actions is None else int(actions)
        )
        self.position = position
        self.counter = counter

    def __repr__(self):
        return "Learner(%s, %r, width %d, depth %d, %s, %s, %s)" % (
            self.backend_name,
            self.kind,
            self.width,
            self.depth,
            self.rule,
            self.utility,
            self.game,
        )


def _resolve_kind(architecture, sizes):
    """The kind, and the record its settings are read from (`surface.md` §4)."""
    if isinstance(architecture, Mapping):
        if "kind" not in architecture:
            raise InvalidSpec(
                "build_learner(spec): 'architecture' is missing the required key 'kind'"
            )
        return architecture["kind"], architecture
    if isinstance(architecture, str):
        if not isinstance(sizes, Mapping) or "width" not in sizes or "depth" not in sizes:
            raise InvalidSpec(
                "build_learner(spec): the kind %r names no width or depth, and 'sizes' "
                "is absent" % (architecture,)
            )
        return architecture, sizes
    raise InvalidSpec(
        "build_learner(spec): 'architecture' must be a mapping or a kind name, got %s"
        % type(architecture).__name__
    )


def build_learner(spec):
    """One learner from one spec, under the rule and utility the spec names (`surface.md` §4).

    `learning_rule`, `utility` and `counterfactual` are optional: absent, the learner is
    built under the catalogue's **first** member of each, the declared defaults of
    `rules.md` §4, `utilities.md` §5 and `counterfactual.md` §6 -- `counterfactual` being
    the third optional catalogue key, the axis the learner takes its targets from
    (D-19, D-20, D-43).  A named member the catalogue does not carry is refused before
    anything is built (`errors.md` §4).

    **Which size the learner is built at is the shape's question.**  `encoder` is
    optional too: with one, the learner is sized from its `observation_spec` -- a dense
    spec's width or a token spec's vocabulary -- and on a non-default shape that width is
    the shape's own, 329 on `no-limit-100` (`shapes.md` §8, ASM-44).  With none, it is
    sized from the kind's declared `observation_size`, which is the **default** shape's
    size, so a spec naming another shape with no encoder is refused by name and never
    built at 203 (`docs/L2/features/capacity.md` §2, §5).
    """
    if not isinstance(spec, Mapping):
        raise InvalidSpec(
            "build_learner(spec): the spec must be a mapping, got %s"
            % type(spec).__name__
        )
    for key in ("backend", "architecture", "seed"):
        if key not in spec:
            raise InvalidSpec(
                "build_learner(spec): the spec is missing the required key '%s'" % (key,)
            )

    backend_name = spec["backend"]
    if not isinstance(backend_name, str) or backend_name not in declarations.BACKENDS:
        raise UnknownBackend(
            "build_learner(spec): the backend must be one of %r, got %r"
            % (declarations.BACKENDS, backend_name)
        )
    seed = _seed(spec["seed"], "build_learner", "spec")

    sizes = spec.get("sizes")
    kind, settings = _resolve_kind(spec["architecture"], sizes)
    if not isinstance(kind, str) or kind not in declarations.KINDS:
        raise UnknownArchitecture(
            "build_learner(spec): the kind must be one of %r, got %r"
            % (declarations.KINDS, kind)
        )

    # The catalogue members are read here, before any setting is resolved and before a
    # parameter is drawn, so a refused name leaves nothing built (`errors.md` §1).
    # Absent, each is the declared default and not a value inferred from the caller's
    # silence (`rules.md` §4, `utilities.md` §5, `records.md` §3).  A third member is
    # read here on the same rule: absent, the catalogue's first; named and uncarried,
    # refused before anything is built (`counterfactual.md` §6, D-43).
    under = (
        learning_rule(spec["learning_rule"], "build_learner")
        if "learning_rule" in spec
        else declarations.DEFAULT_LEARNING_RULE
    )
    trained_on = (
        utility(spec["utility"], "build_learner")
        if "utility" in spec
        else declarations.DEFAULT_UTILITY
    )
    targets_from = (
        counterfactual(spec["counterfactual"], "build_learner")
        if "counterfactual" in spec
        else declarations.DEFAULT_COUNTERFACTUAL
    )
    # The shape the learner decides in, read beside the two catalogue members and before
    # a parameter is drawn: absent it is the declared default, and a name the catalogue
    # does not carry is refused naming it and the declared names, never substituted —
    # and `A`, the head's width, is **read** off that shape (`shapes.md` §1–§2, §6,
    # `sizing.md` §6, ASM-40, D-29).
    game = declarations.require_game(spec.get("game"), "build_learner", "'game'")
    actions = declarations.actions_for(game)
    fallback = sizes if isinstance(sizes, Mapping) else {}
    width = _integer(settings.get("width", fallback.get("width")), "width", "build_learner")
    depth = _integer(settings.get("depth", fallback.get("depth")), "depth", "build_learner")
    # `sparsity` is validated for every kind and read by `sparse` alone
    # (`architecture.md` §3); the declared value is checked before it is resolved.
    declared = settings.get("sparsity", fallback.get("sparsity", 0.0))
    if isinstance(declared, bool) or not isinstance(declared, Real):
        raise InvalidSetting(
            "build_learner(spec): 'sparsity' must be in [0, 1], got %r" % (declared,)
        )
    declared = float(declared)
    if not 0.0 <= declared <= 1.0:
        raise InvalidSetting(
            "build_learner(spec): 'sparsity' must be in [0, 1], got %r" % (declared,)
        )
    # `architecture.md` §3: the kind decides the connection.  The spec's own
    # `residual` flag mirrors the kind and is accepted and never read — it is not
    # even looked up here, so no flag can refuse a spec and no flag can turn one
    # kind into another (R6).
    #
    # `sparsity` is a setting a kind may not read: `sparse` keeps the spec's `s` and
    # every other kind's own `0.0` stands.
    sparsity = declared if kind == "sparse" else 0.0

    row = declarations.kind_row(kind)
    family = row["observation"]
    encoding = row["encoding"]
    # The size an encoder-less build is sized from: the kind's declared
    # `observation_size`, which is the **default** shape's size and not a per-shape
    # table's (`shapes.md` §8, ASM-44).  A learner on any other shape takes its input
    # width from that shape's own encoder -- 329 dense, a vocabulary of 96 on
    # `no-limit-100` -- and a spec naming one with no encoder is refused below rather
    # than sized from a number that is not that shape's (`docs/L2/features/capacity.md`
    # §2, §5).
    size = row["observation_size"]
    shape = None
    dtype = None
    if "encoder" in spec:
        encoded = encoder_spec(spec["encoder"], "build_learner", "spec", "encoder")
        declared_family = encoded["kind"]
        declared_size = encoder_size(encoded)
        # The **family** is the kind's on every shape: a token encoder for a dense kind
        # and the reverse is refused naming both, and a token learner is sized by its
        # vocabulary and never by its sequence length (`encodings.md` §1, §4, D-3).  The
        # **size** is the kind's only on the default shape -- where the two are 203 and
        # 96 anyway -- so on any other shape the shape's encoder is authoritative and
        # the kind's 203 is not consulted as an equality (`shapes.md` §8, ASM-44).
        if declared_family != family or (
            declarations.sized_by_kind(game) and declared_size != size
        ):
            raise EncoderMismatch(
                "build_learner(spec): the encoder is %s and the kind %s"
                % (encoder_side(encoded), kind_side(kind))
            )
        family = declared_family
        encoding = encoded["representation"]
        size = declared_size
        shape = tuple(encoded["shape"])
        dtype = encoded["dtype"]
    elif not declarations.sized_by_kind(game):
        # An encoder-less build is sized from the kind's declared `observation_size`,
        # and that number is the **default** shape's: on any other shape there is no
        # size to build at, so the spec is refused by name rather than silently sized
        # at 203, which would be an observation of one shape fed to a head of another
        # (`shapes.md` §8, ASM-44, `docs/L2/features/capacity.md` §5).
        raise EncoderMismatch(
            "build_learner(spec): the spec names the shape %r and carries no 'encoder'; "
            "the kind %s, which is the size of the default shape %r and not of that "
            "shape, so a learner on another shape takes its input width from that "
            "shape's encoder"
            % (game, kind_side(kind), declarations.DEFAULT_SHAPE)
        )

    layout, parameters, masks, _kept = model.initial_draw(
        kind, width, depth, sparsity, seed, size, family, actions=actions
    )
    backend = _backend(backend_name)
    state = backend.new_state(layout, parameters, masks)
    return Learner(
        backend_name,
        layout,
        state,
        seed,
        kind,
        width,
        depth,
        # The resolved values in force, which is what a checkpoint records and what
        # `sparse` alone reads (`architecture.md` §3, `checkpoint.md` §2.1).
        layout.sparsity,
        layout.residual,
        family,
        encoding,
        size,
        shape,
        dtype,
        # The catalogue member this learner learns under: the spec's or the declared
        # default, recorded by every checkpoint it writes (`rules.md` §4, §6).
        under,
        # The catalogue member whose reward its training target carries: the spec's or
        # the declared default `net-chips`, recorded by every checkpoint it writes and
        # reported by every policy `as_policy` builds (`utilities.md` §5, §6, D-20).
        trained_on,
        # The shape it decides in and that shape's descriptor count: the head is the
        # shape's, so a checkpoint of any other shape is a format version of its own
        # (`shapes.md` §1–§2, §5, ASM-40).
        game=game,
        actions=actions,
        # The catalogue member the learner takes its targets from: the spec's or the
        # declared default `none`, recorded by every checkpoint it writes
        # (`counterfactual.md` §6, D-43).
        counterfactual=targets_from,
    )


def param_count(learner):
    """The learner's trainable parameter count, a plain `int` (`surface.md` §5)."""
    held = _require_learner(learner, "param_count")
    return int(held.layout.count)


def act(learner, observation, legal_mask):
    """One training-time decision: `{"action": <plain int>, "tie": <bool>}` (`surface.md` §6)."""
    held = _require_learner(learner, "act")
    values = _observation(observation, held, "act", "observation")
    mask = _mask(legal_mask, "act", "legal_mask", held)
    scored, _cache = held.backend.forward(held.state, held.layout, values, need_cache=False)
    # The index and whether the **tie-break** — and not a strict maximum — chose it: false
    # wherever the exploring arm drew the index, and false on a one-element mask
    # (`shapes.md` §3, `records.md` §6, §15, ASM-37).
    index, tie = rule.decide(
        held.seed, held.family, held.position, scored, values, mask
    )
    return {"action": int(index), "tie": bool(tie)}


def _transition(learner, record):
    """One transition record, validated against the learner before any arithmetic."""
    if not isinstance(record, Mapping):
        raise InvalidBatch(
            "learn(transitions): a transition must be a mapping, got %s"
            % type(record).__name__
        )
    for key in TRANSITION_KEYS:
        if key not in record:
            raise InvalidBatch(
                "learn(transitions): the transition is missing the required key '%s'"
                % (key,)
            )
    observation = _observation(record["observation"], learner, "learn", "observation")
    successor = _observation(
        record["next_observation"], learner, "learn", "next_observation"
    )
    legal = _mask(record["legal"], "learn", "legal", learner)
    next_legal = _mask(record["next_legal"], "learn", "next_legal", learner)
    # The episode boundary, which D-43 makes required of every transition: the episode's
    # own seed, so two transitions of one hand carry one number and two hands of one run
    # carry two (`records.md` §4, §5, `counterfactual.md` §2).  A missing one was already
    # refused by the required-key loop above, which names the key.
    episode = record["episode"]
    if not is_count(episode):
        raise InvalidBatch(
            "learn(transitions): 'episode' must be an episode's integer seed, got %r"
            % (episode,)
        )
    # The index range is the learner's shape's, on `action`, `legal` and `next_legal`
    # alike, so a transition recorded on another shape is refused rather than read as one
    # of this learner's indices (`shapes.md` §3, `surface.md` §7).
    span = int(learner.actions)
    if not is_count(record["action"]) or not 0 <= int(record["action"]) < span:
        raise InvalidBatch(
            "learn(transitions): 'action' must be an integer index of 0..%d on the shape "
            "%r, got %r" % (span - 1, learner.game, record["action"])
        )
    action = int(record["action"])
    if action not in legal:
        raise InvalidBatch(
            "learn(transitions): 'action' %d is not in that transition's legal mask %r"
            % (action, legal)
        )
    reward = record["reward"]
    if isinstance(reward, bool) or not isinstance(
        reward, (int, float, numpy.floating, numpy.integer)
    ):
        raise InvalidBatch(
            "learn(reward): the reward must be a number, got %r" % (reward,)
        )
    terminal = record["terminal"]
    if not isinstance(terminal, (bool, numpy.bool_)):
        raise InvalidBatch(
            "learn(terminal): the terminal flag must be a bool, got %r" % (terminal,)
        )
    # The optional resolution D-43 adds: absent or `None` is a hand the member falls back
    # from, and otherwise one value per descriptor of the shape, a number where the action
    # was legal and `None` where it was not, so a masked action is never valued and never
    # updated (`records.md` §4, `counterfactual.md` §4-§5).
    supplied = record["counterfactual"] if "counterfactual" in record else None
    if supplied is None:
        resolution = None
    else:
        if isinstance(supplied, (str, bytes, Mapping)) or not isinstance(
            supplied, Iterable
        ):
            raise InvalidBatch(
                "learn(transitions): 'counterfactual' must be None or a sequence over "
                "the shape %r's %d descriptors, got %s"
                % (learner.game, span, type(supplied).__name__)
            )
        entries = list(supplied)
        if len(entries) != span:
            raise InvalidBatch(
                "learn(transitions): 'counterfactual' carries %d entries and the shape "
                "%r declares %d descriptors, over the transition's legal mask %r"
                % (len(entries), learner.game, span, legal)
            )
        stored = []
        for position, entry in enumerate(entries):
            # `None` in any slot is an action this episode did not resolve, and it is
            # **stored** rather than refused: a sequence carrying one at an index of its
            # own legal mask is the partial resolution `learn` falls back from, taking the
            # ordinary single step instead of a fraction of one (`counterfactual.md` §4,
            # §6).
            if entry is None:
                stored.append(None)
                continue
            if position not in legal:
                raise InvalidBatch(
                    "learn(transitions): 'counterfactual' carries a value at index "
                    "%d, which is outside the transition's legal mask %r"
                    % (position, legal)
                )
            if isinstance(entry, bool) or not isinstance(
                entry, (int, float, numpy.integer, numpy.floating)
            ):
                raise InvalidBatch(
                    "learn(transitions): 'counterfactual' carries %r at index %d over "
                    "the transition's legal mask %r, and an entry of a resolution is a "
                    "number or None" % (entry, position, legal)
                )
            stored.append(float(entry))
        resolution = tuple(stored)
    return {
        "observation": observation,
        "next_observation": successor,
        "action": action,
        "reward": float(reward),
        "terminal": bool(terminal),
        "legal": legal,
        "next_legal": next_legal,
        "episode": int(episode),
        "counterfactual": resolution,
    }


def _batch(transitions):
    """The batch's records, in the caller's order, or the refusal (`rule.md` §3)."""
    if isinstance(transitions, (str, bytes, Mapping)) or not isinstance(
        transitions, Iterable
    ):
        raise InvalidBatch(
            "learn(transitions): the batch must be a non-empty sequence of transitions, "
            "got %r" % (transitions,)
        )
    records = list(transitions)
    if not records:
        raise InvalidBatch(
            "learn(transitions): a batch holds at least one transition, got %r"
            % (transitions,)
        )
    return records


def _step(held, backend, cache, action, delta, site, rate, interval, total, divisor=1):
    """One guarded semi-gradient step, and the batch's total with the raw `|delta|` added.

    `delta` is one transition's **raw** residual -- the rule's td_error under `none`, and
    one legal action's `value − q[action]` under `reveal-counterfactual` -- and the step
    applies `delta / divisor`, `divisor` being the number of steps that transition takes
    (`counterfactual.md` §6: one transition's movement is the **mean** over the steps it
    takes, and `1` is the one step of the ordinary path).  The magnitude accumulated is the
    raw one, **before** the division, so the figure `learn` returns keeps the scale of the
    values the member learns (`rule.md` §3).  `site` names the transition, and on the
    member's path the action too, in both refusals (`divergence.md` §2).
    """
    # GUARD 1 (`divergence.md` §2): a non-finite td_error refuses **before** |td| is
    # accumulated and before the step, naming the transition -- and, on the member's
    # path, the action too -- and the value.
    if not numpy.isfinite(delta):
        raise LearningDiverged(
            "learn(transitions): %s computed a non-finite td_error and the learner has "
            "diverged, got %r" % (site, float(delta))
        )
    total += abs(delta)
    backend.apply(held.state, held.layout, cache, action, delta / divisor, rate)
    # GUARD 2 (`divergence.md` §2): a step that left any of the whole 2·P array
    # non-finite refuses **after** it and before the counter moves, naming the
    # transition -- and, on the member's path, the action too -- and the first parameter
    # index out of range.
    values = backend.parameters(held.state)
    finite = numpy.isfinite(values)
    if not finite.all():
        slot = int(numpy.argmax(~finite))
        raise LearningDiverged(
            "learn(transitions): %s drove parameter index %d out of finite range and "
            "the learner has diverged, got %r" % (site, slot, float(values[slot]))
        )
    held.counter += 1
    if held.counter >= interval:
        backend.copy_online_to_target(held.state, held.layout)
        held.counter = 0
    return total


def learn(learner, transitions):
    """`rule.md` §3: one semi-gradient step per transition, in the caller's order.

    The two learning rules differ in the target's arithmetic and nowhere else: the
    terminal target, the validation order, the per-transition loop, the td-error
    accumulation, the SGD step, the refresh counter, the schedule position and the two
    returned keys are one shared path (`rule.md` §2-§3, `rules.md` §3, D-19).

    The third catalogue's `none` member **is** that path: the residual is the rule's own
    bootstrap target and one step is taken per transition.  `reveal-counterfactual`
    replaces the target with the transition's own resolved whole-hand values and takes one
    semi-gradient step **per legal action**, all of them computed from one forward pass, so
    no step of a transition is visible to a later residual of the same transition -- and it
    reads no successor and no discount at all (`counterfactual.md` §4-§6, D-43).  A
    **terminal** transition is **not** exempt: the seat's last decision of a hand carries
    the whole-hand value of every legal action and the realised one equals that transition's
    `reward`, so the terminal one is where the outcome is known and it takes its steps
    exactly as any other transition does (`counterfactual.md` §4, §6).  Two transitions fall
    back to the ordinary path and take exactly one step: one whose `counterfactual` is
    `None`, and one whose sequence carries `None` at an index of its own legal mask -- a
    partial resolution is not a resolution, and a fraction of a step is never taken
    (`rule.md` §2-§3, D-43).

    **One transition's movement is the mean over the steps it takes**, so each step applies
    `(v_i - q[i]) / A` where `A` is **the number of steps that transition takes**.  That is
    how §6's sentence is read here: `A = len(record["legal"])`, the count of *the
    transition's own* legal actions, and not the shape's descriptor count -- a transition
    with 3 of a six-descriptor shape's actions legal takes 3 steps and divides by 3, while
    dividing by the shape's full count would be a fraction of a step and not a mean over the
    steps taken (`counterfactual.md` §6).

    `td_error` is the batch's mean absolute **raw** residual over its **steps**: the
    magnitude `|v_i - q[i]|` is accumulated **before** the divisor, so the statistic keeps
    the scale of the values the member learns, and under `none` it is unchanged, where steps
    and transitions are one number; a batch that produced no step at all answers `0.0`
    rather than dividing by zero.  `transitions` is the record count, and the schedule
    position advances by it -- the number of transitions, never the number of steps
    (`counterfactual.md` §6, `rule.md` §4).
    """
    held = _require_learner(learner, "learn")
    records = [_transition(held, record) for record in _batch(transitions)]

    backend = held.backend
    rate = float(declarations.HYPER["learning_rate"])
    discount = float(declarations.HYPER["discount"])
    interval = int(declarations.HYPER["target_update_interval"])
    revealed = held.counterfactual != declarations.DEFAULT_COUNTERFACTUAL
    total = 0.0
    steps = 0
    for index, record in enumerate(records):
        scored, cache = backend.forward(
            held.state, held.layout, record["observation"], need_cache=True
        )
        if revealed and record["counterfactual"] is not None:
            # every index of the transition's own legal mask is resolved, or this is not
            # a resolution at all and the transition falls back to the ordinary path
            # below -- a partial resolution is not a resolution, and a fraction of a step
            # is never taken (`counterfactual.md` §4, §6, D-43).  A **terminal** transition
            # is not exempt: the seat's last decision carries the whole-hand value of every
            # legal action and the realised one is that transition's `reward`, so it takes
            # its steps here exactly as any other transition does (`counterfactual.md` §4).
            if all(
                record["counterfactual"][member] is not None
                for member in record["legal"]
            ):
                # `A`, the divisor of every step of this transition: the **number of steps
                # it takes**, which is the count of its own legal actions and not the
                # shape's descriptor count -- 3 legal actions take 3 steps and divide by 3,
                # so one transition's movement is the mean over its steps
                # (`counterfactual.md` §6, `rule.md` §2).
                count = len(record["legal"])
                # All the residuals are read off the one forward pass before **any** step
                # of this transition is taken, in the legal mask's ascending order, which
                # is `_mask`'s own, so no step of a transition is visible to a later
                # residual of that transition (`counterfactual.md` §6, `rule.md` §2).
                residual_of = [
                    (member, float(record["counterfactual"][member]) - float(scored[member]))
                    for member in record["legal"]
                ]
                # One semi-gradient step per legal index, each on that same cache and each
                # applying its raw residual over `count`, so the member's step count is the
                # transition's legal-action count where a rule's is one (`rule.md` §2-§3,
                # D-43).
                for member, residual in residual_of:
                    total = _step(
                        held, backend, cache, member, residual,
                        "transition index %d at action index %d" % (index, member),
                        rate, interval, total, count,
                    )
                    steps += 1
                continue
        if record["terminal"]:
            target = record["reward"]
        else:
            successor, _unused = backend.forward(
                held.state,
                held.layout,
                record["next_observation"],
                target=True,
                need_cache=False,
            )
            if held.rule == "double-q-learning":
                # Double Q-learning decouples selection from evaluation: the **online**
                # parameters choose the masked index under the declared tie-break, and
                # the **target copy** values it (`rules.md` §2, `rule.md` §2).  It is a
                # second forward pass of one observation and no new state.
                online, _discarded = backend.forward(
                    held.state,
                    held.layout,
                    record["next_observation"],
                    need_cache=False,
                )
                chosen = rule._tie_break(online, record["next_legal"])
                bootstrap = float(successor[chosen])
            else:
                # `masked-q-learning`, the catalogue's first member and the only other
                # one: the masked maximum of the target copy's values (`rule.md` §2).
                bootstrap = max(
                    float(successor[index]) for index in record["next_legal"]
                )
            target = record["reward"] + discount * bootstrap
        delta = target - float(scored[record["action"]])
        total = _step(
            held, backend, cache, record["action"], delta,
            "transition index %d" % (index,), rate, interval, total,
        )
        steps += 1
    held.position += len(records)
    return {
        "td_error": float(total / steps) if steps else 0.0,
        "transitions": int(len(records)),
    }
