"""pytest plumbing for the module batteries, owned by the `harness` module.

The six declared packages live in ``src/`` and are imported by their bare names
(``engine``, ``features``, ``agents``, ``evaluation``, ``training``, ``harness``), so
``src/`` goes on ``sys.path`` once per session — the same plumbing each battery's own
support module performs for the other runners (`docs/L1/module-map.md` §5,
`docs/L3/harness/layout.md` §5).

It also sets the session write root, ``PYPOKER_CHECKPOINT_ROOT`` — the one ambient override
`docs/L2/training/write-root.md` §3-§4 gives a single command line — to a private
``tempfile.mkdtemp(prefix="pypoker-battery-checkpoints-")`` **unconditionally**, so a value
inherited from a developer's shell cannot send a battery's writes into ``<repo>/checkpoints``;
the directory is removed with ``atexit`` and ``shutil.rmtree(path, True)`` when the process
exits, because a battery leaves the repository as it found it (`docs/L3/harness/layout.md` §5).

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

_WRITE_ROOT = tempfile.mkdtemp(prefix="pypoker-battery-checkpoints-")
os.environ["PYPOKER_CHECKPOINT_ROOT"] = _WRITE_ROOT
atexit.register(shutil.rmtree, _WRITE_ROOT, True)
