"""FEA-11 -- the declared bounds: every slot of every observation is inside one.

``docs/L3/features/flat-numeric.md`` §4; ``docs/L3/features/card-tokens.md`` §6;
``docs/L3/features/encoder.md`` §5; ``docs/L2/features/surface.md`` §6;
``docs/L1/seats.md`` §3; ``docs/L1/assumptions.md`` ASM-42, ASM-44;
``strata/decisions.md`` D-60, D-61 and ``strata/records/input-collapse-rca.md``.

D-61 makes the bound a **declared** property of the layout: a `flat-numeric` slot carries
a number in `[0, 1]` and a `card-tokens` slot an integer id in `[0, vocabulary)`, and a
scaled block whose numerator exceeds the shape's normaliser saturates at its declared
high by the layout's rule -- never silently, never by a run, never by a writer
(``flat-numeric.md`` §4).  Why that matters is the record: the net-chip models' trunks
were dead and their input path collapsed at the ReLU (D-60,
``strata/records/input-collapse-rca.md``), so the magnitude an observation carries is the
first term of that chain.

Four cases hold the bound:

* FEA-11.1 the bound table covers **every** writer tag and every block of every declared
  shape's declaration, and the blocks partition every slot -- so no slot of any
  observation is outside a declared bound;
* FEA-11.2 each of the five scaled slot classes emits exactly its declared high and not
  more for an amount above the normaliser, on every row, while a half-normaliser amount
  is 0.5 and a zero amount is 0.0;
* FEA-11.3 an `exact` block emits nothing but `0.0` and `1.0`;
* FEA-11.4 the seat block's index slot is `index / (seats - 1)` and every slot of the
  block is in `[0, 1]`.

FEA-11.1 is deliberately the one case here that reads the layout's two tables
(`declarations.bounds()` and `encode.WRITERS`) instead of the seven names: coverage --
"every slot is inside a declared bound" -- is a statement about the declaration itself
and is not decidable through any call (`docs/L3/features/README.md` §3, D-12).  It asserts
coverage and never the tables' spelling, so a tag renamed on both sides passes.  The other
three cases reach the module through its seven declared names only.

No case asserts an exception class -- the classes are this module's freedom
(``errors.md`` §2) -- and no case re-derives a divisor or an edge: every number below is
the design's (``flat-numeric.md`` §4, ``card-tokens.md`` §6).
"""

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
# The design's own numbers, restated once for this battery (flat-numeric.md §4)
# --------------------------------------------------------------------------
#: The five amount normalisers each declared row divides by, under ``engine``'s own key
#: names: ``stack``, ``pot``, ``to_call``, ``amount`` (the bet size in force) and
#: ``count`` (the bet-or-raise actions this street).  They are the shape's, and only the
#: pot's moves between the two uncapped rows (``flat-numeric.md`` §4, ``sizing.md`` §5).
NORMALISERS = {
    S.DEFAULT_SHAPE: {"stack": 20, "pot": 40, "to_call": 20, "amount": 4, "count": 4},
    S.SECOND_SHAPE: {"stack": 100, "pot": 200, "to_call": 100, "amount": 100, "count": 50},
    S.THIRD_SHAPE: {"stack": 100, "pot": 600, "to_call": 100, "amount": 100, "count": 50},
}

#: The five scaled slot classes as ``(block, position, normaliser key)``: the stacks block
#: is one slot per seat and every other scaled block is read at the position given, so a
#: case walks the classes the design declares and not the widths of one row
#: (``flat-numeric.md`` §2, §4, ``seats.md`` §3).
SCALED = (
    ("stacks", None, "stack"),
    ("pot", 0, "pot"),
    ("to_call", 0, "to_call"),
    ("limit", 0, "amount"),
    ("limit", 1, "count"),
)

#: The four dense writers whose value cannot leave `{0.0, 1.0}` by construction: a street
#: one-hot, the seat block's two declared modes, the 17-wide card slot and the history
#: slot (``flat-numeric.md`` §2-§5, D-61).
EXACT_BLOCKS = ("street", "seat", "hole", "board", "history")

#: The three policies a bound record may declare (``declarations.py``, D-61).
POLICIES = ("saturate", "exact", "id")


def amount(divisor, factor):
    """``factor`` times one normaliser, as the integer a readout carries.

    ``factor`` is 0, a half, one or twenty: every normaliser is even, so the half is a
    whole number of chips and the expected value is exactly 0.0, 0.5, 1.0 or the block's
    declared high (``flat-numeric.md`` §4).
    """
    return int(divisor * factor)


def observation_of(self, encoding, shape, record):
    """One observation, from an encoder built by name on one shape."""
    return self.ep("encode")(self.ep("build_encoder")(encoding, shape=shape), record)


class FEA11Case(S.FeaturesCase):
    """The blocks of one row, read as offsets, and a readout placed at its divisors."""

    def blocks(self, shape):
        """One row's dense block table, as ``field -> (offset, width)`` (flat-numeric.md §2)."""
        return {field: (offset, width) for field, offset, width in S.flat_blocks(shape)}

    def placed(self, shape, factor, **facts):
        """A readout of ``shape`` whose five amount facts sit at ``factor`` x their divisors.

        The two per-seat facts are the row's own width, so the same case walks all three
        rows without handing a two-stack readout to a six-seat encoder (``seats.md`` §3,
        ASM-44).  Anything else the caller names -- a street, a history -- is the
        caller's (``battery.md`` §4, D-15).
        """
        divisors = NORMALISERS[shape]
        stack = amount(divisors["stack"], factor)
        return S.shaped_readout(
            shape,
            stacks=(stack,) * S.SEATS[shape],
            pot=amount(divisors["pot"], factor),
            to_call=amount(divisors["to_call"], factor),
            limit=(amount(divisors["amount"], factor),
                   amount(divisors["count"], factor)),
            **facts
        )


class FEA11DeclaredBounds(FEA11Case):
    """The bound table covers every writer and every block of every declaration."""

    def tables(self):
        """`declarations.bounds` and `encode.WRITERS`: the layout's two closed tables.

        ``_features_support``' promise that this battery touches no submodule is kept
        everywhere else; this one case needs the declaration itself, because "no slot is
        outside a declared bound" is a statement about the table and not about a call
        (`docs/L3/features/README.md` §3, D-12, D-61).  A table that is not there is one
        clean ``SurfaceAbsent`` naming it, never an ``AttributeError`` inside a case.
        """
        S.module()
        layouts = importlib.import_module("features.declarations")
        writers = importlib.import_module("features.encode")
        bound_of = getattr(layouts, "bounds", None)
        tags = getattr(writers, "WRITERS", None)
        if bound_of is None or tags is None:
            raise S.SurfaceAbsent(
                "the layout declares no bound table: features.declarations.bounds and "
                "features.encode.WRITERS are what say every block's values end at a "
                "declared high (D-61, flat-numeric.md §4)"
            )
        return bound_of, tags, layouts

    def test_fea11_1_the_bound_table_covers_every_writer_and_every_slot(self):
        """FEA-11.1 the bound table's tags are exactly the writers WRITERS closes over, so
        no block of any encoding on any row names a writer whose bound is undeclared; a
        dense record is `(0.0, 1.0)` under `saturate` or `exact` and a token record is
        `(0, vocabulary)` under `id`; and the blocks of each of the six declarations
        partition that declaration's width, so every slot of every observation is inside
        exactly one block and every one of those blocks has a declared bound
        (flat-numeric.md §4, card-tokens.md §6, encoder.md §4, D-61)."""
        bound_of, writers, layouts = self.tables()
        self.assertTrue(
            callable(bound_of),
            "the bound is read through an accessor, so a caller's edit of one mapping "
            "cannot reach the next caller (guardrails.md G11): %r" % (bound_of,),
        )
        table = bound_of()
        self.assertEqual(
            sorted(table), sorted(writers),
            "the bound table's tags are exactly the fourteen writers WRITERS closes over "
            "-- a writer with no bound is a slot outside every bound (D-61, "
            "flat-numeric.md §4, card-tokens.md §6): %r against %r"
            % (sorted(table), sorted(writers)),
        )
        for tag, record in table.items():
            with self.subTest(tag=tag):
                self.assertEqual(
                    len(record), 3,
                    "a bound is one record of (low, high, policy) for the writer tag %r "
                    "(D-61): %r" % (tag, record),
                )
                low, high, policy = record
                self.assertIn(
                    policy, POLICIES,
                    "the policy of %r is one of the three the layout declares -- a scaled "
                    "block saturates, a one-hot or index block is exact by construction, "
                    "and a token block emits an id (D-61): %r" % (tag, policy),
                )
                if policy == "id":
                    self.assertEqual(
                        low, 0,
                        "a token block's ids start at the pad, the lowest id the row's "
                        "vocabulary holds (card-tokens.md §3, §6): %r" % (record,),
                    )
                    self.assertEqual(
                        high, "vocabulary",
                        "a token block's high is the **shape row's** vocabulary and never "
                        "a number of the table's -- 96 at two seats, 102 at six "
                        "(card-tokens.md §6, capacity.md §4, D-61): %r" % (record,),
                    )
                else:
                    self.assertEqual(
                        (low, high), (0.0, 1.0),
                        "every dense block's bound is the unit interval, whichever policy "
                        "holds its values there (flat-numeric.md §4, D-61): %r" % (record,),
                    )
        covered = 0
        for encoding in S.ENCODINGS:
            for shape in S.ALL_SHAPES:
                record = layouts.declaration(encoding, shape)
                width = record["shape"][0]
                with self.subTest(encoding=encoding, shape=shape):
                    self.assertEqual(
                        tuple(record["shape"]), S.DECLARED_BY_SHAPE[shape][encoding],
                        "the declaration's width is the battery's own statement of it "
                        "(capacity.md §2, encoder.md §4): %r against %r"
                        % (tuple(record["shape"]), S.DECLARED_BY_SHAPE[shape][encoding]),
                    )
                    self.assertEqual(
                        len(record["blocks"]), len(S.FIELDS),
                        "one block per carried field, in the field order "
                        "(encoder.md §3.1, §4): %r blocks" % (len(record["blocks"]),),
                    )
                    holders = [0] * width
                    for field, offset, block_width, writer, reads, params in record["blocks"]:
                        with self.subTest(encoding=encoding, shape=shape, field=field):
                            self.assertIn(
                                writer, table,
                                "%r's block names the writer %r, and every writer has a "
                                "declared bound (D-61, encoder.md §5): %r"
                                % (field, writer, sorted(table)),
                            )
                            self.assertGreaterEqual(
                                offset, 0,
                                "%r starts inside the observation (encoder.md §4): %r"
                                % (field, offset),
                            )
                            self.assertLessEqual(
                                offset + block_width, width,
                                "%r ends inside the observation: %d + %d against a width of "
                                "%d (encoder.md §4, capacity.md §2)"
                                % (field, offset, block_width, width),
                            )
                            for slot in range(offset, offset + block_width):
                                holders[slot] += 1
                            covered += block_width
                    self.assertEqual(
                        holders, [1] * width,
                        "the declaration's blocks partition its %d slots -- every slot in "
                        "exactly one block, and every block's writer has a declared bound, "
                        "so no slot of a %r observation is outside one (D-61, "
                        "flat-numeric.md §4, card-tokens.md §6): %r"
                        % (width, encoding, holders),
                    )
        self.assertGreater(
            covered, 0,
            "the six declarations hold slots at all, so the totality above is not a "
            "statement about nothing (D-61): %d slots" % (covered,),
        )


class FEA11ScaledSaturation(FEA11Case):
    """A scaled block emits its declared high and not more."""

    def test_fea11_2_every_scaled_block_emits_its_high_and_not_more(self):
        """FEA-11.2 for each of the five scaled slot classes and each declared row, an
        amount at or above the row's normaliser emits exactly 1.0 -- the block's declared
        high, not 5.0 and not 25.0 -- a half-normaliser amount emits 0.5 and a zero
        amount 0.0, and no slot of the whole observation leaves [0, 1]: a reachable 1.0
        (a six-seat to_call of 100, a fixed-limit bet of 4) is legal and not an error
        (flat-numeric.md §4, D-61, sizing.md §5)."""
        for shape in S.ALL_SHAPES:
            divisors = NORMALISERS[shape]
            blocks = self.blocks(shape)
            for factor, expected in ((0, 0.0), (0.5, 0.5), (1, 1.0), (20, 1.0)):
                record = self.placed(shape, factor)
                values = S.floats(observation_of(self, S.FLAT, shape, record))
                for field, position, key in SCALED:
                    offset, width = blocks[field]
                    slots = range(width) if position is None else (position,)
                    with self.subTest(shape=shape, field=field, divisor=divisors[key],
                                      factor=factor):
                        self.assert_floats(
                            [values[offset + slot] for slot in slots],
                            [expected] * len(slots),
                            "the %r block's slots of an amount %d x the row's %s divisor "
                            "of %d: %s is the block's declared high, never the magnitude "
                            "the division produces (flat-numeric.md §4, D-61)"
                            % (field, factor, key, divisors[key], expected),
                        )
                with self.subTest(shape=shape, factor=factor, whole="observation"):
                    self.assertGreaterEqual(
                        min(values), 0.0,
                        "no dense slot of a readout placed at %d x the normalisers is "
                        "negative (flat-numeric.md §4, D-61): %r" % (factor, min(values)),
                    )
                    self.assertLessEqual(
                        max(values), 1.0,
                        "and none exceeds the high the layout declares, on any row: the "
                        "bound is the layout's and not the run's (flat-numeric.md §4, "
                        "card-tokens.md §6, D-61): %r" % (max(values),),
                    )


class FEA11ExactBlocks(FEA11Case):
    """An exact block holds `0.0` and `1.0` and nothing else."""

    def test_fea11_3_an_exact_block_holds_only_zero_and_one(self):
        """FEA-11.3 with every amount at its own divisor, each `exact` block of each
        declared row -- the street one-hot, the seat block in whichever mode the row
        declares, the two card blocks and the history one-hots -- holds only 0.0 and 1.0,
        and so does every slot of the whole observation: the bound is a checked statement
        for these writers and a clamp only for the three scaled ones (flat-numeric.md
        §2-§5, seats.md §3, D-61)."""
        for shape in S.ALL_SHAPES:
            blocks = self.blocks(shape)
            record = self.placed(shape, 1, street="river",
                                 history=S.history_entries(3))
            values = S.floats(observation_of(self, S.FLAT, shape, record))
            for field in EXACT_BLOCKS:
                offset, width = blocks[field]
                block = values[offset:offset + width]
                with self.subTest(shape=shape, field=field):
                    self.assertTrue(
                        set(block) <= {0.0, 1.0},
                        "every slot of the %r block is 0.0 or 1.0, so its declared bound "
                        "is a statement about the writer rather than a clamp on it "
                        "(flat-numeric.md §2-§5, D-61): %r"
                        % (field, sorted(set(block) - {0.0, 1.0})[:6]),
                    )
                    self.assertIn(
                        1.0, block,
                        "and the block is live for this readout, so the subset above is "
                        "not the statement a dead block makes (flat-numeric.md §2): %r"
                        % (block[:8],),
                    )
            with self.subTest(shape=shape, whole="observation"):
                self.assertTrue(
                    set(values) <= {0.0, 1.0},
                    "with every amount at its own divisor the whole dense observation is "
                    "0.0 and 1.0 -- five scaled blocks at exactly their high and four "
                    "exact ones by construction (flat-numeric.md §4, D-61): the other "
                    "values are %r" % (sorted(set(values) - {0.0, 1.0})[:6],),
                )


class FEA11SeatSlot(FEA11Case):
    """The seat block's index slot is the index over `seats - 1`."""

    def test_fea11_4_the_index_flag_seat_slot_is_the_index_over_seats_minus_one(self):
        """FEA-11.4 on both two-seat rows the `index-flag` seat block is
        `[index / (seats - 1), the button flag]`, and `seats - 1` is 1 there, so no emitted
        value moved; on every row every slot of the seat block is in [0, 1] -- the
        six-seat row's one-hot sets exactly one 1.0 -- and the denominator is the
        **shape's**, so a six-seat index-flag row would land in [0, 1] too
        (flat-numeric.md §4, seats.md §3, D-61, ASM-44)."""
        for shape in S.ALL_SHAPES:
            seats = S.SEATS[shape]
            offset, width = self.blocks(shape)["seat"]
            self.assertEqual(
                width, seats,
                "the seat block is one slot per seat (seats.md §3, ASM-44): %d against %d"
                % (width, seats),
            )
            for index in range(seats):
                for flag in (False, True):
                    record = S.shaped_readout(shape, seat=(index, flag))
                    block = S.floats(observation_of(self, S.FLAT, shape, record))[
                        offset:offset + width]
                    with self.subTest(shape=shape, seat=index, flag=flag):
                        self.assertGreaterEqual(
                            min(block), 0.0,
                            "no seat slot is negative, in either declared mode "
                            "(flat-numeric.md §4, D-61): %r" % (block,),
                        )
                        self.assertLessEqual(
                            max(block), 1.0,
                            "and none exceeds 1.0: the index's denominator is the shape's "
                            "own seats - 1 (flat-numeric.md §4, D-61): %r"
                            % (block,),
                        )
                        if shape == S.THIRD_SHAPE:
                            self.assert_floats(
                                block,
                                [1.0 if slot == index else 0.0 for slot in range(seats)],
                                "the six-seat row declares the one-hot mode: one slot per "
                                "seat, the acting seat's set (seats.md §3, ASM-44)",
                            )
                        else:
                            self.assert_floats(
                                block[:1], [index / (seats - 1)],
                                "the index slot is the acting seat's index over the row's "
                                "seats - 1, which is 1 on both two-seat rows, so the value "
                                "is the index it always was (flat-numeric.md §4, D-61)",
                            )
                            self.assert_floats(
                                block[1:2], [1.0 if flag else 0.0],
                                "and the second slot is the button flag, a value of the "
                                "same block (flat-numeric.md §4)",
                            )


if __name__ == "__main__":
    unittest.main()
