"""FAM-2 — the game, the action vocabulary and the information set never move.

`docs/L1/battery.md` §3 FAM-2, `docs/L1/e2e-surface.md` §2, D-2 and D-3.  The ladder
changes how the agent *represents* what it knows (D-3); it never changes what it knows
(the readout facts of `e2e-surface.md` §2), the vocabulary it chooses from, or the game
it plays (D-2).  Rev 2 did not move any of that: D-16 changed the opponent, and the
league's cells are played on the same game, from the same readout, over the same three
action indices.  D-21 added an eleventh readout fact, `hand_class`, and this family holds
it to the same rule: it is one of the facts every rung's agent is handed, its contract is
`None` before the flop and an integer 0..8 after it, and no encoding carries it, so D-3's
information set and every shipped checkpoint's shape are unchanged (`e2e-surface.md` §2,
`folders.md` §3, ASM-30).  These cases hold the invariance across every rung and every
declared encoding, and they are the invariants a single module cannot check about itself
(`battery.md` §5).

FAM-2.14 holds the fact's **value** to what a battery may read without a poker
evaluator: over a walk of real hands the post-flop classes take more than one distinct
value and include both high card (0) and a hand better than high card, so a readout
whose `hand_class` were a constant — or never left one end of the range — is caught
here rather than only one layer down in `tests/engine`.  No case asserts a class for a
particular deal, because the battery may not import the library that computes it
(`folders.md` §3, ASM-30, D-13).

**D-29 does not move any of it.**  The project declares a second game shape, and the
invariants of this family are asserted **for the shape in force**: cases 2.1, 2.2, 2.9,
2.10 and 2.11 state today's game, today's three indices and today's readout when no shape
is named — unchanged, because absence is the default shape (`shapes.md` §5) — and cases
2.15–2.18 state the same contracts for the shape the catalogue declares second: its
dealt game, its declared vocabulary in its own index order, one index per legal
descriptor, a decode that round-trips into the engine, and the eleven readout facts
unchanged (`shapes.md` §2–§3, §5, `e2e-surface.md` §2 "Game shape", D-29).

**D-33's widening is the shape's and not the information set's.**  The history block's
capacity became the shape's own data, so the two layouts differ in length — 203 dense and
40 tokens on the default shape, 329 and 82 on `no-limit-100` — while the fields the
encoding carries and the token vocabulary of 96 do not move.  FAM-2.19 holds exactly that:
the widening is a longer layout of the same facts, and with no shape named the observation
is today's 203/40 (`shapes.md` §8, ASM-42, ASM-44, `flat-numeric.md` §5).
"""

import os
import sys
import unittest

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _surface as S  # noqa: E402


# The seeds FAM-2.14 walks to observe `hand_class`'s value.  The battery's own invented
# seeds, one hand per seed (`battery.md` §4), driven through `always-call` so every hand
# reaches the flop, turn and river.  Verified over this walk: 8 seeds and 8 decisions per
# hand give 48 post-flop decisions, on which the fact is not constant — high card `0`
# occurs 15 times and a pair or better 33 times, spread over classes 0, 1, 2, 3, 5 and 6
# (measured 2026-11-09; the game is deterministic from the seed, ASM-2).  Both ends of the
# range are therefore observed, not hoped for (`folders.md` §3, ASM-30, D-21).
HAND_CLASS_WALK_SEEDS = (
    S.SEED_A,
    S.SEED_B,
    S.SEED_C,
    S.SEED_D,
    S.SEED_E,
    S.SEED_F,
    S.SEED_G,
    S.SEED_H,
)


class FAM2Invariance(S.SurfaceCase):
    """The D-2 and D-3 invariants, held across the whole ladder."""

    def encoding_names(self):
        """The declared encoding names, read from ``features.encodings()``."""
        declared = self.ep("features", "encodings")()
        found = []
        for text in S.strings(declared):
            if text in (S.FLAT, S.TOKENS) and text not in found:
                found.append(text)
        self.assertEqual(
            sorted(found),
            sorted([S.FLAT, S.TOKENS]),
            "features.encodings() must declare %r and %r with their representation kind; got %r"
            % (S.FLAT, S.TOKENS, declared),
        )
        return found

    def spec(self, encoding):
        return self.ep("features", "observation_spec")(self.encoder(encoding))

    def test_fam2_1_game_config_is_one_fixed_declaration(self):
        """FAM-2.1 engine.game_config is deterministic and is ASM-6's fixed game (D-2).

        The shape in force is the **default**: naming none is today's game, and naming the
        catalogue's first shape by name is the same row — so a caller that predates the
        catalogue reads the mapping it always read (`shapes.md` §2, §5, D-29).
        """
        config = self.ep("engine", "game_config")()
        again = self.ep("engine", "game_config")()
        self.assertEqual(S.canon(config), S.canon(again), "game_config() changed between calls")
        values = set(S.numbers(config))
        for declared in (20, 4):
            self.assertIn(
                declared,
                values,
                "the fixed game of e2e-surface.md §3.1 must declare %d; got %r" % (declared, config),
            )
        self.assertIn(2, values, "the fixed game must declare its two seats or its blinds")
        self.assertEqual(
            S.canon(config),
            S.canon(self.game_config(self.shape_names()[0])),
            "game_config() with no argument is the default shape's row, and naming that "
            "shape by name is the same row — absence and the first declared name are one "
            "game (shapes.md §2, §3, D-29)",
        )

    def test_fam2_2_the_dealt_game_has_the_fixed_parameters(self):
        """FAM-2.2 a first decision shows blinds 1/2 and stacks 20 (ASM-6, D-2).

        The shape in force is the default, so this is today's game unchanged; the second
        shape's dealt game is FAM-2.15's (``shapes.md`` §2, §5, D-29).
        """
        readout = self.readout(self.hand(S.SEED_A))
        self.assertEqual(readout["street"], "preflop")
        self.assertEqual(readout["pot"], 3, "the blinds committed to the pot must be 1 + 2")
        self.assertEqual(sum(S.numbers(readout["stacks"])), 37,
                         "the two stacks must hold 20 + 20 - 3 chips")
        self.assertEqual(readout["to_call"], 1, "the button owes the big blind one chip")

    def test_fam2_3_readout_has_exactly_the_declared_facts(self):
        """FAM-2.3 readout returns exactly the eleven facts of e2e-surface.md §2."""
        readout = self.readout(self.hand(S.SEED_A))
        self.assertEqual(
            set(readout),
            set(S.READOUT_FACTS),
            "readout's keys must be exactly the declared information set, eleven facts "
            "since D-21 added `hand_class` (e2e-surface.md §2, folders.md §3, ASM-30)",
        )
        self.assertIn(
            "hand_class",
            readout,
            "the eleventh fact is `hand_class`, the class of the acting seat's best "
            "five-card hand of hole plus board (e2e-surface.md §2, folders.md §3, D-21)",
        )

    def test_fam2_4_every_encoding_carries_the_same_fields(self):
        """FAM-2.4 features.observation_spec fields are identical for every encoding."""
        fields = {}
        for encoding in self.encoding_names():
            spec = self.spec(encoding)
            carried = spec["fields"]
            fields[encoding] = set(str(field) for field in carried)
        first = next(iter(fields.values()))
        for encoding, carried in fields.items():
            self.assertEqual(
                carried,
                first,
                "the ladder must not change what the agent may know: %r carries %r, not %r"
                % (encoding, sorted(carried), sorted(first)),
            )

    def test_fam2_5_observation_fields_are_readout_facts(self):
        """FAM-2.5 the encoded fields are a subset of the readout facts (D-3)."""
        for encoding in self.encoding_names():
            spec = self.spec(encoding)
            carried = set(str(field) for field in spec["fields"])
            self.assertTrue(carried, "%r carries no observation at all" % (encoding,))
            self.assertTrue(
                carried <= set(S.READOUT_FACTS),
                "%r carries fields that are not readout facts: %r"
                % (encoding, sorted(carried - set(S.READOUT_FACTS))),
            )

    def test_fam2_6_representation_names_the_encoding(self):
        """FAM-2.6 observation_spec names the representation of §2."""
        for encoding in self.encoding_names():
            spec = self.spec(encoding)
            text = S.flatten_text(spec["representation"])
            self.assertIn(
                S._family_token(encoding),
                S._family_token(text),
                "the spec of %r must declare representation %r; got %r"
                % (encoding, encoding, spec["representation"]),
            )

    def test_fam2_7_spec_declares_shape_and_dtype(self):
        """FAM-2.7 observation_spec declares the shape and dtype of one observation."""
        for encoding in self.encoding_names():
            spec = self.spec(encoding)
            self.assertIn("shape", spec, "the spec of %r declares no shape" % (encoding,))
            self.assertIn("dtype", spec, "the spec of %r declares no dtype" % (encoding,))
            self.assertTrue(S.flatten_text(spec["dtype"]).strip(),
                            "the spec of %r declares an empty dtype" % (encoding,))

    def test_fam2_8_encoded_observation_matches_the_declared_shape(self):
        """FAM-2.8 encode returns one observation of the declared shape."""
        readout = self.readout(self.hand(S.SEED_B))
        for encoding in self.encoding_names():
            encoder = self.encoder(encoding)
            spec = self.ep("features", "observation_spec")(encoder)
            observation = self.ep("features", "encode")(encoder, readout)
            shape = tuple(int(value) for value in S.numbers(spec["shape"]))
            if hasattr(observation, "shape"):
                self.assertEqual(tuple(observation.shape), shape,
                                 "%r returned a %r observation, declared %r"
                                 % (encoding, tuple(observation.shape), shape))
            else:
                self.assertEqual(len(observation), _product(shape),
                                 "%r returned %d values, declared %r"
                                 % (encoding, len(observation), shape))

    def test_fam2_9_action_space_is_the_three_index_vocabulary(self):
        """FAM-2.9 features.action_space is the fixed 0/1/2 vocabulary (D-2).

        The shape in force is the default, so the vocabulary is today's three indices and
        the descriptors they name, read through `decode_action` rather than spelled here;
        the second shape's six are FAM-2.16's (`e2e-surface.md` §2 "Action vocabulary").
        """
        space = self.action_space()
        vocabulary = S.action_vocabulary(space)
        self.assertEqual(
            vocabulary,
            {0, 1, 2},
            "the vocabulary is the game's three indices — fold 0, check/call 1, raise 2 — "
            "however the container keys them, a sequence or a mapping keyed by name or by "
            "the indices themselves (e2e-surface §2): %r" % (space,),
        )
        self.assertEqual(
            [self.decode_action(index) for index in sorted(vocabulary)],
            list(S.FIXED_ACTIONS),
            "the default shape's indices decode to its three declared descriptors, in the "
            "shape's own order (e2e-surface.md §2, shapes.md §2, D-29): %r" % (space,),
        )

    def test_fam2_10_decode_action_round_trips_into_the_engine(self):
        """FAM-2.10 decode_action gives a descriptor apply_action accepts (D-2).

        On the shape in force — the default, whose three indices are asserted above; the
        second shape's round trip is FAM-2.17's (`sizing.md` §3, D-29).
        """
        legal = self.legal(self.hand(S.SEED_C))
        indices = list(self.ep("features", "legal_indices")(legal))
        self.assertTrue(indices, "no legal index at the first decision")
        self.assertTrue(set(indices) <= {0, 1, 2},
                        "legal indices outside the declared vocabulary: %r" % (indices,))
        for index in indices:
            descriptor = self.ep("features", "decode_action")(index)
            fresh = self.hand(S.SEED_C)
            advanced = self.ep("engine", "apply_action")(fresh, descriptor)
            self.assertIsNotNone(advanced,
                                 "decode_action(%r) gave a descriptor the engine refused" % (index,))

    def test_fam2_11_every_legal_descriptor_has_one_index(self):
        """FAM-2.11 the legal descriptors and the legal indices correspond one to one.

        Position-aligned, and never sorted: the alignment is the contract and it does not
        depend on the shape, so the second shape's decisions are held to it as well
        (FAM-2.17) (`e2e-surface.md` §2, `shapes.md` §3, D-29).
        """
        legal = self.legal(self.hand(S.SEED_C))
        indices = list(self.ep("features", "legal_indices")(legal))
        self.assertEqual(
            len(indices),
            len(legal),
            "one index per legal descriptor: %r descriptors, %r indices"
            % (len(legal), len(indices)),
        )
        self.assertEqual(
            len(set(indices)),
            len(indices),
            "the indices of one decision are distinct: %r" % (indices,),
        )
        for index in indices:
            descriptor = self.ep("features", "decode_action")(index)
            advanced = self.ep("engine", "apply_action")(self.hand(S.SEED_C), descriptor)
            self.assertIsNotNone(
                advanced,
                "decode_action(%r) must give a descriptor the engine accepts at this "
                "decision" % (index,),
            )


    def test_fam2_12_hand_class_is_none_before_the_flop_and_a_class_after_it(self):
        """FAM-2.12 hand_class is `None` pre-flop and an integer 0-8 from the flop on.

        D-21's derived fact (`e2e-surface.md` §2, `folders.md` §3, ASM-30): fewer than
        five cards are known before the flop, so no five-card hand exists and the fact is
        `None`; from the flop onward it is the class of the best five-card hand of hole
        plus board, an integer in 0..8 — 0 high card, 1 one pair, 2 two pair, 3 three of a
        kind, 4 straight, 5 flush, 6 full house, 7 four of a kind, 8 straight flush.
        Observed over hands the case plays, so a fact that is `None` on the flop, or a
        string, or a class outside the nine, is caught where it is exposed.
        """
        observed = {"preflop": 0, "later": 0}
        for seed in (S.SEED_A, S.SEED_C, S.SEED_F):
            for _hand, readout, _legal, _action, _index in self.decision_walk(seed):
                street = str(S.readout_fact(readout, "street")).strip().lower()
                hand_class = S.readout_fact(readout, "hand_class")
                if street == "preflop":
                    observed["preflop"] += 1
                    self.assertIsNone(
                        hand_class,
                        "before the flop fewer than five cards are known, so `hand_class` "
                        "is None (e2e-surface.md §2, folders.md §3, ASM-30): %r at seed %r"
                        % (hand_class, seed),
                    )
                    continue
                observed["later"] += 1
                self.assertTrue(
                    S.is_count(hand_class),
                    "from the flop onward `hand_class` is the class of the best five-card "
                    "hand of hole plus board, an integer (e2e-surface.md §2, folders.md §3, "
                    "ASM-30): %r at %s of seed %r" % (hand_class, street, seed),
                )
                self.assertGreaterEqual(
                    int(hand_class),
                    0,
                    "the nine classes are 0..8 — high card is 0 (folders.md §3, ASM-30): "
                    "%r at %s of seed %r" % (hand_class, street, seed),
                )
                self.assertLessEqual(
                    int(hand_class),
                    8,
                    "the nine classes are 0..8 — a straight flush is 8, and there is no "
                    "tenth class (folders.md §3, ASM-30): %r at %s of seed %r"
                    % (hand_class, street, seed),
                )
        self.assertGreater(
            observed["preflop"],
            0,
            "the case must observe the pre-flop arm of the contract it asserts",
        )
        self.assertGreater(
            observed["later"],
            0,
            "the case must observe the fact on a flop, turn or river decision, or its "
            "post-flop arm proves nothing (folders.md §3)",
        )

    def test_fam2_13_no_encoding_carries_hand_class(self):
        """FAM-2.13 hand_class is a readout fact no encoding carries (D-3, ASM-30)."""
        readout = self.readout(self.hand(S.SEED_A))
        self.assertIn(
            "hand_class",
            readout,
            "the readout exposes `hand_class` (e2e-surface.md §2, folders.md §3)",
        )
        for encoding in self.encoding_names():
            spec = self.spec(encoding)
            carried = {str(field) for field in spec["fields"]}
            self.assertNotIn(
                "hand_class",
                carried,
                "`hand_class` is a derived fact of `hole` and `board` and **no encoding "
                "carries it**, so the information set D-3 fixes and every shipped "
                "checkpoint's encoding are unchanged (e2e-surface.md §2, folders.md §3, "
                "ASM-30, D-21): %r carries %r" % (encoding, sorted(carried)),
            )


    def test_fam2_14_hand_class_discriminates_over_a_walk_of_real_hands(self):
        """FAM-2.14 the post-flop `hand_class` takes more than one value: 0 and better.

        FAM-2.12 and FAM-16.2 pin the fact's *contract* — `None` before the flop, an
        integer 0..8 after it — and FAM-5.10 reads its fold rule off the same fact the
        folder reads, so a readout whose `hand_class` were a constant `0` at every
        post-flop decision would satisfy all three, and every rule stated above them.
        The value is falsified one layer down (`tests/engine` re-derives the class), but
        the battery's own division of labour has to make a constant fall here too, and
        this is the strongest claim it may make without a poker evaluator and without
        guessing a class for a particular deal (`folders.md` §3, ASM-30, D-13): over a
        walk of real hands at the battery's own seeds, the post-flop values take **more
        than one** distinct value, at least one decision is exactly `0` (high card) and
        at least one is **strictly above** `0` (a pair or better).  A constant, a class
        that never reaches the high-card end, or a class that never leaves it is caught
        with the distinct values and their counts named in the failure.

        The walk is `engine.new_hand` / `engine.readout` / `engine.legal_actions` /
        `engine.apply_action` / `engine.is_terminal` with `agents.build_baseline`'s
        `always-call` as the policy, so every hand reaches the flop, turn and river
        (`e2e-surface.md` §2, §3.1, §3.3); the walk length and the seeds are fixed, and
        the game is deterministic from the seed (ASM-2), so the observed counts are
        fixed too — the case observes both ends rather than asserting it hopes to.
        """
        counts = {}
        decisions = 0
        for seed in HAND_CLASS_WALK_SEEDS:
            for _hand, readout, _legal, _action, _index in self.decision_walk(seed):
                street = str(S.readout_fact(readout, "street")).strip().lower()
                if street == "preflop":
                    continue
                hand_class = S.readout_fact(readout, "hand_class")
                self.assertTrue(
                    S.is_count(hand_class),
                    "from the flop onward `hand_class` is the class of the best five-card "
                    "hand of hole plus board, an integer 0..8, so this walk can count it "
                    "(e2e-surface.md §2, folders.md §3, ASM-30): %r at %s of seed %r"
                    % (hand_class, street, seed),
                )
                value = int(hand_class)
                counts[value] = counts.get(value, 0) + 1
                decisions += 1
        self.assertGreater(
            decisions,
            0,
            "the case must observe `hand_class` on post-flop decisions of real hands, or "
            "it asserts nothing about its value (folders.md §3): seeds %r"
            % (HAND_CLASS_WALK_SEEDS,),
        )
        seen = ", ".join(
            "class %d x%d" % (value, counts[value]) for value in sorted(counts)
        )
        self.assertGreater(
            len(counts),
            1,
            "over a walk of real hands the post-flop `hand_class` must take more than one "
            "distinct value, or it is a constant and tells a policy nothing its street "
            "did not already — a constant `0` would satisfy the fact's contract and "
            "FAM-5.10's fold rule alike (e2e-surface.md §2, folders.md §3, ASM-30): %d "
            "post-flop decisions at seeds %r, the classes %s"
            % (decisions, HAND_CLASS_WALK_SEEDS, seen),
        )
        self.assertIn(
            0,
            counts,
            "`0` is high card — the class `fold-no-pair-or-better` folds on — so the walk "
            "must observe at least one post-flop decision with no pair at all, or the "
            "fact's low end is asserted from one side only (folders.md §2, §3, ASM-30): "
            "%d post-flop decisions at seeds %r, the classes %s"
            % (decisions, HAND_CLASS_WALK_SEEDS, seen),
        )
        self.assertTrue(
            any(value > 0 for value in counts),
            "the walk must observe at least one post-flop decision whose best five-card "
            "hand is better than high card — at least a pair — so the fact is shown to "
            "separate the class the folder folds on from every class above it "
            "(folders.md §2, §3, ASM-30): %d post-flop decisions at seeds %r, the "
            "classes %s" % (decisions, HAND_CLASS_WALK_SEEDS, seen),
        )


    # ==================================================================
    # The same three contracts, for every shape beside the default
    # ==================================================================
    def test_fam2_15_a_declared_shape_deals_its_own_game(self):
        """FAM-2.15 every shape declared beside the default deals its own game, at its own chips.

        The catalogue declares the default shape first and two rows beside it — D-29's
        two-seat uncapped one and D-33's six-seat one — and naming a row is the only way to
        reach it (`shapes.md` §2, `seats.md` §2, `e2e-surface.md` §2 "Game shape").  So the
        first decision of a hand on each of them shows the blinds committed to the pot and
        that row's own total behind them, and `pot + sum(stacks)` is that total at **every**
        decision of a walk — the invariant each row's `chips_in_play` states, two seats or
        six (`seats.md` §3, ASM-28) — while the default shape's hand at the same seed is a
        different game.
        """
        default = self.shape_names()[0]
        pot = self.readout(self.hand(S.SEED_A))["pot"]
        for shape in self.other_shapes():
            self.assertNotEqual(
                shape, default,
                "the shapes compared here are the ones declared beside the default",
            )
            row = self.shape_row(shape)
            total = [int(number) for number in S.numbers(
                S.declared_field(row, "a declared shape row (shapes.md §2)", "chips_in_play"))]
            self.assertTrue(
                total,
                "a shape row declares the chips in play — `pot + sum(stacks)` at every "
                "decision (shapes.md §2, seats.md §2): %r" % (row,),
            )
            chips = total[0]
            seats = self.seats_of(shape)
            readout = self.readout(self.hand(S.SEED_A, shape))
            self.assertEqual(readout["street"], "preflop")
            self.assertEqual(
                readout["pot"],
                pot,
                "the declared shapes share the table: the blinds committed to the pot are "
                "the same on %r (shapes.md §2): %r against %r"
                % (shape, readout["pot"], pot),
            )
            self.assertEqual(
                len(list(S.numbers(readout["stacks"]))),
                seats,
                "the shape's stacks are one per seat — two on the two-seat rows and six on "
                "the six-seat one (seats.md §3, ASM-28): %r" % (readout["stacks"],),
            )
            self.assertEqual(
                sum(S.numbers(readout["stacks"])),
                chips - readout["pot"],
                "on %r the stacks hold that shape's own total less the pot: %r chips in "
                "play against stacks %r" % (shape, chips, readout["stacks"]),
            )
            decisions = 0
            for seed in S.SHAPE_SEEDS[:4]:
                for _hand, facts, _legal, _action, _index in self.decision_walk(
                    seed, shape=shape
                ):
                    decisions += 1
                    self.assertEqual(
                        facts["pot"] + sum(S.numbers(facts["stacks"])),
                        chips,
                        "`pot + sum(stacks)` is %r's chips in play at every decision and not "
                        "only at the first (shapes.md §2, seats.md §3, D-29): seed %r, street "
                        "%r, pot %r, stacks %r"
                        % (shape, seed, facts["street"], facts["pot"], facts["stacks"]),
                    )
            self.assertGreater(
                decisions, 1,
                "the case must walk real decisions on %r" % (shape,),
            )
            self.assertNotEqual(
                S.canon(self.readout(self.hand(S.SEED_A, shape))),
                S.canon(self.readout(self.hand(S.SEED_A))),
                "naming %r reaches that game, not the default one (shapes.md §2, §3)"
                % (shape,),
            )

    def test_fam2_16_the_uncapped_shapes_declare_their_six_descriptors_in_order(self):
        """FAM-2.16 each uncapped shape's vocabulary is its six descriptors, in its own order.

        `sizing.md` §3 fixes the index order as the measured price order, worst first —
        `fold` 0, `check-call` 1, `raise-quarter` 2, `raise-half` 3, `raise-all-in` 4,
        `raise-minimum` 5 — and `features.action_space(shape)` publishes a shape's
        descriptors in that shape's order (`e2e-surface.md` §2 "Action vocabulary").  A seat
        count adds no descriptor, so both uncapped rows declare the same six in the same
        order and only the default shape's three differ (`shapes.md` §2, `seats.md` §2).  The
        default shape's three are asserted in FAM-2.9 and are untouched.
        """
        for shape in self.other_shapes():
            space = self.action_space(shape)
            vocabulary = S.action_vocabulary(space)
            self.assertEqual(
                vocabulary,
                set(range(len(S.SIZED_ACTIONS))),
                "the no-cap shape's vocabulary is six indices — however the container keys "
                "them, a sequence or a mapping keyed by name or by the indices themselves "
                "(e2e-surface.md §2, shapes.md §2): %r" % (space,),
            )
            self.assertEqual(
                [self.decode_action(index, shape) for index in sorted(vocabulary)],
                list(S.SIZED_ACTIONS),
                "the shape's indices decode to its declared descriptors **in its own index "
                "order** — fold, check-call, quarter, half, all-in, minimum — and the order "
                "is not monotone in amount (sizing.md §2–§3): %r" % (space,),
            )
            # The engine's legal tuple is the shape's declared order too, at a decision where
            # all six are legal: the first of a no-cap hand offers every band.
            hand = self.hand(S.SEED_A, shape)
            legal = self.legal(hand)
            indices = list(self.ep("features", "legal_indices")(legal))
            self.assertEqual(
                indices,
                sorted(indices),
                "engine.legal_actions returns the legal subset in the shape's index order, "
                "and features.legal_indices is position-aligned (e2e-surface.md §2, "
                "sizing.md §3): %r" % (legal,),
            )
            self.assertTrue(
                set(indices) <= vocabulary,
                "every legal descriptor is one of the shape's indices: %r against %r"
                % (indices, sorted(vocabulary)),
            )
            self.assertEqual(
                len(legal),
                len(indices),
                "one index per legal descriptor: %r descriptors, %r indices" % (len(legal), len(indices)),
            )

    def test_fam2_17_each_shapes_indices_round_trip_into_the_engine(self):
        """FAM-2.17 on every declared shape one index per descriptor, and each decodes legally.

        The two facts FAM-2.10 and FAM-2.11 assert of the default shape, held of the shape
        in force: at every decision of a walk, the legal indices are distinct, one per
        descriptor, and each `decode_action(index, shape)` is a descriptor
        `engine.apply_action` accepts at that decision (`e2e-surface.md` §2, D-2, D-29,
        `seats.md` §2 — a six-seat hand is one hand and its indices are its shape's).
        """
        for shape in self.other_shapes():
            vocabulary = S.action_vocabulary(self.action_space(shape))
            decisions = 0
            for seed in S.SHAPE_SEEDS[:4]:
                walk = self.decision_walk(seed, shape=shape)
                for _hand, _facts, legal, _action, _index in walk:
                    decisions += 1
                    indices = list(self.ep("features", "legal_indices")(legal))
                    self.assertEqual(
                        len(indices), len(legal),
                        "one index per legal descriptor on the named shape: %r against %r"
                        % (indices, legal),
                    )
                    self.assertEqual(
                        len(set(indices)), len(indices),
                        "the indices of one decision are distinct: %r" % (indices,),
                    )
                    self.assertTrue(
                        set(indices) <= vocabulary,
                        "legal indices outside the shape's declared vocabulary: %r against %r"
                        % (indices, sorted(vocabulary)),
                    )
                    for index in indices:
                        descriptor = self.decode_action(index, shape)
                        self.assertIn(
                            descriptor, legal,
                            "decode_action(%r, %r) gives %r, which is not legal at this "
                            "decision (%r)" % (index, shape, descriptor, legal),
                        )
                        advanced = self.ep("engine", "apply_action")(
                            self.hand(seed, shape), descriptor
                        )
                        self.assertIsNotNone(
                            advanced,
                            "decode_action(%r, %r) must give a descriptor the engine accepts "
                            "at this decision" % (index, shape),
                        )
            self.assertGreater(decisions, 1, "the case must walk real decisions on the shape")

    def test_fam2_18_every_declared_shape_carries_the_same_eleven_facts(self):
        """FAM-2.18 the readout's eleven facts are the same facts on every declared shape.

        The shape changes what the facts *mean*, how many seats `stacks` carries and what
        the divisors divide, never which facts they are: `e2e-surface.md` §2's eleven keys,
        `hand_class` `None` before the flop in every game, and the shape's own legal set as
        the `legal` fact — so no twelfth fact arrives with a second or a third shape
        (`shapes.md` §2, §5, `seats.md` §3, D-29, D-33).
        """
        default = self.readout(self.hand(S.SEED_B))
        for shape in self.other_shapes():
            named = self.readout(self.hand(S.SEED_B, shape))
            self.assertEqual(
                sorted(named), sorted(default),
                "both declared shapes expose exactly the eleven readout facts of "
                "e2e-surface.md §2; the named shape exposes %r against %r"
                % (sorted(named), sorted(default)),
            )
            self.assertEqual(
                set(named), set(S.READOUT_FACTS),
                "the named shape's readout carries the declared information set, and no "
                "twelfth fact with it (e2e-surface.md §2, shapes.md §2, D-29)",
            )
            self.assertIsNone(
                named["hand_class"],
                "before the flop fewer than five cards are known on the no-cap shape too, so "
                "`hand_class` is None (e2e-surface.md §2, folders.md §3, ASM-30)",
            )
            self.assertEqual(
                list(self.ep("features", "legal_indices")(named["legal"])),
                list(self.ep("features", "legal_indices")(self.legal(self.hand(S.SEED_B, shape)))),
                "the readout's `legal` fact is the same ordered set engine.legal_actions "
                "returns on that shape (e2e-surface.md §2)",
            )

    def test_fam2_19_the_widening_is_the_shapes_and_the_facts_are_not(self):
        """FAM-2.19 each widened history moves its shape's layout, never the facts it carries.

        `shapes.md` §5 is the constraint D-33 widened under, and §8 widened the history block
        **per shape** rather than coarsening it or truncating it (`shapes.md` §8, ASM-42):
        the default shape keeps its 24 slots, so with no shape named the dense observation is
        today's **203** values and the token observation today's **40** over the vocabulary of
        **96**; the two-seat uncapped row is **329** and **82** over the same 96 ids; and the
        six-seat row is **433** and **122** over **102**, its own capacity of 98 behind the
        width and its six seat ids above every id the other rows use (`shapes.md` §2, §8,
        `seats.md` §3, `flat-numeric.md` §5, `card-tokens.md` §2).  What a shape changes is
        the layout's length, the divisors and the ids it needs, never which facts the agent
        is handed: the nine fields the encoding carries are identical on every declared
        shape, so a widening adds no twelfth fact and drops none (`e2e-surface.md` §2
        "Observation spec", D-3, ASM-44).
        """
        default = self.shape_names()[0]
        for shape in self.other_shapes():
            self.assertGreater(
                S.SHAPE_LAYOUTS[shape]["history"], S.SHAPE_LAYOUTS[default]["history"],
                "the case is about a widening: %r's capacity is larger than the default "
                "shape's (shapes.md §8, D-33): %r against %r"
                % (shape, S.SHAPE_LAYOUTS[shape]["history"],
                   S.SHAPE_LAYOUTS[default]["history"]),
            )
            for encoding in self.encoding_names():
                key = "dense" if encoding == S.FLAT else "tokens"
                plain = self.spec(encoding)
                named = self.ep("features", "observation_spec")(self.encoder(encoding, shape))
                widths = {}
                for label, spec, expected in (
                    ("no shape named", plain, S.SHAPE_LAYOUTS[default][key]),
                    ("named", named, S.SHAPE_LAYOUTS[shape][key]),
                ):
                    width = _product(
                        S.declared_field(spec, "an observation spec (e2e-surface.md §2)",
                                         "shape")
                    )
                    widths[label] = width
                    self.assertEqual(
                        width, expected,
                        "%r's observation is %d wide on %r with %r — the default shape's "
                        "unchanged and the named one's widened by its own capacity "
                        "(shapes.md §2, §5, §8): declared %d"
                        % (encoding, expected, shape, label, width),
                    )
                self.assertGreater(
                    widths["named"], widths["no shape named"],
                    "the widening is %r's, so its observation is the wider one (shapes.md "
                    "§8, D-33): %r against %r"
                    % (shape, widths["named"], widths["no shape named"]),
                )
                self.assertEqual(
                    S.canon(S.declared_field(plain, "an observation spec (e2e-surface.md §2)",
                                             "fields")),
                    S.canon(S.declared_field(named, "an observation spec (e2e-surface.md §2)",
                                             "fields")),
                    "the encoding carries the same fields on every declared shape — a "
                    "widening is a longer layout, not a wider information set "
                    "(e2e-surface.md §2, D-3, shapes.md §8)",
                )
                if encoding == S.TOKENS:
                    for label, spec, expected in (
                        ("no shape named", plain, S.SHAPE_LAYOUTS[default]["vocabulary"]),
                        ("named", named, S.SHAPE_LAYOUTS[shape]["vocabulary"]),
                    ):
                        self.assertEqual(
                            int(S.declared_field(
                                spec, "an observation spec (e2e-surface.md §2)", "vocabulary",
                            )),
                            expected,
                            "the token vocabulary is the shape's — 96 on the two-seat rows, "
                            "where a history slot is one id wide and renames nothing, and 102 "
                            "on the six-seat one, whose six seat ids sit above them "
                            "(card-tokens.md §6, shapes.md §8, seats.md §3): %r with %r "
                            "against %r" % (spec, label, expected),
                        )
        # What the default shape returns is what it declared: 203 dense values, unchanged.
        observation = self.ep("features", "encode")(self.encoder(), self.readout(self.hand(S.SEED_B)))
        self.assertEqual(
            len(observation), S.SHAPE_LAYOUTS[default]["dense"],
            "with no shape named, encode returns the default shape's 203-value observation "
            "it always returned (shapes.md §5, §8): %d values" % (len(observation),),
        )


def _product(values):
    total = 1
    for value in values:
        total *= int(value)
    return total


if __name__ == "__main__":
    unittest.main()
