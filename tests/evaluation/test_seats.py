"""EVL-15 — the seat count at this edge: D-33's third shape, the counted draw and four refusals.

Drives `docs/L3/evaluation/seats.md` §1-§5 (the L3 file D-33 is written against: §1
the restated catalogue and the instrument's arity, §2 the counted draw's derivation, §3
the four refusals, §4 the pool's baselines on the pool's own shape), `docs/L2/evaluation/
seats.md` §1-§4 (the same contract at the surface: the one name a shape adds, the one
optional argument whose absence is today's call, the four `SeatCountExceeded` rows and
the pool's shape reaching the baselines it pins) and the L1 pages it is written from --
`docs/L1/seats.md` §4-§5 (five opponents drawn without replacement and the pairwise
instrument's refusal), `docs/L1/league.md` §2, §4 (a draw is without replacement; a cell
is one pair), `docs/L1/records.md` §8 (a pool's membership) with ASM-43 and D-33.

The instrument is the pairwise one, and the battery says so in the same words the module
does: `PAIRWISE_SEATS` is **the instrument's arity and never a game's**, the seat count is
read off `engine.game_config` and never written down here, and the two-seat shapes are
untouched, so every cell, matrix, rating and report they produce is what it was before the
third row existed (`seats.md` §1, §3, §5, D-13, D-22, D-33).  Where the design leaves a
shape free -- the container of a draw's result, the reader of a member's id -- a case here
reads it tolerantly, and where it pins a number -- five distinct members of a seven-member
pool, the boundary `2 x to_call > starting_stack` on each shape's own declared stack, the
two-seat shapes' unchanged pool id -- it asserts it exactly.

**Why the seven-member draw is played on the two-seat no-limit shape.**  `EVL-15.3` and
`EVL-15.4` need a batch of real readouts on which the membership is *separable*, so a
repeated seat cannot hide behind two members that answered alike.  On the default
fixed-limit shape the declared vocabulary is the three descriptors `fold`, `check-call`,
`raise` and the 20-chip stack never makes a call exceed half of it, so `fold-large-bet`
never folds there and answers exactly as `always-call` does on every readout; on
`no-limit-100`, whose six-descriptor vocabulary and 100-chip stack reach a call above 50,
the seven members of `EVL-15.3`'s pool do separate.  That is a fact about the two shapes'
declared rows (`docs/L1/seats.md` §2, §3, `shapes.md` §2) and not a licence to test the
draw on a second instrument, so the cases assert the *seat count* is the engine's and the
*draw* is the same rule on either shape (`seats.md` §2, §4, ASM-43, D-33).

Cost discipline is the battery's (`_evaluation_support.py`): no real `live` matrix is
built here.  The four successes of `EVL-15.6` reuse the shared `k4` table (`shared_matrix`
and `shared_rating`), whose two-seat cells other files of this battery build once for the
whole process, and every other record is either a hand-built `records.md` §10 table or a
real hand read off `engine.new_hand`.  The one new checkpoint is the no-limit member the
seven-member pool declares, written once and cached beside the battery's other
checkpoints (`scheduler.md` §5.1, `guardrails.md` G13).
"""

import itertools
import unittest

from _evaluation_support import (
    BASELINES,
    MATCH_SEED,
    OTHER_LEARNER_SEED,
    OTHER_MATCH_SEED,
    POOL_M,
    RUNG_NAME,
    START_LABEL,
    VERSION_IDS,
    EvaluationCase,
    balanced,
    declaration,
    declared_internal,
    default_shape,
    draw_order,
    first_legal,
    hand_matrix,
    member_id,
    other_shape,
    pairwise_seats,
    pool_digest,
    pool_member_ids,
    probe_readouts,
    rating_record,
    refusal_class,
    report_inputs,
    run_record,
    seats_of,
    shape_names,
    six_seat_shape,
    version_record,
)

#: The invented seed a real six-seat hand of this file's cases is dealt at: a decision's
#: readout, its legal actions and its `to_call` are that hand's (`docs/L1/battery.md` §4,
#: D-15, `engine/surface.md` §4-§6).
SIX_SEAT_HAND_SEED = 550801

#: The invented seeds the seven-member draw's candidate decisions are dealt from, and how
#: many of them the resolution batch may look at (`docs/L1/battery.md` §4, D-15).
CANDIDATE_HAND_SEEDS = tuple(range(550802, 550827))
CANDIDATE_LIMIT = 60

#: The widest batch the case will search for: one row per member it has to tell apart is
#: all a resolving batch needs, and every row is answered by every drawn seat at every
#: seed, so the search prefers the narrowest (`seats.md` §2, G13).
RESOLUTION_ROWS_MAX = 3

#: The seed the seven-member pool's separability is proved at -- the first seed of the
#: draw's own loop, so the batch is proved on a seed the loop then uses (`seats.md` §2).
RESOLUTION_SEED = 0

#: The seeds a counted draw of one is compared with the uncounted draw at (`seats.md` §2,
#: `docs/L1/seats.md` §4, ASM-43).
ONE_DRAW_SEEDS = (0, 7, 12345)

#: The invented seed and start label of the second family the permuted pools declare
#: (`families.md` §1-§2, `docs/L1/evaluation` `pool.md` §3).
SECOND_START_LABEL = "own-start-seats-5601"

#: The `to_call` values the two shapes' declared stacks are read at: 10 and 50 inside both
#: stacks' halves, 11 and 51 one chip past each (`folders.md` §2, ASM-31, `seats.md` §4).
STACK_BOUNDARIES = (10, 11, 50, 51)


def call_when_possible(readout, legal_actions):
    """A caller-side policy that never folds while calling is legal (a real hand's driver)."""
    return "check-call" if "check-call" in legal_actions else legal_actions[0]


def jam(readout, legal_actions):
    """A caller-side policy that bets the largest legal amount, to expose a large `to_call`."""
    for wanted in ("raise-all-in", "raise-half", "raise-quarter", "raise-minimum", "raise"):
        if wanted in legal_actions:
            return wanted
    return legal_actions[0]


def half_pot(readout, legal_actions):
    """A caller-side policy that bets about half the pot, one band below the jam."""
    for wanted in ("raise-half", "raise-quarter", "raise-minimum", "check-call"):
        if wanted in legal_actions:
            return wanted
    return legal_actions[0]


def postflop_raise(readout, legal_actions):
    """Calls before the flop and bets from it, so a folder's post-flop row is reached."""
    if readout["street"] == "preflop":
        return "check-call" if "check-call" in legal_actions else legal_actions[0]
    for wanted in ("raise-quarter", "raise-half", "raise-minimum", "check-call"):
        if wanted in legal_actions:
            return wanted
    return legal_actions[0]


def probe_batch(count=4):
    """The battery's cached probe decisions as ``(readout, legal actions)`` pairs.

    `probe_readouts` is the battery's one cache of real readouts -- one decision each, the
    hands dealt once per process (`engine/surface.md` §4, ASM-2) -- and a case reads the two
    facts it needs of each here, so every batch of this file is the same batch.
    """
    return tuple((row["readout"], row["legal"]) for row in probe_readouts(count))


def answers_of(policy, batch):
    """One policy's answers to a fixed batch of ``(readout, legal actions)`` decisions."""
    return tuple(policy(readout, legal) for readout, legal in batch)


class SeatsCase(EvaluationCase):
    """D-33's seat count, driven through the module's restatement and the engine's own rows."""

    def refused(self, call, entry, groups=(), label="", kind=None):
        """Run `call` and require this module's own refusal naming `entry` and `groups`.

        `errors.md` §1-§2: a refusal must be catchable as `EvaluationError`, so a `TypeError`
        from a mistyped argument is an internal decision leaking as a crash and is red here.
        `kind`, when a case gives one, is the class `errors.md` §2 declares for the contract
        -- D-33's three are `InvalidDrawCount`, `DrawExceedsMembership` and
        `SeatCountExceeded` (`seats.md` §2-§3, §5) -- and the message grammar is §3's.
        """
        where = label or entry
        root = refusal_class()
        try:
            value = call()
        except Exception as exc:  # noqa: BLE001 - the class is asserted by `kind`
            self.assertIsInstance(
                exc,
                root,
                "%s was refused with %s, which is not this module's own refusal (%s), so a "
                "caller catching EvaluationError would miss it: %r (errors.md §1-§2, "
                "seats.md §2-§3)" % (where, type(exc).__name__, root.__name__, exc),
            )
            self.assert_refused_like(exc, entry, groups, where)
            if kind is not None:
                self.assertEqual(
                    type(exc).__name__,
                    kind,
                    "%s is the refusal errors.md §2 declares for this contract, and the "
                    "refusal arrived as %s instead: %r (errors.md §2, seats.md §3, §5, "
                    "D-33)" % (where, type(exc).__name__, exc),
                )
            return exc
        self.fail("%s accepted %r, which the contract refuses" % (where, value))

    def folders(self):
        """The catalogue's three folders, in `agents.baselines()`'s order (`D-21`).

        The names beyond the pinned anchors: with them a pool holds the three anchors and
        the three folders, the six-member composition `docs/L1/seats.md` §2, §4 declares for
        a six-seat hand (`records.md` §8, `agents/surface.md` §11, ASM-32, D-21).
        """
        return tuple(
            name for name in self.agents().baselines() if name not in BASELINES
        )

    def four_member_pool(self):
        """A frozen default-shape pool of the three anchors and `fold-large-bet` (`seats.md` §2).

        Four members is one fewer than the five a six-seat hand seats, which is what a draw
        above the membership is provoked against (`docs/L1/seats.md` §4, `records.md` §8).
        """
        if "pool4" not in self._fixtures:
            self._fixtures["pool4"] = self.evaluation().build_pool(
                declaration(
                    members=(),
                    m=POOL_M,
                    frozen=True,
                    baselines=[self.folders()[-1]],
                )
            )
        return self._fixtures["pool4"]

    def six_seat_pool(self, members=()):
        """A frozen pool on the one shape above the instrument's arity (`seats.md` §1, §3, §4).

        Its membership is the three anchors and the three folders unless a case hands
        versions in, and every baseline it pins is built **for that shape**, so its
        `fold-large-bet` reads 100 and its `oracle` asks the six-way question
        (`docs/L1/seats.md` §2, §4, ASM-31, D-33).
        """
        return self.evaluation().build_pool(
            declaration(
                members=members,
                m=POOL_M,
                frozen=True,
                game=six_seat_shape(),
                baselines=self.folders(),
            )
        )

    def seven_member_pool(self):
        """``(pool, record)``: the six pinned baselines and one real version member.

        The pool is on the two-seat no-limit shape, whose six-descriptor vocabulary and
        100-chip stack separate all seven members on a batch of real readouts -- on the
        default shape `fold-large-bet` never folds and answers exactly as `always-call`
        does, so no batch there could show that five drawn seats are five members
        (`seats.md` §2, §4, `docs/L1/seats.md` §2, §4, ASM-43).  The version member's
        checkpoint is the battery's `checkpoint(name="member")` written **for that shape**,
        so its container records the shape its record declares (`scheduler.md` §5.1,
        `records.md` §7, `shape.md` §4, D-29).
        """
        if "pool7" not in self._fixtures:
            shape = other_shape()
            info = self.checkpoint(name="member", game=shape)
            member = version_record(
                VERSION_IDS[0], START_LABEL, path=info["path"], game=shape
            )
            pool = self.evaluation().build_pool(
                declaration(
                    members=[member],
                    m=POOL_M,
                    frozen=True,
                    game=shape,
                    baselines=self.folders(),
                )
            )
            self._fixtures["pool7"] = (pool, self.pool_members(pool))
        return self._fixtures["pool7"]

    def references(self, pool, seed, positions=None):
        """The pool's members as reference policies at one seed, keyed by membership position.

        A baseline is `agents.build_baseline(name, seed, pool.game)` -- the module's own
        construction, on the pool's shape (`seats.md` §4, ASM-31) -- and a version member is
        `policy_from(path)`, which reads the seed its container records (`pool.md` §7,
        `scheduler.md` §5.1).  `positions` narrows the build to the seats a case compares.
        """
        record = self.pool_members(pool)
        shape = record["game"]
        wanted = range(len(record["members"])) if positions is None else positions
        out = {}
        for position in wanted:
            member = record["members"][position]
            if member.get("baseline"):
                out[position] = self.agents().build_baseline(
                    member["id"], seed, shape
                )
            else:
                out[position] = self.evaluation().policy_from(member["path"])
        return out

    def candidates(self):
        """Real decisions of the no-limit shape where folding is legal, deduplicated once.

        The seven members of `EVL-15.3`'s pool differ only where a decision offers `fold`
        and the price of the call is large, so the batch a draw is identified on is taken
        from decisions a bet reached -- four caller-side drivers over the battery's own
        invented hand seeds, no matrix, no checkpoint touched (`engine/surface.md` §4-§6,
        `docs/L1/battery.md` §4, D-2).
        """
        if "candidates" not in self._fixtures:
            engine = self.engine()
            shape = other_shape()
            rows = []
            seen = set()
            for seed in CANDIDATE_HAND_SEEDS:
                for driver in (call_when_possible, jam, half_pot, postflop_raise):
                    hand = engine.new_hand(seed, shape)
                    step = 0
                    while not engine.is_terminal(hand) and step < 40:
                        readout = engine.readout(hand)
                        legal = tuple(engine.legal_actions(hand))
                        if "fold" in legal:
                            key = (
                                readout["street"],
                                int(readout["to_call"]),
                                readout["hand_class"],
                                tuple(readout["hole"]),
                                tuple(readout["seat"]) if isinstance(
                                    readout["seat"], (tuple, list)
                                ) else readout["seat"],
                                tuple(readout["board"]),
                            )
                            if key not in seen:
                                seen.add(key)
                                rows.append((readout, legal))
                                if len(rows) >= CANDIDATE_LIMIT:
                                    break
                        hand = engine.apply_action(
                            hand, driver(readout, legal)
                        )
                        step += 1
                    if len(rows) >= CANDIDATE_LIMIT:
                        break
                if len(rows) >= CANDIDATE_LIMIT:
                    break
            self._fixtures["candidates"] = tuple(rows)
        return self._fixtures["candidates"]

    def resolution_batch(self, pool):
        """The real readouts on which the pool's several members are told apart.

        `seats.md` §2's draw is asserted by naming the member each seat is, so the batch has
        to resolve the membership: the case reads its own real decisions and keeps the
        fewest of them on which the pool's members return pairwise distinct answers --
        one row if one suffices, then two, then three, and otherwise every row that adds a
        distinction.  The cases then assert that all of them are distinct, so a repeated
        seat is visible as an answer that is not the member's the draw named.  Proved once, at
        `RESOLUTION_SEED`, and the batch is kept small because every row of it is answered
        by every drawn seat at every one of the draw's seeds (`seats.md` §2, §4,
        `docs/L1/seats.md` §4, ASM-43, G13).
        """
        if "batch7" not in self._fixtures:
            rows = self.candidates()
            references = self.references(pool, RESOLUTION_SEED)
            table = {
                position: [policy(readout, legal) for readout, legal in rows]
                for position, policy in references.items()
            }
            size = len(references)
            chosen = None
            values = None
            for width in range(1, RESOLUTION_ROWS_MAX + 1):
                for trial in itertools.combinations(range(len(rows)), width):
                    trial_values = [
                        tuple(table[position][index] for index in trial)
                        for position in range(size)
                    ]
                    if len(set(trial_values)) == size:
                        chosen = list(trial)
                        values = trial_values
                        break
                if chosen is not None:
                    break
            if chosen is None:
                # No batch of at most `RESOLUTION_ROWS_MAX` rows resolves the membership:
                # fall back to the greediest one found row by row, and let the cases'
                # distinctness assertion report what it reached (`seats.md` §2, ASM-43).
                chosen = []
                values = [() for _ in range(size)]
                for row in range(len(rows)):
                    trial = chosen + [row]
                    trial_values = [
                        tuple(table[position][index] for index in trial)
                        for position in range(size)
                    ]
                    if len(set(trial_values)) > len(set(values)):
                        chosen = trial
                        values = trial_values
                    if len(set(values)) == size:
                        break
            self._fixtures["batch7"] = tuple(rows[row] for row in chosen)
            self._fixtures["batch7_values"] = tuple(values)
        return self._fixtures["batch7"]

    def six_seat_table(self):
        """``(matrix, rating, record, rung)``: a complete six-seat table and its report inputs.

        The matrix is built in `records.md` §10's shape -- every cell carrying both
        directions' `wins`, `ties`, `losses`, `mean_chip_delta` and `seat_split`, and the
        shape named on the record **and** on every cell -- and the run record carries the
        seven families `records.md` §12-§13 requires, so `rating` and `report` reach the
        seat check with nothing else to refuse first (`rating.md` §1, §6, `report.md` §2,
        `seats.md` §3, §5).
        """
        if "table6" not in self._fixtures:
            shape = six_seat_shape()
            matrix = hand_matrix(balanced, game=shape, cell_game=shape)
            rating = rating_record(matrix)
            rung, record, matrix, rating = report_inputs(
                matrix=matrix, rating=rating, game=shape
            )
            self._fixtures["table6"] = (matrix, rating, record, rung)
        return self._fixtures["table6"]

    def six_seat_readout(self):
        """A real six-seat decision: its readout and its legal descriptors."""
        engine = self.engine()
        hand = engine.new_hand(SIX_SEAT_HAND_SEED, six_seat_shape())
        return engine.readout(hand), tuple(engine.legal_actions(hand))

    def six_seat_decisions(self, limit=8):
        """``limit`` real decisions a real six-seat hand reaches (`engine/surface.md` §4-§6)."""
        engine = self.engine()
        hand = engine.new_hand(SIX_SEAT_HAND_SEED, six_seat_shape())
        rows = []
        step = 0
        while not engine.is_terminal(hand) and step < 40 and len(rows) < limit:
            readout = engine.readout(hand)
            legal = tuple(engine.legal_actions(hand))
            rows.append((readout, legal))
            hand = engine.apply_action(hand, call_when_possible(readout, legal))
            step += 1
        return rows

    # -- the catalogue and the instrument's arity (seats.md §1, §3) -------------
    def test_evl_15_1_the_three_shapes_and_their_seat_counts(self):
        """EVL-15.1 the restated catalogue's third name is the one shape above the instrument's arity and is published after the two two-seat ones; each name's `seats_of` is `engine.game_config(name)["seats"]`, the two-seat ones are `PAIRWISE_SEATS`, and `PAIRWISE_SEATS` is the default shape's own seat count (`seats.md` §1, §3, `docs/L1/seats.md` §2, §5, `league.md` §4, D-13, D-33)."""
        names = shape_names()
        self.assertEqual(
            len(names),
            3,
            "the catalogue publishes three rows, default first, and this edge restates "
            "their names (seats.md §1, docs/L1/seats.md §2, D-33): %r" % (names,),
        )
        self.assertEqual(
            names[0],
            default_shape(),
            "the first name is the declared default, which is what an absent `game` reads "
            "as (shape.md §2, seats.md §1, D-29): %r" % (names[0],),
        )
        self.assertEqual(
            names[1],
            other_shape(),
            "the second name is the off-default shape whose seat count is the instrument's, "
            "the one a two-seat record declares to be off-default (seats.md §1, §3, "
            "docs/L1/seats.md §5, D-29): %r" % (names[1],),
        )
        self.assertEqual(
            names[2],
            six_seat_shape(),
            "the third name is the shape whose seat count is above the instrument's arity, "
            "published after the two-seat rows (seats.md §1, §3, docs/L1/seats.md §2, "
            "D-33): %r" % (names[2],),
        )
        pairwise = pairwise_seats()
        self.assertEqual(
            pairwise,
            int(self.engine().game_config(default_shape())["seats"]),
            "PAIRWISE_SEATS is the instrument's arity and the default shape's own seat "
            "count, read off the engine and never written down here (seats.md §1, §3, "
            "docs/L1/seats.md §2-§3, D-13, D-33): %r vs %r"
            % (pairwise, int(self.engine().game_config(default_shape())["seats"])),
        )
        counts = []
        for name in names:
            with self.subTest(shape=name):
                seats = seats_of(name)
                counts.append(seats)
                self.assertEqual(
                    seats,
                    int(self.engine().game_config(name)["seats"]),
                    "a shape's seat count is engine.game_config(%r)['seats'] and no other "
                    "number (seats.md §1-§3, module-map.md §2, D-13): %r vs %r"
                    % (name, seats, int(self.engine().game_config(name)["seats"])),
                )
                self.assertEqual(
                    int(declared_internal("declarations", "seat_count")(name)),
                    seats,
                    "the edge's own reader and this battery's agree on %r, so a case that "
                    "compares a seat count with the instrument's compares the engine's "
                    "numbers twice (seats.md §3, D-13, D-33)" % (name,),
                )
        self.assertEqual(
            counts[:2],
            [pairwise, pairwise],
            "the two two-seat shapes have the instrument's own arity, which is what keeps "
            "every cell, matrix, rating and report they produce today untouched "
            "(seats.md §5, docs/L1/seats.md §5, D-33): %r against %r"
            % (counts, pairwise),
        )
        self.assertGreater(
            counts[2],
            pairwise,
            "the third shape's seat count is above the instrument's, so a cell is no longer "
            "the whole of a hand's seating (seats.md §1, §3, docs/L1/seats.md §5, D-33): "
            "%r against %r" % (counts[2], pairwise),
        )

    # -- the uncounted draw is today's draw (seats.md §2, §4) -------------------
    def test_evl_15_2_the_draw_without_a_count_is_today_s_draw(self):
        """EVL-15.2 `opponent(pool, seed)` is one policy -- the pool member at `seed % n` -- built exactly as `agents.build_baseline(member, seed)` and as `agents.build_baseline(member, seed, default_shape)`, equal on two calls at one seed, and it moves no stream (`seats.md` §2, §4, `docs/L1/seats.md` §4, `pool.md` §7, ASM-2, ASM-43)."""
        package = self.evaluation()
        pool = self.four_member_pool()
        record = self.pool_members(pool)
        ids = pool_member_ids(record)
        self.assertEqual(
            len(ids),
            4,
            "the case's pool is the three anchors and one folder, four members "
            "(records.md §8, docs/L1/seats.md §4, ASM-32, D-21): %r" % (ids,),
        )
        self.assertEqual(
            record["game"],
            default_shape(),
            "an absent `game` in the declaration is the default shape, and the pool reads "
            "back with it (shape.md §2, pool.md §5, seats.md §4): %r" % (record["game"],),
        )
        batch = probe_batch(4)
        before = self.stream_state()
        for seed in range(12):
            with self.subTest(seed=seed):
                drawn = package.opponent(pool, seed)
                self.assertTrue(
                    callable(drawn),
                    "a draw without a count returns one policy and not a tuple, which is "
                    "today's call (seats.md §2, docs/L1/seats.md §4, ASM-43): %r"
                    % (drawn,),
                )
                name = ids[seed % len(ids)]
                answers = answers_of(drawn, batch)
                self.assertEqual(
                    answers,
                    answers_of(self.agents().build_baseline(name, seed), batch),
                    "the member the seed names is _draw_index(seed, n) = seed %% n, and the "
                    "policy it draws is agents.build_baseline(member, seed) answer for "
                    "answer (seats.md §2, pool.md §7, ASM-43): seed %r names %r"
                    % (seed, name),
                )
                self.assertEqual(
                    answers,
                    answers_of(
                        self.agents().build_baseline(name, seed, default_shape()), batch
                    ),
                    "the shape argument moves nothing on the default shape, so the drawn "
                    "policy is the two-argument build and the three-argument default one at "
                    "once (seats.md §4, shape.md §2, ASM-31, D-33): %r" % (name,),
                )
                self.assertEqual(
                    answers_of(package.opponent(pool, seed), batch),
                    answers,
                    "two calls at one seed give one opponent, answer for answer, because "
                    "the draw is a function of the seed and the membership alone "
                    "(seats.md §2, pool.md §4, ASM-2, ASM-43): seed %r" % (seed,),
                )
        self.assert_stream_unchanged(before, "a draw without a count")

    # -- five distinct members of seven (seats.md §2, docs/L1/seats.md §4) ------
    def test_evl_15_3_the_counted_draw_is_five_distinct_members_of_seven(self):
        """EVL-15.3 `opponent(pool, seed, 5)` is five policies in the draw's order, drawn without replacement from a seven-member pool: two calls at one seed agree, the k-th policy is the member at `_draw_order(seed, 7)[k]`, the seven members' references are seven pairwise distinct answers on the batch, and a draw of one is the uncounted draw -- at every seed of `range(200)` (`seats.md` §2, `docs/L1/seats.md` §4, `league.md` §2, ASM-43)."""
        package = self.evaluation()
        pool, record = self.seven_member_pool()
        ids = pool_member_ids(record)
        self.assertEqual(
            len(ids),
            7,
            "the pool is the six pinned baselines and one real version member, so a draw of "
            "five is a strict subset (records.md §8, docs/L1/seats.md §4, ASM-32, D-21): %r"
            % (ids,),
        )
        batch = self.resolution_batch(pool)
        self.assertGreaterEqual(
            len(batch),
            1,
            "the case's own real decisions include rows a folder's and an anchor's answers "
            "differ on, so the membership is separable at all (seats.md §2, "
            "engine/surface.md §4-§6): %r" % (len(batch),),
        )
        self.assertEqual(
            len(self._fixtures["batch7_values"]),
            7,
            "the batch resolves the whole membership: every one of the seven members "
            "answers differently from every other on it, so a repeated seat cannot hide "
            "behind two members that answered alike (seats.md §2, docs/L1/seats.md §4, "
            "ASM-43): %r" % (self._fixtures["batch7_values"],),
        )
        self.assertEqual(
            len(set(self._fixtures["batch7_values"])),
            len(self._fixtures["batch7_values"]),
            "the seven references are seven **distinct** answer-tuples on the batch "
            "(seats.md §2, §4, ASM-43): %r" % (self._fixtures["batch7_values"],),
        )
        before = self.stream_state()
        for seed in range(200):
            with self.subTest(seed=seed):
                order = draw_order(seed, len(ids))
                self.assertEqual(
                    sorted(order),
                    list(range(len(ids))),
                    "the draw's order is a permutation of the membership's seven "
                    "positions, so the draw is without replacement (seats.md §2, "
                    "league.md §2, ASM-43): %r" % (order,),
                )
                first = package.opponent(pool, seed, 5)
                second = package.opponent(pool, seed, 5)
                self.assertEqual(
                    len(first),
                    5,
                    "a draw of five returns five policies, in the draw's order "
                    "(seats.md §2, docs/L1/seats.md §4, ASM-43): %r" % (first,),
                )
                self.assertEqual(
                    tuple(answers_of(policy, batch) for policy in second),
                    tuple(answers_of(policy, batch) for policy in first),
                    "two calls at one seed draw one tuple, answer for answer, because the "
                    "draw is a function of the seed and the ordered membership "
                    "(seats.md §2, pool.md §4, ASM-2, ASM-43): seed %r" % (seed,),
                )
                references = self.references(pool, seed, positions=order[:5])
                for seat, position in enumerate(order[:5]):
                    self.assertEqual(
                        answers_of(first[seat], batch),
                        answers_of(references[position], batch),
                        "seat %d of the draw is the member at position %d of the "
                        "membership, built exactly as the uncounted draw builds it -- a "
                        "baseline at the seed on the pool's shape, a version at its "
                        "container's (seats.md §2, §4, pool.md §4, ASM-31, ASM-43): "
                        "%r against %r" % (seat, position, ids[position], ids),
                    )
        self.assert_stream_unchanged(before, "the counted draws")
        for seed in ONE_DRAW_SEEDS:
            with self.subTest(seed=seed, draw=1):
                one = package.opponent(pool, seed)
                counted = package.opponent(pool, seed, 1)
                self.assertEqual(
                    len(counted),
                    1,
                    "a draw of one is still a tuple of one, because a count was named "
                    "(seats.md §2, ASM-43): %r" % (counted,),
                )
                self.assertEqual(
                    answers_of(counted[0], batch),
                    answers_of(one, batch),
                    "the first position of a counted draw is seed %% n, the very member the "
                    "uncounted draw names, so a draw of one is today's opponent "
                    "(seats.md §2, scheduler.md §3, docs/L1/seats.md §4, ASM-43): seed %r"
                    % (seed,),
                )

    # -- the draw is a function of the seed and the ordered membership ---------
    def test_evl_15_4_the_draw_is_a_function_of_the_seed_and_the_ordered_membership(self):
        """EVL-15.4 two pools of one five-member membership -- the same two version records declared in the other order, so the window, and therefore the membership, is permuted -- draw at the same positions in the membership, so the drawn members differ exactly where the membership does, and one pool twice draws once (`seats.md` §2, `families.md` §1-§2, `pool.md` §3, `docs/L1/league.md` §2, ASM-2, ASM-43)."""
        package = self.evaluation()
        first_checkpoint = self.checkpoint(name="member")
        # Two **different** containers: one learner seed each, so the two versions are two
        # members and not one member declared twice.  The second is the battery's own
        # second-seed checkpoint, so this case writes no file of its own
        # (`scheduler.md` §5.1, `records.md` §7, G13).
        second_checkpoint = self.checkpoint(name="other", seed=OTHER_LEARNER_SEED)
        first = version_record(
            VERSION_IDS[1], START_LABEL, path=first_checkpoint["path"]
        )
        second = version_record(
            VERSION_IDS[2], SECOND_START_LABEL, path=second_checkpoint["path"]
        )
        pool_a = self.evaluation().build_pool(
            declaration(members=[first, second], m=POOL_M, frozen=True)
        )
        pool_b = self.evaluation().build_pool(
            declaration(members=[second, first], m=POOL_M, frozen=True)
        )
        ids_a = pool_member_ids(self.pool_members(pool_a))
        ids_b = pool_member_ids(self.pool_members(pool_b))
        self.assertEqual(
            sorted(ids_a),
            sorted(ids_b),
            "the two pools declare one membership: two versions with two different lineage "
            "starts, so each opens a family of its own and the families' order is the "
            "declaration's (families.md §1-§2, pool.md §3, records.md §8): %r vs %r"
            % (ids_a, ids_b),
        )
        self.assertEqual(
            ids_a[:3],
            ids_b[:3],
            "the pinned anchors come first in the catalogue's order whatever the "
            "declaration says, so only the window is permuted (pool.md §2, ASM-32, D-21): "
            "%r vs %r" % (ids_a, ids_b),
        )
        self.assertEqual(
            ids_a[3:],
            tuple(reversed(ids_b[3:])),
            "the two version records are declared in the other order and each is its own "
            "family, so the window -- and therefore the membership's tail -- is the "
            "permutation of the two (families.md §1-§2, records.md §8, ASM-26): %r vs %r"
            % (ids_a[3:], ids_b[3:]),
        )
        seed = OTHER_MATCH_SEED
        order = draw_order(seed, len(ids_a))
        self.assertEqual(
            sorted(order),
            list(range(len(ids_a))),
            "the draw's order is a permutation of the five positions (seats.md §2, "
            "league.md §2, ASM-43): %r" % (order,),
        )
        batch = probe_batch(4)
        draw_a = package.opponent(pool_a, seed, len(ids_a))
        draw_b = package.opponent(pool_b, seed, len(ids_b))
        references_a = self.references(pool_a, seed)
        references_b = self.references(pool_b, seed)
        for seat, position in enumerate(order):
            with self.subTest(seat=seat):
                self.assertEqual(
                    answers_of(draw_a[seat], batch),
                    answers_of(references_a[position], batch),
                    "in the first pool seat %d draws the member at membership position %d, "
                    "so the draw is read off that pool's own order (seats.md §2, pool.md "
                    "§4, ASM-43): %r" % (seat, position, ids_a[position]),
                )
                self.assertEqual(
                    answers_of(draw_b[seat], batch),
                    answers_of(references_b[position], batch),
                    "in the second pool seat %d draws the member at the same membership "
                    "position %d, because the draw is a function of the seed and of the "
                    "membership's size and order (seats.md §2, docs/L1/league.md §2, "
                    "ASM-43): %r" % (seat, position, ids_b[position]),
                )
        permuted = [seat for seat, position in enumerate(order) if position >= 3]
        self.assertEqual(
            len(permuted),
            2,
            "both window positions fall inside a draw of five, so the permutation is "
            "observable in the draw (seats.md §2, ASM-43): %r" % (order,),
        )
        for seat in permuted:
            with self.subTest(seat=seat, permuted=True):
                self.assertNotEqual(
                    answers_of(draw_a[seat], batch),
                    answers_of(draw_b[seat], batch),
                    "at a permuted position the two pools draw **different** members, so "
                    "the drawn seats differ where the membership does and a draw of the "
                    "positions alone would be red here (seats.md §2, pool.md §3, "
                    "ASM-43): %r against %r"
                    % (ids_a[order[seat]], ids_b[order[seat]]),
                )
        again = package.opponent(pool_a, seed, len(ids_a))
        self.assertEqual(
            tuple(answers_of(policy, batch) for policy in again),
            tuple(answers_of(policy, batch) for policy in draw_a),
            "one pool twice gives one draw, answer for answer (seats.md §2, pool.md §4, "
            "ASM-2, ASM-43)",
        )

    # -- a draw above the membership is refused naming both counts -------------
    def test_evl_15_5_a_draw_larger_than_the_membership_is_refused_naming_both_counts(self):
        """EVL-15.5 `opponent(pool, seed, 5)` on a four-member pool is `DrawExceedsMembership` naming both counts, `count=4` is accepted and returns the four members in the draw's order, a count that is not a positive integer is `InvalidDrawCount`, and no hand is played by any of them (`seats.md` §2, §3, `docs/L1/seats.md` §4, `records.md` §8, ASM-2, ASM-43)."""
        package = self.evaluation()
        pool = self.four_member_pool()
        ids = pool_member_ids(self.pool_members(pool))
        self.assertEqual(
            len(ids),
            4,
            "the pool a draw of five exceeds holds four members (records.md §8, "
            "docs/L1/seats.md §4): %r" % (ids,),
        )
        seed = MATCH_SEED
        before = self.stream_state()
        error = self.refused(
            lambda: package.opponent(pool, seed, 5),
            "opponent",
            groups=(("count",), (str(len(ids)),)),
            label="opponent(pool, seed, 5) on a four-member pool",
            kind="DrawExceedsMembership",
        )
        message = str(error)
        for count in ("5", str(len(ids))):
            with self.subTest(count=count):
                self.assertIn(
                    count,
                    message,
                    "the refusal names **both** counts -- what the draw asked for and what "
                    "the membership holds -- because a substitute seat would be an "
                    "opponent the membership does not carry (seats.md §2, §3, "
                    "docs/L1/seats.md §4, records.md §8, ASM-43): %r" % (message,),
                )
        for label, count in (
            ("zero", 0),
            ("negative", -1),
            ("a half", 1.5),
            ("a flag", True),
        ):
            with self.subTest(case=label):
                self.refused(
                    lambda count=count: package.opponent(pool, seed, count),
                    "opponent",
                    groups=(("count",), (str(count),)),
                    label="opponent(pool, seed, %r)" % (count,),
                    kind="InvalidDrawCount",
                )
        self.assert_stream_unchanged(before, "a refused draw")
        four = package.opponent(pool, seed, len(ids))
        order = draw_order(seed, len(ids))
        self.assertEqual(
            sorted(order),
            list(range(len(ids))),
            "a draw of the whole membership is a permutation of it (seats.md §2, "
            "league.md §2, ASM-43): %r" % (order,),
        )
        self.assertEqual(
            len(four),
            len(ids),
            "a count equal to the membership is accepted and returns that many policies "
            "(seats.md §2, ASM-43): %r" % (four,),
        )
        batch = probe_batch(4)
        references = self.references(pool, seed)
        for seat, position in enumerate(order):
            with self.subTest(seat=seat):
                self.assertEqual(
                    answers_of(four[seat], batch),
                    answers_of(references[position], batch),
                    "the four policies are four **distinct** members, in the draw's order, "
                    "each built as the uncounted draw builds it (seats.md §2, §4, "
                    "docs/L1/seats.md §4, ASM-43): seat %d is %r"
                    % (seat, ids[position]),
                )
        self.assertEqual(
            len(set(order)),
            len(ids),
            "the four seats are four **distinct** membership positions and not one member "
            "four times, which is what a draw is without replacement means; on the default "
            "shape two members may answer alike on a readout -- `fold-large-bet` never "
            "folds there and calls exactly where `always-call` does -- so the membership is "
            "named by the draw's positions and each seat is held to its own member's "
            "reference above (seats.md §2, §4, docs/L1/seats.md §4, ASM-43): %r"
            % (order,),
        )

    # -- the four refusals -- a cell is a pair (seats.md §3, §5) ----------------
    def test_evl_15_6_the_four_pairwise_entry_points_refuse_a_six_seat_shape(self):
        """EVL-15.6 `match`, `matrix`, `rating` and `report` each refuse a six-seat shape as `SeatCountExceeded`, naming the shape and its seat count, and each of the same four calls returns normally on the default shape and on the two-seat no-limit shape (`seats.md` §3, §5, `docs/L1/seats.md` §5, `league.md` §4, D-22, D-33)."""
        package = self.evaluation()
        shape = six_seat_shape()
        groups = ((shape,), (str(seats_of(shape)),))

        def six_seat_side(readout, legal_actions):
            """An opaque callable whose own `game` names the six-seat shape (`shape.md` §4)."""
            return legal_actions[0]

        six_seat_side.game = shape
        self.refused(
            lambda: package.match(six_seat_side, first_legal, 2, MATCH_SEED),
            "match",
            groups=groups,
            label="match(six-seat side, plain side, 2, seed)",
            kind="SeatCountExceeded",
        )
        pool = self.six_seat_pool()
        self.refused(
            lambda: package.matrix(pool, [first_legal], "live"),
            "matrix",
            groups=groups,
            label="matrix(six-seat pool, one variant, live)",
            kind="SeatCountExceeded",
        )
        matrix, rating, record, rung = self.six_seat_table()
        self.refused(
            lambda: package.rating(matrix),
            "rating",
            groups=groups,
            label="rating(a complete six-seat matrix)",
            kind="SeatCountExceeded",
        )
        self.refused(
            lambda: package.report(rung, record, matrix, rating),
            "report",
            groups=groups,
            label="report(a complete six-seat run record)",
            kind="SeatCountExceeded",
        )

        # ... and the same four calls on the two two-seat shapes.  A cell of two hands is
        # enough for `match`: the subject is the seat count the cell is played at, not a
        # census (scheduler.md §1, §4, seats.md §5, D-33).
        cell = package.match("random", "always-call", 2, MATCH_SEED)
        self.assertEqual(
            cell["game"],
            default_shape(),
            "a two-hand cell of two shape-silent sides is played on the default shape and "
            "the instrument accepts it (scheduler.md §5, shape.md §2, seats.md §5): %r"
            % (cell.get("game"),),
        )
        # The same no-limit container the seven-member pool declares: one new real
        # checkpoint is all this battery writes, and two cases naming its spec share it
        # (`scheduler.md` §5.1, `shape.md` §4, G13, D-29).
        info = self.checkpoint(name="member", game=other_shape())
        member = version_record(
            VERSION_IDS[3],
            "own-start-seats-5602",
            path=info["path"],
            game=other_shape(),
        )
        cell = package.match("random", member, 2, MATCH_SEED)
        self.assertEqual(
            cell["game"],
            other_shape(),
            "a cell against a no-limit version is played on that shape, and the instrument "
            "accepts it because its seat count is the arity (scheduler.md §5, shape.md "
            "§3-§4, seats.md §5, D-33): %r" % (cell.get("game"),),
        )
        table = self.shared_matrix("k4")
        self.assertEqual(
            table["game"],
            default_shape(),
            "the battery's shared live table is a two-seat table and matrix returns it "
            "(matrix.md §1, §5, seats.md §5): %r" % (table.get("game"),),
        )
        fitted = self.shared_rating("k4")
        self.assertEqual(
            set(fitted["values"]),
            set(table["members"]),
            "a rating over the same two-seat table fits one value per member, so the seat "
            "count refuses nothing it used to accept (rating.md §1, §6, seats.md §5, "
            "D-33): %r" % (fitted.get("values"),),
        )
        assembled = package.report(
            RUNG_NAME, run_record(table, fitted), table, fitted
        )
        self.assertEqual(
            assembled["rung"],
            RUNG_NAME,
            "a report of that table and that rating is assembled, its seven families and "
            "its five facts intact (report.md §1-§3, seats.md §5, D-33): %r"
            % (assembled.get("rung"),),
        )
        # ... and on the two-seat no-limit shape beside it.  `matrix` is reached on a pool
        # of that shape without playing a table: the seat count is read **first**, so an
        # uncallable variant is refused by `matrix` itself and not by the instrument, which
        # is the cheap way to see that the pairwise check accepted the shape
        # (matrix.md §7, seats.md §3, §5, D-33).
        no_limit_table = hand_matrix(
            balanced, game=other_shape(), cell_game=other_shape()
        )
        fitted = package.rating(no_limit_table)
        self.assertEqual(
            set(fitted["values"]),
            set(no_limit_table["members"]),
            "a rating over a hand-built table of the two-seat no-limit shape fits one "
            "value per member, the seat count refusing nothing (rating.md §1, §6, "
            "seats.md §5, D-33): %r" % (fitted.get("values"),),
        )
        rung, record, no_limit_table, fitted = report_inputs(game=other_shape())
        assembled = package.report(rung, record, no_limit_table, fitted)
        self.assertEqual(
            assembled["header"]["shape"],
            other_shape(),
            "a report of that shape's records is assembled and its header names the shape "
            "the three records agree on (report.md §3 item 6, shape.md §4, seats.md §5, "
            "D-33): %r" % (assembled.get("header"),),
        )
        for shape in (default_shape(), other_shape()):
            with self.subTest(shape=shape, entry="matrix", after="the seat count"):
                two_seat_pool = self.evaluation().build_pool(
                    declaration(members=(), m=POOL_M, frozen=True, game=shape)
                )
                self.refused(
                    lambda: package.matrix(two_seat_pool, [42], "live"),
                    "matrix",
                    groups=(("variant",),),
                    label="matrix(a %r pool, [42], live)" % (shape,),
                    kind="VariantInvalid",
                )

    # -- a two-seat pool is unchanged (seats.md §4, §5, D-33) -------------------
    def test_evl_15_7_a_two_seat_pool_is_unchanged(self):
        """EVL-15.7 on both two-seat shapes a pool declaring the three folders has the anchors' and folders' ids in the catalogue's order, records that carry exactly `id`, `baseline`, `pinned`, `params` and `game: None`, a `pool_digest` id that does not move with the shape, and an uncounted draw that names the member at `seed % n` -- so a baseline's record and the pool's id are exactly what they are today (`seats.md` §4, `docs/L1/records.md` §8, `pool.md` §5, `families.md` §4, ASM-27, ASM-32, D-33)."""
        package = self.evaluation()
        folder_names = self.folders()
        expected_ids = tuple(BASELINES) + folder_names
        expected_records = tuple(
            {"id": name, "baseline": True, "pinned": True, "params": 0, "game": None}
            for name in expected_ids
        )
        expected_id = pool_digest(list(expected_records))
        seen = []
        for shape in (default_shape(), other_shape()):
            with self.subTest(shape=shape):
                pool = self.evaluation().build_pool(
                    declaration(
                        members=(),
                        m=POOL_M,
                        frozen=True,
                        game=shape,
                        baselines=folder_names,
                    )
                )
                record = self.pool_members(pool)
                seen.append(pool.id)
                self.assertEqual(
                    record["game"],
                    shape,
                    "the pool reads back with the shape it was declared on, and the shape "
                    "is a field of the pool and never of its id (shape.md §4, pool.md §5, "
                    "families.md §4, D-33): %r vs %r" % (record["game"], shape),
                )
                self.assertEqual(
                    pool_member_ids(record),
                    expected_ids,
                    "the pinned anchors come first in the catalogue's order and the "
                    "declared folders follow them, in that same order, whatever the "
                    "declaration's sequence says (pool.md §2, ASM-32, D-21): %r vs %r"
                    % (pool_member_ids(record), expected_ids),
                )
                self.assertEqual(
                    tuple(record["members"]),
                    expected_records,
                    "a baseline's member record is exactly its id, `baseline`, `pinned`, "
                    "`params` and `game: None` -- a baseline is shape-silent, so the pool's "
                    "shape never enters it and a default-shape pool's records are the ones "
                    "it held before the third row existed (records.md §8, pool.md §5, "
                    "seats.md §4, D-33): %r" % (record["members"],),
                )
                for member in record["members"]:
                    with self.subTest(shape=shape, member=member_id(member)):
                        self.assertEqual(
                            set(member),
                            {"id", "baseline", "pinned", "params", "game"},
                            "a pinned baseline's record carries these five keys and no "
                            "sixth (records.md §8, scheduler.md §4, seats.md §4): %r"
                            % (member,),
                        )
                        self.assertIsNone(
                            member["game"],
                            "a baseline's `game` is `None` on every shape, because the "
                            "shape it is built for is the pool's and passed to "
                            "agents.build_baseline (pool.md §5, seats.md §4, ASM-31, "
                            "D-33): %r" % (member,),
                        )
                self.assertEqual(
                    record["id"],
                    expected_id,
                    "the id is families.md §4's digest over the ordered membership lines, "
                    "recomputed here, and the shape is not in the payload "
                    "(families.md §4, ASM-27, D-33): %r vs %r"
                    % (record["id"], expected_id),
                )
                self.assertEqual(
                    pool.id,
                    expected_id,
                    "the pool's own id is the record's, and it is a function of the "
                    "membership alone (families.md §4, pool.md §5, ASM-27, D-33): %r vs %r"
                    % (pool.id, expected_id),
                )
                batch = probe_batch(4)
                for seed in range(12):
                    with self.subTest(shape=shape, seed=seed):
                        drawn = package.opponent(pool, seed)
                        name = expected_ids[seed % len(expected_ids)]
                        self.assertTrue(
                            callable(drawn),
                            "a draw without a count is one policy on every shape "
                            "(seats.md §2, ASM-43): %r" % (drawn,),
                        )
                        self.assertEqual(
                            answers_of(drawn, batch),
                            answers_of(
                                self.agents().build_baseline(name, seed, shape), batch
                            ),
                            "the draw names the member at seed %% n and builds it for the "
                            "pool's shape, which on a two-seat shape is the policy it "
                            "always built (seats.md §2, §4, pool.md §7, ASM-31, ASM-43): "
                            "seed %r names %r" % (seed, name),
                        )
        self.assertEqual(
            len(set(seen)),
            1,
            "the pool id does not move with the shape, because a shape is a field of the "
            "pool and never of its id (families.md §4, shape.md §4, ASM-27, D-33): %r"
            % (seen,),
        )

    # -- a six-seat pool's baselines read the pool's own rows (seats.md §4) ----
    def test_evl_15_8_a_six_seat_pool_s_baselines_read_the_pool_s_own_rows(self):
        """EVL-15.8 a six-seat pool's drawn `fold-large-bet` and drawn `oracle` are `agents.build_baseline`'s policies for the six-seat shape; the folder folds where `2 x to_call` exceeds **that** shape's declared stack and calls where it does not, while the default-shape build answers the default's boundary; the oracle answers a legal descriptor on every decision of a real six-seat hand; and building the six-seat pool leaves the default-shape pool untouched (`seats.md` §2, §4, `docs/L1/seats.md` §4, `folders.md` §2, ASM-31, D-33)."""
        package = self.evaluation()
        shape = six_seat_shape()
        # The default-shape pool of the same declaration, read before the six-seat pool is
        # built and again after it: a baseline's records and the pool's id are the
        # membership's and no shape's (records.md §8, families.md §4, seats.md §4).
        untouched_pool = self.evaluation().build_pool(
            declaration(members=(), m=POOL_M, frozen=True, baselines=self.folders())
        )
        untouched = self.pool_members(untouched_pool)
        pool = self.six_seat_pool()
        record = self.pool_members(pool)
        ids = pool_member_ids(record)
        self.assertEqual(
            record["game"],
            shape,
            "the pool is on the six-seat shape and says so on read-back (shape.md §4, "
            "pool.md §5, seats.md §4): %r" % (record["game"],),
        )
        self.assertEqual(
            len(ids),
            6,
            "the six-seat pool holds the three anchors and the three folders, the "
            "composition docs/L1/seats.md §2, §4 declares for a six-seat hand "
            "(records.md §8, ASM-32, D-21): %r" % (ids,),
        )
        folder_position = 5
        oracle_position = 2
        self.assertEqual(
            ids[folder_position],
            self.folders()[-1],
            "the drawn folder is the catalogue's last baseline, in the catalogue's order "
            "(pool.md §2, ASM-32, D-21): %r" % (ids,),
        )
        self.assertEqual(
            ids[oracle_position],
            BASELINES[2],
            "the drawn oracle is the third pinned anchor, in the catalogue's order "
            "(protocol.md §3, ASM-32): %r" % (ids,),
        )
        folder_seed = folder_position
        oracle_seed = oracle_position
        self.assertEqual(
            folder_seed % len(ids),
            folder_position,
            "a seed congruent to the folder's position draws it, because the draw is "
            "seed %% n (scheduler.md §3, pool.md §7, ASM-43): %r" % (folder_seed,),
        )
        self.assertEqual(
            oracle_seed % len(ids),
            oracle_position,
            "and a seed congruent to the oracle's position draws it (scheduler.md §3, "
            "pool.md §7, ASM-43): %r" % (oracle_seed,),
        )
        readout, legal = self.six_seat_readout()
        stack = int(self.engine().game_config(shape)["starting_stack"])
        default_stack = int(self.engine().game_config(default_shape())["starting_stack"])
        self.assertGreater(
            stack,
            default_stack,
            "the six-seat row's declared stack is the deeper one, which is what moves the "
            "folder's boundary (docs/L1/seats.md §2, folders.md §2, ASM-31, D-33): %r vs %r"
            % (stack, default_stack),
        )
        batch = tuple(
            (dict(readout, to_call=value), legal) for value in STACK_BOUNDARIES
        )
        drawn_folder = package.opponent(pool, folder_seed)
        six_seat_folder = self.agents().build_baseline(ids[folder_position], folder_seed, shape)
        default_folder = self.agents().build_baseline(ids[folder_position], folder_seed)
        self.assertEqual(
            answers_of(drawn_folder, batch),
            answers_of(six_seat_folder, batch),
            "the drawn folder is agents.build_baseline(name, seed, the pool's shape) and "
            "not the default-shape construction (seats.md §4, docs/L1/seats.md §4, "
            "ASM-31, D-33)",
        )
        for value in STACK_BOUNDARIES:
            copy = dict(readout, to_call=value)
            with self.subTest(to_call=value):
                self.assertEqual(
                    six_seat_folder(copy, legal),
                    "fold" if 2 * value > stack else "check-call",
                    "the six-seat build folds exactly where 2 x to_call exceeds **that** "
                    "row's declared stack of %d and calls where it does not, so its "
                    "boundary is 51 and not 11 (seats.md §4, folders.md §2, ASM-31, "
                    "D-33): to_call %d" % (stack, value),
                )
                self.assertEqual(
                    default_folder(copy, legal),
                    "fold" if 2 * value > default_stack else "check-call",
                    "while the default-shape build answers the default row's boundary, "
                    "which is 11 on its %d chips -- the same rule read off each shape's "
                    "own starting stack (seats.md §2, §4, folders.md §2, ASM-31, D-33): "
                    "to_call %d" % (default_stack, value),
                )
        self.assertEqual(
            six_seat_folder(dict(readout, to_call=11), legal),
            "check-call",
            "11 is a call on the six-seat row's hundred chips and a fold on the "
            "default's twenty, so a policy built for the wrong shape is visible here "
            "(seats.md §2, §4, ASM-31, D-33)",
        )
        self.assertEqual(
            six_seat_folder(dict(readout, to_call=51), legal),
            "fold",
            "and 51 is a fold on the six-seat row, one chip past half its stack "
            "(seats.md §4, folders.md §2, ASM-31, D-33)",
        )
        drawn_oracle = package.opponent(pool, oracle_seed)
        self.assertEqual(
            answers_of(drawn_oracle, batch),
            answers_of(
                self.agents().build_baseline(ids[oracle_position], oracle_seed, shape),
                batch,
            ),
            "the drawn oracle is the six-seat build too, so the equity question it asks "
            "is that readout's six-way one (seats.md §2, §4, ASM-31, D-33)",
        )
        decisions = self.six_seat_decisions()
        self.assertGreaterEqual(
            len(decisions),
            4,
            "a real six-seat hand reaches several decisions to ask the oracle on "
            "(engine/surface.md §4-§6): %r" % (len(decisions),),
        )
        for position, (facts, actions) in enumerate(decisions):
            with self.subTest(decision=position):
                answer = drawn_oracle(facts, actions)
                self.assertIn(
                    answer,
                    actions,
                    "the drawn oracle answers one descriptor of the deal's own legal set "
                    "on every decision of a six-seat hand, so its equity is that shape's "
                    "and never a three-index vocabulary's (surface.md §2, seats.md §2, "
                    "§4, ASM-31, D-33): %r against %r" % (answer, actions),
                )
                self.assertIn(
                    "raise-quarter",
                    actions,
                    "the deal's legal set is the six-descriptor vocabulary, which is how "
                    "the case knows the hand was dealt on the six-seat shape "
                    "(docs/L1/seats.md §2-§3, features/surface.md §9, D-33): %r"
                    % (actions,),
                )
        self.assertEqual(
            self.pool_members(untouched_pool),
            untouched,
            "building the six-seat pool leaves the default-shape pool's id, membership and "
            "member records untouched, because a shape is a field of one pool and never a "
            "change to another (pool.md §1, §5, families.md §4, seats.md §4, D-33)",
        )

    # -- the league builds no six-seat table in this pass (seats.md §3, §5) ----
    def test_evl_15_9_the_league_builds_no_six_seat_table_in_this_pass(self):
        """EVL-15.9 `matrix` refuses a six-seat pool **before** a variant or a checkpoint is touched -- a variant that is not even callable is never reached -- while `rating` and `report` refuse the six-seat table, and the six-seat pool's own read-back still states its shape, its two populations and its six members, so a run can freeze a pool and draw opponents and pass no matrix at all (`seats.md` §1, §3, §5, `docs/L1/seats.md` §5, `records.md` §12-§13, D-22, D-33)."""
        package = self.evaluation()
        shape = six_seat_shape()
        pool = self.six_seat_pool()
        record = self.pool_members(pool)
        self.assertEqual(
            record["game"],
            shape,
            "a six-seat run still freezes a pool and reads it back on its own shape "
            "(pool.md §5, seats.md §1, §4, D-33): %r" % (record["game"],),
        )
        self.assertEqual(
            len(record["members"]),
            6,
            "the pool's four anchors-and-folders membership is complete and readable "
            "(records.md §8, docs/L1/seats.md §4): %r" % (record["members"],),
        )
        self.assertEqual(
            tuple(record["rules"]),
            (),
            "a baselines-only membership declares no learning rule, and the read-back says "
            "so as the empty tuple (records.md §8, pool.md §5, rules.md §4, D-19): %r"
            % (record["rules"],),
        )
        self.assertEqual(
            tuple(record["utilities"]),
            (),
            "and no utility either, on the same terms (records.md §8, pool.md §5, "
            "utilities.md §5, D-20): %r" % (record["utilities"],),
        )
        # A variant that is not callable is never reached: `matrix` refuses the shape
        # **before** it looks at a variant or touches a checkpoint, so the refusal here is
        # the seat count's and not VariantInvalid's (matrix.md §7, seats.md §3, §5).
        self.refused(
            lambda: package.matrix(pool, [42], "live"),
            "matrix",
            groups=((shape,), (str(seats_of(shape)),)),
            label="matrix(six-seat pool, [42], live)",
            kind="SeatCountExceeded",
        )
        matrix, rating, record_of_run, rung = self.six_seat_table()
        self.refused(
            lambda: package.rating(matrix),
            "rating",
            groups=((shape,), (str(seats_of(shape)),)),
            label="rating(a six-seat matrix)",
            kind="SeatCountExceeded",
        )
        self.refused(
            lambda: package.report(rung, record_of_run, matrix, rating),
            "report",
            groups=((shape,), (str(seats_of(shape)),)),
            label="report(a six-seat run record)",
            kind="SeatCountExceeded",
        )
        self.assertTrue(
            pool.frozen,
            "the pool a six-seat run freezes is frozen, which is what a draw and a hand "
            "need of it and what a matrix would have demanded too (pool.md §1, "
            "matrix.md §1, seats.md §1): %r" % (pool.frozen,),
        )
        drawn = package.opponent(pool, 0, 5)
        self.assertEqual(
            len(drawn),
            5,
            "five opponents are drawn from that pool without replacement, which is the "
            "whole of what a six-seat hand needs and all this pass builds "
            "(docs/L1/seats.md §4, §5, ASM-43, D-33): %r" % (drawn,),
        )
        self.assertEqual(
            len({id(policy) for policy in drawn}),
            5,
            "the five seats are five distinct policies, drawn without replacement "
            "(docs/L1/seats.md §4, league.md §2, ASM-43): %r" % (drawn,),
        )


if __name__ == "__main__":
    unittest.main()
