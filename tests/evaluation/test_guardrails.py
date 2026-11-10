"""EVL-11 — one case per numbered guardrail of `docs/L3/evaluation/guardrails.md`.

Each case is named after the guardrail id it drives (`EVL-11.g1` ... `EVL-11.g21`,
plus `EVL-11.g31` for the shape's absence rule) and asserts the external behaviour
that guardrail says is at risk: a plausible implementation that breaks the contract it
names is red here. The cases reuse the support module's invented instances, hand-built
records and the two shared real matrices, so each one is a focused check and not a
second copy of the whole battery. Three of them carry D-29: G7's read-back now has
seven keys with `game` among them (`shape.md` §4), G14's matrix record requires its own
`game`, and G21's header family is the record's header **plus** the resolved `shape`.

Two guardrails are read carefully:

* **G8.** The four derivations are `scheduler.md` §3's tagged digests and the fifth is
  one modulo, which `EVL-11.g8` recomputes in the case, so `seed + i`,
  `random.Random(seed)` or a counter is red. G8's caught-by clause pairs that with the
  stream rule exactly as the design now states it: in a clean interpreter the nine
  entry points that play nothing leave Python's global `random` stream where they
  found it, while `match` and `matrix` move it only through `engine.new_hand`
  (`surface.md` §1, `engine/surface.md` §4, ASM-2). `EVL-11.g8` therefore calls the nine
  non-playing entry points between two reads of the stream and asserts it unchanged; it
  does not read `random.random()` across a whole `match` or `matrix`, because those
  play and so legitimately move the stream through `engine.new_hand`
  (`guardrails.md` G8).
* **G22** is the command list that runs both batteries; it is a procedure and not an
  observable of this module, so it has no case here (`guardrails.md` header: a note's
  Unverified clause names what no case drives).
"""

import copy
import json
import os
import unittest

from _evaluation_support import (
    BASELINES,
    FAMILIES,
    OPPONENT_SEEDS,
    OTHER_RULE,
    POOL_M,
    REPO_ROOT,
    SEED_SET,
    START_LABEL,
    VERSION_IDS,
    AXIS_ROW,
    EvaluationCase,
    balanced,
    bootstrap_seed,
    cell_directions,
    champion_won_everything,
    chosen_action,
    count,
    declared_internal,
    declaration,
    default_shape,
    direction_counts,
    family_value,
    first_legal,
    hand_matrix,
    interval_bounds,
    lopsided,
    matrix_cells,
    matrix_member_ids,
    member_id,
    member_ids_of_cell,
    no_file_reads,
    other_shape,
    params_of,
    pool_digest,
    pool_member_ids,
    probe_readouts,
    rating_entries,
    rating_record,
    report_inputs,
    run_record,
    seat_split_counts,
    shapes,
    token,
    unlabelled_of,
    version_chain,
    version_record,
)


class GuardrailsTest(EvaluationCase):
    def test_evl_11_g1_eleven_names_and_all_in_the_l1_order(self):
        """EVL-11.G1 `__init__.py` exports exactly the eleven names of `README.md` §3 in that order and no twelfth -- not `Pool`, not `EvaluationError`, not `TABLE_SEED` (`e2e-surface.md` §1, D-12)."""
        package = self.evaluation()
        exported = tuple(getattr(package, "__all__", ()))
        expected = (
            "protocol",
            "league",
            "build_pool",
            "pool_members",
            "offer",
            "opponent",
            "match",
            "matrix",
            "rating",
            "policy_from",
            "report",
        )
        self.assertEqual(
            exported,
            expected,
            "the package exports exactly the eleven entry points of e2e-surface.md §3.4 "
            "in that order (README.md §3, D-12, G1): %r" % (exported,),
        )
        for name in ("Pool", "_MemberPolicy", "EvaluationError", "TABLE_SEED", "BOUND"):
            with self.subTest(name=name):
                self.assertNotIn(
                    name,
                    exported,
                    "%r lives below an entry point and is not a twelfth surface name "
                    "(README.md §3, G1): %r" % (name, exported),
                )

    def test_evl_11_g2_the_pool_id_is_that_digest_and_no_other(self):
        """EVL-11.G2 `"pool-" + sha256(payload).hexdigest()[:16]` with one line per member -- a baseline's id alone, a version's id, `\\x1f`, its rule -- and `m`, `frozen` and every other member field excluded; a digest over the ids alone, over member records, a `repr` or a salted `hash()` is red (`families.md` §4, ASM-27)."""
        package = self.evaluation()
        chain = version_chain(VERSION_IDS[:3])
        pool = package.build_pool(declaration(members=chain, m=POOL_M, frozen=True))
        read = package.pool_members(pool)
        ids = pool_member_ids(read)
        self.assertEqual(
            read["id"],
            pool_digest(read["members"]),
            "the pool id is the SHA-256 digest of the ordered member lines, truncated to "
            "16 hex characters and prefixed `pool-` (families.md §4, ASM-27): %r"
            % (read["id"],),
        )
        renamed = [dict(record) for record in chain]
        renamed[1]["step"] = 4444
        renamed[1]["seed"] = 4444
        with self.subTest(case="member fields excluded"):
            other = package.build_pool(declaration(members=renamed, m=POOL_M, frozen=True))
            self.assertEqual(
                package.pool_members(other)["id"],
                read["id"],
                "the digest excludes every member field but the id and the rule, so a "
                "corrected seed or step does not rename the pool (families.md §4, ASM-27)",
            )
        with self.subTest(case="the rule is inside the payload"):
            other_rule = [dict(record, rule=OTHER_RULE) for record in chain]
            relabelled = package.build_pool(
                declaration(members=other_rule, m=POOL_M, frozen=True)
            )
            self.assertNotEqual(
                package.pool_members(relabelled)["id"],
                read["id"],
                "the digest carries each version's rule, so two pools of one membership "
                "under two estimators do not wear one id (families.md §4, ASM-27)",
            )
        with self.subTest(case="bound and flag excluded"):
            bound = package.build_pool(declaration(members=chain, m=2, frozen=False))
            self.assertEqual(
                package.pool_members(bound)["id"],
                pool_digest(package.pool_members(bound)["members"]),
                "m and frozen are excluded from the payload and the id is recomputed "
                "over the membership alone (families.md §4, ASM-27): %r"
                % (package.pool_members(bound)["id"],),
            )
        with self.subTest(case="membership change"):
            grown = package.build_pool(
                declaration(members=version_chain(VERSION_IDS[:4]), m=4, frozen=True)
            )
            self.assertNotEqual(
                package.pool_members(grown)["id"],
                read["id"],
                "the id changes when and only when the membership does (pool.md §4, "
                "records.md §8, G2)",
            )

    def test_evl_11_g3_the_baselines_come_first_pinned_with_the_id_that_is_their_name(self):
        """EVL-11.G3 `build_pool` prepends `random`, `always-call`, `oracle` in `agents.baselines()`'s order, each `{id, baseline: True, pinned: True, params: 0}`, and `offer` never evicts one (`pool.md` §2, §6)."""
        package = self.evaluation()
        pool = package.build_pool(
            declaration(members=version_chain(VERSION_IDS[:POOL_M]), m=POOL_M, frozen=False)
        )
        read = package.pool_members(pool)
        for index, name in enumerate(BASELINES):
            with self.subTest(baseline=name):
                record = read["members"][index]
                self.assertEqual(
                    member_id(record),
                    name,
                    "a baseline's id is its name, in agents.baselines()'s order "
                    "(pool.md §2, G3): %r" % (member_id(record),),
                )
                self.assertTrue(
                    bool(record.get("baseline")) and bool(record.get("pinned")),
                    "a baseline is pinned and never evicted (pool.md §2, G3): %r"
                    % (record,),
                )
                self.assertEqual(
                    int(record.get("params", -1)),
                    0,
                    "a baseline's params is the catalogue's zero (pool.md §2, "
                    "agents/surface.md §11, G3): %r" % (record,),
                )
        newest = read["members"][-1]
        advanced = package.offer(
            pool,
            version_record(VERSION_IDS[POOL_M], member_id(newest), step=800, samples=800),
        )
        self.assertEqual(
            pool_member_ids(package.pool_members(advanced))[:3],
            BASELINES,
            "offer never evicts a baseline: the three pinned members stay first "
            "(pool.md §6 step 4, G3)",
        )

    def test_evl_11_g4_the_lineage_order_is_the_links_not_the_declaration_s_order(self):
        """EVL-11.G4 `_families` follows `lineage == id` from a start, refuses two members descending from one and a chain reaching no start, and orders the families by the position of each one's start in the declaration (`families.md` §1-§2, G4)."""
        package = self.evaluation()
        records = version_chain(VERSION_IDS[:4])
        shuffled = [records[2], records[0], records[3], records[1]]
        ids = pool_member_ids(
            package.pool_members(
                package.build_pool(declaration(members=shuffled, m=4, frozen=True))
            )
        )
        self.assertEqual(
            ids,
            BASELINES + VERSION_IDS[:4],
            "the window follows the lineage links and not the declaration's order, step "
            "or samples (pool.md §3, G4): %r" % (ids,),
        )
        two_successors = (
            version_record(VERSION_IDS[0], START_LABEL, step=1),
            version_record(VERSION_IDS[1], VERSION_IDS[0], step=2),
            version_record(VERSION_IDS[2], VERSION_IDS[0], step=3),
        )
        self.assert_evaluation_refusal(
            package.build_pool,
            declaration(members=two_successors, m=3, frozen=True),
            entry="build_pool",
            groups=(("lineage",),),
            label="two members descending from one",
        )
        cycle = (
            version_record(VERSION_IDS[0], VERSION_IDS[1], step=1),
            version_record(VERSION_IDS[1], VERSION_IDS[0], step=2),
        )
        self.assert_evaluation_refusal(
            package.build_pool,
            declaration(members=cycle, m=3, frozen=True),
            entry="build_pool",
            groups=(("lineage",),),
            label="a chain that reaches no start",
        )

    def test_evl_11_g5_a_rich_declaration_is_windowed_never_refused_and_frozen_is_a_flag(self):
        """EVL-11.G5 a declaration holding more than `m` versions keeps its last `m`; `m` above the league's M is refused and `m` ≤ M is not; `frozen` must be a boolean and is stored, not interpreted (`pool.md` §2)."""
        package = self.evaluation()
        records = version_chain(VERSION_IDS[:5])
        windowed = package.build_pool(declaration(members=records, m=2, frozen=True))
        self.assertEqual(
            pool_member_ids(package.pool_members(windowed)),
            BASELINES + VERSION_IDS[3:5],
            "a declaration richer than the bound holds its last m versions and is "
            "windowed, never refused (pool.md §2, league.md §2, G5)",
        )
        league_m = int(package.league()["m"])
        for bound in (1, POOL_M, league_m):
            with self.subTest(bound=bound):
                declared = package.build_pool(
                    declaration(members=version_chain(VERSION_IDS[:5]), m=bound, frozen=True)
                )
                self.assertEqual(
                    int(package.pool_members(declared)["m"]),
                    bound,
                    "a declaration may be tighter than M and never wider, and m <= M is "
                    "not refused (pool.md §2, D-16, G5): %r" % (bound,),
                )
        self.assert_evaluation_refusal(
            package.build_pool,
            declaration(members=(), m=league_m + 1, frozen=True),
            entry="build_pool",
            groups=(("m", "bound"),),
            label="a bound above the league's M",
        )
        with self.subTest(flag="a string is not a flag"):
            self.assert_evaluation_refusal(
                package.build_pool,
                {"members": [], "m": 2, "frozen": "yes"},
                entry="build_pool",
                groups=(("frozen",),),
                label="a string frozen flag",
            )
        with self.subTest(flag="stored not interpreted"):
            unfrozen = package.build_pool(declaration(members=(), m=2, frozen=False))
            self.assertFalse(
                bool(package.pool_members(unfrozen)["frozen"]),
                "frozen is stored, not interpreted: build_pool freezes what the "
                "declaration says to freeze (pool.md §2 step 3, G5)",
            )

    def test_evl_11_g6_offer_drops_the_oldest_and_nothing_else_and_returns_a_new_pool(self):
        """EVL-11.G6 the offered version joins the head, the oldest leaves when the window is full, the baselines stay, the argument pool is unchanged and the id is recomputed -- mutating the argument, or evicting by `samples` rather than by window position, is red (`pool.md` §6)."""
        package = self.evaluation()
        records = version_chain(VERSION_IDS[:POOL_M])
        # The oldest member carries the largest `samples`, so an eviction by samples
        # would drop the wrong member.
        records[0] = dict(records[0], samples=999999, step=999)
        pool = package.build_pool(declaration(members=records, m=POOL_M, frozen=False))
        before = package.pool_members(pool)
        newcomer = version_record(
            VERSION_IDS[POOL_M], records[-1]["id"], step=1, samples=1
        )
        advanced = package.offer(pool, newcomer)
        after = package.pool_members(advanced)
        versions = [name for name in pool_member_ids(after) if name not in BASELINES]
        self.assertEqual(
            versions,
            list(VERSION_IDS[1:POOL_M]) + [VERSION_IDS[POOL_M]],
            "offer drops the oldest window position and nothing else, not the member "
            "with the fewest samples (pool.md §6 step 4, G6): %r" % (versions,),
        )
        self.assertEqual(
            after["id"],
            pool_digest(after["members"]),
            "the advanced pool's id is recomputed over its new ordered member lines "
            "(families.md §4, §5, G6): %r" % (after["id"],),
        )
        self.assertEqual(
            package.pool_members(pool),
            before,
            "offer returns a new pool and leaves its argument unchanged (pool.md §6, "
            "surface.md §7, G6)",
        )

    def test_evl_11_g7_pool_members_returns_the_record_and_the_version_records_verbatim(self):
        """EVL-11.G7 `pool_members` is `{id, m, frozen, game, members, rules, utilities}` freshly built per call -- `game` **required**, naming the one shape the pool is on, so a read-back that omits it or reads it off a member is red -- and each version the `records.md` §7 record the declaration carried, its `rule`, its `utility` and its `game` untouched (`pool.md` §5, `records.md` §8, §7, `shape.md` §4, D-19, D-20, D-29)."""
        package = self.evaluation()
        declared = version_chain(VERSION_IDS[:2])
        pool = package.build_pool(declaration(members=declared, m=POOL_M, frozen=True))
        first = package.pool_members(pool)
        self.assertEqual(
            set(first),
            {"id", "m", "frozen", "game", "members", "rules", "utilities"},
            "a pool record is records.md §8's seven required keys, `game` beside `rules` "
            "and `utilities` (pool.md §5, records.md §8, shape.md §4, D-19, D-20, D-29): "
            "%r" % (tuple(first),),
        )
        self.assertEqual(
            first["game"],
            default_shape(),
            "the read-back names the one shape the pool is on, and a declaration that "
            "named none is the default -- read off the **pool** and not off a member, "
            "which names no shape at all (pool.md §5, shape.md §2, §4, G7): %r"
            % (first["game"],),
        )
        first["members"] = ()
        first["id"] = "pool-0000000000000000"
        self.assertEqual(
            package.pool_members(pool)["id"],
            pool_digest(package.pool_members(pool)["members"]),
            "the read-back is freshly built, so a caller that edits it changes nothing "
            "(pool.md §5, G7)",
        )
        versions = package.pool_members(pool)["members"][3:]
        for index, record in enumerate(declared):
            with self.subTest(member=record["id"]):
                for key, value in record.items():
                    self.assertEqual(
                        versions[index].get(key),
                        value,
                        "each version reads back as the records.md §7 record the "
                        "declaration carried, %r untouched (pool.md §5, G7): %r"
                        % (key, versions[index]),
                    )
                self.assertEqual(
                    set(versions[index]),
                    set(record),
                    "and a version that declared no `game` reads back with **none**: "
                    "absence is the default shape and is never filled in, so the record "
                    "gains no key (pool.md §5, shape.md §2, §4, G7): %r"
                    % (versions[index],),
                )
        with self.subTest(case="the shape is the pool's, on either shape"):
            for shape in shapes():
                built = package.build_pool(declaration(members=(), m=5, frozen=True, game=shape))
                self.assertEqual(
                    package.pool_members(built)["game"],
                    shape,
                    "a baselines-only pool carries the declaration's shape even though no "
                    "member names one, so the fact is the pool's and never a member's "
                    "(pool.md §5, shape.md §4, G7): %r" % (shape,),
                )
        with self.subTest(case="a member of the pool's other shape reads back with it"):
            declared_with_shape = version_chain(VERSION_IDS[:2], game=other_shape())
            other = package.build_pool(
                declaration(members=declared_with_shape, m=POOL_M, frozen=True, game=other_shape())
            )
            read = package.pool_members(other)
            self.assertEqual(
                read["game"],
                other_shape(),
                "the record names the shape the pool was declared on (pool.md §5, "
                "shape.md §3-§4): %r" % (read["game"],),
            )
            for record in read["members"][3:]:
                self.assertEqual(
                    record.get("game"),
                    other_shape(),
                    "a member that declared the pool's shape reads back with it, "
                    "untouched (records.md §7, shape.md §4, G7): %r" % (record,),
                )

    def test_evl_11_g8_every_seed_is_a_derivation_and_no_stream_is_seeded_here(self):
        """EVL-11.G8 the four tagged derivations are `int.from_bytes(sha256(...).digest()[:8], "big") % 2**31` over the parts joined by `\\x1f`, `_draw_index` is a modulo, and every entry point that plays nothing leaves the global stream where it found it (`scheduler.md` §3, `surface.md` §1, ASM-2)."""
        from _evaluation_support import (
            BOOTSTRAP_TAG,
            CELL_TAG,
            HAND_TAG,
            MATCH_SEED,
            MEMBER_TAG,
            cell_seed,
            draw_index,
            hand_seed,
            member_seed,
        )

        package = self.evaluation()
        hand = declared_internal("seeds", "_hand_seed")
        cell = declared_internal("seeds", "_cell_seed")
        member = declared_internal("seeds", "_member_seed")
        boot = declared_internal("seeds", "_bootstrap_seed")
        drawn = declared_internal("seeds", "_draw_index")
        derivations = (
            ("_hand_seed", hand, (MATCH_SEED, 4), hand_seed),
            ("_cell_seed", cell, (MATCH_SEED, 1, 3), cell_seed),
            ("_member_seed", member, (MATCH_SEED, 2), member_seed),
            ("_bootstrap_seed", boot, (MATCH_SEED,), bootstrap_seed),
        )
        for name, fn, args, expected in derivations:
            with self.subTest(derivation=name):
                self.assertEqual(
                    fn(*args),
                    expected(*args),
                    "%s is the tagged SHA-256 digest of scheduler.md §3, not seed+i, "
                    "random.Random(seed), a counter or a path digest (G8): %r != %r"
                    % (name, fn(*args), expected(*args)),
                )
        self.assertEqual(
            drawn(MATCH_SEED, 7),
            draw_index(MATCH_SEED, 7),
            "_draw_index is the seed's position in the membership, seed %% n, and not a "
            "digest (scheduler.md §3, G8)",
        )
        matrix = hand_matrix(balanced)
        rating = rating_record(matrix)
        record = run_record(matrix, rating)
        probe_readouts(2)
        before = self.stream_state()
        package.protocol()
        package.league()
        package.build_pool(declaration(members=(), m=5, frozen=True))
        pool = package.build_pool(declaration(members=(), m=5, frozen=False))
        package.pool_members(pool)
        package.offer(pool, version_record(VERSION_IDS[0], START_LABEL))
        package.opponent(pool, OPPONENT_SEEDS[0])
        package.rating(matrix)
        package.policy_from(self.checkpoint(name="member")["path"])
        package.report(*report_inputs(matrix, rating))
        self.assert_stream_unchanged(before, "the nine entry points that play nothing")

    def test_evl_11_g9_seats_alternate_and_seat_split_carries_two_counts(self):
        """EVL-11.G9 hand `i` gives seat 0 to `left` when `i` is even; `seat_split` is keyed `seat 0`/`seat 1` and its two values sum to `hands` and differ by at most one (`scheduler.md` §2, G9)."""
        package = self.evaluation()
        hands = 11
        cell = package.match("random", "always-call", hands, OPPONENT_SEEDS[1])
        for index, direction in enumerate(cell_directions(cell)):
            split = direction["seat_split"]
            with self.subTest(direction=index):
                self.assertEqual(
                    {token(key) for key in split},
                    {"seat0", "seat1"},
                    "seat_split is keyed by the engine's seat order and not by "
                    "button/big blind (scheduler.md §2, G9): %r" % (split,),
                )
                seat0, seat1 = seat_split_counts(split)
                self.assertEqual(
                    seat0 + seat1,
                    hands,
                    "the two counts cover every hand of the cell (scheduler.md §2, G9): %r"
                    % (split,),
                )
                self.assertLessEqual(
                    abs(seat0 - seat1),
                    1,
                    "seats alternate, so the counts differ by at most one "
                    "(scheduler.md §2, G9): %r" % (split,),
                )

    def test_evl_11_g10_a_hand_s_class_is_the_sign_of_its_delta_and_directions_mirror(self):
        """EVL-11.G10 the hand's class comes from `play_hand`'s `payoffs`, the two directions are exact mirrors and the two means exact negations because both are one integer total over the same hands (`scheduler.md` §4, G10)."""
        package = self.evaluation()
        cell = package.match("random", "always-call", 12, OPPONENT_SEEDS[2])
        hands = count(cell["hands"], "a cell's hands")
        left, right = cell_directions(cell)
        left_counts = direction_counts(left, "the left direction")
        right_counts = direction_counts(right, "the right direction")
        self.assert_plain_counts(left_counts, hands, "the left direction")
        self.assert_plain_counts(right_counts, hands, "the right direction")
        self.assertEqual(
            (left_counts[0], left_counts[1], left_counts[2]),
            (right_counts[2], right_counts[1], right_counts[0]),
            "one direction's wins are the other's losses and a tied hand is a tie for "
            "both (scheduler.md §4, G10): %r vs %r" % (left_counts[:3], right_counts[:3]),
        )
        self.assertEqual(
            left_counts[3],
            -right_counts[3],
            "the two mean chip deltas are exact negations (scheduler.md §4, G10): %r vs %r"
            % (left_counts[3], right_counts[3]),
        )

    def test_evl_11_g11_params_is_two_integers_and_unlabelled_names_the_unmeasured_zeros(self):
        """EVL-11.G11 `params` holds one plain integer per member, position-aligned with `members`; a variant handed in as an opaque policy gets `0` **and** its id in `unlabelled`, at the cell and at the table (`scheduler.md` §4, `matrix.md` §5)."""
        package = self.evaluation()
        cell = package.match(first_legal, "always-call", 9, OPPONENT_SEEDS[3])
        self.assertEqual(
            params_of(cell),
            [0, 0],
            "an opaque policy's zero is unmeasured and a baseline's is the catalogue's "
            "(scheduler.md §4, G11): %r" % (cell["params"],),
        )
        self.assertEqual(
            tuple(unlabelled_of(cell)),
            ("policy-1",),
            "the cell names the id whose params is an unmeasured 0 (scheduler.md §4, "
            "G11): %r" % (unlabelled_of(cell),),
        )
        matrix = self.shared_matrix("k5")
        self.assertEqual(
            tuple(unlabelled_of(matrix)),
            ("variant-2",),
            "the table names the opaque variant's unmeasured zero, so a reader tells a "
            "measured 0 from an unmeasured one (matrix.md §5, G11): %r"
            % (unlabelled_of(matrix),),
        )

    def test_evl_11_g12_the_membership_order_and_the_pair_enumeration_are_both_fixed(self):
        """EVL-11.G12 `members` is the pool's members then `variant-1`, `variant-2`, and `cells` is `(0,1) (0,2) … (1,2) …`, K(K-1)/2 of them, one per unordered pair (`matrix.md` §1-§2, G12)."""
        matrix = self.shared_matrix("k5")
        members = matrix_member_ids(matrix)
        self.assertEqual(
            members[:3],
            BASELINES,
            "the pool's members come first, in pool_members' order (matrix.md §1, "
            "G12): %r" % (members,),
        )
        self.assertEqual(
            members[3:],
            ("variant-1", "variant-2"),
            "a variant is named by its slot in the argument list, whatever it carries "
            "(matrix.md §1, G12): %r" % (members,),
        )
        cells = matrix_cells(matrix)
        expected = [
            (i, j) for i in range(len(members)) for j in range(i + 1, len(members))
        ]
        self.assertEqual(
            [tuple(members.index(name) for name in member_ids_of_cell(cell)) for cell in cells],
            expected,
            "the cells are matrix.md §2's enumeration, one per unordered pair and no "
            "repeat (matrix.md §2, G12): %r" % (expected,),
        )

    def test_evl_11_g13_every_cell_is_played_at_the_table_s_one_hand_count(self):
        """EVL-11.G13 every cell gets `league()["tables"][table]["hands_per_cell"]`, the three baseline cells included -- a cheaper cell for a baseline, or a count derived from a wall clock, is red (`matrix.md` §6, `league.md` §3, ASM-15)."""
        package = self.evaluation()
        matrix = self.shared_matrix("k5")
        declared = int(package.league()["tables"][matrix["table"]]["hands_per_cell"])
        for cell in matrix_cells(matrix):
            with self.subTest(pair=member_ids_of_cell(cell)):
                self.assertEqual(
                    count(cell["hands"], "a cell's hands"),
                    declared,
                    "every cell of a table is played at the one declared hand count, "
                    "baseline cells included (matrix.md §6, league.md §3, G13): %r"
                    % (cell["hands"],),
                )
        for cell in matrix_cells(matrix):
            if set(member_ids_of_cell(cell)) <= set(BASELINES):
                with self.subTest(baseline_cell=member_ids_of_cell(cell)):
                    self.assertEqual(
                        count(cell["hands"], "a baseline cell's hands"),
                        count(matrix["hands_per_cell"], "hands_per_cell"),
                        "no baseline cell is cheaper than a model cell (matrix.md §4, "
                        "G13): %r" % (cell["hands"],),
                    )

    def test_evl_11_g14_the_matrix_record_s_carries_its_keys_and_a_table_seed_no_argument_supplies(self):
        """EVL-11.G14 `members`, `cells`, `rules`, `population`, `utilities`, `utility_population`, `hands_per_cell`, `table_seed`, `table`, then this module's own `game` (**required**), `pool`, `member_records`, `unlabelled`, `cell_count`; `table_seed` is the league's, a second seed argument does not exist, and `table` is the label as a value (`matrix.md` §5, §7, `records.md` §10, `shape.md` §4, G14, D-19, D-20, D-29)."""
        package = self.evaluation()
        matrix = self.shared_matrix("k4")
        self.assertEqual(
            tuple(matrix),
            (
                "members",
                "cells",
                "rules",
                "population",
                "utilities",
                "utility_population",
                "hands_per_cell",
                "table_seed",
                "table",
                "game",
                "pool",
                "member_records",
                "unlabelled",
                "cell_count",
            ),
            "the matrix record's keys and their order are matrix.md §5's, `game` after the "
            "nine records.md §10 keys and before this module's other four (G14, "
            "shape.md §4): %r" % (tuple(matrix),),
        )
        self.assertEqual(
            matrix["game"],
            self.pool_members(self.shared_pool("k4"))["game"],
            "a table's shape is the pool's and it takes no shape argument, so the record "
            "names the shape of the pool it measured (matrix.md §1, §5, shape.md §4, "
            "G14): %r" % (matrix["game"],),
        )
        self.assertEqual(
            count(matrix["table_seed"], "a matrix's table_seed"),
            int(package.league()["table_seed"]),
            "a matrix is played from the league's one declared table seed, and takes no "
            "seed argument (matrix.md §3, declarations.md §6, G14): %r"
            % (matrix["table_seed"],),
        )
        self.assertIn(
            matrix["table"],
            ("live", "full"),
            "table is the label as a value (matrix.md §6, G14): %r" % (matrix["table"],),
        )
        self.assertIsInstance(
            matrix["pool"],
            str,
            "the record's `pool` is the pool record's id string and not the pool record "
            "(matrix.md §5, §8, G14): %r" % (matrix["pool"],),
        )
        frozen = package.build_pool(declaration(members=(), m=5, frozen=True))
        self.assert_evaluation_refusal(
            package.matrix,
            frozen,
            [first_legal],
            "live-table",
            entry="matrix",
            groups=(("table",), ("live", "full")),
            label="a table label as a substring",
        )

    def test_evl_11_g15_the_anchor_is_applied_so_the_baselines_mean_is_zero(self):
        """EVL-11.G15 the anchor's shift of `rating.md` §3 step 4 runs inside the loop, so the three baselines' mean is (to floating point) exactly 0 -- a mean of 0.04 is red (`rating.md` §2-§3, ASM-17)."""
        package = self.evaluation()
        rating = package.rating(hand_matrix(lopsided))
        entries = rating_entries(rating)
        baselines = [float(entries[name]["value"]) for name in BASELINES]
        mean = sum(baselines) / len(baselines)
        self.assertLess(
            abs(mean),
            1e-6,
            "the anchor re-centres every iteration, so the three baselines' mean is 0 "
            "and not an unanchored 0.04 (rating.md §3 step 4, G15): %r" % (baselines,),
        )

    def test_evl_11_g16_refuse_exactly_what_the_contract_refuses_with_the_grammar(self):
        """EVL-11.G16 every declared refusal happens with §3's grammar and no other, before the first cell is played, checkpoint loaded or value fitted; and a valid instance -- a rich declaration, a `path`-less member, a hand-built matrix, an explicit `n/a` family -- is not refused (`errors.md` §1, §5, G16)."""
        package = self.evaluation()
        for label, fn, args in (
            ("a bad declaration", package.build_pool, ([],)),
            ("a bad bound", package.build_pool, (declaration(members=(), m=0, frozen=True),)),
            ("a bad hand count", package.match, ("random", "always-call", 0, 1)),
            ("a bad seed", package.opponent, (package.build_pool(declaration(members=(), m=5, frozen=True)), "x")),
            ("a bad matrix", package.rating, ([],)),
        ):
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    fn, *args, entry=self._entry_of(fn), label=label
                )
        rich = package.build_pool(
            declaration(members=version_chain(VERSION_IDS[:5]), m=2, frozen=True)
        )
        self.assertEqual(
            len(pool_member_ids(package.pool_members(rich))),
            5,
            "a declaration richer than the bound is windowed and never refused "
            "(pool.md §2, errors.md §5, G16)",
        )
        pathless = package.build_pool(
            declaration(
                members=[version_record(VERSION_IDS[0], START_LABEL, step=1)],
                m=2,
                frozen=True,
            )
        )
        self.assertIn(
            VERSION_IDS[0],
            pool_member_ids(package.pool_members(pathless)),
            "a member declared without a path is admitted and only a loader refuses it "
            "(surface.md §5, errors.md §5, G16)",
        )
        matrix = hand_matrix(balanced)
        with self.subTest(case="a hand-built matrix with this module's own keys"):
            augmented = dict(matrix, pool="pool-0000000000000000", cell_count=6)
            rating = package.rating(augmented)
            self.assertIn(
                "values",
                rating,
                "a hand-built matrix, and one carrying this module's own keys beside the "
                "required ones, is rated and never refused (rating.md §1, errors.md §5, "
                "G16): %r" % (rating,),
            )
        rung, record, matrix, rating = report_inputs()
        explicit = copy.deepcopy(record)
        explicit["axis row"] = "n/a"
        report = package.report(rung, explicit, matrix, rating)
        self.assertEqual(
            family_value(report, "axis row"),
            "n/a",
            "an explicit `n/a` family is a value and is never refused "
            "(report.md §3, errors.md §5, G16): %r" % (family_value(report, "axis row"),),
        )

    def _entry_of(self, fn):
        """The entry point name one support helper's function carries (`errors.md` §3)."""
        for name in (
            "protocol",
            "league",
            "build_pool",
            "pool_members",
            "offer",
            "opponent",
            "match",
            "matrix",
            "rating",
            "policy_from",
            "report",
        ):
            if getattr(fn, "__name__", "") == name:
                return name
        return "evaluation"

    def test_evl_11_g17_the_bound_is_ten_and_it_never_breaks_the_interval_open(self):
        """EVL-11.G17 a member that won everything has no finite value; the clamped theta is `BOUND = 10.0`, `bound_applied` and that member's own `bounded` are true, and the widened interval still contains the value -- returning an infinity or clipping the interval is red (`rating.md` §3-§4, G17)."""
        package = self.evaluation()
        bound = float(declared_internal("rating", "BOUND"))
        self.assertEqual(
            bound,
            10.0,
            "the fit's bound is 10.0, the largest |theta| it may return (rating.md §3, "
            "G17): %r" % (bound,),
        )
        rating = package.rating(hand_matrix(champion_won_everything))
        entry = rating_entries(rating)["variant-1"]
        value = float(entry["value"])
        low, high = interval_bounds(entry)
        self.assertLessEqual(
            abs(value - bound),
            0.01,
            "the clamp holds a member that won everything at BOUND and never reports an "
            "infinity (rating.md §3, G17): %r" % (value,),
        )
        self.assertTrue(
            bool(rating["bound_applied"]) and bool(entry["bounded"]),
            "both the record and the member's own flag say the bound was applied "
            "(rating.md §5, records.md §11, G17): %r / %r"
            % (rating["bound_applied"], entry.get("bounded")),
        )
        self.assertLessEqual(low, value, "the interval is widened, never clipped (rating.md §4, G17)")
        self.assertGreaterEqual(high, value, "the interval is widened, never clipped (rating.md §4, G17)")

    def test_evl_11_g18_the_bootstrap_resamples_hands_two_hundred_times_from_the_table_seed(self):
        """EVL-11.G18 `RESAMPLES = 200`, the generator is seeded from `_bootstrap_seed(matrix["table_seed"])`, its seed is recorded, and the value lies inside the interval the replicates state (`rating.md` §4, ASM-17, G18)."""
        package = self.evaluation()
        self.assertEqual(
            int(declared_internal("rating", "RESAMPLES")),
            200,
            "the bootstrap draws 200 replicates, one multinomial draw per cell per "
            "replicate (rating.md §4, G18): %r" % (declared_internal("rating", "RESAMPLES"),),
        )
        matrix = hand_matrix(lopsided)
        rating = package.rating(matrix)
        self.assertEqual(
            count(rating["bootstrap_seed"], "a rating's bootstrap_seed"),
            bootstrap_seed(matrix["table_seed"]),
            "the generator is seeded from the matrix's own table seed, through "
            "_bootstrap_seed (rating.md §4, scheduler.md §3, G18): %r"
            % (rating["bootstrap_seed"],),
        )
        for member, entry in rating_entries(rating).items():
            with self.subTest(member=member):
                value = float(entry["value"])
                low, high = interval_bounds(entry)
                self.assertLessEqual(low, value, "the value lies inside its interval (rating.md §4, G18)")
                self.assertGreaterEqual(high, value, "the value lies inside its interval (rating.md §4, G18)")

    def test_evl_11_g19_the_shipped_artefact_is_evidence_and_nothing_reads_it(self):
        """EVL-11.G19 `tables/league-full.json` carries `schema`, `table`, `pool`, `matrix`, `rating`, `provenance` and `cost`, its cost block is a measurement with `device: "cpu"` and no ceiling -- ASM-21 supersedes ASM-15's bound -- its `provenance.member_status` says which player each member is, and no entry point reads the file (`tables.md` §2-§5, ASM-21, G19)."""
        package = self.evaluation()
        shipped = declared_internal("tables", "SHIPPED_PATH")
        path = os.path.join(REPO_ROOT, str(shipped))
        self.assertTrue(
            os.path.isfile(path),
            "the full table ships as one committed data artefact (tables.md §3-§4, "
            "G19): %r is absent" % (path,),
        )
        with open(path, "r", encoding="utf-8") as handle:
            document = json.load(handle)
        for key in ("schema", "table", "pool", "matrix", "rating", "provenance", "cost"):
            with self.subTest(key=key):
                self.assertIn(
                    key,
                    document,
                    "the artefact's top-level keys are tables.md §3's seven (G19): %r"
                    % (tuple(document),),
                )
        self.assertEqual(
            document["schema"],
            "pypoker-evaluation-league-table/1",
            "the artefact names its schema and version (tables.md §3, G19): %r"
            % (document["schema"],),
        )
        cost = document["cost"]
        self.assertTrue(
            bool(cost.get("measured")),
            "the cost block is a measurement (tables.md §5, G19): %r" % (cost,),
        )
        self.assertEqual(
            cost.get("device"),
            "cpu",
            "the artefact records the device that ran it (tables.md §5, G19): %r"
            % (cost.get("device"),),
        )
        self.assertNotIn(
            "per_hand_ceiling_seconds",
            cost,
            "the cost block carries the measurement and no ceiling: ASM-21 ratifies the "
            "measured seconds per hand and supersedes ASM-15's bound "
            "(tables.md §5, ASM-21, G19): %r" % (cost.get("per_hand_ceiling_seconds"),),
        )
        for budget in ("live", "full"):
            with self.subTest(budget=budget):
                self.assertNotIn(
                    "per_hand_ceiling_seconds",
                    package.league()["tables"][budget],
                    msg="league() carries no per-hand figure at all, the bound having been "
                    "superseded (declarations.md §4.1, tables.md §5, ASM-21, G19)",
                )
        before = self.stream_state()
        with no_file_reads("league() and protocol()"):
            package.league()
            package.protocol()
        self.assert_stream_unchanged(before, "league() and protocol()")

    def test_evl_11_g20_policy_from_reads_exactly_two_recorded_facts_and_substitutes_no_seed(self):
        """EVL-11.G20 the seed and the encoding name come from the checkpoint's own container and nothing else: the policy decides as `agents.act` decided, a container recording no seed is `CheckpointRecordMissing` and never patched, and no path digest is a seed (`scheduler.md` §5.1, `surface.md` §12, G20)."""
        package = self.evaluation()
        saved = self.checkpoint(name="member")
        policy = package.policy_from(saved["path"])
        for row in probe_readouts(3):
            with self.subTest(hand=row["seed"]):
                self.assertEqual(
                    policy(row["readout"], row["legal"]),
                    chosen_action(saved["learner"], saved["encoder"], row["readout"]),
                    "a member reached through its path is built at the seed its container "
                    "records, so it decides as its learner did (scheduler.md §5.1, G20)",
                )
        from _evaluation_support import checkpoint_without_seed

        self.assert_evaluation_refusal(
            package.policy_from,
            checkpoint_without_seed(),
            entry="policy_from",
            groups=(("seed",),),
            label="a container recording no seed",
        )
        folder = self.tempdir()
        second = os.path.join(folder, "another-path.ckpt")
        self.agents().save(saved["learner"], second)
        other = package.policy_from(second)
        for row in probe_readouts(2):
            with self.subTest(copy=row["seed"]):
                self.assertEqual(
                    other(row["readout"], row["legal"]),
                    policy(row["readout"], row["legal"]),
                    "two paths of one learner are one player, so the seed is the recorded "
                    "one and never a digest of the path (scheduler.md §5.1, G20): %r"
                    % (policy(row["readout"], row["legal"]),),
                )

    def test_evl_11_g21_report_copies_and_never_invents(self):
        """EVL-11.G21 each of the seven families is copied by value from the record under `protocol()`'s spelling, `axis row` included -- except the header, which is that record's header **plus** the tenth key `shape` the report resolved, written on the report's own copy -- R1's pool row is the baselines it had, the single-variant axis row stays `n/a, single variant`, and the seeds, table, table seed and device travel beside them (`report.md` §1-§2, §4, `shape.md` §4, G21, G35, D-29)."""
        package = self.evaluation()
        rung, record, matrix, rating = report_inputs()
        report = package.report(rung, record, matrix, rating)
        for family in FAMILIES:
            with self.subTest(family=family):
                if family == "header":
                    self.assertEqual(
                        family_value(report, family),
                        dict(record[family], shape=default_shape()),
                        "the header family is the record's own nine items and the one "
                        "shape the report resolved, completed on the report's copy and "
                        "never in the argument (report.md §1-§2, shape.md §4, G21, "
                        "G35): %r" % (family_value(report, family),),
                    )
                    self.assertEqual(
                        dict(family_value(report, family), shape=None),
                        dict(dict(record[family]), shape=None),
                        "the completion adds `shape` and changes no item the record "
                        "states, so every other header item is copied unchanged "
                        "(report.md §2, G21, G35): %r" % (family_value(report, family),),
                    )
                else:
                    self.assertEqual(
                        family_value(report, family),
                        record[family],
                        "every other family is copied by value from the record and never "
                        "invented, reshaped or sorted (report.md §2, §4, G21): %r"
                        % (family_value(report, family),),
                    )
        self.assertNotIn(
            "shape",
            dict(record["header"]),
            "the completion is written onto the report's own copy and never into the "
            "record it was handed (report.md §4, shape.md §4, G35)",
        )
        self.assertEqual(
            pool_member_ids(family_value(report, "pool")),
            BASELINES,
            "R1's pool row is the three baselines it had, and no version is invented "
            "(report.md §4, league.md §2, G21): %r"
            % (pool_member_ids(family_value(report, "pool")),),
        )
        self.assertEqual(
            family_value(report, "axis row"),
            AXIS_ROW,
            "a single-variant rung's axis row stays the string `n/a, single variant` and "
            "is not wrapped into a record (report.md §2, §4, G21): %r"
            % (family_value(report, "axis row"),),
        )
        self.assertEqual(
            tuple(report["seeds"]),
            SEED_SET,
            "the seeds travel beside the families (report.md §2, G21): %r"
            % (report.get("seeds"),),
        )
        self.assertEqual(
            report["table"],
            matrix["table"],
            "the table budget travels beside the families (report.md §2, G21): %r"
            % (report.get("table"),),
        )
        self.assertEqual(
            int(report["table seed"]),
            int(matrix["table_seed"]),
            "the table seed travels beside the families (report.md §2, G21): %r"
            % (report.get("table seed"),),
        )
        self.assertEqual(
            report["device"],
            "cpu",
            "the device travels beside the families, so a GPU run and a CPU run are never "
            "confused (report.md §2, protocol.md §6, G21): %r"
            % (report.get("device"),),
        )

    def test_evl_11_g31_an_absent_game_reads_as_the_default_shape_everywhere(self):
        """EVL-11.G31 an absent `game` reads as `DEFAULT_SHAPE` in every record this module returns and every record it accepts -- a pool declaration, a member record, a cell, a matrix, a rating and a report's three records -- and none of them is refused for the absence; only a name that **is** declared and uncatalogued is refused, never mapped onto the default (`shape.md` §2, §4, `errors.md` §5, G31, D-29)."""
        package = self.evaluation()
        default = default_shape()
        with self.subTest(carrier="a pool declaration"):
            silent = declaration(members=(), m=5, frozen=True)
            self.assertNotIn(
                "game",
                silent,
                "the case drives the absence itself and never a named shape "
                "(shape.md §2, G31)",
            )
            self.assertEqual(
                package.pool_members(package.build_pool(silent))["game"],
                default,
                "a declaration that names no shape is a pool on the default one and is "
                "not refused for the silence (pool.md §1, shape.md §2, G31): %r"
                % (package.pool_members(package.build_pool(silent))["game"],),
            )
        with self.subTest(carrier="a member record"):
            member = version_record(VERSION_IDS[0], START_LABEL, step=2)
            self.assertNotIn("game", member, "the member record names no shape (records.md §7)")
            pool = package.build_pool(declaration(members=[member], m=POOL_M, frozen=True))
            self.assertIn(
                VERSION_IDS[0],
                self.members_of(pool),
                "a version record that names no shape is a default-shape member and is "
                "admitted, the default shape being the absence and not a defaulting "
                "(records.md §7, shape.md §2, §4, G31): %r" % (self.members_of(pool),),
            )
        with self.subTest(carrier="a cell"):
            cell = package.match("random", "always-call", 2, OPPONENT_SEEDS[2])
            self.assertEqual(
                cell["game"],
                default,
                "a cell whose two sides name no shape is played on the default shape "
                "and says so (scheduler.md §1, §4, shape.md §4, G31): %r"
                % (cell["game"],),
            )
        with self.subTest(carrier="a matrix"):
            matrix = hand_matrix(balanced)
            self.assertNotIn("game", matrix, "the hand-built table names no shape")
            self.assertFalse(
                [cell for cell in matrix_cells(matrix) if "game" in cell],
                "no cell of it names a shape either, so the absence is the table's "
                "and its cells' both (rating.md §6, shape.md §2, G31)",
            )
            rating = package.rating(matrix)
            self.assertEqual(
                rating["game"],
                default,
                "a matrix with no shape anywhere is rated as the default shape's, which "
                "is what keeps every table already recorded ratable and every rating "
                "already fitted readable (rating.md §1, §6, shape.md §2, G31): %r"
                % (rating["game"],),
            )
        with self.subTest(carrier="a report's three records"):
            rung, record, matrix, rating = report_inputs()
            self.assertNotIn("game", record, "the run record names no shape")
            self.assertNotIn(
                "game",
                record["pool"],
                "the pool family names no shape either, and a report completes nothing "
                "into it (report.md §2, shape.md §4, G35)",
            )
            report = package.report(rung, record, matrix, rating)
            self.assertEqual(
                family_value(report, "header")["shape"],
                default,
                "a run record, a pool family and a matrix that name no shape are one "
                "shape -- the default -- and the report says so without refusing any of "
                "the three (report.md §3 item 6, shape.md §2, §4, G31): %r"
                % (family_value(report, "header"),),
            )
        with self.subTest(carrier="a version-1-to-3 container"):
            saved = self.checkpoint(name="member")
            self.assertEqual(
                package.policy_from(saved["path"]).game,
                default,
                "a container that records no shape -- a version-1, 2 or 3 one, which is "
                "what a default-shape save writes -- is a default-shape member, which is "
                "what keeps the 18 shipped containers loadable (scheduler.md §5.1, "
                "shape.md §2, docs/L1/shapes.md §3, §5, G31): %r" % (saved["path"],),
            )
        with self.subTest(carrier="only a declared but uncatalogued name is refused"):
            self.assert_evaluation_refusal(
                package.build_pool,
                dict(declaration(members=(), m=5, frozen=True), game="fixed-limit-40"),
                entry="build_pool",
                groups=(("fixed-limit-40",), (default,), (other_shape(),)),
                label="a declared shape the catalogue does not carry",
                kind="UnknownShape",
            )


if __name__ == "__main__":
    unittest.main()
