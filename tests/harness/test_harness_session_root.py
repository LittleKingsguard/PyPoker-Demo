"""HRN-9 — the battery's session write root is private, and `tests/conftest.py` is harness-owned.

Drives `docs/L3/harness/layout.md` §5, `docs/L2/training/write-root.md` §3-§4 and
`docs/L1/battery.md` §2, and closes `strata/records/phase1-walkthrough.md` finding 5, where the
documented batteries left `seed-4103`, `seed-8807`, `R2/` and `R4/` in the shipped `checkpoints/`
tree: the one file every battery's pytest invocation executes sets `PYPOKER_CHECKPOINT_ROOT` to a
private `tempfile.mkdtemp(prefix="pypoker-battery-checkpoints-")` at import, **unconditionally**,
so a value inherited from a developer's shell cannot send a battery's writes into
`<repo>/checkpoints`; the directory is removed when the process that created it exits. It keeps
its one existing job — `<repo>/src` on `sys.path` once — and imports no subsystem, so the load
itself is invisible to the five packages and to `harness` (layout.md §5, module-map.md §5, D-13).

Each case runs ONE child interpreter with an explicit environment in which the inherited root is
the shipped tree — a hostile developer shell — loads `tests/conftest.py` the way pytest does
(importlib), and reads one JSON line it prints. HRN-9.3 runs one child per documented environment
under judgement — `PYTHONPATH` removed, and `PYTHONPATH=src` as the documented command line spells
it — so its verdict is the same whichever way the battery itself is invoked. The parent imports no
subsystem and no pytest: these cases judge the conftest, not the package (`battery.md` §2, D-13).
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
#: `layout.md` §5 fixes, and not a position (`module-map.md` §5, finding 5).
SRC_PATH = os.path.join(REPO_ROOT, "src")

#: The one package the child imports by its bare name to show the `sys.path` entry is
#: functional: `engine` is the foundation the other four import and pulls in `pokerkit` only,
#: so the probe is cheap and stable (`module-map.md` §3, D-13).
IMPORT_PROBE = "engine"

#: The child: load the conftest the way pytest does (importlib, never `runpy`), snapshot
#: `sys.path` and the six packages straight after the load, then import one of the six by its
#: bare name — and report all of it on one JSON line, so a failure names its reason instead of
#: an opaque traceback (layout.md §5, module-map.md §5, finding 5).
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
        """HRN-9.1 with `PYPOKER_CHECKPOINT_ROOT` already set to `<repo>/checkpoints`, the child's value is an absolute `pypoker-battery-checkpoints-*` directory that exists and is not inside the repository — the override is unconditional (layout ¶5, write-root §3-§4, battery §2, finding 5)."""
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
            "writes into the shipped tree the walkthrough found dirty (layout.md §5, "
            "write-root.md §3-§4, battery.md §2, finding 5): %r"
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
            "and never under `<repo>/checkpoints`, the tree the walkthrough found dirty "
            "(layout.md §5, write-root.md §3-§4, battery.md §2, finding 5): %r is inside %r"
            % (resolved, shipped),
        )

    def test_hrn_9_2_the_directory_is_gone_once_the_session_s_process_exits(self):
        """HRN-9.2 the child's directory existed while it ran and is gone once that process has exited — `atexit` removes it with `shutil.rmtree(path, True)`, because a battery leaves the repository as it found it (layout §5, battery §2, finding 5)."""
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
            "(layout.md §5, battery.md §2, finding 5): %r still exists in the parent"
            % (path,),
        )

    def test_hrn_9_3_it_keeps_its_one_existing_job_and_imports_no_subsystem(self):
        """HRN-9.3 in both documented environments — `PYTHONPATH` removed, and `PYTHONPATH=src` — loading `tests/conftest.py` imports none of `engine`, `features`, `agents`, `evaluation`, `training` or `harness`, leaves the absolute `<repo>/src` on `sys.path` exactly once, and that entry imports `engine` by its bare name — it keeps its one existing job, it adds none, and the position is not its contract (layout §5, module-map §5, D-13, finding 5)."""
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
                    "§5, docs/L1/module-map.md §5, strata/records/phase1-walkthrough.md "
                    "finding 5): the child had %r loaded" % (label, report["modules"]),
                )
                paths = report["paths"]
                matched = src_entries(paths)
                self.assertEqual(
                    len(matched),
                    1,
                    "under %s the file still does its one existing job — the absolute "
                    "`<repo>/src` on `sys.path` exactly once — and no more (docs/L3/harness/"
                    "layout.md §5, docs/L1/module-map.md §5, strata/records/"
                    "phase1-walkthrough.md finding 5). The position is not asserted, and "
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
                    "docs/L1/module-map.md §5, strata/records/phase1-walkthrough.md finding "
                    "5): the child reported %r with %r"
                    % (label, IMPORT_PROBE, report["imported"], report["error"]),
                )


if __name__ == "__main__":
    unittest.main()
