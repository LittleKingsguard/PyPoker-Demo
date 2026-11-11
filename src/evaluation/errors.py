"""The refusals of the `evaluation` module (`docs/L3/evaluation/errors.md` §2).

One `EvaluationError` base and forty-five subclasses, one per refusal family the L2
surface declares (`docs/L2/evaluation/surface.md` §5-§13, `§14`).  A caller catches
`EvaluationError` to know that *this* module refused it, so a mistyped record key or a
`TypeError` from a helper never masquerades as a refusal (`errors.md` §1).

Every message follows §3's grammar -- ``"<entry>(<argument or field>): <the violated
contract>, got <what was passed>"`` -- and the canonical spellings are §4's.  These
names are contract for `tests/evaluation/` (`README.md` §4) and are *not* module-level
names of the package (`e2e-surface.md` §1, D-12).
"""


class EvaluationError(Exception):
    """Base of every refusal this module makes (`errors.md` §2)."""


class InvalidPool(EvaluationError):
    """`pool_members`, `offer`, `opponent`, `matrix`: not a pool this module built."""


class PoolDeclarationInvalid(EvaluationError):
    """`build_pool`: not a mapping, or missing `members` / `m` / `frozen`."""


class PoolBoundInvalid(EvaluationError):
    """`build_pool`: `m` not a positive integer, a bool, or above the league's M."""


class MemberInvalid(EvaluationError):
    """A member or a side is not the record it must be; a bad id or lineage."""


class MemberUnloadable(EvaluationError):
    """A member or version carries no `path`, or its path is not readable."""


class MemberDuplicate(EvaluationError):
    """Two records carry one id, or an offered version is already a member."""


class LineageConflict(EvaluationError):
    """Two members descend from one (`surface.md` §5)."""


class LineageCycle(EvaluationError):
    """A chain reaches no start (`surface.md` §5)."""


class PoolFrozen(EvaluationError):
    """`offer` into a frozen pool."""


class LineageNotExtended(EvaluationError):
    """`offer`: the lineage is not the newest member of the family it names."""


class UnknownRule(EvaluationError):
    """A member's `rule` is not one of the catalogue's members (`rules.md` §4, D-19)."""


class UnknownUtility(EvaluationError):
    """A member's `utility` is not one of the catalogue's members (`utilities.md` §5,
    D-20)."""


class UnknownBaseline(EvaluationError):
    """A pool declaration's `baselines` names a baseline the catalogue does not carry
    (`records.md` §8, `agents/surface.md` §11, ASM-32, D-21)."""


class UnknownShape(EvaluationError):
    """A shape name the restated catalogue does not carry — a pool declaration's `game`, a
    member record's, an offered version's, a container's or a variant's (`shape.md` §3,
    D-29)."""


class RuleMismatch(EvaluationError):
    """Two declarations of one rule disagree: a member's record against its checkpoint's,
    or a version's `rule` against the rule of the family it extends (`records.md` §7,
    ASM-26, D-19)."""


class UtilityMismatch(EvaluationError):
    """Two declarations of one utility disagree: a member's record against its
    checkpoint's, or a version's `utility` against the family it extends
    (`records.md` §7, `utilities.md` §6, ASM-26, D-20)."""


class ShapeMismatch(EvaluationError):
    """Two declarations of one shape disagree: a member's record against its pool's or its
    container's, an offered version's against its pool's, a cell's two sides, a matrix's
    variant against its pool, a matrix's cells against each other or against its own
    `game`, and a report's run, pool and matrix (`shape.md` §3, §4, D-29)."""


class FamilyBoundExceeded(EvaluationError):
    """A declaration or an offer holds more families than the window's bound allows
    (`docs/L1/league.md` §2, ASM-26)."""


class PoolNotFrozen(EvaluationError):
    """`matrix`: the pool may still change while it is tabled."""


class InvalidSeed(EvaluationError):
    """`opponent`, `match`: the seed is not an integer."""


class InvalidDrawCount(EvaluationError):
    """`opponent`: the optional draw count is not a positive integer (`seats.md` §4, ASM-43)."""


class DrawExceedsMembership(EvaluationError):
    """`opponent`: the draw asks for more distinct members than the pool holds, and a draw is
    without replacement (`seats.md` §4, `records.md` §8, ASM-43)."""


class SeatCountExceeded(EvaluationError):
    """`match`, `matrix`, `rating`, `report`: the shape has more seats than a pair has, and a
    cell is a pair (`seats.md` §5, `league.md` §4, D-33)."""


class InvalidHandCount(EvaluationError):
    """`match`: the hand count is not a positive integer."""


class SameMemberPair(EvaluationError):
    """`match`: the two sides carry one id."""


class VariantCountInvalid(EvaluationError):
    """`matrix`: not one and not two variants."""


class VariantInvalid(EvaluationError):
    """`matrix`: a variant is not a policy."""


class UnknownTable(EvaluationError):
    """`matrix`: the label is not `live` or `full`."""


class InvalidMembership(EvaluationError):
    """`league()`'s `cell_count`: not an int of at least 2, a sequence or a members mapping."""


class InvalidMatrix(EvaluationError):
    """`rating`: the argument is not a matrix record."""


class MissingMatrixKey(EvaluationError):
    """`rating`: a required matrix key is absent -- the key is named."""


class CellCountMismatch(EvaluationError):
    """`rating`, `report`: the cell count is not K(K-1)/2."""


class DuplicatePair(EvaluationError):
    """`rating`, `report`: one unordered pair appears in two cells."""


class ForeignMember(EvaluationError):
    """`rating`, `report`: a cell names a member the membership does not hold."""


class UnevenCell(EvaluationError):
    """`rating`, `report`: a cell's hands differ from `hands_per_cell`."""


class MissingBaseline(EvaluationError):
    """`rating`, `report`: the three-baseline anchor is incomplete."""


class CheckpointUnreadable(EvaluationError):
    """`policy_from`, a member's path: no readable file, or no readable zip."""


class CheckpointRecordMissing(EvaluationError):
    """The container records no seed or encoding name, or not in a form this module reads."""


class UnknownEncoding(EvaluationError):
    """A checkpoint: `features.build_encoder` refuses the recorded name, or `as_policy` refuses the encoder it builds."""


class UnknownExploration(EvaluationError):
    """`policy_from`'s mode is neither `schedule` nor `off` (`shape.md` §5, `sizing.md` §4,
    D-29)."""


class MissingFamily(EvaluationError):
    """`report`: an absent evidence family -- named as `protocol()` spells it."""


class MembershipMismatch(EvaluationError):
    """`report`: the matrix's membership is not the pool's plus the variants."""


class RatingMismatch(EvaluationError):
    """`report`: the rating does not name exactly the matrix's members."""


class HeaderIncomplete(EvaluationError):
    """`report`: a header item is missing -- the item is named."""


class InvalidArgument(EvaluationError):
    """Any: an argument of the wrong type -- a record that is not a mapping, a rung name that is not a str."""
