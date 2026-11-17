"""FEA-12 -- the declared tenth block: `strength`, the fact the readout does not carry.

``docs/L1/strength-design.md`` §A (the fact), §F.2 (this battery); ``ASM-46``, ``ASM-48``;
``docs/L2/features/surface.md`` §4-§6; ``docs/L3/features/encoder.md`` §4-§5;
``docs/L3/features/errors.md`` §2-§3.

A supervised estimator's win probability for the decision's own deal is a **declared
field with an injected value**: it is a deterministic function of `hole` and `board`, so
it widens no information set, and it is not a readout fact.  `build_encoder` gains an
optional keyword naming one of the axis' two members: its **absence** is today's
declaration byte for byte -- 203/329/433, 40/82/122, over 96 and 102 ids -- and any other
member appends **one block after the history block**, so every pre-existing offset is
untouched and only the width grows by one.

Eight cases hold it:

* FEA-12.1 the block is the **last** of both encodings on all three rows, its offset is
  the pre-change width and its width one, and no earlier block moves;
* FEA-12.2 the dense slot carries `p` exactly, and a value outside `[0, 1]` -- or a
  non-finite one -- is refused **by name**, never clamped;
* FEA-12.3 the token slot is one id of the eight-band ladder, the ladder is total, no band
  emits the pad, and the vocabulary is 110 on every row;
* FEA-12.4 a declaring encoder refuses a readout carrying no `strength` -- the
  anti-silence assertion;
* FEA-12.5 the fields are the nine or the ten with `strength` last, the block count equals
  the field count, and the spec keys are the six on both;
* FEA-12.6 the bound table covers the two new tags and the strength-on declaration
  partitions its width exactly as the absence one does;
* FEA-12.7 the era guard: the absence declaration is the record this change found;
* FEA-12.8 an uncatalogued member is refused by name, and `None` is the absence.

No case asserts an exception class (``errors.md`` §2).  Every number below is the
design's and none is re-derived from the module's own arithmetic.
"""

import importlib
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


#: The five probabilities FEA-12.2 carries through the dense slot, and the exact value the
#: design fixes for each (`0.87` is not representable in binary, so the slot holds the
#: float32 the writer was handed and the comparison is to that).
DENSE_VALUES = (0.0, 0.25, 0.5, 0.87, 1.0)

#: The values FEA-12.2 refuses, and the words its refusal must name (`errors.md` §3).
REFUSED_VALUES = (-0.01, 1.01, float("nan"), float("inf"), float("-inf"))

#: FEA-12.3's ladder, as `(value, id)` pairs: the two ends of a band, a value one
#: thousandth past an edge, and the interval's two ends (`ASM-48`).
LADDER_CASES = (
    (0.0, 102),
    (0.05, 102),
    (0.051, 103),
    (0.30, 105),
    (0.61, 108),
    (1.0, 109),
)


class FEA12Case(S.FeaturesCase):
    """The calls this battery is written in, and the one declared exception it makes."""

    def strength_encoder(self, name=S.FLAT, shape=None, member=S.STRENGTH_ON):
        """One encoder declaring the strength member, on one shape."""
        build = self.ep("build_encoder")
        return build(name, shape=shape, strength=member)

    def observation(self, name=S.FLAT, shape=None, member=S.STRENGTH_ON, strength=None):
        """One observation of an invented readout, through the declaring encoder.

        `strength` is handed over as the readout's `extra` key -- the injection the
        harness writes -- so no case builds the readout by hand and the battery keeps
        using `_features_support.readout`'s own builder (`ASM-47`).
        """
        extra = {} if strength is None else {S.STRENGTH_FIELD: strength}
        encoder = self.strength_encoder(name, shape, member)
        return self.ep("encode")(encoder, S.shaped_readout(shape, extra=extra))

    def declaration(self, encoding, shape=None, member=S.STRENGTH_ON):
        """The block table of one declaration -- FEA-12.1's and FEA-12.6's subject.

        The battery's promise to reach only the declared names has one declared exception
        already (FEA-11.1 reads `declarations.bounds()` and `encode.WRITERS`, because
        "no slot is outside a declared bound" is a statement about the declaration).  This
        is the second: the **block table** is what says which block is last and where it
        starts, and no call returns it.  Nothing here asserts a private spelling -- the
        records' six-tuple shape is `encoder.md` §4's -- and a table that is not there is
        one clean `SurfaceAbsent`.
        """
        S.module()
        try:
            layouts = importlib.import_module("features.declarations")
        except Exception as exc:
            raise S.SurfaceAbsent(
                "surface absent: features.declarations is not importable (%s: %s)"
                % (type(exc).__name__, exc)
            ) from exc
        build = getattr(layouts, "declaration", None)
        if build is None:
            raise S.SurfaceAbsent(
                "the layout declares no `declaration`: features.declarations.declaration "
                "is the one table both encodings are rows of (encoder.md §4)"
            )
        return build(encoding, shape, strength=member)

    def bound_table(self):
        """`features.declarations.bounds()` -- FEA-12.6's subject, for FEA-11.1's reason."""
        S.module()
        try:
            layouts = importlib.import_module("features.declarations")
        except Exception as exc:
            raise S.SurfaceAbsent(
                "surface absent: features.declarations is not importable (%s: %s)"
                % (type(exc).__name__, exc)
            ) from exc
        bound_of = getattr(layouts, "bounds", None)
        if bound_of is None:
            raise S.SurfaceAbsent(
                "the layout declares no bound table: features.declarations.bounds is what "
                "says every block's values end at a declared high (D-61)"
            )
        return bound_of()


class FEA12Placement(FEA12Case):
    """The tenth block is the last one, and nothing before it moves."""

    def test_fea12_1_the_block_is_last_and_its_offset_is_the_prechange_width(self):
        """FEA-12.1 on all three rows and both encodings, a declaring declaration's last
        block is `strength` with width one, its offset is the width the **pre-change**
        declaration named -- 203, 329, 433 and 40, 82, 122 -- and the declaration's own
        width is that number plus one; and the slots before it carry exactly what the
        absence declaration carries for the same readout, so no earlier block moved
        (`ASM-46`, encoder.md §4)."""
        for shape in S.ALL_SHAPES:
            for encoding in S.ENCODINGS:
                absence = self.declaration(encoding, shape, S.ABSENT)
                declaring = self.declaration(encoding, shape, S.STRENGTH_ON)
                old_width = S.DECLARED_BY_SHAPE[shape][encoding][0]
                new_width = S.DECLARED_BY_SHAPE_STRENGTH[shape][encoding][0]
                with self.subTest(shape=shape, encoding=encoding):
                    self.assertEqual(
                        tuple(absence["shape"]), (old_width,),
                        "the absence declaration's width is the battery's own statement of "
                        "it (capacity.md §2): %r against %r"
                        % (tuple(absence["shape"]), (old_width,)),
                    )
                    self.assertEqual(
                        tuple(declaring["shape"]), (new_width,),
                        "a declaring declaration is exactly one slot wider than the "
                        "absence one, on every row (ASM-46): %r against %r"
                        % (tuple(declaring["shape"]), (new_width,)),
                    )
                    self.assertEqual(
                        len(declaring["blocks"]), len(absence["blocks"]) + 1,
                        "the declaring table carries exactly one more block than the "
                        "absence table (ASM-46): %d against %d"
                        % (len(declaring["blocks"]), len(absence["blocks"])),
                    )
                    self.assertEqual(
                        declaring["blocks"][:-1], absence["blocks"],
                        "every block before the last one is the absence declaration's own "
                        "record, offset included -- so no pre-existing offset moved "
                        "(ASM-46): %r" % (declaring["blocks"],),
                    )
                    field, offset, width = declaring["blocks"][-1][:3]
                    self.assertEqual(
                        (field, offset, width), (S.STRENGTH_FIELD, old_width, 1),
                        "the last block is `strength`, one slot wide, at the offset the "
                        "pre-change declaration's width named -- %d on %r -- which is what "
                        "makes the slot index one assertion instead of six (ASM-46): %r"
                        % (old_width, shape, declaring["blocks"][-1]),
                    )
                    # And through the declared calls: the same readout's observation
                    # agrees with the absence observation on every slot before the last.
                    record = S.shaped_readout(shape)
                    plain = self.ep("encode")(self.strength_encoder(
                        encoding, shape, S.ABSENT), record)
                    raised = self.ep("encode")(self.strength_encoder(
                        encoding, shape, S.STRENGTH_ON),
                        S.with_facts(record, strength=0.5))
                    self.assertEqual(
                        list(S.floats(raised))[:old_width],
                        list(S.floats(plain)),
                        "the %d slots before the tenth block carry what the absence "
                        "observation carries for the same readout, so no earlier block "
                        "moved (ASM-46): %r" % (old_width, S.floats(raised)[:8]),
                    )


class FEA12DenseValue(FEA12Case):
    """The dense slot carries the probability exactly, and refuses what is not one."""

    def test_fea12_2_the_dense_slot_is_p_and_a_value_outside_the_interval_is_refused(self):
        """FEA-12.2 on all three rows, the dense declaration's last slot carries each of
        FEA-12.2's five probabilities as the `float32` the writer was handed, and a value
        of `-0.01`, `1.01`, `nan`, `inf` or `-inf` is **refused by name** -- naming the
        injected key `'strength'` -- never clamped into the block's bound, never defaulted
        and never dropped (`ASM-46`, errors.md §3, D-95)."""
        for shape in S.ALL_SHAPES:
            record = S.shaped_readout(shape)
            offset = S.DECLARED_BY_SHAPE[shape][S.FLAT][0]
            for value in DENSE_VALUES:
                raised = self.observation(S.FLAT, shape, S.STRENGTH_ON,
                                          strength=value)
                slots = S.floats(raised)
                with self.subTest(shape=shape, value=value):
                    self.assertEqual(
                        len(slots), offset + 1,
                        "a declaring dense declaration is one slot wider on %r (ASM-46): "
                        "%d slots" % (shape, len(slots)),
                    )
                    self.assertEqual(
                        slots[offset], float(numpy.float32(value)),
                        "the tenth slot carries the probability itself, exactly, as the "
                        "encoding's own float32 -- not a bucket, not a normalised "
                        "distance and not a clamp (ASM-46, encoder.md §5): %r against %r"
                        % (slots[offset], float(numpy.float32(value))),
                    )
            encoder = self.strength_encoder(S.FLAT, shape, S.STRENGTH_ON)
            for value in REFUSED_VALUES:
                with self.subTest(shape=shape, refused=value):
                    exc = self.refuses(
                        self.ep("encode"), encoder,
                        S.with_facts(record, strength=value),
                        words=("'strength'",),
                    )
                    # ... and states the interval the value left, so a value outside it is
                    # a broken estimator and not a saturated one (ASM-46, D-95).
                    self.assert_names(exc, "0.0", "1.0")

    def test_fea12_2b_a_value_that_is_not_a_real_is_refused_and_never_coerced(self):
        """FEA-12.2 (second half) the slot is a **real**: a string, a `bool`, `None` or a
        sequence is refused by name rather than coerced by `float()`, which is the rule
        the module's other writers already keep (`errors.md` §4, ASM-46)."""
        record = S.shaped_readout(S.DEFAULT_SHAPE)
        encoder = self.strength_encoder(S.FLAT, S.DEFAULT_SHAPE, S.STRENGTH_ON)
        for value in ("0.5", True, False, None, (0.5,), [0.5], {"p": 0.5}):
            with self.subTest(value=value):
                self.refuses(
                    self.ep("encode"), encoder,
                    S.with_facts(record, strength=value),
                    words=("'strength'",),
                )


class FEA12TokenLadder(FEA12Case):
    """The token slot is one id of the eight-band ladder, and the pad is unreachable."""

    def test_fea12_3_the_token_slot_is_the_last_id_of_the_ladder(self):
        """FEA-12.3 the declaring token declaration's last slot is one id of the eight-band
        ladder over `[0, 1]` -- `0.0` and `0.05` are 102, `0.051` is 103, `0.30` is 105,
        `0.61` is 108 and `1.0` is 109 -- the ladder is **total** (every value in `[0, 1]`
        maps to exactly one of the eight ids), no band emits the pad, and the declaration's
        vocabulary is 110 on **every** row while the absence encoder still declares 96 and
        102 (`ASM-48`, card-tokens.md §3, §6)."""
        for shape in S.ALL_SHAPES:
            record = S.shaped_readout(shape)
            offset = S.DECLARED_BY_SHAPE[shape][S.TOKENS][0]
            for value, wanted in LADDER_CASES:
                slots = S.ints(self.observation(S.TOKENS, shape, S.STRENGTH_ON,
                                                strength=value))
                with self.subTest(shape=shape, value=value):
                    self.assertEqual(
                        len(slots), offset + 1,
                        "a declaring token declaration is one id wider on %r (ASM-46): "
                        "%d ids" % (shape, len(slots)),
                    )
                    self.assertEqual(
                        slots[offset], wanted,
                        "the value %r maps to the id %d the ladder declares (ASM-48): %r"
                        % (value, wanted, slots[offset]),
                    )
            # Totality: a fine sweep of [0, 1] lands on exactly the eight declared ids and
            # never on the pad (`card-tokens.md` §3: no other block may emit it).
            step = 0.0
            seen = set()
            while step <= 1.0:
                slots = S.ints(self.observation(S.TOKENS, shape, S.STRENGTH_ON,
                                                strength=step))
                seen.add(slots[offset])
                with self.subTest(shape=shape, probed=round(step, 6)):
                    self.assertIn(
                        slots[offset], S.STRENGTH_IDS,
                        "every value in [0, 1] maps to one of the ladder's eight ids, so "
                        "the ladder is total and the block has no unrepresentable value "
                        "(ASM-48, card-tokens.md §4): %r mapped to %r"
                        % (step, slots[offset]),
                    )
                    self.assertNotEqual(
                        slots[offset], 0,
                        "no strength band may emit the pad: the lowest id of the ladder "
                        "sits above every id any row allocates (ASM-48, card-tokens.md "
                        "§3): %r mapped to the pad" % (step,),
                    )
                step += 0.01
            self.assertEqual(
                seen, set(S.STRENGTH_IDS),
                "the sweep visits every one of the ladder's eight ids, so the coverage "
                "above is not a statement about a dead block (ASM-48): %r"
                % (sorted(seen),),
            )
        # The vocabulary the declaration reports: 110 everywhere, and the absence one is
        # still the shape row's 96 or 102.
        for shape in S.ALL_SHAPES:
            with self.subTest(shape=shape, declaration="declaring"):
                declared = self.ep("observation_spec")(
                    self.strength_encoder(S.TOKENS, shape, S.STRENGTH_ON))
                self.assertEqual(
                    declared["vocabulary"], S.STRENGTH_VOCABULARY,
                    "a declaring token declaration reports the vocabulary 110 on every "
                    "row -- the ladder's own top, above the six-seat row's 102 -- because "
                    "the block's ids must lie inside the vocabulary a learner is sized by "
                    "and a container records (ASM-48): %r on %r"
                    % (declared["vocabulary"], shape),
                )
            with self.subTest(shape=shape, declaration="absence"):
                quiet = self.ep("observation_spec")(
                    self.strength_encoder(S.TOKENS, shape, S.ABSENT))
                self.assertEqual(
                    quiet["vocabulary"], S.VOCABULARY_BY_SHAPE[shape],
                    "the absence encoder still declares the shape row's own vocabulary "
                    "(capacity.md §4): %r on %r"
                    % (quiet["vocabulary"], shape),
                )
        flat = self.ep("observation_spec")(
            self.strength_encoder(S.FLAT, S.DEFAULT_SHAPE, S.STRENGTH_ON))
        self.assertIsNone(
            flat["vocabulary"],
            "the flat encoding declares no vocabulary, declaring or not (surface.md §5): "
            "%r" % (flat["vocabulary"],),
        )


class FEA12AntiSilence(FEA12Case):
    """A declaring encoder refuses a readout that does not carry the declared fact."""

    def test_fea12_4_a_readout_without_the_declared_strength_is_refused(self):
        """FEA-12.4 on all three rows and both encodings, an encoder that **declares**
        `strength` refuses a readout carrying no such key, naming it -- so a forgotten
        injection is a named refusal and never a silent zero -- and accepts the same
        readout once the key is there (`ASM-46`, `ASM-47`, encoder.md §5)."""
        for shape in S.ALL_SHAPES:
            record = S.shaped_readout(shape)
            self.assertNotIn(
                S.STRENGTH_FIELD, record,
                "this case's readout carries no strength, which is the input the case is "
                "about (%r): %r" % (shape, sorted(record)),
            )
            for encoding in S.ENCODINGS:
                encoder = self.strength_encoder(encoding, shape, S.STRENGTH_ON)
                with self.subTest(shape=shape, encoding=encoding):
                    self.refuses(
                        self.ep("encode"), encoder, record,
                        words=("encode", repr(S.STRENGTH_FIELD)),
                    )
                    accepted = self.ep("encode")(
                        encoder, S.with_facts(record, strength=0.5))
                    self.assertEqual(
                        len(S.floats(accepted)),
                        S.DECLARED_BY_SHAPE_STRENGTH[shape][encoding][0],
                        "the same readout with the declared key encodes to the declaring "
                        "declaration's width (ASM-46): %d slots"
                        % (len(S.floats(accepted)),),
                    )

    def test_fea12_4b_an_absence_encoder_ignores_the_injected_key(self):
        """FEA-12.4 (second half) an encoder that declares **no** strength block ignores a
        readout that carries the key anyway: a key the encoding does not carry is ignored
        and never refused, which is the rule `legal` already follows (`surface.md` §6,
        guardrails.md G9, ASM-46)."""
        for shape in S.ALL_SHAPES:
            record = S.shaped_readout(shape)
            carried = S.with_facts(record, strength=0.5)
            for encoding in S.ENCODINGS:
                encoder = self.strength_encoder(encoding, shape, S.ABSENT)
                with self.subTest(shape=shape, encoding=encoding):
                    self.assertEqual(
                        list(S.floats(self.ep("encode")(encoder, carried))),
                        list(S.floats(self.ep("encode")(encoder, record))),
                        "a key the absence encoding does not carry changes nothing, "
                        "because it reads the facts its blocks declare and nothing else "
                        "(surface.md §6, guardrails.md G9): %r" % (encoding,),
                    )


class FEA12Fields(FEA12Case):
    """The declared fields are the nine, or the ten with `strength` last."""

    def test_fea12_5_the_fields_are_nine_or_ten_with_strength_last(self):
        """FEA-12.5 `observation_spec(...)["fields"]` is the nine carried facts for an
        absence encoder and the ten with `'strength'` **last** for a declaring one, the
        declaration's block count equals its field count on both, and the spec record's
        keys are the six keys on both (`encoder.md` §3, §4, ASM-46)."""
        for shape in S.ALL_SHAPES:
            for encoding in S.ENCODINGS:
                quiet = self.ep("observation_spec")(
                    self.strength_encoder(encoding, shape, S.ABSENT))
                declared = self.ep("observation_spec")(
                    self.strength_encoder(encoding, shape, S.STRENGTH_ON))
                with self.subTest(shape=shape, encoding=encoding):
                    self.assertEqual(
                        tuple(quiet["fields"]), S.FIELDS,
                        "an absence encoder carries the nine facts and nothing else "
                        "(encoder.md §3.1): %r" % (tuple(quiet["fields"]),),
                    )
                    self.assertEqual(
                        tuple(declared["fields"]), S.FIELDS + (S.STRENGTH_FIELD,),
                        "a declaring encoder carries the ten, with `strength` **last** -- "
                        "appended after the history and never interleaved, so every other "
                        "field keeps the index it had (ASM-46): %r"
                        % (tuple(declared["fields"]),),
                    )
                    self.assertEqual(
                        tuple(quiet), S.SPEC_KEYS,
                        "the six spec keys are the six on an absence encoder "
                        "(surface.md §5): %r" % (tuple(quiet),),
                    )
                    self.assertEqual(
                        tuple(declared), S.SPEC_KEYS,
                        "and the six on a declaring one: the block is a fact the "
                        "declaration carries and not a seventh key (surface.md §5, "
                        "ASM-46): %r" % (tuple(declared),),
                    )
                    self.assertEqual(
                        len(self.declaration(encoding, shape, S.ABSENT)["blocks"]),
                        len(S.FIELDS),
                        "the absence table holds one block per carried field "
                        "(encoder.md §4): %r"
                        % (len(self.declaration(encoding, shape, S.ABSENT)["blocks"]),),
                    )
                    self.assertEqual(
                        len(self.declaration(encoding, shape, S.STRENGTH_ON)["blocks"]),
                        len(declared["fields"]),
                        "and the declaring table holds one per declared field, so the "
                        "tenth block is the tenth field and not an eleventh record "
                        "(ASM-46): %r"
                        % (len(self.declaration(encoding, shape,
                                                S.STRENGTH_ON)["blocks"]),),
                    )


class FEA12Bounds(FEA12Case):
    """The two new writer tags have declared bounds, and the table still partitions."""

    def test_fea12_6_every_block_of_a_declaring_declaration_is_inside_a_bound(self):
        """FEA-12.6 the bound table covers the two tags the tenth block can name, and
        FEA-11.1's totality re-runs against the strength-on twin: on all three rows and
        both encodings the declaring declaration's blocks **partition** its width -- every
        slot in exactly one block, `holders == [1] * width` -- and every block's writer has
        a declared bound (`ASM-46`, `ASM-48`, D-61, flat-numeric.md §4)."""
        table = self.bound_table()
        for tag in ("strength-scaled", "strength-bucket"):
            with self.subTest(tag=tag):
                self.assertIn(
                    tag, table,
                    "the tenth block's writer has a declared bound, because every writer "
                    "of `encode`'s closed set has one (D-61): the table carries %r"
                    % (sorted(table),),
                )
                low, high, policy = table[tag]
                self.assertIn(
                    policy, ("exact", "id"),
                    "the probability block is `exact` -- its writer refuses a value "
                    "outside the interval rather than clipping one -- and the token block "
                    "emits an id, exactly as the other indicator and token blocks do "
                    "(flat-numeric.md §4, card-tokens.md §6): %r" % (table[tag],),
                )
                if policy == "id":
                    self.assertEqual(
                        (low, high), (0, "vocabulary"),
                        "a token block's bound follows the declaration's vocabulary, which "
                        "is 110 on a declaring row (ASM-48): %r" % (table[tag],),
                    )
                else:
                    self.assertEqual(
                        (low, high), (0.0, 1.0),
                        "a probability's declared bound is the unit interval (ASM-46): %r"
                        % (table[tag],),
                    )
        for shape in S.ALL_SHAPES:
            for encoding in S.ENCODINGS:
                declaration = self.declaration(encoding, shape, S.STRENGTH_ON)
                width = declaration["shape"][0]
                with self.subTest(shape=shape, encoding=encoding):
                    holders = [0] * width
                    for _field, offset, block_width, writer, _reads, _params in \
                            declaration["blocks"]:
                        with self.subTest(shape=shape, encoding=encoding, writer=writer):
                            self.assertIn(
                                writer, table,
                                "every writer a declaring block names has a declared bound "
                                "(D-61): %r" % (writer,),
                            )
                        for slot in range(offset, offset + block_width):
                            holders[slot] += 1
                    self.assertEqual(
                        holders, [1] * width,
                        "the declaring declaration's blocks partition its %d slots, so the "
                        "tenth block costs one slot and no slot is uncovered (ASM-46): %r"
                        % (width, holders[-6:]),
                    )


class FEA12Era(FEA12Case):
    """The absence declaration is the record this change found."""

    def test_fea12_7_the_absence_declaration_is_the_record_it_was(self):
        """FEA-12.7 on all three rows and both encodings, an encoder built with no member
        -- and one built with the axis' declared default `none` -- declares the six spec
        keys, the nine fields, the widths 203/329/433 and 40/82/122 and the vocabularies
        96 and 102, asserted against the values this change found and **not** against the
        new code's own arithmetic (`ASM-46`, `ASM-50`)."""
        for shape in S.ALL_SHAPES:
            for encoding in S.ENCODINGS:
                width = S.DECLARED_BY_SHAPE[shape][encoding][0]
                vocabulary = (None if encoding == S.FLAT
                              else S.VOCABULARY_BY_SHAPE[shape])
                quiet = self.ep("observation_spec")(
                    self.strength_encoder(encoding, shape, S.ABSENT))
                named = self.ep("observation_spec")(
                    self.strength_encoder(encoding, shape, S.STRENGTH_NONE))
                with self.subTest(shape=shape, encoding=encoding):
                    self.assertEqual(
                        quiet, named,
                        "the axis' declared default `none` and an absent keyword are one "
                        "declaration, and neither is a defaulting of the other: the "
                        "resolved default is exactly the absence (ASM-46, FEA-12.8): "
                        "%r against %r" % (quiet, named),
                    )
                    self.assertEqual(
                        tuple(quiet), S.SPEC_KEYS,
                        "the six spec keys, unchanged (surface.md §5): %r" % (tuple(quiet),),
                    )
                    self.assertEqual(
                        tuple(quiet["fields"]), S.FIELDS,
                        "the nine carried facts, unchanged -- `strength` is not one of "
                        "them on the absence path (encoder.md §3.1, ASM-46): %r"
                        % (tuple(quiet["fields"]),),
                    )
                    self.assertEqual(
                        tuple(quiet["shape"]), (width,),
                        "the absence width is the one this change found -- 203/329/433 "
                        "dense and 40/82/122 token -- so the ~250 width assertions of the "
                        "battery are untouched (ASM-46): %r on %r/%r"
                        % (tuple(quiet["shape"]), shape, encoding),
                    )
                    self.assertEqual(
                        quiet["vocabulary"], vocabulary,
                        "the absence vocabulary is the shape row's -- 96 on the two-seat "
                        "rows, 102 on the six-seat one, and none for the flat encoding "
                        "(capacity.md §4): %r on %r/%r"
                        % (quiet["vocabulary"], shape, encoding),
                    )
                    self.assertEqual(
                        len(self.declaration(encoding, shape, S.ABSENT)["blocks"]),
                        len(S.FIELDS),
                        "and the absence table holds the nine blocks it always held "
                        "(encoder.md §4): %r"
                        % (len(self.declaration(encoding, shape, S.ABSENT)["blocks"]),),
                    )
        # The catalogue the surface publishes is the absence one: it names no shape and
        # no member, so a new member cannot silently become every encoder's declaration.
        for name, record in self.ep("encodings")().items():
            with self.subTest(encoding=name, catalogue=True):
                self.assertEqual(
                    tuple(record["shape"]),
                    (S.DECLARED[name]["shape"]),
                    "features.encodings() publishes the absence declaration on the "
                    "default shape, so a declaring encoder is always one a caller asked "
                    "for (surface.md §3, ASM-46): %r" % (tuple(record["shape"]),),
                )


class FEA12MemberRefusal(FEA12Case):
    """An uncatalogued member is refused by name; `None` is the absence."""

    def test_fea12_8_an_unknown_member_is_refused_and_none_is_the_absence(self):
        """FEA-12.8 `build_encoder(name, strength=<unknown>)` is refused naming the value
        and the two declared members -- never mapped onto `none` and never onto
        `supervised` -- while `strength=None` is the absence and not a defaulting of a
        member, so it builds the same declaration the keyword's absence builds
        (`ASM-46`, errors.md §2-§3)."""
        build = self.ep("build_encoder")
        unknown = (
            "strength", "Supervised", "SUPERVISED", " supervised", "supervised ",
            "on", "off", "attn-60", True, 1, 0, ("supervised",), {"member": "supervised"},
        )
        for value in unknown:
            with self.subTest(value=value):
                exc = self.refuses(
                    lambda name=S.FLAT, member=value: build(name, strength=member),
                    words=("build_encoder", "strength", repr(value)),
                )
                self.assert_names(exc, repr(S.STRENGTH_NONE), repr(S.STRENGTH_ON))
        self.assertEqual(
            self.ep("observation_spec")(build(S.FLAT, strength=None)),
            self.ep("observation_spec")(build(S.FLAT)),
            "`strength=None` is the absence: it builds exactly the declaration the "
            "keyword's absence builds (ASM-46, FEA-12.7): %r"
            % (self.ep("observation_spec")(build(S.FLAT, strength=None)),),
        )
        for shape in S.ALL_SHAPES:
            for encoding in S.ENCODINGS:
                with self.subTest(shape=shape, encoding=encoding, member=None):
                    self.assertEqual(
                        tuple(self.ep("observation_spec")(
                            build(encoding, shape=shape, strength=None))["shape"]),
                        tuple(self.ep("observation_spec")(
                            build(encoding, shape=shape))["shape"]),
                        "the absence of the member and the member `None` are one "
                        "declaration on every row (ASM-46)",
                    )


if __name__ == "__main__":  # pragma: no cover - a case file, run by pytest
    unittest.main()
