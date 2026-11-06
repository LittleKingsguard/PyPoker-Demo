"""JOIN-AGT-8 — the three fixed baselines at the join.

`docs/L1/protocol.md` §3 and `docs/L2/agents/surface.md` §11–§12: `always-call`
folds in no decision, `random` draws uniformly over the decision's legal indices from
its own seed, and `oracle` is consistent with the pot-odds inequality re-issued as
`engine.equity` at the baseline's own seed and the sample count `baselines()`
declares.  The policies are played through `engine.play_hand`, so the decisions, the
masks and the equity query are read from the engine's side of the edge and not from
anything this module keeps.
"""

import importlib.util
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
# The support module is loaded under a private name: this repository's integration
# batteries share the file name `_join_support.py`, so a plain import would hand one
# battery another's helpers when two test directories are collected in one process.
if "agents_join_support" in sys.modules:
    J = sys.modules["agents_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "agents_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["agents_join_support"] = J
    _spec.loader.exec_module(J)

#: The margin a decisive decision must clear the oracle's inequality by.  The L1
#: battery pairs its pot-odds probes with this same 1e-9 band (AGT-9.7,
#: `tests/agents/test_baselines.py`), so a decision counted as decisive is strictly
#: on one side of the boundary and never on it.
DECISIVE_BAND = 1e-9


class BaselinesAtTheJoin(J.JoinCase):
    """The three rules of D-6, checked through whole episodes."""

    def test_join_agt_8_1_always_call_folds_in_no_decision_of_any_episode(self):
        """JOIN-AGT-8.1 check/call whenever legal, never fold.

        `docs/L1/protocol.md` §3: `always-call` checks or calls whenever that is
        legal, never folds, and completes minimally when raising is the only option.
        The fold descriptor is `features.decode_action(0)`, so the check is on the
        decoded vocabulary index of every decision the engine recorded.  Two invented
        deals.
        """
        fold = J.decode_action(0)
        for deal in (J.DEAL_POLICY_A, J.DEAL_POLICY_B):
            with self.subTest(deal=deal):
                policy = J.build_baseline("always-call", J.BASELINE_SEED)
                record = J.play_hand(deal, policy, policy)
                decisions = J.episode_decisions(record)
                self.assertTrue(decisions)
                for decision in decisions:
                    chosen = J.decision_action(decision)
                    self.assert_descriptor_in(
                        J.decision_legal(decision), chosen, "always-call"
                    )
                    self.assertFalse(
                        J.same_descriptor(chosen, fold),
                        "the always-call baseline folded at deal %r: %r"
                        % (deal, chosen),
                    )

    def test_join_agt_8_2_random_stays_in_the_mask_and_is_seeded(self):
        """JOIN-AGT-8.2 random never leaves the mask; one seed repeats, two differ.

        `docs/L1/protocol.md` §3 and `docs/L2/agents/surface.md` §12: the draw is
        uniform over the decision's legal indices and keyed by the decision, so one
        seed answers alike twice and two seeds answer differently.  Played at two
        invented deals, each episode read from its record.
        """
        same_seed = J.build_baseline("random", J.BASELINE_SEED)
        repeat = J.build_baseline("random", J.BASELINE_SEED)
        other_seed = J.build_baseline("random", J.BASELINE_SEED_OTHER)

        def sequence(record, label):
            decisions = J.episode_decisions(record)
            self.assertTrue(decisions)
            indices = []
            for decision in decisions:
                legal = J.decision_legal(decision)
                chosen = J.decision_action(decision)
                self.assert_descriptor_in(legal, chosen, label)
                indices.append(J.descriptor_index(legal, chosen))
            return indices

        first = J.play_hand(J.DEAL_DECISION_A, same_seed, same_seed)
        second = J.play_hand(J.DEAL_DECISION_A, repeat, repeat)
        third = J.play_hand(J.DEAL_DECISION_A, other_seed, other_seed)
        one = sequence(first, "first")
        two = sequence(second, "repeat")
        three = sequence(third, "other seed")
        self.assertEqual(
            one,
            two,
            "one baseline seed must repeat its choices "
            "(docs/L1/protocol.md §3)",
        )
        self.assertNotEqual(
            one,
            three,
            "two baseline seeds must differ at one deal "
            "(docs/L2/agents/surface.md §12)",
        )
        # A second invented deal, so "never illegal" is shown on more than one hand.
        sequence(
            J.play_hand(J.DEAL_DECISION_B, other_seed, other_seed),
            "second deal",
        )

    def test_join_agt_8_3_the_oracle_is_consistent_with_the_pot_odds(self):
        """JOIN-AGT-8.3 the oracle's own decisions agree with the re-issued inequality.

        `docs/L2/agents/learner.md` §5 and `docs/L1/protocol.md` §3: the oracle calls
        when `engine.equity(readout, seed, baselines()'s count)` is at least
        `to_call / (pot + to_call)`, folds when it is not and folding is legal, folds
        nowhere folding is not legal and raises nowhere check/call is legal.
        `docs/L2/agents/surface.md` §11–§12 fix the sample count the query is re-issued
        at and make `(readout, legal_actions)` the policy's whole argument, and
        `docs/L2/engine/surface.md` §11 makes the readout a legal first argument, so
        the query is re-issued with the decision's own facts.  The inequality is a
        claim about the decisions the *oracle* made, so the walk and both non-vacuity
        floors cover the decisions of the seat the oracle held only:
        `engine.play_hand`'s record carries each decision's `seat`, and every invented
        deal is played twice, once with the oracle in seat 0 and once in seat 1,
        against the battery's aggressive caller (`e2e-surface.md` §2).  A decision is
        decisive when its equity clears the odds by more than the 1e-9 band the L1
        battery uses, and on the above side only where folding was legal, so the
        "never folds at or above the odds" clause is exercised where a fold was
        offered; each seat must carry at least two such decisions on each side (the
        two invented deals were chosen for it), because a case that proves nothing
        fails (`docs/L1/battery.md` §2).  Caught here is an oracle that folds at or
        above the odds, calls below them with a fold available, folds where folding is
        not legal or raises where check/call is — and an episode whose opponent's
        decisions are mistaken for the oracle's.
        """
        samples = J.oracle_samples()
        policy = J.build_baseline("oracle", J.BASELINE_SEED)
        for seat in (0, 1):
            above = 0
            below = 0
            for deal in (J.DEAL_ORACLE_A, J.DEAL_ORACLE_B):
                with self.subTest(seat=seat, deal=deal):
                    if seat == 0:
                        record = J.play_hand(deal, policy, J.raiser)
                    else:
                        record = J.play_hand(deal, J.raiser, policy)
                    mine = [
                        decision
                        for decision in J.episode_decisions(record)
                        if J.decision_seat(decision) == seat
                    ]
                    self.assertTrue(
                        mine,
                        "the oracle held seat %r at deal %r, so its decisions are the "
                        "ones this case judges (docs/L1/records.md §5): %r"
                        % (seat, deal, J.episode_decisions(record)),
                    )
                    for decision in mine:
                        facts = J.decision_readout(decision)
                        legal = J.decision_legal(decision)
                        mask = J.legal_indices(legal)
                        chosen = J.decision_action(decision)
                        self.assert_descriptor_in(legal, chosen, "oracle")
                        index = J.descriptor_index(legal, chosen)
                        self.assert_index_in(index, mask, "oracle")
                        pot = facts["pot"]
                        to_call = facts["to_call"]
                        odds = (
                            float(to_call) / float(pot + to_call)
                            if pot + to_call
                            else 0.0
                        )
                        estimate = float(J.equity(facts, J.BASELINE_SEED, samples))
                        self.assertTrue(
                            0.0 <= estimate <= 1.0,
                            "engine.equity is a probability in [0, 1] "
                            "(docs/L2/engine/surface.md §11): %r" % (estimate,),
                        )
                        if 1 in mask:
                            self.assertNotEqual(
                                index,
                                2,
                                "the oracle raises nowhere check/call is legal "
                                "(docs/L1/protocol.md §3, docs/L2/agents/learner.md "
                                "§5): decision %r" % (decision,),
                            )
                        if 0 not in mask:
                            self.assertNotEqual(
                                index,
                                0,
                                "the oracle folds nowhere folding is not legal "
                                "(docs/L1/protocol.md §3, docs/L2/features/surface.md "
                                "§8): decision %r" % (decision,),
                            )
                        if estimate >= odds:
                            self.assertNotEqual(
                                index,
                                0,
                                "at or above the pot odds the oracle never folds "
                                "(docs/L1/protocol.md §3): equity %r against odds %r"
                                % (estimate, odds),
                            )
                            if 0 in mask and estimate > odds + DECISIVE_BAND:
                                above += 1
                        elif 0 in mask:
                            self.assertEqual(
                                index,
                                0,
                                "below the pot odds the oracle folds where folding is "
                                "legal (docs/L1/protocol.md §3): equity %r against "
                                "odds %r" % (estimate, odds),
                            )
                            if estimate < odds - DECISIVE_BAND:
                                below += 1
                        else:
                            self.assertIn(
                                index,
                                (1, 2),
                                "below the pot odds the oracle folds only where "
                                "folding is legal, and this mask excludes it "
                                "(docs/L1/protocol.md §3, docs/L2/features/"
                                "surface.md §8)",
                            )
            self.assertGreaterEqual(
                above,
                2,
                "the oracle held seat %r, so at least two of its own decisions must "
                "be decisive above the inequality with a fold offered; a case that "
                "proves nothing fails (docs/L1/battery.md §2)" % (seat,),
            )
            self.assertGreaterEqual(
                below,
                2,
                "the oracle held seat %r, so at least two of its own decisions must "
                "be decisive below the inequality; a case that proves nothing fails "
                "(docs/L1/battery.md §2)" % (seat,),
            )


if __name__ == "__main__":
    unittest.main()
