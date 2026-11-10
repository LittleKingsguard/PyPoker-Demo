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
)

VOCABULARY = (0, 1, 2)


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


def _mask(value, entry, field):
    """One legal mask: non-empty, distinct indices of `0`, `1` or `2`, ascending."""
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Iterable):
        raise InvalidMask(
            "%s(%s): the mask must be non-empty, distinct indices of 0, 1 or 2, got %r"
            % (entry, field, value)
        )
    items = []
    for item in value:
        if not is_count(item) or int(item) not in VOCABULARY:
            raise InvalidMask(
                "%s(%s): the mask must be non-empty, distinct indices of 0, 1 or 2, got %r"
                % (entry, field, value)
            )
        items.append(int(item))
    if not items or len(set(items)) != len(items):
        raise InvalidMask(
            "%s(%s): the mask must be non-empty, distinct indices of 0, 1 or 2, got %r"
            % (entry, field, value)
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
    catalogue member whose reward its training target carries, the schedule position
    `learn` advances and the target copy's consumed-transition counter (`rule.md` §2-§4,
    `checkpoint.md` §1, D-19, D-20).  `rule` is the only field a learner's arithmetic
    reads and nothing else does: `act`, `param_count`, `as_policy` and the two
    checkpoints' members are rule-free; `utility` is read by no arithmetic here at all,
    because the reward is the caller's and the transform is `training`'s
    (`utilities.md` §4, `surface.md` §4-§7, D-19, D-20).
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
        self.position = position
        self.counter = counter

    def __repr__(self):
        return "Learner(%s, %r, width %d, depth %d, %s, %s)" % (
            self.backend_name,
            self.kind,
            self.width,
            self.depth,
            self.rule,
            self.utility,
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

    `learning_rule` and `utility` are optional: absent, the learner is built under the
    catalogue's **first** member of each, the declared defaults of `rules.md` §4 and
    `utilities.md` §5.  A named member the catalogue does not carry is refused before
    anything is built (`errors.md` §4, D-19, D-20).
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
    # silence (`rules.md` §4, `utilities.md` §5, `records.md` §3).
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
    size = row["observation_size"]
    shape = None
    dtype = None
    if "encoder" in spec:
        encoded = encoder_spec(spec["encoder"], "build_learner", "spec", "encoder")
        declared_family = encoded["kind"]
        declared_size = encoder_size(encoded)
        if declared_family != family or declared_size != size:
            raise EncoderMismatch(
                "build_learner(spec): the encoder is %s and the kind %s"
                % (encoder_side(encoded), kind_side(kind))
            )
        family = declared_family
        encoding = encoded["representation"]
        size = declared_size
        shape = tuple(encoded["shape"])
        dtype = encoded["dtype"]

    layout, parameters, masks, _kept = model.initial_draw(
        kind, width, depth, sparsity, seed, size, family
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
    )


def param_count(learner):
    """The learner's trainable parameter count, a plain `int` (`surface.md` §5)."""
    held = _require_learner(learner, "param_count")
    return int(held.layout.count)


def act(learner, observation, legal_mask):
    """One training-time decision: `{"action": <plain int>}` (`surface.md` §6)."""
    held = _require_learner(learner, "act")
    values = _observation(observation, held, "act", "observation")
    mask = _mask(legal_mask, "act", "legal_mask")
    scored, _cache = held.backend.forward(held.state, held.layout, values, need_cache=False)
    index = rule.decide(
        held.seed, held.family, held.position, scored, values, mask
    )
    return {"action": int(index)}


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
    legal = _mask(record["legal"], "learn", "legal")
    next_legal = _mask(record["next_legal"], "learn", "next_legal")
    if not is_count(record["action"]):
        raise InvalidBatch(
            "learn(transitions): 'action' must be an integer index of 0, 1 or 2, got %r"
            % (record["action"],)
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
    return {
        "observation": observation,
        "next_observation": successor,
        "action": action,
        "reward": float(reward),
        "terminal": bool(terminal),
        "legal": legal,
        "next_legal": next_legal,
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


def learn(learner, transitions):
    """`rule.md` §3: one semi-gradient step per transition, in the caller's order.

    The two catalogue members differ in the target's arithmetic and nowhere else: the
    terminal target, the validation order, the per-transition loop, the td-error
    accumulation, the SGD step, the refresh counter, the schedule position and the two
    returned keys are one shared path (`rule.md` §2-§3, `rules.md` §3, D-19).
    """
    held = _require_learner(learner, "learn")
    records = [_transition(held, record) for record in _batch(transitions)]

    backend = held.backend
    rate = float(declarations.HYPER["learning_rate"])
    discount = float(declarations.HYPER["discount"])
    interval = int(declarations.HYPER["target_update_interval"])
    total = 0.0
    for index, record in enumerate(records):
        scored, cache = backend.forward(
            held.state, held.layout, record["observation"], need_cache=True
        )
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
        # GUARD 1 (`divergence.md` §2): a non-finite td_error refuses **before** |td|
        # is accumulated and before the step, naming the transition and the value.
        if not numpy.isfinite(delta):
            raise LearningDiverged(
                "learn(transitions): transition index %d computed a non-finite "
                "td_error and the learner has diverged, got %r"
                % (index, float(delta))
            )
        total += abs(delta)
        backend.apply(held.state, held.layout, cache, record["action"], delta, rate)
        # GUARD 2 (`divergence.md` §2): a step that left any of the whole 2·P array
        # non-finite refuses **after** it and before the counter moves, naming the
        # transition and the first parameter index out of range.
        values = backend.parameters(held.state)
        finite = numpy.isfinite(values)
        if not finite.all():
            slot = int(numpy.argmax(~finite))
            raise LearningDiverged(
                "learn(transitions): transition index %d drove parameter index %d out "
                "of finite range and the learner has diverged, got %r"
                % (index, slot, float(values[slot]))
            )
        held.counter += 1
        if held.counter >= interval:
            backend.copy_online_to_target(held.state, held.layout)
            held.counter = 0
    held.position += len(records)
    return {
        "td_error": float(total / len(records)),
        "transitions": int(len(records)),
    }
