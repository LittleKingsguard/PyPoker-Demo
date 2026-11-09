"""Shared support for the `training` unit battery.

Puts `<repo>/src` on `sys.path`, imports the `training` package **lazily inside a
helper** (so an absent `src/training/` is one red case per contract and never a
collection error), and holds the battery's invented instances, its tolerant readers
and the base `unittest.TestCase` every case derives from. A battery's runs write under
`write_root()` — the ambient `PYPOKER_CHECKPOINT_ROOT`, set by `tests/conftest.py` for
the whole session — and never into the shipped `<repo>/checkpoints` tree
(`docs/L2/training/write-root.md` §1, §3, `docs/L3/training/checkpoints.md` §5).

Everything asserted here is stated in `docs/L3/training/` and
`docs/L2/training/surface.md` (Rev 2) and `docs/L2/training/loop.md`; the four consumed
edges are read only through their declared surfaces — `docs/L2/agents/surface.md` §3-§8,
`docs/L2/features/surface.md` §3-§9, `docs/L2/engine/surface.md` §3-§10 and
`docs/L2/evaluation/surface.md` §4-§8 (`module-map.md` §2, D-13). A refusal's *class* is
asserted where `errors.md` §2 names it, and the message is read for the offending value
because §3-§4 make "the value is named" part of the contract.

Three declarations are the battery's own and appear in no design document: the seeds
(5501 … 5507, so no artefact collides with the shipped `0, 1, 2` or with a battery that
ran before this one), the two budgets (10 and 60 hands, where `loop.md` §2's interval is
`budget // 10` and the retained window is observable at both) and the invented rung and
pool labels below. Nothing in this module restates the implementation of `src/training/`:
the readers tolerate the shapes the design leaves free — a `Path` or a `str`, a list or a
tuple, an id given as a string or as a `records.md` §7 record — and assert the shapes the
design fixes.
"""

import importlib
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
SRC_ROOT = os.path.join(REPO_ROOT, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

CHECKPOINT_ROOT = os.path.join(REPO_ROOT, "checkpoints")

#: The six entry points, in `README.md` §3's order (`e2e-surface.md` §3.5, D-12).
SIX_NAMES = ("rungs", "rung", "run", "fairness", "devices", "checkpoints")

#: brief §2's order, which is never rearranged (D-2, `registry.md` §1, §5).
RUNG_NAMES = ("R1", "R2", "R3", "R4", "R5", "R6")

#: `registry.md` §1's nine variants, one row each, in declaration order.
VARIANTS = {
    "R1": ("naive-numeric",),
    "R2": ("naive-numeric-torch",),
    "R3": ("card-tokens",),
    "R4": ("wide", "deep"),
    "R5": ("dense", "sparse"),
    "R6": ("residual", "plain"),
}

#: `registry.md` §1's `primary`, and the previous rung's primary as `carried_from`.
PRIMARY = {
    "R1": "naive-numeric",
    "R2": "naive-numeric-torch",
    "R3": "card-tokens",
    "R4": "deep",
    "R5": "dense",
    "R6": "residual",
}
CARRIED_FROM = {"R1": None}
for _previous, _name in zip(RUNG_NAMES, RUNG_NAMES[1:]):
    CARRIED_FROM[_name] = PRIMARY[_previous]

#: `registry.md` §1's `axis` column, verbatim: the sentence, under a one-word label.
AXES = {
    "R1": "encoding — a naive numeric encoding, hand-rolled NumPy (D-7)",
    "R2": "backend — the same model in PyTorch, for the speed difference (D-7)",
    "R3": "tokenisation — card tokenisation into a learned embedding",
    "R4": "width against depth, at one budget",
    "R5": "dense against sparse connectivity, at one budget",
    "R6": "residual — a residual path against none, at R5's depth",
}

#: The labels `registry.md` §1 says the axis sentences carry (FAM-3.6-3.10 read as text).
AXIS_LABELS = {
    "R1": ("encoding",),
    "R2": ("backend",),
    "R3": ("tokenisation",),
    "R4": ("width", "depth"),
    "R5": ("dense", "sparse", "connectivity"),
    "R6": ("residual",),
}

#: `registry.md` §1's backend and encoding per variant (D-7, D-3).
BACKEND = {
    "naive-numeric": "numpy",
    "naive-numeric-torch": "torch",
    "card-tokens": "torch",
    "wide": "torch",
    "deep": "torch",
    "dense": "torch",
    "sparse": "torch",
    "residual": "torch",
    "plain": "torch",
}
ENCODING = {
    "naive-numeric": "flat-numeric",
    "naive-numeric-torch": "flat-numeric",
    "card-tokens": "card-tokens",
    "wide": "card-tokens",
    "deep": "card-tokens",
    "dense": "card-tokens",
    "sparse": "card-tokens",
    "residual": "card-tokens",
    "plain": "card-tokens",
}

#: `registry.md` §1's architecture column: kind, width, depth, sparsity, residual.
ARCHITECTURE = {
    "naive-numeric": ("naive-stack", 36, 2, 0.0, False),
    "naive-numeric-torch": ("naive-stack", 36, 2, 0.0, False),
    "card-tokens": ("token-embedding", 50, 2, 0.0, False),
    "wide": ("wide", 62, 1, 0.0, False),
    "deep": ("deep", 50, 2, 0.0, False),
    "dense": ("deep", 50, 2, 0.0, False),
    "sparse": ("sparse", 62, 2, 0.5, False),
    "residual": ("residual", 50, 2, 0.0, True),
    "plain": ("plain", 50, 2, 0.0, False),
}

#: `registry.md` §1's Params column — the count `docs/L3/agents/architecture.md` §5 gives.
PARAM_COUNT = {
    "naive-numeric": 10119,
    "naive-numeric-torch": 10119,
    "card-tokens": 10053,
    "wide": 10047,
    "deep": 10053,
    "dense": 10053,
    "sparse": 10109,
    "residual": 10053,
    "plain": 10053,
}

#: ASM-10's band: 10,000 ± 2%, and the tolerance a comparison pair is matched within.
PARAM_BUDGET = 10000
PARAM_TOLERANCE = 0.02

#: `registry.md` §1's shared declarations, written once in `declarations.py`.
LEARNING_RULE = "masked-q-learning"
HYPER = {
    "learning_rate": 0.001,
    "batch_size": 32,
    "target_update_interval": 200,
    "optimiser": "sgd",
    "exploration": {"start": 1.0, "end": 0.05, "samples": 2000},
    "discount": 0.99,
}
SHARED = {
    "learning_rule": LEARNING_RULE,
    "hyper": HYPER,
    "param_budget": PARAM_BUDGET,
    "samples": 1000,
    "seeds": (0, 1, 2),
    "device": "cpu",
    "snapshot_every": 100,
    "table": "live",
}

#: ASM-18's two numbers (`README.md` §4): M = 5 retained of 10 written.
RETAINED = 5
SNAPSHOTS = 10

#: `fairness.md` §4's fourteen held-constant declarations, under its own key names.
#: `rules` and `utilities` are the **sets** of rules and of utilities the two sides are
#: trained under and never one side's value: `learning_rule` left the settings a pair must
#: share when D-19 made it a sixth axis, and D-20's `utility` is the seventh, so neither
#: carries a scalar row (`fairness.md` §4, `declarations.md` §4, `rules.md` §8,
#: `utilities.md` §8, D-19, D-20).
CONSTANT_KEYS = (
    "game",
    "action vocabulary",
    "readout facts",
    "reward",
    "rules",
    "utilities",
    "hyper",
    "sample budget",
    "param budget",
    "seed set",
    "pool",
    "table budget",
    "checkpoint policy",
    "device policy",
)

#: `fairness.md` §3's eight reportable pairs: (left, right) -> the axis they differ in.
ADJACENT_PAIRS = (
    ("R1", "R2", "backend"),
    ("R2", "R3", "encoding"),
    ("R3", "R4", None),
    ("R4", "R5", None),
    ("R5", "R6", "residual"),
)

#: The eight reportable pairs as `fairness.md` §3 tabulates them: the later rung's axis
#: for two configurations, and the field names that differ for two variant entries.
ENTRY_PAIRS = {
    ("R4", "wide", "deep"): ("architecture", {"width", "depth"}),
    ("R5", "dense", "sparse"): ("connectivity", {"sparsity"}),
    ("R6", "residual", "plain"): ("residual", {"residual"}),
}

#: Invented instances. None of these numbers, names or labels appears in a design
#: document (`battery.md` §4), and none collides with the shipped seeds `0, 1, 2` or
#: with a seed an earlier battery used.
RUN_SEED = 5501
SPREAD_SEED = 5502
OTHER_SEED = 5503
SIXTY_SEED = 5504
PAIR_SEED = 5505
CUSTOM_SEED = 5506
FALLBACK_SEED = 5507
REFUSED_SEED = 5511
TINY_BUDGET = 10
SIXTY_BUDGET = 60
INVENTED_RUNG = "R9-invented-5520"
INVENTED_CUSTOM = "rung-invented-5506"
INVENTED_VARIANT = "variant-invented-5506"
INVENTED_FALLBACK = "rung-invented-5507"
INVENTED_VARIANT_FALLBACK = "variant-invented-5507"
INVENTED_POOL = "pool-invented-5506"
INVENTED_PAIR_POOL = "pool-invented-5508"
INVENTED_POOL_A = "pool-invented-5512-a"
INVENTED_POOL_B = "pool-invented-5512-b"
INVENTED_DEVICE = "gpu-invented-5513"
EPISODE_SEED = 7721
FOLD_SEED = 7722
BASELINE_SEED = 7714

#: The declarations a run would refuse (`docs/L2/training/declarations.md` §2-§4,
#: `docs/L3/training/errors.md` §4). Each is the battery's own and names a value in force
#: nowhere: a `learning_rate` the declaration does not carry, a sentence where the
#: `exploration` schedule record is declared, a `hyper` key `HYPER` does not carry, a
#: second learning rule, two intervals off the declared budget ÷ 10, two more rates for a
#: pair `fairness` is asked to hold constant, and a second arm's sample budget. The
#: configuration-level parameter budgets are §2's other honoured declaration.
IGNORED_RATE = 0.00025
IGNORED_SCHEDULE = "linear-decay-5517"
IGNORED_HYPER_KEY = "entropy_decay"
IGNORED_HYPER_VALUE = 0.025
IGNORED_RULE = "masked-q-5517"
IGNORED_INTERVAL = 27
CONFIGURATION_INTERVAL = 34
HELD_RATE_LEFT = 0.00075
HELD_RATE_RIGHT = 0.00125
PAIR_SAMPLES = 60
INVENTED_PARAM_BUDGET = 13400
INVENTED_SECOND_BUDGET = 13500
INVENTED_BUDGET_RUNG = "rung-invented-5519"
INVENTED_BUDGET_VARIANT = "variant-invented-5519"
INVENTED_BUDGET_POOL = "pool-invented-5519"
INVENTED_PAIR_RUNG = "rung-invented-5521"
INVENTED_PAIR_LEFT = "variant-invented-5521-a"
INVENTED_PAIR_RIGHT = "variant-invented-5521-b"

#: The invented two-rule configuration of D-19 (`rules.md` §7): one rung name, two arm
#: names and a declared pool id, none of which a design document carries (`battery.md` §4).
INVENTED_RULE_RUNG = "rung-invented-5522"
INVENTED_RULE_LEFT = "variant-invented-5522-a"
INVENTED_RULE_RIGHT = "variant-invented-5522-b"
INVENTED_RULE_POOL = "pool-invented-5522"

#: The invented two-utility configuration of D-20 (`utilities.md` §7): one rung name, two
#: arm names and a declared pool id, none of which a design document carries
#: (`battery.md` §4, D-15).
INVENTED_UTILITY_RUNG = "rung-invented-5523"
INVENTED_UTILITY_LEFT = "variant-invented-5523-a"
INVENTED_UTILITY_RIGHT = "variant-invented-5523-b"
INVENTED_UTILITY_POOL = "pool-invented-5523"

#: A utility name the catalogue in force nowhere carries (`utilities.md` §5, D-20). It is
#: the battery's own, like `IGNORED_RULE`, so the refusal it earns can only be about the
#: name and never about a catalogue member this battery misread.
IGNORED_UTILITY = "progress-5524"

#: D-20's four invented hands, in the fixed game of D-2: 40 chips in play, 20 dealt to
#: each seat. Two are played with both seats calling, so the winner's net delta is ±2; two
#: are played with both seats raising whenever they may, so the hand goes all-in and the
#: winner's net delta is ±20 (`utilities.md` §2, §4, ASM-6). Each seed is the battery's
#: own and appears in no design document (`battery.md` §4); the cases assert the payoff
#: they found at the seed before they assert the reward it scores.
WIN_TWO_SEED = 7730
ALL_IN_WIN_SEED = 7731
LOSE_TWO_SEED = 7733
ALL_IN_LOSE_SEED = 7734


class SurfaceAbsent(AssertionError):
    """`src/training/`, one of the six entry points, or a declared internal is missing.

    Every case that cannot find the package fails with this message rather than a
    collection error, which is what keeps the battery red for the right reason
    (`README.md` §4, D-12).
    """


_TRAINING = None


def training():
    """Return the `training` package, or raise `SurfaceAbsent`."""
    global _TRAINING
    if _TRAINING is not None:
        return _TRAINING
    try:
        import training as package
    except SurfaceAbsent:
        raise
    except Exception as exc:  # absent package, or absent on sys.path
        raise SurfaceAbsent(
            "src/training/ is not importable, so the six entry points cannot be "
            "driven (%s: %s)" % (type(exc).__name__, exc)
        )
    missing = [name for name in SIX_NAMES if not hasattr(package, name)]
    if missing:
        raise SurfaceAbsent(
            "the training package is missing entry point(s): " + ", ".join(missing)
        )
    _TRAINING = package
    return package


def internal_module(name):
    """One `src/training/<name>.py` module (`README.md` §4 fixes the layout)."""
    training()
    try:
        return importlib.import_module("training." + name)
    except SurfaceAbsent:
        raise
    except Exception as exc:
        raise SurfaceAbsent(
            "src/training/%s.py is not importable, so the names README.md §4 declares "
            "contract for this battery cannot be driven (%s: %s)"
            % (name, type(exc).__name__, exc)
        )


def internal(module_name, attribute):
    """One private name `README.md` §4 makes contract, or `SurfaceAbsent`."""
    module = internal_module(module_name)
    if not hasattr(module, attribute):
        raise SurfaceAbsent(
            "training.%s.%s is not declared, and README.md §4 fixes its spelling for "
            "this battery" % (module_name, attribute)
        )
    return getattr(module, attribute)


_AGENTS = None
_FEATURES = None
_ENGINE = None


def agents():
    """The `agents` package, read only through its declared surface (D-13)."""
    global _AGENTS
    if _AGENTS is None:
        import agents as package

        _AGENTS = package
    return _AGENTS


def features():
    """The `features` package, read only through its declared surface (D-13)."""
    global _FEATURES
    if _FEATURES is None:
        import features as package

        _FEATURES = package
    return _FEATURES


def engine():
    """The `engine` package, read only through its declared surface (D-13)."""
    global _ENGINE
    if _ENGINE is None:
        import engine as package

        _ENGINE = package
    return _ENGINE


_EVALUATION = None


def evaluation():
    """The `evaluation` package, read only through its declared surface (D-13)."""
    global _EVALUATION
    if _EVALUATION is None:
        import evaluation as package

        _EVALUATION = package
    return _EVALUATION


def error_root():
    """`training.errors.TrainingError`, the base `errors.md` §2 declares."""
    module = internal_module("errors")
    root = getattr(module, "TrainingError", None)
    if not isinstance(root, type) or not issubclass(root, Exception):
        raise SurfaceAbsent(
            "training.errors.TrainingError is not an exception class, and errors.md §2 "
            "declares it the base of every refusal of this module"
        )
    return root


#: The sixteen refusal classes `errors.md` §2 fixes, in its order (Rev 2's
#: `IgnoredDeclaration` and `PairDeclarationsDiffer`, and Rev 5's `ChipConservationBroken`,
#: included).
ERROR_CLASSES = (
    "UnknownRung",
    "ConfigurationInvalid",
    "MissingConfigurationKey",
    "VariantCountInvalid",
    "VariantSettingInvalid",
    "InvalidSeeds",
    "InvalidBudget",
    "UnknownDevice",
    "NotAComparisonSide",
    "SideKindMismatch",
    "ComparisonKeyMissing",
    "MultipleAxes",
    "PoolIdsDiffer",
    "IgnoredDeclaration",
    "ChipConservationBroken",
    "PairDeclarationsDiffer",
)


def error_class(name):
    """One refusal class `errors.md` §2 names, and that it descends from the base."""
    module = internal_module("errors")
    klass = getattr(module, name, None)
    if not isinstance(klass, type) or not issubclass(klass, error_root()):
        raise SurfaceAbsent(
            "training.errors.%s is missing or does not descend from TrainingError, and "
            "errors.md §2 declares the sixteen classes as design" % (name,)
        )
    return klass


def baseline_names():
    """The three pinned baselines, in `agents.baselines()`'s order (`fairness.md` §5)."""
    catalogue = agents().baselines()
    if isinstance(catalogue, dict):
        return [str(name) for name in catalogue]
    names = []
    for entry in catalogue:
        if isinstance(entry, dict):
            names.append(str(entry.get("name", entry.get("id"))))
        else:
            names.append(str(entry))
    return names


def learning_rules():
    """The rule catalogue `agents.learners()` publishes, in its declared order.

    `agents.learners()["learning_rules"]` is keyed by the catalogue's members in
    `rules.md` §2's order, and its first member is the default `agents.build_learner`
    applies to a spec naming none. A case reads the vocabulary from that call and never
    restates a rule name, because the catalogue is what a `learning_rule` is judged
    against — the one setting this battery does not invent (`battery.md` §4,
    `docs/L2/training/declarations.md` §2, `rules.md` §2, §4, D-19).
    """
    published = agents().learners()["learning_rules"]
    if hasattr(published, "keys"):
        return tuple(str(name) for name in published)
    names = []
    for entry in published:
        if hasattr(entry, "get"):
            names.append(str(entry.get("name", entry.get("id"))))
        else:
            names.append(str(entry))
    return tuple(names)


def two_rule_names():
    """The two catalogue rules an invented two-rule configuration declares, in order.

    D-19 makes the estimator a parameter a variant names, so a configuration may train two
    arms under two rules (`rules.md` §7-§8); this reader says which two, from the catalogue
    itself, and refuses to invent a name the catalogue does not carry (`rules.md` §2, §4).
    """
    catalogue = learning_rules()
    if len(catalogue) < 2:
        raise SurfaceAbsent(
            "agents.learners() publishes %d rule(s) and D-19 ratifies two estimators, so a "
            "configuration cannot be shown training two rules: %r"
            % (len(catalogue), catalogue)
        )
    return catalogue[0], catalogue[1]


def rule_set(value):
    """A `rules` row read as the **set** of rules it names.

    `fairness.md` §4 and `rules.md` §7 make the row a set of rule names — one per distinct
    estimator — so a case compares it as a set and never as one side's value; whether the
    row is a `list` or a `set` is a shape the design leaves free (`fairness.md` §4, §8).
    """
    return {as_text(rule, "a rule name") for rule in as_sequence(value, "a rules row")}


def utility_catalogue():
    """The utility catalogue `agents.learners()` publishes, as name → member record.

    `utilities.md` §2 makes `learners()["utilities"]` the catalogue: more than one member,
    in a declared order whose first is the default of §5, each stating its `name`, the
    `reward` token it delivers and the `normaliser` that reward is divided by. A case reads
    the vocabulary from that call and never restates a member name, because the catalogue is
    what a `utility` is judged against — the second setting this battery does not invent
    (`battery.md` §4, `utilities.md` §2, §5, D-20).
    """
    published = agents().learners()["utilities"]
    catalogue = {}
    if hasattr(published, "keys"):
        for name in published:
            entry = published[name]
            catalogue[str(name)] = dict(entry) if hasattr(entry, "items") else entry
        return catalogue
    for entry in published:
        if hasattr(entry, "get"):
            catalogue[str(entry.get("name", entry.get("id")))] = dict(entry)
        else:
            catalogue[str(entry)] = {}
    return catalogue


def utility_names():
    """The catalogue's utility names, in the order `agents.learners()` publishes them."""
    return tuple(utility_catalogue())


def two_utility_names():
    """The two catalogue utilities an invented two-utility configuration declares, in order.

    D-20 makes the objective a parameter a variant names, so a configuration may train two
    arms under two utilities (`utilities.md` §2, §7); this reader says which two, from the
    catalogue itself, and refuses to invent a name the catalogue does not carry
    (`utilities.md` §2, §5).
    """
    catalogue = utility_names()
    if len(catalogue) < 2:
        raise SurfaceAbsent(
            "agents.learners() publishes %d utility/utilities and D-20 ratifies two "
            "objectives, so a configuration cannot be shown training two utilities: %r"
            % (len(catalogue), catalogue)
        )
    return catalogue[0], catalogue[1]


def utility_reward(name):
    """The `reward` token the catalogue states for one utility (`utilities.md` §2, D-20).

    A member's reward is the token `training`'s transition step selects its arithmetic by,
    so a case reads it off the catalogue's own record and never off a sentence of its own
    (`utilities.md` §2, §4).
    """
    entry = utility_catalogue().get(as_text(name, "a utility name"))
    reward = entry.get("reward") if hasattr(entry, "get") else None
    if not isinstance(reward, str):
        raise SurfaceAbsent(
            "the catalogue member %r states no `reward` token, and utilities.md §2 makes "
            "the token what a utility delivers: %r" % (name, entry)
        )
    return reward


def utility_set(value):
    """A `utilities` row read as the **set** of utilities it names.

    The utility side of :func:`rule_set`: `utilities.md` §8 and `records.md` §12 make the
    row a set of members — one per distinct objective — so a case compares it as a set and
    never as one side's value, and whether the row is a `list` or a `set` is a shape the
    design leaves free (`utilities.md` §7, §8, D-20).
    """
    return {
        as_text(utility, "a utility name")
        for utility in as_sequence(value, "a utilities row")
    }


# --------------------------------------------------------------------------
# Tolerant readers for the shapes the design leaves free
# --------------------------------------------------------------------------
def as_mapping(value, what):
    """One mapping, or an `AssertionError` naming what was expected."""
    if not isinstance(value, dict) and not hasattr(value, "items"):
        raise AssertionError("%s must be one mapping, got %r" % (what, value))
    return value


def as_sequence(value, what):
    """One sequence (never a `str` or a mapping), or an `AssertionError`."""
    if isinstance(value, (str, bytes)) or hasattr(value, "items"):
        raise AssertionError("%s must be a sequence, got %r" % (what, value))
    try:
        return list(value)
    except TypeError:
        raise AssertionError("%s must be a sequence, got %r" % (what, value))


def as_int(value, what):
    """A plain `int` (not a `bool`, not a numpy scalar)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise AssertionError(
            "%s must be a plain Python int, got %r (%s)"
            % (what, value, type(value).__name__)
        )
    return value


def as_float(value, what):
    """A real number, as a `float`."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AssertionError(
            "%s must be a number, got %r (%s)" % (what, value, type(value).__name__)
        )
    return float(value)


def as_text(value, what):
    """One string."""
    if not isinstance(value, str):
        raise AssertionError(
            "%s must be a string, got %r (%s)" % (what, value, type(value).__name__)
        )
    return value


def seed_key(value):
    """A seed as the decimal string a record keys its per-seed entries by (`loop.md` §4)."""
    return str(as_int(value, "a seed"))


def variant_entries(configuration):
    """`config["variants"]`, one or two `records.md` §2 entries, in declaration order."""
    entries = as_sequence(
        as_mapping(configuration, "a configuration").get("variants"),
        "a configuration's 'variants'",
    )
    return [as_mapping(entry, "a variant entry") for entry in entries]


def variant_name(entry):
    """One variant entry's `name` (`records.md` §2 makes it required)."""
    return as_text(as_mapping(entry, "a variant entry").get("name"), "a variant's 'name'")


def entry_of(configuration, name):
    """The entry of `configuration` whose variant name is `name`."""
    for entry in variant_entries(configuration):
        if variant_name(entry) == name:
            return entry
    raise AssertionError(
        "the configuration declares no variant %r; it declares %r"
        % (name, [variant_name(entry) for entry in variant_entries(configuration)])
    )


def architecture_of(entry):
    """One variant entry's `architecture` mapping (`records.md` §2, `ladder.md` §3)."""
    return as_mapping(
        as_mapping(entry, "a variant entry").get("architecture"),
        "a variant's 'architecture'",
    )


def member_id(member):
    """A pool member's id: a string, or a `records.md` §7 record carrying `id`."""
    if isinstance(member, str):
        return member
    if hasattr(member, "get"):
        return as_text(member.get("id"), "a pool member's 'id'")
    return as_text(member, "a pool member")


def member_ids(members):
    """The ids of a member sequence, in order."""
    return [member_id(member) for member in as_sequence(members, "a member sequence")]


def seed_set(record):
    """The seed set a record states it used, as a tuple of plain ints."""
    return tuple(as_int(value, "a recorded seed") for value in as_sequence(
        as_mapping(record, "a record").get("seeds"), "a record's 'seeds'"
    ))


def curve_block(record, variant, seed):
    """`curves[variant][str(seed)]` — the three ten-element lists of `curves.md` §5."""
    curves = as_mapping(as_mapping(record, "a run record").get("curves"), "'curves'")
    per_variant = as_mapping(curves.get(variant), "curves[%r]" % (variant,))
    block = per_variant.get(seed_key(seed))
    if block is None:
        raise AssertionError(
            "curves[%r] carries no entry keyed %r; it carries %r"
            % (variant, seed_key(seed), sorted(per_variant))
        )
    return as_mapping(block, "curves[%r][%r]" % (variant, seed_key(seed)))


def checkpoint_block(record, variant, seed):
    """`checkpoints[variant][str(seed)]` — `{snapshots, final}` (`loop.md` §3, §4)."""
    block = as_mapping(
        as_mapping(record, "a run record").get("checkpoints"), "'checkpoints'"
    )
    per_variant = as_mapping(block.get(variant), "checkpoints[%r]" % (variant,))
    entry = per_variant.get(seed_key(seed))
    if entry is None:
        raise AssertionError(
            "checkpoints[%r] carries no entry keyed %r; it carries %r"
            % (variant, seed_key(seed), sorted(per_variant))
        )
    return as_mapping(entry, "checkpoints[%r][%r]" % (variant, seed_key(seed)))


def repo_relative(path):
    """`path` as the repository relative spelling `checkpoints.md` §2 fixes, or as given."""
    text = os.fspath(path) if not isinstance(path, str) else path
    root = REPO_ROOT + os.sep
    if text.startswith(root):
        return text[len(root):].replace(os.sep, "/")
    return text.replace(os.sep, "/")


def resolved(path):
    """A record's path as a file on disk, relative paths resolved against the repository."""
    text = os.fspath(path) if not isinstance(path, str) else path
    if os.path.isabs(text):
        return text
    return os.path.join(REPO_ROOT, text)


def write_root():
    """The root a run writes under, read from the environment and never the implementation.

    `docs/L2/training/write-root.md` §1 and §3 fix two roots: the **declared** root,
    `CHECKPOINT_ROOT` (`<repo>/checkpoints`), which every read and the index resolve
    against and which the repository ships, and the **write** root, which is what a run
    actually writes under — the declared root unless the ambient
    `PYPOKER_CHECKPOINT_ROOT` names another one. This derives that answer from
    `os.environ` alone and never by calling `layout._write_root()`, so a case can hold the
    implementation's answer against an independent statement of the contract: a
    redirected run's artefacts must land here, and the shipped tree must gain nothing
    (`docs/L3/training/checkpoints.md` §2, §5).
    """
    return os.path.abspath(os.environ.get("PYPOKER_CHECKPOINT_ROOT") or CHECKPOINT_ROOT)


def checkpoint_tree():
    """Every file under `<repo>/checkpoints/`, repository-relative, sorted.

    The **declared** tree, which the repository ships and every read resolves against:
    a battery's own artefacts land in `write_tree()` and never here
    (`docs/L2/training/write-root.md` §1, §3, `docs/L3/training/checkpoints.md` §5).
    """
    found = []
    for base, _dirs, files in os.walk(CHECKPOINT_ROOT):
        for name in files:
            found.append(repo_relative(os.path.join(base, name)))
    return sorted(found)


def write_tree(root=None):
    """Every file under the write root, relative to that root with POSIX separators, sorted.

    The counterpart of `checkpoint_tree()`, because a battery's own artefacts land in the
    first and never in the second (`docs/L2/training/write-root.md` §1, §3). A case about
    a call that writes nothing must read this tree: after the redirection "the shipped
    tree gained no file" is trivially true for a run and could not fail, so a pure call
    has to be shown to have left *this* root alone as well. `root` is `write_root()` when
    it is `None`; an absent root is no files at all (`tests/conftest.py`'s private
    `mkdtemp` is the session's, and a case may pass its own).
    """
    base = write_root() if root is None else root
    if not os.path.isdir(base):
        return []
    found = []
    for directory, _dirs, files in os.walk(base):
        for name in files:
            found.append(
                os.path.relpath(os.path.join(directory, name), base).replace(os.sep, "/")
            )
    return sorted(found)


def paths_mentioning(needle, tree=None):
    """The paths in the checkpoint tree that contain `needle` (a seed or a rung label)."""
    paths = checkpoint_tree() if tree is None else tree
    return [path for path in paths if needle in path]


def listed_paths(value):
    """Every checkpoint-shaped path a value lists, as listed, repeats included.

    `checkpoints.md` §4 and FAM-12.6 make "no artefact is listed twice" an assertion
    *about the listing*, so the reader keeps every repeat: de-duplicating would erase
    the only evidence the assertion is about (`battery.md` §2).
    """
    suffixes = (".ckpt",)

    def is_path(text):
        return isinstance(text, str) and text.lower().endswith(suffixes)

    found = []

    def walk(node, depth=0):
        if depth > 24:
            return
        if hasattr(node, "items"):
            names = []
            for key, inner in node.items():
                candidates = (key,) if is_path(key) else ()
                if is_path(inner):
                    candidates += (inner,)
                for candidate in candidates:
                    if candidate not in names:
                        names.append(str(candidate))
            found.extend(names)
            for inner in node.values():
                if isinstance(inner, str):
                    continue
                walk(inner, depth + 1)
        elif isinstance(node, (list, tuple, set, frozenset)):
            for inner in node:
                if is_path(inner):
                    found.append(str(inner))
                elif not isinstance(inner, str):
                    walk(inner, depth + 1)

    walk(value)
    return found


def same_observation(left, right):
    """Two encoded observations equal value for value (a numpy array or a sequence)."""
    try:
        import numpy as np

        return bool(np.array_equal(np.asarray(left), np.asarray(right)))
    except Exception:
        return left == right


# --------------------------------------------------------------------------
# The battery's invented instances
# --------------------------------------------------------------------------
def custom_configuration(name=INVENTED_CUSTOM, variant=INVENTED_VARIANT,
                         pool_id=INVENTED_POOL, seeds=None, samples=TINY_BUDGET,
                         table="live"):
    """A configuration written to `ladder.md` §3's shape and in no design document.

    One variant, the naive stack of `registry.md` §4's arithmetic, a pool declared by
    this battery with no members — so the pool it trains against is the three pinned
    baselines and the record still carries **its own** declared id (`loop.md` §3,
    `registry.md` §3, FAM-15.2).
    """
    entry = {
        "name": variant,
        "backend": "numpy",
        "encoding": "flat-numeric",
        "architecture": {
            "kind": "naive-stack",
            "width": 36,
            "depth": 2,
            "sparsity": 0.0,
            "residual": False,
        },
        "learning_rule": LEARNING_RULE,
        "hyper": HYPER,
        "param_budget": PARAM_BUDGET,
        "samples": samples,
        "seeds": list(seeds if seeds is not None else (CUSTOM_SEED,)),
        "device": "cpu",
        "snapshot_every": samples // SNAPSHOTS,
        "table": table,
    }
    configuration = {
        "name": name,
        "axis": "the encoding of a configuration in no registry",
        "carried_from": None,
        "primary": variant,
        "variants": [entry],
        "pool": {
            "id": pool_id,
            "lineage": None,
            "m": RETAINED,
            "frozen": True,
            "members": [],
        },
        "seeds": list(seeds if seeds is not None else (CUSTOM_SEED,)),
        "samples": samples,
        "param_budget": PARAM_BUDGET,
        "table": table,
        "device": "cpu",
        "snapshot_every": samples // SNAPSHOTS,
    }
    return configuration


def with_pool(entry, pool_id):
    """A copy of a variant entry declaring the pool id both arms of a rung train against."""
    copy = dict(entry)
    copy["pool"] = {
        "id": pool_id,
        "lineage": None,
        "m": RETAINED,
        "frozen": True,
        "members": [],
    }
    return copy


def two_rule_configuration(name=INVENTED_RULE_RUNG, left=INVENTED_RULE_LEFT,
                           right=INVENTED_RULE_RIGHT, pool_id=INVENTED_RULE_POOL,
                           seeds=None, samples=TINY_BUDGET):
    """A two-entry configuration whose arms declare the catalogue's two rules (D-19).

    The invented configuration's one entry, declared twice: the second arm carries the
    catalogue's second rule and nothing else moves, so the pair the run trains differs on
    the `rule` axis alone and every setting both arms must share — `hyper`, `samples`,
    `seeds`, `device`, `snapshot_every`, `table`, `param_budget` — is one declaration
    (`rules.md` §7-§8, `docs/L2/training/declarations.md` §4, `docs/L3/training/fairness.md`
    §3). The rules are read from `agents.learners()`, so no name is restated here
    (`rules.md` §2, §4).
    """
    first_rule, second_rule = two_rule_names()
    configuration = custom_configuration(
        name=name, variant=left, pool_id=pool_id, seeds=seeds, samples=samples
    )
    first = with_setting(variant_entries(configuration)[0], learning_rule=first_rule)
    second = with_setting(first, name=right, learning_rule=second_rule)
    configuration["variants"] = [first, second]
    configuration["primary"] = left
    configuration["axis"] = "the learning rule, at one architecture"
    return configuration


def two_utility_configuration(name=INVENTED_UTILITY_RUNG, left=INVENTED_UTILITY_LEFT,
                              right=INVENTED_UTILITY_RIGHT, pool_id=INVENTED_UTILITY_POOL,
                              seeds=None, samples=TINY_BUDGET):
    """A two-entry configuration whose arms declare the catalogue's two utilities (D-20).

    The utility side of :func:`two_rule_configuration`, from the same invented entry: the
    second arm carries the catalogue's second utility and nothing else moves, so the pair
    the run trains differs on the `utility` axis alone and every setting both arms must
    share — `hyper`, `samples`, `seeds`, `device`, `snapshot_every`, `table`,
    `param_budget`, and the learning rule — is one declaration (`utilities.md` §7-§8,
    `records.md` §2, `docs/L2/training/declarations.md` §4). The utilities are read from
    `agents.learners()`, so no member name is restated here (`utilities.md` §2, §5).
    """
    first_utility, second_utility = two_utility_names()
    configuration = custom_configuration(
        name=name, variant=left, pool_id=pool_id, seeds=seeds, samples=samples
    )
    first = with_setting(variant_entries(configuration)[0], utility=first_utility)
    second = with_setting(first, name=right, utility=second_utility)
    configuration["variants"] = [first, second]
    configuration["primary"] = left
    configuration["axis"] = "the utility, at one architecture"
    return configuration


def with_setting(entry, **settings):
    """A copy of a variant entry with top-level settings replaced."""
    copy = dict(entry)
    copy.update(settings)
    return copy


def with_architecture(entry, **settings):
    """A copy of a variant entry with architecture settings replaced."""
    copy = dict(entry)
    copy["architecture"] = dict(architecture_of(entry), **settings)
    return copy


# --------------------------------------------------------------------------
# Runs, cached once per session
# --------------------------------------------------------------------------
_RUNS = {}


def run_once(key, thunk):
    """Call `thunk` once per session and hand the same record to every case."""
    if key not in _RUNS:
        _RUNS[key] = thunk()
    return _RUNS[key]


def registry_run(rung_name, seeds, budget, device=None):
    """One run of a registry rung, at the battery's budget, cached by its arguments."""
    args = (rung_name, tuple(seeds), budget, device)

    def thunk():
        package = training()
        if device is None:
            return package.run(rung_name, list(seeds), budget)
        return package.run(rung_name, list(seeds), budget, device)

    return run_once(("registry",) + args, thunk)


def one_seed_run():
    """R1 at one invented seed, 10 hands: `budget // 10` is one, so ten points."""
    return registry_run("R1", (RUN_SEED,), TINY_BUDGET)


def repeated_run():
    """The same tuple as `one_seed_run`, run a second time (`loop.md` §7's determinism)."""
    return registry_run("R1", (RUN_SEED,), TINY_BUDGET, device="cpu")


def two_seed_run():
    """R1 at two invented seeds, 10 hands: the first run whose spread can be non-zero."""
    return registry_run("R1", (SPREAD_SEED, RUN_SEED), TINY_BUDGET)


def other_seed_run():
    """R1 at a third invented seed, 10 hands: a different seed is a different record."""
    return registry_run("R1", (OTHER_SEED,), TINY_BUDGET)


def sixty_hand_run():
    """R1 at 60 hands: `budget // 10` is 6, so the ten snapshots end at step 0060."""
    return registry_run("R1", (SIXTY_SEED,), SIXTY_BUDGET)


def pair_run():
    """R4's two arms at one invented seed, 10 hands: one record, one pool id."""
    return registry_run("R4", (PAIR_SEED,), TINY_BUDGET)


def custom_run():
    """`run` of the invented configuration, with `seeds` and `budget` omitted."""
    configuration = custom_configuration()

    def thunk():
        return training().run(configuration)

    return run_once(("custom", INVENTED_CUSTOM), thunk)


def two_rule_run():
    """`run` of the invented two-rule configuration, at the battery's tiny budget.

    One seed and ten hands per arm, so `budget // 10` is one and every arm's curve closes
    with ten points. Both arms are trained — D-19 makes the estimator a parameter a variant
    names, so a configuration declaring two catalogue rules trains two learners — and the
    record names each variant's rule and the run's `rules` set (`rules.md` §7,
    `docs/L3/training/loop.md` §1 step 3, §3-§4).
    """
    configuration = two_rule_configuration()

    def thunk():
        return training().run(configuration)

    return run_once(("two-rule", INVENTED_RULE_RUNG), thunk)


def two_utility_run():
    """`run` of the invented two-utility configuration, at the battery's tiny budget.

    One seed and ten hands per arm, so `budget // 10` is one and every arm's curve closes
    with ten points. Both arms are trained — D-20 makes the objective a parameter a variant
    names, so a configuration declaring two catalogue utilities trains two learners — and the
    record names each variant's utility and the run's `utilities` set (`utilities.md` §7,
    `docs/L3/training/loop.md` §1 step 3, §3-§4, `records.md` §12).
    """
    configuration = two_utility_configuration()

    def thunk():
        return training().run(configuration)

    return run_once(("two-utility", INVENTED_UTILITY_RUNG), thunk)


def fallback_configuration():
    """A configuration declaring no `seeds` of its own: its entry carries them (§5)."""
    configuration = custom_configuration(
        name=INVENTED_FALLBACK,
        variant=INVENTED_VARIANT_FALLBACK,
        pool_id="pool-invented-5507",
        seeds=(FALLBACK_SEED,),
        samples=TINY_BUDGET,
    )
    configuration.pop("seeds")
    return configuration


def fallback_run():
    """`run` of that configuration: the seed set comes from its first variant entry."""
    configuration = fallback_configuration()

    def thunk():
        return training().run(configuration)

    return run_once(("fallback", INVENTED_FALLBACK), thunk)


def variant_learner(entry):
    """A learner built from one variant entry through the granted `agents` call.

    The count a case reads from it is `agents.param_count`'s, which is the arithmetic
    `registry.md` §4 tabulates (FAM-3.15, FAM-13.3); the encoder is omitted so the
    learner is sized from the kind's declared `observation_size`
    (`agents/surface.md` §3-§5).
    """
    spec = {
        "backend": entry["backend"],
        "architecture": dict(architecture_of(entry)),
        "seed": RUN_SEED,
    }
    return agents().build_learner(spec)


_COUNTS = {}


def param_count_of(entry):
    """`agents.param_count` of one variant entry's learner, cached by variant name."""
    name = variant_name(entry)
    if name not in _COUNTS:
        _COUNTS[name] = agents().param_count(variant_learner(entry))
    return _COUNTS[name]


# --------------------------------------------------------------------------
# One real episode, for the transition cases
# --------------------------------------------------------------------------
_ENCODERS = {}


def encoder(name="flat-numeric"):
    """One encoder the ladder declares, cached (`features/surface.md` §4)."""
    if name not in _ENCODERS:
        _ENCODERS[name] = features().build_encoder(name)
    return _ENCODERS[name]


def baseline_policy(name="always-call", seed=BASELINE_SEED):
    """One of the three pinned baselines as a policy (`agents/surface.md` §12)."""
    return agents().build_baseline(name, seed)


def fold_first_policy():
    """A policy that folds whenever folding is legal, else takes the first descriptor.

    It is what makes `episode.md` §3's empty list observable: the button folds preflop,
    so the big blind never acts and that seat's decision list is empty.
    """
    fold = features().decode_action(0)

    def policy(readout, legal_actions):
        del readout
        for descriptor in legal_actions:
            if descriptor == fold:
                return descriptor
        return legal_actions[0]

    return policy


def raise_first_policy():
    """A policy that raises whenever raising is legal, else calls, else takes the first.

    It is what makes D-20's all-in numbers observable: in the fixed game of D-2 a seat that
    raises at every opportunity commits the twenty chips it was dealt, so the hand's two
    payoffs are ±20 and the shortfall reward is +1.000 / −3.000 (`utilities.md` §2, §4,
    ASM-6).
    """
    raise_descriptor = features().decode_action(2)
    call_descriptor = features().decode_action(1)

    def policy(readout, legal_actions):
        del readout
        for wanted in (raise_descriptor, call_descriptor):
            for descriptor in legal_actions:
                if descriptor == wanted:
                    return descriptor
        return legal_actions[0]

    return policy


_EPISODES = {}


def episode(seed=EPISODE_SEED):
    """One real episode at one invented seed, both seats always-call (`engine` §10)."""
    if seed not in _EPISODES:
        _EPISODES[seed] = engine().play_hand(
            seed, baseline_policy("always-call", BASELINE_SEED),
            baseline_policy("always-call", BASELINE_SEED),
        )
    return _EPISODES[seed]


def fold_episode():
    """One real episode whose button folds preflop, so seat 1 never acts."""
    if "fold" not in _EPISODES:
        _EPISODES["fold"] = engine().play_hand(
            FOLD_SEED, fold_first_policy(),
            baseline_policy("always-call", BASELINE_SEED),
        )
    return _EPISODES["fold"]


def all_in_episode(seed=ALL_IN_WIN_SEED):
    """One real episode whose two seats raise whenever they may, so the hand goes all-in.

    The engine deals one seeded hand and both seats commit their twenty chips, so the
    episode's payoffs are ±20 and the shortfall reward is +1.000 at the winner's terminal
    decision and −3.000 at the loser's (`utilities.md` §2, §4, `records.md` §5, ASM-6).
    Each call builds its policies fresh, because a baseline is a stateful object and a
    shared one would make the second hand depend on the first.
    """
    key = ("all-in", int(seed))
    if key not in _EPISODES:
        _EPISODES[key] = engine().play_hand(
            int(seed), raise_first_policy(), raise_first_policy()
        )
    return _EPISODES[key]


def decisions_of(record):
    """An episode record's ordered decisions (`records.md` §5)."""
    return [
        as_mapping(decision, "one episode decision")
        for decision in as_sequence(
            as_mapping(record, "an episode record").get("decisions"),
            "an episode record's 'decisions'",
        )
    ]


def decision_seat(decision):
    """The seat a decision belongs to.

    `engine.play_hand` reports a decision's seat as `(index, on_button)` here, and a
    bare index is what `episode.md` §1 hands `_seat`; this reader accepts both, because
    which of the two the episode record spells is the engine's shape and not this
    module's contract (`engine/surface.md` §10, `records.md` §5).
    """
    value = as_mapping(decision, "one episode decision").get("seat")
    if isinstance(value, (list, tuple)):
        return as_int(value[0], "a decision's seat index")
    return as_int(value, "a decision's seat")


def seat_decisions(record, seat):
    """The decisions of one seat, in the order the hand played them (`episode.md` §3)."""
    return [decision for decision in decisions_of(record) if decision_seat(decision) == seat]


def payoff_of(record, seat):
    """One seat's net chip delta (`records.md` §5, ASM-12)."""
    payoffs = as_mapping(as_mapping(record, "an episode record").get("payoffs"), "'payoffs'")
    for key, value in payoffs.items():
        if key == seat or str(key) == str(seat):
            return as_float(value, "a seat's payoff")
    raise AssertionError("the episode record carries no payoff for seat %r: %r" % (seat, payoffs))


# --------------------------------------------------------------------------
# The base case
# --------------------------------------------------------------------------
class TrainingCase(unittest.TestCase):
    """Base case: the package, the invented fixtures and the refusal reader."""

    def training(self):
        return training()

    def internal(self, module_name, attribute):
        return internal(module_name, attribute)

    def refuse(self, thunk, error_name, groups=(), label="", entry=None):
        """Assert a refusal of the class `errors.md` §2 names, naming the value.

        `thunk` is called with no argument. The class is asserted exactly, because
        `errors.md` §2 names the sixteen classes as design and a subclass would be an
        invention; the message must name the entry point that refused (`errors.md` §3)
        and every token of `groups` — one alternative per tuple — which is how a case
        says "the offending value is named" (§3 rule 1, §4).

        `entry` names the entry point the message must mention when the class itself does
        not fix one: `entry_name` maps a class to the entry point `errors.md` §2's comment
        gives it once, and `PairDeclarationsDiffer` is the one class **two** entry points
        raise — `run` for a configuration's two arms and `fairness` for a pair it is asked
        to hold constant. Left unset, the table's answer stands; a `fairness`-raised case
        passes `entry="fairness"` rather than weakening the assertion, so no case reads a
        message it did not pin (`docs/L2/training/declarations.md` §3-§4, `docs/L3/
        training/errors.md` §2, §4).
        """
        klass = error_class(error_name)
        where = label or error_name
        try:
            value = thunk()
        except SurfaceAbsent:
            raise
        except Exception as exc:
            self.assertIs(
                type(exc),
                klass,
                "%s must be refused with %s exactly (errors.md §2, §4); it raised %s: %r"
                % (where, klass.__name__, type(exc).__name__, exc),
            )
            self.assertIsInstance(
                exc,
                error_root(),
                "%s must be a TrainingError, so a caller can catch this module's "
                "refusals without catching a bug (errors.md §1-§2): %r" % (where, exc),
            )
            message = str(exc)
            self.assertTrue(
                message.strip(), "%s was refused with an empty message" % (where,)
            )
            lowered = message.lower()
            named = self.entry_name(klass) if entry is None else str(entry)
            self.assertIn(
                "training." + named.lower(),
                lowered,
                "%s's message must name the entry point that refused, training.%s "
                "(errors.md §3): %r" % (where, named, message),
            )
            for group in groups:
                if not any(str(token).lower() in lowered for token in group):
                    self.fail(
                        "%s was refused without naming any of %r: %r"
                        % (where, tuple(group), message)
                    )
            return exc
        self.fail("%s accepted %r, which the contract refuses" % (where, value))

    @staticmethod
    def entry_name(klass):
        """The entry point a refusal class belongs to (`errors.md` §2's comments)."""
        if klass.__name__ in ("UnknownRung",):
            return "rung"
        if klass.__name__ in (
            "NotAComparisonSide",
            "SideKindMismatch",
            "ComparisonKeyMissing",
            "MultipleAxes",
            "PoolIdsDiffer",
        ):
            return "fairness"
        return "run"

    def assert_tree_untouched(self, before, label):
        """The **shipped** tree under `<repo>/checkpoints` gained no file since `before`.

        It asserts exactly one thing, and it is not weakened: the declared root the
        repository ships and every read resolves against gained nothing
        (`docs/L3/training/checkpoints.md` §5). That is what a pure function must leave
        untouched (`rung`, `rungs`, `fairness`), and it is also what a **redirected** run
        leaves untouched, because a run's writes go under `write_root()` — the ambient
        `PYPOKER_CHECKPOINT_ROOT` — and never into the shipped set
        (`docs/L2/training/write-root.md` §1, §3). Because the second half is true of
        every run after the redirection, a case about a call that might write reads
        `write_tree()` beside this tree: "the shipped tree gained nothing" alone would be
        trivially true and could not fail (`battery.md` §2).
        """
        after = checkpoint_tree()
        added = [path for path in after if path not in before]
        self.assertEqual(
            added,
            [],
            "%s writes no file: the checkpoint tree gained %r (D-3, `checkpoints.md` §1)"
            % (label, added),
        )

    def assert_no_hand_dealt(self, before, label):
        """The global `random` stream is where it was, so no hand was dealt (ASM-2)."""
        import random

        self.assertEqual(
            random.getstate(),
            before,
            "%s must not deal a hand: only dealing moves the global stream, and it was "
            "moved here (seeds.md §1, ASM-2)" % (label,),
        )
