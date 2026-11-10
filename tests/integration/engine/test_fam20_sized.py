"""FAM-20 — the sized action: four bands, one amount each, and the three amount facts.

`docs/L2/engine/surface.md` §2, §6, §7 and §10, `docs/L2/engine/environment.md` §3,
`docs/L1/sizing.md` §2–§3 and §5, `battery.md` §3 FAM-20, D-29.

A shape without a cap declares four raise descriptors — `raise-quarter`, `raise-half`,
`raise-all-in` and `raise-minimum` — that partition the legal integer interval
`[m, A]` between the minimum legal raise-to `m` and the all-in raise-to `A`, where
`L = A − m`: `raise-minimum` owns `{m}`, `raise-quarter` `(m, m + ⌊L/4⌋]`,
`raise-half` `(m + ⌊L/4⌋, m + ⌊L/2⌋]` and `raise-all-in` `(m + ⌊L/2⌋, A]`, and each
resolves to its own band's maximum.  The bands are disjoint and total, a band with no
legal integer in it is **masked out and never collapsed onto its neighbour**, and the
index order is the measured price order, worst first, so it is not monotone in amount.

Every assertion below is read from the entry points: the vocabulary and its order from
`legal_actions`, the interval from the episode record's own `minimum`/`maximum`, and
the resolution the engine chose from its `amount`.  The arithmetic is never assumed from
a span the battery hoped to reach — each case computes the expected bands from the
decision's own reported bounds, and the `L`-dependent masks are asserted at the spans
the drive is shown to reach.
"""

import os
import sys
import unittest

try:  # collected as part of a package
    from . import _support as S
except ImportError:  # collected as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _support as S  # noqa: E402


# sizing.md §2: the four bands of a shape without a cap, in the shape's declared index
# order (quarter, half, all-in, minimum) and the two descriptors every shape carries.
BANDS = S.SIZED_RAISES
BASES = ("fold", "check-call")
DECLARED_SIZED = BASES + BANDS
DECLARED_FIXED = ("fold", "check-call", "raise")
# Both vocabularies at once, because a decision's descriptors are its own shape's and a
# case that walks either shape reads them here (shapes.md §2, §5).
DECLARED_ALL = BASES + ("raise",) + BANDS

# environment.md §1, sizing.md §2: the first no-limit decision's own interval — the
# button owes the big blind one chip, so the minimum raise-to is 4 and the all-in
# raise-to is the 100-chip stack.  Stated here as the fact the case checks, never as an
# input to the arithmetic.
FIRST_MINIMUM = 4
FIRST_MAXIMUM = 100


# ---------------------------------------------------------------------------
# The band arithmetic of sizing.md §2 — the expected side, computed from one
# decision's own reported bounds and never from a span the battery assumed
# ---------------------------------------------------------------------------
def resolutions(minimum, maximum):
    """The four declared raise descriptors' resolutions at one decision (sizing.md §2)."""
    span = maximum - minimum
    return {
        "raise-minimum": minimum,
        "raise-quarter": minimum + span // 4,
        "raise-half": minimum + span // 2,
        "raise-all-in": maximum,
    }


def legal_bands(minimum, maximum):
    """The bands holding at least one legal amount, in the declared index order.

    `raise-minimum` is legal whenever a raise is; `raise-quarter` iff `⌊L/4⌋ ≥ 1`,
    `raise-half` iff `⌊L/2⌋ > ⌊L/4⌋`, and `raise-all-in` iff `A > m + ⌊L/2⌋`, so at
    `L = 0` only the minimum is legal and at `L = 1` only it and the all-in
    (sizing.md §2).
    """
    span = maximum - minimum
    wanted = ["raise-minimum"]
    if span // 4 >= 1:
        wanted.append("raise-quarter")
    if span // 2 > span // 4:
        wanted.append("raise-half")
    if maximum > minimum + span // 2:
        wanted.append("raise-all-in")
    return [name for name in BANDS if name in wanted]


def declared_name(descriptor, declared=DECLARED_ALL):
    """The declared descriptor a returned descriptor denotes, read by letters and digits.

    The catalogue declares the vocabulary as names, so a descriptor that denotes one of
    them is read here by its stable text and never by a spelling this case invented.
    """
    want = S.token(descriptor)
    for name in declared:
        if S.token(name) == want:
            return name
    return None


def band_name(descriptor, declared=DECLARED_ALL):
    """Which raise band a descriptor names, or ``None`` when it names no raise."""
    name = declared_name(descriptor, declared)
    return name if name in BANDS else None


# ---------------------------------------------------------------------------
# The battery's own policies
# ---------------------------------------------------------------------------
class ReplayMiss(AssertionError):
    """The replayed decision did not offer the descriptor the battery asked for."""


class CycleBands:
    """A policy that asks for the declared bands in turn, continuing when it cannot raise.

    It is deterministic and needs nothing but the protocol's two arguments, so an
    episode it plays is a function of the seed and the shape alone.
    """

    def __init__(self, pattern):
        self.pattern = tuple(pattern)
        self.calls = 0

    def __call__(self, readout, legal):
        descriptors = S.descriptor_list(legal, "the legal descriptors a policy is called with")
        names = [declared_name(descriptor) for descriptor in descriptors]
        want = self.pattern[self.calls % len(self.pattern)]
        self.calls += 1
        if want in names:
            return descriptors[names.index(want)]
        for fallback in BASES[::-1]:  # check-call, then fold
            if fallback in names:
                return descriptors[names.index(fallback)]
        return descriptors[0]


class Replay:
    """A policy that replays a prefix, answers one decision with ``answer``, then continues.

    A decision's own position is read from the readout's `history` fact, which carries
    one entry per applied action (environment.md §2), so the policy needs nothing but
    what the protocol hands every policy (surface.md §10).
    """

    def __init__(self, prefix, target, answer):
        self.prefix = tuple(prefix)
        self.target = target
        self.answer = answer

    def __call__(self, readout, legal):
        descriptors = S.descriptor_list(legal, "the legal descriptors a policy is called with")
        names = [declared_name(descriptor) for descriptor in descriptors]
        position = len(S.required(readout, "the readout a policy is called with", "history"))
        if position == self.target:
            if self.answer not in names:
                raise ReplayMiss(
                    "the replayed decision %d does not offer %r, which the source episode "
                    "did offer: legal_actions is %r (surface.md §6)"
                    % (self.target, self.answer, descriptors)
                )
            return descriptors[names.index(self.answer)]
        if position < self.target and position < len(self.prefix):
            want = declared_name(self.prefix[position])
            if want in names:
                return descriptors[names.index(want)]
        for fallback in BASES[::-1]:
            if fallback in names:
                return descriptors[names.index(fallback)]
        return descriptors[0]


class FAM20Sized(S.EngineCase):
    """The sized action, through the declared entry points and nothing below them."""

    # -- readers -----------------------------------------------------------
    def sized_row(self):
        """The `no-limit-100` row of the catalogue, or a failure naming what is absent."""
        shapes = self.game_shapes()
        if not S.is_mapping(shapes) or S.SHAPE_SIZED not in shapes:
            self.fail(
                "game_shapes() must declare the row %r beside the default (surface.md §12, "
                "shapes.md §2); it returned %r" % (S.SHAPE_SIZED, shapes)
            )
        return shapes[S.SHAPE_SIZED]

    def bounds(self, decision, position):
        """The decision's own legal raise interval, or ``None`` when it states none.

        environment.md §3: `minimum` and `maximum` are the bounds of the legal raise
        interval and are `None` **exactly** when no raise was legal, so the two are read
        together and neither is taken on its own.
        """
        minimum = S.decision_fact(decision, "minimum")
        maximum = S.decision_fact(decision, "maximum")
        if minimum is None or maximum is None:
            self.assertIsNone(
                minimum,
                "a decision states both bounds or neither: `minimum` and `maximum` are "
                "None exactly when no raise was legal (environment.md §3, surface.md §10); "
                "decision %d stated %r against %r" % (position, minimum, maximum),
            )
            self.assertIsNone(
                maximum,
                "a decision states both bounds or neither: `minimum` and `maximum` are "
                "None exactly when no raise was legal (environment.md §3, surface.md §10); "
                "decision %d stated %r against %r" % (position, minimum, maximum),
            )
            return None
        for name, value in (("minimum", minimum), ("maximum", maximum)):
            self.assertTrue(
                S.is_count(value),
                "the raise interval's bounds are legal raise-to amounts, so %r is an "
                "integer count of chips (environment.md §3, sizing.md §2); decision %d "
                "stated %r" % (name, position, value),
            )
        self.assertLessEqual(
            int(minimum),
            int(maximum),
            "the interval is a closed integer interval whose lower bound is the minimum "
            "legal raise-to (sizing.md §2); decision %d stated (%r, %r)"
            % (position, minimum, maximum),
        )
        return int(minimum), int(maximum)

    def legal_names(self, legal):
        """The declared descriptors of a legal sequence, in the sequence's order."""
        descriptors = S.descriptor_list(legal, "legal_actions")
        names = [declared_name(descriptor) for descriptor in descriptors]
        self.assertNotIn(
            None,
            names,
            "a descriptor names one of its shape's declared actions, so every legal entry "
            "names a declared descriptor (surface.md §2, §6); the decision offered %r"
            % (descriptors,),
        )
        return names

    def raise_names(self, legal):
        """Every raise descriptor of a legal sequence, the fixed shape's `raise` included."""
        return [
            name for name in self.legal_names(legal)
            if name == "raise" or name in BANDS
        ]

    def band_names(self, legal):
        """The sized shape's legal raise descriptors, in the sequence's order."""
        return [name for name in self.legal_names(legal) if name in BANDS]

    def decisions_of(self, episode):
        return S.decision_list(episode)

    def sized_episode(self, seed, pattern):
        """One no-limit episode played by a policy that asks for the given bands in turn."""
        return self.play_hand(
            seed,
            S.PolicyProbe(CycleBands(pattern), name="seat 0"),
            S.PolicyProbe(CycleBands(pattern), name="seat 1"),
            S.SHAPE_SIZED,
        )

    def replayed(self, seed, prefix, target, answer, shape=None):
        """The episode in which the prefix is replayed and decision ``target`` answers ``answer``."""
        seat0 = S.PolicyProbe(Replay(prefix, target, answer), name="seat 0")
        seat1 = S.PolicyProbe(Replay(prefix, target, answer), name="seat 1")
        try:
            return self.play_hand(seed, seat0, seat1, S.SHAPE_SIZED if shape is None else shape)
        except ReplayMiss as miss:
            self.fail(str(miss))

    # -- the vocabulary ----------------------------------------------------
    def test_fam20_01_legal_actions_returns_the_six_descriptors_in_declared_index_order(self):
        """FAM-20.1 legal_actions returns the shape's six descriptors in its own order, which is not amount order (§6, sizing.md §3)."""
        declared = tuple(S.descriptor_list(self.sized_row()["actions"], "the sized row's actions"))
        self.assertEqual(
            declared,
            DECLARED_SIZED,
            "the sized row declares fold, check-call and the four bands in its index order "
            "(surface.md §12, sizing.md §3): the catalogue declared %r" % (declared,),
        )
        for seed in (S.SEED_Q, S.SEED_R, S.SEED_S):
            hand = self.new_hand(seed, S.SHAPE_SIZED)
            legal = S.descriptor_list(self.legal_actions(hand), "legal_actions")
            names = [declared_name(descriptor) for descriptor in legal]
            self.assertEqual(
                names,
                list(declared),
                "legal_actions returns the hand's own shape's descriptors in that shape's "
                "declared index order (surface.md §6, sizing.md §3): the first decision of "
                "seed %r returned %r" % (seed, legal),
            )
            self.assertEqual(
                len(names),
                len(declared),
                "at the first decision of a no-limit hand every declared action is legal — "
                "the button owes the big blind a chip, so folding, calling and all four "
                "bands are available (surface.md §6, sizing.md §2): seed %r returned %r"
                % (seed, legal),
            )
            positions = dict((name, index) for index, name in enumerate(names))
            self.assertLess(
                positions["raise-all-in"],
                positions["raise-minimum"],
                "the declared order is the measured price order, worst first, so the "
                "all-in sits before the minimum and the order is not monotone in amount "
                "(sizing.md §3, D-29): the first decision of seed %r returned %r"
                % (seed, legal),
            )
            self.assertEqual(
                S.canon(S.required(self.readout(hand), "the readout", "legal")),
                S.canon(legal),
                "legal_actions returns the same sequence in value and order as the "
                "readout's `legal` fact (surface.md §6, environment.md §2)",
            )

    # -- the resolutions ---------------------------------------------------
    def test_fam20_02_the_first_decision_resolves_four_distinct_amounts(self):
        """FAM-20.2 at the first no-limit decision the four bands resolve to 4, 28, 52 and 100, pairwise distinct (sizing.md §2)."""
        for seed in (S.SEED_Q, S.SEED_R, S.SEED_S):
            measured = {}
            for band in BANDS:
                decision = self.decisions_of(self.replayed(seed, (), 0, band))[0]
                bounds = self.bounds(decision, 0)
                self.assertIsNotNone(
                    bounds,
                    "a fresh no-limit hand's first decision faces the big blind, so a raise "
                    "is legal and the record states the interval's bounds (surface.md §10, "
                    "sizing.md §2): seed %r stated none" % (seed,),
                )
                self.assertEqual(
                    bounds,
                    (FIRST_MINIMUM, FIRST_MAXIMUM),
                    "the first no-limit decision's minimum raise-to is 4 and its all-in "
                    "raise-to is the 100-chip stack (sizing.md §2, shapes.md §2): seed %r "
                    "stated %r" % (seed, bounds),
                )
                expected = resolutions(*bounds)[band]
                amount = S.decision_fact(decision, "amount")
                measured[band] = amount
                self.assertEqual(
                    amount,
                    expected,
                    "a sized descriptor resolves to its own band's maximum — `raise-minimum` "
                    "to m, `raise-quarter` to m + ⌊L/4⌋, `raise-half` to m + ⌊L/2⌋ and "
                    "`raise-all-in` to A (sizing.md §2, surface.md §7): with bounds %r, %r "
                    "resolved to %r, not %r" % (bounds, band, amount, expected),
                )
            self.assertEqual(
                measured,
                {
                    "raise-quarter": 28,
                    "raise-half": 52,
                    "raise-all-in": 100,
                    "raise-minimum": 4,
                },
                "with m = 4, A = 100 and L = 96 the four bands resolve to 4, 28, 52 and 100 "
                "(sizing.md §2): seed %r resolved %r" % (seed, measured),
            )
            self.assertEqual(
                len(set(measured.values())),
                len(BANDS),
                "the four bands resolve to four amounts, so two descriptors never claim one "
                "amount at one decision (sizing.md §2): seed %r resolved %r"
                % (seed, measured),
            )

    def test_fam20_03_every_decisions_raise_resolves_to_its_own_bands_maximum(self):
        """FAM-20.3 over several hands the legal raise set is the band arithmetic and a chosen raise's amount is its band's maximum (§6, §7, sizing.md §2)."""
        chosen = dict((band, 0) for band in BANDS)
        masked = 0
        spans = set()
        for seed in (S.SEED_Q, S.SEED_R, S.SEED_S, S.SEED_T, S.SEED_V):
            for pattern in (("raise-quarter",), ("raise-minimum",),
                            ("raise-quarter", "raise-half"), ("raise-all-in",)):
                decisions = self.decisions_of(self.sized_episode(seed, pattern))
                for position, decision in enumerate(decisions):
                    bounds = self.bounds(decision, position)
                    legal = S.decision_fact(decision, "legal")
                    present = self.band_names(legal)
                    amount = S.decision_fact(decision, "amount")
                    if bounds is None:
                        self.assertEqual(
                            present,
                            [],
                            "a decision whose record states no interval offers no raise "
                            "descriptor: `minimum`/`maximum` are None exactly when no raise "
                            "was legal (environment.md §3, surface.md §6): decision %d of "
                            "seed %r offered %r" % (position, seed, legal),
                        )
                        self.assertIsNone(
                            amount,
                            "no raise was legal, so no raise was applied and `amount` is "
                            "None (environment.md §3): decision %d of seed %r stated %r"
                            % (position, seed, amount),
                        )
                        continue
                    expected = legal_bands(*bounds)
                    self.assertEqual(
                        present,
                        expected,
                        "a raise descriptor appears only when its band holds at least one "
                        "legal amount, and a band with no legal integer in it is masked out, "
                        "never collapsed onto its neighbour (surface.md §6, sizing.md §2): "
                        "decision %d of seed %r stated bounds %r and offered %r against the "
                        "arithmetic's %r"
                        % (position, seed, bounds, present, expected),
                    )
                    spans.add(bounds[1] - bounds[0])
                    if len(present) < len(BANDS):
                        masked += 1
                    action = S.decision_fact(decision, "action")
                    band = band_name(action)
                    if band is None:
                        self.assertIsNone(
                            amount,
                            "`amount` is the raise-to the engine resolved and is None "
                            "whenever the chosen descriptor is not a raise (environment.md "
                            "§3, surface.md §10): decision %d of seed %r chose %r and stated "
                            "%r" % (position, seed, action, amount),
                        )
                        continue
                    chosen[band] += 1
                    self.assertEqual(
                        amount,
                        resolutions(*bounds)[band],
                        "every raise resolves to its own band's maximum (sizing.md §2, "
                        "surface.md §7): decision %d of seed %r chose %r with bounds %r and "
                        "resolved to %r, not %r"
                        % (position, seed, band, bounds, amount, resolutions(*bounds)[band]),
                    )
                    self.assertGreaterEqual(
                        amount,
                        bounds[0],
                        "the resolved raise-to lies inside the legal interval, whose lower "
                        "bound is the minimum legal raise-to (sizing.md §2): decision %d of "
                        "seed %r resolved to %r against %r"
                        % (position, seed, amount, bounds),
                    )
                    self.assertLessEqual(
                        amount,
                        bounds[1],
                        "the resolved raise-to lies inside the legal interval, whose upper "
                        "bound is the all-in raise-to (sizing.md §2): decision %d of seed %r "
                        "resolved to %r against %r" % (position, seed, amount, bounds),
                    )
        for band in BANDS:
            self.assertGreaterEqual(
                chosen[band],
                1,
                "the battery's own drive must choose %r at least once, or this case says "
                "nothing about its resolution (sizing.md §2): the sample chose %r"
                % (band, chosen),
            )
        self.assertGreaterEqual(
            masked,
            1,
            "the sample must contain a decision whose raise set is masked, so the empty-band "
            "rule is exercised and not merely stated (surface.md §6, sizing.md §2): the "
            "spans reached were %r" % (sorted(spans),),
        )
        # Every legal band at every decision of one hand, each chosen in turn by replaying
        # the same prefix, so no band's resolution is left to the arithmetic alone.
        seed = S.SEED_Q
        source = self.decisions_of(self.sized_episode(seed, ("raise-quarter", "raise-half")))
        resolved = 0
        for position, decision in enumerate(source):
            if self.bounds(decision, position) is None:
                continue
            prefix = [S.decision_fact(earlier, "action") for earlier in source[:position]]
            for band in self.band_names(S.decision_fact(decision, "legal")):
                replayed = self.decisions_of(self.replayed(seed, prefix, position, band))
                bounds = self.bounds(replayed[position], position)
                self.assertEqual(
                    S.canon(bounds),
                    S.canon(self.bounds(decision, position)),
                    "the replay is the same decision — one seed, one prefix and one shape "
                    "declare one raise interval (surface.md §6, sizing.md §2): decision %d of "
                    "seed %r stated %r in the replay against %r in the source"
                    % (position, seed, bounds, self.bounds(decision, position)),
                )
                amount = S.decision_fact(replayed[position], "amount")
                self.assertEqual(
                    amount,
                    resolutions(*bounds)[band],
                    "every legal raise descriptor resolves to its own band's maximum, so no "
                    "band's amount is left to a neighbour (sizing.md §2, surface.md §7): "
                    "decision %d of seed %r chose %r with bounds %r and resolved to %r, not "
                    "%r" % (position, seed, band, bounds, amount, resolutions(*bounds)[band]),
                )
                resolved += 1
        self.assertGreaterEqual(
            resolved,
            len(BANDS),
            "the sweep must resolve at least one legal band per descriptor, or a band's "
            "resolution is untested (sizing.md §2): it resolved %d" % (resolved,),
        )

    def test_fam20_04_an_empty_band_is_masked_out_and_never_collapsed(self):
        """FAM-20.4 at the spans the drive reaches, an empty band is absent from legal_actions and never collapsed onto a neighbour (§6, sizing.md §2)."""
        patterns = (
            ("raise-quarter",),
            ("raise-minimum",),
            ("raise-quarter", "raise-half"),
            ("raise-quarter", "raise-quarter", "raise-half"),
        )
        reached = {}
        for pattern in patterns:
            for seed in (S.SEED_Q, S.SEED_R, S.SEED_S, S.SEED_U):
                decisions = self.decisions_of(self.sized_episode(seed, pattern))
                for position, decision in enumerate(decisions):
                    bounds = self.bounds(decision, position)
                    if bounds is None:
                        continue
                    minimum, maximum = bounds
                    span = maximum - minimum
                    present = self.band_names(S.decision_fact(decision, "legal"))
                    self.assertEqual(
                        present,
                        legal_bands(minimum, maximum),
                        "a raise descriptor appears only when its band holds a legal "
                        "amount, so the legal raise set is the band arithmetic of the "
                        "decision's own bounds (surface.md §6, sizing.md §2): decision %d of "
                        "seed %r stated (%r, %r) and offered %r"
                        % (position, seed, minimum, maximum, present),
                    )
                    if span >= 4:
                        self.assertEqual(
                            present,
                            list(BANDS),
                            "a span of at least four gives every band its own amount, so "
                            "all four raise descriptors are legal and none is masked "
                            "(sizing.md §2): decision %d of seed %r stated a span of %d and "
                            "offered %r" % (position, seed, span, present),
                        )
                        continue
                    reached.setdefault(span, (seed, position, bounds, present))
                    if span == 0:
                        self.assertEqual(
                            present,
                            ["raise-minimum"],
                            "at a span of 0 the all-in band (m + ⌊L/2⌋, A] is empty, so "
                            "`raise-minimum` alone is legal and the all-in is masked out, "
                            "never collapsed onto its neighbour (sizing.md §2, "
                            "surface.md §6): decision %d of seed %r stated (%r, %r) and "
                            "offered %r" % (position, seed, minimum, maximum, present),
                        )
                    elif span == 1:
                        self.assertEqual(
                            present,
                            ["raise-all-in", "raise-minimum"],
                            "at a span of 1 the legal raise descriptors are exactly "
                            "`raise-minimum` and `raise-all-in`, in the declared index order: "
                            "the quarter and half bands own no integer and are masked out, "
                            "never collapsed onto a neighbour (sizing.md §2, surface.md §6): "
                            "decision %d of seed %r stated (%r, %r) and offered %r"
                            % (position, seed, minimum, maximum, present),
                        )
                    elif span in (2, 3):
                        self.assertEqual(
                            present,
                            ["raise-half", "raise-all-in", "raise-minimum"],
                            "below a span of 4 the quarter band owns no integer, so "
                            "`raise-quarter` is masked out and never collapsed onto "
                            "`raise-half`; the half band and the all-in still own their own "
                            "amounts (sizing.md §2, surface.md §6): decision %d of seed %r "
                            "stated (%r, %r) and offered %r"
                            % (position, seed, minimum, maximum, present),
                        )
        for span in (0, 1, 2, 3):
            self.assertIn(
                span,
                reached,
                "the battery's drive must reach a span of %d for this case to say anything "
                "about that band being empty (sizing.md §2): the spans reached were %r"
                % (span, sorted(reached)),
            )

    def test_fam20_05_the_four_bands_resolve_pairwise_distinctly_when_the_span_allows(self):
        """FAM-20.5 at a mid-hand decision where every band is legal, the four bands resolve to four distinct amounts (§2)."""
        seed = S.SEED_T
        decisions = self.decisions_of(self.sized_episode(seed, ("raise-minimum",)))
        candidates = []
        for position, decision in enumerate(decisions):
            if self.bounds(decision, position) is None:
                continue
            if len(self.band_names(S.decision_fact(decision, "legal"))) == len(BANDS):
                candidates.append(position)
        self.assertTrue(
            candidates,
            "the drive must reach a decision where every band is legal, or this case says "
            "nothing about two bands resolving apart (sizing.md §2): seed %r recorded %d "
            "decisions" % (seed, len(decisions)),
        )
        # The last such decision: the shortest span the four bands share, so the case is
        # not a second reading of the fresh hand's first decision.
        target = candidates[-1]
        self.assertGreaterEqual(
            target,
            1,
            "the case replays a decision after the first, whose prefix is not empty, so the "
            "bands are resolved at a mid-hand interval and not only at the deal "
            "(sizing.md §2): seed %r offered every band only at decision 0" % (seed,),
        )
        source = self.bounds(decisions[target], target)
        self.assertGreaterEqual(
            source[1] - source[0],
            4,
            "four bands are legal only where the span leaves each of them an integer "
            "(sizing.md §2): the target decision stated %r" % (source,),
        )
        prefix = [S.decision_fact(decision, "action") for decision in decisions[:target]]
        measured = {}
        for band in BANDS:
            replayed = self.decisions_of(self.replayed(seed, prefix, target, band))
            replayed_bounds = self.bounds(replayed[target], target)
            self.assertEqual(
                replayed_bounds,
                source,
                "the replay is the same decision — one seed, one prefix and one shape "
                "declare one raise interval (surface.md §6, sizing.md §2): the replay of "
                "%r stated %r against the source's %r"
                % (band, replayed_bounds, source),
            )
            amount = S.decision_fact(replayed[target], "amount")
            measured[band] = amount
            self.assertEqual(
                amount,
                resolutions(*source)[band],
                "every band resolves to its own maximum, so the amount is the arithmetic's "
                "and not a neighbour's (sizing.md §2, surface.md §7): %r resolved to %r "
                "against %r with bounds %r"
                % (band, amount, resolutions(*source)[band], source),
            )
        self.assertEqual(
            len(set(measured.values())),
            len(BANDS),
            "each band resolves to its own maximum, so two descriptors never resolve to one "
            "amount at one decision (sizing.md §2): the four resolved %r" % (measured,),
        )

    # -- the three amount facts -------------------------------------------
    def test_fam20_06_the_episode_carries_the_three_amount_facts_on_both_shapes(self):
        """FAM-20.6 every decision of both shapes carries amount, minimum and maximum with their declared None rules, and the readout keeps eleven facts (§10, environment.md §3)."""
        seen = {"fold": 0, "check-call": 0, "raise": 0}
        for shape in (S.SHAPE_DEFAULT, S.SHAPE_SIZED):
            for seed in (S.SEED_Q, S.SEED_S):
                for choosers in ((S.choose_raise, S.choose_fold), (S.choose_call, S.choose_call)):
                    episode = self.play_hand(
                        seed,
                        S.PolicyProbe(choosers[0], name="seat 0"),
                        S.PolicyProbe(choosers[1], name="seat 1"),
                        shape,
                    )
                    decisions = self.decisions_of(episode)
                    self.assertTrue(
                        decisions,
                        "an episode of a hand records its decisions (records.md §5): shape "
                        "%r seed %r recorded none" % (shape, seed),
                    )
                    for position, decision in enumerate(decisions):
                        for fact in S.DECISION_AMOUNT_FACTS:
                            S.decision_fact(decision, fact)
                        readout = S.decision_fact(decision, "readout")
                        self.assertEqual(
                            set(readout),
                            set(S.READOUT_FACTS),
                            "the decision's readout is the whole eleven-fact mapping of its "
                            "shape, so the bounds are the record's and never a twelfth fact "
                            "(environment.md §3, surface.md §5): decision %d of shape %r "
                            "carried %r"
                            % (position, shape, sorted(str(key) for key in readout)),
                        )
                        bounds = self.bounds(decision, position)
                        legal = S.decision_fact(decision, "legal")
                        present = self.raise_names(legal)
                        self.assertEqual(
                            bounds is None,
                            not present,
                            "`minimum` and `maximum` are the legal raise interval's bounds "
                            "and are None exactly when no raise was legal (environment.md "
                            "§3, surface.md §10): decision %d of shape %r stated %r while "
                            "legal_actions offered %r"
                            % (position, shape, bounds, legal),
                        )
                        action = S.decision_fact(decision, "action")
                        kind = S.descriptor_kind(action)
                        amount = S.decision_fact(decision, "amount")
                        if kind == "fold":
                            seen["fold"] += 1
                            self.assertIsNone(
                                amount,
                                "`amount` is the raise-to the engine resolved and is None "
                                "whenever the chosen descriptor is not a raise, so a fold "
                                "states None (environment.md §3, surface.md §10): decision "
                                "%d of shape %r chose %r and stated %r"
                                % (position, shape, action, amount),
                            )
                        elif kind == "check-call":
                            seen["check-call"] += 1
                            self.assertIsNone(
                                amount,
                                "a check/call is not a raise, so its `amount` is None "
                                "(environment.md §3, surface.md §10): decision %d of shape "
                                "%r chose %r and stated %r"
                                % (position, shape, action, amount),
                            )
                        else:
                            seen["raise"] += 1
                            self.assertIsNotNone(
                                amount,
                                "a raise states the raise-to the engine resolved "
                                "(environment.md §3, surface.md §10): decision %d of shape "
                                "%r chose %r and stated None"
                                % (position, shape, action),
                            )
                            self.assertGreaterEqual(
                                amount,
                                bounds[0],
                                "the resolved raise-to lies inside the decision's own legal "
                                "interval (sizing.md §2): decision %d of shape %r resolved "
                                "to %r against %r"
                                % (position, shape, amount, bounds),
                            )
                            self.assertLessEqual(
                                amount,
                                bounds[1],
                                "the resolved raise-to lies inside the decision's own legal "
                                "interval (sizing.md §2): decision %d of shape %r resolved "
                                "to %r against %r"
                                % (position, shape, amount, bounds),
                            )
                            if shape == S.SHAPE_DEFAULT:
                                self.assertEqual(
                                    (bounds[0], bounds[1], amount),
                                    (amount, amount, amount),
                                    "the fixed-limit `raise` resolves to the minimum legal "
                                    "completion, which for that shape is both bounds, so "
                                    "minimum == maximum == amount (environment.md §3, "
                                    "sizing.md §2): decision %d resolved to %r against %r"
                                    % (position, amount, bounds),
                                )
        for kind in ("fold", "check-call", "raise"):
            self.assertGreaterEqual(
                seen[kind],
                1,
                "the battery's own policies must produce a %r decision on both shapes, or "
                "its amount rule is untested (environment.md §3): the sample saw %r"
                % (kind, seen),
            )

    # -- the step and the fixed shape --------------------------------------
    def test_fam20_07_a_foreign_shapes_descriptor_is_refused_on_both_shapes(self):
        """FAM-20.7 apply_action accepts every legal sized descriptor and refuses the other shape's vocabulary (§6, §7)."""
        for seed in (S.SEED_Q, S.SEED_S):
            legal = S.descriptor_list(
                self.legal_actions(self.new_hand(seed, S.SHAPE_SIZED)), "legal_actions"
            )
            self.assertEqual(
                [declared_name(descriptor) for descriptor in legal],
                list(DECLARED_SIZED),
                "the first no-limit decision offers every declared descriptor (surface.md "
                "§6, sizing.md §2): seed %r offered %r" % (seed, legal),
            )
            for descriptor in legal:
                advanced = self.apply_action(
                    self.new_hand(seed, S.SHAPE_SIZED), descriptor
                )
                self.assertIsInstance(
                    self.is_terminal(advanced),
                    bool,
                    "every descriptor legal_actions returns is one apply_action accepts at "
                    "that decision (surface.md §6, §7): seed %r refused or mangled %r"
                    % (seed, descriptor),
                )
        sized = self.new_hand(S.SEED_Q, S.SHAPE_SIZED)
        fixed = self.new_hand(S.SEED_Q)
        self.assertEqual(
            [declared_name(descriptor, DECLARED_FIXED)
             for descriptor in S.descriptor_list(self.legal_actions(fixed), "legal_actions")],
            list(DECLARED_FIXED),
            "the default shape keeps its three descriptors and declares none of the four "
            "bands (surface.md §2, shapes.md §5): the fixed hand offered %r"
            % (self.legal_actions(fixed),),
        )
        before_sized = S.canon(self.readout(sized))
        before_fixed = S.canon(self.readout(fixed))
        self.assert_refused(
            lambda: self.apply_action(sized, "raise"),
            "apply_action with the fixed-limit shape's `raise` on a no-limit hand",
            ("action", "descriptor", "legal"),
        )
        for band in BANDS:
            self.assert_refused(
                lambda band=band: self.apply_action(fixed, band),
                "apply_action with the sized shape's %r on a fixed-limit hand" % (band,),
                ("action", "descriptor", "legal"),
            )
        self.assertEqual(
            S.canon(self.readout(sized)),
            before_sized,
            "a refused descriptor neither advances the hand nor changes its facts "
            "(surface.md §7)",
        )
        self.assertEqual(
            S.canon(self.readout(fixed)),
            before_fixed,
            "a refused descriptor neither advances the hand nor changes its facts "
            "(surface.md §7)",
        )

    def test_fam20_08_the_fixed_limit_shape_keeps_its_single_raise(self):
        """FAM-20.8 on the default shape the one raise resolves to the minimum completion, with minimum == maximum == amount (§7, environment.md §3)."""
        for seed in (S.SEED_Q, S.SEED_T):
            episode = self.play_hand(
                seed,
                S.PolicyProbe(S.choose_raise, name="seat 0"),
                S.PolicyProbe(S.choose_raise, name="seat 1"),
            )
            decisions = self.decisions_of(episode)
            self.assertTrue(
                decisions,
                "an episode of a hand records its decisions (records.md §5): seed %r "
                "recorded none" % (seed,),
            )
            for position, decision in enumerate(decisions):
                legal = S.decision_fact(decision, "legal")
                names = [declared_name(descriptor, DECLARED_FIXED)
                         for descriptor in S.descriptor_list(legal, "legal_actions")]
                for name in names:
                    self.assertIn(
                        name,
                        DECLARED_FIXED,
                        "the default shape's vocabulary is fold, check-call and raise, and "
                        "a sized descriptor is not an action of it (surface.md §2, "
                        "shapes.md §5): decision %d of seed %r offered %r"
                        % (position, seed, legal),
                    )
                bounds = self.bounds(decision, position)
                if bounds is None:
                    self.assertNotIn(
                        "raise",
                        names,
                        "the fixed-limit raise is legal exactly where the record states an "
                        "interval (environment.md §3, surface.md §6): decision %d of seed "
                        "%r stated none and offered %r" % (position, seed, legal),
                    )
                    continue
                self.assertEqual(
                    bounds[0],
                    bounds[1],
                    "the fixed-limit `raise` is the minimum legal completion, which that "
                    "shape makes unique, so the interval's bounds are one amount "
                    "(sizing.md §2, environment.md §3): decision %d of seed %r stated %r"
                    % (position, seed, bounds),
                )
                if S.descriptor_kind(S.decision_fact(decision, "action")) == "raise":
                    amount = S.decision_fact(decision, "amount")
                    self.assertEqual(
                        (bounds[0], bounds[1], amount),
                        (amount, amount, amount),
                        "the fixed-limit raise resolves to its minimum legal completion, so "
                        "minimum == maximum == amount (environment.md §3, sizing.md §2): "
                        "decision %d of seed %r stated %r against %r"
                        % (position, seed, bounds, amount),
                    )
        first = self.decisions_of(
            self.play_hand(
                S.SEED_Q,
                S.PolicyProbe(S.choose_raise, name="seat 0"),
                S.PolicyProbe(S.choose_call, name="seat 1"),
            )
        )[0]
        self.assertEqual(
            self.bounds(first, 0),
            (4, 4),
            "at the first decision of a 2/4 game the minimum legal completion is 4 and it "
            "is the whole interval (environment.md §3, ASM-6): it stated %r"
            % (self.bounds(first, 0),),
        )
        self.assertEqual(
            S.decision_fact(first, "amount"),
            4,
            "the fixed-limit `raise` resolves to the minimum legal completion, 4 at the "
            "first decision of a 2/4 game (environment.md §3, sizing.md §2): it resolved "
            "to %r" % (S.decision_fact(first, "amount"),),
        )


if __name__ == "__main__":
    unittest.main()
