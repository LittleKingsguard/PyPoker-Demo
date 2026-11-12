"""The one loop every rung is a configuration of (D-3, D-16, docs/L3/training/loop.md).

One pass of `run`, in the documented order, for any configuration: resolve; freeze the pool
before the first hand; build the encoder and one learner per seed; derive each hand's deal
and opponent seed; play through `engine.play_hand` with the learner at `hand index mod
seats` and the hand's opponents in the other seats; learn once per hand on the learner's
own decisions; snapshot every `budget // 10` hands; write the final model and close the
curve; assemble `records.md` §12's record and nothing beyond it. The nine steps are the same
for R1 and for a configuration in no design document; only the data differs, and that is the
whole of D-3 (`ladder.md` §1, FAM-15, `seats.md` §4).
"""

import copy
import os
import time
from collections.abc import Mapping

import agents
import engine
import evaluation
import features

from . import (
    curves,
    declarations,
    episode,
    errors,
    greedy,
    layout,
    policies,
    registry,
)
from .devices import DEFAULT as DEFAULT_DEVICE
from .devices import devices as device_catalogue


def _configuration(value):
    """Step 1: a rung name resolved, or a caller's configuration used as it stands."""
    if isinstance(value, str):
        return registry.rung(value)
    if not isinstance(value, Mapping):
        raise errors.ConfigurationInvalid(
            "training.run refused the configuration %r: a run takes a rung name or a rung "
            "configuration, which is a mapping" % (value,)
        )
    for key in ("name", "variants", "pool"):
        if key not in value:
            raise errors.MissingConfigurationKey(
                "training.run refused the configuration %r: it carries no %r key, which the "
                "run reads" % (value.get("name"), key)
            )
    variants = value["variants"]
    if isinstance(variants, (str, bytes)) or not isinstance(variants, (list, tuple)):
        raise errors.ConfigurationInvalid(
            "training.run refused the configuration %r: 'variants' must be a sequence of "
            "variant entries" % (value.get("name"),)
        )
    if not 1 <= len(variants) <= 2:
        raise errors.VariantCountInvalid(
            "training.run refused the configuration %r: it declares %d variants, and a "
            "configuration declares one or two (ladder.md §2, ASM-9)"
            % (value.get("name"), len(variants))
        )
    configuration = dict(value)
    configuration["variants"] = [copy.deepcopy(entry) for entry in variants]
    return configuration


def _declared(configuration, key):
    """One configuration-level declaration, else its first variant entry's, else `None`."""
    if configuration.get(key) is not None:
        return configuration[key]
    for entry in configuration["variants"]:
        if isinstance(entry, Mapping) and entry.get(key) is not None:
            return entry[key]
    return None


def _seed_set(given, configuration):
    """Step 4's seed set: what the caller gave, or the configuration's declared set."""
    if given is None:
        declared = _declared(configuration, "seeds")
        if declared is None:
            raise errors.MissingConfigurationKey(
                "training.run refused the configuration %r: neither it nor its variant "
                "entries declare 'seeds', so no seed set is substituted for an absent one"
                % (configuration.get("name"),)
            )
        given = declared
    if isinstance(given, (str, bytes)) or not hasattr(given, "__iter__"):
        raise errors.InvalidSeeds(
            "training.run refused the seed set %r: a run needs at least one distinct "
            "integer seed (ASM-2)" % (given,)
        )
    values = list(given)
    if not values:
        raise errors.InvalidSeeds(
            "training.run refused the seed set []: a run needs at least one distinct "
            "integer seed (ASM-2)"
        )
    result = []
    for value in values:
        if not isinstance(value, int) or isinstance(value, bool):
            raise errors.InvalidSeeds(
                "training.run refused the seed set %r: the seeds must be distinct integers "
                "(ASM-2)" % (values,)
            )
        result.append(int(value))
    if len(set(result)) != len(result):
        raise errors.InvalidSeeds(
            "training.run refused the seed set %r: the seeds must be distinct integers "
            "(ASM-2)" % (result,)
        )
    return tuple(result)


def _budget(given, configuration):
    """Hands per variant per seed: what the caller gave, or the declared budget."""
    if given is None:
        declared = _declared(configuration, "samples")
        if declared is None:
            raise errors.MissingConfigurationKey(
                "training.run refused the configuration %r: neither it nor its variant "
                "entries declare 'samples', so no budget is substituted for an absent one"
                % (configuration.get("name"),)
            )
        given = declared
    if not isinstance(given, int) or isinstance(given, bool) or given < 1:
        raise errors.InvalidBudget(
            "training.run refused the budget %r: a run needs a positive budget of at least "
            "ten hands, one for each snapshot interval (ASM-18)" % (given,)
        )
    if given < declarations.SNAPSHOTS:
        raise errors.InvalidBudget(
            "training.run refused the budget %d: a run needs at least ten hands, one for "
            "each snapshot interval (ASM-18)" % (given,)
        )
    return int(given)


def _device(given, configuration):
    """The device a run uses: what the caller gave, or the configuration's default."""
    if given is None:
        given = _declared(configuration, "device")
        if given is None:
            given = DEFAULT_DEVICE
    available = device_catalogue()["available"]
    if given not in available:
        raise errors.UnknownDevice(
            "training.run refused the device %r: devices() lists %s (D-8)"
            % (given, ", ".join(available))
        )
    return str(given)


def _table(configuration):
    """The table budget the variant's row is measured at (ladder.md §3, league.md §6)."""
    table = _declared(configuration, "table")
    if table is None:
        table = declarations.TABLE
    if table not in declarations.TABLE_BUDGETS:
        raise errors.ConfigurationInvalid(
            "training.run refused the table budget %r: it is one of %s (league.md §6)"
            % (table, ", ".join(declarations.TABLE_BUDGETS))
        )
    return str(table)


def _param_budget(configuration, entry):
    """The parameter budget the record reports: the entry's, else the configuration's.

    A declaration and not a capacity: `surface.md` §4 says the `params` block reports the
    declared budget, so the order is the entry's own `param_budget`, then the
    configuration's, then `declarations.PARAM_BUDGET` — and no capacity is measured
    (`agents.param_count` is not among the four granted `agents` calls, `module-map.md`
    §2, ASM-10, docs/L2/training/declarations.md §2). A declared number is resolved
    through `declarations.check_param_budget_value`, so a `bool`, a non-integer or a value
    below one never reaches the ±2% band; `declarations.PARAM_BUDGET` is the module's own
    data rather than a declaration and is returned as it stands (docs/L3/training/errors.md
    §4).
    """
    where = configuration.get("name")
    declared = entry.get("param_budget")
    if declared is not None:
        return declarations.check_param_budget_value(declared, where, entry.get("name"))
    declared = configuration.get("param_budget")
    if declared is not None:
        return declarations.check_param_budget_value(declared, where)
    return declarations.PARAM_BUDGET


def _pool(configuration):
    """Step 2: freeze the pool before the first hand, and read it back.

    A declared version whose checkpoint the repository does not carry is not a member, so
    the pool holds what is present and the record states the membership it used
    (protocol.md §5, docs/L3/training/loop.md §1).  A membership declaration may name the
    catalogue baselines it admits beyond the flagged three — D-21's folders — and that key
    is forwarded to `evaluation.build_pool` as it stands, never defaulted here; the six
    registry rows declare none, so their pools hold the anchor three plus their window
    (`records.md` §8, ASM-32, D-21).  The **shape** is forwarded too: a pool is one
    shape's, so the declaration carries the run's own name and a member of another shape is
    that entry point's `ShapeMismatch`, refused before a hand (`records.md` §8, `shapes.md`
    §3, D-29).  Nothing of this run ever enters the pool: rolling is `evaluation.offer`'s,
    between runs (ASM-16).
    """
    declaration = configuration["pool"]
    if not isinstance(declaration, Mapping):
        raise errors.ConfigurationInvalid(
            "training.run refused the configuration %r: its 'pool' entry must be a "
            "membership declaration (records.md §8)" % (configuration.get("name"),)
        )
    members = []
    for member in declaration.get("members") or ():
        if not isinstance(member, Mapping):
            raise errors.ConfigurationInvalid(
                "training.run refused the pool member %r: a member is a records.md §7 "
                "version record" % (member,)
            )
        path = member.get("path")
        if path and os.path.isfile(layout._resolve(path)):
            members.append(dict(member))
    bound = declaration.get("m", declarations.LEAGUE_M)
    frozen = {
        "members": layout._resolved(members),
        "m": bound,
        "frozen": True,
        "game": _game(configuration),
    }
    declared_baselines = declaration.get("baselines")
    if declared_baselines is not None:
        frozen["baselines"] = declared_baselines
    built = evaluation.build_pool(frozen)
    record = evaluation.pool_members(built)
    identifier = declaration.get("id")
    if identifier is None:
        identifier = record["id"]
    return built, str(identifier), record


def _pool_baselines(pool_record):
    """The ids of the baselines the frozen pool actually holds, in the pool's order.

    Read off `pool_members`' read-back and never off a declared list: the three anchor
    baselines are members whether a declaration names them or not, a declared folder
    joins after them, and a run record states the membership it had (`records.md` §8,
    §12, ASM-32, D-21).
    """
    return tuple(
        str(member["id"])
        for member in pool_record["members"]
        if member.get("baseline")
    )


def _timings(start, hands):
    """The four cost facts one pair's pass measured (records.md §12, ASM-15)."""
    elapsed = time.perf_counter() - start
    return {
        "hands": int(hands),
        "wall_clock_seconds": float(elapsed),
        "seconds_per_hand": float(elapsed) / int(hands),
        "hands_per_second": float(hands) / float(elapsed) if elapsed > 0 else 0.0,
    }


def _declared_rule(configuration, entry):
    """The rule a variant declares — its entry's, else its configuration's, else `None`.

    A rule is read at either level, so a configuration may carry the declaration beside its
    entries and an entry may name its own; a level that declares none — or declares `None`
    — is no claim, and `None` is returned so a caller passes no rule at all rather than a
    rule this module substituted (docs/L2/training/declarations.md §1–§2, rules.md §4,
    D-19).
    """
    declared = entry.get("learning_rule")
    if declared is not None:
        return declared
    declared = configuration.get("learning_rule")
    if declared is not None:
        return declared
    return None


def _game(configuration):
    """Step 1's shape: the `game` a configuration names, else the default (`shapes.md` §3).

    Read at the configuration first and then at its first variant entry, exactly as
    `seeds`, `samples` and `device` are, so a configuration may carry the declaration
    beside its entries and an entry may name its own.  A name the catalogue does not carry
    is refused **here**, naming it and the declared names, before the pool is built and
    before the first hand — never defaulted — while a configuration naming none reads as
    the catalogue's first row, which is what keeps every record the repository already
    holds readable (`shapes.md` §2–§3, `records.md` §2, §12, D-29, D-13).
    """
    return declarations.require_game(_declared(configuration, "game"), "training.run")


def _trained_rule(configuration, entry):
    """The rule a variant's learner is built under: the declared one, else the first.

    A variant naming no rule is built by `agents` under the catalogue's **first** member,
    so the rule is resolved by reading `declarations.learning_rules()` — the catalogue
    `agents.learners()` publishes — and never by standing `declarations.LEARNING_RULE` in
    for it, because that constant is what the six rows declare and not a default this
    module owns (rules.md §4, D-19, docs/L3/training/loop.md §1 step 3).
    """
    declared = _declared_rule(configuration, entry)
    if declared is not None:
        return declared
    return declarations.learning_rules()[0]


def _declared_utility(configuration, entry):
    """The utility a variant declares — its entry's, else its configuration's, else `None`.

    The utility side of :func:`_declared_rule`, read at either level so a configuration may
    carry the declaration beside its entries and an entry may name its own; a level that
    declares none — or declares `None` — is no claim, and `None` is returned so a caller
    passes no utility at all rather than a utility this module substituted
    (docs/L2/training/declarations.md §1–§2, utilities.md §5, D-20).
    """
    declared = entry.get("utility")
    if declared is not None:
        return declared
    declared = configuration.get("utility")
    if declared is not None:
        return declared
    return None


def _trained_utility(configuration, entry):
    """The utility a variant's learner is trained on: the declared one, else the first.

    A variant naming no utility is built by `agents` under the catalogue's **first**
    member, so the utility is resolved by reading `declarations.utilities()` — the
    catalogue `agents.learners()` publishes — and never by standing
    `declarations.UTILITY` in for it, because that constant is what the six rows declare
    and not a default this module owns (utilities.md §5, D-20,
    docs/L3/training/loop.md §1 step 3).
    """
    declared = _declared_utility(configuration, entry)
    if declared is not None:
        return declared
    return declarations.utilities()[0]


def _declared_counterfactual(configuration, entry):
    """The counterfactual member a variant declares — its entry's, else its configuration's.

    The third axis' side of :func:`_declared_rule` and :func:`_declared_utility`, read at
    either level so a configuration may carry the declaration beside its entries and an
    entry may name its own; a level that declares none — or declares `None` — is no claim,
    and `None` is returned so a caller passes no member at all rather than a member this
    module substituted (`counterfactual.md` §6, `docs/L2/training/declarations.md` §1–§2,
    D-43).  It is what decides whether the spec carries the key **at all**, which is what
    keeps a variant trained under the default writing the container it always wrote.
    """
    declared = entry.get("counterfactual")
    if declared is not None:
        return declared
    declared = configuration.get("counterfactual")
    if declared is not None:
        return declared
    return None


def _trained_counterfactual(configuration, entry):
    """The counterfactual member a variant's learner is built under: the declared one, else the first.

    A variant naming no counterfactual is built by `agents` under the catalogue's **first**
    member, so the member is resolved by reading `declarations.counterfactuals()` — the
    catalogue `agents.learners()` publishes — and never by standing
    `declarations.COUNTERFACTUAL` in for it, because that constant is what the six rows
    declare and not a default this module owns (`counterfactual.md` §6, D-43,
    docs/L3/training/loop.md §2).
    """
    declared = _declared_counterfactual(configuration, entry)
    if declared is not None:
        return declared
    return declarations.counterfactuals()[0]


def _train_variant_seed(configuration, entry, seed, budget, device, pool=None, shape=None):
    """Steps 3-9 for one variant at one seed: train, snapshot, save, and pass.

    The interval is `budget // 10` and not the declared `snapshot_every`, because ASM-18
    fixes ten equally spaced snapshots at whatever budget the run was given. The learner is
    built at the run seed itself, under the rule the entry — else its configuration —
    declares and on the reward of the utility the entry — else its configuration —
    declares: a spec naming either none carries no key at all, so `agents` builds that
    catalogue's first and this module substitutes nothing of its own (D-19, D-20,
    rules.md §4, utilities.md §5). The hand's deal seed and opponent seed are `seeds.py`'s
    derivations, so both arms of a pair play the same hands against the same opponents
    (protocol.md §4, ASM-2, ASM-8).

    **Everything the loop derives from the game comes from `shape`** — the run's own and
    never `engine.game_config()`'s default: the encoder is built for it
    (`features.build_encoder(encoding, shape=...)`), the learner's head is its width
    (`build_learner`'s `game`), the hand is dealt on it (`engine.play_hand(..., shape=...)`)
    and the transition step's chips-in-play guard reads that shape's own total
    (`episode._transitions`'s `shape`, `shapes.md` §2, `sizing.md` §5–§6, D-29).  A learner
    built on the six-descriptor shape therefore trains without one line of this loop
    branching on the shape: the shape is data all the way down.

    **The pass comes last, and it is the one decision stream the run retains.**  Once the
    pair's final model is written, `greedy._pass` replays the pair's own sample — its first
    `greedy._sample(budget)` hands — against `agents.as_policy`'s exploration-off policy and
    returns `records.md` §15's block (`greedy.md` §1, §4, `sizing.md` §4, ASM-38, D-36).
    Running it after the save is what makes the block reproducible from the record: the
    model it reads is the checkpoint the record names.  The training decisions themselves
    are never retained (D-28).

    `agents.save` is handed `layout._write_path` of a declared path — the write root,
    which is the declared `<repo>/checkpoints` unless the ambient override names another
    one — and writes it; what the record carries is `layout._relative` of that path, so a
    default run's six artefacts of a pair are named as they read from the repository root
    and travel with the tree, while a redirected run's are carried absolute and name a file
    that exists (protocol.md §5, write-root.md §1, §5,
    docs/L3/training/checkpoints.md §2).
    """
    del device  # the run records it; a pair's pass measures the same work on any device
    if pool is None:
        pool = _pool(configuration)[0]
    if shape is None:
        shape = _game(configuration)
    name = str(configuration.get("name"))
    variant = str(entry.get("name"))
    interval = max(1, int(budget) // declarations.SNAPSHOTS)
    encoder = features.build_encoder(entry["encoding"], shape=shape)
    features.observation_spec(encoder)
    spec = {
        "backend": entry["backend"],
        "architecture": dict(entry["architecture"]),
        "seed": int(seed),
        "encoder": encoder,
        # The shape the learner decides in: its head is as wide as that shape's
        # vocabulary, so the parameter count follows the shape and no backend holds a
        # `3` of its own (`sizing.md` §6, `shapes.md` §2, D-29).
        "game": shape,
    }
    rule = _declared_rule(configuration, entry)
    if rule is not None:
        spec["learning_rule"] = rule
    # The utility the variant is trained on, forwarded exactly as the rule is: a spec
    # naming none carries no `utility` key and `agents` builds the catalogue's first
    # (utilities.md §5, D-20).
    trained_utility = _declared_utility(configuration, entry)
    if trained_utility is not None:
        spec["utility"] = trained_utility
    # The counterfactual member the variant is trained under, forwarded on the same terms
    # and only when it was declared: a spec naming none carries no `counterfactual` key and
    # `agents` builds the catalogue's first, so a variant that declares nothing writes the
    # version-4 container it always wrote (counterfactual.md §6, §9, D-43).
    trained_counterfactual = _declared_counterfactual(configuration, entry)
    if trained_counterfactual is not None:
        spec["counterfactual"] = trained_counterfactual
    learner = agents.build_learner(spec)
    policy = policies._learner_policy(learner, encoder, shape)
    layout._prepare(name, variant, seed)
    curve = curves._Curve(curves._axis(int(budget), interval))
    snapshots = []
    start = time.perf_counter()
    for index in range(int(budget)):
        # The hand, and the seat the learner holds in it: `episode._hand` derives both
        # seeds, seats the learner at `index mod seats` and fills the other seats with the
        # hand's opponents — one draw of `seats − 1` distinct members on a shape with more
        # seats, and the two positional policies on a two-seat one (`seats.md` §4, ASM-43,
        # `shapes.md` §5).  Training and the pass call it, so they cannot drift apart.
        played, seat = episode._hand(pool, shape, seed, index, policy)
        # The utility the variant is trained on, resolved once and handed to the step
        # that turns the hand into transitions — the one place D-20's reward is applied
        # (`utilities.md` §4, D-20).
        batch = episode._transitions(
            played, seat, encoder, _trained_utility(configuration, entry), shape
        )
        trained = index + 1
        if batch:
            statistics = agents.learn(learner, batch)
            curve.add(trained, statistics["td_error"])
        if trained % interval == 0:
            snapshots.append(
                agents.save(
                    learner,
                    layout._write_path(
                        layout._snapshot_path(name, variant, seed, trained)
                    ),
                )
            )
    final = agents.save(
        learner, layout._write_path(layout._final_path(name, variant, seed))
    )
    timing = _timings(start, budget)
    # The one retained decision stream, played after the model is on disk: the block covers
    # the run's first `min(budget, 2,000)` hands and is a function of the checkpoint the
    # record names, those hands and the frozen pool (`greedy.md` §1, §4, ASM-38, D-36).
    passed = greedy._pass(
        pool,
        shape,
        seed,
        greedy._sample(budget),
        agents.as_policy(learner, encoder, int(seed), greedy.MODE),
        "training.run at the variant %r and seed %r" % (variant, int(seed)),
    )
    return (
        curve.close([]),
        {
            "snapshots": [layout._relative(path) for path in snapshots[-declarations.RETAINED:]],
            "final": layout._relative(final),
        },
        timing,
        passed,
    )


def _header(configuration, table, hands, seed_set, device, checkpoints, interval, baselines,
            shape=None):
    """The header family: everything a third party needs to re-run the table.

    Eight of `protocol.md` §1's nine items are what the run used; the ninth, the cell size,
    is `evaluation.league()`'s declaration for the table budget this row is measured at
    (`docs/L2/training/surface.md` §4.1). A parameter count is the **declared** budget,
    because `agents.param_count` is not among the four `agents` calls this module is
    granted (ASM-10, `module-map.md` §2).  `baselines` is the pool's own baseline list, so
    the declared `0` reaches the header for every baseline the membership holds — the
    anchor three and any declared folder — and not for a hard-coded three (ASM-32, D-21).
    The game and the vocabulary are the **run's shape's**, read off `engine.game_config`
    and `features.decode_action` for that name: three descriptors in the fixed-limit shape
    and six on the no-cap one, so the header is the only route by which a D-5 notebook can
    see which game its curves are about (`shapes.md` §3, `sizing.md` §3, D-29).  The nine
    items are the nine and they do not grow: the shape is the record's own top-level `game`
    and `evaluation.report`'s to add as the report's tenth (`report.md` §2, `shape.md` §4).
    """
    league = evaluation.league()
    tables = league.get("tables") or {}
    declared = tables.get(table) if isinstance(tables, Mapping) else None
    cell = 120
    if isinstance(declared, Mapping):
        for key, value in declared.items():
            if "hand" in str(key).lower() and isinstance(value, int):
                cell = int(value)
                break
    counts = {baseline: 0 for baseline in baselines}
    for position, entry in enumerate(configuration["variants"], start=1):
        budget = _param_budget(configuration, entry)
        counts[str(entry.get("name"))] = budget
        counts["variant-%d" % (position,)] = budget
    return {
        "game": engine.game_config(shape),
        "action space": declarations.vocabulary(shape),
        "parameter counts": counts,
        "sample budget": int(hands),
        "cell size": cell,
        "seeds": list(seed_set),
        "table seed": league.get("table_seed"),
        "device": device,
        "checkpoints": [
            path
            for variant in checkpoints.values()
            for seed_block in variant.values()
            for path in list(seed_block["snapshots"]) + [seed_block["final"]]
        ],
        "snapshot interval": int(interval),
    }


def _recorded_members(members):
    """The read-back members as the record carries them: every `path` repository-relative.

    `evaluation.build_pool` was handed resolved filesystem paths (`layout._resolved`), so
    the read-back echoes those; the record spells them back through `layout._relative`, so
    one artefact has one spelling in a pool member, a run record and the index
    (`checkpoints.md` §2, `records.md` §7, `protocol.md` §5).
    """
    recorded = []
    for member in members:
        entry = dict(member)
        if entry.get("path") is not None:
            entry["path"] = layout._relative(entry["path"])
        recorded.append(entry)
    return recorded


def _member_rules(members):
    """The distinct rules the pool's **version** members declare, in membership order.

    `records.md` §8's pool record carries `rules` — the population a table over the pool
    measured — and a run record's `pool` block carries the same set, because a run says
    which estimators its opposition was trained under (`records.md` §8, §12, `rules.md` §7,
    D-19). It is read off the members `pool_members` returned and never invented here: the
    three pinned baselines declare no rule, so a baselines-only window reports an empty set
    (`records.md` §7, §8; `docs/L3/training/loop.md` §3).
    """
    rules = []
    for member in members:
        rule = member.get("rule") if isinstance(member, Mapping) else None
        if rule is None or rule in rules:
            continue
        rules.append(rule)
    return rules


def _member_utilities(members):
    """The distinct utilities the pool's **version** members declare, in membership order.

    The utility side of :func:`_member_rules`: `records.md` §8's pool record carries
    `utilities` — the objective population a table over the pool measured — and a run
    record's `pool` block carries the same set, because a run says which objectives its
    opposition was trained on (`records.md` §8, §12, `utilities.md` §7, D-20).  It is read
    off the members `pool_members` returned and never invented here: the three pinned
    baselines declare none, so a baselines-only window reports an empty set
    (`records.md` §7, §8; `docs/L3/training/loop.md` §3).
    """
    utilities = []
    for member in members:
        utility = member.get("utility") if isinstance(member, Mapping) else None
        if utility is None or utility in utilities:
            continue
        utilities.append(utility)
    return utilities


def _record(
    configuration,
    pool_id,
    pool_record,
    curve_block,
    checkpoints_block,
    timings_block,
    variant_block,
    seed_set,
    hands,
    device,
    table,
    interval,
    shape=None,
    greedy_block=None,
):
    """Step 9: `records.md` §12's record and this module's own three evidence keys.

    `rules` is the distinct set of rules the run trained, in declaration order and deduped:
    one name for a ladder rung, whose six rows declare the catalogue's first, and two for a
    configuration whose arms name two estimators (`records.md` §12, rules.md §7, D-19).
    `utilities` is the same set on D-20's axis — the utilities the run declared and
    trained, one for a ladder rung and two for a configuration whose arms name two
    (`records.md` §12, utilities.md §7, D-20). The `pool` block carries both kinds of set
    for the opposition — `_member_rules` and `_member_utilities` of the members
    `pool_members` returned — because `records.md` §12 makes the pool's `rules` and
    `utilities` part of the record (`records.md` §8, D-19, D-20).

    **The two keys D-29 adds.**  `game` names the shape the run played — the configuration's
    own declaration, or the default when it named none — so a record never names a shape it
    did not measure and `evaluation.report` can hold the run, the pool and the matrix to one
    (`records.md` §12, `shapes.md` §3, `protocol.md` §1, D-29).  `greedy` is `records.md`
    §15's block, one per variant per seed: **the only decision stream a run retains**, so
    the record holds no log of the behaviour policy and a census can be computed from it
    (`sizing.md` §4, §7, ASM-38, D-28).  The pool block repeats the shape, as `records.md`
    §8 makes it a required field of a pool record.

    **The one key D-43 adds, and it is conditional.**  `counterfactuals` is the set of
    counterfactual members the run declared and trained, and it is written **only when at
    least one variant declares one that is not the catalogue's first**: a member that is
    the default — declared or absent — writes no entry and a run where every variant is on
    it writes no key, which is what keeps a default record field for field at its capture
    (`records.md` §12, `counterfactual.md` §6, §9, D-43).  Each `variants` row names its own
    member on the same condition, so a run says which targets produced which curve without
    ever saying `none`.
    """
    name = declarations.require_game(shape, "training.run")
    params = {}
    for entry in configuration["variants"]:
        budget = _param_budget(configuration, entry)
        params[str(entry.get("name"))] = {
            "budget": budget,
            "lower": budget * (1.0 - declarations.PARAM_TOLERANCE),
            "upper": budget * (1.0 + declarations.PARAM_TOLERANCE),
        }
    rules = []
    for entry in configuration["variants"]:
        rule = _trained_rule(configuration, entry)
        if rule not in rules:
            rules.append(rule)
    utilities = []
    for entry in configuration["variants"]:
        utility = _trained_utility(configuration, entry)
        if utility not in utilities:
            utilities.append(utility)
    # The third axis' set, on the same terms and **conditional**: a member is listed only
    # when it is not the catalogue's first, and an empty list writes no key at all — so a
    # run declaring nothing leaves the record at the shape its capture took
    # (records.md §12, counterfactual.md §6, §9, D-43).
    default_counterfactual = declarations.counterfactuals()[0]
    counterfactuals = []
    for entry in configuration["variants"]:
        member = _trained_counterfactual(configuration, entry)
        if member != default_counterfactual and member not in counterfactuals:
            counterfactuals.append(member)
    record = {
        "rung": configuration.get("name"),
        "game": name,
        "greedy": dict(greedy_block or {}),
        "curves": curve_block,
        "pool": {
            "id": pool_id,
            "lineage": configuration["pool"].get("lineage"),
            "m": int(pool_record["m"]),
            "frozen": bool(pool_record["frozen"]),
            "game": pool_record.get("game", name),
            "members": _recorded_members(pool_record["members"]),
            "rules": _member_rules(pool_record["members"]),
            "utilities": _member_utilities(pool_record["members"]),
        },
        "checkpoints": checkpoints_block,
        "seeds": list(seed_set),
        "budget": int(hands),
        "device": device,
        "params": params,
        "table": table,
        "timings": timings_block,
        "variants": variant_block,
        "rules": rules,
        "utilities": utilities,
    }
    record["header"] = _header(
        configuration,
        table,
        hands,
        seed_set,
        device,
        checkpoints_block,
        interval,
        _pool_baselines(pool_record),
        shape,
    )
    record["baselines"] = {
        "rows": [
            {
                "member": baseline,
                "hand count": record["header"]["cell size"],
                "pinned": True,
                "measured": False,
            }
            for baseline in _pool_baselines(pool_record)
        ],
        "note": "every baseline the pool holds is a pool member and a table row — the "
        "three anchor baselines always, plus any folding baseline the membership "
        "declared, and the anchor three are the rating's; the run declares the rows and "
        "measures no cell (D-16, D-21, protocol.md §3)",
    }
    if len(configuration["variants"]) == 1:
        record["axis row"] = "n/a, single variant"
    if counterfactuals:
        record["counterfactuals"] = counterfactuals
    return record


def run(rung, seeds=None, budget=None, device=None):
    """One loop's record: `records.md` §12's run record (`surface.md` §4)."""
    configuration = _configuration(rung)
    seed_set = _seed_set(seeds, configuration)
    hands = _budget(budget, configuration)
    chosen_device = _device(device, configuration)
    table = _table(configuration)
    for entry in configuration["variants"]:
        declarations.check_variant(entry, str(configuration.get("name")))
    declarations.check_param_budget(configuration)
    declarations.check_declarations(configuration)
    # The shape, resolved once and refused before a hand: a name outside the catalogue is
    # named with the declared names here, and everything the loop derives from the game is
    # derived from this one name (`shapes.md` §2–§3, D-29).
    shape = _game(configuration)
    # No bound of the pass's is checked here: the pass samples the run rather than
    # replaying it whole, so a budget above 2,000 hands is a run this step accepts (D-36).
    pool, pool_id, pool_record = _pool(configuration)
    interval = max(1, hands // declarations.SNAPSHOTS)

    curve_block = {}
    checkpoints_block = {}
    timings_block = {}
    greedy_block = {}
    variant_block = []
    for entry in configuration["variants"]:
        variant = str(entry.get("name"))
        points = {}
        for seed in seed_set:
            curve, written, timing, passed = _train_variant_seed(
                configuration, entry, seed, hands, chosen_device, pool=pool, shape=shape
            )
            points[str(seed)] = curve
            checkpoints_block.setdefault(variant, {})[str(seed)] = written
            timings_block.setdefault(variant, {})[str(seed)] = timing
            greedy_block.setdefault(variant, {})[str(seed)] = passed
        spread = curves._spread([points[str(seed)]["td_error"] for seed in seed_set])
        for point in points.values():
            point["spread"] = list(spread)
        curve_block[variant] = points
        row = {
            "name": variant,
            "backend": entry["backend"],
            "encoding": entry["encoding"],
            "architecture": dict(entry["architecture"]),
            "learning_rule": _trained_rule(configuration, entry),
            "utility": _trained_utility(configuration, entry),
            "samples": int(entry.get("samples", hands)),
            "snapshot_every": int(interval),
        }
        # The third axis appears in the row **only when it is not the catalogue's first**,
        # which is what keeps a default declaration's record at the shape its capture took
        # (counterfactual.md §6, §9, records.md §12, D-43).
        trained_counterfactual = _trained_counterfactual(configuration, entry)
        if trained_counterfactual != declarations.counterfactuals()[0]:
            row["counterfactual"] = trained_counterfactual
        variant_block.append(row)

    return _record(
        configuration,
        pool_id,
        pool_record,
        curve_block,
        checkpoints_block,
        timings_block,
        variant_block,
        seed_set,
        hands,
        chosen_device,
        table,
        interval,
        shape,
        greedy_block,
    )
