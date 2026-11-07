"""HRN-9 — the battery's write root is private under both runners, and its two hooks are harness-owned.

Drives `docs/L3/harness/layout.md` §5, `docs/L2/training/write-root.md` §3-§4 and
`docs/L1/battery.md` §2, and holds that write rule and ASM-18's eighteen shipped artefacts
against the documented census: the two hooks a documented runner loads —
`tests/conftest.py` under `pytest`, and `tests/e2e/__init__.py` under
`unittest discover -s tests/e2e -t .`, which loads no conftest at all — set
`PYPOKER_CHECKPOINT_ROOT` to a private `tempfile.mkdtemp(prefix="pypoker-battery-checkpoints-")`
at import, **unconditionally**, so a value inherited from a developer's shell cannot send a
battery's writes into `<repo>/checkpoints`; the directory is removed when the process that
created it exits. The two hooks are **idempotent with each other**: the one that makes the root
marks it in `PYPOKER_BATTERY_ROOT`, a name no file under `src/` reads, and the second declines,
so a process that loads both ends with one root. The conftest keeps its one existing job —
`<repo>/src` on `sys.path` once — and neither hook imports a subsystem, so the load itself is
invisible to the five packages and to `harness` (layout.md §5, module-map.md §5, D-13).

Each case runs ONE child interpreter with an explicit environment in which the inherited root is
the shipped tree — a hostile developer shell — loads the hook under judgement the way its own
runner does: the conftest by `importlib` for pytest, `import tests.e2e` for the census. HRN-9.3
runs one child per documented environment under judgement — `PYTHONPATH` removed, and
`PYTHONPATH=src` as the documented command line spells it — so its verdict is the same whichever
way the battery itself is invoked, and HRN-9.5 loads both hooks in one child, which is what a
`pytest` session does. The parent imports no subsystem and no pytest: these cases judge the
hooks, not the package (`battery.md` §2, D-13).
"""

import json
import os
import subprocess
import sys
import unittest

from _harness_support import REPO_ROOT

#: The file under judgement: harness-owned, executed by every battery's pytest invocation
#: (`docs/L3/harness/layout.md` §5, `module-map.md` §5).
CONFTEST_PATH = os.path.join(REPO_ROOT, "tests", "conftest.py")

#: `<repo>/checkpoints`, the shipped tree `layout.md` §5 says a battery must never write into.
HOSTILE_ROOT = os.path.join(REPO_ROOT, "checkpoints")

#: The variable `write-root.md` §3 names, and the prefix `layout.md` §5 fixes for its value.
ROOT_VARIABLE = "PYPOKER_CHECKPOINT_ROOT"
ROOT_PREFIX = "pypoker-battery-checkpoints-"

#: `<repo>/src`: the one path the conftest puts on `sys.path`, exactly once — the outcome
#: `layout.md` §5 fixes, and not a position (`module-map.md` §5, `battery.md` §2).
SRC_PATH = os.path.join(REPO_ROOT, "src")

#: The one package the child imports by its bare name to show the `sys.path` entry is
#: functional: `engine` is the foundation the other four import and pulls in `pokerkit` only,
#: so the probe is cheap and stable (`module-map.md` §3, D-13).
IMPORT_PROBE = "engine"

#: The second hook: the e2e battery's package init, which
#: `unittest discover -s tests/e2e -t .` imports — as the package `tests.e2e` — before it
#: imports a case module, and which `pytest` loads beside the conftest (`layout.md` §5).
E2E_INIT_PATH = os.path.join(REPO_ROOT, "tests", "e2e", "__init__.py")

#: The battery-only marker `layout.md` §5 adds beside the override: written by the hook that
#: makes the root, read by the second hook so it declines, and read by nothing under `src/`.
MARKER_VARIABLE = "PYPOKER_BATTERY_ROOT"

#: The child: load the conftest the way pytest does (importlib, never `runpy`), snapshot
#: `sys.path` and the six packages straight after the load, then import one of the six by its
#: bare name — and report all of it on one JSON line, so a failure names its reason instead of
#: an opaque traceback (layout.md §5, module-map.md §5, battery.md §2).
CHILD = """\
import importlib, importlib.util, json, os, sys
spec = importlib.util.spec_from_file_location("conftest_probe", %(conftest)r)
module = importlib.util.module_from_spec(spec)
sys.modules["conftest_probe"] = module
spec.loader.exec_module(module)
paths = list(sys.path)
modules = [name for name in ("engine", "features", "agents", "evaluation", "training", "harness") if name in sys.modules]
imported = None
error = None
try:
    imported = importlib.import_module(%(probe)r).__name__
except BaseException as exc:
    error = type(exc).__name__ + ": " + str(exc)
path = os.environ.get("PYPOKER_CHECKPOINT_ROOT")
print(json.dumps({"path": path, "exists": bool(path) and os.path.isdir(path), "modules": modules, "paths": paths, "imported": imported, "error": error}))
"""

#: The child that loads the census's hook the way `unittest discover -s tests/e2e -t .` does:
#: `<repo>` on `sys.path`, then `import tests.e2e` — the import `TestLoader.discover` performs
#: on the start directory, and the reason the documented `-t .` form needs the package — then
#: reports the root, the marker, and whether any case module was already in `sys.modules`, so
#: "the hook runs before a case" is a fact the case can assert (`layout.md` §5, battery.md §2).
E2E_CHILD = """\
import importlib, json, os, sys
sys.path.insert(0, %(repo)r)
package = None
error = None
try:
    package = importlib.import_module("tests.e2e")
except BaseException as exc:
    error = type(exc).__name__ + ": " + str(exc)
path = os.environ.get("PYPOKER_CHECKPOINT_ROOT")
marker = os.environ.get("PYPOKER_BATTERY_ROOT")
cases = sorted(name for name in sys.modules if name.startswith("tests.e2e.") and ".test_" in name)
print(json.dumps({"path": path, "marker": marker, "exists": bool(path) and os.path.isdir(path), "package": getattr(package, "__name__", None), "file": getattr(package, "__file__", None), "cases": cases, "error": error}))
"""

#: The child that loads BOTH hooks in one interpreter, in the order a `pytest` session loads
#: them — the conftest first, then the e2e package init — so the composition is observable: one
#: root, the marker holding it, and the second hook declining to replace it (`layout.md` §5).
BOTH_CHILD = """\
import importlib, importlib.util, json, os, sys
sys.path.insert(0, %(repo)r)
spec = importlib.util.spec_from_file_location("conftest_probe", %(conftest)r)
module = importlib.util.module_from_spec(spec)
sys.modules["conftest_probe"] = module
spec.loader.exec_module(module)
first = os.environ.get("PYPOKER_CHECKPOINT_ROOT")
importlib.import_module("tests.e2e")
second = os.environ.get("PYPOKER_CHECKPOINT_ROOT")
print(json.dumps({"first": first, "second": second, "marker": os.environ.get("PYPOKER_BATTERY_ROOT"), "exists": bool(second) and os.path.isdir(second)}))
"""


def src_entries(paths):
    """The `sys.path` entries that are `<repo>/src`, matched by `os.path.realpath`.

    A relative entry — `PYTHONPATH=src` carries one, which the interpreter absolutises at
    startup — is resolved against `REPO_ROOT`, the directory the child runs in, and never
    against the caller's own cwd. Nothing is skipped silently: the count is the fact this
    battery asserts, so every entry stays visible to the message that asserts it (layout.md
    §5, module-map.md §5).
    """
    target = os.path.realpath(SRC_PATH)
    matched = []
    for entry in paths:
        if not isinstance(entry, str):
            continue
        candidate = entry if os.path.isabs(entry) else os.path.join(REPO_ROOT, entry)
        if os.path.realpath(candidate) == target:
            matched.append(entry)
    return matched


class SessionRootTest(unittest.TestCase):
    def environment(self):
        """The child's environment: the parent's, with the hostile inherited root set."""
        env = dict(os.environ)
        env[ROOT_VARIABLE] = HOSTILE_ROOT
        return env

    def environment_with(self, pythonpath):
        """`environment()` as one documented command line leaves it, `PYTHONPATH` included.

        `None` removes the variable, so the conftest acts on a bare interpreter; any other
        value is set verbatim — the documented line's `PYTHONPATH=src` is the literal
        relative `"src"`, which the child resolves against its `cwd` (`REPO_ROOT`). The
        hostile inherited root of `environment()` stays in both (layout.md §5).
        """
        env = self.environment()
        if pythonpath is None:
            env.pop("PYTHONPATH", None)
        else:
            env["PYTHONPATH"] = pythonpath
        return env

    def probe(self, env=None):
        """Run ONE child that loads `tests/conftest.py` as pytest does, and return its report.

        `env` defaults to `environment()`, the hostile shell HRN-9.1 and HRN-9.2 judge; a
        case that judges a documented environment passes its own (`layout.md` §5).
        """
        completed = subprocess.run(
            [sys.executable, "-c", CHILD % {"conftest": CONFTEST_PATH, "probe": IMPORT_PROBE}],
            cwd=REPO_ROOT,
            env=self.environment() if env is None else env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(
            completed.returncode,
            0,
            "a child interpreter must be able to load %r the way pytest loads a conftest, "
            "so the session write root can be read (layout.md §5, battery.md §2); it exited "
            "%r with stderr: %s"
            % (CONFTEST_PATH, completed.returncode, completed.stderr.strip()),
        )
        printed = [line for line in completed.stdout.splitlines() if line.strip()]
        self.assertTrue(
            printed,
            "the child prints one JSON line this battery reads (layout.md §5); it printed "
            "%r and stderr %r" % (completed.stdout, completed.stderr),
        )
        try:
            return json.loads(printed[-1])
        except ValueError as exc:
            self.fail(
                "the child's last non-empty stdout line must be the JSON report and not "
                "prose (layout.md §5): %r failed to parse (%s)"
                % (printed[-1], exc)
            )

    def test_hrn_9_1_the_override_is_unconditional_and_the_root_is_outside_the_repository(self):
        """HRN-9.1 with `PYPOKER_CHECKPOINT_ROOT` already set to `<repo>/checkpoints`, the child's value is an absolute `pypoker-battery-checkpoints-*` directory that exists and is not inside the repository — the override is unconditional (layout ¶5, write-root §3-§4, battery §2, ASM-18)."""
        report = self.probe()
        path = report["path"]
        self.assertIsNotNone(
            path,
            "loading tests/conftest.py sets %r before any case is collected, whatever the "
            "shell carries (layout.md §5, write-root.md §3-§4): it is still unset" % (ROOT_VARIABLE,),
        )
        self.assertIsInstance(
            path,
            str,
            "the variable names a filesystem path as text (layout.md §5, write-root.md §3): "
            "%r" % (path,),
        )
        self.assertNotEqual(
            path,
            HOSTILE_ROOT,
            "the override is unconditional: an inherited %r must not survive, or a battery "
            "writes into the shipped tree ASM-18 protects — the eighteen artefacts a reader "
            "keeps (layout.md §5, write-root.md §3-§4, battery.md §2, ASM-18): %r"
            % (ROOT_VARIABLE, path),
        )
        self.assertTrue(
            os.path.isabs(path),
            "the write root is an absolute path, so a battery writes under it wherever it "
            "is run from (layout.md §5, write-root.md §3): %r" % (path,),
        )
        self.assertTrue(
            os.path.basename(path).startswith(ROOT_PREFIX),
            "the directory is made with tempfile.mkdtemp(prefix=%r), so its basename "
            "starts with that prefix (layout.md §5): %r" % (ROOT_PREFIX, path),
        )
        self.assertTrue(
            report["exists"],
            "mkdtemp creates the directory at import, before a case is collected, so the "
            "child sees it as an existing directory (layout.md §5, battery.md §2): %r"
            % (path,),
        )
        resolved = os.path.realpath(path)
        repository = os.path.realpath(REPO_ROOT)
        shipped = os.path.realpath(HOSTILE_ROOT)
        self.assertFalse(
            resolved == repository or resolved.startswith(repository + os.sep),
            "the session write root is outside the repository, so a battery cannot write "
            "into a shipped tree (layout.md §5, write-root.md §3-§4, battery.md §2): %r is "
            "inside %r" % (resolved, repository),
        )
        self.assertFalse(
            resolved == shipped or resolved.startswith(shipped + os.sep),
            "and never under `<repo>/checkpoints`, the shipped tree ASM-18 protects — the "
            "eighteen artefacts a reader keeps (layout.md §5, write-root.md §3-§4, "
            "battery.md §2, ASM-18): %r is inside %r"
            % (resolved, shipped),
        )

    def test_hrn_9_2_the_directory_is_gone_once_the_session_s_process_exits(self):
        """HRN-9.2 the child's directory existed while it ran and is gone once that process has exited — `atexit` removes it with `shutil.rmtree(path, True)`, because a battery leaves the repository as it found it (layout §5, battery §2, ASM-18)."""
        report = self.probe()
        path = report["path"]
        self.assertIsNotNone(
            path,
            "the child reports the directory it made, so its removal is observable "
            "(layout.md §5): %r is still unset" % (ROOT_VARIABLE,),
        )
        self.assertTrue(
            report["exists"],
            "the directory exists inside the child, so the removal assertion is not "
            "vacuous: a path that never was a directory proves nothing about cleanup "
            "(layout.md §5, battery.md §2): %r" % (path,),
        )
        self.assertFalse(
            os.path.exists(path),
            "the directory that process created is removed when it exits, with atexit and "
            "shutil.rmtree(path, True), so a battery leaves the repository as it found it "
            "(layout.md §5, battery.md §2, ASM-18): %r still exists in the parent"
            % (path,),
        )

    def test_hrn_9_3_it_keeps_its_one_existing_job_and_imports_no_subsystem(self):
        """HRN-9.3 in both documented environments — `PYTHONPATH` removed, and `PYTHONPATH=src` — loading `tests/conftest.py` imports none of `engine`, `features`, `agents`, `evaluation`, `training` or `harness`, leaves the absolute `<repo>/src` on `sys.path` exactly once, and that entry imports `engine` by its bare name — it keeps its one existing job, it adds none, and the position is not its contract (layout §5, module-map §5, battery §2, D-13)."""
        for label, pythonpath in (
            ("`PYTHONPATH` removed", None),
            ("`PYTHONPATH=src`", "src"),
        ):
            with self.subTest(environment=label):
                report = self.probe(self.environment_with(pythonpath))
                self.assertEqual(
                    report["modules"],
                    [],
                    "under %s loading tests/conftest.py imports no subsystem and stands in "
                    "for no entry point: the package's import boundary is unchanged and the "
                    "conftest is not a harness by another route (docs/L3/harness/layout.md "
                    "§5, docs/L1/module-map.md §5, docs/L1/battery.md §2): the child had "
                    "%r loaded" % (label, report["modules"]),
                )
                paths = report["paths"]
                matched = src_entries(paths)
                self.assertEqual(
                    len(matched),
                    1,
                    "under %s the file still does its one existing job — the absolute "
                    "`<repo>/src` on `sys.path` exactly once — and no more (docs/L3/harness/"
                    "layout.md §5, docs/L1/module-map.md §5, docs/L1/battery.md §2). The "
                    "position is not asserted, and "
                    "neither is which statement performed the insert: with `PYTHONPATH=src` "
                    "the documented command line's spelling is absolutised at interpreter "
                    "startup, the conftest's membership guard then correctly declines a "
                    "duplicate insert, and the documents fix the outcome and not which "
                    "statement produced it. %d entries matched %r out of the target %r, in "
                    "the child's sys.path %r; an entry counts as `<repo>/src` when its "
                    "os.path.realpath equals that of %r, a relative entry being resolved "
                    "against %r"
                    % (label, len(matched), matched, SRC_PATH, paths, SRC_PATH, REPO_ROOT),
                )
                self.assertEqual(
                    report["imported"],
                    IMPORT_PROBE,
                    "under %s the `sys.path` entry is functional, not decorative: a battery "
                    "imports each of the six declared packages by its bare name, so %r must "
                    "import where the conftest has loaded (docs/L3/harness/layout.md §5, "
                    "docs/L1/module-map.md §5, docs/L1/battery.md §2): the child reported "
                    "%r with %r"
                    % (label, IMPORT_PROBE, report["imported"], report["error"]),
                )

    def child_report(self, program, replacements, env=None):
        """Run ONE child interpreter on `program`, and return the JSON line it printed.

        `program` is a child that loads the hook under judgement; `replacements` fills in the
        paths it needs. `env` defaults to `environment()`, the hostile shell every case here
        judges. The child's own report is the fact, so a failure names its reason instead of
        an opaque traceback (`docs/L3/harness/layout.md` §5).
        """
        completed = subprocess.run(
            [sys.executable, "-c", program % replacements],
            cwd=REPO_ROOT,
            env=self.environment() if env is None else env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(
            completed.returncode,
            0,
            "a child interpreter must be able to load the hook under judgement, so the write "
            "root it establishes can be read (layout.md §5, battery.md §2); it exited %r with "
            "stderr: %s" % (completed.returncode, completed.stderr.strip()),
        )
        printed = [line for line in completed.stdout.splitlines() if line.strip()]
        self.assertTrue(
            printed,
            "the child prints one JSON line this battery reads (layout.md §5); it printed "
            "%r and stderr %r" % (completed.stdout, completed.stderr),
        )
        try:
            return json.loads(printed[-1])
        except ValueError as exc:
            self.fail(
                "the child's last non-empty stdout line must be the JSON report and not "
                "prose (layout.md §5): %r failed to parse (%s)" % (printed[-1], exc)
            )

    def assert_outside_the_repository(self, path, hook, exists):
        """One absolute `pypoker-battery-checkpoints-*` directory that exists and is outside.

        The four facts HRN-9.1 states for the conftest, asserted for whichever hook is under
        judgement: absolute, the fixed prefix, existing, and outside both the repository and
        its shipped `checkpoints/` tree (`layout.md` §5, write-root.md §3-§4). `exists` is the
        child's own `os.path.isdir` fact, read inside the process that ran the hook: the
        directory is removed when that process exits (`layout.md` §5), so the parent cannot
        observe it there and must not pretend to — HRN-9.1 reads the same child-side fact.
        """
        self.assertIsInstance(
            path,
            str,
            "%s must set %r to a filesystem path as text (layout.md §5, write-root.md §3): %r"
            % (hook, ROOT_VARIABLE, path),
        )
        self.assertTrue(
            os.path.isabs(path),
            "%s publishes an absolute write root, so a battery writes under it wherever it is "
            "run from (layout.md §5, write-root.md §3): %r" % (hook, path),
        )
        self.assertTrue(
            os.path.basename(path).startswith(ROOT_PREFIX),
            "%s makes the directory with tempfile.mkdtemp(prefix=%r), so its basename starts "
            "with that prefix (layout.md §5): %r" % (hook, ROOT_PREFIX, path),
        )
        self.assertTrue(
            exists,
            "%s made the directory at import, before a case ran, so the child saw it as an "
            "existing directory while it was alive (layout.md §5, battery.md §2): %r is not "
            "there in the child" % (hook, path),
        )
        resolved = os.path.realpath(path)
        repository = os.path.realpath(REPO_ROOT)
        shipped = os.path.realpath(HOSTILE_ROOT)
        self.assertFalse(
            resolved == repository or resolved.startswith(repository + os.sep),
            "%s puts the write root outside the repository, so a battery cannot write into a "
            "shipped tree (layout.md §5, write-root.md §3-§4, battery.md §2): %r is inside %r"
            % (hook, resolved, repository),
        )
        self.assertFalse(
            resolved == shipped or resolved.startswith(shipped + os.sep),
            "%s must never put the write root under `<repo>/checkpoints`, the shipped tree "
            "ASM-18 protects — the eighteen artefacts a reader keeps (layout.md §5, "
            "write-root.md §3-§4, battery.md §2, ASM-18): %r is inside %r"
            % (hook, resolved, shipped),
        )

    def test_hrn_9_4_the_census_hook_establishes_the_root_before_any_case(self):
        """HRN-9.4 imported as `unittest discover -s tests/e2e -t .` imports it, and with `PYPOKER_CHECKPOINT_ROOT` inherited as `<repo>/checkpoints`, `tests/e2e/__init__.py` publishes an absolute `pypoker-battery-checkpoints-*` directory that exists, is outside the repository, is marked in `PYPOKER_BATTERY_ROOT`, precedes every case module, and is gone once the child exits — the census is safe without a conftest (layout §5, write-root §4, battery §2)."""
        report = self.child_report(E2E_CHILD, {"repo": REPO_ROOT})
        self.assertIsNone(
            report["error"],
            "the census imports tests/e2e before it imports a case module, so the package "
            "init must load on its own: it raised %r (layout.md §5, battery.md §2)"
            % (report["error"],),
        )
        self.assertEqual(
            report["package"],
            "tests.e2e",
            "the hook is reached as the package `unittest discover -s tests/e2e -t .` imports, "
            "and not as a file loaded beside it (layout.md §5): %r" % (report["package"],),
        )
        self.assertEqual(
            os.path.realpath(report["file"] or ""),
            os.path.realpath(E2E_INIT_PATH),
            "the package init under judgement is the file the census executes (layout.md §5): "
            "%r is not %r" % (report["file"], E2E_INIT_PATH),
        )
        self.assertEqual(
            report["cases"],
            [],
            "the hook runs before any case module is imported, which is what makes it a hook "
            "and not a case (layout.md §5, battery.md §2): the child already had %r loaded"
            % (report["cases"],),
        )
        path = report["path"]
        self.assertNotEqual(
            path,
            HOSTILE_ROOT,
            "the establishment is unconditional under the census too: an inherited %r must not "
            "survive, or the documented census writes into the shipped tree (layout.md §5, "
            "write-root.md §3-§4, battery.md §2)" % (ROOT_VARIABLE,),
        )
        self.assert_outside_the_repository(path, "tests/e2e/__init__.py", report["exists"])
        self.assertEqual(
            report["marker"],
            path,
            "the hook that makes the root records it in %r, so the other hook of a process "
            "that loads both can decline (layout.md §5): %r against %r"
            % (MARKER_VARIABLE, report["marker"], path),
        )
        self.assertFalse(
            os.path.exists(path),
            "the directory the child created is removed when it exits, with atexit and "
            "shutil.rmtree(path, True), so the census leaves the repository as it found it "
            "(layout.md §5, battery.md §2): %r still exists in the parent" % (path,),
        )

    def test_hrn_9_5_the_two_hooks_compose_into_one_root_and_the_marker_is_battery_only(self):
        """HRN-9.5 loading `tests/conftest.py` and then `tests/e2e/__init__.py` in one child — the order a pytest session loads them — leaves exactly one root, the second hook does not replace the first, the marker names that one root and is removed with it, and no file under `src/` reads the marker: one name points a run (layout §5, write-root §3-§4, D-13)."""
        report = self.child_report(
            BOTH_CHILD, {"repo": REPO_ROOT, "conftest": CONFTEST_PATH}
        )
        first = report["first"]
        second = report["second"]
        self.assertIsNotNone(
            first,
            "the first hook establishes the root, whatever the shell carries (layout.md §5, "
            "write-root.md §3-§4): %r is still unset" % (ROOT_VARIABLE,),
        )
        self.assertEqual(
            second,
            first,
            "a process that loads both hooks ends with ONE root: the second finds the marker "
            "equal to the current override and declines, and a second mkdtemp here would leak "
            "a directory and split a run's writes across two trees (layout.md §5, "
            "write-root.md §4): the first root was %r and the second hook left %r"
            % (first, second),
        )
        self.assertNotEqual(
            second,
            HOSTILE_ROOT,
            "the one root is the private one and not the inherited shipped tree (layout.md "
            "§5, write-root.md §3-§4): %r" % (second,),
        )
        self.assert_outside_the_repository(second, "the two hooks together", report["exists"])
        self.assertEqual(
            report["marker"],
            second,
            "the marker names the one root the composition settled on, which is what the "
            "second hook compares against (layout.md §5): %r against %r"
            % (report["marker"], second),
        )
        self.assertFalse(
            os.path.exists(second),
            "the one root is removed when the process exits, once, so a process that loads "
            "both hooks leaves nothing behind (layout.md §5, battery.md §2): %r still "
            "exists in the parent" % (second,),
        )
        self.assertTrue(
            os.path.isdir(SRC_PATH),
            "`src/` is where the six packages live, so the marker scan below is not vacuous "
            "(module-map.md §5): %r is not a directory" % (SRC_PATH,),
        )
        offenders = []
        for root, _directories, files in os.walk(SRC_PATH):
            for name in sorted(files):
                if not name.endswith(".py"):
                    continue
                candidate = os.path.join(root, name)
                with open(candidate, encoding="utf-8") as handle:
                    if MARKER_VARIABLE in handle.read():
                        offenders.append(os.path.relpath(candidate, REPO_ROOT))
        self.assertEqual(
            offenders,
            [],
            "the marker is the battery's own and no file under `src/` reads it: %r is the one "
            "ambient override a run is pointed by, and a second name in the packages would be "
            "the second mechanism write-root.md §3 forbids (layout.md §5, D-13): %r carries "
            "it" % (ROOT_VARIABLE, offenders),
        )


if __name__ == "__main__":
    unittest.main()
