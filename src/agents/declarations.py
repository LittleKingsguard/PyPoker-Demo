"""The one catalogue: `BACKENDS`, `ARCHITECTURES`, `HYPER`, `LEARNING_RULE`, `KINDS`.

`learners()` publishes these and nothing is restated elsewhere (`README.md` §5,
`surface.md` §3): the two backends in `numpy` then `torch` order (D-7), the seven kinds
in `architecture.md` §1's order with the family and the declared size each is sized
from, the one learning rule (ASM-7), and the rule's six fixed declarations
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

#: The one value, for the whole ladder (ASM-7).
LEARNING_RULE = "masked-q-learning"

#: The rule's six fixed declarations (`rule.md` §6): one value each, never a
#: per-learner argument.
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
    """`learners()`'s record: four keys in order, plain data, rebuilt per call."""
    return {
        "backends": {name: {"name": name} for name in BACKENDS},
        "architectures": {kind: dict(entry) for kind, entry in ARCHITECTURES.items()},
        "learning_rule": LEARNING_RULE,
        "hyper": hyper_record(),
    }
