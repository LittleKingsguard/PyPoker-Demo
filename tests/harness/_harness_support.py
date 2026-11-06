"""Shared support for the `harness` unit battery.

Puts ``<repo>/src`` on ``sys.path``, imports the `harness` package **lazily inside a
helper** (so an absent ``src/harness/`` is one red case per contract and never a
collection error), and holds the battery's invented instances, its tolerant readers and
the base ``unittest.TestCase`` every case derives from.

Everything asserted here is stated in ``docs/L3/harness/`` — the module design
(``README.md`` §3-§5, ``layout.md`` §1-§3), the driver (``driver.md``), the support
(``support.md``), the expectations (``expectations.md``), the refusals (``errors.md``)
and the guardrail list (``guardrails.md``, G1-G25) — and in ``docs/L2/harness/surface.md``
(Rev 1).  The five modules the harness *calls* are driven through their declared entry
points only — ``features.encode``/``observation_spec``/``legal_indices``,
``agents.build_learner``/``param_count``/``build_baseline``, ``engine.new_hand``/
``readout``/``legal_actions``/``is_terminal``/``play_hand``, ``training.rung`` and
``evaluation.build_pool``/``pool_members``/``match`` (``README.md`` §6, D-13): a stand-in
for one of them would test the stand-in, so the battery uses the real objects they return
(``guardrails.md``'s preamble).

Three things are the battery's own and appear in no design document: the seeds
(6101 … 6110, so no deal collides with the shipped ``0, 1, 2`` or with another battery's),
the seam labels (``echo-legal`` and the empty string, invented so G22's "and every label
that is not ``synthetic``" is driven), and the case ids.  The learner spec, the pool
declaration and the encoding names are *not* invented: they carry declared values
(``records.md`` §3, §8, ``features/surface.md`` §4), because a spec the design never
declares would be testing an invented catalogue rather than the owner's.
"""

import ast
import os
import sys
import unittest
from collections.abc import Mapping

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
SRC_ROOT = os.path.join(REPO_ROOT, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

#: The six entry points, in `README.md` §3's order (`layout.md` §1, `__all__`'s order).
SIX_NAMES = ("drive", "expect", "factory", "fixtures", "seam", "timings")

#: `expectations.md` §2's four kinds, in their declared order (`surface.md` §6).
EXPECTATION_KINDS = ("zero-sum", "legal-choice", "counted", "refused")

#: `errors.md` §4's six factory kinds, in the sorted order its messages spell them.
FACTORY_KINDS = ("baseline", "encoder", "hand", "learner", "pool", "rung")

#: `errors.md` §2's four classes, base first.
REFUSAL_NAMES = (
    "HarnessError",
    "UnknownFactoryKind",
    "UnknownExpectationKind",
    "NoLegalAction",
)

#: `layout.md` §1's five declarations: module-level names that are not surface.
DECLARED_NAMES = ("KINDS", "COUNTS", "OBJECTS", "ROOT", "COST")

#: The five packages `README.md` §5 lets the harness import, and nothing else.
PACKAGES = ("features", "agents", "engine", "training", "evaluation")

#: `layout.md` §3's three standard-library imports; `os`, `random`, `json` and `math` are
#: the rejected four, and `pokerkit`/`numpy`/`torch` are never imported here (D-8, D-13).
STDLIB_ROOTS = ("tempfile", "time", "collections")
FORBIDDEN_ROOTS = ("pokerkit", "numpy", "torch", "os", "random", "json", "math")

# -- the battery's own seeds, one per use, so no deal collides with another -------------
SEED_HAND = 6101        # a bare deal, `factory("hand", …)`
SEED_OTHER = 6102       # a second deal, so "one seed deals one hand" is observable
SEED_EPISODE = 6103     # the seed a driven episode is played at
SEED_CELL = 6104        # the seed a real `evaluation.match` cell is played at
SEED_POLICY = 6105      # the seed a baseline policy is built at
SEED_LEARNER = 6106     # the seed of the invented learner spec
SEED_STRANGER = 6107    # an invented seed the design never mentions

#: Declared values, not inventions: `features/surface.md` §4's two encodings,
#: `agents/surface.md` §11's three baselines and `training/surface.md` §3's first rung.
ENCODING_DENSE = "flat-numeric"
ENCODING_TOKENS = "card-tokens"
BASELINE_CALL = "always-call"
BASELINE_RANDOM = "random"
BASELINE_ORACLE = "oracle"
RUNG_NAME = "R1"

#: `records.md` §3's learner spec, with `agents/surface.md` §3's first declared kind.
LEARNER_SPEC = {
    "backend": "numpy",
    "architecture": {"kind": "naive-stack", "width": 16, "depth": 1},
    "seed": SEED_LEARNER,
}

#: `records.md` §8's declaration: the three keys are required, and a declaration with no
#: version still pins the three baselines (`evaluation/surface.md` §5-§6).
POOL_DECLARATION = {"members": [], "m": 4, "frozen": True}

#: A declaration `evaluation.build_pool` refuses: `m` is not a positive integer.
BAD_POOL_DECLARATION = {"members": [], "m": 0, "frozen": True}

#: `support.md` §3's two documented seam labels, plus two the design never mentions —
#: the label is never checked against a list (`surface.md` §5, D-15).
SEAM_RECORDING = "recording"
SEAM_SYNTHETIC = "synthetic"
SEAM_INVENTED = "echo-legal"
SEAM_EMPTY = ""

#: The battery's own case ids (`driver.md` §4 repeats a case's id verbatim).
CASE_ID = "HRN-invented-case"
CASE_ID_OTHER = "HRN-invented-case-two"

_HARNESS = None
_PACKAGES = {}


class SurfaceAbsent(AssertionError):
    """`src/harness/` (or one of its six names) is not there to be driven.

    Derived from `AssertionError` on purpose: an absent surface is a **red case**, not a
    collection error and not an error in a caller's runner, so every case fails loudly
    with a message naming what is missing (`guardrails.md`'s preamble).
    """


def _import(name):
    import importlib

    return importlib.import_module(name)


def harness():
    """The `harness` package, or `SurfaceAbsent` naming what is missing."""
    global _HARNESS
    if _HARNESS is not None:
        return _HARNESS
    try:
        package = _import("harness")
    except SurfaceAbsent:
        raise
    except Exception as exc:  # absent package, or absent from `src/`
        raise SurfaceAbsent(
            "src/harness/ is not importable, so its six entry points cannot be driven "
            "(%s: %s)" % (type(exc).__name__, exc)
        )
    missing = [name for name in SIX_NAMES if not hasattr(package, name)]
    if missing:
        raise SurfaceAbsent(
            "the harness package is missing entry point(s): " + ", ".join(missing)
        )
    _HARNESS = package
    return package


def entry(name):
    """One of the six entry points, or `SurfaceAbsent` naming it."""
    package = harness()
    value = getattr(package, name, None)
    if value is None:
        raise SurfaceAbsent("the harness package carries no %r entry point" % (name,))
    if not callable(value):
        raise SurfaceAbsent("harness.%s is not callable: %r" % (name, value))
    return value


def ep(name):
    """Shorthand for `entry(name)`."""
    return entry(name)


def error_class(name):
    """One of `errors.md` §2's four refusal classes, or `SurfaceAbsent` naming it."""
    package = harness()
    value = getattr(package, name, None)
    if value is None or not isinstance(value, type):
        raise SurfaceAbsent(
            "the harness package carries no %s refusal class (%r); errors.md §2 declares "
            "%s" % (name, value, ", ".join(REFUSAL_NAMES))
        )
    return value


def _package(name):
    if name not in _PACKAGES:
        try:
            _PACKAGES[name] = _import(name)
        except Exception as exc:
            raise SurfaceAbsent(
                "the %r package is not importable, so the harness cannot be driven "
                "against it (%s: %s)" % (name, type(exc).__name__, exc)
            )
    return _PACKAGES[name]


def features():
    return _package("features")


def agents():
    return _package("agents")


def engine():
    return _package("engine")


def training():
    return _package("training")


def evaluation():
    return _package("evaluation")


# -- tolerant readers: the design fixes the facts, not the container -------------------


def as_mapping(value, what):
    """One mapping, or an `AssertionError` naming what was expected."""
    if not isinstance(value, Mapping):
        raise AssertionError("%s must be one mapping, got %r" % (what, value))
    return value


def as_sequence(value, what):
    """One sequence (never a `str`, never a mapping), or an `AssertionError`."""
    if (
        isinstance(value, (str, bytes))
        or isinstance(value, Mapping)
        or not hasattr(value, "__iter__")
    ):
        raise AssertionError("%s must be a sequence, got %r" % (what, value))
    return value


def as_list(value, what):
    """One sequence, as a list, or an `AssertionError`."""
    return list(as_sequence(value, what))


def as_text(value, what):
    if not isinstance(value, str):
        raise AssertionError("%s must be a string, got %r" % (what, value))
    return value


def as_number(value, what):
    """A real number that is not a `bool` (`expectations.md` §2.5's `_quantity`)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AssertionError("%s must be a real number, got %r" % (what, value))
    return value


def as_int(value, what):
    if isinstance(value, bool) or not isinstance(value, int):
        raise AssertionError("%s must be an integer, got %r" % (what, value))
    return value


def same_observation(left, right):
    """Tolerant equality for two observations, numpy arrays included (`encode`'s return).

    A sequence-of-numbers comparison reads a numpy array as a list, because the battery
    may not carry a dependency beyond the standard library and the six packages.
    """

    def plain(value):
        to_list = getattr(value, "tolist", None)
        if callable(to_list) and not isinstance(value, (list, tuple, Mapping)):
            try:
                return to_list()
            except Exception:
                return value
        if isinstance(value, Mapping):
            return {key: plain(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [plain(item) for item in value]
        return value

    return plain(left) == plain(right)


# -- the battery's own values and cases ------------------------------------------------


def case(case_id=CASE_ID, steps=(), expect=()):
    """One case in `driver.md` §1's shape."""
    return {"id": case_id, "steps": list(steps), "expect": list(expect)}


def pure_value(value=(7, -7)):
    """A zero-argument step returning an invented value and touching no module."""

    def step():
        return value

    return step


def pure_case(case_id=CASE_ID, value=(7, -7), expect=("zero-sum",)):
    """A case over a pure value: it drives no engine call and moves no stream (G25)."""
    return case(case_id, [pure_value(value)], list(expect))


def play(seed=SEED_EPISODE):
    """`engine.play_hand` at one seed, through the two declared baselines."""
    return engine().play_hand(
        seed,
        agents().build_baseline(BASELINE_CALL, SEED_POLICY),
        agents().build_baseline(BASELINE_RANDOM, SEED_POLICY),
    )


def episode_case(case_id=CASE_ID, seed=SEED_EPISODE, ran=None):
    """A case whose one step plays a real hand: `records.md` §5's episode record."""

    def step():
        if ran is not None:
            ran.append(case_id)
        return play(seed)

    return case(case_id, [step], ["zero-sum"])


def real_cell(hands=4, seed=SEED_CELL):
    """One real `evaluation.match` cell: `records.md` §9's record."""
    return evaluation().match(BASELINE_CALL, BASELINE_RANDOM, hands, seed)


def readout(seed=SEED_HAND):
    """A real `engine.readout`: the observation `features.encode` takes."""
    return engine().readout(engine().new_hand(seed))


def invented_descriptors(count=3):
    """Opaque descriptors with no design-document spelling: identity is observable."""
    return [{"descriptor": index} for index in range(count)]


def source_text():
    """The module's own source, for the static read `guardrails.md` G2 allows."""
    package = harness()
    path = getattr(package, "__file__", None)
    if not path or not os.path.isfile(path):
        raise AssertionError(
            "harness.__file__ must name the module's own source file, got %r" % (path,)
        )
    with open(path, encoding="utf-8") as handle:
        return path, handle.read()


def import_roots(text):
    """Every import root in one source text, dotted project imports included.

    Returns `(roots, dotted)` where `roots` is the set of first components and `dotted`
    is every module name an `import`/`from … import` statement spelled.
    """
    tree = ast.parse(text)
    roots, dotted = set(), []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                dotted.append(alias.name)
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                raise AssertionError(
                    "the harness source is a top-level package and imports no relative "
                    "module (layout.md §3): level %d, module %r" % (node.level, node.module)
                )
            name = node.module or ""
            dotted.append(name)
            roots.add(name.split(".")[0])
    return roots, dotted


class HarnessCase(unittest.TestCase):
    """The base every harness case derives from: lazy access and two assertion helpers."""

    def harness(self):
        return harness()

    def subTest(self, *args, **kwargs):
        """A subtest of a harness case, with the surface required **outside** the block.

        The surface is required once per method as well, so an absent `src/harness/`
        fails the case itself and never only a subtest: a red battery must read as red
        in both runners, not as "passed with failed subtests".
        """
        harness()
        return super().subTest(*args, **kwargs)

    def ep(self, name):
        return entry(name)

    def refusal_class(self, name):
        return error_class(name)

    def raised(self, thunk, what):
        """The exception a call raised, or an `AssertionError` naming what should have."""
        try:
            value = thunk()
        except SurfaceAbsent:
            raise
        except Exception as exc:
            return exc
        raise AssertionError("%s must be refused, and it returned %r" % (what, value))

    def not_raised(self, thunk, what):
        """The value a call returned, or an `AssertionError` saying it must not raise."""
        try:
            return thunk()
        except SurfaceAbsent:
            raise
        except Exception as exc:
            raise AssertionError(
                "%s must not raise, and it raised %s: %r"
                % (what, type(exc).__name__, exc)
            )

    def refuse(self, thunk, class_name, tokens=(), label=""):
        """Assert a refusal of one of `errors.md` §2's classes, naming the value.

        `thunk` is called with no argument.  The class is asserted exactly, because
        `errors.md` §2 names the four as design and a subclass would be an invention;
        the message must name the entry point by module path and carry every token of
        `tokens` — one alternative per tuple — which is `errors.md` §3's four-part
        grammar ("the offending value is named", "the entry point is named by its module
        path", "the contract that was violated").
        """
        where = label or class_name
        exc = self.raised(thunk, where)
        expected = error_class(class_name)
        self.assertIs(
            type(exc),
            expected,
            "%s must be refused with %s exactly (errors.md §2, §4); it raised %s: %r"
            % (where, class_name, type(exc).__name__, exc),
        )
        self.assertIsInstance(
            exc,
            error_class("HarnessError"),
            "%s must be a HarnessError, so a caller can catch this module's refusals "
            "without catching a bug of its own (errors.md §1-§2): %r" % (where, exc),
        )
        message = str(exc)
        for group in tokens:
            alternatives = group if isinstance(group, tuple) else (group,)
            self.assertTrue(
                any(token in message for token in alternatives),
                "%s must name %r (errors.md §3 rule 1, §4): %r"
                % (where, alternatives[0], message),
            )
        return exc

    def assert_verdict_record(self, record, kind, label=""):
        """Assert `expectations.md` §1's three keys, in order, and return the record.

        `expect` returns `{kind, verdict, reason}` (`surface.md` §6), so the caller keeps
        the whole record: a verdict is one field of it, never the record itself.
        """
        record = as_mapping(record, (label or "the verdict") + " record")
        self.assertEqual(
            list(record),
            ["kind", "verdict", "reason"],
            "expect(kind, observation) returns {kind, verdict, reason}, in that order "
            "(expectations.md §1): %r" % (list(record),),
        )
        self.assertEqual(
            record["kind"],
            kind,
            "the record repeats the kind as handed, verbatim (expectations.md §1): %r"
            % (record["kind"],),
        )
        self.assertIn(
            record["verdict"],
            ("pass", "fail"),
            "a verdict is 'pass' or 'fail' (expectations.md §1, surface.md §6): %r"
            % (record["verdict"],),
        )
        if record["verdict"] == "pass":
            self.assertIsNone(
                record["reason"],
                "a pass states no reason (expectations.md §1): %r" % (record["reason"],),
            )
        else:
            reason = record["reason"]
            if not isinstance(reason, str) or not reason.strip():
                raise AssertionError(
                    "a failure states one sentence in 'reason' (expectations.md §1): %r"
                    % (reason,)
                )
            self.assertIn(
                kind,
                reason,
                "a failure names the kind verbatim (expectations.md §1): %r" % (reason,),
            )
        return record

    def assert_no_random_motion(self, thunk, label):
        """`guardrails.md` G25: the call leaves the global `random` stream where it was."""
        import random

        random.seed(0)
        before = random.getstate()
        reference = random.random()
        random.seed(0)
        thunk()
        self.assertEqual(
            random.getstate(),
            before,
            "%s must not seed or advance the global random stream (surface.md §1, "
            "ASM-2, protocol.md §4)" % (label,),
        )
        self.assertEqual(
            random.random(),
            reference,
            "%s must leave random.random() at the value it would have had (G25)"
            % (label,),
        )
