"""J-8 -- the second declared game shape, at the module join.

`docs/L2/features/shapes.md` §1-§6, `docs/L2/features/surface.md` §4 and §7-§9,
`docs/L2/engine/surface.md` §12, `docs/L1/shapes.md` §2-§3 (D-29, D-13) and
`docs/L1/e2e-surface.md` §3.2.

The shape is declared twice -- once by `engine.game_shapes()` and once by this module's
own row -- and the join battery is the whole of how the two statements stay equal
(`shapes.md` §1, §6).  Every case here therefore reads the engine's catalogue and hands
the module what the engine actually produces: a real hand of one shape, a real readout,
the engine's own legal descriptors, and the handle `engine.apply_action` returns for a
descriptor `features.decode_action` decoded.

Nothing here writes down a shape's descriptors, its normalisers or a slot index of its
own: they are read from `engine.game_shapes()`, from the observation the module returns,
and from the row the catalogue publishes -- so a case asserts that the two statements
agree and never that this battery's copy of one of them is the design
(`docs/L1/battery.md` §2, §4, D-11, D-15).
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
        """
        record = dict(base)
        record["stacks"] = (int(values["stack"]), int(values["stack"]))
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
        the same table (shapes.md §1, §2, §6; flat-numeric.md §4, D-13)."""
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
                encoder = self.shaped_encoder(DENSE, name)
                floor_facts = {key: 0 for key in NORMALISERS}
                floor = S.canonical(self.encode(encoder, self.at_normalisers(base, floor_facts)))
                self.assertEqual(
                    len(floor), S.SHAPES[DENSE][0],
                    "the dense observation is as long as the encoding declares on either "
                    "shape: the slot count does not move (shapes.md §5, surface.md §5): "
                    "%d slots against %r" % (len(floor), S.SHAPES[DENSE]),
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
                    ["stack", "stack"],
                    "the stack normaliser is the one that reaches two slots, because the "
                    "block carries both seats' stacks (flat-numeric.md §2, §4): %r"
                    % (sorted(reached),),
                )
                self.assertEqual(
                    len(reached), 6,
                    "the two stacks plus the pot, the amount to call and the bet size "
                    "and count are six amount slots on either shape (surface.md §5, "
                    "flat-numeric.md §2, §4): %r" % (sorted(reached),),
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
    """Both encodings keep the declared shape, and the default's values do not move."""

    def test_join_shapes_04_both_encodings_keep_their_declared_shape_and_dtype(self):
        """J-8.4 both encodings encode a no-limit-100 readout to their declared shape and
        dtype, and both encode a default-shape readout to the very values
        build_encoder(name) with no shape produces, so the default shape's observations
        are unchanged (surface.md §4-§6, shapes.md §5, e2e-surface.md §3.2, D-29)."""
        shaped = self.readout(self.new_shaped_hand(S.SEED_ENCODE, SECOND))
        for name in (DENSE, TOKENS):
            with self.subTest(encoding=name, readout=SECOND):
                encoder = self.shaped_encoder(name, SECOND)
                spec = self.observation_spec(encoder)
                observation = self.encode(encoder, shaped)
                self.assert_observation(name, spec, observation)
                self.assertEqual(
                    self.declared_shape(spec), S.SHAPES[name],
                    "an encoder built for the second shape still declares %r: the slot "
                    "count is the encoding's and not the shape's (shapes.md §5, "
                    "surface.md §5): %r" % (S.SHAPES[name], self.declared_shape(spec)),
                )
                self.assertEqual(
                    str(spec["dtype"]), S.DTYPES[name],
                    "and still declares the encoding's dtype (shapes.md §5, surface.md "
                    "§5): %r" % (spec["dtype"],),
                )
                self.assertEqual(
                    self.observation_spec(self.build_encoder(name)), spec,
                    "the spec record of an encoder built for the second shape is the "
                    "record of one built with no shape, value for value: the shape names "
                    "no key (shapes.md §5, surface.md §5): %r"
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
                self.assert_observation(name, self.spec(name), named)


class ShapesRefusals(ShapesCase):
    """The refusals the shape adds, and the arity it does not move."""

    def test_join_shapes_05_an_undeclared_shape_is_refused_and_the_shape_stays_a_keyword(self):
        """J-8.5 features.action_space(shape=...) and features.build_encoder(..., shape=...)
        -- and features.decode_action(index, shape=...) -- refuse a name that is no
        declared shape by a message naming the rejected value and both declared names,
        and a positional shape argument is still Python's TypeError, so no pre-existing
        arity moved (shapes.md §1, §6, surface.md §4, §7, §9, D-11, D-29)."""
        declared = self.shape_names()
        self.assertEqual(
            set(declared), {DEFAULT, SECOND},
            "the two declared names this case reads out of the engine's catalogue are the "
            "two the module declares (shapes.md §1, §6): %r" % (list(declared),),
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


if __name__ == "__main__":
    unittest.main()
