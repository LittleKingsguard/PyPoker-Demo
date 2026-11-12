"""ENG-22 -- D-43's resolution: the reveal, `amounts`, `counterfactual`, and the invariant.

``docs/L3/engine/episode.md`` §2, §3, §5; ``docs/L3/engine/episode-battery.md`` §2, §4;
``docs/L1/counterfactual.md`` §2, §4, §5; ``docs/L1/records.md`` §5;
``docs/L1/sizing.md`` §2, §3; ``docs/L3/engine/readout.md`` §2, §4; ``docs/L1/battery.md``
§3 FAM-22 (D-43).

One whole hand now resolves itself.  The episode record carries a ``reveal`` — the board
as dealt, whether the hand reached a showdown, whether the shown hands tie, and one entry
per seat in seat order with its two ``hole`` cards, whether it ``shown`` and whether it
``won`` — and every decision carries ``amounts``, the raise-to each of its legal
descriptors resolves to, and ``counterfactual``, each legal descriptor's whole-hand net
chip delta for the acting seat.

Three things this file is careful about, because a fourth spelling of any of them would
be a second contract:

* the arithmetic is compared against the **declaration** and never against the engine's
  own answer: an ``amounts`` entry is checked against ``S.band_amount`` computed from that
  decision's own ``minimum``/``maximum`` (and against ``minimum`` for the fixed row's one
  ``raise``, which resolves to its minimum completion), and ``won``/``split``/``showdown``
  are recomputed from the reveal's own card spellings by the library's own hand order, so
  a class of hand — which cannot see a kicker and so cannot see a tie — fails here
  (``sizing.md`` §2, ``episode.md`` §5).
* the direction of that comparison is the library's: ``StandardHighHand`` is not a low
  hand, so ``a < b`` reads "``a`` is the weaker hand" and "at least as good as ``other``"
  is ``not (best < other)`` (``episode.md`` §5, ``hands.py:96-188``).
* the engine is reached through the ten declared entry points only, through the support
  module's own instances and helpers, and no case asserts anything the documents do not
  pin.
"""

import os
import sys
import unittest

try:  # discovered as part of a tests.engine package
    from . import _engine_support as S
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _engine_support as S  # noqa: E402

#: The reveal's four keys, as ``records.md`` §5 and ``episode.md`` §5 word them.
REVEAL_KEYS = ("board", "showdown", "split", "seats")

#: One seat entry of the reveal: the four facts it carries in seat order (records.md §5).
SEAT_KEYS = ("seat", "hole", "shown", "won")

#: The episode record's four keys: the three it has always carried and D-43's ``reveal``
#: (``episode.md`` §3, ``records.md`` §5).  Asserted as an exact set, never a subset.
RECORD_KEYS = ("seed", "decisions", "payoffs", "reveal")

#: The one seed this file invents beside the support module's own sets (D-15): an
#: all-call two-seat walk at it deals ``Tc Qs Jd 8d Js``, which no hole improves on, so the
#: two shown hands tie for best and the reveal states a split (``counterfactual.md`` §4).
#: Pinned here, never read off the engine: if the deck order moved, ENG-22.3 fails loudly
#: on the split rather than silently measuring another hand.
SPLIT_SEED = 550010

#: ENG-22.10's bounded search: eight consecutive seeds, each played by
#: ``folding_seating``, a six-seat hand in which seat ``FOLDING_SEAT`` calls until the turn
#: and then folds once a bet faces it while seat ``BETTING_SEAT`` raises the river.  The
#: pattern the case needs -- a resolved hand in which the folding seat's cards were the best
#: of the table, so ``won`` is true while ``shown`` is false -- is dealt at three of the
#: eight, ``FOLD_LATER_SEED`` first.  Pinned here, never read off the engine, and exactly as
#: ``SPLIT_SEED`` is: if the deck order moved, ENG-22.10 fails loudly on the pinned seed
#: rather than quietly measuring another hand (``counterfactual.md`` §4).
FOLD_LATER_BASE = 1015
FOLD_LATER_WIDTH = 8
FOLD_LATER_SEED = 1017
FOLDING_SEAT = 3
BETTING_SEAT = 5


# --------------------------------------------------------------------------
# The battery's own policies, invented for this file (episode.md §4)
# --------------------------------------------------------------------------
def fold_facing_a_bet(readout, legal):
    """Fold when there is something to call, otherwise check or call.

    A seat can only fold a decision that faces a bet — ``fold`` is absent from a legal
    tuple the actor can check behind — so this is the policy that reaches a fold in the
    middle of a multiway hand without ending it at the first decision (``actions.md`` §1).
    """
    return "fold" if "fold" in legal else "check-call"


def bet_the_river(readout, legal):
    """Raise the half band on the river when it is legal, otherwise check or call."""
    if readout["street"] == "river" and "raise-half" in legal:
        return "raise-half"
    return "check-call"


def fold_from_the_turn(readout, legal):
    """Call while it may, and fold from the turn on whenever there is something to fold to.

    ``fold`` is legal only at a decision that faces a bet (``actions.md`` §1), so this
    policy is inert on its own and needs a bettor at the table: seated with the file's own
    ``bet_the_river`` it calls the pre-flop, the flop and the turn and then folds on the
    river, which is the one shape ``counterfactual.md`` §4 asks about -- a seat that made
    four **live** decisions and then left the hand on a later street while its cards were
    the best of the table.
    """
    if readout["street"] in ("turn", "river") and "fold" in legal:
        return "fold"
    return "check-call"


def amount_of(descriptor, minimum, maximum):
    """The raise-to ``descriptor`` resolves to at a decision with these bounds.

    The declaration, not a reading of the engine (``sizing.md`` §2, ``episode.md`` §3): the
    two bases carry no amount; the fixed row's one ``raise`` resolves to its minimum
    completion, which is the only legal amount that shape has; and the four bands of a row
    without a cap resolve to their own band's maximum, which ``S.band_amount`` states.  A
    band that was legal holds a legal integer, so the answer is never ``None`` here.
    """
    if descriptor in S.BASES:
        return None
    if descriptor == "raise":
        return minimum
    return S.band_amount(descriptor, minimum, maximum)


def leaves_of(reveal):
    """``(card spellings, other facts)`` of one reveal, counted from the value itself.

    Values and not keys, so what is counted is what the record names: a two-character card
    of the declared alphabet is a card spelling, every other leaf — a board-less reveal's
    empty tuple contributes none, an entry's ``seat`` index and its two flags one each — is
    an other fact (``episode.md`` §5, ``records.md`` §5).
    """
    cards = 0
    other = 0
    pending = [reveal]
    while pending:
        value = pending.pop()
        if S.is_mapping(value):
            pending.extend(value.values())
        elif isinstance(value, (list, tuple)):
            pending.extend(value)
        elif S.card_spelling_ok(value):
            cards += 1
        else:
            other += 1
    return cards, other


def library_hand(spellings):
    """The ``Card`` objects of one sequence of two-character spellings."""
    from pokerkit.utilities import Card

    return [Card(spelling[0], spelling[1]) for spelling in spellings]


def best_hands(reveal):
    """Every seat's best five-card hand off the reveal's own spellings, by seat index.

    A second, differently built witness for the reveal's three verdicts: the library's own
    ``StandardHighHand.from_game_or_none(hole, board)`` — the same search ``readout``'s
    ``hand_class`` is derived from and a different reader from the engine's own — with
    ``None`` while no five-card hand can be formed (``episode.md`` §5, ``readout.md`` §2).
    """
    from pokerkit.hands import StandardHighHand

    board = library_hand(reveal["board"])
    return {
        entry["seat"]: StandardHighHand.from_game_or_none(library_hand(entry["hole"]), board)
        for entry in reveal["seats"]
    }


def declared_verdicts(reveal):
    """``(showdown, split, {seat: won})`` as ``episode.md`` §5 defines them.

    ``showdown`` is two or more seats ``shown`` **and** a five-card board; ``won`` is that
    seat's ``hole`` plus ``board`` being at least as good as every shown seat's, which is
    ``not (best < other)`` because the library's ``<`` reads "weaker"; ``split`` is
    ``showdown`` and two or more shown seats tied for best, a tie being
    ``not (best < other) and not (other < best)`` (``episode.md`` §5,
    ``counterfactual.md`` §4).
    """
    bests = best_hands(reveal)
    shown = [entry["seat"] for entry in reveal["seats"] if entry["shown"]]
    shown_bests = [bests[seat] for seat in shown if bests[seat] is not None]
    showdown = bool(len(shown) >= 2 and len(reveal["board"]) == 5)
    won = {
        seat: bool(best is not None and all(not (best < other) for other in shown_bests))
        for seat, best in bests.items()
    }
    top = None
    for best in shown_bests:
        if top is None or top < best:
            top = best
    tied = 0 if top is None else sum(
        1 for best in shown_bests if not (best < top) and not (top < best)
    )
    return showdown, bool(showdown and top is not None and tied >= 2), won


class ENG22Resolution(S.EngineCase):
    """The reveal, the two per-decision facts, and the invariant they must satisfy."""

    # -- driving (episode.md §1, seats.md §4) --------------------------------
    def played_on_shape(self, shape, seed, policy=None):
        """One episode on ``shape``, seated the way that shape's seat count demands.

        Two seats take the positional pair, six seats take the shape's whole seating
        through the optional ``seats`` argument (``episode.md`` §1, ``seats.md`` §4).
        Every policy used here is stateless, so one object may hold every seat.
        """
        if policy is None:
            policy = S.always_call
        if S.SHAPE_SEATS[shape] == 2:
            return self.shaped_episode(seed, policy, policy, shape)
        return self.seated_episode(seed, self.seating(shape, lambda: policy), shape)

    def seat_entries(self, reveal):
        """One seat entry per seat of the shape, in seat order (records.md §5)."""
        self.assertTrue(S.is_mapping(reveal), "a reveal is a mapping (records.md §5)")
        self.assertEqual(
            set(reveal), set(REVEAL_KEYS),
            "the reveal carries exactly its four keys -- the board, the showdown, the split "
            "and the seat entries -- and no fifth (records.md §5, episode.md §5): got %r"
            % (sorted(reveal),),
        )
        entries = reveal["seats"]
        self.assertIsInstance(entries, (list, tuple),
                              "the reveal's `seats` is an ordered sequence (records.md §5)")
        return list(entries)

    def holes_by_seat(self, reveal):
        """Every seat's two cards, by seat index, off the reveal's own entries."""
        return {entry["seat"]: tuple(entry["hole"]) for entry in self.seat_entries(reveal)}

    # -- the reveal's shape and its bounds (episode.md §5, records.md §5) ----
    def test_eng22_1_the_reveal_is_a_bounded_record_on_every_shape(self):
        """ENG-22.1 the episode record carries the four keys of ``records.md`` §5 and its
        ``reveal`` is one mapping whose key set is exactly ``board``, ``showdown``, ``split``
        and ``seats`` on all three declared shapes; ``board`` is a tuple of 0-5 spellings of
        the declared alphabet, ``showdown`` and ``split`` real booleans, ``seats`` one entry
        per seat **in seat order** each carrying exactly ``seat``, ``hole``, ``shown`` and
        ``won`` with ``seat`` the seat index, ``hole`` two spellings and the two flags real
        booleans; and the hand names at most ``2·seats + 5`` card spellings and one ``seat``,
        one ``shown`` and one ``won`` per seat beside ``showdown`` and ``split``, the counts
        ``S.SHAPE_SEATS[shape]`` derives (episode.md §5, records.md §5,
        episode-battery.md §2)."""
        for shape in S.SHAPE_NAMES:
            seats = S.SHAPE_SEATS[shape]
            seeds = ((S.SHAPE_SEED_A, S.SHAPE_SEED_B) if seats == 2
                     else (S.SIX_SEED_A, S.SIX_SEED_B))
            for seed in seeds:
                with self.subTest(shape=shape, seed=seed):
                    record = self.played_on_shape(shape, seed)
                    self.assertEqual(
                        set(record), set(RECORD_KEYS),
                        "the episode record carries its seed, its decisions, its payoffs and "
                        "D-43's reveal, and nothing else a caller may depend on "
                        "(episode.md §3, records.md §5): got %r" % (sorted(record),),
                    )
                    reveal = record["reveal"]
                    entries = self.seat_entries(reveal)

                    board = reveal["board"]
                    self.assertIsInstance(
                        board, tuple,
                        "the reveal's board is a tuple and may be empty (records.md §5, "
                        "readout.md §2): %r" % (board,),
                    )
                    self.assertIn(
                        len(board), S.BOARD_SIZES,
                        "the board is the board as dealt, so it holds 0, 3, 4 or 5 cards "
                        "(readout.md §2, records.md §5): %r" % (board,),
                    )
                    for card in board:
                        self.assertTrue(
                            S.card_spelling_ok(card),
                            "every board spelling is two characters, one rank of %r and one "
                            "suit of %r (readout.md §2): %r" % (S.RANKS, S.SUITS, card),
                        )
                    for key in ("showdown", "split"):
                        self.assertIs(
                            type(reveal[key]), bool,
                            "the reveal's %r is a real boolean -- not an int, not None "
                            "(records.md §5, episode.md §5): %r" % (key, reveal[key]),
                        )

                    self.assertEqual(
                        len(entries), seats,
                        "the reveal holds one entry per seat of the hand's own shape -- %d "
                        "on %r -- in seat order (records.md §5, seats.md §3): %r"
                        % (seats, shape, entries),
                    )
                    for position, entry in enumerate(entries):
                        with self.subTest(shape=shape, seed=seed, entry=position):
                            self.assertTrue(
                                S.is_mapping(entry),
                                "one seat entry is a mapping of four facts (records.md §5): %r"
                                % (entry,),
                            )
                            self.assertEqual(
                                set(entry), set(SEAT_KEYS),
                                "one seat entry carries exactly `seat`, `hole`, `shown` and "
                                "`won` and no fifth fact (records.md §5, episode.md §5): got "
                                "%r" % (sorted(entry),),
                            )
                            self.assertEqual(
                                entry["seat"], position,
                                "the entries are in seat order, so the entry at position %d "
                                "names seat %d (records.md §5, seats.md §3): %r"
                                % (position, position, entry["seat"]),
                            )
                            self.assertIn(
                                entry["seat"], range(seats),
                                "a seat entry's `seat` is the seat index of the hand's own "
                                "shape, 0 .. seats - 1 (seats.md §3): %r" % (entry["seat"],),
                            )
                            hole = entry["hole"]
                            self.assertIsInstance(
                                hole, tuple,
                                "a seat's `hole` is its two cards however it finished "
                                "(records.md §5): %r" % (hole,),
                            )
                            self.assertEqual(
                                len(hole), 2,
                                "a seat's `hole` is exactly two card spellings, a folded "
                                "seat's included (records.md §5, episode.md §5): %r" % (hole,),
                            )
                            for card in hole:
                                self.assertTrue(
                                    S.card_spelling_ok(card),
                                    "every hole spelling is two characters, one rank of %r "
                                    "and one suit of %r (readout.md §2): %r"
                                    % (S.RANKS, S.SUITS, card),
                                )
                            for key in ("shown", "won"):
                                self.assertIs(
                                    type(entry[key]), bool,
                                    "a seat entry's %r is a real boolean -- never an int and "
                                    "never None (records.md §5, episode.md §5): %r"
                                    % (key, entry[key]),
                                )

                    cards, facts = leaves_of(reveal)
                    self.assertLessEqual(
                        cards, 2 * seats + 5,
                        "the hand names at most 2·seats + 5 card spellings -- %d on %r, "
                        "because it knows its board and every seat's two cards and no more "
                        "(episode.md §5, records.md §5): %d spellings"
                        % (2 * seats + 5, shape, cards),
                    )
                    named = (len(reveal) - 1) + len(reveal["seats"])
                    self.assertEqual(
                        named, seats + 3,
                        "and at most `seats + 3` other facts: three hand-level facts -- "
                        "`board`, `showdown` and `split` -- and one `seats` entry per seat, "
                        "which is %d on %r and is `records.md` §5's own count of what the "
                        "reveal holds beside the card spellings (episode.md §5). A fourth "
                        "hand-level key or a second entry per seat would move it: got %d"
                        % (seats + 3, shape, named),
                    )
                    self.assertEqual(
                        facts, 2 + 3 * seats,
                        "counted leaf by leaf the reveal names one `seat` index, one `shown` "
                        "and one `won` per seat beside `showdown` and `split`, which is %d "
                        "other facts on %r -- the record-level `seats + 3` figure is the same "
                        "statement with the `seats` entry itself standing for its own facts, "
                        "and neither reading admits a fifth fact anywhere (records.md §5, "
                        "episode.md §5).  Got %d"
                        % (2 + 3 * seats, shape, facts),
                    )

    # -- a hand that ends by a fold resolves nothing (episode-battery.md §4)
    def test_eng22_2_a_hand_that_ends_by_a_fold_shows_no_showdown(self):
        """ENG-22.2 a hand that ends by a fold has ``showdown`` false, at most one seat
        ``shown``, ``split`` false, every seat's ``won`` a plain ``False`` while fewer than
        three board cards were dealt, and ``counterfactual`` ``None`` at **every** decision
        -- on ``fixed-limit-20`` and on ``six-seat-no-limit-100`` (episode.md §5,
        episode-battery.md §4, counterfactual.md §4)."""
        for shape, seed in ((S.DEFAULT_SHAPE, S.SEED_C), (S.SIX_SEAT_SHAPE, S.SIX_SEED_C)):
            with self.subTest(shape=shape, seed=seed):
                record = self.played_on_shape(shape, seed, S.always_fold)
                decisions = record["decisions"]
                reveal = record["reveal"]
                self.assertTrue(
                    any(decision["action"] == "fold" for decision in decisions),
                    "the premise: a folding seating ends this hand by a fold (episode.md §3): "
                    "%r" % ([decision["action"] for decision in decisions],),
                )
                self.assertIs(
                    reveal["showdown"], False,
                    "a hand that ends by a fold reaches no showdown, and a fold is not a "
                    "show (episode.md §5, episode-battery.md §4): %r" % (reveal,),
                )
                self.assertIs(
                    reveal["split"], False,
                    "and no split: `split` is defined against a showdown the hand never "
                    "reached (episode.md §5): %r" % (reveal["split"],),
                )
                shown = [entry for entry in reveal["seats"] if entry["shown"]]
                self.assertLessEqual(
                    len(shown), 1,
                    "at most one seat is `shown` -- the seat that never folded -- because "
                    "every other seat applied a fold descriptor (episode.md §5, "
                    "episode-battery.md §4): %r" % (reveal["seats"],),
                )
                self.assertLess(
                    len(reveal["board"]), 3,
                    "the hand ended before a flop, so fewer than three board cards were "
                    "dealt (episode-battery.md §4): %r" % (reveal["board"],),
                )
                for entry in reveal["seats"]:
                    self.assertIs(
                        entry["won"], False,
                        "no five-card hand can be formed, so `won` is a plain False for every "
                        "seat and never None (episode.md §5, records.md §5): seat %r carries "
                        "%r" % (entry["seat"], entry["won"]),
                    )
                for position, decision in enumerate(decisions):
                    with self.subTest(shape=shape, decision=position):
                        self.assertIsNone(
                            decision["counterfactual"],
                            "a hand whose reveal does not resolve a showdown carries no "
                            "counterfactual at any of its decisions, the applied one "
                            "included (episode.md §5, counterfactual.md §2, §4): decision "
                            "%d at seat %r carried %r"
                            % (position, decision["seat"], decision["counterfactual"]),
                        )

    # -- a river showdown, and the verdicts recomputed from the cards -------
    def test_eng22_3_a_river_showdown_names_the_best_shown_hand(self):
        """ENG-22.3 on ``fixed-limit-20`` and ``six-seat-no-limit-100`` a hand whose seats
        call to the river has ``showdown`` true with five board cards and two or more seats
        ``shown``, and ``won`` and ``split`` are the library's own answer recomputed from
        the reveal's ``hole`` and ``board``: ``won`` true exactly for a seat whose best
        five-card hand is at least as good as every shown seat's, ``split`` true exactly when
        two or more shown seats tie for best -- a split hand being one this battery reaches
        as well as a won one (episode.md §5, episode-battery.md §4, counterfactual.md §4)."""
        walks = (
            (S.DEFAULT_SHAPE, S.SEED_A),
            (S.DEFAULT_SHAPE, SPLIT_SEED),
            (S.SIX_SEAT_SHAPE, S.SIX_SEED_A),
            (S.SIX_SEAT_SHAPE, S.SIX_SEED_B),
        )
        splits = set()
        for shape, seed in walks:
            with self.subTest(shape=shape, seed=seed):
                reveal = self.played_on_shape(shape, seed)["reveal"]
                entries = self.seat_entries(reveal)
                shown = [entry for entry in entries if entry["shown"]]
                self.assertIs(
                    reveal["showdown"], True,
                    "seats that call to the end show, and the hand reached its showdown "
                    "(episode.md §5, episode-battery.md §4): %r" % (reveal,),
                )
                self.assertEqual(
                    len(reveal["board"]), 5,
                    "a showdown hand has been dealt its whole board of five cards "
                    "(episode.md §5): %r" % (reveal["board"],),
                )
                self.assertGreaterEqual(
                    len(shown), 2,
                    "`showdown` is two or more seats `shown` (episode.md §5): %r"
                    % ([entry["shown"] for entry in entries],),
                )

                showdown, split, won = declared_verdicts(reveal)
                self.assertIs(
                    reveal["showdown"], showdown,
                    "the reveal's `showdown` is what the cards show: two or more seats "
                    "`shown` on a five-card board (episode.md §5)",
                )
                self.assertIs(
                    reveal["split"], split,
                    "the reveal's `split` is a tie of two or more shown seats for best, "
                    "read off the library's own hand order -- never a class of hand, which "
                    "cannot see a kicker and so cannot see a tie (episode.md §5, "
                    "counterfactual.md §4): the library says %r, the reveal says %r on %r"
                    % (split, reveal["split"], reveal["board"]),
                )
                for entry in entries:
                    self.assertIs(
                        entry["won"], won[entry["seat"]],
                        "seat %d's `won` is its own `hole` plus `board` being at least as "
                        "good as every **shown** seat's -- `not (best < other)`, because the "
                        "library's `<` reads weaker -- recomputed here from the reveal's own "
                        "spellings (episode.md §5, records.md §5): the library says %r, the "
                        "reveal says %r, on board %r with hole %r"
                        % (entry["seat"], won[entry["seat"]], entry["won"],
                           reveal["board"], entry["hole"]),
                    )
                self.assertGreaterEqual(
                    sum(1 for entry in entries if entry["won"]), 1,
                    "some seat's cards are at least as good as every shown seat's, so at "
                    "least one seat carries `won` (episode.md §5): %r" % (reveal,),
                )
                splits.add(reveal["split"])
        self.assertEqual(
            splits, {True, False},
            "the battery reaches both a hand one seat wins outright and a hand two shown "
            "seats tie, so neither branch passes by not happening (episode.md §5, "
            "counterfactual.md §4): %r" % (splits,),
        )

    # -- a folded seat's cards are still recorded (records.md §5) -----------
    def test_eng22_4_a_folded_seats_two_cards_are_still_in_the_reveal(self):
        """ENG-22.4 on ``six-seat-no-limit-100`` a seat that folds facing a river bet is
        ``shown`` false while its two spellings are still in the reveal, equal to the two
        cards its own decisions' readouts carried, and the hand still reaches its showdown
        with the other five seats shown; the folded seat's ``won`` is still the reveal's own
        question -- its cards against the shown seats' (episode.md §5, records.md §5,
        episode-battery.md §4)."""
        shape, seed = S.SIX_SEAT_SHAPE, S.SIX_SEED_A
        folding_seat = 2
        policies = [S.always_call for _ in range(S.SHAPE_SEATS[shape])]
        policies[folding_seat] = fold_facing_a_bet
        policies[5] = bet_the_river
        record = self.seated_episode(seed, policies, shape)
        reveal = record["reveal"]
        decisions = record["decisions"]

        folds = [decision for decision in decisions
                 if decision["seat"][0] == folding_seat and decision["action"] == "fold"]
        self.assertTrue(
            folds,
            "the premise: seat %d folds facing the river bet (episode.md §3): %r"
            % (folding_seat, [(decision["seat"], decision["action"]) for decision in decisions]),
        )
        self.assertEqual(
            folds[0]["readout"]["street"], "river",
            "and the fold comes on the river, so the hand has a board of five to show "
            "(episode.md §5): %r" % (folds[0]["readout"]["street"],),
        )
        self.assertIs(
            reveal["showdown"], True,
            "the five seats still live show, so the hand reached its showdown even though "
            "one seat folded (episode.md §5): %r" % (reveal,),
        )
        entries = self.seat_entries(reveal)
        self.assertEqual(
            [entry["shown"] for entry in entries],
            [seat != folding_seat for seat in range(len(entries))],
            "`shown` is 'never applied a fold descriptor at any of its decisions' -- not "
            "`state.statuses`, which reads False for a seat that mucks at showdown exactly as "
            "for a folder -- so the folding seat alone is not shown and the other five are "
            "(episode.md §5): %r" % ([entry["shown"] for entry in entries],),
        )
        folded = entries[folding_seat]
        self.assertEqual(
            tuple(folded["hole"]),
            tuple(folds[0]["readout"]["hole"]),
            "the folded seat's two cards are still in the reveal, and they are the cards its "
            "own readout carried -- however it finished, a folded seat's included "
            "(records.md §5): the reveal says %r, its readout said %r"
            % (folded["hole"], folds[0]["readout"]["hole"]),
        )
        for card in folded["hole"]:
            self.assertTrue(
                S.card_spelling_ok(card),
                "a folded seat's hole is two spellings of the declared alphabet "
                "(records.md §5, readout.md §2): %r" % (card,),
            )
        showdown, split, won = declared_verdicts(reveal)
        self.assertIs(
            folded["won"], won[folding_seat],
            "the folded seat's `won` is still its cards' worth against the shown seats' -- "
            "the one question a counterfactual at a fold asks -- so it is the reveal's own "
            "answer and not a copy of `shown` (episode.md §5, counterfactual.md §2): the "
            "library says %r, the reveal says %r" % (won[folding_seat], folded["won"]),
        )
        self.assertEqual(
            [len(entry["hole"]) for entry in entries], [2] * len(entries),
            "every seat's hole is exactly two spellings, the folded seat's included "
            "(records.md §5, episode-battery.md §3): %r" % (entries,),
        )

    # -- `amounts` (episode.md §5, sizing.md §2, §3) ------------------------
    def test_eng22_5_amounts_holds_one_entry_per_legal_descriptor(self):
        """ENG-22.5 on the default shape, on ``no-limit-100`` and on
        ``six-seat-no-limit-100``, every decision's ``amounts`` is a ``dict`` whose key set
        is exactly that decision's ``legal`` tuple -- no masked band valued and no legal
        descriptor missing -- with ``None`` at ``fold`` and ``check-call`` wherever they are
        legal and every legal raise descriptor at the raise-to its own band owns, computed
        from that decision's own ``minimum``/``maximum``; and the decision's ``amount`` is
        ``amounts[action]``, one value and not two derivations (episode.md §5, sizing.md
        §2, §3, episode-battery.md §4)."""
        walks = (
            ("fixed-limit raise", S.DEFAULT_SHAPE, S.SEED_B, S.always_raise),
            ("no-limit sizes", S.NO_LIMIT_SHAPE, S.SHAPE_SEED_A, S.last_legal),
            ("six-seat sizes", S.SIX_SEAT_SHAPE, S.SIX_SEED_A, S.last_legal),
        )
        for label, shape, seed, policy in walks:
            with self.subTest(walk=label):
                record = self.played_on_shape(shape, seed, policy)
                raises = 0
                for position, decision in enumerate(record["decisions"]):
                    with self.subTest(walk=label, decision=position):
                        amounts = decision["amounts"]
                        legal = tuple(decision["legal"])
                        self.assertIsInstance(
                            amounts, dict,
                            "`amounts` is one dict over the decision's legal descriptors "
                            "(episode.md §5): %r" % (amounts,),
                        )
                        self.assertEqual(
                            set(amounts), set(legal),
                            "`amounts` holds exactly one entry per **legal** descriptor -- "
                            "an illegal index has no entry, its band being empty and masked "
                            "out, and no legal index is missing (episode.md §5, sizing.md "
                            "§2): legal %r, amounts %r"
                            % (legal, sorted(amounts)),
                        )
                        for descriptor in legal:
                            expected = amount_of(
                                descriptor, decision["minimum"], decision["maximum"]
                            )
                            if S.is_raise(descriptor):
                                raises += 1
                                self.assertTrue(
                                    S.is_integer(amounts[descriptor]),
                                    "a legal raise descriptor resolves to an int, not to None "
                                    "and not to a float (sizing.md §2, episode.md §5): %r at "
                                    "decision %d resolves to %r"
                                    % (descriptor, position, amounts[descriptor]),
                                )
                            else:
                                self.assertIsNone(
                                    amounts[descriptor],
                                    "the two bases carry no amount -- `None` for `fold` and "
                                    "`check-call` (episode.md §5, sizing.md §2): %r at "
                                    "decision %d resolved to %r"
                                    % (descriptor, position, amounts[descriptor]),
                                )
                            self.assertEqual(
                                amounts[descriptor], expected,
                                "%r resolves to the amount its own band owns at this "
                                "decision, computed here from the decision's own minimum %r "
                                "and maximum %r (sizing.md §2, episode.md §3): got %r, the "
                                "declaration says %r"
                                % (descriptor, decision["minimum"], decision["maximum"],
                                   amounts[descriptor], expected),
                            )
                        self.assertEqual(
                            decision["amount"], amounts[decision["action"]],
                            "`amount` **is** `amounts[action]` -- one value and not two "
                            "derivations (episode.md §5, records.md §5): the action %r "
                            "carried amount %r and amounts %r"
                            % (decision["action"], decision["amount"], amounts),
                        )
                self.assertGreater(
                    raises, 0,
                    "the walk reaches decisions where raises are legal, or this case "
                    "measures nothing (sizing.md §2): %r at seed %r recorded none"
                    % (label, seed),
                )

    # -- `counterfactual`'s domain (counterfactual.md §2, §5) ---------------
    def test_eng22_6_counterfactual_covers_exactly_the_legal_descriptors(self):
        """ENG-22.6 ``counterfactual`` is ``None`` at every decision of a hand the reveal
        does not resolve -- one that ends without a showdown, and one whose shown hands tie
        for best -- and on a resolved hand it is a ``dict`` whose key set is exactly that
        decision's ``legal`` tuple at **every** decision, every value a plain ``int``, with
        ``fold``, ``check-call`` and every legal raise band present (episode.md §5,
        counterfactual.md §2, §4, §5, episode-battery.md §4)."""
        unresolved = (
            ("a hand that ends by a fold", S.DEFAULT_SHAPE, S.SEED_C, S.always_fold),
            ("a two-seat split", S.DEFAULT_SHAPE, SPLIT_SEED, S.always_call),
            ("a six-seat split", S.SIX_SEAT_SHAPE, S.SIX_SEED_B, S.always_call),
        )
        for label, shape, seed, policy in unresolved:
            with self.subTest(hand=label):
                record = self.played_on_shape(shape, seed, policy)
                self.assertFalse(
                    record["reveal"]["showdown"] and not record["reveal"]["split"],
                    "the premise: this hand's reveal resolves nothing, so the case asserts "
                    "the `None` branch rather than passing by not happening "
                    "(counterfactual.md §4): %r" % (record["reveal"],),
                )
                for position, decision in enumerate(record["decisions"]):
                    with self.subTest(hand=label, decision=position):
                        self.assertIsNone(
                            decision["counterfactual"],
                            "a hand the reveal does not resolve carries a `counterfactual` "
                            "of None at every decision -- the applied one included -- and "
                            "`amounts` is still written (episode.md §5, counterfactual.md "
                            "§2, §5): decision %d carried %r"
                            % (position, decision["counterfactual"]),
                        )
                        self.assertEqual(
                            set(decision["amounts"]), set(decision["legal"]),
                            "`amounts` is written whether the hand resolved or not "
                            "(episode.md §5): decision %d legal %r against amounts %r"
                            % (position, tuple(decision["legal"]),
                               sorted(decision["amounts"])),
                        )

        resolved = (
            ("two-seat calling", S.DEFAULT_SHAPE, S.SEED_A, S.always_call),
            ("six-seat calling", S.SIX_SEAT_SHAPE, S.SIX_SEED_A, S.always_call),
        )
        for label, shape, seed, policy in resolved:
            with self.subTest(hand=label):
                record = self.played_on_shape(shape, seed, policy)
                self.assertTrue(
                    record["reveal"]["showdown"] and not record["reveal"]["split"],
                    "the premise: this hand reaches a showdown and does not split, so the "
                    "reveal resolves it (counterfactual.md §4): %r" % (record["reveal"],),
                )
                for position, decision in enumerate(record["decisions"]):
                    with self.subTest(hand=label, decision=position):
                        values = decision["counterfactual"]
                        legal = tuple(decision["legal"])
                        self.assertTrue(
                            S.is_mapping(values),
                            "a resolved hand's decision carries a mapping of values, never "
                            "None (episode.md §5, counterfactual.md §2): decision %d carried "
                            "%r" % (position, values),
                        )
                        self.assertEqual(
                            set(values), set(legal),
                            "`counterfactual` covers **every** legal index at that decision "
                            "and no others -- an index that was not legal carries no value, "
                            "and no legal index is missing (counterfactual.md §5, "
                            "episode-battery.md §4): legal %r, values %r"
                            % (legal, sorted(values)),
                        )
                        for descriptor, value in values.items():
                            self.assertTrue(
                                S.is_integer(value),
                                "every counterfactual value is a plain int of chips -- not a "
                                "float, not a bool, not None (episode.md §5, "
                                "counterfactual.md §2): %r at decision %d is %r"
                                % (descriptor, position, value),
                            )
                        self.assertIn(
                            "check-call", values,
                            "`check-call` is always legal, so it is always valued "
                            "(counterfactual.md §5): %r" % (sorted(values),),
                        )
                        if "fold" in legal:
                            self.assertIn(
                                "fold", values,
                                "`fold` is illegal only when there is nothing to call, so "
                                "where it is legal it is valued (counterfactual.md §5): "
                                "legal %r against values %r" % (legal, sorted(values)),
                            )
                        for descriptor in S.raises_in(legal):
                            self.assertIn(
                                descriptor, values,
                                "every raise band the decision offers is valued, the untaken "
                                "arms being the whole point (counterfactual.md §5): %r "
                                "missing from %r" % (descriptor, sorted(values)),
                            )

    # -- the invariant (counterfactual.md §4, episode-battery.md §4) -------
    def test_eng22_7_the_realised_value_is_the_seats_net_chip_delta(self):
        """ENG-22.7 on a two-seat resolved hand (``fixed-limit-20``, both seats calling) and
        on a six-seat resolved hand (``six-seat-no-limit-100``, all six calling), for
        **every** decision the counterfactual's value at the descriptor the hand applied
        equals that seat's realised net chip delta, ``episode["payoffs"][seat]`` -- and that
        number is the ``reward`` at that seat's last decision, so the resolution states the
        outcome once and does not drift from it (counterfactual.md §4,
        episode-battery.md §4, episode.md §3, ASM-12)."""
        walks = (
            (S.DEFAULT_SHAPE, S.SEED_A),
            (S.DEFAULT_SHAPE, S.SEED_E),
            (S.SIX_SEAT_SHAPE, S.SIX_SEED_A),
        )
        for shape, seed in walks:
            with self.subTest(shape=shape, seed=seed):
                record = self.played_on_shape(shape, seed, S.always_call)
                reveal = record["reveal"]
                payoffs = record["payoffs"]
                self.assertTrue(
                    reveal["showdown"] and not reveal["split"],
                    "the scope episode-battery.md §4 pins is a hand whose seats call to the "
                    "end: it reached a showdown, and it did not split (counterfactual.md "
                    "§4): %r" % (reveal,),
                )
                last = {}
                for position, decision in enumerate(record["decisions"]):
                    last[decision["seat"][0]] = position
                for position, decision in enumerate(record["decisions"]):
                    with self.subTest(shape=shape, seed=seed, decision=position):
                        seat = decision["seat"][0]
                        values = decision["counterfactual"]
                        self.assertTrue(
                            S.is_mapping(values),
                            "a resolved hand's decision carries its values "
                            "(counterfactual.md §4): %r" % (values,),
                        )
                        self.assertIn(
                            decision["action"], values,
                            "the descriptor the hand applied is one of the valued ones -- "
                            "its value is the invariant's left side (counterfactual.md §4, "
                            "episode-battery.md §4): action %r against %r"
                            % (decision["action"], sorted(values)),
                        )
                        self.assertEqual(
                            values[decision["action"]], payoffs[seat],
                            "at the applied descriptor the whole-hand value **is** the "
                            "seat's realised net chip delta -- a realised call or raise "
                            "commits what the hand committed and wins what it won, so "
                            "`v(a_realised) = Δ` (counterfactual.md §4, "
                            "episode-battery.md §4): seat %d at decision %d applied %r, "
                            "valued at %r, against payoffs %r"
                            % (seat, position, decision["action"],
                               values[decision["action"]], payoffs[seat]),
                        )
                        self.assertEqual(
                            record["decisions"][last[seat]]["reward"], payoffs[seat],
                            "and that number is the reward the record carries at that "
                            "seat's last decision, so the resolution and the terminal "
                            "transition state one outcome (episode.md §3, ASM-12, "
                            "episode-battery.md §4): seat %d was paid %r and its last "
                            "decision carried %r"
                            % (seat, payoffs[seat],
                               record["decisions"][last[seat]]["reward"]),
                        )

    # -- the readout is unchanged (readout.md §2, §4, FAM-2) ----------------
    def test_eng22_8_the_readout_still_carries_only_the_acting_seats_cards(self):
        """ENG-22.8 every decision's ``readout`` still holds exactly the eleven facts of
        ``readout.md`` §2 -- no twelfth, the reveal's keys among the absent -- and its
        ``hole`` is the acting seat's own two cards and **no** other seat's: it equals the
        reveal's entry for that decision's seat and differs from every other seat's entry
        in that hand, so no encoding and no policy call can reach a card another seat holds
        (readout.md §2, §4, episode-battery.md §2, counterfactual.md §2, FAM-2)."""
        walks = (
            (S.DEFAULT_SHAPE, S.SEED_B, S.always_raise),
            (S.SIX_SEAT_SHAPE, S.SIX_SEED_A, S.last_legal),
        )
        for shape, seed, policy in walks:
            with self.subTest(shape=shape, seed=seed):
                record = self.played_on_shape(shape, seed, policy)
                holes = self.holes_by_seat(record["reveal"])
                self.assertEqual(
                    len(set(holes.values())), len(holes),
                    "the premise: every seat of this hand holds a different pair -- one "
                    "card cannot be in two seats -- so 'another seat's hole' is a different "
                    "fact (readout.md §4): %r" % (holes,),
                )
                for position, decision in enumerate(record["decisions"]):
                    with self.subTest(shape=shape, seed=seed, decision=position):
                        facts = decision["readout"]
                        seat = decision["seat"][0]
                        self.assertEqual(
                            set(facts), set(S.FACTS),
                            "the readout is still exactly the eleven declared facts -- a "
                            "policy's observation is the one it had before D-43, and no "
                            "reveal key is among them (readout.md §2, §4, FAM-2): got %r"
                            % (sorted(facts),),
                        )
                        self.assertEqual(
                            tuple(facts["hole"]), holes[seat],
                            "the readout's `hole` is the acting seat's own two cards, the "
                            "same two the reveal records for that seat (readout.md §2, "
                            "episode.md §5): seat %d read %r, the reveal holds %r"
                            % (seat, facts["hole"], holes[seat]),
                        )
                        for other, hole in holes.items():
                            if other == seat:
                                continue
                            self.assertNotEqual(
                                tuple(facts["hole"]), hole,
                                "and no other seat's hole is exposed: seat %d's readout "
                                "carries seat %d's cards, which is the one thing the facts "
                                "may never carry (readout.md §4, D-3, FAM-2): %r against %r"
                                % (seat, other, facts["hole"], hole),
                            )

    # -- the refusals and the determinism (episode.md §1, §4) --------------
    def test_eng22_9_the_refusals_and_the_determinism_are_unchanged(self):
        """ENG-22.9 the refusals D-43 did not move still refuse -- a non-callable policy, a
        shape outside the catalogue, an answer outside ``legal_actions``, a seating of the
        wrong length on the six-seat shape and a seating beside a positional policy -- a
        policy that raises still lets its own exception propagate unchanged, two identical
        calls give equal records, ``reveal`` and all, and two different seeds give different
        ones (episode.md §1, §4, episode-battery.md §1, §4, D-2)."""
        six = self.seating(S.SIX_SEAT_SHAPE)
        refusals = (
            ("a non-callable positional policy",
             lambda: S.ep("play_hand")(S.SEED_A, "always-call", S.always_call),
             ("policy",)),
            ("a shape outside the catalogue",
             lambda: S.ep("play_hand")(S.SEED_A, S.always_call, S.always_call, "no-limit-50"),
             ("no-limit-50",)),
            ("an answer outside the legal descriptors",
             lambda: S.ep("play_hand")(S.SEED_B,
                                       lambda readout, legal: "bet-the-pot",
                                       S.always_call),
             ("policy", "legal", "action")),
            ("a seating of the wrong length on the six-seat shape",
             lambda: S.ep("play_hand")(S.SIX_SEED_A, seats=six[:5], shape=S.SIX_SEAT_SHAPE),
             ("seat", "6", "5")),
            ("a seating beside a positional policy",
             lambda: S.ep("play_hand")(S.SIX_SEED_A, S.always_call, None,
                                       S.SIX_SEAT_SHAPE, six),
             ("seat", "policy")),
        )
        for label, call, words in refusals:
            with self.subTest(refusal=label):
                exc = self.refusal(call)
                self.assert_mentions(exc, *words)

        class ResolutionExploded(RuntimeError):
            pass

        def exploding(readout, legal):
            raise ResolutionExploded("this policy refuses to be resolved")

        try:
            S.ep("play_hand")(S.SEED_E, exploding, S.always_call)
        except ResolutionExploded as exc:
            self.assertIs(
                type(exc), ResolutionExploded,
                "a policy's own exception reaches the caller unchanged, never wrapped in a "
                "refusal of this module (episode.md §1, D-2, guardrails G8)",
            )
            self.assertEqual(
                str(exc), "this policy refuses to be resolved",
                "and its message is the policy's own (episode.md §1, D-2)",
            )
        except S.SurfaceAbsent:
            raise
        except Exception as exc:  # pragma: no cover - the defect this case exists for
            self.fail(
                "play_hand turned the policy's own exception into %s(%s) instead of letting "
                "it propagate (episode.md §1, D-2, guardrails G8)"
                % (type(exc).__name__, exc)
            )
        else:  # pragma: no cover
            self.fail("play_hand swallowed the policy's exception and played on (episode.md §1)")

        first = self.shaped_episode(S.SEED_F, S.always_call, S.always_call, S.DEFAULT_SHAPE)
        again = self.shaped_episode(S.SEED_F, S.always_call, S.always_call, S.DEFAULT_SHAPE)
        other = self.shaped_episode(S.SEED_E, S.always_call, S.always_call, S.DEFAULT_SHAPE)
        self.assertEqual(
            first, again,
            "one seed and one seating give one record, the reveal and the two per-decision "
            "facts included -- the record is a function of the seed and the seating alone "
            "(episode.md §4, episode-battery.md §4, ASM-2): %r against %r" % (first, again),
        )
        self.assertEqual(
            first["reveal"], again["reveal"],
            "and the reveal is stable with it, so no post-hand fact is drawn from a stream "
            "of its own (episode.md §4, ASM-2)",
        )
        self.assertNotEqual(
            first["reveal"], other["reveal"],
            "a different seed deals a different hand, so its reveal names other cards "
            "(episode.md §4, ASM-2): %r against %r" % (first["reveal"], other["reveal"]),
        )
        self.assertNotEqual(
            first, other,
            "and the two records differ, so the resolution did not flatten two hands into "
            "one (episode.md §4, ASM-2)",
        )

    # -- the arithmetic both new cases read, from the record alone ----------
    def contributions_from_record(self, record, shape):
        """Every seat's whole-hand contribution, recomputed from the record alone.

        ``C_R(seat)`` is ``starting_stack − the last recorded decision's stacks[seat]``,
        the shape's ``starting_stack`` being ``game_config``'s and not the engine's answer,
        with the **last actor's own** ``added`` restored: the last decision's readout is
        taken before the action it applied, and no other seat commits a chip after it, so
        every other seat's contribution is already final there (``episode.md`` §5,
        ``counterfactual.md`` §4).

        The two hands this file reads with it are chosen so that the last decision applied
        one of the two bases, whose ``added`` the record carries -- ``0`` for ``fold`` and
        the decision's own ``to_call`` for ``check-call``.  A raise's ``added`` is its
        ``amounts`` entry less the actor's own street bet, which the record deliberately
        does not hold (``episode.md`` §5), so a hand whose last decision raised is one this
        recomputation cannot state and the case does not pretend to.

        Returns ``(contributions, starting stack, the last actor's own added)``.
        """
        decisions = record["decisions"]
        self.assertTrue(
            decisions,
            "the premise: a hand this battery recomputes has decisions to read "
            "(episode.md §3): %r" % (record,),
        )
        last = decisions[-1]
        self.assertIn(
            last["action"], S.BASES,
            "the last decision of this hand applied %r; this recomputation restores the "
            "last actor's own `added` from the record, which only the two bases carry -- "
            "`check-call`'s `to_call` and `fold`'s nothing -- because a raise's added is "
            "its `amounts` entry less the actor's own street bet, which the record does "
            "not hold (episode.md §5, counterfactual.md §4)" % (last["action"],),
        )
        added = 0 if last["action"] == "fold" else int(last["readout"]["to_call"])
        start = int(S.ep("game_config")(shape)["starting_stack"])
        contributions = [start - int(chips) for chips in last["readout"]["stacks"]]
        contributions[last["seat"][0]] += added
        return tuple(contributions), start, added

    # -- the `shown` conjunct (counterfactual.md §4, §5 of episode.md) ------
    def folding_seating(self, seed):
        """One six-seat episode in which seat 3 may fold after calling and seat 5 bets."""
        policies = [S.always_call for _ in range(S.SHAPE_SEATS[S.SIX_SEAT_SHAPE])]
        policies[FOLDING_SEAT] = fold_from_the_turn
        policies[BETTING_SEAT] = bet_the_river
        return self.seated_episode(seed, policies, S.SIX_SEAT_SHAPE)

    def live_before_a_fold(self, record, seat):
        """``(fold position, live positions before it)`` if this hand states the pattern.

        The pattern ENG-22.10 searches for, read off the record alone: the hand resolved
        -- ``showdown`` true, ``split`` false, a mapping at every decision -- and ``seat``
        made at least one live decision and then applied a ``fold`` at a later decision of
        its own while its cards were the best of the shown seats, so its ``won`` is true
        and its ``shown`` false (``episode.md`` §5, ``counterfactual.md`` §4).
        ``None`` when any of that is absent, so the case can walk a bounded seed range and
        assert that it found one rather than pass by not happening.
        """
        reveal = record["reveal"]
        if not reveal["showdown"] or reveal["split"]:
            return None
        if any(decision["counterfactual"] is None for decision in record["decisions"]):
            return None
        shown = {entry["seat"]: entry["shown"] for entry in reveal["seats"]}
        won = {entry["seat"]: entry["won"] for entry in reveal["seats"]}
        if shown[seat] or not won[seat]:
            return None
        own = [position for position, decision in enumerate(record["decisions"])
               if decision["seat"][0] == seat]
        folds = [position for position in own
                 if record["decisions"][position]["action"] == "fold"]
        if not folds:
            return None
        live = [position for position in own
                if position < folds[0] and record["decisions"][position]["action"] != "fold"]
        if not live:
            return None
        return folds[0], live

    def test_eng22_10_a_live_decision_before_a_later_fold_is_valued_at_its_own_loss(self):
        """ENG-22.10 a bounded search of eight seeds finds a six-seat hand that resolves
        (``showdown`` true, ``split`` false, a mapping at every decision) in which seat 3
        folds on the river holding the best cards of the table -- ``shown`` false and
        ``won`` true -- after four live decisions; at each of those live decisions
        ``counterfactual[action]`` is ``−(C + added(a) + later)``, the seat's own committed
        chips and none of the pot, and it is **not** ``O``, the chips every other seat put
        in, which is what ``won`` alone would have made it; and the invariant holds at
        **every** decision of that hand, the seat's own fold included
        (counterfactual.md §4 and the paragraph under its table, episode.md §5,
        episode-battery.md §4)."""
        found = []
        for seed in range(FOLD_LATER_BASE, FOLD_LATER_BASE + FOLD_LATER_WIDTH):
            record = self.folding_seating(seed)
            pattern = self.live_before_a_fold(record, FOLDING_SEAT)
            if pattern is not None:
                found.append((seed, record, pattern))
        self.assertTrue(
            found,
            "the premise of this case is a hand that exists: one of the seeds %r deals a "
            "six-seat hand in which seat %d calls, keeps the best cards of the table and "
            "then folds on a later street, and the hand still resolves -- the `shown` "
            "conjunct is load-bearing only where such a hand is reached, so this case "
            "asserts that it found one instead of passing by not happening "
            "(counterfactual.md §4)" % (list(range(FOLD_LATER_BASE,
                                                  FOLD_LATER_BASE + FOLD_LATER_WIDTH)),
                                        FOLDING_SEAT),
        )
        seed, record, (fold_position, live_positions) = found[0]
        self.assertEqual(
            seed, FOLD_LATER_SEED,
            "the hand this case is written on is pinned, as SPLIT_SEED is: the first of "
            "the searched seeds whose record states the pattern (counterfactual.md §4).  A "
            "different seed means the deal moved, and every number below would be "
            "measuring another hand",
        )

        decisions = record["decisions"]
        reveal = record["reveal"]
        entries = {entry["seat"]: entry for entry in reveal["seats"]}
        self.assertIs(
            reveal["showdown"], True,
            "the hand is resolved: two or more seats are shown on a five-card board "
            "(episode.md §5): %r" % (reveal,),
        )
        self.assertIs(
            reveal["split"], False,
            "and it is not a split, so the reveal resolves it rather than refusing it "
            "(episode.md §5, counterfactual.md §4): %r" % (reveal["split"],),
        )
        self.assertEqual(
            len(reveal["board"]), 5,
            "the board is whole, so a best five-card hand exists for every seat "
            "(episode.md §5): %r" % (reveal["board"],),
        )
        self.assertGreaterEqual(
            sum(1 for entry in reveal["seats"] if entry["shown"]), 2,
            "two or more seats are `shown`, which is half of `showdown` (episode.md §5): "
            "%r" % ([entry["shown"] for entry in reveal["seats"]],),
        )
        self.assertIs(
            entries[FOLDING_SEAT]["shown"], False,
            "the premise: this seat applied a fold descriptor, so it is not `shown` "
            "(episode.md §5): %r" % (entries[FOLDING_SEAT],),
        )
        self.assertIs(
            entries[FOLDING_SEAT]["won"], True,
            "and its cards would have been the best of the table -- at least as good as "
            "every shown seat's -- which is the one fact `won` reports and the one the "
            "`shown` conjunct must not trust (episode.md §5, counterfactual.md §4): %r"
            % (entries[FOLDING_SEAT],),
        )
        self.assertEqual(
            decisions[fold_position]["seat"][0], FOLDING_SEAT,
            "the seat's last decision is its fold (counterfactual.md §4): %r"
            % (decisions[fold_position]["seat"],),
        )
        self.assertEqual(
            decisions[fold_position]["action"], "fold",
            "the later decision of its own is the fold itself (episode.md §3): %r"
            % (decisions[fold_position]["action"],),
        )
        self.assertEqual(
            decisions[fold_position]["readout"]["street"], "river",
            "and it comes on a later street than the live decisions it abandons "
            "(counterfactual.md §4): %r" % (decisions[fold_position]["readout"]["street"],),
        )
        self.assertGreaterEqual(
            len(live_positions), 1,
            "with at least one live decision before it -- the decision whose value the "
            "`shown` conjunct decides (counterfactual.md §4): %r" % (live_positions,),
        )
        for position, decision in enumerate(decisions):
            with self.subTest(hand=seed, decision=position):
                self.assertTrue(
                    S.is_mapping(decision["counterfactual"]),
                    "the hand resolves, so every decision of it carries values -- the "
                    "folded seat's own included, and no level guard fires on this hand "
                    "(episode.md §5, counterfactual.md §4): decision %d carried %r"
                    % (position, decision["counterfactual"]),
                )

        contributions, start, _added = self.contributions_from_record(
            record, S.SIX_SEAT_SHAPE
        )
        self.assertEqual(
            len(contributions), S.SHAPE_SEATS[S.SIX_SEAT_SHAPE],
            "one whole-hand contribution per seat of the six-seat shape (seats.md §3): %r"
            % (contributions,),
        )
        own = contributions[FOLDING_SEAT]
        pot = sum(contributions)
        others = pot - own
        self.assertNotEqual(
            others, -own,
            "the premise that makes this hand the case: `O`, the %d chips the other five "
            "seats put in, is **not** this seat's %d-chip loss, so §4's two branches give "
            "different numbers here and the `shown` conjunct is measurable rather than "
            "inert (counterfactual.md §4)" % (others, own),
        )
        for position in live_positions:
            with self.subTest(hand=seed, live=position):
                decision = decisions[position]
                self.assertEqual(
                    decision["seat"][0], FOLDING_SEAT,
                    "the live decisions valued here are that seat's own (episode.md §3): "
                    "decision %d names seat %r" % (position, decision["seat"]),
                )
                self.assertEqual(
                    decision["action"], "check-call",
                    "the premise: every live decision this seat made before it folded is a "
                    "call, so its `added(a)` is that decision's own `to_call`, which the "
                    "readout carries -- a raise's added is its `amounts` entry less the "
                    "actor's own street bet, which the record does not hold "
                    "(episode.md §5, counterfactual.md §4): decision %d applied %r"
                    % (position, decision["action"]),
                )
                committed = start - int(decision["readout"]["stacks"][FOLDING_SEAT])
                added = int(decision["readout"]["to_call"])
                later = own - committed - added
                loss = -(committed + added + later)
                self.assertEqual(
                    decision["counterfactual"][decision["action"]], loss,
                    "at a live decision on a seat that is not `shown`, the value is "
                    "**−(C + added(a) + later)**: the chips it had put in before the "
                    "decision, the chips the descriptor commits and the chips it committed "
                    "after it -- its own loss and none of the pot, because the seat left "
                    "the hand on a later street and the middle branch needs `shown` as "
                    "well as `won` (counterfactual.md §4): seat %d at decision %d applied "
                    "%r with C %d, added(a) %d and later %d, so the declaration says %d and "
                    "the record says %r"
                    % (FOLDING_SEAT, position, decision["action"], committed, added, later,
                       loss, decision["counterfactual"][decision["action"]]),
                )
                self.assertNotEqual(
                    decision["counterfactual"][decision["action"]], others,
                    "and it is **not** `O`, the %d chips every other seat contributed: this "
                    "seat's cards were the best of the table, so a resolution that read "
                    "`won` without `shown` would value this decision at the whole rest of "
                    "the pot -- the arithmetic `counterfactual.md` §4's `shown` conjunct "
                    "exists to forbid, since the seat folded and wins nothing"
                    % (others,),
                )

        folded = decisions[fold_position]
        fold_committed = start - int(folded["readout"]["stacks"][FOLDING_SEAT])
        self.assertEqual(
            folded["counterfactual"]["fold"], -fold_committed,
            "the seat's own realised fold is `−C`: it forfeits the pot and commits nothing "
            "further, so its value is the chips it had already put in "
            "(counterfactual.md §4): C was %d and the record says %r"
            % (fold_committed, folded["counterfactual"]["fold"]),
        )
        for position, decision in enumerate(decisions):
            with self.subTest(hand=seed, decision=position):
                seat = decision["seat"][0]
                self.assertEqual(
                    decision["counterfactual"][decision["action"]],
                    record["payoffs"][seat],
                    "and the invariant holds at **every** decision of this hand -- the "
                    "folded seat's live ones, its fold, and the five calls behind it -- so "
                    "the seat that folded later is the one place §4's middle branch could "
                    "have been taken by mistake, and it was not (counterfactual.md §4, "
                    "episode-battery.md §4): seat %d at decision %d applied %r, valued at "
                    "%r, against payoffs %r"
                    % (seat, position, decision["action"],
                       decision["counterfactual"][decision["action"]],
                       record["payoffs"][seat]),
                )

    # -- the self-check, as a premise the battery measures (episode.md §5) --
    def test_eng22_11_no_seats_take_lies_outside_the_pot_on_a_resolved_hand(self):
        """ENG-22.11 on the two-seat and on the six-seat resolved hand this battery already
        drives, every seat's whole-hand contribution is recomputed from the record alone
        -- ``game_config(shape)``'s ``starting_stack`` less the last decision's ``stacks``,
        with the last actor's own ``added`` restored, and the record's own ``pot`` fact
        agreeing -- and the hand passes the resolution's own self-check: every seat's take
        from the pot, ``payoffs[seat] + contribution``, is exactly ``0`` or exactly the
        whole pot, and the seat the pot was paid to took exactly the other seats' chips,
        ``O``, which is §4's middle branch; therefore no seat's take lies outside
        ``{0, pot}``, the level guard does not fire, and ``counterfactual`` is a mapping --
        never ``None`` -- at **every** decision of both hands (counterfactual.md §4's last
        paragraph, episode.md §5, episode-battery.md §4)."""
        walks = (
            ("two seats", S.DEFAULT_SHAPE, S.SEED_A),
            ("six seats", S.SIX_SEAT_SHAPE, S.SIX_SEED_A),
        )
        for label, shape, seed in walks:
            with self.subTest(hand=label):
                record = self.played_on_shape(shape, seed)
                seats = S.SHAPE_SEATS[shape]
                reveal = record["reveal"]
                self.assertTrue(
                    reveal["showdown"] and not reveal["split"],
                    "the premise: this hand reaches its showdown and does not split, so "
                    "the resolution speaks and the level guard is the only thing that could "
                    "take its values away (counterfactual.md §4): %r" % (reveal,),
                )
                contributions, start, added = self.contributions_from_record(record, shape)
                self.assertEqual(
                    len(contributions), seats,
                    "one contribution per seat of the shape, in seat order -- %d on %r "
                    "(seats.md §3): %r" % (seats, shape, contributions),
                )
                pot = sum(contributions)
                last = record["decisions"][-1]
                self.assertEqual(
                    int(last["readout"]["pot"]) + added, pot,
                    "the recomputation is the record's own pot: a decision's `pot` fact is "
                    "the pot before its action, so with the last actor's own added restored "
                    "it is the chips every seat put in (readout.md §2, episode.md §5).  The "
                    "record says %r and this recomputation says %d"
                    % (last["readout"]["pot"], pot),
                )
                self.assertEqual(
                    int(last["readout"]["pot"])
                    + sum(int(chips) for chips in last["readout"]["stacks"]),
                    seats * start,
                    "and `pot + sum(stacks)` is the shape's chips in play at every "
                    "decision -- %d on %r -- which is what makes `starting_stack − stacks` "
                    "the seat's own whole contribution and not a coincidence of one "
                    "decision (readout.md §2, seats.md §3): the record reads %r and %r"
                    % (seats * start, shape, last["readout"]["pot"],
                       last["readout"]["stacks"]),
                )
                for seat in range(seats):
                    take = record["payoffs"][seat] + contributions[seat]
                    self.assertIn(
                        take,
                        (0, pot),
                        "every seat's take from the pot is exactly 0 or exactly the whole "
                        "pot: `payoffs[seat] + C_R(seat)` is the number the resolution's "
                        "self-check reads, and a seat paid a side pot -- an all-in for "
                        "less, paid by its eligibility as well as its rank -- satisfies "
                        "neither (counterfactual.md §4's last paragraph, episode.md §5): "
                        "seat %d netted %r after contributing %d of a %d-chip pot, a take "
                        "of %d" % (seat, record["payoffs"][seat], contributions[seat], pot,
                                   take),
                    )
                won = {entry["seat"]: entry["won"] for entry in reveal["seats"]}
                winners = [seat for seat in range(seats) if won[seat]]
                self.assertEqual(
                    len(winners), 1,
                    "the premise: this hand was paid to one seat, so 'the seat that won' "
                    "is one seat and the `O` below is unambiguously its (episode.md §5): "
                    "%r" % (won,),
                )
                for seat in winners:
                    self.assertEqual(
                        record["payoffs"][seat],
                        pot - contributions[seat],
                        "and the seat the pot was paid to took exactly the sum of the other "
                        "seats' contributions -- the pot less its own, `Δ = O`, which is §4's "
                        "middle branch and the one its `won` and its `shown` both license "
                        "(counterfactual.md §4): seat %d netted %r against %d, its own "
                        "contribution being %d of a %d-chip pot"
                        % (seat, record["payoffs"][seat], pot - contributions[seat],
                           contributions[seat], pot),
                    )
                for position, decision in enumerate(record["decisions"]):
                    with self.subTest(hand=label, decision=position):
                        self.assertTrue(
                            S.is_mapping(decision["counterfactual"]),
                            "and therefore this hand carries a mapping at **every** "
                            "decision: no seat's take lies outside {0, pot}, so the level "
                            "guard does not fire and `counterfactual` is never None here "
                            "(episode.md §5, counterfactual.md §4's last paragraph, "
                            "episode-battery.md §4): decision %d at seat %r carried %r"
                            % (position, decision["seat"], decision["counterfactual"]),
                        )


if __name__ == "__main__":
    unittest.main()
