"""The shape's action vocabulary (vocabulary.md).

The vocabulary is the **shape's** and is held constant across the whole ladder: the
fixed-limit shape declares three indices and the no-cap shape six, in that shape's own
declared index order, and never an amount (D-29, sizing.md §3).  The descriptor spelling
is the one `engine.apply_action` accepts, restated here instead of imported -- this
module imports no other project module (layout.md §3, guardrails.md G12).

One table, `declarations.SHAPE_ROWS`, is the whole of this document's data: it carries
each shape's descriptors in that shape's index order, and `action_space`, `legal_indices`
and `decode_action` are three readings of it (declarations.py, shapes.md §2).
"""

from __future__ import annotations

from collections.abc import Sequence
from numbers import Integral

from .declarations import _RESOLUTIONS, shape_row, shape_rows
from .errors import InvalidActionIndex, InvalidActionList, UnknownAction


def _descriptor_index():
    """Every declared descriptor's index, read off the shape that declares it.

    A descriptor's index is its position in its shape's vocabulary, and the two declared
    vocabularies share their first two entries, so one table is total over every
    descriptor a decision can carry: `legal_indices` is given descriptors and no shape,
    and it must still be position-aligned for whichever shape's vocabulary they came
    from (shapes.md §3).  A descriptor whose index moved between shapes is a design
    defect, so it is refused here rather than read as one index at two positions.
    """
    index_of = {}
    for row in shape_rows(entry_point="legal_indices"):
        for position, descriptor in enumerate(row["actions"]):
            declared = index_of.setdefault(descriptor, position)
            if declared != position:
                raise AssertionError(
                    "%r is index %d on one declared shape and %d on another, and one "
                    "descriptor is one index (vocabulary.md §3)"
                    % (descriptor, declared, position)
                )
    return index_of


#: Descriptor -> index, over every declared shape's vocabulary (vocabulary.md §1).
DESCRIPTOR_INDEX = _descriptor_index()


def declared_descriptors():
    """Every declared descriptor, in the catalogue's order, each named once."""
    names = []
    for row in shape_rows(entry_point="legal_indices"):
        for descriptor in row["actions"]:
            if descriptor not in names:
                names.append(descriptor)
    return tuple(names)


def action_space(shape=None):
    """One shape's vocabulary, rebuilt fresh on every call (surface.md §7).

    The keys are the shape's indices: 0, 1 and 2 on the fixed-limit shape, 0 to 5 on the
    no-cap one, in the shape's **declared** order -- for `no-limit-100` that order is
    deliberately not monotone in amount, so no reader and no test can read an index as a
    size (sizing.md §3).  A raise descriptor's record adds the resolution it denotes,
    as prose: no string in the record contains a digit (guardrails.md G6).
    """
    row = shape_row(shape, "action_space")
    space = {}
    for index, name in enumerate(row["actions"]):
        record = {"name": name}
        resolution = _RESOLUTIONS.get(name)
        if resolution is not None:
            key, prose = resolution
            record[key] = prose
        space[index] = record
    return space


def legal_indices(legal_actions):
    """One index per descriptor, position-aligned and never sorted (surface.md §8).

    The i-th index is the shape's index of the i-th descriptor, so an argument out of the
    engine's order yields its indices in that same order -- the alignment is contract,
    and this function never sorts, de-duplicates or decides legality (vocabulary.md §3,
    guardrails.md G7).  It is given no shape, and needs none: a decision's legal set is
    one shape's vocabulary and every descriptor carries its own index (shapes.md §3).
    """
    if isinstance(legal_actions, (str, bytes)) or not isinstance(legal_actions, Sequence):
        raise InvalidActionList(
            "legal_indices(legal_actions): the argument must be a non-empty sequence of "
            "action descriptors, got %r" % (legal_actions,)
        )
    if not legal_actions:
        raise InvalidActionList(
            "legal_indices(legal_actions): a decision has at least one legal action, "
            "got %r" % (legal_actions,)
        )
    indices = []
    for descriptor in legal_actions:
        # Gated on `str` first: a foreign type that defines its own equality protocol
        # must not talk its way into the vocabulary (vocabulary.md §5, errors.md §1).
        if not isinstance(descriptor, str) or descriptor not in DESCRIPTOR_INDEX:
            raise UnknownAction(
                "legal_indices(legal_actions): %r is not one of the declared action "
                "descriptors %r" % (descriptor, declared_descriptors())
            )
        indices.append(DESCRIPTOR_INDEX[descriptor])
    return tuple(indices)


def decode_action(index, shape=None):
    """The descriptor of one index in one shape's vocabulary, and nothing else (§9).

    Two checks and a lookup: no coercion, no clamping against a decision's legal set, and
    no default descriptor for an unknown index (vocabulary.md §4, guardrails.md G8).  The
    shape decides how many indices there are -- 0 to 2 by default, 0 to 5 on the no-cap
    shape -- because an index decodes to a descriptor `engine.apply_action` accepts only
    in the vocabulary that declared it (shapes.md §4, D-29).  The index's own type is refused
    before the shape is consulted, so a non-integer is one refusal whatever name came with it.
    """
    if isinstance(index, bool) or not isinstance(index, Integral):
        raise InvalidActionIndex(
            "decode_action(index): the index must be an integer, got %r" % (index,)
        )
    row = shape_row(shape, "decode_action")
    actions = row["actions"]
    if not 0 <= index < len(actions):
        raise InvalidActionIndex(
            "decode_action(index, shape): the index must be one of %r on the shape %r, "
            "whose vocabulary is %r, got %r"
            % (tuple(range(len(actions))), row["name"], actions, index)
        )
    return actions[int(index)]
