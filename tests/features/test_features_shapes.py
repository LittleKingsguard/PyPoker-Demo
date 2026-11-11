"""FEA-8 -- the declared game shapes, and the three names that take one.

``docs/L2/features/surface.md`` §4, §7-§9; ``docs/L2/features/shapes.md`` §1-§6;
``docs/L3/features/vocabulary.md`` §1-§4; ``docs/L3/features/flat-numeric.md`` §4;
``docs/L3/features/card-tokens.md`` §4; ``docs/L1/shapes.md`` (D-29), §8 (the history
block's capacity is the shape's); ``docs/L1/seats.md`` §3; ``docs/L1/assumptions.md``
ASM-42, ASM-44.

The shape is this module's data and one table is its whole statement: three of the
seven names take it as an optional **keyword**, absence is the **default** shape
(``fixed-limit-20``) and a name the catalogue does not carry is refused rather than
substituted.  The shape moves the divisor table, the bucket ladders, the history block's
capacity, the **seat count** with both per-seat blocks' widths and modes, and the **token
vocabulary** those blocks need -- from which one observation's width follows -- so the
default's observations are unmoved to the last slot while each other row's are its own.

This battery asserts the shape as the design states it: the default record key for key
and value for value, the six indices of each uncapped row in their declared (deliberately
non-monotone) order, the three rows' tables, widths and vocabularies, and the mask over
the six-descriptor vocabulary.  Every number below is the design's, not a re-derivation:
``declarations.py`` is the authority and ``shapes.md`` §2-§5, §8, ``flat-numeric.md`` §4,
``card-tokens.md`` §4 and ``capacity.md`` §2-§4 are where it is written down.

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
    """An encoder's divisor and bucket tables are its shape's, and so is its width."""

    def spec_on(self, name, shape):
        """The six-key spec of one encoding built on one shape, read through two names."""
        return self.ep("observation_spec")(self.ep("build_encoder")(name, shape=shape))

    def test_fea8_28_the_second_shapes_spec_is_the_same_five_values_and_its_own_width(self):
        """FEA-8.28 build_encoder(name, shape="no-limit-100") yields an encoder whose
        observation_spec carries the same six keys and five of the same six values as the
        default's -- representation, kind, fields, dtype and vocabulary do not move --
        and its own `shape`, because one observation's width follows the history block's
        capacity and the capacity is the shape's: (329,) dense and (82,) tokens against
        the default's (203,) and (40,), which is the record it always was (surface.md §4,
        §5, §6; shapes.md §5, §8, ASM-42, ASM-44)."""
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
                self.assertEqual(
                    second, dict(default, shape=S.DECLARED_BY_SHAPE[SECOND][name]),
                    "the second shape's record is the default's with its own width and "
                    "nothing else changed: the capacity is the one fact the shape adds to "
                    "a spec (shapes.md §8, ASM-42, ASM-44): %r against %r"
                    % (second, default),
                )
                self.assertEqual(
                    plain,
                    {
                        "representation": name,
                        "kind": declared["kind"],
                        "fields": S.FIELDS,
                        "shape": declared["shape"],
                        "dtype": declared["dtype"],
                        "vocabulary": declared["vocabulary"],
                    },
                    "the no-shape encoder's record is what it always was: %r's kind, the "
                    "nine fields, (203,)/(40,), its dtype and 96 ids (surface.md §5, "
                    "shapes.md §5): %r" % (name, plain),
                )
                self.assertEqual(
                    default, plain,
                    "naming the default shape is the no-shape record value for value "
                    "(shapes.md §3, D-29): %r != %r" % (default, plain),
                )
                for key in ("representation", "kind", "fields", "dtype", "vocabulary"):
                    with self.subTest(encoding=name, key=key):
                        self.assertEqual(
                            second[key], default[key],
                            "the second shape's %r is the default's: only `shape` follows "
                            "the shape, because only the history block's capacity does "
                            "(shapes.md §8, ASM-44): %r against %r"
                            % (key, second[key], default[key]),
                        )
                self.assertEqual(
                    tuple(second["shape"]), S.DECLARED_BY_SHAPE[SECOND][name],
                    "the second shape declares its own width -- %r dense and %r tokens -- "
                    "and this record is where a learner reads it (surface.md §5, shapes.md "
                    "§8, ASM-44): %r"
                    % (S.DECLARED_BY_SHAPE[SECOND][S.FLAT],
                       S.DECLARED_BY_SHAPE[SECOND][S.TOKENS], second["shape"]),
                )
                observation = observation_of(self, name, SECOND, record)
                self.assertEqual(
                    self.shape_of(observation), tuple(second["shape"]),
                    "an encoder built for the second shape returns the shape its own spec "
                    "declares (surface.md §6, shapes.md §8): %r"
                    % (self.shape_of(observation),),
                )
                self.assertEqual(
                    observation.dtype, numpy.dtype(declared["dtype"]),
                    "and the declared dtype, which the shape does not move (surface.md §5, "
                    "§6): %r" % (observation.dtype,),
                )
                self.assertEqual(
                    self.shape_of(observation_of(self, name, DEFAULT, record)),
                    declared["shape"],
                    "while the default shape's observation is still the declared %r: the "
                    "fixed-limit path does not move (shapes.md §5, §8): %r"
                    % (declared["shape"],
                       self.shape_of(observation_of(self, name, DEFAULT, record))),
                )


class FEA8DenseDivisors(S.FeaturesCase):
    """The dense encoding divides by the shape's five normalisers and no others."""

    def test_fea8_29_the_dense_divisors_are_the_shapes(self):
        """FEA-8.29 one readout with stacks=(100,100), pot=200, to_call=100 and
        limit=(100,50) encodes to exactly 1.0 in the stacks, pot, to_call and both limit
        slots on no-limit-100, and to 5.0, 5.0, 5.0, 25.0 and 12.5 on the default shape
        -- a divisor of 20, 40, 20, 4 and 4 while the second shape divides by 100, 200,
        100, 100 and 50; the two observations are their shapes' own widths, 329 against
        203, and every slot before the history is the same number of slots on both
        (surface.md §6, shapes.md §2, §8, flat-numeric.md §4, §5, FAM-2.9, ASM-42)."""
        record = S.readout(stacks=(100, 100), pot=200, to_call=100, limit=(100, 50))
        block = {field: (offset, width) for field, offset, width in S.FLAT_BLOCKS}
        on_second = S.floats(observation_of(self, S.FLAT, SECOND, record))
        on_default = S.floats(observation_of(self, S.FLAT, DEFAULT, record))
        unnamed = S.floats(self.flat(record))
        self.assertEqual(
            len(on_default), S.DECLARED[S.FLAT]["shape"][0],
            "the default shape's dense observation is the 203 slots it always was "
            "(shapes.md §5, §8): %d" % (len(on_default),),
        )
        self.assertEqual(
            (len(on_second), len(on_default)),
            (S.DECLARED_BY_SHAPE[SECOND][S.FLAT][0], S.DECLARED[S.FLAT]["shape"][0]),
            "the two shapes' dense observations are their own widths -- 131 + 3 x 66 = "
            "329 and 131 + 3 x 24 = 203 -- because the history block's capacity is the "
            "shape's, and the 131 slots before it are one table (shapes.md §8, ASM-42, "
            "ASM-44): %d against %d" % (len(on_second), len(on_default)),
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
                    "the %r block is %d slots on both shapes (shapes.md §2, §8)"
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
            on_second[:len(on_default)], on_default,
            "and the second shape's observation is its own: one readout at both shapes' "
            "normalisers cannot encode the same (shapes.md §2): %r" % (on_second[:8],),
        )
        self.assert_floats(
            on_second[S.FIXED_FLAT_SLOTS:], [0.0] * (3 * S.CAPACITY[SECOND]),
            "the extra slots the second shape declares are its history block and nothing "
            "else -- 3 x 66 = 198 of them, all zero for an empty history -- so the shape "
            "widens the block and adds no other (shapes.md §8, ASM-42): %r"
            % (on_second[S.FIXED_FLAT_SLOTS:][:6],),
        )


class FEA8TokenLadders(S.FeaturesCase):
    """The token encoding's five bucket ladders are the shape's too."""

    def test_fea8_30_the_token_ladders_are_the_shapes(self):
        """FEA-8.30 on no-limit-100 stacks=(96, 5) bucket to ids (84, 77), pot 151 to 76,
        to_call 11 to 67 and limit=(26, 6) to (88, 92); the same amounts on the default
        shape bucket by the default tables -- (84, 79), 76, 68 and (88, 92) -- and every
        id either shape emits stays inside its own block's id range, which does not move
        between shapes; the two observations are their own token counts, 82 against 40,
        while the sixteen tokens of the laddered blocks and the vocabulary of 96 are the
        same on both (surface.md §6, shapes.md §2, §8, card-tokens.md §4, ASM-42)."""
        block = {field: (offset, width) for field, offset, width in S.TOKEN_BLOCKS}
        record = S.readout(stacks=(96, 5), pot=151, to_call=11, limit=(26, 6))
        on_second = S.ints(observation_of(self, S.TOKENS, SECOND, record))
        on_default = S.ints(observation_of(self, S.TOKENS, DEFAULT, record))
        self.assertEqual(
            (len(on_second), len(on_default)),
            (S.DECLARED_BY_SHAPE[SECOND][S.TOKENS][0], S.DECLARED[S.TOKENS]["shape"][0]),
            "the two shapes' token observations are their own counts -- 16 + 66 = 82 and "
            "16 + 24 = 40 -- because the history block's capacity is the shape's, and the "
            "16 tokens before it are one table (shapes.md §8, ASM-42, ASM-44): %d against %d"
            % (len(on_second), len(on_default)),
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
                    "the %r block is %d tokens on both shapes (shapes.md §2, §8)"
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
            on_second[:len(on_default)], on_default,
            "the two shapes' token observations are their own bucket tables: one amount "
            "set cannot encode the same (shapes.md §2): %r" % (on_second[10:16],),
        )
        self.assert_ints(
            on_second[S.FIXED_TOKEN_SLOTS:], [S.PAD] * S.CAPACITY[SECOND],
            "the extra tokens the second shape declares are its history block and nothing "
            "else -- 66 pads for an empty history -- so the shape widens the block and "
            "moves no ladder (shapes.md §8, card-tokens.md §5): %r"
            % (on_second[S.FIXED_TOKEN_SLOTS:][:6],),
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
                    self.shape_of(dense), S.DECLARED_BY_SHAPE[SECOND][S.FLAT],
                    "the dense observation of the second shape is its own width, 131 + 3 "
                    "x 66 = 329 (surface.md §5, §6, shapes.md §8, ASM-42): %r"
                    % (self.shape_of(dense),),
                )
                self.assertEqual(
                    self.shape_of(tokens), S.DECLARED_BY_SHAPE[SECOND][S.TOKENS],
                    "the token observation of the second shape is its own count, 16 + 66 "
                    "= 82 (surface.md §5, §6, shapes.md §8, ASM-42): %r"
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


class FEA8ThirdShapeNumbers(S.FeaturesCase):
    """All three declared rows, and the five numbers each one declares."""

    #: The three rows' five numbers, as the design states them (capacity.md §2, §4,
    #: shapes.md §2-§3, §5, seats.md §2-§3, ASM-42, ASM-44).
    WANTED = {
        S.DEFAULT_SHAPE: {
            "seats": 2, "capacity": 24, "flat": 203, "tokens": 40,
            "vocabulary": 96, "indices": 3,
        },
        S.SECOND_SHAPE: {
            "seats": 2, "capacity": 66, "flat": 329, "tokens": 82,
            "vocabulary": 96, "indices": 6,
        },
        S.THIRD_SHAPE: {
            "seats": 6, "capacity": 98, "flat": 433, "tokens": 122,
            "vocabulary": 102, "indices": 6,
        },
    }

    def test_fea8_36_all_three_rows_declare_their_widths_vocabulary_seats_and_capacity(self):
        """FEA-8.36 for each declared row the two encoders declare that row's widths --
        203/329/433 dense and 40/82/122 tokens -- the token encoder declares that row's
        vocabulary (96 on the two-seat rows, 102 on the six-seat one), the row's seat
        count and capacity are the 2/2/6 and 24/66/98 the widths are built from, the
        block arithmetic is `127 + 2 x seats + 3 x capacity` and `12 + 2 x seats +
        capacity`, its action_space publishes the row's 3 or 6 indices, a readout of the
        row's own seat count encodes at that width, and a history of exactly the capacity
        encodes while one entry more is refused naming the field, the capacity and the
        count, on both encodings (capacity.md §2-§3, shapes.md §2, §3, §5, §8,
        seats.md §2-§3, flat-numeric.md §5, card-tokens.md §5-§6, ASM-42, ASM-44)."""
        F = self.surface()
        for shape, wanted in self.WANTED.items():
            seats, capacity = wanted["seats"], wanted["capacity"]
            with self.subTest(shape=shape):
                self.assertEqual(
                    (S.SEATS[shape], S.CAPACITY[shape]), (seats, capacity),
                    "the row's seat count and capacity are its own: %d seats and %d "
                    "history slots (seats.md §2-§3, capacity.md §2, ASM-42, ASM-44)"
                    % (seats, capacity),
                )
                self.assertEqual(
                    (wanted["flat"], wanted["tokens"]),
                    (S.SEAT_INVARIANT_FLAT_SLOTS + 2 * seats + 3 * capacity,
                     S.SEAT_INVARIANT_TOKEN_SLOTS + 2 * seats + capacity),
                    "127 + 2 x %d + 3 x %d = %d dense and 12 + 2 x %d + %d = %d tokens: "
                    "the 127 dense and 12 token slots no seat count touches, the two "
                    "per-seat blocks one slot per seat, and the history block 3 x "
                    "capacity / capacity (capacity.md §2, ASM-44)"
                    % (seats, capacity, wanted["flat"], seats, capacity,
                       wanted["tokens"]),
                )
                self.assertEqual(
                    (S.flat_width(shape), S.token_width(shape)),
                    (wanted["flat"], wanted["tokens"]),
                    "the width arithmetic and the declared widths are one statement "
                    "(capacity.md §2): %r"
                    % ((S.flat_width(shape), S.token_width(shape)),),
                )
                record = S.shaped_readout(shape)
                self.assertEqual(
                    len(record["stacks"]), seats,
                    "the battery's readout of %r holds one stack per seat, so the "
                    "per-seat blocks are that row's width (seats.md §3, ASM-44): %r"
                    % (shape, record["stacks"]),
                )
                for name in S.ENCODINGS:
                    with self.subTest(shape=shape, encoding=name):
                        encoder = self.ep("build_encoder")(name, shape=shape)
                        spec = self.ep("observation_spec")(encoder)
                        width = wanted["flat"] if name == S.FLAT else wanted["tokens"]
                        self.assertEqual(
                            tuple(spec["shape"]), (width,),
                            "the %r encoder on %r declares that row's one-dimension width "
                            "of %d (capacity.md §2, surface.md §5): %r"
                            % (name, shape, width, spec["shape"]),
                        )
                        self.assertEqual(
                            tuple(spec["shape"]), S.DECLARED_BY_SHAPE[shape][name],
                            "and it is the width the battery's table carries: %r against "
                            "%r" % (tuple(spec["shape"]),
                                    S.DECLARED_BY_SHAPE[shape][name]),
                        )
                        if name == S.TOKENS:
                            self.assertEqual(
                                int(spec["vocabulary"]), wanted["vocabulary"],
                                "the token vocabulary is the shape's: %d ids on %r, six "
                                "seat ids above every id the two-seat rows use "
                                "(card-tokens.md §6, seats.md §3, ASM-44): %r"
                                % (wanted["vocabulary"], shape, spec["vocabulary"]),
                            )
                        else:
                            self.assertIsNone(
                                spec["vocabulary"],
                                "the dense encoding declares no vocabulary on any row "
                                "(encodings.md §4, surface.md §5): %r"
                                % (spec["vocabulary"],),
                            )
                        observation = self.ep("encode")(encoder, record)
                        self.assertEqual(
                            self.shape_of(observation), (width,),
                            "a readout of the row's own seat count encodes to the row's "
                            "declared width (surface.md §6, capacity.md §2): %r"
                            % (self.shape_of(observation),),
                        )
                self.assertEqual(
                    list(self.ep("action_space")(shape=shape)),
                    list(range(wanted["indices"])),
                    "the row's vocabulary is %d indices, its head width's own count "
                    "(shapes.md §3, vocabulary.md §1): %r"
                    % (wanted["indices"], list(self.ep("action_space")(shape=shape))),
                )
                history = S.history_entries(capacity)
                self.assertEqual(
                    len(history), capacity,
                    "the battery builds a history of exactly the row's capacity "
                    "(capacity.md §1, §3): %d entries" % (len(history),),
                )
                for name in S.ENCODINGS:
                    with self.subTest(shape=shape, encoding=name, entries=capacity):
                        encoder = self.ep("build_encoder")(name, shape=shape)
                        observation = self.ep("encode")(
                            encoder, S.shaped_readout(shape, history=history))
                        self.assertEqual(
                            len(observation),
                            wanted["flat"] if name == S.FLAT else wanted["tokens"],
                            "a history of exactly the capacity encodes, and the "
                            "observation is still the declared width (capacity.md §3, "
                            "ASM-42): %d" % (len(observation),),
                        )
                        exc = self.refuses(
                            self.ep("encode"), encoder,
                            S.shaped_readout(shape,
                                             history=S.history_entries(capacity + 1)),
                            words=("encode", "history", str(capacity),
                                   str(capacity + 1)),
                        )
                        self.assertIn(
                            str(capacity), str(exc),
                            "the refusal names the capacity it was measured against, so "
                            "a caller learns how long this row's history may be "
                            "(capacity.md §3, errors.md §3): %r" % (str(exc),),
                        )
                last = S.shaped_readout(
                    shape, seat=(seats - 1, True),
                    stacks=tuple(range(seats)))
                for name in S.ENCODINGS:
                    with self.subTest(shape=shape, encoding=name, seat=seats - 1):
                        self.ep("encode")(
                            self.ep("build_encoder")(name, shape=shape), last)
        self.assertEqual(
            [record["name"] for record in
             self.ep("action_space")(shape=S.THIRD_SHAPE).values()],
            list(SECOND_VOCABULARY),
            "the six-seat row declares the uncapped row's six descriptors, index for "
            "index: a seat count adds no descriptor, it changes the price of aggression "
            "(shapes.md §3, seats.md §2, D-33)",
        )


class FEA8SixSeatSeatBlocks(S.FeaturesCase):
    """The six-seat row's two seat blocks: a one-hot dense, six own ids in the tokens."""

    def test_fea8_37_the_six_seat_dense_seat_block_is_a_one_hot_and_its_token_block_six_ids(self):
        """FEA-8.37 on `six-seat-no-limit-100` the dense seat block is the acting seat's
        one-hot over the six seats -- seat index i sets slot `4 + i` to 1.0 and the other
        five to 0.0 -- and the token seat block is six tokens, the acting seat's slot
        holding `96 + i` and the other five the pad 0, so the row emits ids 96-101 above
        every id the two-seat rows use and its vocabulary of 102 covers all six (seats.md
        §3, flat-numeric.md §4, card-tokens.md §3, §6, capacity.md §4, ASM-44)."""
        F = self.surface()
        dense_blocks = S.THIRD_FLAT_BLOCKS
        token_blocks = S.THIRD_TOKEN_BLOCKS
        dense_offset = {field: offset for field, offset, _width in dense_blocks}
        token_offset = {field: offset for field, offset, _width in token_blocks}
        dense_width = dense_blocks[1][2]
        token_count = token_blocks[1][2]
        self.assertEqual(
            (dense_width, token_count, dense_offset["seat"], token_offset["seat"]),
            (6, 6, 4, 1),
            "the row's two seat blocks are six slots wide, at dense slot 4 and token 1 "
            "(capacity.md §2, seats.md §3): %r"
            % ((dense_width, token_count, dense_offset["seat"], token_offset["seat"]),),
        )
        seen = set()
        for index in range(S.SEATS[S.THIRD_SHAPE]):
            for flag in (True, False):
                record = S.six_seat_readout(seat=(index, flag))
                with self.subTest(seat=(index, flag)):
                    dense = S.floats(observation_of(self, S.FLAT, S.THIRD_SHAPE, record))
                    block = dense[dense_offset["seat"]:
                                  dense_offset["seat"] + dense_width]
                    self.assert_floats(
                        block,
                        [1.0 if position == index else 0.0
                         for position in range(dense_width)],
                        "the dense seat block of seat index %d: its one-hot over six "
                        "seats, the flag carried nowhere in this block (seats.md §3, "
                        "flat-numeric.md §4)" % (index,),
                    )
                    self.assertEqual(
                        sum(1 for value in block if value != 0.0), 1,
                        "exactly one seat slot is live, so the block is a one-hot "
                        "(flat-numeric.md §4): %r" % (block,),
                    )
                    tokens = S.ints(observation_of(self, S.TOKENS, S.THIRD_SHAPE, record))
                    ids = tokens[token_offset["seat"]:
                                 token_offset["seat"] + token_count]
                    expected = [S.SEAT_TOKEN_BASE + index
                                if position == index else S.PAD
                                for position in range(token_count)]
                    self.assert_ints(
                        ids, expected,
                        "the token seat block of seat index %d: 96 + the seat slot, the "
                        "pad in the other five (card-tokens.md §3, seats.md §3)"
                        % (index,),
                    )
                    self.assertEqual(
                        [ident for ident in ids if ident != S.PAD], [96 + index],
                        "the acting seat's own id and no other: the row's six ids are "
                        "96-101, one per seat slot (card-tokens.md §3, ASM-44): %r"
                        % (ids,),
                    )
                    seen.add(ids[index])
        self.assertEqual(
            tuple(sorted(seen)), S.SIX_SEAT_SEAT_IDS,
            "all six of the row's seat ids 96-101 are reachable, one per seat slot "
            "(seats.md §3, ASM-44): %r" % (tuple(sorted(seen)),),
        )
        self.assertEqual(
            S.VOCABULARY_BY_SHAPE[S.THIRD_SHAPE], 102,
            "the vocabulary of 102 covers ids 0-101, so the six seat ids are inside it "
            "(card-tokens.md §6, capacity.md §4): %r"
            % (S.VOCABULARY_BY_SHAPE[S.THIRD_SHAPE],),
        )
        self.assertEqual(
            max(S.SIX_SEAT_SEAT_IDS), S.VOCABULARY_BY_SHAPE[S.THIRD_SHAPE] - 1,
            "the row's top id is 101, the last id its vocabulary of 102 carries "
            "(card-tokens.md §6, ASM-44): %r"
            % (max(S.SIX_SEAT_SEAT_IDS),),
        )
        for shape in S.SHAPES:
            with self.subTest(shape=shape, ids="57-60"):
                record = S.readout(seat=(1, False))
                tokens = S.ints(observation_of(self, S.TOKENS, shape, record))
                offset = {field: position for field, position, _width
                          in S.TOKEN_BLOCKS_BY_SHAPE[shape]}["seat"]
                self.assert_ints(
                    tokens[offset:offset + 2], [58, 59],
                    "a two-seat row still writes 57 + index then 59 + flag: the six "
                    "seat ids are the third row's own and rename nothing (card-tokens.md "
                    "§3, seats.md §3, ASM-44): %r" % (tokens[offset:offset + 2],),
                )


class FEA8SixSeatStacksBlocks(S.FeaturesCase):
    """The six-seat row's stacks blocks are one slot per seat, in seat order."""

    def test_fea8_38_the_six_seat_stacks_block_is_one_slot_per_seat_in_seat_order(self):
        """FEA-8.38 on `six-seat-no-limit-100` the dense stacks block is six slots, one
        per seat in seat order, each divided by the row's 100, and the token stacks block
        is six buckets in the same seat order over the row's own ladder -- neither block
        follows the acting seat, so the same stacks read the same on any seat (seats.md
        §3, flat-numeric.md §4, card-tokens.md §4, capacity.md §4, ASM-44)."""
        F = self.surface()
        stacks = (100, 96, 80, 60, 40, 5)
        dense_offset = {field: offset for field, offset, _width
                        in S.THIRD_FLAT_BLOCKS}["stacks"]
        token_offset = {field: offset for field, offset, _count
                        in S.THIRD_TOKEN_BLOCKS}["stacks"]
        self.assertEqual(
            (dense_offset, token_offset), (129, 14),
            "the six-seat stacks blocks start at dense slot 129 and token 14, after the "
            "six-wide seat block and the 34/85 or 2/5 card blocks (capacity.md §2, "
            "seats.md §3): %r" % ((dense_offset, token_offset),),
        )
        for index in range(S.SEATS[S.THIRD_SHAPE]):
            record = S.six_seat_readout(seat=(index, index != 0), stacks=stacks)
            with self.subTest(seat=index):
                dense = S.floats(observation_of(self, S.FLAT, S.THIRD_SHAPE, record))
                self.assert_floats(
                    dense[dense_offset:dense_offset + S.SEATS[S.THIRD_SHAPE]],
                    [amount / 100.0 for amount in stacks],
                    "the dense stacks block of seat %d is the six stacks in seat order, "
                    "each over the row's 100: the acting seat does not move them "
                    "(flat-numeric.md §4, seats.md §3)" % (index,),
                )
                tokens = S.ints(observation_of(self, S.TOKENS, S.THIRD_SHAPE, record))
                self.assert_ints(
                    tokens[token_offset:token_offset + S.SEATS[S.THIRD_SHAPE]],
                    [S.bucket_on(S.THIRD_SHAPE, "stacks", amount) for amount in stacks],
                    "the token stacks block of seat %d is the six buckets in seat order "
                    "over the six-seat row's ladder -- 5, 10, 20, 40, 60, 80, 95, 100+ -- "
                    "and never the acting seat's first (card-tokens.md §4, seats.md §3)"
                    % (index,),
                )
        with self.subTest(seat="moved", case="same stacks"):
            first = S.six_seat_readout(seat=(0, True), stacks=stacks)
            last = S.six_seat_readout(seat=(5, False), stacks=stacks)
            self.assert_floats(
                S.floats(observation_of(self, S.FLAT, S.THIRD_SHAPE, first))[
                    dense_offset:dense_offset + 6],
                S.floats(observation_of(self, S.FLAT, S.THIRD_SHAPE, last))[
                    dense_offset:dense_offset + 6],
                "one stacks tuple reads the same on seat 0 and seat 5: the six-seat "
                "block is the readout's seat order and not the acting seat's "
                "(flat-numeric.md §4, card-tokens.md §4, ASM-44)",
            )
        for shape in S.SHAPES:
            with self.subTest(shape=shape, order="actor-first"):
                record = S.readout(seat=(1, False), stacks=(3, 10))
                dense = S.floats(observation_of(self, S.FLAT, shape, record))
                offset = {field: position for field, position, _width
                          in S.FLAT_BLOCKS_BY_SHAPE[shape]}["stacks"]
                divisor = 20.0 if shape == S.DEFAULT_SHAPE else 100.0
                self.assert_floats(
                    dense[offset:offset + 2], [10 / divisor, 3 / divisor],
                    "a two-seat row still writes the acting seat's stack then the "
                    "other's -- seat 1's 10 then seat 0's 3, over that row's divisor: the "
                    "third row's seat-order mode is its own (flat-numeric.md §4, "
                    "seats.md §3, ASM-44): %r" % (dense[offset:offset + 2],),
                )


class FEA8SixSeatPotLadder(S.FeaturesCase):
    """The six-seat pot ladder, at every edge and the value either side of it."""

    def test_fea8_39_the_six_seat_pot_ladder_is_re_edged_for_600_chips(self):
        """FEA-8.39 the six-seat pot ladder's edges are 12, 24, 48, 96, 192, 300 and 450
        -- exactly three times `no-limit-100`'s -- so a pot at an edge takes that
        bucket's id, the value one past it takes the next, and the seven ids 69-76 are
        the ones every row emits: the pot is re-edged because 600 chips in play make a
        divisor of 200 a clip, and no id is renamed (card-tokens.md §4, capacity.md §2,
        §4, seats.md §2, sizing.md §5, ASM-39, ASM-44)."""
        F = self.surface()
        ladder = (
            (12, 69), (24, 70), (48, 71), (96, 72), (192, 73), (300, 74), (450, 75),
            (None, 76),
        )
        self.assertEqual(
            ladder, S.SIX_SEAT_LADDERS["pot"],
            "the six-seat pot ladder is 12, 24, 48, 96, 192, 300, 450 and then "
            "unbounded (card-tokens.md §4, capacity.md §2): %r"
            % (S.SIX_SEAT_LADDERS["pot"],),
        )
        self.assertEqual(
            [bound for bound, _ident in ladder[:-1]],
            [3 * bound for bound, _ident in S.SECOND_LADDERS["pot"][:-1]],
            "each edge is exactly three times the two-seat uncapped row's, the ratio of "
            "the two games' chips in play -- 200 against 600 (capacity.md §2, "
            "sizing.md §5): %r" % ([bound for bound, _ident in ladder[:-1]],),
        )
        self.assertEqual(
            sorted({ident for _bound, ident in ladder}),
            S.ladder_ids("pot"),
            "the seven pot ids 69-76 are the same ids on every row: only the edges move "
            "(card-tokens.md §4, shapes.md §5): %r against %r"
            % (sorted({ident for _bound, ident in ladder}), S.ladder_ids("pot")),
        )
        offset = {field: position for field, position, _count
                  in S.THIRD_TOKEN_BLOCKS}["pot"]
        probes = (0, 11, 12, 13, 23, 24, 25, 47, 48, 49, 95, 96, 97, 191, 192, 193,
                  299, 300, 301, 449, 450, 451, 600)
        for pot in probes:
            with self.subTest(pot=pot):
                record = S.six_seat_readout(pot=pot)
                values = S.ints(observation_of(self, S.TOKENS, S.THIRD_SHAPE, record))
                expected = S.bucket_on(S.THIRD_SHAPE, "pot", pot)
                self.assertEqual(
                    values[offset], expected,
                    "a pot of %r takes the id the six-seat row's ladder fixes "
                    "(card-tokens.md §4, capacity.md §2): %r, expected %r"
                    % (pot, values[offset], expected),
                )
                self.assertIn(
                    values[offset], S.ladder_ids("pot"),
                    "and that id is one of the seven 69-76 every row emits "
                    "(card-tokens.md §4, ASM-44): %r" % (values[offset],),
                )
        for edge, ident in ladder[:-1]:
            with self.subTest(edge=edge, at="edge"):
                self.assertEqual(
                    S.bucket_on(S.THIRD_SHAPE, "pot", edge), ident,
                    "the pot at the edge %r is inside that bucket (card-tokens.md §4, "
                    "capacity.md §2): %r" % (edge, S.bucket_on(S.THIRD_SHAPE, "pot", edge)),
                )
            with self.subTest(edge=edge, at="edge+1"):
                self.assertNotEqual(
                    S.bucket_on(S.THIRD_SHAPE, "pot", edge + 1), ident,
                    "one chip past the edge %r is the next bucket, so each edge is a real "
                    "boundary and not a coincidence (card-tokens.md §4): %r"
                    % (edge, S.bucket_on(S.THIRD_SHAPE, "pot", edge + 1)),
                )
                self.assertNotEqual(
                    S.bucket_on(S.SECOND_SHAPE, "pot", edge),
                    S.bucket_on(S.THIRD_SHAPE, "pot", edge),
                    "the same pot of %r buckets differently on the two uncapped rows, "
                    "because the pot ladder is the shape's (card-tokens.md §4, "
                    "capacity.md §2): %r against %r"
                    % (edge, S.bucket_on(S.SECOND_SHAPE, "pot", edge),
                       S.bucket_on(S.THIRD_SHAPE, "pot", edge)),
                )


class FEA8TwoSeatRowsUnmoved(S.FeaturesCase):
    """The two two-seat rows are unchanged: records, offsets and values."""

    def test_fea8_40_the_two_two_seat_rows_are_unmoved_value_for_value(self):
        """FEA-8.40 the two two-seat rows keep today's observations and block offsets:
        the dense offsets are `0, 4, 6, 40, 125, 127, 128, 129, 131` on both, the token
        offsets `0, 1, 3, 5, 10, 12, 13, 14, 16`, the widths 203/329 dense and 40/82
        tokens over 96 ids, the dense seat block `[index, flag]`, the dense stacks block
        `[stacks[i] / d, stacks[1 - i] / d]` and the token seat block `[57 + index,
        59 + flag]` with two stack buckets in seat order -- so the third row adds a shape
        and moves neither of the other two (shapes.md §5, §8, seats.md §3, capacity.md
        §4, flat-numeric.md §4, §5, card-tokens.md §3, §5, ASM-44, D-29)."""
        dense_offsets = (0, 4, 6, 40, 125, 127, 128, 129, 131)
        token_offsets = (0, 1, 3, 5, 10, 12, 13, 14, 16)
        rows = {
            S.DEFAULT_SHAPE: {
                "flat": (203, [0, 4, 6, 40, 125, 127, 128, 129, 131],
                         [("street", 0, 4), ("seat", 4, 2), ("hole", 6, 34),
                          ("board", 40, 85), ("stacks", 125, 2), ("pot", 127, 1),
                          ("to_call", 128, 1), ("limit", 129, 2),
                          ("history", 131, 72)]),
                "tokens": (40, [0, 1, 3, 5, 10, 12, 13, 14, 16],
                           [("street", 0, 1), ("seat", 1, 2), ("hole", 3, 2),
                            ("board", 5, 5), ("stacks", 10, 2), ("pot", 12, 1),
                            ("to_call", 13, 1), ("limit", 14, 2),
                            ("history", 16, 24)]),
                "divisor": 20.0, "pot": 40.0, "to_call": 20.0,
                "amount": 4.0, "count": 4.0,
            },
            S.SECOND_SHAPE: {
                "flat": (329, [0, 4, 6, 40, 125, 127, 128, 129, 131],
                         [("street", 0, 4), ("seat", 4, 2), ("hole", 6, 34),
                          ("board", 40, 85), ("stacks", 125, 2), ("pot", 127, 1),
                          ("to_call", 128, 1), ("limit", 129, 2),
                          ("history", 131, 198)]),
                "tokens": (82, [0, 1, 3, 5, 10, 12, 13, 14, 16],
                           [("street", 0, 1), ("seat", 1, 2), ("hole", 3, 2),
                            ("board", 5, 5), ("stacks", 10, 2), ("pot", 12, 1),
                            ("to_call", 13, 1), ("limit", 14, 2),
                            ("history", 16, 66)]),
                "divisor": 100.0, "pot": 200.0, "to_call": 100.0,
                "amount": 100.0, "count": 50.0,
            },
        }
        record = S.readout(street="flop", seat=(1, False), hole=("2c", "Td"),
                           board=("Jh", "7c", "2d"), stacks=(17, 5), pot=6,
                           to_call=0, limit=(2, 0), history=S.history_entries(2))
        for shape, row in rows.items():
            with self.subTest(shape=shape):
                for key, name in (("flat", S.FLAT), ("tokens", S.TOKENS)):
                    with self.subTest(shape=shape, encoding=name):
                        width, offsets, table = row[key]
                        actual = S.FLAT_BLOCKS_BY_SHAPE[shape] if name == S.FLAT \
                            else S.TOKEN_BLOCKS_BY_SHAPE[shape]
                        self.assertEqual(
                            actual, tuple(table),
                            "the %r block table of %r is the one it always was, field "
                            "for field, offset for offset and width for width (shapes.md "
                            "§8, ASM-44): %r" % (name, shape, actual),
                        )
                        self.assertEqual(
                            tuple(offset for _field, offset, _width in actual),
                            tuple(offsets),
                            "its offsets are %r (flat-numeric.md §2, card-tokens.md §2): "
                            "%r" % (offsets,
                                    tuple(offset for _field, offset, _width in actual)),
                        )
                        self.assertEqual(
                            sum(width for _field, _offset, width in actual), width,
                            "and its widths sum to the declared %d (encoder.md §4): %d"
                            % (width, sum(width for _f, _o, width in actual)),
                        )
                        self.assertEqual(
                            tuple(self.ep("observation_spec")(
                                self.ep("build_encoder")(name, shape=shape))["shape"]),
                            (width,),
                            "the record is the declared %d, unmoved (surface.md §5, "
                            "shapes.md §5): %r"
                            % (width, self.ep("observation_spec")(
                                self.ep("build_encoder")(name, shape=shape))["shape"]),
                        )
                        if name == S.TOKENS:
                            self.assertEqual(
                                int(self.ep("observation_spec")(
                                    self.ep("build_encoder")(name, shape=shape))[
                                        "vocabulary"]), 96,
                                "the two-seat rows still declare 96 ids: the six seat ids "
                                "96-101 are the third row's and rename nothing "
                                "(card-tokens.md §6, seats.md §3, ASM-44)",
                            )
                        observation = observation_of(self, name, shape, record)
                        self.assertEqual(
                            len(observation), width,
                            "and one observation of %r is %d wide (surface.md §6): %d"
                            % (shape, width, len(observation)),
                        )
                dense = S.floats(observation_of(self, S.FLAT, shape, record))
                self.assert_floats(
                    dense[4:6], [1.0, 0.0],
                    "the dense seat block of seat 1 without the button is still "
                    "[index, flag] = [1.0, 0.0], not a six-wide one-hot (flat-numeric.md "
                    "§4, seats.md §3): %r" % (dense[4:6],),
                )
                self.assert_floats(
                    dense[125:127], [5 / row["divisor"], 17 / row["divisor"]],
                    "the dense stacks block is still the acting seat's stack then the "
                    "other's: seat 1's 5 then seat 0's 17 (flat-numeric.md §4, "
                    "ASM-44): %r" % (dense[125:127],),
                )
                self.assert_floats(
                    dense[127:128], [6 / row["pot"]],
                    "the pot is still divided by %r (flat-numeric.md §4, shapes.md §2): "
                    "%r" % (row["pot"], dense[127:128]),
                )
                self.assert_floats(
                    dense[128:129], [0 / row["to_call"]],
                    "and to_call by %r (flat-numeric.md §4, shapes.md §2): %r"
                    % (row["to_call"], dense[128:129]),
                )
                self.assert_floats(
                    dense[129:131], [2 / row["amount"], 0 / row["count"]],
                    "and the limit pair by %r and %r (flat-numeric.md §4, shapes.md §2): "
                    "%r" % (row["amount"], row["count"], dense[129:131]),
                )
                self.assert_floats(
                    dense[131:],
                    S.history_block(record["history"], S.CAPACITY[shape]),
                    "the history block stays at 131 and is 3 x the row's capacity "
                    "(flat-numeric.md §5, capacity.md §2)",
                )
                tokens = S.ints(observation_of(self, S.TOKENS, shape, record))
                self.assert_ints(
                    tokens[1:3], [58, 59],
                    "the token seat block is still 57 + index then 59 + flag "
                    "(card-tokens.md §3, seats.md §3): %r" % (tokens[1:3],),
                )
                self.assert_ints(
                    tokens[10:12],
                    [S.bucket_on(shape, "stacks", 17),
                     S.bucket_on(shape, "stacks", 5)],
                    "and the two stack tokens are still stacks[0] then stacks[1] in seat "
                    "order, over that row's ladder (card-tokens.md §4): %r"
                    % (tokens[10:12],),
                )
                self.assert_ints(
                    tokens[16:], S.history_tokens(record["history"], S.CAPACITY[shape]),
                    "with the history block still the last `capacity` tokens "
                    "(card-tokens.md §5, capacity.md §2)",
                )
        self.assertEqual(
            (S.SEATS[S.DEFAULT_SHAPE], S.SEATS[S.SECOND_SHAPE]), (2, 2),
            "the two two-seat rows keep two seats, so their per-seat blocks keep today's "
            "two slots and today's modes (seats.md §3, ASM-44): %r"
            % ((S.SEATS[S.DEFAULT_SHAPE], S.SEATS[S.SECOND_SHAPE]),),
        )
        self.assertEqual(
            tuple(dense_offsets), tuple(offset for _field, offset, _width in S.FLAT_BLOCKS),
            "the default row's dense offsets are today's %r (flat-numeric.md §2, "
            "shapes.md §5): %r" % (dense_offsets,
                                  tuple(offset for _f, offset, _w in S.FLAT_BLOCKS)),
        )
        self.assertEqual(
            tuple(token_offsets), tuple(offset for _field, offset, _width in S.TOKEN_BLOCKS),
            "and its token offsets today's %r (card-tokens.md §2, shapes.md §5): %r"
            % (token_offsets,
               tuple(offset for _f, offset, _w in S.TOKEN_BLOCKS)),
        )


if __name__ == "__main__":
    unittest.main()
