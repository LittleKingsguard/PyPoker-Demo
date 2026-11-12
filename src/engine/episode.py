"""`play_hand`: one whole hand as a record (docs/L3/engine/episode.md).

The policy protocol is a callable taking `(readout, legal)` and returning one member
of `legal`; the engine knows no builder by name, does not inspect the policy, and
lets the policy's own exception propagate unchanged (episode.md §1, §4, G8).  One
hand is in flight and no re-entry: `play_hand` deals through `new_hand` and seeds
nothing itself (episode.md §2, D-16).

The **seating** is the shape's.  A shape with more than two seats seats more than two
policies, so the seating is an optional `seats` argument — the shape's whole seating,
in seat order — and its absence is exactly the two positional policies this entry
point has always played (seats.md §4, e2e-surface.md §3.1).  A seating of the wrong
length, or one handed beside two positional policies, is refused by name and never
truncated or padded (seats.md §4, errors.md §2).

The record's post-hand facts are D-43's and are resolved after the hand, never inside a
decision: each decision carries `amounts`, the raise-to every legal descriptor resolves
to there, and a `counterfactual` over exactly its legal descriptors; the episode carries
the `reveal` — the board, whether the hand reached a showdown or a split, and one entry
per seat with its two cards, whether it showed and whether it held the best of the shown
hands (episode.md §5, counterfactual.md §2, §4).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from pokerkit.hands import StandardHighHand

from .actions import apply_action, raise_amount, raise_interval
from .cards import card_spelling, parse_card
from .config import SEAT_COUNT, game_config, require_shape, seat_count
from .errors import InvalidAction, InvalidPolicy, InvalidSeating
from .hand import is_terminal, new_hand, payoffs, player_index, validate_seed
from .readout import readout

#: The two positional policies' argument names, which is what a two-policy refusal names
#: (episode.md §1, surface.md §10).
POSITIONAL = ("seat0_policy", "seat1_policy")


def play_hand(
    seed: int,
    seat0_policy=None,
    seat1_policy=None,
    shape=None,
    seats=None,
) -> dict:
    """One episode: its seed, its decisions and the hand's payoffs (episode.md §3).

    `shape` is optional and absence is the default shape, so today's call plays today's
    hand (surface.md §10, shapes.md §3).  Each decision is created with reward 0; at the
    end each seat's **last** decision takes that seat's net chip delta and every other
    decision stays 0, so a hand carries at most one non-zero reward per seat and it is
    the hand's outcome (episode.md §3, ASM-12, guardrails.md G9).

    With the optional `seats` argument the two positional policies are **absent** and the
    sequence is the shape's whole seating, one policy per seat in seat order, so a
    six-seat hand is six policies of which one is the learner's (seats.md §4).  A call
    naming neither form, a `seats` whose length is not the shape's seat count, and a
    `seats` given beside a positional policy are each refused by name (seats.md §4,
    e2e-surface.md §3.1).

    Each decision carries the three amount facts beside its five:
    `minimum`/`maximum`, the bounds of the legal raise interval at that decision and
    `None` exactly when no raise was legal, and `amount`, the raise-to the engine
    resolved — `None` whenever the chosen descriptor was not a raise (records.md §5,
    sizing.md §2).  `seat` is the readout's own seat fact, so a seat index means the
    same thing in the record as in the facts (records.md §5, seats.md §3).  Each
    decision also carries `amounts`, the raise-to every **legal** descriptor resolves to
    at that decision and `None` at the two bases, so `amount` is `amounts[action]` and
    never a second derivation of it (episode.md §5, sizing.md §2).

    **The cards are captured during the loop, and must be.**  `State._muck_hole_cards`
    **clears** `hole_cards[i]` and sets `statuses[i] = False` (`state.py:2414-2422`,
    reached from `:5711-5740`) for every seat that does not show, and it is reached for a
    folder exactly as for a seat that mucks at showdown — so a finished state is no record
    of who held what and its `statuses` cannot say who folded.  Every seat's two cards are
    therefore read at the **first** decision, and each actor's own street bet before every
    step; the recorded board is the last decision's `board` fact, which is the board as
    dealt up to that decision and is short when the betting closed all-in and the rest of
    the board was dealt in the terminal transition (episode.md §5).  A later reader must
    not "simplify" this back to the finished state.
    """
    validate_seed(seed)
    name = require_shape(shape, "play_hand")
    policies, labels = _seating(name, seat0_policy, seat1_policy, seats)

    hand = new_hand(seed, name)
    count = seat_count(hand._shape)
    decisions = []
    holes = None  # every seat's two cards, captured once, at the first decision
    streets = []  # each actor's own street bet, captured before its step (episode.md §5)
    while not is_terminal(hand):
        facts = readout(hand)
        legal = facts["legal"]
        seat = facts["seat"][0]
        action = policies[seat](facts, legal)
        if action not in legal:
            raise InvalidAction(
                "play_hand(%s): the policy returned %r, which is not legal at this decision"
                % (labels[seat], action)
            )
        bounds = raise_interval(hand)
        amounts = {descriptor: raise_amount(hand, descriptor) for descriptor in legal}
        if holes is None:
            holes = tuple(
                tuple(
                    card_spelling(card)
                    for card in hand._state.hole_cards[player_index(index, count)]
                )
                for index in range(count)
            )
        streets.append(hand._state.bets[player_index(seat, count)])
        decisions.append(
            {
                "seat": facts["seat"],
                "readout": facts,
                "legal": legal,
                "action": action,
                "reward": 0,
                "amount": amounts[action],
                "minimum": None if bounds is None else bounds[0],
                "maximum": None if bounds is None else bounds[1],
                "amounts": amounts,
                "counterfactual": None,
            }
        )
        hand = apply_action(hand, action)

    outcome = payoffs(hand)
    last = {}
    for position, decision in enumerate(decisions):
        last[decision["seat"][0]] = position
    for seat, position in last.items():
        decisions[position]["reward"] = outcome[seat]
    reveal = _reveal(decisions, holes, count)
    try:
        values = _counterfactuals(decisions, streets, reveal, count, name, outcome)
    except Exception:  # a resolution the facts cannot support degrades, never raises
        values = None
    if values is not None:
        for decision, value in zip(decisions, values):
            decision["counterfactual"] = value
    return {"seed": seed, "decisions": decisions, "payoffs": outcome, "reveal": reveal}


def _seating(name: str, seat0_policy, seat1_policy, seats):
    """The policy of every seat in seat order, and the argument name to refuse with.

    The two forms are exclusive: the positional pair is what this entry point has always
    taken, and it is what an absent `seats` still means, so a two-seat caller changes
    nothing (e2e-surface.md §3.1, seats.md §4).  Every refusal happens before the deal, so
    a refused call cannot move the global stream (hand.md §2).
    """
    count = seat_count(name)
    if seats is None:
        for label, policy in zip(POSITIONAL, (seat0_policy, seat1_policy)):
            if not callable(policy):
                raise InvalidPolicy(
                    "play_hand(%s): the policy must be callable, got %s"
                    % (label, type(policy).__name__)
                )
        if count != SEAT_COUNT:
            raise InvalidSeating(
                "play_hand(shape): the shape %r seats %d, so its hand needs %d policies "
                "and the two positional policies seat %d; the seating is the optional "
                "`seats` argument, one policy per seat in seat order (seats.md §4)"
                % (name, count, count, SEAT_COUNT)
            )
        return (seat0_policy, seat1_policy), POSITIONAL
    if seat0_policy is not None or seat1_policy is not None:
        raise InvalidSeating(
            "play_hand(seats): the seating is given, so the two positional policies "
            "seat0_policy and seat1_policy are absent, and one of them was given; the "
            "seating and the positional pair are exclusive (seats.md §4, "
            "e2e-surface.md §3.1)"
        )
    if isinstance(seats, (str, bytes, Mapping)) or not isinstance(seats, Iterable):
        raise InvalidSeating(
            "play_hand(seats): the seating must be an ordered sequence of one policy per "
            "seat, got %s (seats.md §4)" % type(seats).__name__
        )
    ordered = tuple(seats)
    if len(ordered) != count:
        raise InvalidSeating(
            "play_hand(seats): the shape %r seats %d, so the seating must hold %d "
            "policies in seat order, got %d (seats.md §4)" % (name, count, count, len(ordered))
        )
    labels = tuple("seats[%d]" % position for position in range(count))
    for label, policy in zip(labels, ordered):
        if not callable(policy):
            raise InvalidPolicy(
                "play_hand(%s): the policy must be callable, got %s"
                % (label, type(policy).__name__)
            )
    return ordered, labels


def _reveal(decisions: list[dict], holes, seats: int) -> dict:
    """The hand's cards, and who held the best of them (episode.md §5).

    `shown` is "never applied a `fold` descriptor at any of its decisions" and **not**
    `state.statuses`, which reads `False` for a seat that mucks at showdown exactly as for
    a folder (`state.py:2414-2422`); `won` is the seat's own `hole` plus `board` being at
    least as good as **every shown seat's**, compared by the `Hand`'s own `__lt__` so a
    kicker and a tie are visible and `readout.CLASS_OF`'s 0-8 class is never used.  The
    direction of that comparison is the library's and is the one a reader must not flip:
    `StandardHighHand` is not a low hand, so `a < b` is `a.entry < b.entry` and reads
    "`a` is the **weaker** hand" — one pair's entry 2340 is less than a wheel straight's
    5853 — which is why "at least as good as `other`" is `not (best < other)`.  With fewer
    than three board cards no five-card hand exists, so no best hand is searched for and
    every `won` is a plain `False`, never `None` (counterfactual.md §4, records.md §5).
    """
    board = tuple(decisions[-1]["readout"]["board"]) if decisions else ()
    folded = {
        decision["seat"][0] for decision in decisions if decision["action"] == "fold"
    }
    board_cards = [parse_card(spelling) for spelling in board]
    entries = []
    bests = []
    for seat in range(seats):
        hole = tuple(holes[seat]) if holes is not None else ()
        best = None
        if len(board) >= 3:
            try:
                best = StandardHighHand.from_game_or_none(
                    [parse_card(spelling) for spelling in hole], board_cards
                )
            except Exception:  # a best-five search that cannot be taken is no hand
                best = None
        entries.append(
            {"seat": seat, "hole": hole, "shown": seat not in folded, "won": False}
        )
        bests.append(best)

    shown = sum(1 for entry in entries if entry["shown"])
    # `showdown` is the hand's own fact and takes no view of the hands: two or more seats
    # `shown`, and five board cards.  `split` is defined against it, so a board of four
    # cards -- a hand whose last decision closed the betting all-in and then dealt the
    # river -- can never be a split (episode.md §5, records.md §5).
    showdown = bool(shown >= 2 and len(board) == 5)
    shown_bests = [
        best for entry, best in zip(entries, bests) if entry["shown"] and best is not None
    ]
    top = None
    for best in shown_bests:
        if top is None or top < best:
            top = best
    for entry, best in zip(entries, bests):
        entry["won"] = bool(
            best is not None and all(not (best < other) for other in shown_bests)
        )
    return {
        "board": board,
        "showdown": showdown,
        "split": bool(
            showdown
            and top is not None
            and sum(
                1
                for best in shown_bests
                if not (best < top) and not (top < best)
            )
            >= 2
        ),
        "seats": tuple(entries),
    }


def _counterfactuals(
    decisions: list[dict],
    streets: list[int],
    reveal: dict,
    seats: int,
    name: str,
    outcome: dict,
) -> list[dict] | None:
    """Each legal descriptor's whole-hand net chip delta for the acting seat, or `None`.

    `None` at **every** decision of a hand whose `showdown` is false, whose `split` is
    true, or whose pot was built in **levels** — `counterfactual.md` §4's three
    unresolvable cases, and the reveal is what carries the outcome of the first two
    while a share of a split pot would be a second spelling of the engine's odd-chip
    rule.  The third is this function's own **self-check**: `outcome` is the mapping
    `payoffs(hand)` returned for this completed hand, and the arithmetic below is only
    taken when, for **every** seat, the chips that seat took from the pot,
    `outcome[seat] + C_R(seat)`, are exactly `0` or exactly the whole pot `Σ C_R(seat)` —
    which is `Δ` being exactly `-C_R(seat)` or exactly `O(seat)`, the two values the table
    can produce.  A seat paid a **side pot** — an all-in for less, so a seat is paid by
    its eligibility as well as by its rank — satisfies neither, and such a hand carries
    no values rather than wrong ones (`counterfactual.md` §4's last paragraph).

    The arithmetic is that page's and is never re-derived here: `C = s_0 - stacks[s]` and
    `to_call` at the decision, `added(a)` = `0` for `fold`, `to_call` for `check-call` and
    `amounts[a] - own_street_bet` for a raise, `C_R(t)` from the **last** decision's
    `stacks` with the acting seat's own `added` restored, `O` the other seats'
    contributions and `later` the seat's own commitments after the decision — so
    `fold → -C`, a live action on a won **and shown** seat `→ O`, on any other `→ -(C +
    added(a) + later)` (episode.md §5, counterfactual.md §4).  The `shown` conjunct is
    load-bearing: a seat that makes a live decision and then folds on a later street is
    not live at the end, so that decision still ends in a fold and wins nothing, however
    good its cards were.
    """
    if not reveal["showdown"] or reveal["split"]:
        return None
    start = int(game_config(name)["starting_stack"])
    won = {entry["seat"]: entry["won"] for entry in reveal["seats"]}
    shown = {entry["seat"]: entry["shown"] for entry in reveal["seats"]}

    def added(position: int, descriptor: str) -> int:
        """The chips `descriptor` commits at the decision at `position` (§4)."""
        decision = decisions[position]
        if descriptor == "fold":
            return 0
        if descriptor == "check-call":
            return int(decision["readout"]["to_call"])
        return int(decision["amounts"][descriptor]) - int(streets[position])

    last = len(decisions) - 1
    last_stacks = decisions[last]["readout"]["stacks"]
    contributions = [start - int(last_stacks[seat]) for seat in range(seats)]
    contributions[decisions[last]["seat"][0]] += added(last, decisions[last]["action"])

    # The self-check: this hand's own payoffs must be exactly what the `O`-or-zero
    # arithmetic says it paid.  A pot built in levels pays a seat by its eligibility as
    # well as by its rank, so `O` is not what it won and the identity would be false.
    pot = sum(contributions)
    for seat in range(seats):
        if int(outcome[seat]) + contributions[seat] not in (0, pot):
            return None

    values = []
    for position, decision in enumerate(decisions):
        seat = decision["seat"][0]
        chips = start - int(decision["readout"]["stacks"][seat])
        others = sum(contributions[other] for other in range(seats) if other != seat)
        later = contributions[seat] - chips - added(position, decision["action"])
        row = {}
        for descriptor in decision["legal"]:
            if descriptor == "fold":
                row[descriptor] = -chips
            elif won[seat] and shown[seat]:
                row[descriptor] = others
            else:
                row[descriptor] = -(chips + added(position, descriptor) + later)
        values.append(row)
    return values
