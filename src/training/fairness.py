"""What a comparison pair holds constant, and the one axis on which it differs (D-3, D-6).

`fairness` reports; it never asserts that a pair is fair, because a pair that differs on
more than one axis is refused and never gets that far. It plays no hand, builds no learner,
writes nothing and moves no stream (`docs/L2/training/surface.md` §5).

**The one rule that is this design's own.** The seven axes are `backend`, `encoding`,
`architecture` (width and depth), `connectivity` (sparsity), `residual`, `rule` (the rule a
variant is trained under) and `utility` (the reward its training target carries). A pair
compares `architecture` only when its two sides agree on the representation family *and* on
`sparsity`: where they differ, the width is the capacity match's compensation — ASM-10
requires a `sparse` arm to be declared wider than its dense mate, and a token encoding to
sit at a different width than a dense one — so it belongs to the `encoding` or the
`connectivity` axis and is never counted a second time (`docs/L3/training/fairness.md`
§2, `utilities.md` §8, D-20).
"""

from collections.abc import Mapping

import agents
import engine

from . import declarations, errors

#: The eleven readout facts, declared here because `engine.readout` is not a granted
#: call.  `hand_class` is D-21's derived fact (ASM-30): a fact of the information set that
#: no encoding carries, so it is declared here and not in `features`' `fields`.
READOUT_FACTS = (
    "street",
    "seat",
    "hole",
    "board",
    "stacks",
    "pot",
    "to_call",
    "limit",
    "history",
    "legal",
    "hand_class",
)


def _sides(left, right):
    """Classify both sides: `(kind, left, right)`, refusing anything that is not a side."""
    classified = []
    for value in (left, right):
        if isinstance(value, Mapping) and "variants" in value:
            classified.append(("configuration", value))
        elif isinstance(value, Mapping) and "architecture" in value:
            classified.append(("entry", value))
        else:
            raise errors.NotAComparisonSide(
                "training.fairness refused %r: a side is a configuration (carrying "
                "'variants') or a variant entry (carrying 'architecture')" % (value,)
            )
    (left_kind, left_value), (right_kind, right_value) = classified
    if left_kind != right_kind:
        raise errors.SideKindMismatch(
            "training.fairness refused the pair: the left side is a %s and the right is a "
            "%s, and two sides of one pair are the same kind" % (left_kind, right_kind)
        )
    return left_kind, left_value, right_value


def _require(side, keys, where):
    """Refuse a side that carries no key the comparison reads, naming the key.

    A comparison reads its two entries' `architecture`, `backend` and `encoding`, and a
    configuration's `variants` and `pool` (`docs/L3/training/fairness.md` §6, surface.md
    §5). A missing key is named and never defaulted: a side is not repaired into one.
    """
    for key in keys:
        if key not in side:
            raise errors.ComparisonKeyMissing(
                "training.fairness refused the pair: %s carries no %r key, which the "
                "comparison reads" % (where, key)
            )


def _entries(configuration):
    """The variant entries of a resolved configuration, in declaration order."""
    variants = configuration["variants"]
    if isinstance(variants, (str, bytes)) or not isinstance(variants, (list, tuple)):
        raise errors.ComparisonKeyMissing(
            "training.fairness refused the pair: the configuration %r carries a 'variants' "
            "key that is not a sequence of entries, which the comparison reads"
            % (configuration.get("name"),)
        )
    for position, entry in enumerate(variants):
        if not isinstance(entry, Mapping):
            raise errors.ComparisonKeyMissing(
                "training.fairness refused the pair: the configuration %r carries a variant "
                "entry %d that is not a mapping" % (configuration.get("name"), position)
            )
    return list(variants)


def _primary(configuration):
    """The variant entry a configuration names as its primary — the lineage it inherits."""
    entries = _entries(configuration)
    primary = configuration.get("primary")
    if primary is None:
        return entries[0]
    for entry in entries:
        if entry.get("name") == primary:
            return entry
    raise errors.ComparisonKeyMissing(
        "training.fairness refused the pair: the configuration %r declares the primary %r "
        "and carries no such entry" % (configuration.get("name"), primary)
    )


def _architecture(entry):
    value = entry.get("architecture")
    if not isinstance(value, Mapping):
        raise errors.ComparisonKeyMissing(
            "training.fairness refused the pair: the variant %r carries no 'architecture' "
            "key, which the comparison reads" % (entry.get("name"),)
        )
    return value


def _family(entry):
    """The representation family an entry's kind consumes, or its encoding's family."""
    kind = _architecture(entry).get("kind")
    if kind in declarations.KIND_FAMILY:
        return declarations.KIND_FAMILY[kind]
    return declarations.FAMILY.get(entry.get("encoding"))


def _setting(entry, key, default=None):
    value = _architecture(entry).get(key)
    return default if value is None else value


def _rule(entry, configuration=None):
    """The rule a side is trained under: its own, else its configuration's, else the first.

    A side that declares no `learning_rule` is trained under the catalogue's **first**
    member, the declared default `agents.build_learner` applies to a spec naming none, so
    the rule is resolved through `declarations.learning_rules()` rather than compared as a
    raw key: a side spelling the default out and a side leaving it unsaid are one rule and
    never a phantom difference (`rules.md` §4, D-19, `fairness.md` §2, §7).
    """
    declared = entry.get("learning_rule") if isinstance(entry, Mapping) else None
    if declared is None and isinstance(configuration, Mapping):
        declared = configuration.get("learning_rule")
    if declared is not None:
        return declared
    return declarations.learning_rules()[0]


def _utility(entry, configuration=None):
    """The utility a side is trained on: its own, else its configuration's, else the first.

    The utility side of :func:`_rule`, on the same terms: a side that declares no
    `utility` is trained on the catalogue's **first** member's reward, the declared default
    of `utilities.md` §5, so it is resolved through `declarations.utilities()` and a side
    spelling the default out and a side leaving it unsaid are one utility and never a
    phantom difference (`utilities.md` §5, §8, D-20, `fairness.md` §2, §7).
    """
    declared = entry.get("utility") if isinstance(entry, Mapping) else None
    if declared is None and isinstance(configuration, Mapping):
        declared = configuration.get("utility")
    if declared is not None:
        return declared
    return declarations.utilities()[0]


def _shape(entry, configuration=None):
    """The shape a side names: its own, else its configuration's, else the default.

    A pair is compared on **one** shape, so the shape is resolved on the same terms the
    rule and the utility are — the entry's declaration first, its configuration's second —
    and a side that names none is on the catalogue's first row, because absence is the
    default shape and never "no claim" (`declarations.require_game`, `shapes.md` §3,
    D-29).  A name the catalogue does not carry is refused here, naming it and the declared
    names, and is never defaulted.
    """
    declared = entry.get("game") if isinstance(entry, Mapping) else None
    if declared is None and isinstance(configuration, Mapping):
        declared = configuration.get("game")
    return declarations.require_game(declared, "training.fairness", "game")


def _pair_shapes(left, right):
    """The one shape a pair is on, or the refusal naming both — a pair is one shape's.

    A shape is a property of a configuration and never a rung's axis, so two arms naming
    two shapes are not a reportable comparison at all: their games differ in the stack, the
    amounts, the action space and the price of every decision, and no curve, cell or rating
    on one is comparable with one on the other (`shapes.md` §1, §6, `ladder.md` §4, D-3,
    D-29).  The refusal names both shapes, the way `PoolIdsDiffer` names both ids.
    """
    left_shape, right_shape = left, right
    if left_shape != right_shape:
        raise errors.PairDeclarationsDiffer(
            "training.fairness refused the pair: its two sides name two shapes, %r and "
            "%r, and a comparison pair is one shape's (shapes.md §1, §6, ladder.md §4, "
            "D-29)" % (left_shape, right_shape)
        )
    return left_shape


def _rule_set(rules):
    """The **set** of rules two sides are trained under, in declaration order, left first.

    Never one side's value: what a rung holds constant is the set of rules its variants
    declare, and two rules are the pair's `rule` axis rather than a constant one arm
    imposed (`rules.md` §8, D-19, `fairness.md` §4).
    """
    distinct = []
    for rule in rules:
        if rule not in distinct:
            distinct.append(rule)
    return distinct


def _utility_set(utilities):
    """The **set** of utilities two sides are trained on, in declaration order, left first.

    The utility side of :func:`_rule_set`, and never one side's value: what a rung holds
    constant is the set of utilities its variants declare, and two utilities are the pair's
    `utility` axis rather than a constant one arm imposed (`utilities.md` §8, D-20,
    `fairness.md` §4).
    """
    distinct = []
    for utility in utilities:
        if utility not in distinct:
            distinct.append(utility)
    return distinct


def _differences(left, right, rules=None, utilities=None):
    """The axes two variant entries differ on, and the field names that differ."""
    if rules is None:
        rules = (_rule(left), _rule(right))
    if utilities is None:
        utilities = (_utility(left), _utility(right))
    axes = []
    fields = []
    if left.get("backend") != right.get("backend"):
        axes.append("backend")
        fields.append("backend")
    family_left, family_right = _family(left), _family(right)
    if left.get("encoding") != right.get("encoding") or family_left != family_right:
        axes.append("encoding")
        fields.append("encoding")
    sparsity_left = _setting(left, "sparsity", 0.0)
    sparsity_right = _setting(right, "sparsity", 0.0)
    if family_left == family_right and sparsity_left == sparsity_right:
        for setting in ("width", "depth"):
            if _setting(left, setting) != _setting(right, setting):
                if "architecture" not in axes:
                    axes.append("architecture")
                fields.append(setting)
    if sparsity_left != sparsity_right:
        axes.append("connectivity")
        fields.append("sparsity")
    if bool(_setting(left, "residual", False)) != bool(_setting(right, "residual", False)):
        axes.append("residual")
        fields.append("residual")
    if rules[0] != rules[1]:
        axes.append("rule")
        fields.append("learning_rule")
    # D-20's axis: the token and the field are one word, unlike the rule's pairing of the
    # token `rule` with the field `learning_rule` (`utilities.md` §8, D-20).
    if utilities[0] != utilities[1]:
        axes.append("utility")
        fields.append("utility")
    return axes, fields


def _axis(left, right, later=None, rules=None, utilities=None):
    """`{of, differs, declared}` for two entries, or for two primaries and their rung."""
    axes, fields = _differences(left, right, rules, utilities)
    if len(axes) > 1:
        raise errors.MultipleAxes(
            "training.fairness refused the pair: it differs on %d axes, %s, and a reportable "
            "pair differs on one" % (len(axes), " and ".join(axes))
        )
    if later is None:
        return {
            "of": axes[0] if axes else "no difference",
            "differs": list(fields),
            "declared": None,
        }
    return {
        "of": later.get("axis"),
        "differs": list(fields),
        "declared": later.get("axis"),
    }


def _declared_pool(value):
    """The pool id a side declares, or `None` when it declares none."""
    pool = value.get("pool")
    if isinstance(pool, Mapping):
        identifier = pool.get("id")
        if isinstance(identifier, str) and identifier:
            return identifier
    return None


def _member_ids(value):
    """The member ids one side's pool declares: the pinned baselines, then its window.

    The pinned set is the anchor three **plus** any folding baseline the side's membership
    declaration names, because that is the pool the side trains against and the parity
    pair is played over the membership both sides share (`records.md` §8, `loop.md` §4,
    ASM-32, D-21).  The declared names are read off the declaration itself; the anchor
    three come from `declarations.BASELINES`, which is `evaluation.league()`'s pinned set
    read through the granted arrow and never a literal here (`module-map.md` §2, D-13).
    """
    ids = list(declarations.BASELINES)
    pool = value.get("pool")
    declared = pool.get("baselines") if isinstance(pool, Mapping) else None
    if isinstance(declared, (list, tuple)):
        for name in declared:
            if isinstance(name, str) and name not in ids:
                ids.append(name)
    members = pool.get("members") if isinstance(pool, Mapping) else None
    if not isinstance(members, (list, tuple)):
        return ids
    for member in members:
        if not isinstance(member, Mapping):
            continue
        identifier = member.get("id")
        if not isinstance(identifier, str) or not identifier:
            continue
        token = "".join(character for character in identifier.lower() if character.isalnum())
        if any(name.replace("-", "") in token for name in declarations.BASELINES):
            continue
        ids.append(identifier)
    return ids


def _pinned_ids(*sides):
    """The pinned baselines the sides' pools hold: the anchor three, then declared folders.

    `declarations.BASELINES` is `evaluation.league()`'s pinned set — the catalogue's
    `anchor: True` members — and a folder joins only through a side's own `pool`
    declaration, so this module names no baseline it did not read from a granted call
    (`module-map.md` §2, `records.md` §8, ASM-32, D-21).
    """
    names = list(declarations.BASELINES)
    for side in sides:
        pool = side.get("pool") if isinstance(side, Mapping) else None
        declared = pool.get("baselines") if isinstance(pool, Mapping) else None
        if not isinstance(declared, (list, tuple)):
            continue
        for name in declared:
            if isinstance(name, str) and name not in names:
                names.append(name)
    return names


def _pool_report(left, right):
    """The frozen pool a pair is read against: `m`, `frozen`, the baselines, the ids."""
    left_id = _declared_pool(left)
    right_id = _declared_pool(right)
    left_members = _member_ids(left)
    right_members = _member_ids(right)
    shared = set(left_members) & set(right_members)
    membership = [member for member in left_members if member in shared]
    for member in right_members:
        if member in shared and member not in membership:
            membership.append(member)
    held = set(left_members) | set(right_members)
    return {
        "m": declarations.LEAGUE_M,
        "frozen": True,
        "baselines": [name for name in _pinned_ids(left, right) if name in held],
        "ids": [left_id, right_id],
        "same": left_id if left_id is not None and left_id == right_id else None,
        "membership": membership,
    }


def _constants(left, right, pool_report=None, rules=None, utilities=None, shape=None):
    """The fifteen declarations `ladder.md` §4 makes a comparison hold constant.

    `rules` and `utilities` are the **sets** the two sides are trained under — each side's
    own member, else its configuration's copy, else the catalogue's first — so a row never
    reports one side's value as the constant held (`fairness.md` §4, `rules.md` §8,
    `utilities.md` §8, D-19, D-20).  The `reward` row states the reward each side's utility
    delivers, read off the catalogue's own tokens, so a pair of two objectives says so
    there and a pair of one says one (`utilities.md` §2, §8, ASM-12, D-20).

    **`shape` is the first constant and the game is the shape's.**  A pair is on one shape,
    so the row names it, and `game` and `action vocabulary` are that shape's — the row
    `engine.game_config` returns for the name and the descriptors `features.decode_action`
    answers in its vocabulary, three on the default shape and six on the no-cap one.  For
    the default shape both are byte-for-byte what a pair has always reported (`shapes.md`
    §2–§3, `sizing.md` §3, §6, D-29).
    """
    name = declarations.require_game(shape, "training.fairness")
    left_entry = _primary(left) if "variants" in left else left
    right_entry = _primary(right) if "variants" in right else right
    if rules is None:
        rules = (
            _rule(left_entry, left if "variants" in left else None),
            _rule(right_entry, right if "variants" in right else None),
        )
    if utilities is None:
        utilities = (
            _utility(left_entry, left if "variants" in left else None),
            _utility(right_entry, right if "variants" in right else None),
        )
    if pool_report is None:
        pool_report = _pool_report(left, right)
    return {
        "shape": name,
        "game": engine.game_config(name),
        "action vocabulary": declarations.vocabulary(name),
        "readout facts": list(READOUT_FACTS),
        "reward": _reward_row(_utility_set(utilities)),
        "rules": _rule_set(rules),
        "utilities": _utility_set(utilities),
        "hyper": left_entry.get("hyper")
        or right_entry.get("hyper")
        or dict(declarations.HYPER),
        "sample budget": left_entry.get("samples", declarations.LIVE_BUDGET),
        "param budget": {
            "budget": left_entry.get("param_budget", declarations.PARAM_BUDGET),
            "tolerance": declarations.PARAM_TOLERANCE,
        },
        "seed set": list(left_entry.get("seeds") or declarations.SEEDS),
        "pool": pool_report,
        "table budget": {
            "table": left_entry.get("table") or declarations.TABLE,
            "hands per cell": {"live": 120, "full": 1500},
            "seat alternation": "the two sides swap seats hand by hand (league.md §3)",
        },
        "checkpoint policy": "ten snapshots at budget // 10, the last %d retained plus the "
        "final model per variant per seed (ASM-18)" % (declarations.RETAINED,),
        "device policy": "cpu inside the sandbox; a user-started run records the device it "
        "used (D-8)",
    }


def _reward_row(utilities):
    """The `reward` constant as the catalogue states it for each utility the pair names.

    A pair trained on one reward states that one; a pair whose arms name two states both,
    because the row is a constant of the comparison and a comparison of two objectives
    holds the *set* of rewards constant and never one side's (`utilities.md` §2, §8,
    ASM-12, D-20).  The tokens are the catalogue's, read through `agents.learners()`, and
    never a sentence this module wrote about them.
    """
    catalogue = agents.learners().get("utilities") or {}
    stated = []
    for utility in utilities:
        entry = catalogue.get(utility) if isinstance(catalogue, dict) else None
        token = entry.get("reward") if isinstance(entry, dict) else None
        if not isinstance(token, str):
            token = "an undeclared reward"
        stated.append("%s's terminal reward at the seat's terminal decision: %s (ASM-12)"
                      % (utility, token))
    return "; ".join(stated)


def fairness(left, right):
    """What a pair holds constant and the one axis it differs on (`surface.md` §5)."""
    kind, left_value, right_value = _sides(left, right)
    if kind == "configuration":
        for position, configuration in enumerate((left_value, right_value)):
            _require(
                configuration,
                ("pool", "variants"),
                "the %s configuration" % ("left" if position == 0 else "right",),
            )
        left_entry = _primary(left_value)
        right_entry = _primary(right_value)
        pair = [
            str(left_value.get("primary") or left_entry.get("name")),
            str(right_value.get("primary") or right_entry.get("name")),
        ]
        rules = (
            _rule(left_entry, left_value),
            _rule(right_entry, right_value),
        )
        utilities = (
            _utility(left_entry, left_value),
            _utility(right_entry, right_value),
        )
        shapes = (
            _shape(left_entry, left_value),
            _shape(right_entry, right_value),
        )
    else:
        left_entry = left_value
        right_entry = right_value
        pair = [str(left_entry.get("name")), str(right_entry.get("name"))]
        rules = (_rule(left_entry), _rule(right_entry))
        utilities = (_utility(left_entry), _utility(right_entry))
        shapes = (_shape(left_entry), _shape(right_entry))
    # The shape is refused **before** the axes are read: a pair on two shapes is not a
    # comparison that differs on an axis, it is not a comparison at all, and reporting one
    # of the two as the constant held would be the same defect in a report instead of a run
    # (shapes.md §1, §6, ladder.md §4, D-29).
    shape = _pair_shapes(*shapes)
    for position, entry in enumerate((left_entry, right_entry)):
        _require(
            entry,
            ("architecture", "backend", "encoding"),
            "the variant %r of the %s side" % (
                entry.get("name"), "left" if position == 0 else "right"
            ),
        )
    if kind == "configuration":
        axis = _axis(left_entry, right_entry, later=right_value, rules=rules,
                     utilities=utilities)
    else:
        axis = _axis(left_entry, right_entry, rules=rules, utilities=utilities)
    left_id = _declared_pool(left_value)
    right_id = _declared_pool(right_value)
    if kind == "entry" and left_id is not None and right_id is not None:
        if left_id != right_id:
            raise errors.PoolIdsDiffer(
                "training.fairness refused the pair: its two variants declare two pool ids, "
                "%r and %r, and both arms train against one frozen pool (ASM-16)"
                % (left_id, right_id)
            )
    difference = declarations.pair_difference(left_entry, right_entry, keys=("hyper",))
    if difference is not None:
        key, declared_left, declared_right = difference
        raise errors.PairDeclarationsDiffer(
            "training.fairness refused the pair: its two sides declare two %r values, "
            "%r and %r, and a held constant is not one side's declaration (ASM-7)"
            % (key, declared_left, declared_right)
        )
    report = _pool_report(left_value, right_value)
    return {
        "pair": pair,
        "axis": axis,
        "constants": _constants(
            left_value,
            right_value,
            report,
            rules=rules,
            utilities=utilities,
            shape=shape,
        ),
        "pool": report,
    }
