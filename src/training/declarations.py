"""The ladder as data: six rows, one shape (D-3, ladder.md §2, §3).

There is one rollout driver, one encoder factory, one learner family, one loop and one
league; a rung is a row of this file, so no rung can drift into its own copy of the loop
and a seventh configuration runs without new code (ladder.md §1, FAM-15). Nothing here
computes: it is data a resolver reads and a fairness report quotes.
"""

from collections.abc import Mapping

import agents

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

#: What the six rows below declare: the catalogue's first member (rules.md §2, §4, D-19).
#: Not a rule the run is fixed to — a variant may name another catalogued rule, and
#: `learning_rules()` is how the run learns which names exist.
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

#: The six axes a comparison is read on (`docs/L2/training/surface.md` §5,
#: `docs/L3/training/fairness.md` §2, and D-19, which makes the rule an axis).
AXES = ("backend", "encoding", "architecture", "connectivity", "residual", "rule")

#: The three pinned baselines, in `agents.baselines()`'s order (D-6, ASM-16).
BASELINES = ("random", "always-call", "oracle")

#: The seven settings both arms of one pair declare one value for: `learning_rule` is not
#: one of them, because two arms may declare two catalogue rules and every variant is
#: trained (docs/L2/training/declarations.md §4, rules.md §8, D-19).
PAIR_SETTINGS = (
    "hyper",
    "samples",
    "seeds",
    "device",
    "snapshot_every",
    "table",
    "param_budget",
)


def learning_rules():
    """The catalogue's rule names, in `agents.learners()`'s order (rules.md §2, §4, D-19).

    The one place this module reads the catalogue: `agents.learners()["learning_rules"]` is
    keyed by the catalogue's members in `rules.md` §2's order, so a reader learns which
    rules exist and which one is first — the declared default `agents.build_learner`
    applies to a spec naming none — without a second copy of the names here. Never
    hard-coded, because a private list would be a vocabulary that drifts from its owner's
    (`rules.md` §2, §4, D-19, `agents/surface.md` §3).
    """
    return tuple(agents.learners()["learning_rules"])


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

    A variant declares its own `learning_rule` — these six rows name the catalogue's first
    member, and a variant may name another catalogued rule — while the hyperparameters, the
    budgets, the seed set, the device, the snapshot interval and the table budget stay one
    declaration for the whole ladder, so two arms of a pair quote the same values and no
    rung carries a second copy (rules.md §2, §4, D-19, ASM-7, ASM-8, ASM-10).
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


def check_param_budget_value(declared, where, entry=None):
    """Refuse a declared `param_budget` that is not a positive integer, at either level.

    The `params` block reports the **declared** budget and measures no capacity, so the
    number the record's ±2% band is computed around is the number the configuration
    declared, returned unchanged: a `bool`, a non-integer or a value below one is refused
    here rather than coerced by an `int()` or truncated (ASM-10,
    docs/L2/training/declarations.md §2, docs/L3/training/errors.md §4).
    """
    if isinstance(declared, bool) or not isinstance(declared, int) or declared < 1:
        if entry is not None:
            raise errors.VariantSettingInvalid(
                "training.run refused the variant %r of the configuration %r: "
                "'param_budget' is %r, and a parameter budget is a positive integer, "
                "because the params block reports the declared budget and measures no "
                "capacity (ASM-10)" % (entry, where, declared)
            )
        raise errors.VariantSettingInvalid(
            "training.run refused the configuration %r: 'param_budget' is %r, and a "
            "parameter budget is a positive integer, because the params block reports the "
            "declared budget and measures no capacity (ASM-10)" % (where, declared)
        )
    return declared


def check_param_budget(configuration):
    """Refuse every declared `param_budget` that is not a positive integer (ASM-10).

    The configuration's own declaration is read first, then each entry's in declaration
    order, so a run refuses a number it could not report or band before the pool is built
    and before the first hand is dealt (`docs/L3/training/loop.md` §1 steps 1-2,
    docs/L3/training/errors.md §4). A level that declares none is no claim and is skipped.
    """
    where = configuration.get("name")
    own = configuration.get("param_budget")
    if own is not None:
        check_param_budget_value(own, where)
    for entry in configuration["variants"]:
        if not isinstance(entry, Mapping):
            continue
        declared = entry.get("param_budget")
        if declared is None:
            continue
        check_param_budget_value(declared, where, entry.get("name"))


def _text(value):
    """One declared value as a refusal names it (docs/L3/training/errors.md §3)."""
    return repr(value)


def _declaration(key, value):
    """One declared value in the shape §4's comparison reads it in.

    `seeds` is a set, so a list `[0, 1, 2]` and a tuple `(0, 1, 2)` are one declaration;
    every other setting is compared as it stands (docs/L2/training/declarations.md §4).
    """
    if (
        key == "seeds"
        and not isinstance(value, (str, bytes))
        and hasattr(value, "__iter__")
    ):
        return tuple(value)
    return value


def _same_declaration(key, left, right):
    """Whether two arms declare one value for one setting both of them declare (§4).

    A `hyper` pair differs when a key both blocks name carries two values: a key only one
    block names is no claim, and the nested `exploration` schedule is compared by mapping
    equality, so a sentence written where the schedule is declared is a disagreement and
    not a tolerance (docs/L2/training/declarations.md §2, §4, `agents/surface.md` §3).
    """
    if key == "hyper" and isinstance(left, Mapping) and isinstance(right, Mapping):
        for name, value in left.items():
            if name in right and right[name] != value:
                return False
        return True
    return _declaration(key, left) == _declaration(key, right)


def pair_difference(left, right, keys=PAIR_SETTINGS):
    """The first setting two arms both declare and declare differently, with both values.

    `None` when every setting one arm declares carries the value the other declares too: a
    setting one side leaves absent — or declares as `None` — is no claim and is skipped, so
    only both-declared-and-different is a difference (docs/L2/training/declarations.md §4).
    """
    for key in keys:
        first = left.get(key) if isinstance(left, Mapping) else None
        second = right.get(key) if isinstance(right, Mapping) else None
        if first is None or second is None:
            continue
        if not _same_declaration(key, first, second):
            return key, first, second
    return None


def _declared_samples(configuration, entries):
    """The budget a configuration declares: its own, else its first entry's (§2)."""
    if configuration.get("samples") is not None:
        return configuration["samples"]
    for entry in entries:
        declared = entry.get("samples") if isinstance(entry, Mapping) else None
        if declared is not None:
            return declared
    return None


def _check_hyper(where, configuration, entries):
    """Refuse a `hyper` key a run would not use, at the configuration and at each entry.

    One `HYPER` does not carry the key, or the key carries another value. The module's
    declared hyper is the ladder's one set of hyperparameters, so a block that names
    another value names something the learner is not built from, at either level; a block
    that is not a mapping names no key and is no claim (ASM-7, D-13,
    docs/L2/training/declarations.md §2).
    """
    own = configuration.get("hyper")
    if isinstance(own, Mapping):
        for key, value in own.items():
            if key not in HYPER:
                raise errors.IgnoredDeclaration(
                    "training.run refused the configuration %r: 'hyper' names %r %r "
                    "and the run uses no such declaration, because the module's declared "
                    "hyper is fixed for the whole ladder and carries %s — vary it in "
                    "src/training/declarations.py (ASM-7)"
                    % (where, key, value, ", ".join(HYPER))
                )
            if value != HYPER[key]:
                raise errors.IgnoredDeclaration(
                    "training.run refused the configuration %r: 'hyper' names %r %r "
                    "and the run uses %r, because the module's declared hyper is fixed "
                    "for the whole ladder — vary it in src/training/declarations.py "
                    "(ASM-7)" % (where, key, value, HYPER[key])
                )
    for entry in entries:
        block = entry.get("hyper") if isinstance(entry, Mapping) else None
        if not isinstance(block, Mapping):
            continue
        for key, value in block.items():
            if key not in HYPER:
                raise errors.IgnoredDeclaration(
                    "training.run refused the variant %r of the configuration %r: 'hyper' "
                    "names %r %r and the run uses no such declaration, because the "
                    "module's declared hyper is fixed for the whole ladder and carries "
                    "%s — vary it in src/training/declarations.py (ASM-7)"
                    % (entry.get("name"), where, key, value, ", ".join(HYPER))
                )
            if value != HYPER[key]:
                raise errors.IgnoredDeclaration(
                    "training.run refused the variant %r of the configuration %r: 'hyper' "
                    "names %r %r and the run uses %r, because the module's declared hyper "
                    "is fixed for the whole ladder — vary it in src/training/declarations.py "
                    "(ASM-7)" % (entry.get("name"), where, key, value, HYPER[key])
                )


def _check_learning_rule(where, configuration, entries):
    """Refuse a `learning_rule` the catalogue does not carry, at either level (D-19).

    The catalogue `agents.learners()` publishes — read once through `learning_rules()` — is
    the whole vocabulary a rule is judged against, at the configuration first and then at
    each entry. A declared name no member carries, or a name that is not a string, is a
    rule no learner can be built under; a **second catalogued** rule is read, forwarded and
    trained, so what is refused here is an uncatalogued name and never a rule the run is
    not fixed to. A level that declares no rule — or declares `None` — is no claim and is
    accepted (rules.md §2, §4, D-19, docs/L2/training/declarations.md §2).
    """
    catalogue = learning_rules()
    own = configuration.get("learning_rule")
    if own is not None and own not in catalogue:
        raise errors.IgnoredDeclaration(
            "training.run refused the configuration %r: 'learning_rule' is %r, and the "
            "catalogue agents.learners() publishes (src/agents/declarations.py) carries "
            "%s — name one of those, or name none for the catalogue's first "
            "(rules.md §2, §4, D-19)" % (where, own, ", ".join(catalogue))
        )
    for entry in entries:
        rule = entry.get("learning_rule") if isinstance(entry, Mapping) else None
        if rule is None or rule in catalogue:
            continue
        raise errors.IgnoredDeclaration(
            "training.run refused the variant %r of the configuration %r: 'learning_rule' "
            "is %r, and the catalogue agents.learners() publishes (src/agents/"
            "declarations.py) carries %s — name one of those, or name none for the "
            "catalogue's first (rules.md §2, §4, D-19)"
            % (entry.get("name"), where, rule, ", ".join(catalogue))
        )


def _check_snapshot_every(configuration, where, entries):
    """Refuse a `snapshot_every`, at either level, that is not the declared samples ÷ 10.

    ASM-18 holds ten equally spaced snapshots at the declared budget, so an interval that
    is not `max(1, samples // SNAPSHOTS)` would write fewer than ten. The check is judged
    against the **declared** samples and never against the budget a caller passed, so a
    caller overriding `budget` trips nothing; a configuration declaring no samples at all
    is left to the budget's own refusal (docs/L2/training/declarations.md §2,
    docs/L3/training/loop.md §2, ASM-18).
    """
    declared = _declared_samples(configuration, entries)
    if declared is None:
        return
    if isinstance(declared, bool) or not isinstance(declared, int) or declared < 1:
        return
    expected = max(1, declared // SNAPSHOTS)
    own = configuration.get("snapshot_every")
    if own is not None and own != expected:
        raise errors.IgnoredDeclaration(
            "training.run refused the configuration %r: 'snapshot_every' is %r, and the "
            "run uses the interval the declared %d samples fix, %d, because ASM-18 holds "
            "ten equally spaced snapshots — vary it in src/training/declarations.py "
            "(ASM-18)" % (where, own, declared, expected)
        )
    for entry in entries:
        own = entry.get("snapshot_every") if isinstance(entry, Mapping) else None
        if own is None or own == expected:
            continue
        raise errors.IgnoredDeclaration(
            "training.run refused the variant %r of the configuration %r: "
            "'snapshot_every' is %r, and the run uses the interval the declared %d "
            "samples fix, %d, because ASM-18 holds ten equally spaced snapshots — "
            "vary it in src/training/declarations.py (ASM-18)"
            % (entry.get("name"), where, own, declared, expected)
        )


def check_declarations(configuration):
    """Refuse every declaration a run would not use, before the pool is built.

    One place for the rule `docs/L2/training/declarations.md` §2–§4 states: a `hyper` key
    that is unknown or disagrees with `HYPER`, and a `learning_rule` the catalogue
    `agents.learners()` publishes does not carry — each **at the configuration and at each
    entry** — and a `snapshot_every` at either level that is not the declared samples ÷ 10,
    plus, for a two-entry configuration, the seven settings both arms must share. Every
    refusal is raised before the first hand is dealt and before anything is written
    (ASM-7, ASM-8, ASM-18, docs/L3/training/loop.md §1 step 1).
    """
    where = configuration.get("name")
    entries = list(configuration["variants"])
    _check_hyper(where, configuration, entries)
    _check_learning_rule(where, configuration, entries)
    _check_snapshot_every(configuration, where, entries)
    if len(entries) != 2:
        return
    difference = pair_difference(entries[0], entries[1])
    if difference is None:
        return
    key, first, second = difference
    raise errors.PairDeclarationsDiffer(
        "training.run refused the configuration %r: its two variants %r and %r declare "
        "two %r values, %s and %s, and both arms of a pair are trained at one value "
        "(ASM-8)"
        % (
            where,
            entries[0].get("name"),
            entries[1].get("name"),
            key,
            _text(first),
            _text(second),
        )
    )
