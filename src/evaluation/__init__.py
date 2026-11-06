"""`evaluation` -- the league: the pool, the scheduler, the matrix, the rating, the report.

The eleven entry points of `docs/L1/e2e-surface.md` §3.4, in that order, and nothing
else: `protocol`, `league`, `build_pool`, `pool_members`, `offer`, `opponent`, `match`,
`matrix`, `rating`, `policy_from`, `report` (`docs/L3/evaluation/README.md` §3, D-12).

A pool and a policy are opaque values a caller only passes back; every other returned
value is plain data.  This package never trains, never edits a curve, never chooses a
pool's membership and never seeds Python's global `random` stream: the one seeding point
is `engine.new_hand` (ASM-2, `module-map.md` §3, D-16).

The layout is `docs/L3/evaluation/README.md` §4: `declarations.py` (the two declarations
and the league's constants), `seeds.py` (the five derivations), `pool.py`, `policy.py`,
`scheduler.py`, `matrix.py`, `rating.py`, `report.py`, `tables.py` (the shipped artefact's
producer) and `errors.py` (the refusal hierarchy).
"""

from .declarations import league, protocol
from .matrix import matrix
from .policy import opponent, policy_from
from .pool import build_pool, offer, pool_members
from .rating import rating
from .report import report
from .scheduler import match

__all__ = (
    "protocol",
    "league",
    "build_pool",
    "pool_members",
    "offer",
    "opponent",
    "match",
    "matrix",
    "rating",
    "policy_from",
    "report",
)
