"""The one catalogue: `BACKENDS`, `ARCHITECTURES`, `LEARNING_RULES`, `UTILITIES`, `HYPER`.

`learners()` publishes these and nothing is restated elsewhere (`README.md` §5,
`surface.md` §3): the two backends in `numpy` then `torch` order (D-7), the seven kinds
in `architecture.md` §1's order with the family and the declared size each is sized
from, the two learning rules in `rules.md` §2's order with the target each aims at
(D-19), the two terminal-reward utilities in `utilities.md` §2's order with the reward
each delivers (D-20), and the six fixed declarations both catalogues share
(`rule.md` §6).  The record is plain data, rebuilt on every call, so no caller can
mutate the catalogue through a returned mapping.
"""

from __future__ import annotations

BACKENDS = ("numpy", "torch")

#: The two representation families a kind consumes (`architecture.md` §1, §6).
DENSE_FAMILY = "dense-numeric"
TOKEN_FAMILY = "token-sequence"

#: The two encoding names a kind's row declares (`architecture.md` §6, `encodings.md` §1).
FLAT_ENCODING = "flat-numeric"
TOKEN_ENCODING = "card-tokens"

#: The seven kinds in `architecture.md` §1's order, each row carrying the family it
#: consumes, the size an encoder-less build is sized from and the encoding its rungs
#: declare.  `KINDS` is the key order of this table, so the two cannot drift.
KIND_ROWS = {
    "naive-stack": {
        "observation": DENSE_FAMILY,
        "observation_size": 203,
        "encoding": FLAT_ENCODING,
    },
    "token-embedding": {
        "observation": TOKEN_FAMILY,
        "observation_size": 96,
        "encoding": TOKEN_ENCODING,
    },
    "wide": {
        "observation": TOKEN_FAMILY,
        "observation_size": 96,
        "encoding": TOKEN_ENCODING,
    },
    "deep": {
        "observation": TOKEN_FAMILY,
        "observation_size": 96,
        "encoding": TOKEN_ENCODING,
    },
    "sparse": {
        "observation": TOKEN_FAMILY,
        "observation_size": 96,
        "encoding": TOKEN_ENCODING,
    },
    "residual": {
        "observation": TOKEN_FAMILY,
        "observation_size": 96,
        "encoding": TOKEN_ENCODING,
    },
    "plain": {
        "observation": TOKEN_FAMILY,
        "observation_size": 96,
        "encoding": TOKEN_ENCODING,
    },
}

KINDS = tuple(KIND_ROWS)

#: Each kind's catalogue value: three keys, `name`, `observation`, `observation_size`,
#: in that order (`surface.md` §3, `architecture.md` §1).
ARCHITECTURES = {
    kind: {
        "name": kind,
        "observation": row["observation"],
        "observation_size": row["observation_size"],
    }
    for kind, row in KIND_ROWS.items()
}

#: The learning-rule catalogue, in the declared order (`rules.md` §2, D-19): each
#: member is a record carrying its `name` and the `target` it aims at, as a stable
#: token and never a sentence.  `masked-q-learning` bootstraps from the masked maximum
#: of the target copy's values; `double-q-learning` lets the online parameters choose
#: the index and reads that index's value from the target copy (`rule.md` §2).
LEARNING_RULES = {
    "masked-q-learning": {
        "name": "masked-q-learning",
        "target": "max-of-target-copy-over-next-legal",
    },
    "double-q-learning": {
        "name": "double-q-learning",
        "target": "target-copy-at-online-argmax-over-next-legal",
    },
}

#: The declared default: the catalogue's **first** member, which is what a learner
#: spec naming none is built under and what a version-1 checkpoint reads as.  It is
#: derived from the order above so the declaration cannot drift (`rules.md` §4, §6).
DEFAULT_LEARNING_RULE = next(iter(LEARNING_RULES))

#: The terminal-reward catalogue, in the declared order (`utilities.md` §2, D-20): each
#: member is a record of exactly three keys -- its `name`, the `reward` it delivers as a
#: stable token and never a sentence, and the `normaliser` that reward is divided by.
#: `net-chips` is the unshaped net chip delta of ASM-12; `stack-shortfall` is the delta
#: of the squared stack shortfall over the chips in play, normalised by the shortfall a
#: hand begins with (`utilities.md` §2, §4).
UTILITIES = {
    "net-chips": {
        "name": "net-chips",
        "reward": "net-chip-delta",
        "normaliser": "none",
    },
    "stack-shortfall": {
        "name": "stack-shortfall",
        "reward": "squared-stack-shortfall-delta",
        "normaliser": "U(s_0)",
    },
}

#: The declared default of the utility axis: the catalogue's **first** member, which is
#: what a learner spec naming none is built under and what a version-1 or version-2
#: checkpoint is read as (`utilities.md` §5, §6, D-20).  Derived from the order above.
DEFAULT_UTILITY = next(iter(UTILITIES))

#: The six fixed declarations both catalogue members consume (`rule.md` §6): one
#: value each, never a per-learner argument and never a per-rule block, so a rule swap
#: is one axis and no budget moves with it (`rules.md` §2, ASM-7).
HYPER = {
    "learning_rate": 0.001,
    "batch_size": 32,
    "target_update_interval": 200,
    "optimiser": "sgd",
    "exploration": {"start": 1.0, "end": 0.05, "samples": 2000},
    "discount": 0.99,
}


def kind_row(kind):
    """The catalogue row of one kind, or a `KeyError` naming it."""
    try:
        return KIND_ROWS[kind]
    except (KeyError, TypeError):
        raise KeyError(
            "agents.declarations: %r is not one of the seven kinds %r" % (kind, KINDS)
        ) from None


def hyper_record():
    """A fresh copy of the six fixed declarations, so a caller cannot mutate them."""
    record = {}
    for key, value in HYPER.items():
        record[key] = dict(value) if isinstance(value, dict) else value
    return record


def catalogue():
    """`learners()`'s record: five keys in order, plain data, rebuilt per call."""
    return {
        "backends": {name: {"name": name} for name in BACKENDS},
        "architectures": {kind: dict(entry) for kind, entry in ARCHITECTURES.items()},
        "learning_rules": {
            name: dict(entry) for name, entry in LEARNING_RULES.items()
        },
        "utilities": {name: dict(entry) for name, entry in UTILITIES.items()},
        "hyper": hyper_record(),
    }
