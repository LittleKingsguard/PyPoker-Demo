"""EVL-2 — the pool: `build_pool`, `pool_members`, `offer` and `opponent`.

Drives `docs/L3/evaluation/pool.md` §1-§8, `docs/L2/evaluation/surface.md` §5-§8 and
`docs/L1/league.md` §2: the three pinned baselines first in `agents.baselines()`'s
order, the lineage order that *is* the links and not the declaration's order, the
window to `m`, the id's exact digest (`"pool-" + sha256("\\n".join(ids))[:16]`, with
`m`, `frozen` and every member field excluded), the `Path`-less member admitted and
refused only when it must be a policy, `offer`'s eviction of the oldest version and
of nothing else, the read-back that is freshly built each call, and `opponent`'s draw
-- `seed % n`, one member per residue, no stream moved.

The refusals are `pool.md` §8's, and each one is asserted to be this module's own
`EvaluationError` naming the contract (`errors.md` §1-§2): a declaration that is not
a mapping or misses one of §8's three keys, a bound outside `1 … league()["m"]`, a
member without `id` or `lineage`, a declared `path` that names no file, two members
descending from one, a chain that reaches no start, a frozen pool offered into, a
version already a member or not extending the window's newest, a draw that must load
a version carrying no `path`, and a seed that is not an integer.
"""

import os
import unittest

from _evaluation_support import (
    BASELINES,
    DEFAULT_RULE,
    OPPONENT_SEEDS,
    OTHER_RULE,
    POOL_M,
    START_LABEL,
    VERSION_IDS,
    EvaluationCase,
    baseline_members,
    declaration,
    member_id,
    pool_digest,
    pool_member_ids,
    pool_rules,
    probe_readouts,
    version_chain,
    version_record,
)


def unreadable_path(case):
    """A path inside the case's own temporary directory that names no file."""
    return os.path.join(case.tempdir(), "absent-checkpoint.ckpt")


class PoolTest(EvaluationCase):
    def test_evl_2_1_one_declaration_yields_one_ordered_membership(self):
        """EVL-2.1 a declaration becomes the baselines first and then its versions oldest to newest, whatever order the declaration lists them in (`pool.md` §2-§3, `records.md` §8, FAM-6.1)."""
        records = version_chain(VERSION_IDS[:3])
        # Declared newest-first; the window's order is the lineage links, not the list.
        shuffled = [records[2], records[0], records[1]]
        pool = self.frozen_pool(members=shuffled, m=POOL_M)
        read = self.pool_members(pool)
        ids = pool_member_ids(read)
        expected = list(BASELINES) + list(VERSION_IDS[:3])
        self.assertEqual(
            ids,
            tuple(expected),
            "a pool holds the three baselines first and then its versions oldest to "
            "newest, and the order is the lineage links (`pool.md` §2-§3, §5): %r"
            % (ids,),
        )
        self.assertEqual(
            pool_member_ids(self.pool_members(self.evaluation().build_pool(declaration(members=records, m=POOL_M)))),
            tuple(expected),
            "one declaration yields one ordered member list, and listing the same chain "
            "in lineage order gives the same membership (`pool.md` §2, ASM-2): %r"
            % (pool_member_ids(self.pool_members(self.evaluation().build_pool(declaration(members=records, m=POOL_M)))),),
        )

    def test_evl_2_2_the_three_baselines_come_first_pinned_with_the_id_that_is_their_name(self):
        """EVL-2.2 the first three members are `random`, `always-call`, `oracle` in `agents.baselines()`'s order, each `{id, baseline: True, pinned: True, params: 0}` (`pool.md` §2 step 5, `records.md` §8, G3)."""
        pool = self.frozen_pool(members=version_chain(VERSION_IDS[:2]))
        members = self.pool_members(pool)["members"]
        self.assertGreaterEqual(
            len(members),
            3,
            "a pool always holds the three pinned baselines (league.md §2, pool.md §2)",
        )
        for index, name in enumerate(BASELINES):
            with self.subTest(baseline=name, position=index):
                record = members[index]
                self.assertIsInstance(
                    record,
                    dict,
                    "a pool member is the records.md §7/§2 step 5 record (pool.md §5): %r"
                    % (record,),
                )
                self.assertEqual(
                    member_id(record),
                    name,
                    "a baseline's id is its name, in agents.baselines()'s order "
                    "(pool.md §2, README.md §6, G3): %r" % (member_id(record),),
                )
                self.assertTrue(
                    bool(record.get("baseline")),
                    "a pinned baseline is marked `baseline: True` (pool.md §2, G3): %r"
                    % (record,),
                )
                self.assertTrue(
                    bool(record.get("pinned")),
                    "the three baselines are `pinned: True` and never evicted "
                    "(pool.md §2, G3): %r" % (record,),
                )
                self.assertEqual(
                    int(record.get("params", -1)),
                    0,
                    "a baseline's parameter count is the zero agents.baselines() declares "
                    "(pool.md §2 step 5, agents/surface.md §11): %r" % (record,),
                )

    def test_evl_2_27_a_declaration_admits_a_folder_pinned_and_refuses_an_unknown_name(self):
        """EVL-2.27 the optional `baselines` key of a membership declaration admits the catalogue's names beyond the flagged three — pinned after them in the catalogue's order, with the id following the membership — and a name the catalogue does not carry is refused naming it; a declaration that names none keeps the membership, the order and the id it had (`records.md` §8, `pool.md` §1, ASM-27, ASM-32, D-21)."""
        package = self.evaluation()
        catalogue = tuple(package.league()["catalogue"])
        pinned = tuple(package.protocol()["baselines"])
        self.assertTrue(
            set(pinned) < set(catalogue),
            "the catalogue carries the flagged three and D-21's folders "
            "(declarations.md §4, ASM-32, D-21): %r against %r" % (pinned, catalogue),
        )
        folders = tuple(name for name in catalogue if name not in pinned)
        self.assertTrue(folders, "the catalogue carries at least one folding baseline")
        plain = self.pool_members(self.frozen_pool(members=()))
        self.assertEqual(
            tuple(member_id(record) for record in plain["members"]),
            pinned,
            "a declaration naming no folder holds the flagged three, in that order "
            "(records.md §8, ASM-32, D-21)",
        )
        admitted = self.pool_members(
            package.build_pool(
                {
                    "members": (),
                    "m": 5,
                    "frozen": True,
                    "baselines": list(reversed(folders)),
                }
            )
        )
        self.assertEqual(
            tuple(member_id(record) for record in admitted["members"]),
            pinned + folders,
            "the declared folders join after the anchor three, in the catalogue's order "
            "rather than the declaration's (pool.md §1, ASM-32, D-21): %r"
            % ([member_id(record) for record in admitted["members"]],),
        )
        for record in admitted["members"][len(pinned):]:
            self.assertTrue(
                bool(record.get("pinned")),
                "a declared folder is pinned like any baseline, because eviction is the "
                "version window's (league.md §2, ASM-32, D-21): %r" % (record,),
            )
        self.assertNotEqual(
            admitted["id"],
            plain["id"],
            "the id is the digest of the membership, so admitting a folder renames the "
            "pool while naming none keeps the id (records.md §8, ASM-27, D-21)",
        )
        for unknown in ("fold-no-pair", "oracle-two", "always-raise"):
            with self.subTest(unknown=unknown):
                with self.assertRaises(Exception) as caught:
                    package.build_pool(
                        {
                            "members": (),
                            "m": 5,
                            "frozen": True,
                            "baselines": [unknown],
                        }
                    )
                self.assertIn(
                    unknown,
                    str(caught.exception),
                    "a name the catalogue does not carry is refused by name, because the "
                    "membership would name a row no rule exists for (records.md §8, "
                    "errors.md §3-§4, D-21): %r" % (str(caught.exception),),
                )

    def test_evl_2_3_a_rich_declaration_is_windowed_and_the_bound_is_checked(self):
        """EVL-2.3 a declaration richer than `m` keeps its last `m` versions and is not refused; `m` from 1 to the league's M is accepted, `0`, a bool and above M are refused naming the bound, and `frozen` must be a boolean (`pool.md` §2, `surface.md` §5, G5)."""
        package = self.evaluation()
        records = version_chain(VERSION_IDS[:5])
        pool = self.frozen_pool(members=records, m=POOL_M)
        ids = pool_member_ids(self.pool_members(pool))
        self.assertEqual(
            ids,
            tuple(BASELINES) + VERSION_IDS[2:5],
            "a declaration richer than the bound is windowed to its last m versions and "
            "never refused (pool.md §2, league.md §2, G5): %r" % (ids,),
        )
        league_m = int(package.league()["m"])
        with self.subTest(bound="the league's M"):
            wide = self.frozen_pool(members=records, m=league_m)
            self.assertEqual(
                len(pool_member_ids(self.pool_members(wide))),
                3 + min(len(records), league_m),
                "m equal to the league's M is a legal declaration (pool.md §2, D-16)",
            )
        with self.subTest(flag="a NumPy boolean is a flag"):
            import numpy as np

            frozen = package.build_pool({"members": [], "m": POOL_M, "frozen": np.bool_(True)})
            self.assertTrue(
                bool(self.pool_members(frozen)["frozen"]),
                "frozen is stored, not interpreted, and a NumPy bool_ is a boolean "
                "(pool.md §2 step 3, errors.md §5)",
            )
        with self.subTest(flag="an unfrozen pool says so"):
            open_pool = self.open_pool(members=records, m=POOL_M)
            self.assertFalse(
                bool(self.pool_members(open_pool)["frozen"]),
                "a declaration's frozen flag is stored and read back "
                "(pool.md §2 step 3, records.md §8)",
            )
        bad = (
            ("a bound of zero", {"members": [], "m": 0, "frozen": True}, (("m",), ("bound",))),
            ("a negative bound", {"members": [], "m": -2, "frozen": True}, (("m",), ("bound",))),
            ("a bound above M", {"members": [], "m": league_m + 1, "frozen": True}, (("m",), ("bound",))),
            ("a bool bound", {"members": [], "m": True, "frozen": True}, (("m",), ("bound",))),
            ("a fractional bound", {"members": [], "m": 2.5, "frozen": True}, (("m",), ("bound",))),
            ("a string flag", {"members": [], "m": 2, "frozen": "yes"}, (("frozen",), ("boolean", "flag"))),
        )
        for label, bad_declaration, groups in bad:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    package.build_pool,
                    bad_declaration,
                    entry="build_pool",
                    groups=groups,
                    label=label,
                )

    def test_evl_2_4_the_id_is_the_declared_digest_and_no_other(self):
        """EVL-2.4 `id == "pool-" + sha256(payload).hexdigest()[:16]` over `pool_members`'s order -- a baseline's id alone, a version's id, `\\x1f`, its rule -- recomputed here (`families.md` §4, G2, ASM-27)."""
        pool = self.frozen_pool(members=version_chain(VERSION_IDS[:3]))
        read = self.pool_members(pool)
        ids = pool_member_ids(read)
        expected = pool_digest(read["members"])
        self.assertEqual(
            read["id"],
            expected,
            "the pool id is sha256 of the payload -- one line per member, a baseline's id "
            "alone and a version's id, \\x1f, its rule -- joined by a single \\n, lowercase "
            "hex truncated to 16 characters and prefixed `pool-` (families.md §4, ASM-27): "
            "got %r for %r, expected %r" % (read["id"], ids, expected),
        )
        self.assertEqual(
            list(read)[0],
            "id",
            "the id is the pool record's first key (pool.md §4, records.md §8): %r"
            % (list(read),),
        )
        self.assertTrue(
            isinstance(read["id"], str) and read["id"].startswith("pool-") and len(read["id"]) == 21,
            "the id is the string `pool-` plus 16 hex characters (pool.md §4, G2): %r"
            % (read["id"],),
        )
        self.assertRegex(
            read["id"][5:],
            r"^[0-9a-f]{16}$",
            "the digest is lowercase hex truncated to 16 characters (pool.md §4, G2): %r"
            % (read["id"],),
        )

    def test_evl_2_5_the_id_changes_when_and_only_when_the_membership_does(self):
        """EVL-2.5 the digest covers the ordered ids and nothing else: a different bound, a different frozen flag or a corrected member field keeps the id, and a membership change moves it (`pool.md` §4, `surface.md` §5, `records.md` §8)."""
        package = self.evaluation()
        chain = version_chain(VERSION_IDS[:2])
        base = self.frozen_pool(members=chain, m=3)
        base_id = self.pool_members(base)["id"]
        same = (
            ("a tighter bound", declaration(members=chain, m=2, frozen=True)),
            ("a wider bound", declaration(members=chain, m=5, frozen=True)),
            ("an unfrozen pool", declaration(members=chain, m=3, frozen=False)),
        )
        for label, declared in same:
            with self.subTest(case=label):
                other = package.build_pool(dict(declared, members=chain))
                self.assertEqual(
                    self.pool_members(other)["id"],
                    base_id,
                    "the id is a function of the ordered member ids and of nothing else, "
                    "so %s does not rename the pool (pool.md §4, surface.md §5)" % label,
                )
        corrected = [dict(record) for record in chain]
        corrected[0]["seed"] = OTHER_SEED_FOR_DIGEST
        corrected[0]["step"] = 777
        with self.subTest(case="a corrected member field"):
            other = self.frozen_pool(members=corrected, m=3)
            self.assertEqual(
                self.pool_members(other)["id"],
                base_id,
                "a corrected seed or step does not rename the pool, because the digest "
                "excludes every member field but the id (pool.md §4)",
            )
        grown = self.frozen_pool(members=version_chain(VERSION_IDS[:3]), m=3)
        self.assertNotEqual(
            self.pool_members(grown)["id"],
            base_id,
            "the id changes when the membership does (pool.md §4, records.md §8, FAM-6.8)",
        )

    def test_evl_2_6_the_lineage_order_is_the_links_not_the_declaration_order(self):
        """EVL-2.6 `_families` follows `lineage == id` from a start, and orders the families by the position of each one's start in the declaration -- sorting by step, by samples or by the declaration's own order is red (`families.md` §1-§2, G4)."""
        records = version_chain(VERSION_IDS[:4])
        shuffled = [records[3], records[1], records[0], records[2]]
        ids = pool_member_ids(self.pool_members(self.frozen_pool(members=shuffled, m=4)))
        self.assertEqual(
            ids,
            tuple(BASELINES) + VERSION_IDS[:4],
            "the window is ordered by the lineage links and not by the declaration's "
            "order or by step/samples (pool.md §3, G4): %r" % (ids,),
        )
        first_chain = version_chain([VERSION_IDS[0], VERSION_IDS[1]])
        second_chain = [
            version_record(VERSION_IDS[2], "other-start-5509"),
            version_record(VERSION_IDS[3], VERSION_IDS[2]),
        ]
        declared = [second_chain[0], second_chain[1], first_chain[0], first_chain[1]]
        two = pool_member_ids(self.pool_members(self.frozen_pool(members=declared, m=5)))
        self.assertEqual(
            two,
            tuple(BASELINES) + (VERSION_IDS[2], VERSION_IDS[3], VERSION_IDS[0], VERSION_IDS[1]),
            "two chains are concatenated in the order their starts are declared, each "
            "oldest to newest (pool.md §3 step 6, G4): %r" % (two,),
        )

    def test_evl_2_7_two_members_descending_from_one_are_refused(self):
        """EVL-2.7 a declaration holding two successors for one link is refused as a lineage conflict, naming the member (`pool.md` §3 step 2, §8, `surface.md` §5, G4)."""
        records = [
            version_record(VERSION_IDS[0], START_LABEL, step=1),
            version_record(VERSION_IDS[1], VERSION_IDS[0], step=2),
            version_record(VERSION_IDS[2], VERSION_IDS[0], step=3),
        ]
        self.assert_evaluation_refusal(
            self.evaluation().build_pool,
            declaration(members=records, m=POOL_M),
            entry="build_pool",
            groups=(("lineage",), ("version-heron-5501",)),
            label="two members descending from one",
        )

    def test_evl_2_8_a_chain_that_reaches_no_start_is_refused(self):
        """EVL-2.8 a declaration whose walk revisits a member is a cycle and is refused, naming a member on it (`pool.md` §3 step 5, §8, `surface.md` §5, G4)."""
        records = [
            version_record(VERSION_IDS[0], VERSION_IDS[1], step=1),
            version_record(VERSION_IDS[1], VERSION_IDS[0], step=2),
        ]
        self.assert_evaluation_refusal(
            self.evaluation().build_pool,
            declaration(members=records, m=POOL_M),
            entry="build_pool",
            groups=(("lineage",), ("start", "cycle", "closes")),
            label="a two-member cycle",
        )

    def test_evl_2_9_offer_never_evicts_a_baseline(self):
        """EVL-2.9 a window already holding `m` versions loses its oldest version and no baseline: the three pinned members are still first and still three (`pool.md` §6 step 4, `surface.md` §7, FAM-6.5)."""
        records = version_chain(VERSION_IDS[:POOL_M])
        pool = self.open_pool(members=records, m=POOL_M)
        newest = records[-1]
        newcomer = version_record(
            VERSION_IDS[POOL_M], newest["id"], seed=OTHER_SEED_FOR_DIGEST, step=900, samples=900
        )
        advanced = self.evaluation().offer(pool, newcomer)
        read = self.pool_members(advanced)
        ids = pool_member_ids(read)
        self.assertEqual(
            ids[:3],
            BASELINES,
            "the three baselines are pinned and never evicted, so they are still the "
            "first three members after an offer (pool.md §6 step 4, FAM-6.5): %r" % (ids,),
        )
        versions = [name for name in ids if name not in BASELINES]
        self.assertEqual(
            versions,
            list(VERSION_IDS[1:POOL_M]) + [VERSION_IDS[POOL_M]],
            "one offer drops the oldest version and nothing else, and the window is "
            "still m versions long (pool.md §6 step 4): %r" % (versions,),
        )
        self.assertNotIn(
            VERSION_IDS[0],
            ids,
            "the evicted member is the oldest evictable version (pool.md §6 step 4, G6): %r"
            % (ids,),
        )

    def test_evl_2_10_build_pool_refuses_what_the_contract_refuses(self):
        """EVL-2.10 a declaration that is not a mapping or misses one of §8's three keys, a member without `id` or `lineage`, a duplicate id, a version declared under one of the three pinned baselines' names and an unreadable declared `path` are refused, naming the key, the member or the path (`pool.md` §2 item 1, §8, `surface.md` §5, `errors.md` §4, G16)."""
        package = self.evaluation()
        missing_path = unreadable_path(self)
        cases = (
            ("not a mapping", [], (("declaration",), ("mapping",))),
            ("missing members", {"m": POOL_M, "frozen": True}, (("members",),)),
            ("missing m", {"members": [], "frozen": True}, (("m",),)),
            ("missing frozen", {"members": [], "m": POOL_M}, (("frozen",),)),
            (
                "a member without an id",
                declaration(members=[{"lineage": START_LABEL}], m=POOL_M),
                (("id",),),
            ),
            (
                "a member without a lineage",
                declaration(members=[{"id": VERSION_IDS[0]}], m=POOL_M),
                (("lineage",),),
            ),
            (
                "an empty id",
                declaration(members=[{"id": "", "lineage": START_LABEL}], m=POOL_M),
                (("id",),),
            ),
            (
                "an id holding a newline",
                declaration(members=[{"id": "version\nsplit", "lineage": START_LABEL}], m=POOL_M),
                (("id",), ("newline", "separator")),
            ),
            (
                "two records carrying one id",
                declaration(
                    members=[
                        version_record(VERSION_IDS[0], START_LABEL, step=1),
                        version_record(VERSION_IDS[0], START_LABEL + "-b", step=2),
                    ],
                    m=POOL_M,
                ),
                (("version-heron-5501",),),
            ),
            (
                "a version declared under a baseline's name",
                declaration(
                    members=[{"id": "random", "lineage": START_LABEL}],
                    m=POOL_M,
                    frozen=True,
                ),
                (("random",), ("baseline",)),
            ),
            (
                "a declared path that names no file",
                declaration(
                    members=[version_record(VERSION_IDS[0], START_LABEL, path=missing_path)],
                    m=POOL_M,
                ),
                (("version-heron-5501",), ("path",), ("readable",)),
            ),
            (
                "a member that is not a record",
                declaration(members=[42], m=POOL_M),
                (("member",),),
            ),
        )
        for label, bad, groups in cases:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    package.build_pool, bad, entry="build_pool", groups=groups, label=label
                )

    def test_evl_2_11_offer_drops_the_oldest_version_recomputes_the_id_and_returns_a_new_pool(self):
        """EVL-2.11 `offer` joins the version at the window's head, drops the oldest when `m` versions are held, recomputes the id and returns a **new** pool (`pool.md` §6, `surface.md` §7, G6)."""
        package = self.evaluation()
        records = version_chain(VERSION_IDS[:POOL_M])
        pool = self.open_pool(members=records, m=POOL_M)
        before = self.pool_members(pool)
        newcomer = version_record(
            VERSION_IDS[POOL_M], records[-1]["id"], seed=OTHER_SEED_FOR_DIGEST, step=900, samples=900
        )
        advanced = package.offer(pool, newcomer)
        after = self.pool_members(advanced)
        ids = pool_member_ids(after)
        self.assertEqual(
            ids[-1],
            VERSION_IDS[POOL_M],
            "the offered version joins the window at its head, so it reads back newest "
            "(pool.md §6 step 4): %r" % (ids,),
        )
        self.assertNotEqual(
            after["id"],
            before["id"],
            "the id is recomputed from the new ordered ids (pool.md §6 step 5, G6): %r"
            % (after["id"],),
        )
        self.assertEqual(
            after["id"],
            pool_digest(after["members"]),
            "the advanced pool's id is the digest of its own ordered membership "
            "(families.md §4, §5): %r" % (after["id"],),
        )
        self.assertEqual(
            int(after["m"]),
            POOL_M,
            "the advanced pool keeps the bound it held to (pool.md §6, records.md §8)",
        )
        with self.subTest(version="an empty window accepts any version"):
            empty = self.open_pool(members=(), m=5)
            begun = package.offer(empty, version_record(VERSION_IDS[5], "no-such-parent-5508"))
            self.assertEqual(
                pool_member_ids(self.pool_members(begun)),
                tuple(BASELINES) + (VERSION_IDS[5],),
                "a window holding no version accepts any version and begins its order "
                "(pool.md §6 step 3, league.md §2): %r"
                % (pool_member_ids(self.pool_members(begun)),),
            )

    def test_evl_2_12_offer_refuses_and_leaves_its_argument_unchanged(self):
        """EVL-2.12 `offer` refuses a frozen pool, a version already a member, a version that does not extend the newest and a version without id or lineage -- and its argument pool reads back unchanged (`pool.md` §6, §8, `surface.md` §7, G6, G16)."""
        package = self.evaluation()
        records = version_chain(VERSION_IDS[:POOL_M])
        open_pool = self.open_pool(members=records, m=POOL_M)
        before = self.pool_members(open_pool)
        package.offer(open_pool, version_record(VERSION_IDS[POOL_M], records[-1]["id"]))
        self.assertEqual(
            self.pool_members(open_pool),
            before,
            "offer returns a new pool and leaves its argument unchanged, so a caller may "
            "keep an earlier pool (pool.md §6, surface.md §7, G6)",
        )
        frozen = self.frozen_pool(members=records, m=POOL_M)
        cases = (
            (
                "a frozen pool",
                frozen,
                version_record(VERSION_IDS[POOL_M], records[-1]["id"]),
                (("frozen",), ("does not change", "flag")),
            ),
            (
                "a version already a member",
                open_pool,
                version_record(VERSION_IDS[1], records[-1]["id"]),
                (("version-otter-5502",), ("already",)),
            ),
            (
                "a version that does not extend the newest",
                open_pool,
                version_record(VERSION_IDS[POOL_M], records[0]["id"]),
                (("lineage",), ("version-pika-5503",)),
            ),
            (
                "a version without a lineage",
                open_pool,
                {"id": VERSION_IDS[POOL_M]},
                (("lineage",),),
            ),
            (
                "a version without an id",
                open_pool,
                {"lineage": records[-1]["id"]},
                (("id",),),
            ),
        )
        for label, pool, version, groups in cases:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    package.offer, pool, version, entry="offer", groups=groups, label=label
                )

    def test_evl_2_13_pool_members_is_a_fresh_record_on_every_call(self):
        """EVL-2.13 the read-back is freshly built: editing the returned record and asking again returns the pool's own record, unchanged (`pool.md` §5, `surface.md` §6, G7)."""
        package = self.evaluation()
        pool = self.frozen_pool(members=version_chain(VERSION_IDS[:2]))
        first = self.pool_members(pool)
        snapshot = dict(first)
        first["id"] = "pool-0000000000000000"
        first["m"] = 99
        first["frozen"] = not bool(first["frozen"])
        first["members"] = ()
        again = self.pool_members(pool)
        self.assertEqual(
            again,
            snapshot,
            "pool_members returns records.md §8's record freshly built on each call, so "
            "a caller that edits it changes nothing (pool.md §5, G7)",
        )
        self.assertEqual(
            self.pool_members(pool),
            self.pool_members(pool),
            "one pool reads back one record (surface.md §6, pool.md §5)",
        )

    def test_evl_2_14_pool_members_returns_the_version_records_verbatim(self):
        """EVL-2.14 each version reads back as the `records.md` §7 record the declaration carried, its own keys and values untouched, in window order (`pool.md` §5, G7)."""
        declared = version_chain(VERSION_IDS[:3])
        pool = self.frozen_pool(members=declared, m=POOL_M)
        members = self.pool_members(pool)["members"]
        versions = members[3:]
        self.assertEqual(
            len(versions),
            3,
            "the three declared versions are the window's members (pool.md §2, §5): %r"
            % (versions,),
        )
        for index, record in enumerate(declared):
            with self.subTest(member=record["id"]):
                read = versions[index]
                self.assertIsInstance(
                    read, dict, "a version reads back as a mapping (records.md §7, G7)"
                )
                for key, value in record.items():
                    self.assertEqual(
                        read.get(key),
                        value,
                        "the read-back carries the declared %r of %r untouched "
                        "(pool.md §5, G7): %r" % (key, record["id"], read),
                    )

    def test_evl_2_15_a_value_that_is_not_a_pool_is_refused(self):
        """EVL-2.15 `pool_members`, `offer` and `opponent` refuse a value that is not a pool this module built, naming their own entry point (`pool.md` §8, `surface.md` §6-§8, G16)."""
        package = self.evaluation()
        version = version_record(VERSION_IDS[0], START_LABEL)
        cases = (
            ("pool_members with a dict", package.pool_members, ({},), "pool_members"),
            ("pool_members with None", package.pool_members, (None,), "pool_members"),
            ("offer with a dict", package.offer, ({}, version), "offer"),
            ("offer with a list", package.offer, ([], version), "offer"),
            ("opponent with a dict", package.opponent, ({}, OPPONENT_SEEDS[0]), "opponent"),
            ("opponent with None", package.opponent, (None, OPPONENT_SEEDS[0]), "opponent"),
        )
        for label, fn, args, entry in cases:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    fn, *args, entry=entry, groups=(("pool",),), label=label
                )

    def test_evl_2_16_a_member_declared_without_a_path_is_admitted(self):
        """EVL-2.16 a version declared without a `path` is admitted and read back without one, and only `matrix`/`opponent` refuse it when it must be a policy (`surface.md` §5, `pool.md` §2, §8, G16, G20)."""
        package = self.evaluation()
        declared = [
            version_record(VERSION_IDS[0], START_LABEL, step=11),
            version_record(VERSION_IDS[1], VERSION_IDS[0], step=22),
        ]
        pool = package.build_pool(declaration(members=declared, m=POOL_M))
        read = self.pool_members(pool)
        self.assertEqual(
            pool_member_ids(read),
            tuple(BASELINES) + tuple(VERSION_IDS[:2]),
            "a member without a path is admitted, because only `id` and `lineage` "
            "declare a version (surface.md §5, pool.md §2): %r"
            % (pool_member_ids(read),),
        )
        for record in read["members"][3:]:
            with self.subTest(member=member_id(record)):
                self.assertFalse(
                    record.get("path"),
                    "the read-back carries the record the declaration carried and "
                    "invents no path (pool.md §5, surface.md §5): %r" % (record,),
                )

    def test_evl_2_17_the_draw_is_one_member_and_one_policy_for_one_seed(self):
        """EVL-2.17 one pool and one seed draw one opponent, it answers one decision one way, and the draw plays no hand and moves no stream (`surface.md` §8, `pool.md` §7, FAM-7.9)."""
        package = self.evaluation()
        pool = self.frozen_pool(members=(), m=5)
        seed = OPPONENT_SEEDS[0]
        before = self.stream_state()
        first = package.opponent(pool, seed)
        second = package.opponent(pool, seed)
        self.assert_stream_unchanged(before, "opponent()")
        self.assertTrue(
            callable(first),
            "opponent returns one policy in the sense of surface.md §2: %r" % (first,),
        )
        rows = probe_readouts(3)
        for row in rows:
            with self.subTest(hand=row["seed"]):
                answer = first(row["readout"], row["legal"])
                self.assertIn(
                    answer,
                    row["legal"],
                    "a drawn policy answers one descriptor of legal_actions "
                    "(surface.md §2, pool.md §7): %r" % (answer,),
                )
                self.assertEqual(
                    answer,
                    second(row["readout"], row["legal"]),
                    "one pool and one seed draw one opponent, and it answers one decision "
                    "one way (surface.md §8, pool.md §7)",
                )

    def test_evl_2_18_the_draw_is_the_seed_reduced_modulo_the_membership(self):
        """EVL-2.18 the drawn member is the membership's `seed % n`: a pool of eight members, five of them versions without a `path`, names the member at that position for eight consecutive seeds (`pool.md` §7, `scheduler.md` §3, FAM-7.9)."""
        package = self.evaluation()
        declared = version_chain(VERSION_IDS[:5])
        pool = self.open_pool(members=declared, m=5)
        members = pool_member_ids(self.pool_members(pool))
        self.assertEqual(
            len(members),
            8,
            "the fixture is a full window: three baselines and five versions "
            "(league.md §2, pool.md §2): %r" % (members,),
        )
        seeds = tuple(range(OPPONENT_SEEDS[0], OPPONENT_SEEDS[0] + 8))
        for seed in seeds:
            expected = members[seed % len(members)]
            with self.subTest(seed=seed):
                if expected in BASELINES:
                    drawn = package.opponent(pool, seed)
                    self.assertTrue(
                        callable(drawn),
                        "the draw at index %d is the baseline %r, so it returns a policy "
                        "(pool.md §7): %r" % (seed % len(members), expected, drawn),
                    )
                else:
                    self.assert_evaluation_refusal(
                        package.opponent,
                        pool,
                        seed,
                        entry="opponent",
                        groups=((expected,), ("path",)),
                        label="opponent at seed %d" % seed,
                    )

    def test_evl_2_19_a_spread_of_seeds_samples_the_whole_pool(self):
        """EVL-2.19 `n` consecutive seeds visit each of the `n` members once, so a spread of seeds samples the whole pool and not one fixed policy (`pool.md` §7, `surface.md` §8, FAM-7.9)."""
        package = self.evaluation()
        pool = self.open_pool(members=version_chain(VERSION_IDS[:5]), m=5)
        members = pool_member_ids(self.pool_members(pool))
        named = set()
        policies = 0
        for seed in range(OPPONENT_SEEDS[0], OPPONENT_SEEDS[0] + len(members)):
            drawn = members[seed % len(members)]
            if drawn in BASELINES:
                policies += 1
                self.assertTrue(
                    callable(package.opponent(pool, seed)),
                    "a baseline draw is a policy (pool.md §7): %r" % (drawn,),
                )
            else:
                try:
                    package.opponent(pool, seed)
                except Exception as exc:  # the refusal names the member drawn
                    self.assertIn(
                        drawn,
                        str(exc),
                        "a version without a path is refused naming the member drawn, "
                        "so the draw is observable (pool.md §7, §8): %r" % (str(exc),),
                    )
                    named.add(drawn)
                else:
                    self.fail(
                        "the draw at seed %d is the path-less version %r and must be "
                        "refused naming it (pool.md §7, §8): accepted instead"
                        % (seed, drawn),
                    )
        self.assertEqual(
            named,
            set(VERSION_IDS[:5]) - set(),
            "eight consecutive seeds over eight members draw each member once, so every "
            "version is drawn and named (pool.md §7, FAM-7.9): %r" % (named,),
        )
        self.assertEqual(
            policies,
            3,
            "the three baseline residues draw a policy and the five version residues a "
            "refusal (pool.md §7): %r" % (policies,),
        )
        self.assertGreaterEqual(
            len(named | set(BASELINES)),
            len(members),
            "a spread of seeds samples the whole membership and not one fixed policy "
            "(surface.md §8, FAM-7.9)",
        )

    def test_evl_2_20_a_drawn_version_is_the_player_its_checkpoint_records(self):
        """EVL-2.20 a drawn version is `policy_from` of its checkpoint -- the same player, answering one decision one way -- and a drawn baseline answers a decision legally (`pool.md` §7, `scheduler.md` §5, `surface.md` §2)."""
        package = self.evaluation()
        saved = self.checkpoint(name="opponent-member")
        declared = [version_record(VERSION_IDS[0], START_LABEL, path=saved["path"], seed=saved["seed"])]
        pool = self.frozen_pool(members=declared, m=POOL_M)
        members = pool_member_ids(self.pool_members(pool))
        seed = next(
            candidate
            for candidate in range(OPPONENT_SEEDS[0], OPPONENT_SEEDS[0] + 4)
            if members[candidate % len(members)] == VERSION_IDS[0]
        )
        drawn = package.opponent(pool, seed)
        reference = package.policy_from(saved["path"])
        rows = probe_readouts(3)
        for row in rows:
            with self.subTest(hand=row["seed"]):
                self.assertIn(
                    drawn(row["readout"], row["legal"]),
                    row["legal"],
                    "a drawn version answers a decision with a legal descriptor "
                    "(surface.md §2, pool.md §7)",
                )
                self.assertEqual(
                    drawn(row["readout"], row["legal"]),
                    reference(row["readout"], row["legal"]),
                    "a drawn version is policy_from of its checkpoint, so it is the same "
                    "player as the member it names (pool.md §7, scheduler.md §5)",
                )
        baseline_seed = next(
            candidate
            for candidate in range(OPPONENT_SEEDS[0], OPPONENT_SEEDS[0] + 4)
            if members[candidate % len(members)] in BASELINES
        )
        baseline_drawn = package.opponent(pool, baseline_seed)
        for row in rows:
            with self.subTest(baseline_hand=row["seed"]):
                self.assertIn(
                    baseline_drawn(row["readout"], row["legal"]),
                    row["legal"],
                    "a drawn baseline is a policy and answers a legal descriptor "
                    "(surface.md §2, agents/surface.md §12)",
                )

    def test_evl_2_21_opponent_refuses_a_seed_that_is_not_an_integer(self):
        """EVL-2.21 `opponent` refuses a seed that is not an integer, naming its entry point and the seed (`pool.md` §8, `surface.md` §8, `errors.md` §2, G16)."""
        package = self.evaluation()
        pool = self.frozen_pool(members=(), m=5)
        for label, seed in (
            ("a string", "8086"),
            ("None", None),
            ("a bool", True),
            ("a float", 3.5),
        ):
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    package.opponent,
                    pool,
                    seed,
                    entry="opponent",
                    groups=(("seed",),),
                    label="opponent(seed=%r)" % (seed,),
                )


    # -- the rule a member declares, and the families it groups (D-19) ----
    def test_evl_2_22_a_version_member_declares_its_rule_and_an_uncatalogued_one_is_refused(self):
        """EVL-2.22 every version member declares a catalogue `rule` -- read from `agents.learners()` and never from a copy -- and a name the catalogue lacks is refused by name, before the pool exists (`pool.md` §2 item 1, `rules.md` §4, `records.md` §7, ASM-26)."""
        package = self.evaluation()
        catalogue = self.catalogue_rules()
        self.assertEqual(
            tuple(catalogue[:2]),
            (DEFAULT_RULE, OTHER_RULE),
            "the catalogue publishes the two rules in rules.md §2's order, so the names "
            "this case asserts against are the module's own (rules.md §2, §4, D-19): %r"
            % (catalogue,),
        )
        declared_rule = version_record(VERSION_IDS[0], START_LABEL, rule=OTHER_RULE)
        read = self.pool_members(self.frozen_pool(members=[declared_rule]))
        members = {member_id(entry): entry for entry in read["members"]}
        self.assertEqual(
            members[VERSION_IDS[0]]["rule"],
            OTHER_RULE,
            "each version member carries the rule it was trained under, so a table can "
            "name the population it measured (records.md §7, ASM-27): %r"
            % (members.get(VERSION_IDS[0]),),
        )
        for label, rule in (
            ("a name outside the catalogue", "n-step-returns-battery"),
            ("an empty name", ""),
            ("a name holding the digest's separator", "masked\x1fq-learning"),
            ("a name holding a newline", "masked\nq-learning"),
            ("a name that is not a string", 42),
        ):
            with self.subTest(case=label):
                offender = version_record(VERSION_IDS[0], START_LABEL)
                offender["rule"] = rule
                self.assert_evaluation_refusal(
                    package.build_pool,
                    declaration(members=[offender], m=POOL_M),
                    entry="build_pool",
                    groups=(("rule",),),
                    label="a version declaring %r" % (rule,),
                )
        missing = version_record(VERSION_IDS[0], START_LABEL)
        missing.pop("rule")
        self.assert_evaluation_refusal(
            package.build_pool,
            declaration(members=[missing], m=POOL_M),
            entry="build_pool",
            groups=(("rule",),),
            label="a version declaring no rule at all",
        )

    def test_evl_2_23_the_pool_record_declares_the_rules_its_versions_hold(self):
        """EVL-2.23 `pool_members` returns the distinct rules its version members declare, in the window's order -- the empty tuple for a baselines-only pool, both rules for a window holding two families (`pool.md` §5, `records.md` §8, ASM-27)."""
        masked = version_chain(VERSION_IDS[:2], rule=DEFAULT_RULE)
        doubled = version_chain(
            VERSION_IDS[2:4], start="own-start-other-5600", rule=OTHER_RULE
        )
        two = self.pool_members(self.frozen_pool(members=masked + doubled, m=5))
        self.assertEqual(
            tuple(pool_rules(two)),
            (DEFAULT_RULE, OTHER_RULE),
            "a pool record carries `rules`, the distinct rules its version members "
            "declare, in the window's order (records.md §8, D-19): %r"
            % (pool_rules(two),),
        )
        baselines_only = self.pool_members(self.frozen_pool(members=(), m=5))
        self.assertEqual(
            tuple(pool_rules(baselines_only)),
            (),
            "R1's pool is the three baselines alone, which declare no rule at all, so its "
            "`rules` is the empty tuple (records.md §8, league.md §2): %r"
            % (pool_rules(baselines_only),),
        )
        id_before = pool_digest(baselines_only["members"])
        self.assertEqual(
            baselines_only["id"],
            id_before,
            "a baselines-only pool digests as a bare list of names, so the id a shipped "
            "artefact records survives the rule's arrival unchanged (families.md §4, "
            "ASM-27)",
        )

    def test_evl_2_24_a_second_family_is_accepted_and_extends_its_own_newest(self):
        """EVL-2.24 `offer` accepts a version whose lineage is a label no member carries -- which opens a second family -- where the single-chain rule refused it, and then rolls that family by its own newest member (`families.md` §5, `pool.md` §6, ASM-26)."""
        package = self.evaluation()
        first = version_chain(VERSION_IDS[:2], rule=DEFAULT_RULE)
        pool = self.open_pool(members=first, m=5)
        opening = version_record(
            VERSION_IDS[2], "own-start-second-family-5601", rule=OTHER_RULE
        )
        pool = package.offer(pool, opening)
        self.assertEqual(
            pool_member_ids(self.pool_members(pool)),
            tuple(BASELINES) + (VERSION_IDS[0], VERSION_IDS[1], VERSION_IDS[2]),
            "a version whose lineage no member carries opens a second family, and the "
            "window lists each family contiguously oldest to newest (families.md §2, §5): "
            "%r" % (pool_member_ids(self.pool_members(pool)),),
        )
        extending = version_record(
            VERSION_IDS[3], VERSION_IDS[2], rule=OTHER_RULE, step=400
        )
        pool = package.offer(pool, extending)
        self.assertEqual(
            pool_member_ids(self.pool_members(pool)),
            tuple(BASELINES) + (VERSION_IDS[0], VERSION_IDS[1], VERSION_IDS[2],
                                VERSION_IDS[3]),
            "the second family rolls by its own newest member, so a window holding two "
            "chains advances where the single-chain rule refused the second snapshot "
            "(families.md §5, league.md §2, D-19): %r"
            % (pool_member_ids(self.pool_members(pool)),),
        )
        with self.subTest(case="a lineage that forks its family"):
            fork = version_record(VERSION_IDS[4], VERSION_IDS[2], step=500)
            self.assert_evaluation_refusal(
                package.offer,
                pool,
                fork,
                entry="offer",
                groups=(("lineage",), (VERSION_IDS[3],)),
                label="a lineage naming a member that is not its family's newest",
            )
        with self.subTest(case="the same start label opens a second family"):
            sibling = version_record(
                VERSION_IDS[5], START_LABEL, rule=OTHER_RULE, step=600
            )
            opened = package.offer(
                self.open_pool(members=version_chain(VERSION_IDS[:2]), m=5), sibling
            )
            self.assertEqual(
                pool_member_ids(self.pool_members(opened)),
                tuple(BASELINES) + (VERSION_IDS[0], VERSION_IDS[1], VERSION_IDS[5]),
                "a lineage that is no member's id opens a new family, which is how a "
                "second arm's first snapshot -- naming the rung start its sibling's "
                "names -- joins the window (families.md §5, ASM-26, D-19): %r"
                % (pool_member_ids(self.pool_members(opened)),),
            )
        with self.subTest(case="a version changing its family's rule"):
            relabelled = version_record(VERSION_IDS[4], VERSION_IDS[3], rule=DEFAULT_RULE)
            self.assert_evaluation_refusal(
                package.offer,
                pool,
                relabelled,
                entry="offer",
                groups=(("rule",), (OTHER_RULE,), (DEFAULT_RULE,)),
                label="a version whose rule is not the rule of the family it extends",
            )

    def test_evl_2_25_eviction_is_fair_share_and_never_empties_a_family(self):
        """EVL-2.25 a full window evicts the oldest member of the family that holds the most, so no family is emptied while another holds two or more -- and one family's window is the last `m` of its chain, as it was before the catalogue (`families.md` §3, ASM-26)."""
        package = self.evaluation()
        alpha = version_chain(
            VERSION_IDS[:3], start="own-start-family-a-5602", rule=DEFAULT_RULE
        )
        bravo = version_chain(
            VERSION_IDS[3:6], start="own-start-family-b-5603", rule=OTHER_RULE
        )
        pool = self.open_pool(members=alpha + bravo, m=4)
        kept = pool_member_ids(self.pool_members(pool))
        self.assertEqual(
            len(kept),
            len(BASELINES) + 4,
            "a window holds at most the bound it declares, beside the three pinned "
            "baselines (pool.md §2, league.md §2): %r" % (kept,),
        )
        for family, names in (("a", VERSION_IDS[:3]), ("b", VERSION_IDS[3:6])):
            with self.subTest(family=family):
                self.assertTrue(
                    any(name in kept for name in names),
                    "fair-share eviction leaves at least one member of each family while "
                    "another holds two or more (families.md §3, ASM-26): %r" % (kept,),
                )
        advanced = package.offer(
            pool, version_record(VERSION_IDS[6], alpha[-1]["id"], rule=DEFAULT_RULE, step=700)
        )
        after = pool_member_ids(self.pool_members(advanced))
        self.assertEqual(
            len(after),
            len(BASELINES) + 4,
            "offering into a full window keeps the window at its bound (families.md §3): %r"
            % (after,),
        )
        for family, names in (("a", VERSION_IDS[:3] + (VERSION_IDS[6],)),
                              ("b", VERSION_IDS[3:6])):
            with self.subTest(after_family=family):
                self.assertTrue(
                    any(name in after for name in names),
                    "a seventh version rolls its own family and no family is emptied "
                    "(families.md §3, §5, ASM-26): %r" % (after,),
                )
        with self.subTest(case="one family behaves as it did before"):
            single = self.open_pool(members=version_chain(VERSION_IDS[:5]), m=3)
            self.assertEqual(
                pool_member_ids(self.pool_members(single)),
                tuple(BASELINES) + VERSION_IDS[2:5],
                "a window holding one family keeps the last `m` of that chain, which is "
                "what every pool in the shipped tree holds (families.md §3, ASM-18): %r"
                % (pool_member_ids(self.pool_members(single)),),
            )

    def test_evl_2_26_opening_the_mth_plus_one_family_is_refused_by_name(self):
        """EVL-2.26 a declaration holding more families than its bound, and an offer that would open the (m+1)th family, are refused -- windowing could not keep one member of each, so a family would be emptied (`families.md` §3, §5, ASM-26)."""
        package = self.evaluation()
        starts = ("own-start-fam-1", "own-start-fam-2", "own-start-fam-3")
        declared = [
            version_record(name, start)
            for name, start in zip(VERSION_IDS[:3], starts)
        ]
        self.assert_evaluation_refusal(
            package.build_pool,
            declaration(members=declared, m=2),
            entry="build_pool",
            groups=(("m", "bound", "famil"), ("2",)),
            label="a declaration holding three families under a bound of two",
        )
        two = self.open_pool(members=declared[:2], m=2)
        third = version_record(VERSION_IDS[2], starts[2])
        self.assert_evaluation_refusal(
            package.offer,
            two,
            third,
            entry="offer",
            groups=(("famil",), ("2",)),
            label="an offer that would open the third family of a two-member window",
        )


#: A seed for a corrected member field: the digest must not read it (EVL-2.5).
OTHER_SEED_FOR_DIGEST = 55099


if __name__ == "__main__":
    unittest.main()
