"""JOIN-EVL-14 — the utility axis at the join (D-20).

D-20 makes the terminal reward selectable, so a model is trained *under* one of the
catalogue's two utilities and every record it reaches has to name it
(`docs/L1/utilities.md` §2, §5–§9, `docs/L1/records.md` §7–§10, D-20).  At the join
that is one chain of facts: `agents.build_learner` writes a checkpoint whose container
records the utility, `evaluation.build_pool` reads the version record's declaration,
`pool_members` reads it back and the pool id digests it, `evaluation.policy_from`
reports the one the container holds, and `evaluation.matrix` names each member's
objective and the `utility_population` those members make up.

This file drives that chain with **two real checkpoints, one per catalogue utility**,
each declared as one family member, so the pool holds two objectives and the table
measures two — the heterodoxy D-18 and D-19 ask of the *rule* axis, now on the reward
axis (`docs/L1/records.md` §8, `docs/L2/evaluation/league.md` §1, D-18, D-19, D-20).
The two containers are compared against what `policy_from` reports, so a case never
asserts a declaration the file does not hold.

The one expensive observable is the table: six members (three pinned baselines, the
two version members and the rung's one variant) at the `live` budget's 120 hands a
cell, built once per process and shared by the cases that read it
(`docs/L1/protocol.md` §2, ASM-8, ASM-15).  Every invented value below — the version
ids, the two lineage starts, the checkpoint names and seeds — is this battery's own
(`docs/L1/battery.md` §4, D-15).
"""

import importlib.util
import os
import random
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
# The support module is loaded under a private name: this repository's integration
# batteries share the file name `_join_support.py`, so a plain import would hand one
# battery another's helpers when two test directories are collected in one process.
if "evaluation_join_support" in sys.modules:
    J = sys.modules["evaluation_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "evaluation_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["evaluation_join_support"] = J
    _spec.loader.exec_module(J)

#: The two version ids, each one family's only member, and the start labels their
#: families open at (`families.md` §1-§2) — the battery's own values.
VERSION_SHORTFALL = "version-tattler-5601"
VERSION_CHIPS = "version-grebe-5602"
START_SHORTFALL = "R9/start-utility-shortfall"
START_CHIPS = "R9/start-utility-chips"

#: The two checkpoint file names, one per catalogue utility (`utilities.md` §6, D-20).
CHECKPOINT_SHORTFALL = "evaluation-join-utility-shortfall.ckpt"
CHECKPOINT_CHIPS = "evaluation-join-utility-chips.ckpt"

_CACHE = {}


def shortfall_member():
    """The version record whose checkpoint was written under the catalogue's second utility."""
    if "shortfall" not in _CACHE:
        _CACHE["shortfall"] = J.version(
            VERSION_SHORTFALL,
            START_SHORTFALL,
            checkpoint_name=CHECKPOINT_SHORTFALL,
            seed=J.CHECKPOINT_SEED_C,
            utility=J.OTHER_UTILITY,
        )
    return _CACHE["shortfall"]


def chips_member():
    """The version record whose checkpoint was written under the catalogue's first utility."""
    if "chips" not in _CACHE:
        _CACHE["chips"] = J.version(
            VERSION_CHIPS,
            START_CHIPS,
            checkpoint_name=CHECKPOINT_CHIPS,
            seed=J.CHECKPOINT_SEED_D,
            utility=J.DEFAULT_UTILITY,
        )
    return _CACHE["chips"]


def utility_pool():
    """One frozen pool holding both members, one family each, the shortfall family first.

    The order matters to the read-back: the window lists the families in the order they
    entered, so the pool's `utilities` is `(stack-shortfall, net-chips)` while a table's
    `utility_population` sorts the same two names the other way round
    (`families.md` §2, `records.md` §8, §10, D-20).
    """
    if "pool" not in _CACHE:
        _CACHE["pool"] = J.build_pool(
            {
                "members": [shortfall_member(), chips_member()],
                "m": J.league()["m"],
                "frozen": True,
            }
        )
    return _CACHE["pool"]


def utility_matrix():
    """The one real `live` table over `utility_pool()`, built once and shared."""
    if "matrix" not in _CACHE:
        _CACHE["matrix"] = J.matrix(utility_pool(), [J.variant_policy()], "live")
    return _CACHE["matrix"]


def utility_of_container(member):
    """The utility the policy built from one member's checkpoint reports (`utilities.md` §6)."""
    return getattr(J.policy_from(member["path"]), "utility", None)


class UtilityJoin(J.JoinCase):
    """Two containers, two declared objectives, and the records that carry them."""

    def test_join_evl_14_1_a_checkpoint_is_written_under_one_catalogue_utility(self):
        """JOIN-EVL-14.1 a real checkpoint written under each catalogue utility reports that utility through `policy_from`, so the two containers are the two objectives the records will name (`utilities.md` §2, §5, §6, `e2e-surface.md` §2, §3.4, D-20)."""
        catalogue = tuple(str(name) for name in J.learners()["utilities"])
        self.assertEqual(
            catalogue[:2],
            (J.DEFAULT_UTILITY, J.OTHER_UTILITY),
            "agents.learners() publishes the two utilities in utilities.md §2's order, so "
            "the names this case asserts against are the module's own (D-20): %r"
            % (catalogue,),
        )
        for label, member, utility in (
            ("net-chips", chips_member(), J.DEFAULT_UTILITY),
            ("stack-shortfall", shortfall_member(), J.OTHER_UTILITY),
        ):
            with self.subTest(utility=label):
                self.assertEqual(
                    str(member["utility"]),
                    utility,
                    "the version record declares the utility its checkpoint was written "
                    "under, which is the pair records.md §7 requires of a member "
                    "(utilities.md §6, §7, D-20): %r" % (member,),
                )
                self.assertTrue(
                    os.path.isfile(member["path"]),
                    "the member names a checkpoint agents.save wrote, not a hand-built "
                    "file (protocol.md §5): %r" % (member.get("path"),),
                )
                self.assertEqual(
                    utility_of_container(member),
                    utility,
                    "a container records the utility its learner was trained under and "
                    "evaluation.policy_from reports it, because playback is utility-free "
                    "and the file is the only witness (utilities.md §6, ASM-20, D-20): %r"
                    % (member["path"],),
                )

    def test_join_evl_14_2_the_pool_reads_back_both_objectives_from_its_members(self):
        """JOIN-EVL-14.2 `build_pool` → `pool_members` carries each member's utility and the pool's `utilities` holds both, in the window's order, while the pool's single rule population stands beside it (`records.md` §7, §8, `utilities.md` §7, ASM-27, D-20)."""
        record = J.pool_members(utility_pool())
        self.assertEqual(
            J.names_of(record),
            ["random", "always-call", "oracle", VERSION_SHORTFALL, VERSION_CHIPS],
            "the window holds the three pinned baselines and then each family's one "
            "member, the families in the order they entered (families.md §2, ASM-16): %r"
            % (J.names_of(record),),
        )
        for member, utility in (
            (shortfall_member(), J.OTHER_UTILITY),
            (chips_member(), J.DEFAULT_UTILITY),
        ):
            with self.subTest(member=member["id"]):
                self.assertEqual(
                    J.member_utility(record, member["id"]),
                    utility,
                    "a version member of a pool carries the utility it was trained under, "
                    "and it is the name its own container records — a table can name it "
                    "and the pool id can certify it (records.md §7, utilities.md §6, §7, "
                    "ASM-20, D-20): %r" % (J.member_record(record, member["id"]),),
                )
                self.assertEqual(
                    J.member_utility(record, member["id"]),
                    utility_of_container(member),
                    "the record's declaration and the container's agree, which is what "
                    "makes the declaration a fact rather than a claim (utilities.md §6, "
                    "§7, ASM-20, D-20)",
                )
        self.assertEqual(
            J.pool_utilities(record),
            (J.OTHER_UTILITY, J.DEFAULT_UTILITY),
            "the pool record declares the `utilities` its version members declare, in the "
            "window's order — the shortfall family entered first, so the set is not "
            "sorted here (records.md §8, utilities.md §7, D-20): %r"
            % (J.pool_utilities(record),),
        )
        self.assertEqual(
            J.pool_rules(record),
            (J.DEFAULT_RULE,),
            "both members learned under one rule, so the rule population is one name "
            "beside the two objectives (records.md §8, D-19, D-20): %r"
            % (J.pool_rules(record),),
        )
        self.assertEqual(
            str(record["id"]),
            J.pool_id(J.members_of(record)),
            "the id is one line per member — a baseline's id alone, a version's id, its "
            "rule and its utility — and of nothing else (families.md §4, ASM-27, D-20)",
        )

    def test_join_evl_14_3_the_matrix_names_each_objective_and_their_population(self):
        """JOIN-EVL-14.3 the table played over that pool names each member's utility by its id — `None` for a baseline — and its `utility_population` holds both objectives, sorted, so the table states the objectives it measured (`records.md` §10, `utilities.md` §9, `matrix.md` §5, D-20)."""
        table = utility_matrix()
        members = J.matrix_members(table)
        utilities = table["utilities"]
        self.assertEqual(
            members,
            ["random", "always-call", "oracle", VERSION_SHORTFALL,
             VERSION_CHIPS, "variant-1"],
            "the membership is the pool's order and then the variant slot (matrix.md §1, "
            "G12): %r" % (members,),
        )
        for name in [str(baseline) for baseline in J.protocol()["baselines"]]:
            with self.subTest(baseline=name):
                self.assertIsNone(
                    utilities[name],
                    "a pinned baseline is a fixed policy and declares no utility, and the "
                    "table says so with `None` (records.md §10, e2e-surface.md §2, "
                    "D-20): %r" % (utilities,),
                )
        for member, utility in (
            (shortfall_member(), J.OTHER_UTILITY),
            (chips_member(), J.DEFAULT_UTILITY),
        ):
            with self.subTest(member=member["id"]):
                self.assertEqual(
                    utilities[member["id"]],
                    utility,
                    "each version member's utility is the one its checkpoint records, "
                    "read back through the pool record the table names (records.md §10, "
                    "utilities.md §6, §7, D-20): %r" % (utilities,),
                )
        self.assertEqual(
            utilities["variant-1"],
            J.DEFAULT_UTILITY,
            "the rung's variant names the objective its own learner was built under "
            "(utilities.md §7, matrix.md §5, D-20): %r" % (utilities,),
        )
        self.assertEqual(
            table["utility_population"],
            tuple(sorted((J.DEFAULT_UTILITY, J.OTHER_UTILITY))),
            "a table states the distinct utilities its members declared, sorted, beside "
            "the `population` of rules — the two objectives it measured (records.md §10, "
            "utilities.md §9, D-20): %r" % (table["utility_population"],),
        )
        self.assertEqual(
            table["population"],
            (J.DEFAULT_RULE,),
            "the rule population is one name, so the table's two populations are two "
            "different sets and not one repeated (records.md §10, D-19, D-20): %r"
            % (table["population"],),
        )
        cell = J.cell_by_pair(table, VERSION_SHORTFALL, VERSION_CHIPS)
        self.assertEqual(
            cell["utilities"],
            {VERSION_SHORTFALL: J.OTHER_UTILITY, VERSION_CHIPS: J.DEFAULT_UTILITY},
            "the cell the two objectives met in names each side's utility by its id, so "
            "a reader of one cell is told which questions the two players were asked "
            "(records.md §9, utilities.md §9, D-20): %r" % (cell["utilities"],),
        )
        self.assertEqual(
            str(table["pool"]),
            str(J.pool_members(utility_pool())["id"]),
            "the table names the pool it measured by id, and that pool's record declares "
            "the same two objectives (records.md §8, §10): %r" % (table["pool"],),
        )
        for record, name in zip(list(table["member_records"]), members):
            with self.subTest(member=name, row="member_records"):
                self.assertIn(
                    "utility",
                    record,
                    "each member row carries the utility its policy carries (matrix.md "
                    "§5, records.md §10, D-20): %r" % (record,),
                )
                self.assertEqual(
                    record["utility"],
                    utilities[name],
                    "a member's row and the table's `utilities` name one utility "
                    "(matrix.md §5, D-20): %r against %r"
                    % (record["utility"], utilities[name]),
                )

    def test_join_evl_14_4_one_membership_under_two_objectives_is_two_pool_ids(self):
        """JOIN-EVL-14.4 the same two members declared under one utility is a different pool with a different id, and it is not a table: `matrix` refuses it naming the member and both utilities before a hand is played (`records.md` §8, `utilities.md` §6, §7, ASM-20, ASM-27, D-20)."""
        honest = J.pool_members(utility_pool())
        misdeclared = J.build_pool(
            {
                "members": [
                    dict(shortfall_member(), utility=J.DEFAULT_UTILITY),
                    chips_member(),
                ],
                "m": J.league()["m"],
                "frozen": True,
            }
        )
        read = J.pool_members(misdeclared)
        self.assertEqual(
            J.pool_utilities(read),
            (J.DEFAULT_UTILITY,),
            "a declaration that claims one objective for both families reads back as one "
            "objective — build_pool compares the records and touches no checkpoint "
            "(records.md §8, utilities.md §7, D-20): %r" % (read,),
        )
        self.assertEqual(
            J.names_of(read),
            J.names_of(honest),
            "the two declarations hold one membership, so the id is what has to change "
            "(records.md §8, ASM-27): %r against %r"
            % (J.names_of(read), J.names_of(honest)),
        )
        self.assertNotEqual(
            str(read["id"]),
            str(honest["id"]),
            "one membership under two objectives does not wear the id it wears under "
            "one: the id certifies the objective population a table was measured over "
            "(records.md §8, utilities.md §7, ASM-27, D-20): %r against %r"
            % (read["id"], honest["id"]),
        )
        self.assertEqual(
            str(read["id"]),
            J.pool_id(J.members_of(read)),
            "the changed id is still the digest of the new ordered membership, each "
            "version's utility included (families.md §4, ASM-27, D-20)",
        )
        before = random.getstate()
        try:
            message = self.assert_refusal(
                "matrix",
                [VERSION_SHORTFALL, J.DEFAULT_UTILITY, J.OTHER_UTILITY],
                lambda: J.matrix(misdeclared, [J.variant_policy()], "live"),
                "a table over a pool whose member contradicts its container",
            )
        finally:
            after = random.getstate()
            random.setstate(before)
        self.assertEqual(
            after,
            before,
            "the table is refused before its first cell is played, so no hand moved the "
            "global stream (matrix.md §7, ASM-2, D-20)",
        )
        self.assertIn(
            "utility",
            message.lower(),
            "the refusal names the field at fault, so a caller is told which axis "
            "disagreed (errors.md §3, D-20): %r" % (message,),
        )


if __name__ == "__main__":
    unittest.main()
