"""FAM-24 — the [0, 1] input invariant: what both encodings emit, and where a slot caps.

`docs/L1/battery.md` §3 FAM-24, `docs/L1/normalisation.md` §2–§5, `docs/L1/e2e-surface.md`
§2 ("Readout facts", "Game shape", "Observation spec") and §3, D-61.  D-60 measured the input
path dead — O(100) rewards drove input weights to 313 and every pre-activation onto the
negative side — and D-61 answers the input term of that chain: **both encodings emit values
in [0, 1]**, and every magnitude slot that can reach its denominator is held there by one
documented saturation rule.

`normalisation.md` §5 states the invariant in two halves, and §5 and `battery.md` §5 place
each half in exactly one battery.  This file is the **layer-level** half, asserted through
declared entry points only (`battery.md` §2):

* **INV-1 (dense)** — every slot of every `flat-numeric` observation `features.encode` emits,
  on every declared shape, lies in `[0, 1]` (FAM-24.1);
* **INV-2's first part (tokens)** — every slot of every `card-tokens` observation is an
  integer inside the shape's declared vocabulary, so the pad `0` is legal and nothing is
  negative (FAM-24.2);
* **the saturation rule** — a readout whose magnitude exceeds its shape's denominator — a
  readout the engine would never deal but the encoder accepts — encodes to exactly `1.0`,
  never to a value above 1, and a readout sitting exactly at the shape's own normalisers
  reads exactly `1.0`, because the bound is a ceiling and not a clip below it
  (`normalisation.md` §4, FAM-24.3);
* **the widths** — each encoding's declared shape and a shaped learner's `param_count` are
  the values they were before the change, because D-61 moves what a value *means* and not
  the layout (`normalisation.md` §1, FAM-24.4);
* **the join** — both encodings still carry the same nine fields and still accept a readout
  the engine produced on every declared shape (FAM-24.5).

The cases are:

* **FAM-24.1** a sweep of real hands over all three declared shapes asserts every slot of
  every `flat-numeric` observation is in `[0, 1]`, on a decision of each shape at every
  street the sweep reaches — with `card-tokens` encoded from the same decisions beside it, so
  both encodings run over the whole sweep — reporting shape, encoding, street, slot index
  and value on failure.
* **FAM-24.2** the same sweep for `card-tokens`: every slot is a plain `int` in
  `[0, vocabulary)`, with the vocabulary read from `features.observation_spec` and never
  hard-coded as an expectation.
* **FAM-24.3** a readout built past the six-seat shape's denominators — `stacks` far above
  the starting stack, `pot` above the chips in play, `to_call` above the stack, `limit` above
  its normalisers — encodes to exactly `1.0` in each magnitude slot and to nothing above
  `1.0` anywhere; and a readout exactly at each declared shape's own normalisers reads
  exactly `1.0` (`normalisation.md` §4).
* **FAM-24.4** each shape and encoding reports the width it had before the change, and one
  learner of **each family** on each declared shape, built from that shape's own encoder,
  reports a positive `agents.param_count` that follows that shape's width (`normalisation.md`
  §1, `e2e-surface.md` §3.2–§3.3).
* **FAM-24.5** both encodings carry the same nine fields and accept one readout on every
  declared shape, so normalisation refused nothing the engine can produce.

The shapes, their normalisers, their vocabularies and their widths are the **design's** and
are read off `engine.game_shapes()` and `features.observation_spec`; the seeds, the walk
limit, the seam label and the probe multipliers are the battery's own (`battery.md` §4,
D-15).  The readouts of FAM-24.3 are built by hand: they are values the engine cannot deal
(`readout.md` §2, `normalisation.md` §4) and are the only way a case can observe a slot that
can saturate actually saturating.

There is deliberately **no** case here for the refusal of a readout that cannot be
normalised: no declared shape omits a denominator, and `battery.md` §5 places that structural
guard in `tests/features/`, where a row without one can be built (`normalisation.md` §4).

**FAM-24.3 is the case that holds `normalisation.md` §4's clamp.**  Measured, not assumed:
against a writer that divides by the shape's normaliser and does not clamp, the probe readout
below encodes its six `stacks` slots as `6.0` — 600 over a divisor of 100 — its `pot` as
`3.0`, its `to_call` as `3.0` and both `limit` slots as `3.0`, so FAM-24.3 fails on a value
above 1 while FAM-24.1, .2, .4 and .5 pass, because no readout a hand can deal ever crosses
its shape's denominator (`normalisation.md` §2; the largest dense slot a sweep of real hands
reaches is `1.0`, on an indicator and on a six-seat stack of 100 over 100).  With §4's
`min(1, numerator / denominator)` in the encode loop the same readout reads exactly `1.0` and
the case passes — the second state was measured the same way, against the encoder that
carries the clamp.  Red before the clamp is the expected state of a design-stage case and
"completable" is what matters (`battery.md` §1, `strata/examiner.md` §3).
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

#: The two declared encodings, by the names `features.encodings` declares (D-3).
FLAT = S.FLAT
TOKENS = S.TOKENS

#: The four streets `e2e-surface.md` §2 names for the readout's `street` fact, in the order
#: the readout reports them.  The sweep asserts a decision of each shape was encoded at every
#: one of them, so "several streets" is a measured fact and not an assumption.
STREETS = ("preflop", "flop", "turn", "river")

#: The invented seed set the sweep walks — the battery's own, five of `_surface`'s ten
#: (`battery.md` §4, D-15).  Five seeds reach every street on every declared shape with a
#: policy that never folds, and one hand per shape is driven by a `harness.seam` policy
#: beside them so the family's seam row is exercised on real readouts (`e2e-surface.md` §3.6).
SWEEP_SEEDS = S.SHAPE_SEEDS[:5]

#: The most decisions one walked hand may spend.  A no-limit hand ends sooner than a
#: fixed-limit one (an all-in raise is legal at every decision), so the limit is a guard and
#: never a truncation a case depends on.
WALK_LIMIT = 120

#: The seed and the label of the seam-driven hand: `synthetic` is the documented behaviour
#: that walks the legal set, so the hand is a real episode and not a fold on its first
#: decision (`e2e-surface.md` §3.6).  The seed is the battery's own.
SEAM_SEED = S.SEED_J
SEAM_LABEL = "synthetic"

#: The probe multipliers FAM-24.3 drives the six-seat shape's denominators past: the battery's
#: own numbers (`battery.md` §4, D-15), each applied to the shape's **own** normaliser so no
#: denominator is written down here.  Six is the ratio of the six-seat row's pot normaliser to
#: its stack normaliser — a stack of `6 × stack` is far above the 100-chip starting stack —
#: and three keeps the readout small enough that a float32 states every product exactly.
STACK_MULTIPLE = 6
POT_MULTIPLE = 3
TO_CALL_MULTIPLE = 3
LIMIT_MULTIPLE = 3

#: The two readout facts no encoding carries: `legal` is the engine's order and not a fact of
#: the information set, and `hand_class` is derived from facts already present
#: (`e2e-surface.md` §2, `folders.md` §3, ASM-30).  The nine carried facts are the eleven of
#: `e2e-surface.md` §2 less these two (`normalisation.md` §1, `fields` in the spec record).
NOT_CARRIED = ("legal", "hand_class")

#: The nine fields both encodings carry, derived from the readout's declared facts and never
#: spelled a second time here (`e2e-surface.md` §2, D-13).
CARRIED_FIELDS = tuple(fact for fact in S.READOUT_FACTS if fact not in NOT_CARRIED)

#: The width each declared encoding declares on each declared shape — `shapes.md` §8's
#: layout, which D-61 keeps and which is therefore the value it was before the change: the
#: dense row is `131 + 3 × capacity` and the token row `16 + capacity` over the shape's own
#: seat count, so 203, 329 and 433 dense and 40, 82 and 122 tokens on `fixed-limit-20`,
#: `no-limit-100` and `six-seat-no-limit-100` (`normalisation.md` §1, §3, `shapes.md` §8,
#: ASM-44).  These are the design's declared numbers and not instances the battery invents:
#: the shape catalogue is a `fixed` row, and FAM-24.4 is the case the row's "the widths are
#: unchanged" clause is written for (`battery.md` §3, §4, `e2e-surface.md` §5).
WIDTHS = {
    S.SHAPE_DEFAULT: {FLAT: 203, TOKENS: 40},
    S.SHAPE_SECOND: {FLAT: 329, TOKENS: 82},
    S.SHAPE_THIRD: {FLAT: 433, TOKENS: 122},
}

#: The walks this family reads, built once per process and keyed by shape: the sweep is
#: deterministic from its seeds and its shape (ASM-2), so a second case that re-walked it
#: would pay for the same hands (`battery.md` §2).
_SWEEPS = {}


def sweep(case, shape):
    """Every readout a real hand of ``shape`` produces, as ``[(seed, readout)]``.

    One hand per seed of :data:`SWEEP_SEEDS` is driven through the declared engine entry
    points — `engine.new_hand`, `engine.readout`, `engine.legal_actions`,
    `engine.apply_action`, `engine.is_terminal` — by a policy that never folds, so the hand
    reaches the river on every shape; one further hand is driven by a `harness.seam` policy,
    which satisfies the same policy protocol (``e2e-surface.md`` §2, §3.6); and one whole
    episode per shape is played through `engine.play_hand`, whose every decision record
    carries a `readout` — a **required** key of ``records.md`` §5 — so the facts the episode
    path hands a learner are swept beside the ones a decision walk reads.  Every decision is
    one entry, in the order the engine produced them, and the cases below encode each of
    them with both encodings.
    """
    if shape in _SWEEPS:
        return _SWEEPS[shape]
    entries = []
    policy = case.baseline("always-call", S.SEED_D, shape)
    for seed in SWEEP_SEEDS:
        for _hand, readout, _legal, _action, _index in case.decision_walk(
            seed, policy, limit=WALK_LIMIT, shape=shape
        ):
            entries.append((seed, readout))
    seam = case.ep("harness", "seam")(SEAM_LABEL)
    for _hand, readout, _legal, _action, _index in case.decision_walk(
        SEAM_SEED, seam, limit=WALK_LIMIT, shape=shape
    ):
        entries.append((SEAM_SEED, readout))
    seats = case.seats_of(shape)
    episode_seat = S.SEED_C
    record = case.play(
        episode_seat,
        shape=shape,
        seats=[case.baseline("always-call", S.SEED_D, shape) for _seat in range(seats)],
    )
    for decision in S.declared_field(
        record, "an episode record (records.md §5)", "decisions"
    ):
        entries.append(
            (
                episode_seat,
                S.declared_field(
                    decision, "a decision record (records.md §5)", "readout"
                ),
            )
        )
    _SWEEPS[shape] = entries
    return entries


def slots(observation):
    """One observation as a plain Python list of its slots, in slot order.

    The array's backend is the implementation's freedom — `float32` for the dense encoding
    and `int32` for the token one (`features.observation_spec`'s `dtype`) — so the slots are
    read through :func:`_surface.numbers`, which flattens a sequence, a mapping or anything
    carrying `tolist()` and never assumes a type this battery made up.
    """
    return list(S.numbers(observation))


def moved_slots(base, probe):
    """The slot indices two observations of one encoder disagree at, in slot order.

    FAM-24.3 needs the indices of the magnitude slots of a hand-built readout, and the
    declaration's block offsets are not part of the surface (`e2e-surface.md` §1: nothing
    below an entry point is).  Encoding two readouts that differ **only** in the magnitude
    facts and reading which slots moved locates them through `features.encode` itself, so
    the case holds no copy of a block table (`battery.md` §2: an outcome, never a restating
    of an implementation).
    """
    return [
        index
        for index, (left, right) in enumerate(zip(slots(base), slots(probe)))
        if float(left) != float(right)
    ]


def hand_built_readout(stacks, pot, to_call, limit):
    """One readout the engine would never deal, in the shape `e2e-surface.md` §2 declares.

    The nine facts an encoding carries are present and well formed — a street, a seat pair,
    two hole cards, a board of three, one stack per seat, the pot, the amount to call, the
    limit pair and two documented history entries (ASM-E2's four forms, `flat-numeric.md`
    §5) — so the readout is one the encoder accepts (FAM-24.3's premise).
    The **magnitudes** are the caller's: FAM-24.3 drives them past the shape's denominators,
    which is a value no hand can produce (`readout.md` §2, `normalisation.md` §4).
    """
    seats = len(stacks)
    return {
        "street": STREETS[-1],
        "seat": (seats - 1, False),
        "hole": ("Ah", "Kd"),
        "board": ("2c", "7d", "Ts"),
        "stacks": tuple(int(amount) for amount in stacks),
        "pot": int(pot),
        "to_call": int(to_call),
        "limit": tuple(int(amount) for amount in limit),
        "history": ("preflop seat 0 calls 2", "flop seat %d checks" % (seats - 1,)),
    }


class FAM24Normalisation(S.SurfaceCase):
    """INV-1, INV-2's first part, the saturation rule, and the unchanged widths."""

    # -- readers of the declared surface ----------------------------------
    def spec(self, encoder):
        """`features.observation_spec`'s six-key record for one encoder (§3.2)."""
        record = self.ep("features", "observation_spec")(encoder)
        self.assertTrue(
            S.is_mapping(record),
            "features.observation_spec returns the spec record of e2e-surface.md §2; it "
            "returned %r" % (record,),
        )
        return record

    def width_of(self, encoder):
        """The declared width of one observation, as a plain `int` (§3.2)."""
        declared = self.spec(encoder)["shape"]
        self.assertTrue(
            isinstance(declared, (tuple, list)) and len(declared) == 1,
            "an observation's declared `shape` is one dimension — the spec record's `shape` "
            "— in e2e-surface.md §2; it declared %r" % (declared,),
        )
        return int(declared[0])

    def vocabulary_of(self, encoder):
        """The token vocabulary one encoder's spec declares, or a failure naming it."""
        declared = self.spec(encoder)["vocabulary"]
        self.assertTrue(
            S.is_count(declared) and int(declared) > 0,
            "a card-tokens encoder declares the token-id cardinality it emits — "
            "e2e-surface.md §2's `vocabulary`, 96 on the two-seat rows and 102 on the "
            "six-seat one — and it declared %r" % (declared,),
        )
        return int(declared)

    def chips_in_play(self, shape):
        """`seats × starting_stack`, read off `engine.game_config` for one shape (§3.1).

        `seats.md` §2 makes the shape's chips in play `pot + sum(stacks)` at every decision,
        and `shapes.md` §2 states it as the seat count times the starting stack — 40 on the
        default row, 200 on the two-seat uncapped one and 600 on the six-seat one.  Both
        numbers are read off the surface here, so no total is written down in this file.
        """
        return self.seats_of(shape) * self.stack_of(shape)

    def normalisers(self, shape):
        """One shape row's five amount normalisers, under whatever key declares them (§2)."""
        declared = S.normalisers_of(self.shape_row(shape))
        self.assertTrue(
            S.is_mapping(declared),
            "a shape row declares its five amount normalisers as one mapping "
            "(shapes.md §2, sizing.md §5): %r" % (declared,),
        )
        for key in S.NORMALISER_KEYS:
            self.assertIn(
                key,
                declared,
                "the normalisers carry the five keys %r — the ones normalisation.md §2 "
                "divides by — and this row carries %r"
                % (S.NORMALISER_KEYS, sorted(str(name) for name in declared)),
            )
        return {key: int(declared[key]) for key in S.NORMALISER_KEYS}

    # -- FAM-24.1 ----------------------------------------------------------
    def test_fam24_1_no_dense_observation_slot_exceeds_one(self):
        """FAM-24.1 every slot of every `flat-numeric` observation of a real hand is in `[0, 1]`, at every street of all three shapes.

        INV-1 as `normalisation.md` §5 states it: every slot of every observation
        `features.encode` emits, on every declared shape, lies in `[0, 1]`.  The case walks
        real hands on the three declared shapes — the default fixed-limit row, the two-seat
        uncapped one and D-33's six-seat one — and encodes the readout of **every decision**
        with `flat-numeric` **and with `card-tokens`**, so the assertion is made on the
        values the engine actually deals, on both encodings, and not on a sample the battery
        chose; the dense slots are held to `[0, 1]` here and the token ids to their shape's
        vocabulary in FAM-24.2 over the same decisions (`normalisation.md` §3, §5).  It
        reports shape, encoding, street,
        slot index and value on failure, because a value out of range is only useful with
        the decision it came from.  It also asserts the sweep covered all four streets and
        read a non-zero value, so a case that walked nothing cannot pass.
        """
        largest = 0.0
        for shape in self.shape_names():
            encoder = self.encoder(FLAT, shape=shape)
            width = self.width_of(encoder)
            token_encoder = self.encoder(TOKENS, shape=shape)
            token_width = self.width_of(token_encoder)
            entries = sweep(self, shape)
            self.assertTrue(
                entries,
                "the sweep must produce readouts of %r for INV-1 to be asserted on real "
                "hands (normalisation.md §5, D-61): it produced none" % (shape,),
            )
            streets = set()
            for seed, readout in entries:
                street = str(S.readout_fact(readout, "street"))
                streets.add(street)
                values = slots(self.observation(encoder, readout))
                self.assertEqual(
                    len(values),
                    width,
                    "one observation of %r is %d slots wide, the width its own spec record "
                    "declares (e2e-surface.md §2): it encoded %d at seed %r, street %r"
                    % (shape, width, len(values), seed, street),
                )
                # Both encodings are driven at **every** decision of the sweep, which is
                # what FAM-24's row asks of it: the dense bound is asserted slot by slot
                # below, and the token path is encoded from the same readouts so its own
                # bound (`normalisation.md` §3) is asserted on the same decisions in
                # FAM-24.2 rather than on a second, cheaper sample.
                token_values = slots(self.observation(token_encoder, readout))
                self.assertEqual(
                    len(token_values),
                    token_width,
                    "the token encoder encodes the same decision into the %d slots its own "
                    "spec record declares, so both encodings run over every decision of the "
                    "sweep (e2e-surface.md §2, normalisation.md §3): shape %r seed %r street "
                    "%r carried %d" % (token_width, shape, seed, street, len(token_values)),
                )
                for index, value in enumerate(values):
                    self.assertGreaterEqual(
                        value,
                        0.0,
                        "INV-1 makes every slot of every dense observation lie in [0, 1] "
                        "(normalisation.md §5, D-61), and shape %r encoding %r street %r "
                        "slot %d reads %r — below the floor"
                        % (shape, FLAT, street, index, value),
                    )
                    self.assertLessEqual(
                        value,
                        1.0,
                        "INV-1 makes every slot of every dense observation lie in [0, 1] "
                        "(normalisation.md §5, D-61), and shape %r encoding %r street %r "
                        "slot %d reads %r — above the ceiling"
                        % (shape, FLAT, street, index, value),
                    )
                    if float(value) > largest:
                        largest = float(value)
            self.assertEqual(
                streets,
                set(STREETS),
                "the sweep reaches a decision of %r at every street e2e-surface.md §2 names, "
                "so the invariant is asserted past the pre-flop block and not only on it: it "
                "reached %r" % (shape, sorted(streets)),
            )
        self.assertGreater(
            largest,
            0.0,
            "the sweep read a non-zero slot somewhere, so `max(observation) <= 1` is an "
            "assertion about values and not about an all-zero array (battery.md §2: a case "
            "that cannot fail is a defect)",
        )

    # -- FAM-24.2 ----------------------------------------------------------
    def test_fam24_2_a_token_observation_is_an_integer_inside_the_vocabulary(self):
        """FAM-24.2 every slot of every `card-tokens` observation is a plain `int` in `[0, vocabulary)`, the vocabulary read off the spec.

        INV-2's first part as `normalisation.md` §3 states it: an id is a label, not a
        magnitude, so asking it to lie in `[0, 1]` asks the wrong question of the wrong
        quantity — the bound the token path owes the layer is that **every id lies in the
        shape's declared vocabulary**, 96 on the two-seat rows and 102 on the six-seat one,
        with the pad `0` the only id outside a block's own ladder.  The same sweep as
        FAM-24.1 is encoded with `card-tokens` at every decision, and the vocabulary is read
        from `features.observation_spec` and never hard-coded as an expectation, so the case
        holds for a fourth row the catalogue may declare later (`normalisation.md` §3,
        `seats.md` §3, ASM-44).  The pad is legal and nothing is negative; the sweep is
        asserted to reach both ends, so neither bound is vacuous.
        """
        for shape in self.shape_names():
            encoder = self.encoder(TOKENS, shape=shape)
            width = self.width_of(encoder)
            vocabulary = self.vocabulary_of(encoder)
            entries = sweep(self, shape)
            self.assertTrue(
                entries,
                "the sweep must produce readouts of %r for INV-2's first part to be asserted "
                "on real hands (normalisation.md §3, §5): it produced none" % (shape,),
            )
            smallest, largest = None, None
            for seed, readout in entries:
                street = str(S.readout_fact(readout, "street"))
                values = slots(self.observation(encoder, readout))
                self.assertEqual(
                    len(values),
                    width,
                    "one token observation of %r is %d slots wide, the width its own spec "
                    "record declares (e2e-surface.md §2): it encoded %d at seed %r, street "
                    "%r" % (shape, width, len(values), seed, street),
                )
                for index, value in enumerate(values):
                    self.assertTrue(
                        S.is_count(value),
                        "every token slot is a plain integer id (normalisation.md §3), and "
                        "shape %r encoding %r street %r slot %d reads %r (%s)"
                        % (shape, TOKENS, street, index, value, type(value).__name__),
                    )
                    self.assertGreaterEqual(
                        int(value),
                        0,
                        "no token id is negative — the pad 0 is the lowest id a token block "
                        "emits (normalisation.md §3, card-tokens.md §3) — and shape %r "
                        "encoding %r street %r slot %d reads %r"
                        % (shape, TOKENS, street, index, value),
                    )
                    self.assertLess(
                        int(value),
                        vocabulary,
                        "every id lies inside the vocabulary the shape's own spec record "
                        "declares (normalisation.md §3, ASM-44), and shape %r encoding %r "
                        "street %r slot %d reads %r against a vocabulary of %d"
                        % (shape, TOKENS, street, index, value, vocabulary),
                    )
                    if smallest is None or int(value) < smallest:
                        smallest = int(value)
                    if largest is None or int(value) > largest:
                        largest = int(value)
            self.assertEqual(
                smallest,
                0,
                "the pad is id 0 and is legal, so a sweep of real hands reads it at the "
                "undealt board slots and past the end of the history block "
                "(normalisation.md §3, card-tokens.md §3): the smallest id %r read on %r"
                % (smallest, shape),
            )
            self.assertGreater(
                largest,
                0,
                "and the sweep read a real id as well, so the vocabulary's interior is "
                "exercised and not only its pad (battery.md §2): the largest id %r read on "
                "%r" % (largest, shape),
            )

    # -- FAM-24.3 ----------------------------------------------------------
    def test_fam24_3_a_slot_that_can_saturate_saturates_at_exactly_one(self):
        """FAM-24.3 a readout past its shape's denominators encodes each magnitude slot to exactly `1.0` and nothing above `1.0`, and a readout exactly at the normalisers reads exactly `1.0`.

        `normalisation.md` §4 gives one saturation rule in one place: a magnitude slot — the
        five of §2 that can reach their denominator — emits `min(1, numerator / denominator)`
        and never a value above 1.  The premise has to be a readout the engine would never
        deal, because a hand cannot produce a stack above its starting stack, a pot above the
        chips in play or a call above the stack (`readout.md` §2, `normalisation.md` §2); so
        the case builds one on the six-seat shape whose `stacks` are `6 ×` the stack
        normaliser, whose `pot` is `3 ×` the chips in play, whose `to_call` is `3 ×` its
        normaliser and whose `limit` pair is `3 ×` both of its normalisers — each multiplier
        applied to the shape's **own** declared normaliser, so no denominator is written down
        here — and asserts every one of those slots reads exactly `1.0` and that nothing in
        that observation is above `1.0`.

        The magnitude slots are located by encoding two readouts that differ only in those
        facts and reading which slots moved (:func:`moved_slots`), so the block table stays
        the implementation's business.  The second half asserts the other direction of §4:
        the bound is a ceiling and not a clip below it, so a readout sitting **exactly** at
        the shape's own normalisers reads exactly `1.0` — on every declared shape, with the
        normalisers read through `engine.game_shapes()`.
        """
        shape = self.shape_names()[-1]
        self.assertGreater(
            self.seats_of(shape),
            2,
            "the case drives D-33's six-seat row, whose pot normaliser is its own 600 chips "
            "in play and whose two per-seat blocks are six slots each (seats.md §2, "
            "normalisation.md §2): the catalogue's last row declares %r seats"
            % (self.seats_of(shape),),
        )
        normalisers = self.normalisers(shape)
        seats = self.seats_of(shape)
        chips = self.chips_in_play(shape)
        starting = self.stack_of(shape)

        stack_probe = STACK_MULTIPLE * normalisers["stack"]
        pot_probe = POT_MULTIPLE * chips
        to_call_probe = TO_CALL_MULTIPLE * normalisers["to_call"]
        limit_probe = (LIMIT_MULTIPLE * normalisers["amount"],
                       LIMIT_MULTIPLE * normalisers["count"])
        self.assertGreater(
            stack_probe,
            starting,
            "the probe's stacks lie above the shape's starting stack, so the readout is one "
            "no hand can deal (readout.md §2, normalisation.md §2): %r against %r"
            % (stack_probe, starting),
        )
        self.assertGreater(
            pot_probe,
            chips,
            "and its pot lies above the chips in play, which is the largest pot a hand of "
            "this shape can reach (normalisation.md §2, seats.md §2, ASM-28): %r against %r"
            % (pot_probe, chips),
        )
        self.assertGreater(
            to_call_probe,
            starting,
            "and its amount to call lies above a whole starting stack, which no seat can be "
            "asked to add (readout.md §2): %r against %r" % (to_call_probe, starting),
        )

        # The base readout sits strictly **below** every normaliser, so the probe's slots
        # are the only ones a saturation rule can move: a base already at the ceiling would
        # encode to the same 1.0 as the probe and hide which slots were driven past
        # `normalisation.md` §2's denominators.
        base = hand_built_readout(
            stacks=(starting // 4,) * seats,
            pot=starting,
            to_call=normalisers["to_call"] // 2,
            limit=(normalisers["amount"] // 5, 1),
        )
        probe = hand_built_readout(
            stacks=(stack_probe,) * seats,
            pot=pot_probe,
            to_call=to_call_probe,
            limit=limit_probe,
        )
        encoder = self.encoder(FLAT, shape=shape)
        before = slots(self.observation(encoder, base))
        after = slots(self.observation(encoder, probe))
        self.assertEqual(
            len(after),
            self.width_of(encoder),
            "the hand-built readout encodes to one observation of the declared width "
            "(e2e-surface.md §2): %d slots against %d"
            % (len(after), self.width_of(encoder)),
        )
        magnitude = moved_slots(before, after)
        self.assertEqual(
            len(magnitude),
            seats + 4,
            "the readout differs in the five magnitude blocks of normalisation.md §2 and "
            "nothing else — `stacks` (%d slots on this shape), `pot` (1), `to_call` (1) and "
            "`limit` (2), so %d slots — and exactly those slots moved: %r"
            % (seats, seats + 4, magnitude),
        )
        street = str(S.readout_fact(probe, "street"))
        for index in magnitude:
            self.assertEqual(
                after[index],
                1.0,
                "a magnitude slot whose numerator exceeds its shape's denominator emits "
                "min(1, numerator / denominator) and saturates at exactly 1.0 — never a "
                "value above 1 (normalisation.md §4, D-61) — and shape %r encoding %r "
                "street %r slot %d reads %r for a numerator past its denominator"
                % (shape, FLAT, street, index, after[index]),
            )
        for index, value in enumerate(after):
            self.assertLessEqual(
                value,
                1.0,
                "nothing in an observation whose magnitudes exceed their denominators is "
                "above 1 (normalisation.md §4, §5): shape %r encoding %r street %r slot %d "
                "reads %r" % (shape, FLAT, street, index, value),
            )
            self.assertGreaterEqual(
                value,
                0.0,
                "and nothing in it is below 0 (normalisation.md §5): shape %r encoding %r "
                "street %r slot %d reads %r" % (shape, FLAT, street, index, value),
            )

        # The bound is a ceiling and not a clip below it: exactly at the normaliser, 1.0.
        for shape in self.shape_names():
            with self.subTest(shape=shape, at="normalisers"):
                normalisers = self.normalisers(shape)
                seats = self.seats_of(shape)
                encoder = self.encoder(FLAT, shape=shape)
                below = hand_built_readout(
                    stacks=(0,) * seats,
                    pot=0,
                    to_call=0,
                    limit=(0, 0),
                )
                exact = hand_built_readout(
                    stacks=(normalisers["stack"],) * seats,
                    pot=normalisers["pot"],
                    to_call=normalisers["to_call"],
                    limit=(normalisers["amount"], normalisers["count"]),
                )
                low = slots(self.observation(encoder, below))
                high = slots(self.observation(encoder, exact))
                at_ceiling = moved_slots(low, high)
                self.assertEqual(
                    len(at_ceiling),
                    seats + 4,
                    "a readout at the shape's own normalisers differs from one at zero in "
                    "the five magnitude blocks of normalisation.md §2 and nothing else: %r "
                    "on %r" % (at_ceiling, shape),
                )
                street = str(S.readout_fact(exact, "street"))
                for index in at_ceiling:
                    self.assertEqual(
                        high[index],
                        1.0,
                        "a magnitude slot exactly at its shape's declared normaliser reads "
                        "exactly 1.0 — the bound is a ceiling, not a clip below it "
                        "(normalisation.md §2, §4) — and shape %r encoding %r street %r "
                        "slot %d reads %r"
                        % (shape, FLAT, street, index, high[index]),
                    )

    # -- FAM-24.4 ----------------------------------------------------------
    def test_fam24_4_the_widths_and_the_shaped_parameter_count_are_unchanged(self):
        """FAM-24.4 each shape and encoding reports the width it had before the change, and a six-seat learner built from that shape's encoder reports a positive `param_count`.

        `normalisation.md` §1 declares that the layouts keep their widths, so every container
        still loads and every width, head and `param_count` stands (`shapes.md` §8, ASM-44):
        the change moves what a slot's **value** means and not the layout.  The case reads
        `features.observation_spec(encoder)["shape"]` for both encodings on all three declared
        shapes against the widths the catalogue declares — 203, 329 and 433 dense, 40, 82 and
        122 tokens — and then builds one learner of **each family** on each shape from that
        shape's own encoder (`agents.build_learner`), asserting each `agents.param_count` is a
        positive count measured here, that the three shapes give three different counts, and
        that every shape beside the default is larger than it — the width and the head both
        grow — so a build that was sized from the default shape's encoder would be caught.  No
        parameter total is written down as a number this battery has not measured (ASM-10).
        Each family's six-seat learner then decides one real decision through `agents.act`, so
        the observation the invariant bounds is one the learner's own entry point consumes
        (FAM-24's seam on the agents surface, `e2e-surface.md` §3.3).
        """
        for shape in self.shape_names():
            declared = S.SHAPE_LAYOUTS[shape]
            for encoding, key in ((FLAT, "dense"), (TOKENS, "tokens")):
                with self.subTest(shape=shape, encoding=encoding):
                    encoder = self.encoder(encoding, shape=shape)
                    self.assertEqual(
                        tuple(self.spec(encoder)["shape"]),
                        (declared[key],),
                        "D-61 moves what a value means and not the layout, so %r on %r keeps "
                        "the width it had before the change, %d (normalisation.md §1, "
                        "shapes.md §8, ASM-44): the spec record declares %r"
                        % (encoding, shape, declared[key],
                           self.spec(encoder)["shape"]),
                    )
                    self.assertIn(
                        shape,
                        WIDTHS,
                        "the case holds the widths of the three declared shapes %r — they "
                        "are the catalogue's, and its instances are the declaration itself "
                        "(shapes.md §2, seats.md §2, e2e-surface.md §5): the catalogue "
                        "declared %r" % (list(WIDTHS), self.shape_names()),
                    )
                    self.assertEqual(
                        self.width_of(encoder),
                        WIDTHS[shape][encoding],
                        "and that width is the design's own: %r on %r is %d slots — 203, 329 "
                        "and 433 for `flat-numeric` and 40, 82 and 122 for `card-tokens` over "
                        "the three rows — because the change moves what a value means and "
                        "not the layout (normalisation.md §1, §3, shapes.md §8, ASM-44, "
                        "D-61): the spec record declares %d"
                        % (encoding, shape, WIDTHS[shape][encoding],
                           self.width_of(encoder)),
                    )

        for encoding, preference in ((FLAT, "naive"), (TOKENS, "token")):
            kind = self.architecture_kind(preference)
            self.assertEqual(
                self.encoding_of(kind),
                encoding,
                "the case builds one architecture of each family, and each consumes the "
                "encoding whose width its input block is sized from (e2e-surface.md §3.3, "
                "shapes.md §8, ASM-44): %r consumes the %r family"
                % (kind, self.encoding_of(kind)),
            )
            counts = {}
            learners = {}
            for shape in self.shape_names():
                encoder = self.encoder(encoding, shape=shape)
                learner = self.learner(
                    width=S.PARAM_WIDTH,
                    depth=S.PARAM_DEPTH,
                    game=shape,
                    kind=kind,
                    encoder=encoder,
                )
                learners[shape] = learner
                count = self.ep("agents", "param_count")(learner)
                self.assertTrue(
                    S.is_count(count),
                    "agents.param_count reports a plain integer parameter count (sizing.md "
                    "§6, e2e-surface.md §3.3): %r for a %r learner built on %r"
                    % (count, encoding, shape),
                )
                self.assertGreater(
                    int(count),
                    0,
                    "a %r learner built on %r from that shape's own encoder is a real sized "
                    "model and reports a positive parameter count (normalisation.md §5: a "
                    "learner of each family built at its shape's own width): %r"
                    % (encoding, shape, count),
                )
                counts[shape] = int(count)
            default_shape = self.shape_names()[0]
            self.assertEqual(
                len(set(counts.values())),
                len(counts),
                "each declared shape's build is sized from that shape's own encoder, so the "
                "three counts are three numbers and not one repeated: %r — the widths are "
                "%r, and the change moves what a value means and not the layout "
                "(normalisation.md §1, shapes.md §8, ASM-44, D-61)"
                % (
                    counts,
                    {shape: WIDTHS[shape][encoding] for shape in self.shape_names()},
                ),
            )
            for shape in self.shape_names()[1:]:
                self.assertGreater(
                    counts[shape],
                    counts[default_shape],
                    "a %r learner on %r reports more parameters than the same build on %r, "
                    "because its input block is that shape's encoder's width — %d slots "
                    "against %d — and its head that shape's vocabulary (shapes.md §8, "
                    "ASM-44, sizing.md §6): %r against %r"
                    % (encoding, shape, default_shape, WIDTHS[shape][encoding],
                       WIDTHS[default_shape][encoding], counts[shape],
                       counts[default_shape]),
                )

            # The learner consumes the observation this family bounds, at that shape's width.
            shape = self.shape_names()[-1]
            seed, readout = sweep(self, shape)[0]
            observation = self.observation(self.encoder(encoding, shape=shape), readout)
            mask = list(self.ep("features", "legal_indices")(S.readout_fact(readout, "legal")))
            chosen = self.action_index(
                self.ep("agents", "act")(learners[shape], observation, mask)
            )
            self.assertIn(
                chosen,
                mask,
                "agents.act decides inside the legal mask on a %r observation of %r taken at "
                "seed %r, street %r — the observation the invariant bounds is the one the "
                "learner reads, at the width that shape's encoder declares "
                "(e2e-surface.md §2, §3.3, normalisation.md §5): it chose %r from %r"
                % (encoding, shape, seed, readout["street"], chosen, mask),
            )

    # -- FAM-24.5 ----------------------------------------------------------
    def test_fam24_5_both_encodings_carry_the_same_nine_fields_on_every_shape(self):
        """FAM-24.5 both encodings declare the same nine fields and each accepts a readout the engine produced on every declared shape.

        `e2e-surface.md` §2 makes `fields` identical for every encoding — the ladder never
        changes what the agent may know, only how it is represented (D-3) — so the nine facts
        of the readout both encodings carry are read off `features.observation_spec` for both
        encodings on all three declared shapes and held equal to the eleven `e2e-surface.md`
        §2 facts less the two no encoding carries: `legal`, which is the engine's order, and
        the derived `hand_class` (`folders.md` §3, ASM-30).  A smoke assertion follows: one
        readout the engine actually produced on each shape encodes through both encodings to
        an observation of the declared width, so D-61's normalisation refused nothing the
        engine can deal (`normalisation.md` §4: the refusal is for a fact that cannot be
        normalised, which no declared shape produces).
        """
        for shape in self.shape_names():
            with self.subTest(shape=shape):
                declared_fields = {}
                for encoding in (FLAT, TOKENS):
                    encoder = self.encoder(encoding, shape=shape)
                    fields = tuple(self.spec(encoder)["fields"])
                    declared_fields[encoding] = fields
                    self.assertEqual(
                        len(fields),
                        9,
                        "both encodings carry the nine facts of the readout — e2e-surface.md "
                        "§2's eleven less `legal` and `hand_class` — and %r on %r declares %r"
                        % (encoding, shape, fields),
                    )
                    self.assertEqual(
                        fields,
                        CARRIED_FIELDS,
                        "the facts both encodings carry are the readout's nine, in the "
                        "readout's own order (e2e-surface.md §2, D-3): %r on %r declares %r "
                        "against %r"
                        % (encoding, shape, fields, CARRIED_FIELDS),
                    )
                    seed, readout = sweep(self, shape)[0]
                    missing = [fact for fact in fields if fact not in readout]
                    self.assertEqual(
                        missing,
                        [],
                        "the readout the smoke encodes carries every field both encodings "
                        "declare (e2e-surface.md §2): %r carries %r"
                        % (sorted(str(key) for key in readout), missing),
                    )
                    values = slots(self.observation(encoder, readout))
                    self.assertEqual(
                        len(values),
                        self.width_of(encoder),
                        "%r accepts a readout the engine produced on %r at seed %r and "
                        "encodes it to an observation of its declared width (normalisation.md "
                        "§4, §5): %d slots against %d"
                        % (encoding, shape, seed, len(values), self.width_of(encoder)),
                    )
                self.assertEqual(
                    declared_fields[FLAT],
                    declared_fields[TOKENS],
                    "the two encodings carry the same fields on every declared shape — the "
                    "ladder never changes what the agent may know (e2e-surface.md §2, D-3): "
                    "%r against %r on %r"
                    % (declared_fields[FLAT], declared_fields[TOKENS], shape),
                )


if __name__ == "__main__":
    unittest.main()
