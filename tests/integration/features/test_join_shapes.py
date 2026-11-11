"""J-8 -- the declared game shapes, at the module join.

`docs/L2/features/shapes.md` §1-§6, `docs/L2/features/capacity.md` §1-§5,
`docs/L2/features/surface.md` §4 and §7-§9, `docs/L2/engine/surface.md` §12,
`docs/L1/shapes.md` §2-§3 and §8 (D-29, D-33, D-13), `docs/L1/seats.md` §2-§3,
`docs/L1/assumptions.md` ASM-42, ASM-44 and `docs/L1/e2e-surface.md` §3.2.

The shapes are declared twice -- once by `engine.game_shapes()` and once by this module's
own row -- and the join battery is the whole of how the two statements stay equal
(`shapes.md` §1, §6).  Every case here therefore reads the engine's catalogue and hands
the module what the engine actually produces: a real hand of one shape, a real readout,
the engine's own legal descriptors, and the handle `engine.apply_action` returns for a
descriptor `features.decode_action` decoded.

Nothing here writes down a shape's descriptors, its normalisers, its seat count, its
history capacity or a slot index of its own: they are read from `engine.game_shapes()` --
whose rows now publish `seats` and `history` as well as `actions`, `head_width` and
`normalisers` -- from the observation the module returns, and from the row the catalogue
publishes, so a case asserts that the two statements agree and never that this battery's
copy of one of them is the design (`docs/L1/battery.md` §2, §4, D-11, D-15).  The three
pairs of widths in `_join_support.SHAPES_BY_CATALOGUE` are the battery's second statement
of the arithmetic `capacity.md` §2 fixes, and `_join_support.dense_width` /
`token_width` compute the same widths out of the engine's own `seats` and `history`.
"""

import os
import sys
import unittest

try:  # collected as part of a package
    from . import _join_support as S
except ImportError:  # collected as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _join_support as S  # noqa: E402

#: The two declared shapes, by the names both modules publish: the default first
#: (`shapes.md` §2, §3).  ``None`` is the default too, and is not a third name.
DEFAULT = "fixed-limit-20"
SECOND = "no-limit-100"

#: A shape name that is no declared shape: the writer's own, invented from the catalogue
#: the engine publishes, exactly as the undeclared encoding and descriptor of this
#: battery are (`docs/L1/battery.md` §4, D-15).
UNDECLARED_SHAPE = "no-limit-200"

#: The policy name that takes the **last** legal descriptor.  On a shape whose six
#: descriptors are ordered worst-price-first it is the minimum raise wherever raising is
#: legal, and taking it every decision is what drives the raise war whose top masks bands
#: out (`docs/L3/engine/actions.md` §1-§2, `sizing.md` §2, §3).
LAST = "last"

#: The two declared encodings, in the ladder's order: the dense one is the encoding
#: whose divisors the shape moves, and the token one the encoding whose bucket edges it
#: moves (`surface.md` §3, `shapes.md` §2, §5).
DENSE, TOKENS = S.ENCODING_NAMES

#: The five amount normalisers a readout is placed at -- the names
#: `engine.game_shapes()` publishes (`shapes.md` §2).
NORMALISERS = ("stack", "pot", "to_call", "amount", "count")


def pick(legal, policy):
    """One descriptor of a policy's choosing, taken from the engine's own sequence.

    ``raise`` takes the first legal raise -- the cheapest band on the no-cap shape --
    ``call`` the check/call, and ``last`` the last legal descriptor, which is the
    minimum raise where raising is legal (`sizing.md` §2, §3).  No choice is read from
    the module this battery judges: every descriptor is one the engine returned.
    """
    sequence = S.descriptors(legal, "a decision's legal descriptors")
    if policy == LAST:
        return sequence[-1]
    return S.pick_descriptor(legal, S.RAISE if policy == "raise" else S.CHECK_CALL)


class ShapesCase(S.JoinCase):
    """The join written on the engine's catalogue, its hands and this module's names."""

    # -- the engine's side of the shape -------------------------------------
    def catalog(self):
        """`engine.game_shapes()`, the declared catalogue, default first (§12)."""
        return S.entry(S.ENGINE, "game_shapes")()

    def shape_names(self):
        """Every declared shape name, in the catalogue's own order."""
        return tuple(self.catalog())

    def new_shaped_hand(self, seed, shape):
        """One real hand of one shape, through the engine's own seeding point (§4)."""
        return S.entry(S.ENGINE, "new_hand")(seed, shape=shape)

    # -- this module's side ------------------------------------------------
    def shaped_encoder(self, name, shape):
        """One encoder, by encoding name, on one declared shape (surface.md §4)."""
        return self.ep("build_encoder")(name, shape=shape)

    def shaped_space(self, shape):
        """One shape's vocabulary, through the one name that publishes it (§7)."""
        return self.ep("action_space")(shape=shape)

    def shaped_decode(self, index, shape):
        """One index decoded in one shape's vocabulary (§9)."""
        return self.ep("decode_action")(index, shape=shape)

    # -- walks -------------------------------------------------------------
    def walk_shaped(self, seed, shape, policy):
        """Drive one real hand of one shape, taking the policy's descriptor each step.

        The decisions are returned as :class:`S.Step` values, each carrying the handle
        it was read at, so a case can hand a decoded descriptor back to the engine at
        exactly the decision whose mask made its index legal (`stepping.md` §1).
        """
        hand = self.new_shaped_hand(seed, shape)
        steps = []
        while len(steps) < S.DECISION_BOUND and not self.is_terminal(hand):
            step = S.Step(hand, self.readout(hand), self.legal_actions(hand))
            steps.append(step)
            hand = self.apply_action(hand, pick(step.legal, policy))
        return steps

    def decisions(self, shape, policies=("raise", LAST),
                  seeds=(S.SEED_MASK, S.SEED_DECODE)):
        """Every decision of a few walks of one shape, labelled by walk and position."""
        walked = []
        for policy in policies:
            for seed in seeds:
                for position, step in enumerate(self.walk_shaped(seed, shape, policy)):
                    walked.append((policy, seed, position, step))
        return walked

    # -- readouts at a shape's own normalisers ------------------------------
    def at_normalisers(self, base, values):
        """A copy of a real readout whose five amount facts are ``values``.

        Every other fact is the engine's own, so the encoding sees a real seat, a real
        board and a real history, and only the amounts are placed -- which is what
        `shapes.md` §2 makes the shape's: the divisors a value is written with.
        ``stacks`` is one entry per seat, the engine's own count -- two on the two-seat
        rows and six on the six-seat one -- because both per-seat blocks are the seat
        count wide (`seats.md` §3, `capacity.md` §4, ASM-44).
        """
        record = dict(base)
        seats = len(tuple(base["stacks"]))
        record["stacks"] = tuple(int(values["stack"]) for _ in range(seats))
        record["pot"] = int(values["pot"])
        record["to_call"] = int(values["to_call"])
        record["limit"] = (int(values["amount"]), int(values["count"]))
        return record


class ShapesVocabulary(ShapesCase):
    """Every declared shape's vocabulary reaches the engine's hands."""

    def test_join_shapes_01_every_declared_shape_publishes_the_engines_vocabulary(self):
        """J-8.1 for every shape engine.game_shapes() declares, features.action_space(
        shape=name)'s names are the row's `actions` position by position, and the number
        of indices is that row's `head_width` (shapes.md §1, §3, §6; surface.md §7;
        e2e-surface.md §3.2, D-13)."""
        catalog = self.catalog()
        self.assertGreaterEqual(
            len(catalog), 2,
            "the catalogue declares the second shape beside the default, so this case "
            "has two statements to hold equal (shapes.md §1, §2): %r" % (list(catalog),),
        )
        first = tuple(catalog)[0]
        self.assertEqual(
            tuple(catalog)[0], DEFAULT,
            "the catalogue is read in its own declared order, the default shape first "
            "(shapes.md §2): %r" % (tuple(catalog),),
        )
        self.assertTrue(
            catalog[first]["default"],
            "the row the catalogue reads first is the row it marks as the default, so "
            "the order and the flag are one statement and not two (shapes.md §2, D-29): "
            "%r" % (catalog[first],),
        )
        self.assertIn(
            DEFAULT, catalog,
            "the default shape is a declared row of the catalogue (shapes.md §2, D-29): "
            "%r" % (list(catalog),),
        )
        for name, row in catalog.items():
            with self.subTest(shape=name):
                space = self.shaped_space(name)
                indices = list(space)
                names = [space[index]["name"] for index in indices]
                self.assertEqual(
                    indices, list(range(row["head_width"])),
                    "the shape's indices are 0 to its head width less one, in its "
                    "declared order (surface.md §7, shapes.md §5): %r against a head "
                    "width of %r" % (indices, row["head_width"]),
                )
                self.assertEqual(
                    len(space), row["head_width"],
                    "the number of indices is the row's `head_width`, so the action axis "
                    "the agent reads and the axis this module publishes are one width "
                    "(shapes.md §5, sizing.md §6): %d against %r"
                    % (len(space), row["head_width"]),
                )
                self.assertEqual(
                    names, list(row["actions"]),
                    "the record names the row's descriptors position by position, in "
                    "that shape's order (shapes.md §3, §6): %r against %r"
                    % (names, list(row["actions"])),
                )
                for position, descriptor in enumerate(row["actions"]):
                    with self.subTest(shape=name, index=position):
                        self.assertEqual(
                            space[position]["name"], descriptor,
                            "index %d is the engine's own descriptor for it "
                            "(vocabulary.md §1, D-13): %r against %r"
                            % (position, space[position]["name"], descriptor),
                        )
                        self.assertEqual(
                            self.shaped_decode(position, name), descriptor,
                            "and decode_action on that shape returns that same "
                            "descriptor, which is the round trip engine.apply_action "
                            "accepts (surface.md §2, §9, e2e-surface.md §3.2): %r "
                            "against %r"
                            % (self.shaped_decode(position, name), descriptor),
                        )


class ShapesNormalisers(ShapesCase):
    """The dense encoding divides by the engine's own declared normalisers."""

    def test_join_shapes_02_the_dense_encoding_divides_by_the_engines_normalisers(self):
        """J-8.2 for every declared shape a readout whose stacks, pot, to_call and limit
        sit exactly at that row's five normalisers encodes to 1.0 in each of those slots,
        so the divisor the encoding applies and the normaliser the engine publishes are
        the same table; the one normaliser that reaches several slots reaches one per
        seat -- two on the two-seat rows and six on the six-seat one, whose observation is
        433 slots against 203 and 329 (shapes.md §1, §2, §6; capacity.md §2, §4;
        flat-numeric.md §4, seats.md §3, D-13)."""
        catalog = self.catalog()
        for name, row in catalog.items():
            with self.subTest(shape=name):
                normalisers = dict(row["normalisers"])
                self.assertEqual(
                    set(normalisers), set(NORMALISERS),
                    "the row publishes the five amount normalisers this module restates, "
                    "under the same five keys (shapes.md §2, declarations.py, D-13): %r"
                    % (sorted(normalisers),),
                )
                base = self.readout(self.new_shaped_hand(S.SEED_ENCODE, name))
                seats = len(tuple(base["stacks"]))
                self.assertEqual(
                    seats, int(row["seats"]),
                    "the real readout carries one stack per seat of the row it was dealt "
                    "on, so the stacks block is that row's width (seats.md §3, ASM-44): "
                    "%r against %r" % (seats, row["seats"]),
                )
                encoder = self.shaped_encoder(DENSE, name)
                floor_facts = {key: 0 for key in NORMALISERS}
                floor = S.canonical(self.encode(encoder, self.at_normalisers(base, floor_facts)))
                self.assertEqual(
                    len(floor), S.SHAPES_BY_CATALOGUE[name][DENSE][0],
                    "the dense observation is as long as the encoding declares on that "
                    "shape -- 131 + 3 x 24 = 203 on the default, 131 + 3 x 66 = 329 on "
                    "the two-seat no-cap shape and 139 + 3 x 98 = 433 on the six-seat one "
                    "-- because the history block's capacity and the two per-seat blocks "
                    "are the shape's (capacity.md §2, shapes.md §8, ASM-42, ASM-44; "
                    "surface.md §5): %d slots against %r"
                    % (len(floor), S.SHAPES_BY_CATALOGUE[name][DENSE]),
                )
                self.assertEqual(
                    len(floor), S.dense_width(row),
                    "and it is the width the engine's own `seats` and `history` imply, "
                    "127 + 2 x seats + 3 x history, so the two statements are one "
                    "arithmetic (capacity.md §2, §5, D-13): %d against %d"
                    % (len(floor), S.dense_width(row)),
                )
                reached = {}
                for fact in NORMALISERS:
                    with self.subTest(shape=name, normaliser=fact):
                        probe = dict(floor_facts)
                        probe[fact] = normalisers[fact]
                        values = S.canonical(
                            self.encode(encoder, self.at_normalisers(base, probe))
                        )
                        moved = [
                            slot for slot, (got, was) in enumerate(zip(values, floor))
                            if got != was
                        ]
                        self.assertTrue(
                            moved,
                            "a %r at the shape's own normaliser of %r moves a slot of "
                            "the dense observation, because the amount is carried "
                            "(shapes.md §2, surface.md §6): %r"
                            % (fact, normalisers[fact], values),
                        )
                        for slot in moved:
                            self.assertAlmostEqual(
                                values[slot], 1.0, delta=1e-6,
                                msg="the %r slot the %r fact writes reads 1.0 when that "
                                    "fact sits at the engine's normaliser of %r: the "
                                    "encoding's divisor is that normaliser and no other "
                                    "(shapes.md §2, flat-numeric.md §4, D-13): %r"
                                    % (slot, fact, normalisers[fact], values[slot]),
                            )
                            self.assertNotIn(
                                slot, reached,
                                "one normaliser per slot: %r is reached by %r and by %r, "
                                "so the five facts are not five independent amounts "
                                "(shapes.md §2): %r" % (slot, reached.get(slot), fact,
                                                        values),
                            )
                            reached[slot] = fact
                self.assertEqual(
                    set(reached.values()), set(NORMALISERS),
                    "all five normalisers reach the observation (shapes.md §2, "
                    "flat-numeric.md §4): %r" % (sorted(reached.values()),),
                )
                self.assertEqual(
                    [fact for fact in reached.values() if fact == "stack"],
                    ["stack"] * seats,
                    "the stack normaliser is the one that reaches one slot per seat, "
                    "because the block carries every seat's stack: two slots on a "
                    "two-seat row and six on the six-seat one (flat-numeric.md §2, §4, "
                    "seats.md §3, ASM-44): %r" % (sorted(reached),),
                )
                self.assertEqual(
                    len(reached), seats + 4,
                    "the stacks' one slot per seat plus the pot, the amount to call and "
                    "the bet size and count are %d amount slots on this row (surface.md "
                    "§5, flat-numeric.md §2, §4, ASM-44): %r"
                    % (seats + 4, sorted(reached)),
                )


class ShapesSecondVocabulary(ShapesCase):
    """`no-limit-100`'s six descriptors reach a real hand's decisions."""

    def test_join_shapes_03_the_second_shapes_vocabulary_reaches_the_engine(self):
        """J-8.3 on a no-limit-100 hand the engine's legal set is a subset of that
        shape's vocabulary in that shape's order, features.legal_indices gives the
        subset's positions, features.decode_action(index, shape="no-limit-100") returns
        the descriptor at that position, engine.apply_action accepts it and returns a
        handle -- and where a band is masked out the mask is exactly the legal set's
        positions (shapes.md §3, §4, §6; surface.md §7-§9; sizing.md §2, §3, FAM-2.11)."""
        catalog = self.catalog()
        self.assertIn(
            SECOND, catalog,
            "the second shape is a declared row of the engine's catalogue, so a hand can "
            "be dealt on it (shapes.md §1, §2, D-29): %r" % (list(catalog),),
        )
        vocabulary = tuple(catalog[SECOND]["actions"])
        walked = self.decisions(SECOND)
        self.assertGreater(
            len(walked), len(vocabulary),
            "the walks reach more decisions than the shape has descriptors, so the mask "
            "is asserted over a real hand's whole course (shapes.md §3): %d decisions"
            % (len(walked),),
        )
        masked = 0
        for policy, seed, position, step in walked:
            with self.subTest(policy=policy, seed=seed, decision=position):
                legal = S.descriptors(step.legal, "a decision's legal descriptors")
                self.assertGreaterEqual(
                    len(legal), 1,
                    "a live decision has at least one legal action (engine/surface.md "
                    "§6): %r" % (legal,),
                )
                self.assertEqual(
                    len(set(legal)), len(legal),
                    "at most one descriptor per index, so no duplicate in the legal set "
                    "(surface.md §2, engine/surface.md §2): %r" % (legal,),
                )
                self.assertEqual(
                    legal, [descriptor for descriptor in vocabulary
                            if descriptor in legal],
                    "the legal set is this shape's vocabulary, in the shape's own "
                    "declared order (shapes.md §3, engine/surface.md §6): %r against %r"
                    % (legal, list(vocabulary)),
                )
                indices = self.ep("legal_indices")(legal)
                self.assertEqual(
                    tuple(indices),
                    tuple(vocabulary.index(descriptor) for descriptor in legal),
                    "features.legal_indices turns the engine's descriptors into that "
                    "vocabulary's positions, one per descriptor (surface.md §8, "
                    "vocabulary.md §3): %r against %r" % (tuple(indices), legal),
                )
                for slot, index in enumerate(indices):
                    descriptor = self.shaped_decode(index, SECOND)
                    self.assertEqual(
                        descriptor, legal[slot],
                        "decode_action(index, shape=%r) is the descriptor at that "
                        "position, which is legal_indices' reverse step (surface.md §2, "
                        "§9, FAM-2.10): %r -> %r, expected %r"
                        % (SECOND, index, descriptor, legal[slot]),
                    )
                    advanced = self.apply_action(step.hand, descriptor)
                    self.assertIsNotNone(
                        advanced,
                        "engine.apply_action accepts the descriptor features decoded at "
                        "the decision whose mask holds its index, and returns a handle "
                        "(shapes.md §6, engine/surface.md §7): %r was refused"
                        % (descriptor,),
                    )
                    self.assertIn(
                        self.is_terminal(advanced), (True, False),
                        "the handle a decoded descriptor advances is a live one the "
                        "engine answers about (engine/surface.md §8): %r"
                        % (advanced,),
                    )
                if len(legal) < len(vocabulary):
                    masked += 1
                    self.assertEqual(
                        tuple(indices),
                        tuple(sorted(vocabulary.index(descriptor) for descriptor in legal)),
                        "a legal set shorter than the vocabulary is a band masked out, "
                        "and the mask is exactly the legal set's positions -- nothing "
                        "collapsed onto a neighbour and nothing invented (shapes.md §3, "
                        "§4, sizing.md §2): %r against %r" % (tuple(indices), legal),
                    )
                    self.assertEqual(
                        len(indices), len(legal),
                        "the six-descriptor shape's mask is exactly as long as the legal "
                        "set the engine returned, never padded out to six (shapes.md §4, "
                        "surface.md §8): %r against %r" % (tuple(indices), legal),
                    )
                    self.assertLess(
                        len(indices), len(vocabulary),
                        "a band masked out is simply absent from the mask (shapes.md §4, "
                        "sizing.md §2): %r" % (tuple(indices),),
                    )
        self.assertGreater(
            masked, 0,
            "the walks reach at least one decision whose band set is masked out, so the "
            "shorter mask is asserted and not only the full six (shapes.md §3, §4, "
            "sizing.md §2): %d of %d decisions are masked"
            % (masked, len(walked)),
        )


class ShapesEncodings(ShapesCase):
    """Both encodings declare the shape's own width, and the default's values do not move."""

    def test_join_shapes_04_both_encodings_declare_the_shapes_width_and_dtype(self):
        """J-8.4 both encodings encode a no-limit-100 readout to that shape's declared
        width -- 329 dense and 82 tokens, the 131 and 16 slots before the history plus
        3 x 66 and 66 -- and to their own dtype, while both encode a default-shape readout
        to the very values build_encoder(name) with no shape produces, at 203 and 40, so
        the default shape's observations are unchanged (surface.md §4-§6, shapes.md §5,
        §8, ASM-42, ASM-44, e2e-surface.md §3.2, D-29)."""
        shaped = self.readout(self.new_shaped_hand(S.SEED_ENCODE, SECOND))
        for name in (DENSE, TOKENS):
            with self.subTest(encoding=name, readout=SECOND):
                encoder = self.shaped_encoder(name, SECOND)
                spec = self.observation_spec(encoder)
                observation = self.encode(encoder, shaped)
                self.assert_observation(name, spec, observation)
                self.assertEqual(
                    self.declared_shape(spec),
                    S.SHAPES_BY_CATALOGUE[SECOND][name],
                    "an encoder built for the second shape declares that shape's own "
                    "width, because one observation's shape follows the history block's "
                    "capacity (shapes.md §8, ASM-42, ASM-44; surface.md §5): %r against %r"
                    % (S.SHAPES_BY_CATALOGUE[SECOND][name], self.declared_shape(spec)),
                )
                self.assertEqual(
                    str(spec["dtype"]), S.DTYPES[name],
                    "and still declares the encoding's dtype, which the shape does not "
                    "move (shapes.md §5, surface.md §5): %r" % (spec["dtype"],),
                )
                self.assertEqual(
                    self.observation_spec(self.build_encoder(name)),
                    dict(spec, shape=S.SHAPES[name]),
                    "the spec of an encoder built with no shape is the second shape's "
                    "record with the default shape's width in place of its own, value for "
                    "value elsewhere: the capacity is the one fact the shape adds to a "
                    "record (shapes.md §5, §8, surface.md §5): %r"
                    % (self.observation_spec(self.build_encoder(name)),),
                )
        plain = self.readout(self.new_hand(S.SEED_ENCODE))
        for name in (DENSE, TOKENS):
            with self.subTest(encoding=name, readout=DEFAULT):
                unnamed = self.encode(self.build_encoder(name), plain)
                named = self.encode(self.shaped_encoder(name, DEFAULT), plain)
                self.assertTrue(
                    S.same_observation(unnamed, named),
                    "naming the default shape gives the observation the no-shape encoder "
                    "gives, value for value: the default shape's encoding is unmoved "
                    "(shapes.md §2, §5, D-29): %r against %r"
                    % (S.canonical(named), S.canonical(unnamed)),
                )
                self.assertEqual(
                    tuple(unnamed.shape), S.SHAPES[name],
                    "and that observation is still the declared %r: the fixed-limit width "
                    "does not move (shapes.md §5, §8): %r"
                    % (S.SHAPES[name], tuple(unnamed.shape)),
                )
                self.assert_observation(name, self.spec(name), named)


class ShapesRefusals(ShapesCase):
    """The refusals the shape adds, and the arity it does not move."""

    def test_join_shapes_05_an_undeclared_shape_is_refused_and_the_shape_stays_a_keyword(self):
        """J-8.5 features.action_space(shape=...) and features.build_encoder(..., shape=...)
        -- and features.decode_action(index, shape=...) -- refuse a name that is no
        declared shape by a message naming the rejected value and every declared name,
        and a positional shape argument is still Python's TypeError, so no pre-existing
        arity moved; the declared names are the three the engine's catalogue publishes,
        default first, the six-seat row included (shapes.md §1, §6, surface.md §4, §7, §9,
        seats.md §2, capacity.md §5, D-11, D-29, D-33)."""
        declared = self.shape_names()
        self.assertEqual(
            set(declared), {DEFAULT, SECOND, S.THIRD_SHAPE},
            "the three declared names this case reads out of the engine's catalogue are "
            "the three the module declares, the six-seat row included (shapes.md §1, §6, "
            "seats.md §2, D-33): %r" % (list(declared),),
        )
        self.assertEqual(
            len(set(declared)), 3,
            "three declared shapes and no fourth: the catalogue is the whole set "
            "(shapes.md §2, seats.md §2, D-13): %r" % (list(declared),),
        )
        calls = (
            ("action_space", lambda: self.ep("action_space")(shape=UNDECLARED_SHAPE)),
            ("build_encoder",
             lambda: self.shaped_encoder(DENSE, UNDECLARED_SHAPE)),
            ("decode_action",
             lambda: self.shaped_decode(0, UNDECLARED_SHAPE)),
        )
        for entry_point, call in calls:
            with self.subTest(entry_point=entry_point, refused="shape"):
                self.assert_named_refusal(
                    call, entry_point,
                    "%s must refuse a shape name the catalogue does not carry, never "
                    "defaulting it (shapes.md §6, surface.md §1 rule 2)" % (entry_point,),
                    words=(UNDECLARED_SHAPE,) + declared,
                )
            for name in declared:
                with self.subTest(entry_point=entry_point, declared=name):
                    self.assert_named_refusal(
                        call, entry_point,
                        "%s must name the declared shape %r the caller could have given, "
                        "so a typo reads as one (shapes.md §6, D-13): %r"
                        % (entry_point, name, UNDECLARED_SHAPE),
                        words=(name,),
                    )
        positional = (
            ("action_space", lambda: self.ep("action_space")(SECOND)),
            ("build_encoder", lambda: self.ep("build_encoder")(DENSE, SECOND)),
            ("decode_action", lambda: self.ep("decode_action")(0, SECOND)),
        )
        for entry_point, call in positional:
            with self.subTest(entry_point=entry_point, supplied="positional"):
                with self.assertRaises(TypeError):
                    call()
        self.assertEqual(
            list(self.ep("action_space")(shape=SECOND)),
            list(range(len(self.catalog()[SECOND]["actions"]))),
            "the shape is keyword-only, so the positional calls above never reach it and "
            "the named call is the one that declares the second vocabulary (shapes.md §1, "
            "vocabulary.md §4, D-11): %r" % (list(self.ep("action_space")(shape=SECOND)),),
        )


class ShapesDefault(ShapesCase):
    """The default shape at the join: one record, and every descriptor usable."""

    def test_join_shapes_06_the_default_shape_is_one_record_and_its_descriptors_all_apply(self):
        """J-8.6 features.action_space() equals features.action_space(shape="fixed-limit-20"),
        and every descriptor features.decode_action returns on the default shape is one
        engine.apply_action accepts at the decision whose mask holds its index
        (surface.md §2, §7, §9, shapes.md §3, §4, engine/surface.md §6, §7)."""
        self.assertEqual(
            self.ep("action_space")(), self.shaped_space(DEFAULT),
            "the no-shape call and the named default are one record, key for key and "
            "value for value (surface.md §7, shapes.md §3, D-29): %r != %r"
            % (self.ep("action_space")(), self.shaped_space(DEFAULT)),
        )
        space = self.ep("action_space")()
        vocabulary = tuple(self.catalog()[DEFAULT]["actions"])
        decisions = self.decisions(DEFAULT, policies=("raise", "call"),
                                   seeds=(S.SEED_DECODE,))
        self.assertGreater(
            len(decisions), len(space),
            "the walks reach more decisions than the three indices, so every index's "
            "descriptor is applied at a real decision (surface.md §9): %d decisions"
            % (len(decisions),),
        )
        applied = set()
        for policy, seed, position, step in decisions:
            with self.subTest(policy=policy, seed=seed, decision=position):
                legal = S.descriptors(step.legal, "a decision's legal descriptors")
                indices = self.ep("legal_indices")(legal)
                self.assertEqual(
                    tuple(indices),
                    tuple(vocabulary.index(descriptor) for descriptor in legal),
                    "the default shape's mask is the descriptors' own positions in the "
                    "engine's vocabulary, positionally (surface.md §8): %r against %r"
                    % (tuple(indices), legal),
                )
                for index in range(len(space)):
                    descriptor = self.ep("decode_action")(index)
                    self.assertEqual(
                        descriptor, space[index]["name"],
                        "decode_action and action_space are two directions of one "
                        "vocabulary, whatever the decision (vocabulary.md §1, §2): %r "
                        "against %r" % (descriptor, space[index]["name"]),
                    )
                    if index not in tuple(indices):
                        self.assertNotIn(
                            descriptor, legal,
                            "an index the mask does not hold is a descriptor this "
                            "decision does not allow, and decode_action claims no "
                            "legality (surface.md §2, §9, D-2): %r" % (descriptor,),
                        )
                        continue
                    advanced = self.apply_action(step.hand, descriptor)
                    self.assertIsNotNone(
                        advanced,
                        "engine.apply_action accepts every descriptor decode_action "
                        "returns at a decision whose mask holds its index (surface.md "
                        "§2, §9, engine/surface.md §7): %r was refused at %r"
                        % (descriptor, legal),
                    )
                    applied.add(descriptor)
        self.assertEqual(
            applied, set(vocabulary),
            "all three of the default shape's descriptors were applied to a real hand "
            "along the walks, so no index was left only decoded (surface.md §2, §9): %r "
            "against %r" % (sorted(applied), list(vocabulary)),
        )


class ShapesHistoryCapacity(ShapesCase):
    """A real no-cap hand's history runs past 24 entries -- and the shape carries it."""

    def test_join_shapes_07_a_real_no_limit_history_past_24_encodes_and_the_next_is_refused(self):
        """J-8.7 a real no-limit-100 hand driven to the minimum raise every decision applies
        more than the fixed-limit capacity's 24 actions while staying inside the no-cap
        shape's 66, every readout of that hand encodes in both encodings at that shape's own
        width (329 and 82), and a history one entry past the 66 is refused naming the field,
        the capacity and the count -- the overflow D-32 recorded is closed by the shape's own
        capacity and never by a truncation (shapes.md §8, ASM-42, ASM-44; flat-numeric.md §5,
        card-tokens.md §5, surface.md §6)."""
        steps = self.walk_shaped(S.SEED_MASK, SECOND, LAST)
        longest = max(len(step.readout["history"]) for step in steps)
        longest_step = max(steps, key=lambda step: len(step.readout["history"]))
        self.assertGreater(
            longest, S.CAPACITY[S.DEFAULT_SHAPE],
            "the raise war on the uncapped shape applies more than the fixed-limit "
            "capacity's 24 actions, which is the hand the 24-slot block refused "
            "(shapes.md §8, ASM-42): %d entries" % (longest,),
        )
        self.assertLessEqual(
            longest, S.CAPACITY[SECOND],
            "and it stays inside the no-cap shape's own capacity of 66, so the block the "
            "shape declares carries a legal hand whole (shapes.md §8, ASM-42): %d entries"
            % (longest,),
        )
        for position, step in enumerate(steps):
            for name in (DENSE, TOKENS):
                with self.subTest(encoding=name, decision=position,
                                  entries=len(step.readout["history"])):
                    observation = self.encode(self.shaped_encoder(name, SECOND),
                                              step.readout)
                    self.assertEqual(
                        tuple(observation.shape),
                        S.SHAPES_BY_CATALOGUE[SECOND][name],
                        "every real decision of the hand encodes at the shape's declared "
                        "width, whatever the history's length (surface.md §6, shapes.md "
                        "§8): %r at %d entries"
                        % (tuple(observation.shape), len(step.readout["history"])),
                    )
        real = list(longest_step.readout["history"])
        room = (real * 2)[:S.CAPACITY[SECOND]]
        self.assertEqual(
            len(room), S.CAPACITY[SECOND],
            "the battery holds a history of exactly the capacity, built from the entries "
            "this real hand really applied (shapes.md §8, ASM-42): %d" % (len(room),),
        )
        for name in (DENSE, TOKENS):
            with self.subTest(encoding=name, entries=S.CAPACITY[SECOND]):
                encoder = self.shaped_encoder(name, SECOND)
                self.assertEqual(
                    tuple(self.encode(encoder, dict(longest_step.readout,
                                                    history=room)).shape),
                    S.SHAPES_BY_CATALOGUE[SECOND][name],
                    "a history of exactly the capacity encodes: the threshold is the "
                    "capacity and not one less (shapes.md §8, ASM-42): %r"
                    % (S.SHAPES_BY_CATALOGUE[SECOND][name],),
                )
                self.assert_named_refusal(
                    lambda encoder=encoder, room=room: self.encode(
                        encoder, dict(longest_step.readout,
                                      history=room + [real[0]])),
                    "encode",
                    "one entry past the shape's capacity must be refused, never "
                    "truncated, on both encodings (shapes.md §8, ASM-42)",
                    words=("history", str(S.CAPACITY[SECOND]),
                           str(S.CAPACITY[SECOND] + 1)),
                )


class ShapesSeatsAndCapacity(ShapesCase):
    """The engine's `seats` and `history` and this module's rows are one statement."""

    def test_join_shapes_08_the_rows_seats_and_history_are_the_engines(self):
        """J-8.8 for every declared shape the row engine.game_shapes() publishes and the
        row this module encodes to agree about the two numbers the widths are built from:
        the dense encoder declares 127 + 2 x seats + 3 x history slots and the token
        encoder 12 + 2 x seats + history tokens, a real readout of the shape carries one
        stack per seat, the last seat index is accepted while the seat count is refused
        naming seat, one more stack than seats is refused naming stacks, and a history of
        exactly the row's capacity encodes while one entry more is refused naming the
        field, the capacity and the count -- so 139/24 and 433/122 on the six-seat row
        are its own arithmetic and 131/16 and 203/329 stay the two-seat rows'
        (capacity.md §2-§5, shapes.md §1-§2, §8, seats.md §2-§3, surface.md §5-§6,
        ASM-42, ASM-44, D-13)."""
        catalog = self.catalog()
        self.assertEqual(
            tuple(catalog), (DEFAULT, SECOND, S.THIRD_SHAPE),
            "the catalogue declares the three shapes default first, the six-seat row "
            "third (shapes.md §2, seats.md §2, D-33): %r" % (tuple(catalog),),
        )
        for name, row in catalog.items():
            seats, history = int(row["seats"]), int(row["history"])
            with self.subTest(shape=name):
                self.assertEqual(
                    (seats, history), (S.SEATS[name], S.CAPACITY[name]),
                    "the row's seat count and history capacity are the two this module "
                    "restates and the widths are built from (capacity.md §2, §5, "
                    "shapes.md §8, seats.md §3, ASM-42, ASM-44): %r against %r"
                    % ((seats, history), (S.SEATS[name], S.CAPACITY[name])),
                )
                self.assertIn(
                    seats, (2, 6),
                    "a declared row seats two or six: the third row is the six-seat "
                    "table and no other count exists (seats.md §2, D-33): %r" % (seats,),
                )
                base = self.readout(self.new_shaped_hand(S.SEED_ENCODE, name))
                self.assertEqual(
                    len(tuple(base["stacks"])), seats,
                    "a real readout of %r carries one stack per seat -- six here, two "
                    "on the two-seat rows -- because `stacks` is in seat order "
                    "(seats.md §3, ASM-44): %r" % (name, base["stacks"]),
                )
                for encoding, width in (
                    (DENSE, S.dense_width(row)), (TOKENS, S.token_width(row)),
                ):
                    with self.subTest(shape=name, encoding=encoding):
                        spec = self.observation_spec(
                            self.shaped_encoder(encoding, name))
                        self.assertEqual(
                            self.declared_shape(spec), (width,),
                            "the encoder declares the width the engine's own seats and "
                            "history imply -- 127 + 2 x %d + 3 x %d = %d dense, "
                            "12 + 2 x %d + %d = %d tokens (capacity.md §2, §5, D-13): "
                            "%r"
                            % (seats, history, S.dense_width(row), seats, history,
                               S.token_width(row), self.declared_shape(spec)),
                        )
                        self.assertEqual(
                            (width,), S.SHAPES_BY_CATALOGUE[name][encoding],
                            "and that width is the battery's second statement of the "
                            "same arithmetic (capacity.md §2): %r against %r"
                            % ((width,), S.SHAPES_BY_CATALOGUE[name][encoding]),
                        )
                        observation = self.encode(self.shaped_encoder(encoding, name),
                                                   base)
                        self.assert_observation(encoding, spec, observation)
                token_spec = self.observation_spec(
                    self.shaped_encoder(TOKENS, name))
                self.assertEqual(
                    int(token_spec["vocabulary"]), S.TOKEN_VOCABULARY[name],
                    "the token vocabulary is the row's own: 96 on the two-seat rows, "
                    "102 on the six-seat one, whose seat ids are 96-101 (card-tokens.md "
                    "§6, seats.md §3, capacity.md §4, ASM-44): %r against %r"
                    % (token_spec["vocabulary"], S.TOKEN_VOCABULARY[name]),
                )
                dense = self.shaped_encoder(DENSE, name)
                last_seat = dict(base, seat=(seats - 1, True))
                self.encode(dense, last_seat)
                self.assert_named_refusal(
                    lambda dense=dense, base=base, seats=seats: self.encode(
                        dense, dict(base, seat=(seats, True))),
                    "encode",
                    "a seat index equal to the shape's seat count must be refused, "
                    "naming seat (seats.md §3, ASM-44)",
                    words=("seat",),
                )
                self.encode(dense, dict(base, stacks=tuple([0] * seats)))
                self.assert_named_refusal(
                    lambda dense=dense, base=base, seats=seats: self.encode(
                        dense, dict(base, stacks=tuple([0] * (seats + 1)))),
                    "encode",
                    "one stack more than the shape seats must be refused, naming "
                    "stacks (seats.md §3, ASM-44)",
                    words=("stacks",),
                )
                steps = self.walk_shaped(S.SEED_MASK, name, LAST)
                longest = max(steps, key=lambda step: len(step.readout["history"]))
                real = list(longest.readout["history"])
                self.assertTrue(
                    real,
                    "the walk really applied actions, so a real entry exists to build "
                    "the capacity's history from (capacity.md §1, §3): %r" % (real,),
                )
                room = (real * (history // len(real) + 1))[:history]
                self.assertEqual(
                    len(room), history,
                    "the battery holds a history of exactly the row's capacity, built "
                    "from the entries this real hand really applied (capacity.md §3, "
                    "ASM-42): %d entries" % (len(room),),
                )
                for encoding in (DENSE, TOKENS):
                    with self.subTest(shape=name, encoding=encoding,
                                      entries=history):
                        encoder = self.shaped_encoder(encoding, name)
                        spec = self.observation_spec(encoder)
                        self.assert_observation(
                            encoding, spec,
                            self.encode(encoder, dict(base, history=room)))
                        self.assert_named_refusal(
                            lambda encoder=encoder, base=base, room=room, real=real:
                            self.encode(encoder, dict(base, history=room + [real[0]])),
                            "encode",
                            "one entry past the shape's capacity must be refused, never "
                            "truncated (capacity.md §3, ASM-42)",
                            words=("history", str(history), str(history + 1)),
                        )


class ShapesSixSeatHand(ShapesCase):
    """A real six-seat hand's every decision encodes at 433 and 122."""

    def test_join_shapes_09_a_real_six_seat_hand_encodes_at_every_decision(self):
        """J-8.9 a real six-seat-no-limit-100 hand, driven through engine.new_hand,
        engine.legal_actions and engine.apply_action, has every one of its decisions
        encoded at that row's 433 dense slots and 122 tokens, at the declared dtypes; its
        stacks carry six entries, its legal set is the row's six descriptors in the row's
        order, features.legal_indices gives those positions, and every descriptor
        features.decode_action returns at a legal index is one engine.apply_action
        accepts, so the shape's widths are the widths a real hand produces (surface.md
        §4-§9, shapes.md §2-§4, §8, capacity.md §1-§2, seats.md §2-§4, engine/surface.md
        §6-§7, e2e-surface.md §3.2, D-13, D-33)."""
        catalog = self.catalog()
        self.assertIn(
            S.THIRD_SHAPE, catalog,
            "the six-seat row is a declared row of the engine's catalogue, so a hand "
            "can be dealt on it (shapes.md §2, seats.md §2, D-33): %r" % (list(catalog),),
        )
        row = catalog[S.THIRD_SHAPE]
        vocabulary = tuple(row["actions"])
        self.assertEqual(
            len(vocabulary), int(row["head_width"]),
            "the row's six descriptors are its head width's count (shapes.md §3, "
            "sizing.md §6): %r" % (list(vocabulary),),
        )
        steps = self.walk_shaped(S.SEED_MASK, S.THIRD_SHAPE, LAST)
        self.assertGreater(
            len(steps), len(vocabulary),
            "the walk reaches more decisions than the six descriptors, so every one of "
            "the shape's widths is asserted over a real hand's course (seats.md §4): %d "
            "decisions" % (len(steps),),
        )
        self.assertEqual(
            (S.dense_width(row), S.token_width(row)), (433, 122),
            "the six-seat row's two widths are 139 + 3 x 98 = 433 dense and 24 + 98 = "
            "122 tokens (capacity.md §2, seats.md §3): %r"
            % ((S.dense_width(row), S.token_width(row)),),
        )
        encoders = {encoding: self.shaped_encoder(encoding, S.THIRD_SHAPE)
                    for encoding in (DENSE, TOKENS)}
        specs = {encoding: self.observation_spec(encoders[encoding])
                 for encoding in encoders}
        for encoding, width in (
            (DENSE, S.SHAPES_BY_CATALOGUE[S.THIRD_SHAPE][DENSE]),
            (TOKENS, S.SHAPES_BY_CATALOGUE[S.THIRD_SHAPE][TOKENS]),
        ):
            with self.subTest(encoding=encoding, declared=width):
                self.assertEqual(
                    self.declared_shape(specs[encoding]), width,
                    "an encoder built for the six-seat row declares that row's width "
                    "(surface.md §5, capacity.md §2): %r against %r"
                    % (self.declared_shape(specs[encoding]), width),
                )
        longest = 0
        for position, step in enumerate(steps):
            with self.subTest(decision=position,
                              entries=len(step.readout["history"])):
                self.assertEqual(
                    len(tuple(step.readout["stacks"])), S.SEATS[S.THIRD_SHAPE],
                    "every decision's readout carries six stacks in seat order, so the "
                    "six-wide blocks are what the engine really produces (seats.md §3, "
                    "ASM-28, ASM-44): %r" % (step.readout["stacks"],),
                )
                self.assertLessEqual(
                    len(step.readout["history"]), int(row["history"]),
                    "no decision of the hand overflows the row's own capacity: the "
                    "history the engine applies is inside the 98 the block declares "
                    "(capacity.md §1, §3, ASM-42): %d entries"
                    % (len(step.readout["history"]),),
                )
                longest = max(longest, len(step.readout["history"]))
                for encoding in (DENSE, TOKENS):
                    with self.subTest(decision=position, encoding=encoding):
                        observation = self.encode(encoders[encoding], step.readout)
                        self.assert_observation(encoding, specs[encoding], observation)
                        if encoding == DENSE:
                            self.assertTrue(
                                S.all_finite(observation),
                                "the dense observation of a real six-seat decision is "
                                "all finite numbers, so a dense layer can multiply it "
                                "(encodings.md §3, capacity.md §2): %r"
                                % (S.canonical(observation)[:8],),
                            )
                legal = S.descriptors(step.legal, "a decision's legal descriptors")
                self.assertEqual(
                    legal,
                    [descriptor for descriptor in vocabulary if descriptor in legal],
                    "the six-seat legal set is the row's whole vocabulary in the row's "
                    "own order, with the bands its price masks out simply absent "
                    "(shapes.md §3-§4, engine/surface.md §6): %r against %r"
                    % (legal, list(vocabulary)),
                )
                indices = self.legal_indices(legal)
                self.assertEqual(
                    tuple(indices),
                    tuple(vocabulary.index(descriptor) for descriptor in legal),
                    "features.legal_indices gives the positions of the descriptors the "
                    "engine returned, position for position (surface.md §8, "
                    "vocabulary.md §3): %r against %r" % (tuple(indices), legal),
                )
                for slot, index in enumerate(indices):
                    with self.subTest(decision=position, index=index):
                        descriptor = self.shaped_decode(index, S.THIRD_SHAPE)
                        self.assertEqual(
                            descriptor, legal[slot],
                            "decode_action(index, shape=%r) returns the descriptor at "
                            "that position, which is legal_indices' reverse step "
                            "(surface.md §9, FAM-2.10): %r -> %r, expected %r"
                            % (S.THIRD_SHAPE, index, descriptor, legal[slot]),
                        )
                        advanced = self.apply_action(step.hand, descriptor)
                        self.assertIsNotNone(
                            advanced,
                            "engine.apply_action accepts every descriptor features "
                            "decoded at the decision whose mask holds its index "
                            "(engine/surface.md §7, shapes.md §6): %r was refused at %r"
                            % (descriptor, legal),
                        )
        self.assertGreaterEqual(
            longest, 1,
            "the walk's longest history is at least one applied action, so the history "
            "block is exercised by a real hand (capacity.md §1): %d entries" % (longest,),
        )


class ShapesSixSeatSeatTokens(ShapesCase):
    """A real six-seat decision's acting seat is one of 96-101, and nowhere else."""

    def test_join_shapes_10_the_six_seat_token_seat_ids_are_96_to_101_for_the_acting_seat(self):
        """J-8.10 on every decision of a real six-seat hand the token observation carries
        exactly one id from 96-101 and it is `96 + the acting seat's index`, so the six
        seat ids appear only for the seat that acts and every other seat slot holds the
        pad; across the walk all six ids appear, and every id of every observation stays
        inside the row's vocabulary of 102 (seats.md §3, card-tokens.md §3, §6,
        capacity.md §4, ASM-44)."""
        row = self.catalog()[S.THIRD_SHAPE]
        encoder = self.shaped_encoder(TOKENS, S.THIRD_SHAPE)
        spec = self.observation_spec(encoder)
        vocabulary = int(spec["vocabulary"])
        self.assertEqual(
            vocabulary, S.TOKEN_VOCABULARY[S.THIRD_SHAPE],
            "the six-seat row's token vocabulary is the 102 its encoder declares "
            "(card-tokens.md §6, capacity.md §4, ASM-44): %r" % (vocabulary,),
        )
        self.assertEqual(
            vocabulary, max(S.SIX_SEAT_SEAT_IDS) + 1,
            "and its top seat id 101 is the last id inside it (seats.md §3, ASM-44): "
            "%r" % (vocabulary,),
        )
        steps = self.walk_shaped(S.SEED_MASK, S.THIRD_SHAPE, LAST)
        reached = set()
        for position, step in enumerate(steps):
            index, flag = S.seat_fact(step.readout["seat"])
            with self.subTest(decision=position, seat=(index, flag)):
                self.assertTrue(
                    0 <= index < S.SEATS[S.THIRD_SHAPE],
                    "the readout's seat index is inside the row's 0-5 (seats.md §3, "
                    "ASM-44): %r" % (index,),
                )
                values = [int(value) for value in
                          self.encode(encoder, step.readout).tolist()]
                self.assertEqual(
                    len(values), S.token_width(row),
                    "one real six-seat decision is the row's 122 tokens (capacity.md §2, "
                    "surface.md §6): %d" % (len(values),),
                )
                seat_ids = [ident for ident in values
                            if ident in S.SIX_SEAT_SEAT_IDS]
                self.assertEqual(
                    seat_ids, [S.SEAT_TOKEN_BASE + index],
                    "exactly one id from 96-101, and it is 96 + the acting seat's "
                    "index: the five other seat slots hold the pad and no other block "
                    "reaches the row's own seat ids (seats.md §3, card-tokens.md §3, "
                    "§6, ASM-44): %r for seat %r" % (seat_ids, index),
                )
                self.assertIn(
                    S.SEAT_TOKEN_BASE + index, S.SIX_SEAT_SEAT_IDS,
                    "the id is one of the six the row declares (seats.md §3, ASM-44): "
                    "%r" % (S.SEAT_TOKEN_BASE + index,),
                )
                self.assertLess(
                    max(values), vocabulary,
                    "every id of the observation stays inside the vocabulary of 102, so "
                    "an embedding table of that size holds the whole row (card-tokens.md "
                    "§6, capacity.md §4): %r" % (max(values),),
                )
                self.assertGreaterEqual(
                    min(values), 0,
                    "and no id is negative (card-tokens.md §6, guardrails.md G10): %r"
                    % (min(values),),
                )
                reached.add(S.SEAT_TOKEN_BASE + index)
        self.assertEqual(
            sorted(reached), list(S.SIX_SEAT_SEAT_IDS),
            "the walk rotates the acting seat through all six, so every id 96-101 is "
            "produced by a real decision (seats.md §3, §4, D-33): %r"
            % (sorted(reached),),
        )


class ShapesSixSeatHistory(ShapesCase):
    """A real six-seat readout carries a history of 98 entries, and refuses a 99th."""

    def test_join_shapes_11_a_real_six_seat_history_of_98_encodes_and_99_is_refused(self):
        """J-8.11 a history of exactly 98 entries, built from the entries a real
        six-seat hand really applied, encodes on that row in both encodings -- the dense
        history block's last 294 slots all live, the token history block's last 98 tokens
        all non-pad -- and a 99th entry is refused naming the field, the capacity and the
        count, never truncated, so the row's derived bound is what carries a real hand
        whole (capacity.md §1-§3, shapes.md §8, flat-numeric.md §5, card-tokens.md §5,
        ASM-42, ASM-44)."""
        row = self.catalog()[S.THIRD_SHAPE]
        capacity = int(row["history"])
        self.assertEqual(
            capacity, S.CAPACITY[S.THIRD_SHAPE],
            "the six-seat row's capacity is the 98 the battery reads out of the engine's "
            "catalogue (capacity.md §1, §5, D-13): %r" % (capacity,),
        )
        steps = self.walk_shaped(S.SEED_MASK, S.THIRD_SHAPE, LAST)
        longest = max(steps, key=lambda step: len(step.readout["history"]))
        real = list(longest.readout["history"])
        self.assertTrue(
            real,
            "the walk applied at least one real action, so the capacity's entries are "
            "the engine's own and not this battery's (capacity.md §3, D-13): %r"
            % (real,),
        )
        self.assertLessEqual(
            len(real), capacity,
            "a real six-seat hand's longest history is inside the row's own capacity, so "
            "no real decision is ever truncated (capacity.md §1, §3, ASM-42): %d entries"
            % (len(real),),
        )
        room = (real * (capacity // len(real) + 1))[:capacity]
        self.assertEqual(
            len(room), 98,
            "the battery holds 98 real entries, one per history slot (capacity.md §3, "
            "ASM-42): %d" % (len(room),),
        )
        readout = dict(longest.readout, history=room)
        for encoding in (DENSE, TOKENS):
            with self.subTest(encoding=encoding, entries=capacity):
                encoder = self.shaped_encoder(encoding, S.THIRD_SHAPE)
                spec = self.observation_spec(encoder)
                observation = self.encode(encoder, readout)
                self.assert_observation(encoding, spec, observation)
                values = [int(value) if encoding == TOKENS else float(value)
                          for value in observation.tolist()]
                if encoding == DENSE:
                    start = (S.SEAT_INVARIANT_DENSE_SLOTS
                             + 2 * S.SEATS[S.THIRD_SHAPE])
                    block = values[start:]
                    self.assertEqual(
                        len(block), 3 * capacity,
                        "the dense history block is the last 3 x 98 = 294 slots, from "
                        "slot 139 to 432 (flat-numeric.md §5, capacity.md §2): %d"
                        % (len(block),),
                    )
                    self.assertEqual(
                        sum(1 for value in block if value == 1.0), capacity,
                        "98 applied actions are 98 one-hots, so the last slot is live and "
                        "the block was not truncated (flat-numeric.md §5, ASM-42)",
                    )
                else:
                    start = (S.SEAT_INVARIANT_TOKEN_SLOTS
                             + 2 * S.SEATS[S.THIRD_SHAPE])
                    block = values[start:]
                    self.assertEqual(
                        len(block), capacity,
                        "the token history block is the last 98 tokens, from token 24 to "
                        "121 (card-tokens.md §5, capacity.md §2): %d" % (len(block),),
                    )
                    self.assertNotIn(
                        0, block,
                        "a full 98-entry history leaves no pad token: the block's width "
                        "and its capacity are one number (card-tokens.md §5, ASM-42): %r"
                        % (block[:6],),
                    )
                self.assert_named_refusal(
                    lambda encoder=encoder, readout=readout, real=real: self.encode(
                        encoder, dict(readout, history=room + [real[0]])),
                    "encode",
                    "one entry past the six-seat row's 98 must be refused, never "
                    "truncated (capacity.md §3, ASM-42)",
                    words=("history", str(capacity), str(capacity + 1)),
                )


if __name__ == "__main__":
    unittest.main()

