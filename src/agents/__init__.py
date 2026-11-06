"""`agents` -- everything that chooses or learns an action (`docs/L3/agents/README.md`).

Exactly the ten entry points of `docs/L1/e2e-surface.md` §3.3, in that order, and no
eleventh name (D-12, `surface.md` §1): `learners`, `build_learner`, `param_count`,
`act`, `learn`, `save`, `load`, `as_policy`, `baselines`, `build_baseline`.
`Learner`, the error classes, the kind table, the hyper-declarations and every helper
below an entry point are not surface.

`import agents` imports `numpy`, the standard library and the five granted `features`
calls — never `torch`, which lives inside `torch_backend.py` and is imported on the
first torch learner's build, and never `pokerkit`, which `engine` holds at module level
and which only the oracle's policy imports (`README.md` §6, `backends.md` §4).
"""

from __future__ import annotations

from . import declarations as _declarations
from .baselines import baselines, build_baseline
from .checkpoint import load, save
from .learner import act, build_learner, learn, param_count
from .policy import as_policy

__all__ = (
    "learners",
    "build_learner",
    "param_count",
    "act",
    "learn",
    "save",
    "load",
    "as_policy",
    "baselines",
    "build_baseline",
)


def learners():
    """The declared backends, the seven kinds, the one rule and its six declarations.

    Plain data, rebuilt on every call: `backends` keyed `numpy` then `torch`,
    `architectures` keyed by the seven kind names in `architecture.md` §1's order,
    `learning_rule` the one `str`, `hyper` the rule's six fixed values (`surface.md` §3).
    """
    return _declarations.catalogue()
