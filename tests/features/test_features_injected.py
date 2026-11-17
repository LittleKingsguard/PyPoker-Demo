"""FEA-13 -- the three further injected facts: `bet_size`, `opp_action`, `opp_strength`.

``docs/L1/strength-design.md`` §A (the fact), §B.2-§B.3 (the injection), §F.2 (the FEA-12
battery this one is written beside); ``ASM-46``; ``docs/L2/features/surface.md`` §4-§6;
``docs/L3/features/encoder.md`` §4-§5; ``docs/L3/features/errors.md`` §2-§3.

`strength` established the pattern: a **declared field with an injected value**, opted into
behind a keyword on `build_encoder`, appended **after** the history block in both encodings,
carried by a copy of the readout and never by the readout itself, and refused by name when
the value is missing rather than defaulted to zero.  Three more facts follow it exactly:

* `bet_size` -- the amount facing the acting seat over the shape's chips in play, the one
  fact the design review found the `history` block was carrying and the encoder discarding;
* `opp_action` -- a frozen opponent model's probability that the seat that acted last
  raises on its next turn;
* `opp_strength` -- that same opponent's hand strength, from the same frozen model.

Six cases hold them:

* FEA-13.1 the **absence path is unchanged** -- 203/329/433 and 40/82/122 over 96 and 102 --
  and any subset of the four facts appends one slot (dense) or one id (token) each, in the
  declared order, at the offset the pre-change width named;
* FEA-13.2 each fact's dense slot carries its value exactly, and a value outside `[0, 1]` --
  or a non-finite one -- is refused **by name**, never clamped;
* FEA-13.3 each fact's token id falls in its own eight-band ladder, the ladders are total,
  no band emits the pad, and the vocabulary follows the widest declared band;
* FEA-13.4 a declared fact the readout does not carry is refused **by name** -- the
  anti-silence assertion, for all three new facts;
* FEA-13.5 an uncatalogued, duplicated or non-sequence `facts` is refused by name, a named
  member the facts leave out is refused rather than dropped, and `facts=()` is the absence;
* FEA-13.6 the **injection** attaches exactly the declared facts to a **fresh** mapping,
  leaves the readout it was handed untouched, derives `bet_size` from `to_call` and the
  shape's chips in play, and refuses a declared fact it cannot produce.

No case asserts an exception class (``errors.md`` §2).  Every number below is the design's
and none is re-derived from the module's own arithmetic.
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


#: The four injected facts, in the order a declaration appends them (`strength` first, so a
#: declaration that declares it alone is the ten-field record `ASM-46` fixed).
INJECTED = ("strength", "bet_size", "opp_action", "opp_strength")

#: The three this battery adds, on their own.
ADDED = INJECTED[1:]

#: Each fact's eight-band ladder: the ids `strength-design.md` §A.3's edges allocate, one
#: eight-id band per fact, appended after the strength band.  The edges are the same eight
#: on every fact and every row.
BANDS = {
    "strength": (102, 103, 104, 105, 106, 107, 108, 109),
    "bet_size": (110, 111, 112, 113, 114, 115, 116, 117),
    "opp_action": (118, 119, 120, 121, 122, 123, 124, 125),
    "opp_strength": (126, 127, 128, 129, 130, 131, 132, 133),
}

#: The vocabulary each fact's band needs: the widest id it can emit plus one.  A declaration
#: reports the widest one it declares, so a strength-only declaration is still 110.
VOCABULARY = {"strength": 110, "bet_size": 118, "opp_action": 126, "opp_strength": 134}

#: The token vocabulary a declaration of **all four** reports on every row.
VOCABULARY_ALL = 134

#: The widths a declaration of one fact declares: the absence width plus one, on all three
#: rows and both encodings (the strength column is `S.DECLARED_BY_SHAPE_STRENGTH`'s).
DECLARED_ONE = {
    S.DEFAULT_SHAPE: {S.FLAT: (204,), S.TOKENS: (41,)},
    S.SECOND_SHAPE: {S.FLAT: (330,), S.TOKENS: (83,)},
    S.THIRD_SHAPE: {S.FLAT: (434,), S.TOKENS: (123,)},
}

#: The widths a declaration of **all four** facts declares: the absence width plus four.
DECLARED_ALL = {
    S.DEFAULT_SHAPE: {S.FLAT: (207,), S.TOKENS: (44,)},
    S.SECOND_SHAPE: {S.FLAT: (333,), S.TOKENS: (86,)},
    S.THIRD_SHAPE: {S.FLAT: (437,), S.TOKENS: (126,)},
}

#: The five probabilities the dense slots carry, and the exact value each fixes (`0.87` is
#: not representable in binary, so the slot holds the float32 the writer was handed).
DENSE_VALUES = (0.0, 0.25, 0.5, 0.87, 1.0)

#: The values the dense writers refuse, and what the refusal must name (`errors.md` §3).
REFUSED_VALUES = (-0.01, 1.01, float("nan"), float("inf"), float("-inf"))

#: One ladder's fixed points, as `(value, rung)`: the two ends of a band, a value a
#: thousandth past an edge, and the interval's two ends -- FEA-12.3's cases, read against a
#: band base instead of a literal id.
LADDER_CASES = (
    (0.0, 0),
    (0.05, 0),
    (0.051, 1),
    (0.30, 3),
    (0.61, 6),
    (1.0, 7),
)

#: The five amount normalisers of each row, from which the shape's **chips in play** are
#: read: the pot's normaliser is the total every seat's stack is a fraction of.
CHIPS_IN_PLAY = {S.DEFAULT_SHAPE: 40, S.SECOND_SHAPE: 200, S.THIRD_SHAPE: 600}


class FEA13Case(S.FeaturesCase):
    """The calls this battery is written in: one encoder per declaration, one readout."""

    def declaring(self, name=S.FLAT, shape=None, facts=INJECTED):
        """One encoder declaring `facts`, on one shape."""
        return self.ep("build_encoder")(name, shape=shape, facts=facts)

    def observation(self, name=S.FLAT, shape=None, facts=INJECTED, values=None):
        """One observation of an invented readout through a declaring encoder.

        `values` is handed over as the readout's `extra` keys -- the injection the harness
        writes -- so no case builds a readout by hand (`ASM-47`).
        """
        extra = dict(values or {})
        encoder = self.declaring(name, shape, facts)
        return self.ep("encode")(encoder, S.shaped_readout(shape, extra=extra))

    def supplied(self, values):
        """Every declared fact's value, with `values` overriding one at a time."""
        base = {"strength": 0.5, "bet_size": 0.25, "opp_action": 0.5, "opp_strength": 0.5}
        base.update(values or {})
        return base

    def spec_of(self, name=S.FLAT, shape=None, facts=INJECTED):
        """The six-key spec record of a declaring encoder."""
        return self.ep("observation_spec")(self.declaring(name, shape, facts))


class FEA13Absence(FEA13Case):
    """The absence path is unchanged, and each declared fact is one slot at the end."""

    def test_fea13_1_absence_is_unchanged_and_each_fact_is_one_appended_slot(self):
        """FEA-13.1 on all three rows and both encodings, `build_encoder(name, shape)` is
        the record it was -- the six spec keys, the nine fields, the widths 203/329/433 and
        40/82/122 over 96 and 102 -- while a declaration of one fact is that width plus one
        and one of all four is that width plus four, each fact a **last** one-slot block in
        the declared order with no earlier offset moved (`strength-design.md` §A.1, §A.5,
        `ASM-46`)."""
        self.assertEqual(
            INJECTED[0], S.STRENGTH_FIELD,
            "the injected order puts `strength` first, so the ten-field record is the one "
            "`ASM-46` fixed (`strength-design.md` §A.1): %r" % (INJECTED,),
        )
        for shape in S.ALL_SHAPES:
            for encoding in S.ENCODINGS:
                old_width = S.DECLARED_BY_SHAPE[shape][encoding][0]
                one_width = DECLARED_ONE[shape][encoding][0]
                all_width = DECLARED_ALL[shape][encoding][0]
                quiet = self.spec_of(encoding, shape, facts=None)
                with self.subTest(shape=shape, encoding=encoding):
                    self.assertEqual(
                        tuple(quiet), S.SPEC_KEYS,
                        "the six spec keys are the six on the absence path (surface.md §5): "
                        "%r" % (tuple(quiet),),
                    )
                    self.assertEqual(
                        tuple(quiet["fields"]), S.FIELDS,
                        "an encoder that declares no fact carries the nine facts and "
                        "nothing else (encoder.md §3.1, strength-design.md §A.5): %r"
                        % (tuple(quiet["fields"]),),
                    )
                    self.assertEqual(
                        tuple(quiet["shape"]), (old_width,),
                        "the absence width is the one this change found -- 203/329/433 "
                        "dense and 40/82/122 token -- asserted against the value and not "
                        "against the new code's arithmetic (strength-design.md §A.5): %r "
                        "on %r/%r" % (tuple(quiet["shape"]), shape, encoding),
                    )
                    self.assertEqual(
                        quiet["vocabulary"],
                        None if encoding == S.FLAT else S.VOCABULARY_BY_SHAPE[shape],
                        "the absence vocabulary is the shape row's -- 96 on the two-seat "
                        "rows and 102 on the six-seat one, none for the dense encoding "
                        "(capacity.md §4): %r on %r/%r"
                        % (quiet["vocabulary"], shape, encoding),
                    )
                for facts, width in (
                    ((S.STRENGTH_FIELD,), one_width),
                    (INJECTED, all_width),
                ):
                    declared = self.spec_of(encoding, shape, facts=facts)
                    with self.subTest(shape=shape, encoding=encoding, facts=facts):
                        self.assertEqual(
                            tuple(declared["fields"]), S.FIELDS + tuple(facts),
                            "the declared facts are appended to the nine, in the declared "
                            "order, and no readout fact is interleaved with them "
                            "(strength-design.md §A.1): %r"
                            % (tuple(declared["fields"]),),
                        )
                        self.assertEqual(
                            tuple(declared["shape"]), (width,),
                            "a declaration of %d fact(s) is exactly that many slots (or "
                            "ids) wider (strength-design.md §A.1): %r on %r/%r"
                            % (len(facts), tuple(declared["shape"]), shape, encoding),
                        )
                # Every block before the appended ones is the absence record's own, offsets
                # included, so no pre-existing offset moved.
                from_import = self.tables()
                absence = from_import(encoding, shape, None)
                raised = from_import(encoding, shape, INJECTED)
                with self.subTest(shape=shape, encoding=encoding, blocks=True):
                    self.assertEqual(
                        raised["blocks"][: len(absence["blocks"])], absence["blocks"],
                        "every block before the appended ones is the absence declaration's "
                        "own record, offset included (strength-design.md §A.1): %r"
                        % (raised["blocks"],),
                    )
                    for position, fact in enumerate(INJECTED):
                        field, offset, width = raised["blocks"][
                            len(absence["blocks"]) + position
                        ][:3]
                        self.assertEqual(
                            (field, offset, width), (fact, old_width + position, 1),
                            "the fact %r is the %dth appended block, one slot wide, at the "
                            "offset the pre-change width named plus its own position "
                            "(strength-design.md §A.1): %r"
                            % (fact, position, raised["blocks"][-1]),
                        )
                    self.assertEqual(
                        len(raised["blocks"]), len(raised["fields"]),
                        "one block per declared field, so the appended facts are fields "
                        "and not extra records (encoder.md §4): %d against %d"
                        % (len(raised["blocks"]), len(raised["fields"])),
                    )

    def tables(self):
        """`features.declarations.declaration` -- the block table, as FEA-12.1 reads it.

        The block table is what says which block is last and where it starts, and no call
        returns it; this battery's promise to reach only the declared names has the one
        declared exception FEA-11.1 and FEA-12.1 already take (`docs/L3/features/README.md`
        §3, D-12).
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

        def table(encoding, shape, facts):
            return build(encoding, shape, facts=facts)

        return table


class FEA13DenseValue(FEA13Case):
    """Each fact's dense slot carries its value exactly, and refuses what is not one."""

    def test_fea13_2_each_dense_slot_is_its_value_and_an_outside_value_is_refused(self):
        """FEA-13.2 on all three rows, each of the three added facts' dense slot carries
        FEA-13.2's five probabilities as the `float32` the writer was handed, and a value of
        `-0.01`, `1.01`, `nan`, `inf` or `-inf` is **refused by name** -- naming the
        injected key -- never clamped into the block's bound, never defaulted and never
        dropped (`strength-design.md` §A.3, errors.md §3, D-95)."""
        for shape in S.ALL_SHAPES:
            base = S.DECLARED_BY_SHAPE[shape][S.FLAT][0]
            for position, fact in enumerate(ADDED):
                offset = base + 1 + position
                for value in (0.0, 0.25, 0.5, 0.87, 1.0):
                    slots = S.floats(
                        self.observation(S.FLAT, shape, INJECTED, self.supplied({fact: value}))
                    )
                    with self.subTest(shape=shape, fact=fact, value=value):
                        self.assertEqual(
                            len(slots), DECLARED_ALL[shape][S.FLAT][0],
                            "a declaration of all four facts is four slots wider on %r "
                            "(strength-design.md §A.1): %d slots" % (shape, len(slots)),
                        )
                        self.assertEqual(
                            slots[offset], float(numpy.float32(value)),
                            "the %r slot carries the value itself, exactly, as the "
                            "encoding's own float32 -- not a bucket, not a normalised "
                            "distance and not a clamp (encoder.md §5): %r against %r"
                            % (fact, slots[offset], float(numpy.float32(value))),
                        )
                for value in REFUSED_VALUES:
                    with self.subTest(shape=shape, fact=fact, refused=value):
                        exc = self.refuses(
                            self.ep("encode"),
                            self.declaring(S.FLAT, shape, INJECTED),
                            S.shaped_readout(shape, extra=self.supplied({fact: value})),
                            words=("encode", repr(fact)),
                        )
                        self.assert_names(exc, "0.0", "1.0")

    def test_fea13_2b_a_value_that_is_not_a_real_is_refused_and_never_coerced(self):
        """FEA-13.2 (second half) each added fact's slot is a **real**: a string, a `bool`,
        `None` or a sequence is refused by name rather than coerced by `float()`, which is
        the rule the module's other writers already keep (`errors.md` §4)."""
        shape = S.DEFAULT_SHAPE
        for fact in ADDED:
            for value in ("0.5", True, False, None, (0.5,), [0.5], {"p": 0.5}):
                with self.subTest(fact=fact, value=value):
                    self.refuses(
                        self.ep("encode"),
                        self.declaring(S.FLAT, shape, INJECTED),
                        S.shaped_readout(shape, extra=self.supplied({fact: value})),
                        words=("encode", repr(fact)),
                    )


class FEA13TokenLadder(FEA13Case):
    """Each fact is one id of its own eight-band ladder, and the pad is unreachable."""

    def test_fea13_3_each_token_slot_is_its_own_ladder_s_rung(self):
        """FEA-13.3 on all three rows, each added fact's token slot is one id of its **own**
        eight-band ladder -- `bet_size` 110-117, `opp_action` 118-125, `opp_strength`
        126-133 -- the ladders are **total** over `[0, 1]`, no band emits the pad, and the
        declaration's vocabulary follows the widest declared band while the absence encoder
        still declares 96 and 102 (`strength-design.md` §A.3, card-tokens.md §3, §6)."""
        for shape in S.ALL_SHAPES:
            base = S.DECLARED_BY_SHAPE[shape][S.TOKENS][0]
            for position, fact in enumerate(ADDED):
                offset = base + 1 + position
                for value, rung in LADDER_CASES:
                    slots = S.ints(
                        self.observation(
                            S.TOKENS, shape, INJECTED, self.supplied({fact: value})
                        )
                    )
                    wanted = BANDS[fact][rung]
                    with self.subTest(shape=shape, fact=fact, value=value):
                        self.assertEqual(
                            len(slots), DECLARED_ALL[shape][S.TOKENS][0],
                            "a declaration of all four facts is four ids wider on %r "
                            "(strength-design.md §A.1): %d ids" % (shape, len(slots)),
                        )
                        self.assertEqual(
                            slots[offset], wanted,
                            "the value %r of %r maps to the id %d its own ladder declares "
                            "(strength-design.md §A.3): %r"
                            % (value, fact, wanted, slots[offset]),
                        )
                step = 0.0
                seen = set()
                while step <= 1.0:
                    slots = S.ints(
                        self.observation(
                            S.TOKENS, shape, INJECTED, self.supplied({fact: step})
                        )
                    )
                    seen.add(slots[offset])
                    self.assertIn(
                        slots[offset], BANDS[fact],
                        "every value in [0, 1] maps to one id of %r's own band, so the "
                        "ladder is total and the block has no unrepresentable value "
                        "(card-tokens.md §4): %r mapped to %r"
                        % (fact, step, slots[offset]),
                    )
                    self.assertNotEqual(
                        slots[offset], 0,
                        "no injected band may emit the pad: every fact's lowest id sits "
                        "above every id any row allocates (card-tokens.md §3, "
                        "strength-design.md §A.3): %r mapped to the pad" % (step,),
                    )
                    step += 0.05
                self.assertEqual(
                    seen, set(BANDS[fact]),
                    "the sweep visits every id of %r's ladder, so the coverage above is not "
                    "a statement about a dead block: %r" % (fact, sorted(seen)),
                )
        for shape in S.ALL_SHAPES:
            with self.subTest(shape=shape, declaration="all four"):
                self.assertEqual(
                    self.spec_of(S.TOKENS, shape, INJECTED)["vocabulary"], VOCABULARY_ALL,
                    "a declaration of all four facts reports the vocabulary the widest band "
                    "needs, 134, on every row -- the block's ids must lie inside the "
                    "vocabulary a learner is sized by and a container records "
                    "(strength-design.md §A.3): %r on %r"
                    % (self.spec_of(S.TOKENS, shape, INJECTED)["vocabulary"], shape),
                )
            for fact in ADDED:
                with self.subTest(shape=shape, declaration=fact):
                    self.assertEqual(
                        self.spec_of(S.TOKENS, shape, (fact,))["vocabulary"],
                        VOCABULARY[fact],
                        "a declaration of %r alone reports the vocabulary its own band needs "
                        "-- 118, 126 or 134 -- because the bands are positional and do not "
                        "depend on which other facts are declared (strength-design.md §A.3): "
                        "%r" % (fact, self.spec_of(S.TOKENS, shape, (fact,))["vocabulary"]),
                    )
            with self.subTest(shape=shape, declaration="absence"):
                self.assertEqual(
                    self.spec_of(S.TOKENS, shape, None)["vocabulary"],
                    S.VOCABULARY_BY_SHAPE[shape],
                    "the absence encoder still declares the shape row's own vocabulary "
                    "(capacity.md §4): %r on %r"
                    % (self.spec_of(S.TOKENS, shape, None)["vocabulary"], shape),
                )
        self.assertIsNone(
            self.spec_of(S.FLAT, S.DEFAULT_SHAPE, INJECTED)["vocabulary"],
            "the flat encoding declares no vocabulary, declaring or not (surface.md §5)",
        )


class FEA13AntiSilence(FEA13Case):
    """A declaring encoder refuses a readout that does not carry a declared fact."""

    def test_fea13_4_a_declared_fact_the_readout_lacks_is_refused_by_name(self):
        """FEA-13.4 on all three rows and both encodings, an encoder that **declares** a
        fact refuses a readout carrying no such key, naming it -- so a forgotten injection
        is a named refusal and never a silent zero -- and accepts the same readout once the
        key is there (`strength-design.md` §B.2, encoder.md §5)."""
        for shape in S.ALL_SHAPES:
            for fact in ADDED:
                encoder = self.declaring(S.FLAT, shape, INJECTED)
                carried = S.shaped_readout(shape, extra=self.supplied(None))
                missing = S.without(carried, fact)
                with self.subTest(shape=shape, fact=fact):
                    self.refuses(
                        self.ep("encode"), encoder, missing,
                        words=("encode", repr(fact)),
                    )
                    accepted = self.ep("encode")(encoder, carried)
                    self.assertEqual(
                        len(S.floats(accepted)),
                        DECLARED_ALL[shape][S.FLAT][0],
                        "the same readout with the declared key encodes to the declaring "
                        "declaration's width: %d slots" % (len(S.floats(accepted)),),
                    )
        # ... and the token encoding, where the missing fact is a missing id.
        for shape in S.ALL_SHAPES:
            for fact in ADDED:
                token_encoder = self.declaring(S.TOKENS, shape, INJECTED)
                carried = S.shaped_readout(shape, extra=self.supplied(None))
                with self.subTest(shape=shape, fact=fact, encoding=S.TOKENS):
                    self.refuses(
                        self.ep("encode"), token_encoder, S.without(carried, fact),
                        words=("encode", repr(fact)),
                    )


class FEA13Declared(FEA13Case):
    """The `facts` keyword refuses what it cannot declare, and declares nothing by default."""

    def test_fea13_5_an_unknown_or_conflicting_declaration_is_refused_by_name(self):
        """FEA-13.5 a fact outside the four, a duplicate, a bare string and a value that is
        not a sequence are refused naming the value and the four -- never dropped from the
        declaration they were written into -- a named strength member the facts leave out is
        refused rather than reconciled, `facts=()` is the absence of the keyword, and
        `facts=("strength",)` is the same declaration `strength="supervised"` builds
        (`strength-design.md` §A.5, errors.md §2-§3)."""
        build = self.ep("build_encoder")
        unknown = (
            "pot", "Strength", "BET_SIZE", " bet_size", "bet_size ", "to_call",
            ("bet_size", "pot"), True, 1, 0.5, {"fact": "bet_size"},
        )
        for value in unknown:
            with self.subTest(value=value):
                exc = self.refuses(
                    lambda facts=value: build(S.FLAT, facts=facts),
                    words=("build_encoder", "facts"),
                )
                if isinstance(value, tuple) and len(value) == 2:
                    # A tuple carrying one unknown name is refused naming that name.
                    self.assert_names(exc, repr("pot"))
        for value in ("bet_size", "strength"):
            with self.subTest(value=value, bare=True):
                self.refuses(
                    lambda facts=value: build(S.FLAT, facts=facts),
                    words=("build_encoder", "facts", repr(value)),
                )
        self.refuses(
            lambda: build(S.FLAT, facts=("bet_size", "bet_size")),
            words=("build_encoder", "facts", "distinct"),
        )
        # The member and the facts are two spellings of one declaration: a member the facts
        # leave out is a declaration the encoder would drop, and it is refused by name.
        self.refuses(
            lambda: build(S.FLAT, strength=S.STRENGTH_ON, facts=("bet_size",)),
            words=("build_encoder", S.STRENGTH_ON, S.STRENGTH_FIELD),
        )
        # `facts=()` and the keyword's absence are one declaration; `facts=("strength",)`
        # and the member `supervised` are one declaration.
        for shape in S.ALL_SHAPES:
            for encoding in S.ENCODINGS:
                with self.subTest(shape=shape, encoding=encoding, facts=()):
                    self.assertEqual(
                        self.spec_of(encoding, shape, facts=()),
                        self.spec_of(encoding, shape, facts=None),
                        "an empty declaration is the absence of the keyword, and neither is "
                        "a defaulting of a fact (strength-design.md §A.5)",
                    )
                with self.subTest(shape=shape, encoding=encoding, member=S.STRENGTH_ON):
                    self.assertEqual(
                        self.spec_of(encoding, shape, facts=(S.STRENGTH_FIELD,)),
                        self.ep("observation_spec")(
                            build(encoding, shape=shape, strength=S.STRENGTH_ON)
                        ),
                        "`facts=('strength',)` and `strength='supervised'` are one "
                        "declaration, so the two spellings cannot drift apart "
                        "(strength-design.md §A.5)",
                    )


class FEA13Injection(FEA13Case):
    """The injection attaches exactly the declared facts, to a copy."""

    def test_fea13_6_stated_attaches_exactly_the_declared_facts(self):
        """FEA-13.6 `features.stated(model, readout, encoder=..., shape=..., values=...)`
        returns a **fresh** mapping carrying exactly the facts that encoder declares --
        `strength` from the estimator (supplied here, so no torch is loaded), `bet_size`
        from `to_call ÷ the shape's chips in play` (40/200/600), the two opponent readings
        from `values` -- encodes to a value the slot agrees with, leaves the readout it was
        handed untouched, hands an encoder that declares nothing the readout itself, and
        **refuses by name** a declared fact it cannot produce (`strength-design.md` §B.2,
        §B.3, `ASM-47`)."""
        stated = self.ep("stated")
        for shape in S.ALL_SHAPES:
            chips = CHIPS_IN_PLAY[shape]
            plain = S.shaped_readout(shape, to_call=chips // 4)
            encoder = self.declaring(S.FLAT, shape, INJECTED)
            with self.subTest(shape=shape):
                injected = stated(
                    None, plain, encoder=encoder, shape=shape,
                    values=self.supplied(None),
                )
                self.assertIsNot(
                    injected, plain,
                    "the injection is a fresh mapping and never the caller's own "
                    "(ASM-47, strength-design.md §B.2): %r" % (type(injected).__name__,),
                )
                self.assertEqual(
                    S.without(injected, *INJECTED), plain,
                    "the injected mapping is the readout plus the declared facts and "
                    "nothing else (ASM-47): %r" % (sorted(injected),),
                )
                for fact in INJECTED:
                    self.assertIn(
                        fact, injected,
                        "every fact the encoder declares is injected (strength-design.md "
                        "§B.2): %r missing from %r" % (fact, sorted(injected)),
                    )
                self.assertEqual(
                    injected["bet_size"], 0.25,
                    "bet_size is the amount to call over the shape's %d chips in play -- "
                    "%d / %d = 0.25 -- and not a chip count (strength-design.md §A.1): %r"
                    % (chips, chips // 4, chips, injected["bet_size"]),
                )
                for fact in ("strength",) + tuple(ADDED[1:]):
                    self.assertEqual(
                        injected[fact], 0.5,
                        "the fact %r is the value the estimator or the caller supplied, "
                        "unchanged (strength-design.md §B.2): %r"
                        % (fact, injected[fact]),
                    )
                slots = S.floats(self.ep("encode")(encoder, injected))
                base = S.DECLARED_BY_SHAPE[shape][S.FLAT][0]
                self.assert_floats(
                    slots[base:base + 4], [0.5, 0.25, 0.5, 0.5],
                    "the four injected slots, in the declared order (%r)" % (INJECTED,),
                )
                self.assertNotIn(
                    "bet_size", plain,
                    "the readout the caller handed in is never mutated (ASM-47, "
                    "test_join_purity.py): %r" % (sorted(plain),),
                )
        # A readout that carries a declared key already is not double-counted: the copy
        # overrides it with the produced value.
        shape = S.DEFAULT_SHAPE
        stale = S.shaped_readout(shape, extra={"bet_size": 0.75})
        refreshed = self.ep("stated")(
            None, stale, encoder=self.declaring(S.FLAT, shape, ("bet_size",)), shape=shape,
        )
        self.assertEqual(
            refreshed["bet_size"], stale["to_call"] / CHIPS_IN_PLAY[shape],
            "the injection produces the declared fact's value -- here 0.0, because no bet "
            "faces the first actor -- and never keeps the stale 0.75 the readout carried "
            "(strength-design.md §B.2): %r" % (refreshed["bet_size"],),
        )
        # An encoder that declares nothing is handed the readout itself.
        quiet = self.declaring(S.FLAT, shape, None)
        self.assertIs(
            self.ep("stated")(None, stale, encoder=quiet, shape=shape), stale,
            "an encoder that declares no fact needs no copy, so the readout is handed on "
            "unchanged (strength-design.md §B.2)",
        )
        # A declared fact with no producer is refused, never defaulted.
        opponent = self.declaring(S.FLAT, shape, ("opp_action",))
        exc = self.refuses(
            lambda: self.ep("stated")(
                None, S.shaped_readout(shape), encoder=opponent, shape=shape,
            ),
            words=("stated", "'opp_action'"),
        )
        self.assert_names(exc, "values")
        # ... and bet_size with no shape to divide by is refused too.
        self.refuses(
            lambda: self.ep("stated")(
                None, S.shaped_readout(shape),
                encoder=self.declaring(S.FLAT, shape, ("bet_size",)),
            ),
            words=("stated", "'bet_size'"),
        )


if __name__ == "__main__":  # pragma: no cover - a case file, run by pytest
    unittest.main()
