"""HRN-3 — `expect`: four kinds, total over any value, each reading declared facts.

Drives `docs/L3/harness/expectations.md` §1-§3 and `docs/L2/harness/surface.md` §6: the
verdict record's three keys, the four kinds in their declared order, each kind's reader
order and the fact it names when it fails, totality over odd values, determinism, and
`refused`'s declared flag — never the wording of a record
(`guardrails.md` G9-G11, FAM-14.8, FAM-16.36).

The records judged here are the ones `engine.play_hand`, `evaluation.match` and
`harness.seam` really return, plus values a case composes, which §2 judges exactly as it
judges a returned record (`surface.md` §2, FAM-14.10).
"""

import copy
import unittest

from _harness_support import (
    EXPECTATION_KINDS,
    SEAM_RECORDING,
    SEED_HAND,
    HarnessCase,
    as_mapping,
    as_number,
    as_sequence,
    case,
    engine,
    play,
    pure_value,
    readout,
    real_cell,
)


class Opaque(object):
    """A value with no mapping interface, no sequence and no number in it."""

    def __repr__(self):
        return "<an opaque observed value>"


def _raiser():
    """A zero-argument step that raises, so `drive` records a real refusal observation."""
    raise RuntimeError("an invented refusal")


#: The descriptors a `legal-choice` value offers, spelled as `expectations.md` §2.2 does.
LEGAL_DESCRIPTORS = ("fold", "check-call")


class RaisingEquality(object):
    """A descriptor whose `__eq__` raises: a reader that compares it inherits the raise."""

    def __eq__(self, other):
        raise RuntimeError("comparison exploded")

    def __repr__(self):
        return "<a descriptor whose == raises>"


class UnboolableComparison(object):
    """The value a hostile `==` returns: a non-boolean that refuses to become one."""

    def __bool__(self):
        raise ValueError("the comparison has no truth value")

    def __repr__(self):
        return "<a comparison with no truth value>"


class UnboolableEquality(object):
    """A descriptor whose `==` is not a boolean — numpy's array-`==` shape, without numpy.

    `chosen == candidate` returns an `UnboolableComparison`, so `any(...)` raises the
    first time it has to coerce a comparison to a truth value (`expectations.md` §2.2).
    """

    def __eq__(self, other):
        return UnboolableComparison()

    def __repr__(self):
        return "<a descriptor whose == is not a boolean>"


class CoercibleEquality(object):
    """A descriptor whose `==` is a falsy non-boolean (`[]`), which `any(...)` can coerce."""

    def __eq__(self, other):
        return []

    def __repr__(self):
        return "<a descriptor whose == is a falsy list>"


def _raised_class(thunk, what):
    """The class name of the exception `thunk` raises, computed and never hardcoded.

    §3 keeps a reader's bug visible by carrying the exception's class in the reason, so
    the case computes the class from the same arithmetic or comparison the reader runs
    instead of pinning a CPython literal (`expectations.md` §3, G9).
    """
    try:
        thunk()
    except Exception as exc:
        return type(exc).__name__
    raise AssertionError(
        "%s must raise, because the reader runs that same arithmetic or comparison and "
        "a case that pins a raise needs one (expectations.md §3)" % (what,)
    )


def _sum_class(terms, what):
    """The class `sum(terms)` raises — `zero-sum`'s and `counted`'s own arithmetic."""
    return _raised_class(lambda: sum(terms), what)


def _comparison_class(chosen):
    """The class `any(chosen == candidate …)` raises for one hostile descriptor."""
    return _raised_class(
        lambda: any(chosen == candidate for candidate in LEGAL_DESCRIPTORS),
        "the membership comparison `legal-choice` runs on this chosen descriptor",
    )


class ExpectationsTest(HarnessCase):
    def judge(self, kind, observation):
        """One verdict through the surface, with §1's record shape asserted."""
        record = self.ep("expect")(kind, observation)
        return self.assert_verdict_record(record, kind)

    def verdict_of(self, kind, observation):
        return self.judge(kind, observation)["verdict"]

    def reason_of(self, kind, observation):
        record = self.judge(kind, observation)
        return record["reason"]

    # -- totality ------------------------------------------------------------
    def test_hrn_3_1_every_kind_is_total_over_odd_values(self):
        """HRN-3.1 each of the four kinds yields `{kind, verdict, reason}` for `None`, `0`, `""`, `[]`, `{}`, `True`, an opaque object, a 1000-digit integer, a nested record, a cell-shaped value whose `mean_chip_delta`s are a string, a `None` and a boolean beside a number, a delta pair mixing `10**999` with a float, a per-seat mapping mixing them, a cell-shaped value whose counts mix them and a chosen descriptor whose `==` raises — and never raises (expectations §2.5, §3, G9, FAM-14.8, surface §6)."""
        values = (
            ("None", None),
            ("zero", 0),
            ("the empty string", ""),
            ("the empty list", []),
            ("the empty mapping", {}),
            ("True", True),
            ("an opaque object", Opaque()),
            ("a 1000-digit integer", 10 ** 999),
            (
                "a nested record",
                {"nested": {"payoffs": (1, -1)}, "more": [1, {"deep": 2}]},
            ),
            (
                "a cell-shaped value with a string mean",
                {
                    "directions": [
                        {"mean_chip_delta": "x"},
                        {"mean_chip_delta": 0},
                    ],
                    "hands": 4,
                },
            ),
            (
                "a cell-shaped value with a None mean",
                {
                    "directions": [
                        {"mean_chip_delta": None},
                        {"mean_chip_delta": 0},
                    ],
                    "hands": 4,
                },
            ),
            (
                "a cell-shaped value with a boolean mean beside a number",
                {
                    "directions": [
                        {"mean_chip_delta": True},
                        {"mean_chip_delta": -1},
                    ],
                    "hands": 4,
                },
            ),
            (
                "a delta pair mixing a huge integer with a float",
                (10 ** 999, 1.5),
            ),
            (
                "a per-seat mapping mixing a huge integer with a float",
                {"seat 0": 1.5, "seat 1": 10 ** 999},
            ),
            (
                "a cell-shaped value whose counts mix a huge integer with a float",
                {
                    "hands": 4,
                    "directions": (
                        {"wins": 10 ** 999, "ties": 1.5, "losses": 0},
                        {"wins": 4, "ties": 0, "losses": 0},
                    ),
                },
            ),
            (
                "a chosen descriptor whose == raises",
                {"chosen": RaisingEquality(), "legal": ["fold"]},
            ),
        )
        for kind in EXPECTATION_KINDS:
            for label, value in values:
                with self.subTest(kind=kind, value=label):
                    record = self.ep("expect")(kind, value)
                    record = as_mapping(record, "the %r verdict" % (kind,))
                    self.assertEqual(
                        list(record),
                        ["kind", "verdict", "reason"],
                        "every listed kind yields the verdict record for any observed "
                        "value (expectations §1, §3, G9): %r" % (list(record),),
                    )
                    self.assertEqual(
                        record["verdict"],
                        "fail",
                        "a value the %r kind cannot read is a named failure and never a "
                        "pass and never a silence (%s; expectations §3, G9)"
                        % (kind, label,),
                    )
                    self.assertIsInstance(
                        record["reason"],
                        str,
                        "and the failure is named in one sentence (%s; expectations §1, "
                        "§3): %r" % (label, record["reason"]),
                    )

    def test_hrn_3_2_a_failure_names_the_kind_verbatim_and_the_fact(self):
        """HRN-3.2 a value a kind cannot read fails with one sentence carrying the kind verbatim and the fact that did not hold, and the record repeats the kind as handed (expectations §1, §3, G9)."""
        for kind in EXPECTATION_KINDS:
            with self.subTest(kind=kind):
                record = self.judge(kind, None)
                reason = record["reason"]
                self.assertIn(
                    kind,
                    reason,
                    "the reason names the kind verbatim, so a reader can find it by "
                    "token (expectations §1, FAM-16.36): %r" % (reason,),
                )
                self.assertIn(
                    "harness.expect failed the kind",
                    reason,
                    "one form for all four kinds: `harness.expect failed the kind "
                    "'<kind>': <the fact that did not hold>` (expectations §1): %r"
                    % (reason,),
                )
                self.assertEqual(
                    record["verdict"],
                    "fail",
                    "a value a kind cannot read is a fail (expectations §3, G9): %r"
                    % (record,),
                )

    # -- zero-sum: the four shapes, in order --------------------------------
    def test_hrn_3_3_zero_sum_reads_its_four_shapes_and_passes_each_balanced_one(self):
        """HRN-3.3 `zero-sum` reads an episode record's `payoffs`, a cell record's two `mean_chip_delta`s, a mapping of two per-seat numbers and a sequence of two numbers, and passes each when they balance (expectations §2.1, G10, FAM-7)."""
        episode = play()
        self.assertEqual(
            self.judge("zero-sum", episode)["verdict"],
            "pass",
            "a real episode record balances by ASM-12 (expectations §2.1, records.md "
            "§5): %r" % (episode["payoffs"],),
        )
        cell = real_cell(hands=4)
        self.assertEqual(
            self.judge("zero-sum", cell)["verdict"],
            "pass",
            "a real cell's two directions are each other's negative, so its deltas "
            "balance (expectations §2.1, records.md §9): %r" % (cell["directions"],),
        )
        self.assertEqual(
            self.judge("zero-sum", {"seat 0": 12, "seat 1": -12})["verdict"],
            "pass",
            "a mapping of two per-seat numbers, named by seat (expectations §2.1): "
            "%r" % ({"seat 0": 12, "seat 1": -12},),
        )
        payoffs = episode["payoffs"]
        self.assertEqual(
            len(as_mapping(payoffs, "engine.payoffs' own mapping")),
            2,
            "engine.payoffs returns one number per seat (engine/surface.md §9): %r"
            % (payoffs,),
        )
        self.assertEqual(
            self.judge("zero-sum", dict(payoffs))["verdict"],
            "pass",
            "engine.payoffs' own {0: x, 1: y} mapping is the third shape (expectations "
            "§2.1): %r" % (dict(payoffs),),
        )
        self.assertEqual(
            self.judge("zero-sum", [7, -7])["verdict"],
            "pass",
            "a sequence of two numbers is the fourth shape (expectations §2.1): %r"
            % ([7, -7],),
        )

    def test_hrn_3_4_zero_sum_tries_the_shapes_in_their_declared_order(self):
        """HRN-3.4 `payoffs` is read before any other number, a cell's `directions` before its other numeric facts, and a mapping stating three or more numbers with no `payoffs` and no `directions` states no deltas (expectations §2.1, G10)."""
        with_payoffs = {
            "payoffs": {0: 5, 1: -5},
            "decisions": (),
            "hands": 40,
            "seed": 1,
            "extra": 991,
        }
        self.assertEqual(
            self.judge("zero-sum", with_payoffs)["verdict"],
            "pass",
            "a mapping carrying `payoffs` is read under it, so its other numbers are "
            "not deltas (expectations §2.1): %r" % (with_payoffs,),
        )
        with_directions = {
            "hands": 4,
            "directions": (
                {"wins": 1, "ties": 0, "losses": 3, "mean_chip_delta": 2.0},
                {"wins": 3, "ties": 0, "losses": 1, "mean_chip_delta": -2.0},
            ),
            "params": [12, 34],
        }
        self.assertEqual(
            self.judge("zero-sum", with_directions)["verdict"],
            "pass",
            "a mapping carrying `directions` is read under each direction's "
            "`mean_chip_delta`, not under every number it carries (expectations §2.1): "
            "%r" % (with_directions,),
        )
        three_numbers = {"a": 1, "b": -1, "c": 0}
        record = self.judge("zero-sum", three_numbers)
        self.assertEqual(
            record["verdict"],
            "fail",
            "a record with no `payoffs`, no `directions` and more than two numbers "
            "states no two per-seat deltas (expectations §2.1, G10): %r" % (record,),
        )
        self.assertIn(
            "per-seat",
            record["reason"],
            "the named fact is `the value states no two per-seat chip deltas` "
            "(expectations §2.1): %r" % (record["reason"],),
        )

    def test_hrn_3_5_zero_sum_fails_a_bare_number_and_deltas_that_do_not_balance(self):
        """HRN-3.5 a bare number, a mapping of two numbers that do not sum to zero and a sequence of two numbers that do not each fail, naming the fact (expectations §2.1, G10, surface §6)."""
        for label, value in (
            ("a bare number", 3),
            ("an unbalanced mapping", {"seat 0": 8, "seat 1": -5}),
            ("an unbalanced sequence", [1, -2]),
        ):
            with self.subTest(value=label):
                record = self.judge("zero-sum", value)
                self.assertEqual(
                    record["verdict"],
                    "fail",
                    "%s does not state two deltas that sum to zero (expectations §2.1): "
                    "%r" % (label, record,),
                )
                self.assertIn(
                    "zero-sum",
                    record["reason"],
                    "the failure names the kind (expectations §1): %r"
                    % (record["reason"],),
                )
        unbalanced = self.reason_of("zero-sum", {"seat 0": 8, "seat 1": -5})
        self.assertIn(
            "sum to zero",
            unbalanced,
            "the named fact is `the chip deltas <deltas> do not sum to zero` "
            "(expectations §2.1): %r" % (unbalanced,),
        )

    def test_hrn_3_6_zero_sum_tolerates_a_float_sum_and_still_refuses_a_real_drift(self):
        """HRN-3.6 the tolerance is `abs(sum) <= 1e-9`: a float sum of 5.6e-17 passes, where an exact `== 0` would fail, and a 1e-6 drift fails (expectations §2.1, G10, FAM-7)."""
        float_sum = 0.1 + 0.2 + -0.3
        self.assertNotEqual(
            float_sum,
            0,
            "the battery's own arithmetic: 0.1 + 0.2 - 0.3 is not exactly zero in "
            "binary floating point (%r)" % (float_sum,),
        )
        self.assertLessEqual(
            abs(float_sum),
            1e-9,
            "and it is inside the declared tolerance (%r)" % (float_sum,),
        )
        tolerant_cell = {
            "hands": 3,
            "directions": (
                {"mean_chip_delta": 0.1 + 0.2},
                {"mean_chip_delta": -0.3},
            ),
        }
        self.assertEqual(
            self.judge("zero-sum", tolerant_cell)["verdict"],
            "pass",
            "the tolerance is absolute and not a rounded comparison: a cell's two "
            "directions are each other's negative, so a float sum may land on 1e-17 "
            "(expectations §2.1, G10): %r" % (tolerant_cell,),
        )
        drifted = {"seat 0": 0.500001, "seat 1": -0.5}
        self.assertEqual(
            self.judge("zero-sum", drifted)["verdict"],
            "fail",
            "a drift larger than 1e-9 is not a balanced pair (expectations §2.1): %r"
            % (drifted,),
        )

    # -- refused: the declared flag, never the word --------------------------
    def test_hrn_3_7_refused_reads_the_declared_flag_and_never_the_wording(self):
        """HRN-3.7 `refused` passes `{"refused": True}` and the driver's refusal observation, and fails every record that merely says 'refused' somewhere (expectations §2.4, G11, D-13, L2's H-1)."""
        self.assertEqual(
            self.judge("refused", {"refused": True})["verdict"],
            "pass",
            "the declared flag is the only fact the kind reads (expectations §2.4): "
            "%r" % ({"refused": True},),
        )
        observation = {"refused": True, "error": "InvalidSeed: the seed must be an int"}
        self.assertEqual(
            self.judge("refused", observation)["verdict"],
            "pass",
            "the driver's own refusal observation is exactly the shape this kind reads "
            "(driver §2, expectations §2.4): %r" % (observation,),
        )
        worded = (
            ("an error that says refused", {"error": "refused"}),
            ("a text that says refused", {"text": "the work refused"}),
            ("a flag that says no", {"refused": False}),
            ("a record whose text says refused", {"refused": False, "note": "refused"}),
        )
        for label, value in worded:
            with self.subTest(observation=label):
                record = self.judge("refused", value)
                self.assertEqual(
                    record["verdict"],
                    "fail",
                    "%s is not a declared refusal: the kind reads a flag and not the "
                    "words of a record (expectations §2.4, G11, D-13): %r"
                    % (label, record,),
                )
                self.assertIn(
                    "refused",
                    record["reason"],
                    "the failure names the kind (expectations §1): %r"
                    % (record["reason"],),
                )

    def test_hrn_3_8_refused_fails_a_raised_exception_and_any_non_mapping_value(self):
        """HRN-3.8 `refused` fails an exception handed in as an observation, a bare string, `None` and an episode record that simply returned, because none of them declares the flag (expectations §2.4, G11)."""
        values = (
            ("a raised exception", ValueError("refused")),
            ("the bare word", "refused"),
            ("None", None),
            ("a real episode record", play()),
            ("an opaque object", Opaque()),
        )
        for label, value in values:
            with self.subTest(observation=label):
                record = self.judge("refused", value)
                self.assertEqual(
                    record["verdict"],
                    "fail",
                    "the observed work returned a value rather than refusing, and a "
                    "verdict of refusal depends on a flag and not on which words an "
                    "entry point chose (%s; expectations §2.4, G11): %r"
                    % (label, record,),
                )

    # -- legal-choice --------------------------------------------------------
    def test_hrn_3_9_legal_choice_asks_whether_the_chosen_descriptor_is_one_of_the_legal_ones(self):
        """HRN-3.9 `legal-choice` passes a real decision's action against its own legal set and fails a chosen descriptor outside it or a value stating no legal descriptors (expectations §2.2, surface §6, D-2)."""
        legal = engine().legal_actions(engine().new_hand(SEED_HAND))
        self.assertTrue(
            len(legal),
            "a freshly dealt hand has at least one legal descriptor (engine/surface.md "
            "§6): %r" % (legal,),
        )
        self.assertEqual(
            self.judge("legal-choice", {"chosen": legal[0], "legal": legal})["verdict"],
            "pass",
            "membership is by equality, in the order the value states them "
            "(expectations §2.2): %r" % (legal,),
        )
        decision = play()["decisions"][0]
        self.assertEqual(
            self.judge(
                "legal-choice",
                {"chosen": decision["action"], "legal": decision["legal"]},
            )["verdict"],
            "pass",
            "a real episode record's own decision passes: the work returned one of the "
            "descriptors it was handed (expectations §2.2, records.md §5): %r"
            % (decision,),
        )
        self.assertEqual(
            self.judge(
                "legal-choice", {"chosen": "an-invented-descriptor", "legal": legal}
            )["verdict"],
            "fail",
            "a descriptor outside the legal set is a contract violation and not a fold "
            "(expectations §2.2, D-2): %r" % (legal,),
        )
        for label, value in (
            ("no legal descriptors", {"chosen": legal[0], "legal": []}),
            ("no legal key", {"chosen": legal[0]}),
            ("not a mapping", legal),
        ):
            with self.subTest(observation=label):
                record = self.judge("legal-choice", value)
                self.assertEqual(
                    record["verdict"],
                    "fail",
                    "%s states no legal descriptors and fails (expectations §2.2): %r"
                    % (label, record,),
                )

    def test_hrn_3_10_counted_accounts_for_every_hand_a_cell_reports(self):
        """HRN-3.10 `counted` passes a real cell and a composed cell under either count spelling, fails counts that do not close, and never sums `seat_split` or `mean_chip_delta` (expectations §2.3, records.md §9, protocol §2)."""
        cell = real_cell(hands=4)
        hands = as_number(cell["hands"], "the real cell's hands")
        self.assertEqual(
            self.judge("counted", cell)["verdict"],
            "pass",
            "a real cell's directions account for every hand it reports (expectations "
            "§2.3, records.md §9): %r" % (cell["directions"],),
        )
        plain = {"wins": 2, "ties": 1, "losses": 3}
        composed = {
            "hands": 6,
            "directions": (
                dict(plain),
                dict(plain),
            ),
        }
        self.assertEqual(
            self.judge("counted", composed)["verdict"],
            "pass",
            "wins + ties + losses equal the hands each direction counts "
            "(expectations §2.3): %r" % (composed,),
        )
        singular = {
            "hands": 6,
            "directions": (
                {"win": 2, "tie": 1, "loss": 3},
                {"win": 2, "tie": 1, "loss": 3},
            ),
        }
        self.assertEqual(
            self.judge("counted", singular)["verdict"],
            "pass",
            "the counts are read under either spelling — COUNTS is wins, win, ties, tie, "
            "losses, loss (expectations §2.3): %r" % (singular,),
        )
        with_extra_fields = {
            "hands": 6,
            "directions": (
                {"wins": 2, "ties": 1, "losses": 3, "seat_split": 6, "mean_chip_delta": 0.5},
                {"wins": 3, "ties": 1, "losses": 2, "seat_split": 6, "mean_chip_delta": -0.5},
            ),
        }
        self.assertEqual(
            self.judge("counted", with_extra_fields)["verdict"],
            "pass",
            "only COUNTS' keys are counts: `seat_split`, `mean_chip_delta` and every "
            "other field are never summed (expectations §2.3): %r" % (with_extra_fields,),
        )
        wrong = {"hands": hands + 1, "directions": (dict(plain), dict(plain))}
        record = self.judge("counted", wrong)
        self.assertEqual(
            record["verdict"],
            "fail",
            "six counted outcomes against the wrong number of reported hands do not "
            "close (expectations §2.3): %r" % (record,),
        )
        self.assertIn(
            "counted",
            record["reason"],
            "the failure names the kind (expectations §1): %r" % (record["reason"],),
        )
        for label, value in (
            ("hands with no directions", {"hands": 6}),
            ("directions with no hands", {"directions": (dict(plain),)}),
            ("a bare number", 6),
        ):
            with self.subTest(observation=label):
                self.assertEqual(
                    self.verdict_of("counted", value),
                    "fail",
                    "%s is not a cell record carrying its directions and hands "
                    "(expectations §2.3): %r" % (label, value),
                )

    # -- determinism ---------------------------------------------------------
    def test_hrn_3_11_a_verdict_reads_only_the_value_it_was_handed(self):
        """HRN-3.11 two calls on two equal values give two equal records, and no call mutates the observation (expectations §3, FAM-16.36)."""
        values = {
            "zero-sum": {"seat 0": 4, "seat 1": -4},
            "legal-choice": {"chosen": "fold", "legal": ["fold", "check-call"]},
            "counted": {
                "hands": 3,
                "directions": ({"wins": 1, "ties": 1, "losses": 1},),
            },
            "refused": {"refused": True},
        }
        for kind, value in values.items():
            with self.subTest(kind=kind):
                before = copy.deepcopy(value)
                first = self.judge(kind, value)
                second = self.judge(kind, copy.deepcopy(value))
                self.assertEqual(
                    dict(first),
                    dict(second),
                    "one kind and one observed value give one verdict, in one process "
                    "and across processes (expectations §3, FAM-16.36): %r vs %r"
                    % (dict(first), dict(second)),
                )
                self.assertEqual(
                    value,
                    before,
                    "an expectation reads only the value it was handed and never "
                    "mutates it (expectations §3): %r" % (value,),
                )

    def test_hrn_3_12_each_kind_judges_the_record_its_owner_really_returns(self):
        """HRN-3.12 the four kinds pass the real records they exist for: `engine.play_hand`'s episode, `evaluation.match`'s cell, a real decision's chosen descriptor, and the refusal observation a real `drive` records (expectations §2, surface §6)."""
        episode = play()
        cell = real_cell(hands=4)
        policy = self.ep("seam")(SEAM_RECORDING)
        legal = engine().legal_actions(engine().new_hand(SEED_HAND))
        chosen = policy(readout(), legal)
        refusal = self.ep("drive")(
            {"id": "HRN-3.12-invented-refusal", "steps": [_raiser], "expect": ["refused"]}
        )

        def observation_of(record):
            return record["steps"][0]["outcome"]

        self.assertEqual(
            self.verdict_of("zero-sum", episode),
            "pass",
            "an episode record's payoffs balance (expectations §2.1, ASM-12): %r"
            % (episode["payoffs"],),
        )
        self.assertEqual(
            self.verdict_of("zero-sum", cell),
            "pass",
            "a cell record's two directions balance (expectations §2.1, records.md §9)",
        )
        self.assertEqual(
            self.verdict_of("counted", cell),
            "pass",
            "a cell accounts for every hand it reports (expectations §2.3, protocol §2)",
        )
        self.assertEqual(
            self.verdict_of("legal-choice", {"chosen": chosen, "legal": list(legal)}),
            "pass",
            "a seam returns a member of the legal descriptors it was handed "
            "(expectations §2.2, surface §5, D-2)",
        )
        self.assertEqual(
            refusal["verdict"],
            "pass",
            "the refusal observation a real drive records is judged by `refused` "
            "(driver §2, expectations §2.4): %r" % (refusal,),
        )
        self.assertEqual(
            self.verdict_of("refused", observation_of(refusal)),
            "pass",
            "and the observation is the shape expectations §2.4 reads: %r"
            % (observation_of(refusal),),
        )

    def test_hrn_3_13_zero_sum_fails_a_non_finite_pair_and_still_passes_a_finite_one(self):
        """HRN-3.13 a `NaN` pair, a `+inf`/`-inf` pair and a half-infinite pair each fail `zero-sum` naming the `sum to zero` fact, while `(7, -7)`, the float tolerance pair and a real cell's two `mean_chip_delta`s still pass (expectations §2.1, G10, surface §6)."""
        non_finite = (
            ("a NaN tuple", (float("nan"), float("nan"))),
            ("a NaN list", [float("nan"), float("nan")]),
            ("a NaN mapping", {"seat 0": float("nan"), "seat 1": float("nan")}),
            ("an infinite tuple", (float("inf"), float("-inf"))),
            ("an infinite mapping", {"seat 0": float("inf"), "seat 1": float("-inf")}),
            ("a half-infinite tuple", (float("inf"), 5)),
        )
        for label, value in non_finite:
            with self.subTest(value=label):
                record = self.judge("zero-sum", value)
                self.assertEqual(
                    record["verdict"],
                    "fail",
                    "%s does not balance: `NaN + NaN` and `+inf + (-inf)` sum to a "
                    "non-finite number, and the pass predicate `abs(sum) <= 1e-9` is "
                    "evaluated and never negated (expectations §2.1, G10): %r"
                    % (label, record,),
                )
                self.assertIn(
                    "zero-sum",
                    record["reason"],
                    "the failure names the kind (expectations §1): %r"
                    % (record["reason"],),
                )
                self.assertIn(
                    "sum to zero",
                    record["reason"],
                    "and the fact it names is `the chip deltas <deltas> do not sum to "
                    "zero`, which a non-finite pair gets too (expectations §2.1, G10): %r"
                    % (record["reason"],),
                )
        for label, value in (
            ("two integers", (7, -7)),
            ("the float tolerance pair", [0.1 + 0.2, -0.3]),
        ):
            with self.subTest(value=label):
                self.assertEqual(
                    self.verdict_of("zero-sum", value),
                    "pass",
                    "%s balances inside the 1e-9 tolerance, so the non-finite refusal is "
                    "not a blanket one (expectations §2.1, G10, surface §6): %r"
                    % (label, value),
                )
        cell = real_cell(hands=4)
        deltas = [
            as_number(row["mean_chip_delta"], "a direction's mean_chip_delta")
            for row in cell["directions"]
        ]
        self.assertEqual(
            len(deltas),
            2,
            "a real cell carries one mean_chip_delta per direction (records.md §9): %r"
            % (cell["directions"],),
        )
        self.assertEqual(
            self.verdict_of("zero-sum", deltas),
            "pass",
            "and its two means, which are each other's negative, still pass (expectations "
            "§2.1, G10): %r" % (deltas,),
        )

    def test_hrn_3_14_refused_reads_a_boolean_flag_and_never_a_merely_true_value(self):
        """HRN-3.14 `{"refused": "yes"}`, `{"refused": 1}`, `{"refused": [0]}` and `{"refused": "False"}` each fail `refused` naming the kind, while the boolean `True` and the refusal observation a real `drive` builds pass (expectations §2.4, G11, surface §6)."""
        for label, value in (
            ("a string flag", {"refused": "yes"}),
            ("a numeric flag", {"refused": 1}),
            ("a list flag", {"refused": [0]}),
            ("the string False", {"refused": "False"}),
        ):
            with self.subTest(flag=label):
                record = self.judge("refused", value)
                self.assertEqual(
                    record["verdict"],
                    "fail",
                    "%s is a true value and not the boolean `True`: the kind reads a "
                    "declared flag, and a flag is a boolean (expectations §2.4, G11): %r"
                    % (label, record,),
                )
                self.assertIn(
                    "refused",
                    record["reason"],
                    "the failure names the kind verbatim (expectations §1): %r"
                    % (record["reason"],),
                )
        self.assertEqual(
            self.verdict_of("refused", {"refused": True}),
            "pass",
            "the flag that is the boolean `True` is the declared refusal (expectations "
            "§2.4, G11): %r" % ({"refused": True},),
        )
        driven = self.ep("drive")(
            {"id": "HRN-3.14-invented-refusal", "steps": [_raiser], "expect": ["refused"]}
        )
        observation = as_mapping(
            driven["steps"][0]["outcome"],
            "the refusal observation a real drive builds",
        )
        self.assertIs(
            observation.get("refused"),
            True,
            "the driver declares the flag as the boolean `True`, because that is the fact "
            "this kind reads (driver §2, expectations §2.4): %r" % (observation,),
        )
        self.assertEqual(
            self.verdict_of("refused", observation),
            "pass",
            "so the refusal observation a real drive records passes, beside a merely "
            "truthy flag that fails (driver §2, expectations §2.4, G11): %r"
            % (observation,),
        )
        self.assertEqual(
            self.verdict_of("refused", {"refused": "yes"}),
            "fail",
            "while `{'refused': 'yes'}` beside it is not a declared refusal, whatever "
            "the observation was (expectations §2.4, G11, surface §6): %r"
            % (observation,),
        )

    # -- zero-sum: a cell-shaped value whose means are not quantities ---------
    def test_hrn_3_15_a_cell_shaped_value_whose_means_are_not_quantities_is_a_named_failure(
        self,
    ):
        """HRN-3.15 a cell-shaped value whose `mean_chip_delta`s are a string, a `None` or a boolean beside a number fails `zero-sum` naming `per-seat`, raises nothing, and `drive` reports the failure at its step instead of raising out of its judging pass (expectations §2.1 item 2, §2.5, §3, G9, G10, surface §6)."""
        unreadable = (
            (
                "a string mean",
                "string-mean",
                {
                    "directions": [
                        {"mean_chip_delta": "x"},
                        {"mean_chip_delta": 0},
                    ],
                    "hands": 4,
                },
            ),
            (
                "a None mean",
                "none-mean",
                {
                    "directions": [
                        {"mean_chip_delta": None},
                        {"mean_chip_delta": 0},
                    ],
                    "hands": 4,
                },
            ),
            (
                "a boolean mean beside a number",
                "boolean-mean",
                {
                    "directions": [
                        {"mean_chip_delta": True},
                        {"mean_chip_delta": -1},
                    ],
                    "hands": 4,
                },
            ),
        )
        for label, slug, value in unreadable:
            # The two edges of one reader, each pinned on its own subtest: §6's Total
            # rule breaks at `expect` (no verdict at all) and at `drive` (a raise out of
            # the judging pass, which runs outside the step's own `try`), and one red
            # subtest per edge says which way the reader is partial (expectations §2.5,
            # §3, G9).
            with self.subTest(path="expect", value=label):
                # `judge`'s assertion set with the call inside the control: `_deltas`
                # must drop the means `_quantity` cannot read, so a bare `TypeError` out
                # of `sum` reads as "must not raise", never as an opaque error
                # (expectations §2.5, §3, G9).
                record = self.not_raised(
                    lambda handed=value: self.ep("expect")("zero-sum", handed),
                    "expect('zero-sum', a cell record whose means are %s) must return one "
                    "verdict record and must never raise (expectations §2.5, §3, G9)"
                    % (label,),
                )
                record = self.assert_verdict_record(record, "zero-sum")
                self.assertEqual(
                    record["verdict"],
                    "fail",
                    "a %s is not a quantity, so the cell states no two per-seat chip "
                    "deltas: a recognised shape read into fewer than two deltas is a "
                    "named failure and never a pass (expectations §2.1 item 2, §2.5, "
                    "G9, G10): %r" % (label, record),
                )
                self.assertIn(
                    "zero-sum",
                    record["reason"],
                    "and the failure names the kind verbatim (expectations §1): %r"
                    % (record["reason"],),
                )
                self.assertIn(
                    "per-seat",
                    record["reason"],
                    "the fact it names is `the value states no two per-seat chip "
                    "deltas`, because a mean `_quantity` cannot read is dropped before "
                    "§2.1 counts the pair (expectations §2.1 item 2, §2.5, G10): %r"
                    % (record["reason"],),
                )
            with self.subTest(path="drive", value=label):
                driven = self.not_raised(
                    lambda handed=value, name="HRN-3.15-invented-" + slug: self.ep(
                        "drive"
                    )(case(name, [pure_value(handed)], ["zero-sum"])),
                    "drive(...) on a case whose step returned a cell record whose means "
                    "are %s must never raise: judging runs on the step's own outcome "
                    "(expectations §3, §2.5, G9)" % (label,),
                )
                driven = as_mapping(
                    driven, "the case record a drive returned for a %s" % (label,)
                )
                self.assertEqual(
                    driven["verdict"],
                    "fail",
                    "the case fails, because the expectation it rests on failed "
                    "(driver §3, expectations §3): %r" % (driven,),
                )
                reason = driven["reason"]
                self.assertIsInstance(
                    reason,
                    str,
                    "a failed case states one sentence in `reason` (driver §3): %r"
                    % (reason,),
                )
                self.assertTrue(
                    reason.startswith("harness.drive failed step 0:"),
                    "the failure is attributed to step 0, the step whose outcome the "
                    "expectation judged (driver §3, expectations §2.1): %r" % (reason,),
                )
                self.assertIn(
                    "zero-sum",
                    reason,
                    "and the sentence carries the kind that failed (expectations §1, "
                    "driver §3): %r" % (reason,),
                )
                self.assertIn(
                    "per-seat",
                    reason,
                    "and the fact the kind could not read, so an unreadable %s mean "
                    "reaches the named failure and not a raise out of `drive`'s judging "
                    "pass (expectations §2.1 item 2, §2.5, §3, G9): %r"
                    % (label, reason),
                )
                entries = as_sequence(
                    driven["expectations"], "the expectations a real drive recorded"
                )
                self.assertEqual(
                    len(entries),
                    1,
                    "exactly one expectation entry is recorded, so the failure is "
                    "attributed to the expectation and not to a malformed case "
                    "(driver §3): %r" % (driven,),
                )
                entry = as_mapping(
                    entries[0], "the one expectation entry a real drive recorded"
                )
                self.assertEqual(
                    entry["step"],
                    0,
                    "and the entry names step 0 (driver §3): %r" % (entry,),
                )
                self.assertEqual(
                    entry["verdict"],
                    "fail",
                    "recording the failed verdict rather than no verdict at all "
                    "(expectations §1, driver §3): %r" % (entry,),
                )

    def test_hrn_3_16_the_cell_shaped_values_that_keep_passing_and_the_pair_a_filter_counts(
        self,
    ):
        """HRN-3.16 a real cell's two quantities and a composed cell's finite zero-sum pair still pass `zero-sum`, while a cell-shaped value with one readable mean and one unreadable one reads one delta and fails naming `per-seat` — so the quantity filter drops nothing a cell really states and keeps the count that makes a pair (expectations §2.1 item 2, §2.5, G10, surface §6)."""
        cell = as_mapping(real_cell(hands=4), "the real cell evaluation.match returned")
        rows = as_sequence(cell["directions"], "the real cell's directions")
        self.assertEqual(
            len(rows),
            2,
            "the control: a cell record carries one direction per seat, so two means "
            "are on offer (records.md §9, expectations §2.1): %r"
            % (cell["directions"],),
        )
        means = [
            as_number(
                as_mapping(row, "one direction of the real cell")["mean_chip_delta"],
                "a direction's mean_chip_delta, which must be a quantity",
            )
            for row in rows
        ]
        self.assertEqual(
            len(means),
            2,
            "both means of a real cell are quantities, so `_quantity` keeps both "
            "(expectations §2.1 item 2, §2.5): %r" % (means,),
        )
        self.assertLessEqual(
            abs(sum(means)),
            1e-9,
            "and they are each other's negative, which is why the cell passes at all "
            "(expectations §2.1, G10): %r" % (means,),
        )
        self.assertEqual(
            self.verdict_of("zero-sum", cell),
            "pass",
            "so a real `evaluation.match` cell keeps passing: the filter drops nothing "
            "a cell states as a quantity (expectations §2.1 item 2, §2.5, records.md "
            "§9): %r" % (means,),
        )
        composed = {
            "hands": 3,
            "directions": (
                {"mean_chip_delta": 0.1 + 0.2},
                {"mean_chip_delta": -0.3},
            ),
        }
        self.assertEqual(
            self.verdict_of("zero-sum", composed),
            "pass",
            "a composed cell whose two means are a finite pair summing inside the "
            "declared tolerance still passes, because both are quantities (expectations "
            "§2.1 item 2, §2.5, G10): %r" % (composed,),
        )
        half_readable = {
            "directions": [
                {"mean_chip_delta": 5.0},
                {"mean_chip_delta": "x"},
            ],
            "hands": 4,
        }
        record = self.not_raised(
            lambda: self.ep("expect")("zero-sum", half_readable),
            "expect('zero-sum', a cell-shaped value with one readable mean and one "
            "unreadable one) must count the one delta it read and name the fact; it must "
            "never raise (expectations §2.1 item 2, §2.5, G9)",
        )
        record = self.assert_verdict_record(record, "zero-sum")
        self.assertEqual(
            record["verdict"],
            "fail",
            "one readable mean and one unreadable one is one delta and not a pair: "
            "§2.1's count is what the filter leaves, so the value fails rather than "
            "passing on a mean it never read (expectations §2.1 item 2, §2.5, G10): %r"
            % (record,),
        )
        self.assertIn(
            "per-seat",
            record["reason"],
            "and the fact it names is `the value states no two per-seat chip deltas` "
            "(expectations §2.1 item 2, §2.5): %r" % (record["reason"],),
        )

    # -- totality: the values whose reader arithmetic raises -----------------
    def test_hrn_3_17_zero_sum_on_a_huge_integer_beside_a_float_is_a_named_failure(self):
        """HRN-3.17 `zero-sum` on a delta pair mixing `10**999` with a float fails by name in all four §2.1 shapes and in both orders, carrying the class of the exception that same `sum` raises out of the one guard in `expect` (expectations §2.1, §3, G9, surface §6)."""
        huge = 10 ** 999
        orders = (
            ("the huge integer first", (huge, 1.5)),
            ("the float first", (1.5, huge)),
        )
        for order, pair in orders:
            # `sum` cannot add a 1000-digit integer to a float, so §2.1's *own* expression
            # raises and the pair is never even compared with the tolerance.  The class is
            # computed from that arithmetic and never hardcoded: §3 keeps a genuine bug
            # inside a reader visible by carrying the exception's class in the reason
            # (expectations §2.1, §3, G9).
            reader_class = _sum_class(
                list(pair),
                "sum of the mixed huge-integer/float pair the `zero-sum` reader sums",
            )
            shapes = (
                (
                    "an episode-shaped mapping",
                    "episode",
                    {"payoffs": pair, "decisions": ()},
                ),
                (
                    "a cell-shaped mapping",
                    "cell",
                    {
                        "directions": [
                            {"mean_chip_delta": pair[0]},
                            {"mean_chip_delta": pair[1]},
                        ],
                        "hands": 4,
                    },
                ),
                (
                    "a mapping of two per-seat numbers",
                    "per-seat",
                    {"seat 0": pair[0], "seat 1": pair[1]},
                ),
                ("a sequence", "sequence", [pair[0], pair[1]]),
            )
            for shape_label, shape, value in shapes:
                with self.subTest(shape=shape, order=order):
                    record = self.not_raised(
                        lambda handed=value: self.ep("expect")("zero-sum", handed),
                        "expect('zero-sum', %s with %s) must return one verdict record "
                        "and must never raise: §6's Total rule makes a value the kind "
                        "cannot read a named failure and never a silence (expectations "
                        "§2.1, §3, G9, surface §6)" % (shape_label, order),
                    )
                    record = self.assert_verdict_record(record, "zero-sum")
                    self.assertEqual(
                        record["verdict"],
                        "fail",
                        "the reader's own `sum` cannot add the pair with %s, so it never "
                        "reaches the tolerance and balances nothing: a value a kind cannot "
                        "read is a named failure and never a pass (expectations §2.1, §3, "
                        "G9): %r" % (order, record["verdict"],),
                    )
                    self.assertIn(
                        "zero-sum",
                        record["reason"],
                        "the failure names the kind verbatim (expectations §1, §3): %r"
                        % (record["reason"],),
                    )
                    self.assertIn(
                        "could not be read",
                        record["reason"],
                        "and it is the one guard in `expect`, whose sentence is "
                        "`harness.expect failed the kind '<kind>': the value could not be "
                        "read: <Class>: <message>` (expectations §3, surface §6): %r"
                        % (record["reason"],),
                    )
                    self.assertIn(
                        reader_class,
                        record["reason"],
                        "the reason carries the class of the exception the reader's own "
                        "arithmetic raises (%s), so a genuine bug inside a reader stays "
                        "visible in the verdict instead of vanishing (expectations §3, "
                        "G9): %r" % (reader_class, record["reason"],),
                    )

    def test_hrn_3_18_counted_on_a_cell_whose_counts_mix_a_huge_integer_and_a_float(self):
        """HRN-3.18 `counted` on a cell whose one direction's counts mix `10**999` with a float fails by name, carrying the class that same `sum` raises, inside the one guard in `expect` (expectations §2.3, §3, G9, surface §6)."""
        huge = 10 ** 999
        # The counts a direction states are summed, so a 1000-digit integer beside a float
        # is a raise out of §2.3's own expression and not a value the kind can read —
        # whichever key the huge integer sits under (expectations §2.3, §3, G9).
        reader_class = _sum_class(
            [huge, 1.5],
            "sum of the mixed huge-integer/float counts the `counted` reader sums",
        )
        mixed = (
            (
                "the huge integer under wins",
                "huge-wins",
                (
                    {"wins": huge, "ties": 1.5, "losses": 0},
                    {"wins": 4, "ties": 0, "losses": 0},
                ),
            ),
            (
                "the huge integer under losses",
                "huge-losses",
                (
                    {"wins": 3, "ties": 1.5, "losses": huge},
                    {"wins": 4, "ties": 0, "losses": 0},
                ),
            ),
        )
        for label, slug, directions in mixed:
            value = {"hands": 4, "directions": directions}
            with self.subTest(value=slug):
                record = self.not_raised(
                    lambda handed=value: self.ep("expect")("counted", handed),
                    "expect('counted', a cell record with %s) must return one verdict "
                    "record and must never raise: a cell the kind cannot read is a named "
                    "failure (expectations §2.3, §3, G9, surface §6)" % (label,),
                )
                record = self.assert_verdict_record(record, "counted")
                self.assertEqual(
                    record["verdict"],
                    "fail",
                    "with %s the reader's `sum` cannot count the direction at all, so "
                    "the cell does not close: a value a kind cannot read is a named "
                    "failure and never a pass (expectations §2.3, §3, G9): %r"
                    % (label, record["verdict"],),
                )
                self.assertIn(
                    "counted",
                    record["reason"],
                    "the failure names the kind verbatim (expectations §1, §3): %r"
                    % (record["reason"],),
                )
                self.assertIn(
                    "could not be read",
                    record["reason"],
                    "and it is the one guard in `expect`, whose sentence is "
                    "`harness.expect failed the kind '<kind>': the value could not be "
                    "read: <Class>: <message>` (expectations §3, surface §6): %r"
                    % (record["reason"],),
                )
                self.assertIn(
                    reader_class,
                    record["reason"],
                    "the reason carries the class of the exception the reader's own "
                    "arithmetic raises (%s), so a genuine bug inside a reader stays "
                    "visible in the verdict instead of vanishing (expectations §3, G9): "
                    "%r" % (reader_class, record["reason"],),
                )

    def test_hrn_3_19_legal_choice_when_a_descriptor_equality_is_not_a_boolean(self):
        """HRN-3.19 `legal-choice` on a chosen descriptor whose `==` raises and on one whose `==` is a non-boolean that will not coerce fails by name carrying that exception's class, while a falsy comparison `any(...)` can coerce stays a plain failure (expectations §2.2, §3, G9, surface §6)."""
        # Membership is decided by `chosen == candidate` inside `any(...)`, so a descriptor
        # that answers the comparison with a raise — or with something `any` cannot coerce
        # to a truth value — is a value §2.2's reader cannot read.  Both are invented here
        # because neither needs numpy and the battery carries no dependency (G2).
        hostile = (
            ("a descriptor whose == raises", "raising", RaisingEquality()),
            (
                "a descriptor whose == is not a boolean",
                "unboolable",
                UnboolableEquality(),
            ),
        )
        legal = list(LEGAL_DESCRIPTORS)
        for label, slug, chosen in hostile:
            value = {"chosen": chosen, "legal": legal}
            with self.subTest(observation=slug):
                comparison_class = _comparison_class(chosen)
                record = self.not_raised(
                    lambda handed=value: self.ep("expect")("legal-choice", handed),
                    "expect('legal-choice', %s) must return one verdict record and must "
                    "never raise: a comparison the kind cannot make is a named failure "
                    "and never a silence (expectations §2.2, §3, G9, surface §6)"
                    % (label,),
                )
                record = self.assert_verdict_record(record, "legal-choice")
                self.assertEqual(
                    record["verdict"],
                    "fail",
                    "membership by equality is unanswerable for %s, so the chosen "
                    "descriptor is not shown to be one of the legal ones, and an "
                    "unreadable value is a failure rather than a pass (expectations "
                    "§2.2, §3, G9): %r" % (label, record["verdict"],),
                )
                self.assertIn(
                    "legal-choice",
                    record["reason"],
                    "the failure names the kind verbatim (expectations §1, §3): %r"
                    % (record["reason"],),
                )
                self.assertIn(
                    "could not be read",
                    record["reason"],
                    "and it is the one guard in `expect`, whose sentence is "
                    "`harness.expect failed the kind '<kind>': the value could not be "
                    "read: <Class>: <message>` (expectations §3, surface §6): %r"
                    % (record["reason"],),
                )
                self.assertIn(
                    comparison_class,
                    record["reason"],
                    "the reason carries the class of the exception that comparison "
                    "raises (%s), so a genuine bug inside a reader stays visible in the "
                    "verdict instead of vanishing (expectations §3, G9): %r"
                    % (comparison_class, record["reason"],),
                )
        # The documented control: a comparison the reader *can* coerce is not turned into
        # a raise and not into a pass by the guard.  `[]` is falsy, so `any(...)` answers
        # false and §2.2's own fact — the chosen descriptor is outside the legal set — is
        # what the verdict states, which is why this value needs no guard at all
        # (expectations §2.2, §3, G9).
        coercible = {"chosen": CoercibleEquality(), "legal": legal}
        record = self.not_raised(
            lambda: self.ep("expect")("legal-choice", coercible),
            "expect('legal-choice', a chosen descriptor whose == is a falsy list) must "
            "return one verdict record and must never raise (expectations §2.2, §3, G9)",
        )
        record = self.assert_verdict_record(record, "legal-choice")
        self.assertEqual(
            record["verdict"],
            "fail",
            "a comparison `any(...)` can coerce is not turned into a raise or a pass by "
            "the guard: `[]` is falsy, so the reader's own predicate answers and the "
            "descriptor is outside the legal set (expectations §2.2, §3, G9): %r"
            % (record["verdict"],),
        )
        self.assertIn(
            "outside the legal set",
            record["reason"],
            "the control states §2.2's own fact, so a coercible comparison reaches the "
            "reader's predicate and not the guard (expectations §2.2, §3): %r"
            % (record["reason"],),
        )
        self.assertNotIn(
            "could not be read",
            record["reason"],
            "so the guard never fires for a comparison the reader can coerce: the fix is "
            "not a blanket refusal of odd values (expectations §3, G9): %r"
            % (record["reason"],),
        )

    def test_hrn_3_20_drive_judges_each_hostile_value_as_a_named_failure_and_never_raises(self):
        """HRN-3.20 `drive` reports each hostile value as a named failure at step 0 rather than raising out of its judging pass, for `zero-sum`, `counted` and `legal-choice` (expectations §3, G9, driver §2, §3, surface §2, §6)."""
        huge = 10 ** 999
        hostile = (
            ("zero-sum", "mixed-pair", (huge, 1.5)),
            (
                "zero-sum",
                "mixed-episode",
                {"payoffs": (huge, 1.5), "decisions": ()},
            ),
            (
                "zero-sum",
                "mixed-cell",
                {
                    "directions": [
                        {"mean_chip_delta": huge},
                        {"mean_chip_delta": 1.5},
                    ],
                    "hands": 4,
                },
            ),
            ("zero-sum", "mixed-per-seat", {"seat 0": 1.5, "seat 1": huge}),
            (
                "counted",
                "mixed-counts",
                {
                    "hands": 4,
                    "directions": (
                        {"wins": huge, "ties": 1.5, "losses": 0},
                        {"wins": 4, "ties": 0, "losses": 0},
                    ),
                },
            ),
            (
                "legal-choice",
                "raising-equality",
                {"chosen": RaisingEquality(), "legal": ["fold"]},
            ),
            (
                "legal-choice",
                "unboolable-equality",
                {"chosen": UnboolableEquality(), "legal": ["fold"]},
            ),
        )
        for kind, slug, value in hostile:
            # This is the edge that made the defect a *class* rather than an instance:
            # `drive` judges after the per-step `try`, so a raise out of `expect` is a
            # raise out of `drive` and out of every case that judges a value — one guard,
            # in `expect`, is the only place the rule can hold (expectations §3, driver
            # §2, §3, G9).
            with self.subTest(kind=kind, value=slug):
                driven = self.not_raised(
                    lambda handed=value, name="HRN-3.20-invented-" + slug, wanted=kind: (
                        self.ep("drive")(case(name, [pure_value(handed)], [wanted]))
                    ),
                    "drive(...) on a case whose step returned the hostile value %r must "
                    "never raise: the judging pass runs outside the step's own `try`, so "
                    "a reader's exception escapes the driver (expectations §3, driver "
                    "§2, §3, G9)" % (slug,),
                )
                driven = as_mapping(
                    driven, "the case record a drive returned for %s" % (slug,)
                )
                self.assertEqual(
                    driven["verdict"],
                    "fail",
                    "the case fails, because the one expectation it rests on failed "
                    "(driver §3, expectations §3): %r" % (driven["verdict"],),
                )
                reason = driven["reason"]
                self.assertIsInstance(
                    reason,
                    str,
                    "a failed case states one sentence in `reason` (driver §3, §4): %r"
                    % (reason,),
                )
                self.assertTrue(
                    reason.startswith("harness.drive failed step 0:"),
                    "the failure is attributed to step 0, the step whose outcome the "
                    "expectation judged (driver §3): %r" % (reason,),
                )
                self.assertIn(
                    kind,
                    reason,
                    "and the sentence carries the kind that failed, because the driver "
                    "adds no second judging rule (driver §2, §3, expectations §1): %r"
                    % (reason,),
                )
                entries = as_sequence(
                    driven["expectations"], "the expectations a real drive recorded"
                )
                self.assertEqual(
                    len(entries),
                    1,
                    "exactly one expectation entry is recorded, so the failure is "
                    "attributed to the expectation and not to a malformed case "
                    "(driver §3): %r" % (driven["expectations"],),
                )
                entry = as_mapping(
                    entries[0], "the one expectation entry a real drive recorded"
                )
                self.assertEqual(
                    entry["step"],
                    0,
                    "and the entry names step 0 (driver §3): %r" % (entry["step"],),
                )
                self.assertEqual(
                    entry["verdict"],
                    "fail",
                    "recording the failed verdict rather than no verdict at all "
                    "(expectations §1, driver §3): %r" % (entry["verdict"],),
                )

    def test_hrn_3_21_the_huge_and_finite_pairs_that_keep_passing(self):
        """HRN-3.21 `zero-sum` still passes an exactly-balancing huge integer pair in all four shapes and a composed finite pair, and `counted` still passes a cell whose counts close at a huge integer, so the guard is no blanket refusal of big or odd numbers (expectations §2.1, §2.3, §3, G9, G10, surface §6)."""
        huge = 10 ** 999
        shapes = (
            ("an episode-shaped mapping", {"payoffs": (huge, -huge), "decisions": ()}),
            (
                "a cell-shaped mapping",
                {
                    "directions": [
                        {"mean_chip_delta": huge},
                        {"mean_chip_delta": -huge},
                    ],
                    "hands": 4,
                },
            ),
            ("a mapping of two per-seat numbers", {"seat 0": huge, "seat 1": -huge}),
            ("a sequence", [huge, -huge]),
        )
        for shape_label, value in shapes:
            with self.subTest(shape=shape_label):
                record = self.not_raised(
                    lambda handed=value: self.ep("expect")("zero-sum", handed),
                    "expect('zero-sum', %s whose two deltas are %s and its negation) "
                    "must return one verdict record: a pair of integers is a value the "
                    "kind reads (expectations §2.1, §3, G9)" % (shape_label, "10**999"),
                )
                record = self.assert_verdict_record(record, "zero-sum")
                self.assertEqual(
                    record["verdict"],
                    "pass",
                    "both deltas are integers, so `sum` stays an exact `int` and never "
                    "converts to `float`, and `abs(0) <= 1e-9` is true — which is why "
                    "this pair passes where `(10**999, 1.5)` does not: the reader's own "
                    "predicate already handles an exact big pair, so no nearest finite "
                    "pair needs inventing (expectations §2.1, §3, G9, G10): %s"
                    % (shape_label,),
                )
        huge_cell = {
            "hands": huge,
            "directions": ({"wins": huge, "ties": 0, "losses": 0},),
        }
        self.assertEqual(
            self.verdict_of("counted", huge_cell),
            "pass",
            "the counts close at the huge integer too: every term is an `int`, so the "
            "direction's sum is exact and equals the `hands` the cell reports "
            "(expectations §2.3, §3, G9, G10): the huge-cell control",
        )
        cell = real_cell(hands=4)
        self.assertEqual(
            self.verdict_of("zero-sum", cell),
            "pass",
            "a real `evaluation.match` cell keeps passing `zero-sum` (expectations §2.1, "
            "records.md §9): %r" % (cell["directions"],),
        )
        self.assertEqual(
            self.verdict_of("counted", cell),
            "pass",
            "and keeps passing `counted`, so the guard changes no real record "
            "(expectations §2.3, records.md §9): %r" % (cell["hands"],),
        )
        tolerance = {"seat 0": 0.1 + 0.2, "seat 1": -0.3}
        self.assertEqual(
            self.verdict_of("zero-sum", tolerance),
            "pass",
            "and the composed finite tolerance pair still passes, so the guard is not a "
            "refusal of floats either (expectations §2.1, G10): %r" % (tolerance,),
        )
        self.assertEqual(
            self.verdict_of("zero-sum", [7, -7]),
            "pass",
            "and the plain integer pair that shipped from the first day still passes "
            "(expectations §2.1, G10): %r" % ([7, -7],),
        )


if __name__ == "__main__":
    unittest.main()
