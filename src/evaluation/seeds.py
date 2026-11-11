"""The six seed derivations (`docs/L3/evaluation/scheduler.md` §3).

Five are `hashlib.sha256` digests of a fixed payload -- the idiom
`docs/L3/agents/rule.md` §4 uses for a keyed draw -- and the sixth is one modulo, so one
seed and one position give one result on any host, whatever was played before.  Nothing
here seeds or draws from Python's global `random` stream; the one seeding point of the
project is `engine.new_hand` (ASM-2, `protocol.md` §4).

The six function names below are contract for `tests/evaluation/` (`README.md` §4); every
one of them returns a plain `int`, or -- for `_draw_order` -- a tuple of them.
"""

import hashlib

_HAND_TAG = b"pypoker-evaluation/hand/v1"
_CELL_TAG = b"pypoker-evaluation/cell/v1"
_MEMBER_TAG = b"pypoker-evaluation/member/v1"
_BOOTSTRAP_TAG = b"pypoker-evaluation/bootstrap/v1"
_DRAW_TAG = b"pypoker-evaluation/draw/v1"

_SEPARATOR = b"\x1f"
_MODULUS = 2 ** 31


def _seed(tag, *parts):
    """`int.from_bytes(sha256(tag \\x1f part \\x1f ...).digest()[:8], "big") % 2**31`.

    The tag and the parts are joined by ``\\x1f`` with none trailing, each part written
    as ``str(part)`` in UTF-8 (`scheduler.md` §3).  A ``seed + i``, a
    ``random.Random(seed)``, a counter or a path digest is not this derivation and is
    red (`guardrails.md` G8).
    """
    payload = tag + _SEPARATOR + _SEPARATOR.join(
        str(part).encode("utf-8") for part in parts
    )
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % _MODULUS


def _hand_seed(seed, index):
    """The seed of one hand of a cell: the cell's seed and the hand's index (§3)."""
    return _seed(_HAND_TAG, seed, index)


def _cell_seed(table_seed, i, j):
    """One cell's own seed: the table seed and the pair's membership positions (§3)."""
    return _seed(_CELL_TAG, table_seed, i, j)


def _member_seed(table_seed, position):
    """One of the three baselines' policy seeds: the table seed and its position (§3)."""
    return _seed(_MEMBER_TAG, table_seed, position)


def _bootstrap_seed(table_seed):
    """The rating's bootstrap seed: the table seed alone (§3, `rating.md` §4)."""
    return _seed(_BOOTSTRAP_TAG, table_seed)


def _draw_index(seed, n):
    """`seed % n` -- the seed's position in the membership's order, not a digest (§3).

    Arithmetic on the membership's size, so one seed draws one member every time; it
    does not make distinct seeds distinct members (`pool.md` §7).  This is the **one**
    opponent a training hand faces, and it is unchanged by the counted draw beside it
    (`seats.md` §4, ASM-43).
    """
    return int(seed) % int(n)


def _draw_order(seed, n):
    """The membership's positions in one **counted** draw's order -- `n` distinct positions.

    The first position is `_draw_index(seed, n)`, so a draw of one is the opponent the
    uncounted draw names; the rest follow it in the ascending order of
    ``_seed(_DRAW_TAG, seed, position)``, ties broken by position, so the order is a
    function of the seed and the membership's **own order** and of nothing else -- two
    calls at one seed over one pool agree, and two pools of one membership listed in two
    orders draw in two orders (`seats.md` §4, `league.md` §2, ASM-43, ASM-2).  Without
    replacement: the returned positions are a permutation of ``0 .. n-1``, so a six-seat
    hand never seats one member twice (`league.md` §2, ASM-43).
    """
    size = int(n)
    first = _draw_index(seed, size)
    rest = [position for position in range(size) if position != first]
    rest.sort(key=lambda position: (_seed(_DRAW_TAG, seed, position), position))
    return (first,) + tuple(rest)
