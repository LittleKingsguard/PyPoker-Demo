"""training's refusals (docs/L3/training/errors.md).

One base class and one subclass per refusal family, because a caller routes on the
contract that was violated and never on a message it has to parse (`e2e-surface.md` §2).
Every message names the offending value: no entry point coerces a value, substitutes a
default it did not declare, or repairs a declaration it was handed. A refusal raised by
`features`, `agents` or `evaluation` propagates unchanged in its owner's class, because a
refusal re-wrapped here would hide which module owns the contract (`module-map.md` §2).
"""


class TrainingError(Exception):
    """Base class of every refusal this module raises."""


class UnknownRung(TrainingError):
    """`rung`: the name is not one the registry carries (ladder.md §3)."""


class ConfigurationInvalid(TrainingError):
    """`run`: not a mapping, or `variants` / `pool` / `name` is the wrong thing."""


class MissingConfigurationKey(TrainingError):
    """`run`: a configuration missing a key the run reads — the key is named."""


class VariantCountInvalid(TrainingError):
    """`run`: a variant count other than one or two (ladder.md §2, ASM-9)."""


class VariantSettingInvalid(TrainingError):
    """`run`: a setting the run reads is not a positive integer, a string or in [0, 1]."""


class InvalidSeeds(TrainingError):
    """`run`: the seed set is empty, repeats a seed, or holds a non-integer (ASM-2)."""


class InvalidBudget(TrainingError):
    """`run`: the budget is not a positive integer, or is below ten hands (ASM-18)."""


class UnknownDevice(TrainingError):
    """`run`: a device `devices()` does not list (D-8)."""


class NotAComparisonSide(TrainingError):
    """`fairness`: a side is neither a configuration nor a variant entry."""


class SideKindMismatch(TrainingError):
    """`fairness`: one side is a configuration and the other a variant entry."""


class ComparisonKeyMissing(TrainingError):
    """`fairness`: a key the comparison reads is absent — the key is named."""


class MultipleAxes(TrainingError):
    """`fairness`: the differences fall in more than one axis — every axis is named."""


class PoolIdsDiffer(TrainingError):
    """`fairness`: two variants of one configuration declare two pool ids (ASM-16)."""


class IgnoredDeclaration(TrainingError):
    """`run`: a declared `learning_rule`, `hyper` key or `snapshot_every` the run would not use (ASM-7, ASM-18)."""


class PairDeclarationsDiffer(TrainingError):
    """`run` / `fairness`: two arms of a pair declare two values for one setting they share."""
