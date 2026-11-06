"""FAM-15 — a rung is a configuration and a league is data.

`docs/L1/battery.md` §3 FAM-15, `docs/L1/ladder.md` §3 and `docs/L1/league.md` §2
(D-3, D-16).  The proof that the machinery is generic: a seventh rung configuration and
a pool membership that appear in no design document run through the same loop, the same
fairness report, the same pool operations and the same report as R1..R6 and the league's
own membership.  The axis, the variant names, the sizes, the hyperparameters, the budget,
the seeds and the version lineage are the battery's own.
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


class FAM15Custom(S.SurfaceCase):
    """The battery's own configuration and membership, driven as data."""

    # -- helpers -----------------------------------------------------------
    def custom(self):
        return S.custom_rung()

    def variants(self):
        return S.variant_entries(self.custom())

    # -- the custom rung ---------------------------------------------------
    def test_fam15_1_training_run_accepts_a_configuration_instead_of_a_name(self):
        """FAM-15.1 training.run takes ladder.md §3's schema directly as data."""
        seeds = (S.SEED_A,)
        record = self.run_record(self.custom(), seeds, S.BUDGET_TINY)
        self.assertTrue(S.is_mapping(record), "training.run must return a run record")
        self.assertTrue(
            self.curves_of(record),
            "the seventh rung reports its curves like any rung (protocol.md §1): %r"
            % (sorted(str(key) for key in record),),
        )
        paths = R.checkpoint_paths_of(record)
        variants = len(self.variants())
        least, most = R.checkpoint_span(S.LEAGUE_BOUND, variants, len(seeds))
        self.assertGreaterEqual(
            len(paths),
            least,
            "the configuration's %d variants write one final checkpoint each, so the run "
            "record names at least %d artefact (records.md §12, protocol.md §5): %r"
            % (variants, least, paths),
        )
        self.assertLessEqual(
            len(paths),
            most,
            "records.md §12 makes the checkpoints key the retained snapshots plus the final "
            "model per variant per seed: at most %d at M = %d for %d variant × seed pairs, "
            "even though the run wrote ten snapshots apiece (ASM-18): %r"
            % (most, S.LEAGUE_BOUND, variants * len(seeds), paths),
        )
        for path in paths:
            self.assertTrue(
                os.path.exists(path),
                "a configuration in no document still ships artefacts that exist: %r" % (path,),
            )

    def test_fam15_2_the_custom_run_records_its_own_budget_seeds_and_pool(self):
        """FAM-15.2 the record carries the configuration's budget, seed and pool id."""
        record = self.run_record(self.custom(), (S.SEED_A,), S.BUDGET_TINY)
        self.assertIn(
            S.SEED_A,
            [int(number) for number in S.declared_numbers(record, "seeds", "seed")],
            "the run record carries the seed set it was given (records.md §12): %r"
            % (record,),
        )
        self.assertIn(
            str(S.BUDGET_TINY),
            S.flatten_text(record),
            "the run record carries the sample budget it actually used (%d, invented): %r"
            % (S.BUDGET_TINY, record),
        )
        declared = S.pool_identity(self.custom())
        self.assertTrue(
            declared,
            "the configuration's pool entry carries the id every arm's run record must carry "
            "(ladder.md §3): %r" % (self.custom(),),
        )
        carried = S.pool_identity(record)
        self.assertTrue(
            any(str(identifier) in carried for identifier in declared),
            "the run record carries the pool id its configuration declared (%r), so both arms "
            "of the pair can be shown to have trained against one pool (ladder.md §4, "
            "ASM-16): %r" % (declared, carried),
        )

    def test_fam15_3_fairness_reports_the_custom_pair_s_own_axis(self):
        """FAM-15.3 fairness reads the axis out of the configuration, not a table."""
        variants = self.variants()
        self.assertEqual(
            len(variants),
            2,
            "the battery's seventh rung declares its own pair of variants (ladder.md §3)",
        )
        result = self.ep("training", "fairness")(variants[0], variants[1])
        text = S.axis_text(result)
        self.assertTrue(
            "depth" in text or "width" in text or "spars" in text,
            "fairness reports the pair's own axis — depth against width at sparse "
            "connectivity — and not the ladder's (ladder.md §4): %r" % (text,),
        )
        body = S.flatten_text(result)
        for token in ("budget", "seed", "param"):
            self.assertIn(
                token,
                body,
                "fairness reports what the pair holds constant, including %r (ladder.md §4): %r"
                % (token, result),
            )

    # -- the custom membership --------------------------------------------
    def test_fam15_4_a_custom_membership_runs_through_the_pool_and_a_cell(self):
        """FAM-15.4 an invented membership is data: build, read back, advance, play."""
        declaration = {
            "members": [R.make_version(self, "kestrel", seed=S.SEED_A, step=53),
                        R.make_version(self, "bramble", seed=S.SEED_B, step=106,
                                       lineage="version-kestrel")],
            "m": S.LEAGUE_BOUND,
            # The case advances this pool, and records.md §8 ties frozen-ness to the
            # membership not changing while the pool is used, so it is declared unfrozen.
            "frozen": False,
        }
        pool = self.pool(declaration)
        row = self.members(pool)
        members = R.member_ids(row)
        self.assertEqual(
            len(R.version_members(row)),
            2,
            "the pool carries the two invented versions the declaration names "
            "(records.md §8): %r" % (members,),
        )
        for baseline in S.BASELINES:
            self.assertIsNotNone(
                R.baseline_member(members, baseline),
                "the baselines are added and pinned for an invented membership too "
                "(league.md §2): %r" % (members,),
            )
        advanced = self.ep("evaluation", "offer")(
            pool, R.make_version(self, "thistle", seed=S.SEED_C, step=159,
                                 lineage="version-bramble")
        )
        self.assertEqual(
            len(R.version_members(self.members(advanced))),
            3,
            "the invented membership grows by the version it is offered (league.md §2): %r"
            % (self.members(advanced),),
        )
        cell = self.match(
            left=self.member_policy("kestrel"),
            right=self.member_policy("bramble"),
            hands=S.CELL_HANDS_SMALL,
            seed=S.TABLE_SEED_B,
        )
        self.assertEqual(
            R.cell_hands(cell),
            S.CELL_HANDS_SMALL,
            "two invented members play one cell at the invented cell size (14 hands, "
            "battery.md §2): %r" % (cell,),
        )

    def test_fam15_5_the_registry_does_not_know_the_custom_rung_but_the_report_does(self):
        """FAM-15.5 the custom rung is not a registry entry and still reports."""
        name = self.custom()["name"]
        self.assertNotIn(
            name,
            S.rung_names(self.ep("training", "rungs")()),
            "the seventh rung is a configuration, not a registry entry: %r"
            % (S.rung_names(self.ep("training", "rungs")()),),
        )
        text = S.refusal_text(lambda: self.ep("training", "rung")(name))
        self.assertIsNotNone(
            text,
            "training.rung refuses a name it does not carry and does not resolve it as a "
            "configuration (e2e-surface §2, ladder.md §3)",
        )
        self.assertIn(
            S._family_token(name),
            S._family_token(text),
            "the refusal names the unknown rung: %r" % (text,),
        )
        league = S.shared_league(self)
        pair_cell = self.match(
            left=self.member_policy("kestrel"),
            right=self.member_policy("bramble"),
            hands=S.CELL_HANDS_SMALL,
            seed=S.TABLE_SEED_A,
        )
        record = self.evidence_record(
            self.run_record(self.custom(), (S.SEED_A,), S.BUDGET_TINY),
            matrix=league["matrix"],
            rating=league["rating"],
            pool_row=self.members(league["pool"]),
            axis_row=pair_cell,
            seeds=(S.SEED_A,),
            budget=S.BUDGET_TINY,
        )
        report = self.report_of(name, record, league["matrix"], league["rating"])
        self.assertTrue(S.is_mapping(report), "the custom rung's report is a record")
        for family in S.FAMILIES:
            self.assertTrue(
                S.has_family(report, family),
                "a configuration in no design document reports every family (protocol.md "
                "§1): missing %r in %r" % (family, sorted(str(key) for key in report)),
            )


if __name__ == "__main__":
    unittest.main()
