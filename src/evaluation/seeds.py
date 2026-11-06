"""The five seed derivations (`docs/L3/evaluation/scheduler.md` §3).

Four are `hashlib.sha256` digests of a fixed payload -- the idiom
`docs/L3/agents/rule.md` §4 uses for a keyed draw -- and the fifth is one modulo, so one
seed and one position give one result on any host, whatever was played before.  Nothing
here seeds or draws from Python's global `random` stream; the one seeding point of the
project is `engine.new_hand` (ASM-2, `protocol.md` §4).

The four function names below and `_seed` are contract for `tests/evaluation/`
(`README.md` §4); every one of them returns a plain `int`.
"""

import hashlib

_HAND_TAG = b"pypoker-evaluation/hand/v1"
_CELL_TAG = b"pypoker-evaluation/cell/v1"
_MEMBER_TAG = b"pypoker-evaluation/member/v1"
_BOOTSTRAP_TAG = b"pypoker-evaluation/bootstrap/v1"

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
    does not make distinct seeds distinct members (`pool.md` §7).
    """
    return int(seed) % int(n)
