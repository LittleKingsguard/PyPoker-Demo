"""The scheduler: one cell at a time (`docs/L3/evaluation/scheduler.md` §1-§4).

A cell is one unordered pair of members, played at one hand count and on **one shape**,
reported in both directions (`league.md` §2, `shape.md` §4).  The i-th hand is dealt at a
seed derived from the cell's seed and the index alone, so one pair, one hand count and one
seed give one cell however much was played before it.  Seats alternate hand by hand, and a
cell costs its hand count and not twice it: the two directions are the same hands seen from
each seat.

`match(left, right, hands, seed)`'s signature is unchanged -- **there is no shape
argument**: the cell is played on the one shape its two sides name, the default when
neither names one, and two distinct named shapes are `ShapeMismatch` naming both sides and
both shapes (`scheduler.md` §1, §5, `shape.md` §3).  The one shape the sides fix is the
shape **every hand of the cell is dealt on**, so `engine.play_hand` is called with it as
its fourth argument (`engine/surface.md` §10, `shape.md` §4): a side that names a shape
answers that shape's vocabulary, and a hand dealt on another would hand it descriptors it
does not own.  A cell on the default shape is dealt with the default shape's own name,
which the engine reads exactly as an absent one, so the numbers such a cell reports do not
move (ASM-6, `shape.md` §2).

Two cells are never interleaved and none runs concurrently -- one global `random` stream
deals every hand and `engine.new_hand` is its single seeding point (ASM-2, D-16).

**`match` refuses a shape with more than two seats**, naming the shape and its seat count:
a cell is a pair and a six-way hand is a placement, so no cell is played on the six-seat
row at all and the seat count comes from `engine.game_config` and never from a literal
(`docs/L1/seats.md` §5, `league.md` §4, D-22, D-33).  The default shape and the two-seat
no-limit shape pass this check untouched, so every cell they produced before it is the
cell they produce after it (`seats.md` §5, D-33).
"""

import engine

from .declarations import DEFAULT_SHAPE, require_pairwise
from .errors import InvalidHandCount, InvalidSeed, SameMemberPair, ShapeMismatch
from .policy import _is_int, _side
from .seeds import _hand_seed


def _cell_shape(left, right, entry="match"):
    """The one shape a cell is played on, from the two shapes its sides name (§5).

    A side names its shape at ``side[6]``: a version its container's, a `_MemberPolicy`
    its own, an opaque callable whatever its ``game`` says, and a **baseline none** -- a
    baseline is shape-silent, because `agents.build_baseline` takes a name and a seed and
    no shape (`shape.md` §4).  So a cell between two shape-silent sides is played on
    `DEFAULT_SHAPE` with exactly the numbers it had before the shape existed, a baseline
    opposite a version on that version's shape, and a pair of two named shapes is refused
    naming both sides and both shapes: a cell is played on one game (`shape.md` §3, §6).
    """
    left_game = left[6]
    right_game = right[6]
    if left_game is None and right_game is None:
        return DEFAULT_SHAPE
    if left_game is None:
        return right_game
    if right_game is None:
        return left_game
    if left_game != right_game:
        raise ShapeMismatch(
            "%s(left, right): the sides record the shapes %r and %r, and a cell is played "
            "on one shape" % (entry, left_game, right_game)
        )
    return left_game


def match(left, right, hands, seed):
    """One `records.md` §9 cell: two policies or two members, a hand count and a seed.

    Its `members` are the two ids in argument order, its `directions` are position-aligned
    with them, its `params` carries one integer per member with the unmeasured zeros named
    in `unlabelled`, its `rules` and `utilities` name each member's rule and utility, and
    its `game` names the one shape the hands were played on -- this module's own key, which
    two shape-silent sides carry as the default (`surface.md` §9, `scheduler.md` §4-§5,
    `shape.md` §4).
    """
    if not _is_int(hands) or int(hands) < 1:
        raise InvalidHandCount(
            "match(hands): the hand count must be a positive integer, got %r" % (hands,)
        )
    if not _is_int(seed):
        raise InvalidSeed("match(seed): the seed must be an integer, got %r" % (seed,))
    left_side = _side(left, "left", "match", seed=seed, position=1)
    right_side = _side(right, "right", "match", seed=seed, position=2)
    if left_side[0] == right_side[0]:
        raise SameMemberPair(
            "match(left, right): the two sides carry one id %r, and a cell pairs two "
            "distinct members" % (left_side[0],)
        )
    # The cell's shape is fixed before a hand is dealt: a pair naming two shapes is
    # refused here and never played (`scheduler.md` §5-§6, `shape.md` §3), and a shape
    # whose seat count is not the instrument's is refused here too -- a cell is a pair, a
    # six-way hand is a placement, and the count is read off `engine.game_config`
    # (`docs/L1/seats.md` §5, `league.md` §4, D-22, D-33).
    game = _cell_shape(left_side, right_side, "match")
    require_pairwise(game, "match", "left, right")
    return _play_cell(left_side, right_side, int(hands), int(seed), game)


def _play_cell(left, right, hands, seed, game=None):
    """One cell played hand after hand, from one seed, with the seats alternating.

    A hand's class is the sign of the member's own net chip delta -- positive is a win,
    negative a loss, zero a tie -- and the two means are exact negations because the hand
    was zero-sum and both are divided by the same `hands` (`scheduler.md` §4, G10).  The
    cell's `rules` and `utilities` name each member's rule and utility by its id, `None`
    for a baseline or an opaque policy that carries neither, and its `game` names the one
    shape the hands were played on (`records.md` §9, `scheduler.md` §4-§5, D-19, D-20,
    `shape.md` §4).  ``game`` is the shape **every hand of the cell is dealt on**, passed to
    `engine.play_hand` as its fourth argument: a table fixes it for every cell of it
    (`matrix.md` §4-§5); left out, the cell resolves the one its two sides name (§5).  Either
    way it is a declared shape's name by the time the first hand is dealt -- the default's
    own name for a cell of two shape-silent sides -- and the engine reads that name exactly
    as it reads an absent one, so a default-shape cell's hands, payoffs and counts are the
    ones it had before the shape existed (ASM-6, `shape.md` §2).
    """
    (
        left_id,
        left_policy,
        left_params,
        left_unlabelled,
        left_rule,
        left_utility,
        _left_game,
    ) = left
    (
        right_id,
        right_policy,
        right_params,
        right_unlabelled,
        right_rule,
        right_utility,
        _right_game,
    ) = right
    if game is None:
        game = _cell_shape(left, right, "match")

    left_wins = left_ties = left_losses = 0
    right_wins = right_ties = right_losses = 0
    left_total = right_total = 0
    left_seat0 = left_seat1 = right_seat0 = right_seat1 = 0

    for index in range(hands):
        hand_seed = _hand_seed(seed, index)
        # Every hand of the cell is dealt on the cell's one shape, from the cell's seed
        # alone: the seat arrangement is the only thing the index moves (`scheduler.md`
        # §1-§3, `shape.md` §4).
        if index % 2 == 0:
            episode = engine.play_hand(
                hand_seed, left_policy, right_policy, shape=game
            )
            left_delta = episode["payoffs"][0]
            right_delta = episode["payoffs"][1]
            left_seat0 += 1
            right_seat1 += 1
        else:
            episode = engine.play_hand(
                hand_seed, right_policy, left_policy, shape=game
            )
            left_delta = episode["payoffs"][1]
            right_delta = episode["payoffs"][0]
            left_seat1 += 1
            right_seat0 += 1

        left_total += left_delta
        right_total += right_delta
        if left_delta > 0:
            left_wins += 1
        elif left_delta < 0:
            left_losses += 1
        else:
            left_ties += 1
        if right_delta > 0:
            right_wins += 1
        elif right_delta < 0:
            right_losses += 1
        else:
            right_ties += 1

    unlabelled = tuple(
        member_id
        for member_id, flag in ((left_id, left_unlabelled), (right_id, right_unlabelled))
        if flag
    )
    return {
        "members": (left_id, right_id),
        "hands": hands,
        "directions": (
            {
                "wins": left_wins,
                "ties": left_ties,
                "losses": left_losses,
                "mean_chip_delta": left_total / hands,
                "seat_split": {"seat 0": left_seat0, "seat 1": left_seat1},
            },
            {
                "wins": right_wins,
                "ties": right_ties,
                "losses": right_losses,
                "mean_chip_delta": right_total / hands,
                "seat_split": {"seat 0": right_seat0, "seat 1": right_seat1},
            },
        ),
        "params": [int(left_params), int(right_params)],
        "rules": {left_id: left_rule, right_id: right_rule},
        "utilities": {left_id: left_utility, right_id: right_utility},
        "seed": seed,
        "unlabelled": unlabelled,
        # This module's own key, beside records.md §9's seven: the one shape the hands
        # were played on, the default for a cell of two shape-silent sides (`shape.md` §4).
        "game": game,
    }
