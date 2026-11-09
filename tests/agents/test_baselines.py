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
    NONEMPTY_MASKS,
    SECOND_BASELINE_SEED,
    AgentsCase,
    chosen_index,
    engine,
    features,
    plain_int,
)

FOLD = "fold"
CHECK_CALL = "check-call"
RAISE = "raise"
FULL = (FOLD, CHECK_CALL, RAISE)

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

    # -- helpers ---------------------------------------------------------

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
