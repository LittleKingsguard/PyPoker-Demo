"""pytest plumbing for the module batteries, owned by the `harness` module.

The six declared packages live in ``src/`` and are imported by their bare names
(``engine``, ``features``, ``agents``, ``evaluation``, ``training``, ``harness``), so
``src/`` goes on ``sys.path`` once per session — the same plumbing each battery's own
support module performs for the other runners (`docs/L1/battery.md` §2,
`docs/L1/module-map.md` §5).

Nothing here imports a subsystem, stands in for one, configures a case, or skips one: a
battery is complete on its own and stays collectable without this file
(`docs/L1/battery.md` §2).
"""

import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
