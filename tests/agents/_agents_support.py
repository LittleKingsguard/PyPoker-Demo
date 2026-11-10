"""Shared support for the `agents` unit battery.

Puts `<repo>/src` on `sys.path`, imports the `agents` package **lazily inside a
helper** (so an absent `src/agents/` is one red case per contract and never a
collection error), and holds the battery's invented instances, its tolerant
readers, the container surgery a case needs to build a file this module did not
write (`container_document`, `write_container`, `version_container`,
`game_container`) and the base `unittest.TestCase` every case derives from.

It also carries the two declared game shapes' names and the six-index vocabulary
of the second one, the decisions a case reads on that shape (`shape_decisions`)
and the submodule reader a monkey-patch of one declared internal needs
(`declared_module`), so a shape case reaches the same readers every other case
does (`docs/L2/agents/shapes.md` §1, §3, `docs/L3/agents/shapes.md` §1-§4).

Everything asserted here is stated in `docs/L3/agents/` and `docs/L2/agents/`;
the two consumed edges are read through `docs/L2/features/surface.md` §5, §8, §9
and `docs/L2/engine/surface.md` §11 (D-13). A refusal's *behaviour* is asserted and
never its subclass, the subclass being this module's freedom (`docs/L3/agents/errors.md`
§1-§3); the one class a case may name is the hierarchy's root `AgentsError`, which
`errors.md` §2 declares and which makes "this module refused me" catchable —
`refusal_class` reads it, and `assert_agents_refusal` requires it where a refusal
must not arrive as a `TypeError` or another module's error.

A learner at schedule position 0 explores at the schedule's `start`, so no case
that only builds one ever reads a value (`rule.md` §4). `anneal_batch` therefore
supplies a batch of exactly the schedule's `samples` records, and
`AgentsCase.annealed_learner` caches one annealed learner per test class;
`quiet_batch` reaches the same position without moving a parameter, so a total
tie can be decided at the annealed rate. The six internals `rule.md` §8 declares
are reachable through `declared_internal`, and they are the only private
spellings this battery imports.
"""

import importlib
import json
import os
import sys
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
SRC_ROOT = os.path.join(REPO_ROOT, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

#: The ten entry points, in the L1 order (`e2e-surface.md` §3.3, `README.md` §3).
TEN_NAMES = (
    "learners",
    "build_learner",
    "param_count",
    "act",
    "learn",
    "save",
    "load",
    "as_policy",
    "baselines",
    "build_baseline",
)

#: The seven architecture kinds, in the order `learners()` declares them
#: (`architecture.md` §1, `README.md` §5).
SEVEN_KINDS = (
    "naive-stack",
    "token-embedding",
    "wide",
    "deep",
    "sparse",
    "residual",
    "plain",
)

DENSE_KIND = "naive-stack"
TOKEN_KINDS = ("token-embedding", "wide", "deep", "sparse", "residual", "plain")

#: Invented instances: none of these numbers or names appears in a design document.
LEARNER_SEED = 8127
OTHER_SEED = 4409
BASELINE_SEED = 20271
SECOND_BASELINE_SEED = 7314
EXTRA_LEARNER_SEED = 8128
CHECKPOINT_NAMES = ("v-8127-a.pt", "v-8127-b.pth", "v-8127-c.ckpt")

#: Invented instances for the annealed batteries. A learner at schedule position
#: 0 explores at the schedule's `start` (1.0), so no case that only builds one
#: reaches the greedy arm of `rule.md` §4; these drive the annealed end instead.
ANNEAL_SEED = 6011
TEACH_SEED = 6091
TEACH_REWARD = 40.0
TIE_SEEDS = tuple(range(6413, 6428))

#: The decision vocabulary, and the seven non-empty masks over it.
ALL_MASK = (0, 1, 2)
NONEMPTY_MASKS = ((0,), (1,), (2,), (0, 1), (0, 2), (1, 2), (0, 1, 2))

#: The two declared game shapes' names, default first (`shapes.md` §1, D-29): the names
#: are the catalogue's restatement in `declarations.SHAPE_NAMES`, and the default is
#: first, so the fixed game is the shape a spec naming none is built on.
DEFAULT_SHAPE = "fixed-limit-20"
OTHER_SHAPE = "no-limit-100"

#: The second shape's whole index space and a spread of masks over it (`shapes.md` §3,
#: `sizing.md` §3, ASM-37): one-, two-, three- and six-member masks, some carrying the
#: three indices the default shape has no name for (3, 4 and 5) and some the two shapes
#: share.  The indices are the declared vocabulary's, never invented ones.
SIX_MASK = (0, 1, 2, 3, 4, 5)
SIX_MASKS = (
    (0,),
    (3,),
    (5,),
    (3, 4),
    (4, 5),
    (0, 3),
    (3, 4, 5),
    (0, 1, 3, 4, 5),
    SIX_MASK,
)


class SurfaceAbsent(AssertionError):
    """`src/agents/` or one of the ten entry points is missing.

    Every case that cannot find the package fails with this message rather than
    a collection error, which is what keeps the battery red for the right
    reason before `src/agents/` exists (`strata/examiner.md` §2-§3).
    """


_AGENTS = None


def agents():
    """Return the `agents` package, or raise `SurfaceAbsent`."""
    global _AGENTS
    if _AGENTS is not None:
        return _AGENTS
    try:
        import agents as package
    except SurfaceAbsent:
        raise
    except Exception as exc:  # absent package, or absent on sys.path
        raise SurfaceAbsent(
            "src/agents/ is not importable, so the ten entry points cannot be "
            "driven (%s: %s)" % (type(exc).__name__, exc)
        )
    missing = [name for name in TEN_NAMES if not hasattr(package, name)]
    if missing:
        raise SurfaceAbsent(
            "the agents package is missing entry point(s): " + ", ".join(missing)
        )
    _AGENTS = package
    return package


_FEATURES = None


def features():
    """The `features` package, read only through its declared surface (D-13)."""
    global _FEATURES
    if _FEATURES is None:
        import features as package

        _FEATURES = package
    return _FEATURES


_ENGINE = None


def engine():
    """The `engine` package, read only through its declared surface (D-13)."""
    global _ENGINE
    if _ENGINE is None:
        import engine as package

        _ENGINE = package
    return _ENGINE


def flat_encoder():
    """The `flat-numeric` encoder the caller owns (`learner.md` §6)."""
    return features().build_encoder("flat-numeric")


def token_encoder():
    """The `card-tokens` encoder the caller owns (`learner.md` §6)."""
    return features().build_encoder("card-tokens")


_DECISIONS = None


def decisions(count=14):
    """`count` real decisions as `{readout, legal, mask, dense, tokens}` records.

    Each row is the acting seat's first readout of one real hand, encoded by the
    two encoders the ladder declares, with the mask `legal_indices` gives for
    that readout (`features/surface.md` §6, §8; `engine/surface.md` §5).
    """
    global _DECISIONS
    if _DECISIONS is None:
        feats = features()
        eng = engine()
        flat = feats.build_encoder("flat-numeric")
        tokens = feats.build_encoder("card-tokens")
        rows = []
        for hand_seed in range(9300, 9300 + 24):
            hand = eng.new_hand(hand_seed)
            readout = eng.readout(hand)
            rows.append(
                {
                    "readout": readout,
                    "legal": readout["legal"],
                    "mask": tuple(feats.legal_indices(readout["legal"])),
                    "dense": feats.encode(flat, readout),
                    "tokens": feats.encode(tokens, readout),
                }
            )
        _DECISIONS = rows
    return [dict(row) for row in _DECISIONS[:count]]


_SHAPE_DECISIONS = {}


def shape_decisions(shape, count=14):
    """`count` real decisions **on one declared game shape**, in `decisions`' record form.

    The hand is dealt on that shape (`engine.new_hand(seed, shape=shape)`), so the readout
    is that shape's and the mask is its own `legal_indices` sequence — three indices on the
    default shape and six on the other, in that shape's declared order (`shapes.md` §3,
    `sizing.md` §3, `features/surface.md` §6, §8; `engine/surface.md` §4).  Both encodings
    are the ones the ladder declares, since the shape moves the amount normalisers and the
    index order and never an encoding's slot count (`docs/L2/agents/shapes.md` §7).
    """
    if shape not in _SHAPE_DECISIONS:
        feats = features()
        eng = engine()
        flat = feats.build_encoder("flat-numeric")
        tokens = feats.build_encoder("card-tokens")
        rows = []
        for hand_seed in range(9300, 9300 + 24):
            hand = eng.new_hand(hand_seed, shape=shape)
            readout = eng.readout(hand)
            rows.append(
                {
                    "readout": readout,
                    "legal": readout["legal"],
                    "mask": tuple(feats.legal_indices(readout["legal"])),
                    "dense": feats.encode(flat, readout),
                    "tokens": feats.encode(tokens, readout),
                }
            )
        _SHAPE_DECISIONS[shape] = rows
    return [dict(row) for row in _SHAPE_DECISIONS[shape][:count]]


def dense_observation(offset=0.0, width=203):
    """An invented dense observation of the declared `(width,)` float32 shape."""
    import numpy as np

    return np.linspace(-1.0, 1.0, width, dtype=np.float32) + np.float32(offset)


def token_observation(ids=None, positions=40, first=3):
    """An invented token observation of the declared `(40,)` int32 shape."""
    import numpy as np

    if ids is None:
        ids = [(first + offset) % 96 for offset in range(positions)]
    return np.asarray(ids, dtype=np.int32)


def learner_spec(
    backend="numpy",
    kind="deep",
    width=6,
    depth=1,
    seed=LEARNER_SEED,
    sizes=None,
    encoder=None,
    extra=None,
    architecture=None,
    game=None,
):
    """One invented learner spec (`records.md` §3, `surface.md` §4).

    `game` is the spec's optional shape key and is written only when the caller names
    one, because absence **is** the default shape and is not a defaulting of a name
    (`surface.md` §4, `shapes.md` §1, D-29).
    """
    spec = {"backend": backend}
    if architecture is None:
        spec["architecture"] = {"kind": kind, "width": width, "depth": depth}
    else:
        spec["architecture"] = architecture
    spec["seed"] = seed
    if game is not None:
        spec["game"] = game
    if sizes is not None:
        spec["sizes"] = sizes
    if encoder is not None:
        spec["encoder"] = encoder
    if extra:
        spec.update(extra)
    return spec


def transition(
    observation,
    action=1,
    reward=0.0,
    terminal=False,
    legal=ALL_MASK,
    next_legal=ALL_MASK,
    next_observation=None,
):
    """One invented transition record with all seven required keys (`records.md` §4)."""
    return {
        "observation": observation,
        "next_observation": observation if next_observation is None else next_observation,
        "action": action,
        "reward": reward,
        "terminal": terminal,
        "legal": legal,
        "next_legal": next_legal,
    }


def batch(observations, next_observation=None, reward=0.0, terminal=False):
    """A batch of one step per observation, in the order handed."""
    return [
        transition(observation, next_observation=next_observation, reward=reward, terminal=terminal)
        for observation in observations
    ]


def hyper():
    """`learners()['hyper']`: the rule's six fixed declarations (`rule.md` §6)."""
    return agents().learners()["hyper"]


def schedule():
    """The exploration schedule `{start, end, samples}` (`rule.md` §4, §6), never hardcoded."""
    return dict(hyper()["exploration"])


def target_interval():
    """`target_update_interval`, counted in transitions (`rule.md` §3, §6)."""
    return int(hyper()["target_update_interval"])


def family_of(kind):
    """The representation family a kind consumes (`architecture.md` §1)."""
    return "dense-numeric" if kind == DENSE_KIND else "token-sequence"


def observation_template(family):
    """A zero observation of a family's declared shape and dtype, and that spec.

    The shape and dtype come from `features.observation_spec`, which is the
    declaration `architecture.md` §6 sizes every learner against
    (`features/surface.md` §5).
    """
    import numpy as np

    encoder = flat_encoder() if family == "dense-numeric" else token_encoder()
    spec = features().observation_spec(encoder)
    return np.zeros(tuple(spec["shape"]), dtype=spec["dtype"]), spec


def invented_observations(kind, count, seed):
    """`count` invented observations for a learner of `kind`, random but seeded.

    Dense observations are uniform on `[-1, 1]`; token ones are ids inside the
    declared vocabulary. Nothing here is a design number: the shape, the dtype
    and the vocabulary are read from `features.observation_spec`.
    """
    import numpy as np

    family = family_of(kind)
    _zero, spec = observation_template(family)
    rng = np.random.default_rng(seed)
    shape = (count,) + tuple(spec["shape"])
    if family == "dense-numeric":
        return rng.uniform(-1.0, 1.0, size=shape).astype(spec["dtype"])
    return rng.integers(
        0, int(spec["vocabulary"]), size=shape, dtype=spec["dtype"]
    )


def anneal_batch(kind, seed=ANNEAL_SEED, reward_scale=5.0):
    """A batch of the schedule's own length: one anneal's worth of transitions.

    The length is `learners()['hyper']['exploration']['samples']`, read and never
    hardcoded, so one `learn` call moves the schedule position to the annealed
    end of `rule.md` §4. The records are invented, valid and seeded; the rewards
    sit on terminal records only, because ASM-12 delivers the reward at that
    seat's terminal decision and zero at every other one (`rule.md` §2).
    """
    samples = int(schedule()["samples"])
    values = invented_observations(kind, samples, seed)
    records = []
    for step in range(samples):
        terminal = step % 7 == 0
        if not terminal:
            reward = 0.0
        elif step % 14 == 0:
            reward = float(reward_scale)
        else:
            reward = -float(reward_scale)
        records.append(
            transition(
                values[step],
                action=step % 3,
                reward=reward,
                terminal=terminal,
                next_observation=values[(step + 1) % samples],
            )
        )
    return records


def quiet_batch(kind):
    """A batch of the schedule's length that leaves every parameter exactly as it was.

    A zero observation makes every masked value `0.0` (`architecture.md` §4's
    initialisation has zero biases), a zero reward makes the target `0.0` and the
    TD error `0.0`, so `rule.md` §3's semi-gradient step adds nothing — while §4's
    position still advances by the batch's length. That is the only way to hold a
    learner at the annealed rate without moving the values its tie-break reads.
    """
    samples = int(schedule()["samples"])
    zero, _spec = observation_template(family_of(kind))
    return [
        transition(zero, action=1, reward=0.0, terminal=False, next_observation=zero)
        for _ in range(samples)
    ]


def taught_observations(kind, pool=20, seed=TEACH_SEED):
    """The pool of invented observations a `taught_batch` cycles through."""
    return invented_observations(kind, pool, seed)


def taught_batch(kind, reward, pool=20, seed=TEACH_SEED):
    """A batch of the schedule's length teaching index 1 one constant reward.

    Every record is terminal, so the target is the reward alone (`rule.md` §2) and
    the update drives that index's value towards `reward`. Two learners from one
    spec taught `+reward` and `-reward` over the same pool therefore hold visibly
    different parameters, which is what makes "the parameters decide the action"
    an observable claim.
    """
    samples = int(schedule()["samples"])
    values = invented_observations(kind, pool, seed)
    return [
        transition(values[step % pool], action=1, reward=float(reward), terminal=True)
        for step in range(samples)
    ]


def declared_module(module_name):
    """One `agents` submodule, or `SurfaceAbsent`.

    `declared_internal` reads one declared name out of a submodule; this hands the
    submodule itself back, which is what a case needs when it has to stand one of the
    internals `rule.md` §8 declares **aside** for the length of one call — the `off`
    mode's claim that no generator is reached is only observable by replacing the draw
    with one that raises (`shapes.md` §4, `sizing.md` §4, D-13).
    """
    agents()
    try:
        return importlib.import_module("agents." + module_name)
    except SurfaceAbsent:
        raise
    except Exception as exc:
        raise SurfaceAbsent(
            "src/agents/%s.py is not importable, so agents.%s (rule.md §8) cannot be "
            "driven (%s: %s)" % (module_name, module_name, type(exc).__name__, exc)
        )


def declared_internal(module_name, attribute):
    """One internal `rule.md` §8 declares, or `SurfaceAbsent`.

    The six names of §8 are the only private spellings this battery may import;
    they are declared contract for it, and nothing else below the ten entry
    points is (`rule.md` §8, D-13).
    """
    agents()
    try:
        module = importlib.import_module("agents." + module_name)
    except SurfaceAbsent:
        raise
    except Exception as exc:
        raise SurfaceAbsent(
            "src/agents/%s.py is not importable, so %s.%s (rule.md §8) cannot be "
            "driven (%s: %s)" % (module_name, module_name, attribute, type(exc).__name__, exc)
        )
    if not hasattr(module, attribute):
        raise SurfaceAbsent(
            "agents.%s.%s is not declared, and rule.md §8 fixes its name and "
            "signature for this battery" % (module_name, attribute)
        )
    return getattr(module, attribute)


_ERROR_ROOT = None


def refusal_class():
    """`agents.errors.AgentsError`, the root `errors.md` §2 declares and no subclass.

    §2 fixes both the module path (`src/agents/errors.py`) and the root's name: a
    caller catches `AgentsError` to know that *this* module refused it, so a
    refusal that arrives as a `TypeError`, a `numpy` error or an `engine` error
    escapes that catch (`errors.md` §2-§3). The sixteen subclasses stay that
    module's freedom and are never asserted; this root is not (`errors.md` §2).
    """
    global _ERROR_ROOT
    if _ERROR_ROOT is None:
        agents()
        try:
            module = importlib.import_module("agents.errors")
        except Exception as exc:
            raise SurfaceAbsent(
                "src/agents/errors.py is not importable, so the hierarchy of "
                "errors.md §2 cannot be asserted (%s: %s)" % (type(exc).__name__, exc)
            )
        root = getattr(module, "AgentsError", None)
        if not isinstance(root, type) or not issubclass(root, Exception):
            raise SurfaceAbsent(
                "agents.errors.AgentsError is not an exception class, and "
                "errors.md §2 declares it the base of every refusal of this module"
            )
        _ERROR_ROOT = root
    return _ERROR_ROOT


def decision_draw(seed, family, observation, mask):
    """`(u, v)` exactly as `rule.md` §4 takes them from the declared decision key."""
    import numpy as np

    key = declared_internal("rule", "_decision_key")(seed, family, observation, mask)
    draws = np.random.Generator(np.random.PCG64(int.from_bytes(key[:16], "big")))
    return float(draws.random()), float(draws.random())


def greedy_expectation(seed, kind, observations, masks):
    """How many of those decisions the annealed schedule leaves to the greedy arm.

    At the annealed position `n = samples` the rate is the schedule's `end`
    (`rule.md` §4), and the arm is §4's: the exploring arm is taken exactly when
    `u < epsilon`. A decision is greedy-expected when its own keyed draw gives
    `u >= end`, so a case can say what its equality assertions are actually
    deciding on the parameters.
    """
    end = float(declared_internal("rule", "_epsilon")(int(schedule()["samples"])))
    greedy = 0
    for observation, mask in zip(observations, masks):
        u, _v = decision_draw(seed, family_of(kind), observation, mask)
        if u >= end:
            greedy += 1
    return greedy


def container_document(path):
    """`(metadata, parameters)` of one checkpoint: the document parsed, the array as bytes.

    A checkpoint is one zip container of `metadata.json` and `parameters.npy`
    (`checkpoint.md` §2), and the two member names are contract, so a case that has to
    say what a container *records* — its `format_version` and its fields, in the order
    the document holds them — reads that document here rather than through an entry
    point, which is the reading rule of §2's byte paragraph.  The array is handed back
    as the bytes it was read as, so a rewrite carries it through untouched.
    """
    with zipfile.ZipFile(path) as container:
        metadata = json.loads(container.read("metadata.json").decode("utf-8"))
        parameters = container.read("parameters.npy")
    return metadata, parameters


def write_container(target, metadata, parameters):
    """Write one container at `target`: the document re-serialised, the array's bytes kept.

    The container is the one form `checkpoint.md` §2 declares — two members, the array
    written back exactly as it was read — so a rewritten file differs from the one
    `save` wrote in `metadata.json` alone.
    """
    with open(target, "wb") as handle:
        with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_STORED) as container:
            container.writestr("metadata.json", json.dumps(metadata).encode("utf-8"))
            container.writestr("parameters.npy", parameters)
    return target


def version_container(source, target, version, drop=()):
    """Copy one container to `target` in another format version's form.

    `format_version` is set to `version` and each field named in `drop` is removed; both
    members are otherwise the source file's own, which is how a case builds a container
    this module did not write without touching `checkpoints/` (`checkpoint.md` §2, §3).
    """
    metadata, parameters = container_document(source)
    metadata["format_version"] = int(version)
    for field in drop:
        metadata.pop(field, None)
    return write_container(target, metadata, parameters)


def game_container(source, target, version, game=None, drop=()):
    """Copy one container to `target` in another format version's form, with a `game` field.

    `version_container` rewrites the version and drops fields; this one can also **write**
    one, which is how a case builds the version-4 container this module's writer would not
    have produced for that shape — one naming the default shape, or one of an older version
    carrying the field at all — and how it builds a version-4 container from a version-3
    save (`checkpoint.md` §2.1, §3, `shapes.md` §5).  `game` is set only when the caller
    names it, so `game=None` is a container without the field, exactly as
    `version_container` leaves it.
    """
    metadata, parameters = container_document(source)
    metadata["format_version"] = int(version)
    if game is not None:
        metadata["game"] = game
    for field in drop:
        metadata.pop(field, None)
    return write_container(target, metadata, parameters)


def plain_int(value, what):
    """Read a plain Python `int` (not a `bool`, not a numpy scalar)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise AssertionError(
            "%s must be a plain Python int, got %r (%s)"
            % (what, value, type(value).__name__)
        )
    return value


def finite_float(value, what):
    """Read a finite, non-`bool` `float`."""
    import math

    if isinstance(value, bool) or not isinstance(value, float):
        raise AssertionError(
            "%s must be a float, got %r (%s)" % (what, value, type(value).__name__)
        )
    if not math.isfinite(value):
        raise AssertionError("%s must be finite, got %r" % (what, value))
    return value


def chosen_index(descriptor, legal):
    """The index of `descriptor` in `legal`, position-aligned (`features/surface.md` §8)."""
    feats = features()
    for index in feats.legal_indices(legal):
        if feats.decode_action(int(index)) == descriptor:
            return int(index)
    return None


class AgentsCase(unittest.TestCase):
    """Base case: the package, the invented fixtures and the refusal reader."""

    @classmethod
    def setUpClass(cls):
        """One annealed-learner cache per test class.

        A learner is annealed by `learn`, so the 2,000-step cost is paid once per
        class and reused: `act` reads the parameters, the position and the seed
        and advances nothing, so an annealed learner is safe to hand to every
        case of its class (`rule.md` §1, §4). The cache is filled lazily inside a
        case rather than here, so an absent `src/agents/` is still one
        `SurfaceAbsent` failure per contract and never a setup error.
        """
        super().setUpClass()
        cls._annealed = {}

    def agents(self):
        return agents()

    def build(self, **kwargs):
        return agents().build_learner(learner_spec(**kwargs))

    def decisions(self, count=14):
        return decisions(count)

    def tempdir(self):
        import shutil
        import tempfile

        folder = tempfile.mkdtemp(prefix="agents-unit-")
        self.addCleanup(shutil.rmtree, folder, True)
        return folder

    def annealed_learner(self, key, build_kwargs=None, records=None, quiet=False):
        """An annealed learner, learned once per test class and then reused.

        `records` defaults to `anneal_batch` at the schedule's own length, so the
        position reaches the annealed end and the greedy arm of `rule.md` §4
        dominates; `quiet=True` uses `quiet_batch` instead, which reaches the same
        position without moving a value. `key` names the cache slot, so two cases
        that need different learners (or one case that needs two learners from one
        spec) each pay for their own anneal once.
        """
        package = self.agents()
        cache = type(self)._annealed
        if key not in cache:
            spec_kwargs = dict(build_kwargs or {})
            learner = package.build_learner(learner_spec(**spec_kwargs))
            kind = spec_kwargs.get("kind", "deep")
            if records is None:
                records = quiet_batch(kind) if quiet else anneal_batch(kind)
            package.learn(learner, records)
            cache[key] = learner
        return cache[key]

    @staticmethod
    def decision_observations(rows, kind):
        """`(observation, mask)` over decision rows that carry both encoded families."""
        key = "dense" if family_of(kind) == "dense-numeric" else "tokens"
        return [(row[key], row["mask"]) for row in rows]

    def pool_decisions(self, kind, pool=20, seed=TEACH_SEED):
        """`pool` invented decisions over a taught batch's own observations."""
        values = taught_observations(kind, pool, seed)
        masks = tuple(
            NONEMPTY_MASKS[index % len(NONEMPTY_MASKS)] for index in range(pool)
        )
        return values, masks

    def greedy_arm(self, seed, kind, observations, masks, minimum):
        """Assert that at least `minimum` of these decisions are greedy-expected.

        The count is derived from the declared key and the schedule's `end`
        (`rule.md` §4, §8), so a case whose equality assertion passes this guard
        is deciding on the parameters and the tie-break rather than on the
        exploring arm.
        """
        greedy = greedy_expectation(seed, kind, observations, masks)
        self.assertGreaterEqual(
            greedy,
            minimum,
            "only %d of %d decisions are expected in the greedy arm at the "
            "annealed position, so these decisions do not exercise the "
            "parameters or the tie-break (rule.md §4)" % (greedy, len(masks)),
        )
        return greedy

    def assert_refused(self, fn, *args, entry, groups=(), label=""):
        """Assert a refusal: the call raises, the message names `entry` and each group.

        `groups` is a tuple of alternatives-tuples: every group must have one
        member which the message contains. The exception *class* is tolerated
        (`errors.md` §1, §3).
        """
        where = label or entry
        try:
            value = fn(*args)
        except SurfaceAbsent:
            raise
        except Exception as exc:
            message = str(exc)
            self.assertTrue(
                message.strip(),
                "%s was refused with an empty message (%s)" % (where, type(exc).__name__),
            )
            lowered = message.lower()
            self.assertIn(
                entry.lower(),
                lowered,
                "%s was refused without naming %r: %r" % (where, entry, message),
            )
            for group in groups:
                if not any(token.lower() in lowered for token in group):
                    self.fail(
                        "%s was refused without naming any of %r: %r"
                        % (where, tuple(group), message)
                    )
        else:
            self.fail(
                "%s accepted %r, which the contract refuses" % (where, value)
            )

    def assert_agents_refusal(self, fn, *args, entry, groups=(), label=""):
        """Assert the refusal is this module's **own**, naming `entry` and each group.

        `assert_refused` tolerates the class, and rightly: the sixteen subclasses
        are this module's freedom (`errors.md` §2). It still has to be *this*
        module's refusal, catchable as `AgentsError` — a `TypeError` from a
        mistyped record key, a `KeyError`, a `numpy` or an `engine` error that
        escapes a policy is an internal decision leaking as a crash, and a caller
        cannot catch it (`errors.md` §1-§3). The subclass is never asserted; the
        root `refusal_class` reads is (`errors.md` §2).
        """
        where = label or entry
        root = refusal_class()
        try:
            value = fn(*args)
        except SurfaceAbsent:
            raise
        except Exception as exc:
            message = str(exc)
            self.assertIsInstance(
                exc,
                root,
                "%s was refused with %s, which is not this module's own refusal "
                "(%s), so a caller catching AgentsError would miss it: %r"
                % (where, type(exc).__name__, root.__name__, message),
            )
            self.assertTrue(
                message.strip(),
                "%s was refused with an empty message (%s)" % (where, type(exc).__name__),
            )
            lowered = message.lower()
            self.assertIn(
                entry.lower(),
                lowered,
                "%s was refused without naming %r: %r" % (where, entry, message),
            )
            for group in groups:
                if not any(token.lower() in lowered for token in group):
                    self.fail(
                        "%s was refused without naming any of %r: %r"
                        % (where, tuple(group), message)
                    )
        else:
            self.fail(
                "%s accepted %r, which the contract refuses" % (where, value)
            )
