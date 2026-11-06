"""The checkpoint join -- TRNJ-6.

`surface.md` §7 and `docs/L3/training/checkpoints.md` §4-§5: the index names per
rung and variant and seed that variant's final model and per rung the retained
versions of the window its successor inherits, every path is an artefact inside the
repository that `evaluation.policy_from` loads, and every artefact appears once.

The join is the one no single module can check (`docs/L1/battery.md` §5,
`docs/L1/protocol.md` §5): a checkpoint is a league member only if `agents.save`
wrote it, `agents.load` restores it at the capacity the run declared, and
`evaluation.policy_from` turns it into a policy that answers a decision at a real
readout.  `agents.save`/`agents.load` loss-free at the decision boundary is what
makes a shipped version a league member at all (ASM-5, D-16,
`docs/L2/evaluation/surface.md` §12).
"""

import importlib.util
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
# The support module is loaded under a private name: this repository's integration
# batteries share the file name `_join_support.py`, so a plain import would hand one
# battery another's helpers when two test directories are collected in one process.
if "training_join_support" in sys.modules:
    J = sys.modules["training_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "training_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["training_join_support"] = J
    _spec.loader.exec_module(J)


class CheckpointJoin(J.JoinCase):
    """TRNJ-6 -- a run's final model loads as a league member."""

    def test_trnj_6_1_a_runs_final_model_loads_as_a_league_member(self):
        """TRNJ-6.1 the record's final path is a loadable, capped league member.

        `docs/L2/training/surface.md` §4 makes `checkpoints` the paths
        `agents.save` wrote; `docs/L2/evaluation/surface.md` §12 loads one through
        `evaluation.policy_from`, which is `agents.as_policy` of `agents.load(None,
        path)` at the seed and encoding the container records, in evaluation mode.
        The capacity the restored member reports is inside the declared parameter
        budget of ±2%, which is the capacity ASM-10 matches a comparison pair on --
        measured here by the battery, because a run measures no capacity
        (`docs/L3/training/loop.md` §3, `loop.md` §9's FAM-3 note, ASM-10).
        """
        record = J.small_run()
        variant = str(record["variants"][0]["name"])
        final = str(J.checkpoints_of(record, variant, J.RUN_SEED)["final"])
        self.assertTrue(
            os.path.exists(J.resolve(final)),
            "the record carries agents.save's path spelled repository-relative, so the "
            "repository root resolves it to the file that was written and the record "
            "travels with the tree (docs/L3/training/checkpoints.md §2, FAM-12.1): %r"
            % (final,),
        )
        readout, legal = J.readout_at(J.REPLAY_SEED)
        member = J.policy_from(final)
        self.assertTrue(
            callable(member),
            "`policy_from` returns a policy in the sense of e2e-surface.md §2 "
            "(docs/L2/evaluation/surface.md §12)",
        )
        descriptor = member(readout, legal)
        self.assert_descriptor_in(
            legal, descriptor,
            "a shipped member answers one decision at a real readout",
        )
        learner = J.load(None, final)
        count = J.param_count(learner)
        self.assertIsInstance(
            count, int,
            "`agents.param_count` returns one integer, the member's capacity "
            "(ASM-10, docs/L2/agents/surface.md §5)",
        )
        declared = J.params_of(record, variant)
        self.assertEqual(
            (float(declared["lower"]), float(declared["upper"])),
            J.band(int(declared["budget"])),
            "the record states the declared parameter budget and its ±2% bound, and "
            "no measurement substituted for it (docs/L2/training/surface.md §4, "
            "ASM-10)",
        )
        self.assertLessEqual(
            float(declared["lower"]),
            float(count),
            "the member's measured capacity is inside the declared parameter budget "
            "(ASM-10): %r < %r" % (count, declared["lower"]),
        )
        self.assertLessEqual(
            float(count),
            float(declared["upper"]),
            "the member's measured capacity is inside the declared parameter budget "
            "(ASM-10): %r > %r" % (count, declared["upper"]),
        )
        entry = J.variant_entry(J.rung(str(record["rung"])), variant)
        encoder = J.build_encoder(entry["encoding"])
        index = J.action_index(
            J.act(learner, J.encode(encoder, readout), J.legal_indices(legal))
        )
        self.assertTrue(
            J.same_descriptor(descriptor, J.decode_action(index)),
            "a loaded checkpoint chooses the action its learner chose on the same "
            "readout, so a shipped version is a league member at all (ASM-5, "
            "docs/L2/evaluation/surface.md §12, docs/L1/protocol.md §5): readout "
            "seed %r" % (J.REPLAY_SEED,),
        )

    def test_trnj_6_2_the_indexs_first_entry_loads_the_same_way(self):
        """TRNJ-6.2 the shipped index's first entry is a loadable checkpoint.

        `docs/L2/training/surface.md` §7: every path the index names is an artefact
        "that `evaluation.policy_from` loads", and `docs/L3/training/checkpoints.md`
        §5 adds that the first entry must be a checkpoint `agents.save` wrote and
        never a manifest.  Its capacity sits in the declared ±2% band of its rung
        variant's parameter budget, the same band ASM-10 holds every member to.
        """
        entries = J.entries()
        self.assertGreater(
            len(entries),
            0,
            "the shipped index names the artefacts the repository declared; it is "
            "declared data and never filtered to what happens to be on disk "
            "(docs/L2/training/surface.md §7, "
            "docs/L3/training/checkpoints.md §4)",
        )
        first = entries[0]
        path = str(first["path"])
        self.assertTrue(
            os.path.exists(J.resolve(path)),
            "an artefact the index names is a file the repository carries "
            "(docs/L3/training/checkpoints.md §5, FAM-12.5): %r" % (path,),
        )
        readout, legal = J.readout_at(J.REPLAY_SEED + 4)
        member = J.policy_from(path)
        descriptor = member(readout, legal)
        self.assert_descriptor_in(
            legal, descriptor,
            "the index's first entry is a policy that answers a real decision",
        )
        learner = J.load(None, path)
        count = J.param_count(learner)
        configuration = J.rung(str(first["rung"]))
        budget = J.declared_param_budget(configuration, str(first["variant"]))
        lower, upper = J.band(budget)
        self.assertGreaterEqual(
            float(count),
            lower,
            "the shipped member's capacity is inside the parameter budget its variant "
            "declares (ASM-10, docs/L3/training/registry.md §4): %r < %r"
            % (count, lower),
        )
        self.assertLessEqual(
            float(count),
            upper,
            "the shipped member's capacity is inside the parameter budget its variant "
            "declares (ASM-10, docs/L3/training/registry.md §4): %r > %r"
            % (count, upper),
        )

    def test_trnj_6_3_the_index_names_one_path_per_artefact_inside_the_repository(self):
        """TRNJ-6.3 every entry names one in-repository artefact, once.

        `docs/L2/training/surface.md` §7: "Every path is an artefact inside the
        repository ... and every artefact appears once", and the index is "declared
        data over `checkpoints/`, never a directory scan".  An entry is a
        `records.md` §7 record extended with `kind`, which is what lets a window be
        read as the snapshot entries alone (`docs/L3/training/checkpoints.md` §4).
        """
        entries = J.entries()
        root = os.path.abspath(J.ROOT)
        paths = [str(entry["path"]) for entry in entries]
        ids = [str(entry["id"]) for entry in entries]
        self.assertEqual(
            len(set(paths)),
            len(paths),
            "each artefact is listed exactly once, because a repeat would make the "
            "index count an artefact twice (docs/L3/training/checkpoints.md §4, "
            "FAM-12.6)",
        )
        self.assertEqual(
            len(set(ids)),
            len(ids),
            "an entry's id is unique within the index, so two reports can name one "
            "version (records.md §7, docs/L3/training/checkpoints.md §4)",
        )
        for entry in entries:
            entry_path = str(entry["path"])
            absolute = J.resolve(entry_path)
            self.assertTrue(
                absolute == root or absolute.startswith(root + os.sep),
                "no entry names a path outside the repository "
                "(docs/L2/training/surface.md §7, "
                "docs/L3/training/checkpoints.md §5): %r" % (entry_path,),
            )
            self.assertTrue(
                os.path.exists(absolute),
                "every path the index names is a file the repository carries "
                "(docs/L3/training/checkpoints.md §5): %r" % (entry_path,),
            )
            for key in ("id", "path", "rung", "variant", "seed", "step",
                        "samples", "lineage", "kind"):
                self.assertIn(
                    key,
                    entry,
                    "an entry is a records.md §7 record extended with `kind` "
                    "(docs/L3/training/checkpoints.md §4): %r is missing from %r"
                    % (key, entry.get("id")),
                )
            self.assertIn(
                str(entry["kind"]),
                ("snapshot", "final"),
                "`kind` says whether the entry is one of the retained snapshots or "
                "the pair's final model (docs/L3/training/checkpoints.md §4)",
            )


if __name__ == "__main__":
    unittest.main()
