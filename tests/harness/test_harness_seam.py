"""HRN-6 — `seam`: one policy double that answers inside the legal set.

Drives `docs/L3/harness/support.md` §3 and `docs/L2/harness/surface.md` §5: a callable
returning **a member of the list it was handed** (by identity, so `engine.apply_action`
accepts it), both documented behaviours recorded in a `calls` log in call order, the
`recording`/`synthetic` schedules, a fresh instance per `seam()` call, an empty legal set
refused rather than folded, and no generator of its own
(`guardrails.md` G21-G25, FAM-14.5, FAM-14.6, FAM-14.7, FAM-16.35).
"""

import unittest

from _harness_support import (
    BASELINE_CALL,
    SEAM_EMPTY,
    SEAM_INVENTED,
    SEAM_RECORDING,
    SEAM_SYNTHETIC,
    SEED_HAND,
    SEED_OTHER,
    SEED_POLICY,
    HarnessCase,
    agents,
    as_int,
    as_mapping,
    as_sequence,
    engine,
    features,
    invented_descriptors,
)


class SeamTest(HarnessCase):
    def seam(self, label):
        policy = self.ep("seam")(label)
        self.assertTrue(
            callable(policy),
            "harness.seam(%r) returns a policy in the sense of e2e-surface.md §2 "
            "(support §3, FAM-14.5): %r" % (label, policy),
        )
        log = getattr(policy, "calls", None)
        self.assertIsNotNone(
            log,
            "the returned policy carries a `calls` sequence, because it records every "
            "call it answered (surface §5, support §3, L2's H-3): %r" % (policy,),
        )
        self.assertEqual(
            len(as_sequence(log, "the policy's call log")),
            0,
            "a fresh seam's log starts empty (support §3, FAM-16.35): %r" % (log,),
        )
        return policy

    def legal(self):
        return list(engine().legal_actions(engine().new_hand(SEED_HAND)))

    # -- membership, by identity --------------------------------------------
    def test_hrn_6_1_the_seam_returns_a_member_of_the_list_it_was_handed(self):
        """HRN-6.1 the seam returns `legal[position]` itself — the very object in the list it was handed, for every label — and not a copy, a name or a rebuilt descriptor (support §3, e2e-surface.md §2, G21, FAM-14.5, FAM-16.35)."""
        for label in (SEAM_RECORDING, SEAM_SYNTHETIC, SEAM_INVENTED, SEAM_EMPTY):
            with self.subTest(label=label):
                policy = self.seam(label)
                handed = invented_descriptors(3)
                for index in range(3):
                    chosen = policy({"street": "invented"}, handed)
                    position = index % len(handed) if label == SEAM_SYNTHETIC else 0
                    self.assertIs(
                        chosen,
                        handed[position],
                        "a %r seam returns legal[position] itself — the very object in "
                        "the list it was handed — and not a copy, a name or a rebuilt "
                        "descriptor (support §3 step 5, G21): %r" % (label, chosen),
                    )
                    self.assertEqual(
                        len(policy.calls),
                        index + 1,
                        "one call answered is one log entry, so the battery's control "
                        "holds for %r (support §3 step 4): %r"
                        % (label, policy.calls),
                    )

    def test_hrn_6_2_a_seam_plays_a_real_episode_inside_the_legal_set(self):
        """HRN-6.2 a seam is playable beside a declared baseline: `engine.play_hand` drives the hand, every descriptor it answered with was one of the legal descriptors it was handed and the log holds those legal sets, and the descriptor it returned is one `engine.apply_action` accepts — returning the advanced hand as a new handle and leaving its argument at its own state — while `features.legal_indices` places it in `{0, 1, 2}` (support §3, surface §5, G21, FAM-14.7). The episode the engine plays is the engine's, so the episode-level zero-sum fact belongs to `tests/integration/harness/` (HRNJ-3) and `tests/e2e/`, and this case does not re-assert it."""
        policy = self.seam(SEAM_SYNTHETIC)
        episode = as_mapping(
            engine().play_hand(
                SEED_OTHER, policy, agents().build_baseline(BASELINE_CALL, SEED_POLICY)
            ),
            "the episode a seam played",
        )
        decisions = as_sequence(episode["decisions"], "the episode's decisions")
        self.assertTrue(
            len(decisions),
            "the seam answered the decisions the engine asked it (engine/surface.md "
            "§10, support §3): %r" % (episode,),
        )
        self.assertTrue(
            len(policy.calls),
            "the seam recorded the calls it answered during the episode (surface §5, "
            "support §3, L2's H-3): %r" % (policy.calls,),
        )
        for entry in policy.calls:
            entry = as_mapping(entry, "one call-log entry from the episode")
            self.assertIn(
                entry["chosen"],
                list(as_sequence(entry["legal"], "the logged legal set")),
                "every descriptor it answered with during the episode was legal "
                "(support §3 step 4, e2e-surface.md §2, G21): %r" % (entry,),
            )
        hand = engine().new_hand(SEED_HAND)
        legal = list(engine().legal_actions(hand))
        handed_readout = engine().readout(hand)
        chosen = policy(handed_readout, legal)
        self.assertIn(
            chosen,
            legal,
            "the seam never invents a descriptor: its answer is one of the legal ones "
            "(support §3 step 5, e2e-surface.md §2, G21): %r" % (chosen,),
        )
        indices = features().legal_indices(legal)
        self.assertIn(
            legal.index(chosen),
            [as_int(index, "a legal index") for index in indices],
            "features.legal_indices gives the descriptor it returned an index in the "
            "three-index vocabulary (support §3 step 5, features/surface.md §8, G21): %r"
            % (indices,),
        )
        self.assertTrue(
            set(as_int(index, "a legal index") for index in indices) <= {0, 1, 2},
            "the vocabulary is the three indices fold/check-call/raise (features/"
            "surface.md §7, e2e-surface.md §2, G21): %r" % (indices,),
        )
        advanced = engine().apply_action(hand, chosen)
        self.assertIsNot(
            advanced,
            hand,
            "engine.apply_action accepts what the seam returned: it advances the hand, "
            "so it hands back the advanced hand as a new handle and never the handle it "
            "was given (engine/surface.md §1 rule 6, §7, G21): %r" % (advanced,),
        )
        self.assertEqual(
            engine().readout(hand),
            handed_readout,
            "and the handle it was given is left at its own state, because a caller "
            "keeps an earlier handle and queries it after the hand has moved on "
            "(engine/surface.md §1 rule 6, §5, §7, G21): %r" % (engine().readout(hand),),
        )

    # -- both behaviours record ---------------------------------------------
    def test_hrn_6_3_both_behaviours_record_every_call_they_answered(self):
        """HRN-6.3 `recording` and `synthetic` both append one log entry per call, in call order, holding the `readout`, the `legal` set it was handed and the `chosen` descriptor (support §3 steps 1 and 4, surface §5, G22, L2's H-3)."""
        legal = self.legal()
        for label in (SEAM_RECORDING, SEAM_SYNTHETIC, SEAM_INVENTED):
            with self.subTest(label=label):
                policy = self.seam(label)
                observations = [{"call": 0}, {"call": 1}, {"call": 2}]
                for observation in observations:
                    policy(observation, legal)
                log = as_sequence(policy.calls, "the seam's call log")
                self.assertEqual(
                    len(log),
                    len(observations),
                    "one entry per call answered, in call order (support §3 step 4, "
                    "G22): %r" % (log,),
                )
                for position, observation in enumerate(observations):
                    entry = as_mapping(log[position], "one call-log entry")
                    self.assertEqual(
                        list(entry),
                        ["readout", "legal", "chosen"],
                        "an entry holds readout, legal and chosen, in that key order "
                        "(support §3 step 4, H-3): %r" % (list(entry),),
                    )
                    self.assertEqual(
                        entry["readout"],
                        observation,
                        "the log holds what the seam was handed on that call "
                        "(support §3 step 4, H-3): %r" % (entry["readout"],),
                    )
                    self.assertEqual(
                        list(as_sequence(entry["legal"], "the logged legal set")),
                        legal,
                        "and the legal set it was handed on that call (support §3 "
                        "step 4): %r" % (entry["legal"],),
                    )
                    self.assertIn(
                        entry["chosen"],
                        legal,
                        "and the descriptor it returned, which is one of the legal "
                        "ones (support §3 step 4, D-2): %r" % (entry["chosen"],),
                    )

    def test_hrn_6_4_synthetic_walks_the_legal_set_and_recording_takes_the_first(self):
        """HRN-6.4 `recording` — and every label that is not `synthetic`, including an invented one and the empty string — takes `legal[0]` every call, while `synthetic` takes `legal[n]` modulo the legal count, so its second call differs (support §3 step 3, surface §5, G22, FAM-14.6)."""
        legal = self.legal()
        for label in (SEAM_RECORDING, SEAM_INVENTED, SEAM_EMPTY):
            with self.subTest(label=label):
                policy = self.seam(label)
                for _call in range(3):
                    self.assertEqual(
                        policy({"street": "preflop"}, legal),
                        legal[0],
                        "the %r label takes the first descriptor legal_actions "
                        "returned, every call (support §3 step 3, surface §5, G22): %r"
                        % (label, legal),
                    )
        synthetic = self.seam(SEAM_SYNTHETIC)
        calls = len(legal) + 2
        choices = [synthetic({"street": "preflop"}, legal) for _call in range(calls)]
        expected = [legal[position % len(legal)] for position in range(calls)]
        self.assertEqual(
            choices,
            expected,
            "call n returns the descriptor at position n modulo the number of legal "
            "descriptors, 0-based, so the schedule spreads a case's choices over the "
            "vocabulary and wraps (support §3 step 3, FAM-14.6, README §7 decision 4): "
            "%r vs %r" % (choices, expected),
        )
        self.assertEqual(
            choices[0],
            legal[0],
            "synthetic's first call agrees with recording's (README §7 decision 4, "
            "support §3, G22): %r" % (choices,),
        )
        self.assertNotEqual(
            choices[1],
            legal[0],
            "from the second call on the synthetic schedule differs from recording's, "
            "because the position advances (support §3, G22): %r" % (choices,),
        )

    # -- two instances, one label -------------------------------------------
    def test_hrn_6_5_two_seams_of_one_label_answer_alike(self):
        """HRN-6.5 two closures from `seam(label)` driven over the same sequence of `(readout, legal_actions)` pairs return the same descriptors and hold equal logs, because a seam's choice is a function of its label and the calls it answered (support §3, surface §5, G23, FAM-14.5, FAM-14.6, FAM-16.35)."""
        legal = self.legal()
        pairs = [({"call": position}, legal) for position in range(3)]
        for label in (SEAM_RECORDING, SEAM_SYNTHETIC):
            with self.subTest(label=label):
                first = self.seam(label)
                second = self.seam(label)
                answers_first = [first(observation, actions) for observation, actions in pairs]
                answers_second = [second(observation, actions) for observation, actions in pairs]
                self.assertEqual(
                    answers_first,
                    answers_second,
                    "two seams of one label answer the same descriptors (support §3, "
                    "G23, FAM-14.5): %r vs %r" % (answers_first, answers_second),
                )
                self.assertEqual(
                    [dict(entry) for entry in first.calls],
                    [dict(entry) for entry in second.calls],
                    "and hold equal logs (support §3, G23, FAM-16.35): %r vs %r"
                    % (first.calls, second.calls),
                )

    def test_hrn_6_6_two_seam_calls_are_two_instances(self):
        """HRN-6.6 each `seam(label)` call returns a fresh instance whose log starts empty and whose schedule starts at its first call: the second seam's log does not contain the first's calls (support §3, surface §5, G23, FAM-16.35)."""
        legal = self.legal()
        first = self.seam(SEAM_SYNTHETIC)
        first({"call": "first"}, legal)
        first({"call": "first"}, legal)
        self.assertEqual(
            len(first.calls),
            2,
            "the control: the first instance logged the calls it answered (support §3): "
            "%r" % (first.calls,),
        )
        second = self.seam(SEAM_SYNTHETIC)
        self.assertEqual(
            len(second.calls),
            0,
            "a second seam's log starts empty and does not contain the first's calls "
            "(support §3, G23, FAM-16.35): %r" % (second.calls,),
        )
        self.assertEqual(
            second({"call": "second"}, legal),
            legal[0],
            "and its schedule starts at its first call, as a fresh instance's does "
            "(support §3, README §7 decision 4, G23): %r" % (second.calls,),
        )
        self.assertEqual(
            len(second.calls),
            1,
            "the fresh instance logs only its own call (support §3, G23): %r"
            % (second.calls,),
        )
        self.assertEqual(
            [entry["readout"] for entry in first.calls],
            [{"call": "first"}, {"call": "first"}],
            "the first instance's log is untouched by the second (support §3, G23): %r"
            % (first.calls,),
        )

    # -- the empty legal set ------------------------------------------------
    def test_hrn_6_7_an_empty_legal_set_is_refused_and_never_folded_or_logged(self):
        """HRN-6.7 `seam(label)(readout, [])` raises `NoLegalAction` naming the label and the contract — it returns no descriptor, invents no fold and logs no call — and the seam still answers a non-empty set afterwards (support §3, surface §5, G24, D-2, errors §4)."""
        policy = self.seam(SEAM_RECORDING)
        exc = self.refuse(
            lambda: policy({"street": "preflop"}, []),
            "NoLegalAction",
            tokens=(
                "harness.seam",
                SEAM_RECORDING,
                "a policy returns a member of legal_actions",
            ),
            label="seam('recording')(readout, [])",
        )
        self.assertIn(
            "empty legal set",
            str(exc),
            "the message names the empty legal set it refused (errors §4, G24): %r"
            % (str(exc),),
        )
        self.assertEqual(
            len(policy.calls),
            0,
            "a refused call is not logged, because it answered nothing (support §3 "
            "step 2, G24): %r" % (policy.calls,),
        )
        legal = self.legal()
        self.assertIn(
            policy({"street": "preflop"}, legal),
            legal,
            "and the same instance still answers a non-empty set (support §3, G24): %r"
            % (policy.calls,),
        )
        invented = self.seam(SEAM_INVENTED)
        refused = self.refuse(
            lambda: invented({"street": "invented"}, ()),
            "NoLegalAction",
            tokens=(SEAM_INVENTED, "legal_actions"),
            label="seam('echo-legal')(readout, ())",
        )
        self.assertIn(
            SEAM_INVENTED,
            str(refused),
            "the label is named for any label, not only the documented ones "
            "(support §3 step 2, errors §4, G24): %r" % (str(refused),),
        )

    # -- no stream, no generator --------------------------------------------
    def test_hrn_6_8_a_seam_touches_no_clock_no_seed_and_no_global_stream(self):
        """HRN-6.8 building seams and answering calls neither seeds nor advances the global `random` stream, and a seam's choice is a function of its label and the calls it answered (support §3, surface §1, G25, ASM-2, D-6)."""
        self.harness()
        legal = self.legal()

        def build_and_call():
            for label in (SEAM_RECORDING, SEAM_SYNTHETIC, SEAM_INVENTED):
                policy = self.ep("seam")(label)
                for _call in range(3):
                    chosen = policy({"street": "preflop"}, legal)
                    self.assertIn(
                        chosen,
                        legal,
                        "every answer is one of the legal descriptors (support §3, "
                        "e2e-surface.md §2, G25): %r" % (chosen,),
                    )

        self.assert_no_random_motion(
            build_and_call,
            "seam construction and its calls",
        )
        first = [self.seam(SEAM_SYNTHETIC)({"call": position}, legal) for position in range(4)]
        second = [self.seam(SEAM_SYNTHETIC)({"call": position}, legal) for position in range(4)]
        self.assertEqual(
            first,
            second,
            "no clock, generator, global stream or ambient fixture decides a seam's "
            "choice (support §3, ASM-2, D-6): %r vs %r" % (first, second),
        )

    def test_hrn_6_9_the_log_holds_the_legal_set_the_seam_was_handed(self):
        """HRN-6.9 the legal set is read once per call, so a caller that later mutates its own list cannot change what the seam chose or logged, while a later call reads the list as it then stands (support §3 step 1, G21)."""
        policy = self.seam(SEAM_RECORDING)
        handed = ["fold", "check-call", "raise"]
        chosen = policy({"street": "preflop"}, handed)
        self.assertEqual(
            chosen,
            "fold",
            "the control: recording takes the first descriptor (support §3, G22): %r"
            % (chosen,),
        )
        handed[0] = "an-invented-descriptor"
        handed.append("another-invented-descriptor")
        entry = as_mapping(policy.calls[0], "the call-log entry")
        self.assertEqual(
            list(as_sequence(entry["legal"], "the logged legal set")),
            ["fold", "check-call", "raise"],
            "the sequence is read once, so a caller's later mutation cannot change what "
            "the seam logged (support §3 step 1, G21): %r" % (entry["legal"],),
        )
        self.assertEqual(
            entry["chosen"],
            "fold",
            "nor what it chose (support §3 step 1, G21): %r" % (entry["chosen"],),
        )
        self.assertEqual(
            policy({"street": "preflop"}, handed),
            "an-invented-descriptor",
            "while a later call reads the list as it then stands (support §3 step 1): "
            "%r" % (policy.calls,),
        )


if __name__ == "__main__":
    unittest.main()
