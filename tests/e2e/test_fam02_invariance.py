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
        """FAM-2.1 engine.game_config is deterministic and is ASM-6's fixed game (D-2)."""
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

    def test_fam2_2_the_dealt_game_has_the_fixed_parameters(self):
        """FAM-2.2 a first decision shows blinds 1/2 and stacks 20 (ASM-6, D-2)."""
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
        """FAM-2.9 features.action_space is the fixed 0/1/2 vocabulary (D-2)."""
        space = self.ep("features", "action_space")()
        vocabulary = S.action_vocabulary(space)
        self.assertEqual(
            vocabulary,
            {0, 1, 2},
            "the vocabulary is the game's three indices — fold 0, check/call 1, raise 2 — "
            "however the container keys them, a sequence or a mapping keyed by name or by "
            "the indices themselves (e2e-surface §2): %r" % (space,),
        )

    def test_fam2_10_decode_action_round_trips_into_the_engine(self):
        """FAM-2.10 decode_action gives a descriptor apply_action accepts (D-2)."""
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
        """FAM-2.11 the legal descriptors and the legal indices correspond one to one."""
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


def _product(values):
    total = 1
    for value in values:
        total *= int(value)
    return total


if __name__ == "__main__":
    unittest.main()
