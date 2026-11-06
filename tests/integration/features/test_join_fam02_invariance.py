"""FAM-2 — the representation axis is declared, and every declared fact reaches it.

`docs/L2/features/surface.md` §2, §3, §5–§9, `docs/L2/features/encodings.md` §1–§4,
`docs/L1/battery.md` §3 FAM-2, D-2 and D-3.  The ladder changes how the agent
*represents* what it knows and never what it knows, so this battery asserts the two
declarations, their identity, the vocabulary's three indices, the mask, the decode
round trip — and that each of the nine carried facts really reaches the observation,
one fact at a time and layout-free (``docs/L1/battery.md`` §2: a case asserts outcomes,
never an internal shape).

Every readout here is `engine.readout`'s own, at a real decision: a first decision (an
empty history and no board), a flop, a turn and a river, a decision with nothing to
call, and the last readout of a hand that has ended (`docs/L2/engine/environment.md`
§1–§2, D-13).
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


class FAM2Invariance(S.JoinCase):
    """The D-2 and D-3 invariants, held across both encodings at the module join."""

    def test_fam2_1_both_encodings_are_declared_with_their_kind(self):
        """FAM-2.1 each encoding declares its representation family, kind (encodings §1)."""
        kinds = {}
        for name in S.ENCODING_NAMES:
            spec = self.spec(name)
            kind = str(spec["kind"])
            kinds[name] = kind
            self.assertEqual(
                kind,
                S.KINDS[name],
                "%r is the %r representation family, and its spec must declare that "
                "kind (encodings.md §1, surface.md §5); got %r"
                % (name, S.KINDS[name], spec["kind"]),
            )
            self.assertTrue(
                S.is_plain(spec["kind"]),
                "a spec's kind is plain data (surface.md §1, §5); got %r" % (spec["kind"],),
            )
        self.assertNotEqual(
            kinds["flat-numeric"],
            kinds["card-tokens"],
            "the two encodings are two representation families, so their kinds differ "
            "(encodings.md §1): %r" % (kinds,),
        )

    def test_fam2_2_both_encodings_carry_the_same_nine_readout_facts(self):
        """FAM-2.2 fields is identical for both encodings and never holds legal (§2)."""
        carried = {}
        for name in S.ENCODING_NAMES:
            spec = self.spec(name)
            fields = tuple(spec["fields"])
            carried[name] = fields
            self.assertEqual(
                set(fields),
                set(S.CARRIED_FACTS),
                "the encoding carries the readout's ten facts less `legal` "
                "(encodings.md §2); %r carries %r" % (name, list(fields)),
            )
            self.assertNotIn(
                "legal",
                set(fields),
                "`legal` reaches a policy beside the observation and is never carried "
                "inside it (encodings.md §2, surface.md §6); %r carries it" % (name,),
            )
            self.assertEqual(
                len(fields),
                len(S.CARRIED_FACTS),
                "a fact is carried once (encodings.md §2); %r carries %r"
                % (name, list(fields)),
            )
        self.assertEqual(
            carried["flat-numeric"],
            carried["card-tokens"],
            "the fact set is what the ladder holds constant and only the spelling "
            "varies, so both encodings declare the same fields in one order "
            "(encodings.md §2, ladder.md §4): %r against %r"
            % (list(carried["flat-numeric"]), list(carried["card-tokens"])),
        )

    def test_fam2_3_each_spec_names_its_own_representation(self):
        """FAM-2.3 a spec's representation is the encoding's own name (surface §5)."""
        for name in S.ENCODING_NAMES:
            with self.subTest(encoding=name):
                spec = self.spec(name)
                self.assertEqual(
                    str(spec["representation"]),
                    name,
                    "the spec's representation is the encoding's own name "
                    "(surface.md §5); the spec of %r declares %r"
                    % (name, spec["representation"]),
                )
                self.assertIn(
                    S.token(spec["representation"]),
                    S.token(name),
                    "the representation the spec declares must read as the encoding it "
                    "belongs to (surface.md §5): %r against %r"
                    % (spec["representation"], name),
                )

    def test_fam2_4_shape_dtype_and_vocabulary_are_declared(self):
        """FAM-2.4 a spec declares one observation's shape, dtype and vocabulary (§5)."""
        for name in S.ENCODING_NAMES:
            with self.subTest(encoding=name):
                spec = self.spec(name)
                self.assertEqual(
                    self.declared_shape(spec),
                    S.SHAPES[name],
                    "%r declares the one observation's shape (surface.md §5, "
                    "encodings.md §3–§4): %r" % (name, spec["shape"]),
                )
                self.assertEqual(
                    str(spec["dtype"]),
                    S.DTYPES[name],
                    "%r declares one observation's element type (surface.md §5, "
                    "encodings.md §3–§4): %r" % (name, spec["dtype"]),
                )
                self.assertTrue(
                    S.is_plain(spec["dtype"]),
                    "the dtype is plain data numpy.dtype accepts, so a report can quote "
                    "it (surface.md §5); got %r" % (spec["dtype"],),
                )
                declared = spec["vocabulary"]
                if S.VOCABULARIES[name] is None:
                    self.assertIsNone(
                        declared,
                        "the dense encoding has no embedding table, so its vocabulary "
                        "is null (surface.md §5, encodings.md §3): %r" % (declared,),
                    )
                else:
                    self.assertTrue(
                        S.is_count(declared),
                        "the token encoding declares the id cardinality a learner sizes "
                        "an embedding table from (surface.md §5); got %r" % (declared,),
                    )
                    self.assertEqual(
                        int(declared),
                        S.VOCABULARIES[name],
                        "the token vocabulary is the one this encoding declares "
                        "(surface.md §5, encodings.md §4): %r" % (declared,),
                    )
                self.assertTrue(
                    S.is_plain(spec["vocabulary"]),
                    "the vocabulary is plain data a learner is sized from, and null for "
                    "the dense encoding (surface.md §1, §5): %r" % (spec["vocabulary"],),
                )

    def test_fam2_5_the_real_observation_matches_the_declaration_at_every_street(self):
        """FAM-2.5 the real observation has the declared shape and dtype at 0/3/4/5 cards."""
        samples = self.samples()
        lengths = set(len(tuple(readout["board"])) for readout in samples)
        self.assertEqual(
            lengths,
            {0, 3, 4, 5},
            "a real game deals a board of 0, 3, 4 and 5 cards, and the battery sampled "
            "%r (engine/environment.md §1): the observation is declared at every one of "
            "them (surface.md §6)" % (sorted(lengths),),
        )
        self.assertTrue(
            any(not readout["history"] for readout in samples),
            "the battery sampled no decision with an empty history (engine/"
            "environment.md §2)",
        )
        self.assertTrue(
            any(readout["history"] for readout in samples),
            "the battery sampled no decision with a history behind it (engine/"
            "environment.md §2)",
        )
        for name in S.ENCODING_NAMES:
            spec = self.spec(name)
            encoder = self.encoder(name)
            for readout in samples:
                with self.subTest(
                    encoding=name,
                    street=readout["street"],
                    board=len(tuple(readout["board"])),
                    history=len(readout["history"]),
                ):
                    self.assert_observation(name, spec, self.encode(encoder, readout))

    def test_fam2_6_the_catalogue_is_the_spec_of_each_built_encoder(self):
        """FAM-2.6 encodings()[name] equals observation_spec(build_encoder(name)) (§3)."""
        declared = self.encodings()
        for name in S.ENCODING_NAMES:
            with self.subTest(encoding=name):
                self.assertEqual(
                    S.canonical(declared[name]),
                    S.canonical(self.observation_spec(self.build_encoder(name))),
                    "the catalogue's entry for %r is the record its encoder declares, "
                    "because a rung names an encoding and a caller builds it "
                    "(surface.md §3, §4): %r against %r"
                    % (name, declared[name], self.observation_spec(self.build_encoder(name))),
                )

    def test_fam2_7_the_action_vocabulary_is_exactly_the_three_indices(self):
        """FAM-2.7 action_space is the fixed 0/1/2 vocabulary and no other integer (§7)."""
        space = self.action_space()
        self.assertEqual(
            set(space),
            set(S.ACTION_INDICES),
            "the vocabulary is keyed by the three indices 0, 1 and 2 (surface.md §7): %r"
            % (sorted(str(key) for key in space),),
        )
        found = set(S.integers_in(space))
        self.assertEqual(
            found,
            set(S.ACTION_INDICES),
            "the three indices are the only integers anywhere in the record — a stray "
            "bet size or chip count would make the vocabulary larger than the game's, "
            "because the invariance family reads it as the set of integers it finds "
            "(surface.md §7, battery.md §3 FAM-2.9): %r" % (sorted(found),),
        )
        for index in S.ACTION_INDICES:
            with self.subTest(index=index):
                declared = S.ACTION_NAMES[index]
                names = [S.token(text) for text in S.strings_in(space[index])]
                self.assertIn(
                    S.token(declared),
                    names,
                    "index %d is %r, and its record carries that name (surface.md §2, "
                    "§7): %r" % (index, declared, space[index]),
                )
                self.assertEqual(
                    self.decode_action(index),
                    declared,
                    "index %d decodes to the descriptor the two modules share "
                    "(surface.md §2, §9): %r" % (index, self.decode_action(index)),
                )

    def test_fam2_8_a_decisions_descriptors_and_indices_correspond_one_to_one(self):
        """FAM-2.8 the mask is position-aligned, distinct and ascending (surface §2, §8)."""
        for seed, kind in ((S.SEED_MASK, S.CHECK_CALL), (S.SEED_DECODE, S.RAISE)):
            steps, _hand = self.walk(seed, kind)
            self.assertGreaterEqual(
                len(steps), 2, "the case needs more than one decision at seed %r" % (seed,)
            )
            for position, step in enumerate(steps):
                legal = S.descriptors(step.legal, "a decision's legal descriptors")
                indices = [int(index) for index in self.legal_indices(step.legal)]
                with self.subTest(seed=seed, decision=position, indices=indices):
                    self.assertEqual(
                        len(indices),
                        len(legal),
                        "one index per legal descriptor (surface.md §8): %r descriptors, "
                        "%r indices" % (len(legal), len(indices)),
                    )
                    self.assertEqual(
                        len(set(indices)),
                        len(indices),
                        "a decision's indices are distinct, because a descriptor appears "
                        "once (surface.md §2, §8): %r" % (indices,),
                    )
                    self.assertEqual(
                        indices,
                        sorted(indices),
                        "the indices ascend, because the engine hands a decision its "
                        "descriptors in the vocabulary's order (surface.md §2, §8): %r"
                        % (indices,),
                    )
                    self.assertTrue(
                        set(indices) <= set(S.ACTION_INDICES),
                        "every legal index is one of the three vocabulary indices "
                        "(surface.md §2, §8): %r" % (indices,),
                    )
                    for slot, index in enumerate(indices):
                        self.assertEqual(
                            S.token(self.decode_action(index)),
                            S.token(legal[slot]),
                            "the %d-th index is the index of the %d-th descriptor, so "
                            "the round trip returns that same action (surface.md §8, "
                            "§9): index %r decoded to %r against %r"
                            % (slot, slot, index, self.decode_action(index), legal[slot]),
                        )
                    self.assertEqual(
                        [int(index) for index in self.legal_indices(step.readout["legal"])],
                        indices,
                        "the engine makes the readout's legal fact the same sequence "
                        "legal_actions returns, so the mask is the same from either "
                        "(engine/surface.md §6, surface.md §8): %r against %r"
                        % (list(step.readout["legal"]), list(step.legal)),
                    )

    def test_fam2_9_a_decoded_descriptor_is_accepted_at_its_own_decision(self):
        """FAM-2.9 decode_action's descriptor is one apply_action accepts (§2, §9)."""
        steps, _hand = self.walk(S.SEED_ENCODE, S.CHECK_CALL)
        self.assertGreaterEqual(len(steps), 3, "the case needs several decisions")
        for position, step in enumerate(steps):
            for index in [int(value) for value in self.legal_indices(step.legal)]:
                with self.subTest(decision=position, index=index):
                    descriptor = self.decode_action(index)
                    advanced = self.apply_action(step.hand, descriptor)
                    self.assertIsNotNone(
                        advanced,
                        "index %r is legal at decision %d, so its descriptor is one the "
                        "engine accepts there (surface.md §2, §9): %r"
                        % (index, position, descriptor),
                    )
                    self.assertIsInstance(
                        self.is_terminal(advanced),
                        bool,
                        "the value apply_action returned for %r is a hand: is_terminal "
                        "answers for it (engine/surface.md §7)" % (descriptor,),
                    )

    def test_fam2_10_every_carried_fact_reaches_the_observation(self):
        """FAM-2.10 one carried fact changed changes the observation (encodings §2)."""
        samples = self.samples()
        pool = S.card_pool(samples)
        by_street = self.by_street()
        self.assertEqual(
            set(by_street),
            {"preflop", "flop", "turn", "river"},
            "the battery samples a decision on each of the four streets "
            "(engine/environment.md §1): %r" % (sorted(by_street),),
        )
        for name in S.ENCODING_NAMES:
            encoder = self.encoder(name)
            for street, readout in sorted(by_street.items()):
                changes = S.far_end_changes(readout, pool, samples)
                baseline = self.encode(encoder, readout)
                for fact in S.CARRIED_FACTS:
                    with self.subTest(encoding=name, street=street, fact=fact):
                        changed = dict(readout)
                        changed[fact] = changes[fact]
                        self.assertFalse(
                            S.same_observation(baseline, self.encode(encoder, changed)),
                            "%r carries %r, so a readout whose %r moved to the far end of "
                            "its range must encode differently (encodings.md §2, §3–§4): "
                            "the observation did not change, from %r to %r"
                            % (name, fact, fact, readout[fact], changes[fact]),
                        )

    def test_fam2_11_the_uncarried_legal_fact_and_an_invented_key_are_ignored(self):
        """FAM-2.11 a key the encoding does not carry is ignored, not refused (§6)."""
        by_street = self.by_street()
        readouts = [by_street[street] for street in ("preflop", "flop", "river")]
        for name in S.ENCODING_NAMES:
            encoder = self.encoder(name)
            for position, readout in enumerate(readouts):
                baseline = self.encode(encoder, readout)
                uncarried = {
                    "legal dropped": dict(readout, legal=()),
                    "legal replaced": dict(readout, legal=(S.UNDECLARED_DESCRIPTOR,)),
                    "legal kept": dict(readout),
                    "invented key added": dict(readout, **{S.INVENTED_KEY: "calm"}),
                }
                for what, changed in uncarried.items():
                    with self.subTest(encoding=name, decision=position, case=what):
                        self.assertTrue(
                            S.same_observation(baseline, self.encode(encoder, changed)),
                            "`legal` is the readout's tenth fact and is not carried, so "
                            "changing it changes no observation, and a key the encoding "
                            "does not carry is ignored rather than refused (surface.md "
                            "§6, encodings.md §2): %r changed the observation of %r"
                            % (what, name),
                        )

    def test_fam2_12_every_emitted_token_lies_inside_the_declared_vocabulary(self):
        """FAM-2.12 token ids lie in [0, vocabulary) and the dense vector is finite (§4)."""
        samples = self.samples()
        tokens = self.spec("card-tokens")
        vocabulary = int(tokens["vocabulary"])
        flat = self.spec("flat-numeric")
        self.assertIsNone(
            flat["vocabulary"],
            "the dense encoding has no embedding table, so its vocabulary is null "
            "(surface.md §5): %r" % (flat["vocabulary"],),
        )
        token_encoder = self.encoder("card-tokens")
        flat_encoder = self.encoder("flat-numeric")
        for readout in samples:
            with self.subTest(street=readout["street"], history=len(readout["history"])):
                ids = [int(value) for value in self.encode(token_encoder, readout)]
                self.assertEqual(
                    len(ids),
                    self.declared_shape(tokens)[0],
                    "one token per carried occurrence is the declared shape "
                    "(encodings.md §4): %r tokens" % (len(ids),),
                )
                for position, ident in enumerate(ids):
                    self.assertGreaterEqual(
                        ident,
                        0,
                        "a token id is never negative, because a learner embeds it "
                        "(encodings.md §4): slot %d holds %r" % (position, ident),
                    )
                    self.assertLess(
                        ident,
                        vocabulary,
                        "every emitted id lies inside the declared vocabulary, because "
                        "agents sizes an embedding table from it and an id outside the "
                        "table would break the learner (surface.md §5, encodings.md "
                        "§4): slot %d holds %r, vocabulary %r"
                        % (position, ident, vocabulary),
                    )
                values = self.encode(flat_encoder, readout)
                self.assertTrue(
                    S.all_finite(values),
                    "the dense encoding divides and buckets nothing, so every element "
                    "is a finite number (encodings.md §3): %r"
                    % ([float(value) for value in values],),
                )

    def test_fam2_19_an_out_of_order_argument_keeps_its_own_order(self):
        """FAM-2.19 legal_indices is position-aligned and never sorts (§8)."""
        # surface.md §2 and §7 fix the three indices — fold 0, check-call 1, raise 2 —
        # and the descriptors are the three strings both modules share, so the expected
        # indices below are the vocabulary's own and not a shape this battery read out
        # of the module under test.
        vocabulary = {name: index for index, name in enumerate(S.ACTION_NAMES)}
        self.assertEqual(
            vocabulary,
            {"fold": 0, "check-call": 1, "raise": 2},
            "the vocabulary is the game's and fixed by surface.md §2 and §7: fold 0, "
            "check-call 1, raise 2",
        )

        # Two invented sequences, and one real decision's own descriptors reversed, so
        # the out-of-order argument is both spelled from the contract and driven with
        # descriptors the engine really handed out (docs/L1/e2e-surface.md §2, D-13).
        steps, _hand = self.walk(S.SEED_MASK, S.CHECK_CALL)
        shortest = min(steps, key=lambda step: len(step.legal))
        self.assertGreaterEqual(
            len(shortest.legal),
            2,
            "the case needs a decision with more than one legal action; the walk's "
            "shortest decision held %r" % (list(shortest.legal),),
        )
        real = S.descriptors(shortest.legal, "a decision's legal descriptors")
        arguments = [
            ("raise", "fold"),
            ("raise", "check-call", "fold"),
            tuple(reversed(real)),
        ]

        for argument in arguments:
            expected = [
                vocabulary[S.descriptor_kind(descriptor)] for descriptor in argument
            ]
            self.assertNotEqual(
                expected,
                sorted(expected),
                "every argument this case drives is deliberately out of the engine's "
                "order, which is the vocabulary's (surface.md §2, §8): %r reads as the "
                "ascending %r" % (argument, expected),
            )
            with self.subTest(argument=argument):
                returned = [int(index) for index in self.legal_indices(argument)]
                self.assertEqual(
                    returned,
                    expected,
                    "the i-th index is the vocabulary index of the i-th descriptor, so an "
                    "out-of-order argument keeps its own order and is never sorted "
                    "(surface.md §8): %r read as %r, not %r"
                    % (argument, returned, expected),
                )
                self.assertEqual(
                    len(returned),
                    len(argument),
                    "one index per descriptor, because the battery reads the mask "
                    "positionally (surface.md §8, tests/e2e/_surface.py chosen_index): "
                    "%r descriptors, %r indices" % (len(argument), len(returned)),
                )
                self.assertEqual(
                    len(set(returned)),
                    len(returned),
                    "the i-th index is the i-th descriptor's, so two descriptors never "
                    "share one index in one argument (surface.md §8): %r" % (returned,),
                )
                self.assertNotEqual(
                    returned,
                    sorted(returned),
                    "an argument out of the engine's order is never sorted back into "
                    "it, because the alignment is what the battery reads (surface.md "
                    "§8): %r came back as %r" % (argument, returned),
                )
                for position, descriptor in enumerate(argument):
                    decoded = self.decode_action(returned[position])
                    self.assertEqual(
                        S.token(decoded),
                        S.token(descriptor),
                        "index %r is the index of the descriptor in position %d, so the "
                        "round trip returns that same action (surface.md §2, §8, §9): "
                        "%r against %r" % (returned[position], position, decoded, descriptor),
                    )


if __name__ == "__main__":
    unittest.main()
