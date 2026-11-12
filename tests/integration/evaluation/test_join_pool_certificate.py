"""JOIN-EVL-17 — the pool certifies the counterfactual member, and no shipped id moves (D-43).

`docs/L1/counterfactual.md` §6 makes the member a **third** catalogue and asks the pool to
certify it as it certifies a rule and a utility: a version record declares it when — and only
when — it is not `none`, a name the catalogue does not carry is refused **by name**, the
read-back states the `counterfactuals` set those members declare (and no such key when every
one of them is `none`), and the id digests the member only when it is not `none`, which is
what leaves every shipped id, R1's among them, exactly as it was (`records.md` §7, §8,
`docs/L2/evaluation/pool.md` §7, §8, ASM-27, D-43).

The two facts this file adds to the neighbouring `test_join_counterfactual.py` are the two
that file does not state: the **refusal by name** at both places a member record is read —
`build_pool` and `offer` — with the catalogue's own second member admitted beside it as the
control, and the **shipped id** held: the pool R1's own declaration builds reads back the id
that declaration carries and the registry of rungs publishes, computed nowhere in this case,
which is the assertion that D-43's digest change moved nothing that was already on disk
(`counterfactual.md` §6, §9, `records.md` §8, `families.md` §4).

Every value below that is not a catalogue name is this battery's own (`battery.md` §4, D-15):
the member id, its lineage start, the seed and the checkpoint name it names.  The two runs
this file does not do are the two a run record owns; that join is `test_counterfactual_pair.py`
in `tests/integration/training/`.
"""

import importlib.util
import os
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

#: The invented member this file declares: its id, its lineage start and its seed
#: (`docs/L1/battery.md` §4, D-15).  Nothing here is a version of a design document.
MEMBER_ID = "version-invented-counterfactual-17"
MEMBER_START = "R9/start-invented-counterfactual-17"
MEMBER_SEED = 69109

#: The name outside the third catalogue this file declares, and the one it does:
#: the catalogue itself is read off `agents.learners()` in the case, so only the invented
#: spelling is written down here (`counterfactual.md` §6, `battery.md` §4, D-15).
UNCATALOGUED = "join-invented-not-a-counterfactual"

#: The declaration's bound, which is the league's own (`records.md` §8, ASM-14).
BOUND = 5


def rung(name):
    """`training.rung(name)`: the resolved rung configuration its registry publishes.

    The pool this file reads the shipped id off is the **training** side's own declaration, so
    the case takes it from the module that publishes it and never writes the id down: the join
    is exactly that one module's `pool` is the other module's `build_pool` over the same
    membership (`e2e-surface.md` §3.5, `records.md` §8, D-16).
    """
    return J.mod("training").rung(name)


def declared(record, member):
    """One version record with the counterfactual member it declares (`records.md` §7).

    A copy of the support's real version record — a `path` to a checkpoint `agents.save`
    wrote — plus the conditional key, so the pool reads one member whose file and record
    agree on the members it declares and differ only in the third catalogue's name.
    """
    doctored = dict(record)
    doctored["counterfactual"] = str(member)
    return doctored


class MemberCertificate(J.JoinCase):
    """The pool reads the member of a version record, and refuses a name it cannot carry."""

    def version_record(self):
        """One real version record: a `records.md` §7 record naming a written checkpoint."""
        return J.version(MEMBER_ID, MEMBER_START, seed=MEMBER_SEED)

    def test_join_evl_17_1_a_declared_member_outside_the_catalogue_is_refused_by_name(self):
        """JOIN-EVL-17.1 `build_pool` and `offer` each refuse a declared counterfactual the third catalogue does not carry, naming the member, the name and the catalogue, while the catalogue's second member is admitted.

        `docs/L2/evaluation/pool.md` §7 and `docs/L3/evaluation/pool.md` §2: a version
        member's `counterfactual` is a **conditional** key, read where the record declares
        one and refused by name where the catalogue lacks it — naming the entry point, the
        member, the name and the catalogue — while a record that declares none is a member
        under `none` and gains no key (`counterfactual.md` §6, `records.md` §7,
        `docs/L3/evaluation/pool.md` §8, `errors.md` §4, D-43).  The case asserts the refusal
        at **both** places a member record is read and keeps the admitted member beside it as
        the control, so a refusal that came from the record's shape rather than from its
        member would be visible.
        """
        catalogue = [str(name) for name in J.learners()["counterfactuals"]]
        self.assertGreaterEqual(
            len(catalogue),
            2,
            "agents.learners() publishes the third catalogue beside the other two, with "
            "`none` first and the member D-43 adds second, so the pool has a population to "
            "certify (counterfactual.md §6, e2e-surface.md §2, D-43): %r" % (catalogue,),
        )
        self.assertNotIn(
            UNCATALOGUED,
            catalogue,
            "this case's name is one the catalogue does not carry — that is its whole "
            "subject — so it must not be a member of it (counterfactual.md §6, "
            "battery.md §4): %r" % (catalogue,),
        )
        record = self.version_record()
        declaration = {
            "members": [declared(record, UNCATALOGUED)],
            "m": BOUND,
            "frozen": True,
        }
        self.assert_refusal(
            "build_pool",
            (("counterfactual",), (UNCATALOGUED,), (MEMBER_ID,),
             tuple(catalogue)),
            lambda: J.build_pool(declaration),
            note="JOIN-EVL-17.1 build_pool over a member declaring %r" % (UNCATALOGUED,),
        )
        advancing = J.build_pool({"members": [], "m": BOUND, "frozen": False})
        self.assert_refusal(
            "offer",
            (("counterfactual",), (UNCATALOGUED,), (MEMBER_ID,),
             tuple(catalogue)),
            lambda: J.offer(advancing, declared(record, UNCATALOGUED)),
            note="JOIN-EVL-17.1 offer of a version declaring %r" % (UNCATALOGUED,),
        )
        member = catalogue[1]
        admitted = J.pool_members(
            J.build_pool(
                {
                    "members": [declared(record, member)],
                    "m": BOUND,
                    "frozen": True,
                }
            )
        )
        entry = J.member_record(admitted, MEMBER_ID)
        self.assertEqual(
            entry.get("counterfactual"),
            member,
            "the same record declaring the catalogue's own second member is admitted and "
            "reads back carrying it, so the refusal above was the name's and not the "
            "record's (records.md §7, §8, counterfactual.md §6, D-43): %r" % (entry,),
        )
        self.assertEqual(
            [str(name) for name in admitted["counterfactuals"]],
            [member],
            "and the pool record's `counterfactuals` set names the member its one version "
            "declares, in the window's order (records.md §8, docs/L3/evaluation/pool.md §5, "
            "D-43): %r" % (admitted.get("counterfactuals"),),
        )

    def test_join_evl_17_2_the_shipped_pool_id_does_not_move(self):
        """JOIN-EVL-17.2 the pool R1's own declaration builds reads back the id that declaration carries and the rung registry publishes, with no `counterfactuals` key at all.

        `docs/L1/counterfactual.md` §6 and §9: the pool id digests the member **only** when it
        is not `none`, so a declaration naming no folder and whose members were all trained
        under `none` keeps the id it had — R1's among them — and no shipped id moves.  The id
        is read from the declaration the registry publishes and from the record
        `pool_members` reads back, and **not** recomputed: a digest restated in a case could
        agree with itself while the shipped value had moved.  The same record states no
        `counterfactuals` key, which is the other half of the conditionality
        (`records.md` §8, `families.md` §4, ASM-27, D-43).
        """
        configuration = rung("R1")
        declaration = configuration["pool"]
        self.assertTrue(
            str(declaration.get("id") or ""),
            "the rung's pool declaration carries the id a run record and a table are compared "
            "by (records.md §8, §12, e2e-surface.md §3.5, D-16): %r" % (declaration,),
        )
        self.assertEqual(
            [dict(member) for member in declaration.get("members") or ()],
            [],
            "R1's pool is the three anchor baselines alone, so nothing in it can declare a "
            "counterfactual member (league.md §2, records.md §8, counterfactual.md §6): %r"
            % (declaration.get("members"),),
        )
        record = J.pool_members(J.build_pool(declaration))
        self.assertEqual(
            str(record["id"]),
            str(declaration["id"]),
            "the pool R1's own declaration builds reads back the id that declaration carries "
            "and the registry publishes, so D-43's digest change moved no shipped id — the two "
            "are held to each other and no digest is recomputed here "
            "(counterfactual.md §6, §9, families.md §4, ASM-27, D-43): %r against %r"
            % (record["id"], declaration["id"]),
        )
        self.assertNotIn(
            "counterfactuals",
            record,
            "a pool whose members were all trained under `none` records no `counterfactuals` "
            "key at all, which is what keeps the record it reads back exactly the record it "
            "read back before the catalogue existed (records.md §8, counterfactual.md §6, §9, "
            "D-43): %r" % (sorted(record),),
        )
        self.assertEqual(
            [str(member.get("id")) for member in record["members"]],
            [str(name) for name in J.protocol()["baselines"]],
            "its membership is the three pinned baselines in the catalogue's order, so the "
            "unchanged id is the unchanged membership and not an unchanged spelling of one "
            "(records.md §8, ASM-16, ASM-32, D-21): %r"
            % ([member.get("id") for member in record["members"]],),
        )


if __name__ == "__main__":
    unittest.main()
