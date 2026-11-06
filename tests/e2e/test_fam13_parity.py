"""FAM-13 — R1 against R2: one model, two backends, the D-7 speed comparison.

`docs/L1/battery.md` §3 FAM-13 and `docs/L1/ladder.md` §5 (D-7, D-8).  R1 and R2 declare
the same encoding, the same model shapes, the same update rule and the same sample order,
and differ only in ``backend``; so they must choose the same actions on the same seeded
hands, and the run record must carry the throughput both were measured at.  A parity row
that shows a large skill difference is a defect and not a finding, but the battery does
not assert one: it asserts that the work is the same and that the clock was measured.
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


class FAM13Parity(S.SurfaceCase):
    """The parity row and the clock that makes it a speed comparison."""

    # -- helpers -----------------------------------------------------------
    def variant(self, rung_name):
        """The single variant R1 and R2 each declare."""
        entries = S.variant_entries(self.ep("training", "rung")(rung_name))
        self.assertEqual(
            len(entries),
            1,
            "rung %r declares one variant, so it has no intra-rung pair" % (rung_name,),
        )
        return entries[0]

    def test_fam13_1_r1_and_r2_declare_the_same_encoding_and_shapes(self):
        """FAM-13.1 R1 and R2 declare one encoding and one architecture (D-7)."""
        one = self.variant("R1")
        two = self.variant("R2")
        self.assertEqual(
            S.canon(S.variant_setting(one, "encoding")),
            S.canon(S.variant_setting(two, "encoding")),
            "R1 and R2 are the same model, so they declare the same encoding (ladder.md §5)",
        )
        self.assertEqual(
            S.canon(S.variant_setting(one, "architecture")),
            S.canon(S.variant_setting(two, "architecture")),
            "R1 and R2 declare the same model shapes, or the speed difference is not the "
            "backend's (ladder.md §5, D-7)",
        )

    def test_fam13_2_r1_and_r2_differ_only_on_the_backend(self):
        """FAM-13.2 the backend is the single declared difference (D-7)."""
        one = S.variant_setting(self.variant("R1"), "backend")
        two = S.variant_setting(self.variant("R2"), "backend")
        self.assertNotEqual(
            S.canon(one),
            S.canon(two),
            "R1 is hand-rolled NumPy and R2 is PyTorch, so their declared backends differ "
            "(D-7)",
        )
        self.assertIn("numpy", S.flatten_text(one), "R1's backend is NumPy (D-7)")
        self.assertIn("torch", S.flatten_text(two), "R2's backend is PyTorch (D-7)")

    def test_fam13_3_r1_and_r2_hold_the_update_rule_and_its_budgets_fixed(self):
        """FAM-13.3 one learning rule, one hyper set, one sample budget, one capacity."""
        # What a pair holds constant is reported by the declared reporter of it rather than
        # read off a variant entry's own key: records.md §2 marks only `name`, `backend`,
        # `encoding` and `architecture` required, and battery.md §2 forbids depending on
        # any other key.  `training.fairness` is required to report the learning rule and
        # the budgets it holds constant (ladder.md §4, §5).
        result = self.ep("training", "fairness")(
            self.ep("training", "rung")("R1"), self.ep("training", "rung")("R2")
        )
        body = S.flatten_text(result)
        for alternatives in (("learning", "hyper", "update", "optimis", "optimiz",
                              "exploration"),
                             ("budget",),
                             ("param",)):
            self.assertTrue(
                any(token in body for token in alternatives),
                "R1 and R2 differ on the backend alone, so fairness reports the learning "
                "rule, the budgets and the capacity it holds constant — including one of "
                "%r; it reported %r" % (alternatives, result),
            )
        one = self.ep("agents", "param_count")(
            self.variant_learner(self.variant("R1"), seed=S.SEED_A)
        )
        two = self.ep("agents", "param_count")(
            self.variant_learner(self.variant("R2"), seed=S.SEED_A)
        )
        self.assertGreater(one, 0, "R1's model carries trainable parameters (ASM-10)")
        self.assertGreater(two, 0, "R2's model carries trainable parameters (ASM-10)")
        self.assertLessEqual(
            abs(one - two),
            0.02 * max(one, two),
            "the parity pair is matched on capacity within ±2%% — the same model in two "
            "backends, not two models (ASM-10, D-7): %r against %r" % (one, two),
        )

    def test_fam13_4_r1_and_r2_choose_the_same_actions_on_seeded_hands(self):
        """FAM-13.4 the two backends make the same decisions on the same hands."""
        one = self.variant_learner(self.variant("R1"), seed=S.SEED_A)
        two = self.variant_learner(self.variant("R2"), seed=S.SEED_A)
        encoder = self.encoder()
        walk = self.decision_walk(S.SEED_C, self.baseline("always-call", S.SEED_D), limit=5)
        self.assertTrue(walk, "the case drove no decision at all")
        for _hand, readout, _legal, _action, _index in walk:
            self.assertEqual(
                self.action_index(self.act(one, encoder, readout)),
                self.action_index(self.act(two, encoder, readout)),
                "R1 and R2 are the same model on the same work, so they choose the same "
                "action on the same readout (ladder.md §5, D-7)",
            )

    def test_fam13_5_both_run_records_carry_their_throughput(self):
        """FAM-13.5 the run record carries the cost both backends were measured at."""
        for rung_name in ("R1", "R2"):
            record = self.run_record(rung_name, (S.SEED_A,), S.BUDGET_TINY)
            timings = R.run_timings(record)
            self.assertTrue(
                timings,
                "the %r run record carries the cost record of harness.timings, which is the "
                "D-7 speed evidence (records.md §12, ladder.md §5): %r"
                % (rung_name, sorted(str(key) for key in record)
                   if S.is_mapping(record) else record),
            )
            facts = R.timing_facts(timings)
            self.assertTrue(
                facts["hands"],
                "the %r cost record carries the hands it measured: %r" % (rung_name, timings),
            )
            self.assertTrue(
                facts["per_hand"] or facts["throughput"],
                "the %r cost record carries seconds per hand or a throughput, read by what "
                "its keys name — seconds_per_hand / hands_per_second included — and never by a "
                "literal spelling this battery invented (records.md §12, ASM-15): %r"
                % (rung_name, timings),
            )
            # Neither case asserts that a wall clock was beaten: R1 against R2 is a
            # comparison of measured cost, not a race (battery.md §2, ASM-15).

    def test_fam13_6_the_parity_pair_s_clock_comes_from_the_driver(self):
        """FAM-13.6 harness.timings measures the per-hand cost the parity row cites."""
        case = {
            "id": "fam13-6-parity-clock",
            "steps": [lambda: self.play(S.SEED_G)],
            # The expectation kind is one the fixture lists: it is the harness's vocabulary,
            # not this battery's (e2e-surface §3.6, records.md §14).
            "expect": [self.an_expectation_kind()],
        }
        result = self.ep("harness", "drive")(case)
        self.assertIsNotNone(
            S.verdict(result),
            "the driver judges the parity case it played and records the verdict: %r"
            % (result,),
        )
        timings = self.ep("harness", "timings")()
        facts = R.timing_facts(timings)
        self.assertTrue(
            facts["hands"],
            "harness.timings is the cost record of the work the driver measured, so it "
            "carries the hands counted (e2e-surface §3.6, ladder.md §5): %r" % (timings,),
        )
        self.assertTrue(
            facts["per_hand"] or facts["throughput"],
            "the parity row's speed evidence is a per-hand cost or a throughput, measured "
            "and not asserted (ASM-15): %r" % (timings,),
        )
        self.assertTrue(
            any(number > 0 for number in facts["per_hand"] + facts["throughput"]),
            "a measured per-hand cost is a positive number: %r" % (timings,),
        )


if __name__ == "__main__":
    unittest.main()
