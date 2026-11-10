"""FAM-20 — the sized action: four bands, one amount each, and the exploration-off read.

`docs/L1/battery.md` §3 FAM-20, `docs/L1/sizing.md` §2–§4 and §7, `docs/L1/records.md` §5
and §15, `docs/L1/e2e-surface.md` §2 "Action vocabulary", D-29, D-13.

The no-cap shape declares four raise descriptors that partition the legal integer interval
`[m, A]` between the minimum legal raise-to `m` and the all-in raise-to `A`, with
`L = A − m`: `raise-minimum` owns `{m}`, `raise-quarter` `(m, m + ⌊L/4⌋]`, `raise-half`
`(m + ⌊L/4⌋, m + ⌊L/2⌋]` and `raise-all-in` `(m + ⌊L/2⌋, A]`, and each resolves to its own
band's maximum.  So **every legal amount belongs to exactly one descriptor**, two
descriptors never resolve to one amount, the all-in is reachable, and a band with no legal
integer in it is **masked out** rather than collapsed onto its neighbour — which is the
overlap D-28 recorded, made impossible by construction.

What this family asserts is the machinery and never the verdict: that the bands are
disjoint and total, that a recorded amount attributes to one descriptor, that a decision
record carries the amount and both bounds, that the greedy mode decides without a draw and
that the pass is bounded and refused beyond its bound.  Whether a trained learner's census
meets `sizing.md` §7's criterion is a script's measurement over a run record and **never a
case** (`battery.md` §5, D-11, ASM-38).

Every assertion is read from entry points and from the decision records they return.  The
arithmetic of `sizing.md` §2 is the **expected** side and is computed from each decision's
own reported bounds (`_surface.band_resolution`, `_surface.band_owners`), never from a span
this battery hoped the walk would reach.
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


# sizing.md §4, records.md §15: the two bounds one pass stays inside, per variant per seed.
PASS_HANDS_BOUND = 2000
PASS_DECISIONS_BOUND = 24000

# The battery's own invented budget for the pass it reads back, and the budget one above
# the hand bound that must be refused (`battery.md` §4, sizing.md §4).
PASS_HANDS = 10
REFUSED_HANDS = PASS_HANDS_BOUND + 1

# The modes the exploration surface declares: `schedule` is today's behaviour and the
# default, `off` is the masked maximum and the tie-break alone (sizing.md §4).
MODE_DEFAULT = "schedule"
MODE_GREEDY = "off"

# One invented mode the surface does **not** declare, refused by name at both policy
# entry points.  It is the battery's own and appears in no design document (§4, battery.md
# §4).
UNKNOWN_MODE = "epsilon-floor-battery"


class FAM20Sized(S.SurfaceCase):
    """The sized vocabulary: disjoint bands, one attribution, and the greedy read."""

    # -- helpers -----------------------------------------------------------
    def chooser(self, descriptor):
        """A policy of §2 that returns one named descriptor where it is legal.

        It is the battery's own and appears in no design document (`battery.md` §4): it
        returns the descriptor under test where the decision allows it, else the
        check/call, else the first legal descriptor — always a member of
        ``legal_actions`` (`e2e-surface.md` §2).  Driving one descriptor at a time is how
        a case reads the amount the engine resolved **for that descriptor** off the
        episode record (`records.md` §5).
        """

        def policy(readout, legal):
            if descriptor in legal:
                return descriptor
            if "check-call" in legal:
                return "check-call"
            return legal[0]

        return policy

    def episodes(self, descriptor=None, seeds=None, shape=None):
        """Episodes on the shape in force, driven against a caller, one per seed.

        ``descriptor`` names the raise descriptor the battery's own seat tries first;
        ``None`` drives the catalogue's `random` baseline instead, which reaches the small
        spans a one-descriptor drive does not (`sizing.md` §2's masked bands).
        """
        if seeds is None:
            seeds = S.SHAPE_SEEDS
        shape = shape or self.second_shape()
        out = []
        for seed in seeds:
            policy = (
                self.baseline("random", S.SEED_D) if descriptor is None
                else self.chooser(descriptor)
            )
            out.append(self.play(seed, policy, self.baseline("always-call", S.SEED_G),
                                 shape=shape))
        return out

    def every_decision(self, episodes):
        """Every decision record of every episode, in order (`records.md` §5)."""
        for episode in episodes:
            for decision in self.decisions(episode):
                yield episode, decision

    def decisions(self, episode):
        """The ordered decision records of one episode, read tolerantly (§5)."""
        found = S.find_values(episode, "decision")
        for value in found:
            if isinstance(value, (list, tuple)) and value and S.is_mapping(value[0]):
                return list(value)
        raise AssertionError(
            "engine.play_hand's episode record carries its ordered decisions "
            "(records.md §5); it carries %r" % (
                sorted(str(key) for key in episode) if S.is_mapping(episode) else episode,
            )
        )

    def decision_amounts(self, decision):
        """One decision's ``(amount, minimum, maximum)`` — the three keys of §5."""
        amount = S.declared_field(decision, "a decision record (records.md §5)", "amount")
        minimum = S.declared_field(decision, "a decision record (records.md §5)", "minimum")
        maximum = S.declared_field(decision, "a decision record (records.md §5)", "maximum")
        return amount, minimum, maximum

    def raise_decisions(self, episodes):
        """Every decision of the walk that is a raise, with its own bounds."""
        for episode, decision in self.every_decision(episodes):
            amount, minimum, maximum = self.decision_amounts(decision)
            if S.is_raise(decision["action"]):
                yield episode, decision, amount, minimum, maximum

    def bounded_decision(self, episodes):
        """The first decision whose interval is wide enough to offer all four bands."""
        wanted = len(S.SIZED_RAISES)
        for episode, decision in self.every_decision(episodes):
            _amount, minimum, maximum = self.decision_amounts(decision)
            if minimum is None or maximum is None:
                continue
            legal = set(decision["legal"])
            if len([name for name in S.SIZED_RAISES if name in legal]) == wanted:
                return decision, minimum, maximum
        raise AssertionError(
            "the walk must reach one decision on which every declared raise band is legal, "
            "or the disjointness of the four bands is asserted on decisions that mask one "
            "of them (sizing.md §2): %d episodes"
            % (len(list(episodes)),)
        )

    def empty_band_decisions(self, episodes):
        """Every decision whose interval masks at least one declared raise band out."""
        out = []
        for episode, decision in self.every_decision(episodes):
            _amount, minimum, maximum = self.decision_amounts(decision)
            if minimum is None or maximum is None:
                continue
            masked = [
                name for name in S.SIZED_RAISES
                if S.band_resolution(name, minimum, maximum) is None
            ]
            if masked:
                out.append((decision, minimum, maximum, masked))
        return out

    def greedy_passes(self, record):
        """Every ``records.md`` §15 pass a run record retains, as ``(path, block)``."""
        passes = S.run_greedy(record)
        self.assertTrue(
            passes,
            "a run record carries `greedy` — the one decision stream a run retains "
            "(records.md §12, §15, sizing.md §4): %r"
            % (sorted(str(key) for key in record) if S.is_mapping(record) else record,),
        )
        return passes

    # -- the vocabulary (sizing.md §2–§3) ---------------------------------
    def test_fam20_1_the_second_shape_declares_its_six_descriptors_in_order(self):
        """FAM-20.1 the six descriptors are declared in the shape's own index order.

        `sizing.md` §3 fixes the order as the measured price order, worst first — `fold` 0,
        `check-call` 1, `raise-quarter` 2, `raise-half` 3, `raise-all-in` 4,
        `raise-minimum` 5 — and `e2e-surface.md` §2 makes `features.action_space(shape)`
        the declaration and `engine.legal_actions` the legal subset in the same order.
        """
        shape = self.second_shape()
        space = self.action_space(shape)
        self.assertEqual(
            sorted(S.action_vocabulary(space)),
            list(range(len(S.SIZED_ACTIONS))),
            "the named shape's vocabulary is six indices, whichever way the container "
            "keys them (e2e-surface.md §2, shapes.md §2): %r" % (space,),
        )
        self.assertEqual(
            [self.decode_action(index, shape) for index in range(len(S.SIZED_ACTIONS))],
            list(S.SIZED_ACTIONS),
            "the indices decode to the declared descriptors **in the declared order** "
            "(sizing.md §3): %r" % (space,),
        )
        hand = self.hand(S.SEED_A, shape)
        legal = self.legal(hand)
        self.assertEqual(
            list(self.ep("features", "legal_indices")(legal)),
            sorted(self.ep("features", "legal_indices")(legal)),
            "engine.legal_actions returns the legal subset in the shape's index order "
            "and legal_indices is position-aligned (sizing.md §3): %r" % (legal,),
        )
        self.assertEqual(
            set(legal),
            set(S.SIZED_ACTIONS),
            "the first decision of a no-cap hand is the one decision on which every "
            "declared descriptor is legal, so the whole vocabulary is observable "
            "(sizing.md §2): %r" % (legal,),
        )

    def test_fam20_2_a_raise_resolves_to_its_own_band_s_maximum(self):
        """FAM-20.2 every raise resolves to its band's maximum, at its own bounds.

        `sizing.md` §2: each band resolves to **its own maximum** — so no two descriptors
        resolve to one amount at one decision, and a raise descriptor carries no amount of
        its own.  The case drives each descriptor in turn, reads the amount the engine
        resolved and the two bounds it was resolved between off the episode record
        (`records.md` §5), and compares them with the arithmetic of the decision itself.
        """
        shape = self.second_shape()
        seen = {}
        for descriptor in S.SIZED_RAISES:
            resolved = 0
            for episode in self.episodes(descriptor, seeds=S.SHAPE_SEEDS[:6]):
                for _episode, decision, amount, minimum, maximum in self.raise_decisions(
                    [episode]
                ):
                    if decision["action"] != descriptor:
                        continue
                    resolved += 1
                    expected = S.band_resolution(descriptor, minimum, maximum)
                    self.assertIsNotNone(
                        expected,
                        "%r was legal, so its band is not empty (sizing.md §2): bounds "
                        "%r..%r" % (descriptor, minimum, maximum),
                    )
                    self.assertEqual(
                        amount,
                        expected,
                        "%r resolves to its band's maximum (sizing.md §2): at bounds "
                        "%r..%r the band's maximum is %r, the engine resolved %r"
                        % (descriptor, minimum, maximum, expected, amount),
                    )
            seen[descriptor] = resolved
            self.assertGreater(
                resolved,
                0,
                "the case must drive %r on a real decision, or its resolution is asserted "
                "on nothing (sizing.md §2): %r" % (descriptor, seen),
            )

    def test_fam20_3_every_legal_amount_belongs_to_exactly_one_descriptor(self):
        """FAM-20.3 the four bands partition `[m, A]`: no overlap, no gap, one owner each.

        `sizing.md` §2 makes the four bands disjoint and total over the legal integer
        interval, and that is the property D-28's measured overlap violated.  The case
        walks decisions on the named shape and, at each one, computes from the decision's
        **own** bounds which descriptor owns each legal amount: every amount must have
        exactly one owner, and the four resolutions must be four distinct amounts (the
        empty bands excepted).
        """
        decisions = 0
        for episode, decision in self.every_decision(
            self.episodes(seeds=S.SHAPE_SEEDS[:6])
        ):
            _amount, minimum, maximum = self.decision_amounts(decision)
            if minimum is None or maximum is None:
                continue
            decisions += 1
            owners = S.band_owners(minimum, maximum)
            for amount, descriptors in owners.items():
                self.assertEqual(
                    len(descriptors),
                    1,
                    "every legal amount belongs to exactly one descriptor — the overlap "
                    "D-28 recorded is impossible by construction (sizing.md §2): amount %r "
                    "of [%r, %r] is owned by %r"
                    % (amount, minimum, maximum, descriptors),
                )
            resolutions = {}
            for descriptor in S.SIZED_RAISES:
                resolved = S.band_resolution(descriptor, minimum, maximum)
                if resolved is None:
                    continue
                resolutions[descriptor] = resolved
                self.assertIn(
                    resolved,
                    owners,
                    "%r's resolution is a legal amount of the interval it was resolved "
                    "between (sizing.md §2): %r outside [%r, %r]"
                    % (descriptor, resolved, minimum, maximum),
                )
                self.assertIn(
                    descriptor,
                    owners[resolved],
                    "the band's own resolution is inside the band it owns (sizing.md §2): "
                    "%r resolves to %r, whose owner is %r"
                    % (descriptor, resolved, owners[resolved]),
                )
            self.assertEqual(
                len(set(resolutions.values())),
                len(resolutions),
                "two descriptors never resolve to one amount at one decision "
                "(sizing.md §2): bounds %r..%r, resolutions %r"
                % (minimum, maximum, resolutions),
            )
            self.assertIn(
                maximum,
                resolutions.values(),
                "the all-in is reachable — it is the top band's resolution whenever the "
                "interval holds more than the minimum (sizing.md §2): bounds %r..%r, "
                "resolutions %r" % (minimum, maximum, resolutions),
            )
        self.assertGreater(
            decisions,
            1,
            "the case must walk decisions that declare raise bounds before it asserts "
            "the partition (records.md §5, sizing.md §2)",
        )

    def test_fam20_4_an_empty_band_is_masked_out_and_never_collapsed(self):
        """FAM-20.4 a band with no legal amount is masked out, not folded onto a neighbour.

        `sizing.md` §2: at `L = 0` only `raise-minimum` is legal and at `L = 1` only it and
        `raise-all-in`; a band with no legal integer in it never collapses onto its
        neighbour.  So at every decision the **legal** raise descriptors are exactly the
        bands whose resolution exists, and at an interval that masks a band the masked
        descriptors are absent from `legal_actions` while the minimum is present.  The
        walk must reach such a decision, or the masking is asserted on nothing.
        """
        episodes = self.episodes(seeds=S.SHAPE_SEEDS)
        decisions = 0
        for _episode, decision in self.every_decision(episodes):
            _amount, minimum, maximum = self.decision_amounts(decision)
            if minimum is None or maximum is None:
                continue
            decisions += 1
            legal = set(decision["legal"])
            for descriptor in S.SIZED_RAISES:
                wanted = S.band_resolution(descriptor, minimum, maximum) is not None
                self.assertEqual(
                    descriptor in legal,
                    wanted,
                    "a raise descriptor is legal exactly when its band holds a legal "
                    "amount, and an empty band is masked out rather than collapsed onto "
                    "its neighbour (sizing.md §2): at bounds %r..%r %r is %r and the legal "
                    "set is %r" % (minimum, maximum, descriptor,
                                   "legal" if wanted else "masked", sorted(legal)),
                )
        self.assertGreater(decisions, 1, "the walk must reach decisions with raise bounds")
        masked = self.empty_band_decisions(episodes)
        self.assertTrue(
            masked,
            "the walk must reach an interval that masks at least one declared band, or the "
            "masking this case asserts is never exercised (sizing.md §2): %d decisions"
            % (decisions,),
        )
        for decision, minimum, maximum, names in masked:
            legal = set(decision["legal"])
            self.assertIn(
                "raise-minimum",
                legal,
                "the minimum band is never empty while a raise is legal at all — an "
                "interval that masked it too would be no interval (sizing.md §2): bounds "
                "%r..%r" % (minimum, maximum),
            )
            for name in names:
                self.assertNotIn(
                    name,
                    legal,
                    "a band with no legal amount is masked out, never collapsed onto its "
                    "neighbour (sizing.md §2): %r at bounds %r..%r, legal %r"
                    % (name, minimum, maximum, sorted(legal)),
                )
            if maximum == minimum:
                self.assertEqual(
                    set(name for name in S.SIZED_RAISES if name in legal),
                    {"raise-minimum"},
                    "at L = 0 only `raise-minimum` is legal (sizing.md §2): bounds %r..%r, "
                    "legal %r" % (minimum, maximum, sorted(legal)),
                )

    def test_fam20_5_the_index_order_is_not_monotone_in_amount(self):
        """FAM-20.5 the index order is the price order, so it is not monotone in amount.

        `sizing.md` §3 makes the order a claim about nothing: the all-in sits **before**
        the minimum, so no reader and no test can read an index as a size, and the
        smallest raise index is not the cheapest band — a tie therefore resolves toward a
        worse-priced band and never manufactures a PASS (ASM-37, validity V-F13, D-29).
        """
        episodes = self.episodes(seeds=S.SHAPE_SEEDS[:6])
        decision, minimum, maximum = self.bounded_decision(episodes)
        amounts = {}
        for descriptor in S.SIZED_RAISES:
            resolved = S.band_resolution(descriptor, minimum, maximum)
            self.assertIsNotNone(
                resolved,
                "%r must be legal at the decision this case reads (sizing.md §2): bounds "
                "%r..%r" % (descriptor, minimum, maximum),
            )
            index = list(S.SIZED_ACTIONS).index(descriptor)
            self.assertIn(
                index,
                self.ep("features", "legal_indices")(decision["legal"]),
                "the descriptor's own index is legal at this decision: %r against %r"
                % (descriptor, decision["legal"]),
            )
            amounts[index] = resolved
        ordered = [amounts[index] for index in sorted(amounts)]
        self.assertNotEqual(
            ordered,
            sorted(ordered),
            "the index order is **not** monotone in amount — the all-in sits before the "
            "minimum (sizing.md §3, ASM-37): index order %r resolves to %r"
            % (sorted(amounts), ordered),
        )
        smallest_raise_index = min(
            index for index in amounts
            if S.is_raise(self.decode_action(index, self.second_shape()))
        )
        self.assertNotEqual(
            amounts[smallest_raise_index],
            min(amounts.values()),
            "the smallest raise index is not the cheapest band, so a learner whose values "
            "are all equal cannot read as one that found the minimum raise (sizing.md §3, "
            "V-F13): index %r resolves to %r against the cheapest %r"
            % (smallest_raise_index, amounts[smallest_raise_index], min(amounts.values())),
        )
        self.assertEqual(
            amounts[list(S.SIZED_ACTIONS).index("raise-all-in")],
            max(amounts.values()),
            "the all-in's own index resolves to the largest legal amount (sizing.md §2): "
            "%r" % (amounts,),
        )
        self.assertEqual(
            amounts[max(amounts)],
            min(amounts.values()),
            "the **last** raise index resolves to the cheapest band and the first to the "
            "second-cheapest, so the order runs against the price and no reader can take "
            "an index for a size (sizing.md §3, ASM-37): %r" % (amounts,),
        )

    # -- the record (records.md §5, §15) ----------------------------------
    def test_fam20_6_a_decision_record_carries_its_amount_and_both_bounds(self):
        """FAM-20.6 `records.md` §5's three amount facts are on every decision record.

        The episode record carries the amount a raise was resolved to and the two bounds it
        was resolved between — `None` on a decision where no raise was legal — so a chosen
        size is attributable to one descriptor after the hand is over (`sizing.md` §2,
        `records.md` §5, D-29).  Both shapes are asserted: the default game's raises carry
        their own resolution and its no-raise decisions carry `None`.
        """
        for shape in (None, self.second_shape()):
            decisions = 0
            raises = 0
            for episode in self.episodes(seeds=S.SHAPE_SEEDS[:4], shape=shape):
                for _episode, decision in self.every_decision([episode]):
                    decisions += 1
                    amount, minimum, maximum = self.decision_amounts(decision)
                    if minimum is not None:
                        self.assertLessEqual(
                            int(minimum), int(maximum),
                            "the minimum legal raise-to never exceeds the maximum "
                            "(sizing.md §2): %r..%r" % (minimum, maximum),
                        )
                    if S.is_raise(decision["action"]):
                        raises += 1
                        self.assertIsNotNone(
                            amount,
                            "a decision whose action is a raise carries the amount the "
                            "engine resolved (records.md §5, sizing.md §2): %r"
                            % (decision,),
                        )
                        self.assertIsNotNone(
                            minimum,
                            "a raise decision carries the lower bound it was resolved "
                            "between (records.md §5): %r" % (decision,),
                        )
                        self.assertGreaterEqual(
                            int(amount), int(minimum),
                            "the resolved amount is inside the interval it was resolved "
                            "between (sizing.md §2): %r against %r..%r"
                            % (amount, minimum, maximum),
                        )
                        self.assertLessEqual(
                            int(amount), int(maximum),
                            "the resolved amount is inside the interval it was resolved "
                            "between (sizing.md §2): %r against %r..%r"
                            % (amount, minimum, maximum),
                        )
                    else:
                        self.assertIsNone(
                            amount,
                            "a fold or a check/call carries no amount (records.md §5): %r"
                            % (decision,),
                        )
            self.assertGreater(decisions, 0, "the case must walk decisions on shape %r"
                               % (shape,))
            self.assertGreater(
                raises, 0,
                "the walk must include a raise, or the amount fact is asserted on "
                "decisions that carry none (sizing.md §2): shape %r" % (shape,),
            )

    def test_fam20_7_the_greedy_pass_is_bounded_refused_and_never_truncated(self):
        """FAM-20.7 the pass plays the run's own sample, and a pass beyond its bound is refused.

        `sizing.md` §4 and `records.md` §15: a run retains one decision stream — the
        exploration-off pass — at most 2,000 hands and 24,000 decision records per variant
        per seed, and a pass that would exceed either bound is **refused, never
        truncated**.  The case reads a run at a ten-hand budget, so the pass's own hand
        count is ten (the sample is the run's), and it then hands the same configuration a
        budget one hand over the bound: the call must be refused, naming the bound, and
        must return no record at all — a truncated log would silently report a different
        sample (ASM-38, D-28).
        """
        shape = self.second_shape()
        configuration = self.shaped_rung(shape=shape, seeds=(S.SEED_A,))
        record = self.ep("training", "run")(
            configuration, [S.SEED_A], PASS_HANDS, "cpu"
        )
        self.assertEqual(
            int(S.declared_field(record, "a run record (records.md §12)", "budget")),
            PASS_HANDS,
            "the run's budget is the sample it played (records.md §12, sizing.md §4)",
        )
        passes = self.greedy_passes(record)
        for path, block in passes:
            mode = S.declared_field(block, "a greedy pass (records.md §15)", "mode")
            self.assertEqual(
                str(mode), MODE_GREEDY,
                "a retained decision stream is the exploration-off pass and its mode is "
                "`off` (records.md §15, sizing.md §4): %r" % (block,),
            )
            hands = int(S.declared_field(block, "a greedy pass (records.md §15)", "hands"))
            self.assertEqual(
                hands, PASS_HANDS,
                "the pass's hand count is the run's own sample budget — a ten-hand run "
                "yields a ten-hand pass (sizing.md §4, ASM-38): %r" % (block,),
            )
            self.assertLessEqual(
                hands, PASS_HANDS_BOUND,
                "one pass plays at most %d hands (sizing.md §4, records.md §15): %r"
                % (PASS_HANDS_BOUND, hands),
            )
            self.assertEqual(
                int(S.declared_field(block, "a greedy pass (records.md §15)", "seed")),
                S.SEED_A,
                "the pass is played at the run's own seed (records.md §15, sizing.md §4): "
                "%r" % (block.get("seed"),),
            )
            net_chips = S.declared_field(block, "a greedy pass (records.md §15)",
                                         "net_chips")
            self.assertEqual(
                len(list(net_chips)), hands,
                "the pass carries one net chip delta per hand it played, so the price can "
                "be recomputed and not only quoted (records.md §15, ASM-23): %d deltas "
                "for %d hands" % (len(list(net_chips)), hands),
            )
            decisions = S.declared_field(block, "a greedy pass (records.md §15)",
                                         "decisions")
            decisions = list(decisions)
            # The learner's own decisions only: a hand its opponent ends pre-flop (the
            # button folds and the learner is the big blind) holds none of them, so the
            # record's length is bounded by the sample and is not the sample's hand count
            # (`records.md` §5, §15).  What "never truncated" means here is that every hand
            # of the pass is present with its own outcome and that the log stays inside its
            # bound: a pass over the bound is refused below, and a shorter **sample** is
            # caught by the hand count above.
            self.assertGreaterEqual(
                len(decisions), 1,
                "the pass retains the decisions it played — an empty log is no stream at "
                "all (sizing.md §4, records.md §15): %r" % (block,),
            )
            self.assertLessEqual(
                len(decisions), PASS_DECISIONS_BOUND,
                "one pass records at most %d decision records (records.md §15): %d"
                % (PASS_DECISIONS_BOUND, len(decisions)),
            )
            vocabulary = set(self.vocabulary(shape))
            for decision in decisions:
                for key in ("index", "descriptor", "amount", "minimum", "maximum",
                            "legal", "tie"):
                    self.assertIn(
                        key, decision,
                        "records.md §15 makes %r a required key of a retained decision: %r"
                        % (key, decision),
                    )
                self.assertIn(
                    int(decision["index"]),
                    set(int(member) for member in decision["legal"]),
                    "a retained decision's index is one of its own legal mask "
                    "(records.md §15): %r" % (decision,),
                )
                self.assertEqual(
                    str(decision["descriptor"]),
                    self.decode_action(int(decision["index"]), shape),
                    "a retained decision carries the descriptor its index decodes to in "
                    "the run's shape (records.md §15, sizing.md §3): %r" % (decision,),
                )
                self.assertIn(
                    int(decision["index"]),
                    vocabulary,
                    "the pass is played on the run's shape, so its indices are that "
                    "shape's (records.md §15, shapes.md §3): %r" % (decision,),
                )
                self.assertIsInstance(
                    bool(decision["tie"]), bool,
                    "`tie` is a boolean flag on every retained decision (records.md §15, "
                    "sizing.md §3): %r" % (decision["tie"],),
                )
        # One hand over the bound: refused with both counts named, and no record written.
        text = S.refusal_text(
            lambda: self.ep("training", "run")(
                configuration, [S.SEED_A], REFUSED_HANDS, "cpu"
            )
        )
        self.assertIsNotNone(
            text,
            "a run whose budget would make the pass exceed its hand bound is refused, not "
            "truncated (sizing.md §4, records.md §15, ASM-38): a %d-hand budget"
            % (REFUSED_HANDS,),
        )
        self.assertIn(
            str(PASS_HANDS_BOUND),
            text,
            "the refusal names the bound the pass would cross (records.md §15, sizing.md "
            "§4): %r" % (text,),
        )
        self.assertIn(
            str(REFUSED_HANDS),
            text,
            "the refusal names the count that crossed it, so a reader knows the sample it "
            "asked for and the sample the bound allows (sizing.md §4): %r" % (text,),
        )

    # -- the exploration-off surface (sizing.md §4) -----------------------
    def test_fam20_8_exploration_off_decides_without_a_draw(self):
        """FAM-20.8 two `off` policies at two seeds decide identically; `schedule` does not.

        `sizing.md` §4: `off` is the masked maximum and the tie-break alone and **no
        generator is drawn from**, so the decision is a function of the model and the
        readout and not of a seed; `schedule` is today's keyed draw and does move with the
        seed.  The case drives both modes on the same hands: the two greedy policies agree
        decision for decision, and at least one hand's scheduled decisions differ — so the
        identity asserted of `off` is a property of the mode and not of a learner that
        happens to be constant (`e2e-surface.md` §3.3, ASM-38).
        """
        shape = self.second_shape()
        learner = self.learner(width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH, seed=S.SEED_I,
                               game=shape)
        greedy_first = self.policy(learner, self.encoder(shape=shape), S.SEED_A,
                                   MODE_GREEDY)
        greedy_second = self.policy(learner, self.encoder(shape=shape), S.SEED_B,
                                    MODE_GREEDY)
        scheduled_first = self.policy(learner, self.encoder(shape=shape), S.SEED_A,
                                      MODE_DEFAULT)
        scheduled_second = self.policy(learner, self.encoder(shape=shape), S.SEED_B,
                                       MODE_DEFAULT)
        hands = 0
        scheduled_differs = 0
        for seed in S.SHAPE_SEEDS[:5]:
            first = [entry[4] for entry in
                     self.decision_walk(seed, greedy_first, limit=4, shape=shape)]
            second = [entry[4] for entry in
                      self.decision_walk(seed, greedy_second, limit=4, shape=shape)]
            self.assertTrue(first, "the greedy policy answered no decision at all")
            self.assertEqual(
                first,
                second,
                "at exploration `off` the decision is the masked maximum and the "
                "tie-break alone, so two greedy policies built at two seeds decide "
                "identically on the same readouts (sizing.md §4, e2e-surface.md §3.3): "
                "seed %r, %r against %r" % (seed, first, second),
            )
            hands += 1
            one = [entry[4] for entry in
                   self.decision_walk(seed, scheduled_first, limit=4, shape=shape)]
            other = [entry[4] for entry in
                     self.decision_walk(seed, scheduled_second, limit=4, shape=shape)]
            if one != other:
                scheduled_differs += 1
        self.assertGreater(hands, 0, "the case must drive real hands")
        self.assertGreater(
            scheduled_differs,
            0,
            "the default `schedule` mode does draw from the policy's own generator, so two "
            "scheduled policies at two seeds differ somewhere — otherwise the identity "
            "asserted of `off` would be a property of the learner and not of the mode "
            "(sizing.md §4, docs/L3/agents/rule.md §4): %d hands, %d differed"
            % (hands, scheduled_differs),
        )
        # `policy_from(path, "off")` is the same greedy read of the model the file holds.
        path = self.ep("agents", "save")(
            learner, os.path.join(self.scratch(), "fam20-8-greedy.ckpt")
        )
        loaded = self.ep("evaluation", "policy_from")(path, MODE_GREEDY)
        self.assertTrue(
            callable(loaded),
            "evaluation.policy_from(path, \"off\") returns a policy in the sense of §2 "
            "(e2e-surface.md §3.4, sizing.md §4): %r" % (loaded,),
        )
        for seed in S.SHAPE_SEEDS[:3]:
            from_file = [entry[4] for entry in
                         self.decision_walk(seed, loaded, limit=4, shape=shape)]
            from_learner = [entry[4] for entry in
                            self.decision_walk(seed, greedy_first, limit=4, shape=shape)]
            self.assertEqual(
                from_file,
                from_learner,
                "`policy_from(..., \"off\")` is the same masked maximum over the same "
                "model that `as_policy(..., \"off\")` takes, so the two agree decision for "
                "decision (sizing.md §4, e2e-surface.md §3.4): seed %r" % (seed,),
            )

    def test_fam20_9_a_mode_outside_the_two_is_refused_by_name(self):
        """FAM-20.9 the exploration mode is closed: anything but `schedule`/`off` is refused.

        `sizing.md` §4 makes the two values the whole vocabulary of the mode — the policy's
        and not the schedule's — so a third one cannot be asked for at either policy entry
        point, and no retained pass can carry a mode other than `off` (`records.md` §15,
        `e2e-surface.md` §3.3–§3.4).  A mode outside the two is refused **naming it**,
        before a checkpoint is touched, so a census can never be computed over a log that
        says something else (D-28's exploration artefact).
        """
        learner = self.learner(width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH, seed=S.SEED_I)
        encoder = self.encoder()
        text = S.refusal_text(
            lambda: self.ep("agents", "as_policy")(learner, encoder, S.SEED_A,
                                                   UNKNOWN_MODE)
        )
        self.assertIsNotNone(
            text,
            "agents.as_policy refuses an exploration mode that is neither `schedule` nor "
            "`off` (e2e-surface.md §3.3, sizing.md §4): %r" % (UNKNOWN_MODE,),
        )
        self.assertIn(
            S._family_token(UNKNOWN_MODE),
            S._family_token(text),
            "the refusal names the mode it refused (sizing.md §4): %r" % (text,),
        )
        for mode in (MODE_DEFAULT, MODE_GREEDY):
            self.assertIn(
                S._family_token(mode),
                S._family_token(text),
                "the refusal names the two declared modes beside the one it refused "
                "(sizing.md §4): %r" % (text,),
            )
        path = self.ep("agents", "save")(
            learner, os.path.join(self.scratch(), "fam20-9-modes.ckpt")
        )
        text = S.refusal_text(
            lambda: self.ep("evaluation", "policy_from")(path, UNKNOWN_MODE)
        )
        self.assertIsNotNone(
            text,
            "evaluation.policy_from refuses the same mode, before a checkpoint is touched "
            "(e2e-surface.md §3.4, sizing.md §4)",
        )
        self.assertIn(
            S._family_token(UNKNOWN_MODE),
            S._family_token(text),
            "the refusal names the mode it refused (sizing.md §4): %r" % (text,),
        )
        # And no retained pass carries another mode: the mode is `off` or it is not a pass.
        configuration = self.shaped_rung(shape=self.second_shape(), seeds=(S.SEED_A,))
        record = self.ep("training", "run")(
            configuration, [S.SEED_A], PASS_HANDS, "cpu"
        )
        for path_keys, block in self.greedy_passes(record):
            self.assertEqual(
                str(block.get("mode")), MODE_GREEDY,
                "every pass a run records is the exploration-off pass — a block whose "
                "mode is not `off` is refused rather than read (records.md §15, sizing.md "
                "§4, §7): %r" % (path_keys,),
            )


if __name__ == "__main__":
    unittest.main()
