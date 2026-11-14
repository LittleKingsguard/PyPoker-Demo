"""FEA-12 -- the denominator refusal: a shape row with no normaliser is refused by name.

``docs/L2/features/normalisers.md`` §1-§4 (the owner of this refusal);
``docs/L1/normalisation.md`` §4 (the same rule at L1, and the name of the class);
``docs/L3/features/errors.md`` §2-§3 (the class hierarchy and the message grammar);
``docs/L2/features/shapes.md`` §2, §6; ``docs/L3/features/flat-numeric.md`` §4 (the five
denominators); ``docs/L3/features/encoder.md`` §4 (the declaration table);
``strata/decisions.md`` D-61; ``docs/L1/battery.md`` §5; ``docs/L3/features/README.md`` §3.

D-61 makes normalisation the input term the whole change is about, and
``normalisation.md`` §4 names its structural guard: a magnitude block whose shape row
declares no denominator is **refused**, never scaled by a substituted denominator, never
clamped, never defaulted.  ``normalisers.md`` §1 states the rule and §2 the refusal, §3
fixes *when* it is raised -- while the declaration for that shape is built, so
`build_encoder`, `observation_spec` and `encodings()` all reach it through the declaration
and nothing on `encode`'s hot path re-checks it -- and §4 states the consequence the
control case exists for: all three declared rows carry all five normalisers, so no
declared shape reaches the refusal at all.

Three cases hold it:

* FEA-12.1 for **both** encodings and **all three** rows, a row whose whole
  ``normalisers`` mapping is removed is refused as an `InvalidReadout` naming
  `build_encoder`, the argument `shape`, the declared shape, the word ``normalisers``, all
  five normaliser keys and all four block names -- and, for the default row only, so is
  `features.encodings()`, which is the evidence the refusal happens while the declaration
  is built rather than per observation (``normalisers.md`` §3);
* FEA-12.2 on the six-seat row, each of the five keys removed **alone** is refused with
  that key quoted, the **block** whose denominator it is named (``stack``→``stacks``,
  ``pot``→``pot``, ``to_call``→``to_call``, ``amount``→``limit``, ``count``→``limit``) and
  the shape named, so a case can tell the key from the block (``normalisers.md`` §2);
* FEA-12.3 the control: with the catalogue untouched, all three rows still build on both
  encodings, still declare the width and dtype the design gives them, and still emit every
  slot of one fixed invented readout at the value the design's own numbers produce -- so
  the guard cannot be met by refusing everything (``normalisers.md`` §4, D-61).

**The one declared exception to "the battery reaches only the seven declared names".**
Every other file in this battery drives `docs/L2/features/surface.md` §3-§9 and nothing
below it (``docs/L3/features/README.md`` §3).  These cases cannot: §4 says no declared row
omits a denominator, and ``battery.md`` §5 hands exactly this guard to the module battery
("`tests/features/` exercises that guard at the block level where a row without one can be
built").  So this family reads `features.declarations.SHAPE_ROWS` -- the module-level
`shape name -> dict` catalogue -- **doctors one row in process** (a missing
``normalisers`` mapping, or one missing key), asserts the refusal the design states, and
**restores the row exactly in a `finally`**: a `contextlib.contextmanager` saves the row's
own mapping (or a copy of it, put back into the same mapping) and no case leaves a doctored
row behind, so the catalogue is value-for-value what it was when the case began
(``normalisers.md`` §4, ``battery.md`` §5, ``guardrails.md`` G11).

**This is also the one family that asserts an exception class**, because
``normalisation.md`` §4 (and ``normalisers.md`` §2) name it: the refusal is
`features.errors.InvalidReadout`, a subclass of `features.errors.FeaturesError`, and it is
never the `KeyError` a mistyped table raises.  The classes are not module-level names of
the package and are not surface (``errors.md`` §2, ``README.md`` §3), so FEA-12 reads them
from `features.errors` lazily, exactly as it reads the catalogue.  That one read is the
whole of the family's second declared exception to the seven names.

Nothing else is asserted about the refusal: the message is matched as **plain
substrings** -- the entry point, the argument, the shape, the block, the quoted key and the
words "cannot be normalised" -- and never as a sentence and never by position
(``errors.md`` §3).  No number below is re-derived from the module under test: every
denominator is the design's five (``normalisers.md`` §1, ``flat-numeric.md`` §4), and every
offset, width, id and bucket is `_features_support`'s own statement of the design.
"""

import contextlib
import importlib
import os
import sys
import unittest

try:  # discovered as part of a tests.features package
    from . import _features_support as S
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _features_support as S  # noqa: E402


# --------------------------------------------------------------------------
# The design's own numbers, restated once for this battery (normalisers.md §1)
# --------------------------------------------------------------------------
#: The five amount normalisers each declared row carries, under ``engine``'s own key names:
#: ``stack``, ``pot``, ``to_call``, ``amount`` (the bet size in force) and ``count`` (the
#: bet-or-raise actions this street).  They are the shape's, and only the pot's moves
#: between the two uncapped rows, exactly three times ``no-limit-100``'s on the six-seat row
#: because that row's chips in play are 600 (``normalisers.md`` §1, §4,
#: ``flat-numeric.md`` §4, ``normalisation.md`` §2, ``sizing.md`` §5).
NORMALISERS = {
    S.DEFAULT_SHAPE: {"stack": 20, "pot": 40, "to_call": 20, "amount": 4, "count": 4},
    S.SECOND_SHAPE: {"stack": 100, "pot": 200, "to_call": 100, "amount": 100, "count": 50},
    S.THIRD_SHAPE: {"stack": 100, "pot": 600, "to_call": 100, "amount": 100, "count": 50},
}

#: The five keys, in the order the catalogue declares them (``normalisers.md`` §1).
KEYS = ("stack", "pot", "to_call", "amount", "count")

#: ``(normaliser key, the block whose one denominator it is)``, as ``normalisers.md`` §2's
#: table states it: the stacks block divides by ``stack``, the pot and the amount to call by
#: their own keys, and **both** slots of the limit block divide -- the bet size in force by
#: ``amount`` and the bet-or-raise count by ``count`` (``flat-numeric.md`` §4).
BLOCK_OF_KEY = (
    ("stack", "stacks"),
    ("pot", "pot"),
    ("to_call", "to_call"),
    ("amount", "limit"),
    ("count", "limit"),
)

#: The four blocks that read one of the five denominators, one name each: the blocks a row
#: with no ``normalisers`` mapping at all leaves without a denominator (``normalisers.md``
#: §2, ``normalisation.md`` §2's block table).
BLOCKS = ("stacks", "pot", "to_call", "limit")

#: The documents every assertion message below cites, so a failure says which contract it
#: measured and not only what differed.
DESIGN = (
    "docs/L2/features/normalisers.md §1-§4, docs/L1/normalisation.md §4, "
    "docs/L3/features/errors.md §2-§3, strata/decisions.md D-61, docs/L1/battery.md §5"
)

#: What the absent-mapping refusal's message must contain, as plain substrings
#: (``normalisers.md`` §2's first row): the entry point and its argument, the shape, the
#: word ``normalisers``, all four block names and all five keys -- and, in every case, that
#: the readout cannot be normalised.
ABSENT_WORDS = ("build_encoder", "shape", "normalisers") + BLOCKS + KEYS + (
    "cannot be normalised",
)

#: The two-seat rows' stacks for the one fixed invented readout: two entries, because the
#: two-seat rows declare two seats.  Their values are the writer's own (``battery.md`` §4,
#: D-15); only their *count* is the contract's (``seats.md`` §3, ASM-44).
TWO_SEAT_STACKS = (17, 17)


# --------------------------------------------------------------------------
# The one fixed invented readout, and the value the design gives every slot of it
# --------------------------------------------------------------------------
def stacks_of(shape):
    """The fixed readout's stacks on one row: two entries, or six on the third row.

    ``S.shaped_readout`` already defaults to the row's own count; this states it explicitly
    because a case asserts one stack slot per seat, and a two-stack readout handed to a
    six-seat encoder is exactly the accident ``seats.md`` §3 forbids (ASM-44).
    """
    return S.SIX_SEAT_STACKS if shape == S.THIRD_SHAPE else TWO_SEAT_STACKS


def fixed_readout(shape):
    """The one invented readout every row is encoded with in FEA-12.3.

    A flop with every amount the design reads: seat 0 acting with the button, ``Td 2c`` in
    hand, ``Jh 7c 2d`` on the board, the row's own stacks, a pot of 6, nothing to call, a
    bet size in force of 2 and no raises yet, and an empty history.  The values are the
    writer's own (``battery.md`` §4, D-15); only their shapes are the contract's, and the
    per-seat facts are the row's own width.
    """
    return S.shaped_readout(
        shape,
        street="flop",
        seat=(0, True),
        hole=("Td", "2c"),
        board=("Jh", "7c", "2d"),
        stacks=stacks_of(shape),
        pot=6,
        to_call=0,
        limit=(2, 0),
        history=[],
    )


def dense_expectation(shape):
    """The dense observation the fixed readout must encode to, block by block.

    Every value is the design's: a magnitude slot is ``numerator / denominator`` at the
    row's own normaliser (``normalisers.md`` §1, ``flat-numeric.md`` §4), and every other
    slot is an indicator the layout fixes (``flat-numeric.md`` §2-§5).  The stacks block is
    one slot per seat holding ``stacks[i] / stack normaliser`` on **all three** rows: the
    six-seat row declares ``seat-order``, and the two-seat rows declare ``actor-first`` with
    the acting seat 0, so the acting seat's stack is the first entry on every row and the
    two orders agree for this readout -- stated once here instead of derived twice
    (``seats.md`` §3, ``flat-numeric.md`` §4, ASM-44).
    """
    divisors = NORMALISERS[shape]
    seats = S.SEATS[shape]
    stacks = stacks_of(shape)
    undealt = S.CARD_SLOT * (5 - len(fixed_readout(shape)["board"]))
    return {
        "street": S.street_onehot("flop"),
        # the seat block: `index-flag` writes index / (seats - 1) then the button flag -- the
        # acting seat is 0 on both two-seat rows, so the pair is (0.0, 1.0) -- and `one-hot`
        # sets the acting seat's own slot (flat-numeric.md §4, seats.md §3, ASM-44).
        "seat": [0.0, 1.0] if seats == 2 else [1.0] + [0.0] * (seats - 1),
        "hole": S.card_slot("Td") + S.card_slot("2c"),
        "board": [value for card in ("Jh", "7c", "2d") for value in S.card_slot(card)]
        + [0.0] * undealt,
        "stacks": [value / divisors["stack"] for value in stacks],
        "pot": [6 / divisors["pot"]],
        "to_call": [0.0],
        "limit": [2 / divisors["amount"], 0.0],
        "history": [0.0] * (S.HISTORY_SLOT_WIDTH * S.CAPACITY[shape]),
    }


def token_expectation(shape):
    """The token observation the fixed readout must encode to, token by token.

    Every id is the design's: the street, card, seat and bucket ids of
    ``card-tokens.md`` §3-§4 as ``_features_support`` restates them -- the ladder is the
    row's, so the three rows bucket their own amounts (``capacity.md`` §2, ASM-44) -- and
    the pad 0 past the deal and past the history.
    """
    seats = S.SEATS[shape]
    stacks = stacks_of(shape)
    if seats == 2:
        seat = [S.SEAT_INDEX_BASE + 0, S.SEAT_FLAG_BASE + 1]
    else:
        # the six-seat row declares the one-hot mode: the acting seat's own id at its slot,
        # the pad everywhere else (src/features/encode.py's `_seat_ids`, seats.md §3).
        seat = [S.PAD] * seats
        seat[0] = S.SEAT_TOKEN_BASE + 0
    return {
        "street": [S.STREET_IDS["flop"]],
        "seat": seat,
        "hole": [S.card_id("Td"), S.card_id("2c")],
        "board": [S.card_id(card) for card in ("Jh", "7c", "2d")]
        + [S.PAD] * (5 - 3),
        "stacks": [S.bucket_on(shape, "stacks", value) for value in stacks],
        "pot": [S.bucket_on(shape, "pot", 6)],
        "to_call": [S.bucket_on(shape, "to_call", 0)],
        # the two limit slots are bucketed by the ladders `_features_support` names after the
        # design's own words for them -- the bet size in force ("bet") and the bet-or-raise
        # actions this street ("raises") -- while their *denominators* are the ``amount`` and
        # ``count`` keys (card-tokens.md §4, normalisers.md §1, flat-numeric.md §4).
        "limit": [S.bucket_on(shape, "bet", 2), S.bucket_on(shape, "raises", 0)],
        "history": [S.PAD] * S.CAPACITY[shape],
    }


# --------------------------------------------------------------------------
# The plumbing the three cases share: the catalogue, doctored and restored
# --------------------------------------------------------------------------
class FEA12Case(S.FeaturesCase):
    """The declared catalogue, doctored in process for one case and restored exactly."""

    def catalogue(self):
        """`declarations.SHAPE_ROWS`: the one table these cases read and patch.

        ``_features_support``' promise that this battery reaches only the seven declared
        names is kept everywhere else; this family needs the catalogue itself, because a
        row without a denominator is **unreachable through any call** -- all three declared
        rows carry all five (``normalisers.md`` §4) -- so the guard can only be exercised by
        doctoring a row in process, which ``battery.md`` §5 hands to this battery and
        ``README.md`` §3 records as the declared exception.  A module or a table that is not
        there is one clean ``SurfaceAbsent`` naming it, never an ``AttributeError`` inside a
        case.
        """
        S.module()
        try:
            declarations = importlib.import_module("features.declarations")
        except Exception as exc:
            raise S.SurfaceAbsent(
                "surface absent: features.declarations is not importable, so no shape row "
                "can be doctored and the denominator refusal cannot be exercised "
                "(normalisers.md §2, errors.md §3, D-61): %s: %s"
                % (type(exc).__name__, exc)
            ) from exc
        rows = getattr(declarations, "SHAPE_ROWS", None)
        if rows is None:
            raise S.SurfaceAbsent(
                "surface absent: features.declarations.SHAPE_ROWS is not declared, and it "
                "is the one table a row without a denominator can be built in "
                "(normalisers.md §4, battery.md §5, D-61)"
            )
        return rows

    def row(self, shape):
        """One row of the catalogue, doctored in place by :meth:`doctored`."""
        rows = self.catalogue()
        row = rows.get(shape) if hasattr(rows, "get") else None
        if row is None:
            raise S.SurfaceAbsent(
                "surface absent: features.declarations.SHAPE_ROWS carries no %r row, so the "
                "denominator refusal cannot be exercised on it (normalisers.md §3, "
                "shapes.md §2, D-61)" % (shape,)
            )
        return row

    @contextlib.contextmanager
    def doctored(self, shape, key=None):
        """One row doctored in process and restored **exactly** in a ``finally``.

        ``key`` is ``None`` for the whole ``normalisers`` mapping and a normaliser key for
        that one entry.  What is saved is the row's own mapping object (restored as it was)
        or a copy of the mapping's content, put back into the **same** mapping after the
        window, so the catalogue a case leaves behind is the one it found -- value for
        value and object for object: no case may leak a doctored row into the next one
        (``normalisers.md`` §4, ``battery.md`` §5, ``guardrails.md`` G11).
        """
        row = self.row(shape)
        if "normalisers" not in row:  # nothing to remove, and nothing to put back
            yield row
            return
        normalisers = row["normalisers"]
        if key is None:
            row.pop("normalisers")
            try:
                yield row
            finally:
                row["normalisers"] = normalisers
            return
        saved = dict(normalisers)
        normalisers.pop(key, None)
        try:
            yield row
        finally:
            normalisers.clear()
            normalisers.update(saved)

    def error_classes(self):
        """`features.errors.FeaturesError` and `.InvalidReadout`: the two classes asserted.

        The classes live below an entry point and are not module-level names of the package
        (``errors.md`` §2, ``README.md`` §3), so this is the family's second declared read
        below the seven names -- and it is the one place a class is asserted at all, because
        ``normalisation.md`` §4 names `InvalidReadout` for a fact that cannot be normalised.
        """
        S.module()
        try:
            errors = importlib.import_module("features.errors")
        except Exception as exc:
            raise S.SurfaceAbsent(
                "surface absent: features.errors is not importable, and normalisation.md §4 "
                "names the refusal it holds (InvalidReadout) for a fact that cannot be "
                "normalised (errors.md §2, D-61): %s: %s" % (type(exc).__name__, exc)
            ) from exc
        base = getattr(errors, "FeaturesError", None)
        refusal = getattr(errors, "InvalidReadout", None)
        if base is None or refusal is None:
            raise S.SurfaceAbsent(
                "surface absent: features.errors declares no FeaturesError/InvalidReadout "
                "pair, which is the refusal normalisation.md §4 names for a block with no "
                "denominator (normalisers.md §2, errors.md §2)"
            )
        return base, refusal

    def refused(self, where, call):
        """Run one call that must refuse, catching **any** `Exception`, and return it.

        The catch is deliberately wide: the failure this family is written against is a
        ``KeyError`` escaping a mistyped table, so a helper that caught only this module's
        own error family would let the crash out as an *error* instead of failing the case
        with the message that says what the contract wants (``errors.md`` §1-§3, D-61).
        """
        try:
            call()
        except S.SurfaceAbsent:  # this battery's own failure, never the module's refusal
            raise
        except Exception as exc:  # the refusal the design asks for, and the crash it is not
            return exc
        self.fail(
            "%s was accepted, and a shape row with no denominator for a magnitude block is "
            "refused rather than defaulted or scaled by a substituted divisor (%s)"
            % (where, DESIGN)
        )

    def refused_build(self, encoding, shape):
        """`build_encoder(encoding, shape=shape)` on a doctored row, caught as one Exception."""
        build = self.ep("build_encoder")
        return self.refused(
            "build_encoder(%r, shape=%r)" % (encoding, shape),
            lambda: build(encoding, shape=shape),
        )

    def assert_refusal(self, exc, where, *words):
        """The refusal is this module's own class, is not a crash, and names the contract.

        Three properties, all of them the design's: it is `InvalidReadout` below
        `FeaturesError` -- so a caller catches "this module refused me" and never a mistyped
        table (``normalisers.md`` §2, ``errors.md`` §2, ``normalisation.md`` §4); it is not
        a `KeyError`/`LookupError`/`TypeError`, because a row's own table is the
        declaration's defect and not the caller's bad argument (``errors.md`` §1); and each
        word below is in its message as a **plain substring**, which is the tolerance
        ``errors.md`` §3 gives the battery's match.
        """
        base, refusal = self.error_classes()
        self.assertIsInstance(
            exc, refusal,
            "%s raised %s, and the design's refusal for a block with no denominator is "
            "features.errors.InvalidReadout (normalisers.md §2, normalisation.md §4, "
            "errors.md §2, D-61): %s" % (where, type(exc).__name__, DESIGN),
        )
        self.assertIsInstance(
            exc, base,
            "%s raised %s, which is not a features.errors.FeaturesError -- a caller catches "
            "one class to know this module refused it, and a %s is a crash (errors.md §1-§2, "
            "normalisers.md §2, D-61): %s"
            % (where, type(exc).__name__, type(exc).__name__, DESIGN),
        )
        for crash in (KeyError, LookupError, TypeError):
            self.assertNotIsInstance(
                exc, crash,
                "%s raised %s, which is a %s: a catalogue row with no denominator is the "
                "declaration's own table and never the caller's argument, so it is refused "
                "below FeaturesError and not as a lookup or type crash (normalisers.md §2, "
                "errors.md §1-§3, D-61): %s"
                % (where, type(exc).__name__, crash.__name__, DESIGN),
            )
        text = str(exc)
        for word in words:
            self.assertIn(
                str(word), text,
                "%s: the refusal must name %r in its message -- the entry point, the "
                "argument 'shape', the declared shape, the block whose denominator is "
                "missing, the missing normaliser key quoted, and that the readout cannot be "
                "normalised (errors.md §3, normalisers.md §2, D-61): %r"
                % (where, str(word), text),
            )

    def assert_restored(self, encoding, shape):
        """The doctored row is back, and its declaration builds and declares its width again.

        A case that left a doctored row behind would change what every later case measures,
        so the restore is asserted and not assumed: the row carries the design's five
        normalisers value for value, and the encoder built from it declares the width the
        design gives that encoding on that shape (``normalisers.md`` §4, ``battery.md`` §5,
        ``guardrails.md`` G11).
        """
        row = self.row(shape)
        self.assertIn(
            "normalisers", row,
            "the %r row carries its normalisers mapping again once the doctored window "
            "closes, so no case leaks a row without one (%s)" % (shape, DESIGN),
        )
        self.assertEqual(
            dict(row.get("normalisers") or {}), NORMALISERS[shape],
            "the %r row's five normalisers are the design's again, value for value -- a "
            "doctored row left behind would change every later case (%s)"
            % (shape, DESIGN),
        )
        build = self.ep("build_encoder")
        try:
            encoder = build(encoding, shape=shape)
        except Exception as exc:
            self.fail(
                "build_encoder(%r, shape=%r) must build again on the restored row, and it "
                "raised %s: the catalogue is the one it was before the doctored window (%s)"
                % (encoding, shape, type(exc).__name__, DESIGN)
            )
        spec = self.ep("observation_spec")(encoder)
        self.assertEqual(
            tuple(spec["shape"]), S.DECLARED_BY_SHAPE[shape][encoding],
            "the encoder built from the restored %r row declares the width the design gives "
            "%r on it (capacity.md §2, encoder.md §4, %s)"
            % (shape, encoding, DESIGN),
        )

    def assert_catalogue_intact(self):
        """Every declared row still carries the design's five normalisers, in every shape."""
        for shape in S.ALL_SHAPES:
            row = self.row(shape)
            self.assertEqual(
                dict(row.get("normalisers") or {}), NORMALISERS[shape],
                "the %r row carries the design's five normalisers -- the catalogue is what "
                "it was, so no earlier case leaked a doctored row into this one (%s)"
                % (shape, DESIGN),
            )


# --------------------------------------------------------------------------
# FEA-12.1 -- the whole mapping absent
# --------------------------------------------------------------------------
class FEA12MissingMapping(FEA12Case):
    """A row with no `normalisers` mapping at all is refused, by shape and by block."""

    def test_fea12_1_a_row_with_no_normalisers_mapping_is_refused_by_name(self):
        """FEA-12.1 for both encodings and all three rows, a row whose whole
        ``normalisers`` mapping is removed makes `build_encoder(encoding, shape=shape)`
        an `InvalidReadout` below `FeaturesError` -- never a `KeyError` -- naming
        `build_encoder`, the argument `shape`, the declared shape, the word
        ``normalisers``, all four block names (`stacks`, `pot`, `to_call`, `limit`) and all
        five keys (`stack`, `pot`, `to_call`, `amount`, `count`) and saying the readout
        cannot be normalised (normalisers.md §1-§2, normalisation.md §4, errors.md §2-§3,
        D-61).  The row is restored and rebuilds, and -- for the default row only --
        `features.encodings()` is refused too while it is doctored, which is the evidence
        the refusal is raised while the declaration is built and not per observation
        (normalisers.md §3, §4)."""
        for encoding in S.ENCODINGS:
            for shape in S.ALL_SHAPES:
                with self.subTest(encoding=encoding, shape=shape):
                    where = (
                        "build_encoder(%r, shape=%r) on a row with no normalisers mapping"
                        % (encoding, shape)
                    )
                    with self.doctored(shape) as row:
                        self.assertNotIn(
                            "normalisers", row,
                            "%s: the case removes the whole mapping, so no denominator of "
                            "any magnitude block survives the doctoring (%s)"
                            % (where, DESIGN),
                        )
                        exc = self.refused_build(encoding, shape)
                    self.assert_refusal(exc, where, shape, *ABSENT_WORDS)
                    self.assert_restored(encoding, shape)
        with self.subTest(entry_point="encodings", shape=S.DEFAULT_SHAPE):
            where = "encodings() with the default row carrying no normalisers mapping"
            with self.doctored(S.DEFAULT_SHAPE):
                exc = self.refused(where, self.ep("encodings"))
            self.assert_refusal(exc, where)
            catalogue = self.ep("encodings")()
            self.assertEqual(
                sorted(catalogue), sorted(S.ENCODINGS),
                "with the default row restored, encodings() publishes its two records again "
                "-- the refusal is the declaration's and not a state the module keeps "
                "(normalisers.md §3-§4, surface.md §3, %s)" % (DESIGN,),
            )
            for encoding in S.ENCODINGS:
                self.assertEqual(
                    tuple(catalogue[encoding]["shape"]),
                    S.DECLARED_BY_SHAPE[S.DEFAULT_SHAPE][encoding],
                    "and each restored record declares the default row's width for %r, so "
                    "the catalogue is the one the design publishes (surface.md §3, "
                    "capacity.md §2, %s)" % (encoding, DESIGN),
                )


# --------------------------------------------------------------------------
# FEA-12.2 -- one key absent, five times over
# --------------------------------------------------------------------------
class FEA12MissingKey(FEA12Case):
    """Each one missing normaliser key is refused, naming its block, its key and the shape."""

    def test_fea12_2_each_missing_normaliser_key_is_refused_naming_field_key_and_shape(self):
        """FEA-12.2 on the six-seat row (`six-seat-no-limit-100`, whose stack and amount
        normalisers are 100, its pot 600 and its count 50), for both encodings and for each
        of the five keys removed **alone**, `build_encoder(encoding, shape=shape)` is an
        `InvalidReadout` below `FeaturesError` whose message names `build_encoder`, the
        argument `shape`, the shape, the missing key **quoted with single quotes** (so a
        case can tell `'stack'` from the block ``stacks``), the block that key is the
        denominator of (`stack`→`stacks`, `pot`→`pot`, `to_call`→`to_call`,
        `amount`→`limit`, `count`→`limit`) and that the readout cannot be normalised
        (normalisers.md §1-§2, normalisation.md §4, errors.md §3, D-61).  The other four
        keys are measured to still be in the doctored row, so only one key was removed, and
        after each iteration the row is restored and rebuilds (normalisers.md §4,
        battery.md §5)."""
        shape = S.THIRD_SHAPE
        for encoding in S.ENCODINGS:
            for key, block in BLOCK_OF_KEY:
                with self.subTest(encoding=encoding, key=key):
                    where = (
                        "build_encoder(%r, shape=%r) on a row with no %r normaliser, whose "
                        "%r block has no denominator" % (encoding, shape, key, block)
                    )
                    with self.doctored(shape, key) as row:
                        remaining = row.get("normalisers") or {}
                        self.assertNotIn(
                            key, remaining,
                            "%s: the case removes exactly the %r key, so that block's "
                            "denominator is the one missing (%s)"
                            % (where, key, DESIGN),
                        )
                        for other in KEYS:
                            if other == key:
                                continue
                            self.assertIn(
                                other, remaining,
                                "%s: the other four normaliser keys are still in the "
                                "doctored row -- measured, not assumed, so the refusal below "
                                "is the one missing key's (%s)"
                                % (where, DESIGN),
                            )
                        exc = self.refused_build(encoding, shape)
                    self.assert_refusal(
                        exc, where,
                        "build_encoder", "shape", shape, "'%s'" % key, block,
                        "cannot be normalised",
                    )
                    self.assert_restored(encoding, shape)


# --------------------------------------------------------------------------
# FEA-12.3 -- the control: the declared rows still build and still emit their values
# --------------------------------------------------------------------------
class FEA12DeclaredRowsStillEmit(FEA12Case):
    """The guard cannot be met by refusing everything: the three rows still emit."""

    def test_fea12_3_the_three_declared_rows_still_build_and_still_emit_their_values(self):
        """FEA-12.3 with the catalogue untouched, on every row and both encodings: the
        encoder builds, `observation_spec` declares the width and dtype the design gives
        that pair, and one fixed invented readout -- a flop with the acting seat 0 and the
        button, `Td 2c`, `Jh 7c 2d`, the row's own stacks, pot 6, nothing to call, limit
        (2, 0) and an empty history -- encodes to exactly the design's numbers, block by
        block: every magnitude slot is its numerator over the row's own normaliser and every
        other slot is the indicator or id the layout fixes (normalisers.md §1, §4,
        flat-numeric.md §2-§5, card-tokens.md §2-§5, normalisation.md §4, D-61).  Nothing
        here is read from the module under test, and the rows' five normalisers are checked
        again at the end so no earlier case leaked a doctored row."""
        for shape in S.ALL_SHAPES:
            record = fixed_readout(shape)
            for encoding in S.ENCODINGS:
                with self.subTest(shape=shape, encoding=encoding):
                    build = self.ep("build_encoder")
                    encoder = build(encoding, shape=shape)
                    spec = self.ep("observation_spec")(encoder)
                    self.assertEqual(
                        tuple(spec["shape"]), S.DECLARED_BY_SHAPE[shape][encoding],
                        "observation_spec's shape is the design's width for %r on %r "
                        "(encoder.md §3-§4, capacity.md §2, %s)"
                        % (encoding, shape, DESIGN),
                    )
                    self.assertEqual(
                        spec["dtype"], S.DECLARED[encoding]["dtype"],
                        "and its dtype is the encoding's own, the same on every row "
                        "(encodings.md §1, encoder.md §3, %s)" % (DESIGN,),
                    )
                    observation = self.ep("encode")(encoder, record)
                    if encoding == S.FLAT:
                        values = S.floats(observation)
                        expected = dense_expectation(shape)
                        blocks = {field: (offset, width)
                                  for field, offset, width in S.flat_blocks(shape)}
                        compare = self.assert_floats
                    else:
                        values = S.ints(observation)
                        expected = token_expectation(shape)
                        blocks = {field: (offset, width)
                                  for field, offset, width in S.token_blocks(shape)}
                        compare = self.assert_ints
                    self.assertEqual(
                        len(values), sum(width for _offset, width in blocks.values()),
                        "the observation is exactly as wide as the design's block table "
                        "says for %r on %r (capacity.md §2, encoder.md §4, %s)"
                        % (encoding, shape, DESIGN),
                    )
                    for field in S.FIELDS:
                        offset, width = blocks[field]
                        compare(
                            values[offset:offset + width],
                            expected[field],
                            "%r, the %r block of an observation on %r, slots %d-%d: the "
                            "design's own numbers, so the guard against a row without a "
                            "denominator does not move what a declared row emits (%s)"
                            % (encoding, field, shape, offset, offset + width, DESIGN),
                        )
        self.assert_catalogue_intact()


if __name__ == "__main__":
    unittest.main()
