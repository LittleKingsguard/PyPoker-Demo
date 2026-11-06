"""EVL-4 — the pairwise matrix: `matrix`.

Drives `docs/L3/evaluation/matrix.md` §1-§8, `docs/L2/evaluation/surface.md` §10 and
`docs/L1/league.md` §3-§4: the membership is `pool_members`'s order and then
`variant-1`, `variant-2` by argument position (a variant is named by its slot,
whatever the policy carries), the cells are exactly K(K-1)/2 unordered pairs in the
lexicographic enumeration, every cell is played at the table's one hand count with the
three baseline cells included, and the record carries `table_seed` -- the league's one
integer, no argument supplying it -- and the `table` label as a value.

Cost discipline (`guardrails.md` G13, ASM-15): a `live` cell is 120 hands and every
cell holding the pinned `oracle` asks `engine.equity` at each decision, so this file
shares the battery's three real matrices (`k4`, `k5`, `k6`, built once by
`_evaluation_support.shared_matrix`) and provokes every refusal -- which the design
orders before any cell is played (`matrix.md` §7) -- without playing a hand at all.
`k4` and `k5` are played over the frozen baselines-only pool; `k6` is played over a
frozen pool whose window holds one real version member, so `EVL-4.10` plays
`matrix.md` §4's version row through `matrix` instead of leaving it to `opponent`,
`match` and `policy_from`.
"""

import os
import unittest

from _evaluation_support import (
    BASELINES,
    BUDGETS,
    POOL_M,
    VERSION_IDS,
    START_LABEL,
    EvaluationCase,
    cell_directions,
    cell_seed,
    checkpoint_without_seed,
    count,
    declaration,
    direction_counts,
    direction_values,
    first_legal,
    matrix_cells,
    matrix_member_ids,
    member_id,
    member_ids_of_cell,
    params_of,
    seat_split_counts,
    unlabelled_of,
    version_pool_member,
    version_record,
)


def slot_names(count_of_variants):
    """The names `matrix.md` §1 gives the variants by argument position."""
    return tuple("variant-%d" % (index + 1) for index in range(count_of_variants))


class MatrixTest(EvaluationCase):
    def test_evl_4_1_the_membership_is_the_pool_s_order_and_the_two_variant_slots(self):
        """EVL-4.1 `members` is `pool_members`'s order and then `variant-1`, `variant-2` by argument position, whatever the policy carries (`matrix.md` §1, `surface.md` §10, G12)."""
        package = self.evaluation()
        matrix = self.shared_matrix("k5")
        pool = package.build_pool(declaration(members=(), m=5, frozen=True))
        pool_ids = tuple(
            member_id(entry) for entry in package.pool_members(pool)["members"]
        )
        members = matrix_member_ids(matrix)
        self.assertEqual(
            members,
            pool_ids + slot_names(2),
            "a table's membership is the frozen pool's members in pool_members' order "
            "and then variant-1, variant-2 in argument order (matrix.md §1, "
            "surface.md §10, G12): %r" % (members,),
        )
        self.assertEqual(
            members[:3],
            BASELINES,
            "the three pinned baselines are the first three rows and columns "
            "(matrix.md §1, league.md §3): %r" % (members,),
        )
        self.assertIn(
            "variant-1",
            members,
            "a variant is named by the slot it was handed in, even when the policy "
            "itself carries an id -- this one is a member policy policy_from built "
            "(matrix.md §1, G12): %r" % (members,),
        )

    def test_evl_4_2_the_cells_are_exactly_the_unordered_pairs_in_enumeration_order(self):
        """EVL-4.2 `cells` is exactly K(K-1)/2 records, one per unordered pair and no repeat, in `matrix.md` §2's lexicographic enumeration (`matrix.md` §2, §5, `league.md` §3, G12)."""
        matrix = self.shared_matrix("k5")
        members = matrix_member_ids(matrix)
        cells = matrix_cells(matrix)
        expected_pairs = [
            (i, j) for i in range(len(members)) for j in range(i + 1, len(members))
        ]
        self.assertEqual(
            len(cells),
            len(members) * (len(members) - 1) // 2,
            "a table holds exactly K(K-1)/2 cells, one per unordered pair "
            "(matrix.md §2, league.md §3, G12): %d cells for K = %d"
            % (len(cells), len(members)),
        )
        seen = []
        for cell in cells:
            pair = member_ids_of_cell(cell)
            self.assertEqual(
                len(pair),
                2,
                "a cell is one unordered pair of members (records.md §9): %r" % (pair,),
            )
            positions = tuple(members.index(name) for name in pair)
            self.assertEqual(
                positions,
                tuple(sorted(positions)),
                "a cell's pair is listed in membership order, (i, j) with i < j "
                "(matrix.md §2, rating.md §2): %r" % (pair,),
            )
            seen.append(positions)
        self.assertEqual(
            seen,
            expected_pairs,
            "the cells are position-for-position matrix.md §2's enumeration, "
            "(0,1) (0,2) ... (0,K-1) (1,2) ... (K-2,K-1) (matrix.md §2, G12): %r"
            % (seen,),
        )
        self.assertEqual(
            len(set(frozenset(pair) for pair in seen)),
            len(seen),
            "no pair appears in two cells (matrix.md §2, league.md §3, G12)",
        )

    def test_evl_4_3_every_cell_is_played_at_the_table_s_one_hand_count(self):
        """EVL-4.3 `hands_per_cell` is the budget's one hand count, every cell carries it, and no cell is cheaper than another (`matrix.md` §6, `league.md` §3, G13)."""
        package = self.evaluation()
        matrix = self.shared_matrix("k5")
        declared = int(package.league()["tables"][matrix["table"]]["hands_per_cell"])
        self.assertEqual(
            count(matrix["hands_per_cell"], "a matrix's hands_per_cell"),
            declared,
            "hands_per_cell is the one hand count the budget declares -- 120 live, 1500 "
            "full (matrix.md §6, declarations.md §4.1, G13): %r"
            % (matrix["hands_per_cell"],),
        )
        for cell in matrix_cells(matrix):
            with self.subTest(pair=member_ids_of_cell(cell)):
                self.assertEqual(
                    count(cell["hands"], "a cell's hands"),
                    declared,
                    "every cell of a table is played at that one count, so no member's "
                    "row is measured more precisely than another's (matrix.md §6, "
                    "league.md §3, ASM-14, G13): %r" % (cell["hands"],),
                )

    def test_evl_4_4_the_three_baseline_cells_are_in_the_table_at_that_count(self):
        """EVL-4.4 the three cells no model influences are rows and columns of the table at the same hand count, with the baselines' measured zero (`matrix.md` §4, §6, `protocol.md` §3, G13)."""
        matrix = self.shared_matrix("k5")
        members = matrix_member_ids(matrix)
        baselines = list(BASELINES)
        cells = matrix_cells(matrix)
        by_pair = {frozenset(member_ids_of_cell(cell)): cell for cell in cells}
        for index, left in enumerate(baselines):
            for right in baselines[index + 1:]:
                with self.subTest(pair=(left, right)):
                    cell = by_pair[frozenset((left, right))]
                    self.assertEqual(
                        count(cell["hands"], "a baseline cell's hands"),
                        count(matrix["hands_per_cell"], "hands_per_cell"),
                        "the three baseline cells are in the table like every other "
                        "cell and at the same one hand count (matrix.md §4, §6, "
                        "league.md §3, G13): %r" % (cell["hands"],),
                    )
                    self.assertEqual(
                        params_of(cell),
                        [0, 0],
                        "a baseline's parameter count is the zero agents.baselines() "
                        "declares, and it is measured (scheduler.md §5, G11): %r"
                        % (cell["params"],),
                    )
                    for name in (left, right):
                        self.assertNotIn(
                            name,
                            tuple(unlabelled_of(cell)),
                            "a baseline's zero is not an unmeasured zero "
                            "(scheduler.md §4, G11): %r" % (unlabelled_of(cell),),
                        )

    def test_evl_4_5_the_record_carries_its_keys_and_the_cell_count(self):
        """EVL-4.5 the record's five required keys come first in `matrix.md` §5's order, then `pool`, `member_records`, `unlabelled` and `cell_count`; `unlabelled` names the opaque variant's unmeasured zero and a variant record is its three-key record (`matrix.md` §5, `records.md` §10, G11, G14)."""
        package = self.evaluation()
        matrix = self.shared_matrix("k5")
        self.assertEqual(
            tuple(matrix),
            (
                "members",
                "cells",
                "hands_per_cell",
                "table_seed",
                "table",
                "pool",
                "member_records",
                "unlabelled",
                "cell_count",
            ),
            "matrix returns exactly matrix.md §5's keys, in its order, the five "
            "records.md §10 keys first (matrix.md §5, G14): %r" % (tuple(matrix),),
        )
        members = matrix_member_ids(matrix)
        self.assertEqual(
            count(matrix["cell_count"], "a matrix's cell_count"),
            len(matrix_cells(matrix)),
            "cell_count is the number of cells the record holds (matrix.md §5, G14): %r"
            % (matrix["cell_count"],),
        )
        self.assertEqual(
            matrix["cell_count"],
            package.league()["cell_count"](len(members)),
            "cell_count is the same number league()['cell_count'](K) returns "
            "(matrix.md §5, declarations.md §5, G14)",
        )
        self.assertEqual(
            tuple(unlabelled_of(matrix)),
            ("variant-2",),
            "the ids whose capacity is unmeasured are the opaque variant's, and the "
            "labelled variant's measured 0 is not among them (matrix.md §5, "
            "surface.md §2, G11): %r" % (unlabelled_of(matrix),),
        )
        records = list(matrix["member_records"].values()) if isinstance(
            matrix["member_records"], dict
        ) else list(matrix["member_records"])
        self.assertEqual(
            len(records),
            len(members),
            "member_records holds one record per member, in members order "
            "(matrix.md §5): %r" % (records,),
        )
        for record, name in zip(records, members):
            with self.subTest(member=name):
                self.assertEqual(
                    member_id(record),
                    name,
                    "member_records is position-aligned with members (matrix.md §5): %r"
                    % (record,),
                )
                if name in BASELINES:
                    self.assertTrue(
                        bool(record.get("baseline")) and bool(record.get("pinned")),
                        "a baseline's record is its pinned four-key record "
                        "(matrix.md §5): %r" % (record,),
                    )
                elif name.startswith("variant-"):
                    self.assertIn(
                        "params",
                        record,
                        "a variant's record carries `params` (matrix.md §5): %r" % (record,),
                    )
                    self.assertIsInstance(
                        record["params"],
                        int,
                        "a variant's params is an integer measurement or the unmeasured "
                        "0 (matrix.md §5, ASM-10): %r" % (record,),
                    )
        variant_one = records[members.index("variant-1")]
        self.assertGreater(
            variant_one["params"],
            0,
            "variant-1 is a member policy policy_from built, so its capacity is a "
            "measurement and not an invented 0 (matrix.md §5, surface.md §2, ASM-10): %r"
            % (variant_one,),
        )

    def test_evl_4_6_the_table_seed_is_the_league_s_and_the_table_is_the_label(self):
        """EVL-4.6 `table_seed` is `league()["table_seed"]` -- no argument supplies it -- and `table` is the label as a value, never a substring; the table also names the pool it measured by id (`matrix.md` §3, §5, `surface.md` §10, G14)."""
        package = self.evaluation()
        league_seed = int(package.league()["table_seed"])
        for key in ("k4", "k5"):
            matrix = self.shared_matrix(key)
            with self.subTest(matrix=key):
                self.assertEqual(
                    count(matrix["table_seed"], "a matrix's table_seed"),
                    league_seed,
                    "a matrix is played from the league's one table seed and takes no "
                    "seed argument (matrix.md §3, declarations.md §6, G14): %r"
                    % (matrix["table_seed"],),
                )
                self.assertIn(
                    matrix["table"],
                    BUDGETS,
                    "the table label is one of the two budget names (matrix.md §6, "
                    "records.md §10, G14): %r" % (matrix["table"],),
                )
        pool = package.build_pool(declaration(members=(), m=5, frozen=True))
        expected_pool = package.pool_members(pool)["id"]
        for key in ("k4", "k5"):
            with self.subTest(pool_of=key):
                self.assertEqual(
                    self.shared_matrix(key)["pool"],
                    expected_pool,
                    "a table names the pool it measured by the pool record's id string, "
                    "and not by the pool record (matrix.md §5, §8, G14): %r"
                    % (self.shared_matrix(key)["pool"],),
                )
                self.assertIsInstance(
                    self.shared_matrix(key)["pool"],
                    str,
                    "the table's `pool` is the id string (matrix.md §5, §8): %r"
                    % (self.shared_matrix(key)["pool"],),
                )

    def test_evl_4_7_one_variant_is_a_table_too_the_smallest_legal_membership(self):
        """EVL-4.7 a frozen pool plus **one** variant is a table: K = 4, six cells, one membership and one hand count (`matrix.md` §1-§2, `tables.md` §1, `ladder.md` §2)."""
        package = self.evaluation()
        matrix = self.shared_matrix("k4")
        members = matrix_member_ids(matrix)
        self.assertEqual(
            members,
            BASELINES + ("variant-1",),
            "one variant makes K = 4, the smallest membership this surface allows "
            "(matrix.md §1, tables.md §1): %r" % (members,),
        )
        self.assertEqual(
            len(matrix_cells(matrix)),
            6,
            "K = 4 has K(K-1)/2 = 6 unordered pairs and no more (matrix.md §2, "
            "tables.md §1): %r" % (len(matrix_cells(matrix)),),
        )
        self.assertEqual(
            sorted(frozenset(member_ids_of_cell(cell)) for cell in matrix_cells(matrix)),
            sorted(
                frozenset((left, right))
                for index, left in enumerate(members)
                for right in members[index + 1:]
            ),
            "the six cells are one per unordered pair of the four members "
            "(matrix.md §2): %r" % ([member_ids_of_cell(c) for c in matrix_cells(matrix)],),
        )
        self.assertEqual(
            count(matrix["hands_per_cell"], "hands_per_cell"),
            int(package.league()["tables"]["live"]["hands_per_cell"]),
            "a live table's one cell size is the league's live cell size "
            "(matrix.md §6, declarations.md §4.1): %r" % (matrix["hands_per_cell"],),
        )
        self.assertEqual(
            tuple(unlabelled_of(matrix)),
            (),
            "a labelled variant's capacity is measured, so a one-variant table has "
            "nothing unlabelled (matrix.md §5, surface.md §2, G11): %r"
            % (unlabelled_of(matrix),),
        )

    def test_evl_4_8_matrix_refuses_what_the_contract_refuses(self):
        """EVL-4.8 `matrix` refuses a value that is not a pool, an unfrozen pool, a label that is not `live` or `full`, a variant count other than one or two, a variant that is not a policy, a membership that is not distinct (`MemberDuplicate`, naming the id) and a pool member with no `path` -- in the design's order, before a checkpoint is loaded or any cell is played (`matrix.md` §7, `surface.md` §10, G16)."""
        package = self.evaluation()
        frozen = package.build_pool(declaration(members=(), m=5, frozen=True))
        unfrozen = package.build_pool(declaration(members=(), m=5, frozen=False))
        pathless = version_record(VERSION_IDS[0], START_LABEL, step=3)
        pool_with_pathless = package.build_pool(
            declaration(members=[pathless], m=3, frozen=True)
        )
        # A frozen pool declaring a version whose id is `variant-1`: with one variant the
        # table's membership names `variant-1` twice, so §7 refuses it and never pairs a
        # member with itself. The member carries no `path`, so no checkpoint exists and
        # nothing can be loaded: the guard is what is driven here (matrix.md §7).
        colliding = package.build_pool(
            declaration(
                members=[version_record("variant-1", START_LABEL, step=5)],
                m=3,
                frozen=True,
            )
        )
        cases = (
            (
                "a value that is not a pool",
                ({}, [first_legal], "live"),
                (("pool",),),
            ),
            (
                "an unfrozen pool",
                (unfrozen, [first_legal], "live"),
                (("frozen",), ("does not change", "may still change", "not frozen")),
            ),
            (
                "a label that is no budget",
                (frozen, [first_legal], "medium"),
                (("table",), ("medium",), ("live", "full")),
            ),
            (
                "a label as a substring",
                (frozen, [first_legal], "live-table"),
                (("table",), ("live", "full")),
            ),
            (
                "a label in the wrong case",
                (frozen, [first_legal], "LIVE"),
                (("table",), ("live", "full")),
            ),
            (
                "three variants",
                (frozen, [first_legal, first_legal, first_legal], "live"),
                (("variants",), ("3",)),
            ),
            (
                "no variants",
                (frozen, [], "live"),
                (("variants",), ("0",)),
            ),
            (
                "a variant that is not a policy",
                (frozen, [42], "live"),
                (("variant",), ("42",)),
            ),
            (
                "a membership that is not distinct",
                (colliding, [first_legal], "live"),
                (("variant-1",), ("distinct",)),
            ),
        )
        for label, args, groups in cases:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    package.matrix, *args, entry="matrix", groups=groups, label=label
                )
        with self.subTest(case="a pool member with no path"):
            # The refusal's subject is the member that cannot be loaded, so the case
            # asks for the member's id and the path and not for the entry point's name
            # (matrix.md §7: "naming the member"; scheduler.md §6's member classes).
            self.assert_evaluation_refusal(
                package.matrix,
                pool_with_pathless,
                [first_legal],
                "live",
                entry=VERSION_IDS[0],
                groups=(("path",),),
                label="a pool member with no path",
            )

    def test_evl_4_9_a_version_whose_container_records_no_seed_is_refused_before_a_cell(self):
        """EVL-4.9 `matrix` builds a pool version's policy from the two facts its checkpoint records: a frozen pool holding a version whose container records no seed is refused before any cell is played, naming the fact, the member and the path, and a refused table moves no stream (`matrix.md` §7, `scheduler.md` §5.1, §6, `surface.md` §10, G16)."""
        package = self.evaluation()
        path = checkpoint_without_seed()
        member = VERSION_IDS[0]
        pool = package.build_pool(
            declaration(
                members=[version_record(member, START_LABEL, path=path)],
                m=POOL_M,
                frozen=True,
            )
        )
        before = self.stream_state()
        # The refusal's subject is the version whose facts cannot be read, so the case
        # asks for the member, the fact and the path -- matrix.md §7's three names --
        # and not for the entry point's own word (as EVL-4.8's path-less member does).
        # The facts are checked before a policy is built and before the first cell, so
        # this drives §7's refusal and not §4's version row, which EVL-4.10 plays.
        self.assert_evaluation_refusal(
            package.matrix,
            pool,
            [first_legal],
            "live",
            entry=member,
            groups=(("seed",), (path, os.path.basename(path))),
            label="a version whose container records no seed",
        )
        self.assert_stream_unchanged(
            before,
            "matrix() refusing a table over a version whose recorded facts are missing",
        )

    def test_evl_4_10_a_version_member_is_played_by_matrix_at_its_checkpoint_s_seed(self):
        """EVL-4.10 a pool member carrying a `path` is played by `matrix` as `policy._member_policy(record)` -- `policy_from`'s builder, at the seed its checkpoint records -- so the table lists it after the three baselines, carries its `records.md` §7 record back verbatim, measures its capacity instead of unlabelling it, and is one record for one pool, one variant list and one budget: this plays `matrix.md` §4's version row, which is what `matrix.md` §7's **Unverified** clause said no unit case did (`matrix.md` §1-§6, `scheduler.md` §5.1, `surface.md` §12)."""
        package = self.evaluation()
        pool = self.shared_pool("k6")
        matrix = self.shared_matrix("k6")
        declared = version_pool_member()
        member = VERSION_IDS[0]
        path = declared["path"]
        members = matrix_member_ids(matrix)
        cells = matrix_cells(matrix)

        # §1: the pool's window holds one real version, and a table's membership is the
        # pool's members in pool_members' order and then the variant slot.
        self.assertEqual(
            self.members_of(pool),
            BASELINES + (member,),
            "the k6 pool's window holds the three pinned baselines and one real version "
            "member, and `matrix` tables that pool (matrix.md §1, pool.md §5, "
            "records.md §8): %r" % (self.members_of(pool),),
        )
        self.assertEqual(
            members,
            BASELINES + (member,) + slot_names(1),
            "a table's membership is pool_members' order and then variant-1, so the "
            "version is a member of the table and not a variant of it (matrix.md §1, "
            "§4, surface.md §10): %r" % (members,),
        )
        self.assertEqual(
            len(cells),
            10,
            "K = 5 -- the three baselines, the version and one variant -- has "
            "K(K-1)/2 = 10 unordered pairs (matrix.md §1-§2, league.md §3): %d cells"
            % (len(cells),),
        )
        expected_pairs = [
            (i, j) for i in range(len(members)) for j in range(i + 1, len(members))
        ]
        seen = [
            tuple(members.index(name) for name in member_ids_of_cell(cell))
            for cell in cells
        ]
        self.assertEqual(
            seen,
            expected_pairs,
            "the ten cells are matrix.md §2's enumeration, position for position, with "
            "the version's four pairs ((0,3) (1,3) (2,3) (3,4)) among them (matrix.md "
            "§2, G12): %r" % (seen,),
        )
        self.assertEqual(
            len(set(frozenset(pair) for pair in seen)),
            len(seen),
            "no pair appears in two cells (matrix.md §2, league.md §3, G12): %r"
            % (seen,),
        )

        # §5: a version's member record is the records.md §7 record it was declared
        # with, verbatim -- its `path` included.
        records = (
            list(matrix["member_records"].values())
            if isinstance(matrix["member_records"], dict)
            else list(matrix["member_records"])
        )
        position = members.index(member)
        self.assertEqual(
            [member_id(entry) for entry in records],
            list(members),
            "member_records holds one record per member, position-aligned with members "
            "(matrix.md §5): %r" % (records,),
        )
        self.assertEqual(
            records[position],
            declared,
            "a version's member record is the records.md §7 record the declaration "
            "carried, carried verbatim -- id, path, rung, variant, seed, step, samples "
            "and lineage (matrix.md §5, pool.md §5, records.md §7, G7): %r vs %r"
            % (records[position], declared),
        )
        self.assertEqual(
            records[position]["path"],
            path,
            "the record carries the checkpoint the member is loaded from (matrix.md "
            "§4-§5, scheduler.md §5.1): %r" % (records[position]["path"],),
        )
        self.assertTrue(
            os.path.isfile(path),
            "the version's path names the real checkpoint this table plays (matrix.md "
            "§4, scheduler.md §5.1): %r" % (path,),
        )

        # §4-§5: the version is played as its checkpoint's learner, so the table measures
        # its real capacity -- and a measured capacity is not an unlabelled zero.
        capacity = self.agents().param_count(self.agents().load(None, path))
        self.assertGreater(
            capacity,
            0,
            "the checkpoint restores a learner whose capacity is a real measurement "
            "(matrix.md §4-§5, ASM-10): %r" % (capacity,),
        )
        version_cells = [cell for cell in cells if member in member_ids_of_cell(cell)]
        self.assertEqual(
            len(version_cells),
            len(members) - 1,
            "the version is a row and a column of the table: one cell against each of "
            "the four other members (matrix.md §1-§2): %r"
            % ([member_ids_of_cell(cell) for cell in version_cells],),
        )
        for cell in version_cells:
            pair = member_ids_of_cell(cell)
            with self.subTest(pair=pair):
                params = params_of(cell)
                self.assertEqual(
                    params[pair.index(member)],
                    capacity,
                    "a version's params is agents.param_count of the learner its "
                    "checkpoint restores -- the checkpoint's real capacity, not the "
                    "baselines' catalogue 0 (records.md §9, matrix.md §4, "
                    "scheduler.md §5, ASM-10): %r for %r, whose checkpoint restores %r"
                    % (params, member, capacity),
                )
                for index, name in enumerate(pair):
                    if name in BASELINES:
                        self.assertEqual(
                            params[index],
                            0,
                            "a baseline's params is the zero agents.baselines() "
                            "declares, which is what the version's measured count is "
                            "distinguished from (matrix.md §4-§5, G11): %r" % (params,),
                        )
                self.assertNotIn(
                    member,
                    tuple(unlabelled_of(cell)),
                    "the version's capacity is measured, so the cell does not report "
                    "its number as unmeasured (matrix.md §5, scheduler.md §4, "
                    "ASM-10): %r" % (unlabelled_of(cell),),
                )
        self.assertNotIn(
            member,
            tuple(unlabelled_of(matrix)),
            "the table does not name the version among the unmeasured zeros, because "
            "its params is a measurement (matrix.md §5, surface.md §2, ASM-10): %r"
            % (unlabelled_of(matrix),),
        )
        self.assertEqual(
            tuple(unlabelled_of(matrix)),
            (),
            "nothing in this table is unlabelled: the version is a loaded member and "
            "variant-1 is the member policy policy_from built (matrix.md §5, "
            "ASM-10): %r" % (unlabelled_of(matrix),),
        )
        self.assertEqual(
            matrix["pool"],
            self.pool_members(pool)["id"],
            "a table names the pool it measured by the pool record's id string, and the "
            "version makes that id the version-holding pool's own (matrix.md §5, pool.md "
            "§4, G14): %r" % (matrix["pool"],),
        )

        # §6: the version's four cells exist, are played at the table's one hand count,
        # and account for every hand they were given.
        one_count = count(matrix["hands_per_cell"], "a matrix's hands_per_cell")
        self.assertEqual(
            one_count,
            int(package.league()["tables"][matrix["table"]]["hands_per_cell"]),
            "the table's one hand count is the budget row's -- 120 for live -- and a "
            "version member's cell is neither cheaper nor dearer than another's "
            "(matrix.md §6, league.md §3, G13): %r" % (one_count,),
        )
        version_hands = 0
        for cell in version_cells:
            with self.subTest(cell=member_ids_of_cell(cell)):
                self.assertEqual(
                    count(cell["hands"], "a version cell's hands"),
                    one_count,
                    "every cell holding the version is played at the table's one hand "
                    "count (matrix.md §6, league.md §3, G13): %r" % (cell["hands"],),
                )
                for direction in cell_directions(cell):
                    self.assert_plain_counts(
                        direction_counts(direction),
                        one_count,
                        "a version cell's direction",
                    )
                version_hands += count(cell["hands"], "a version cell's hands")
        self.assertEqual(
            version_hands,
            (len(members) - 1) * one_count,
            "the version's four cells account for (K-1) x hands_per_cell = %d hands at "
            "the table's one hand count, so its row is measured once against each "
            "opponent (matrix.md §3-§4, §6, rating.md §5): %d"
            % ((len(members) - 1) * one_count, version_hands),
        )

        # §3-§5: one pool, one variant list and one budget give one matrix. The same
        # frozen pool and the same variant list are tabled to one record, and every part
        # of it is then recomputed from the table seed, the membership and the budget
        # below, so nothing outside those three inputs steers it. The shared build is
        # read again and never rebuilt, so this case costs no second table (G13, ASM-15).
        self.assertEqual(
            self.shared_matrix("k6"),
            matrix,
            "one frozen pool, one variant list and one budget give one record: the "
            "shared build read again is equal value for value, so no assertion rebuilds "
            "the table (matrix.md §3, §5, G13)",
        )
        for (i, j), cell in zip(expected_pairs, cells):
            with self.subTest(seed_of=(i, j)):
                self.assertEqual(
                    count(cell["seed"], "a cell's seed"),
                    cell_seed(matrix["table_seed"], i, j),
                    "every cell is played at seeds._cell_seed(table_seed, i, j), so the "
                    "table is reproduced from its seed and its pair positions alone "
                    "(matrix.md §3, G8): %r" % (cell["seed"],),
                )

        # The three baselines' mutual cells are played at the table seed and their
        # positions, so they are the same hands in every table at this seed and budget:
        # a version in the pool moves nobody else's cell (matrix.md §3-§4).
        def baseline_cells_of(table):
            """One entry per baseline pair, projected onto records.md §9's five facts."""
            found = {}
            for cell in matrix_cells(table):
                pair = member_ids_of_cell(cell)
                if not set(pair) <= set(BASELINES):
                    continue
                facts = []
                for direction in cell_directions(cell):
                    values = direction_values(direction, "a baseline cell's direction")
                    wins, ties, losses, mean = direction_counts(
                        values, "a baseline cell's direction"
                    )
                    facts.append(
                        (
                            wins,
                            ties,
                            losses,
                            mean,
                            seat_split_counts(
                                values["seat_split"], "a baseline cell's direction"
                            ),
                        )
                    )
                found[frozenset(pair)] = (
                    tuple(pair),
                    count(cell["hands"], "a baseline cell's hands"),
                    tuple(facts),
                    tuple(params_of(cell)),
                    count(cell["seed"], "a cell's seed"),
                )
            return found

        baseline_pairs = {
            frozenset((left, right))
            for index, left in enumerate(BASELINES)
            for right in BASELINES[index + 1:]
        }
        self.assertEqual(
            set(baseline_cells_of(matrix)),
            baseline_pairs,
            "the three baseline cells are rows and columns of the version's table too, "
            "at its one hand count (matrix.md §1, §4, league.md §3): %r"
            % (sorted(tuple(sorted(pair)) for pair in baseline_cells_of(matrix)),),
        )
        for key in ("k4", "k5"):
            with self.subTest(reproduced_against=key):
                self.assertEqual(
                    baseline_cells_of(matrix),
                    baseline_cells_of(self.shared_matrix(key)),
                    "the three baselines are built at the table seed and their member "
                    "positions, and the cells at the table seed and the pair positions, "
                    "so the same three baseline cells appear in the table holding the "
                    "version as in the %s table that holds none (matrix.md §3-§4, G13)"
                    % (key,),
                )


if __name__ == "__main__":
    unittest.main()
