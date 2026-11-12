"""FAM-22 — the revealed counterfactual: the resolution, the one quantity and the member.

`docs/L1/battery.md` §3 FAM-22, `docs/L1/counterfactual.md` §2, §4, §6–§9,
`docs/L1/records.md` §4, §5, §7, §8, §12 and D-43.  D-43 authorises the surface change
D-41 refused: the episode record gains the hand's **reveal** — the board as dealt, whether
two or more seats showed, whether the pot was split, and per seat its two cards, whether it
showed and whether its cards were best among the **shown** seats — and each decision record
gains **`amounts`**, every legal descriptor's resolved raise-to, and **`counterfactual`**,
every legal descriptor's whole-hand net chip delta for the acting seat.  The transition
record gains the **episode boundary** `episode` and the optional `counterfactual` of length
`A`, and `agents.learners()` publishes a third catalogue under `counterfactuals` whose
second member, `reveal-counterfactual`, takes one semi-gradient step per legal action of
each transition from that transition's resolved values and reads no successor.

The cases are, in the order `docs/L1/battery.md` §3 FAM-22 lists them:

* **FAM-22.1** the reveal's four keys, one seat entry per seat in seat order, the
  `2·seats + 5` card-spelling bound, a fold-ended hand's absent showdown, and the two
  determinism facts a seeded deal gives (`counterfactual.md` §2).
* **FAM-22.2** `won` is the right question — at least as good as **every shown** seat's,
  a folded seat's included — and `split` is exactly the shown hands' tie
  (`counterfactual.md` §2, §4).
* **FAM-22.3** `amounts` and `counterfactual` on every decision: one entry per legal
  descriptor, `None` for `fold` and `check-call`, agreement with the decision's own
  `amount`, `None` throughout a hand the reveal does not resolve, and on the uncapped
  shapes a raise band's value differing from `check-call`'s exactly when the two commit
  different chips (`counterfactual.md` §4, §5).
* **FAM-22.4** the one quantity: the value `counterfactual` assigns to the action the hand
  applied **is** the reward the engine placed at that seat's terminal decision — §4's proof
  obligation, asserted per decision over several hands on all three shapes and at a
  decision that was not the seat's last.
* **FAM-22.5** the readout is untouched: exactly the eleven facts at every decision of
  every hand this family plays, no readout carrying another seat's cards, the board's
  undealt cards or the reveal, and `observation_spec`'s `fields` naming nothing new
  (`counterfactual.md` §2, `docs/L3/engine/readout.md` §4, D-3).
* **FAM-22.6** the catalogue and the member: `counterfactuals` with `none` first and
  `reveal-counterfactual` second, each stating what it reads and its step count; a spec
  naming no member building exactly the learner an explicit `none` builds; and an
  uncatalogued name refused by name in a spec, a variant entry, a pool member and a `load`
  spec (`counterfactual.md` §6).
* **FAM-22.7** the member trains on transitions carrying the resolved values and reads no
  successor; `param_count` does not move with it; its container is **version 5** with a
  required `counterfactual` field where `none` writes version 3 (default shape) or 4
  (another) with no such field; and a version-5 container round-trips through `load` and
  `save` (`counterfactual.md` §6, §9, `records.md` §4).
* **FAM-22.8** the transition record's boundary: `episode` required and an integer, the
  `counterfactual` tuple of length `A` with `None` outside the decision's legal mask, and
  one hand's transitions carrying one `episode` value (`records.md` §4).
* **FAM-22.9** a paired configuration differing in `counterfactual` alone: both arms
  trained against **one** frozen pool id, the non-default arm's member named in its record
  and in the run's `counterfactuals` set, the default arm's row carrying no such key, and
  `training.fairness` reporting the `counterfactual` axis — while a pair differing on this
  axis and on another is refused (`counterfactual.md` §6, §7, D-3).

What this file does not assert is `counterfactual.md` §7's **criterion**.  Whether a
learner trained under the member folds more than the same learner under `none` is a pinned
measurement computed by a script from two run records, and no case of a battery is a
verdict about it (`battery.md` §5, D-43).

The instances below — the seeds `SHOWDOWN_SEEDS`, `SPLIT_SEEDS` and `FOLD_SEEDS`, the
configuration `R12-dual-counterfactual`, its two variant names, the counterfactual values
`KNOWN` a hand-built batch carries and the two invented catalogue names — appear in no
design document; they are the battery's own, invented from the surface alone
(`battery.md` §4, D-15).  The seeds are chosen so that the hands the cases assert about
actually occur, and every one of them is asserted to have occurred.

**Red is the expected state of this file** until D-43's implementation lands: each case
asserts an observable outcome of the declared surface (`e2e-surface.md` §3.1, §3.3, §3.5),
and every one of them is red against absent code (`strata/examiner.md` §1, D-11).
"""

import itertools
import json
import os
import sys
import unittest
import zipfile

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _records as R  # noqa: F401
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _records as R  # noqa: E402
    import _surface as S  # noqa: E402

#: The reveal's four keys, as `records.md` §5 words them: the board as dealt, whether the
#: hand reached a showdown, whether the shown hands tie for best, and one entry per seat.
REVEAL_KEYS = ("board", "showdown", "split", "seats")

#: The four keys of one seat entry, in seat order (`records.md` §5, `counterfactual.md` §2).
SEAT_KEYS = ("seat", "hole", "shown", "won")

#: The names D-43's resolution must **not** reach the observation by: the reveal, the two
#: per-decision facts and the episode boundary are post-hand data and no encoding carries
#: them (`counterfactual.md` §2, `readout.md` §4, D-3).  A case asserts each is absent from
#: `features.observation_spec`'s declaration, which is what "the observation is unchanged"
#: is observable as.
UNDER_THE_REVEAL = ("reveal", "counterfactual", "amounts", "episode")

#: The invented seeds the all-call walks are driven at: a hand on which every seat calls
#: reaches the river and a showdown, so the reveal has a board of five and hands to compare
#: (`counterfactual.md` §2, `battery.md` §4).
SHOWDOWN_SEEDS = (S.SEED_A, S.SEED_B, S.SEED_C, S.SEED_D)

#: The invented seeds on which a hand's shown hands **tie** for best: a heads-up hand on
#: the default shape twice and a six-seat hand.  A case asserts that a split occurred
#: rather than passing by not happening (`counterfactual.md` §2, §4).
SPLIT_SEEDS = (S.SEED_F, S.SEED_I, S.SEED_H)

#: The invented seeds a six-seat hand is dealt at with **one** seat folding and the rest
#: calling, so the hand still reaches a showdown and the reveal can carry a folded seat
#: whose cards would have been best — the question `won` is defined against the shown seats
#: to answer (`counterfactual.md` §2, §4).  The battery's own numbers (`battery.md` §4).
FOLD_SEEDS = tuple(range(2, 23))

#: The known counterfactual values a hand-built batch carries, one per descriptor index:
#: fixed numbers the case wrote, so the residual the member reads is known and the update's
#: consequence is observable without reading the learner's own arithmetic
#: (`counterfactual.md` §6, `records.md` §4).
KNOWN = (11, -7, 23, 5, -13, 2)

#: The two members of the catalogue whose names the design fixes: `none`, the declared
#: default and today's behaviour exactly, and `reveal-counterfactual`
#: (`counterfactual.md` §6, `e2e-surface.md` §2 "Counterfactual").
NONE = S.COUNTERFACTUAL_DEFAULT
REVEAL = S.COUNTERFACTUAL_SECOND

#: The two invented names the catalogue does not carry, driving the four refusal sites
#: (`counterfactual.md` §6: a name outside the catalogue is refused where it is declared,
#: by name).  The battery's own; no document under `docs/L1/` carries either.
UNKNOWN = S.UNKNOWN_COUNTERFACTUAL
UNKNOWN_ENTRY = S.UNKNOWN_ENTRY_COUNTERFACTUAL

#: The one architecture both learners of the member case are built at, so the only thing
#: that differs between them is the counterfactual member (`counterfactual.md` §6, ASM-10).
MEMBER_WIDTH = S.UTILITY_WIDTH
MEMBER_DEPTH = S.UTILITY_DEPTH

#: The rank values two hands are compared with: the index of the character in the declared
#: alphabet plus two, so the two is 2 and the ace is 14 (`docs/L3/engine/readout.md` §3, and
#: `e2e-surface.md` §2's `hand_class` row for the nine classes' order).
RANK_VALUE = {character: position + 2 for position, character in enumerate(S.RANKS)}


# --------------------------------------------------------------------------
# The policies the family's hands are played with
# --------------------------------------------------------------------------
def calling_policy(readout, legal):
    """Call or check whenever the shape allows it — the walk that reaches a showdown."""
    return "check-call" if "check-call" in legal else legal[0]


def folding_policy(readout, legal):
    """Fold wherever folding is legal — the walk that ends a hand before any showdown."""
    return "fold" if "fold" in legal else "check-call"


def is_card(value):
    """Whether a value is one card of the declared spelling (`docs/L3/engine/readout.md` §3)."""
    return (
        isinstance(value, str)
        and len(value) == 2
        and value[0] in S.RANKS
        and value[1] in S.SUITS
    )


def score_five(cards):
    """One five-card hand's strength: ``(class, tie-break)``, greater being better.

    The nine classes are the order `e2e-surface.md` §2 declares for `hand_class` — 0 high
    card, 1 one pair, 2 two pair, 3 three of a kind, 4 straight, 5 flush, 6 full house, 7 four
    of a kind, 8 straight flush — and the tie-break is the ranks that decide between two
    hands of one class, so comparing two scores compares two hands.  A battery may compare
    the reveal's own card spellings: the comparison is the game's rule and not a second
    spelling of the engine's evaluator, which no case here reaches (`battery.md` §2,
    `counterfactual.md` §2's `won`, `folders.md` §3).
    """
    ranks = sorted((RANK_VALUE[card[0]] for card in cards), reverse=True)
    suits = [card[1] for card in cards]
    counts = {}
    for rank in ranks:
        counts[rank] = counts.get(rank, 0) + 1
    groups = sorted(((count, rank) for rank, count in counts.items()), reverse=True)
    distinct = sorted(set(ranks), reverse=True)
    flush = len(set(suits)) == 1
    straight = None
    if len(distinct) == 5:
        if distinct[0] - distinct[4] == 4:
            straight = distinct[0]
        elif distinct == [14, 5, 4, 3, 2]:
            straight = 5
    if straight and flush:
        return (8, (straight,))
    if groups[0][0] == 4:
        return (7, (groups[0][1], groups[1][1]))
    if groups[0][0] == 3 and groups[1][0] == 2:
        return (6, (groups[0][1], groups[1][1]))
    if flush:
        return (5, tuple(ranks))
    if straight:
        return (4, (straight,))
    if groups[0][0] == 3:
        return (3, (groups[0][1],) + tuple(rank for _count, rank in groups[1:]))
    if groups[0][0] == 2 and groups[1][0] == 2:
        return (2, (groups[0][1], groups[1][1], groups[2][1]))
    if groups[0][0] == 2:
        return (1, (groups[0][1],) + tuple(rank for _count, rank in groups[1:]))
    return (0, tuple(ranks))


def best_five(hole, board):
    """The best five-card hand of ``hole`` plus ``board`` — the comparison `won` asks for.

    `records.md` §5 makes `won` the answer to "is this seat's `hole` plus `board` at least as
    good as **every shown** seat's", so the battery compares two seats' best five of one
    board.  ``None`` while fewer than five cards are known, where no five-card hand exists,
    exactly as `hand_class` is (`e2e-surface.md` §2, `folders.md` §3, ASM-30).
    """
    cards = list(hole) + list(board)
    if len(cards) < 5:
        return None
    return max(score_five(list(combination))
               for combination in itertools.combinations(cards, 5))


class FAM22Counterfactual(S.SurfaceCase):
    """The reveal, the one quantity, the member, and the records that name it."""

    # -- the reveal (records.md §5, counterfactual.md §2) ------------------
    def reveal(self, episode):
        """An episode record's ``reveal``, or a failure naming what it does not carry."""
        return S.declared_field(
            episode, "an episode record (records.md §5)", "reveal"
        )

    def seat_entries(self, reveal):
        """The reveal's seat entries, one per seat, in seat order (`records.md` §5)."""
        value = S.declared_field(
            reveal, "the reveal of an episode record (records.md §5)", "seats"
        )
        if S.is_mapping(value):
            def order(item):
                key = str(item[0]).strip()
                return int(key) if key.isdigit() else 0
            entries = [entry for _key, entry in sorted(value.items(), key=order)]
        else:
            entries = list(value)
        for entry in entries:
            self.assertTrue(
                S.is_mapping(entry),
                "one seat entry of the reveal is a mapping carrying %r (records.md §5, "
                "counterfactual.md §2): %r" % (SEAT_KEYS, entry),
            )
        return entries

    def entry_seat(self, entry):
        """The seat index one seat entry names, read as the first number it gives."""
        value = S.declared_field(
            entry, "one seat entry of an episode record's reveal (records.md §5)", "seat"
        )
        numbers = S.numbers(value)
        self.assertTrue(
            numbers,
            "one seat entry of the reveal names its seat by index — 0 to the shape's seat "
            "count less one, in seat order (records.md §5, seats.md §3): %r" % (entry,),
        )
        return int(numbers[0])

    def flag(self, entry, key, what):
        """One boolean fact of a reveal record, read as a flag and returned as a value."""
        value = S.declared_field(entry, what, key)
        self.assertTrue(
            S.is_flag(value),
            "%s carries %r as a boolean flag (records.md §5, counterfactual.md §2): %r"
            % (what, key, value),
        )
        return bool(value)

    def board_of(self, reveal):
        """The reveal's board, as dealt, as a list of card spellings (`records.md` §5)."""
        value = S.declared_field(
            reveal, "the reveal of an episode record (records.md §5)", "board"
        )
        return [str(card) for card in value]

    def hole_of(self, entry):
        """One seat entry's two card spellings, however the seat finished (`records.md` §5)."""
        value = S.declared_field(
            entry, "one seat entry of an episode record's reveal (records.md §5)", "hole"
        )
        return [str(card) for card in value]

    def holes(self, reveal):
        """Every seat's two cards, by seat index, off the reveal's own entries."""
        out = {}
        for entry in self.seat_entries(reveal):
            out[self.entry_seat(entry)] = self.hole_of(entry)
        return out

    def seat_flags(self, reveal, key):
        """One boolean fact per seat, by seat index, off the reveal (`records.md` §5)."""
        what = "one seat entry of an episode record's reveal (records.md §5)"
        return {
            self.entry_seat(entry): self.flag(entry, key, what)
            for entry in self.seat_entries(reveal)
        }

    def won_seats(self, reveal):
        """The seats the reveal marks ``won``, in seat order."""
        return [seat for seat, flag in self.seat_flags(reveal, "won").items() if flag]

    def shown_seats(self, reveal):
        """The seats the reveal marks ``shown``, in seat order."""
        return [seat for seat, flag in self.seat_flags(reveal, "shown").items() if flag]

    def showdown(self, reveal):
        """The reveal's ``showdown`` fact (`records.md` §5, `counterfactual.md` §2)."""
        return self.flag(reveal, "showdown", "the reveal of an episode record (records.md §5)")

    def split(self, reveal):
        """The reveal's ``split`` fact (`records.md` §5, `counterfactual.md` §2)."""
        return self.flag(reveal, "split", "the reveal of an episode record (records.md §5)")

    # -- the episode and its decisions (records.md §5) ---------------------
    def played(self, shape=None, seed=S.SEED_A, fold_seat=None):
        """One episode on the shape in force, every seat calling but ``fold_seat``."""
        count = self.seats_of(shape)
        policies = [
            folding_policy if seat == fold_seat else calling_policy
            for seat in range(count)
        ]
        return self.play(seed, seats=policies, shape=shape)

    def folded(self, shape=None, seed=S.SEED_A):
        """One episode in which every seat folds wherever folding is legal.

        Such a hand ends before any street is dealt out and no seat shows, so its reveal
        records no showdown and its board is short of five — the hand that is not a
        resolution at all (`counterfactual.md` §2, §4).
        """
        count = self.seats_of(shape)
        return self.play(seed, seats=[folding_policy] * count, shape=shape)

    def decisions(self, episode):
        """The ordered decision records of one episode (`records.md` §5)."""
        return R.decision_records(episode)

    def episode_seed(self, episode):
        """The episode's own ``seed`` — the number its transitions carry as ``episode``."""
        raw = S.declared_field(
            episode, "an episode record (records.md §5)", "seed"
        )
        numbers = S.numbers(raw)
        self.assertTrue(
            numbers,
            "an episode record carries the seed it was dealt from (records.md §5): %r"
            % (episode,),
        )
        return int(numbers[0])

    def payoffs(self, episode):
        """One net chip delta per seat, by seat index (`records.md` §5, ASM-12)."""
        raw = S.declared_field(
            episode, "an episode record (records.md §5)", "payoffs"
        )
        if S.is_mapping(raw):
            return {int(key): int(round(float(value))) for key, value in raw.items()}
        values = [int(round(float(number))) for number in S.numbers(raw)]
        return {seat: value for seat, value in enumerate(values)}

    def indices_of(self, legal):
        """The legal index set of one decision, in the vocabulary's own order (§2)."""
        return [int(index) for index in self.ep("features", "legal_indices")(legal)]

    def index_of(self, decision):
        """The vocabulary index of the descriptor the hand actually applied at a decision."""
        what = "a decision record (records.md §5)"
        legal = list(S.declared_field(decision, what, "legal"))
        action = S.declared_field(decision, what, "action")
        return int(self.chosen_index(legal, action))

    def labelled(self, decision, key, shape=None):
        """The per-descriptor values of a decision's ``amounts`` or ``counterfactual``.

        `records.md` §5 gives the decision record `amounts` — every **legal** descriptor's
        resolved raise-to — and `counterfactual` — every legal descriptor's whole-hand net
        chip delta — each bounded by `A`, the shape's descriptor count
        (`counterfactual.md` §2, §4).  The container is the implementation's freedom: a
        mapping keyed by the descriptor or by its index, or a sequence of length `A` with
        `None` at the indices the decision did not permit, or — in a hand §4 refuses to
        resolve — the field itself as `None`, which is the record's own way of spelling
        "no value at any index".  All three are read here against the decision's own
        `legal` tuple, so "one entry per legal descriptor and none for an illegal one" is
        enforced where a case reads the record, and a container that names a descriptor the
        decision did not permit fails with its own message.
        """
        what = "a decision record (records.md §5)"
        raw = S.declared_field(decision, what, key)
        legal = list(S.declared_field(decision, what, "legal"))
        indices = self.indices_of(legal)
        vocabulary = self.vocabulary(shape)
        width = len(vocabulary)
        out = {}
        if raw is None:
            for index in indices:
                out[int(index)] = None
            return out
        if S.is_mapping(raw):
            tokens = {}
            for name in raw:
                tokens.setdefault(R.tok(name), name)
            for position, index in enumerate(indices):
                found = None
                for candidate in (legal[position], vocabulary.get(index), index, str(index)):
                    if candidate is None:
                        continue
                    token = R.tok(candidate)
                    if token in tokens:
                        found = tokens[token]
                        break
                self.assertIsNotNone(
                    found,
                    "%s carries %r for every legal descriptor of the decision — %r here — "
                    "and none at all for %r (records.md §5, counterfactual.md §2, §4): it "
                    "carries %r" % (what, key, legal[position], key, sorted(raw)),
                )
                out[int(index)] = raw[found]
            allowed = {R.tok(descriptor) for descriptor in legal}
            allowed |= {R.tok(vocabulary[index]) for index in indices if index in vocabulary}
            allowed |= {R.tok(index) for index in indices}
            for name in raw:
                self.assertIn(
                    R.tok(name),
                    allowed,
                    "%s carries %r for the decision's **legal** descriptors only, and the "
                    "descriptor %r was not legal at it (records.md §5, counterfactual.md "
                    "§4, §5): %r" % (what, key, name, sorted(raw)),
                )
            return out
        entries = list(raw)
        self.assertEqual(
            len(entries),
            width,
            "%s carries %r over the shape's whole vocabulary — %d descriptors — with None at "
            "the indices the decision did not permit (records.md §5, counterfactual.md §4): "
            "%r" % (what, key, width, raw),
        )
        for index in range(width):
            if index in indices:
                out[index] = entries[index]
            else:
                self.assertIsNone(
                    entries[index],
                    "%s carries %r with %r at index %d, which the decision did not permit: "
                    "an index that was not legal carries None (records.md §5, "
                    "counterfactual.md §4, `agents/rule.md` §2): %r"
                    % (what, key, entries[index], index, raw),
                )
        return out

    # -- what a decision's band commits (counterfactual.md §4) ------------
    def fresh_street(self, decision):
        """Whether this decision opens a post-flop street with nobody having bet.

        `counterfactual.md` §4's ``c(a)`` for a raise is ``amounts[a]`` less the seat's own
        bet on the street, so the arithmetic is exact only where that bet is zero.  The
        readout declares both facts that establish it: the street, and the second half of
        the `limit` fact — the bet-or-raise actions made this street (`e2e-surface.md` §2).
        With ``to_call`` zero on a post-flop street nobody has contributed to, the seat's own
        street bet is zero and ``c(check-call)`` is zero, so the two commitments are
        comparable as plain numbers.
        """
        readout = S.declared_field(decision, "a decision record (records.md §5)", "readout")
        street = str(S.readout_fact(readout, "street")).strip().lower()
        if street == "preflop":
            return False
        limit = S.readout_fact(readout, "limit")
        if not isinstance(limit, (list, tuple)) or len(limit) < 2:
            return False
        return int(limit[1]) == 0 and int(S.readout_fact(readout, "to_call")) == 0

    # -- the observation (counterfactual.md §2, readout.md §4) -------------
    def spellings_in(self, value):
        """Every card spelling found anywhere in an observable value."""
        return {text for text in S.strings(value) if is_card(text)}

    def declared_width(self, shape, representation=S.FLAT):
        """One shape's declared observation width, off ``observation_spec`` (§2, §3.2)."""
        spec = self.ep("features", "observation_spec")(self.encoder(representation, shape))
        width = 1
        for value in S.numbers(
            S.declared_field(spec, "an observation spec (e2e-surface.md §2)", "shape")
        ):
            width *= int(value)
        return width

    # -- the catalogue and the learner (counterfactual.md §6) --------------
    def catalogue(self):
        """The counterfactual catalogue `agents.learners()` publishes, as ordered pairs."""
        return S.counterfactual_catalogue(self.ep("agents", "learners")())

    def member(self, name):
        """One catalogue member by name, or `None`."""
        for candidate, member in self.catalogue():
            if candidate == name:
                return member
        return None

    def one_readout(self, seed=S.SEED_D, count=1, shape=None):
        """``count`` decisions of a hand the battery drives, with their readouts and masks.

        The walk is played by a declared baseline, so no learner's own state is read and two
        learners built at one seed decide on the very same observations and masks — the
        comparison "the same observation and mask" is made of (`counterfactual.md` §6).
        """
        walk = self.decision_walk(
            seed, self.baseline("always-call", S.SEED_D), limit=count, shape=shape
        )
        self.assertTrue(walk, "the case drove no decision at all")
        return [(readout, legal) for _hand, readout, legal, _action, _index in walk]

    def hand_batch(self, encoder, counterfactuals=False, shape=None):
        """Two hand-built transitions of one hand, with a known `counterfactual` each.

        The record is `records.md` §4's: the two encoded observations, the applied index,
        the reward, the terminal flag, the two legal masks, and — required since D-43 —
        the episode boundary.  The first transition is the hand's opening decision and the
        second ends the batch, so a learner reads one bootstrapped target and one terminal
        one unless the member's `counterfactual` speaks (`counterfactual.md` §4, §6).  With
        ``counterfactuals`` each record carries the known values of :data:`KNOWN` at its
        legal indices and ``None`` at the others, which is the record's own rule.
        """
        seed = S.SEED_C
        walk = self.decision_walk(
            seed, self.baseline("always-call", S.SEED_D), limit=2, shape=shape
        )
        self.assertEqual(
            len(walk), 2,
            "the case must drive two decisions of one hand for a two-transition batch "
            "(records.md §4): %d" % (len(walk),),
        )
        width = len(self.vocabulary(shape))
        out = []
        for position, (_hand, readout, legal, _action, index) in enumerate(walk):
            terminal = position == len(walk) - 1
            next_readout = walk[position + 1][1] if not terminal else readout
            next_legal = walk[position + 1][2] if not terminal else legal
            record = {
                "observation": self.observation(encoder, readout),
                "next_observation": self.observation(encoder, next_readout),
                "action": int(index),
                "reward": 5.0 if terminal else 0.0,
                "terminal": terminal,
                "legal": self.indices_of(legal),
                "next_legal": self.indices_of(next_legal),
                "episode": int(seed),
            }
            if counterfactuals:
                values = [None] * width
                for legal_index in self.indices_of(legal):
                    values[legal_index] = KNOWN[legal_index % len(KNOWN)]
                record["counterfactual"] = tuple(values)
            out.append(record)
        return out

    def stream(self, episode, encoder):
        """Every decision of one episode record as a transition, its boundary set (§4, §5)."""
        decisions = self.decisions(episode)
        seed = self.episode_seed(episode)
        out = []
        for position, decision in enumerate(decisions):
            what = "a decision record (records.md §5)"
            readout = S.declared_field(decision, what, "readout")
            legal = list(S.declared_field(decision, what, "legal"))
            terminal = position == len(decisions) - 1
            if terminal:
                next_readout = readout
                next_legal = legal
                reward = float(S.numbers(S.declared_field(decision, what, "reward"))[0])
            else:
                next_readout = S.declared_field(decisions[position + 1], what, "readout")
                next_legal = list(S.declared_field(decisions[position + 1], what, "legal"))
                reward = 0.0
            out.append({
                "observation": self.observation(encoder, readout),
                "next_observation": self.observation(encoder, next_readout),
                "action": self.index_of(decision),
                "reward": reward,
                "terminal": terminal,
                "legal": self.indices_of(legal),
                "next_legal": self.indices_of(next_legal),
                "episode": seed,
            })
        return out

    def named_subtree(self, value, name, depth=0):
        """The part of a record that belongs to one variant, found by its own name."""
        wanted = R.tok(name)
        if depth > 8:
            return None
        if S.is_mapping(value):
            for key, inner in value.items():
                if R.tok(key) == wanted:
                    return inner
            for inner in value.values():
                found = self.named_subtree(inner, name, depth + 1)
                if found is not None:
                    return found
        elif isinstance(value, (list, tuple)):
            for inner in value:
                found = self.named_subtree(inner, name, depth + 1)
                if found is not None:
                    return found
        return None

    # -- the artefact an entry point wrote (docs/L3/agents/checkpoint.md §2)
    def container(self, path):
        """The metadata one checkpoint container carries, read from the file it wrote.

        ``agents.save`` writes a zip with ``metadata.json`` inside it
        (``docs/L3/agents/checkpoint.md`` §2), and the **format version** is what says
        whether a field is there: a version-3 container is the default shape's, a
        version-4 one carries ``game``, and a version-5 one carries the counterfactual
        member its learner was trained under (`counterfactual.md` §6, §9, `sizing.md` §6).
        The case reads the artefact an entry point wrote and never a second spelling of it;
        the entry points are still the only thing the battery *calls* (``battery.md`` §2).
        """
        with zipfile.ZipFile(str(path)) as archive:
            return json.loads(archive.read("metadata.json").decode("utf-8"))

    def parameters(self, path):
        """The parameter array one container carries, as the bytes it stored.

        The one quantity the member's update moves is the learner's parameters, and
        ``param_count`` does not see it: the array the container stored is the artefact that
        does (`counterfactual.md` §6, ASM-10, `docs/L3/agents/checkpoint.md` §2).  The bytes
        are compared, never parsed, so the battery holds no reader of the array's layout.
        """
        with zipfile.ZipFile(str(path)) as archive:
            names = [name for name in archive.namelist() if "param" in name.lower()]
            self.assertTrue(
                names,
                "a checkpoint container carries its parameter array beside its metadata "
                "(docs/L3/agents/checkpoint.md §2): %r" % (archive.namelist(),),
            )
            return archive.read(names[0])

    def write(self, learner, name):
        """Save one learner into this case's scratch directory and return the path."""
        target = os.path.join(self.scratch(), name)
        written = self.ep("agents", "save")(learner, target)
        return str(written) if written else target

    def member_learner(self, name=NONE, seed=S.SEED_I, width=MEMBER_WIDTH,
                       depth=MEMBER_DEPTH, shape=None):
        """One learner built from the battery's spec under one counterfactual member."""
        return self.ep("agents", "build_learner")(
            self.learner_spec(width=width, depth=depth, seed=seed,
                              counterfactual=name, game=shape)
        )

    def td_error(self, statistics):
        """The learning signal out of one ``agents.learn`` statistics record."""
        values = S.numbers(S.find_values(statistics, "td_error"))
        return float(values[0]) if values else None

    def refusal_of(self, call):
        """The text of the refusal one declared call **raises**, or ``None`` if it returned.

        ``e2e-surface.md`` §2 makes an invalid argument *raise* an error naming the violated
        contract, so "refused" is read here as "the call raised".  The battery's shared
        :func:`_surface.refusal_text` also reads a *returned* record for a failure word, and
        that is the wrong reader for ``agents.learn``: a successful ``learn`` returns the
        update's statistics, whose `td_error` key holds the word "error", so the word test
        would read a trained batch as a refused one — a case that cannot fail
        (``battery.md`` §2).  Nothing here reads past an entry point either way.
        """
        try:
            call()
        except S.SurfaceAbsent:
            raise
        except Exception as exc:
            return "%s: %s" % (type(exc).__name__, exc)
        return None

    # -- FAM-22.1 ----------------------------------------------------------
    def test_fam22_1_the_episode_record_carries_a_bounded_reveal(self):
        """FAM-22.1 the reveal's four keys, one seat entry per seat, and its bound.

        `counterfactual.md` §2: the episode record carries `reveal` with exactly the four
        keys `board`, `showdown`, `split` and `seats`; `seats` holds one entry per seat of
        the shape the hand was dealt on, in seat order, each with exactly `seat`, `hole`,
        `shown` and `won`; the board is 0, 3, 4 or 5 card spellings; every spelling is two
        characters from the declared rank and suit alphabets; and the hand's card spellings
        hold to `2·seats + 5`.  Two calls at one seed give equal reveals, two seeds give
        different hands, and a hand that ends with the seats folding never reaches a
        showdown — so `showdown` is false there and the board is short of five
        (`counterfactual.md` §2, `records.md` §5).
        """
        for shape in self.shape_names():
            seats = self.seats_of(shape)
            for seed in SHOWDOWN_SEEDS[:2]:
                episode = self.played(shape, seed)
                reveal = self.reveal(episode)
                self.assertEqual(
                    sorted(str(key) for key in reveal),
                    sorted(REVEAL_KEYS),
                    "the reveal carries exactly the four keys of counterfactual.md §2 — the "
                    "board, whether the hand reached a showdown, whether the shown hands "
                    "tie, and one entry per seat — and no fifth: shape %r, seed %d holds %r"
                    % (shape, seed, sorted(str(key) for key in reveal)),
                )
                entries = self.seat_entries(reveal)
                self.assertEqual(
                    len(entries), seats,
                    "the reveal holds one seat entry per seat of the shape the hand was "
                    "dealt on — %d on %r (records.md §5, seats.md §3): %r"
                    % (seats, shape, entries),
                )
                for position, entry in enumerate(entries):
                    self.assertEqual(
                        sorted(str(key) for key in entry),
                        sorted(SEAT_KEYS),
                        "one seat entry carries exactly `seat`, `hole`, `shown` and `won` "
                        "(counterfactual.md §2, records.md §5): %r" % (entry,),
                    )
                    self.assertEqual(
                        self.entry_seat(entry), position,
                        "the reveal's seat entries are in seat order, so the entry at "
                        "position %d names seat %d (records.md §5, seats.md §3): %r"
                        % (position, position, entries),
                    )
                    hole = self.hole_of(entry)
                    self.assertEqual(
                        len(hole), 2,
                        "one seat entry's `hole` is that seat's two cards however it "
                        "finished (records.md §5, counterfactual.md §2): %r" % (hole,),
                    )
                    for card in hole:
                        self.assertTrue(
                            is_card(card),
                            "a card is two characters, one rank from %r and one suit from %r "
                            "(docs/L3/engine/readout.md §3, counterfactual.md §2): %r"
                            % (S.RANKS, S.SUITS, card),
                        )
                    for key in ("shown", "won"):
                        self.flag(
                            entry, key,
                            "one seat entry of an episode record's reveal (records.md §5)",
                        )
                board = self.board_of(reveal)
                self.assertIn(
                    len(board), (0, 3, 4, 5),
                    "the reveal's board is the board as dealt — 0, 3, 4 or 5 card spellings, "
                    "because a street deals three or one (records.md §5, "
                    "counterfactual.md §2): %r on %r at seed %d" % (board, shape, seed),
                )
                for card in board:
                    self.assertTrue(
                        is_card(card),
                        "the board's spellings are cards too — two characters from %r and "
                        "%r (docs/L3/engine/readout.md §3): %r" % (S.RANKS, S.SUITS, card),
                    )
                self.showdown(reveal)
                self.split(reveal)
                spellings = self.spellings_in(reveal)
                self.assertLessEqual(
                    len(spellings), 2 * seats + 5,
                    "the reveal carries at most 2·seats + 5 card spellings — %d on %r — "
                    "because a hand knows its board and every seat's two cards and no more, "
                    "and no fifth card of a seat's nor one of the deck's own "
                    "(counterfactual.md §2, records.md §5): the reveal holds %r"
                    % (2 * seats + 5, shape, sorted(spellings)),
                )

            # Two identical calls give one reveal, and two seeds give two hands.
            first = self.reveal(self.played(shape, S.SEED_A))
            again = self.reveal(self.played(shape, S.SEED_A))
            self.assertEqual(
                S.canon(first), S.canon(again),
                "one seed and one seating give one reveal, because the deal is the seed's "
                "(protocol.md §4, ASM-2): %r against %r on %r"
                % (first, again, shape),
            )
            other = self.reveal(self.played(shape, S.SEED_B))
            self.assertNotEqual(
                S.canon(first), S.canon(other),
                "a different seed deals a different hand, so its reveal differs — neither "
                "the hole cards nor the board is shared across seeds (protocol.md §4, "
                "counterfactual.md §2): %r on %r" % (other, shape),
            )

            # A hand that ends with the seats folding reaches no showdown.
            reveal = self.reveal(self.folded(shape, S.SEED_A))
            self.assertFalse(
                self.showdown(reveal),
                "a hand that ends with the seats folding reaches no showdown, so its reveal "
                "records none (counterfactual.md §2, records.md §5): %r on %r"
                % (reveal, shape),
            )
            self.assertLess(
                len(self.board_of(reveal)), 5,
                "a hand that ended before the river has fewer than five board cards, so the "
                "reveal's board is short of five (counterfactual.md §2): %r on %r"
                % (reveal, shape),
            )

    # -- FAM-22.2 ----------------------------------------------------------
    def test_fam22_2_won_is_the_right_question_and_split_is_the_tie(self):
        """FAM-22.2 `won` against the **shown** seats, a folded seat's included; `split` a tie.

        `counterfactual.md` §2 and `records.md` §5 define the reveal's `won` as "its `hole`
        plus `board` is at least as good as **every shown seat's**", `showdown` as "whether
        two or more seats showed", and `split` as "whether the shown hands tie for best".
        The case recomputes all three off the reveal's own card spellings: on the all-call
        walks one seat's cards are best and `won` is true for exactly that seat, and on a
        hand whose shown hands tie `split` is true and `won` is true for every tied seat.  A
        seat that **folded** can carry `won: true` — its cards would have been best — and
        that is the question a counterfactual at a fold asks, so the case finds such a hand
        and asserts it rather than passing by not happening (`counterfactual.md` §2, §4).
        """
        # 1. The all-call walks: `showdown` is what showed, `won` is what is best.
        for shape in self.shape_names():
            seen = 0
            for seed in SHOWDOWN_SEEDS:
                episode = self.played(shape, seed)
                reveal = self.reveal(episode)
                board = self.board_of(reveal)
                holes = self.holes(reveal)
                shown = self.shown_seats(reveal)
                self.assertEqual(
                    self.showdown(reveal), len(shown) >= 2,
                    "`showdown` is whether two or more seats showed (counterfactual.md §2, "
                    "records.md §5): %r showed %r on %r at seed %d"
                    % (self.showdown(reveal), shown, shape, seed),
                )
                self.assertEqual(
                    len(board), 5,
                    "every seat calling takes the hand to the river, so its reveal's board "
                    "is the whole board (counterfactual.md §2): %r on %r at seed %d"
                    % (board, shape, seed),
                )
                self.assertGreaterEqual(
                    len(shown), 2,
                    "a hand every seat calls to the river shows at least two hands, or there "
                    "is no showdown to compare (counterfactual.md §2): %r on %r at seed %d"
                    % (shown, shape, seed),
                )
                scores = {seat: best_five(holes[seat], board) for seat in holes}
                best = max(scores[seat] for seat in shown)
                tied = [seat for seat in shown if scores[seat] == best]
                won = set(self.won_seats(reveal))
                for seat in scores:
                    self.assertEqual(
                        seat in won, scores[seat] == best,
                        "`won` is true exactly for the seats whose cards are at least as "
                        "good as every **shown** seat's — seat %d of %r at seed %d scores %r "
                        "against the shown best %r, so its `won` is %r and not %r "
                        "(counterfactual.md §2)"
                        % (seat, shape, seed, scores[seat], best,
                           scores[seat] == best, seat in won),
                    )
                self.assertEqual(
                    self.split(reveal), len(tied) >= 2,
                    "`split` is true exactly when two or more shown seats' hands equal the "
                    "best — %r tie on %r at seed %d — and the shown hands are %r "
                    "(counterfactual.md §2, §4): it records %r"
                    % (tied, shape, seed, scores, self.split(reveal)),
                )
                seen += 1
            self.assertGreaterEqual(
                seen, len(SHOWDOWN_SEEDS),
                "the case must play the showdown hands it asserts about on every declared "
                "shape (battery.md §3 FAM-22): %r played %d" % (shape, seen),
            )

        # 2. The split: on the seeds chosen for it, the shown hands tie for best.
        splits = 0
        for shape, seed in ((self.shape_names()[0], SPLIT_SEEDS[0]),
                            (self.shape_names()[0], SPLIT_SEEDS[1]),
                            (self.shape_names()[-1], SPLIT_SEEDS[2])):
            episode = self.played(shape, seed)
            reveal = self.reveal(episode)
            board = self.board_of(reveal)
            holes = self.holes(reveal)
            shown = [seat for seat in self.shown_seats(reveal) if len(board) == 5]
            if len(shown) < 2:
                continue
            best = max(best_five(holes[seat], board) for seat in shown)
            tied = [seat for seat in shown if best_five(holes[seat], board) == best]
            if len(tied) < 2:
                continue
            splits += 1
            self.assertTrue(
                self.split(reveal),
                "a hand whose shown hands tie for best is a split, and the reveal records it "
                "as one (counterfactual.md §2): seed %d on %r ties %r" % (seed, shape, tied),
            )
            self.assertEqual(
                sorted(self.won_seats(reveal)), sorted(tied),
                "on a split every tied shown seat's cards are at least as good as every "
                "other shown seat's, so `won` is true for each of them (counterfactual.md "
                "§2): seed %d on %r ties %r but the reveal marks %r"
                % (seed, shape, tied, self.won_seats(reveal)),
            )
        self.assertGreaterEqual(
            splits, 2,
            "the case must find a split on a two-seat shape and one on the six-seat shape "
            "before it asserts what a split's reveal says, or it passes by not happening "
            "(battery.md §3 FAM-22, counterfactual.md §2, §4)",
        )

        # 3. A folded seat whose cards would have been best carries `won: true`.
        six = self.shape_names()[-1]
        self.assertGreaterEqual(
            self.seats_of(six), 3,
            "this case drives the third declared shape, whose seats can fold while others "
            "play on to a showdown (seats.md §2, D-33): %r" % (six,),
        )
        folded_won = 0
        for seed in FOLD_SEEDS:
            episode = self.played(six, seed, fold_seat=0)
            reveal = self.reveal(episode)
            if not self.showdown(reveal):
                continue
            board = self.board_of(reveal)
            holes = self.holes(reveal)
            shown = self.shown_seats(reveal)
            if 0 in shown or len(shown) < 2 or len(board) < 5:
                continue
            best = max(best_five(holes[seat], board) for seat in shown)
            if best_five(holes[0], board) != best:
                continue
            folded_won += 1
            won = self.seat_flags(reveal, "won")
            shown_flags = self.seat_flags(reveal, "shown")
            self.assertFalse(
                shown_flags[0],
                "the seat that folded did not show, so its entry's `shown` is false "
                "(counterfactual.md §2, records.md §5): seed %d on %r" % (seed, six),
            )
            self.assertTrue(
                won[0],
                "a seat that folded can carry `won: true` — its cards would have been best "
                "among the shown seats — and that is not a defect but the question a "
                "counterfactual at a fold asks (counterfactual.md §2, §4): seed %d on %r "
                "holds the folded seat's cards %r over the shown best"
                % (seed, six, holes[0]),
            )
            self.assertEqual(
                sorted(self.won_seats(reveal)),
                sorted([0] + [seat for seat in shown
                              if best_five(holes[seat], board) == best]),
                "`won` is the seat's cards at least as good as every **shown** seat's, "
                "folded seats included (counterfactual.md §2): seed %d on %r marks %r"
                % (seed, six, self.won_seats(reveal)),
            )
        self.assertGreater(
            folded_won, 0,
            "the case must find a hand on %r where the folded seat's cards would have been "
            "best among the shown ones, before it asserts what the reveal says about it "
            "(battery.md §3 FAM-22, counterfactual.md §2, §4): %d seeds played"
            % (six, len(FOLD_SEEDS)),
        )

    # -- FAM-22.3 ----------------------------------------------------------
    def test_fam22_3_amounts_and_counterfactual_are_per_decision_and_bounded(self):
        """FAM-22.3 `amounts` and `counterfactual`: one entry per legal descriptor.

        `counterfactual.md` §2 and `records.md` §5 give each decision record both keys:
        `amounts` maps every **legal** descriptor to the raise-to it resolves to and `None`
        for `fold` and `check-call`, and `counterfactual` maps every legal descriptor to that
        action's whole-hand net chip delta for the acting seat, or `None` throughout a hand
        the reveal does not resolve.  The case asserts the labels against the decision's own
        `legal` tuple, the agreement of `amounts` with the decision's `amount` on the
        descriptor the hand applied, the bound of every value, and — on the uncapped shapes —
        that a raise band's value differs from `check-call`'s exactly when the two commit
        different chips: `c(check-call)` is `to_call`, `c(raise)` is `amounts[raise]` less the
        seat's own bet on the street, and on a street nobody has bet in the two are the plain
        numbers the difference is asserted with (`counterfactual.md` §4, §5).
        """
        for shape in self.shape_names():
            checked = 0
            for seed in SHOWDOWN_SEEDS[:2]:
                episode = self.played(shape, seed)
                for decision in self.decisions(episode):
                    what = "a decision record (records.md §5)"
                    legal = list(S.declared_field(decision, what, "legal"))
                    indices = self.indices_of(legal)
                    amounts = self.labelled(decision, "amounts", shape)
                    values = self.labelled(decision, "counterfactual", shape)
                    applied = self.index_of(decision)
                    amount = S.declared_field(decision, what, "amount")
                    minimum = S.declared_field(decision, what, "minimum")
                    maximum = S.declared_field(decision, what, "maximum")
                    for position, index in enumerate(indices):
                        descriptor = legal[position]
                        self.assertIn(
                            index, amounts,
                            "`amounts` holds one entry per descriptor of the decision's "
                            "legal tuple, %r included (records.md §5): %r"
                            % (descriptor, sorted(amounts)),
                        )
                        if descriptor in ("fold", "check-call"):
                            self.assertIsNone(
                                amounts[index],
                                "`amounts` is `None` for `fold` and `check-call`, because "
                                "neither resolves to a raise-to (counterfactual.md §2, "
                                "records.md §5): %r resolves to %r"
                                % (descriptor, amounts[index]),
                            )
                        else:
                            self.assertTrue(
                                S._is_number(amounts[index])
                                and float(amounts[index]).is_integer(),
                                "a raise descriptor's `amounts` entry is the raise-to the "
                                "engine resolved, an integer of chips (counterfactual.md §2, "
                                "sizing.md §2): %r resolves to %r"
                                % (descriptor, amounts[index]),
                            )
                            self.assertIsNotNone(
                                minimum,
                                "a decision with a legal raise records the bounds it was "
                                "resolved between (records.md §5, sizing.md §2): %r"
                                % (decision,),
                            )
                            self.assertGreaterEqual(
                                int(amounts[index]), int(minimum),
                                "a resolved raise-to is inside the bounds the decision "
                                "records (sizing.md §2, records.md §5): %r resolved to %r "
                                "against [%r, %r]"
                                % (descriptor, amounts[index], minimum, maximum),
                            )
                            self.assertLessEqual(
                                int(amounts[index]), int(maximum),
                                "a resolved raise-to is inside the bounds the decision "
                                "records (sizing.md §2, records.md §5): %r resolved to %r "
                                "against [%r, %r]"
                                % (descriptor, amounts[index], minimum, maximum),
                            )
                        self.assertIn(
                            index, values,
                            "`counterfactual` indexes the same legal descriptors `amounts` "
                            "does (counterfactual.md §2, §4, §5): %r is missing from %r"
                            % (descriptor, sorted(values)),
                        )
                        value = values[index]
                        self.assertTrue(
                            value is None
                            or (S._is_number(value) and float(value).is_integer()),
                            "a counterfactual value is either an integer chip delta or "
                            "`None` (counterfactual.md §4): %r is %r at %r"
                            % (descriptor, value, index),
                        )
                    self.assertEqual(
                        amounts[applied], amount,
                        "`amounts` agrees with the decision's own `amount` on the descriptor "
                        "the hand applied, because both are the engine's one band arithmetic "
                        "(counterfactual.md §2, sizing.md §2, D-13): the applied index %d "
                        "carries %r against `amount` %r"
                        % (applied, amounts[applied], amount),
                    )
                    checked += 1
            self.assertGreater(
                checked, 1,
                "the case must walk real decisions on %r before it asserts their labels "
                "(battery.md §3 FAM-22): %d" % (shape, checked),
            )

        # An unresolved hand — no showdown — carries `None` throughout.
        plain = self.shape_names()[0]
        folded = self.folded(plain, S.SEED_A)
        reveal = self.reveal(folded)
        self.assertFalse(
            self.showdown(reveal),
            "this hand ends with the seats folding, so the reveal resolves nothing "
            "(counterfactual.md §2, §4): %r" % (reveal,),
        )
        for decision in self.decisions(folded):
            for index, value in self.labelled(decision, "counterfactual", plain).items():
                self.assertIsNone(
                    value,
                    "a hand the reveal does not resolve carries `None` throughout its "
                    "`counterfactual`, and no number at any legal index (counterfactual.md "
                    "§2, §4, records.md §5): index %d holds %r" % (index, value),
                )

        # On the uncapped shapes a raise band's value differs from check-call's exactly
        # when the two commit different chips (counterfactual.md §4).
        compared = 0
        exact = 0
        for shape in self.other_shapes():
            for seed in SHOWDOWN_SEEDS[:2]:
                episode = self.played(shape, seed)
                reveal = self.reveal(episode)
                if not self.showdown(reveal) or self.split(reveal):
                    continue
                won = self.seat_flags(reveal, "won")
                for decision in self.decisions(episode):
                    what = "a decision record (records.md §5)"
                    legal = list(S.declared_field(decision, what, "legal"))
                    indices = self.indices_of(legal)
                    if "check-call" not in legal:
                        continue
                    bands = [
                        (legal[position], indices[position])
                        for position in range(len(legal))
                        if legal[position] not in ("fold", "check-call")
                    ]
                    if not bands:
                        continue
                    seat = int(R.decision_seat(decision))
                    amounts = self.labelled(decision, "amounts", shape)
                    values = self.labelled(decision, "counterfactual", shape)
                    call = indices[legal.index("check-call")]
                    self.assertIsNotNone(
                        values[call],
                        "a resolved episode's every legal index carries a value, "
                        "`check-call` included (counterfactual.md §4, §5): %r" % (values,),
                    )
                    fresh = self.fresh_street(decision)
                    for descriptor, index in bands:
                        compared += 1
                        if won[seat]:
                            # §4's won branch: the seat wins the pot whatever it committed,
                            # so every non-fold action is worth the others' chips.
                            self.assertEqual(
                                float(values[index]), float(values[call]),
                                "a seat whose cards are best among the shown ones wins the "
                                "pot whatever it committed, so a raise band's value is "
                                "`check-call`'s — the others' chips — and not a second "
                                "number (counterfactual.md §4's won branch): %r against %r "
                                "at descriptor %r, seat %d of %r"
                                % (values[index], values[call], descriptor, seat, shape),
                            )
                        else:
                            # §4's not-won branch: the value is the negative of the seat's
                            # own commitment, so the two differ exactly when they commit
                            # differently — and a raise-to always exceeds the call amount.
                            self.assertNotEqual(
                                float(values[index]), float(values[call]),
                                "a seat that does not win is worth the negative of its own "
                                "commitment, so a raise band's value differs from "
                                "`check-call`'s because a raise always commits more chips "
                                "than a call (counterfactual.md §4's not-won branch, "
                                "sizing.md §2): %r against %r at descriptor %r, seat %d of "
                                "%r"
                                % (values[index], values[call], descriptor, seat, shape),
                            )
                            if fresh:
                                exact += 1
                                self.assertEqual(
                                    float(values[call]) - float(values[index]),
                                    float(amounts[index]),
                                    "on a street nobody has bet in, `check-call` commits "
                                    "nothing and a raise commits its whole raise-to, so the "
                                    "two values differ by exactly the amount the band "
                                    "resolves to (counterfactual.md §4): %r less %r is not "
                                    "%r at descriptor %r, seat %d of %r"
                                    % (values[call], values[index], amounts[index],
                                       descriptor, seat, shape),
                                )
        self.assertGreater(
            compared, 1,
            "the case must compare real raise bands against `check-call` on the uncapped "
            "shapes before it asserts the chips (battery.md §3 FAM-22): %d" % (compared,),
        )
        self.assertGreater(
            exact, 0,
            "the case must reach a decision on a street nobody has bet in — where the "
            "commitments are plain numbers — or the exact difference is never asserted "
            "(counterfactual.md §4): %d" % (exact,),
        )

    # -- FAM-22.4 ----------------------------------------------------------
    def test_fam22_4_the_applied_action_s_value_is_the_terminal_reward(self):
        """FAM-22.4 `counterfactual.md` §4's proof obligation: one quantity, per decision.

        §4 defines `counterfactual`'s entry for an action as that action's whole-hand net
        chip delta for the acting seat, and proves that at the action the hand **applied**
        it is that seat's realised delta — the number the engine places at that seat's
        terminal decision (`records.md` §5, ASM-12).  **This case is that proof obligation,
        asserted at the observable edge**: for every decision of a resolved episode — a hand
        whose reveal has `showdown: true` and `split: false` — the value `counterfactual`
        assigns to the applied action equals the seat's net chip delta, the reward that
        seat's terminal decision carries.  It is asserted per decision over several hands on
        all three declared shapes, and the case requires that at least one of them was
        **not** the seat's last decision in the hand, so it cannot pass by reading terminal
        decisions alone (`counterfactual.md` §4, §8, D-43).  §4's other exact branch is
        asserted beside it: a fold forfeits the pot and commits nothing further, so its
        value is the negated contribution at the decision, `-(s_0 - stacks[seat])`, read off
        the readout's own `stacks` and the shape's declared starting stack
        (`counterfactual.md` §4, `e2e-surface.md` §2).
        """
        for shape in self.shape_names():
            start = self.stack_of(shape)
            folds = 0
            resolved = 0
            nonterminal = 0
            for seed in SHOWDOWN_SEEDS:
                episode = self.played(shape, seed)
                reveal = self.reveal(episode)
                if not self.showdown(reveal) or self.split(reveal):
                    continue
                resolved += 1
                decisions = self.decisions(episode)
                payoffs = self.payoffs(episode)
                last = {}
                for position, decision in enumerate(decisions):
                    last[int(R.decision_seat(decision))] = position
                for position, decision in enumerate(decisions):
                    seat = int(R.decision_seat(decision))
                    values = self.labelled(decision, "counterfactual", shape)
                    applied = self.index_of(decision)
                    delta = payoffs[seat]
                    self.assertIsNotNone(
                        values[applied],
                        "a resolved episode's `counterfactual` carries a value at every "
                        "legal index, the one the hand applied included (counterfactual.md "
                        "§4, §5): seat %d of %r at seed %d holds %r"
                        % (seat, shape, seed, values),
                    )
                    self.assertEqual(
                        float(values[applied]), float(delta),
                        "counterfactual.md §4's proof: the value of the action the hand "
                        "applied is that action's realised whole-hand net chip delta, which "
                        "is the reward the engine places at that seat's terminal decision — "
                        "seat %d of %r at seed %d, decision %d, carries %r against the "
                        "delta %r"
                        % (seat, shape, seed, position, values[applied], delta),
                    )
                    self.assertEqual(
                        float(S.numbers(S.declared_field(
                            decisions[last[seat]],
                            "a decision record (records.md §5)",
                            "reward",
                        ))[0]),
                        float(delta),
                        "the reward the engine placed at that seat's terminal decision is "
                        "the hand's net chip delta and no shaped term (records.md §5, "
                        "ASM-12, utilities.md §4): seat %d of %r at seed %d"
                        % (seat, shape, seed),
                    )
                    readout = S.declared_field(
                        decision, "a decision record (records.md §5)", "readout"
                    )
                    legal = list(S.declared_field(
                        decision, "a decision record (records.md §5)", "legal"
                    ))
                    if "fold" in legal:
                        folds += 1
                        fold = self.indices_of(legal)[legal.index("fold")]
                        contribution = start - int(
                            S.numbers(S.readout_fact(readout, "stacks"))[seat]
                        )
                        self.assertEqual(
                            float(values[fold]), float(-contribution),
                            "counterfactual.md §4's fold branch: a fold forfeits the pot and "
                            "commits nothing further, so its value is the negated "
                            "contribution at the decision — seat %d of %r at seed %d has "
                            "contributed %r and the reveal values its fold at %r"
                            % (seat, shape, seed, contribution, values[fold]),
                        )
                    if position != last[seat]:
                        nonterminal += 1
            self.assertGreaterEqual(
                folds, 1,
                "the case must reach a decision where folding is legal before it asserts "
                "§4's fold branch, or the branch that catches an omitted commitment passes "
                "unasserted (counterfactual.md §4): %d folds on %r" % (folds, shape),
            )
            self.assertGreaterEqual(
                resolved, 2,
                "the case must play more than one resolved episode on %r — a hand with a "
                "showdown and no split — before it asserts §4's equality "
                "(counterfactual.md §4, §8): %d" % (shape, resolved),
            )
            self.assertGreater(
                nonterminal, 0,
                "the case must assert §4's equality at a decision that was **not** the "
                "seat's last in the hand, where the seat still has chips to commit after it, "
                "or it only reads terminal decisions and the omitted-later-street defect "
                "would pass (counterfactual.md §4, D-43's second finding): %d such "
                "decisions on %r" % (nonterminal, shape),
            )

    # -- FAM-22.5 ----------------------------------------------------------
    def test_fam22_5_the_readout_gains_no_fact_and_no_card_of_another_seat(self):
        """FAM-22.5 the readout is untouched: eleven facts, no other seat's cards, no reveal.

        `counterfactual.md` §2 and `docs/L3/engine/readout.md` §4 keep the information set
        closed: the reveal, `amounts`, `counterfactual` and `episode` are post-hand data
        written when the hand ends, so at every decision of every hand this family plays
        `engine.readout`'s keys are exactly the eleven facts of `e2e-surface.md` §2 and no
        twelfth; no readout carries another seat's cards, the board's undealt cards or the
        reveal itself; and `features.observation_spec`'s `fields` names nothing of the
        resolution, so a learner's observation is the one it had before (D-3).
        """
        deck = {rank + suit for rank in S.RANKS for suit in S.SUITS}
        for shape in self.shape_names():
            encoder = self.encoder(S.FLAT, shape)
            width = self.declared_width(shape)
            spec = self.ep("features", "observation_spec")(encoder)
            fields = S.declared_field(
                spec, "an observation spec (e2e-surface.md §2)", "fields"
            )
            self.assertTrue(
                set(str(name) for name in fields) <= set(S.READOUT_FACTS),
                "the observation spec's `fields` is a subset of the eleven readout facts — "
                "the encoding carries the information set and no fact beside it — and no "
                "twelfth fact arrives with D-43's resolution (e2e-surface.md §2, "
                "counterfactual.md §2, D-3): %r" % (list(fields),),
            )
            declared = R.tok(S.flatten_text(spec))
            for name in UNDER_THE_REVEAL:
                self.assertNotIn(
                    R.tok(name), declared,
                    "features.observation_spec declares no part of the resolution — %r — "
                    "because the reveal and the two per-decision facts are written after the "
                    "hand and no encoding may carry them (counterfactual.md §2, "
                    "readout.md §4, D-3): it declares %r" % (name, spec),
                )

            for seed, episode in ((S.SEED_A, self.played(shape, S.SEED_A)),
                                  (S.SEED_B, self.folded(shape, S.SEED_B))):
                reveal = self.reveal(episode)
                board = self.board_of(reveal)
                holes = self.holes(reveal)
                dealt = set(board)
                for hole in holes.values():
                    dealt |= set(hole)
                undealt = deck - dealt
                self.assertTrue(
                    undealt,
                    "the case must know which cards nobody held, or it cannot assert that "
                    "no readout carries one: %r on %r" % (undealt, shape),
                )
                for decision in self.decisions(episode):
                    readout = S.declared_field(
                        decision, "a decision record (records.md §5)", "readout"
                    )
                    self.assertEqual(
                        sorted(str(key) for key in readout),
                        sorted(S.READOUT_FACTS),
                        "engine.readout returns exactly the eleven facts of e2e-surface.md §2 "
                        "at every decision of every hand — no twelfth, and no part of the "
                        "reveal (counterfactual.md §2, readout.md §4): shape %r, seed %d "
                        "carries %r"
                        % (shape, seed, sorted(str(key) for key in readout)),
                    )
                    seat = S.seat_of(readout)
                    own = [str(card) for card in S.readout_fact(readout, "hole")]
                    self.assertEqual(
                        own, holes[seat],
                        "the acting seat's `hole` fact is its own two cards and no other "
                        "seat's (readout.md §4, counterfactual.md §2): seat %d of %r at seed "
                        "%d read %r against the reveal's %r"
                        % (seat, shape, seed, own, holes[seat]),
                    )
                    seen = self.spellings_in(readout)
                    self.assertTrue(
                        seen <= set(own) | set(board),
                        "a readout carries only the cards it may know — its own hole and the "
                        "public board — and never another seat's or the deck's undealt cards "
                        "(readout.md §4, counterfactual.md §2): shape %r, seed %d read %r"
                        % (shape, seed, sorted(seen - (set(own) | set(board)))),
                    )
                    self.assertFalse(
                        seen & undealt,
                        "no readout carries a card nobody has been dealt, because the deck "
                        "after the deal is not the information set (readout.md §4, "
                        "counterfactual.md §2): %r at seed %d"
                        % (sorted(seen & undealt), seed),
                    )
                    others = set()
                    for other, hole in holes.items():
                        if other != seat:
                            others |= set(hole)
                    self.assertFalse(
                        seen & others,
                        "no readout carries another seat's cards while the hand is live "
                        "(readout.md §4, counterfactual.md §2, D-43's first finding): "
                        "%r at seat %d of %r, seed %d"
                        % (sorted(seen & others), seat, shape, seed),
                    )
                    observation = self.observation(encoder, readout)
                    self.assertEqual(
                        len(S.numbers(observation)), width,
                        "the encoding of a readout is the shape's own width — %d values on "
                        "%r — so the resolution widened no observation (counterfactual.md "
                        "§2, shapes.md §8, ASM-44): %r"
                        % (width, shape, len(S.numbers(observation))),
                    )

    # -- FAM-22.6 ----------------------------------------------------------
    def test_fam22_6_the_catalogue_publishes_the_member_and_the_default_is_none(self):
        """FAM-22.6 `counterfactuals`: `none` first and the default, and no uncatalogued name.

        `counterfactual.md` §6 makes the member a third catalogue rather than a rule or a
        utility: `agents.learners()` publishes it under `counterfactuals`, in the declared
        order, with `none` first — the declared default, the rule's own target unchanged —
        and `reveal-counterfactual` second, each stating what it reads and its **step
        count**, which is the promise `rules.md` §2 corrects.  A spec naming no member builds
        the same learner a spec naming `none` builds — same `param_count`, same decision on
        the same observation and mask — and a name outside the catalogue is refused **by
        name** in a spec, in a variant entry, in a pool member and in a `load` spec
        (`counterfactual.md` §6, `records.md` §3, §7, `rules.md` §7).
        """
        declared = self.ep("agents", "learners")()
        self.assertTrue(
            S.is_mapping(declared),
            "agents.learners() returns one mapping of its catalogues (e2e-surface.md §3.3): "
            "%r" % (declared,),
        )
        self.assertEqual(
            len(declared), 6,
            "the catalogue record carries six keys — the backends, the architecture kinds, "
            "the learning rules, the utilities, the counterfactuals and the one `hyper` "
            "block — because D-43's member is a third catalogue beside the two and not a "
            "seventh record (e2e-surface.md §2, §3.3, counterfactual.md §6): it carries %r"
            % (sorted(str(key) for key in declared),),
        )
        tokens = {R.tok(key) for key in declared}
        for wanted in ("rule", "util", "counterfactual", "hyper", "backend", "architecture"):
            self.assertTrue(
                any(wanted in token for token in tokens),
                "agents.learners() publishes the %r key beside the others — the record's six "
                "keys are the backends, the architectures, the rules, the utilities, the "
                "counterfactuals and the hyper block (e2e-surface.md §3.3, "
                "counterfactual.md §6): it publishes %r"
                % (wanted, sorted(str(key) for key in declared)),
            )

        pairs = self.catalogue()
        names = [name for name, _member in pairs]
        self.assertGreaterEqual(
            len(pairs), len(S.COUNTERFACTUALS),
            "the counterfactual catalogue holds the members counterfactual.md §6 declares "
            "beside one another — `none` and `reveal-counterfactual` at least — so a spec can "
            "select one (counterfactual.md §6): it publishes %r" % (names,),
        )
        self.assertEqual(
            names[0], NONE,
            "the catalogue's first member is `none`, the declared default — the rule's own "
            "target, today's behaviour exactly (counterfactual.md §6, e2e-surface.md §2 "
            "'Counterfactual'): it publishes %r first" % (names,),
        )
        self.assertEqual(
            names[1], REVEAL,
            "the catalogue's second member is `reveal-counterfactual`, the member that takes "
            "its residual from the transition's whole-hand values and reads no successor "
            "(counterfactual.md §6): it publishes %r second" % (names,),
        )
        for name, member in pairs:
            self.assertTrue(
                S.is_mapping(member),
                "each catalogue member is a mapping stating that member (counterfactual.md "
                "§6): %r holds a %r" % (name, type(member).__name__),
            )
            self.assertEqual(
                S.member_counterfactual(member), name,
                "each catalogue member carries its own name (counterfactual.md §6): the "
                "member under %r carries %r" % (name, S.member_counterfactual(member)),
            )
            self.assertTrue(
                S.member_reads(member),
                "each catalogue member states what it reads — `none` the rule's own target, "
                "`reveal-counterfactual` the transition's whole-hand values and no successor "
                "(counterfactual.md §6): the member %r states %r"
                % (name, sorted(str(key) for key in member)),
            )
            self.assertTrue(
                S.member_steps(member),
                "each catalogue member states its own step count, which is the promise "
                "rules.md §2 corrects: `reveal-counterfactual` takes A steps per transition, "
                "A the shape's descriptor count (counterfactual.md §6, rules.md §2): the "
                "member %r states %r" % (name, sorted(str(key) for key in member)),
            )
        first, second = self.member(NONE), self.member(REVEAL)
        self.assertIsNotNone(first, "the catalogue carries `none`: %r" % (names,))
        self.assertIsNotNone(second, "the catalogue carries `reveal-counterfactual`: %r"
                             % (names,))
        self.assertNotEqual(
            S.canon(S.member_reads(first)), S.canon(S.member_reads(second)),
            "the two members read different things — one the rule's own target, the other "
            "the transition's resolved values — so their contracts differ "
            "(counterfactual.md §6): %r against %r"
            % (S.member_reads(first), S.member_reads(second)),
        )
        self.assertNotIn(
            "successor",
            R.tok(S.flatten_text(S.member_reads(second))),
            "`reveal-counterfactual` reads **no successor**: its residual is the "
            "transition's own resolved values, so its contract names no bootstrap "
            "(counterfactual.md §4, §6): %r" % (S.member_reads(second),),
        )

        # The declared default: no key at all is the same learner as an explicit `none`.
        encoder = self.encoder()
        decisions = self.one_readout(S.SEED_D, count=3)
        spec = self.learner_spec(width=MEMBER_WIDTH, depth=MEMBER_DEPTH, seed=S.SEED_I)
        self.assertNotIn(
            "counterfactual", spec,
            "this case's spec names no counterfactual member at all, which is the input "
            "counterfactual.md §6 is about: %r" % (spec,),
        )
        quiet = self.ep("agents", "build_learner")(spec)
        named = self.member_learner(NONE)
        self.assertEqual(
            int(self.ep("agents", "param_count")(quiet)),
            int(self.ep("agents", "param_count")(named)),
            "a learner built under the declared default and one built under `none` are one "
            "learner: the member owns no parameter (counterfactual.md §6, ASM-10, rules.md "
            "§3): %r against %r"
            % (self.ep("agents", "param_count")(quiet),
               self.ep("agents", "param_count")(named)),
        )
        for readout, _legal in decisions:
            self.assertEqual(
                self.action_index(self.act(named, encoder, readout)),
                self.action_index(self.act(quiet, encoder, readout)),
                "a learner built from a spec naming no counterfactual decides exactly as one "
                "built under `none` on the same observation and mask — the default is the "
                "member the catalogue declares first, and it never changes a decision "
                "(counterfactual.md §6, records.md §3): %r" % (readout,),
            )

        # A name outside the catalogue is refused by name at each of the four sites.
        outside = self.learner_spec(width=MEMBER_WIDTH, depth=MEMBER_DEPTH, seed=S.SEED_I,
                                    counterfactual=UNKNOWN)
        text = S.refusal_text(lambda: self.ep("agents", "build_learner")(outside))
        self.assertIsNotNone(
            text,
            "a learner spec naming a counterfactual member outside the catalogue is refused "
            "and never silently defaulted to `none` (counterfactual.md §6, e2e-surface.md "
            "§2 'Failure', D-43): the spec %r built a learner" % (outside,),
        )
        self.assertIn(
            R.tok(UNKNOWN), R.tok(text),
            "the refusal names the member it refused, because a name outside the catalogue "
            "is refused where it is declared, by name (counterfactual.md §6): %r" % (text,),
        )

        config = self.two_counterfactual_rung()
        config["variants"][1]["counterfactual"] = UNKNOWN_ENTRY
        text = self.refusal_of(
            lambda: self.run_record(config, (S.SEED_A,), S.BUDGET_TINY)
        )
        self.assertIsNotNone(
            text,
            "a variant entry declaring a member the catalogue does not carry is a "
            "declaration the run would not honour, so the run refuses it instead of training "
            "it under `none` (counterfactual.md §6, records.md §2, D-43): the run returned",
        )
        self.assertIn(
            R.tok(UNKNOWN_ENTRY), R.tok(text or ""),
            "the refusal names the member it refused (counterfactual.md §6): %r" % (text,),
        )

        member = self.version("kestrel")
        offending = dict(member)
        offending["counterfactual"] = UNKNOWN
        text = S.refusal_text(
            lambda: self.pool(
                {"members": [offending], "m": S.LEAGUE_BOUND, "frozen": True}
            )
        )
        self.assertIsNotNone(
            text,
            "a pool member declaring a member outside the catalogue is refused where it is "
            "declared and never mapped onto `none`, because a pool must be able to certify "
            "what its member's targets were read from (counterfactual.md §6, records.md §7, "
            "e2e-surface.md §2 'Counterfactual'): the declaration %r built a pool"
            % (offending,),
        )
        self.assertIn(
            R.tok(UNKNOWN), R.tok(text or ""),
            "the refusal names the member it refused (counterfactual.md §6): %r" % (text,),
        )
        control = self.pool(
            {"members": [dict(member)], "m": S.LEAGUE_BOUND, "frozen": True}
        )
        self.assertIn(
            R.tok(member["id"]),
            {R.tok(name) for name in R.member_ids(self.members(control))},
            "the same member declaring the catalogued member its own container records "
            "builds a pool, so it is the counterfactual name that was refused and not its "
            "checkpoint (records.md §7, §8, counterfactual.md §6): %r"
            % (R.member_ids(self.members(control)),),
        )

        path = self.write(self.member_learner(NONE), "fam22-6-none.ckpt")
        text = S.refusal_text(lambda: self.ep("agents", "load")(outside, path))
        self.assertIsNotNone(
            text,
            "a `load` spec carrying a member outside the catalogue is refused and never "
            "silently restored under the file's member (counterfactual.md §6, "
            "e2e-surface.md §2 'Counterfactual'): the spec %r loaded %r" % (outside, path),
        )
        self.assertIn(
            R.tok(UNKNOWN), R.tok(text or ""),
            "the refusal names the member it refused (counterfactual.md §6): %r" % (text,),
        )

    # -- FAM-22.7 ----------------------------------------------------------
    def test_fam22_7_the_member_trains_from_the_resolved_values_and_saves_version_5(self):
        """FAM-22.7 the member's arithmetic, its capacity, and its version-5 container.

        `counterfactual.md` §6 and `e2e-surface.md` §3.3 make `reveal-counterfactual` take
        one semi-gradient step per legal action of each transition from that transition's
        own resolved values and read no successor, `A` being the shape's descriptor count;
        `param_count` does not move with the member, because a member owns no parameter; a
        learner under it writes a **format-version-5** container carrying a required
        `counterfactual` field, where a `none` learner writes version 3 on the default shape
        and version 4 on another and carries no such field; and a version-5 container
        round-trips through `load` and `save` (`counterfactual.md` §6, §9, `records.md` §4,
        §5, D-43).
        """
        encoder = self.encoder()
        readout, _legal = self.one_readout()[0]
        plain = self.member_learner(NONE)
        member = self.member_learner(REVEAL)
        self.assertEqual(
            int(self.ep("agents", "param_count")(plain)),
            int(self.ep("agents", "param_count")(member)),
            "the member owns no parameter — it changes where a residual comes from, not the "
            "state layout — so param_count is unchanged by it (counterfactual.md §6, "
            "rules.md §3, ASM-10)",
        )

        # 1. A batch carrying the resolved values moves the parameters, and moves them from
        #    the resolved values and not from a bootstrap.
        batch = self.hand_batch(encoder, counterfactuals=True)
        before = self.parameters(self.write(member, "fam22-7-before.ckpt"))
        statistics = self.ep("agents", "learn")(member, [dict(record) for record in batch])
        self.assertTrue(
            S.is_mapping(statistics),
            "agents.learn returns the update's own statistics under the member too, so one "
            "curve is one shape whatever the member (rules.md §3, e2e-surface.md §3.3): %r"
            % (statistics,),
        )
        after = self.parameters(self.write(member, "fam22-7-after.ckpt"))
        self.assertNotEqual(
            before, after,
            "one semi-gradient step per legal action of each transition moves the learner's "
            "parameters — the observable consequence of an update that happened "
            "(counterfactual.md §6, rules.md §3): the array the container stored is unchanged",
        )
        ordinary = self.member_learner(NONE, seed=S.SEED_I)
        same_batch = self.ep("agents", "learn")(
            ordinary, [dict(record) for record in batch]
        )
        self.assertIsNotNone(
            self.td_error(same_batch),
            "the default member's update reports its learning signal for a curve "
            "(rules.md §3, protocol.md §1): %r" % (same_batch,),
        )
        self.assertNotEqual(
            self.td_error(statistics), self.td_error(same_batch),
            "the member's residual comes from the transition's own `counterfactual` values "
            "and the default member's from the rule's bootstrap, so the two learners report "
            "different errors on one batch — the observable that the resolved values were "
            "read and no successor was (counterfactual.md §4, §6): %r against %r"
            % (statistics, same_batch),
        )

        # 2. A batch whose counterfactual is absent trains under the ordinary target.
        absent = self.hand_batch(encoder)
        self.assertFalse(
            any("counterfactual" in record for record in absent),
            "this case's fallback batch carries no `counterfactual` key at all, which is the "
            "record counterfactual.md §4 refuses to resolve (records.md §4): %r"
            % (absent,),
        )
        quiet = self.member_learner(NONE, seed=S.SEED_J)
        fallback = self.member_learner(REVEAL, seed=S.SEED_J)
        quiet_before = self.parameters(self.write(quiet, "fam22-7-quiet-before.ckpt"))
        fallback_before = self.parameters(self.write(fallback, "fam22-7-fallback-before.ckpt"))
        self.assertEqual(
            quiet_before, fallback_before,
            "two learners built from one spec at one seed and one architecture draw one "
            "initial parameter array, because the member owns no parameter and the draw is "
            "the seed's (protocol.md §4, ASM-2, counterfactual.md §6)",
        )
        self.ep("agents", "learn")(quiet, [dict(record) for record in absent])
        fallback_batch = self.ep("agents", "learn")(
            fallback, [dict(record) for record in absent]
        )
        quiet_after = self.parameters(self.write(quiet, "fam22-7-quiet-after.ckpt"))
        fallback_after = self.parameters(self.write(fallback, "fam22-7-fallback-after.ckpt"))
        self.assertNotEqual(
            fallback_before, fallback_after,
            "a batch whose `counterfactual` is absent still trains: the member falls back to "
            "its rule's own target and the update moves the parameters (counterfactual.md "
            "§4, §6): the array the container stored is unchanged",
        )
        self.assertEqual(
            quiet_after, fallback_after,
            "where the transition carries no `counterfactual` the member's residual is the "
            "rule's own target — the same target the default member reads — so the two "
            "learners' updates land on one parameter array (counterfactual.md §4, §6, "
            "D-40): they differ",
        )

        # 3. The containers: version 5 with the field, and version 3 / 4 without it.
        default_meta = self.container(self.write(plain, "fam22-7-version-3.ckpt"))
        self.assertEqual(
            int(default_meta["format_version"]), 3,
            "a `none` learner of the default shape keeps writing version 3 — the container "
            "it always wrote, byte for byte (counterfactual.md §6, §9, sizing.md §6): %r"
            % (default_meta.get("format_version"),),
        )
        self.assertNotIn(
            "counterfactual", default_meta,
            "a container written under `none` carries no `counterfactual` field, so a "
            "fixed-limit save under the default member is today's container "
            "(counterfactual.md §6, §9): %r" % (sorted(default_meta),),
        )
        other = self.other_shapes()[0]
        shaped_meta = self.container(self.write(
            self.ep("agents", "build_learner")(
                self.learner_spec(width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH, seed=S.SEED_I,
                                  counterfactual=NONE, game=other)
            ),
            "fam22-7-version-4.ckpt",
        ))
        self.assertEqual(
            int(shaped_meta["format_version"]), 4,
            "a `none` learner of another declared shape keeps writing version 4, its `game` "
            "field and no counterfactual one (counterfactual.md §6, §9, shapes.md §5): %r"
            % (shaped_meta.get("format_version"),),
        )
        self.assertNotIn(
            "counterfactual", shaped_meta,
            "a version-4 container carries the shape and still no `counterfactual` field "
            "(counterfactual.md §6, §9, sizing.md §6): %r" % (sorted(shaped_meta),),
        )
        version_five = self.write(self.member_learner(REVEAL), "fam22-7-version-5.ckpt")
        five = self.container(version_five)
        self.assertEqual(
            int(five["format_version"]), 5,
            "a learner under a member other than `none` writes format **version 5**, which "
            "is what lets a reader name the member that produced its whole-hand targets "
            "(counterfactual.md §6, §9, records.md §7): %r"
            % (five.get("format_version"),),
        )
        self.assertEqual(
            str(five.get("counterfactual")), REVEAL,
            "a version-5 container carries the `counterfactual` field as a **required** one, "
            "naming the catalogue member its targets came from (counterfactual.md §6): %r"
            % (five.get("counterfactual"),),
        )

        # 4. And it round-trips through `load` and `save`.
        fresh = self.member_learner(REVEAL)
        restored = self.ep("agents", "load")(
            self.learner_spec(width=MEMBER_WIDTH, depth=MEMBER_DEPTH, seed=S.SEED_I,
                              counterfactual=REVEAL),
            version_five,
        )
        self.assertEqual(
            int(self.ep("agents", "param_count")(restored)),
            int(self.ep("agents", "param_count")(fresh)),
            "a version-5 container restores the learner it recorded, at its own capacity "
            "(counterfactual.md §6, rules.md §3, ASM-10)",
        )
        self.assertEqual(
            self.action_index(self.act(restored, encoder, readout)),
            self.action_index(self.act(fresh, encoder, readout)),
            "save and load are loss-free at the decision boundary under the member, as under "
            "any rule and utility (rules.md §3, counterfactual.md §6): %r" % (version_five,),
        )
        written = self.container(self.write(restored, "fam22-7-version-5-again.ckpt"))
        self.assertEqual(
            int(written["format_version"]), 5,
            "a learner restored from a version-5 container saves one again — the member is "
            "still the member after a round trip (counterfactual.md §6, §9): %r"
            % (written.get("format_version"),),
        )
        self.assertEqual(
            str(written.get("counterfactual")), REVEAL,
            "the round-tripped container carries the same `counterfactual` field: %r"
            % (written.get("counterfactual"),),
        )

    # -- FAM-22.8 ----------------------------------------------------------
    def test_fam22_8_the_transition_record_s_boundary_is_refused_by_name(self):
        """FAM-22.8 `episode` required and an integer; `counterfactual` of length `A`, masked.

        `records.md` §4 makes the transition record carry `episode` — the episode's own
        `seed` as an `int`, so one hand's transitions carry one number — and the optional
        `counterfactual` a tuple of length `A` whose entry at a legal index is that action's
        whole-hand value and `None` at an index that was not legal (`counterfactual.md` §2,
        §4, §6).  `agents.learn` refuses a transition missing the boundary, one whose
        boundary is not an integer, one whose values are the wrong length, and one carrying
        a value at an index outside the decision's legal mask — each **by name** — and
        accepts a well-formed batch of one hand's transitions carrying one boundary value.
        """
        encoder = self.encoder()
        shape = self.shape_names()[0]
        width = len(self.vocabulary(shape))
        batch = self.hand_batch(encoder, counterfactuals=True, shape=shape)
        statistics = self.ep("agents", "learn")(
            self.member_learner(REVEAL), [dict(record) for record in batch]
        )
        self.assertTrue(
            S.is_mapping(statistics),
            "a transition carrying the episode boundary and a masked `counterfactual` of "
            "length A is the record records.md §4 declares, and it trains: `agents.learn` "
            "returns the update's statistics for the curve (records.md §4, counterfactual.md "
            "§2, §4): %r" % (statistics,),
        )

        for position, record in enumerate(batch):
            missing = {
                key: value for key, value in record.items()
                if key != "episode"
            }
            text = self.refusal_of(
                lambda missing=missing: self.ep("agents", "learn")(
                    self.member_learner(REVEAL), [missing]
                )
            )
            self.assertIsNotNone(
                text,
                "`episode` is a **required** key of the transition record since D-43, and "
                "`agents.learn` refuses a transition without it rather than learning from a "
                "record that cannot express an episode-scoped target (records.md §4, "
                "counterfactual.md §2, rules.md §5): transition %d trained" % (position,),
            )
            self.assertIn(
                R.tok("episode"), R.tok(text or ""),
                "the refusal names the missing boundary (records.md §4): %r" % (text,),
            )

        not_integer = dict(batch[0])
        not_integer["episode"] = 1.5
        text = self.refusal_of(
            lambda: self.ep("agents", "learn")(
                self.member_learner(REVEAL), [not_integer]
            )
        )
        self.assertIsNotNone(
            text,
            "the boundary is the episode's own `seed` as an **int**, and 1.5 is no episode "
            "seed: `agents.learn` refuses it rather than coercing it (records.md §4, "
            "counterfactual.md §2): the batch trained",
        )
        self.assertIn(
            R.tok("episode"), R.tok(text or ""),
            "the refusal names `episode` (records.md §4): %r" % (text,),
        )

        wrong_length = dict(batch[0])
        values = list(S.declared_field(
            wrong_length, "a transition record (records.md §4)", "counterfactual"
        ))
        wrong_length["counterfactual"] = tuple(values[:-1])
        text = self.refusal_of(
            lambda: self.ep("agents", "learn")(
                self.member_learner(REVEAL), [wrong_length]
            )
        )
        self.assertIsNotNone(
            text,
            "`counterfactual` is a tuple of length A — %d on %r — and a tuple one short is "
            "not that record: `agents.learn` refuses it by name rather than reading the "
            "wrong descriptor's value (records.md §4, counterfactual.md §6): it trained"
            % (width, shape),
        )
        self.assertIn(
            R.tok("counterfactual"), R.tok(text or ""),
            "the refusal names `counterfactual` (records.md §4): %r" % (text,),
        )

        outside = dict(batch[1])
        mask = [index for index in range(1, width)]
        outside["legal"] = mask
        outside["next_legal"] = list(mask)
        outside["action"] = mask[0]
        leaked = [None] * width
        leaked[0] = KNOWN[0]
        outside["counterfactual"] = tuple(leaked)
        text = self.refusal_of(
            lambda: self.ep("agents", "learn")(
                self.member_learner(REVEAL), [outside]
            )
        )
        self.assertIsNotNone(
            text,
            "a masked action is never valued and never updated: a `counterfactual` carrying "
            "a value at an index outside the transition's legal mask is refused by name "
            "(counterfactual.md §4, §5, records.md §4, `agents/rule.md` §2): it trained",
        )
        self.assertIn(
            R.tok("counterfactual"), R.tok(text or ""),
            "the refusal names `counterfactual` (records.md §4): %r" % (text,),
        )

        # One hand's transitions carry one boundary; the boundary is that hand's own seed.
        episode = self.played(shape, S.SEED_C)
        stream = self.stream(episode, encoder)
        self.assertGreaterEqual(
            len(stream), 2,
            "the case must build more than one transition of one hand, or one boundary value "
            "is not evidence (records.md §4): %d" % (len(stream),),
        )
        seed = self.episode_seed(episode)
        boundaries = {record["episode"] for record in stream}
        self.assertEqual(
            len(boundaries), 1,
            "two transitions of one hand handed in one batch carry **one** `episode` value, "
            "which is that episode's own seed (records.md §4, §5): %r"
            % (sorted(boundaries),),
        )
        self.assertEqual(
            boundaries.pop(), seed,
            "the boundary is the episode's own `seed` — the number engine.play_hand's record "
            "carries — so a second hand's transitions carry a second number (records.md §4, "
            "§5, counterfactual.md §2): it carried a value against the seed %r" % (seed,),
        )
        trained = self.ep("agents", "learn")(
            self.member_learner(REVEAL), [dict(record) for record in stream]
        )
        self.assertTrue(
            S.is_mapping(trained),
            "one hand's whole transition stream, its boundary and its masks included, is an "
            "admissible batch for the member: the boundary is expressible for every member "
            "and no member refuses it (records.md §4, rules.md §5, counterfactual.md §2): %r"
            % (trained,),
        )

    # -- FAM-22.9 ----------------------------------------------------------
    def test_fam22_9_a_pair_differing_in_the_member_alone_trains_both_arms(self):
        """FAM-22.9 one configuration, two arms differing in `counterfactual` alone.

        `counterfactual.md` §6 and §7 and D-3: the member is opt-in per variant, so a paired
        arm differs only in it — one configuration, one frozen pool, one seed set, one
        budget.  Both arms are trained; the run record names the member for the non-default
        variant and carries it in its `counterfactuals` set; the default arm's row carries
        **no** such key, so a default declaration's record keeps the shape its capture took;
        the two arms name **one** pool id; and `training.fairness` reports the
        `counterfactual` axis.  A pair whose arms differ on this axis **and** on another is
        refused, because it is no longer the one-axis comparison the member exists for
        (`counterfactual.md` §6, §7, `rules.md` §8, `ladder.md` §4).
        """
        seeds = (S.SEED_A,)
        config = self.two_counterfactual_rung(seeds=seeds)
        left, right = config["variants"]
        self.assertEqual(
            left["counterfactual"], NONE,
            "this configuration's first arm names the catalogue's first member explicitly, "
            "so the two arms differ on `counterfactual` alone (counterfactual.md §6, D-3): "
            "%r" % (left,),
        )
        self.assertEqual(
            right["counterfactual"], REVEAL,
            "its second arm names `reveal-counterfactual` (counterfactual.md §6): %r"
            % (right,),
        )
        record = self.run_record(config, seeds, S.BUDGET_TINY)
        names = [str(entry["name"]) for entry in config["variants"]]

        curves = S.family_value(record, "curves")
        self.assertIsNotNone(
            curves,
            "the run record carries its curves family (records.md §12): %r"
            % (sorted(str(key) for key in record),),
        )
        if S.is_mapping(curves):
            self.assertEqual(
                sorted(str(key) for key in curves),
                sorted(names),
                "every variant a configuration declares is trained, so the curves hold one "
                "entry per variant — not one arm and its opposition (counterfactual.md §6, "
                "records.md §12): %r" % (sorted(str(key) for key in curves),),
            )
        else:
            body = R.tok(S.flatten_text(curves))
            for name in names:
                self.assertIn(
                    R.tok(name), body,
                    "the curves the run reports name the variant %r that trained them "
                    "(records.md §12): %r" % (name, curves),
                )

        block = S.family_value(record, "checkpoints")
        self.assertIsNotNone(
            block,
            "the run record carries its checkpoints family (records.md §12): %r"
            % (sorted(str(key) for key in record),),
        )
        for name in names:
            subtree = self.named_subtree(block, name)
            self.assertIsNotNone(
                subtree,
                "the checkpoints entry names the artefacts of the variant %r, because each "
                "variant produces its own final model (records.md §12, counterfactual.md "
                "§6): %r" % (name, block),
            )
            paths = S.checkpoint_paths(subtree)
            self.assertGreaterEqual(
                len(paths), len(seeds),
                "the variant %r writes one final model per seed (records.md §12, ASM-18): %r"
                % (name, paths),
            )
            for path in paths:
                self.assertTrue(
                    os.path.exists(path),
                    "a checkpoint the run record names is on disk, so the two arms' models "
                    "are two artefacts (protocol.md §5): %r" % (path,),
                )

        declared = S.counterfactual_names_of(S.run_counterfactuals(record))
        self.assertIn(
            REVEAL, declared,
            "the run record's `counterfactuals` set is the set of members the run declared "
            "and trained, and one arm declared `reveal-counterfactual` "
            "(records.md §12, counterfactual.md §6): %r" % (declared,),
        )

        entries = S.family_value(record, "variants")
        if S.is_mapping(entries):
            entries = list(entries.values())
        entries = [entry for entry in (entries or ()) if S.is_mapping(entry)]
        self.assertEqual(
            len(entries), len(names),
            "the run record carries one entry per declared variant (records.md §12): %r"
            % (entries,),
        )
        for name, member in ((names[0], NONE), (names[1], REVEAL)):
            entry = None
            for candidate in entries:
                if R.tok(S.variant_name(candidate)) == R.tok(name):
                    entry = candidate
                    break
            self.assertIsNotNone(
                entry, "the run record names no variant %r: %r" % (name, entries)
            )
            tokens = {R.tok(key) for key in entry}
            if member == NONE:
                self.assertFalse(
                    any("counterfactual" in token for token in tokens),
                    "the default arm's row carries **no** `counterfactual` key: records.md "
                    "§12 makes a variant entry name its member only when it is not `none`, "
                    "which is what keeps a default declaration's record at the shape its "
                    "capture took (counterfactual.md §6, §9): %r" % (entry,),
                )
            else:
                self.assertEqual(
                    S.variant_counterfactual(entry), REVEAL,
                    "the run record names each non-default variant's member, so a run says "
                    "which member's whole-hand values produced which curve (records.md §12, "
                    "counterfactual.md §6): %r" % (entry,),
                )

        identifiers = S.pool_identity(record)
        self.assertTrue(
            identifiers,
            "the run record carries the frozen pool's id it trained against "
            "(e2e-surface.md §3.5, D-16): %r" % (record,),
        )
        self.assertEqual(
            len(set(identifiers)), 1,
            "two arms of one paired configuration train against **one** frozen pool, so one "
            "run record carries one pool id (counterfactual.md §6, §7, D-3, ASM-16): %r"
            % (sorted(set(identifiers)),),
        )

        text = S.refusal_text(lambda: self.ep("training", "fairness")(left, right))
        self.assertIsNone(
            text,
            "a pair whose two arms declare two counterfactual members is a reportable "
            "comparison that differs on that axis, and not a refused pair: `counterfactual` "
            "joined the axes a pair may differ on (rules.md §8, counterfactual.md §6, D-3): "
            "%r" % (text,),
        )
        result = self.ep("training", "fairness")(left, right)
        axis = S.axis_text(result)
        self.assertIn(
            "counterfactual", axis,
            "the pair differs on the counterfactual member, so the axis fairness returns is "
            "that axis (training.fairness returns the one axis it differs on, "
            "counterfactual.md §6, e2e-surface.md §3.5): %r" % (axis,),
        )
        constants = R.tok(S.flatten_text(result))
        for token in ("budget", "seed", "param"):
            self.assertIn(
                token, constants,
                "the pair still reports what it holds constant, including %r, beside the "
                "axis it differs on (rules.md §8, ladder.md §4): %r" % (token, result),
            )

        doctored = [dict(left), dict(right)]
        doctored[1]["backend"] = "torch"
        refusal = S.refusal_text(
            lambda: self.ep("training", "fairness")(doctored[0], doctored[1])
        )
        self.assertIsNotNone(
            refusal,
            "a pair whose arms declare two counterfactual members and differ on `backend` "
            "differs on two axes, and such a pair is refused by name (counterfactual.md §6, "
            "rules.md §8, D-3): it was reported as %r" % (refusal,),
        )
        for axis_name in ("backend", "counterfactual"):
            self.assertIn(
                R.tok(axis_name), R.tok(refusal),
                "the refusal names both axes the pair differs on — %r among them — so a "
                "reader can see which comparison the pair was not (rules.md §8, "
                "counterfactual.md §6): %r" % (axis_name, refusal),
            )


if __name__ == "__main__":
    unittest.main()
