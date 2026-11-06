"""HRN-1 — the surface: six names, one dispatch table, and no seventh name.

Drives `docs/L3/harness/README.md` §3-§5, `layout.md` §1-§3 and
`docs/L2/harness/surface.md` §1: the package exports exactly the six entry points of
`e2e-surface.md` §3.6, in the declared order, declares them in `__all__`, adds no seventh
public name, imports only the five project packages and the three standard-library
modules, and never seeds or advances the global `random` stream.

The module's source is read once, statically, through `harness.__file__` — that is a
reading of the shipped text and not a stand-in for an implementation
(`guardrails.md` G2).  Everything else is driven through the six names.
"""

import ast
import os
import unittest

from _harness_support import (
    DECLARED_NAMES,
    FACTORY_KINDS,
    FORBIDDEN_ROOTS,
    PACKAGES,
    REFUSAL_NAMES,
    SEAM_RECORDING,
    SIX_NAMES,
    STDLIB_ROOTS,
    HarnessCase,
    as_sequence,
    entry,
    harness,
    import_roots,
    pure_case,
    source_text,
)


def imported_names(text):
    """Every name one source text binds through an `import` statement."""
    names = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
    return names


class SurfaceTest(HarnessCase):
    def test_hrn_1_1_the_six_names_exist_are_callable_and_are_the_whole_public_surface(self):
        """HRN-1.1 `__all__` is the six names in the declared order, each is callable, and no seventh public name exists at module level (README §3-§5, layout §1, G1, D-12)."""
        package = harness()
        declared = getattr(package, "__all__", None)
        self.assertIsNotNone(
            declared,
            "the package declares its six exports in __all__ (README §3, layout §1): "
            "%r" % (declared,),
        )
        self.assertEqual(
            list(as_sequence(declared, "__all__")),
            list(SIX_NAMES),
            "__all__ carries the six entry points of README §3 in that order, and adds, "
            "removes and renames none (README §3, D-12, e2e-surface.md §1)",
        )
        self.assertEqual(
            len(list(declared)),
            len(SIX_NAMES),
            "__all__ holds six names and no seventh (G1, layout §1): %r" % (list(declared),),
        )
        for name in SIX_NAMES:
            self.assertTrue(
                callable(entry(name)),
                "harness.%s is one of the six callable entry points (README §3, "
                "surface.md §1)" % (name,),
            )
        _path, text = source_text()
        roots, _dotted = import_roots(text)
        allowed = (
            set(SIX_NAMES)
            | set(REFUSAL_NAMES)
            | set(DECLARED_NAMES)
            | set(roots)
            | imported_names(text)
        )
        public = {name for name in vars(package) if not name.startswith("_")}
        unexpected = sorted(public - allowed)
        self.assertEqual(
            unexpected,
            [],
            "the six names, KINDS/COUNTS/OBJECTS/ROOT/COST, the four refusal classes of "
            "errors.md §2, their imports and every _-name are the only module-level names "
            "(layout §1, G1): a seventh public name is %r" % (unexpected,),
        )
        for name in SIX_NAMES:
            self.assertIn(
                name,
                public,
                "harness.%s is a module-level name of the package (README §3, D-12)"
                % (name,),
            )

    def test_hrn_1_2_the_module_imports_only_the_five_packages_and_three_stdlib_modules(self):
        """HRN-1.2 the module's own source imports the five declared packages and `tempfile`/`time`/`collections.abc`, and no sibling internal module, `pokerkit`, `numpy` or `torch` (README §5, layout §3, G2, D-13)."""
        path, text = source_text()
        roots, dotted = import_roots(text)
        where = os.path.basename(path)
        self.assertEqual(
            {root for root in roots if root in PACKAGES},
            set(PACKAGES),
            "%s imports all five declared packages and no other project package "
            "(README §5, D-13): %r" % (where, sorted(roots)),
        )
        outside = sorted(
            root
            for root in roots
            if root not in PACKAGES + STDLIB_ROOTS and root != "__future__"
        )
        self.assertEqual(
            outside,
            [],
            "%s imports only the five packages and tempfile, time and collections.abc; "
            "os, random, json, math, pokerkit, numpy and torch are the rejected names "
            "(layout §3, battery.md §2, D-8): %r" % (where, outside),
        )
        forbidden = sorted(root for root in roots if root in FORBIDDEN_ROOTS)
        self.assertEqual(
            forbidden,
            [],
            "%s imports no name below another module's entry point and no added "
            "dependency (README §5, layout §3, G2): %r" % (where, forbidden),
        )
        internal = sorted(
            name
            for name in dotted
            if name.split(".")[0] in PACKAGES and "." in name
        )
        self.assertEqual(
            internal,
            [],
            "%s reaches a sibling through its declared entry point and never through an "
            "internal module (README §5, module-map.md §3, D-13): %r" % (where, internal),
        )

    def test_hrn_1_3_the_factory_declares_exactly_six_kinds_and_never_a_seventh(self):
        """HRN-1.3 `factory` refuses a kind the map does not carry, and its refusal names exactly the six declared kinds in sorted order — a seventh kind would have to appear there (README §5, support §2, errors §4, G2, FAM-14.4)."""
        exc = self.refuse(
            lambda: entry("factory")("deck-of-cards", None),
            "UnknownFactoryKind",
            tokens=(
                "deck-of-cards",
                "harness.factory",
                tuple("the map declares " + ", ".join(FACTORY_KINDS),),
            ),
            label="factory('deck-of-cards', None)",
        )
        message = str(exc)
        _, separator, declared = message.partition("the map declares ")
        self.assertTrue(
            separator,
            "the refusal quotes the contract the factory's map declares (errors §3, §4): "
            "%r" % (message,),
        )
        self.assertEqual(
            declared.strip().rstrip("."),
            ", ".join(FACTORY_KINDS),
            "exactly the six declared kinds are listed, sorted, so a seventh kind would "
            "be visible here (errors §4, G2): %r" % (declared,),
        )

    def test_hrn_1_4_no_entry_point_seeds_or_advances_the_global_random_stream(self):
        """HRN-1.4 `fixtures`, `expect`, `seam`, `timings` and a `drive` of a case over pure values leave `random.random()` where a fresh `random.seed(0)` put it (surface §1, ASM-2, protocol §4, G25)."""

        def drive_pure_values():
            record = entry("drive")(pure_case())
            self.assertEqual(
                record["verdict"],
                "pass",
                "the driven pure-value case passes, so the call did what it says: %r"
                % (record,),
            )

        def call_seam():
            policy = entry("seam")(SEAM_RECORDING)
            policy({"street": "preflop"}, ["fold", "check-call", "raise"])

        self.harness()
        self.assert_no_random_motion(
            lambda: (
                call_seam(),
                entry("fixtures")(),
                entry("expect")("zero-sum", [7, -7]),
                entry("expect")("refused", {"refused": True}),
                entry("timings")(),
                drive_pure_values(),
            ),
            "seam, fixtures, expect, timings and a drive over pure values",
        )

    def test_hrn_1_5_the_package_is_one_file_named_init(self):
        """HRN-1.5 `src/harness/` is one file, `__init__.py`, and carries no second module (README §4, layout §1, G1)."""
        path, _text = source_text()
        self.assertEqual(
            os.path.basename(path),
            "__init__.py",
            "src/harness/__init__.py is the whole module (README §4, layout §1): %r"
            % (path,),
        )
        directory = os.path.dirname(path)
        self.assertTrue(
            os.path.isdir(directory),
            "the module is a package directory (README §4): %r" % (directory,),
        )
        modules = sorted(
            name
            for name in os.listdir(directory)
            if name.endswith(".py") and name != "__init__.py"
        )
        self.assertEqual(
            modules,
            [],
            "the package is one file: a file per concern would cost two import-scaffolding "
            "lines, a docstring and a blank each, six times over (README §4, layout §1, "
            "G1); found %r" % (modules,),
        )


if __name__ == "__main__":
    unittest.main()
