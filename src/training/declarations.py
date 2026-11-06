"""The ladder as data: six rows, one shape (D-3, ladder.md §2, §3).

There is one rollout driver, one encoder factory, one learner family, one loop and one
league; a rung is a row of this file, so no rung can drift into its own copy of the loop
and a seventh configuration runs without new code (ladder.md §1, FAM-15). Nothing here
computes: it is data a resolver reads and a fairness report quotes.
"""

from . import errors

#: The seed set of protocol.md §2, fixed at `0, 1, 2` and recorded in every run record.
SEEDS = (0, 1, 2)

#: Hands per variant per seed, live (ladder.md §6, ASM-8); the shipped run is 200,000.
LIVE_BUDGET = 1000

#: Snapshots a run writes, at equal intervals (ASM-18, ladder.md §6).
SNAPSHOTS = 10

#: Of the ten snapshots, how many the pool's window retains (ASM-18, league.md §2).
RETAINED = 5

#: The pool's bound M, which no declaration may exceed (league.md §2, ASM-14).
LEAGUE_M = 5

#: The declared parameter budget of a comparison pair, and its ±2% bound (ASM-10).
PARAM_BUDGET = 10000
PARAM_TOLERANCE = 0.02

#: The table budget a variant's row is measured at when a configuration declares none.
TABLE = "live"
TABLE_BUDGETS = ("live", "full")

#: The device a run uses when none is named (D-8, protocol.md §6).
DEVICE = "cpu"

#: The one learning rule of the whole ladder (ASM-7, agents/surface.md §3).
LEARNING_RULE = "masked-q-learning"

#: `agents.learners()["hyper"]`'s declarations, quoted so a fairness report can name the
#: hyperparameters a pair holds constant (ladder.md §4, docs/L3/agents/rule.md §6).
HYPER = {
    "learning_rate": 0.001,
    "batch_size": 32,
    "target_update_interval": 200,
    "optimiser": "sgd",
    "exploration": {"start": 1.0, "end": 0.05, "samples": 2000},
    "discount": 0.99,
}

#: The declared vocabularies an entry is checked against: `agents.learners()`'s two
#: backends and seven kinds, and `features.encodings()`'s two encodings (D-3, D-7).
BACKENDS = ("numpy", "torch")
KINDS = (
    "naive-stack",
    "token-embedding",
    "wide",
    "deep",
    "sparse",
    "residual",
    "plain",
)
ENCODINGS = ("flat-numeric", "card-tokens")

#: The representation family each encoding carries, and the family each kind consumes.
#: The two are one correspondence in this project (D-3, docs/L3/agents/architecture.md §1).
FAMILY = {
    "flat-numeric": "dense-numeric",
    "card-tokens": "token-sequence",
}
KIND_FAMILY = {
    "naive-stack": "dense-numeric",
    "token-embedding": "token-sequence",
    "wide": "token-sequence",
    "deep": "token-sequence",
    "sparse": "token-sequence",
    "residual": "token-sequence",
    "plain": "token-sequence",
}

#: The five axes a comparison is read on (`docs/L2/training/surface.md` §5).
AXES = ("backend", "encoding", "architecture", "connectivity", "residual")

#: The three pinned baselines, in `agents.baselines()`'s order (D-6, ASM-16).
BASELINES = ("random", "always-call", "oracle")


def _architecture(kind, width, depth, sparsity=0.0, residual=False):
    """One architecture record: the kind and the four settings (records.md §2)."""
    return {
        "kind": kind,
        "width": int(width),
        "depth": int(depth),
        "sparsity": float(sparsity),
        "residual": bool(residual),
    }


def _variant(name, backend, encoding, architecture):
    """One variant entry of a rung configuration (records.md §2, ladder.md §3).

    The rule and its hyperparameters, the budgets, the seed set, the device, the
    snapshot interval and the table budget are one declaration for the whole ladder, so
    two arms of a pair quote the same values and no rung carries a second copy (ASM-7,
    ASM-8, ASM-10).
    """
    return {
        "name": name,
        "backend": backend,
        "encoding": encoding,
        "architecture": architecture,
        "learning_rule": LEARNING_RULE,
        "hyper": {
            key: (dict(value) if isinstance(value, dict) else value)
            for key, value in HYPER.items()
        },
        "param_budget": PARAM_BUDGET,
        "samples": LIVE_BUDGET,
        "seeds": list(SEEDS),
        "device": DEVICE,
        "snapshot_every": LIVE_BUDGET // SNAPSHOTS,
        "table": TABLE,
    }


#: The six rows, in brief §2's fixed order (D-2, D-3, ladder.md §2). `lineage` names the
#: rung whose retained window this rung's pool is built from, and `None` for R1, which
#: inherits nothing: its pool is the three baselines alone (league.md §2, ASM-16).
RUNGS = (
    {
        "name": "R1",
        "axis": "encoding — a naive numeric encoding, hand-rolled NumPy (D-7)",
        "carried_from": None,
        "primary": "naive-numeric",
        "lineage": None,
        "variants": (
            _variant(
                "naive-numeric",
                "numpy",
                "flat-numeric",
                _architecture("naive-stack", 36, 2),
            ),
        ),
    },
    {
        "name": "R2",
        "axis": "backend — the same model in PyTorch, for the speed difference (D-7)",
        "carried_from": "naive-numeric",
        "primary": "naive-numeric-torch",
        "lineage": "R1",
        "variants": (
            _variant(
                "naive-numeric-torch",
                "torch",
                "flat-numeric",
                _architecture("naive-stack", 36, 2),
            ),
        ),
    },
    {
        "name": "R3",
        "axis": "tokenisation — card tokenisation into a learned embedding",
        "carried_from": "naive-numeric-torch",
        "primary": "card-tokens",
        "lineage": "R2",
        "variants": (
            _variant(
                "card-tokens",
                "torch",
                "card-tokens",
                _architecture("token-embedding", 50, 2),
            ),
        ),
    },
    {
        "name": "R4",
        "axis": "width against depth, at one budget",
        "carried_from": "card-tokens",
        "primary": "deep",
        "lineage": "R3",
        "variants": (
            _variant("wide", "torch", "card-tokens",
                     _architecture("wide", 62, 1)),
            _variant("deep", "torch", "card-tokens",
                     _architecture("deep", 50, 2)),
        ),
    },
    {
        "name": "R5",
        "axis": "dense against sparse connectivity, at one budget",
        "carried_from": "deep",
        "primary": "dense",
        "lineage": "R4",
        "variants": (
            _variant("dense", "torch", "card-tokens",
                     _architecture("deep", 50, 2)),
            _variant("sparse", "torch", "card-tokens",
                     _architecture("sparse", 62, 2, sparsity=0.5)),
        ),
    },
    {
        "name": "R6",
        "axis": "residual — a residual path against none, at R5's depth",
        "carried_from": "dense",
        "primary": "residual",
        "lineage": "R5",
        "variants": (
            _variant("residual", "torch", "card-tokens",
                     _architecture("residual", 50, 2, residual=True)),
            _variant("plain", "torch", "card-tokens",
                     _architecture("plain", 50, 2)),
        ),
    },
)

#: The registry by name, in `RUNGS`'s order: one read, one order (D-2, `rungs()`).
RUNG_NAMES = tuple(row["name"] for row in RUNGS)
ROWS = {row["name"]: row for row in RUNGS}


def check_variant(entry, where):
    """Refuse a variant entry this module's declared vocabularies do not carry.

    `where` names the configuration the entry belongs to, so the refusal says which entry
    declared what (`surface.md` §4.2, D-3, D-7, docs/L3/training/errors.md §3).
    """
    if not isinstance(entry, dict):
        raise errors.VariantSettingInvalid(
            "training.run refused a variant entry of %r: a variant entry is a mapping, and "
            "this one is %r" % (where, entry)
        )
    backend = entry.get("backend")
    if backend not in BACKENDS:
        raise errors.VariantSettingInvalid(
            "training.run refused the variant %r: 'backend' is %r, and the declared backends "
            "are %s" % (entry.get("name"), backend, ", ".join(BACKENDS))
        )
    encoding = entry.get("encoding")
    if encoding not in ENCODINGS:
        raise errors.VariantSettingInvalid(
            "training.run refused the variant %r: 'encoding' is %r, and the declared "
            "encodings are %s" % (entry.get("name"), encoding, ", ".join(ENCODINGS))
        )
    architecture = entry.get("architecture")
    if not isinstance(architecture, dict):
        raise errors.VariantSettingInvalid(
            "training.run refused the variant %r: 'architecture' is %r, and it is a mapping "
            "of a kind and its settings" % (entry.get("name"), architecture)
        )
    kind = architecture.get("kind")
    if kind not in KINDS:
        raise errors.VariantSettingInvalid(
            "training.run refused the variant %r: 'architecture.kind' is %r, and the declared "
            "kinds are %s" % (entry.get("name"), kind, ", ".join(KINDS))
        )
    if KIND_FAMILY[kind] != FAMILY[encoding]:
        raise errors.VariantSettingInvalid(
            "training.run refused the variant %r: it pairs the encoding %r (%s) with the kind "
            "%r (%s)" % (entry.get("name"), encoding, FAMILY[encoding], kind, KIND_FAMILY[kind])
        )
    for setting in ("width", "depth"):
        value = architecture.get(setting)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise errors.VariantSettingInvalid(
                "training.run refused the variant %r: 'architecture.%s' is %r, and a width or "
                "a depth is a positive integer" % (entry.get("name"), setting, value)
            )
    sparsity = architecture.get("sparsity", 0.0)
    if not isinstance(sparsity, (int, float)) or isinstance(sparsity, bool):
        raise errors.VariantSettingInvalid(
            "training.run refused the variant %r: 'architecture.sparsity' is %r, which is "
            "outside [0, 1]" % (entry.get("name"), sparsity)
        )
    if not 0.0 <= float(sparsity) <= 1.0:
        raise errors.VariantSettingInvalid(
            "training.run refused the variant %r: 'architecture.sparsity' is %r, which is "
            "outside [0, 1]" % (entry.get("name"), sparsity)
        )
