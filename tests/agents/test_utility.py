"""AGT-15 — the utility catalogue, the spec's utility, and the container's field.

Drives `docs/L3/agents/utility.md` §2-§8 and `docs/L3/agents/checkpoint.md` §2.1-§4,
beside the L1 statements the same contracts are published under — `docs/L1/utilities.md`
§2, §5, §6, `docs/L1/records.md` §3, §7, `docs/L1/e2e-surface.md` §2, §3.3,
`docs/L1/battery.md` §5 and `strata/decisions.md` D-20: `learners()` publishes a
terminal-reward **catalogue** of two members in a declared order — `net-chips`, the
unshaped net chip delta of ASM-12 and the declared default, then `stack-shortfall`, the
delta of the squared stack shortfall over the chips in play — each a record of exactly
three keys, its `name`, the `reward` it delivers as a stable token and the `normaliser`
that reward is divided by (`utility.md` §2); a learner spec selects one with `utility`,
an absent key being the catalogue's first member and never a value inferred from the
caller's silence (§3, `records.md` §3); a name the catalogue does not carry is refused by
name in a spec and in a `load` spec alike (§8); one capacity is shared by both members,
because a utility changes the number a terminal transition carries and nothing of the
state layout (§4, ASM-10); and the container's `format_version` is **3**, its `utility`
field is **required** and is written immediately after `learning_rule`, a version-2
container carries no `utility` and is read as `net-chips`, a version-1 one is read as
`net-chips` too, and a container of either older version that *carries* the field is
refused by name (`checkpoint.md` §2.1, §3, `utilities.md` §6, D-20).

`docs/L1/battery.md` §5 draws the boundary this file exists for: the utility's arithmetic
is applied where the transition record is built, it has no entry point of its own, and
that is why the catalogue, the selection, the default, the refusals and the container's
field are asserted **here** and not in `tests/e2e/test_fam18_utilities.py`, which drives
the same surface one layer up (`training`'s transform, the run record, the pool, the
table).  Two spellings below an entry point are read, and both are contract: `Learner`'s
`utility`, one of the "two carried fields" `utility.md` §7 makes the learner's own and
§9 takes from L4, and the container's own `metadata.json`, whose two member names and
field order `checkpoint.md` §2 and §2.1 fix.  The older-version containers of
AGT-15.6–15.8 are built by rewriting a container this module wrote — both members the
file's own bytes, the format version and the field of §2.1 the case is about doctored —
so `checkpoints/` is neither read nor written here.
"""

import os
import unittest
from collections.abc import Mapping

from _agents_support import (
    DENSE_KIND,
    LEARNER_SEED,
    AgentsCase,
    container_document,
    flat_encoder,
    learner_spec,
    plain_int,
    version_container,
    write_container,
)

#: The catalogue's two members, in `utilities.md` §2's declared order, with the reward
#: each delivers as a stable token and the normaliser that reward is divided by.  These
#: are design tokens — the same spelling `learners()` publishes — and not invented
#: instances: §2's table and D-20 fix every one of them.
DECLARED_UTILITIES = (
    ("net-chips", "net-chip-delta", "none"),
    ("stack-shortfall", "squared-stack-shortfall-delta", "U(s_0)"),
)

#: The declared default of `utilities.md` §5: the catalogue's **first** member.
DECLARED_DEFAULT = "net-chips"

#: Invented names, one utility and one rule the catalogues do not carry (`battery.md` §4,
#: D-15): no document in `docs/` holds either spelling.
UNCATALOGUED_UTILITY = "reward-per-hour-8127"


def utility_of(learner):
    """The catalogue member a learner reports, through the field `as_policy` copies.

    `Learner.utility` is one of the "two carried fields" `utility.md` §7 makes the
    learner's own: `build_learner` sets it beside `rule`, `load` restores it from the
    container, and `as_policy` copies it onto the policy `e2e-surface.md` §2 declares.
    Reading both here is what makes "the learner carries the member its spec names"
    observable, and §9 leaves the field itself to L4 rather than to this battery's
    discretion (§7, §8, `checkpoint.md` §2.1).
    """
    return getattr(learner, "utility", None)


class UtilityCatalogueTest(AgentsCase):
    """The catalogue's shape and default, the spec's selection, and the refusals."""

    def test_agt15_1_utilities_is_the_two_member_reward_catalogue(self):
        """AGT-15.1 `utilities` is exactly two members in the declared order, each carrying only `name`, `reward` and `normaliser` (`utilities.md` §2, §5, `surface.md` §3, D-20).

        §2 publishes the catalogue through `learners()`: two members, in that order, each
        a plain record of its `name`, the `reward` it delivers as a **stable token and
        never a sentence**, and the `normaliser` that reward is divided by.  The order is
        contract and not decoration: its first member is the declared default of §5, so
        the order and the default are one statement.  A member carrying a fourth key
        would be a catalogue a report could not quote by name, and §2's tokens are what
        a record states.
        """
        catalogue = self.agents().learners()["utilities"]
        self.assertIsInstance(
            catalogue,
            Mapping,
            "learners()['utilities'] is one plain record of the catalogue's members "
            "(utilities.md §2, surface.md §3)",
        )
        self.assertEqual(
            tuple(catalogue),
            tuple(name for name, _reward, _normaliser in DECLARED_UTILITIES),
            "utilities is keyed by the two catalogue members in utilities.md §2's "
            "declared order — net-chips first, the declared default of §5 — and each "
            "key is the member's own name (surface.md §3, D-20)",
        )
        for name, entry in catalogue.items():
            with self.subTest(utility=name):
                self.assertIsInstance(
                    entry,
                    Mapping,
                    "a catalogue member is one plain record (utilities.md §2)",
                )
                self.assertEqual(
                    set(entry),
                    {"name", "reward", "normaliser"},
                    "a member carries its `name`, the `reward` it delivers and the "
                    "`normaliser` that reward is divided by, and nothing else "
                    "(utilities.md §2, e2e-surface.md §2)",
                )
                self.assertEqual(
                    entry["name"],
                    name,
                    "a catalogue member's `name` is the key it is published under",
                )
        for name, reward, normaliser in DECLARED_UTILITIES:
            with self.subTest(utility=name):
                self.assertEqual(
                    catalogue[name]["reward"],
                    reward,
                    "the member %r delivers the reward %r, the stable token "
                    "utilities.md §2's table declares (D-20)" % (name, reward),
                )
                self.assertEqual(
                    catalogue[name]["normaliser"],
                    normaliser,
                    "the member %r's reward is divided by %r, the normaliser "
                    "utilities.md §2's table declares (D-20)" % (name, normaliser),
                )
                self.assertTrue(
                    isinstance(catalogue[name]["reward"], str)
                    and catalogue[name]["reward"].strip(),
                    "a member's `reward` is a non-empty stable token: %r"
                    % (catalogue[name]["reward"],),
                )
                self.assertEqual(
                    [
                        character
                        for character in catalogue[name]["reward"]
                        if character.isspace()
                    ],
                    [],
                    "the reward %r of %r carries whitespace: utilities.md §2 declares a "
                    "stable token and never a sentence"
                    % (catalogue[name]["reward"], name),
                )
        self.assertEqual(
            tuple(catalogue)[0],
            DECLARED_DEFAULT,
            "the catalogue's first member — the default a spec naming no `utility` is "
            "built under — is %r (utilities.md §5, records.md §3, D-20)"
            % (DECLARED_DEFAULT,),
        )

    def test_agt15_2_the_spec_selects_the_member_and_one_capacity_serves_both(self):
        """AGT-15.2 no `utility` builds the declared default and a named one builds that member, both reported by the learner and its policy, at one `param_count` (`utilities.md` §3, §5, `records.md` §3, `surface.md` §4, §5, §10, e2e-surface.md §2, ASM-10, D-20).

        Absent, the utility is the catalogue's **first** member and never a value inferred
        from the caller's silence; present, it is the member the spec names (§5,
        `records.md` §3).  The two members are **one capacity**: a utility changes the
        number a terminal transition carries and nothing of the state layout, so
        `param_count` cannot tell them apart (§3, ASM-10) while the member each reports
        can — the learner's own `utility` and the `utility` its `as_policy` policy carries
        (`e2e-surface.md` §2).
        """
        package = self.agents()
        catalogue = tuple(package.learners()["utilities"])
        self.assertEqual(
            catalogue,
            tuple(name for name, _reward, _normaliser in DECLARED_UTILITIES),
            "the catalogue's two members, in utilities.md §2's order, are what this case "
            "selects between (D-20)",
        )
        default, second = catalogue[0], catalogue[1]

        def policy_of(learner):
            return package.as_policy(learner, flat_encoder(), LEARNER_SEED)

        silent = package.build_learner(learner_spec(kind=DENSE_KIND))
        self.assertEqual(
            utility_of(silent),
            default,
            "a spec naming no `utility` is built under the catalogue's first member, "
            "%r, the declared default (utilities.md §5, records.md §3)" % (default,),
        )
        self.assertEqual(
            getattr(policy_of(silent), "utility", None),
            default,
            "the policy built from a learner under the declared default reports that "
            "member, which is how a table names the objective it measured "
            "(e2e-surface.md §2, utilities.md §7)",
        )

        named = package.build_learner(
            learner_spec(kind=DENSE_KIND, extra={"utility": second})
        )
        self.assertEqual(
            utility_of(named),
            second,
            "a spec naming %r builds a learner trained on that member's reward "
            "(utilities.md §5, surface.md §4, D-20)" % (second,),
        )
        self.assertEqual(
            getattr(policy_of(named), "utility", None),
            second,
            "the policy built from a learner under %r reports that member, and no "
            "decision it makes reads it (e2e-surface.md §2, utilities.md §7)"
            % (second,),
        )
        self.assertEqual(
            package.param_count(named),
            package.param_count(silent),
            "the two utilities are one capacity: param_count is the matched-budget "
            "measurement no utility changes (utilities.md §3, ASM-10, D-20)",
        )
        self.assertGreater(
            package.param_count(named),
            0,
            "a learner built under either catalogue member is sized like a learner "
            "(surface.md §5, utilities.md §3)",
        )

    def test_agt15_3_an_uncatalogued_utility_is_refused_by_name(self):
        """AGT-15.3 `build_learner` refuses a `utility` the catalogue does not carry, and a value that is not a string, naming the entry point, the key, the value and the catalogue's names (`surface.md` §4, §9, `utilities.md` §5, `errors.md` §3-§4, D-20).

        §5 refuses a name outside the catalogue **where it is declared** and never maps it
        onto the default, because a silent substitution would train a model on a reward
        its spec does not name; a non-string is refused the same way, so no `str()` and no
        lookup coerces a caller's value.  The refusal is this module's own (`errors.md`
        §2): a caller catching `AgentsError` catches it, which a `KeyError` from a mistyped
        catalogue would escape.
        """
        package = self.agents()
        catalogue = tuple(package.learners()["utilities"])
        cases = (
            ("a name outside the catalogue", UNCATALOGUED_UTILITY),
            ("another name outside the catalogue", "chips-per-hour-8127"),
            ("an integer", 3),
            ("a float", 2.5),
            ("None", None),
            ("a bool", True),
        )
        for label, value in cases:
            with self.subTest(case=label):
                self.assert_agents_refusal(
                    package.build_learner,
                    learner_spec(kind=DENSE_KIND, extra={"utility": value}),
                    entry="build_learner",
                    groups=(
                        ("utility",),
                        (str(value),),
                        (catalogue[0],),
                        (catalogue[1],),
                    ),
                    label="%s: utility = %r" % (label, value),
                )


class UtilityCheckpointTest(AgentsCase):
    """The container's `format_version` 3, its `utility` field and the two older readings."""

    def setUp(self):
        """One scratch directory per case, made on first use and removed with the case."""
        super().setUp()
        self._folder = None

    def path(self, name):
        """A container's path inside this case's own scratch directory."""
        if self._folder is None:
            self._folder = self.tempdir()
        return os.path.join(self._folder, name)

    def member(self):
        """A learned `stack-shortfall` learner, at a state a checkpoint records.

        `net-chips` is what a version-1 and a version-2 container are read as, so the
        source member of every case below is the **other** one: a reading that fell back
        to the default is then visible as a change, and not as an agreement that was true
        anyway (`utilities.md` §5, §6).  Annealed, so its parameters are past the initial
        draw and its recorded schedule position is a real one.
        """
        learner = self.annealed_learner(
            "utility-checkpoint",
            {
                "kind": DENSE_KIND,
                "width": 8,
                "depth": 1,
                "extra": {"utility": "stack-shortfall"},
            },
        )
        self.assertEqual(
            utility_of(learner),
            "stack-shortfall",
            "the source member of these cases is trained on stack-shortfall, so a "
            "container read as net-chips differs from what was written "
            "(utilities.md §5, §6)",
        )
        return learner

    def test_agt15_4_a_written_container_is_version_three_and_orders_the_field(self):
        """AGT-15.4 a container this module writes records `format_version` 3 and its `utility` immediately after its `learning_rule` (`utilities.md` §6, `checkpoint.md` §2, §2.1, `surface.md` §8, `records.md` §7, D-20).

        `utilities.md` §6 makes the `utility` field **required** of the container and the
        `format_version` **3**; the field is written immediately after the `learning_rule`,
        so the two catalogue members a version's record must name are one pair a reader
        sees together.  The document is read from the container's own `metadata.json` — the
        member name `checkpoint.md` §2 fixes — with the JSON's key order preserved, which
        is the only way "immediately after" is observable at all.
        """
        package = self.agents()
        learner = self.member()
        path = package.save(learner, self.path("v3-8127.pt"))
        metadata, _parameters = container_document(path)
        self.assertEqual(
            plain_int(metadata["format_version"], "metadata['format_version']"),
            3,
            "a container this module writes is format version 3 (utilities.md §6, "
            "checkpoint.md §2.1, D-20)",
        )
        self.assertIn(
            "utility",
            metadata,
            "a version 3 container records the utility its learner was trained under, as "
            "a required field (utilities.md §6, records.md §7, D-20)",
        )
        self.assertEqual(
            metadata["utility"],
            "stack-shortfall",
            "the container records the catalogue member its learner carries "
            "(utilities.md §6, D-20)",
        )
        self.assertIn(
            "learning_rule",
            metadata,
            "a version 3 container records the rule its learner was trained under beside "
            "the utility (utilities.md §6, rules.md §6, D-19)",
        )
        keys = tuple(metadata)
        self.assertEqual(
            keys.index("utility"),
            keys.index("learning_rule") + 1,
            "`utility` is written immediately after `learning_rule` in the document's own "
            "key order, so a version's two catalogue members are read as one pair "
            "(utilities.md §6, checkpoint.md §2.1); the document's order was %r"
            % (keys,),
        )

    def test_agt15_5_a_version_three_container_round_trips_the_utility(self):
        """AGT-15.5 `save`/`load` restores the member a version-3 container records, through `load(None, path)`, an agreeing `load` spec and `as_policy(...).utility` (`utilities.md` §6, §7, `surface.md` §9, §10, `e2e-surface.md` §2, ASM-5, D-20).

        A restore recovers the objective as it recovers the rule: the learner a version-3
        file yields carries the member the file names, and so does the policy
        `as_policy` builds from it — which is what lets a table name a shipped member's
        objective even when no record of the run exists yet (§6, §7).  A spec naming the
        file's own utility agrees on that compared key and loads; the file's member is
        the one no default would have given, so the equality is observable (§5, §6).
        """
        package = self.agents()
        learner = self.member()
        path = package.save(learner, self.path("v3-round-trip-8127.pt"))
        restored = package.load(None, path)
        self.assertEqual(
            utility_of(restored),
            "stack-shortfall",
            "a learner restored from a version 3 container carries the utility the file "
            "records (utilities.md §6, surface.md §9, ASM-5)",
        )
        self.assertEqual(
            getattr(
                package.as_policy(restored, flat_encoder(), LEARNER_SEED),
                "utility",
                None,
            ),
            "stack-shortfall",
            "the policy built from a restored learner reports the member the container "
            "records, and no decision it makes reads it (utilities.md §6, §7, "
            "e2e-surface.md §2)",
        )
        via_spec = package.load(
            learner_spec(
                kind=DENSE_KIND,
                width=8,
                depth=1,
                extra={"utility": "stack-shortfall"},
            ),
            path,
        )
        self.assertEqual(
            package.param_count(via_spec),
            package.param_count(learner),
            "a spec naming the file's own utility agrees on that compared key and loads "
            "(utilities.md §6, checkpoint.md §3)",
        )

    def test_agt15_6_a_version_two_container_is_read_as_net_chips(self):
        """AGT-15.6 a container rewritten to `format_version` 2, or to 1, with `utility` dropped loads and is read as `net-chips`, the member its writer could only have used (`checkpoint.md` §3, `utilities.md` §6, `surface.md` §9, `records.md` §7, ASM-5, D-20).

        A version-2 container carries a `learning_rule` and no `utility`, and a version-1
        one carries neither, because both were written before the utility existed, so each
        is read as the catalogue's first member — the only one such a writer could have
        used (`checkpoint.md` §3's version table).  Each file is built from one this module
        wrote: both members the file's own bytes, `format_version` rewritten and the fields
        that version forbids dropped, the `learning_rule` kept in the version-2 copy
        because that version requires it.  The source member is `stack-shortfall`, so a
        reading that silently kept it would fail here rather than pass.
        """
        package = self.agents()
        learner = self.member()
        source = package.save(learner, self.path("v3-source-8127.pt"))
        older = version_container(
            source, self.path("v2-8127.pt"), 2, drop=("utility",)
        )
        metadata, _parameters = container_document(older)
        self.assertNotIn(
            "utility",
            metadata,
            "the version 2 container this case reads carries no `utility`, which is the "
            "one fact its reader's default rests on (checkpoint.md §3, utilities.md §6)",
        )
        restored = package.load(None, older)
        self.assertEqual(
            utility_of(restored),
            DECLARED_DEFAULT,
            "a version 2 container carries no `utility` and is read as %r, the only "
            "member its writer could have used (checkpoint.md §3, utilities.md §5, §6, "
            "D-20)" % (DECLARED_DEFAULT,),
        )
        self.assertEqual(
            getattr(
                package.as_policy(restored, flat_encoder(), LEARNER_SEED),
                "utility",
                None,
            ),
            DECLARED_DEFAULT,
            "the policy a version-2 container yields names the member the file is read "
            "as, so a table can still label the member (utilities.md §6, §7, "
            "e2e-surface.md §2)",
        )
        self.assertEqual(
            package.param_count(restored),
            package.param_count(learner),
            "the older reading changes the utility alone: the parameters the file "
            "carries restore at the same capacity (utilities.md §3, checkpoint.md §3)",
        )

        oldest = version_container(
            source,
            self.path("v1-8127.pt"),
            1,
            drop=("learning_rule", "utility"),
        )
        ancient_metadata, _parameters = container_document(oldest)
        self.assertEqual(
            sorted(
                field
                for field in ("learning_rule", "utility")
                if field in ancient_metadata
            ),
            [],
            "the version 1 container this case reads carries neither catalogue field, "
            "which is the silence its reader's two defaults rest on "
            "(checkpoint.md §3, utilities.md §6)",
        )
        ancient = package.load(None, oldest)
        self.assertEqual(
            utility_of(ancient),
            DECLARED_DEFAULT,
            "a version 1 container carries no `utility` either and is read as %r "
            "(checkpoint.md §3, utilities.md §5, §6)" % (DECLARED_DEFAULT,),
        )
        self.assertEqual(
            getattr(
                package.as_policy(ancient, flat_encoder(), LEARNER_SEED),
                "utility",
                None,
            ),
            DECLARED_DEFAULT,
            "the policy a version-1 container yields names the member the file is read "
            "as, so the shipped set's objectives are nameable too (checkpoint.md §3, "
            "utilities.md §6, §7)",
        )

    def test_agt15_7_an_older_container_carrying_the_field_is_refused(self):
        """AGT-15.7 a version-2 and a version-1 container that *carry* `utility` are refused naming the field and the value (`utilities.md` §6, `checkpoint.md` §3, `errors.md` §3, D-20).

        No writer of either version wrote the field, so a container of that version that
        carries one was edited and is refused by name — never read as its version's
        silence.  The version-1 copy drops `learning_rule` as well, so the field the
        refusal is about is `utility` and not the rule a version-1 container also may not
        carry.  The refusal is this module's own and names the value, so a caller reads
        which member the edited file claimed (`errors.md` §2-§3).
        """
        package = self.agents()
        learner = self.member()
        source = package.save(learner, self.path("v3-source-carried-8127.pt"))
        cases = (
            (
                "a version 2 container carrying utility",
                version_container(source, self.path("v2-carried-8127.pt"), 2),
            ),
            (
                "a version 1 container carrying utility",
                version_container(
                    source,
                    self.path("v1-carried-8127.pt"),
                    1,
                    drop=("learning_rule",),
                ),
            ),
        )
        for label, path in cases:
            with self.subTest(case=label):
                metadata, _parameters = container_document(path)
                self.assertIn(
                    "utility",
                    metadata,
                    "the doctored copy this case refuses is one that carries the field, "
                    "which is the edited file utilities.md §6 describes",
                )
                self.assert_agents_refusal(
                    package.load,
                    None,
                    path,
                    entry="load",
                    groups=(("load(path)",), ("utility",), (metadata["utility"],)),
                    label=label,
                )

    def test_agt15_8_a_container_naming_an_uncatalogued_utility_is_refused(self):
        """AGT-15.8 a version-3 container whose `utility` the catalogue does not carry is refused naming the field and the value (`utilities.md` §5, §6, `checkpoint.md` §3, ASM-20, D-20).

        A name outside the catalogue is refused **where it is declared**, and a container
        is one of the five places a utility is named (§5, `records.md` §7): a value the
        catalogue does not carry is never mapped onto the default, because a member whose
        objective cannot be certified cannot be a league member (`utilities.md` §7,
        `records.md` §7).  The container is the one this module wrote with that single
        value doctored, so the refusal is the value's and not the file's.
        """
        package = self.agents()
        learner = self.member()
        source = package.save(learner, self.path("v3-source-uncarried-8127.pt"))
        metadata, parameters = container_document(source)
        metadata["utility"] = UNCATALOGUED_UTILITY
        doctored = write_container(
            self.path("v3-uncarried-8127.pt"), metadata, parameters
        )
        self.assert_agents_refusal(
            package.load,
            None,
            doctored,
            entry="load",
            groups=(("utility",), (UNCATALOGUED_UTILITY,)),
            label="a version 3 container naming an uncatalogued utility",
        )
        self.assertEqual(
            package.param_count(package.load(None, source)),
            package.param_count(learner),
            "the container the doctored copy came from must still load, so the refusal "
            "above is the doctored value's and not the file's (checkpoint.md §3)",
        )

    def test_agt15_9_load_compares_the_specs_utility_with_the_files(self):
        """AGT-15.9 a `load` spec whose `utility` disagrees with the file's is refused naming both values, and a spec naming a utility outside the catalogue is refused naming it (`utilities.md` §6, `surface.md` §9, `records.md` §7, `checkpoint.md` §3, `errors.md` §3-§4, D-20).

        `utility` is a compared key exactly as `seed`, `backend`, the kind and
        `learning_rule` are: a disagreement is the comparison family's refusal
        (`checkpoint.md` §3's third row, `CheckpointMismatch`) and names both values, while
        a value the catalogue does not carry is validated **before** it is compared and
        refused naming it — never coerced onto the file's member (`errors.md` §4).  The
        message names `load(spec)`, which is what tells this refusal apart from a
        container's own (`load(path)`).  A spec naming the file's member is the control
        that loads.
        """
        package = self.agents()
        catalogue = tuple(package.learners()["utilities"])
        default, recorded = catalogue[0], "stack-shortfall"
        self.assertIn(recorded, catalogue)
        learner = self.member()
        path = package.save(learner, self.path("v3-compared-8127.pt"))
        self.assert_refused(
            package.load,
            learner_spec(
                kind=DENSE_KIND, width=8, depth=1, extra={"utility": default}
            ),
            path,
            entry="load",
            groups=(("load(spec)",), ("utility",), (default,), (recorded,)),
            label="a spec naming another catalogue member than the file records",
        )
        self.assert_agents_refusal(
            package.load,
            learner_spec(
                kind=DENSE_KIND,
                width=8,
                depth=1,
                extra={"utility": UNCATALOGUED_UTILITY},
            ),
            path,
            entry="load",
            groups=(
                ("utility",),
                (UNCATALOGUED_UTILITY,),
                (catalogue[0],),
                (catalogue[1],),
            ),
            label="a spec naming a utility outside the catalogue",
        )
        agreed = package.load(
            learner_spec(
                kind=DENSE_KIND, width=8, depth=1, extra={"utility": recorded}
            ),
            path,
        )
        self.assertEqual(
            package.param_count(agreed),
            package.param_count(learner),
            "a spec naming the file's own utility agrees on that compared key and loads "
            "(utilities.md §6, checkpoint.md §3)",
        )


if __name__ == "__main__":
    unittest.main()
