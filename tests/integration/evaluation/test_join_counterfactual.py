"""JOIN-EVL-16 — the counterfactual axis at the join (D-43).

`docs/L1/counterfactual.md` §6 makes the counterfactual a **third** catalogue rather than a
rule or a utility: `agents.learners()` publishes `counterfactuals`, `none` first and the
declared default — the rule's own target, unchanged — and `reveal-counterfactual` second.
A learner trained under a member other than the first writes a **format version 5**
container whose `counterfactual` field sits immediately after `utility`, a learner under
`none` writes none at all, and versions 1–4 read as `none` (`docs/L1/records.md` §7–§8,
`docs/L3/agents/rule.md` §8, `docs/L3/agents/checkpoint.md` §2.1, D-43).

At the join that is one chain of facts: `agents.build_learner` takes the member,
`agents.save` lays it in the container's `metadata.json`, `evaluation.build_pool` reads
the version record's declaration, `pool_members` reads it back, and the pool id digests
it — **only** when it is not `none`, so a `none` pool, R1's among them, keeps the id it
had (`counterfactual.md` §6, §9, `families.md` §4, ASM-27).

So this file drives two real checkpoints, one per catalogue member, each declared as one
family member, and compares what the container records against what the pool certifies,
so no case asserts a declaration its file does not hold. The container's own bytes are
read twice: through `agents.checkpoint._read_metadata(path)`, the internal `rule.md` §8
declares for exactly this, and — for the **absence** this change is about — off the
container's `metadata.json` itself, which is `checkpoint.md` §2.1's file, because the
reader normalises a version-1-to-4 container's silence into the catalogue's first member.

`JOIN-EVL-16.2` holds the other half of §6's id rule: one membership under two
counterfactual members wears two ids, and each of them is still exactly the digest the
support recomputes from that pool's own members, so the difference is the appended field
alone and nothing else. Both checkpoints are the battery's own invented instances, built
once, one `agents.save` each, at the small width and depth the neighbouring join files use
(`docs/L1/battery.md` §4, D-15).
"""

import importlib.util
import json
import os
import sys
import unittest
import zipfile

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

#: The two catalogue members this file asserts against (`counterfactual.md` §2, §6, D-43).
#: The catalogue itself is read off `agents.learners()` in the case; these are only the
#: names the case spells when it must hand one to a call.
DEFAULT_COUNTERFACTUAL = "none"
REVEAL_COUNTERFACTUAL = "reveal-counterfactual"

#: The invented facts of this file's two checkpoints and the two version records that name
#: them: the ids, the lineage starts their one-member families open at, the file names and
#: the learner seeds (`docs/L1/battery.md` §4, D-15).
VERSION_REVEAL = "version-jacana-5611"
VERSION_PLAIN = "version-merlin-5612"
START_REVEAL = "R9/start-counterfactual-reveal"
START_PLAIN = "R9/start-counterfactual-none"
CHECKPOINT_REVEAL = "evaluation-join-counterfactual-reveal.ckpt"
REVEAL_SEED = J.CHECKPOINT_SEED_E

_CACHE = {}


def revealed_checkpoint():
    """One real checkpoint whose learner was built under the catalogue's second member.

    `agents.build_learner` takes the member in its spec and `agents.save` writes the
    **version 5** container that records it (`counterfactual.md` §6, `checkpoint.md` §2.1,
    D-43).  The learner is built and saved once, at the battery's small width and depth,
    under the scratch root — an absolute path in the platform's temporary area.
    """
    if "reveal" not in _CACHE:
        encoder = J.build_encoder(J.encoding_for(J.DEFAULT_KIND))
        learner = J.build_learner(
            {
                "backend": "numpy",
                "architecture": {
                    "kind": J.DEFAULT_KIND,
                    "width": J.WIDTH_A,
                    "depth": J.DEPTH_A,
                },
                "seed": REVEAL_SEED,
                "encoder": encoder,
                "counterfactual": REVEAL_COUNTERFACTUAL,
            }
        )
        path = J.save(learner, os.path.join(J.scratch_root(), CHECKPOINT_REVEAL))
        _CACHE["reveal"] = {
            "path": path,
            "learner": learner,
            "encoder": encoder,
            "seed": REVEAL_SEED,
        }
    return _CACHE["reveal"]


def plain_checkpoint():
    """The battery's own default checkpoint: a learner built under `none`, or under nothing.

    A learner spec that names no counterfactual is built under the catalogue's first
    member, its declared default, and its container records no such field
    (`counterfactual.md` §6, §9, D-43).  The checkpoint is the support's shared invented
    one, so this case adds no second save.
    """
    return J.checkpoint()


def revealed_member():
    """The version record of the reveal checkpoint, declaring the member its file records."""
    info = revealed_checkpoint()
    return {
        "id": VERSION_REVEAL,
        "path": info["path"],
        "rung": J.RUNG,
        "variant": J.VARIANT_LABEL,
        "seed": info["seed"],
        "step": J.STEP,
        "samples": J.SAMPLES,
        "lineage": START_REVEAL,
        "rule": J.DEFAULT_RULE,
        "utility": J.DEFAULT_UTILITY,
        "counterfactual": REVEAL_COUNTERFACTUAL,
    }


def plain_member():
    """The version record of the default checkpoint, carrying **no** `counterfactual` key.

    A member trained under the catalogue's first member records no field of the third
    catalogue at all -- neither in its container nor in its declaration
    (`counterfactual.md` §6, §9, `records.md` §7, D-43).
    """
    info = plain_checkpoint()
    return {
        "id": VERSION_PLAIN,
        "path": info["path"],
        "rung": J.RUNG,
        "variant": J.VARIANT_LABEL,
        "seed": info["seed"],
        "step": J.STEP,
        "samples": J.SAMPLES,
        "lineage": START_PLAIN,
        "rule": J.DEFAULT_RULE,
        "utility": J.DEFAULT_UTILITY,
    }


def pool_of(members):
    """One frozen pool holding the given version records, at the league's own bound."""
    return J.build_pool(
        {"members": list(members), "m": J.league()["m"], "frozen": True}
    )


def container_metadata(path):
    """The container's own `metadata.json`, exactly as the file lays it down (§2.1).

    `agents.checkpoint._read_metadata` answers the record the file is **read as**, which
    fills a version-1-to-4 container's absent conditional field with the catalogue's first
    member; the *file's* silence — the fact D-43 adds — is therefore read off the
    container's own member, the spelling `tests/agents/` uses for the same purpose.
    """
    with zipfile.ZipFile(path) as container:
        return json.loads(container.read("metadata.json").decode("utf-8"))


class CounterfactualJoin(J.JoinCase):
    """Two containers, one per catalogue member, and the pool records that certify them."""

    def test_join_evl_16_1_the_pool_certifies_the_member_its_container_records(self):
        """JOIN-EVL-16.1 a learner built under `reveal-counterfactual` writes a format-version-5 container recording that member, the version record declaring it is admitted and reads back carrying it, and the pool record's member and its `counterfactuals` set both name it; a learner under `none` writes a container with **no** such field, its version record carries none, and the pool record has no `counterfactuals` key at all (`counterfactual.md` §6, §9, `records.md` §7–§8, `checkpoint.md` §2.1, `rule.md` §8, `families.md` §4, ASM-27, D-43)."""
        read_metadata = J.mod("agents.checkpoint")._read_metadata
        catalogue = tuple(str(name) for name in J.learners()["counterfactuals"])
        self.assertEqual(
            catalogue[:2],
            (DEFAULT_COUNTERFACTUAL, REVEAL_COUNTERFACTUAL),
            "agents.learners() publishes the counterfactual catalogue in counterfactual.md "
            "§6's order, `none` first and the declared default, so the names this case "
            "asserts against are the module's own (D-43): %r" % (catalogue,),
        )
        with self.subTest(member=REVEAL_COUNTERFACTUAL):
            info = revealed_checkpoint()
            self.assertTrue(
                os.path.isfile(info["path"]),
                "the member names a checkpoint agents.save wrote, not a hand-built file "
                "(protocol.md §5, checkpoint.md §2.1): %r" % (info["path"],),
            )
            metadata = read_metadata(info["path"])
            self.assertEqual(
                int(metadata["format_version"]),
                5,
                "a learner whose counterfactual member is not `none` writes format version "
                "5, the version that records it (counterfactual.md §6, checkpoint.md §2.1, "
                "D-43): %r" % (metadata.get("format_version"),),
            )
            self.assertEqual(
                metadata["counterfactual"],
                REVEAL_COUNTERFACTUAL,
                "the container records the catalogue member its targets came from, "
                "immediately after the utility, so the file is the witness the pool "
                "certifies (counterfactual.md §6, records.md §7, ASM-20, D-43): %r"
                % (metadata.get("counterfactual"),),
            )
            record = J.pool_members(pool_of([revealed_member()]))
            member = J.member_record(record, VERSION_REVEAL)
            self.assertEqual(
                member.get("counterfactual"),
                REVEAL_COUNTERFACTUAL,
                "build_pool admits the declaration and pool_members reads it back carrying "
                "the member the record named (records.md §7, pool.md §5, D-43): %r"
                % (member,),
            )
            self.assertEqual(
                member["counterfactual"],
                metadata["counterfactual"],
                "the pool member's declaration and its own container's field agree, which "
                "is what makes the read-back a certification rather than a claim "
                "(counterfactual.md §6, records.md §7, ASM-20, D-43)",
            )
            self.assertIn(
                "counterfactuals",
                record,
                "the pool record carries the third catalogue's conditional key when a "
                "version was trained under a non-default member (records.md §8, "
                "counterfactual.md §6, D-43): %r" % (sorted(record),),
            )
            self.assertEqual(
                tuple(str(name) for name in record["counterfactuals"]),
                (REVEAL_COUNTERFACTUAL,),
                "the pool record's `counterfactuals` set names the member its member "
                "declares, once and in the window's order (records.md §8, families.md §2, "
                "D-43): %r" % (record["counterfactuals"],),
            )
        with self.subTest(member=DEFAULT_COUNTERFACTUAL):
            info = plain_checkpoint()
            metadata = read_metadata(info["path"])
            self.assertEqual(
                int(metadata["format_version"]),
                3,
                "a learner under `none` writes today's version, so the third catalogue "
                "moved no field of a default container (counterfactual.md §6, §9, "
                "checkpoint.md §2.1, D-43): %r" % (metadata.get("format_version"),),
            )
            self.assertEqual(
                metadata["counterfactual"],
                DEFAULT_COUNTERFACTUAL,
                "the container records no such field and is read as the catalogue's first "
                "member, which is what makes the silence a member and not a gap "
                "(counterfactual.md §6, records.md §7, D-43): %r"
                % (metadata.get("counterfactual"),),
            )
            self.assertNotIn(
                "counterfactual",
                container_metadata(info["path"]),
                "the file itself lays down no `counterfactual` field, so a `none` save is "
                "byte-identical to the one it wrote before the catalogue existed "
                "(checkpoint.md §2.1, counterfactual.md §6, §9, D-43): %r"
                % (sorted(container_metadata(info["path"])),),
            )
            record = J.pool_members(pool_of([plain_member()]))
            member = J.member_record(record, VERSION_PLAIN)
            self.assertNotIn(
                "counterfactual",
                member,
                "a version record that named no counterfactual reads back without one, "
                "because absence is the default and no key is invented for it (records.md "
                "§7, pool.md §5, counterfactual.md §6, D-43): %r" % (member,),
            )
            self.assertNotIn(
                "counterfactuals",
                record,
                "the pool record of a version trained under `none` carries **no** "
                "`counterfactuals` key, which is what keeps a `none` pool reading back the "
                "record it read back before (records.md §8, counterfactual.md §6, §9, "
                "D-43): %r" % (sorted(record),),
            )

    def test_join_evl_16_2_the_two_members_pools_do_not_wear_one_id(self):
        """JOIN-EVL-16.2 the same one-member declaration under the two catalogue members yields two different pool ids, and each id is exactly the digest the support recomputes from that pool's own members — so the difference is the appended field alone — while a baselines-only pool over the same declaration set keeps one id, the third catalogue reaching no baseline line (`families.md` §4, `records.md` §8, `counterfactual.md` §6, §9, ASM-27, D-43)."""
        silent = J.pool_members(pool_of([plain_member()]))
        declared = J.pool_members(
            pool_of([dict(plain_member(), counterfactual=REVEAL_COUNTERFACTUAL)])
        )
        self.assertEqual(
            J.names_of(declared),
            J.names_of(silent),
            "the same one-member declaration is one membership — the three pinned baselines "
            "and the one version — under either member, so the id is what has to change "
            "(records.md §8, families.md §4, D-43): %r against %r"
            % (J.names_of(declared), J.names_of(silent)),
        )
        self.assertNotEqual(
            declared["id"],
            silent["id"],
            "one membership under two counterfactual members wears two ids, because the "
            "digest appends the member when it is not `none` (families.md §4, ASM-27, "
            "D-43): %r against %r" % (declared["id"], silent["id"]),
        )
        for label, record in (
            ("the member declared under `none`", silent),
            ("the same member declared under the reveal", declared),
        ):
            with self.subTest(pool=label):
                self.assertEqual(
                    str(record["id"]),
                    J.pool_id(J.members_of(record)),
                    "each id is exactly the digest of that pool's own ordered members, the "
                    "declaring member's line carrying the appended field and the silent "
                    "one's carrying none, so nothing but that field separates the two "
                    "(families.md §4, ASM-27, D-43): %r for %r"
                    % (record["id"], J.names_of(record)),
                )
        with self.subTest(case="the two real containers"):
            reveal_record = J.pool_members(pool_of([revealed_member()]))
            self.assertEqual(
                J.names_of(reveal_record),
                [str(name) for name in J.protocol()["baselines"]] + [VERSION_REVEAL],
                "the reveal container declared as one family's only member is a pool of the "
                "three pinned baselines and it (records.md §8, families.md §2, D-43): %r"
                % (J.names_of(reveal_record),),
            )
            self.assertNotEqual(
                reveal_record["id"],
                silent["id"],
                "the pool of a member trained under the reveal wears an id the same shape "
                "of pool under `none` does not (families.md §4, ASM-27, D-43): %r against %r"
                % (reveal_record["id"], silent["id"]),
            )
            self.assertEqual(
                str(reveal_record["id"]),
                J.pool_id(J.members_of(reveal_record)),
                "and that id is the digest of that pool's own members, the version's line "
                "carrying its declared member (families.md §4, ASM-27, D-43): %r for %r"
                % (reveal_record["id"], J.names_of(reveal_record)),
            )
        with self.subTest(case="a baselines-only pool keeps one id"):
            bare = J.pool_members(pool_of([]))
            again = J.pool_members(
                J.build_pool(
                    {"members": [], "m": J.league()["m"], "frozen": True}
                )
            )
            self.assertEqual(
                bare["id"],
                again["id"],
                "a baselines-only pool over the same declaration set keeps one id, so the "
                "third catalogue renames nothing that holds no version (records.md §8, "
                "families.md §4, ASM-27, D-43): %r against %r"
                % (bare["id"], again["id"]),
            )
            self.assertEqual(
                bare["id"],
                J.pool_id(J.members_of(bare)),
                "that one id is the digest of the three pinned baseline lines and nothing "
                "else, so no counterfactual field can reach it (families.md §4, "
                "counterfactual.md §9, ASM-27, D-43): %r for %r"
                % (bare["id"], J.names_of(bare)),
            )
            self.assertNotIn(
                "counterfactuals",
                bare,
                "a pool with no version names no counterfactual member at all (records.md "
                "§8, counterfactual.md §6, D-43): %r" % (sorted(bare),),
            )


if __name__ == "__main__":
    unittest.main()
