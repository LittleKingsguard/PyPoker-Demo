"""The seed derivations: hand *i*'s deal seed and opponent seed (protocol.md §4, ASM-2).

Hand *i*'s deal seed and its opponent seed are functions of the run seed and *i* alone,
so both arms of a comparison pair play the same hands in the same order against the same
opponents and differ only on their declared axis (docs/L2/training/loop.md §3, ASM-8,
D-7). A derivation draws from no stream, so `training` never seeds or advances Python's
global `random`: every deal goes through `engine.play_hand`, the project's one seeding
point (engine/surface.md §1, §4).
"""

import hashlib

_PREFIX = b"pypoker-training/"
_SUFFIX = b"/v1"
_SEPARATOR = b"\x1f"
_CEILING = 2 ** 63


def _derive(domain, seed, index):
    """One derived seed: `sha256` of a fixed `(domain, seed, index)` payload, reduced.

    The domain is `b"deal"` or `b"opponent"`, so the two chains never coincide, and the run
    seed is in the payload, so two runs never share a hand (`docs/L3/training/seeds.md` §2).
    """
    domain = domain if isinstance(domain, bytes) else str(domain).encode("ascii")
    payload = (
        _PREFIX
        + domain
        + _SUFFIX
        + _SEPARATOR
        + str(int(seed)).encode("ascii")
        + _SEPARATOR
        + str(int(index)).encode("ascii")
    )
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big") % _CEILING


def _deal_seed(seed, index):
    """The deal seed of hand `index` of the run trained at `seed`."""
    return _derive(b"deal", seed, index)


def _opponent_seed(seed, index):
    """The seed `evaluation.opponent` draws hand `index`'s opponent with."""
    return _derive(b"opponent", seed, index)
