"""The e2e battery's package init: the write root the `unittest` census has no conftest for.

``pytest`` loads ``tests/conftest.py`` for every battery; ``unittest`` loads no conftest at
all, and ``unittest discover -s tests/e2e -t .`` imports this start directory as the package
``tests.e2e`` before it imports a case module — so this file is the second hook that
establishes a battery's write root (`docs/L1/battery.md` §2, `docs/L3/harness/layout.md` §5).

It publishes ``PYPOKER_CHECKPOINT_ROOT`` — the one ambient override `training.layout` reads on
every call (`docs/L2/training/write-root.md` §3) — to a private
``tempfile.mkdtemp(prefix="pypoker-battery-checkpoints-")`` outside the repository, removed at
exit with ``atexit`` and ``shutil.rmtree(path, True)``, because a battery leaves the repository
as it found it.

The establishment is **unconditional**: a value inherited from a developer's shell, the
shipped ``<repo>/checkpoints`` included, is replaced. It is **idempotent with the conftest's**:
the hook that makes the root records it in ``PYPOKER_BATTERY_ROOT`` — a marker no file under
``src/`` reads — and a hook that finds that marker equal to the current override declines, so a
process that loads both (as a `pytest` run does) ends with one root and not two.

It imports no subsystem and stands in for no entry point: the battery is complete on its own
(`docs/L1/battery.md` §2).
"""

import atexit
import os
import shutil
import tempfile

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
