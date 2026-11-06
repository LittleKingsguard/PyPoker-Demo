"""FAM-3 — six rungs, one machinery, one axis per comparison, one frozen pool.

`docs/L1/battery.md` §3 FAM-3, `docs/L1/ladder.md` §2–§4, D-3 and D-16 (ASM-16).  The
ladder is data: six rung declarations in brief §2's order, and every comparison pair —
adjacent or intra-rung — differs on exactly the one axis the pair is named for and is
matched on everything `training.fairness` is required to report.

Rev 2 adds the frozen-pool clause.  A rung trains and is evaluated against the last M
versions of the rung it inherits plus the three baselines, frozen before either arm
trains, so both arms of R4, R5 and R6 sample one pool and their records carry one pool
id (`ladder.md` §2, ASM-16).  The cases below assert that at the declarations and, where
a run is cheap enough, at the run record.
"""

import os
import sys
import unittest

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _surface as S  # noqa: E402


class FAM3Ladder(S.SurfaceCase):
    """The rung registry, the fairness of every pair, and the one frozen pool."""

    # -- helpers -----------------------------------------------------------
    def names(self):
        return S.rung_names(self.ep("training", "rungs")())

    def rung(self, name):
        return self.ep("training", "rung")(name)

    def variant_names(self, config):
        return [S.variant_name(entry, index)
                for index, entry in enumerate(S.variant_entries(config))]

    def variant(self, rung_name, variant_name):
        for entry in S.variant_entries(self.rung(rung_name)):
            if S.variant_name(entry) == variant_name:
                return entry
        raise AssertionError(
            "rung %r declares no variant %r; it declares %r"
            % (rung_name, variant_name, self.variant_names(self.rung(rung_name)))
        )

    def primary(self, config):
        values = S.find_values(config, "primary")
        self.assertTrue(values, "the rung configuration declares no primary variant: %r" % (config,))
        value = values[0]
        if S.is_mapping(value):
            return S.variant_name(value)
        return str(value)

    def carried_from(self, config):
        values = S.find_values(config, "carried_from") or S.find_values(config, "carried")
        self.assertTrue(values, "the rung configuration declares no carried_from: %r" % (config,))
        value = values[0]
        if S.is_mapping(value):
            return S.variant_name(value)
        return str(value)

    def axis_of(self, result):
        return S.axis_text(result)

    def assert_axis(self, result, wanted, pair):
        text = self.axis_of(result)
        self.assertTrue(
            any(token in text for token in wanted),
            "training.fairness(%s) must report the axis it found, one of %r; it reported %r"
            % (pair, wanted, text),
        )

    def declared_bound(self, config):
        """The pool bound a rung configuration declares (``ladder.md`` §3: the pool's M)."""
        return S.bound_numbers(config)

    # -- the registry ------------------------------------------------------
    def test_fam3_1_six_rungs_in_brief_order(self):
        """FAM-3.1 training.rungs declares R1..R6 in brief §2's order (D-3)."""
        names = self.names()
        self.assertEqual(
            names,
            list(S.RUNGS),
            "the ladder's order is brief §2's and is never rearranged: got %r" % (names,),
        )

    def test_fam3_2_each_rung_declares_its_variants(self):
        """FAM-3.2 every rung declares the variants of ladder.md §2."""
        for name in S.RUNGS:
            declared = self.variant_names(self.rung(name))
            self.assertEqual(
                sorted(declared),
                sorted(S.VARIANTS[name]),
                "rung %r must declare %r; it declared %r" % (name, S.VARIANTS[name], declared),
            )

    def test_fam3_3_resolved_config_carries_the_schema(self):
        """FAM-3.3 training.rung resolves ladder.md §3's configuration schema."""
        for name in S.RUNGS:
            config = self.rung(name)
            text = S.flatten_text(config)
            for key in ("name", "axis", "carried", "primary", "variant", "pool"):
                self.assertIn(
                    key,
                    text,
                    "the resolved configuration of %r lacks the schema key %r: %r"
                    % (name, key, config),
                )

    def test_fam3_4_primary_variants_are_the_declared_lineage(self):
        """FAM-3.4 each rung's primary is the variant ladder.md §2 names."""
        for name in S.RUNGS:
            self.assertEqual(
                self.primary(self.rung(name)),
                S.PRIMARY[name],
                "rung %r inherits its primary variant into the next rung's lineage" % (name,),
            )

    def test_fam3_5_each_rung_carries_the_previous_primary(self):
        """FAM-3.5 rung n+1 is carried from rung n's primary variant (ladder §2)."""
        for previous, name in zip(S.RUNGS, S.RUNGS[1:]):
            self.assertEqual(
                self.carried_from(self.rung(name)),
                self.primary(self.rung(previous)),
                "rung %r must be carried from %r's primary" % (name, previous),
            )

    # -- adjacent pairs ----------------------------------------------------
    def test_fam3_6_r1_r2_differ_on_backend_only(self):
        """FAM-3.6 (R1, R2) differs on the backend — NumPy against PyTorch (D-7)."""
        result = self.ep("training", "fairness")(self.rung("R1"), self.rung("R2"))
        self.assert_axis(result, ("backend", "numpy", "torch"), "R1, R2")

    def test_fam3_7_r2_r3_differ_on_encoding_only(self):
        """FAM-3.7 (R2, R3) differs on the encoding — numbers against tokens (D-3)."""
        result = self.ep("training", "fairness")(self.rung("R2"), self.rung("R3"))
        self.assert_axis(result, ("encoding", "embedding", "token", "representation"), "R2, R3")

    def test_fam3_8_r3_r4_differ_on_width_against_depth(self):
        """FAM-3.8 (R3, R4) differs on the architecture — width against depth (D-3)."""
        result = self.ep("training", "fairness")(self.rung("R3"), self.rung("R4"))
        self.assert_axis(result, ("width", "depth", "architecture"), "R3, R4")

    def test_fam3_9_r4_r5_differ_on_connectivity(self):
        """FAM-3.9 (R4, R5) differs on connectivity — dense against sparse."""
        result = self.ep("training", "fairness")(self.rung("R4"), self.rung("R5"))
        self.assert_axis(result, ("dense", "sparse", "connectivity"), "R4, R5")

    def test_fam3_10_r5_r6_differ_on_the_residual_path(self):
        """FAM-3.10 (R5, R6) differs on the residual path (D-3)."""
        result = self.ep("training", "fairness")(self.rung("R5"), self.rung("R6"))
        self.assert_axis(result, ("residual",), "R5, R6")

    # -- intra-rung pairs --------------------------------------------------
    def test_fam3_11_r4_pair_differs_on_width_against_depth(self):
        """FAM-3.11 (R4 wide, R4 deep) differs on width against depth (ladder §2)."""
        result = self.ep("training", "fairness")(
            self.variant("R4", "wide"), self.variant("R4", "deep")
        )
        self.assert_axis(result, ("width", "depth"), "R4 wide, R4 deep")

    def test_fam3_12_r5_pair_differs_on_density(self):
        """FAM-3.12 (R5 dense, R5 sparse) differs on connectivity at one budget."""
        result = self.ep("training", "fairness")(
            self.variant("R5", "dense"), self.variant("R5", "sparse")
        )
        self.assert_axis(result, ("dense", "sparse", "connectivity", "densit"), "R5 pair")

    def test_fam3_13_r6_pair_differs_on_the_residual_path(self):
        """FAM-3.13 (R6 residual, R6 plain) differs on the residual path alone."""
        result = self.ep("training", "fairness")(
            self.variant("R6", "residual"), self.variant("R6", "plain")
        )
        self.assert_axis(result, ("residual",), "R6 pair")

    # -- what a comparison holds constant ---------------------------------
    def test_fam3_14_fairness_reports_what_it_holds_constant(self):
        """FAM-3.14 fairness reports the constants of ladder.md §4, pool included."""
        result = self.ep("training", "fairness")(self.rung("R1"), self.rung("R2"))
        text = S.flatten_text(result)
        for token in ("game", "action", "reward", "seed", "budget", "param", "device", "pool"):
            self.assertIn(
                token,
                text,
                "training.fairness must report the comparison it holds constant, including %r: %r"
                % (token, result),
            )

    # -- matched budgets ---------------------------------------------------
    def test_fam3_15_pair_mates_are_parameter_matched(self):
        """FAM-3.15 each pair's two learners match in param count within ±2% (ASM-10)."""
        pairs = [
            ("R4", "wide", "deep"),
            ("R5", "dense", "sparse"),
            ("R6", "residual", "plain"),
        ]
        for rung_name, left, right in pairs:
            left_count = self.ep("agents", "param_count")(
                self.variant_learner(self.variant(rung_name, left))
            )
            right_count = self.ep("agents", "param_count")(
                self.variant_learner(self.variant(rung_name, right))
            )
            self.assertGreater(left_count, 0, "%s/%s has no parameters" % (rung_name, left))
            self.assertGreater(right_count, 0, "%s/%s has no parameters" % (rung_name, right))
            tolerance = 0.02 * max(left_count, right_count)
            self.assertLessEqual(
                abs(left_count - right_count),
                tolerance,
                "%s's pair must be matched on capacity within ±2%%: %d against %d"
                % (rung_name, left_count, right_count),
            )

    def test_fam3_16_pair_mates_are_reported_as_budget_matched(self):
        """FAM-3.16 each intra-rung pair is matched on its budgets, per fairness (ASM-8)."""
        # What a pair holds constant is read from the declared reporter of it, not from a
        # variant entry's own keys: records.md §2 marks only `name`, `backend`, `encoding`
        # and `architecture` required, and battery.md §2 forbids depending on another key.
        # `training.fairness` is required to report the sample budget, the parameter budget
        # and the seed set a comparison pair holds constant (ladder.md §4).
        pairs = [
            ("R4", "wide", "deep"),
            ("R5", "dense", "sparse"),
            ("R6", "residual", "plain"),
        ]
        for rung_name, left, right in pairs:
            result = self.ep("training", "fairness")(
                self.variant(rung_name, left), self.variant(rung_name, right)
            )
            body = S.flatten_text(result)
            for token in ("budget", "param", "seed"):
                self.assertIn(
                    token,
                    body,
                    "%s's pair differs on its one axis and is held constant on its budgets, "
                    "so fairness reports %r among the constants (ladder.md §4, ASM-8): %r"
                    % (rung_name, token, result),
                )

    # -- the frozen pool (D-16, ASM-16) ------------------------------------
    def test_fam3_17_each_rung_declares_the_pool_it_trains_against(self):
        """FAM-3.17 a rung declares its frozen pool's id and bound, one per pair."""
        for name in S.RUNGS:
            config = self.rung(name)
            ids = S.pool_identity(config)
            self.assertTrue(
                ids,
                "rung %r declares no pool id it trains against; the run record must carry "
                "that id (ladder.md §3, ASM-16): %r" % (name, config),
            )
            bounds = self.declared_bound(config)
            self.assertTrue(
                bounds,
                "rung %r's pool declares no bound M: %r" % (name, config),
            )
            if name not in S.TWO_VARIANT_RUNGS:
                continue
            rung_ids = set(ids)
            rung_bounds = set(int(bound) for bound in bounds)
            for entry in S.variant_entries(config):
                arm_ids = set(S.pool_identity(entry))
                if arm_ids:
                    self.assertTrue(
                        arm_ids <= rung_ids,
                        "the arm %r of %r declares another pool than the rung: %r against %r"
                        % (S.variant_name(entry), name, sorted(arm_ids), sorted(rung_ids)),
                    )
                arm_bounds = set(int(bound) for bound in S.bound_numbers(entry))
                if arm_bounds:
                    self.assertTrue(
                        arm_bounds <= rung_bounds,
                        "the arm %r of %r declares another window than the rung: %r against %r"
                        % (S.variant_name(entry), name, sorted(arm_bounds), sorted(rung_bounds)),
                    )

    def test_fam3_18_a_two_variant_rungs_run_record_carries_one_pool(self):
        """FAM-3.18 each of R4, R5 and R6 trains both arms against one frozen pool (D-16)."""
        for rung_name in S.TWO_VARIANT_RUNGS:
            record = self.run_record(rung_name, (S.SEED_A,), S.BUDGET_TINY)
            ids = S.pool_identity(record)
            self.assertTrue(
                ids,
                "%s's run record must carry the frozen pool's id it trained against "
                "(e2e-surface.md §3.5, D-16): %r" % (rung_name, record),
            )
            self.assertEqual(
                len(set(ids)),
                1,
                "%s's two arms train against one frozen pool, so one run record carries one "
                "pool id: %r" % (rung_name, sorted(set(ids))),
            )
            members = S.flatten_text(S.find_values(record, "pool"))
            for baseline in S.BASELINES:
                self.assertIn(
                    baseline,
                    members,
                    "the pool %s's arms trained against is the three pinned baselines and "
                    "whatever lineage checkpoints exist, and the record states the membership "
                    "it used (protocol.md §5, league.md §2): %r" % (rung_name, record),
                )


if __name__ == "__main__":
    unittest.main()
