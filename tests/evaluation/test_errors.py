"""EVL-9 — the refusal hierarchy and the message grammar.

Drives `docs/L3/evaluation/errors.md` §1-§6: one `EvaluationError` base and the
forty-five subclasses of §2 -- D-19's, D-20's, D-21's, D-29's and D-33's included, so the
three shape classes `UnknownShape`, `ShapeMismatch` and `UnknownExploration` and the
three seat-count classes `InvalidDrawCount`, `DrawExceedsMembership` and
`SeatCountExceeded` are driven from this file beside the rest (`shape.md` §3, §5,
`seats.md` §2-§5), each reachable from the refusal the L2 surface
declares for it; the message grammar of §3 -- `"<entry>(<argument or field>): <the
violated contract>, got <what was passed>"` -- so the message names the entry point,
the argument or key at fault and the offending value; the canonical spellings of §4
matched tolerantly (the entry point's name, the field's name and the value, never a
sentence copied from the table); and §5's other direction, that a valid instance is
*not* refused.

`README.md` §4 declares the class hierarchy contract for this battery ("`errors.py`
EvaluationError and its subclasses (errors.md §2)"), so EVL-9.1 and EVL-9.2 are the
one place this battery asserts a subclass by name. `errors.md` §2's closing rule --
"A battery asserts the *behaviour* ... never the class" -- is honoured everywhere else:
every other file of this battery asserts `EvaluationError` as the root and the message
at fault, never which subclass arrived.
"""

import copy
import unittest

from _evaluation_support import (
    BASELINES,
    HANDS_PER_CELL,
    OPPONENT_SEEDS,
    OTHER_RULE,
    OTHER_UTILITY,
    START_LABEL,
    VERSION_IDS,
    EvaluationCase,
    balanced,
    checkpoint_with_unknown_encoding,
    checkpoint_without_seed,
    declaration,
    direction,
    errors_module,
    file_that_is_not_a_checkpoint,
    first_legal,
    hand_matrix,
    header_record,
    lopsided,
    matrix_cells,
    matrix_member_ids,
    other_shape,
    probe_readouts,
    rating_entries,
    rating_record,
    report_inputs,
    run_record,
    six_seat_shape,
    version_chain,
    version_record,
)

#: The forty-five subclasses `errors.md` §2 declares, in the order it lists them.
DECLARED_CLASSES = (
    "InvalidPool",
    "PoolDeclarationInvalid",
    "PoolBoundInvalid",
    "MemberInvalid",
    "MemberUnloadable",
    "MemberDuplicate",
    "LineageConflict",
    "LineageCycle",
    "PoolFrozen",
    "LineageNotExtended",
    "UnknownRule",
    "UnknownUtility",
    "UnknownBaseline",
    "UnknownShape",
    "RuleMismatch",
    "UtilityMismatch",
    "ShapeMismatch",
    "FamilyBoundExceeded",
    "PoolNotFrozen",
    "InvalidSeed",
    "InvalidDrawCount",
    "DrawExceedsMembership",
    "SeatCountExceeded",
    "InvalidHandCount",
    "SameMemberPair",
    "VariantCountInvalid",
    "VariantInvalid",
    "UnknownTable",
    "InvalidMembership",
    "InvalidMatrix",
    "MissingMatrixKey",
    "CellCountMismatch",
    "DuplicatePair",
    "ForeignMember",
    "UnevenCell",
    "MissingBaseline",
    "CheckpointUnreadable",
    "CheckpointRecordMissing",
    "UnknownEncoding",
    "UnknownExploration",
    "MissingFamily",
    "MembershipMismatch",
    "RatingMismatch",
    "HeaderIncomplete",
    "InvalidArgument",
)


class ErrorsTest(EvaluationCase):
    def test_evl_9_1_the_declared_hierarchy_exists(self):
        """EVL-9.1 `src/evaluation/errors.py` declares `EvaluationError` and the forty-five subclasses `errors.md` §2 names -- `UnknownShape`, `ShapeMismatch` and `UnknownExploration` among them -- each a distinct subclass of that base (`errors.md` §2, `README.md` §3-§4, G16)."""
        module = errors_module()
        root = getattr(module, "EvaluationError", None)
        self.assertTrue(
            isinstance(root, type) and issubclass(root, Exception),
            "errors.md §2 declares EvaluationError the base of every refusal of this "
            "module, and a caller catches it to know that this module refused: %r"
            % (root,),
        )
        seen = set()
        for name in DECLARED_CLASSES:
            with self.subTest(error=name):
                candidate = getattr(module, name, None)
                self.assertTrue(
                    isinstance(candidate, type),
                    "errors.md §2 declares the class %r under EvaluationError "
                    "(README.md §4): %r" % (name, candidate),
                )
                self.assertTrue(
                    issubclass(candidate, root),
                    "%r is a subclass of EvaluationError, so one catch finds every "
                    "refusal of this module (errors.md §2): %r" % (name, candidate),
                )
                self.assertNotEqual(
                    candidate,
                    root,
                    "%r is a subclass and not the base itself (errors.md §2): %r"
                    % (name, candidate),
                )
                self.assertNotIn(
                    candidate,
                    seen,
                    "the forty-five classes are one per refusal family, and %r is a "
                    "second name for one already declared (errors.md §2): %r"
                    % (name, candidate),
                )
                seen.add(candidate)
        self.assertEqual(
            len(seen),
            len(DECLARED_CLASSES),
            "errors.md §2 declares forty-five distinct subclasses under one base: %r"
            % (len(seen),),
        )

    def test_evl_9_2_every_declared_class_is_reachable_from_its_refusal(self):
        """EVL-9.2 each of `errors.md` §2's forty-five classes is reachable from the refusal `surface.md` §5-§13 declares for it -- the three shape classes included -- so the hierarchy names what a caller can route on (`errors.md` §2, `guardrails.md` G16)."""
        module = errors_module()
        for name, label, fn, args in self.provocations():
            with self.subTest(error=name, case=label):
                try:
                    value = fn(*args)
                except Exception as exc:
                    self.assertIsInstance(
                        exc,
                        getattr(module, name),
                        "%s is refused with %r by errors.md §2 (got %s): %r"
                        % (label, name, type(exc).__name__, exc),
                    )
                else:
                    self.fail(
                        "%s accepted %r, and errors.md §2 declares %r for that refusal"
                        % (label, value, name)
                    )

    def provocations(self):
        """One provoking call per class of `errors.md` §2, in its order."""
        package = self.evaluation()
        matrix = hand_matrix(balanced)
        rating = rating_record(matrix)
        cells = list(matrix_cells(matrix))
        missing_key = dict(matrix)
        missing_key.pop("hands_per_cell")
        five_cells = dict(matrix, cells=tuple(cells[:5]))
        repeated = list(cells)
        repeated[-1] = cells[0]
        foreign = list(cells)
        foreign[0] = dict(cells[0], members=("random", "version-ghost-5599"))
        uneven = list(cells)
        uneven[0] = dict(cells[0], hands=1)
        no_baseline = hand_matrix(balanced, members=("random", "always-call", "variant-1"))
        wide = hand_matrix(
            balanced, members=BASELINES + ("variant-1", "variant-2", "version-outsider-9901")
        )
        frozen = package.build_pool(declaration(members=(), m=5, frozen=True))
        unfrozen = package.build_pool(declaration(members=(), m=5, frozen=False))
        # A four-member pool: the three pinned anchors and D-21's `fold-large-bet`, so a
        # draw of five is strictly larger than the membership and a draw of four is not
        # (`docs/L1/seats.md` §4, `records.md` §8, ASM-43, D-21).
        four = package.build_pool(
            dict(
                declaration(members=(), m=5, frozen=True),
                baselines=[self.folder_names()[-1]],
            )
        )
        # A six-seat pool: the three anchors and the three folders, on the one declared
        # shape whose seat count is above the pairwise instrument's (`seats.md` §1, §3,
        # §5, `docs/L1/seats.md` §2, §5, D-33).
        six_seat = package.build_pool(
            dict(
                declaration(members=(), m=5, frozen=True),
                baselines=list(self.folder_names()),
                game=six_seat_shape(),
            )
        )
        chain = version_chain(VERSION_IDS[:2])
        open_pool = package.build_pool(declaration(members=chain, m=3, frozen=False))
        rung, record, matrix, rating = report_inputs()
        record_without_axis = dict(record)
        record_without_axis.pop("axis row")
        extra_rating = dict(
            rating, values=dict(rating["values"], **{"variant-2": rating["values"]["variant-1"]})
        )
        header = header_record()
        header.pop("table seed")
        header_record_incomplete = dict(record, header=header)
        return (
            ("InvalidPool", "pool_members of a dict", package.pool_members, ({},)),
            ("PoolDeclarationInvalid", "build_pool of a list", package.build_pool, ([],)),
            (
                "PoolBoundInvalid",
                "a bound above M",
                package.build_pool,
                (declaration(members=(), m=6, frozen=True),),
            ),
            (
                "MemberInvalid",
                "a member without an id",
                package.build_pool,
                (declaration(members=[{"lineage": START_LABEL}], m=3, frozen=True),),
            ),
            (
                "MemberUnloadable",
                "a declared path that names no file",
                package.build_pool,
                (
                    declaration(
                        members=[
                            version_record(VERSION_IDS[0], START_LABEL, path="/no/such/file.ckpt")
                        ],
                        m=3,
                        frozen=True,
                    ),
                ),
            ),
            (
                "MemberDuplicate",
                "two members carrying one id",
                package.build_pool,
                (
                    declaration(
                        members=[
                            version_record(VERSION_IDS[0], START_LABEL, step=1),
                            version_record(VERSION_IDS[0], START_LABEL, step=2),
                        ],
                        m=3,
                        frozen=True,
                    ),
                ),
            ),
            (
                "LineageConflict",
                "two members descending from one",
                package.build_pool,
                (
                    declaration(
                        members=[
                            version_record(VERSION_IDS[0], START_LABEL, step=1),
                            version_record(VERSION_IDS[1], VERSION_IDS[0], step=2),
                            version_record(VERSION_IDS[2], VERSION_IDS[0], step=3),
                        ],
                        m=3,
                        frozen=True,
                    ),
                ),
            ),
            (
                "LineageCycle",
                "a two-member cycle",
                package.build_pool,
                (
                    declaration(
                        members=[
                            version_record(VERSION_IDS[0], VERSION_IDS[1], step=1),
                            version_record(VERSION_IDS[1], VERSION_IDS[0], step=2),
                        ],
                        m=3,
                        frozen=True,
                    ),
                ),
            ),
            (
                "PoolFrozen",
                "an offer into a frozen pool",
                package.offer,
                (frozen, version_record(VERSION_IDS[0], START_LABEL)),
            ),
            (
                "LineageNotExtended",
                "an offer that does not extend the newest",
                package.offer,
                (open_pool, version_record(VERSION_IDS[4], chain[0]["id"])),
            ),
            (
                "UnknownRule",
                "a version naming a rule the catalogue lacks",
                package.build_pool,
                (
                    declaration(
                        members=[
                            version_record(
                                VERSION_IDS[0], START_LABEL, rule="n-step-returns-battery"
                            )
                        ],
                        m=3,
                        frozen=True,
                    ),
                ),
            ),
            (
                "RuleMismatch",
                "a family whose two members declare two rules",
                package.build_pool,
                (
                    declaration(
                        members=[
                            version_record(VERSION_IDS[0], START_LABEL),
                            version_record(VERSION_IDS[1], VERSION_IDS[0], rule=OTHER_RULE),
                        ],
                        m=3,
                        frozen=True,
                    ),
                ),
            ),
            (
                "UnknownUtility",
                "a version naming a utility the catalogue lacks",
                package.build_pool,
                (
                    declaration(
                        members=[
                            version_record(
                                VERSION_IDS[0], START_LABEL, utility="chips-per-hour"
                            )
                        ],
                        m=3,
                        frozen=True,
                    ),
                ),
            ),
            (
                "UnknownBaseline",
                "a declared baseline the catalogue lacks",
                package.build_pool,
                (
                    dict(
                        declaration(members=(), m=5, frozen=True),
                        baselines=["fold-on-river"],
                    ),
                ),
            ),
            (
                "UnknownShape",
                "a declared shape the catalogue lacks",
                package.build_pool,
                (
                    dict(declaration(members=(), m=5, frozen=True), game="fixed-limit-40"),
                ),
            ),
            (
                "UtilityMismatch",
                "a family whose two members declare two utilities",
                package.build_pool,
                (
                    declaration(
                        members=[
                            version_record(VERSION_IDS[0], START_LABEL),
                            version_record(
                                VERSION_IDS[1],
                                VERSION_IDS[0],
                                utility=OTHER_UTILITY,
                            ),
                        ],
                        m=3,
                        frozen=True,
                    ),
                ),
            ),
            (
                "ShapeMismatch",
                "a version of the second shape in a default-shape pool",
                package.build_pool,
                (
                    declaration(
                        members=[
                            version_record(
                                VERSION_IDS[0], START_LABEL, game=other_shape()
                            )
                        ],
                        m=3,
                        frozen=True,
                    ),
                ),
            ),
            (
                "FamilyBoundExceeded",
                "a declaration holding more families than its bound",
                package.build_pool,
                (
                    declaration(
                        members=[
                            version_record(VERSION_IDS[0], "own-start-1"),
                            version_record(VERSION_IDS[1], "own-start-2"),
                            version_record(VERSION_IDS[2], "own-start-3"),
                        ],
                        m=2,
                        frozen=True,
                    ),
                ),
            ),
            (
                "PoolNotFrozen",
                "a matrix over an unfrozen pool",
                package.matrix,
                (unfrozen, [first_legal], "live"),
            ),
            ("InvalidSeed", "a string seed", package.opponent, (frozen, "8086")),
            (
                "InvalidDrawCount",
                "a draw count of zero",
                package.opponent,
                (frozen, OPPONENT_SEEDS[0], 0),
            ),
            (
                "DrawExceedsMembership",
                "a draw of five from a four-member pool",
                package.opponent,
                (four, OPPONENT_SEEDS[0], 5),
            ),
            (
                "SeatCountExceeded",
                "a matrix over a six-seat pool",
                package.matrix,
                (six_seat, [first_legal], "live"),
            ),
            (
                "InvalidHandCount",
                "a hand count of zero",
                package.match,
                ("random", "always-call", 0, 31337),
            ),
            (
                "SameMemberPair",
                "one id on both sides",
                package.match,
                ("random", "random", 12, 31337),
            ),
            (
                "VariantCountInvalid",
                "three variants",
                package.matrix,
                (frozen, [first_legal, first_legal, first_legal], "live"),
            ),
            (
                "VariantInvalid",
                "a variant that is not a policy",
                package.matrix,
                (frozen, [42], "live"),
            ),
            ("UnknownTable", "a label that is no budget", package.matrix, (frozen, [first_legal], "medium")),
            ("InvalidMembership", "cell_count below two", package.league()["cell_count"], (1,)),
            ("InvalidMatrix", "rating a list", package.rating, ([],)),
            ("MissingMatrixKey", "a matrix without hands_per_cell", package.rating, (missing_key,)),
            ("CellCountMismatch", "five cells for four members", package.rating, (five_cells,)),
            ("DuplicatePair", "one pair in two cells", package.rating, (dict(matrix, cells=tuple(repeated)),)),
            ("ForeignMember", "a cell naming a foreign member", package.rating, (dict(matrix, cells=tuple(foreign)),)),
            ("UnevenCell", "a cell of a different hand count", package.rating, (dict(matrix, cells=tuple(uneven)),)),
            ("MissingBaseline", "a membership without oracle", package.rating, (no_baseline,)),
            ("CheckpointUnreadable", "a file that is no checkpoint", package.policy_from, (file_that_is_not_a_checkpoint(),)),
            ("CheckpointRecordMissing", "a checkpoint recording no seed", package.policy_from, (checkpoint_without_seed(),)),
            ("UnknownEncoding", "a checkpoint recording a bogus encoding", package.policy_from, (checkpoint_with_unknown_encoding(),)),
            (
                "UnknownExploration",
                "a policy_from mode the catalogue lacks",
                package.policy_from,
                (self.checkpoint(name="member")["path"], "greedy"),
            ),
            ("MissingFamily", "a record with no axis row", package.report, (rung, record_without_axis, matrix, rating)),
            ("MembershipMismatch", "a matrix with a foreign member", package.report, (rung, record, wide, rating_record(wide))),
            ("RatingMismatch", "a rating naming a foreign member", package.report, (rung, dict(record, rating=extra_rating), matrix, extra_rating)),
            ("HeaderIncomplete", "a header missing the table seed", package.report, (rung, header_record_incomplete, matrix, rating)),
            ("InvalidArgument", "a rung name that is not a str", package.report, (42, record, matrix, rating)),
        )

    def test_evl_9_3_build_pool_refusals_name_the_entry_the_field_and_the_value(self):
        """EVL-9.3 a `build_pool` refusal names `build_pool`, the argument or key at fault and where there is one the offending value (`errors.md` §3-§4)."""
        package = self.evaluation()
        cases = (
            ("not a mapping", ([],), (("build_pool",), ("mapping",), ("list",))),
            (
                "a bound above M",
                (declaration(members=(), m=7, frozen=True),),
                (("build_pool",), ("m", "bound"), ("7",)),
            ),
            (
                "a member missing its lineage",
                (declaration(members=[{"id": VERSION_IDS[0]}], m=3, frozen=True),),
                (("build_pool",), ("lineage",)),
            ),
            (
                "a declared path that names no readable file",
                (
                    declaration(
                        members=[
                            version_record(VERSION_IDS[0], START_LABEL, path="/no/such/x.ckpt")
                        ],
                        m=3,
                        frozen=True,
                    ),
                ),
                (("build_pool",), (VERSION_IDS[0],), ("path",), ("readable",)),
            ),
            (
                "a version declared under a baseline's name",
                (
                    declaration(
                        members=[{"id": "random", "lineage": START_LABEL}],
                        m=3,
                        frozen=True,
                    ),
                ),
                (("build_pool",), ("random",), ("baseline",)),
            ),
        )
        for label, args, groups in cases:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    package.build_pool, *args, entry="build_pool", groups=groups, label=label
                )

    def test_evl_9_4_pool_offer_and_opponent_refusals_name_their_contract(self):
        """EVL-9.4 `pool_members`, `offer` and `opponent` refusals name the entry point at fault and the field (`errors.md` §3-§4)."""
        package = self.evaluation()
        frozen = package.build_pool(declaration(members=(), m=5, frozen=True))
        cases = (
            ("pool_members of a dict", package.pool_members, ({},), (("pool_members",), ("pool",), ("dict",))),
            (
                "an offer into a frozen pool",
                package.offer,
                (frozen, version_record(VERSION_IDS[0], START_LABEL)),
                (("offer",), ("pool",), ("frozen",)),
            ),
            (
                "an opponent seed that is a string",
                package.opponent,
                (frozen, "8086"),
                (("opponent",), ("seed",), ("8086",)),
            ),
        )
        for label, fn, args, groups in cases:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(fn, *args, entry=groups[0][0], groups=groups[1:], label=label)

    def test_evl_9_5_match_refusals_name_the_entry_the_field_and_the_value(self):
        """EVL-9.5 a `match` refusal names `match`, the field at fault and the value -- including the id two sides share (`errors.md` §3-§4)."""
        package = self.evaluation()
        cases = (
            ("a hand count of zero", ("random", "always-call", 0, 31337), (("match",), ("hands",), ("0",))),
            ("a string seed", ("random", "always-call", 12, "31337"), (("match",), ("seed",), ("31337",))),
            ("a number as a side", (42, "random", 12, 31337), (("match",), ("left",), ("42",))),
            (
                "one id on both sides",
                ("random", "random", 12, 31337),
                (("match",), ("random",), ("distinct",)),
            ),
        )
        for label, args, groups in cases:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    package.match, *args, entry="match", groups=groups[1:], label=label
                )

    def test_evl_9_6_matrix_refusals_name_the_entry_the_field_and_the_value(self):
        """EVL-9.6 a `matrix` refusal names `matrix`, the field at fault and the value -- including the id a membership names twice (`errors.md` §3-§4, `matrix.md` §7)."""
        package = self.evaluation()
        frozen = package.build_pool(declaration(members=(), m=5, frozen=True))
        unfrozen = package.build_pool(declaration(members=(), m=5, frozen=False))
        # A pool declaring a version whose id is a variant's slot label: the table's
        # membership names `variant-1` twice, which is refused before a checkpoint is
        # loaded and before any cell is played (matrix.md §7).
        colliding = package.build_pool(
            declaration(
                members=[version_record("variant-1", START_LABEL)],
                m=3,
                frozen=True,
            )
        )
        cases = (
            ("an unfrozen pool", (unfrozen, [first_legal], "live"), (("matrix",), ("frozen",))),
            ("a label that is no budget", (frozen, [first_legal], "medium"), (("matrix",), ("table",), ("medium",))),
            ("three variants", (frozen, [first_legal] * 3, "live"), (("matrix",), ("variant",), ("3",))),
            ("a variant that is not a policy", (frozen, [42], "live"), (("matrix",), ("variant",), ("42",))),
            (
                "a membership that is not distinct",
                (colliding, [first_legal], "live"),
                (("matrix",), ("variant-1",), ("distinct",)),
            ),
        )
        for label, args, groups in cases:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    package.matrix, *args, entry="matrix", groups=groups[1:], label=label
                )

    def test_evl_9_7_rating_refusals_name_the_entry_the_rule_and_the_member(self):
        """EVL-9.7 a `rating` refusal names `rating`, the violated rule and -- where a member or a pair is at fault -- that member or pair (`errors.md` §3-§4)."""
        package = self.evaluation()
        matrix = hand_matrix(balanced)
        cells = list(matrix_cells(matrix))
        foreign = list(cells)
        foreign[0] = dict(cells[0], members=("random", "version-ghost-5599"))
        cases = (
            ("not a matrix record", ([],), (("rating",), ("matrix",))),
            ("a missing required key", (self._without(matrix, "table_seed"),), (("rating",), ("table_seed",))),
            ("a wrong cell count", (dict(matrix, cells=tuple(cells[:5])),), (("rating",), ("cells",))),
            ("a foreign member", (dict(matrix, cells=tuple(foreign)),), (("rating",), ("version-ghost-5599",))),
        )
        for label, args, groups in cases:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    package.rating, *args, entry="rating", groups=groups[1:], label=label
                )

    def test_evl_9_8_policy_from_refusals_name_the_path_and_the_fact(self):
        """EVL-9.8 a `policy_from` refusal names `policy_from`, the path it was handed and the fact it could not read -- a recorded encoding name being a name `features.build_encoder` refuses (`errors.md` §3-§4, `scheduler.md` §5.1)."""
        package = self.evaluation()
        cases = (
            (
                "a file that is not a checkpoint",
                file_that_is_not_a_checkpoint(),
                (("policy_from",), ("path",), ("readable", "zip")),
            ),
            (
                "a checkpoint recording no seed",
                checkpoint_without_seed(),
                (("policy_from",), ("seed",), ("path",)),
            ),
            (
                "a checkpoint recording an encoding name build_encoder refuses",
                checkpoint_with_unknown_encoding(),
                (("policy_from",), ("bogus-encoding",), ("build_encoder", "refuses", "encoding")),
            ),
        )
        for label, path, groups in cases:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    package.policy_from, path, entry="policy_from", groups=groups[1:], label=label
                )

    def test_evl_9_9_report_and_cell_count_refusals_name_their_contract_and_no_bare_error_escapes(self):
        """EVL-9.9 a `report` refusal names the family, the member or the header item at fault, a `cell_count` refusal names the callable, and no bad argument escapes as a `TypeError`, a `KeyError` or another module's error (`errors.md` §1-§4, G16)."""
        package = self.evaluation()
        rung, record, matrix, rating = report_inputs()
        missing = dict(record)
        missing.pop("axis row")
        self.assert_evaluation_refusal(
            package.report,
            rung,
            missing,
            matrix,
            rating,
            entry="report",
            groups=(("axis row",),),
            label="a record with no axis row",
        )
        self.assert_evaluation_refusal(
            package.league()["cell_count"],
            1,
            entry="cell_count",
            groups=(("cell_count",), ("2",)),
            label="cell_count(1)",
        )
        bad_calls = (
            ("build_pool of None", package.build_pool, (None,)),
            ("build_pool of a dict missing m", package.build_pool, ({"members": [], "frozen": True},)),
            ("offer of a dict", package.offer, ({}, version_record(VERSION_IDS[0], START_LABEL))),
            ("pool_members of a list", package.pool_members, ([],)),
            ("opponent of None", package.opponent, (None, 1)),
            ("matrix of None", package.matrix, (None, [first_legal], "live")),
            ("rating of None", package.rating, (None,)),
            ("rating of a dict", package.rating, ({},)),
            ("policy_from of None", package.policy_from, (None,)),
            ("report of None", package.report, (None, None, matrix, rating)),
            ("report of an empty record", package.report, (rung, {}, matrix, rating)),
        )
        for label, fn, args in bad_calls:
            with self.subTest(case=label):
                try:
                    value = fn(*args)
                except Exception as exc:
                    self.assertIsInstance(
                        exc,
                        self._root(),
                        "%s must be this module's own refusal and not a TypeError, a "
                        "KeyError or another module's error escaping an internal "
                        "decision (errors.md §1-§2, G16): got %s: %r"
                        % (label, type(exc).__name__, exc),
                    )
                    self.assertTrue(
                        str(exc).strip(),
                        "%s was refused with an empty message (errors.md §3): %r"
                        % (label, type(exc).__name__),
                    )
                else:
                    self.fail(
                        "%s accepted %r, and an invalid argument is refused with an "
                        "error naming the violated contract (e2e-surface.md §2, "
                        "errors.md §1)" % (label, value)
                    )

    def test_evl_9_10_rating_does_not_refuse_a_label_value_or_a_disagreeing_cell(self):
        """EVL-9.10 a valid hand-built matrix is rated whatever its `table` label says, and a cell whose two directions disagree with its hand count is rated too -- `n_a` is the observed total, and the record is never repaired (`errors.md` §5, `rating.md` §6, `surface.md` §11)."""
        package = self.evaluation()
        labelled = hand_matrix(balanced, table="medium")
        rated = package.rating(labelled)
        self.assertEqual(
            set(rating_entries(rated)),
            set(matrix_member_ids(labelled)),
            "rating fits a hand-built table by rating.md §6's rules and re-judges no "
            "`table` label value, so a label that is neither live nor full is rated "
            "and never refused (errors.md §5, rating.md §6): %r" % (rated,),
        )
        matrix = hand_matrix(lopsided)
        cells = list(matrix_cells(matrix))
        cells[0] = dict(
            cells[0],
            directions=(
                direction(50, 10, 30, HANDS_PER_CELL),
                direction(30, 10, 50, HANDS_PER_CELL),
            ),
        )
        disagreeing = dict(matrix, cells=tuple(cells))
        snapshot = copy.deepcopy(disagreeing)
        rated = package.rating(disagreeing)
        self.assertEqual(
            set(rating_entries(rated)),
            set(matrix_member_ids(disagreeing)),
            "a cell whose two directions disagree with its hand count is rated too: "
            "n_a is the observed total, so the fit reads what the record says instead "
            "of refusing it (errors.md §5, rating.md §6): %r" % (rated,),
        )
        self.assertEqual(
            disagreeing,
            snapshot,
            "the record is never repaired: the fit leaves the disagreeing cell's counts "
            "exactly as it found them (rating.md §1, §6): %r" % (disagreeing,),
        )

    def test_evl_9_11_a_numpy_integer_is_a_seed_and_a_bool_is_not(self):
        """EVL-9.11 a NumPy integer handed to `opponent` as its seed is an integer and is not refused -- the draw returns a policy -- while a `bool` is refused naming the seed, because a flag is not a count (`errors.md` §5, `scheduler.md` §3, §6, `pool.md` §7)."""
        package = self.evaluation()
        import numpy as np

        pool = self.frozen_pool(members=(), m=5)
        drawn = package.opponent(pool, np.int64(OPPONENT_SEEDS[0]))
        self.assertTrue(
            callable(drawn),
            "numpy.int64 is an Integral, so a NumPy integer seed is a seed and the draw "
            "returns a policy instead of being refused (errors.md §5, scheduler.md §6, "
            "pool.md §7): %r" % (drawn,),
        )
        for row in probe_readouts(1):
            self.assertIn(
                drawn(row["readout"], row["legal"]),
                row["legal"],
                "the policy a NumPy-integer seed drew answers one descriptor of "
                "legal_actions, as every drawn opponent does (surface.md §2, pool.md "
                "§7): %r" % (drawn,),
            )
        self.assert_evaluation_refusal(
            package.opponent,
            pool,
            True,
            entry="opponent",
            groups=(("seed",),),
            label="a bool seed",
        )

    def folder_names(self):
        """The catalogue's three folders, in `agents.baselines()`'s order (D-21).

        The catalogue names beyond the pinned anchors: a declaration that admits them
        holds the three anchors and the three folders, which is the six-member
        composition a six-seat hand seats (`docs/L1/seats.md` §2, §4, `records.md` §8,
        ASM-32, D-21).
        """
        return tuple(
            name for name in self.agents().baselines() if name not in BASELINES
        )

    @staticmethod
    def _without(record, key):
        """A copy of a mapping with one key removed."""
        copy = dict(record)
        copy.pop(key)
        return copy

    def _root(self):
        """This module's refusal root (`errors.md` §2)."""
        from _evaluation_support import refusal_class

        return refusal_class()


if __name__ == "__main__":
    unittest.main()
