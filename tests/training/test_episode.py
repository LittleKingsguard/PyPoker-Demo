"""TRN-4 — one episode into transitions: `_seat(index)`, `_transitions(episode, seat, encoder, utility)`.

Drives `docs/L3/training/episode.md` §1-§5 from a **real** episode: `engine.play_hand` at
one invented seed with the three pinned baselines as policies, driven through the two
names `README.md` §4 makes contract. The observations and masks are compared to
`features.encode` and `features.legal_indices` of the decisions they came from, so the
case reads the episode and never the implementation; the terminal flag, the reward and
the terminal mask are `§4`'s four bullets, one case each.

`_transitions` takes an episode record and a seat, so no learner is built and no policy
is assembled here — `episode.md` §2's point that a unit case can build the transitions
without one (`tests/training/test_episode.py::TRN-4.1`).

D-20's arithmetic is `docs/L3/training/reward.md` §1-§5 and `docs/L1/utilities.md` §2, §4,
which `reward.md` §6 makes contract for this battery: `TRN-4.9` derives the four scores from
the implementation's own formula and holds them against the numbers D-20 states, `TRN-4.10`
the `0.0` every non-terminal decision keeps under either utility, `TRN-4.11` the
`net-chips` delta, `TRN-4.12` the chips-in-play guard's refusal, and `TRN-4.13` the
catalogue's **reward token** as the selector. The four hands are the battery's own invented
seeds, and each case asserts the payoff the seed actually produced before it asserts the
reward that payoff scores (`battery.md` §4, §5, D-20).

D-43's two facts are `docs/L3/training/episode.md` §5's and `docs/L1/counterfactual.md` §2,
§4 and §6's: `TRN-4.14` the episode boundary every transition carries, `TRN-4.15` the
resolution — one entry per legal descriptor, the utility applied to each branch's chip delta
by the terminal reward's own function, `None` elsewhere, and `counterfactual.md` §4's
invariant at the descriptor the hand applied — and `TRN-4.16` the hand the reveal cannot
resolve, whose transitions carry no such key at all. `TRN-4.2` reads `records.md` §4's
**eight** required keys, the conditional ninth being the only key either case may find
beside them.
"""

import copy
import unittest

from _training_support import (
    ALL_IN_LOSE_SEED,
    ALL_IN_WIN_SEED,
    IGNORED_UTILITY,
    LOSE_TWO_SEED,
    TrainingCase,
    WIN_TWO_SEED,
    all_in_episode,
    as_float,
    as_int,
    as_mapping,
    as_sequence,
    as_text,
    decision_seat,
    decisions_of,
    encoder,
    engine,
    episode,
    features,
    fold_episode,
    internal,
    payoff_of,
    same_observation,
    seat_decisions,
    shaped_vocabulary,
    two_utility_names,
    utility_catalogue,
    utility_names,
    utility_reward,
)

#: D-20's four numbers, read off a payoff of the fixed game and stated by that decision
#: itself ("a ±2-chip pair scores **+0.190 / −0.210**, and an all-in scores **+1.000 /
#: −3.000**", D-20, `utilities.md` §2, `reward.md` §3). They are the case's expectation and
#: never its derivation: TRN-4.9 computes the same value from `T`, `s0` and the payoff the
#: seed produced, and holds the two together.
D_20_NUMBERS = {2.0: 0.190, -2.0: -0.210, 20.0: 1.000, -20.0: -3.000}

#: `records.md` §4's **eight** required keys of one transition record — D-43's `episode`
#: boundary being the eighth (`records.md` §4, §5, `counterfactual.md` §2).
TRANSITION_KEYS = {
    "observation",
    "next_observation",
    "action",
    "reward",
    "terminal",
    "legal",
    "next_legal",
    "episode",
}

#: The one **conditional** key `records.md` §4 declares: present exactly when the hand
#: resolved and absent — not `None` — in a hand `counterfactual.md` §4 refuses to value
#: (`counterfactual.md` §2, §4, §6, D-43).
OPTIONAL_KEYS = {"counterfactual"}


class EpisodeTest(TrainingCase):
    def transitions(self, record, seat, encoder_name="flat-numeric", utility=None):
        return [
            as_mapping(record_of_transition, "one transition record")
            for record_of_transition in as_sequence(
                internal("episode", "_transitions")(
                    record, seat, encoder(encoder_name), utility
                ),
                "a transition list",
            )
        ]

    def rewards(self, record, seat, utility=None):
        """One seat's reward per decision, in decision order (`reward.md` §1, §5)."""
        return [
            as_float(transition["reward"], "a reward")
            for transition in self.transitions(record, seat, utility=utility)
        ]

    def chip_counts(self, record, seat):
        """`T`, `s_0` and the seat's terminal payoff, read off the hand (`utilities.md` §4).

        `T` is `sum(readout['stacks']) + readout['pot']` at the seat's terminal decision and
        `s_0` is `engine.game_config()['starting_stack']`; the payoff is the episode's own
        net chip delta for that seat (`reward.md` §3, `records.md` §5, ASM-6).
        """
        game = as_mapping(engine().game_config(), "the game's configuration")
        starting_stack = as_float(game["starting_stack"], "the game's starting stack")
        readout = as_mapping(
            seat_decisions(record, seat)[-1]["readout"], "a terminal decision's readout"
        )
        total = sum(
            as_float(stack, "a seat's stack")
            for stack in as_sequence(readout["stacks"], "a readout's 'stacks'")
        ) + as_float(readout["pot"], "a readout's 'pot'")
        return float(total), starting_stack, payoff_of(record, seat)

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
        """TRN-4.2 `_transitions` returns one record per decision the seat made, in the order the hand played them, each carrying `records.md` §4's eight keys and, when the hand resolved, its ninth (episode.md §3, §5, records.md §4, counterfactual.md §2, D-43)."""
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
                        set(transition) - OPTIONAL_KEYS,
                        TRANSITION_KEYS,
                        "a transition carries records.md §4's eight required keys — "
                        "D-43's `episode` among them — and no key of its own "
                        "(episode.md §3-§4, records.md §4, counterfactual.md §2): %r"
                        % (sorted(transition),),
                    )
                    self.assertIn(
                        set(transition),
                        (TRANSITION_KEYS, TRANSITION_KEYS | OPTIONAL_KEYS),
                        "the ninth key is the one conditional one `records.md` §4 "
                        "declares, `counterfactual`, and nothing else: %r"
                        % (sorted(transition),),
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

    # -- D-20: the terminal reward a utility delivers ----------------------
    def hands(self):
        """The battery's four invented hands, as `(what it is, record, seat, delta)`.

        Two are played with both seats calling, so the fixed game's 40 chips split ±2 with
        no bet beyond the blinds; two are played with both seats raising whenever they may,
        so one seat commits all twenty chips and the hand splits ±20 (`utilities.md` §2,
        §4, `reward.md` §3, ASM-6). The seat is the one whose terminal decision is read and
        the delta is the payoff the seed is asserted to produce before any reward is
        asserted.
        """
        return (
            (
                "a hand that wins 2 chips",
                episode(WIN_TWO_SEED),
                0,
                2.0,
            ),
            (
                "a hand that loses 2 chips",
                episode(LOSE_TWO_SEED),
                0,
                -2.0,
            ),
            (
                "an all-in that wins 20 chips",
                all_in_episode(ALL_IN_WIN_SEED),
                0,
                20.0,
            ),
            (
                "an all-in that loses 20 chips",
                all_in_episode(ALL_IN_LOSE_SEED),
                0,
                -20.0,
            ),
        )

    def test_trn_4_9_the_shortfall_reward_is_d_20_s_four_numbers(self):
        """TRN-4.9 under `stack-shortfall` the terminal reward is `((T − s0)² − (T − (s0 + delta))²) / (T − s0)²` — derived in the case from the hand's own `T` and the game's `s0`, not from a memorised float — and the four hands score D-20's +0.190, −0.210, +1.000 and −3.000 (utilities.md §2, §4, reward.md §3, D-20, FAM-18)."""
        _, shortfall = two_utility_names()
        for label, record, seat, delta in self.hands():
            with self.subTest(hand=label):
                total, starting_stack, payoff = self.chip_counts(record, seat)
                self.assertEqual(
                    payoff,
                    delta,
                    "the invented hand at seed %r must be one whose seat %r terminal "
                    "payoff is %r before any reward is read from it, and this seed "
                    "produces %r (records.md §5, ASM-12): %r"
                    % (record["seed"], seat, delta, payoff, label),
                )
                self.assertEqual(
                    total,
                    2.0 * starting_stack,
                    "`T` is every chip the hand holds — sum(readout['stacks']) + "
                    "readout['pot'] — and the fixed game deals two seats of %r, so it is "
                    "%r at every decision (utilities.md §4, ASM-6): %r"
                    % (starting_stack, 2.0 * starting_stack, total),
                )
                before = (total - starting_stack) ** 2
                after = (total - (starting_stack + delta)) ** 2
                expected = (before - after) / before
                observed = self.rewards(record, seat, utility=shortfall)[-1]
                self.assertAlmostEqual(
                    observed,
                    expected,
                    places=12,
                    msg="the terminal reward is the shortfall delta normalised by the "
                    "shortfall a hand begins with, and this case derives it from the "
                    "hand's own `T` = %r and the game's `s0` = %r with delta = %r "
                    "(utilities.md §2, §4, reward.md §3, D-20): %r against %r"
                    % (total, starting_stack, delta, observed, expected),
                )
                self.assertAlmostEqual(
                    round(observed, 3),
                    D_20_NUMBERS[delta],
                    places=3,
                    msg="D-20 states the four numbers this fixed game scores — "
                    "+0.190 / −0.210 for ±2 chips and +1.000 / −3.000 all-in — so a "
                    "loss of a given size costs more than a win of the same size pays "
                    "and all-in aggression is penalised threefold (D-20, utilities.md "
                    "§2, reward.md §3): %r for %r" % (observed, label),
                )
        numbers = [
            self.rewards(record, seat, utility=shortfall)[-1]
            for _label, record, seat, _delta in self.hands()
        ]
        self.assertLess(
            numbers[1],
            -numbers[0],
            "a loss of a given size is always penalised more than a win of the same "
            "size pays — the asymmetry D-20 chose this utility for — so the −2 hand's "
            "reward is strictly below the negation of the +2 hand's (D-20, "
            "utilities.md §2, reward.md §3): %r against %r"
            % (numbers[1], numbers[0]),
        )
        self.assertLess(
            numbers[3],
            -numbers[2],
            "the same asymmetry at the all-in stake, threefold: −3.000 against +1.000 "
            "(D-20, utilities.md §2, reward.md §3): %r against %r"
            % (numbers[3], numbers[2]),
        )

    def test_trn_4_10_every_non_terminal_decision_keeps_the_episode_s_zero(self):
        """TRN-4.10 under **both** catalogue utilities every transition but the seat's terminal one carries exactly `0.0`, so the utility adds no intermediate term and no shaping on top of ASM-12's delivery rule (utilities.md §2, §3, §4, reward.md §5, records.md §4, ASM-12, D-20)."""
        first, second = two_utility_names()
        for utility in (first, second):
            for label, record, seat, delta in self.hands():
                with self.subTest(utility=utility, hand=label):
                    rewards = self.rewards(record, seat, utility=utility)
                    self.assertEqual(
                        rewards[:-1],
                        [0.0] * (len(rewards) - 1),
                        "the reward is terminal only: every decision but the seat's "
                        "last carries `0.0`, which is the value the episode placed and "
                        "the utility leaves alone (utilities.md §2, §3, reward.md §5, "
                        "records.md §4, ASM-12): %r under %r"
                        % (rewards, utility),
                    )
                    self.assertEqual(
                        [reward for reward in rewards if reward != 0.0],
                        [rewards[-1]],
                        "exactly one transition of a hand carries a reward, whatever "
                        "utility scored it, so no second term was introduced (ASM-12, "
                        "reward.md §5): %r under %r" % (rewards, utility),
                    )
                    self.assertNotEqual(
                        rewards[-1],
                        0.0,
                        "the invented hand pays its seat %r chips, so its terminal "
                        "transition is non-zero under either arithmetic and a `0.0` "
                        "there would be a missed decision rather than a split pot "
                        "(reward.md §5, records.md §5): %r under %r"
                        % (delta, rewards, utility),
                    )

    def test_trn_4_11_net_chips_is_the_delta_unshaped(self):
        """TRN-4.11 under `net-chips` — and under no utility name at all, which is that same catalogue first member — the terminal reward is the decision's own `reward`, the seat's net chip delta for the completed hand, unnormalised and unshaped (utilities.md §2, §5, reward.md §3, records.md §4, §5, ASM-12, D-20)."""
        first, _ = two_utility_names()
        self.assertEqual(
            utility_names()[0],
            first,
            "the catalogue's first member is the declared default of utilities.md §5, so "
            "a call naming no utility is that member's arithmetic: %r"
            % (utility_names(),),
        )
        for utility in (first, None):
            for label, record, seat, delta in self.hands():
                decisions = seat_decisions(record, seat)
                _total, _starting_stack, payoff = self.chip_counts(record, seat)
                with self.subTest(utility=utility, hand=label):
                    terminal = self.transitions(record, seat, utility=utility)[-1]
                    observed = as_float(terminal["reward"], "the terminal reward")
                    self.assertAlmostEqual(
                        observed,
                        as_float(
                            decisions[-1]["reward"], "the terminal decision's reward"
                        ),
                        places=12,
                        msg="under net-chips the terminal reward is the decision's own "
                        "`reward` and nothing is added, clipped or normalised "
                        "(utilities.md §2, reward.md §3, ASM-12): %r under %r"
                        % (observed, utility),
                    )
                    self.assertAlmostEqual(
                        observed,
                        payoff,
                        places=12,
                        msg="the terminal reward is the seat's net chip delta for the "
                        "completed hand, which is the engine's own payoff for that seat "
                        "(records.md §5, ASM-12, reward.md §3): %r under %r"
                        % (observed, utility),
                    )
                    self.assertAlmostEqual(
                        observed,
                        delta,
                        places=12,
                        msg="the delta is unnormalised, so a ±20 hand scores ±20 and not "
                        "the shortfall's ±1.000/±3.000 (utilities.md §2, §4, reward.md "
                        "§3): %r under %r" % (observed, utility),
                    )

    def test_trn_4_12_a_hand_whose_totals_disagree_is_refused_naming_the_seed_and_both_totals(self):
        """TRN-4.12 a hand whose terminal readout's `sum(stacks) + pot` is not the chips the game declares is refused with `training`'s `ChipConservationBroken`, naming the hand's seed and both totals — while `net-chips`, which never reads the readout, still scores that hand (utilities.md §4, reward.md §4, errors.md §2, ASM-6, ASM-28, D-20)."""
        first, second = two_utility_names()
        game = as_mapping(engine().game_config(), "the game's configuration")
        starting_stack = as_float(game["starting_stack"], "the starting stack")
        declared = as_float(game["seats"], "the seat count") * starting_stack
        record = copy.deepcopy(episode())
        seat = 0
        readout = as_mapping(
            seat_decisions(record, seat)[-1]["readout"], "a terminal decision's readout"
        )
        # The doctor keeps the readout encodable — `features.encode` reads the pot as a
        # non-negative integer — so the hand is refused by the chips-in-play guard and
        # not by the encoder (`features/surface.md` §6, reward.md §4).
        readout["pot"] = as_int(readout["pot"], "a readout's 'pot'") + 1
        total = sum(
            as_float(stack, "a seat's stack")
            for stack in as_sequence(readout["stacks"], "a readout's 'stacks'")
        ) + as_float(readout["pot"], "a readout's 'pot'")
        self.assertNotEqual(
            total,
            declared,
            "the invented episode must be one whose chips in play disagree with the game "
            "before its refusal is read: it totals %r against %r (reward.md §4)"
            % (total, declared),
        )
        refused = self.refuse(
            lambda: internal("episode", "_transitions")(
                record, seat, encoder(), second
            ),
            "ChipConservationBroken",
            groups=(
                (str(record["seed"]),),
                (repr(float(total)),),
                (repr(float(declared)),),
                ("chips in play", "total", "stack"),
            ),
            label="a hand whose chips in play disagree with the game",
        )
        message = str(refused)
        self.assertIn(
            str(record["seed"]),
            message,
            "the refusal names the hand's seed, so a run can say which hand broke the "
            "guard rather than which hand index (reward.md §4, utilities.md §4): %r"
            % (message,),
        )
        for label, value in (("the readout's total", total),
                             ("the game's declared total", declared)):
            self.assertIn(
                repr(float(value)),
                message,
                "the refusal names both totals — %s is %r — because a normaliser that is "
                "not the game's own would make one reward incommensurable with the next "
                "(utilities.md §4, reward.md §4, ASM-28): %r"
                % (label, float(value), message),
            )
        accepted = self.transitions(episode(), seat, utility=second)
        self.assertTrue(
            accepted,
            "the same hand before it was doctored is scored, so the refusal above is "
            "about the total and not about the hand (reward.md §4): %r" % (accepted,),
        )
        self.assertAlmostEqual(
            self.rewards(record, seat, utility=first)[-1],
            payoff_of(record, seat),
            places=12,
            msg="the guard is reached only by the arithmetic that needs the readout: "
            "`net-chips` reads the decision's own reward and nothing else, so a hand it "
            "scores is never measured for conservation (reward.md §4, utilities.md §2, "
            "§4): %r" % (record["payoffs"],),
        )

    def test_trn_4_13_the_arithmetic_is_selected_by_the_catalogue_s_reward_token(self):
        """TRN-4.13 `REWARDS` is keyed by the **reward tokens** the catalogue states and by nothing else, `_reward_function` resolves a member to its token's arithmetic (`None` meaning the catalogue's first), and a utility name outside the catalogue is refused by name rather than defaulted to the net chip delta (utilities.md §2, §4, §5, reward.md §2, D-20)."""
        catalogue = utility_catalogue()
        self.assertEqual(
            len(catalogue),
            2,
            "the catalogue publishes exactly two members — `net-chips` and the utility "
            "D-20 adds — so a token selects one of two arithmetics (utilities.md §2, "
            "D-20): %r" % (sorted(catalogue),),
        )
        tokens = {
            as_text(name, "a utility name"): utility_reward(name) for name in catalogue
        }
        self.assertEqual(
            len(set(tokens.values())),
            len(tokens),
            "two catalogue members state two distinct reward tokens, which is what makes "
            "the token — and not the member's name — the selector (utilities.md §2, "
            "reward.md §2): %r" % (tokens,),
        )
        rewards = as_mapping(internal("episode", "REWARDS"), "the reward table")
        self.assertEqual(
            set(rewards),
            set(tokens.values()),
            "REWARDS is keyed by the tokens the catalogue states and carries no name of "
            "its own, so the arithmetic is read from the catalogue's own description of "
            "what a member delivers (utilities.md §2, reward.md §2, D-20): %r against %r"
            % (sorted(rewards), sorted(tokens.values())),
        )
        reward_function = internal("episode", "_reward_function")
        for name in catalogue:
            with self.subTest(utility=name):
                resolved, arithmetic = reward_function(name)
                self.assertEqual(
                    as_text(resolved, "a resolved utility"),
                    name,
                    "the member's own name is what is resolved and discarded, the token "
                    "being what the step reads (reward.md §2): %r" % (resolved,),
                )
                self.assertIs(
                    arithmetic,
                    rewards[tokens[name]],
                    "a catalogued member resolves to the callable its reward token names "
                    "(utilities.md §2, reward.md §2): %r under %r"
                    % (arithmetic, name),
                )
        default, default_arithmetic = reward_function(None)
        self.assertEqual(
            as_text(default, "the default utility"),
            utility_names()[0],
            "a call naming no utility is the catalogue's first member, the declared "
            "default of utilities.md §5 (records.md §3, D-20): %r" % (default,),
        )
        self.assertIs(
            default_arithmetic,
            rewards[tokens[utility_names()[0]]],
            "and it is that member's arithmetic, resolved through the same token "
            "(utilities.md §5, reward.md §2): %r" % (default_arithmetic,),
        )
        refused = self.refuse(
            lambda: reward_function(IGNORED_UTILITY),
            "ConfigurationInvalid",
            groups=((IGNORED_UTILITY,), ("catalogue",)),
            label="a utility name outside the catalogue",
        )
        for name in catalogue:
            self.assertIn(
                name,
                str(refused),
                "the refusal names every member the catalogue does carry, so a reader "
                "sees the whole vocabulary it may name instead (utilities.md §5, "
                "reward.md §2): %r" % (str(refused),),
            )
        self.refuse(
            lambda: internal("episode", "_transitions")(
                episode(), 0, encoder(), IGNORED_UTILITY
            ),
            "ConfigurationInvalid",
            groups=((IGNORED_UTILITY,),),
            label="a transition step asked for an uncatalogued utility",
        )
        self.assertTrue(
            self.transitions(episode(), 0, utility=utility_names()[1]),
            "the control: the same call naming a catalogued member is accepted, so the "
            "refusal is about the name and not about the argument (utilities.md §5, "
            "reward.md §2): %r" % (utility_names(),),
        )

    # -- D-43: the episode boundary and the resolution ----------------------
    def branch_deltas(self, decision):
        """One decision's resolved chip deltas, `{descriptor: delta}` (records.md §5)."""
        return as_mapping(
            decision["counterfactual"], "a decision's resolved chip deltas"
        )

    def shortfall(self, total, starting_stack, delta):
        """`(U(s_0) − U(s_0 + delta)) / U(s_0)`, derived from the hand's own `T` (§4)."""
        before = (total - starting_stack) ** 2
        after = (total - (starting_stack + delta)) ** 2
        return (before - after) / before

    def test_trn_4_14_every_transition_carries_the_episodes_own_seed(self):
        """TRN-4.14 every transition carries `episode`, the episode's own `seed` as a plain `int`: one hand's transitions carry one number, two hands of one run carry two, and the boundary is the episode's and never a position in a batch (episode.md §3, §5, records.md §4, §5, counterfactual.md §2, D-43)."""
        first = episode()
        second = episode(WIN_TWO_SEED)
        self.assertNotEqual(
            as_int(first["seed"], "the first hand's seed"),
            as_int(second["seed"], "the second hand's seed"),
            "the two invented hands are dealt at two seeds, which is what makes the "
            "boundary observable across hands (seeds.md §2, records.md §5): %r"
            % ([first.get("seed"), second.get("seed")],),
        )
        seen = set()
        for record in (first, second):
            seed = as_int(record["seed"], "the episode's seed")
            for seat in (0, 1):
                transitions = self.transitions(record, seat)
                if not transitions:
                    continue  # a seat that never acted files no signal (episode.md §3)
                numbers = {
                    as_int(transition["episode"], "a transition's 'episode'")
                    for transition in transitions
                }
                with self.subTest(seed=seed, seat=seat):
                    self.assertEqual(
                        numbers,
                        {seed},
                        "every transition of one hand carries that episode's own seed "
                        "and no other number, so one episode's transitions are one "
                        "episode's (records.md §4, counterfactual.md §2): %r against %r"
                        % (sorted(numbers), seed),
                    )
                seen |= numbers
        self.assertEqual(
            seen,
            {as_int(first["seed"], "a seed"), as_int(second["seed"], "a seed")},
            "two hands of one run carry two numbers, which is the whole of what the "
            "boundary says: the batch is a sequence of episodes and not one episode "
            "(records.md §4, §5, counterfactual.md §2): %r" % (sorted(seen),),
        )

    def test_trn_4_15_each_legal_branch_is_the_utility_s_transform_and_the_applied_one_is_the_delta(self):
        """TRN-4.15 `counterfactual` is a tuple of length `A` holding, at each of that decision's legal indices, the branch's whole-hand chip delta put through the **same** function the terminal `reward` is — the delta itself under `net-chips`, the shortfall delta under `stack-shortfall` — `None` at every other index, and at the descriptor the hand applied it is the seat's realised delta, which the terminal transition carries as its `reward` (episode.md §5, counterfactual.md §4, §6, records.md §4, D-43)."""
        first, second = two_utility_names()
        record = episode()
        reveal = as_mapping(record["reveal"], "the episode's 'reveal'")
        self.assertTrue(
            bool(reveal["showdown"]),
            "the invented hand reaches a showdown, which is what makes it a hand the "
            "reveal can resolve (counterfactual.md §4, records.md §5): %r" % (reveal,),
        )
        self.assertFalse(
            bool(reveal["split"]),
            "and it is not a split pot, so it carries values rather than falling back "
            "(counterfactual.md §4): %r" % (reveal,),
        )
        count = len(shaped_vocabulary())
        for seat in (0, 1):
            decisions = seat_decisions(record, seat)
            total, starting_stack, payoff = self.chip_counts(record, seat)
            for utility in (first, second):
                transitions = self.transitions(record, seat, utility=utility)
                with self.subTest(seat=seat, utility=utility):
                    self.assertEqual(
                        len(transitions),
                        len(decisions),
                        "one transition per decision of the seat (episode.md §3)",
                    )
                    for decision, transition in zip(decisions, transitions):
                        indices = [
                            as_int(index, "a legal index")
                            for index in features().legal_indices(decision["legal"])
                        ]
                        self.assertIn(
                            "counterfactual",
                            transition,
                            "a hand the reveal resolved gives every one of its "
                            "transitions a `counterfactual`, the terminal one included "
                            "(counterfactual.md §4, §6, records.md §4): %r"
                            % (sorted(transition),),
                        )
                        values = as_sequence(
                            transition["counterfactual"], "a resolution"
                        )
                        self.assertEqual(
                            len(values),
                            count,
                            "a resolution is one entry per descriptor of the run's "
                            "shape — `A`, the head's width and the number of indices the "
                            "vocabulary declares (sizing.md §6, counterfactual.md §5, §6): "
                            "%d against %d" % (len(values), count),
                        )
                        deltas = self.branch_deltas(decision)
                        for position, descriptor in enumerate(decision["legal"]):
                            index = indices[position]
                            delta = as_float(
                                deltas[descriptor], "a branch's chip delta"
                            )
                            expected = (
                                delta if utility == first
                                else self.shortfall(total, starting_stack, delta)
                            )
                            self.assertAlmostEqual(
                                as_float(values[index], "a branch's value"),
                                expected,
                                places=12,
                                msg="the entry at a legal index is that branch's "
                                "whole-hand chip delta put through the utility's own "
                                "function — the terminal reward's, by the same call and "
                                "with the same `T` = %r and `s_0` = %r — so the two "
                                "arithmetics are one arithmetic under two units "
                                "(counterfactual.md §4, utilities.md §2, §4, D-20): "
                                "action %r under %r"
                                % (total, starting_stack, descriptor, utility),
                            )
                        for index in range(count):
                            if index in indices:
                                continue
                            self.assertIsNone(
                                values[index],
                                "an index that was not legal at that decision carries "
                                "`None`, so a masked action is never valued and never "
                                "updated (counterfactual.md §5, agents/rule.md §2): "
                                "index %d of %r" % (index, indices),
                            )
                        applied = as_int(transition["action"], "a transition's action")
                        self.assertAlmostEqual(
                            as_float(values[applied], "the applied branch's value"),
                            payoff if utility == first
                            else self.shortfall(total, starting_stack, payoff),
                            places=9,
                            msg="the invariant `counterfactual.md` §4 proves: at the "
                            "descriptor the hand **applied**, the value is the seat's "
                            "realised net chip delta, %r, under either utility — the "
                            "closure charges that branch exactly what the hand "
                            "committed and pays it exactly what it won (%r under %r)"
                            % (payoff, values, utility),
                        )
                    terminal = transitions[-1]
                    self.assertAlmostEqual(
                        as_float(
                            as_sequence(terminal["counterfactual"], "a resolution")[
                                as_int(terminal["action"], "the terminal action")
                            ],
                            "the terminal resolution's applied value",
                        ),
                        as_float(terminal["reward"], "the terminal reward"),
                        places=12,
                        msg="at the seat's terminal decision the resolution's value at "
                        "the applied descriptor **is** that transition's `reward`, "
                        "because the utility is applied to both sides by the same "
                        "function (counterfactual.md §4, ASM-12): %r against %r"
                        % (terminal["counterfactual"], terminal["reward"]),
                    )

    def test_trn_4_16_a_hand_the_reveal_cannot_resolve_carries_no_counterfactual_key(self):
        """TRN-4.16 a hand without a showdown carries **no** `counterfactual` key at all — not `None`, and not a partial tuple — while its eight required keys stand, which is the fallback `counterfactual.md` §4 and D-40 pin; the control: the resolved hand of TRN-4.15 does carry one (episode.md §5, counterfactual.md §2, §4, records.md §4, D-43)."""
        record = fold_episode()
        reveal = as_mapping(record["reveal"], "the episode's 'reveal'")
        self.assertFalse(
            bool(reveal["showdown"]),
            "the invented hand ends on the button's pre-flop fold, so no seat shows and "
            "the reveal cannot resolve it (counterfactual.md §4, episode.md §5): %r"
            % (reveal,),
        )
        for decision in decisions_of(record):
            self.assertIsNone(
                decision["counterfactual"],
                "the engine values no decision of an unresolved hand (engine/episode.md "
                "§5, records.md §5): %r" % (decision.get("counterfactual"),),
            )
        acted = self.transitions(record, 0)
        self.assertEqual(
            len(acted),
            1,
            "the button acted once and that decision is its terminal one "
            "(episode.md §4): %r" % (len(acted),),
        )
        self.assertNotIn(
            "counterfactual",
            acted[0],
            "a hand the reveal cannot resolve carries no `counterfactual` key at all: "
            "`None` and a partial resolution are both refused, because the member then "
            "falls back to the rule's own target exactly as D-40 pinned "
            "(counterfactual.md §4, §6): %r" % (sorted(acted[0]),),
        )
        self.assertEqual(
            set(acted[0]),
            TRANSITION_KEYS,
            "and nothing else is missing: the eight required keys are on an unresolved "
            "hand's transition too, `episode` among them (records.md §4): %r"
            % (sorted(acted[0]),),
        )
        resolved = self.transitions(episode(), 0)
        self.assertTrue(
            any("counterfactual" in transition for transition in resolved),
            "the control: the resolved hand of the battery's own episode does carry the "
            "key, so the absence above is about that hand and not about the step "
            "(counterfactual.md §4): %r" % ([sorted(t) for t in resolved],),
        )


if __name__ == "__main__":
    unittest.main()
