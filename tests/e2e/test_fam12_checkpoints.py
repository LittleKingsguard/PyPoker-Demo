"""FAM-12 — checkpoints, the decision boundary, and the retained window.

`docs/L1/battery.md` §3 FAM-12 and `docs/L1/protocol.md` §5 as D-16 amends it (ASM-5,
ASM-18).  A run writes ten intra-run snapshots at equal intervals plus its final model;
what ships is each rung's final model per variant per seed plus the pool's retained
versions, and the rolling window keeps the last M of the ten.  ``agents.save`` /
``agents.load`` is loss-free at the decision boundary, ``evaluation.policy_from`` loads
one member in evaluation mode, and ``training.checkpoints()`` is the index over exactly
that set.
"""

import os
import sys
import unittest

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _records as R  # noqa: F401
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _records as R  # noqa: E402
    import _surface as S  # noqa: E402


class FAM12Checkpoints(S.SurfaceCase):
    """Snapshots, retention, the save/load round-trip and the shipped index."""

    # -- helpers -----------------------------------------------------------
    def saved(self, name="fam12", width=None, depth=None, seed=S.SEED_A):
        """A learner and the checkpoint it was saved to, both built by the battery."""
        spec = self.learner_spec(
            width=S.VERSION_WIDTH if width is None else width,
            depth=S.VERSION_DEPTH if depth is None else depth,
            seed=seed,
        )
        learner = self.ep("agents", "build_learner")(spec)
        path = self.ep("agents", "save")(
            learner, os.path.join(self.scratch(), "%s.pt" % (name,))
        )
        return spec, learner, path

    def big_run(self):
        """One single-variant run at the battery's own budget (250 hands)."""
        return self.run_record("R1", (S.SEED_A,), S.BUDGET)

    def test_fam12_1_a_run_names_the_retained_snapshots_and_its_final_model(self):
        """FAM-12.1 a run record names at most M retained snapshots plus its final model."""
        seeds = (S.SEED_A,)
        record = self.big_run()
        paths = R.checkpoint_paths_of(record)
        variants = len(S.VARIANTS["R1"])
        least, most = R.checkpoint_span(S.LEAGUE_BOUND, variants, len(seeds))
        self.assertGreaterEqual(
            len(paths),
            least,
            "a run names the final model of each of its variant × seed pairs, so this one "
            "names at least %d checkpoint (protocol.md §5, records.md §12): %r"
            % (least, paths),
        )
        self.assertLessEqual(
            len(paths),
            most,
            "records.md §12 makes the checkpoints key the retained snapshots plus the final "
            "model per variant per seed: a run at M = %d with %d variant × seed pair names at "
            "most %d, even though the run wrote ten snapshots (protocol.md §5, ASM-18): %r"
            % (S.LEAGUE_BOUND, variants * len(seeds), most, paths),
        )
        for path in paths:
            self.assertTrue(
                os.path.exists(path),
                "a snapshot the run record names is on disk, because the pool is built "
                "from the checkpoints the repository ships (protocol.md §5): %r" % (path,),
            )

    def test_fam12_2_save_and_load_are_loss_free_at_the_decision_boundary(self):
        """FAM-12.2 a loaded checkpoint chooses the action its learner chooses."""
        spec, learner, path = self.saved("fam12-2")
        loaded = self.ep("agents", "load")(spec, path)
        encoder = self.encoder()
        walk = self.decision_walk(S.SEED_C, self.baseline("always-call", S.SEED_D), limit=4)
        self.assertTrue(walk, "the case drove no decision at all")
        for _hand, readout, _legal, _action, _index in walk:
            self.assertEqual(
                self.action_index(self.act(learner, encoder, readout)),
                self.action_index(self.act(loaded, encoder, readout)),
                "save/load is loss-free at the decision boundary, which is what lets a "
                "shipped version be a league member (protocol.md §5, ASM-5)",
            )

    def test_fam12_3_policy_from_loads_the_action_its_learner_chooses(self):
        """FAM-12.3 evaluation.policy_from loads one member in evaluation mode."""
        spec, learner, path = self.saved("fam12-3", seed=S.SEED_C)
        del spec
        policy = self.ep("evaluation", "policy_from")(path)
        encoder = self.encoder()
        walk = self.decision_walk(S.SEED_J, self.baseline("always-call", S.SEED_D), limit=3)
        self.assertTrue(walk, "the case drove no decision at all")
        for _hand, readout, legal, _action, _index in walk:
            chosen = policy(readout, legal)
            self.assertEqual(
                self.chosen_index(legal, chosen),
                self.action_index(self.act(learner, encoder, readout)),
                "the policy loaded from a checkpoint chooses the action its learner "
                "chooses on the same readout (protocol.md §5, D-16): %r" % (chosen,),
            )

    def test_fam12_4_the_retained_window_is_the_last_m_of_the_run_s_snapshots(self):
        """FAM-12.4 offering a run's snapshots keeps the window's last M."""
        record = self.big_run()
        paths = R.checkpoint_paths_of(record)
        self.assertGreaterEqual(
            len(paths),
            S.LEAGUE_BOUND + 1,
            "the window can only be observed keeping M of more than M snapshots, so the "
            "record offers its M retained snapshots beside its final model: %r" % (paths,),
        )
        versions = []
        previous = "R1-battery-start"
        for index, path in enumerate(paths):
            versions.append(
                R.make_version(
                    self,
                    "snap-%02d" % (index,),
                    seed=S.SEED_A,
                    step=7 * (index + 1),
                    samples=S.BUDGET * (index + 1) // len(paths),
                    lineage=previous,
                    rung="R1",
                    variant="naive-numeric",
                )
            )
            versions[-1]["path"] = path
            previous = versions[-1]["id"]
        # records.md §8: a frozen pool's membership does not change while it is used, so a
        # case that rolls the window builds the pool unfrozen.
        pool = self.pool({"members": [], "m": S.LEAGUE_BOUND, "frozen": False})
        for version in versions:
            pool = self.ep("evaluation", "offer")(pool, version)
        row = self.members(pool)
        kept = R.version_members(row)
        self.assertEqual(
            len(kept),
            S.LEAGUE_BOUND,
            "the rolling window retains the last M = %d versions of the run's snapshots "
            "(protocol.md §5, ASM-18): %r" % (S.LEAGUE_BOUND, kept),
        )
        expected = [version["id"] for version in versions[-S.LEAGUE_BOUND:]]
        for version_id in expected:
            self.assertIn(
                version_id,
                kept,
                "the retained window holds the last M snapshots by lineage order (%r): %r"
                % (expected, kept),
            )
        for version_id in [version["id"] for version in versions[:-S.LEAGUE_BOUND]]:
            self.assertNotIn(
                version_id,
                kept,
                "a snapshot older than the last M leaves the window as the next one arrives "
                "(ASM-18): %r" % (kept,),
            )

    def test_fam12_5_the_index_carries_each_rung_variant_s_final_model(self):
        """FAM-12.5 training.checkpoints indexes every rung variant's final model."""
        index = self.ep("training", "checkpoints")()
        paths = S.checkpoint_paths(index)
        variants = sum(len(names) for names in S.VARIANTS.values())
        self.assertGreaterEqual(
            len(paths),
            variants,
            "what ships is each rung variant's final model per seed, so the index names at "
            "least the ladder's %d variants' artefacts (protocol.md §5, ASM-5): %r"
            % (variants, paths),
        )
        for path in paths:
            self.assertTrue(
                os.path.exists(path),
                "the index points at artefacts that exist, so a talk can load a member: %r"
                % (path,),
            )

    def test_fam12_6_the_index_lists_no_artefact_twice(self):
        """FAM-12.6 the shipped index is an index: each artefact is listed once."""
        index = self.ep("training", "checkpoints")()
        # The assertion is about the *listing*, so it reads the listing: every path the
        # index names, in the order it names them, with every repeat still in place.  A
        # de-duplicating reader would have erased the very evidence a repeat leaves
        # behind, and an index naming one artefact many times would pass (battery.md §2).
        listed = S.checkpoint_path_listing(index)
        self.assertTrue(
            listed,
            "the shipped index names the shipped checkpoints (protocol.md §5): %r" % (index,),
        )
        repeated = sorted({path for path in listed if listed.count(path) > 1})
        self.assertEqual(
            repeated,
            [],
            "an index entry appears once, so a member is not counted twice when the pool's "
            "retained versions and the rung's finals share an artefact (protocol.md §5): "
            "the index lists %r, and %r appear in it more than once"
            % (listed, repeated),
        )

    # -- the rule a checkpoint records (D-19) ------------------------------
    def test_fam12_7_a_saved_checkpoint_records_the_rule_it_was_trained_under(self):
        """FAM-12.7 a checkpoint records its rule and reloads under it."""
        encoder = self.encoder()
        walk = self.decision_walk(S.SEED_C, self.baseline("always-call", S.SEED_D), limit=2)
        self.assertTrue(walk, "the case drove no decision at all")
        for rule in (S.RULE_DEFAULT, S.RULE_SECOND):
            learner = self.rule_learner(rule, seed=S.SEED_I)
            path = self.ep("agents", "save")(
                learner, os.path.join(self.scratch(), "fam12-7-%s.ckpt" % (S._family_token(rule),))
            )
            self.assertEqual(
                getattr(self.ep("evaluation", "policy_from")(path), "learning_rule", None),
                rule,
                "a checkpoint records the rule its learner was trained under, and "
                "evaluation.policy_from reports the rule the file records, because playback "
                "is rule-free and the file is the only witness (rules.md §6, "
                "e2e-surface.md §3.4, D-19): %r" % (path,),
            )
            spec = self.learner_spec(
                width=S.RULE_WIDTH, depth=S.RULE_DEPTH, seed=S.SEED_I, learning_rule=rule
            )
            restored = self.ep("agents", "load")(spec, path)
            for _hand, readout, _legal, _action, _index in walk:
                self.assertEqual(
                    self.action_index(self.act(restored, encoder, readout)),
                    self.action_index(self.act(learner, encoder, readout)),
                    "a checkpoint restores under the rule it records, and the restored "
                    "learner decides as the saved one (rules.md §6, ASM-5): %r" % (path,),
                )

    def test_fam12_8_the_index_names_the_rule_each_artefact_was_trained_under(self):
        """FAM-12.8 training.checkpoints() carries each entry's rule."""
        index = self.ep("training", "checkpoints")()
        reported = S.find_values(index, "rule")
        self.assertTrue(
            reported,
            "training.checkpoints() indexes the shipped set, and each entry carries the "
            "rule it was trained under, so a reader can tell which estimator a member is "
            "(e2e-surface.md §3.5, rules.md §6, D-19): %r" % (index,),
        )
        names = set()
        for value in reported:
            names |= {text.strip() for text in S.strings(value) if text.strip()}
        declared = S.rule_names(self.ep("agents", "learners")())
        for name in sorted(names):
            self.assertIn(
                name,
                declared,
                "every rule the index reports is a catalogue member, because a name outside "
                "it is refused where it is declared (rules.md §2, §4): %r not in %r"
                % (name, declared),
            )
        self.assertEqual(
            sorted(names),
            [S.RULE_DEFAULT],
            "the checkpoints the repository ships were written before the catalogue "
            "existed, so a version 1 container carries no `learning_rule` and is read as "
            "%r, the only rule its writer could have used — the shipped set is not "
            "regenerated (rules.md §6, ASM-5): the index reports %r"
            % (S.RULE_DEFAULT, sorted(names)),
        )


if __name__ == "__main__":
    unittest.main()
