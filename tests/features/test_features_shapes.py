"""FEA-8 -- the second declared game shape, and the three names that take it.

``docs/L2/features/surface.md`` §4, §7-§9; ``docs/L2/features/shapes.md`` §1-§6;
``docs/L3/features/vocabulary.md`` §1-§4; ``docs/L3/features/flat-numeric.md`` §4;
``docs/L3/features/card-tokens.md`` §4; ``docs/L1/shapes.md`` (D-29).

The shape is this module's data and one table is its whole statement: three of the
seven names take it as an optional **keyword**, absence is the **default** shape
(``fixed-limit-20``) and a name the catalogue does not carry is refused rather than
substituted.  The shape moves two things and nothing else -- the divisor table and the
bucket ladders -- so the default's observations are unmoved to the last slot while the
second shape's are its own.

This battery asserts the shape as the design states it: the default record key for key
and value for value, the second shape's six indices in their declared (deliberately
non-monotone) order, the two tables, and the mask over the six-descriptor vocabulary.
Every number below is the design's, not a re-derivation: ``declarations.py`` is the
authority and ``shapes.md`` §2-§5, ``flat-numeric.md`` §4 and ``card-tokens.md`` §4 are
where it is written down.

The case ids continue the FEA-8 series after the refusals' FEA-8.21, so the battery that
already holds those ids is not renumbered (``battery.md`` §5, D-11).  No case asserts an
exception *class* -- the classes are this module's freedom (``errors.md`` §2) -- and no
case reaches below the seven declared names.
"""

import itertools
import os
import sys
import unittest

import numpy

try:  # discovered as part of a tests.features package
    from . import _features_support as S
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _features_support as S  # noqa: E402


# --------------------------------------------------------------------------
# The design's own numbers, restated once for this battery (shapes.md §2-§5)
# --------------------------------------------------------------------------
#: The two declared shape names, the default first -- the whole catalogue (shapes.md
#: §2).  ``None`` is the default and is not a third shape: absence is not a name.
SHAPES = ("fixed-limit-20", "no-limit-100")
DEFAULT = SHAPES[0]
SECOND = SHAPES[1]

#: The default shape's record, exactly as ``surface.md`` §2 and §7 state it: three
#: indices, no amount, and the sentence the raise denotes.  This is the literal the
#: no-argument call is held to, key for key and value for value (shapes.md §1, D-29).
TODAY = {
    0: {"name": "fold"},
    1: {"name": "check-call"},
    2: {
        "name": "raise",
        "completion": "the engine's minimum legal completion for the decision",
    },
}

#: The second shape's descriptors in its own declared index order -- deliberately not
#: monotone in amount: the all-in is 4 and the minimum raise 5 (shapes.md §3).
SECOND_VOCABULARY = (
    "fold",
    "check-call",
    "raise-quarter",
    "raise-half",
    "raise-all-in",
    "raise-minimum",
)

#: The same four descriptors ordered by the amount each resolves to, which the declared
#: order must **not** be: an index a reader could read as a size is the defect the order
#: exists to prevent (shapes.md §3, sizing.md §3).
AMOUNT_ORDER = ("raise-minimum", "raise-quarter", "raise-half", "raise-all-in")

#: The second shape's five bucket ladders, as ``(upper bound, id)`` pairs read in order
#: with the last bound unbounded (card-tokens.md §4, shapes.md §2).  The ten ids per
#: block do not move between shapes, which is why ``S.LADDERS``' ids are the range every
#: case here checks a shape's ids against.
SECOND_LADDERS = {
    "to_call": (
        (0, 61), (1, 62), (2, 63), (3, 64), (5, 65), (10, 66), (25, 67), (None, 68),
    ),
    "pot": (
        (4, 69), (8, 70), (16, 71), (32, 72), (64, 73), (100, 74), (150, 75), (None, 76),
    ),
    "stacks": (
        (5, 77), (10, 78), (20, 79), (40, 80), (60, 81), (80, 82), (95, 83), (None, 84),
    ),
    "bet": (
        (5, 85), (10, 86), (25, 87), (None, 88),
    ),
    "raises": (
        (0, 89), (2, 90), (5, 91), (None, 92),
    ),
}

#: Which token block each ladder is read from, the readout fact a probe writes, and the
#: position the ladder's own token takes inside that block -- the readout's fact names
#: and the block's own order, never a slot index of this battery's own (card-tokens.md
#: §2).
LADDER_BLOCKS = {
    "to_call": ("to_call", "to_call", 0),
    "pot": ("pot", "pot", 0),
    "stacks": ("stacks", "stacks", 1),
    "bet": ("limit", "limit-size", 0),
    "raises": ("limit", "limit-count", 1),
}

#: The amounts each ladder is walked at: both tables' edges and the value just past
#: each, so a divisor or an edge that moved is visible on either shape (card-tokens.md
#: §4).
LADDER_PROBES = {
    "to_call": (0, 1, 2, 3, 4, 5, 6, 10, 11, 25, 26, 40),
    "pot": (0, 3, 4, 5, 8, 9, 16, 17, 32, 33, 64, 65, 100, 101, 150, 151, 400),
    "stacks": (0, 1, 5, 6, 10, 11, 20, 21, 40, 41, 60, 61, 80, 81, 95, 96, 101),
    "bet": (0, 1, 2, 3, 4, 5, 6, 10, 11, 25, 26, 100),
    "raises": (0, 1, 2, 3, 4, 5, 6, 51),
}

#: A name that is no declared shape, and one that is no declared encoding: both are the
#: writer's own, invented from the declared catalogue (``battery.md`` §4, D-15).
UNDECLARED_SHAPE = "no-limit-200"
UNDECLARED_ENCODING = "tabular-bucket"


def second_bucket(ladder, value):
    """The id the second shape's named ladder gives one non-negative integer."""
    for bound, ident in SECOND_LADDERS[ladder]:
        if bound is None or value <= bound:
            return ident
    raise AssertionError("the %s ladder has no bound for %r" % (ladder, value))


def observation_of(self, encoding, shape, record):
    """One observation, from an encoder built by name on one shape."""
    return self.ep("encode")(self.ep("build_encoder")(encoding, shape=shape), record)


class FEA8ActionSpaceDefault(S.FeaturesCase):
    """`action_space()` with no shape is today's record, and the default shape's."""

    def test_fea8_22_the_default_shape_is_todays_record_key_for_key(self):
        """FEA-8.22 action_space() with no argument is exactly the three-index record the
        surface has always declared -- all three indices, all three names and the
        `completion` sentence -- and equals action_space(shape="fixed-limit-20"), so the
        default is the default key for key and value for value (surface.md §7, shapes.md
        §1, §3, vocabulary.md §2, D-29)."""
        space = self.ep("action_space")()
        named = self.ep("action_space")(shape=DEFAULT)
        self.assertTrue(
            S.is_mapping(space),
            "action_space() returns a mapping keyed by the shape's indices (surface.md §7)",
        )
        self.assertEqual(
            list(space), [0, 1, 2],
            "the default shape's three keys are 0, 1 and 2, in ascending index order "
            "(vocabulary.md §2): %r" % (list(space),),
        )
        self.assertEqual(
            space, TODAY,
            "the no-shape call is today's record exactly: 0 fold, 1 check-call, 2 raise "
            "with the sentence that it denotes the engine's minimum legal completion "
            "(surface.md §2, §7, shapes.md §3): %r" % (space,),
        )
        self.assertEqual(
            named, TODAY,
            "naming the default shape is the same record: absence and the default name "
            "are one shape (shapes.md §3, D-29): %r" % (named,),
        )
        self.assertEqual(
            space, named,
            "action_space() and action_space(shape=%r) are one record (shapes.md §3, "
            "D-29): %r != %r" % (DEFAULT, space, named),
        )
        for index, record in TODAY.items():
            with self.subTest(index=index):
                self.assertEqual(
                    space[index], record,
                    "index %r is %r, value for value (surface.md §2, §7): %r"
                    % (index, record, space[index]),
                )
                self.assertEqual(
                    set(space[index]), set(record),
                    "index %r carries its name%s and no seventh key (surface.md §7): %r"
                    % (index, " and the completion sentence" if index == 2 else "",
                       sorted(space[index])),
                )
        self.assertEqual(
            space[2]["completion"],
            "the engine's minimum legal completion for the decision",
            "the raise's resolution is the declared sentence, not a paraphrase of it "
            "(surface.md §2, §7, vocabulary.md §2): %r" % (space[2].get("completion"),),
        )
        self.assertNotIn(
            "band", space[2],
            "the default shape's raise resolves to a completion and never to a band: a "
            "band is the six-index shape's spelling (shapes.md §3): %r" % (space[2],),
        )


class FEA8ActionSpaceSecondShape(S.FeaturesCase):
    """`action_space(shape=...)` declares the shape's own six indices and nothing more."""

    def test_fea8_23_the_six_names_are_in_declared_index_order_and_not_monotone(self):
        """FEA-8.23 action_space(shape="no-limit-100") is keyed [0,1,2,3,4,5] and names
        the six descriptors in the declared order; the order is deliberately not
        monotone in amount, so index 4 is raise-all-in and index 5 raise-minimum
        (surface.md §7, shapes.md §3, vocabulary.md §1)."""
        space = self.ep("action_space")(shape=SECOND)
        self.assertTrue(
            S.is_mapping(space),
            "action_space(shape=%r) returns one mapping (surface.md §7)" % (SECOND,),
        )
        keys = list(space)
        self.assertEqual(
            keys, [0, 1, 2, 3, 4, 5],
            "the second shape's six keys are 0 to 5, in its declared index order "
            "(vocabulary.md §1, §2): %r" % (keys,),
        )
        for index, expected in enumerate(SECOND_VOCABULARY):
            with self.subTest(index=index):
                record = space[index]
                self.assertTrue(
                    S.is_mapping(record),
                    "each value is a plain record carrying the action's name "
                    "(surface.md §7): %r" % (record,),
                )
                self.assertEqual(
                    record["name"], expected,
                    "index %d is %r, the shape's declared spelling at that position "
                    "(vocabulary.md §1): %r" % (index, expected, record.get("name")),
                )
        self.assertEqual(
            space[4]["name"], "raise-all-in",
            "index 4 is the all-in, the largest legal raise-to amount (shapes.md §3, "
            "vocabulary.md §1): %r" % (space[4].get("name"),),
        )
        self.assertEqual(
            space[5]["name"], "raise-minimum",
            "index 5 is the minimum legal raise-to, the smallest amount, so the order "
            "cannot be read as a size (shapes.md §3, sizing.md §3): %r"
            % (space[5].get("name"),),
        )
        raised = tuple(space[index]["name"] for index in (2, 3, 4, 5))
        self.assertNotEqual(
            raised, AMOUNT_ORDER,
            "the four raise descriptors are not in ascending amount order: the all-in "
            "sits before the minimum raise, deliberately (shapes.md §3, sizing.md §3): "
            "%r against the amount order %r" % (raised, AMOUNT_ORDER),
        )
        self.assertEqual(
            (space[0]["name"], space[1]["name"]), ("fold", "check-call"),
            "the two vocabularies share their first two entries, at the same indices "
            "(vocabulary.md §1, §5): %r"
            % (tuple(space[index]["name"] for index in (0, 1)),),
        )

    def test_fea8_24_the_only_integers_are_the_shapes_own_indices(self):
        """FEA-8.24 on both shapes the integer set the L1 reader finds is exactly the
        shape's own indices -- {0,1,2} and {0,1,2,3,4,5} -- each record carries no number
        of its own, and no string anywhere in the record contains a digit (surface.md §7,
        vocabulary.md §2, guardrails.md G6, FAM-2.9)."""
        for shape, expected in (
            (None, {0, 1, 2}),
            (DEFAULT, {0, 1, 2}),
            (SECOND, {0, 1, 2, 3, 4, 5}),
        ):
            with self.subTest(shape=shape):
                space = self.ep("action_space")(shape=shape)
                vocabulary = S.action_vocabulary(space)
                self.assertEqual(
                    vocabulary, expected,
                    "the vocabulary the record declares is exactly the shape's own "
                    "indices, read from keys as well as values: no amount, no chip count "
                    "and no size (surface.md §7, vocabulary.md §2, FAM-2.9): %r from %r"
                    % (sorted(vocabulary), space),
                )
                for index, record in space.items():
                    with self.subTest(shape=shape, index=index):
                        self.assertEqual(
                            S.numbers(record), [],
                            "no record carries a number of its own: the shape's indices "
                            "are the only numbers in the record (surface.md §7, "
                            "guardrails.md G6): %r" % (record,),
                        )
                with_digits = [
                    text for text in S.strings(space) if any(c.isdigit() for c in text)
                ]
                self.assertEqual(
                    with_digits, [],
                    "no string in the record -- in a key or in a value, at any depth -- "
                    "contains a digit, so no prose smuggles a chip count past the "
                    "integers the reader found (vocabulary.md §2, guardrails.md G6): %r"
                    % (with_digits,),
                )

    def test_fea8_25_every_raise_record_carries_a_prose_resolution(self):
        """FEA-8.25 the default's raise says it denotes the engine's minimum legal
        completion, each of the second shape's four raise records carries a `band` note
        naming the part of the raise interval the index takes, that text is prose and not
        a number, and no descriptor that resolves no amount carries a resolution at all
        (surface.md §7, shapes.md §3, vocabulary.md §2)."""
        default = self.ep("action_space")()
        self.assertEqual(
            sorted(default[2]), ["completion", "name"],
            "the default raise's record is its name and the completion it denotes "
            "(surface.md §2, §7): %r" % (sorted(default[2]),),
        )
        self.assertIn(
            "minimum legal completion", S.flatten_text(default[2]),
            "the raise's resolution says it denotes the engine's minimum legal "
            "completion (surface.md §2, vocabulary.md §2): %r" % (default[2],),
        )
        space = self.ep("action_space")(shape=SECOND)
        bands = []
        for index in (2, 3, 4, 5):
            with self.subTest(index=index, descriptor=SECOND_VOCABULARY[index]):
                record = space[index]
                self.assertEqual(
                    sorted(record), ["band", "name"],
                    "the raise record at index %d is its name and the band it takes, and "
                    "nothing else (surface.md §7, shapes.md §3): %r"
                    % (index, sorted(record)),
                )
                band = record["band"]
                self.assertIsInstance(
                    band, str,
                    "a resolution is prose a report's header may quote, never a number "
                    "(surface.md §7, guardrails.md G11): %r" % (band,),
                )
                self.assertFalse(
                    S.is_number(band),
                    "a band's resolution is prose and not an amount or a fraction "
                    "(surface.md §7, vocabulary.md §2): %r" % (band,),
                )
                self.assertTrue(
                    band.strip(),
                    "the band note says something (surface.md §7): %r" % (band,),
                )
                self.assertEqual(
                    [c for c in band if c.isdigit()], [],
                    "no digit in the band's prose, so no chip count can be read as one "
                    "of the vocabulary's indices (guardrails.md G6): %r" % (band,),
                )
                self.assertGreaterEqual(
                    len(band.split()), 3,
                    "the band note is prose about the legal raise interval, not a token "
                    "(surface.md §7): %r" % (band,),
                )
                bands.append(band)
        self.assertEqual(
            len(set(bands)), 4,
            "four raise indices denote four different bands of the raise interval "
            "(shapes.md §3, vocabulary.md §1): %r" % (bands,),
        )
        for index in (0, 1):
            with self.subTest(index=index):
                self.assertEqual(
                    sorted(space[index]), ["name"],
                    "a descriptor that resolves no amount carries its name and no "
                    "resolution key (surface.md §7, vocabulary.md §1): %r"
                    % (space[index],),
                )

    def test_fea8_26_two_calls_are_equal_and_a_mutation_does_not_persist(self):
        """FEA-8.26 on both shapes two calls of action_space are equal, each is a fresh
        mapping with fresh records, and mutating one is invisible to the next (surface.md
        §7, shapes.md §3, guardrails.md G11)."""
        for shape in (None, DEFAULT, SECOND):
            with self.subTest(shape=shape):
                first = self.ep("action_space")(shape=shape)
                before = {index: dict(record) for index, record in first.items()}
                top = max(before)
                first[0]["name"] = "bet"
                first[top]["sizes"] = (2, 4)
                first[99] = {"name": "call-any"}
                del first[1]
                again = self.ep("action_space")(shape=shape)
                self.assertEqual(
                    again, before,
                    "the vocabulary is the shape's fixed declaration, rebuilt on every "
                    "call (surface.md §7, guardrails.md G11): %r != %r" % (again, before),
                )
                self.assertEqual(
                    again, self.ep("action_space")(shape=shape),
                    "two calls with one shape return equal records (surface.md §7): %r != "
                    "%r" % (again, self.ep("action_space")(shape=shape)),
                )
                self.assertIsNot(
                    first, again,
                    "each call returns a fresh mapping, never the one the caller was "
                    "handed (surface.md §7, guardrails.md G11)",
                )
                self.assertIsNot(
                    first[0], again[0],
                    "and a fresh record inside it, so one caller's edit cannot reach the "
                    "next caller's index (guardrails.md G11): %r" % (first[0],),
                )


class FEA8ShapeRefusals(S.FeaturesCase):
    """A shape name outside the catalogue is refused, never defaulted."""

    def test_fea8_27_an_undeclared_shape_name_is_refused_naming_it_and_the_declared_names(self):
        """FEA-8.27 each of the three names that take a shape refuses a name outside the
        catalogue, by a message naming the entry point, the rejected value and both
        declared names; a name that is not a str is refused too; and build_encoder still
        refuses an unknown encoding first, so the two refusals cannot trade places
        (surface.md §4, §7, §9, shapes.md §6, vocabulary.md §4, D-29)."""
        calls = (
            ("action_space", lambda bad: self.ep("action_space")(shape=bad)),
            ("build_encoder", lambda bad: self.ep("build_encoder")(S.FLAT, shape=bad)),
            ("decode_action", lambda bad: self.ep("decode_action")(0, shape=bad)),
        )
        for bad in (UNDECLARED_SHAPE, "no-limit", "fixed-limit-40", "FIXED-LIMIT-20",
                    " fixed-limit-20", "fixed_limit_20", "", 0, True,
                    ("no-limit-100",)):
            for entry_point, call in calls:
                with self.subTest(shape=bad, entry_point=entry_point):
                    self.refuses(call, bad, words=(entry_point, str(bad)) + SHAPES)
        for entry_point, call in calls:
            with self.subTest(entry_point=entry_point, names="declared"):
                self.refuses(
                    call, UNDECLARED_SHAPE,
                    words=(entry_point, UNDECLARED_SHAPE, DEFAULT, SECOND),
                )
        exc = self.refuses(
            lambda: self.ep("build_encoder")(UNDECLARED_ENCODING, shape=SECOND),
            words=("build_encoder", UNDECLARED_ENCODING, S.FLAT, S.TOKENS),
        )
        self.assertNotIn(
            SECOND, str(exc),
            "an unknown encoding is refused before the shape is looked at, so the two "
            "refusals cannot trade places (shapes.md §6, encoder.md §2): %r" % (str(exc),),
        )
        self.refuses(
            lambda: self.ep("build_encoder")(UNDECLARED_ENCODING, shape=UNDECLARED_SHAPE),
            words=("build_encoder", UNDECLARED_ENCODING),
        )


class FEA8ShapedEncoder(S.FeaturesCase):
    """An encoder's divisor and bucket tables are its shape's; its spec is not."""

    def spec_on(self, name, shape):
        """The six-key spec of one encoding built on one shape, read through two names."""
        return self.ep("observation_spec")(self.ep("build_encoder")(name, shape=shape))

    def test_fea8_28_the_second_shapes_spec_is_the_same_six_values(self):
        """FEA-8.28 build_encoder(name, shape="no-limit-100") yields an encoder whose
        observation_spec carries the same six keys and the same six values as the
        default's -- slot counts, widths, dtype and token vocabulary do not move -- and
        whose encode returns the declared shape and dtype (surface.md §4, §5, §6;
        shapes.md §5, D-29)."""
        record = S.readout(stacks=(96, 5), pot=151, to_call=11, limit=(26, 6))
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                declared = S.DECLARED[name]
                plain = self.ep("observation_spec")(self.ep("build_encoder")(name))
                default = self.spec_on(name, DEFAULT)
                second = self.spec_on(name, SECOND)
                self.assertEqual(
                    set(second), set(S.SPEC_KEYS),
                    "the second shape's spec carries exactly the six declared keys, with "
                    "no seventh naming a shape or a normaliser (surface.md §5, shapes.md "
                    "§5): %r" % (sorted(second),),
                )
                self.assertEqual(
                    len(second), 6,
                    "six keys, not seven (surface.md §5, shapes.md §5): %r"
                    % (sorted(second),),
                )
                for other, where in ((plain, "the no-shape encoder"),
                                     (default, "the default shape's encoder")):
                    with self.subTest(encoding=name, against=where):
                        self.assertEqual(
                            second, other,
                            "the spec's six values are shape-invariant: the second "
                            "shape's record is %s's value for value (shapes.md §5, "
                            "surface.md §5): %r != %r" % (where, second, other),
                        )
                expected = {
                    "representation": name,
                    "kind": declared["kind"],
                    "fields": S.FIELDS,
                    "shape": declared["shape"],
                    "dtype": declared["dtype"],
                    "vocabulary": declared["vocabulary"],
                }
                for key, wanted in expected.items():
                    with self.subTest(encoding=name, key=key):
                        self.assertEqual(
                            second[key], wanted,
                            "the second shape's %r is %r, exactly as the default's is "
                            "(surface.md §5, shapes.md §5): %r"
                            % (key, wanted, second[key]),
                        )
                observation = observation_of(self, name, SECOND, record)
                self.assertEqual(
                    self.shape_of(observation), declared["shape"],
                    "an encoder built for the second shape still returns the declared "
                    "shape (surface.md §6, shapes.md §5): %r"
                    % (self.shape_of(observation),),
                )
                self.assertEqual(
                    observation.dtype, numpy.dtype(declared["dtype"]),
                    "and the declared dtype (surface.md §5, §6): %r"
                    % (observation.dtype,),
                )


class FEA8DenseDivisors(S.FeaturesCase):
    """The dense encoding divides by the shape's five normalisers and no others."""

    def test_fea8_29_the_dense_divisors_are_the_shapes(self):
        """FEA-8.29 one readout with stacks=(100,100), pot=200, to_call=100 and
        limit=(100,50) encodes to exactly 1.0 in the stacks, pot, to_call and both limit
        slots on no-limit-100, and to 5.0, 5.0, 5.0, 25.0 and 12.5 on the default shape
        -- a divisor of 20, 40, 20, 4 and 4 (surface.md §6, shapes.md §2, flat-numeric.md
        §4, FAM-2.9)."""
        record = S.readout(stacks=(100, 100), pot=200, to_call=100, limit=(100, 50))
        block = {field: (offset, width) for field, offset, width in S.FLAT_BLOCKS}
        on_second = S.floats(observation_of(self, S.FLAT, SECOND, record))
        on_default = S.floats(observation_of(self, S.FLAT, DEFAULT, record))
        unnamed = S.floats(self.flat(record))
        self.assertEqual(
            len(on_second), len(on_default),
            "the two shapes' dense observations are one width: the shape moves no slot "
            "count (shapes.md §5): %d against %d" % (len(on_second), len(on_default)),
        )
        expectations = (
            ("stacks", [1.0, 1.0], [5.0, 5.0], "÷100 against ÷20"),
            ("pot", [1.0], [5.0], "÷200 against ÷40"),
            ("to_call", [1.0], [5.0], "÷100 against ÷20"),
            ("limit", [1.0, 1.0], [25.0, 12.5], "÷100 and ÷50 against ÷4 and ÷4"),
        )
        for field, second, default, divisors in expectations:
            offset, width = block[field]
            with self.subTest(field=field):
                self.assertEqual(
                    width, len(second),
                    "the %r block is %d slots on both shapes (shapes.md §5)"
                    % (field, len(second)),
                )
                self.assert_floats(
                    on_second[offset:offset + width], second,
                    "the %r block of a readout sitting at the second shape's normalisers "
                    "(%s, shapes.md §2, flat-numeric.md §4)" % (field, divisors),
                )
                self.assert_floats(
                    on_default[offset:offset + width], default,
                    "the %r block of the same readout on the default shape (%s, "
                    "shapes.md §2, flat-numeric.md §4)" % (field, divisors),
                )
        self.assert_floats(
            unnamed, on_default,
            "an encoder built with no shape is the default shape's encoder: the default's "
            "observation is unmoved, byte for byte (shapes.md §2, §5, D-29)",
        )
        self.assertNotEqual(
            on_second, on_default,
            "and the second shape's observation is its own: one readout at both shapes' "
            "normalisers cannot encode the same (shapes.md §2): %r" % (on_second[:8],),
        )


class FEA8TokenLadders(S.FeaturesCase):
    """The token encoding's five bucket ladders are the shape's too."""

    def test_fea8_30_the_token_ladders_are_the_shapes(self):
        """FEA-8.30 on no-limit-100 stacks=(96, 5) bucket to ids (84, 77), pot 151 to 76,
        to_call 11 to 67 and limit=(26, 6) to (88, 92); the same amounts on the default
        shape bucket by the default tables -- (84, 79), 76, 68 and (88, 92) -- and every
        id either shape emits stays inside its own block's id range, which does not move
        between shapes (surface.md §6, shapes.md §2, §5, card-tokens.md §4)."""
        block = {field: (offset, width) for field, offset, width in S.TOKEN_BLOCKS}
        record = S.readout(stacks=(96, 5), pot=151, to_call=11, limit=(26, 6))
        on_second = S.ints(observation_of(self, S.TOKENS, SECOND, record))
        on_default = S.ints(observation_of(self, S.TOKENS, DEFAULT, record))
        self.assertEqual(
            len(on_second), len(on_default),
            "the two shapes' token observations are one width: the shape moves no token "
            "count (shapes.md §5): %d against %d" % (len(on_second), len(on_default)),
        )
        worked = (
            ("stacks", [84, 77], [84, 79], "0-5 6-10 11-20 ... 96+ against 0-1 2-3 ... 18+"),
            ("pot", [76], [76], "151+ against 33+"),
            ("to_call", [67], [68], "11-25 against 11+"),
            ("limit", [88, 92], [88, 92], "26+ and 6+ against 5+ and 3+"),
        )
        for field, second, default, edges in worked:
            offset, width = block[field]
            with self.subTest(field=field):
                self.assertEqual(
                    width, len(second),
                    "the %r block is %d tokens on both shapes (shapes.md §5)"
                    % (field, len(second)),
                )
                self.assert_ints(
                    on_second[offset:offset + width], second,
                    "the %r block on no-limit-100, whose ladder edges are %s "
                    "(card-tokens.md §4, shapes.md §2)" % (field, edges),
                )
                self.assert_ints(
                    on_default[offset:offset + width], default,
                    "the %r block of the same amounts on the default shape, whose ladder "
                    "edges are unchanged (card-tokens.md §4)" % (field,),
                )
        self.assertNotEqual(
            on_second, on_default,
            "the two shapes' token observations are their own bucket tables: one amount "
            "set cannot encode the same (shapes.md §2): %r" % (on_second[10:16],),
        )
        for ladder in S.LADDERS:
            field, facts, position = LADDER_BLOCKS[ladder]
            offset, width = block[field]
            slot = offset + (position if width > 1 else 0)
            for value in LADDER_PROBES[ladder]:
                for shape, expected in (
                    (SECOND, second_bucket(ladder, value)),
                    (DEFAULT, S.bucket(ladder, value)),
                ):
                    with self.subTest(ladder=ladder, value=value, shape=shape):
                        changed = dict(record)
                        if facts == "stacks":
                            changed["stacks"] = (value, value)
                        elif facts == "limit-size":
                            changed["limit"] = (value, 0)
                        elif facts == "limit-count":
                            changed["limit"] = (2, value)
                        else:
                            changed[facts] = value
                        values = S.ints(observation_of(self, S.TOKENS, shape, changed))
                        if ladder == "stacks":
                            emitted = values[offset:offset + width]
                            self.assertEqual(
                                emitted, [expected, expected],
                                "a stack of %r is id %r on both tokens, and the block "
                                "reads stacks[0] then stacks[1] on either shape "
                                "(card-tokens.md §4, shapes.md §5): %r"
                                % (value, expected, emitted),
                            )
                        else:
                            self.assertEqual(
                                values[slot], expected,
                                "a %s of %r is the id the %r shape's ladder fixes "
                                "(card-tokens.md §4, shapes.md §2): %r, expected %r"
                                % (ladder, value, shape, values[slot], expected),
                            )
                        self.assertIn(
                            expected, S.ladder_ids(ladder),
                            "a %s id is one of %r on every shape: the ids do not move, "
                            "only the edges do (card-tokens.md §4, shapes.md §5): %r"
                            % (ladder, S.ladder_ids(ladder), expected),
                        )


class FEA8LegalIndicesSix(S.FeaturesCase):
    """`legal_indices` covers the six-descriptor vocabulary, masked bands included."""

    def test_fea8_31_the_six_descriptor_vocabulary_is_position_aligned(self):
        """FEA-8.31 legal_indices takes no shape and is position-aligned over the whole
        declared vocabulary: the six in order give (0,1,2,3,4,5), a masked set
        ("check-call","raise-minimum") gives (1,5), an out-of-order argument keeps its
        own order -- never sorted -- every non-empty subset in every order gives its
        descriptors' indices, and each index round-trips through
        decode_action(index, shape="no-limit-100") (surface.md §8, shapes.md §4,
        vocabulary.md §3, FAM-2.11)."""
        def indices(descriptors):
            return self.ep("legal_indices")(descriptors)

        def decode(index):
            return self.ep("decode_action")(index, shape=SECOND)

        self.assertIsInstance(
            indices(SECOND_VOCABULARY), tuple,
            "legal_indices returns a tuple of indices (surface.md §8, layout.md §4): %r"
            % (indices(SECOND_VOCABULARY),),
        )
        self.assertEqual(
            indices(SECOND_VOCABULARY), (0, 1, 2, 3, 4, 5),
            "the full declared six give the six indices in that order (surface.md §8, "
            "shapes.md §4): %r" % (indices(SECOND_VOCABULARY),),
        )
        self.assertEqual(
            indices(("check-call", "raise-minimum")), (1, 5),
            "a masked decision -- no fold, three bands empty -- gives the indices of the "
            "descriptors it really has, and 5 is the minimum raise's own index "
            "(shapes.md §4, vocabulary.md §3): %r"
            % (indices(("check-call", "raise-minimum")),),
        )
        self.assertEqual(
            indices(("raise-all-in", "fold", "raise-half")), (4, 0, 3),
            "the mask is position-aligned with the argument and is never sorted: the "
            "all-in's index comes first because the argument does (surface.md §8, "
            "guardrails.md G7): %r"
            % (indices(("raise-all-in", "fold", "raise-half")),),
        )
        walked = 0
        for size in range(1, len(SECOND_VOCABULARY) + 1):
            for chosen in itertools.permutations(SECOND_VOCABULARY, size):
                walked += 1
                with self.subTest(descriptors=chosen):
                    expected = tuple(
                        SECOND_VOCABULARY.index(descriptor) for descriptor in chosen
                    )
                    self.assertEqual(
                        indices(chosen), expected,
                        "one index per descriptor, in the argument's own order: an "
                        "argument out of the engine's order keeps its order "
                        "(vocabulary.md §3, guardrails.md G7): %r must give %r"
                        % (chosen, expected),
                    )
                    for position, index in enumerate(expected):
                        self.assertEqual(
                            decode(index), chosen[position],
                            "and the index reads back as its descriptor: decode_action is "
                            "legal_indices' reverse step (surface.md §2, §9, FAM-2.10): "
                            "%r -> %r, expected %r"
                            % (index, decode(index), chosen[position]),
                        )
        self.assertEqual(
            walked, sum(1 for _size in range(1, 7)
                        for _ in itertools.permutations(range(6), _size)),
            "every non-empty subset of the six was read in every order (surface.md §8)",
        )
        self.assertEqual(
            len(set(indices(SECOND_VOCABULARY))), 6,
            "one decision's indices are distinct: the six descriptors are six indices "
            "(surface.md §8, FAM-2.11): %r" % (indices(SECOND_VOCABULARY),),
        )
        self.assertEqual(
            indices(S.ACTIONS), (0, 1, 2),
            "the default shape's three descriptors are still indices 0, 1 and 2: the "
            "six-index table is total over both vocabularies (shapes.md §4, "
            "vocabulary.md §3): %r" % (indices(S.ACTIONS),),
        )


class FEA8DecodeActionShapes(S.FeaturesCase):
    """`decode_action` is one shape's index in, that shape's descriptor out."""

    def decode(self, index, shape=None):
        """One index decoded on one shape, through the one name that decodes one."""
        return self.ep("decode_action")(index, shape=shape)

    def test_fea8_32_each_shape_decodes_its_own_vocabulary_and_refuses_the_rest(self):
        """FEA-8.32 0-5 decode to the six declared descriptors on no-limit-100, index 3
        and 5 are refused on the default shape naming the index, the shape and its
        vocabulary while 3 is accepted on the second, 6 and -1 are refused on the
        second, and a bool, a float and a str are refused on both on the word "integer"
        (surface.md §2, §9; shapes.md §4, §6; vocabulary.md §4, FAM-2.10)."""
        space = self.ep("action_space")(shape=SECOND)
        for index, expected in enumerate(SECOND_VOCABULARY):
            with self.subTest(index=index):
                descriptor = self.decode(index, SECOND)
                self.assertIsInstance(
                    descriptor, str,
                    "decode_action returns a plain str (surface.md §9, vocabulary.md "
                    "§4): %r" % (descriptor,),
                )
                self.assertEqual(
                    descriptor, expected,
                    "index %d on the second shape is %r, its declared spelling "
                    "(vocabulary.md §1, §4): %r" % (index, expected, descriptor),
                )
                self.assertEqual(
                    descriptor, space[index]["name"],
                    "decode_action and action_space are two directions of one "
                    "vocabulary (vocabulary.md §1, §2): %r != %r"
                    % (descriptor, space[index]["name"]),
                )
        for index in (3, 5):
            with self.subTest(index=index, shape=DEFAULT, accepted=False):
                self.refuses(
                    lambda index=index: self.decode(index),
                    index,
                    words=("decode_action", str(index), DEFAULT, "fold", "raise"),
                )
                self.refuses(
                    lambda index=index: self.decode(index, DEFAULT),
                    index,
                    words=("decode_action", str(index), DEFAULT),
                )
            with self.subTest(index=index, shape=SECOND, accepted=True):
                self.assertIn(
                    self.decode(index, SECOND), SECOND_VOCABULARY,
                    "index %r is inside the second shape's vocabulary, so it decodes on "
                    "that shape and only that shape (shapes.md §4, D-29): %r"
                    % (index, self.decode(index, SECOND)),
                )
                self.assertEqual(
                    self.decode(index, SECOND), SECOND_VOCABULARY[index],
                    "the same index is a different descriptor on the other shape, which "
                    "is why the shape is an argument at all (vocabulary.md §5): %r != %r"
                    % (self.decode(index, SECOND), SECOND_VOCABULARY[index]),
                )
        for index in (6, -1, 99, -(2 ** 40), 2 ** 40):
            with self.subTest(index=index, shape=SECOND):
                self.refuses(
                    lambda index=index: self.decode(index, SECOND),
                    index,
                    words=("decode_action", str(index), SECOND, "raise-minimum"),
                )
        for bad in (True, False, 1.0, 3.0, "1", "raise-half", None, [1], (1,)):
            for shape in (None, SECOND):
                with self.subTest(value=bad, shape=shape):
                    self.refuses(
                        lambda bad=bad, shape=shape: self.decode(bad, shape),
                        bad,
                        words=("integer",),
                    )
        self.assertIn(
            "0, 1, 2, 3, 4, 5", str(self.refusal(self.decode, 6, SECOND)),
            "the refusal names the second shape's whole vocabulary of indices, so a "
            "caller learns how many indices exist on it (vocabulary.md §4): %r"
            % (str(self.refusal(self.decode, 6, SECOND)),),
        )


class FEA8ShapesAgree(S.FeaturesCase):
    """The two encodings agree about one shape's readout, and never about a shape."""

    def test_fea8_33_the_two_encodings_agree_about_the_shape(self):
        """FEA-8.33 for one readout of the second shape the dense observation and the
        token observation are both the declared shape and dtype, and the to_call token is
        61 exactly when the dense to_call slot is 0.0 -- the two representations carry the
        same fact, each in its own shape's units (surface.md §6, shapes.md §2, §5,
        card-tokens.md §3, §4, D-3)."""
        dense_encoder = self.ep("build_encoder")(S.FLAT, shape=SECOND)
        token_encoder = self.ep("build_encoder")(S.TOKENS, shape=SECOND)
        dense_block = {field: (offset, width) for field, offset, width in S.FLAT_BLOCKS}
        token_block = {field: (offset, width) for field, offset, width in S.TOKEN_BLOCKS}
        dense_slot = dense_block["to_call"][0]
        token_slot = token_block["to_call"][0]
        for to_call in (0, 1, 5, 11, 25, 100):
            with self.subTest(to_call=to_call):
                record = S.readout(stacks=(96, 5), pot=151, to_call=to_call,
                                   limit=(26, 6))
                dense = self.ep("encode")(dense_encoder, record)
                tokens = self.ep("encode")(token_encoder, record)
                self.assertEqual(
                    self.shape_of(dense), S.DECLARED[S.FLAT]["shape"],
                    "the dense observation of the second shape is the declared (203,) "
                    "(surface.md §5, §6, shapes.md §5): %r"
                    % (self.shape_of(dense),),
                )
                self.assertEqual(
                    self.shape_of(tokens), S.DECLARED[S.TOKENS]["shape"],
                    "the token observation of the second shape is the declared (40,) "
                    "(surface.md §5, §6, shapes.md §5): %r"
                    % (self.shape_of(tokens),),
                )
                self.assertEqual(
                    dense.dtype, numpy.dtype(S.DECLARED[S.FLAT]["dtype"]),
                    "and its dtype is unchanged by the shape (shapes.md §5): %r"
                    % (dense.dtype,),
                )
                self.assertEqual(
                    tokens.dtype, numpy.dtype(S.DECLARED[S.TOKENS]["dtype"]),
                    "and the token observation's is too (shapes.md §5): %r"
                    % (tokens.dtype,),
                )
                slot = S.floats(dense)[dense_slot]
                token = S.ints(tokens)[token_slot]
                self.assertEqual(
                    token == 61, slot == 0.0,
                    "the to_call token is 61 exactly when the dense to_call slot is "
                    "0.0: one fact, two representations, and no disagreement about "
                    "whether anything is owed (surface.md §6, card-tokens.md §3, §4): "
                    "token %r at %r" % (token, slot),
                )
                if to_call == 0:
                    self.assertEqual(
                        token, 61,
                        "nothing to call is its own id 61, never the pad and never the "
                        "dense zero's absence (card-tokens.md §3, §4): %r" % (token,),
                    )
                    self.assertEqual(
                        slot, 0.0,
                        "and the dense slot is 0.0 (flat-numeric.md §4): %r" % (slot,),
                    )
                else:
                    self.assertGreater(
                        token, 61,
                        "an amount to call buckets above the zero id (card-tokens.md "
                        "§4): %r at a to_call of %r" % (token, to_call),
                    )
                    self.assertGreater(
                        slot, 0.0,
                        "and divides to a positive slot (flat-numeric.md §4): %r at a "
                        "to_call of %r" % (slot, to_call),
                    )
                    self.assertAlmostEqual(
                        slot, to_call / 100.0, delta=1e-5,
                        msg="the second shape's to_call divisor is its own 100, so %r "
                            "chips are %r (shapes.md §2, flat-numeric.md §4): %r"
                            % (to_call, to_call / 100.0, slot),
                    )


if __name__ == "__main__":
    unittest.main()
