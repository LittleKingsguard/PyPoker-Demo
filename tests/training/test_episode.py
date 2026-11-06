"""TRN-4 — one episode into transitions: `_seat(index)`, `_transitions(episode, seat, encoder)`.

Drives `docs/L3/training/episode.md` §1-§5 from a **real** episode: `engine.play_hand` at
one invented seed with the three pinned baselines as policies, driven through the two
names `README.md` §4 makes contract. The observations and masks are compared to
`features.encode` and `features.legal_indices` of the decisions they came from, so the
case reads the episode and never the implementation; the terminal flag, the reward and
the terminal mask are `§4`'s four bullets, one case each.

`_transitions` takes an episode record and a seat, so no learner is built and no policy
is assembled here — `episode.md` §2's point that a unit case can build the transitions
without one (`tests/training/test_episode.py::TRN-4.1`).
"""

import unittest

from _training_support import (
    TrainingCase,
    as_float,
    as_int,
    as_mapping,
    as_sequence,
    decision_seat,
    decisions_of,
    encoder,
    episode,
    features,
    fold_episode,
    internal,
    payoff_of,
    same_observation,
    seat_decisions,
)

#: `records.md` §4's seven required keys of one transition record.
TRANSITION_KEYS = {
    "observation",
    "next_observation",
    "action",
    "reward",
    "terminal",
    "legal",
    "next_legal",
}


class EpisodeTest(TrainingCase):
    def transitions(self, record, seat, encoder_name="flat-numeric"):
        return [
            as_mapping(record_of_transition, "one transition record")
            for record_of_transition in as_sequence(
                internal("episode", "_transitions")(record, seat, encoder(encoder_name)),
                "a transition list",
            )
        ]

    def test_trn_4_1_the_seat_alternates_by_the_hand_index(self):
        """TRN-4.1 `_seat(index)` is the hand index modulo two, a plain `0` or `1`, so half a run's hands are on the button and half in the big blind (episode.md §1, engine/surface.md §4, D-16)."""
        seat_of = internal("episode", "_seat")
        for index in range(9):
            with self.subTest(index=index):
                seat = as_int(seat_of(index), "a seat")
                self.assertEqual(
                    seat,
                    index % 2,
                    "seat 0 holds the button in every hand, so alternating the seat the "
                    "learner plays is how a run alternates the button (episode.md §1, "
                    "league.md §3)",
                )
                self.assertIn(seat, (0, 1), "a seat is 0 or 1 and nothing else")

    def test_trn_4_2_one_transition_per_decision_of_one_seat_in_order(self):
        """TRN-4.2 `_transitions` returns one record per decision the seat made, in the order the hand played them, each carrying `records.md` §4's seven keys (episode.md §3, records.md §4)."""
        record = episode()
        for seat in (0, 1):
            expected = seat_decisions(record, seat)
            with self.subTest(seat=seat):
                transitions = self.transitions(record, seat)
                self.assertEqual(
                    len(transitions),
                    len(expected),
                    "one transition per decision of that seat and none for the "
                    "opponent's interleaved ones (episode.md §3): %d against %d"
                    % (len(transitions), len(expected)),
                )
                for transition in transitions:
                    self.assertEqual(
                        set(transition),
                        TRANSITION_KEYS,
                        "a transition carries records.md §4's seven keys "
                        "(episode.md §3-§4): %r" % (sorted(transition),),
                    )

    def test_trn_4_3_the_state_and_the_mask_are_the_decision_s_own(self):
        """TRN-4.3 each transition's `observation` is `features.encode` of that decision's readout and its `legal` is `features.legal_indices` of that decision's legals (episode.md §3 items 1-2, features/surface.md §6, §8)."""
        record = episode()
        flat = encoder("flat-numeric")
        for seat in (0, 1):
            decisions = seat_decisions(record, seat)
            transitions = self.transitions(record, seat)
            with self.subTest(seat=seat):
                for decision, transition in zip(decisions, transitions):
                    self.assertTrue(
                        same_observation(
                            transition["observation"],
                            features().encode(flat, decision["readout"]),
                        ),
                        "the observation is the state that seat faced, encoded by the "
                        "run's encoder (episode.md §3 item 1)",
                    )
                    self.assertEqual(
                        [as_int(index, "a legal index") for index in as_sequence(
                            transition["legal"], "a transition's 'legal'")],
                        [as_int(index, "a legal index") for index in
                         features().legal_indices(decision["legal"])],
                        "the mask is legal_indices of that decision's descriptors, "
                        "position-aligned (episode.md §3 item 2, features/surface.md §8)",
                    )

    def test_trn_4_4_the_action_is_the_legal_index_and_round_trips(self):
        """TRN-4.4 `action` is the vocabulary index of the descriptor the hand applied — the descriptor's position in `legal`, which `features.decode_action` maps back — and never the descriptor itself (episode.md §3 item 3, features/surface.md §8-§9, guardrails G7)."""
        record = episode()
        for seat in (0, 1):
            decisions = seat_decisions(record, seat)
            transitions = self.transitions(record, seat)
            with self.subTest(seat=seat):
                for decision, transition in zip(decisions, transitions):
                    legals = list(decision["legal"])
                    indices = [
                        as_int(index, "a legal index")
                        for index in features().legal_indices(legals)
                    ]
                    position = None
                    for candidate, descriptor in enumerate(legals):
                        if descriptor == decision["action"]:
                            position = candidate
                            break
                    self.assertIsNotNone(
                        position,
                        "the episode applied a descriptor of legal_actions "
                        "(engine/surface.md §10): %r of %r"
                        % (decision["action"], legals),
                    )
                    action = as_int(transition["action"], "a transition's 'action'")
                    self.assertEqual(
                        action,
                        indices[position],
                        "the action is the vocabulary index of the applied descriptor, "
                        "read by position because legal_indices is position-aligned "
                        "(episode.md §3 item 3, features/surface.md §8)",
                    )
                    self.assertIn(
                        action,
                        indices,
                        "an index outside the mask is agents.learn's refusal, so a "
                        "transition's action is a member of its legal set "
                        "(agents/surface.md §7, guardrails G7): %r in %r"
                        % (action, indices),
                    )
                    self.assertEqual(
                        features().decode_action(action),
                        decision["action"],
                        "the index round-trips to the descriptor the hand applied "
                        "(episode.md §3 item 3, features/surface.md §9)",
                    )

    def test_trn_4_5_the_successor_is_the_seat_s_next_decision(self):
        """TRN-4.5 a transition's `next_observation` and `next_legal` are the seat's **next** decision's, encoded and masked the same way, so the chain never bootstraps on the other seat's value (episode.md §3 item 4, §3's rejection, agents/rule.md §2)."""
        record = episode()
        flat = encoder("flat-numeric")
        for seat in (0, 1):
            decisions = seat_decisions(record, seat)
            transitions = self.transitions(record, seat)
            with self.subTest(seat=seat):
                for position, transition in enumerate(transitions[:-1]):
                    successor = decisions[position + 1]
                    self.assertTrue(
                        same_observation(
                            transition["next_observation"],
                            features().encode(flat, successor["readout"]),
                        ),
                        "the successor is the learner seat's own next state and never "
                        "the opponent's interleaved one (episode.md §3)",
                    )
                    self.assertEqual(
                        [as_int(index, "a legal index") for index in as_sequence(
                            transition["next_legal"], "a 'next_legal'")],
                        [as_int(index, "a legal index") for index in
                         features().legal_indices(successor["legal"])],
                        "the successor's mask is its own decision's (episode.md §3)",
                    )

    def test_trn_4_6_the_terminal_flag_is_positional_and_the_reward_is_the_decision_s(self):
        """TRN-4.6 the last transition of the list is the only `terminal` one, `reward` is `float(decision['reward'])` — zero everywhere else and the seat's net chip delta at its terminal decision (episode.md §4, records.md §5, ASM-12)."""
        record = episode()
        for seat in (0, 1):
            decisions = seat_decisions(record, seat)
            transitions = self.transitions(record, seat)
            with self.subTest(seat=seat):
                flags = [bool(transition["terminal"]) for transition in transitions]
                self.assertEqual(
                    flags,
                    [False] * (len(transitions) - 1) + [True],
                    "the flag is positional: the seat's last decision is its terminal "
                    "one even when the opponent folded afterwards (episode.md §4)",
                )
                rewards = [as_float(transition["reward"], "a reward") for transition in transitions]
                self.assertEqual(
                    rewards[:-1],
                    [0.0] * (len(transitions) - 1),
                    "the reward is zero at every decision but the seat's terminal one "
                    "(episode.md §4, ASM-12): %r" % (rewards,),
                )
                self.assertAlmostEqual(
                    rewards[-1],
                    as_float(decisions[-1]["reward"], "the terminal decision's reward"),
                    places=12,
                    msg="the terminal transition carries its own decision's reward, "
                    "unshaped (episode.md §4, ASM-12)",
                )
                self.assertAlmostEqual(
                    rewards[-1],
                    payoff_of(record, seat),
                    places=12,
                    msg="the terminal reward is the seat's net chip delta for the "
                    "completed hand (episode.md §4, records.md §5, ASM-12)",
                )

    def test_trn_4_7_the_terminal_transition_carries_its_own_mask_and_observation(self):
        """TRN-4.7 the terminal transition has no successor, so its `next_observation` and `next_legal` repeat its own — an empty mask is illegal (episode.md §4, features/surface.md §8, guardrails G7)."""
        record = episode()
        for seat in (0, 1):
            transitions = self.transitions(record, seat)
            with self.subTest(seat=seat):
                terminal = transitions[-1]
                self.assertTrue(
                    same_observation(terminal["next_observation"], terminal["observation"]),
                    "the terminal transition repeats its own observation, because it "
                    "has none of its own to hand on (episode.md §4)",
                )
                self.assertEqual(
                    [as_int(index, "a legal index") for index in as_sequence(
                        terminal["next_legal"], "a 'next_legal'")],
                    [as_int(index, "a legal index") for index in as_sequence(
                        terminal["legal"], "a 'legal'")],
                    "the terminal transition repeats its own mask, because agents.learn "
                    "refuses an empty one (episode.md §4, agents/rule.md §3)",
                )
                self.assertTrue(
                    as_sequence(terminal["next_legal"], "a 'next_legal'"),
                    "an empty mask is illegal, so the terminal record's own mask is "
                    "non-empty (features/surface.md §8, episode.md §4)",
                )

    def test_trn_4_8_a_seat_that_never_acted_yields_no_transition(self):
        """TRN-4.8 a hand in which the learner's seat never acted yields an empty list — no update, no signal and no error (episode.md §3, loop.md §1 step 6, guardrails G10)."""
        record = fold_episode()
        self.assertEqual(
            seat_decisions(record, 1),
            [],
            "the invented episode must be one where the button folded preflop, so the "
            "big blind never acted (episode.md §3)",
        )
        self.assertEqual(
            self.transitions(record, 1),
            [],
            "a hand in which the seat never acted yields an empty list, and that is not "
            "an error: the run makes no learn call for it (episode.md §3, "
            "agents/surface.md §7)",
        )
        acted = self.transitions(record, 0)
        self.assertEqual(
            len(acted),
            1,
            "the other seat acted once and its one decision is its terminal one "
            "(episode.md §4): %r" % (len(acted),),
        )
        self.assertTrue(acted[0]["terminal"], "that single transition is terminal")
        self.assertAlmostEqual(
            as_float(acted[0]["reward"], "the terminal reward"),
            payoff_of(record, 0),
            places=12,
            msg="a lost hand pays the seat its net chip delta (episode.md §4, ASM-12)",
        )
        self.assertNotEqual(
            as_int(decision_seat(decisions_of(record)[0]), "a seat"),
            1,
            "the episode's first decision is the button's, which is seat 0 in every "
            "hand (engine/surface.md §4)",
        )


if __name__ == "__main__":
    unittest.main()
