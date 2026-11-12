"""records.md §5, ASM-12 — one whole episode, and what its record must carry.

`docs/L2/engine/surface.md` §10 and `environment.md` §3, `records.md` §5.  A record
carries the seed unchanged, the ordered decisions — each with its own seat, the whole
ten-fact readout for that decision, its legal descriptors, the descriptor the policy
returned and the applied action's reward — and the payoffs of the completed hand,
summing to zero.  The policies are called as `policy(readout, legal_actions)` and
their answer is what is applied; the reward is the hand's outcome at a seat's last
decision and zero at every other; a seat that never acted carries no decision; and
the record names no hand handle.  The last case is D-43's resolution as the record
publishes it: each decision's `counterfactual` over its legal descriptors where the
hand's own self-check lets the arithmetic through, and `None` at every decision of a
hand it declines — one without a showdown, one whose shown hands tie, and one whose
pot was built in levels (`docs/L1/counterfactual.md` §4's last paragraph).
"""

import os
import sys
import unittest

try:
    from . import _support as S
except ImportError:
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _support as S  # noqa: E402


#: The all-in band both uncapped shapes declare as one of their four raise descriptors
#: (`sizing.md` §2, §3): the band that commits the seat's whole stack, so a seating holding
#: the policy below puts one stack's worth of chips in and never a slice of one.
ALL_IN_BAND = "raise-all-in"

#: The six-seat sample this case plays: the battery's four six-seat seeds and a range of the
#: writer's own, each played under two seatings, so the sample is an invented instance of the
#: writer's and not a scan for a hand of levels (D-15, `battery.md` §4).
LEVELS_SEEDS = tuple(S.SEEDS_SIX) + tuple(range(40))

#: The two-seat hands the same arithmetic is checked on, one pair per two-seat row, so a
#: resolved hand of a two-seat shape is measured by the same clauses (`shapes.md` §2,
#: `seats.md` §2).
LEVELS_TWO_SEAT = (
    (S.SHAPE_DEFAULT, S.SEED_A),
    (S.SHAPE_DEFAULT, S.SEED_F),
    (S.SHAPE_SIZED, S.SEED_Q),
    (S.SHAPE_SIZED, S.SEED_S),
)


def all_in(readout, legal):
    """A policy that puts the seat all-in whenever that band is legal, and calls otherwise.

    Both uncapped rows declare the all-in as one of their four raise bands (`sizing.md` §2,
    §3), so a seat holding this policy commits one stack's worth of chips whenever it can:
    that is the only all-in a declared shape can produce, and the one a pot built in levels
    would need two of (`counterfactual.md` §4's last paragraph).
    """
    return ALL_IN_BAND if ALL_IN_BAND in legal else S.choose_call(readout, legal)


class Episode(S.EngineCase):
    """The episode record, decision by decision."""

    def test_episode_01_the_record_carries_the_three_required_keys(self):
        """§5 the record carries `seed`, `decisions` and `payoffs`."""
        episode = self.play_hand(
            S.SEED_A, S.PolicyProbe(S.choose_raise, name="seat 0"),
            S.PolicyProbe(S.choose_call, name="seat 1"),
        )
        self.assertTrue(S.is_mapping(episode), "play_hand returns one mapping (records.md §5)")
        for fact in S.EPISODE_FACTS:
            S.required(episode, "the episode record of play_hand", fact)
        decisions = S.decision_list(episode)
        self.assertTrue(
            decisions,
            "an episode of a hand with at least one decision records it (records.md §5, "
            "environment.md §1)",
        )
        S.seat_keyed(
            S.required(episode, "the episode record of play_hand", "payoffs"),
            "the episode's payoffs",
        )

    def test_episode_02_every_decision_carries_its_five_facts(self):
        """§5 each decision carries seat, readout, legal, action and reward."""
        episode = self.play_hand(
            S.SEED_B, S.PolicyProbe(S.choose_raise, name="seat 0"),
            S.PolicyProbe(S.choose_call, name="seat 1"),
        )
        decisions = S.decision_list(episode)
        self.assertTrue(
            decisions, "an episode of this game records at least one decision (records.md §5)")
        for position, decision in enumerate(decisions):
            for fact in S.DECISION_FACTS:
                S.decision_fact(decision, fact)
            readout = S.decision_fact(decision, "readout")
            self.assertEqual(
                set(readout), set(S.READOUT_FACTS),
                "the decision's readout is the whole ten-fact mapping of that decision "
                "(environment.md §3, D-3): decision %d carried %r"
                % (position, sorted(str(key) for key in readout)),
            )
            self.assertEqual(
                len(readout["history"]), position,
                "the decisions are ordered in the order they were taken (records.md §5): "
                "decision %d read a history of %d actions" % (position, len(readout["history"])),
            )
            index, _ = S.seat_fact(S.decision_fact(decision, "seat"))
            readout_index, _ = S.seat_fact(readout["seat"])
            self.assertEqual(
                index, readout_index,
                "a decision's seat is that decision's own acting seat, in the shape of the "
                "seat fact (environment.md §3): decision %d said %r against %r"
                % (position, index, readout_index),
            )
            self.assertTrue(
                S.is_number(S.decision_fact(decision, "reward")),
                "a reward is a number (records.md §5): decision %d read %r"
                % (position, S.decision_fact(decision, "reward")),
            )

    def test_episode_03_the_policies_are_called_with_the_readout_and_the_legal_descriptors(self):
        """§10 the engine asks a policy with (readout, legal) and applies its answer."""
        seed = S.SEED_C
        seat0 = S.PolicyProbe(S.choose_raise, name="seat 0")
        seat1 = S.PolicyProbe(S.choose_call, name="seat 1")
        episode = self.play_hand(seed, seat0, seat1)
        decisions = S.decision_list(episode)
        taken = {0: 0, 1: 0}
        for position, decision in enumerate(decisions):
            index, _ = S.seat_fact(S.decision_fact(decision, "seat"))
            probe = seat0 if index == 0 else seat1
            self.assertLess(
                taken[index], len(probe.calls),
                "decision %d of seat %d has no matching policy call, so the engine did not "
                "ask that seat's policy for it (surface.md §10)" % (position, index),
            )
            call = probe.calls[taken[index]]
            taken[index] += 1
            self.assertEqual(
                S.canon(S.decision_fact(decision, "readout")), S.canon(call["readout"]),
                "the decision's readout is the one its policy was called with "
                "(environment.md §3): decision %d differed" % (position,),
            )
            self.assertTrue(
                S.descriptors_equal(S.decision_fact(decision, "legal"), call["legal"]),
                "the decision's legal list is the list its policy was called with "
                "(environment.md §3): decision %d differed" % (position,),
            )
            self.assertTrue(
                S.same_descriptor(
                    S.decision_fact(decision, "action"), call["action"]
                ),
                "the descriptor the record carries is the one the policy returned and the "
                "engine applied (surface.md §10): decision %d recorded %r against %r"
                % (position, S.decision_fact(decision, "action"), call["action"]),
            )
        self.assertEqual(
            taken[0], len(seat0.calls),
            "the engine asks the seat's policy once per decision it takes (surface.md §10)",
        )
        self.assertEqual(taken[1], len(seat1.calls), "the engine asks one policy per decision")
        self.assertGreaterEqual(
            taken[0] + taken[1], 2, "an episode played by these policies has both seats acting"
        )

    def test_episode_04_the_decisions_are_ordered_and_one_step_apart(self):
        """§10 the decisions are the hand's steps, in order, one action each."""
        seed = S.SEED_D
        seat0 = S.PolicyProbe(S.choose_raise, name="seat 0")
        seat1 = S.PolicyProbe(S.choose_call, name="seat 1")
        episode = self.play_hand(seed, seat0, seat1)
        decisions = S.decision_list(episode)
        hand = self.new_hand(seed)
        for position, decision in enumerate(decisions):
            readout = self.readout(hand)
            self.assertEqual(
                S.canon(readout["history"]),
                S.canon(S.decision_fact(decision, "readout")["history"]),
                "decision %d records the history the hand had when it was taken "
                "(records.md §5, surface.md §7)" % (position,),
            )
            hand = self.apply_action(hand, S.decision_fact(decision, "action"))
        self.assertTrue(
            self.is_terminal(hand),
            "the episode's decisions play that seed's hand to its end (surface.md §10)",
        )

    def test_episode_05_its_payoffs_are_the_completed_hand_s_payoffs(self):
        """§10 the record's payoffs are the payoffs of that completed hand."""
        seed = S.SEED_E
        seat0 = S.PolicyProbe(S.choose_raise, name="seat 0")
        seat1 = S.PolicyProbe(S.choose_call, name="seat 1")
        episode = self.play_hand(seed, seat0, seat1)
        hand = self.new_hand(seed)
        for decision in S.decision_list(episode):
            hand = self.apply_action(hand, S.decision_fact(decision, "action"))
        self.assertTrue(self.is_terminal(hand), "the replayed hand is over (surface.md §10)")
        recorded = S.seat_keyed(
            S.required(episode, "the episode record of play_hand", "payoffs"),
            "the episode's payoffs",
        )
        returned = S.seat_keyed(
            self.payoffs(hand), "payoffs of the hand the episode played"
        )
        self.assertEqual(
            S.canon(recorded), S.canon(returned),
            "the episode's payoffs are the same record payoffs returns for that completed "
            "hand (records.md §5, environment.md §3): %r against %r"
            % (recorded, returned),
        )
        self.assertAlmostEqual(
            float(sum(recorded.values())), 0.0, places=9,
            msg="an episode's payoffs sum to zero (records.md §5, ASM-12): %r" % (recorded,),
        )

    def test_episode_06_rewards_are_the_outcome_at_each_seat_s_last_decision(self):
        """§10 reward is the seat's net delta at its last decision and zero elsewhere."""
        seed = S.SEED_F
        episode = self.play_hand(
            seed, S.PolicyProbe(S.choose_raise, name="seat 0"),
            S.PolicyProbe(S.choose_call, name="seat 1"),
        )
        decisions = S.decision_list(episode)
        self.assertTrue(
            decisions,
            "an episode of this game records the decisions its seats took (records.md §5)",
        )
        payoffs = S.seat_keyed(
            S.required(episode, "the episode record of play_hand", "payoffs"),
            "the episode's payoffs",
        )
        for index in (0, 1):
            owned = [
                (position, float(S.decision_fact(decision, "reward")))
                for position, decision in enumerate(decisions)
                if S.seat_fact(S.decision_fact(decision, "seat"))[0] == index
            ]
            if not owned:
                continue
            non_zero = [(position, reward) for position, reward in owned if reward != 0.0]
            self.assertLessEqual(
                len(non_zero), 1,
                "a seat carries at most one non-zero reward (records.md §5, ASM-12): "
                "seat %r carried %r" % (index, non_zero),
            )
            self.assertAlmostEqual(
                float(sum(reward for _, reward in owned)), float(payoffs[index]),
                places=9,
                msg="a seat's rewards are the hand's net chip delta and nothing else "
                    "(ASM-12): seat %r carried %r against a payoff of %r"
                    % (index, owned, payoffs[index]),
            )
            if non_zero:
                self.assertEqual(
                    non_zero[0][0], owned[-1][0],
                    "the non-zero reward sits at that seat's last decision (records.md §5, "
                    "ASM-12): seat %r carried %r and last acted at decision %d"
                    % (index, non_zero, owned[-1][0]),
                )

    def test_episode_07_a_seat_that_never_acted_carries_no_decision(self):
        """§3 a seat that never acted carries no decision and therefore no reward."""
        seed = S.SEED_G
        seat0 = S.PolicyProbe(S.choose_fold, name="seat 0")
        seat1 = S.PolicyProbe(S.choose_call, name="seat 1")
        episode = self.play_hand(seed, seat0, seat1)
        decisions = S.decision_list(episode)
        self.assertGreaterEqual(
            len(decisions), 1,
            "the button acts first preflop and folds, so the hand records one decision "
            "(environment.md §1)",
        )
        for position, decision in enumerate(decisions):
            index, _ = S.seat_fact(S.decision_fact(decision, "seat"))
            self.assertEqual(
                index, 0,
                "the big blind never acts when the button folds preflop, so no decision "
                "belongs to it (environment.md §3): decision %d named seat %r"
                % (position, index),
            )
        self.assertEqual(
            seat1.calls, [],
            "a seat that never acts is never asked for a decision (environment.md §3)",
        )
        payoffs = S.seat_keyed(
            S.required(episode, "the episode record of play_hand", "payoffs"),
            "the episode's payoffs",
        )
        self.assertAlmostEqual(
            float(payoffs[0]), -float(S.SMALL_BLIND), places=9,
            msg="the button folds after posting the small blind, so it loses it "
                "(environment.md §1): %r" % (payoffs,),
        )
        self.assertAlmostEqual(
            float(payoffs[1]), float(S.SMALL_BLIND), places=9,
            msg="the big blind wins the small blind and the two sum to zero (ASM-12): %r"
                % (payoffs,),
        )

    def test_episode_08_the_seed_is_unchanged_and_the_decisions_are_recorded(self):
        """§10 the record's seed is the seed the call was made with, unchanged."""
        for seed in (S.SEED_H, S.SEED_I):
            episode = self.play_hand(
                seed, S.PolicyProbe(S.choose_raise, name="seat 0"),
                S.PolicyProbe(S.choose_call, name="seat 1"),
            )
            recorded = S.required(episode, "the episode record of play_hand", "seed")
            self.assertEqual(
                recorded, seed,
                "the record carries the seed the call was made with, unchanged "
                "(records.md §5): %r for seed %r" % (recorded, seed),
            )
            self.assertTrue(
                S.decision_list(episode),
                "one seed deals one hand, so its episode records the decisions taken "
                "(records.md §5)",
            )

    def test_episode_09_the_record_exposes_no_hand_handle(self):
        """§10 the record names no hand handle, because nothing below an entry point is surface."""
        episode = self.play_hand(
            S.SEED_J, S.PolicyProbe(S.choose_raise, name="seat 0"),
            S.PolicyProbe(S.choose_call, name="seat 1"),
        )
        for value in S.leaves(episode):
            if isinstance(value, (str, bytes, int, float, bool, type(None))):
                continue
            self.assert_refused(
                lambda value=value: self.is_terminal(value),
                "is_terminal on a value the episode record exposes",
                ("hand", "handle"),
            )
            self.assert_refused(
                lambda value=value: self.readout(value),
                "readout on a value the episode record exposes",
                ("hand", "handle", "over", "terminal"),
            )

    def test_episode_10_a_bad_policy_is_refused_or_its_error_propagates(self):
        """§10 a non-callable policy and an illegal answer are refused; an error propagates."""
        seed = S.SEED_K
        good = S.PolicyProbe(name="the battery's other seat")
        for bad in (None, 7, "a policy", {}, object()):
            self.assert_refused(
                lambda bad=bad: self.play_hand(seed, bad, good),
                "play_hand with a seat-0 policy that is not callable (%r)" % (bad,),
                ("policy", "callable"),
            )
            self.assert_refused(
                lambda bad=bad: self.play_hand(seed, good, bad),
                "play_hand with a seat-1 policy that is not callable (%r)" % (bad,),
                ("policy", "callable"),
            )
        fold = self.fold_descriptor(self.legal_actions(self.new_hand(seed)))
        self.assert_refused(
            lambda: self.play_hand(seed, S.FoldWhenFree(fold), good),
            "play_hand with a policy that answers a free decision with a fold",
            ("legal", "action", "descriptor"),
        )
        self.assert_refused(
            lambda: self.play_hand(seed, S.IllegalAnswer(), good),
            "play_hand with a policy whose answer names no action of the decision",
            ("legal", "action", "descriptor"),
        )
        try:
            self.play_hand(seed, S.ExplodingPolicy(), good)
        except S.PolicyFailure as exc:
            self.assertIn(
                "refuses to choose", str(exc),
                "the policy's own exception propagates unchanged (surface.md §10)",
            )
        except Exception as exc:
            self.fail(
                "play_hand must not catch a policy's own exception and turn it into an "
                "action (surface.md §10); it raised %s: %s"
                % (type(exc).__name__, exc)
            )
        else:
            self.fail(
                "play_hand returned a record for a policy that raised (surface.md §10)"
            )

    def test_episode_11_a_pot_built_in_levels_carries_no_ledger(self):
        """§5 a hand whose pot was built in levels carries `counterfactual` `None` at every decision, and every hand that does carry values satisfies the invariant at each of its decisions (`docs/L3/engine/episode.md` §5, `docs/L3/engine/episode-battery.md` §4, `docs/L1/counterfactual.md` §4's last paragraph).

        The third case the resolution declines is the arithmetic's own **self-check**:
        `payoffs(hand)`'s mapping is handed to it, and the arithmetic is taken only when,
        for every seat, the chips that seat took from the pot — its `payoffs` plus its
        whole-hand contribution — are exactly `0` or exactly the pot.  The case therefore
        recomputes every seat's contribution from the record alone, `s_0 − stacks[s]` at
        the last decision with that decision's own applied commitment restored, and asserts
        the rule in both directions: a hand whose takes lie outside `{0, pot}` carries no
        ledger at any of its decisions, and a hand that carries one satisfies
        `v(action) = payoffs[seat]` at every decision, with every legal descriptor valued
        and no illegal one.  The premise the guard rests on is measured and never skipped:
        every seat starts a hand with one stack's worth of chips and there is no ante, so
        a live seat's all-in commits the whole stack and the pot is not built in levels —
        and the hands a shared pot pays are named by the clause that finds them.  Both
        branches are exercised, so neither clause passes by not happening.
        """
        sample = [
            (S.SHAPE_SIX, seed, mixed)
            for seed in LEVELS_SEEDS
            for mixed in (False, True)
        ] + [(shape, seed, False) for shape, seed in LEVELS_TWO_SEAT]
        played = 0
        resolved = 0
        ledgerless = 0
        checked = 0
        outside = []
        levels = []
        missing = []
        uneven = []
        for shape, seed, mixed in sample:
            seats = S.SHAPE_SEATS[shape]
            if mixed:
                # Half the seats go all-in whenever the band is legal, so the sample reaches
                # the all-in a six-seat table can produce (`sizing.md` §2, `seats.md` §4).
                seating = tuple(
                    (S.choose_call, all_in)[(seed + seat) % 2] for seat in range(seats)
                )
            else:
                seating = S.seating(shape, S.choose_call)
            episode = self.seated_play_hand(seed, seating, shape)
            decisions = S.decision_list(episode)
            played += 1
            start = int(self.game_config(shape)["starting_stack"])
            payoffs = S.seat_keyed(
                S.required(episode, "the episode record of play_hand", "payoffs"),
                "the episode's payoffs",
                seats,
            )
            reveal = S.required(episode, "the episode record of play_hand", "reveal")
            # `counterfactual.md` §4's contribution, recomputed from the record and never
            # taken from a helper below an entry point: `C = s_0 − stacks[s]` at the **last**
            # decision, with that decision's own applied commitment restored — `to_call` for
            # the check/call descriptor and nothing for a fold (`episode.md` §5).
            last = decisions[-1]
            final = last["readout"]["stacks"]
            contribution = {seat: start - int(final[seat]) for seat in range(seats)}
            taken = last["action"]
            kind = S.descriptor_kind(taken)
            self.assertNotEqual(
                kind,
                "raise",
                "seed %r's hand ended on the raise descriptor %r, and a raise cannot close a "
                "hand: this case restores the last decision's own commitment, so its sample "
                "must end on a fold or a check/call (episode.md §5, counterfactual.md §4)"
                % (seed, taken),
            )
            last_seat, _button = S.seat_fact(last["seat"])
            if kind == "check-call":
                contribution[last_seat] += int(
                    S.one_number(last["readout"]["to_call"], "the readout's to_call fact")
                )
            pot = sum(contribution.values())
            take = {
                seat: int(payoffs[seat]) + contribution[seat] for seat in range(seats)
            }
            winnings_is_whole_or_nothing = all(
                value in (0, pot) for value in take.values()
            )
            ledgers = [
                S.decision_fact(decision, "counterfactual") for decision in decisions
            ]
            showdown = bool(reveal["showdown"])
            split = bool(reveal["split"])
            # Every seat the reveal says was never folded, and what each of them committed: a
            # hand of levels is one where a live seat committed fewer chips than another
            # (`counterfactual.md` §4's last paragraph, `episode.md` §5).
            live_chips = set()
            for entry in reveal["seats"]:
                if S.required(entry, "a seat entry of the reveal", "shown"):
                    live_chips.add(
                        contribution[
                            S.required(entry, "a seat entry of the reveal", "seat")
                        ]
                    )
            if len(live_chips) > 1:
                uneven.append((shape, seed, sorted(live_chips), contribution))

            if not winnings_is_whole_or_nothing:
                outside.append((shape, seed, pot, take))
                for position, ledger in enumerate(ledgers):
                    self.assertIsNone(
                        ledger,
                        "seed %r's hand pays %r out of a pot of %d, so some seat's take is "
                        "neither zero nor the whole pot, and a pot built in levels carries no "
                        "ledger at any decision of the hand — but decision %d carries %r.  The "
                        "%d hand(s) of this sample outside {0, pot} are %r on their shape and "
                        "their seed (docs/L1/counterfactual.md §4's last paragraph, "
                        "docs/L3/engine/episode.md §5)"
                        % (
                            seed,
                            take,
                            pot,
                            position,
                            ledger,
                            len(outside),
                            [(one_shape, one_seed) for one_shape, one_seed, _p, _t in outside],
                        ),
                    )
                # §4's second declined hand, and the one these hands are: a shared pot pays
                # two or more seats and together they take exactly the pot.  A hand of levels
                # pays a seat by its eligibility, so one would be named right here.
                paid = sorted(value for value in take.values() if value > 0)
                self.assertGreaterEqual(
                    len(paid),
                    2,
                    "seed %r's hand pays %d seat(s) %r out of a pot of %d, and the only hand "
                    "§4 declines for its pot alone is one built in levels — a seat paid by its "
                    "eligibility as well as by its rank.  Report the seed, its payoffs and its "
                    "per-seat contributions (docs/L1/counterfactual.md §4's last paragraph)"
                    % (seed, len(paid), paid, pot),
                )
                self.assertEqual(
                    sum(paid),
                    pot,
                    "seed %r's hand pays %r out of a pot of %d: what its seats took from the "
                    "pot is the pot and nothing else (docs/L1/counterfactual.md §4, "
                    "docs/L3/engine/episode.md §5)" % (seed, paid, pot),
                )

            if any(ledger is not None for ledger in ledgers):
                resolved += 1
                for position, (decision, ledger) in enumerate(zip(decisions, ledgers)):
                    self.assertTrue(
                        S.is_mapping(ledger),
                        "seed %r's hand carries values and its decision %d carries %r: a hand "
                        "resolves every one of its decisions or none of them "
                        "(docs/L3/engine/episode.md §5)"
                        % (seed, position, ledger),
                    )
                    legal = S.decision_fact(decision, "legal")
                    self.assertEqual(
                        {S.canon(key) for key in ledger},
                        {S.canon(descriptor) for descriptor in legal},
                        "decision %d of seed %r's hand values %r and its legal descriptors are "
                        "%r: a resolution maps exactly the decision's legal descriptors, with "
                        "no illegal index valued and no legal index missing "
                        "(docs/L3/engine/episode-battery.md §4, "
                        "docs/L1/counterfactual.md §5)"
                        % (position, seed, sorted(ledger, key=repr), tuple(legal)),
                    )
                    for descriptor, value in ledger.items():
                        self.assertTrue(
                            S.is_number(value),
                            "decision %d of seed %r's hand values the legal descriptor %r as "
                            "%r: every legal index of a resolved decision carries a number "
                            "(docs/L1/counterfactual.md §4, §5)"
                            % (position, seed, descriptor, value),
                        )
                    owner, _flag = S.seat_fact(S.decision_fact(decision, "seat"))
                    applied = S.decision_fact(decision, "action")
                    at_applied = [
                        value
                        for descriptor, value in ledger.items()
                        if S.canon(descriptor) == S.canon(applied)
                    ]
                    self.assertEqual(
                        len(at_applied),
                        1,
                        "decision %d of seed %r's hand applied %r and its resolution values "
                        "%r: the applied descriptor is one of that decision's legal "
                        "descriptors and carries exactly one value "
                        "(docs/L1/counterfactual.md §4, §5)"
                        % (position, seed, applied, sorted(ledger, key=repr)),
                    )
                    self.assertAlmostEqual(
                        float(at_applied[0]),
                        float(payoffs[owner]),
                        places=9,
                        msg="decision %d of seed %r's hand values the descriptor it applied, "
                            "%r, at %r while that seat's realised delta is %r: the value at the "
                            "applied descriptor equals `payoffs[seat]` at every decision of a "
                            "resolved hand (docs/L1/counterfactual.md §4, "
                            "docs/L3/engine/episode.md §5, "
                            "docs/L3/engine/episode-battery.md §4)"
                            % (
                                position,
                                seed,
                                applied,
                                float(at_applied[0]),
                                float(payoffs[owner]),
                            ),
                    )
                    checked += 1
            else:
                ledgerless += 1
            if showdown and not split and not winnings_is_whole_or_nothing:
                levels.append((shape, seed, pot, take, contribution))
            if showdown and not split and not any(
                ledger is not None for ledger in ledgers
            ):
                missing.append((shape, seed))

        # The premise the guard rests on, measured and never skipped: every seat starts a
        # hand with one stack's worth of chips and there is no ante, so a live seat's all-in
        # commits the whole stack — every seat still live at the end put in the same chips —
        # and no seat is paid by its eligibility as well as by its rank
        # (`counterfactual.md` §4's last paragraph, `episode.md` §5).
        self.assertEqual(
            uneven,
            [],
            "these hands left the seats that never folded holding unequal numbers of chips "
            "(%r, as shape, seed, the distinct chip counts and the per-seat contributions): a "
            "seat that committed fewer chips than another live seat is an all-in for less, "
            "which is what builds a pot in levels.  Every seat starts a hand with one stack's "
            "worth of chips and there is no ante, so a live seat's all-in commits the whole "
            "stack and the pot is not built in levels (docs/L1/counterfactual.md §4's last "
            "paragraph)" % (uneven,),
        )
        self.assertEqual(
            levels,
            [],
            "%d hand(s) of the %d played — %d carrying values, %d carrying none, %d decisions "
            "checked — reached a showdown that is not a split and paid a seat neither zero nor "
            "the whole pot: %r.  Every seat starts a hand with one stack's worth of chips and "
            "there is no ante, so a live seat's all-in commits the whole stack and the pot is "
            "not built in levels — the guard is latent on the declared shapes, and this case "
            "asserts the predicate it rests on rather than skipping the branch "
            "(docs/L3/engine/episode.md §5, docs/L1/counterfactual.md §4's last paragraph)"
            % (len(levels), played, resolved, ledgerless, checked, levels),
        )
        self.assertEqual(
            missing,
            [],
            "these hands (as shape and seed) reached a showdown that is not a split, took "
            "every seat's winnings out of the whole pot, and still carry no ledger at any "
            "decision: %r.  The self-check is the only thing between such a hand and its "
            "values, so of the %d hands played (%d carrying values, %d carrying none) every "
            "hand the check lets through must be resolved (docs/L3/engine/episode.md §5, "
            "docs/L3/engine/episode-battery.md §4)"
            % (missing, played, resolved, ledgerless),
        )
        # Neither clause passes by not happening: the sample holds both kinds of hand.
        self.assertGreaterEqual(
            resolved,
            1,
            "none of the %d hands played carried a single value (%d carried none, %d decisions "
            "checked, %r lay outside {0, pot}): clause 2 and the invariant it asserts passed "
            "by not happening (docs/L3/engine/episode-battery.md §4)"
            % (played, ledgerless, checked, outside),
        )
        self.assertGreaterEqual(
            ledgerless,
            1,
            "all %d hands played carried values (%d decisions checked): the `None` branch the "
            "fallback of docs/L1/counterfactual.md §4's last paragraph lives in was never "
            "taken, so clause 1 passed by not happening"
            % (played, checked),
        )


if __name__ == "__main__":
    unittest.main()
