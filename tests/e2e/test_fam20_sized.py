"""FAM-20 — the sized action: four bands, one amount each, and the exploration-off read.

`docs/L1/battery.md` §3 FAM-20, `docs/L1/sizing.md` §2–§4 and §7, `docs/L1/records.md` §5
and §15, `docs/L1/e2e-surface.md` §2 "Action vocabulary", `docs/L3/training/greedy.md` §1
and §4, D-29, D-36, D-13.

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
record carries the amount and both bounds, that the greedy mode decides without a draw,
that the pass's hand count is the **sample** `min(budget, 2,000)` and never the run's
budget, and that a **run** above the bound completes with its pass bounded at the sample and
never truncated — the pass-side refusal is measured in the unit battery, where private names
are contract (`tests/training/test_greedy.py::TRN-14.5`, `battery.md` §2, D-36).  Whether a
trained learner's census meets `sizing.md` §7's criterion is a script's measurement over a
run record and **never a case** (`battery.md` §5, D-11, ASM-38).

Every assertion is read from entry points and from the decision records they return.  The
arithmetic of `sizing.md` §2 is the **expected** side and is computed from each decision's
own reported bounds (`_surface.band_resolution`, `_surface.band_owners`), never from a span
this battery hoped the walk would reach.

**D-33's widened history is this family's too**, because what a sized hand reaches is what the
block must hold: an uncapped hand is not capped, so a raiser seated opposite a learner takes it
past the 24 decisions the fixed-limit cap bounds — the reach `shapes.md` §8 widened the
`no-limit-100` block to 66 for — and every readout of such a walk must still encode on that
shape's own encoders, at 329 dense values and 82 tokens, with nothing truncated
(`shapes.md` §8, ASM-42, `flat-numeric.md` §5, `card-tokens.md` §5).  FAM-20.10 drives exactly
that; the capacity itself, and the refusal one entry beyond it, is FAM-19.14's.
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

# The battery's own invented budget for the pass it reads back, and the budget one hand above
# the hand bound, which **completes**: the run trains it and its own pass covers the run's
# first 2,000 hands, because the bound bounds the sample and never the run (`battery.md` §4,
# sizing.md §4, greedy.md §1, D-36).
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

        A shape with more than two seats is played through `engine.play_hand`'s seating —
        one policy per seat, which is the only route such a hand has — and every seat is
        handed the same policy, so the walk reaches that descriptor from every position and
        not only from the button (`seats.md` §4, `e2e-surface.md` §3.1, D-33).
        """
        if seeds is None:
            seeds = S.SHAPE_SEEDS
        shape = shape or self.second_shape()
        seats = self.seats_of(shape)
        out = []
        for seed in seeds:
            policy = (
                self.baseline("random", S.SEED_D) if descriptor is None
                else self.chooser(descriptor)
            )
            if seats > 2:
                out.append(self.play(seed, seats=[policy] * seats, shape=shape))
            else:
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
    def test_fam20_1_each_uncapped_shape_declares_its_six_descriptors_in_order(self):
        """FAM-20.1 the six descriptors are declared in each shape's own index order.

        `sizing.md` §3 fixes the order as the measured price order, worst first — `fold` 0,
        `check-call` 1, `raise-quarter` 2, `raise-half` 3, `raise-all-in` 4,
        `raise-minimum` 5 — and `e2e-surface.md` §2 makes `features.action_space(shape)` the
        declaration and `engine.legal_actions` the legal subset in the same order.  A seat
        count adds no descriptor, so both uncapped rows declare the same six in the same
        order and the case is asserted of each (`shapes.md` §2, `seats.md` §2, D-33).
        """
        for shape in self.other_shapes():
            space = self.action_space(shape)
            self.assertEqual(
                sorted(S.action_vocabulary(space)),
                list(range(len(S.SIZED_ACTIONS))),
                "%r's vocabulary is six indices, whichever way the container keys them "
                "(e2e-surface.md §2, shapes.md §2): %r" % (shape, space),
            )
            self.assertEqual(
                [self.decode_action(index, shape) for index in range(len(S.SIZED_ACTIONS))],
                list(S.SIZED_ACTIONS),
                "%r's indices decode to the declared descriptors **in the declared order** "
                "(sizing.md §3): %r" % (shape, space),
            )
            hand = self.hand(S.SEED_A, shape)
            legal = self.legal(hand)
            self.assertEqual(
                list(self.ep("features", "legal_indices")(legal)),
                sorted(self.ep("features", "legal_indices")(legal)),
                "engine.legal_actions returns the legal subset in %r's index order and "
                "legal_indices is position-aligned (sizing.md §3): %r" % (shape, legal),
            )
            self.assertEqual(
                set(legal),
                set(S.SIZED_ACTIONS),
                "the first decision of a no-cap hand of %r is the one decision on which every "
                "declared descriptor is legal, so the whole vocabulary is observable "
                "(sizing.md §2): %r" % (shape, legal),
            )

    def test_fam20_2_a_raise_resolves_to_its_own_band_s_maximum(self):
        """FAM-20.2 every raise resolves to its band's maximum, at its own bounds.

        `sizing.md` §2: each band resolves to **its own maximum** — so no two descriptors
        resolve to one amount at one decision, and a raise descriptor carries no amount of
        its own.  The case drives each descriptor in turn on **each** shape declared beside
        the default, reads the amount the engine resolved and the two bounds it was
        resolved between off the episode record (`records.md` §5), and compares them with
        the arithmetic of the decision itself — the bands are the shape's, and a six-seat
        hand's bounds are its own (`seats.md` §2, D-33).
        """
        for shape in self.other_shapes():
            seen = {}
            for descriptor in S.SIZED_RAISES:
                resolved = 0
                for episode in self.episodes(descriptor, seeds=S.SHAPE_SEEDS[:6], shape=shape):
                    for _episode, decision, amount, minimum, maximum in self.raise_decisions(
                        [episode]
                    ):
                        if decision["action"] != descriptor:
                            continue
                        resolved += 1
                        expected = S.band_resolution(descriptor, minimum, maximum)
                        self.assertIsNotNone(
                            expected,
                            "%r was legal on %r, so its band is not empty (sizing.md §2): "
                            "bounds %r..%r" % (descriptor, shape, minimum, maximum),
                        )
                        self.assertEqual(
                            amount,
                            expected,
                            "%r resolves to its band's maximum (sizing.md §2): at bounds "
                            "%r..%r on %r the band's maximum is %r, the engine resolved %r"
                            % (descriptor, minimum, maximum, shape, expected, amount),
                        )
                seen[descriptor] = resolved
                self.assertGreater(
                    resolved,
                    0,
                    "the case must drive %r on a real decision of %r, or its resolution is "
                    "asserted on nothing (sizing.md §2): %r"
                    % (descriptor, shape, seen),
                )

    def test_fam20_3_every_legal_amount_belongs_to_exactly_one_descriptor(self):
        """FAM-20.3 the four bands partition `[m, A]`: no overlap, no gap, one owner each.

        `sizing.md` §2 makes the four bands disjoint and total over the legal integer
        interval, and that is the property D-28's measured overlap violated.  The case
        walks decisions on **each** shape the catalogue declares beside the default — the
        bands are the shape's, and a six-seat row's bounds are its own — and, at each
        decision, computes from the decision's **own** bounds which descriptor owns each
        legal amount: every amount must have exactly one owner, and the four resolutions
        must be four distinct amounts (the empty bands excepted) (`seats.md` §2, D-33).
        """
        for shape in self.other_shapes():
            decisions = 0
            for episode, decision in self.every_decision(
                self.episodes(seeds=S.SHAPE_SEEDS[:6], shape=shape)
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
                        "D-28 recorded is impossible by construction (sizing.md §2): amount "
                        "%r of [%r, %r] on %r is owned by %r"
                        % (amount, minimum, maximum, shape, descriptors),
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
                        "between (sizing.md §2): %r outside [%r, %r] on %r"
                        % (descriptor, resolved, minimum, maximum, shape),
                    )
                    self.assertIn(
                        descriptor,
                        owners[resolved],
                        "the band's own resolution is inside the band it owns (sizing.md "
                        "§2): %r resolves to %r, whose owner is %r, on %r"
                        % (descriptor, resolved, owners[resolved], shape),
                    )
                self.assertEqual(
                    len(set(resolutions.values())),
                    len(resolutions),
                    "two descriptors never resolve to one amount at one decision "
                    "(sizing.md §2): bounds %r..%r, resolutions %r, on %r"
                    % (minimum, maximum, resolutions, shape),
                )
                self.assertIn(
                    maximum,
                    resolutions.values(),
                    "the all-in is reachable — it is the top band's resolution whenever the "
                    "interval holds more than the minimum (sizing.md §2): bounds %r..%r, "
                    "resolutions %r, on %r" % (minimum, maximum, resolutions, shape),
                )
            self.assertGreater(
                decisions,
                1,
                "the case must walk %r's decisions that declare raise bounds before it "
                "asserts the partition (records.md §5, sizing.md §2)" % (shape,),
            )

    def test_fam20_4_an_empty_band_is_masked_out_and_never_collapsed(self):
        """FAM-20.4 a band with no legal amount is masked out, not folded onto a neighbour.

        `sizing.md` §2: at `L = 0` only `raise-minimum` is legal and at `L = 1` only it and
        `raise-all-in`; a band with no legal integer in it never collapses onto its
        neighbour.  So at every decision the **legal** raise descriptors are exactly the
        bands whose resolution exists, and at an interval that masks a band the masked
        descriptors are absent from `legal_actions` while the minimum is present.  The
        case walks each shape declared beside the default — a six-seat hand's intervals are
        its own — and each walk must reach such a decision, or the masking is asserted on
        nothing (`seats.md` §2, D-33).
        """
        for shape in self.other_shapes():
            episodes = self.episodes(seeds=S.SHAPE_SEEDS, shape=shape)
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
                        "its neighbour (sizing.md §2): at bounds %r..%r %r is %r and the "
                        "legal set is %r on %r"
                        % (minimum, maximum, descriptor,
                           "legal" if wanted else "masked", sorted(legal), shape),
                    )
            self.assertGreater(
                decisions, 1,
                "the %r walk must reach decisions with raise bounds" % (shape,),
            )
            masked = self.empty_band_decisions(episodes)
            self.assertTrue(
                masked,
                "the %r walk must reach an interval that masks at least one declared band, "
                "or the masking this case asserts is never exercised (sizing.md §2): %d "
                "decisions" % (shape, decisions),
            )
            for decision, minimum, maximum, names in masked:
                legal = set(decision["legal"])
                self.assertIn(
                    "raise-minimum",
                    legal,
                    "the minimum band is never empty while a raise is legal at all — an "
                    "interval that masked it too would be no interval (sizing.md §2): bounds "
                    "%r..%r on %r" % (minimum, maximum, shape),
                )
                for name in names:
                    self.assertNotIn(
                        name,
                        legal,
                        "a band with no legal amount is masked out, never collapsed onto its "
                        "neighbour (sizing.md §2): %r at bounds %r..%r on %r, legal %r"
                        % (name, minimum, maximum, shape, sorted(legal)),
                    )
                if maximum == minimum:
                    self.assertEqual(
                        set(name for name in S.SIZED_RAISES if name in legal),
                        {"raise-minimum"},
                        "at L = 0 only `raise-minimum` is legal (sizing.md §2): bounds "
                        "%r..%r on %r, legal %r"
                        % (minimum, maximum, shape, sorted(legal)),
                    )

    def test_fam20_5_the_index_order_is_not_monotone_in_amount(self):
        """FAM-20.5 the index order is the price order, so it is not monotone in amount.

        `sizing.md` §3 makes the order a claim about nothing: the all-in sits **before**
        the minimum, so no reader and no test can read an index as a size, and the
        smallest raise index is not the cheapest band — a tie therefore resolves toward a
        worse-priced band and never manufactures a PASS (ASM-37, validity V-F13, D-29).
        The order is the shape's, so the case reads one bounded decision of **each** shape
        declared beside the default and resolves the four bands from that decision's own
        bounds (`seats.md` §2, D-33).
        """
        for shape in self.other_shapes():
            episodes = self.episodes(seeds=S.SHAPE_SEEDS[:6], shape=shape)
            decision, minimum, maximum = self.bounded_decision(episodes)
            amounts = {}
            for descriptor in S.SIZED_RAISES:
                resolved = S.band_resolution(descriptor, minimum, maximum)
                self.assertIsNotNone(
                    resolved,
                    "%r must be legal at the decision this case reads on %r (sizing.md "
                    "§2): bounds %r..%r" % (descriptor, shape, minimum, maximum),
                )
                index = list(S.SIZED_ACTIONS).index(descriptor)
                self.assertIn(
                    index,
                    self.ep("features", "legal_indices")(decision["legal"]),
                    "the descriptor's own index is legal at this decision on %r: %r against "
                    "%r" % (shape, descriptor, decision["legal"]),
                )
                amounts[index] = resolved
            ordered = [amounts[index] for index in sorted(amounts)]
            self.assertNotEqual(
                ordered,
                sorted(ordered),
                "the index order is **not** monotone in amount — the all-in sits before the "
                "minimum (sizing.md §3, ASM-37): index order %r resolves to %r on %r"
                % (sorted(amounts), ordered, shape),
            )
            smallest_raise_index = min(
                index for index in amounts if S.is_raise(self.decode_action(index, shape))
            )
            self.assertNotEqual(
                amounts[smallest_raise_index],
                min(amounts.values()),
                "the smallest raise index is not the cheapest band, so a learner whose "
                "values are all equal cannot read as one that found the minimum raise "
                "(sizing.md §3, V-F13): index %r resolves to %r against the cheapest %r on "
                "%r" % (smallest_raise_index, amounts[smallest_raise_index],
                        min(amounts.values()), shape),
            )
            self.assertEqual(
                amounts[list(S.SIZED_ACTIONS).index("raise-all-in")],
                max(amounts.values()),
                "the all-in's own index resolves to the largest legal amount (sizing.md §2): "
                "%r on %r" % (amounts, shape),
            )
            self.assertEqual(
                amounts[max(amounts)],
                min(amounts.values()),
                "the **last** raise index resolves to the cheapest band and the first to the "
                "second-cheapest, so the order runs against the price and no reader can take "
                "an index for a size (sizing.md §3, ASM-37): %r on %r" % (amounts, shape),
            )

    def test_fam20_6_a_decision_record_carries_its_amount_and_both_bounds(self):
        """FAM-20.6 `records.md` §5's three amount facts are on every decision record.

        The episode record carries the amount a raise was resolved to and the two bounds it
        was resolved between — `None` on a decision where no raise was legal — so a chosen
        size is attributable to one descriptor after the hand is over (`sizing.md` §2,
        `records.md` §5, D-29).  Both shapes are asserted: the default game's raises carry
        their own resolution and its no-raise decisions carry `None`.
        """
        for shape in (None,) + tuple(self.other_shapes()):
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
        """FAM-20.7 the pass samples the run, and the run above the bound completes.

        `sizing.md` §4 and `records.md` §15: a run retains one decision stream — the
        exploration-off pass — at most 2,000 hands and, per variant per seed, 1,000 decision
        records **per slot of the shape's history capacity** — 24,000 at the default shape,
        66,000 on `no-limit-100` and 98,000 on D-33's six-seat row — and neither bound is
        truncated (`shapes.md` §8, ASM-38, D-33).  **D-36 makes the hand bound bound the
        sample and never the run**: one pass plays `min(budget, 2,000)` hands of the run's
        own hands — the run's prefix — so a budget above the bound **completes**, its pass
        carrying `hands == 2,000` and one net chip delta per hand of that sample, and a
        **pass request** above the bound is still refused naming the count asked for and the
        bound, because a truncated log would silently report a different sample (`greedy.md`
        §1, §4, `sizing.md` §4, `records.md` §15, ASM-38, D-36).

        The case reads a run at a ten-hand budget on each shape declared beside the default,
        so the pass's own hand count is ten — below the bound the sample rule is the
        identity — and it drives the half of D-36 a run can reach:

        * the **sample a run retains at or below the bound**, on each shape declared beside
          the default: a ten-hand run's pass is its own ten hands with `off`, its seed, one
          net chip delta per hand, and indices that are their own mask's, their shape's and
          the descriptor each of them decodes to;
        * the **completing run** at a 2,001-hand budget, whose pass must be exactly 2,000
          hands with `off`, the run's seed, a count that is the bound and not the budget,
          every delta a real number, indices that are their own mask's and their shape's, and
          a log inside `1,000 × the shape's history capacity`.

        The hand-bound **refusal** is not driven here: it is measured by
        `tests/training/test_greedy.py::TRN-14.5`, which calls `_check_hands(2001)` and
        asserts both counts, because private names are contract only for `tests/training/`
        and `battery.md` §2 forbids an e2e case reaching an internal call
        (`docs/L3/training/README.md` §4, D-36).

        That last run is a 2,001-hand pass over 2,000 hands on a **cheap** architecture,
        because the claim is about the count and not about the model
        (`self.seated_rung(..., width=8, depth=1)`).  It is driven on `no-limit-100` only:
        measured on this machine a six-seat configuration of that size costs about 0.46 s a
        hand trained (0.24 s on the two-seat uncapped shape), so the five runs this walk
        already makes are cheap and a 2,001-hand six-seat one is a fifteen-minute run for a
        claim `_sample`'s and `loop`'s that is shape-independent — the unit battery drives it
        at `tests/training/test_greedy.py::TRN-14.5` and the prefix property at TRN-14.8,
        and every shape's pass is read above at ten hands.  A twenty-minute case would buy
        no assertion this one does not already make (`battery.md` §2, `sizing.md` §4, D-36).
        """
        for shape in self.other_shapes():
            configuration = self.seated_rung(shape=shape, seeds=(S.SEED_A,),
                                             samples=PASS_HANDS)
            record = self.ep("training", "run")(
                configuration, [S.SEED_A], PASS_HANDS, "cpu"
            )
            self.assertEqual(
                int(S.declared_field(record, "a run record (records.md §12)", "budget")),
                PASS_HANDS,
                "the run's budget is the sample it played (records.md §12, sizing.md §4): "
                "%r on %r" % (record.get("budget"), shape),
            )
            decisions_bound = 1000 * S.SHAPE_LAYOUTS[shape]["history"]
            passes = self.greedy_passes(record)
            self.assertTrue(
                passes,
                "a %r run retains its pass (records.md §12, §15): %r"
                % (shape, sorted(str(key) for key in record) if S.is_mapping(record)
                   else record),
            )
            for path, block in passes:
                mode = S.declared_field(block, "a greedy pass (records.md §15)", "mode")
                self.assertEqual(
                    str(mode), MODE_GREEDY,
                    "a retained decision stream is the exploration-off pass and its mode is "
                    "`off` (records.md §15, sizing.md §4): %r on %r" % (block, shape),
                )
                hands = int(S.declared_field(block, "a greedy pass (records.md §15)", "hands"))
                self.assertEqual(
                    hands, PASS_HANDS,
                    "the pass's hand count is the run's own sample budget — a ten-hand run "
                    "yields a ten-hand pass (sizing.md §4, ASM-38): %r on %r"
                    % (block, shape),
                )
                self.assertLessEqual(
                    hands, PASS_HANDS_BOUND,
                    "one pass plays at most %d hands (sizing.md §4, records.md §15): %r"
                    % (PASS_HANDS_BOUND, hands),
                )
                self.assertEqual(
                    int(S.declared_field(block, "a greedy pass (records.md §15)", "seed")),
                    S.SEED_A,
                    "the pass is played at the run's own seed (records.md §15, sizing.md "
                    "§4): %r" % (block.get("seed"),),
                )
                net_chips = S.declared_field(block, "a greedy pass (records.md §15)",
                                             "net_chips")
                self.assertEqual(
                    len(list(net_chips)), hands,
                    "the pass carries one net chip delta per hand it played, so the price "
                    "can be recomputed and not only quoted (records.md §15, ASM-23): %d "
                    "deltas for %d hands" % (len(list(net_chips)), hands),
                )
                decisions = S.declared_field(block, "a greedy pass (records.md §15)",
                                             "decisions")
                decisions = list(decisions)
                # The learner's own decisions only: a hand its opponent ends pre-flop (the
                # button folds and the learner is the big blind) holds none of them, so the
                # record's length is bounded by the sample and is not the sample's hand count
                # (`records.md` §5, §15).  What "never truncated" means here is that every
                # hand of the pass is present with its own outcome and that the log stays
                # inside its bound: a shorter **sample** is caught by the hand count above,
                # and the refusal a request beyond the bound earns is `TRN-14.5`'s, because
                # no entry point here can ask for one (`battery.md` §2, D-36).
                self.assertGreaterEqual(
                    len(decisions), 1,
                    "the pass retains the decisions it played — an empty log is no stream at "
                    "all (sizing.md §4, records.md §15): %r on %r" % (block, shape),
                )
                self.assertLessEqual(
                    len(decisions), decisions_bound,
                    "one pass on %r records at most 1,000 × its history capacity = %d "
                    "decision records, refused beyond and never truncated (records.md §15, "
                    "shapes.md §8, ASM-38, D-33): %d"
                    % (shape, decisions_bound, len(decisions)),
                )
                vocabulary = set(self.vocabulary(shape))
                for decision in decisions:
                    for key in ("index", "descriptor", "amount", "minimum", "maximum",
                                "legal", "tie"):
                        self.assertIn(
                            key, decision,
                            "records.md §15 makes %r a required key of a retained decision: "
                            "%r" % (key, decision),
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
                        "the run's shape (records.md §15, sizing.md §3): %r on %r"
                        % (decision, shape),
                    )
                    self.assertIn(
                        int(decision["index"]),
                        vocabulary,
                        "the pass is played on the run's shape, so its indices are that "
                        "shape's (records.md §15, shapes.md §3): %r on %r"
                        % (decision, shape),
                    )
                    self.assertIsInstance(
                        bool(decision["tie"]), bool,
                        "`tie` is a boolean flag on every retained decision (records.md §15, "
                        "sizing.md §3): %r" % (decision["tie"],),
                    )
            # Nothing is refused at this budget: a run's budget is no longer the pass's hand
            # count, so the pass above is read for the sample it played and the count it did
            # not exceed (greedy.md §1, §4, sizing.md §4, D-36).

        # The hand-bound **refusal** is not driven here, and the rule it would break is
        # `battery.md` §2's: `_check_hands` is a private name contract for `tests/training/`
        # (`docs/L3/training/README.md` §4), and an e2e case reaches no internal call.  It is
        # measured there instead — `tests/training/test_greedy.py::TRN-14.5` calls
        # `_check_hands(2001)` and asserts both counts (D-36).
        #
        # What is driven here is the other half, and it is a run's own record: a budget one
        # hand over the bound **completes** (D-36): the per-pair step asks `_pass` for
        # `greedy._sample(budget)`, so the run trains its 2,001 hands and the pass replays the
        # run's first 2,000 — one net chip delta per hand of that sample, in the shape's own
        # vocabulary and inside the shape's own record bound (greedy.md §1, §4, loop.md §1
        # steps 1 and 8, sizing.md §4, records.md §15, ASM-38).
        for shape in (self.second_shape(),):
            configuration = self.seated_rung(shape=shape, seeds=(S.SEED_A,),
                                             samples=REFUSED_HANDS, width=8, depth=1)
            record = self.ep("training", "run")(
                configuration, [S.SEED_A], REFUSED_HANDS, "cpu"
            )
            self.assertEqual(
                int(S.declared_field(record, "a run record (records.md §12)", "budget")),
                REFUSED_HANDS,
                "a budget one hand above the pass's hand bound is a run this module accepts "
                "and records — no bound is checked at resolve, so the run is neither refused "
                "nor shortened (D-36, greedy.md §4, loop.md §1 step 1, sizing.md §4): %r on "
                "%r" % (record.get("budget"), shape),
            )
            passes = self.greedy_passes(record)
            for path, block in passes:
                hands = int(S.declared_field(block, "a greedy pass (records.md §15)", "hands"))
                self.assertEqual(
                    hands, PASS_HANDS_BOUND,
                    "the pass's hand count is the **sample** and not the budget: "
                    "min(%d, %d) is %d, so a 2,001-hand run passes over its first 2,000 "
                    "hands (greedy.md §1, §4, sizing.md §4, records.md §15, D-36): %r on %r"
                    % (REFUSED_HANDS, PASS_HANDS_BOUND, PASS_HANDS_BOUND, block, shape),
                )
                self.assertNotEqual(
                    hands, REFUSED_HANDS,
                    "and that count is **not** the budget: a pass is bounded at the hand "
                    "bound, so a 2,001-hand run's block states 2,000 hands and never the whole "
                    "sample it trained — a `hands` equal to the budget would be the unbounded "
                    "pass D-36 removed (greedy.md §1, §4, sizing.md §4, records.md §15, "
                    "D-36): %r on %r" % (hands, shape),
                )
                net_chips = S.declared_field(block, "a greedy pass (records.md §15)",
                                             "net_chips")
                deltas = list(net_chips)
                self.assertEqual(
                    len(deltas), PASS_HANDS_BOUND,
                    "and it carries one net chip delta per hand of that sample and not per "
                    "hand of the run, so `budget` beside `hands` states the share the block "
                    "covers (records.md §15, ASM-23, greedy.md §4, D-36): %d deltas"
                    % (len(deltas),),
                )
                for value in deltas:
                    self.assertIsInstance(
                        float(value), float,
                        "every one of those deltas is a real number — the learner's seat's "
                        "net chips for one hand of the sample — so the 2,000 entries are one "
                        "delta per hand played and none invented (records.md §5, §15, "
                        "ASM-23, D-36): %r" % (value,),
                    )
                self.assertEqual(
                    str(S.declared_field(block, "a greedy pass (records.md §15)", "mode")),
                    MODE_GREEDY,
                    "the sampled pass is still the exploration-off one — the masked maximum "
                    "and the tie-break alone, with no generator drawn from (records.md §15, "
                    "sizing.md §4, ASM-38): %r on %r" % (block, shape),
                )
                self.assertEqual(
                    int(S.declared_field(block, "a greedy pass (records.md §15)", "seed")),
                    S.SEED_A,
                    "played at the run's own seed, which is what makes the sample replayable "
                    "from the record's own tuple (records.md §15, greedy.md §1, §5, ASM-2): "
                    "%r" % (block.get("seed"),),
                )
                decisions = list(S.declared_field(block, "a greedy pass (records.md §15)",
                                                  "decisions"))
                self.assertGreaterEqual(
                    len(decisions), 1,
                    "the sampled pass retains the decisions it played — an empty log is no "
                    "stream at all, so the reads below are not vacuous (sizing.md §4, "
                    "records.md §15): %r on %r" % (block, shape),
                )
                self.assertLessEqual(
                    len(decisions), 1000 * S.SHAPE_LAYOUTS[shape]["history"],
                    "and it stays inside %r's record bound of 1,000 × its %d-slot history "
                    "capacity, refused beyond and never truncated (records.md §15, "
                    "shapes.md §8, ASM-38, D-33): %d records"
                    % (shape, S.SHAPE_LAYOUTS[shape]["history"], len(decisions)),
                )
                vocabulary = set(self.vocabulary(shape))
                for decision in decisions:
                    self.assertIn(
                        int(decision["index"]),
                        set(int(member) for member in decision["legal"]),
                        "a sampled decision's index is one of its own legal mask, as every "
                        "retained decision's is (records.md §15, greedy.md §2): %r on %r"
                        % (decision, shape),
                    )
                    self.assertIn(
                        int(decision["index"]),
                        vocabulary,
                        "and one of the run's shape's declared indices, because the sample is "
                        "replayed on the shape the run trained on (records.md §15, shapes.md "
                        "§3, sizing.md §3, D-33): %r on %r" % (decision, shape),
                    )
                    self.assertEqual(
                        str(decision["descriptor"]),
                        self.decode_action(int(decision["index"]), shape),
                        "and its descriptor is the one its index decodes to in the run's own "
                        "vocabulary, so the sample is shown to be played in the shape's own "
                        "vocabulary at this edge as it is at ten hands (records.md §15, "
                        "sizing.md §3, D-33): %r on %r" % (decision, shape),
                    )

    def test_fam20_8_exploration_off_decides_without_a_draw(self):
        """FAM-20.8 two `off` policies at two seeds decide identically; `schedule` does not.

        `sizing.md` §4: `off` is the masked maximum and the tie-break alone and **no
        generator is drawn from**, so the decision is a function of the model and the
        readout and not of a seed; `schedule` is today's keyed draw and does move with the
        seed.  The case drives both modes on the same hands of **each** shape declared
        beside the default — a six-seat hand's readouts are the shape's, and its greedy
        pass is what the census of D-33 reads `(seats.md` §2, §4, D-33): the two greedy
        policies agree decision for decision, and at least one hand's scheduled decisions
        differ — so the identity asserted of `off` is a property of the mode and not of a
        learner that happens to be constant (`e2e-surface.md` §3.3, ASM-38).
        """
        for shape in self.other_shapes():
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
                    "%r, seed %r, %r against %r" % (shape, seed, first, second),
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
                "the default `schedule` mode does draw from the policy's own generator, so "
                "two scheduled policies at two seeds differ somewhere — otherwise the "
                "identity asserted of `off` would be a property of the learner and not of "
                "the mode (sizing.md §4, docs/L3/agents/rule.md §4): %d hands on %r, %d "
                "differed" % (hands, shape, scheduled_differs),
            )
            # `policy_from(path, "off")` is the same greedy read of the model the file holds.
            path = self.ep("agents", "save")(
                learner, os.path.join(self.scratch(), "fam20-8-greedy-%s.ckpt" % (shape,))
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
                    "model that `as_policy(..., \"off\")` takes, so the two agree decision "
                    "for decision (sizing.md §4, e2e-surface.md §3.4): %r, seed %r"
                    % (shape, seed),
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
        for shape in self.other_shapes():
            configuration = self.seated_rung(shape=shape, seeds=(S.SEED_A,),
                                             samples=PASS_HANDS)
            record = self.ep("training", "run")(
                configuration, [S.SEED_A], PASS_HANDS, "cpu"
            )
            passes = self.greedy_passes(record)
            self.assertTrue(
                passes,
                "a %r run retains its pass, so the mode it carries is observable "
                "(records.md §12, §15): %r" % (shape, record),
            )
            for path_keys, block in passes:
                self.assertEqual(
                    str(block.get("mode")), MODE_GREEDY,
                    "every pass a run records is the exploration-off pass — a block whose "
                    "mode is not `off` is refused rather than read (records.md §15, "
                    "sizing.md §4, §7): %r on %r" % (path_keys, shape),
                )

    def test_fam20_10_a_sized_hand_s_reach_fits_the_shapes_own_block(self):
        """FAM-20.10 a sized hand reaches past 24 decisions and every readout still encodes.

        D-33 widened the history block because the 24 slots are the *fixed-limit cap's*
        bound and the uncapped shapes have no cap: a raiser seated opposite a learner lifts
        an uncapped hand past 25 decisions, and the 24-slot encoder refuses it
        (`strata/records/pool-without-raiser.md` §2, `shapes.md` §8, ASM-42).  So this case
        drives the sized action through the engine's own hand on **each** shape declared
        beside the default — the battery's `raise-minimum` chooser on every seat, which is
        one of the shape's six declared descriptors — and asserts that the walk reaches more
        decisions than the default shape's capacity, that every readout of the walk encodes
        on **both** of that shape's encoders at the shape's own widths (329 and 82 on
        `no-limit-100`, 433 and 122 on the six-seat row), and that no readout of it is ever
        refused or truncated (`flat-numeric.md` §5, `card-tokens.md` §5, `seats.md` §2).

        The default shape's block holds its own hands: the same chooser's fixed-limit walk
        stays inside 24 decisions and encodes at 203 and 40, so the widening is the uncapped
        shapes' and the capped one's slots are untouched (`shapes.md` §5, §8).
        """
        policy = self.chooser("raise-minimum")
        seats_by_shape = {shape: self.seats_of(shape) for shape in self.other_shapes()}
        for shape in self.other_shapes():
            seats = seats_by_shape[shape]
            sized_encoders = (
                (S.FLAT, self.encoder(S.FLAT, shape), S.SHAPE_LAYOUTS[shape]["dense"]),
                (S.TOKENS, self.encoder(S.TOKENS, shape), S.SHAPE_LAYOUTS[shape]["tokens"]),
            )
            sized_decisions = 0
            longest = 0
            for seed in S.SHAPE_SEEDS[:3]:
                if seats > 2:
                    walk = self.seated_walk(
                        seed, {"default": policy}, limit=200, shape=shape)
                    decisions = [(readout, legal, action, index)
                                 for _seat, readout, legal, action, index in walk]
                else:
                    decisions = [
                        (readout, legal, action, index)
                        for _hand, readout, legal, action, index in self.decision_walk(
                            seed, policy, shape=shape)
                    ]
                self.assertTrue(
                    decisions, "the sized walk must play real hands (seed %r, %r)"
                    % (seed, shape),
                )
                sized_decisions += len(decisions)
                for readout, _legal, _action, _index in decisions:
                    longest = max(longest, len(readout["history"]))
                    for representation, encoder, width in sized_encoders:
                        encoded = self.ep("features", "encode")(encoder, readout)
                        self.assertEqual(
                            len(encoded), width,
                            "every readout a sized hand deals on %r encodes on the shape's %r "
                            "encoder at %d values, so no history the shape allows is refused "
                            "or truncated (shapes.md §8, ASM-42, flat-numeric.md §5): %d "
                            "values at seed %r"
                            % (shape, representation, width, len(encoded), seed),
                        )
            self.assertGreater(
                sized_decisions, S.SHAPE_LAYOUTS[S.SHAPE_DEFAULT]["history"],
                "the %r walk reaches more decisions than the default shape's %d-slot block "
                "would hold, which is the reach the widening exists for (shapes.md §8, "
                "D-33): %d decisions over the seeds walked"
                % (shape, S.SHAPE_LAYOUTS[S.SHAPE_DEFAULT]["history"], sized_decisions),
            )
            self.assertLessEqual(
                longest, S.SHAPE_LAYOUTS[shape]["history"],
                "no readout of the %r walk carries a longer history than the shape's own "
                "capacity (shapes.md §8, ASM-42): %d entries against %d"
                % (shape, longest, S.SHAPE_LAYOUTS[shape]["history"]),
            )
        # The default shape's block holds its own hands, and its layout is untouched.
        default = S.SHAPE_DEFAULT
        capped_encoders = (
            (S.FLAT, self.encoder(), S.SHAPE_LAYOUTS[default]["dense"]),
            (S.TOKENS, self.encoder(S.TOKENS), S.SHAPE_LAYOUTS[default]["tokens"]),
        )
        capped_policy = self.chooser("raise")
        capped_longest = 0
        for seed in S.SHAPE_SEEDS[:3]:
            walk = self.decision_walk(seed, capped_policy)
            self.assertTrue(walk, "the fixed-limit walk must play real hands (seed %r)" % (seed,))
            for _hand, readout, _legal, _action, _index in walk:
                capped_longest = max(capped_longest, len(readout["history"]))
                for representation, encoder, width in capped_encoders:
                    encoded = self.ep("features", "encode")(encoder, readout)
                    self.assertEqual(
                        len(encoded), width,
                        "a fixed-limit readout still encodes at the default shape's %r width "
                        "of %d (shapes.md §5, §8): %d values at seed %r"
                        % (representation, width, len(encoded), seed),
                    )
        self.assertLessEqual(
            capped_longest, S.SHAPE_LAYOUTS[default]["history"],
            "the capped shape's own hands stay inside its 24 slots, so the widening moved "
            "nothing of the fixed-limit path (shapes.md §5, §8): %d entries"
            % (capped_longest,),
        )



if __name__ == "__main__":
    unittest.main()
