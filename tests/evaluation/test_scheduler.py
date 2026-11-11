"""EVL-3 — the scheduler: `match` and `policy_from`.

Drives `docs/L3/evaluation/scheduler.md` §1-§8, `docs/L2/evaluation/surface.md` §9,
§12, `docs/L1/league.md` §3 and `docs/L3/evaluation/seats.md` §2: the six seed
derivations of `scheduler.md` §3 and `seats.md` §2 (recomputed here from the
tag/`\\x1f`/SHA-256 payload, so `seed + i`, `random.Random(seed)` or a counter is red), seat alternation with `seat_split`'s two counts summing to `hands`, the hand's
class from the sign of its net delta with the two directions exact mirrors, the mean
chip delta per hand negating exactly, `params` position-aligned with `members` and
`unlabelled` naming an opaque policy's unmeasured zero, and the two things
`policy_from` reads from a checkpoint's own container -- the seed and the encoding
name -- so a loaded member chooses the action its learner chose on the same readout
(`protocol.md` §5's loss-free boundary).

The refusals are `scheduler.md` §6's: a hand count or a seed that is not an integer, a
side that is neither callable nor a member record nor a baseline name, two sides
carrying one id, a path that names no readable file or no readable zip, a container
recording no seed or no encoding name, and an encoding name
`features.build_encoder` refuses -- the name is checked by *building* it, and no
catalogue is read (`scheduler.md` §5.1). An illegal descriptor is `engine`'s refusal
and is neither caught nor repaired here (D-2), so that case asserts a refusal and not
this module's class.
"""

import os
import unittest

from _evaluation_support import (
    ALT_HANDS,
    BOOTSTRAP_TAG,
    CELL_TAG,
    DEFAULT_RULE,
    HAND_TAG,
    MATCH_HANDS,
    MATCH_SEED,
    MEMBER_TAG,
    ODD_HANDS,
    OTHER_LEARNER_SEED,
    OTHER_MATCH_SEED,
    OTHER_RULE,
    POOL_M,
    START_LABEL,
    VERSION_IDS,
    EvaluationCase,
    bootstrap_seed,
    build_policy,
    cell_directions,
    cell_seed,
    checkpoint,
    default_shape,
    other_shape,
    checkpoint_with_unknown_encoding,
    checkpoint_without_facts,
    checkpoint_without_seed,
    chosen_action,
    count,
    declared_internal,
    direction_counts,
    draw_index,
    draw_order,
    file_that_is_not_a_checkpoint,
    first_legal,
    hand_seed,
    illegal_policy,
    last_legal,
    member_id,
    member_seed,
    params_of,
    probe_readouts,
    refusal_class,
    seat_split_counts,
    shapes,
    token,
    unlabelled_of,
    version_record,
)


class SchedulerTest(EvaluationCase):
    def test_evl_3_1_the_six_seed_derivations_are_the_design_s(self):
        """EVL-3.1 `_hand_seed`, `_cell_seed`, `_member_seed` and `_bootstrap_seed` are the §3 digest of their tag and parts, `_draw_index` is `seed % n`, and `_draw_order` is the counted draw's permutation whose first position is that same index and whose rest ascends by the `draw` digest, ties broken by position — all five recomputed here from `scheduler.md` §3 and `seats.md` §2 (`guardrails.md` G8, `docs/L1/seats.md` §4, FAM-7.5, ASM-43)."""
        self.evaluation()
        seed = declared_internal("seeds", "_seed")
        hand = declared_internal("seeds", "_hand_seed")
        cell = declared_internal("seeds", "_cell_seed")
        member = declared_internal("seeds", "_member_seed")
        boot = declared_internal("seeds", "_bootstrap_seed")
        drawn = declared_internal("seeds", "_draw_index")
        with self.subTest(derivation="_seed"):
            self.assertEqual(
                seed(HAND_TAG, MATCH_SEED, 5),
                hand_seed(MATCH_SEED, 5),
                "_seed(tag, *parts) is int.from_bytes(sha256(payload).digest()[:8], "
                "'big') %% 2**31 over the tag and the parts joined by \\x1f, none "
                "trailing (scheduler.md §3, G8)",
            )
        derivations = (
            (
                "_hand_seed",
                hand,
                ((MATCH_SEED, 0), (MATCH_SEED, 11), (OTHER_MATCH_SEED, 3)),
                hand_seed,
                "one hand of a cell",
            ),
            (
                "_cell_seed",
                cell,
                ((MATCH_SEED, 0, 1), (MATCH_SEED, 2, 3), (OTHER_MATCH_SEED, 1, 2)),
                cell_seed,
                "one cell's own seed",
            ),
            (
                "_member_seed",
                member,
                ((MATCH_SEED, 0), (MATCH_SEED, 2), (OTHER_MATCH_SEED, 1)),
                member_seed,
                "one of the three baselines' policies",
            ),
            (
                "_bootstrap_seed",
                boot,
                ((MATCH_SEED,), (OTHER_MATCH_SEED,)),
                bootstrap_seed,
                "the rating's bootstrap",
            ),
        )
        for name, fn, arguments, expected, what in derivations:
            for args in arguments:
                with self.subTest(derivation=name, args=args):
                    self.assertEqual(
                        fn(*args),
                        expected(*args),
                        "%s seeds %s, and scheduler.md §3 fixes the derivation exactly "
                        "as a tagged SHA-256 digest, so a second scheme is red (G8): "
                        "%r != %r" % (name, what, fn(*args), expected(*args)),
                    )
        for size in (2, 3, 5, 8):
            for value in (MATCH_SEED, OTHER_MATCH_SEED, 0, 7):
                with self.subTest(derivation="_draw_index", args=(value, size)):
                    self.assertEqual(
                        drawn(value, size),
                        draw_index(value, size),
                        "_draw_index(seed, n) is seed %% n, the seed's position in the "
                        "membership's order, and not a digest (scheduler.md §3, "
                        "pool.md §7, G8): %r != %r"
                        % (drawn(value, size), draw_index(value, size)),
                    )
        # The sixth derivation: the counted draw's order, recomputed from seats.md §2
        # rather than imported from `evaluation.seeds`, so the rule is asserted and not
        # restated.  It is a permutation -- a draw is without replacement, so a six-seat
        # hand never seats one member twice -- and its first position is the uncounted
        # draw's own member, which is what makes a draw of one today's opponent
        # (`docs/L1/seats.md` §4, `league.md` §2, ASM-43).
        order = declared_internal("seeds", "_draw_order")
        for size in (2, 5, 7):
            for value in (MATCH_SEED, OTHER_MATCH_SEED, 0, 7, 12345):
                with self.subTest(derivation="_draw_order", args=(value, size)):
                    drawn_order = tuple(order(value, size))
                    self.assertEqual(
                        drawn_order,
                        draw_order(value, size),
                        "_draw_order(seed, n) is the first position seed %% n, then the "
                        "rest ascending by the `draw` digest with ties broken by position "
                        "(seats.md §2, docs/L1/seats.md §4, ASM-43): %r != %r"
                        % (drawn_order, draw_order(value, size)),
                    )
                    self.assertEqual(
                        sorted(drawn_order),
                        list(range(size)),
                        "the draw's order is a permutation of the membership's %d "
                        "positions, so the draw is without replacement and no seat is "
                        "seated twice (docs/L1/seats.md §4, league.md §2, ASM-43): %r"
                        % (size, drawn_order),
                    )
                    self.assertEqual(
                        drawn_order[0],
                        value % size,
                        "the first position of the counted draw is seed %% n, the member "
                        "the uncounted draw names, so a draw of one is today's opponent "
                        "(scheduler.md §3, pool.md §7, docs/L1/seats.md §4, ASM-43): %r"
                        % (drawn_order,),
                    )
                    self.assertEqual(
                        drawn_order[0],
                        drawn(value, size),
                        "the two derivations are one rule at the first position, so a "
                        "counted draw that began anywhere else is red here "
                        "(scheduler.md §3, seats.md §2, ASM-43): %r vs %r"
                        % (drawn_order[0], drawn(value, size)),
                    )

    def test_evl_3_2_the_derived_seeds_are_in_range_distinct_and_move_no_stream(self):
        """EVL-3.2 the digest-derived seeds are plain ints in `[0, 2**31)`, a different position derives a different one, and deriving moves no global stream (`scheduler.md` §3, ASM-2, G8)."""
        self.evaluation()
        hand = declared_internal("seeds", "_hand_seed")
        cell = declared_internal("seeds", "_cell_seed")
        before = self.stream_state()
        hands = [hand(MATCH_SEED, index) for index in range(8)]
        cells = [cell(MATCH_SEED, i, j) for (i, j) in ((0, 1), (0, 2), (1, 2), (0, 3))]
        self.assert_stream_unchanged(before, "the seed derivations")
        for name, values in (("_hand_seed", hands), ("_cell_seed", cells)):
            with self.subTest(derivation=name):
                for value in values:
                    self.assertNotIsInstance(
                        value, bool, "%s returns a plain int (scheduler.md §3)" % name
                    )
                    self.assertIsInstance(
                        value, int, "%s returns a plain int (scheduler.md §3)" % name
                    )
                    self.assertGreaterEqual(
                        value, 0, "%s is in [0, 2**31) (scheduler.md §3): %r" % (name, value)
                    )
                    self.assertLess(
                        value,
                        2 ** 31,
                        "%s is in [0, 2**31) (scheduler.md §3): %r" % (name, value),
                    )
                self.assertEqual(
                    len(set(values)),
                    len(values),
                    "%s derives a different seed for every position it is given, so "
                    "consecutive hands and cells do not collide (scheduler.md §3): %r"
                    % (name, values),
                )

    def test_evl_3_3_seats_alternate_and_the_split_says_so(self):
        """EVL-3.3 hand `i` gives seat 0 to `left` when `i` is even, and `seat_split` is keyed `seat 0`/`seat 1` with the two counts summing to `hands` and differing by at most one (`scheduler.md` §2, G9)."""
        package = self.evaluation()
        cell = package.match("random", "always-call", ODD_HANDS, MATCH_SEED)
        directions = cell_directions(cell)
        self.assertEqual(
            len(directions), 2, "a cell reports both directions (records.md §9)"
        )
        expected = {0: (ODD_HANDS + 1) // 2, 1: ODD_HANDS // 2}
        for index, direction in enumerate(directions):
            with self.subTest(direction=index):
                split = direction["seat_split"]
                self.assertEqual(
                    {token(key) for key in split},
                    {"seat0", "seat1"},
                    "seat_split is keyed by the engine's seat order, `seat 0` and "
                    "`seat 1`, and not by button/big blind (scheduler.md §2, G9): %r"
                    % (split,),
                )
                seat0, seat1 = seat_split_counts(split)
                self.assertEqual(
                    seat0 + seat1,
                    ODD_HANDS,
                    "the split covers every hand of the cell (scheduler.md §2, "
                    "records.md §9, G9): %r" % (split,),
                )
                self.assertLessEqual(
                    abs(seat0 - seat1),
                    1,
                    "the two seat counts differ by at most one, because seats alternate "
                    "(scheduler.md §2, league.md §3, G9): %r" % (split,),
                )
                self.assertEqual(
                    seat0,
                    expected[index],
                    "seat 0 holds the button, so the left member (%d) holds it "
                    "ceil(hands/2) times and the right floor(hands/2) (scheduler.md §1-§2, "
                    "engine/surface.md §4, G9): %r" % (index, split),
                )

    def test_evl_3_4_a_cell_accounts_for_every_hand_it_was_given(self):
        """EVL-3.4 wins + ties + losses = `hands` in both directions, and the cell costs its hand count and not twice it (`scheduler.md` §1, §4, FAM-7.1, D-16)."""
        package = self.evaluation()
        cell = package.match("random", "always-call", MATCH_HANDS, MATCH_SEED)
        self.assertEqual(
            count(cell["hands"], "a cell's hands"),
            MATCH_HANDS,
            "a cell plays the hand count it was given (surface.md §9, records.md §9): %r"
            % (cell["hands"],),
        )
        directions = cell_directions(cell)
        for index, direction in enumerate(directions):
            with self.subTest(direction=index):
                self.assert_plain_counts(
                    direction_counts(direction), MATCH_HANDS, "direction %d" % index
                )
        self.assertEqual(
            len(directions),
            2,
            "the two directions are the same hands seen from each seat, so a cell costs "
            "its hand count and not twice it (scheduler.md §1, §4, ASM-14)",
        )

    def test_evl_3_5_the_two_directions_are_exact_mirrors(self):
        """EVL-3.5 one direction's wins are the other's losses, a tied hand is a tie for both, and the hand's class is the sign of its net delta (`scheduler.md` §4, FAM-7.3, G10)."""
        cell = self.evaluation().match("random", "always-call", MATCH_HANDS, MATCH_SEED)
        left, right = cell_directions(cell)
        left_wins, left_ties, left_losses, _left_mean = direction_counts(left, "the left direction")
        right_wins, right_ties, right_losses, _right_mean = direction_counts(
            right, "the right direction"
        )
        self.assertEqual(
            left_wins,
            right_losses,
            "one direction's wins are the other's losses, because the hand was zero-sum "
            "(scheduler.md §4, league.md §2, FAM-7.4): %r vs %r"
            % ((left_wins, left_ties, left_losses), (right_wins, right_ties, right_losses)),
        )
        self.assertEqual(
            left_losses,
            right_wins,
            "one direction's losses are the other's wins (scheduler.md §4, FAM-7.4)",
        )
        self.assertEqual(
            left_ties,
            right_ties,
            "a tied hand is a tie for both directions (scheduler.md §4, FAM-7.4)",
        )

    def test_evl_3_6_the_two_mean_chip_deltas_negate_exactly(self):
        """EVL-3.6 `mean_chip_delta` is chips per hand and the two means are exact negations, because both are one integer total over the same hands (`scheduler.md` §4, FAM-7.4, G10)."""
        cell = self.evaluation().match("random", "always-call", MATCH_HANDS, MATCH_SEED)
        left, right = cell_directions(cell)
        left_mean = direction_counts(left, "the left direction")[3]
        right_mean = direction_counts(right, "the right direction")[3]
        self.assertEqual(
            left_mean,
            -right_mean,
            "the two mean chip deltas are exact negations, because d0 + d1 == 0 for "
            "every hand and both are divided by the same hands (scheduler.md §4, G10): "
            "%r and %r" % (left_mean, right_mean),
        )

    def test_evl_3_7_params_are_two_integers_and_unlabelled_names_the_unmeasured(self):
        """EVL-3.7 `params` holds one integer per member, position-aligned with `members`, a baseline's zero is the catalogue's, a version's is `agents.param_count`, and an opaque policy's unmeasured `0` is named in `unlabelled` (`scheduler.md` §4-§5, `surface.md` §2, G11)."""
        package = self.evaluation()
        baselines = package.match("random", "always-call", ALT_HANDS, MATCH_SEED)
        self.assertEqual(
            params_of(baselines),
            [0, 0],
            "a baseline's parameter count is the zero agents.baselines() declares, "
            "position-aligned with members (scheduler.md §5, agents/surface.md §11): %r"
            % (params_of(baselines),),
        )
        self.assertEqual(
            unlabelled_of(baselines),
            (),
            "a baseline's zero is measured, so it is not unlabelled (scheduler.md §4, "
            "surface.md §2): %r" % (unlabelled_of(baselines),),
        )
        opaque = package.match(first_legal, last_legal, ALT_HANDS, MATCH_SEED)
        self.assertEqual(
            params_of(opaque),
            [0, 0],
            "an opaque policy's capacity is unmeasured and recorded as 0 "
            "(scheduler.md §5, ASM-10): %r" % (params_of(opaque),),
        )
        self.assertEqual(
            tuple(unlabelled_of(opaque)),
            ("policy-1", "policy-2"),
            "the ids whose params is an unmeasured 0 are named in `unlabelled`, so a "
            "reader tells a measured zero from an unmeasured one (scheduler.md §4, "
            "surface.md §2, G11): %r" % (unlabelled_of(opaque),),
        )
        saved = self.checkpoint(name="member")
        record = version_record(
            VERSION_IDS[0], START_LABEL, path=saved["path"], seed=saved["seed"]
        )
        versioned = package.match(record, "always-call", ALT_HANDS, MATCH_SEED)
        self.assertEqual(
            params_of(versioned),
            [saved["params"], 0],
            "a version's params is agents.param_count of the restored learner "
            "(scheduler.md §5, records.md §9, ASM-10): %r" % (params_of(versioned),),
        )
        self.assertEqual(
            tuple(member_id(entry) for entry in versioned["members"]),
            (VERSION_IDS[0], "always-call"),
            "the cell's members are the two sides' ids in argument order "
            "(surface.md §9, records.md §9): %r" % (versioned["members"],),
        )

    def test_evl_3_8_policy_from_decides_what_agents_act_decides(self):
        """EVL-3.8 `policy_from(path)` chooses the action `agents.act` chooses on the same readout -- the loss-free boundary `protocol.md` §5 requires -- and a checkpoint whose container records no seed is refused rather than patched (`surface.md` §12, `scheduler.md` §5.1, FAM-12.3)."""
        package = self.evaluation()
        for name, encoding, kind in (
            ("dense", "flat-numeric", "naive-stack"),
            ("tokens", "card-tokens", "deep"),
        ):
            saved = self.checkpoint(name=name, encoding=encoding, kind=kind)
            policy = package.policy_from(saved["path"])
            with self.subTest(encoding=encoding):
                for row in probe_readouts(4):
                    expected = chosen_action(saved["learner"], saved["encoder"], row["readout"])
                    self.assertEqual(
                        policy(row["readout"], row["legal"]),
                        expected,
                        "a loaded checkpoint chooses the action its learner chooses on "
                        "the same readout, which is what lets a shipped version be a "
                        "league member (surface.md §12, scheduler.md §5.1, "
                        "protocol.md §5, FAM-12.3): expected %r" % (expected,),
                    )
        self.assert_evaluation_refusal(
            package.policy_from,
            checkpoint_without_seed(),
            entry="policy_from",
            groups=(("seed",), ("no seed", "records no seed", "missing")),
            label="a checkpoint recording no seed",
        )

    def test_evl_3_9_match_refuses_what_the_contract_refuses(self):
        """EVL-3.9 `match` refuses a hand count that is not a positive integer, a seed that is not an integer, two sides carrying one id and a value that is neither callable nor a member record nor a baseline name (`surface.md` §9, `scheduler.md` §6, G16)."""
        package = self.evaluation()
        cases = (
            ("a hand count of zero", ("random", "always-call", 0, MATCH_SEED), (("hands",),)),
            ("a negative hand count", ("random", "always-call", -3, MATCH_SEED), (("hands",),)),
            ("a string hand count", ("random", "always-call", "12", MATCH_SEED), (("hands",),)),
            ("a bool hand count", ("random", "always-call", True, MATCH_SEED), (("hands",),)),
            ("a fractional hand count", ("random", "always-call", 2.5, MATCH_SEED), (("hands",),)),
            ("a string seed", ("random", "always-call", MATCH_HANDS, "31337"), (("seed",),)),
            ("a None seed", ("random", "always-call", MATCH_HANDS, None), (("seed",),)),
            ("a bool seed", ("random", "always-call", MATCH_HANDS, True), (("seed",),)),
            (
                "one id on both sides",
                ("random", "random", MATCH_HANDS, MATCH_SEED),
                (("random",), ("distinct",)),
            ),
            (
                "a number as a side",
                (42, "random", MATCH_HANDS, MATCH_SEED),
                (("left",), ("policy", "record")),
            ),
            (
                "a record without an id",
                ({"path": "/tmp/x.pt"}, "random", MATCH_HANDS, MATCH_SEED),
                (("left", "id"),),
            ),
        )
        for label, args, groups in cases:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    package.match, *args, entry="match", groups=groups, label=label
                )
        saved = self.checkpoint(name="member")
        same_twice = version_record(
            VERSION_IDS[0], START_LABEL, path=saved["path"], seed=saved["seed"]
        )
        with self.subTest(case="two member records with one id"):
            self.assert_evaluation_refusal(
                package.match,
                same_twice,
                dict(same_twice),
                MATCH_HANDS,
                MATCH_SEED,
                entry="match",
                groups=((VERSION_IDS[0],), ("distinct",)),
                label="two records with one id",
            )

    def test_evl_3_10_one_pair_one_hand_count_and_one_seed_give_one_cell(self):
        """EVL-3.10 two calls at one pair, one hand count and one seed are equal value for value, and the record carries its `seed` and its `params` (`surface.md` §9, `scheduler.md` §7, FAM-7.7)."""
        package = self.evaluation()
        first = package.match("random", "always-call", MATCH_HANDS, MATCH_SEED)
        second = package.match("random", "always-call", MATCH_HANDS, MATCH_SEED)
        self.assertEqual(
            first,
            second,
            "one pair, one hand count and one seed give one cell whatever was played "
            "before it, because every hand's seed is a function of the cell's seed and "
            "the hand's index alone (surface.md §9, scheduler.md §7, FAM-7.7)",
        )
        self.assertEqual(
            count(first["seed"], "a cell's seed"),
            MATCH_SEED,
            "the record carries the seed the cell was played at (records.md §9, "
            "surface.md §9): %r" % (first["seed"],),
        )
        self.assertEqual(
            len(params_of(first)),
            len(tuple(first["members"])),
            "params holds one integer per member, position-aligned with members "
            "(scheduler.md §4, G11): %r" % (first["params"],),
        )

    def test_evl_3_11_a_different_seed_deals_different_hands(self):
        """EVL-3.11 the same pair at a different seed gives a different cell -- a different seed deals different hands (`surface.md` §9, `scheduler.md` §7, FAM-4)."""
        package = self.evaluation()
        first = package.match("random", "always-call", MATCH_HANDS, MATCH_SEED)
        second = package.match("random", "always-call", MATCH_HANDS, OTHER_MATCH_SEED)
        self.assertNotEqual(
            count(first["seed"], "a cell's seed"),
            count(second["seed"], "a cell's seed"),
            "each cell records the seed it was played at (records.md §9): %r vs %r"
            % (first["seed"], second["seed"]),
        )
        self.assertNotEqual(
            first,
            second,
            "a different seed deals a different cell (surface.md §9, scheduler.md §7, "
            "FAM-4)",
        )
        self.assertNotEqual(
            [direction_counts(entry) for entry in cell_directions(first)],
            [direction_counts(entry) for entry in cell_directions(second)],
            "a different seed deals different hands, so the cell's own counts differ "
            "and not only its recorded seed (surface.md §9, scheduler.md §7, FAM-4)",
        )

    def test_evl_3_12_an_illegal_descriptor_is_engine_s_refusal_and_is_not_repaired(self):
        """EVL-3.12 a policy returning a descriptor outside `legal_actions` is `engine`'s refusal, propagated unchanged -- never caught, repaired or turned into a fold (`surface.md` §9, `scheduler.md` §6, D-2, `engine/surface.md` §10)."""
        package = self.evaluation()
        try:
            value = package.match(first_legal, illegal_policy, ALT_HANDS, MATCH_SEED)
        except Exception as exc:
            self.assertTrue(
                str(exc).strip(),
                "the refusal names the violated contract (errors.md §3): %r"
                % (type(exc).__name__,),
            )
            self.assertNotIsInstance(
                exc,
                refusal_class(),
                "an illegal descriptor is engine's refusal and is not caught or repaired "
                "here, so it does not arrive as this module's own class "
                "(scheduler.md §6, D-2): %r" % (exc,),
            )
        else:
            self.fail(
                "match accepted a policy returning a descriptor outside legal_actions "
                "and returned %r: a contract violation is never a fold "
                "(surface.md §9, scheduler.md §6, D-2)" % (value,)
            )

    def test_evl_3_13_a_version_record_whose_seed_disagrees_is_not_refused(self):
        """EVL-3.13 a version record whose own `seed` disagrees with its container is not refused: the container decides the action and the record's seed is carried (`scheduler.md` §5, `errors.md` §5, G16)."""
        package = self.evaluation()
        saved = self.checkpoint(name="member")
        wrong = version_record(
            VERSION_IDS[1], START_LABEL, path=saved["path"], seed=OTHER_LEARNER_SEED, step=5
        )
        cell = package.match(wrong, "always-call", ALT_HANDS, MATCH_SEED)
        self.assertEqual(
            tuple(member_id(entry) for entry in cell["members"]),
            (VERSION_IDS[1], "always-call"),
            "a version record's own seed disagreeing with its container is carried and "
            "not refused, because over-refusal is a defect (scheduler.md §5, "
            "errors.md §5): %r" % (cell["members"],),
        )
        self.assertEqual(
            params_of(cell)[0],
            saved["params"],
            "the side is the learner the container restored, so its params is that "
            "learner's measurement (scheduler.md §5, ASM-10): %r" % (cell["params"],),
        )

    def test_evl_3_14_two_paths_of_one_learner_are_one_player(self):
        """EVL-3.14 two checkpoints of one learner written at two paths give one player, so no seed is a digest of the path: both decide as the learner's `act` (`scheduler.md` §5, §5.1, `guardrails.md` G20)."""
        package = self.evaluation()
        saved = self.checkpoint(name="member")
        folder = self.tempdir()
        paths = [os.path.join(folder, "copy-a.ckpt"), os.path.join(folder, "copy-b.ckpt")]
        for path in paths:
            self.agents().save(saved["learner"], path)
        policies = [package.policy_from(path) for path in paths]
        rows = probe_readouts(4)
        for row in rows:
            with self.subTest(hand=row["seed"]):
                answers = [policy(row["readout"], row["legal"]) for policy in policies]
                self.assertEqual(
                    answers[0],
                    answers[1],
                    "one learner at two paths is one player, so a path digest is not a "
                    "seed (scheduler.md §5.1, G20): %r vs %r" % (answers[0], answers[1]),
                )
                self.assertEqual(
                    answers[0],
                    chosen_action(saved["learner"], saved["encoder"], row["readout"]),
                    "both copies decide as the learner decided, at the seed the "
                    "container records (scheduler.md §5.1, protocol.md §5, G20)",
                )

    def test_evl_3_15_policy_from_refuses_what_the_contract_refuses(self):
        """EVL-3.15 `policy_from` refuses a path naming no readable file, a file that is no readable zip, a container recording no seed and one whose recorded encoding name `features.build_encoder` refuses -- each naming the fact and the path, and the name refused by building it rather than by reading a catalogue (`surface.md` §12, `scheduler.md` §5.1, §6, G20)."""
        package = self.evaluation()
        absent = os.path.join(self.tempdir(), "no-such-checkpoint.ckpt")
        cases = (
            ("a path that names no file", absent, (("path",), ("readable",))),
            (
                "a file that is not a checkpoint",
                file_that_is_not_a_checkpoint(),
                (("path",), ("readable", "zip")),
            ),
            (
                "a container recording no facts at all",
                checkpoint_without_facts(),
                (("seed",), ("path",)),
            ),
            (
                "a container recording no seed",
                checkpoint_without_seed(),
                (("seed",), ("path",)),
            ),
            (
                "a container recording an encoding name build_encoder refuses",
                checkpoint_with_unknown_encoding(),
                (("bogus-encoding",), ("build_encoder", "refuses", "encoding")),
            ),
        )
        for label, path, groups in cases:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    package.policy_from, path, entry="policy_from", groups=groups, label=label
                )

    def test_evl_3_16_policy_from_plays_no_hand_and_moves_no_stream(self):
        """EVL-3.16 `policy_from` loads a member in evaluation mode: it plays no hand, moves no global stream and is one policy on two calls (`surface.md` §12, `scheduler.md` §7, ASM-2)."""
        package = self.evaluation()
        saved = self.checkpoint(name="member")
        rows = probe_readouts(3)
        before = self.stream_state()
        first = package.policy_from(saved["path"])
        answers = [first(row["readout"], row["legal"]) for row in rows]
        second = package.policy_from(saved["path"])
        again = [second(row["readout"], row["legal"]) for row in rows]
        self.assert_stream_unchanged(before, "policy_from() and its policy")
        self.assertEqual(
            answers,
            again,
            "one checkpoint gives one policy, and it decides as its learner decided "
            "(surface.md §12, scheduler.md §5.1)",
        )

    def test_evl_3_17_a_policy_handed_in_from_outside_is_named_for_its_position(self):
        """EVL-3.17 a callable handed in from outside carries no id, so it is named `policy-1`, `policy-2` in argument order with an unlabelled zero, whatever was handed in (`surface.md` §2, `scheduler.md` §5, G11)."""
        package = self.evaluation()
        first = package.match(first_legal, last_legal, ALT_HANDS, MATCH_SEED)
        self.assertEqual(
            tuple(member_id(entry) for entry in first["members"]),
            ("policy-1", "policy-2"),
            "an opaque policy is named for its position in the call, `policy-1` then "
            "`policy-2` (surface.md §2, scheduler.md §5): %r" % (first["members"],),
        )
        reversed_call = package.match(last_legal, first_legal, ALT_HANDS, MATCH_SEED)
        self.assertEqual(
            tuple(member_id(entry) for entry in reversed_call["members"]),
            ("policy-1", "policy-2"),
            "the names follow the argument order of each call, not the callable, which "
            "carries none (surface.md §2): %r" % (reversed_call["members"],),
        )
        self.assertEqual(
            tuple(unlabelled_of(first)),
            ("policy-1", "policy-2"),
            "both opaque sides' zeros are unmeasured and named in unlabelled "
            "(scheduler.md §4, G11): %r" % (unlabelled_of(first),),
        )


    def test_evl_3_18_a_cell_names_the_rule_each_member_carried(self):
        """EVL-3.18 a cell's `rules` names each member's rule by its id -- the catalogue member its policy carries, `None` for a baseline or an opaque callable -- so a cell says which estimators met (`scheduler.md` §4-§5, `records.md` §9, D-19)."""
        package = self.evaluation()
        saved = self.checkpoint(name="rule-member")
        policy = package.policy_from(saved["path"])
        cell = package.match(policy, first_legal, MATCH_HANDS, MATCH_SEED)
        rules = cell["rules"]
        self.assertEqual(
            sorted(rules),
            sorted(member_id(entry) for entry in cell["members"]),
            "a cell's `rules` names each member of its pair by the cell's own ids "
            "(records.md §9, D-19): %r" % (rules,),
        )
        self.assertEqual(
            tuple(rules.values())[0],
            DEFAULT_RULE,
            "a member policy built from a checkpoint reports the rule its learner was "
            "built under, so the cell names the estimator that met (rules.md §7, "
            "e2e-surface.md §2, D-19): %r" % (rules,),
        )
        self.assertIsNone(
            tuple(rules.values())[1],
            "an opaque callable carries no rule, and the cell says so with `None` rather "
            "than inventing one (records.md §9, e2e-surface.md §2): %r" % (rules,),
        )
        with self.subTest(case="a baseline cell declares none"):
            baseline_cell = package.match("random", "oracle", MATCH_HANDS, MATCH_SEED)
            self.assertEqual(
                tuple(baseline_cell["rules"].values()),
                (None, None),
                "a baseline is a fixed rule and not a trained estimator, so both sides of "
                "a baseline cell declare no rule (records.md §9, D-19): %r"
                % (baseline_cell["rules"],),
            )

    def test_evl_3_19_policy_from_reports_the_rule_its_container_records(self):
        """EVL-3.19 the policy `policy_from` returns carries the rule the checkpoint records, read from the policy `agents.as_policy` built and never inferred (`scheduler.md` §5-§5.1, `surface.md` §12, `rules.md` §6, D-19)."""
        package = self.evaluation()
        for rule in (DEFAULT_RULE, OTHER_RULE):
            with self.subTest(rule=rule):
                saved = self.checkpoint(name="rule-%s" % (token(rule),), rule=rule)
                policy = package.policy_from(saved["path"])
                self.assertEqual(
                    getattr(policy, "learning_rule", None),
                    rule,
                    "a checkpoint records the rule its learner was trained under, and the "
                    "policy reports it, because playback is rule-free and the file is the "
                    "only witness (rules.md §6, surface.md §12): %r" % (saved["path"],),
                )

    def test_evl_3_20_a_member_record_contradicting_its_checkpoint_is_refused(self):
        """EVL-3.20 a version record whose `rule` disagrees with the rule its checkpoint records is refused naming the member and both values, before a cell is played (`scheduler.md` §5, `records.md` §7, ASM-20, D-19)."""
        package = self.evaluation()
        saved = self.checkpoint(name="contradicted-member")
        honest = version_record(
            VERSION_IDS[0], START_LABEL, path=saved["path"], rule=DEFAULT_RULE
        )
        cell = package.match(honest, "always-call", MATCH_HANDS, MATCH_SEED)
        self.assertEqual(
            cell["rules"][VERSION_IDS[0]],
            DEFAULT_RULE,
            "a member record that agrees with its file is played and its rule recorded "
            "(records.md §7, scheduler.md §5): %r" % (cell["rules"],),
        )
        liar = dict(honest, rule=OTHER_RULE)
        self.assert_evaluation_refusal(
            package.match,
            liar,
            "always-call",
            MATCH_HANDS,
            MATCH_SEED,
            entry="match",
            groups=((OTHER_RULE,), (DEFAULT_RULE,)),
            label="a member record contradicting its checkpoint's rule",
        )
        with self.subTest(case="the same contradiction through a table"):
            pool = self.frozen_pool(members=[liar], m=POOL_M)
            self.assert_evaluation_refusal(
                package.matrix,
                pool,
                [first_legal],
                "live",
                entry="matrix",
                groups=((OTHER_RULE,), (DEFAULT_RULE,)),
                label="a table over a member record that contradicts its checkpoint",
            )

    # -- the one shape a cell is played on (D-29) -----------------------------
    def test_evl_3_21_a_cell_is_played_on_the_one_shape_its_two_sides_name(self):
        """EVL-3.21 a cell's shape is the one its two sides name and `match` takes no shape argument: two sides naming two shapes are refused naming both sides and both shapes, while a cell of two shape-silent sides is played on the default shape with exactly the numbers it produced before the shape existed -- the shape adds no draw, no seed and no policy build (`scheduler.md` §1, §5-§7, `surface.md` §9, `shape.md` §3-§4, D-29)."""
        package = self.evaluation()
        default, other = shapes()
        default_member = package.policy_from(self.checkpoint(name="member")["path"])
        other_member = package.policy_from(
            self.checkpoint(name="member-nolimit", game=other)["path"]
        )
        self.assertEqual(
            getattr(default_member, "game", None),
            default,
            "a container that records no shape is a default-shape member, and its policy "
            "reports that (scheduler.md §5.1, shape.md §2, §4, D-29): %r"
            % (getattr(default_member, "game", None),),
        )
        self.assertEqual(
            getattr(other_member, "game", None),
            other,
            "a version-4 container records its shape and the policy reports it "
            "(scheduler.md §5.1, shape.md §4, D-29): %r"
            % (getattr(other_member, "game", None),),
        )
        before = self.stream_state()
        for label, left, right in (
            ("the second shape on the left", other_member, default_member),
            ("the second shape on the right", default_member, other_member),
        ):
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    package.match,
                    left,
                    right,
                    ALT_HANDS,
                    MATCH_SEED,
                    entry="match",
                    groups=(("match",), ("left",), ("right",), (default,), (other,)),
                    label="a cell whose two sides name two shapes",
                    kind="ShapeMismatch",
                )
        self.assert_stream_unchanged(
            before, "match() refusing a pair that names two shapes"
        )
        # A cell of two shape-silent sides is the cell it was before the shape existed:
        # the two baselines are built at the cell's seed either way, so playing the same
        # pair through the two baseline **names** and through the two baseline policies
        # they name gives one set of numbers -- and both cells say the default shape.
        hands = ALT_HANDS
        named_cell = package.match("random", "always-call", hands, OTHER_MATCH_SEED)
        policies_cell = package.match(
            self.agents().build_baseline("random", OTHER_MATCH_SEED),
            self.agents().build_baseline("always-call", OTHER_MATCH_SEED),
            hands,
            OTHER_MATCH_SEED,
        )
        for cell, label in (
            (named_cell, "the cell of two baseline names"),
            (policies_cell, "the cell of the two baseline policies"),
        ):
            with self.subTest(cell=label):
                self.assertEqual(
                    cell["game"],
                    default_shape(),
                    "a cell whose sides name no shape is played on the default shape, "
                    "and says so (scheduler.md §1, §4, shape.md §4, D-29): %r"
                    % (cell["game"],),
                )
        self.assertEqual(
            [direction_counts(entry) for entry in cell_directions(named_cell)],
            [direction_counts(entry) for entry in cell_directions(policies_cell)],
            "the shape adds no draw, no seed and no policy build: the same pair, hand "
            "count and seed give the same wins, ties, losses and mean chip deltas "
            "whether the sides were named or built (scheduler.md §5, §7, shape.md §4): "
            "%r vs %r"
            % (
                [direction_counts(entry) for entry in cell_directions(named_cell)],
                [direction_counts(entry) for entry in cell_directions(policies_cell)],
            ),
        )
        self.assertNotEqual(
            tuple(member_id(entry) for entry in named_cell["members"]),
            tuple(member_id(entry) for entry in policies_cell["members"]),
            "the two calls are different sides -- named baselines and opaque policies -- "
            "so the numbers agreeing is a fact about the deal and not about the ids "
            "(surface.md §2, scheduler.md §5): %r vs %r"
            % (named_cell["members"], policies_cell["members"]),
        )

    def test_evl_3_22_policy_from_off_decides_identically_at_two_seeds_and_draws_nothing(self):
        """EVL-3.22 `policy_from(path, "off")` is the masked maximum and the tie-break alone with no generator drawn from: it decides the same descriptor as an `off` policy built at another seed from the same saved learner, across a batch of real readouts of its shape, it leaves the global stream untouched, `policy_from(path)` still behaves as `schedule` does, and a mode that is neither `schedule` nor `off` is `UnknownExploration` naming it and both modes -- refused before any file is read (`shape.md` §5, `scheduler.md` §5, §6-§7, `surface.md` §12, guardrails.md G34, D-29)."""
        package = self.evaluation()
        saved = self.checkpoint(name="member")
        rows = probe_readouts(4)
        greedy = package.policy_from(saved["path"], "off")
        other_seed = build_policy(saved["learner"], saved["encoder"], OTHER_LEARNER_SEED, "off")
        before = self.stream_state()
        for row in rows:
            with self.subTest(hand=row["seed"]):
                mine = greedy(row["readout"], row["legal"])
                theirs = other_seed(row["readout"], row["legal"])
                self.assertIn(
                    mine,
                    tuple(row["legal"]),
                    "an off policy answers one descriptor of the decision's legal set "
                    "(surface.md §2, shape.md §5): %r" % (mine,),
                )
                self.assertEqual(
                    mine,
                    theirs,
                    "at `off` two policies at two seeds decide identically on one "
                    "readout, so the greedy reading is a function of the model and not "
                    "of a seed -- which is only true if no draw is taken at all "
                    "(shape.md §5, sizing.md §4, G34): %r vs %r" % (mine, theirs),
                )
        self.assert_stream_unchanged(before, "an `off` policy and its decisions")
        with self.subTest(case="many decisions move no stream"):
            before_many = self.stream_state()
            answers = [
                greedy(row["readout"], row["legal"])
                for _ in range(8)
                for row in rows
            ]
            self.assert_stream_unchanged(
                before_many, "thirty-two `off` decisions"
            )
            self.assertEqual(
                len(answers),
                32,
                "the batch is thirty-two decisions over the four real readouts",
            )
        with self.subTest(case="`policy_from(path)` is the schedule it always was"):
            scheduled = package.policy_from(saved["path"])
            scheduled_named = package.policy_from(saved["path"], "schedule")
            expected = build_policy(
                saved["learner"], saved["encoder"], saved["seed"], "schedule"
            )
            for row in rows:
                with self.subTest(hand=row["seed"]):
                    answer = scheduled(row["readout"], row["legal"])
                    self.assertEqual(
                        answer,
                        scheduled_named(row["readout"], row["legal"]),
                        "the mode's absence is the declared default `schedule`, so one "
                        "checkpoint gives one policy under either spelling "
                        "(shape.md §5, declarations.md §1): %r" % (answer,),
                    )
                    self.assertEqual(
                        answer,
                        expected(row["readout"], row["legal"]),
                        "`policy_from(path)` is `agents.as_policy` of the loaded learner "
                        "at the recorded seed under `schedule`, which is today's "
                        "behaviour unchanged (surface.md §12, scheduler.md §5.1, "
                        "shape.md §5, G20): %r" % (answer,),
                    )
        with self.subTest(case="the mode is refused, and before a file is read"):
            absent = os.path.join(self.tempdir(), "no-such-checkpoint.ckpt")
            for mode in ("greedy", "OFF", "", None):
                with self.subTest(mode=mode):
                    self.assert_evaluation_refusal(
                        package.policy_from,
                        absent,
                        mode,
                        entry="policy_from",
                        groups=(
                            ("schedule",),
                            ("off",),
                            (repr(mode),),
                        ),
                        label="a mode that is neither of the two",
                        kind="UnknownExploration",
                    )
            refused_early = os.path.join(self.tempdir(), "never-opened.ckpt")
            try:
                package.policy_from(refused_early, "greedy")
            except Exception as exc:
                self.assertIn(
                    "mode",
                    str(exc).lower(),
                    "a mode the catalogue does not carry is refused before the path is "
                    "touched, so an absent file cannot be the refusal a caller sees "
                    "(scheduler.md §6, shape.md §5): %r" % (str(exc),),
                )
                self.assertNotIn(
                    "no readable file",
                    str(exc).lower(),
                    "no file is read when the mode is refused, so the refusal is still "
                    "the mode's and never the path's (scheduler.md §6, shape.md §5): %r"
                    % (str(exc),),
                )


if __name__ == "__main__":
    unittest.main()
