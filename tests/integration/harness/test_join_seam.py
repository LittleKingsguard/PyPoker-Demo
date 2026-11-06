"""The seam join -- HRNJ-3.

`docs/L2/harness/surface.md` §5: a seam is a policy in the sense of `e2e-surface.md` §2
and nothing else -- a callable taking `(readout, legal_actions)` that returns one
descriptor **from `legal_actions`** -- so the engine must be able to play it, and the
episode it plays is the engine's: zero-sum, every choice inside the engine's legal set.
Both documented behaviours record; the label decides only the choice rule, `recording`
(and every label that is not `synthetic`) taking the first descriptor `legal_actions`
returned and `synthetic` walking the legal descriptors cyclically (H-2, H-3).  An empty
legal set is refused rather than folded, because a policy that returns an illegal action
is a contract violation and not a fold (`e2e-surface.md` §2, D-2, `docs/L3/harness/
support.md` §3, `docs/L1/battery.md` §5).

The join no single module can check is this one: `engine.play_hand` calls policies and
never imports one, and `harness.seam` re-implements no part of the game, so only a battery
that plays the two together sees that a synthetic double of a *policy* is enough to drive
a real episode to its end (`module-map.md` §3, brief §5, D-13, FAM-14.7, FAM-16.35).
"""

import importlib.util
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
if "harness_join_support" in sys.modules:
    J = sys.modules["harness_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "harness_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["harness_join_support"] = J
    _spec.loader.exec_module(J)


class SeamJoin(J.JoinCase):
    """HRNJ-3 -- a seam is a policy of `e2e-surface.md` §2 inside a real episode."""

    def decision_actions(self, episode, seat):
        """The actions the engine applied at one seat, in played order."""
        return [decision["action"] for decision in episode["decisions"]
                if J.seat_index(decision["seat"]) == seat]

    def learner_policy(self):
        """A real learner policy that does not fold at the battery's first decision.

        A `recording` seam takes the first legal descriptor, which is `fold` wherever
        folding is legal (`features/surface.md` §2), so an episode in which the seam
        answers a decision needs an opponent who keeps the hand alive.  The pair of seeds
        is the battery's own and is *searched* rather than assumed: a policy whose every
        seed folds first would leave the join unobservable, and that would be the finding
        (`docs/L1/battery.md` §4, D-15).
        """
        encoder = J.shared_encoder()
        record, legal = J.readout_and_legal(J.DEAL_SEED)
        for learner_seed in (1, 5, 10, 13):
            learner = J.build_learner(J.learner_spec(seed=learner_seed))
            for policy_seed in range(1, 12):
                policy = J.as_policy(learner, encoder, policy_seed)
                if not J.same_descriptor(policy(record, legal), "fold"):
                    return policy
        self.fail(
            "no `agents.as_policy` over an invented learner spec keeps the battery's hand "
            "alive at its first decision, so a seam beside a real learner policy could "
            "never answer one; the join is unobservable as the surface is built "
            "(docs/L2/agents/surface.md §10, docs/L2/harness/surface.md §5)"
        )

    def test_hrnj_3_1_a_recording_seam_plays_a_real_engine_episode(self):
        """HRNJ-3.1 the engine plays a seam, and the episode stays the engine's.

        `docs/L2/harness/surface.md` §5: the seam "knows the readout only as the argument
        of `e2e-surface.md` §2 and reads no field of it to choose", and "the episode it
        plays is the engine's: `engine.play_hand` stays zero-sum because the engine
        decided the hand and the seam only chose inside the legal set".  So the battery
        puts a seam of an invented label at seat 1 beside a real `always-call` baseline,
        and reads the episode the engine returns: two balanced payoffs, every decision's
        action inside its own legal set, and the seam's log holding exactly the decisions
        the engine called it at, with the readouts the engine handed it (FAM-14.7,
        ASM-12, D-2).
        """
        policy = J.seam(J.SEAM_LABEL)
        opponent = J.build_baseline("always-call", J.BASELINE_SEED_OTHER)
        self.assertTrue(
            callable(policy),
            "harness.seam returns a policy in the sense of e2e-surface.md §2, whatever "
            "the label -- a callable taking a readout and a legal set "
            "(docs/L2/harness/surface.md §5): %r" % (policy,),
        )
        episode = J.play_hand(J.DEAL_SEED, opponent, policy)
        self.assert_required_keys(
            episode, J.EPISODE_KEYS, "the episode `engine.play_hand` played with a seam",
            "docs/L1/records.md §5",
        )
        for position, decision in enumerate(episode["decisions"]):
            self.assert_required_keys(
                decision, J.DECISION_KEYS, "decision %d of the seam's episode" % (position,),
                "docs/L1/records.md §5",
            )
            self.assert_descriptor_in(
                decision["legal"], decision["action"],
                "the engine only applies a descriptor it declared legal, at decision %d"
                % (position,),
                "docs/L2/engine/surface.md §7, D-2",
            )
        self.assertEqual(
            len(episode["payoffs"]), 2,
            "the engine's episode reports one net chip delta per seat "
            "(docs/L1/records.md §5): %r" % (episode["payoffs"],),
        )
        self.assertEqual(
            sum(float(delta) for delta in episode["payoffs"].values()), 0.0,
            "the hand is still zero-sum, because the engine decided it and the seam only "
            "chose inside the legal set (docs/L2/harness/surface.md §5, ASM-12, FAM-14.7): "
            "%r" % (episode["payoffs"],),
        )
        calls = J.logged_calls(policy)
        seam_decisions = [decision for decision in episode["decisions"]
                          if J.seat_index(decision["seat"]) == 1]
        seam_actions = [decision["action"] for decision in seam_decisions]
        self.assertTrue(
            calls,
            "a `recording` seam records every call it answered, and the engine called it "
            "at least once at seat 1 (docs/L2/harness/surface.md §5, H-3): %r"
            % (episode["decisions"],),
        )
        self.assertEqual(
            len(calls), len(seam_actions),
            "the seam answered exactly the decisions the engine called it at: one log "
            "entry per call, in call order (docs/L2/harness/surface.md §5, H-3): %r"
            % (calls,),
        )
        for position, (handed, legal, chosen) in enumerate(calls):
            self.assertIsNotNone(
                legal,
                "a seam's log entry holds the `legal_actions` it was handed "
                "(docs/L2/harness/surface.md §5): %r" % (calls,),
            )
            self.assert_descriptor_in(
                legal, chosen,
                "a seam returns one descriptor from `legal_actions`, never an illegal "
                "action and never an invented one (e2e-surface.md §2, D-2): %r"
                % (chosen,),
                "docs/L2/harness/surface.md §5, e2e-surface.md §2, D-2",
            )
            self.assertTrue(
                J.same_descriptor(chosen, seam_actions[position]),
                "the action the engine applied at seat 1 is the descriptor the seam "
                "returned, in call order: the double decided nothing the engine did not "
                "record (docs/L1/records.md §5, docs/L2/harness/surface.md §5): %r "
                "against %r" % (chosen, seam_actions[position]),
            )
            self.assertEqual(
                J.canon(handed),
                J.canon(seam_decisions[position]["readout"]),
                "the readout the seam was handed is the readout the engine recorded for "
                "that decision, so the double read the engine's information set and no "
                "other (docs/L1/records.md §5, docs/L2/harness/surface.md §5): %r"
                % (sorted(seam_decisions[position]["readout"]),),
            )

    def test_hrnj_3_2_a_seam_plays_beside_a_real_learner_policy(self):
        """HRNJ-3.2 a seam and `agents.as_policy` are the same protocol at one table.

        `agents/surface.md` §10 makes `as_policy(learner, encoder, seed)` a policy in the
        sense of `e2e-surface.md` §2, and `surface.md` §5 makes a seam the same.  The
        battery plays the two against each other, so the join is the protocol itself: the
        engine drives both, the episode is zero-sum, and the decisions the seam answered
        are the engine's decisions, with the choices inside the engine's legal sets
        (`surface.md` §5, `docs/L2/agents/surface.md` §10, D-2).
        """
        policy = J.seam(J.SEAM_LABEL_CYCLE)
        learner_policy = self.learner_policy()
        self.assertTrue(
            callable(learner_policy),
            "`agents.as_policy` returns a policy in the sense of e2e-surface.md §2, which "
            "is the protocol the seam answers too (docs/L2/agents/surface.md §10): %r"
            % (learner_policy,),
        )
        episode = J.play_hand(J.DEAL_SEED, learner_policy, policy)
        self.assert_required_keys(
            episode, J.EPISODE_KEYS,
            "the episode a learner policy and a seam played",
            "docs/L1/records.md §5",
        )
        self.assertEqual(
            sum(float(delta) for delta in episode["payoffs"].values()), 0.0,
            "two policies of the one protocol play one engine episode, and the engine's "
            "payoffs balance whatever they chose (docs/L2/harness/surface.md §5, ASM-12): "
            "%r" % (episode["payoffs"],),
        )
        calls = J.logged_calls(policy)
        self.assertTrue(
            calls,
            "the seam answered at least one decision of the hand the learner policy kept "
            "alive, so the two protocols really met (docs/L2/harness/surface.md §5, "
            "docs/L2/agents/surface.md §10): %r" % (episode["decisions"],),
        )
        seam_actions = self.decision_actions(episode, 1)
        self.assertEqual(
            len(calls), len(seam_actions),
            "the seam answered exactly the decisions at its own seat "
            "(docs/L2/harness/surface.md §5, H-3): %r" % (calls,),
        )
        for position, (_handed, legal, chosen) in enumerate(calls):
            self.assert_descriptor_in(
                legal, chosen,
                "a seam chooses inside the legal set the engine handed it, beside a "
                "learner's policy as beside a baseline: %r" % (chosen,),
                "docs/L2/harness/surface.md §5, e2e-surface.md §2",
            )
            self.assertTrue(
                J.same_descriptor(chosen, seam_actions[position]),
                "the engine applied what the seam returned beside a learner's policy "
                "(docs/L1/records.md §5, D-2): %r against %r"
                % (chosen, seam_actions[position]),
            )
        self.assertTrue(
            self.decision_actions(episode, 0),
            "the learner policy answered a decision of its own, so the episode really is "
            "the two protocols' (docs/L2/agents/surface.md §10): %r"
            % (episode["decisions"],),
        )

    def test_hrnj_3_3_two_seams_of_one_label_choose_the_same_descriptors(self):
        """HRNJ-3.3 one label and one decision sequence give one choice sequence.

        `docs/L2/harness/surface.md` §5: "two seams of one label, driven over the same
        sequence of `(readout, legal_actions)` pairs, return the same descriptors, because
        each `seam(label)` call returns a fresh instance whose log starts empty and whose
        schedule starts at its first call".  The pairs are one real hand's decisions, read
        from the engine (`e2e-surface.md` §2, FAM-14.5, FAM-14.6, FAM-16.35).
        """
        walk = J.shared_walk()
        self.assertTrue(
            walk,
            "the battery's hand offers at least one decision to drive a seam over "
            "(docs/L2/engine/surface.md §6): %r" % (len(walk),),
        )
        first = J.seam(J.SEAM_LABEL)
        second = J.seam(J.SEAM_LABEL)
        self.assertEqual(
            len(J.logged_calls(first)), 0,
            "each `seam(label)` call returns a fresh instance whose log starts empty "
            "(docs/L2/harness/surface.md §5, H-2): %r" % (first,),
        )
        self.assertEqual(
            len(J.logged_calls(second)), 0,
            "a second seam of the same label starts empty too, so two instances cannot "
            "share a log (docs/L2/harness/surface.md §5): %r" % (second,),
        )
        chosen_first = [first(record, legal) for record, legal in walk]
        chosen_second = [second(record, legal) for record, legal in walk]
        self.assertEqual(
            len(chosen_first), len(walk),
            "a seam answers every call it is handed, one descriptor each "
            "(docs/L2/harness/surface.md §5): %r" % (chosen_first,),
        )
        for position, (left, right) in enumerate(zip(chosen_first, chosen_second)):
            self.assertTrue(
                J.same_descriptor(left, right),
                "two seams of one label driven over the same decision sequence return the "
                "same descriptors, because a seam's choice is a function of its label and "
                "of the calls it answered and of nothing else -- no clock, generator, "
                "global stream or ambient fixture (docs/L2/harness/surface.md §5, ASM-2, "
                "D-6, FAM-14.5): decision %d gave %r and %r"
                % (position, left, right),
            )
        self.assertEqual(
            len(J.logged_calls(first)), len(walk),
            "both seams recorded every call they answered, in call order "
            "(docs/L2/harness/surface.md §5, H-3): %r"
            % (len(J.logged_calls(first)),),
        )
        third = J.seam(J.SEAM_LABEL)
        self.assertEqual(
            len(J.logged_calls(third)), 0,
            "a third instance's schedule starts at its first call, so a log is never "
            "inherited from another instance (docs/L2/harness/surface.md §5): %r"
            % (third,),
        )
        replayed = [J.same_descriptor(third(record, legal), left)
                    for (record, legal), left in zip(walk, chosen_first)]
        self.assertIn(
            True, replayed,
            "a fresh seam of the same label agrees with the earlier one at least once, "
            "because the schedule and the label are all it reads "
            "(docs/L2/harness/surface.md §5, D-6): %r" % (replayed,),
        )

    def test_hrnj_3_4_a_synthetic_seam_spreads_its_choices_over_the_vocabulary(self):
        """HRNJ-3.4 `synthetic` walks the legal descriptors cyclically.

        `docs/L2/harness/surface.md` §5: "call *n* of that instance returns the descriptor
        at position *n* modulo the number of legal descriptors, so a case gets a policy
        that spreads its choices over the vocabulary and needs no learner" (H-2).  The
        battery drives the schedule over a real hand's decisions and reads both halves of
        the contract: the position is the cycle's, and the choices are not one descriptor
        repeated (FAM-14.6).
        """
        walk = J.shared_walk()
        self.assertTrue(
            any(len(legal) > 1 for _record, legal in walk),
            "the battery's hand must offer a decision with more than one legal descriptor, "
            "or the schedule has nothing to spread over (docs/L2/engine/surface.md §6): %r"
            % ([list(legal) for _record, legal in walk],),
        )
        policy = J.seam(J.SEAM_LABEL_CYCLE)
        chosen = [policy(record, legal) for record, legal in walk]
        for position, ((_record, legal), choice) in enumerate(zip(walk, chosen)):
            legal_list = list(legal)
            self.assert_descriptor_in(
                legal_list, choice,
                "even the spreading seam returns one descriptor from `legal_actions`: "
                "%r" % (choice,),
                "docs/L2/harness/surface.md §5, e2e-surface.md §2, D-2",
            )
            self.assertTrue(
                J.same_descriptor(choice, legal_list[position % len(legal_list)]),
                "call %d of a `synthetic` seam returns the descriptor at position %d "
                "modulo the %d legal descriptors -- the cycle is the choice rule, and "
                "0-based so its first call agrees with `recording` "
                "(docs/L2/harness/surface.md §5, H-2, FAM-14.6): %r against %r"
                % (position, position, len(legal_list), choice, legal_list[position % len(legal_list)]),
            )
        self.assertGreater(
            len({J.token(choice) for choice in chosen}), 1,
            "a `synthetic` seam spreads its choices over the vocabulary where the hand "
            "offers more than one descriptor, so a case gets a policy that is not one "
            "descriptor repeated (docs/L2/harness/surface.md §5, FAM-14.6): %r" % (chosen,),
        )
        self.assertEqual(
            len(J.logged_calls(policy)), len(walk),
            "a `synthetic` seam records the readouts it was called with, as every seam "
            "does -- H-3's rejected alternative is a spreading seam that logged nothing "
            "(docs/L2/harness/surface.md §5, H-3): %r" % (len(J.logged_calls(policy)),),
        )

    def test_hrnj_3_5_a_recording_seam_takes_the_first_legal_descriptor(self):
        """HRNJ-3.5 `recording` takes `legal_actions`' first descriptor, every call.

        `docs/L2/harness/surface.md` §5: the choice rule of `recording` -- and of every
        label that is not `synthetic` -- is "the **first** descriptor `legal_actions`
        returned, every call" (H-2).  The engine orders a decision's descriptors as the
        vocabulary is, `fold` first wherever folding is legal (`features/surface.md` §2,
        `engine/surface.md` §2), so the two observable halves of the rule are: the choice
        is always the first descriptor, and it is therefore never a fold at a decision
        where folding is not an option at all (D-2).
        """
        walk = J.shared_walk()
        policy = J.seam(J.SEAM_LABEL_RECORDING)
        chosen = [policy(record, legal) for record, legal in walk]
        for position, ((_record, legal), choice) in enumerate(zip(walk, chosen)):
            self.assertTrue(
                J.same_descriptor(choice, list(legal)[0]),
                "a `recording` seam returns the first descriptor `legal_actions` "
                "returned, every call, and reads no field of the readout to choose "
                "(docs/L2/harness/surface.md §5, H-2, D-13): decision %d chose %r from %r"
                % (position, choice, list(legal)),
            )
        without_fold = [position for position, (_record, legal) in enumerate(walk)
                        if not any(J.same_descriptor("fold", candidate)
                                   for candidate in legal)]
        self.assertTrue(
            without_fold,
            "the battery's hand offers a decision where folding is not legal, which is "
            "where a seam's rule is observable at all -- `fold` is absent where `to_call` "
            "is 0 (docs/L2/features/surface.md §2, docs/L2/engine/surface.md §2): %r"
            % ([list(legal) for _record, legal in walk],),
        )
        for position in without_fold:
            self.assertFalse(
                J.same_descriptor(chosen[position], "fold"),
                "a policy never returns an action outside `legal_actions`, so a seam "
                "cannot fold at decision %d, where folding is not legal -- a fold there "
                "would be the contract violation of D-2 and not a fold "
                "(docs/L2/harness/surface.md §5, e2e-surface.md §2): %r"
                % (position, chosen[position]),
            )
        with_fold = [position for position, (_record, legal) in enumerate(walk)
                     if any(J.same_descriptor("fold", candidate) for candidate in legal)]
        self.assertTrue(
            with_fold,
            "the battery's hand offers a decision where folding is legal, so the first "
            "legal descriptor is the fold the rule names "
            "(docs/L2/engine/surface.md §2): %r" % ([list(legal) for _record, legal in walk],),
        )
        for position in with_fold:
            self.assertTrue(
                J.same_descriptor(chosen[position], list(walk[position][1])[0]),
                "where folding is legal the first legal descriptor is the engine's fold, "
                "and the rule is the first descriptor and not the first non-fold one: a "
                "seam is a double of a *policy* and not of a baseline's rule "
                "(docs/L2/harness/surface.md §5, H-2; `always-call` never folding is "
                "`agents`' rule and is asserted through the factory, protocol.md §3): %r"
                % (chosen[position],),
            )

    def test_hrnj_3_6_an_empty_legal_set_is_refused_rather_than_folded(self):
        """HRNJ-3.6 a seam refuses an empty legal set instead of returning a fold.

        `docs/L2/harness/surface.md` §5: "an **empty** legal set, naming that a policy must
        return a member of `legal_actions` -- a seam never folds instead and never invents
        a descriptor, because a policy that returns an illegal action is a contract
        violation and not a fold" (`e2e-surface.md` §2, D-2).  The rule holds for every
        label, because the empty set leaves both documented behaviours nothing to choose
        from (H-2).
        """
        record, _legal = J.readout_and_legal(J.DEAL_SEED)
        for label in (J.SEAM_LABEL_RECORDING, J.SEAM_LABEL_CYCLE, J.SEAM_LABEL):
            policy = J.seam(label)
            _klass, message = self.assert_refusal(
                lambda policy=policy: policy(record, []),
                ("legal",),
                "a seam handed an empty legal set (%r) must refuse it, naming the policy "
                "protocol" % (label,),
                "docs/L2/harness/surface.md §5, e2e-surface.md §2, D-2",
            )
            self.assertIn(
                "policy", str(message).lower(),
                "the refusal names the contract it violates -- that a policy returns a "
                "member of `legal_actions` (docs/L2/harness/surface.md §5, D-2): %r"
                % (message,),
            )


if __name__ == "__main__":
    unittest.main()
