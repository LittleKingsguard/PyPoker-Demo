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
    """`run`: a declared `learning_rule` or `utility` the catalogue does not carry, a `hyper` key, or a `snapshot_every` the run would not use (ASM-7, ASM-18, D-19, D-20)."""


class ChipConservationBroken(TrainingError):
    """`run`: one hand's chips in play disagree with the stacks the game declares, so the
    utility's normaliser would not be the game's own (ASM-6, `utilities.md` §4, D-20)."""


class PairDeclarationsDiffer(TrainingError):
    """`run` / `fairness`: two arms of a pair declare two values for one setting they share."""


class UnknownShape(TrainingError):
    """`run` / `fairness`: a `game` naming a shape the catalogue does not declare, or a
    value that is not a shape name at all — the name and the declared names are named,
    and no name is ever defaulted (shapes.md §2–§3, D-29, D-13)."""


class GreedyPassRefused(TrainingError):
    """`run`: one variant's greedy pass at one seed would exceed its hand or decision
    bound, so it is refused with both counts and never truncated (`sizing.md` §4,
    `records.md` §15, ASM-38)."""
