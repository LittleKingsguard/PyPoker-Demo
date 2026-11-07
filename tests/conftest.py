"""pytest plumbing for the module batteries, owned by the `harness` module.

The six declared packages live in ``src/`` and are imported by their bare names
(``engine``, ``features``, ``agents``, ``evaluation``, ``training``, ``harness``), so
``src/`` goes on ``sys.path`` once per session — the same plumbing each battery's own
support module performs for the other runners (`docs/L1/module-map.md` §5,
`docs/L3/harness/layout.md` §5).

It also establishes the battery write root, and it is the `pytest` half of the two hooks
`docs/L3/harness/layout.md` §5 fixes — the `unittest` half is ``tests/e2e/__init__.py``,
because `unittest` loads no conftest at all and imports that package before a case module.
``PYPOKER_CHECKPOINT_ROOT`` — the one ambient override `docs/L2/training/write-root.md`
§3-§4 gives a single command line — is pointed at a private
``tempfile.mkdtemp(prefix="pypoker-battery-checkpoints-")`` **unconditionally**, so a value
inherited from a developer's shell cannot send a battery's writes into ``<repo>/checkpoints``;
the directory is removed with ``atexit`` and ``shutil.rmtree(path, True)`` when the process
exits, because a battery leaves the repository as it found it.

The establishment is **idempotent across the two hooks**: the hook that makes the root records
it in ``PYPOKER_BATTERY_ROOT`` — a marker no file under ``src/`` reads — and a hook that finds
that marker equal to the current override declines, so a process that loads both ends with one
root. ``PYPOKER_CHECKPOINT_ROOT`` stays the only name that points a run.

Nothing here imports a subsystem, stands in for one, configures a case, or skips one: a
battery is complete on its own and stays collectable without this file
(`docs/L1/battery.md` §2).
"""

import atexit
import os
import shutil
import sys
import tempfile

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

#: The one ambient override `write-root.md` §3 names, and the battery-only marker
#: `layout.md` §5 adds beside it: the marker names the root a hook already made, so the
#: second hook of a process that loads both declines instead of making a second one.
_ROOT = "PYPOKER_CHECKPOINT_ROOT"
_MARKER = "PYPOKER_BATTERY_ROOT"

_marked = os.environ.get(_MARKER)
if not (_marked and _marked == os.environ.get(_ROOT)):
    _WRITE_ROOT = tempfile.mkdtemp(prefix="pypoker-battery-checkpoints-")
    os.environ[_MARKER] = _WRITE_ROOT
    os.environ[_ROOT] = _WRITE_ROOT
    atexit.register(shutil.rmtree, _WRITE_ROOT, True)
