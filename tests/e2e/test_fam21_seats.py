"""FAM-21 — the third declared shape: six seats, six hundred chips, and a block of 98.

`docs/L1/battery.md` §3 FAM-21, `docs/L1/seats.md` §2–§6, `docs/L1/shapes.md` §2 and §8,
`docs/L1/e2e-surface.md` §2 "Game shape", §3.1, §3.3–§3.5, `docs/L1/records.md` §5, §8, §15,
D-33.  The project declares a **third** game shape beside D-2's fixed-limit one and D-29's
two-seat no-limit one, and the seat count is shape data: `engine.game_shapes()` publishes
three rows, default first, and the third is reached as any configuration outside the
registry is — as a value through `training.run`.

What this family asserts, case by case:

* the catalogue's third row declares **six seats**, **600 chips in play** — `pot +
  sum(stacks)` at every decision — a history capacity of **98** and its own layout widths
  (433 dense, 122 tokens over the vocabulary of 102), with the default and the two-seat
  uncapped rows unchanged (203/40/96/24 and 329/82/96/66) (`shapes.md` §2, §8, `seats.md`
  §2–§3);
* a shape's capacity is the block's own refusal threshold: 98 entries encode on the
  six-seat shape and **one slot more is refused naming the field, the capacity and the
  count**, and 66 entries encode on the two-seat uncapped shape where 98 do not fit
  (`shapes.md` §8, ASM-42, D-33);
* a six-seat hand seats the shape's **whole seating** — the optional `seats` argument, one
  policy per seat, the two positional policies absent — and a wrong length, or a seating
  beside two positional policies, is refused by name (`seats.md` §4, `e2e-surface.md`
  §3.1);
* such a hand reports **one payoff per seat**, six of them, summing to zero, and its
  readout carries six stacks and a seat index in `0..5` (`records.md` §5, `seats.md` §3,
  ASM-28);
* `evaluation.opponent(pool, seed, 5)` returns **five distinct members** drawn without
  replacement, two calls at one seed agree, and a pool holding four is refused naming both
  counts (`seats.md` §4, ASM-43);
* `agents.build_baseline`'s optional shape is the stack `fold-large-bet` reads, so "half the
  stack" is 50 on a hundred-chip row and 10 on the default one (`seats.md` §6, ASM-31,
  ASM-34);
* a learner on the six-seat shape takes its **input width from that shape's encoder** —
  `param_count` 18,510 at `W = 36`, `D = 2`, the 433-wide block and the six-wide head — while
  an encoder-less spec naming it is refused by name (`shapes.md` §8, ASM-44,
  `e2e-surface.md` §3.3);
* `evaluation.match`, `matrix`, `rating` and `report` **refuse a six-seat shape by name**,
  naming the shape and its seat count, because a cell is a pair and a six-way hand is a
  placement (`seats.md` §5, `league.md` §4, D-22, D-33);
* a six-seat `training.run` records the shape it played, the membership it trained against
  and its `greedy` block, and the learner's seat's decisions are the shape's six
  (`records.md` §12, §15, `seats.md` §4, §6);
* with **no shape named** every fixed-limit assertion of FAM-2, FAM-5, FAM-7, FAM-14,
  FAM-16, FAM-19 and FAM-20 is unchanged, the pairwise instrument included (`shapes.md`
  §5, D-29, D-33).

The three shapes' names, their rows, their layouts and their widths are the design's own
and are not invented here: the catalogue row is `fixed`, because its instances **are** the
declaration and no caller can invent a shape through the surface (`e2e-surface.md` §5,
`battery.md` §4).  The **instances** this family drives are the battery's: its own seeds,
its own versions, its own configuration and its own hand-built six-seat table (`battery.md`
§4, D-15).
"""

import os
import sys
import unittest

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _records as R  # noqa: F401
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _records as R  # noqa: E402
    import _surface as S  # noqa: E402


#: `seats.md` §2: the third declared row, as the catalogue states it.  The values are the
#: **design's** — the row is `fixed` — and the vocabulary is that shape's own index order,
#: the six descriptors the two no-cap rows share because a seat count adds none
#: (`shapes.md` §2, `sizing.md` §2–§3, D-33).
THIRD_ROW = {
    "name": S.SHAPE_THIRD,
    "default": False,
    "seats": 6,
    "blinds": (1, 2),
    "starting_stack": 100,
    "chips_in_play": 600,
    "history": 98,
    "bet_structure": "no-limit",
    "small_bet": None,
    "big_bet": None,
    "raise_cap": None,
    "actions": S.SIZED_ACTIONS,
    "head_width": 6,
    "normalisers": {"stack": 100, "pot": 600, "to_call": 100, "amount": 100, "count": 50},
}

#: `shapes.md` §2, §8: the two rows beside it, unchanged — the default shape's 203/40/96/24
#: over two seats and 40 chips, and the two-seat uncapped row's 329/82/96/66 over 200.
TWO_SEAT_ROWS = {
    S.SHAPE_DEFAULT: {"seats": 2, "chips_in_play": 40, "history": 24,
                      "dense": 203, "tokens": 40, "vocabulary": 96, "head_width": 3},
    S.SHAPE_SECOND: {"seats": 2, "chips_in_play": 200, "history": 66,
                     "dense": 329, "tokens": 82, "vocabulary": 96, "head_width": 6},
}

#: `shapes.md` §8: 98 is the six-seat row's capacity and one slot more is the block's
#: refusal; 66 is the two-seat uncapped row's, and the six-seat block holds a 66-entry
#: history whole (`seats.md` §2, ASM-42).
SIX_SEAT_CAPACITY = 98
TWO_SEAT_CAPACITY = 66
SIX_SEAT_DENSE = 433
SIX_SEAT_TOKENS = 122
SIX_SEAT_VOCABULARY = 102

#: `shapes.md` §8: `param_count` at `W = 36`, `D = 2` on the six-seat row — the 433-wide
#: input block and the six-wide head — against the default shape's unchanged 10,119.
SIX_SEAT_PARAMS = 18510
DEFAULT_PARAMS = 10119

#: `docs/L1/records.md` §8, `seats.md` §4: a six-seat hand seats `seats − 1` = five distinct
#: opponents from the frozen pool, so the pool holds at least five members and the three
#: pinned baselines are three of them.
SIX_SEAT_OPPONENTS = 5

#: `docs/L1/records.md` §15, `shapes.md` §8: a greedy pass records at most 1,000 × the
#: shape's history capacity per variant per seed — 24,000 at the default shape and 98,000
#: on this one.
PASS_HANDS_BOUND = 2000
SIX_SEAT_DECISIONS_BOUND = 1000 * SIX_SEAT_CAPACITY

#: One entry of the history grammar's documented forms, repeated to fill a block
#: (`flat-numeric.md` §5): a `calls` entry, whose action kind is neither a fold nor a bet,
#: so the entry is the grammar's and nothing about the amount is under test.  The battery's
#: own spelling of a value the grammar declares (`battery.md` §4).
HISTORY_ENTRY = "preflop seat 0 calls 2"

#: The invented cell count and table seed of the hand-built six-seat table FAM-21.9 hands
#: the pairwise instrument: the table is a record in `records.md` §10's shape, written by the
#: battery because no entry point may produce one on six seats and the cells' *values* are no
#: case's subject (`seats.md` §5, `battery.md` §5, D-15).
TABLED_HANDS = 13
TABLED_SEED = 61337


class FAM21Seats(S.SurfaceCase):
    """The six-seat shape: the row, the block, the seating, the draw, and four refusals."""

    # -- helpers -----------------------------------------------------------
    def declared(self):
        """The catalogue as ``[(name, row)]``, default first (§3.1, `shapes.md` §2)."""
        catalogue = self.shapes()
        self.assertTrue(
            catalogue,
            "engine.game_shapes() declares the shapes of the catalogue and not nothing "
            "(e2e-surface.md §3.1, shapes.md §2, seats.md §2)",
        )
        return catalogue

    def row_value(self, row, key):
        """One declared value of a row, under the row's own key or a tolerant spelling."""
        for name, value in row.items():
            if S._family_token(name) == S._family_token(key):
                return value
        raise AssertionError(
            "a shape row declares %r (shapes.md §2, seats.md §2); the row carries %r"
            % (key, sorted(str(name) for name in row))
        )

    def declared_width(self, shape, representation):
        """One shape's declared observation width, off ``observation_spec`` (§2, §3.2)."""
        spec = self.ep("features", "observation_spec")(self.encoder(representation, shape))
        width = 1
        for value in S.numbers(
            S.declared_field(spec, "an observation spec (e2e-surface.md §2)", "shape")
        ):
            width *= int(value)
        return width

    def declared_vocabulary(self, shape, representation=S.TOKENS):
        """One shape's declared token vocabulary, off ``observation_spec`` (§2, §3.2)."""
        spec = self.ep("features", "observation_spec")(self.encoder(representation, shape))
        return S.declared_field(
            spec, "an observation spec (e2e-surface.md §2)", "vocabulary"
        )

    def history_readout(self, shape, count):
        """One shaped readout carrying exactly ``count`` documented history entries.

        The readout is the shape's own — ``engine.readout`` of a hand dealt on it — and the
        entries are the history grammar's `calls` form repeated, because the block's
        contract is over the readout it is handed (`flat-numeric.md` §5,
        `docs/L2/features/capacity.md` §1, §3).  Nothing else about the readout is touched,
        so the only fact under test is the history's own length.
        """
        readout = dict(self.readout(self.hand(S.SEED_I, shape)))
        readout["history"] = [HISTORY_ENTRY] * count
        return readout

    def six_seat_pool(self, tags=("kestrel", "bramble")):
        """A pool on the six-seat shape holding the pinned baselines and its membership.

        `seats.md` §4: a six-seat hand draws five **distinct** members, so the declaration
        carries two of the battery's invented versions beside the three pinned baselines —
        five members in all (`records.md` §7–§8, ASM-43, `battery.md` §4).
        """
        return self.pool(tags=tags, game=S.SHAPE_THIRD)

    def six_seat_seating(self, seed=S.SEED_A):
        """One learner and five opponents, in seat order, for a six-seat hand.

        The learner is the battery's own (a 59-wide, 3-deep learner in the six-seat head)
        and the opponents are the pool's five distinct members drawn at ``seed`` — so the
        seating is the shape's whole table, one policy per seat, and no seat faces itself
        (`seats.md` §2, §4, records.md §5, ASM-43).
        """
        pool = self.six_seat_pool()
        opponents = list(self.ep("evaluation", "opponent")(pool, seed, SIX_SEAT_OPPONENTS))
        self.assertEqual(
            len(opponents), SIX_SEAT_OPPONENTS,
            "a six-seat hand seats five opponents beside the learner (seats.md §4, "
            "records.md §8): the draw returned %r" % (opponents,),
        )
        learner = self.learner(
            width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH, seed=seed, game=S.SHAPE_THIRD
        )
        head = self.policy(learner, self.encoder(shape=S.SHAPE_THIRD), seed)
        return [head] + opponents

    def six_seat_episode(self, seed=S.SEED_A, seating=None):
        """One six-seat episode on the shape's whole seating (`e2e-surface.md` §3.1)."""
        if seating is None:
            seating = self.six_seat_seating(seed)
        return self.play(seed, seats=seating, shape=S.SHAPE_THIRD)

    def six_seat_table(self):
        """A six-seat table in ``records.md`` §10's shape, and a rating record for it.

        No entry point may build one — `evaluation.matrix` refuses a shape whose seat count
        is not a pair's (`seats.md` §5) — so the record is the battery's, written to carry
        the **shape** and the seat count the pairwise instrument must refuse.  K = 4, the
        three anchor baselines and one invented member, six cells, and nothing about the
        cells' values is read (`battery.md` §5, D-15).
        """
        members = list(S.ANCHOR_BASELINES) + ["version-nimbus"]
        hands = TABLED_HANDS
        button = hands // 2

        def direction(wins, losses, delta, held, other):
            return {
                "wins": wins,
                "ties": hands - wins - losses,
                "losses": losses,
                "mean_chip_delta": delta,
                "seat_split": {"button": held, "big blind": other},
            }

        cells = []

        def cell(left, right, left_wins, left_delta):
            cells.append({
                "members": [left, right],
                "hands": hands,
                "directions": [
                    direction(left_wins, hands - left_wins, left_delta, button,
                              hands - button),
                    direction(hands - left_wins, left_wins, -left_delta,
                              hands - button, button),
                ],
                "params": [0, 0],
                "rules": {left: None, right: None},
                "utilities": {left: None, right: None},
                "seed": TABLED_SEED,
                "game": S.SHAPE_THIRD,
            })

        cell("random", "always-call", 8, 0.25)
        cell("random", "oracle", 5, -0.75)
        cell("always-call", "oracle", 6, -0.5)
        cell("version-nimbus", "random", hands, 2.0)
        cell("version-nimbus", "always-call", hands, 2.0)
        cell("version-nimbus", "oracle", hands, 2.0)
        return {
            "members": members,
            "cells": cells,
            "hands_per_cell": hands,
            "table_seed": TABLED_SEED,
            "table": "live",
            "game": S.SHAPE_THIRD,
            "rules": {member: None for member in members},
            "population": (),
            "utilities": {member: None for member in members},
            "utility_population": (),
        }

    def hand_built_rating(self, matrix):
        """A ``records.md`` §11 rating record for a matrix no fit may produce.

        `evaluation.rating` refuses the six-seat table before a value is fitted, so the
        report case needs a rating record to hand `evaluation.report`; the numbers are the
        battery's own and the values are no case's subject (`battery.md` §5, D-15).
        """
        return {
            "values": {
                member: {"value": 0.0, "interval": (-0.5, 0.5), "hands": TABLED_HANDS}
                for member in matrix["members"]
            },
            "method": "Bradley-Terry",
            "anchor": list(S.ANCHOR_BASELINES),
            "bound_applied": False,
            "bootstrap_seed": S.TABLE_SEED_B,
            "converged": True,
        }

    def seating_of(self, decision):
        """The seat index one decision record's own `seat` fact names (``records.md`` §5)."""
        value = R.decision_seat(decision)
        return int(value) if S.is_count(value) else -1

    def decisions_of(self, episode):
        """Every decision of an episode record, in order (``records.md`` §5)."""
        return R.decision_records(episode)

    def refusal_for_shape(self, call, what):
        """Run one call, require a refusal, and return its text.

        A refusal must name the shape and its seat count — `seats.md` §5 makes that the
        observable, because a caller has to see which shape was refused and why a pair's
        instrument cannot measure it (`league.md` §4, D-22, D-33).
        """
        text = S.refusal_text(call)
        self.assertIsNotNone(
            text,
            "%s refuses a shape whose seat count is not a pair's, naming the shape and its "
            "seat count, and never measures a six-way hand as a cell (e2e-surface.md §3.4, "
            "seats.md §5, D-33)" % (what,),
        )
        self.assertIn(
            S._family_token(S.SHAPE_THIRD),
            S._family_token(text),
            "%s's refusal names the shape it refused (seats.md §5): %r" % (what, text),
        )
        self.assertIn(
            str(THIRD_ROW["seats"]),
            text,
            "%s's refusal names the seat count — six — so a reader sees why a cell, which "
            "is a pair, cannot hold it (seats.md §5): %r" % (what, text),
        )
        return text

    # -- the row (shapes.md §2, §8; seats.md §2) ---------------------------
    def test_fam21_1_the_third_row_declares_six_seats_600_chips_and_98_slots(self):
        """FAM-21.1 six seats, 600 chips in play, 98 slots, 433/122/102 — and the two rows beside it.

        `shapes.md` §2 makes the catalogue one ordered declaration, default first, and
        `seats.md` §2 adds the third row: six seats, blinds 1/2, 100 chips a seat and 600 in
        play, no fixed bet and no cap, the same six descriptors in the same index order, and
        its own derived history capacity of 98 with 433 dense slots and 122 tokens over a
        vocabulary of 102 — the six seat ids above every id the other rows use.  The two
        two-seat rows are asserted **unchanged** beside it, because the widening is the new
        row's and the fixed-limit path is not touched (`shapes.md` §5, §8, `seats.md` §2–§3,
        ASM-42, ASM-44).
        """
        catalogue = self.declared()
        names = [name for name, _row in catalogue]
        self.assertEqual(
            names[:3],
            [S.SHAPE_DEFAULT, S.SHAPE_SECOND, S.SHAPE_THIRD],
            "the catalogue declares the default shape first and the two shapes beside it — "
            "`fixed-limit-20`, `no-limit-100`, `six-seat-no-limit-100` — in that order "
            "(shapes.md §2, seats.md §2, D-29, D-33): %r" % (names,),
        )
        rows = dict(catalogue)
        row = rows[S.SHAPE_THIRD]
        present = {S._family_token(name) for name in row}
        missing = [key for key in THIRD_ROW if S._family_token(key) not in present]
        self.assertFalse(
            missing,
            "the six-seat row carries every fact the catalogue declares of it — its seats, "
            "stack, chips in play, capacity, bet structure, vocabulary, head width and "
            "normalisers (e2e-surface.md §3.1, shapes.md §2, seats.md §2); it is missing %r "
            "and carries %r" % (missing, sorted(str(name) for name in row)),
        )
        for key, wanted in THIRD_ROW.items():
            if key == "normalisers":
                normalisers = S.normalisers_of(row)
                for name, value in wanted.items():
                    self.assertEqual(
                        int(S.declared_field(
                            normalisers, "a shape row's normalisers (shapes.md §2)", name,
                        )),
                        value,
                        "the six-seat row's `%s` normaliser is %r — the stack, the blinds "
                        "and the divisors are the two-seat uncapped row's, and the pot divides "
                        "by the 600 chips in play because a divisor of 200 on a six-seat pot "
                        "is a clip (shapes.md §2, sizing.md §5, ASM-39): %r"
                        % (name, value, normalisers),
                    )
                continue
            if key == "actions":
                self.assertEqual(
                    tuple(S.vocabulary_of(row)),
                    wanted,
                    "a seat count adds no descriptor: the six-seat row declares the same six "
                    "in the same index order as the two-seat uncapped one (shapes.md §2, "
                    "sizing.md §3, D-33): %r" % (S.vocabulary_of(row),),
                )
                continue
            if key == "history":
                self.assertEqual(
                    S.history_capacity_of(row),
                    wanted,
                    "the six-seat row's history capacity is its own derived bound, 98 — "
                    "600 ÷ 12 = 50 raises plus 4 × 6 × 2 = 48 non-bet actions (shapes.md §8, "
                    "ASM-42, D-33): %r" % (S.history_capacity_of(row),),
                )
                continue
            if key == "default":
                self.assertIs(
                    bool(self.row_value(row, "default")),
                    wanted,
                    "the six-seat row is not the default shape (shapes.md §2)",
                )
                continue
            got = self.row_value(row, key)
            if isinstance(wanted, tuple):
                self.assertEqual(
                    tuple(got), wanted,
                    "the six-seat row's %s is %r (shapes.md §2, seats.md §2): %r"
                    % (key, wanted, got),
                )
            else:
                self.assertEqual(
                    got, wanted,
                    "the six-seat row's %s is %r (shapes.md §2, seats.md §2): %r"
                    % (key, wanted, got),
                )
        # ... and its own layout widths, declared and returned.
        readout = self.readout(self.hand(S.SEED_B, S.SHAPE_THIRD))
        for representation, wanted in ((S.FLAT, SIX_SEAT_DENSE),
                                       (S.TOKENS, SIX_SEAT_TOKENS)):
            width = self.declared_width(S.SHAPE_THIRD, representation)
            self.assertEqual(
                width, wanted,
                "the six-seat row's %r observation is %d wide — 433 dense slots and 122 "
                "tokens over its own capacity (shapes.md §8, seats.md §3): declared %d"
                % (representation, wanted, width),
            )
            observation = self.ep("features", "encode")(
                self.encoder(representation, S.SHAPE_THIRD), readout)
            self.assertEqual(
                len(observation), width,
                "the six-seat encoder returns one observation of its declared width "
                "(e2e-surface.md §2): %d values, declared %d" % (len(observation), width),
            )
        self.assertEqual(
            int(self.declared_vocabulary(S.SHAPE_THIRD)),
            SIX_SEAT_VOCABULARY,
            "the six-seat token vocabulary is 102 — one id per seat slot above the top id "
            "the other rows use, so no existing id is renamed (seats.md §3, shapes.md §8): "
            "%r" % (self.declared_vocabulary(S.SHAPE_THIRD),),
        )
        # The two rows beside it, unchanged: the widening is the new row's.
        for shape, expected in TWO_SEAT_ROWS.items():
            declared = rows[shape]
            self.assertEqual(
                int(self.row_value(declared, "seats")), expected["seats"],
                "%r still seats two: the third row adds a seat count and moves no other "
                "row's (shapes.md §5, seats.md §2): %r"
                % (shape, self.row_value(declared, "seats")),
            )
            self.assertEqual(
                int(self.row_value(declared, "chips_in_play")), expected["chips_in_play"],
                "%r's chips in play are unchanged (shapes.md §2, §5): %r"
                % (shape, self.row_value(declared, "chips_in_play")),
            )
            self.assertEqual(
                S.history_capacity_of(declared), expected["history"],
                "%r keeps its own capacity: 24 on the fixed-limit row and 66 on the two-seat "
                "uncapped one (shapes.md §8, ASM-42): %r"
                % (shape, S.history_capacity_of(declared)),
            )
            for representation, key in ((S.FLAT, "dense"), (S.TOKENS, "tokens")):
                self.assertEqual(
                    self.declared_width(shape, representation), expected[key],
                    "%r's %r width is unchanged by the third row (shapes.md §5, §8): %d"
                    % (shape, representation, self.declared_width(shape, representation)),
                )
            self.assertEqual(
                int(self.declared_vocabulary(shape)), expected["vocabulary"],
                "%r's token vocabulary is unchanged by the third row, whose six seat ids sit "
                "above these and rename none (seats.md §3, shapes.md §5): %r"
                % (shape, self.declared_vocabulary(shape)),
            )
            self.assertEqual(
                int(self.row_value(declared, "head_width")), expected["head_width"],
                "%r's head width is its own vocabulary's size (shapes.md §2, sizing.md §6): %r"
                % (shape, self.row_value(declared, "head_width")),
            )

    # -- the capacity (shapes.md §8, D-33) --------------------------------
    def test_fam21_2_the_capacity_is_the_blocks_own_refusal_threshold(self):
        """FAM-21.2 98 entries encode on six seats, 99 are refused; 66 encode, 98 do not fit.

        `shapes.md` §8 derives each row's capacity from that row's own betting and
        `flat-numeric.md` §5 makes it the block's refusal threshold as well as its length: a
        history of exactly the capacity encodes whole, one entry more is refused naming the
        field, the capacity and the count, and nothing is truncated
        (`docs/L2/features/capacity.md` §1, §3, ASM-42, D-33).  Both encodings answer to the
        same number on the six-seat row, because the dense block is `3 × capacity` wide and
        the token block one slot per action over it, and the same 66-entry history that is
        whole on the two-seat uncapped row is **66 of the six-seat row's 98** — the widening
        is the seat count's, not a second spelling of the two-seat number.
        """
        capacity = S.history_capacity_of(self.shape_row(S.SHAPE_THIRD))
        self.assertEqual(
            capacity, SIX_SEAT_CAPACITY,
            "the six-seat row's capacity is 98 (shapes.md §8, D-33): %r" % (capacity,),
        )
        two_seat = S.history_capacity_of(self.shape_row(S.SHAPE_SECOND))
        self.assertEqual(
            two_seat, TWO_SEAT_CAPACITY,
            "the two-seat uncapped row's capacity is 66 (shapes.md §8): %r" % (two_seat,),
        )
        for shape, fits_count, over_count in (
            (S.SHAPE_THIRD, SIX_SEAT_CAPACITY, SIX_SEAT_CAPACITY + 1),
            (S.SHAPE_SECOND, TWO_SEAT_CAPACITY, TWO_SEAT_CAPACITY + 1),
        ):
            fits = self.history_readout(shape, fits_count)
            over = self.history_readout(shape, over_count)
            for representation, key in ((S.FLAT, "dense"), (S.TOKENS, "tokens")):
                width = S.SHAPE_LAYOUTS[shape][key]
                encoder = self.encoder(representation, shape)
                encoded = self.ep("features", "encode")(encoder, fits)
                self.assertEqual(
                    len(encoded), width,
                    "a history of exactly %d entries — the whole of %r's capacity — encodes "
                    "in full on %r at its own %d-wide %r block, and is never truncated "
                    "(flat-numeric.md §5, shapes.md §8, ASM-42, D-33): %d values"
                    % (fits_count, shape, representation, width,
                       "dense" if key == "dense" else "token", len(encoded)),
                )
                text = S.refusal_text(
                    lambda: self.ep("features", "encode")(encoder, over)
                )
                self.assertIsNotNone(
                    text,
                    "%r's capacity of %d is the block's refusal threshold: %d entries are "
                    "refused, not truncated (shapes.md §8, ASM-42, D-33)"
                    % (shape, fits_count, over_count),
                )
                self.assertIn(
                    "history", S._family_token(text),
                    "the refusal names the field it refused — the history block "
                    "(flat-numeric.md §5): %r" % (text,),
                )
                for number in (fits_count, over_count):
                    self.assertIn(
                        str(number), text,
                        "the refusal names the capacity %d and the count that crossed it "
                        "(docs/L2/features/capacity.md §1, §3): %r" % (number, text),
                    )
        # A 66-entry history is whole on **both** uncapped rows, and only the six-seat row
        # holds a 98-entry one: the capacity is the shape's own data.
        common = self.history_readout(S.SHAPE_THIRD, TWO_SEAT_CAPACITY)
        self.assertEqual(
            len(self.ep("features", "encode")(
                self.encoder(S.FLAT, S.SHAPE_THIRD), common)),
            SIX_SEAT_DENSE,
            "a 66-entry history — the whole of the two-seat uncapped row's capacity — is well "
            "inside the six-seat row's 98 slots and encodes there at 433 values "
            "(shapes.md §8, seats.md §2): %d values"
            % (len(self.ep("features", "encode")(
                self.encoder(S.FLAT, S.SHAPE_THIRD), common)),),
        )
        too_long = self.history_readout(S.SHAPE_SECOND, SIX_SEAT_CAPACITY)
        self.assertIsNotNone(
            S.refusal_text(
                lambda: self.ep("features", "encode")(
                    self.encoder(S.FLAT, S.SHAPE_SECOND), too_long)
            ),
            "98 entries do **not** fit the two-seat uncapped row's 66 slots: the two rows "
            "are one derivation at two seat counts and not one number (shapes.md §8, D-33)",
        )

    # -- the seating (seats.md §4, e2e-surface.md §3.1) --------------------
    def test_fam21_3_a_six_seat_hand_seats_the_shapes_whole_seating(self):
        """FAM-21.3 `play_hand`'s `seats` plays six policies, one per seat, and refuses the rest.

        `seats.md` §4: a six-seat hand holds six policies and one is the learner's, and
        `engine.play_hand` takes the seating as an **optional** `seats` argument — the
        shape's whole seating, in seat order — with the two positional policies absent when
        it is given.  The shape's seat count is the number the argument must hold: a
        five-policy sequence, a seven-policy one, and a seating handed beside two positional
        policies are each refused by name, because no caller can seat a table the shape does
        not declare (`seats.md` §4, `e2e-surface.md` §2 "Game shape", §3.1, ASM-43).
        """
        seats = self.seats_of(S.SHAPE_THIRD)
        self.assertEqual(
            seats, THIRD_ROW["seats"],
            "the six-seat shape declares six seats (shapes.md §2, seats.md §2): %r" % (seats,),
        )
        seating = self.six_seat_seating(S.SEED_A)
        self.assertEqual(
            len(seating), seats,
            "the seating is the shape's whole table — one policy per seat in seat order "
            "(seats.md §4): %r policies for %d seats" % (len(seating), seats),
        )
        episode = self.play(S.SEED_A, seats=seating, shape=S.SHAPE_THIRD)
        decisions = self.decisions_of(episode)
        self.assertTrue(
            decisions,
            "a six-seat hand played through the seating carries its ordered decisions "
            "(records.md §5): %r" % (episode,),
        )
        seen = set()
        for decision in decisions:
            index = self.seating_of(decision)
            self.assertTrue(
                0 <= index < seats,
                "every decision's `seat` names one of the shape's seats, 0..5 (records.md §5, "
                "seats.md §3): %r" % (decision.get("seat"),),
            )
            seen.add(index)
        self.assertIn(
            0, seen,
            "the learner's own seat — seat 0 of this seating — made its decisions, so the "
            "hand seated the policy the case handed it (seats.md §4, records.md §5): %r"
            % (sorted(seen),),
        )
        self.assertGreater(
            len(seen), 1,
            "a six-seat hand is played by more than one seat's policy, or the seating was "
            "read as a single opponent (seats.md §2, §4): %r" % (sorted(seen),),
        )
        # Every seat's policy is the one the case handed it: the learner at seat 0 and the
        # pool's five distinct members behind it.
        self.assertEqual(
            len(seating), len({id(policy) for policy in seating}),
            "the five opponents are five distinct policies drawn without replacement and the "
            "learner is the sixth (seats.md §4, ASM-43): %r" % (seating,),
        )
        # A seating of the wrong length is refused by name, and so is one beside the pair.
        short = seating[:-1]
        for label, length in (("one short", len(short)),
                              ("one long", len(seating) + 1)):
            sequence = seating[:length] if length <= len(seating) else seating + [seating[0]]
            text = S.refusal_text(
                lambda sequence=sequence: self.play(
                    S.SEED_A, seats=sequence, shape=S.SHAPE_THIRD)
            )
            self.assertIsNotNone(
                text,
                "a seating %s than the shape's seat count is refused by name, not padded or "
                "truncated (seats.md §4, e2e-surface.md §3.1): %d policies for %d seats"
                % (label, length, seats),
            )
            self.assertIn(
                str(seats), text,
                "the refusal names the shape's seat count, so a reader sees what the seating "
                "must hold (seats.md §4): %r" % (text,),
            )
        text = S.refusal_text(
            lambda: self.ep("engine", "play_hand")(
                S.SEED_A, self.baseline("always-call", S.SEED_D, S.SHAPE_THIRD),
                self.baseline("always-call", S.SEED_D, S.SHAPE_THIRD),
                S.SHAPE_THIRD, seating,
            )
        )
        self.assertIsNotNone(
            text,
            "a seating handed **beside** the two positional policies is refused by name: the "
            "two forms are exclusive and neither is defaulted into the other (seats.md §4, "
            "e2e-surface.md §3.1)",
        )
        self.assertIn(
            "seat", S._family_token(text),
            "the refusal names the argument or the policies that conflict (seats.md §4): %r"
            % (text,),
        )

    # -- the payoffs and the readout (records.md §5, seats.md §3) ----------
    def test_fam21_4_a_six_seat_hand_pays_one_delta_per_seat_summing_to_zero(self):
        """FAM-21.4 six payoffs, one per seat, summing to zero; six stacks and a seat fact.

        `records.md` §5 and `seats.md` §3 keep the readout's eleven facts and change only
        what two of them are worth: `payoffs` is one net delta per seat — six on this shape,
        two elsewhere — and `stacks` is one entry per seat in seat order, so `pot +
        sum(stacks)` is the shape's 600 chips in play at every decision (ASM-28).  `seat` is
        `(index, on_button)` with the index in `0..seats − 1` and the shape's declared
        `button_seat` the button, which is 0 on every row, so a seat index means one thing
        and rotating the learner across seats rotates it across positions (`seats.md` §3,
        `league.md` §3, D-33).
        """
        seats = self.seats_of(S.SHAPE_THIRD)
        chips = S.numbers(S.declared_field(
            self.shape_row(S.SHAPE_THIRD),
            "a declared shape row (shapes.md §2)",
            "chips_in_play",
        ))[0]
        self.assertEqual(
            int(chips), THIRD_ROW["chips_in_play"],
            "the six-seat row's chips in play are 600 (shapes.md §2, seats.md §2): %r" % (chips,),
        )
        # The completed hand, played through the engine's own entry points.
        engine = self.mod("engine")
        hand = engine.new_hand(S.SEED_A, S.SHAPE_THIRD)
        steps = 0
        while not engine.is_terminal(hand) and steps < 400:
            readout = engine.readout(hand)
            legal = engine.legal_actions(hand)
            seat = S.seat_of(readout)
            self.assertTrue(
                0 <= seat < seats,
                "the readout's `seat` fact names one of the shape's seats at every decision "
                "(e2e-surface.md §2, seats.md §3): %r" % (readout.get("seat"),),
            )
            self.assertEqual(
                len(list(S.numbers(readout["stacks"]))), seats,
                "`stacks` is one entry per seat in seat order — six here, two on the two-seat "
                "rows (seats.md §3, ASM-28): %r" % (readout.get("stacks"),),
            )
            self.assertEqual(
                int(readout["pot"]) + sum(S.numbers(readout["stacks"])),
                int(chips),
                "`pot + sum(stacks)` is the shape's 600 chips in play at every decision "
                "(shapes.md §2, seats.md §3, ASM-28): pot %r, stacks %r"
                % (readout["pot"], readout["stacks"]),
            )
            descriptor = self.baseline("always-call", S.SEED_D, S.SHAPE_THIRD)(
                readout, legal)
            hand = engine.apply_action(hand, descriptor)
            steps += 1
        self.assertTrue(
            engine.is_terminal(hand),
            "the six-seat hand ends within %d decisions (records.md §5): %r" % (steps, hand),
        )
        payoffs = S.numbers(engine.payoffs(hand))
        self.assertEqual(
            len(payoffs), seats,
            "engine.payoffs answers one net delta per seat — six on the six-seat shape "
            "(e2e-surface.md §3.1, seats.md §3): %r" % (payoffs,),
        )
        self.assertEqual(
            sum(payoffs), 0,
            "the six-seat hand is zero-sum: the deltas cancel across the whole table and not "
            "only across two seats (records.md §5, ASM-12): %r" % (payoffs,),
        )
        # ... and the episode record reports the same per-seat outcome.
        episode = self.six_seat_episode(S.SEED_A)
        recorded = S.numbers(S.find_values(episode, "payoff"))
        self.assertEqual(
            len(recorded), seats,
            "the episode record's `payoffs` carries one entry per seat, six on this shape "
            "(records.md §5, seats.md §3): %r" % (recorded,),
        )
        self.assertEqual(
            sum(recorded), 0,
            "the recorded payoffs sum to zero (records.md §5, ASM-12): %r" % (recorded,),
        )
        # The button is seat 0 on every shape, and only that seat is on the button.
        walked = 0
        for seed in S.SHAPE_SEEDS[:2]:
            for _hand, facts, _legal, _action, _index in self.seated_walk(
                seed, {"default": self.baseline("always-call", S.SEED_D, S.SHAPE_THIRD)},
                shape=S.SHAPE_THIRD,
            ):
                walked += 1
                seat_fact = S.readout_fact(facts, "seat")
                self.assertTrue(
                    isinstance(seat_fact, (list, tuple)) and len(seat_fact) >= 2,
                    "the `seat` fact is the acting seat's index **and** whether it is the "
                    "button (e2e-surface.md §2, seats.md §3): %r" % (seat_fact,),
                )
                index, on_button = int(seat_fact[0]), bool(seat_fact[1])
                self.assertEqual(
                    on_button, index == 0,
                    "seat 0 is the button on every shape's declaration, so only it carries "
                    "the flag (seats.md §3, league.md §3): seat fact %r" % (seat_fact,),
                )
        self.assertGreater(walked, 1, "the case must walk real six-seat decisions")

    # -- the draw (seats.md §4, ASM-43) ------------------------------------
    def test_fam21_5_opponent_draws_five_distinct_members_without_replacement(self):
        """FAM-21.5 five distinct members, one seed twice agrees, and four members are refused.

        `seats.md` §4 and `e2e-surface.md` §3.4 make `evaluation.opponent(pool, seed, count)`
        return that many **distinct** members, drawn without replacement from the frozen
        pool in the draw's order, so a six-seat hand never seats one member twice and the
        draw is reproducible from the seed and the membership; a pool holding fewer is
        refused naming both counts (`records.md` §8, ASM-43, D-33).

        The pool here is five members — the three pinned baselines and two of the battery's
        invented versions — so a draw of five is the **whole** membership: the five drawn
        policies are shown to be five different members by their decisions on the same
        six-seat hands, which is the observable a repeated member would break, and a second
        draw at another seed is the same five behaviours in another order.
        """
        pool = self.six_seat_pool()
        membership = self.members(pool)
        identifiers = [str(member.get("id")) for member in membership["members"]]
        self.assertGreaterEqual(
            len(identifiers), SIX_SEAT_OPPONENTS,
            "the pool a six-seat hand draws from holds at least five members — the three "
            "pinned baselines and the versions beside them (records.md §8, seats.md §4): %r"
            % (identifiers,),
        )
        self.assertEqual(
            str(S.declared_field(membership, "a pool record (records.md §8)", "game")),
            S.SHAPE_THIRD,
            "the pool the draw reads is the six-seat shape's (records.md §8, shapes.md §3)",
        )

        def behaviours(seed):
            drawn = self.ep("evaluation", "opponent")(pool, seed, SIX_SEAT_OPPONENTS)
            self.assertEqual(
                len(list(drawn)), SIX_SEAT_OPPONENTS,
                "a draw of five returns five policies, in the draw's order (seats.md §4): %r"
                % (drawn,),
            )
            vectors = []
            for policy in drawn:
                self.assertTrue(
                    callable(policy),
                    "a drawn member is a policy of e2e-surface.md §2: %r" % (policy,),
                )
                vector = []
                for deal in S.SHAPE_SEEDS[:3]:
                    episode = self.play(deal, seats=[policy] * self.seats_of(S.SHAPE_THIRD),
                                        shape=S.SHAPE_THIRD)
                    vector.append(tuple(
                        self.chosen_index(decision["legal"], decision["action"])
                        for decision in self.decisions_of(episode)
                    ))
                self.assertTrue(
                    any(vector),
                    "a drawn member answers the six-seat decisions it is handed (seats.md "
                    "§4): %r" % (policy,),
                )
                for decisions in vector:
                    for index in decisions:
                        self.assertIn(
                            index, set(self.vocabulary(S.SHAPE_THIRD)),
                            "a drawn member decides in the shape's six indices (sizing.md §3, "
                            "shapes.md §3): %r" % (index,),
                        )
                vectors.append(tuple(vector))
            return vectors, drawn

        first, _drawn = behaviours(S.SEED_A)
        self.assertEqual(
            len(set(first)), SIX_SEAT_OPPONENTS,
            "the five drawn policies are **five distinct members**: their decisions on the "
            "same hands differ, so no member was drawn twice (seats.md §4, ASM-43, D-33): %r"
            % ([len(vector) for vector in first],),
        )
        again, _redrawn = behaviours(S.SEED_A)
        self.assertEqual(
            first, again,
            "one pool and one seed draw one seating: two calls at one seed agree decision for "
            "decision (seats.md §4, ASM-2, ASM-43)",
        )
        other, _third = behaviours(S.SEED_B)
        self.assertEqual(
            len(set(other)), SIX_SEAT_OPPONENTS,
            "a draw at another seed is again **five distinct members**: the draw is without "
            "replacement at every seed and never seats one member twice (seats.md §4, "
            "ASM-43, D-33): %r" % ([len(vector) for vector in other],),
        )
        # ... and the uncounted draw is unchanged: one pool, one seed, one opponent.
        single = self.ep("evaluation", "opponent")(pool, S.SEED_C)
        self.assertTrue(
            callable(single),
            "opponent(pool, seed) with no count is still one policy drawn from the pool "
            "(e2e-surface.md §3.4, seats.md §4): %r" % (single,),
        )
        # A pool holding fewer than the draw is refused, naming both counts.
        thin = self.pool(tags=("kestrel",), game=S.SHAPE_THIRD)
        thin_members = self.members(thin)["members"]
        self.assertEqual(
            len(thin_members), SIX_SEAT_OPPONENTS - 1,
            "the pool this arm declares holds four members — three baselines and one version "
            "(records.md §8): %r" % ([member.get("id") for member in thin_members],),
        )
        text = S.refusal_text(
            lambda: self.ep("evaluation", "opponent")(thin, S.SEED_A, SIX_SEAT_OPPONENTS)
        )
        self.assertIsNotNone(
            text,
            "a pool holding fewer members than the draw asks for is refused, because a "
            "substitute seat would be an opponent the membership does not carry (seats.md "
            "§4, records.md §8, ASM-43)",
        )
        for number in (SIX_SEAT_OPPONENTS, len(thin_members)):
            self.assertIn(
                str(number), text,
                "the refusal names both counts — the draw and the membership (seats.md §4, "
                "ASM-43): %r" % (text,),
            )

    # -- the folder's stack (seats.md §6, ASM-31, ASM-34) ------------------
    def test_fam21_6_build_baselines_shape_is_the_stack_fold_large_bet_reads(self):
        """FAM-21.6 half the stack is 50 on the six-seat row and 10 on the default shape.

        D-21's rule is one inequality — fold when `to_call` exceeds half the declared
        starting stack — and `seats.md` §6 makes `agents.build_baseline`'s optional shape
        the stack it reads, so "half the stack" is the **shape's own**: 50 on a 100-chip
        row, 10 on ASM-6's 20-chip one, and a folder built on no shape reads the default's
        (`e2e-surface.md` §3.3, `folders.md` §2, ASM-31, ASM-34, D-33).

        The case drives the same six-seat hands twice: a seat that raises a quarter of the
        span puts the button's `to_call` at 28, 19, 14 and 11 — above 10 and below 50 — so
        the folder built on the six-seat shape checks or calls and the folder built with no
        shape folds; a seat that raises half puts it at 52, above 50, so the shaped folder
        folds too.  Nothing about the rule moves: the same inequality is recomputed from each
        readout's own `to_call` and the shape's declared stack.
        """
        stack = S.starting_stack(self.game_config(S.SHAPE_THIRD))
        self.assertEqual(
            stack, THIRD_ROW["starting_stack"],
            "the six-seat row's starting stack is 100 (shapes.md §2, seats.md §2): %r" % (stack,),
        )
        threshold = stack // 2
        self.assertEqual(
            threshold, 50,
            "half the six-seat row's stack is 50, so its folder's threshold is 50 and not the "
            "default shape's 10 (seats.md §6, ASM-31, ASM-34): %r" % (threshold,),
        )

        def raiser(band, seat):
            """A policy of §2 that raises one band where it is legal, and calls otherwise."""

            def policy(readout, legal):
                if S.seat_of(readout) == seat and band in legal:
                    return band
                if "check-call" in legal:
                    return "check-call"
                return legal[0]

            return policy

        def button_decisions(folder_shape, band):
            """Every decision the folder makes at seat 0 of a six-seat hand."""
            return [
                (readout, legal, index)
                for seed in S.SHAPE_SEEDS[:3]
                for readout, legal, _action, index in self.folder_walk(
                    "fold-large-bet", raiser(band, 4), seed, 0, S.SHAPE_THIRD,
                    folder_shape=folder_shape,
                )
            ]

        shaped = button_decisions(S.SHAPE_THIRD, "raise-quarter")
        self.assertTrue(
            shaped,
            "the six-seat hands must give the folder decisions, or the inequality is asserted "
            "on nothing (folders.md §2, seats.md §6)",
        )
        default_threshold = S.starting_stack(self.game_config()) // 2
        self.assertLess(
            default_threshold, threshold,
            "one row's half-stack is not another's: the default shape's threshold is 10 and "
            "the six-seat row's is 50 (seats.md §6, ASM-31, ASM-34): %r against %r"
            % (default_threshold, threshold),
        )
        over_default = 0
        for readout, legal, index in shaped:
            to_call = int(S.readout_fact(readout, "to_call"))
            self.assertLessEqual(
                to_call, threshold,
                "this arm's calls are all at or below half the six-seat stack, so the shaped "
                "folder must not fold any of them (folders.md §2, seats.md §6, ASM-34): "
                "to_call %r, threshold %r" % (to_call, threshold),
            )
            if to_call > default_threshold:
                over_default += 1
            self.assertNotEqual(
                index, 0,
                "the shaped folder does not fold a call at or below half its **own** stack "
                "(%r ≤ %r), which the **default** stack's half would have folded (%r > %r) "
                "(seats.md §6, ASM-31, ASM-34): to_call %r, choice %r"
                % (to_call, threshold, to_call, default_threshold, to_call, index),
            )
        self.assertGreater(
            over_default, 0,
            "these calls must cross the **default** shape's threshold of 10 while staying "
            "below 50, or the two builds would agree by accident and the shape would be "
            "unobserved (seats.md §6, ASM-34): %d decisions, calls %r"
            % (len(shaped),
               [S.readout_fact(readout, "to_call") for readout, _l, _i in shaped]),
        )
        # The same calls, judged by a folder built with no shape: it reads the default
        # shape's 20 chips, so it folds every call above 10 — the shape is what differed.
        plain = button_decisions(None, "raise-quarter")
        self.assertTrue(
            plain,
            "the same hands must reach the shapeless folder too (folders.md §2)",
        )
        for readout, legal, index in plain:
            to_call = int(S.readout_fact(readout, "to_call"))
            if to_call > default_threshold:
                self.assertEqual(
                    index, 0,
                    "'fold-large-bet' built with no shape reads the **default** shape's stack "
                    "— more than %r of %r — so it folds the same call the shaped build takes "
                    "(e2e-surface.md §3.3, seats.md §6, ASM-31): to_call %r, choice %r"
                    % (default_threshold, 2 * default_threshold, to_call, index),
                )
        self.assertGreater(
            len([1 for readout, _l, _i in plain
                 if int(S.readout_fact(readout, "to_call")) > default_threshold]),
            0,
            "the default shape's threshold of 10 must be **crossed** by these hands, or the "
            "two builds would agree by accident and the shape would be unobserved "
            "(seats.md §6, ASM-34): %d decisions" % (len(plain),),
        )
        # Above 50 even the shaped folder folds: the half-raise arm.
        higher = button_decisions(S.SHAPE_THIRD, "raise-half")
        self.assertTrue(
            higher,
            "the half-raise arm must give the folder a decision (folders.md §2, ASM-31)",
        )
        folds = [
            (readout, index) for readout, _legal, index in higher
            if int(S.readout_fact(readout, "to_call")) > threshold
        ]
        self.assertTrue(
            folds,
            "the half-raise arm must cross the shaped folder's own threshold of 50, or the "
            "fold arm of the rule is unobserved (seats.md §6, ASM-34): %r"
            % ([S.readout_fact(readout, "to_call") for readout, _legal, _index in higher],),
        )
        for readout, index in folds:
            self.assertEqual(
                index, 0,
                "'fold-large-bet' on the six-seat shape folds a call above 50 (seats.md §6, "
                "ASM-31, ASM-34): to_call %r, choice %r"
                % (S.readout_fact(readout, "to_call"), index),
            )
        # The other hundred-chip row reads the same stack: the threshold is the shape's, and
        # two shapes of one stack are one threshold (shapes.md §2, seats.md §6).
        other_row = button_decisions(S.SHAPE_SECOND, "raise-quarter")
        self.assertEqual(
            [index for _readout, _legal, index in other_row],
            [index for _readout, _legal, index in shaped],
            "a folder built on the two-seat uncapped row — 100 chips a seat too — decides the "
            "same way on the same six-seat hands (shapes.md §2, seats.md §6): %r against %r"
            % ([index for _readout, _legal, index in other_row],
               [index for _readout, _legal, index in shaped]),
        )
        # ... and a name outside the catalogue is refused, never defaulted.
        text = S.refusal_text(
            lambda: self.baseline("fold-large-bet", S.SEED_D, S.UNKNOWN_SHAPE)
        )
        self.assertIsNotNone(
            text,
            "agents.build_baseline's shape refuses a name the catalogue does not carry "
            "(e2e-surface.md §3.3, shapes.md §2, seats.md §6)",
        )
        self.assertIn(
            S._family_token(S.UNKNOWN_SHAPE),
            S._family_token(text),
            "the refusal names the shape it refused (shapes.md §2): %r" % (text,),
        )

    # -- the learner's width and head (shapes.md §8, ASM-44) --------------
    def test_fam21_7_a_six_seat_learner_takes_its_width_from_that_shapes_encoder(self):
        """FAM-21.7 18,510 parameters at W = 36, D = 2: the 433-wide block and the six head.

        `shapes.md` §8 states the six-seat row's `param_count` at one architecture — input,
        trunk, and `A·W + A` — as **18,510** from its 433-wide input block and its six-wide
        head, and makes a kind's declared `observation_size` the **default** shape's 203: a
        learner on this shape therefore takes its input width from that shape's encoder,
        which is what `features.observation_spec` cross-checks, while its head is as wide as
        the shape's vocabulary (`e2e-surface.md` §3.3, `sizing.md` §6, ASM-40, ASM-44, D-33).
        """
        shape = S.SHAPE_THIRD
        kind = self.architecture_kind("naive")
        encoder = self.encoder(S.FLAT, shape)
        width = self.declared_width(shape, S.FLAT)
        self.assertEqual(
            width, SIX_SEAT_DENSE,
            "the six-seat shape's dense observation is 433 wide (shapes.md §8): %d" % (width,),
        )
        self.assertEqual(
            int(self.row_value(self.shape_row(shape), "head_width")),
            THIRD_ROW["head_width"],
            "the six-seat row's head is as wide as its six-descriptor vocabulary "
            "(shapes.md §2, sizing.md §6): %r"
            % (self.row_value(self.shape_row(shape), "head_width"),),
        )
        self.assertEqual(
            len(self.vocabulary(shape)), THIRD_ROW["head_width"],
            "features.action_space declares six descriptors on the six-seat shape, so the head "
            "is six wide (e2e-surface.md §2, sizing.md §6): %r" % (self.vocabulary(shape),),
        )
        learner = self.learner(
            width=S.PARAM_WIDTH, depth=S.PARAM_DEPTH, seed=S.SEED_I, kind=kind, game=shape
        )
        count = int(self.ep("agents", "param_count")(learner))
        self.assertEqual(
            count, SIX_SEAT_PARAMS,
            "the six-seat learner's parameter count at W = %d, D = %d is %d — its 433-wide "
            "input block and its six-wide head (shapes.md §8, ASM-44): %d"
            % (S.PARAM_WIDTH, S.PARAM_DEPTH, SIX_SEAT_PARAMS, count),
        )
        default = self.shape_names()[0]
        plain = int(self.ep("agents", "param_count")(
            self.learner(width=S.PARAM_WIDTH, depth=S.PARAM_DEPTH, seed=S.SEED_I, kind=kind)
        ))
        self.assertEqual(
            plain, DEFAULT_PARAMS,
            "the default shape's count is today's %d, unchanged (shapes.md §5, §8): %d"
            % (DEFAULT_PARAMS, plain),
        )
        delta_size = width - self.declared_width(default, S.FLAT)
        delta_actions = len(self.vocabulary(shape)) - len(S.FIXED_ACTIONS)
        self.assertEqual(
            count - plain,
            delta_size * S.PARAM_WIDTH + delta_actions * S.PARAM_WIDTH + delta_actions,
            "the two counts differ by the two shape terms and nothing else — the input "
            "block's `Δsize·W` and the head's `ΔA·W + ΔA`, %d input slots and %d descriptors "
            "(shapes.md §8, sizing.md §6): %d against %d"
            % (delta_size, delta_actions, plain, count),
        )
        # The head follows the vocabulary: the shaped learner answers a six-seat decision
        # with one of the shape's own indices, and an observation the shape's encoder made.
        readout = self.readout(self.hand(S.SEED_I, shape))
        observation = self.ep("features", "encode")(encoder, readout)
        self.assertEqual(
            len(observation), width,
            "the shaped learner's observation is the shape's own %d values (shapes.md §8, "
            "ASM-44): %d" % (width, len(observation)),
        )
        result = self.act(learner, encoder, readout)
        self.assertIn(
            self.action_index(result),
            self.mask(readout),
            "a learner built in the six-seat head answers that shape's decision with one of "
            "its six legal indices (e2e-surface.md §3.3, sizing.md §6): %r" % (result,),
        )

    def test_fam21_8_an_encoder_less_spec_on_the_six_seat_shape_is_refused_by_name(self):
        """FAM-21.8 a spec naming the six-seat shape and carrying no encoder is refused by name.

        A kind's declared `observation_size` is the **default** shape's 203, so there is no
        width to build a six-seat learner at, and `agents.build_learner` refuses the spec by
        name instead of sizing it from a number that is not that shape's (`shapes.md` §8,
        ASM-44, `e2e-surface.md` §3.3).  The refusal names the shape it was given, the
        missing `encoder` key, the default shape whose width it declined to use and the
        entry point that refused; the same spec beside that shape's encoder builds, and it
        differs in that one key alone.
        """
        shape = S.SHAPE_THIRD
        default = self.shape_names()[0]
        refused = self.learner_spec(
            width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH, seed=S.SEED_I, game=shape, encoder=None
        )
        self.assertNotIn(
            "encoder", refused,
            "this spec is deliberately encoder-less, which is the only thing that makes the "
            "refusal observable (shapes.md §8, ASM-44): %r" % (sorted(refused),),
        )
        self.assertEqual(
            str(refused["game"]), shape,
            "the spec names the six-seat shape (shapes.md §2, seats.md §2): %r"
            % (refused["game"],),
        )
        text = S.refusal_text(lambda: self.ep("agents", "build_learner")(refused))
        self.assertIsNotNone(
            text,
            "an encoder-less spec naming the six-seat shape is refused by name, never sized "
            "at the default shape's 203 (shapes.md §8, ASM-44): %r" % (sorted(refused),),
        )
        for needle, why in (
            (S._family_token("build_learner"), "the entry point that refused (docs/L3/agents/errors.md §3)"),
            (S._family_token(shape), "the shape the spec named (shapes.md §8, ASM-44)"),
            ("encoder", "the key that is missing (shapes.md §8, ASM-44)"),
            (S._family_token(default), "the default shape whose width it declined to use (shapes.md §8)"),
        ):
            self.assertIn(
                needle, S._family_token(text),
                "the refusal names %s: %r" % (why, text),
            )
        accepted = self.learner_spec(
            width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH, seed=S.SEED_I, game=shape
        )
        self.assertIn(
            "encoder", accepted,
            "a six-seat learner spec carries the shape's encoder, which is the declared way "
            "to size one (shapes.md §8, e2e-surface.md §3.3): %r" % (sorted(accepted),),
        )
        beside = dict(accepted)
        del beside["encoder"]
        self.assertEqual(
            S.canon(beside), S.canon(refused),
            "the accepted spec and the refused one differ in the `encoder` key alone, so the "
            "refusal is that key's and nothing else's (shapes.md §8, ASM-44)",
        )
        learner = self.ep("agents", "build_learner")(accepted)
        self.assertGreater(
            int(self.ep("agents", "param_count")(learner)), 0,
            "the spec carrying the shape's encoder builds a six-seat learner "
            "(e2e-surface.md §3.3)",
        )

    # -- the pairwise instrument's refusals (seats.md §5) -----------------
    def test_fam21_9_the_pairwise_instrument_refuses_a_six_seat_shape(self):
        """FAM-21.9 match, matrix, rating and report refuse it, naming shape and seat count.

        `seats.md` §5 and `league.md` §4: a cell is a pair and a rating is fitted over pairs,
        so a placement — which is what a six-way hand is — is not measured by the pairwise
        instrument, and `evaluation.match`, `matrix`, `rating` and `report` each refuse a
        shape whose seat count is not two, naming **the shape and its seat count** (D-22,
        D-33).  What the test needs — hands, readout, encoder, learner, pool, greedy pass —
        works at six seats, which the cases above show; what cannot be written is a matrix,
        and therefore a report (`seats.md` §5, `records.md` §12–§13).

        The same four entry points still measure a two-seat row: the refusal is the seat
        count's and not a blanket one (`shapes.md` §5, seats.md §5).
        """
        shape = S.SHAPE_THIRD
        left = self.variant_policy(seed=S.SEED_H, game=shape)
        right = self.variant_policy(seed=S.SEED_I, game=shape)
        self.refusal_for_shape(
            lambda: self.match(left=left, right=right, hands=S.HANDS_TINY,
                               seed=S.TABLE_SEED_A),
            "evaluation.match",
        )
        matrix = self.six_seat_table()
        self.refusal_for_shape(
            lambda: self.ep("evaluation", "matrix")(
                self.six_seat_pool(), [left], "live"),
            "evaluation.matrix",
        )
        self.refusal_for_shape(
            lambda: self.ep("evaluation", "rating")(matrix),
            "evaluation.rating",
        )
        rating = self.hand_built_rating(matrix)
        run = self.run_record("R1", seeds=(S.SEED_A,), budget=S.BUDGET_MICRO)
        record = self.evidence_record(
            run,
            matrix=matrix,
            rating=rating,
            seeds=(S.SEED_A,),
            budget=S.BUDGET_MICRO,
            shape=shape,
            pool_row=self.pool_row(shape=shape),
        )
        self.refusal_for_shape(
            lambda: self.report_of("R1", record, matrix, rating),
            "evaluation.report",
        )
        # The instrument still measures the rows it is for: a cheap cell of two declared
        # baselines on no shape named, and a table over a two-seat pool.
        cell = self.match(hands=S.HANDS_TINY, seed=S.TABLE_SEED_B)
        self.assertEqual(
            int(R.cell_hands(cell)), S.HANDS_TINY,
            "a cell on no shape named is still a cell of the hands it was given — the refusal "
            "is the seat count's and not a blanket one (e2e-surface.md §3.4, seats.md §5): %r"
            % (cell,),
        )
        two_seat = S.shared_league(self)["matrix"]
        self.assertEqual(
            len(R.matrix_cells(two_seat)), 6,
            "a two-seat table of K = 4 — the three baselines and one variant — is still its "
            "six cells (league.md §4, records.md §10, seats.md §5): %r"
            % (len(R.matrix_cells(two_seat)),),
        )

    # -- the run (records.md §12, §15; seats.md §4, §6) -------------------
    def test_fam21_10_a_six_seat_run_records_the_shape_and_its_greedy_block(self):
        """FAM-21.10 a six-seat run carries its shape, its five-member pool and its pass.

        `seats.md` §4–§6: a run on this shape still writes its curves, its pool, its
        checkpoints and its `greedy` block — what it cannot write is a matrix — and the
        learner sits at `hand index mod seats` against `seats − 1` distinct opponents drawn
        from the frozen pool, so the run record's pool block names a membership holding at
        least five members.  `records.md` §12 and §15 make `game` and `greedy` required of a
        record this build writes, so a six-seat run says which game its curves are about and
        retains one exploration-off pass, bounded at 1,000 × the shape's capacity — 98,000
        decisions here and never truncated (`shapes.md` §8, ASM-38, D-33).
        """
        shape = S.SHAPE_THIRD
        samples = S.BUDGET_MICRO
        configuration = self.seated_rung(shape=shape, seeds=(S.SEED_A,), samples=samples)
        record = self.ep("training", "run")(configuration, [S.SEED_A], samples, "cpu")
        self.assertEqual(
            str(S.declared_field(record, "a run record (records.md §12)", "game")),
            shape,
            "a six-seat run record names the shape it played (records.md §12, shapes.md §3, "
            "seats.md §6): %r" % (record.get("game"),),
        )
        pool_block = S.declared_field(record, "a run record (records.md §12)", "pool")
        self.assertEqual(
            str(S.declared_field(pool_block, "a run record's pool block (records.md §12)",
                                 "game")),
            shape,
            "the record's pool block names the same shape as the record (records.md §8, §12, "
            "shapes.md §3): %r" % (pool_block,),
        )
        members = S.declared_field(pool_block, "a run record's pool block (records.md §12)",
                                   "members")
        member_ids = set()
        for member in members if isinstance(members, (list, tuple)) else list(members or ()):
            if S.is_mapping(member):
                identifier = member.get("id")
                if identifier is not None:
                    member_ids.add(str(identifier))
        self.assertGreaterEqual(
            len(member_ids), SIX_SEAT_OPPONENTS,
            "the membership the run trained against holds at least five members, because a "
            "six-seat hand seats five distinct opponents and the pool is the draw's source "
            "(seats.md §4, records.md §8, ASM-43): %r" % (sorted(member_ids),),
        )
        self.assertEqual(
            str(S.declared_field(record, "a run record (records.md §12)", "budget")).replace(
                ".0", ""),
            str(samples),
            "the record states the budget it actually ran (records.md §12, sizing.md §4): %r"
            % (record.get("budget"),),
        )
        passes = S.run_greedy(record)
        self.assertTrue(
            passes,
            "a run record carries `greedy` — the one decision stream a run retains — on every "
            "shape, six seats included (records.md §12, §15, sizing.md §4, seats.md §5): %r"
            % (sorted(str(key) for key in record) if S.is_mapping(record) else record,),
        )
        decisions = 0
        for path, block in passes:
            self.assertEqual(
                str(S.declared_field(block, "a greedy pass (records.md §15)", "mode")), "off",
                "the pass a six-seat run retains is the exploration-off one (records.md §15, "
                "sizing.md §4): %r" % (block,),
            )
            hands = int(S.declared_field(block, "a greedy pass (records.md §15)", "hands"))
            self.assertEqual(
                hands, samples,
                "the pass plays the run's own sample, so a %d-hand run yields a %d-hand pass "
                "(records.md §15, sizing.md §4, seats.md §5): %r"
                % (samples, samples, block),
            )
            self.assertLessEqual(
                hands, PASS_HANDS_BOUND,
                "one pass plays at most %d hands (sizing.md §4): %r"
                % (PASS_HANDS_BOUND, hands),
            )
            net_chips = S.declared_field(block, "a greedy pass (records.md §15)", "net_chips")
            self.assertEqual(
                len(list(net_chips)), hands,
                "the pass carries one net chip delta per hand for the learner's seat, so its "
                "price can be recomputed and not only quoted (records.md §15, ASM-23): %d "
                "deltas for %d hands" % (len(list(net_chips)), hands),
            )
            retained = list(S.declared_field(
                block, "a greedy pass (records.md §15)", "decisions"))
            self.assertGreaterEqual(
                len(retained), 1,
                "the pass retains the learner's own decisions — a six-seat hand's transition "
                "batch is a subset of its decisions, and the pass at least one of them "
                "(records.md §5, §15, seats.md §4): %r" % (block,),
            )
            self.assertLessEqual(
                len(retained), SIX_SEAT_DECISIONS_BOUND,
                "one pass on the six-seat shape records at most 1,000 × its capacity of 98 = "
                "%d decisions and is refused beyond, never truncated (records.md §15, "
                "shapes.md §8, ASM-38, D-33): %d"
                % (SIX_SEAT_DECISIONS_BOUND, len(retained)),
            )
            vocabulary = set(self.vocabulary(shape))
            for decision in retained:
                for key in ("index", "descriptor", "amount", "minimum", "maximum",
                            "legal", "tie"):
                    self.assertIn(
                        key, decision,
                        "records.md §15 makes %r a required key of a retained decision on any "
                        "shape: %r" % (key, decision),
                    )
                self.assertEqual(
                    str(decision["descriptor"]),
                    self.decode_action(int(decision["index"]), shape),
                    "a retained decision carries the descriptor its index decodes to in the "
                    "run's six-seat vocabulary (records.md §15, sizing.md §3): %r"
                    % (decision,),
                )
                self.assertIn(
                    int(decision["index"]), vocabulary,
                    "the pass is played on the six-seat shape, so its indices are that "
                    "shape's six (records.md §15, shapes.md §3): %r" % (decision,),
                )
            decisions += len(retained)
        self.assertGreater(
            decisions, 0,
            "the six-seat pass retains the learner's decisions on the shape's hands "
            "(records.md §15, seats.md §4): %r" % ([path for path, _block in passes],),
        )

    # -- and the default path is unchanged (shapes.md §5, D-29, D-33) -----
    def test_fam21_11_with_no_shape_named_the_fixed_limit_path_is_unchanged(self):
        """FAM-21.11 naming no shape reproduces today's game, indices, widths and tables.

        `shapes.md` §5 and `seats.md` §6 are the constraint the third row is written under:
        every widening's absence reproduces today's value, so the fixed-limit assertions of
        FAM-2, FAM-5, FAM-7, FAM-14, FAM-16, FAM-19 and FAM-20 stand exactly where they
        stood — the default row's two seats and 40 chips, its three indices, its 203/40/96
        layout and its 10,119 parameters at `W = 36`, `D = 2`, a two-seat hand's zero-sum
        payoffs, a cell between two declared baselines, and a first-rung run whose record
        names the default shape (`shapes.md` §2, §5, D-29, D-33).
        """
        default = self.shape_names()[0]
        config = self.game_config()
        self.assertEqual(
            int(self.seats_of()),
            TWO_SEAT_ROWS[default]["seats"],
            "game_config() with no argument is the default shape's two seats (shapes.md §2, "
            "§5): %r" % (config,),
        )
        plain = self.readout(self.hand(S.SEED_A))
        self.assertEqual(
            plain["pot"] + sum(S.numbers(plain["stacks"])),
            TWO_SEAT_ROWS[default]["chips_in_play"],
            "with no shape named the default game still plays 40 chips — `pot + sum(stacks)` "
            "at every decision (shapes.md §2, §5, ASM-28): pot %r, stacks %r"
            % (plain["pot"], plain["stacks"]),
        )
        self.assertEqual(
            S.action_vocabulary(self.action_space()), {0, 1, 2},
            "features.action_space() with no argument is today's three indices "
            "(e2e-surface.md §2, shapes.md §5): %r" % (self.action_space(),),
        )
        for representation, expected in ((S.FLAT, TWO_SEAT_ROWS[default]["dense"]),
                                         (S.TOKENS, TWO_SEAT_ROWS[default]["tokens"])):
            self.assertEqual(
                self.declared_width(default, representation), expected,
                "the default shape's %r observation is unchanged — 203 dense values, 40 "
                "tokens (shapes.md §5, §8): %d"
                % (representation, self.declared_width(default, representation)),
            )
        self.assertEqual(
            int(self.ep("agents", "param_count")(
                self.learner(width=S.PARAM_WIDTH, depth=S.PARAM_DEPTH, seed=S.SEED_I))),
            DEFAULT_PARAMS,
            "with no shape named the learner is the default shape's and its count is today's "
            "%d (sizing.md §6, shapes.md §5): %r" % (DEFAULT_PARAMS, DEFAULT_PARAMS),
        )
        hand = self.hand(S.SEED_A)
        readout = self.readout(hand)
        self.assertEqual(
            len(list(S.numbers(readout["stacks"]))), 2,
            "a heads-up readout carries two stacks, as it always did (e2e-surface.md §2, "
            "seats.md §3): %r" % (readout.get("stacks"),),
        )
        self.assertEqual(
            readout["pot"] + sum(S.numbers(readout["stacks"])),
            TWO_SEAT_ROWS[default]["chips_in_play"],
            "the default shape's chips in play are 40 at every decision (shapes.md §2, §5)",
        )
        episode = self.play(S.SEED_C)
        self.assertEqual(
            sum(S.numbers(S.find_values(episode, "payoff"))), 0,
            "a two-seat episode is zero-sum, as it always was (records.md §5, ASM-12)",
        )
        drawn = self.opponent(self.baselines_pool(), S.SEED_G)
        self.assertTrue(
            callable(drawn),
            "a default-shape pool still draws one opponent through the unchanged call "
            "(e2e-surface.md §3.4, league.md §3): %r" % (drawn,),
        )
        cell = self.match(hands=S.HANDS_TINY, seed=S.TABLE_SEED_A)
        self.assertEqual(
            int(R.cell_hands(cell)), S.HANDS_TINY,
            "the pairwise instrument still plays a two-seat cell of the hands it was given "
            "(e2e-surface.md §3.4, seats.md §5): %r" % (cell,),
        )
        run = self.run_record("R1", seeds=(S.SEED_A,), budget=S.BUDGET_MICRO)
        self.assertEqual(
            str(S.declared_field(run, "a run record (records.md §12)", "game")), default,
            "a run whose configuration names no shape records the default shape (records.md "
            "§12, shapes.md §3): %r" % (run.get("game"),),
        )
        self.assertTrue(
            S.run_greedy(run),
            "a default-shape run still carries its greedy block (records.md §12, §15): %r"
            % (sorted(str(key) for key in run) if S.is_mapping(run) else run,),
        )

    # -- the readout's equity at six seats (seats.md §2, D-33) ------------
    def test_fam21_12_equity_is_six_way_on_a_shape_with_more_than_two_seats(self):
        """FAM-21.12 the acting seat's equity is against the **other seats'** random hands.

        `e2e-surface.md` §3.1 and `seats.md` §2 make `engine.equity` N-way on a shape with
        more than two seats: the acting seat against the other seats' uniformly random
        hands, so a six-seat call is six-way and its estimate is not the two-seat one at the
        same seed, because it is one hand against five and the cards the five hold are not
        the cards one holds (`D-33`, ASM-4).  The sample count is the caller's, and one hand
        at one seed and one count is one estimate.
        """
        six = self.seats_of(S.SHAPE_THIRD)
        estimates = {}
        for seed in S.SHAPE_SEEDS[:2]:
            value = self.ep("engine", "equity")(
                self.hand(seed, S.SHAPE_THIRD), seed, S.EQUITY_SAMPLES)
            self.assertGreaterEqual(
                value, 0.0,
                "a six-way win probability cannot be negative (e2e-surface.md §3.1, ASM-4): "
                "%r at seed %r" % (value, seed),
            )
            self.assertLessEqual(
                value, 1.0,
                "a six-way win probability cannot exceed one (e2e-surface.md §3.1, ASM-4): "
                "%r at seed %r" % (value, seed),
            )
            again = self.ep("engine", "equity")(
                self.hand(seed, S.SHAPE_THIRD), seed, S.EQUITY_SAMPLES)
            self.assertEqual(
                value, again,
                "one hand at one seed and one sample count is one estimate, at six seats as "
                "at two (e2e-surface.md §3.1, ASM-4): %r against %r" % (value, again),
            )
            estimates[seed] = float(value)
        for seed, value in estimates.items():
            two_way = float(self.ep("engine", "equity")(
                self.hand(seed), seed, S.EQUITY_SAMPLES))
            self.assertNotEqual(
                value, two_way,
                "the six-way estimate is one hand against the **five** other seats' random "
                "hands, so it is not the two-seat estimate at the same seed (e2e-surface.md "
                "§3.1, seats.md §2, D-33): %r against %r at seed %r"
                % (value, two_way, seed),
            )
        self.assertEqual(
            six, THIRD_ROW["seats"],
            "the shape whose equity is six-way declares six seats (seats.md §2): %r" % (six,),
        )


if __name__ == "__main__":
    unittest.main()
