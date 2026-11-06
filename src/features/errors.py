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


class InvalidEncoder(FeaturesError):
    """`observation_spec`/`encode`: a value that is not an encoder this module built."""


class InvalidReadout(FeaturesError):
    """`encode`: not a mapping, a missing carried field, or a value with no spelling."""


class InvalidActionList(FeaturesError):
    """`legal_indices`: not a sequence of descriptors, or an empty one."""


class UnknownAction(FeaturesError):
    """`legal_indices`: a descriptor outside the three-index vocabulary."""


class InvalidActionIndex(FeaturesError):
    """`decode_action`: not an index, or an index outside {0, 1, 2}."""
