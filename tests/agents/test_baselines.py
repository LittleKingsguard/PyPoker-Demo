"""AGT-9 — `baselines()` and `build_baseline(name, seed)`.

Drives `docs/L2/agents/surface.md` §11-§12, `docs/L3/agents/baselines.md` §2-§9
and `docs/L1/protocol.md` §3: **six** fixed names in order — D-6's three and D-21's
three folders — each with its rule, `params: 0` and its `anchor` flag, the
oracle's declared equity sample count, and one catalogue on two calls; `random`
never leaving the mask it was handed and being keyed by its seed; `always-call`
never folding; `always-call` and `oracle` ignoring their seed because they are
functions of the decision alone; and `oracle` consistent with the pot-odds
inequality re-issued through `engine.equity` at the baseline's own seed and the
count `baselines()` declares (ASM-4, D-6).  D-21's folders are asserted as rules:
`fold-no-pair-or-face` folds exactly the unpaired, face-less pre-flop hands,
`fold-no-pair-or-better` folds exactly a high-card-only best five from the flop
onward, `fold-large-bet` folds exactly when the call exceeds half the declared
starting stack — each only where folding is legal, never raising while check/call
is legal (ASM-31, ASM-32, D-21).  And the readout contract `baselines.md` §1's
fourth property fixes: the eleven facts with `hand_class`'s `None`-or-0-8 shape
(ASM-30), a malformed fact refused as this module's own `policy(readout)`, and an
extra fact ignored (`errors.md` §2-§4).
"""

import unittest

from _agents_support import (
    BASELINE_SEED,
    DEFAULT_SHAPE,
    NONEMPTY_MASKS,
    OTHER_SHAPE,
    SECOND_BASELINE_SEED,
    SEAT_PAST_SIX,
    SIX_MASKS,
    SIX_SEAT_SHAPE,
    UNDECLARED_SEATS,
    AgentsCase,
    chosen_index,
    engine,
    features,
    plain_int,
    shape_decisions,
)

FOLD = "fold"
CHECK_CALL = "check-call"
RAISE = "raise"
FULL = (FOLD, CHECK_CALL, RAISE)

#: The three declared game shapes a baseline may be built for, the default named three
#: ways — by absence, by `None` and by name — and the two other rows by name
#: (`shapes.md` §2, `seats.md` §2, `docs/L2/agents/baselines.md` §2, D-29, D-33).
SEAT_SHAPES = (DEFAULT_SHAPE, OTHER_SHAPE, SIX_SEAT_SHAPE)

#: The six catalogue names in `protocol.md` §3's order, and the three that anchor the
#: rating (D-21, ASM-32): the folders are members and never anchors.
NAMES = (
    "random",
    "always-call",
    "oracle",
    "fold-no-pair-or-face",
    "fold-no-pair-or-better",
    "fold-large-bet",
)
ANCHORS = ("random", "always-call", "oracle")
FOLDERS = (
    "fold-no-pair-or-face",
    "fold-no-pair-or-better",
    "fold-large-bet",
)

#: The sentinel `_readout` uses for "the plausible value of this street".
UNSET = object()


def legal_for(mask):
    """The descriptors for one mask, in the mask's order (`features/surface.md` §8-§9)."""
    feats = features()
    return tuple(feats.decode_action(int(index)) for index in mask)


class BaselinesTest(AgentsCase):
    def test_agt9_1_the_catalogue_is_the_six_in_order_with_their_anchor_flags(self):
        """AGT-9.1 `baselines()` names the six of `protocol.md` §3 in order, each with name, rule, `params: 0` and the `anchor` flag that is true for D-6's three and false for D-21's folders (`baselines.md` §6, §9, `surface.md` §11, ASM-32)."""
        package = self.agents()
        record = package.baselines()
        self.assertEqual(tuple(record), NAMES)
        for name, entry in record.items():
            with self.subTest(baseline=name):
                self.assertEqual(entry["name"], name)
                self.assertIsInstance(entry["rule"], str)
                self.assertTrue(entry["rule"].strip(), "the rule is an empty string")
                self.assertEqual(plain_int(entry["params"], "params"), 0)
                self.assertIn("anchor", entry, "every record carries its anchor flag")
                self.assertIsInstance(
                    entry["anchor"], bool, "the anchor flag is a boolean"
                )
                self.assertEqual(
                    entry["anchor"],
                    name in ANCHORS,
                    "the anchor flag is true for the three baselines of D-6 and false "
                    "for the three folders of D-21, which are members and never anchors "
                    "(protocol.md §3, ASM-32, D-21)",
                )
        self.assertTrue(
            all(record[name]["anchor"] for name in ANCHORS),
            "the three of D-6 stay the anchor (protocol.md §3, ASM-32)",
        )
        self.assertFalse(
            any(record[name]["anchor"] for name in FOLDERS),
            "a folder is a member and a table row and never an anchor (ASM-32, D-21)",
        )
        oracle = record["oracle"]
        self.assertIn("equity_samples", oracle)
        samples = plain_int(oracle["equity_samples"], "equity_samples")
        self.assertGreater(samples, 0)
        for folder in FOLDERS:
            self.assertNotIn(
                "equity_samples",
                record[folder],
                "a folder asks no equity question: it reads the readout's own facts "
                "(baselines.md §7-§8, D-21)",
            )
        self.assertEqual(
            record,
            package.baselines(),
            "two calls must return equal records: the catalogue is plain data a "
            "report's header quotes (surface.md §11)",
        )

    def test_agt9_2_an_unknown_name_is_refused(self):
        """AGT-9.2 a name the six do not include is refused naming it (`surface.md` §12, `baselines.md` §10)."""
        package = self.agents()
        self.assert_refused(
            package.build_baseline,
            "gto",
            BASELINE_SEED,
            entry="build_baseline",
            groups=(("name",), ("gto",)),
            label="an unknown baseline name",
        )

    def test_agt9_3_a_non_integer_seed_is_refused(self):
        """AGT-9.3 a seed that is not an integer is refused naming it (`surface.md` §12, ASM-2)."""
        package = self.agents()
        for seed in ("20271", 2.5, True, None):
            with self.subTest(seed=seed):
                self.assert_refused(
                    package.build_baseline,
                    "random",
                    seed,
                    entry="build_baseline",
                    groups=(("seed",), (str(seed),)),
                    label="a %s seed" % type(seed).__name__,
                )

    def test_agt9_4_random_never_leaves_the_mask(self):
        """AGT-9.4 `random` never returns an index outside the mask it was handed, over 21 invented masks (`baselines.md` §2, `surface.md` §12)."""
        package = self.agents()
        policy = package.build_baseline("random", BASELINE_SEED)
        probes = 0
        for row in self.decisions(3):
            for mask in NONEMPTY_MASKS:
                with self.subTest(hand=row["readout"]["hole"], mask=mask):
                    legal = legal_for(mask)
                    index = chosen_index(policy(row["readout"], legal), legal)
                    self.assertIsNotNone(index)
                    self.assertIn(index, mask)
                    probes += 1
        self.assertGreaterEqual(probes, 20)

    def test_agt9_5_random_is_keyed_by_its_seed(self):
        """AGT-9.5 one seed repeats its choices, two seeds differ over a series of decisions (`baselines.md` §2, `protocol.md` §3-§4)."""
        package = self.agents()
        first = package.build_baseline("random", BASELINE_SEED)
        again = package.build_baseline("random", BASELINE_SEED)
        other = package.build_baseline("random", SECOND_BASELINE_SEED)
        differences = 0
        for row in self.decisions(4):
            for mask in NONEMPTY_MASKS:
                with self.subTest(hand=row["readout"]["hole"], mask=mask):
                    legal = legal_for(mask)
                    mine = first(row["readout"], legal)
                    self.assertEqual(mine, again(row["readout"], legal))
                    theirs = other(row["readout"], legal)
                    self.assertIn(theirs, legal)
                    if theirs != mine:
                        differences += 1
        self.assertGreater(
            differences, 0, "two seeds of `random` answered every decision alike"
        )

    def test_agt9_6_always_call_never_folds(self):
        """AGT-9.6 `always-call` returns 1 where 1 is legal and 2 where it is not, never 0 (`baselines.md` §3, `protocol.md` §3)."""
        package = self.agents()
        policy = package.build_baseline("always-call", BASELINE_SEED)
        realistic = tuple(mask for mask in NONEMPTY_MASKS if mask != (0,))
        probes = 0
        for row in self.decisions(4):
            for mask in realistic:
                with self.subTest(hand=row["readout"]["hole"], mask=mask):
                    legal = legal_for(mask)
                    index = chosen_index(policy(row["readout"], legal), legal)
                    self.assertEqual(index, 1 if 1 in mask else 2)
                    self.assertNotEqual(index, 0)
                    probes += 1
        self.assertGreaterEqual(probes, 20)

    def test_agt9_7_the_oracle_follows_the_pot_odds(self):
        """AGT-9.7 the oracle folds exactly below the pot odds it can re-issue, and never folds or raises where the rule forbids it (`baselines.md` §4-§5, ASM-4)."""
        package = self.agents()
        eng = engine()
        declared = plain_int(
            package.baselines()["oracle"]["equity_samples"], "equity_samples"
        )
        policy = package.build_baseline("oracle", BASELINE_SEED)
        card_sets = self._interior_card_sets(eng, declared)[:2]
        self.assertGreaterEqual(
            len(card_sets),
            2,
            "no two invented decisions had an interior equity, so the case "
            "would prove nothing",
        )
        decisive_fold = 0
        decisive_call = 0
        seen = 0
        for hole, board in card_sets:
            probe = self._readout(hole, board, 1, 1, FULL)
            equity = eng.equity(probe, BASELINE_SEED, declared)
            fold_pairs, call_pairs = self._odds_pairs(equity)
            decisions = []
            for pot, to_call in fold_pairs + call_pairs:
                decisions.append((pot, to_call, FULL))
            for pot, to_call in fold_pairs:
                decisions.append((pot, to_call, (CHECK_CALL, RAISE)))
                decisions.append((pot, to_call, (FOLD, CHECK_CALL)))
            for pot, to_call in call_pairs:
                decisions.append((pot, to_call, (FOLD, CHECK_CALL)))
                decisions.append((pot, to_call, (CHECK_CALL,)))
            for pot, to_call, legal in decisions:
                odds = self._odds(pot, to_call)
                indices = self._indices(legal)
                expected = self._expected(equity, odds, indices)
                readout = self._readout(hole, board, pot, to_call, legal)
                answer = policy(readout, legal)
                index = chosen_index(answer, legal)
                seen += 1
                with self.subTest(cards=(hole, board), pot=pot, to_call=to_call,
                                  legal=legal):
                    self.assertIsNotNone(index, "the oracle answered off the legal set")
                    self.assertEqual(
                        index,
                        expected,
                        "equity %r against odds %r is not the rule's answer"
                        % (equity, odds),
                    )
                    if 1 in indices:
                        self.assertNotEqual(
                            index, 2, "the oracle raised where check/call was legal"
                        )
                    if 0 not in indices:
                        self.assertNotEqual(
                            index, 0, "the oracle folded where folding was not legal"
                        )
                    if equity >= odds:
                        self.assertNotEqual(
                            index, 0, "the oracle folded at or above the pot odds"
                        )
                        if 0 in indices:
                            decisive_call += 1
                    elif 0 in indices:
                        self.assertEqual(index, 0)
                        decisive_fold += 1
        self.assertGreaterEqual(
            decisive_fold, 2, "fewer than two decisions were decisive for folding"
        )
        self.assertGreaterEqual(
            decisive_call, 2, "fewer than two decisions were decisive for calling"
        )
        self.assertGreaterEqual(seen, 8)

    def test_agt9_8_always_call_and_the_oracle_ignore_their_seed(self):
        """AGT-9.8 `always-call` and `oracle` are functions of the decision alone: two seeds give one answer and one legal descriptor on every decision (`surface.md` §12, `baselines.md` §1, §3-§4, D-6)."""
        package = self.agents()
        for name in ("always-call", "oracle"):
            first = package.build_baseline(name, BASELINE_SEED)
            second = package.build_baseline(name, SECOND_BASELINE_SEED)
            for row in self.decisions(3):
                with self.subTest(baseline=name, hand=row["readout"]["hole"]):
                    legal = tuple(row["legal"])
                    mine = first(row["readout"], legal)
                    theirs = second(row["readout"], legal)
                    self.assertIn(mine, legal)
                    self.assertIn(theirs, legal)
                    self.assertEqual(
                        mine,
                        theirs,
                        "%r is a function of the decision alone, so two seeds must "
                        "not answer differently (surface.md §12): its state advances "
                        "nowhere and it has no seed to differ by" % name,
                    )

    def test_agt9_9_a_malformed_readout_is_refused_as_a_policy_readout(self):
        """AGT-9.9 each baseline shape-checks the whole readout and refuses a malformed fact as this module's **own** `policy(readout)`, naming the fact and its value — a `stacks` that is not a pair, a `pot` that is not an integer, a `hole` of one card — with no foreign `TypeError` and no `engine` error escaping (`baselines.md` §1's fourth property, `errors.md` §2-§3, `surface.md` §12)."""
        package = self.agents()
        cases = (
            (
                "random",
                "stacks",
                "a pair of numbers",
                {"stacks": (1, 2, 3)},
                (("stacks",), ("1, 2, 3",)),
            ),
            (
                "always-call",
                "pot",
                "an integer",
                {"pot": 7.5},
                (("pot",), ("7.5",)),
            ),
            (
                "oracle",
                "hole",
                "two cards",
                {"hole": ("As",)},
                (("hole",), ("1",)),
            ),
        )
        for name, fact, wanted, change, groups in cases:
            policy = package.build_baseline(name, BASELINE_SEED)
            readout = dict(
                self._readout(("As", "Kd"), ("2c", "7h", "9s"), 12, 4, FULL), **change
            )
            with self.subTest(baseline=name, fact=fact):
                self.assert_agents_refusal(
                    policy,
                    readout,
                    FULL,
                    entry="policy(readout)",
                    groups=groups,
                    label="%r handed a readout whose %r is not %s"
                    % (name, fact, wanted),
                )

    def test_agt9_10_an_extra_readout_fact_is_ignored(self):
        """AGT-9.10 a valid readout carrying an extra fact is answered and not refused, and the extra fact changes no answer: the eleven facts of `README.md` §7 are inspected, so the shape check is a check on well-formedness and never a whitelist over the readout's keys (`errors.md` §4, `baselines.md` §1's fourth property, `surface.md` §12, ASM-30)."""
        package = self.agents()
        readout = self._readout(("As", "Kd"), ("2c", "7h", "9s"), 12, 4, FULL)
        extra = dict(readout, equity=0.42)
        for name in ("always-call", "random"):
            policy = package.build_baseline(name, BASELINE_SEED)
            with self.subTest(baseline=name):
                answer = policy(extra, FULL)
                self.assertIn(
                    answer,
                    FULL,
                    "%r answered off the legal set it was handed" % (name,),
                )
                self.assertEqual(
                    answer,
                    policy(readout, FULL),
                    "an extra readout fact changed %r's answer, so the shape check "
                    "is a whitelist over the readout's keys rather than a check on "
                    "the eleven facts' well-formedness (errors.md §4)" % (name,),
                )

    def test_agt9_11_fold_no_pair_or_face_folds_the_unpaired_faceless_preflop_hands(self):
        """AGT-9.11 `fold-no-pair-or-face` folds pre-flop exactly when the two hole cards are unpaired **and** neither rank is J, Q, K or A, and check/calls every other pre-flop hand and every post-flop decision (`baselines.md` §7, `folders.md` §2, ASM-31, D-21)."""
        package = self.agents()
        policy = package.build_baseline("fold-no-pair-or-face", BASELINE_SEED)
        preflop = (
            (("7c", "2d"), True, "unpaired and neither card is a face card"),
            (("Tc", "5d"), True, "a ten is not a face card, so this hand folds"),
            (("9c", "4d"), True, "two low unpaired cards"),
            (("As", "7c"), False, "an ace is a face card"),
            (("Kd", "Qh"), False, "two face cards, still no fold"),
            (("Jc", "5d"), False, "a jack is a face card"),
            (("Ac", "Ah"), False, "a pair of aces is paired"),
            (("9c", "9d"), False, "a low pair is paired"),
        )
        for hole, folds, why in preflop:
            with self.subTest(hole=hole):
                readout = self._readout(hole, (), 3, 1, FULL)
                answer = chosen_index(policy(readout, FULL), FULL)
                self.assertEqual(
                    answer,
                    0 if folds else 1,
                    "pre-flop %r: %s, so the rule %s (baselines.md §7, D-21)"
                    % (hole, why, "folds" if folds else "check/calls"),
                )
        for hole in ("7c2d", "As7c", "9c4d"):
            cards = (hole[:2], hole[2:])
            with self.subTest(postflop=cards):
                for board, hand in (
                    (("Kh", "8d", "3s"), 0),
                    (("Kh", "8d", "3s"), 1),
                    (("Kh", "8d", "Ks", "3c"), 3),
                ):
                    with self.subTest(board=board, hand_class=hand):
                        readout = self._readout(cards, board, 12, 2, FULL, hand_class=hand)
                        self.assertEqual(
                            chosen_index(policy(readout, FULL), FULL),
                            1,
                            "the rule is pre-flop only, so from the flop onward it "
                            "check/calls whatever the hand class (baselines.md §7, D-21)",
                        )

    def test_agt9_12_fold_no_pair_or_better_folds_a_high_card_from_the_flop_onward(self):
        """AGT-9.12 `fold-no-pair-or-better` folds exactly when the readout's `hand_class` is `0` — a high card only — and never pre-flop, where the fact is `None`; it check/calls every better class (`baselines.md` §8, `folders.md` §2-§3, ASM-30, ASM-31, D-21)."""
        package = self.agents()
        policy = package.build_baseline("fold-no-pair-or-better", BASELINE_SEED)
        board = ("Kh", "8d", "3s")
        for hand in range(9):
            with self.subTest(hand_class=hand):
                readout = self._readout(("7c", "2d"), board, 12, 2, FULL, hand_class=hand)
                self.assertEqual(
                    chosen_index(policy(readout, FULL), FULL),
                    0 if hand == 0 else 1,
                    "hand_class %d is %s, so the rule %s (baselines.md §8, D-21)"
                    % (
                        hand,
                        "a high card only" if hand == 0 else "better than a high card",
                        "folds" if hand == 0 else "check/calls",
                    ),
                )
        for street, board_cards in (("preflop", ()),):
            with self.subTest(street=street):
                readout = self._readout(("7c", "2d"), board_cards, 3, 1, FULL)
                self.assertIsNone(readout["hand_class"], "the pre-flop fact is None")
                self.assertEqual(
                    chosen_index(policy(readout, FULL), FULL),
                    1,
                    "before the flop there is no five-card hand to be worse than a pair, "
                    "so the rule check/calls (baselines.md §8, ASM-30, D-21)",
                )

    def test_agt9_13_fold_large_bet_folds_above_half_the_declared_starting_stack(self):
        """AGT-9.13 `fold-large-bet` folds exactly when `2 * to_call` exceeds the starting stack `engine.game_config()` declares — more than 10 of 20 — on any street, and check/calls at or below it (`baselines.md` §9, `folders.md` §2, ASM-31, D-21)."""
        package = self.agents()
        eng = engine()
        stack = plain_int(eng.game_config()["starting_stack"], "starting_stack")
        self.assertGreater(stack, 0, "the declared starting stack is a positive number")
        policy = package.build_baseline("fold-large-bet", BASELINE_SEED)
        half = stack // 2
        for street, board, hand in (
            ("preflop", (), None),
            ("flop", ("Kh", "8d", "3s"), 1),
            ("turn", ("Kh", "8d", "3s", "4c"), 2),
            ("river", ("Kh", "8d", "3s", "4c", "9h"), 6),
        ):
            for to_call in (0, 1, 2, half, half + 1, stack):
                with self.subTest(street=street, to_call=to_call):
                    legal = FULL if to_call else FULL[1:]
                    folds = 2 * to_call > stack
                    readout = self._readout(
                        ("7c", "2d"), board, 40 - to_call, to_call, legal, hand_class=hand
                    )
                    self.assertEqual(
                        chosen_index(policy(readout, legal), legal),
                        0 if folds else 1,
                        "at the %s with %d chips to call and a declared stack of %d the "
                        "rule %s (baselines.md §9, ASM-31, D-21)"
                        % (street, to_call, stack, "folds" if folds else "check/calls"),
                    )

    def test_agt9_14_the_folders_are_deterministic_and_seed_independent(self):
        """AGT-9.14 each folder decides identically when built twice at one seed and when built at two different seeds, over real decisions and every non-empty mask — it consumes no randomness (`baselines.md` §1, §7-§9, `folders.md` §2)."""
        package = self.agents()
        rows = self.decisions(3)
        self.assertTrue(rows, "the case drives real decisions")
        for name in FOLDERS:
            with self.subTest(baseline=name):
                once = package.build_baseline(name, BASELINE_SEED)
                twice = package.build_baseline(name, BASELINE_SEED)
                other = package.build_baseline(name, SECOND_BASELINE_SEED)
                for row in rows:
                    for mask in NONEMPTY_MASKS:
                        legal = legal_for(mask)
                        readout = row["readout"]
                        mine = once(readout, legal)
                        self.assertEqual(
                            mine,
                            twice(readout, legal),
                            "two builds at one seed decide one way (%r)" % (name,),
                        )
                        self.assertEqual(
                            mine,
                            other(readout, legal),
                            "%r consumes no randomness, so two seeds decide one way "
                            "(folders.md §2, D-21)" % (name,),
                        )
                        self.assertIn(
                            mine,
                            legal,
                            "%r answered off the legal set it was handed" % (name,),
                        )

    def test_agt9_15_a_folder_folds_only_where_folding_is_legal_and_never_raises_over_a_call(self):
        """AGT-9.15 every folder takes index 0 only where `fold` is legal, index 1 whenever check/call is, and index 2 only where a raise is the sole legal action — never raising while check/call is legal (`baselines.md` §7-§9, ASM-31)."""
        package = self.agents()
        for name in FOLDERS:
            policy = package.build_baseline(name, BASELINE_SEED)
            for row in self.decisions(3):
                for mask in NONEMPTY_MASKS:
                    with self.subTest(baseline=name, mask=mask):
                        legal = legal_for(mask)
                        index = chosen_index(policy(row["readout"], legal), legal)
                        self.assertIsNotNone(index)
                        self.assertIn(index, mask)
                        if 1 in mask:
                            self.assertNotEqual(
                                index,
                                2,
                                "%r raised while check/call was legal, and no folder "
                                "raises (ASM-31, D-21)" % (name,),
                            )
                        if 0 not in mask:
                            self.assertNotEqual(
                                index,
                                0,
                                "%r folded where folding was not legal (ASM-31)"
                                % (name,),
                            )
                        if 1 not in mask and mask != (0,):
                            self.assertEqual(
                                index,
                                2,
                                "a raise-only decision is the only place a folder takes "
                                "index 2 (ASM-31): %r" % (mask,),
                            )

    def test_agt9_16_the_hand_class_fact_is_none_or_an_integer_zero_to_eight(self):
        """AGT-9.16 `hand_class` is `None` or an integer 0-8 and anything else — including a missing fact — is refused naming it, for every baseline of the six (`baselines.md` §1, §7-§9, ASM-30, D-21)."""
        package = self.agents()
        hole, board = ("As", "Kd"), ("2c", "7h", "9s")
        for name in NAMES:
            policy = package.build_baseline(name, BASELINE_SEED)
            for hand in (None, 0, 1, 4, 8):
                with self.subTest(baseline=name, hand_class=hand):
                    readout = self._readout(hole, board, 12, 4, FULL, hand_class=hand)
                    self.assertIn(policy(readout, FULL), FULL)
            for hand in (9, -1, 2.5, True, "3"):
                with self.subTest(baseline=name, refused=hand):
                    readout = self._readout(hole, board, 12, 4, FULL, hand_class=hand)
                    self.assert_agents_refusal(
                        policy,
                        readout,
                        FULL,
                        entry="policy(readout)",
                        groups=(("hand_class",), (repr(hand),)),
                        label="%r handed a hand_class of %r" % (name, hand),
                    )
            missing = self._readout(hole, board, 12, 4, FULL)
            missing.pop("hand_class")
            with self.subTest(baseline=name, missing=True):
                self.assert_agents_refusal(
                    policy,
                    missing,
                    FULL,
                    entry="policy(readout)",
                    groups=(("hand_class",),),
                    label="%r handed a readout with no hand_class" % (name,),
                )

    def test_agt9_17_build_baseline_with_no_shape_is_the_default_shape_everywhere(self):
        """AGT-9.17 `build_baseline(name, seed)` — the two-argument call — takes the same decisions as `build_baseline(name, seed, None)` and as `build_baseline(name, seed, shape="fixed-limit-20")` on every decision of every one of the six, so a call that names no shape is today's call and absence is the default rather than a third behaviour (`docs/L2/agents/baselines.md` §2, `e2e-surface.md` §3.3, `shapes.md` §2-§3, `seats.md` §6, ASM-4, D-13, D-33).

        The three spellings drive the same real decisions of the default shape — three
        hands' first readouts with their own legal descriptors and every non-empty mask over
        the three-index vocabulary — so "unchanged" is asserted on decisions a hand
        produced and not on a fabricated readout (`docs/L2/engine/surface.md` §4,
        `docs/L2/features/surface.md` §8).  The optional third argument is the only
        signature change, and this is what its absence buys: no caller in the tree that
        passes two arguments moves (`e2e-surface.md` §2).
        """
        package = self.agents()
        rows = self.decisions(3)
        self.assertTrue(rows, "the case drives real decisions")
        for name in NAMES:
            with self.subTest(baseline=name):
                absent = package.build_baseline(name, BASELINE_SEED)
                explicit_none = package.build_baseline(name, BASELINE_SEED, None)
                explicit_default = package.build_baseline(
                    name, BASELINE_SEED, shape=DEFAULT_SHAPE
                )
                for row in rows:
                    for mask in NONEMPTY_MASKS:
                        legal = legal_for(mask)
                        answer = absent(row["readout"], legal)
                        self.assertIn(
                            answer,
                            legal,
                            "%r answered off the legal set it was handed (%r)"
                            % (name, mask),
                        )
                        self.assertEqual(
                            answer,
                            explicit_none(row["readout"], legal),
                            "%r's two-argument call is not its `shape=None` call, and the "
                            "absent shape means the default (shapes.md §2, "
                            "docs/L2/agents/baselines.md §2)" % (name,),
                        )
                        self.assertEqual(
                            answer,
                            explicit_default(row["readout"], legal),
                            "%r's two-argument call is not its explicit-default call, so "
                            "absence is not reading as the catalogue's first row "
                            "(shapes.md §3, D-13): %r at %r" % (name, answer, mask),
                        )

    def test_agt9_18_the_folder_reads_its_own_shapes_starting_stack(self):
        """AGT-9.18 `fold-large-bet` built for `six-seat-no-limit-100` reads that shape's **100**-chip starting stack through `engine.game_config` and folds at a `to_call` of 51 while check/calling at 11 — the same rule that folds at 11 and check/calls at 10 on the default shape's 20 — so "more than half the starting stack" is the shape's own and no `20` and no `100` is written down here (`docs/L2/agents/baselines.md` §2-§3, `folders.md` §2, ASM-31, `docs/L1/seats.md` §2, §6, D-21, D-33).

        Both boundaries are computed from the stack `engine.game_config(shape)` declares,
        and the one that matters is the pair 11 / 51: 11 chips is more than half of 20 and
        less than half of 100, so a folder holding a copy of the default shape's 20 would
        fold there and one reading the six-seat row's own stack would not — the two
        readings the shape argument exists to separate (`e2e-surface.md` §3.3, §3.1,
        `folders.md` §2, ASM-31).  The decisions are a real readout of each shape with only
        its `to_call` changed, so the rest of the facts stay the hand's own.
        """
        package = self.agents()
        eng = engine()
        six_stack = plain_int(
            eng.game_config(SIX_SEAT_SHAPE)["starting_stack"], "starting_stack"
        )
        default_stack = plain_int(eng.game_config()["starting_stack"], "starting_stack")
        self.assertEqual(
            six_stack,
            100,
            "the six-seat row's declared starting stack is not 100 chips a seat "
            "(docs/L1/seats.md §2, shapes.md §2): %r" % (six_stack,),
        )
        self.assertEqual(
            default_stack,
            20,
            "the default shape's declared starting stack is not the fixed game's 20, and "
            "this case's two arms are then not one rule (ASM-6, shapes.md §2): %r"
            % (default_stack,),
        )
        self.assertLess(
            default_stack,
            six_stack,
            "the two shapes declare one starting stack, so 11 chips cannot separate the two "
            "readings (docs/L1/seats.md §2, §6): %r against %r"
            % (default_stack, six_stack),
        )
        cases = (
            (SIX_SEAT_SHAPE, six_stack, self._six_seat_readout()),
            (DEFAULT_SHAPE, default_stack, self.decisions(1)[0]["readout"]),
        )
        for shape, stack, readout in cases:
            with self.subTest(shape=shape):
                legal = tuple(readout["legal"])
                self.assertIn(FOLD, legal)
                self.assertIn(
                    CHECK_CALL,
                    legal,
                    "the decision under judgement offers no check/call, so the folder's "
                    "'never raises while check/call is legal' half is untested "
                    "(ASM-31): %r" % (legal,),
                )
                policy = package.build_baseline(
                    "fold-large-bet", BASELINE_SEED, shape=shape
                )
                for to_call in (0, 1, stack // 2, stack // 2 + 1, stack):
                    with self.subTest(shape=shape, to_call=to_call):
                        probe = dict(readout, to_call=to_call)
                        folds = 2 * to_call > stack
                        self.assertEqual(
                            policy(probe, legal),
                            FOLD if folds else CHECK_CALL,
                            "at %d chips to call on the shape %r, whose declared starting "
                            "stack is %d, the rule %s (folders.md §2, ASM-31, "
                            "docs/L2/agents/baselines.md §2)"
                            % (
                                to_call,
                                shape,
                                stack,
                                "folds" if folds else "check/calls",
                            ),
                        )
        # The pair the shape exists to separate: 11 chips folds on 20 and does not on 100.
        six_policy = package.build_baseline(
            "fold-large-bet", BASELINE_SEED, shape=SIX_SEAT_SHAPE
        )
        default_policy = package.build_baseline("fold-large-bet", BASELINE_SEED)
        six_readout = self._six_seat_readout()
        default_readout = self.decisions(1)[0]["readout"]
        self.assertEqual(
            six_policy(dict(six_readout, to_call=11), tuple(six_readout["legal"])),
            CHECK_CALL,
            "the folder folds at 11 chips on the six-seat shape's hundred-chip stack, so it "
            "is reading the default shape's 20 rather than its own shape's starting stack "
            "(docs/L1/seats.md §2, §6, ASM-31): %r"
            % (six_policy(dict(six_readout, to_call=11), tuple(six_readout["legal"])),),
        )
        self.assertEqual(
            six_policy(dict(six_readout, to_call=51), tuple(six_readout["legal"])),
            FOLD,
            "the folder check/calls at 51 chips on the six-seat shape's hundred-chip stack, "
            "so it is not folding above half of that shape's own starting stack "
            "(folders.md §2, ASM-31, D-33)",
        )
        self.assertEqual(
            default_policy(dict(default_readout, to_call=11), tuple(default_readout["legal"])),
            FOLD,
            "the folder no longer folds at 11 chips on the default shape's twenty-chip "
            "stack, so the two-seat behaviour moved (folders.md §2, ASM-31, ASM-6)",
        )
        self.assertEqual(
            default_policy(
                dict(default_readout, to_call=default_stack // 2),
                tuple(default_readout["legal"]),
            ),
            CHECK_CALL,
            "the folder folds at exactly half the default shape's stack, and the rule is "
            "'more than half' (folders.md §2, ASM-31)",
        )

    def test_agt9_19_the_oracle_decides_on_a_six_seat_readout(self):
        """AGT-9.19 `build_baseline("oracle", seed, shape="six-seat-no-limit-100")` constructs and decides on real six-seat readouts, answering a legal descriptor at every decision and one consistent with the pot-odds inequality re-issued through `engine.equity` at the baseline's own seed and the declared sample count — an equity that is **six-way** because `engine.equity` reads the seat count off the readout's `stacks` (`docs/L2/agents/baselines.md` §2-§3, `e2e-surface.md` §3.1, §3.3, `engine/equity.md` §3, `docs/L1/seats.md` §2, ASM-4, D-6, D-33).

        This is the shape's second effect on the six: the oracle asks one question and
        `engine` answers it against the other **five** seats' uniformly random hands, so an
        equity of about a sixth rather than about a half is what the inequality is tested
        against, and the readout's own `stacks` is what tells the engine there are six
        seats (`engine/equity.md` §3, `docs/L1/seats.md` §3).  Both decisive sides are
        driven: the call side on the hands' own odds, and the fold side on a decision whose
        call is worth almost the whole pot, which a six-way equity cannot beat.
        """
        package = self.agents()
        eng = engine()
        declared = plain_int(
            package.baselines()["oracle"]["equity_samples"], "equity_samples"
        )
        self.assertGreater(declared, 0)
        policy = package.build_baseline("oracle", BASELINE_SEED, shape=SIX_SEAT_SHAPE)
        rows = shape_decisions(SIX_SEAT_SHAPE, 6)
        self.assertGreaterEqual(
            len(rows),
            4,
            "the case drives several real six-seat decisions and not one "
            "(docs/L2/engine/surface.md §4): %r" % (len(rows),),
        )
        decisive_call = 0
        for position, row in enumerate(rows):
            readout, legal = dict(row["readout"]), tuple(row["legal"])
            with self.subTest(hand=position):
                self.assertEqual(
                    len(readout["stacks"]),
                    6,
                    "the readout under judgement is not a six-seat one, so its equity is not "
                    "six-way (docs/L1/seats.md §3, engine/equity.md §3): %r"
                    % (len(readout["stacks"]),),
                )
                answer = policy(readout, legal)
                self.assertIn(
                    answer,
                    legal,
                    "the oracle answered a descriptor outside `legal_actions` (surface.md "
                    "§2, D-2): %r at %r" % (answer, legal),
                )
                pot, to_call = int(readout["pot"]), int(readout["to_call"])
                total = pot + to_call
                odds = to_call / total if total else 0.0
                equity = eng.equity(readout, BASELINE_SEED, declared)
                self.assertGreaterEqual(
                    float(equity),
                    0.0,
                    "a six-way equity is not a share of the pot (engine/equity.md §3): %r"
                    % (equity,),
                )
                self.assertLessEqual(float(equity), 1.0)
                if equity >= odds:
                    self.assertNotEqual(
                        answer,
                        FOLD,
                        "the oracle folded at or above the six-way pot odds %r, and the "
                        "rule folds only below them (docs/L2/agents/baselines.md §3, "
                        "ASM-4): equity %r on %r" % (odds, equity, readout),
                    )
                    if FOLD in legal:
                        decisive_call += 1
                elif FOLD in legal:
                    self.assertEqual(
                        answer,
                        FOLD,
                        "the oracle did not fold below the six-way pot odds %r although "
                        "folding is legal (docs/L2/agents/baselines.md §3, ASM-4): equity "
                        "%r on %r" % (odds, equity, readout),
                    )
                else:
                    self.assertNotEqual(
                        answer,
                        FOLD,
                        "the oracle folded where folding is not legal (ASM-31, ASM-4)",
                    )
        self.assertGreaterEqual(
            decisive_call,
            1,
            "no decision of these six-seat hands was decisive for calling, so the case "
            "proves only that the oracle answered (ASM-4): %r" % (decisive_call,),
        )
        # The fold side, on a decision whose call is worth almost the whole pot.
        probe = self._six_seat_readout()
        legal = tuple(probe["legal"])
        expensive = dict(probe, pot=1, to_call=400)
        equity = float(eng.equity(expensive, BASELINE_SEED, declared))
        odds = 400.0 / 401.0
        self.assertLess(
            equity,
            odds,
            "a six-way equity of %r beats odds of %r, so this probe cannot decide the fold "
            "side (engine/equity.md §3, ASM-4)" % (equity, odds),
        )
        self.assertEqual(
            policy(expensive, legal),
            FOLD,
            "the oracle did not fold below the pot odds although folding is legal, so it is "
            "not the pot-odds rule at six seats (docs/L2/agents/baselines.md §3, ASM-4): "
            "equity %r against odds %r" % (equity, odds),
        )

    def test_agt9_20_a_baseline_carries_neither_a_rule_nor_a_utility_on_every_shape(self):
        """AGT-9.20 every one of the six, built for each of the three declared shapes and for the absent one, carries **no** `learning_rule` and **no** `utility`, and each still answers a member of a real six-seat decision's `legal_actions` — a baseline learns nothing and is trained on no reward on any shape, and a shape is not a rule (`e2e-surface.md` §2, §3.3, `docs/L2/agents/baselines.md` §2-§3, `docs/L2/agents/surface.md` §10, `rules.md` §7, `utilities.md` §7, D-6, D-19, D-20, D-21).

        The two attributes are the ones `as_policy` adds and a baseline must not have
        (`docs/L2/agents/surface.md` §10): a table names its population by them, so a
        baseline carrying either would be read as a trained member.  The shape is a
        separate statement and is not one of them — a policy built for a shape may know
        which shape it decides in, and it still learns nothing (`e2e-surface.md` §2,
        `docs/L1/seats.md` §6).
        """
        package = self.agents()
        readout = self._six_seat_readout()
        legal = tuple(readout["legal"])
        for shape in (None,) + tuple(SEAT_SHAPES):
            for name in NAMES:
                with self.subTest(shape=shape, baseline=name):
                    policy = package.build_baseline(name, BASELINE_SEED, shape=shape)
                    self.assertFalse(
                        hasattr(policy, "learning_rule"),
                        "%r built for the shape %r carries a `learning_rule`, and a "
                        "baseline learns under no rule (e2e-surface.md §2, rules.md §7, "
                        "D-19): %r"
                        % (name, shape, getattr(policy, "learning_rule", None)),
                    )
                    self.assertFalse(
                        hasattr(policy, "utility"),
                        "%r built for the shape %r carries a `utility`, and a baseline is "
                        "trained on no reward (e2e-surface.md §2, utilities.md §7, D-20): "
                        "%r" % (name, shape, getattr(policy, "utility", None)),
                    )
                    self.assertIn(
                        policy(readout, legal),
                        legal,
                        "%r built for the shape %r did not answer a member of the six-seat "
                        "decision's `legal_actions`, so a baseline is a function of the "
                        "decision it is handed on every shape (e2e-surface.md §2, "
                        "docs/L2/agents/baselines.md §2, D-33): %r"
                        % (name, shape, legal),
                    )
        catalogue = package.baselines()
        for name, entry in catalogue.items():
            with self.subTest(record=name):
                self.assertNotIn(
                    "learning_rule",
                    entry,
                    "the catalogue record %r carries a `learning_rule`, and a baseline "
                    "learns under none (protocol.md §3, D-6, D-19)" % (name,),
                )
                self.assertNotIn(
                    "utility",
                    entry,
                    "the catalogue record %r carries a `utility`, and a baseline is trained "
                    "on no reward (protocol.md §3, D-6, D-20)" % (name,),
                )

    def test_agt9_21_the_readout_is_six_seats_wide_and_no_other(self):
        """AGT-9.21 a readout whose `stacks` carries six numbers is accepted and one carrying three is refused naming the fact and the value, a seat index of 5 is accepted where 6 is refused, and the eleven facts, the distinct-card rule and the `hand_class` rule are the ones they were — the validators admit the shape's seat count and nothing else (`docs/L2/agents/baselines.md` §2, `docs/L1/seats.md` §3, `docs/L2/agents/surface.md` §1, `errors.md` §2-§3, ASM-30, ASM-44, D-33).

        Six is the seat count the six-seat row's readout carries and three is a length no
        declared shape declares, so the two halves of this case are the two sides of one
        rule: the count is the shape's, read off the fact whose length is it, and the seat
        index ranges over the same count (`docs/L1/seats.md` §3, `engine/equity.md` §3).  A
        malformed fact of a six-seat readout — a card named twice, a `hand_class` of nine —
        is still refused as this module's own `policy(readout)`, which is what says the new
        length did not loosen the rest of the check (`folders.md` §2-§3, ASM-30).
        """
        package = self.agents()
        readout = self._six_seat_readout()
        legal = tuple(readout["legal"])
        self.assertEqual(
            len(tuple(readout["stacks"])),
            6,
            "the readout under judgement is not the six-seat one this case is about "
            "(docs/L1/seats.md §3): %r" % (readout["stacks"],),
        )
        for name in NAMES:
            policy = package.build_baseline(name, BASELINE_SEED)
            with self.subTest(baseline=name, stacks="six"):
                self.assertIn(
                    policy(readout, legal),
                    legal,
                    "%r refused or answered off a six-seat readout, so no baseline can be "
                    "seated at the six-seat table (docs/L2/agents/baselines.md §2, "
                    "docs/L1/seats.md §3, D-33): %r" % (name, legal),
                )
            with self.subTest(baseline=name, stacks="five"):
                self.assertIn(
                    policy(dict(readout, seat=(5, False)), legal),
                    legal,
                    "%r refused the acting seat five of a six-seat decision "
                    "(docs/L1/seats.md §3, ASM-44): %r" % (name, readout["seat"]),
                )
            with self.subTest(baseline=name, stacks="three"):
                self.assert_agents_refusal(
                    policy,
                    dict(readout, stacks=(1, 2, 3)),
                    legal,
                    entry="policy(readout)",
                    groups=(("stacks",), ("1, 2, 3",)),
                    label="%r handed a readout whose `stacks` is %d long, a seat count no "
                    "declared shape carries" % (name, UNDECLARED_SEATS),
                )
            with self.subTest(baseline=name, seat="past the seats"):
                self.assert_agents_refusal(
                    policy,
                    dict(readout, seat=(SEAT_PAST_SIX, False)),
                    legal,
                    entry="policy(readout)",
                    groups=(("seat",), (str(SEAT_PAST_SIX),)),
                    label="%r handed a seat index past the six seats `stacks` declares"
                    % (name,),
                )
            with self.subTest(baseline=name, cards="distinct"):
                self.assert_agents_refusal(
                    policy,
                    dict(readout, hole=(readout["hole"][0], readout["hole"][0])),
                    legal,
                    entry="policy(readout)",
                    groups=(("distinct",),),
                    label="%r handed a six-seat readout naming one card twice" % (name,),
                )
            with self.subTest(baseline=name, hand_class="nine"):
                self.assert_agents_refusal(
                    policy,
                    dict(readout, hand_class=9),
                    legal,
                    entry="policy(readout)",
                    groups=(("hand_class",),),
                    label="%r handed a six-seat readout with a hand_class of 9" % (name,),
                )
            with self.subTest(baseline=name, missing="hand_class"):
                missing = dict(readout)
                missing.pop("hand_class")
                self.assert_agents_refusal(
                    policy,
                    missing,
                    legal,
                    entry="policy(readout)",
                    groups=(("hand_class",),),
                    label="%r handed a six-seat readout with no hand_class" % (name,),
                )

    def test_agt9_22_random_is_keyed_by_its_seed_at_six_seats(self):
        """AGT-9.22 `random` built for the six-seat shape never returns an index outside the mask it was handed, one seed repeats its choices and two seeds differ, over real six-seat decisions and every non-empty mask over the six-index vocabulary — its draw is keyed by the decision, and `(stacks, limit, …)` is the six-fact spelling at six seats (`docs/L2/agents/baselines.md` §2, `protocol.md` §3-§4, `docs/L1/seats.md` §3, ASM-4, D-33).

        The key is the decision's canonical spelling, and a six-seat decision's includes six
        `stacks` entries and six legal indices instead of two and three: the draw has to
        keep working there because a baseline that could not decide at six seats could not
        be seated at the six-seat table the pool is drawn for (`docs/L1/seats.md` §4,
        `docs/L2/agents/baselines.md` §2).  The masks are the shape's own six indices, one-,
        two- and six-member (`docs/L1/sizing.md` §3, ASM-37).
        """
        package = self.agents()
        first = package.build_baseline("random", BASELINE_SEED, shape=SIX_SEAT_SHAPE)
        again = package.build_baseline("random", BASELINE_SEED, shape=SIX_SEAT_SHAPE)
        other = package.build_baseline(
            "random", SECOND_BASELINE_SEED, shape=SIX_SEAT_SHAPE
        )
        rows = shape_decisions(SIX_SEAT_SHAPE, 4)
        self.assertGreaterEqual(
            len(rows), 3, "the case drives several real six-seat decisions: %r" % (len(rows),)
        )
        probes = 0
        differences = 0
        for row in rows:
            own = tuple(row["mask"])
            for mask in SIX_MASKS:
                if not set(mask) <= set(own):
                    continue
                legal = tuple(
                    descriptor
                    for descriptor, index in zip(row["legal"], own)
                    if index in mask
                )
                self.assertTrue(
                    legal,
                    "the sub-mask %r this case built is empty, so it hands no decision "
                    "(features/shapes.md §4): %r" % (mask, own),
                )
                with self.subTest(hand=row["readout"]["hole"], mask=mask):
                    self.assertEqual(
                        tuple(int(index) for index in features().legal_indices(legal)),
                        tuple(mask),
                        "the descriptors this case hands the policy are not the mask's own "
                        "indices in that shape's vocabulary (features/shapes.md §4, "
                        "docs/L2/features/surface.md §8): %r against %r"
                        % (tuple(features().legal_indices(legal)), mask),
                    )
                    mine = first(row["readout"], legal)
                    self.assertIn(
                        mine,
                        legal,
                        "random answered off the legal set it was handed at six seats "
                        "(baselines.md §2): %r at %r" % (mine, legal),
                    )
                    self.assertEqual(
                        mine,
                        again(row["readout"], legal),
                        "one seed of `random` answered a six-seat decision twice and chose "
                        "differently, so its draw is not keyed by the decision "
                        "(protocol.md §4, surface.md §1)",
                    )
                    theirs = other(row["readout"], legal)
                    self.assertIn(theirs, legal)
                    if theirs != mine:
                        differences += 1
                    probes += 1
        self.assertGreaterEqual(probes, 20, "%d probes" % (probes,))
        self.assertGreater(
            differences,
            0,
            "two seeds of `random` answered every six-seat decision alike, so the seed did "
            "not reach the six-seat key (protocol.md §3, baselines.md §2)",
        )

    # -- helpers ---------------------------------------------------------

    def _six_seat_readout(self):
        """One real six-seat readout, from the first decision of a hand `engine` dealt.

        The facts are the hand's own — six `stacks` entries, a seat index in `0..5`, the
        six legal descriptors — and only a case that asks about one fact substitutes it, so
        no readout here is fabricated (`docs/L2/engine/surface.md` §4, `docs/L1/seats.md`
        §3, `docs/L2/features/surface.md` §8).
        """
        rows = shape_decisions(SIX_SEAT_SHAPE, 1)
        self.assertTrue(rows, "no hand was dealt on %r" % (SIX_SEAT_SHAPE,))
        return dict(rows[0]["readout"])

    @staticmethod
    def _readout(hole, board, pot, to_call, legal, hand_class=UNSET, street=None):
        """One literal readout mapping: the eleven facts as plain data (`e2e-surface.md` §2).

        `hand_class` defaults to the plausible value for the street it builds -- `None`
        before the flop, and a class from the flop on -- and a case that needs another
        one, `None` included, passes it (`folders.md` §3, ASM-30).
        """
        if street is None:
            street = "flop" if board else "preflop"
        if hand_class is UNSET:
            hand_class = 0 if board else None
        return {
            "street": street,
            "seat": (0, True),
            "hole": tuple(hole),
            "board": tuple(board),
            "stacks": (19, 18),
            "pot": int(pot),
            "to_call": int(to_call),
            "limit": (2, 0),
            "history": (),
            "legal": tuple(legal),
            "hand_class": hand_class,
        }

    @staticmethod
    def _odds(pot, to_call):
        """`to_call / (pot + to_call)`, or 0.0 on a zero denominator (`baselines.md` §4)."""
        total = pot + to_call
        return to_call / total if total else 0.0

    @staticmethod
    def _indices(legal):
        feats = features()
        return tuple(int(index) for index in feats.legal_indices(legal))

    @classmethod
    def _expected(cls, equity, odds, indices):
        """The pot-odds rule's index (`baselines.md` §4)."""
        if equity >= odds:
            return 1 if 1 in indices else 2
        return 0 if 0 in indices else 1

    @staticmethod
    def _odds_pairs(equity):
        """Two (pot, to_call) pairs decisive on each side of the inequality."""
        fold_side = []
        call_side = []
        for pot in range(1, 41):
            for to_call in range(1, 401):
                odds = to_call / (pot + to_call)
                if len(fold_side) < 2 and odds > equity + 1e-9:
                    fold_side.append((pot, to_call))
                if len(call_side) < 2 and odds < equity - 1e-9:
                    call_side.append((pot, to_call))
                if len(fold_side) == 2 and len(call_side) == 2:
                    return fold_side, call_side
        raise AssertionError(
            "equity %r leaves no decisive pot-odds pair on one side" % equity
        )

    @classmethod
    def _interior_card_sets(cls, eng, samples):
        """Invented card decisions from real cards whose equity is strictly interior."""
        pool = []
        for hand_seed in (9611, 9617, 9623, 9629, 9631, 9637):
            readout = eng.readout(eng.new_hand(hand_seed))
            for card in readout["hole"]:
                if card not in pool:
                    pool.append(card)
            if len(pool) >= 8:
                break
        if len(pool) < 8:
            raise AssertionError(
                "the engine dealt fewer than eight distinct cards: %r" % (pool,)
            )
        candidates = [
            ((pool[0], pool[1]), ()),
            ((pool[2], pool[3]), ()),
            ((pool[4], pool[5]), ()),
            ((pool[0], pool[1]), (pool[4], pool[5], pool[6])),
            ((pool[2], pool[3]), (pool[0], pool[5], pool[7])),
        ]
        interior = []
        for hole, board in candidates:
            cards = tuple(hole) + tuple(board)
            if len(set(cards)) != len(cards):
                continue
            equity = eng.equity(cls._readout(hole, board, 1, 1, FULL),
                                BASELINE_SEED, samples)
            if 0.0 < equity < 1.0:
                interior.append((hole, board))
        return interior


if __name__ == "__main__":
    unittest.main()
