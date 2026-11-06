"""training — the rung registry and the one training loop every rung configures (D-3, D-16).

The six module-level names below are the whole surface of this package:

    rungs()                                   the six rung declarations, in brief §2's order
    rung(name)                                one resolved configuration, or a named refusal
    run(rung, seeds=None, budget=None, device=None)   records.md §12's run record
    fairness(left, right)                     what a comparison pair holds constant, and its axis
    devices()                                 what this platform offers, and the default
    checkpoints()                             the shipped checkpoint index

Nothing below an entry point is contract (e2e-surface.md §1); the private names the unit
battery imports are listed in docs/L3/training/README.md §4 and no caller outside
tests/training/ may use them.
"""

from .devices import devices
from .fairness import fairness
from .index import checkpoints
from .loop import run
from .registry import rung, rungs

__all__ = ["rungs", "rung", "run", "fairness", "devices", "checkpoints"]
