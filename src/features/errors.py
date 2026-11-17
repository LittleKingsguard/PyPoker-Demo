"""The refusals `features` raises (docs/L3/features/errors.md §2).

The classes live below an entry point and are never module-level names of the
package: a caller catches `FeaturesError` to know "this module refused me", and the
unit battery asserts the message, never a class (errors.md §2).  The error is the
only reporting channel -- no entry point swaps in a default, swallows an error or
returns part of a record (surface.md §1).
"""


class FeaturesError(Exception):
    """The base of every refusal this module raises."""


class UnknownEncoding(FeaturesError):
    """`build_encoder`: a name that is not a declared encoding."""


class UnknownShape(FeaturesError):
    """`build_encoder`/`action_space`/`decode_action`: a shape name outside the catalogue."""


class UnknownSource(FeaturesError):
    """`load_strength`: a source name outside the declared table, or an artefact the table
    names and the tree does not carry (`ASM-51`)."""


class InvalidModel(FeaturesError):
    """`load_strength`/`strength`/`stated`/`card_rows`: not a frozen model this module
    built, or an artefact whose state dict is not the declared layout row (`ASM-51`)."""


class UnknownStrength(FeaturesError):
    """`build_encoder`: a strength member outside the two the axis declares.

    The member is never defaulted onto `none` and never mapped onto `supervised`: an
    uncatalogued value is refused naming it and both members, exactly as an encoding or a
    shape name is (`errors.md` §2, `ASM-46`).
    """


class UnknownFact(FeaturesError):
    """`build_encoder`: an injected fact outside the four the declaration may append.

    The keyword's absence is the absence of a block and is not an empty declaration; a name
    outside the four, a duplicate and a value that is not a sequence are refused naming what
    was written, exactly as an encoding or a shape name is (`errors.md` §2,
    `strength-design.md` §A.5).
    """


class ConflictingFacts(FeaturesError):
    """`build_encoder`: a named strength member the declared `facts` leave out.

    The member appends the strength block, so a declaration that names the member and omits
    the fact would carry a declaration its caller wrote and its block table dropped; the two
    spellings are refused rather than reconciled (`errors.md` §3, `ASM-46`).
    """


class InvalidEncoder(FeaturesError):
    """`observation_spec`/`encode`: a value that is not an encoder this module built."""


class InvalidReadout(FeaturesError):
    """`encode`: not a mapping, a missing carried field, or a value with no spelling.

    `build_encoder`/`observation_spec`: a shape row carrying no denominator for a magnitude
    block, refused while its declaration is built (normalisers.md §2, errors.md §2, D-61).
    """


class InvalidActionList(FeaturesError):
    """`legal_indices`: not a sequence of descriptors, or an empty one."""


class UnknownAction(FeaturesError):
    """`legal_indices`: a descriptor outside the declared vocabulary."""


class InvalidActionIndex(FeaturesError):
    """`decode_action`: not an index, or an index outside the shape's vocabulary."""
