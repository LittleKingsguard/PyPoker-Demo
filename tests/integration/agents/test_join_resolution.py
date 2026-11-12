"""JOIN-AGT-16 — the resolution reaches the learner (D-43).

`docs/L1/counterfactual.md` §2 gives the records **one resolution** and the readout
**nothing**: `engine.play_hand`'s episode record gains a required `reveal` (the board,
whether the hand reached a showdown, whether the shown hands split, and one entry per seat
in seat order with its two cards, whether it showed and whether its cards were best of the
shown ones), each decision record gains `amounts` (every legal descriptor's resolved
raise-to) and `counterfactual` (every legal descriptor's whole-hand net chip delta for the
acting seat), and `records.md` §4 makes the transition record's `episode` **required** and
its `counterfactual` conditional on the hand having resolved.  The readout keeps its eleven
facts, so a learner's observation is the observation it had before (`counterfactual.md` §2,
§4, §6, FAM-22, D-43).

At the join that is four chains, and this file drives one case each — always through an
entry point and never past one:

- **16.1** the resolution reaches `agents.learn`: a real resolved hand's decisions become
  the transition records `records.md` §4 declares — `episode` the episode's seed, and a
  length-`A` `counterfactual` carrying each legal index's value with `None` at every other —
  and `learn` on a learner built under `reveal-counterfactual` accepts the batch, counts it
  and answers a finite signal, while the same record with its `episode` removed and one
  carrying a value at an illegal index are each refused **by name** (`counterfactual.md`
  §2, §4, §5, `records.md` §4).
- **16.2** the arithmetic is **one quantity**: at the descriptor the hand applied, the
  engine's branch value is the seat's realised net chip delta, under both catalogue
  utilities, on `fixed-limit-20` and on `six-seat-no-limit-100`, at **every** decision of
  the hand and not only the seat's last (`counterfactual.md` §4).
- **16.3** the member is in the container and in the population: a `reveal-counterfactual`
  learner's `agents.save` writes **format version 5** with the required field, a `none`
  learner writes version 3 with no such field, `agents.load(None, path)` restores the member
  the file records, and `evaluation.policy_from` reports the members that file records
  (`counterfactual.md` §6, §9, `records.md` §7, `docs/L3/agents/rule.md` §8).
- **16.4** nothing reaches an observation: the readout is the closed eleven at every
  decision, an encoder's `fields` is the same subset of them for every declared encoding,
  the readout a policy is handed is the readout the record keeps, and no other seat's hole
  cards are in the acting seat's observation (`counterfactual.md` §2, `readout.md` §4,
  `e2e-surface.md` §2, D-3).

Every seed, checkpoint name, width and depth below is this battery's own and appears in no
design document (`docs/L1/battery.md` §4, D-15); the catalogue names, the shapes and the
utilities are read off `agents.learners()` and `engine.game_shapes()` and never restated.
A resolved hand at the default shape costs milliseconds and one at six seats a fraction of
a second, so every case plays its own deals rather than sharing one (`battery.md` §2).
"""

import importlib.util
import math
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

#: The two catalogue members D-43 adds (`counterfactual.md` §6): `none` is the first and
#: the declared default, `reveal-counterfactual` the member whose residual is the
#: transition's own whole-hand values.  The catalogue itself is always read off
#: `agents.learners()` in the case; these are the names a case must spell to a call.
DEFAULT_COUNTERFACTUAL = "none"
REVEAL_COUNTERFACTUAL = "reveal-counterfactual"

#: The format version a non-default member's container writes (`counterfactual.md` §6,
#: `records.md` §7) and the one a `none` learner keeps on the default shape
#: (`docs/L3/agents/checkpoint.md` §3).
COUNTERFACTUAL_FORMAT_VERSION = 5
DEFAULT_FORMAT_VERSION = 3

#: The invented deals this file plays (`docs/L1/battery.md` §4, D-15): one two-seat hand and
#: one six-seat hand, both of which reach a river showdown with no split pot, so every
#: decision of them resolves (`counterfactual.md` §4).
SHOWDOWN_DEAL = 64187
SIX_SEAT_DEAL = 41357

#: The invented baseline and policy seeds (`docs/L1/battery.md` §4, D-15): none of them is a
#: deal of a design document, of the e2e battery or of a sibling integration battery.
BASELINE_SEED = 31733
BASELINE_SEED_OTHER = 50287

#: The invented learner, container and width facts this file builds (D-15).
LEARNER_SEED = 73309
POLICY_SEED = 26417
WIDTH = 10
DEPTH = 2
CHECKPOINT_REVEAL = "join-invented-resolution-reveal.ckpt"
CHECKPOINT_PLAIN = "join-invented-resolution-plain.ckpt"

#: The exploration mode `evaluation.policy_from` takes by default (`sizing.md` §4).
EXPLORATION = "schedule"


def flatten(value):
    """One value as text, recursively, so a card spelling is searchable in a record.

    The readout is a mapping of tuples and scalars and a card is a two-character spelling
    inside a tuple of them; flattening the record's own values is how a case states that a
    fact is **absent** from it without inventing a second spelling of the record
    (`docs/L2/engine/surface.md` §5, `counterfactual.md` §2).
    """
    if isinstance(value, dict):
        return " ".join("%s %s" % (key, flatten(item)) for key, item in value.items())
    if isinstance(value, (tuple, list, set)):
        return " ".join(flatten(item) for item in value)
    return str(value)


class ResolutionAtTheJoin(J.JoinCase):
    """One real resolved hand, its resolution, and the learner on the other side of it."""

    # ------------------------------------------------------------------
    # Readers this file builds its records with
    # ------------------------------------------------------------------
    def resolved_episode(self, seed, shape=None):
        """One real hand that reaches a river showdown, played by `always-call` baselines.

        The hand is dealt and played through `engine.play_hand` at an invented seed, on the
        named shape or on the default one by absence (`e2e-surface.md` §3.1), with one
        `always-call` baseline per seat so that nobody folds and two or more seats show.  The
        case then holds D-43's own preconditions: a showdown, and no split pot — the state in
        which the reveal resolves every decision of the hand (`counterfactual.md` §4, §5,
        `records.md` §5).
        """
        seats = int(J.shape_row(shape)["seats"])
        policies = [
            J.build_baseline("always-call", BASELINE_SEED + index)
            for index in range(seats)
        ]
        if shape is None:
            record = J.play_hand(seed, policies[0], policies[1])
        else:
            record = J.seated_play_hand(seed, policies, shape)
        reveal = J.episode_reveal(record)
        self.assertTrue(
            bool(reveal["showdown"]),
            "the case's hand must reach a showdown, because a hand that ended without one "
            "resolves nothing and the case would assert the fallback instead of the "
            "resolution (counterfactual.md §4): the reveal of seed %r reads %r"
            % (seed, reveal),
        )
        self.assertFalse(
            bool(reveal["split"]),
            "and its shown hands must not tie for best, because a split pot is one of the "
            "kinds of hand §4 resolves nothing in — the reveal carries `split: true` and "
            "every decision's `counterfactual` is `None` (counterfactual.md §4, records.md "
            "§5): %r" % (reveal,),
        )
        return record

    def transition_batch(self, record, seat, encoder, transform=None, shape=None):
        """The seat's decisions as `records.md` §4's transitions, in decision order.

        Each record carries the two encoded observations, the chosen index, the reward the
        engine placed at that seat's **terminal** decision and `0.0` elsewhere, the two legal
        index sequences, `episode` — the episode's own `seed`, required of every transition —
        and `counterfactual`, a tuple of length `A`, the shape's descriptor count, holding
        the decision's value at each of its **legal** indices and `None` at every other
        (`records.md` §4, `counterfactual.md` §2, §4, §5).  The engine's value is keyed by
        descriptor and this record is keyed by index, so the alignment is
        `features.legal_indices`' and never a second reading of the vocabulary
        (`e2e-surface.md` §2, `sizing.md` §3).  `transform` re-expresses a chip delta as the
        utility's reward, which is the one thing the step that builds transitions adds
        (`records.md` §4, `utilities.md` §4).
        """
        decisions = [
            decision
            for decision in J.episode_decisions(record)
            if J.decision_seat(decision) == int(seat)
        ]
        boundary = int(J.episode_seed(record))
        self.assertTrue(
            decisions,
            "the learner's seat must have acted in the hand, or there is no transition to "
            "build (records.md §5, docs/L3/training/episode.md §3): seat %r at seed %r"
            % (seat, boundary),
        )
        payoffs = J.episode_payoffs(record)
        # `A` is read off the vocabulary of the shape the batch belongs to — the caller's,
        # absence being the default shape — and never written down here (`sizing.md` §6).
        count = J.head_width(shape)
        out = []
        for position, decision in enumerate(decisions):
            last = position + 1 == len(decisions)
            successor = decision if last else decisions[position + 1]
            legal = list(J.decision_legal(decision))
            indices = list(J.legal_indices(legal))
            branch = J.decision_counterfactual(decision)
            self.assertIsNotNone(
                branch,
                "this hand resolved, so every one of its decisions carries the "
                "`counterfactual` mapping `records.md` §5 requires of it "
                "(counterfactual.md §4, §5): decision %d of seat %r at seed %r"
                % (position, seat, boundary),
            )
            values = [None] * count
            for slot, descriptor in enumerate(legal):
                value = branch[descriptor]
                values[indices[slot]] = value if transform is None else transform(value)
            reward = payoffs[int(seat)] if last else 0.0
            out.append(
                {
                    "observation": J.encode(encoder, J.decision_readout(decision)),
                    "next_observation": J.encode(
                        encoder, J.decision_readout(successor)
                    ),
                    "action": indices[legal.index(J.decision_action(decision))],
                    "reward": reward if transform is None else transform(reward),
                    "terminal": last,
                    "legal": indices,
                    "next_legal": list(J.legal_indices(J.decision_legal(successor))),
                    "episode": boundary,
                    "counterfactual": tuple(values),
                }
            )
        return out

    def revealed_learner(self, encoder):
        """A learner built under the catalogue's second member (`counterfactual.md` §6)."""
        member = J.counterfactual_names()[1]
        spec = J.learner_spec("naive-stack", WIDTH, DEPTH, LEARNER_SEED)
        spec["encoder"] = encoder
        spec["counterfactual"] = member
        learner = J.build_learner(spec)
        self.assertEqual(
            getattr(learner, "counterfactual", None),
            member,
            "a spec naming a counterfactual member builds the learner under it, so the "
            "member reads as the catalogue's own name (counterfactual.md §6, records.md §3, "
            "D-43): %r" % (getattr(learner, "counterfactual", None),),
        )
        return learner, member

    def utilities(self):
        """The utilities catalogue `agents.learners()` publishes, in its declared order."""
        published = J.learners()["utilities"]
        names = published.keys() if isinstance(published, dict) else published
        return tuple(str(name) for name in names)

    def transformer(self, utility, decision, shape=None):
        """The utility's transform of one chip delta, recomputed from the shape's own game.

        `records.md` §4 and `utilities.md` §2 fix the transform: `net-chips` is the delta
        itself, and `stack-shortfall` is `(U(s_0) − U(s_0 + Δ)) / U(s_0)` with
        `U(s) = (T − s)²`, `T` the chips in play and `s_0` the shape's starting stack, the
        normaliser being the shortfall a hand begins with.  The arithmetic is selected by
        the **reward token** the catalogue states for the member, so no member name is
        copied into this file.  This is a **check** of `training`'s transform and not a
        second spelling of the engine's arithmetic: the engine's job is the chip delta and
        the transform is the loop's, so recomputing it here from `engine.game_config`'s own
        numbers is what holds the two sides to one quantity (`counterfactual.md` §4,
        `utilities.md` §2, §4, D-20).
        """
        published = J.learners()["utilities"]
        token = published[str(utility)]["reward"]
        total = float(sum(decision["readout"]["stacks"]) + decision["readout"]["pot"])
        start = float(J.shape_row(shape)["starting_stack"])
        if token == "net-chip-delta":
            return lambda delta: float(delta)

        def shortfall(stack):
            return (total - float(stack)) ** 2

        before = shortfall(start)
        self.assertNotEqual(
            before,
            0.0,
            "the normaliser is the shortfall a hand begins with, which must not be zero or "
            "the transform is undefined (utilities.md §4): %r chips in play, a starting "
            "stack of %r" % (total, start),
        )
        return lambda delta: (before - shortfall(start + float(delta))) / before

    def seat_terminals(self, decisions):
        """The positions of each seat's **last** decision, which is `terminal` (§4)."""
        last = {}
        for position, decision in enumerate(decisions):
            last[J.decision_seat(decision)] = position
        return last

    # ------------------------------------------------------------------
    # JOIN-AGT-16.1 — the resolution reaches `agents.learn`
    # ------------------------------------------------------------------
    def test_join_agt_16_1_a_resolved_hand_is_a_batch_the_member_learns_from(self):
        """JOIN-AGT-16.1 a resolved hand's decisions become a learnable batch, and the two malformed records are refused by name.

        `docs/L1/records.md` §4 makes `episode` **required** of every transition and
        `counterfactual` a `tuple` of length `A` whose entry at a legal index is that
        action's whole-hand value and `None` at an index that was not legal;
        `docs/L1/counterfactual.md` §4 gives those values and §6 the member's step count.  So
        a batch built the way §4 declares it must be accepted by a learner built under
        `reveal-counterfactual`, `learn` must answer the record count and a finite signal,
        and the two records §4 forbids — one with no `episode`, one carrying a value where
        the action was illegal — must each be refused **naming the field**, which is what
        makes the boundary and the mask part of the contract rather than advice
        (`docs/L3/agents/errors.md` §3, `docs/L3/agents/rule.md` §2, FAM-22, D-43).
        """
        catalogue = J.counterfactual_names()
        self.assertEqual(
            catalogue[:2],
            (DEFAULT_COUNTERFACTUAL, REVEAL_COUNTERFACTUAL),
            "agents.learners() publishes the counterfactual catalogue in counterfactual.md "
            "§6's declared order, `none` first and the declared default, so the member this "
            "case trains under is the catalogue's own second entry (D-43): %r" % (catalogue,),
        )
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        learner, _member = self.revealed_learner(encoder)
        record = self.resolved_episode(SHOWDOWN_DEAL)
        count = J.head_width()
        self.assertEqual(
            count,
            len(J.shaped_action_space()),
            "A is the shape's descriptor count read off features.action_space, which is the "
            "length a resolution carries (counterfactual.md §5, §6, sizing.md §6): %r"
            % (count,),
        )
        batch = self.transition_batch(record, 0, encoder)
        for position, item in enumerate(batch):
            self.assertEqual(
                int(item["episode"]),
                int(J.episode_seed(record)),
                "every transition of one hand carries that episode's own seed, which is what "
                "makes an episode-scoped target expressible (records.md §4, §5, "
                "counterfactual.md §2): record %d carries %r"
                % (position, item["episode"]),
            )
            values = item["counterfactual"]
            self.assertEqual(
                len(values),
                count,
                "a resolution is one entry per descriptor of the shape, `A` and no other "
                "count (records.md §4, counterfactual.md §5, §6): %r" % (values,),
            )
            for index, value in enumerate(values):
                if index in item["legal"]:
                    self.assertIsNotNone(
                        value,
                        "this hand resolved, so every legal index of every decision carries "
                        "a value and no legal action is left unvalued (counterfactual.md §4, "
                        "§5): index %d of %r" % (index, values),
                    )
                else:
                    self.assertIsNone(
                        value,
                        "an index that was not legal carries `None`, so a masked action is "
                        "never valued and never updated (counterfactual.md §5, records.md "
                        "§4): index %d of %r" % (index, values),
                    )
        statistics = J.learn(learner, batch)
        self.assertEqual(
            int(J.transitions_consumed(statistics)),
            len(batch),
            "learn answers the record count it consumed: the member moves the update count "
            "— A steps a transition — and never the sample budget, which counts transitions "
            "(counterfactual.md §6, docs/L2/agents/surface.md §7): %r" % (statistics,),
        )
        signal = J.td_error(statistics)
        self.assertTrue(
            math.isfinite(signal),
            "the batch's signal is one finite number the curve can read, even under the "
            "member whose residual is a whole-hand chip delta (counterfactual.md §6, "
            "docs/L3/agents/rule.md §3): %r" % (signal,),
        )
        missing = {key: value for key, value in batch[0].items() if key != "episode"}
        self.assert_refusal(
            "learn",
            (("episode",),),
            lambda: J.learn(learner, [missing]),
            note="JOIN-AGT-16.1 a transition with no episode boundary",
        )
        illegal = None
        for item in batch:
            absent = [index for index in range(count) if index not in item["legal"]]
            if absent:
                illegal = (item, absent[0])
                break
        self.assertIsNotNone(
            illegal,
            "the hand must reach one decision on which a descriptor was not legal, or the "
            "mask half of §4's rule cannot be asserted on it (counterfactual.md §5, "
            "records.md §4): %r" % ([sorted(item["legal"]) for item in batch],),
        )
        item, outside = illegal
        carrying = dict(item)
        values = list(item["counterfactual"])
        values[outside] = 0.0
        carrying["counterfactual"] = tuple(values)
        self.assert_refusal(
            "learn",
            (("counterfactual",), (str(outside),)),
            lambda: J.learn(learner, [carrying]),
            note="JOIN-AGT-16.1 a resolution carrying a value at the illegal index %d"
            % (outside,),
        )

    # ------------------------------------------------------------------
    # JOIN-AGT-16.2 — the arithmetic is one quantity
    # ------------------------------------------------------------------
    def test_join_agt_16_2_the_applied_branch_is_the_realised_delta_on_both_shapes(self):
        """JOIN-AGT-16.2 at the descriptor the hand applied, the branch is the seat's realised delta, at every decision of either shape.

        `docs/L1/counterfactual.md` §4's proof: if `a` is the action the hand applied then its
        commitment **is** the realised one and its win **is** the one it won, so
        `v(a_realised) = Δ` — the seat's net chip delta, which `records.md` §5 has the engine
        place at that seat's terminal decision — **at every transition of a resolved
        episode**, not only at the seat's last; and the utility is applied to both sides by
        the same function, so the equality survives the transform (`counterfactual.md` §4,
        §6, `utilities.md` §2, §4, FAM-22, D-43).  The case plays one resolved hand on the
        default shape and one on the six-seat shape, walks **every** decision of each — each
        decision's own acting seat — and holds the engine's branch, the hand's payoffs, the
        decision's own reward where the engine placed it, and the transform of each branch
        under **both** catalogue utilities to each other.  The fold branch is checked too,
        because it is the one branch §4 values without the reveal at all (`fold → −C`).

        The transform is recomputed from `engine.game_config`'s own chips and starting stack
        (`transformer`), which is a **check** of `training`'s transform and not a second
        spelling of the engine's arithmetic: the engine's job is the chip delta, and this
        page is the one that says how a delta becomes a reward.
        """
        shapes = (None, self.shaped_rows())
        for shape in shapes:
            with self.subTest(shape=shape or J.shape_names()[0]):
                seed = SHOWDOWN_DEAL if shape is None else SIX_SEAT_DEAL
                record = self.resolved_episode(seed, shape)
                payoffs = J.episode_payoffs(record)
                start = int(J.shape_row(shape)["starting_stack"])
                count = J.head_width(shape)
                decisions = J.episode_decisions(record)
                self.assertGreaterEqual(
                    len(decisions),
                    2,
                    "the hand must hold more than one decision for the invariant to be "
                    "asserted at a decision that is not the seat's last "
                    "(counterfactual.md §4): %r decisions" % (len(decisions),),
                )
                terminals = self.seat_terminals(decisions)
                for position, decision in enumerate(decisions):
                    seat = J.decision_seat(decision)
                    branch = J.decision_counterfactual(decision)
                    applied = J.decision_action(decision)
                    legal = list(J.decision_legal(decision))
                    self.assertIsNotNone(
                        branch,
                        "a resolved hand carries a value at every one of its decisions, "
                        "which is what makes this a property of the hand and not of its last "
                        "decision (counterfactual.md §4): decision %d of seat %r at seed %r"
                        % (position, seat, seed),
                    )
                    self.assertIn(
                        applied,
                        legal,
                        "the recorded action is one of the decision's own legal "
                        "descriptors (records.md §5, docs/L3/engine/episode.md §3): %r "
                        "against %r" % (applied, legal),
                    )
                    self.assertEqual(
                        float(branch[applied]),
                        float(payoffs[seat]),
                        "the value at the descriptor the hand applied is the seat's realised "
                        "net chip delta — the number the engine placed at that seat's "
                        "terminal decision — at decision %d of seat %r on %r, and not only "
                        "at the last one (counterfactual.md §4's proof, records.md §5, "
                        "ASM-12): %r against %r"
                        % (position, seat, shape or J.shape_names()[0],
                           float(branch[applied]), float(payoffs[seat])),
                    )
                    if "fold" in legal:
                        contribution = start - int(decision["readout"]["stacks"][seat])
                        self.assertEqual(
                            float(branch["fold"]),
                            -float(contribution),
                            "a fold forfeits the pot and commits nothing further, so its "
                            "whole-hand value is the negated contribution the seat had "
                            "already made at that decision (counterfactual.md §4): %r "
                            "against %r at decision %d"
                            % (branch["fold"], -contribution, position),
                        )
                    indices = list(J.legal_indices(legal))
                    applied_index = indices[legal.index(applied)]
                    for utility in self.utilities():
                        transform = self.transformer(utility, decision, shape)
                        values = [None] * count
                        for slot, descriptor in enumerate(legal):
                            values[indices[slot]] = transform(branch[descriptor])
                        self.assertAlmostEqual(
                            float(values[applied_index]),
                            float(transform(payoffs[seat])),
                            places=12,
                            msg="the utility is applied to both sides by the same function, "
                            "so the branch at the applied action is the seat's delta under "
                            "%r too — the equality survives the transform "
                            "(counterfactual.md §4, utilities.md §2, §4, D-20): %r against "
                            "%r at decision %d of seat %r on %r"
                            % (utility, values[applied_index],
                               transform(payoffs[seat]), position, seat,
                               shape or J.shape_names()[0]),
                        )
                        if terminals[seat] == position:
                            self.assertAlmostEqual(
                                float(values[applied_index]),
                                float(transform(J.decision_reward(decision))),
                                places=12,
                                msg="at that seat's terminal decision the engine places the "
                                "hand's net chip delta, so the branch there **is** the "
                                "transition's `reward` under %r — the one decision of a hand "
                                "at which the whole-hand value and the placed reward are the "
                                "same number (counterfactual.md §4, records.md §5, "
                                "utilities.md §4): %r against %r at decision %d"
                                % (utility, values[applied_index],
                                   transform(J.decision_reward(decision)), position),
                            )
                self.assertAlmostEqual(
                    sum(float(value) for value in payoffs.values()),
                    0.0,
                    places=9,
                    msg="the payoffs the equality is held to are the hand's own and sum to "
                        "zero (records.md §5, protocol.md §2): %r" % (payoffs,),
                )

    def shaped_rows(self):
        """The catalogue's shape with more than two seats, named by the catalogue itself.

        `engine.game_shapes()` declares the six-seat row and marks it non-default; the case
        reads that row and never writes its name down, so the shape it plays is the
        catalogue's own (`shapes.md` §2, `seats.md` §2, `docs/L1/battery.md` §4, D-15).
        """
        wide = [
            name for name in J.shape_names() if int(J.shape_row(name)["seats"]) > 2
        ]
        self.assertEqual(
            len(wide),
            1,
            "the catalogue declares exactly one shape with more than two seats, which is the "
            "one this case plays the arithmetic on (seats.md §2, shapes.md §2): %r" % (wide,),
        )
        return wide[0]

    # ------------------------------------------------------------------
    # JOIN-AGT-16.3 — the member's containers and the population
    # ------------------------------------------------------------------
    def test_join_agt_16_3_the_member_is_in_the_container_and_in_the_population(self):
        """JOIN-AGT-16.3 a `reveal-counterfactual` learner writes format version 5 recording it, a `none` learner writes version 3 with no field, and every reader restores the file's member.

        `docs/L1/counterfactual.md` §6: a learner trained under a member other than `none`
        carries the name in the container — **format version 5**, a required field, versions
        1–4 read as `none` — while one under `none` writes the version it always wrote, which
        is what keeps a default save byte-identical (`records.md` §7, §9,
        `docs/L3/agents/checkpoint.md` §2.1, §3, `docs/L3/agents/rule.md` §8, FAM-22, D-43).

        The member is read where the design puts it: the container's own `metadata.json`,
        `agents.load`'s restored learner, the policy `agents.as_policy` builds — which carries
        the three catalogue members beside the game (`docs/L3/agents/rule.md` §8) — and the
        members `evaluation.policy_from` reports for that file.  It is deliberately **not**
        read off `policy_from`'s returned object as a fourth attribute: §6 declares the
        carriers to be the container, the run record and the pool member's record, and its
        scope boundary keeps the member out of every cell and matrix record in this pass,
        which is why the side `evaluation` builds carries a rule, a utility and a shape and
        no fourth name (`docs/L3/evaluation/scheduler.md` §5).  So this case holds the
        member where the contract writes it, and holds `policy_from` to the members that
        page does declare.
        """
        catalogue = J.counterfactual_names()
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        member_learner, member = self.revealed_learner(encoder)
        path = J.save(member_learner, self.checkpoint_path(CHECKPOINT_REVEAL))
        metadata = J.container_metadata(path)
        self.assertEqual(
            int(metadata["format_version"]),
            COUNTERFACTUAL_FORMAT_VERSION,
            "a learner whose counterfactual member is not `none` writes the version that "
            "records it — §6's format version 5 — so the container is the witness a pool "
            "certifies (counterfactual.md §6, records.md §7, "
            "docs/L3/agents/checkpoint.md §2.1, D-43): %r"
            % (metadata.get("format_version"),),
        )
        self.assertEqual(
            metadata.get("counterfactual"),
            member,
            "the container records the catalogue member its whole-hand targets came from, "
            "beside the rule and the utility, so a member's training targets are read off "
            "the artefact and never off a record that claims them (counterfactual.md §6, "
            "records.md §7, ASM-20, D-43): %r" % (metadata.get("counterfactual"),),
        )
        plain = J.build_learner(
            dict(
                J.learner_spec("naive-stack", WIDTH, DEPTH, LEARNER_SEED),
                encoder=encoder,
            )
        )
        self.assertEqual(
            getattr(plain, "counterfactual", None),
            catalogue[0],
            "a spec naming no counterfactual member is built under the catalogue's first — "
            "`none`, the declared default — and never under a value inferred from the "
            "caller's silence (counterfactual.md §6, records.md §3, D-43): %r"
            % (getattr(plain, "counterfactual", None),),
        )
        plain_path = J.save(plain, self.checkpoint_path(CHECKPOINT_PLAIN))
        plain_metadata = J.container_metadata(plain_path)
        self.assertEqual(
            int(plain_metadata["format_version"]),
            DEFAULT_FORMAT_VERSION,
            "a learner under `none` on the default shape writes the version it always wrote, "
            "which is what keeps a default save byte-identical to the one written before the "
            "catalogue existed (counterfactual.md §6, §9, "
            "docs/L3/agents/checkpoint.md §3): %r"
            % (plain_metadata.get("format_version"),),
        )
        self.assertNotIn(
            "counterfactual",
            plain_metadata,
            "and it writes **no** `counterfactual` field at all: absence is the member "
            "`none`, and a key nobody declared is a field the default save never had "
            "(counterfactual.md §6, §9, records.md §7, D-43): %r"
            % (sorted(plain_metadata),),
        )
        self.assertNotEqual(
            metadata.get("counterfactual"),
            plain_metadata.get("counterfactual", catalogue[0]),
            "so the two containers this case writes are two members and not one, and the "
            "difference is the field the second one lay down (counterfactual.md §6, D-43)",
        )
        restored = J.load(None, path)
        self.assertEqual(
            getattr(restored, "counterfactual", None),
            member,
            "agents.load restores the learner the file holds, member included, so a member "
            "read off a container is the file's and not the caller's claim "
            "(counterfactual.md §6, docs/L3/agents/restore.md §2-§3, D-43): %r"
            % (getattr(restored, "counterfactual", None),),
        )
        policy = J.as_policy(restored, encoder, POLICY_SEED)
        self.assertEqual(
            getattr(policy, "counterfactual", None),
            member,
            "a policy a learner builds carries the member its targets came from beside the "
            "rule and the utility, so a table can name the population it measured "
            "(docs/L3/agents/rule.md §8, counterfactual.md §6, D-43): %r"
            % (getattr(policy, "counterfactual", None),),
        )
        loaded = J.policy_from(path, EXPLORATION)
        self.assertEqual(
            getattr(loaded, "learning_rule", None),
            metadata.get("learning_rule"),
            "evaluation.policy_from reports the rule the file records, because playback is "
            "rule-free and the container is the only witness (counterfactual.md §6, "
            "records.md §7, docs/L3/evaluation/scheduler.md §5.1, D-19): %r against %r"
            % (getattr(loaded, "learning_rule", None), metadata.get("learning_rule")),
        )
        self.assertEqual(
            getattr(loaded, "utility", None),
            metadata.get("utility"),
            "and the utility on the same terms, so a table names the objectives it measured "
            "from the file and not from a claim (counterfactual.md §6, records.md §7, "
            "utilities.md §6, §7, D-20): %r against %r"
            % (getattr(loaded, "utility", None), metadata.get("utility")),
        )

    # ------------------------------------------------------------------
    # JOIN-AGT-16.4 — nothing reaches an observation
    # ------------------------------------------------------------------
    def test_join_agt_16_4_no_seat_sees_another_seats_cards_through_the_resolution(self):
        """JOIN-AGT-16.4 the readout stays the closed eleven, the encoders carry the same fields, and no other seat's cards are in the acting seat's observation.

        `docs/L1/counterfactual.md` §2's last paragraph and §9: the readout gains **nothing** —
        the eleven facts are closed, no twelfth is added, and at decision time no policy can
        reach the reveal, which is written after the hand ends.  So the case drives a resolved
        hand with a recording policy and asserts that every decision's readout carries the
        same eleven keys, that an encoder's `fields` is the same subset of them for every
        declared encoding and names none of D-43's facts, that the readout a policy was
        handed is the readout the record keeps, and that the reveal's other seats' hole cards
        are named by the reveal and appear nowhere in the acting seat's readout — and, for
        the token encoding, that their own token ids appear nowhere in the observation,
        since a token sequence makes a card a discrete value (`counterfactual.md` §2,
        `readout.md` §4, `e2e-surface.md` §2, §5, D-3, FAM-22, D-43).
        """
        policy = J.recording(J.build_baseline("always-call", BASELINE_SEED))
        opponent = J.build_baseline("always-call", BASELINE_SEED_OTHER)
        record = J.play_hand(SHOWDOWN_DEAL, policy, opponent)
        reveal = J.episode_reveal(record)
        self.assertTrue(
            bool(reveal["showdown"]),
            "the case needs a hand whose reveal names other seats' cards, or the absence it "
            "asserts is vacuous (counterfactual.md §4, records.md §5): %r" % (reveal,),
        )
        seats = {
            J.reveal_seat(entry): J.reveal_hole(entry)
            for entry in J.reveal_seats(reveal)
        }
        decisions = J.episode_decisions(record)
        self.assertTrue(
            decisions,
            "a played hand records its decisions (records.md §5): %r" % (record,),
        )
        first = set(J.decision_readout(decisions[0]))
        for position, decision in enumerate(decisions):
            facts = J.decision_readout(decision)
            self.assertEqual(
                set(facts),
                first,
                "the readout is the same closed set of facts at every decision — the eleven "
                "of e2e-surface.md §2 and no twelfth, so no decision-time read reaches the "
                "reveal (counterfactual.md §2, §9, readout.md §4, D-3): decision %d reads %r"
                % (position, sorted(facts)),
            )
            self.assertEqual(
                len(facts),
                11,
                "the eleven facts are closed: the reveal, `amounts` and `counterfactual` are "
                "keys of the episode and of the decision record, never a twelfth fact of the "
                "information set (counterfactual.md §2, e2e-surface.md §2, D-3): %r"
                % (sorted(facts),),
            )
            for name in ("reveal", "amounts", "counterfactual", "showdown", "shown", "won"):
                self.assertNotIn(
                    name,
                    facts,
                    "D-43's resolution is post-hand data and is not a readout fact; a readout "
                    "carrying %r would hand a policy the hand's own cards "
                    "(counterfactual.md §2, readout.md §4, FAM-22): %r"
                    % (name, sorted(facts)),
                )
            seat = J.decision_seat(decision)
            self.assertEqual(
                flatten(facts["hole"]),
                flatten(seats[seat]),
                "the acting seat's `hole` is its own two cards — the ones the reveal names for "
                "that seat, however the seat finished (records.md §5, e2e-surface.md §2): %r "
                "against %r" % (facts["hole"], seats[seat]),
            )
            text = flatten(facts)
            for other, hole in seats.items():
                if other == seat:
                    continue
                for card in hole:
                    self.assertNotIn(
                        str(card),
                        text,
                        "no readout carries another seat's hole cards while the hand is live, "
                        "so the resolution cannot reach a decision (counterfactual.md §2, "
                        "readout.md §4, FAM-22): seat %r's readout names seat %r's card %r"
                        % (seat, other, card),
                    )
        handed = list(policy.calls)
        own = [decision for decision in decisions if J.decision_seat(decision) == 0]
        self.assertEqual(
            len(handed),
            len(own),
            "the engine calls the seat's policy once per one of that seat's decisions, so the "
            "readouts it was handed are the decisions the record keeps "
            "(docs/L2/engine/surface.md §5, §10): %d calls against %d decisions"
            % (len(handed), len(own)),
        )
        for position, (facts, _legal, _chosen) in enumerate(handed):
            self.assertEqual(
                dict(facts),
                dict(J.decision_readout(own[position])),
                "the readout a policy is handed is the readout the record keeps, so no "
                "decision-time fact reaches the policy that the record does not state "
                "(counterfactual.md §2, docs/L2/engine/surface.md §5): decision %d"
                % (position,),
            )
        names = tuple(str(name) for name in J.encodings())
        self.assertGreaterEqual(
            len(names),
            2,
            "features declares both encodings, so the field set can be held to one answer "
            "across two representations (e2e-surface.md §2, D-3): %r" % (names,),
        )
        declared = None
        token_encoders = []
        for name in names:
            encoder = J.build_encoder(name)
            spec = J.observation_spec(encoder)
            fields = tuple(str(field) for field in spec["fields"])
            self.assertLessEqual(
                set(fields),
                first,
                "an encoding carries a subset of the readout's facts and nothing else, so the "
                "resolution cannot enter an observation through a field (e2e-surface.md §2, "
                "counterfactual.md §2, D-3): %r carries %r"
                % (name, sorted(set(fields) - first)),
            )
            for forbidden in ("reveal", "amounts", "counterfactual"):
                self.assertNotIn(
                    forbidden,
                    fields,
                    "D-43's facts are not fields of any encoding: the ladder changes the "
                    "representation and never what the agent may know, and no encoding carries "
                    "a card another seat holds (counterfactual.md §2, readout.md §4, "
                    "e2e-surface.md §2): %r carries %r" % (name, forbidden),
                )
            if declared is None:
                declared = set(fields)
            self.assertEqual(
                set(fields),
                declared,
                "`fields` is identical for every encoding, because the encoding changes the "
                "representation and never the information set (e2e-surface.md §2, D-3): %r "
                "carries %r against %r" % (name, sorted(fields), sorted(declared)),
            )
            if str(spec["representation"]) == "card-tokens":
                token_encoders.append(encoder)
        self.assertEqual(
            len(token_encoders),
            1,
            "the declared card-tokens representation exists once, and it is the encoding whose "
            "observation makes a card a discrete token — the one this case reads the absent "
            "cards off (e2e-surface.md §2, §5, D-3): %r" % (len(token_encoders),),
        )
        tokens = token_encoders[0]
        checked = 0
        for position, decision in enumerate(decisions):
            seat = J.decision_seat(decision)
            facts = J.decision_readout(decision)
            observation = J.encode(tokens, facts)
            others = [hole for other, hole in seats.items() if other != seat]
            self.assertTrue(
                others,
                "the reveal names at least one other seat's cards on a hand with a showdown, "
                "which is what makes the absence below a fact and not a gap (records.md §5, "
                "counterfactual.md §4): %r" % (seats,),
            )
            for hole in others:
                forged = dict(facts)
                forged["hole"] = tuple(hole)
                shadow = J.encode(tokens, forged)
                differing = [
                    index
                    for index in range(len(observation))
                    if observation[index] != shadow[index]
                ]
                self.assertTrue(
                    differing,
                    "the hole fact **is** carried by the encoding — substituting another "
                    "seat's two cards for the acting seat's must change the observation, or "
                    "the comparison below would be vacuous (e2e-surface.md §2, "
                    "docs/L2/features/surface.md §6): %r" % (hole,),
                )
                leaked = {int(shadow[index]) for index in differing}
                appearing = leaked & {int(value) for value in observation}
                self.assertFalse(
                    appearing,
                    "a token sequence makes a card a discrete value, and the cards of the seat "
                    "that is not acting encode to tokens that appear nowhere in the acting "
                    "seat's observation: no encoding carries a card another seat holds "
                    "(counterfactual.md §2, readout.md §4, FAM-22): tokens %r appear at "
                    "decision %d of seat %r" % (sorted(appearing), position, seat),
                )
                checked += 1
        self.assertGreater(
            checked,
            0,
            "at least one other seat's cards are compared against the acting seat's "
            "observation (counterfactual.md §2, readout.md §4): %d comparisons" % (checked,),
        )


if __name__ == "__main__":
    unittest.main()
