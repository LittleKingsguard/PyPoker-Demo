"""FAM-18 — the utility catalogue, and a configuration that trains two utilities.

`docs/L1/battery.md` §3 FAM-18, `docs/L1/utilities.md` §1–§10 and D-20.  The terminal
reward stops being a module constant — the seat's net chip delta (ASM-12) — and becomes
a **catalogue** a learner spec selects from: `net-chips`, the unshaped net chip delta
and the declared default, and `stack-shortfall`, the delta of the squared stack
shortfall over the chips in play, normalised by the shortfall a hand begins with.  One
utility is **one capacity** with the other — a utility changes the number a terminal
transition carries and nothing of the state layout (§2, §3) — one default, and one name
a checkpoint records.  A configuration may declare its variants under different
utilities and **every variant it declares is trained**, so a run of two utilities
carries two sets of curves, two sets of artefacts and a run record that names each
variant's utility.

The instances below — the two invented utility names (`tournament-payout-battery`,
`chips-per-hour-battery`), the configuration `R11-dual-utility`, its variant names
(`chips-arm`, `shortfall-arm`), its width and depth and its pool id — appear in no
design document; they are the battery's own, invented from the surface alone
(`battery.md` §4, D-15).  D-43 leaves this catalogue exactly two members — its member is a
**third** catalogue under `learners()`'s `counterfactuals` key (`counterfactual.md` §6,
FAM-22) — so FAM-18.1 asserts the count and the first member while the record's key set
admits the sibling.  `tournament-payout-battery` drives the three refusal sites that
read a utility from a caller's declaration — a learner spec (FAM-18.3), a pool member
(FAM-18.12) and a `load` spec (FAM-18.13) — and `chips-per-hour-battery` the fourth, a
variant entry (FAM-18.9), so a name outside the catalogue is refused where it is declared
in all four places `utilities.md` §5 and `e2e-surface.md` §2 name.

FAM-18.6's subject is the **shipped version-1 set**: `training.checkpoints()` indexes the
18 containers the repository carries, every entry names a utility and every one names the
catalogue's first member, and one entry's path is loaded through
`evaluation.policy_from`, which reports the utility and the rule that entry names.  That
is the honest way to read "a container written before the utility existed is read as
`net-chips`": the shipped containers **are** the version-1 set (`protocol.md` §5,
`utilities.md` §6), so the case touches no file format.  The claim that a version-1
container which **carries** the field is refused is container surgery and is **deferred to
`tests/agents/`**, which owns the container's own reader; `battery.md` §5 draws that
boundary and this file does not reach past it.

**Red is the expected state of this file** until D-20's implementation lands: each case
asserts an observable outcome of the declared surface (`e2e-surface.md` §3.3, §3.4,
§3.5), and several of them are deliberately the attribute a policy carries — `utility`
— which `e2e-surface.md` §2 makes part of the policy protocol (D-20).
"""

import os
import sys
import unittest

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _records as R  # noqa: F401
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _records as R  # noqa: E402
    import _surface as S  # noqa: E402

#: The reward token `utilities.md` §2 pins for each catalogue member: the reward is the
#: design's own stable name for what the member delivers at the terminal decision, so a
#: case asserts the token and not a spelling this battery invented.
REWARD_TOKENS = {
    S.UTILITY_DEFAULT: "net-chip-delta",
    S.UTILITY_SECOND: "squared-stack-shortfall-delta",
}


class FAM18Utilities(S.SurfaceCase):
    """The catalogue, one capacity under two utilities, and a run that trains both."""

    # -- helpers -----------------------------------------------------------
    def catalogue(self):
        """The utility catalogue `agents.learners()` publishes, as ordered pairs.

        `utilities.md` §2 makes `learners()` publish the catalogue: more than one member,
        each with its name and the reward it delivers, its first member the declared
        default of §5.  The mapping's own key order is not contract; the catalogue's order
        is, because the default is its first member.
        """
        return S.utility_catalogue(self.ep("agents", "learners")())

    def catalogue_names(self):
        return [name for name, _member in self.catalogue()]

    def policy_utility(self, policy):
        """The utility a policy carries, or `None` (`e2e-surface.md` §2, D-20)."""
        return getattr(policy, "utility", None)

    def utility_of_learner(self, learner, seed=S.SEED_H):
        """The utility a learner reports, through the policy the surface builds from it."""
        return self.policy_utility(
            self.ep("agents", "as_policy")(learner, self.encoder(), seed)
        )

    def one_readout(self, seed=S.SEED_D):
        """One decision of a hand the battery drives, with its readout and legal set."""
        walk = self.decision_walk(seed, self.baseline("always-call", S.SEED_D), limit=1)
        self.assertTrue(walk, "the case drove no decision at all")
        _hand, readout, legal, _action, _index = walk[0]
        return readout, legal

    def named_subtree(self, value, name, depth=0):
        """The part of a record that belongs to one variant, found by its own name."""
        wanted = R.tok(name)
        if depth > 8:
            return None
        if S.is_mapping(value):
            for key, inner in value.items():
                if R.tok(key) == wanted:
                    return inner
            for _key, inner in value.items():
                if isinstance(inner, (dict, list, tuple)) or S.is_mapping(inner):
                    found = self.named_subtree(inner, name, depth + 1)
                    if found is not None:
                        return found
        elif isinstance(value, (list, tuple)):
            for item in value:
                found = self.named_subtree(item, name, depth + 1)
                if found is not None:
                    return found
        return None

    def index_entries(self, index):
        """The per-artefact entries of the shipped checkpoint index.

        ``training.checkpoints()`` is the index over the shipped set — each artefact with
        the rung variant that produced it and the rule and the utility it was trained
        under (``protocol.md`` §5, ``e2e-surface.md`` §3.5) — and the container of its
        entries is the implementation's freedom: a sequence of entries or a mapping keyed
        by the artefact.  Returns ``[]`` when the index names none, so a case that needs
        entries fails with its own message and never inside this reader.
        """
        container = None
        if S.is_mapping(index):
            for key, value in index.items():
                if R.tok(key) in ("entries", "entry", "artefacts", "artifacts"):
                    container = value
                    break
        if container is None:
            found = S.find_values(index, "entries")
            container = found[0] if found else None
        if container is None:
            return []
        if S.is_mapping(container):
            container = list(container.values())
        return [entry for entry in (container or ()) if S.is_mapping(entry)]

    def member_record(self, row, member_id):
        """One member record of a pool, by its id, or `None`."""
        wanted = R.tok(member_id)
        for record in R.member_records(row):
            for key in ("id", "member", "version", "name"):
                value = record.get(key)
                if isinstance(value, str) and R.tok(value) == wanted:
                    return record
        return None

    # -- the catalogue -----------------------------------------------------
    def test_fam18_1_agents_learners_publishes_the_utility_catalogue(self):
        """FAM-18.1 learners() publishes a catalogue of more than one named utility.

        The catalogue is still **exactly** the two utilities of `utilities.md` §2.  D-43's
        counterfactual member is a third catalogue under `learners()`'s `counterfactuals`
        key and never a third utility — a utility owns one terminal number that `training`
        reads and `learn` never does, while the member is `A` numbers per decision that
        `learn` reads (`counterfactual.md` §6, `utilities.md` §3, D-20, D-43) — so the
        objectives a spec selects from stay two, the first being `net-chips`.
        """
        pairs = self.catalogue()
        names = [name for name, _member in pairs]
        self.assertGreaterEqual(
            len(pairs),
            2,
            "agents.learners() publishes the utility catalogue with more than one member, "
            "so a spec can select one (utilities.md §2, e2e-surface.md §2 'Utility', "
            "D-20): it publishes %r" % (names,),
        )
        self.assertEqual(
            len(pairs),
            len(S.UTILITIES),
            "the utility catalogue is exactly the two members of utilities.md §2 and no "
            "third: D-43's counterfactual member is a sibling catalogue under its own key, "
            "not an objective (utilities.md §2, §3, counterfactual.md §6, D-20, D-43): it "
            "publishes %r" % (names,),
        )
        for wanted in (S.UTILITY_DEFAULT, S.UTILITY_SECOND):
            self.assertIn(
                wanted,
                names,
                "the catalogue carries %r by that name, because it is the name a learner "
                "spec, a variant entry, a checkpoint and a pool member all use "
                "(utilities.md §2, §5): it carries %r" % (wanted, names),
            )
        self.assertEqual(
            names[0],
            S.UTILITY_DEFAULT,
            "the catalogue's first member is the declared default of utilities.md §5, "
            "which is %r, and it is declared there so that a spec naming no utility has "
            "one answer (utilities.md §2, §5, records.md §3): it publishes %r first"
            % (S.UTILITY_DEFAULT, names),
        )
        for name, member in pairs:
            self.assertTrue(
                S.is_mapping(member),
                "each catalogue member is a mapping stating that utility (utilities.md "
                "§2): %r holds a %r" % (name, type(member).__name__),
            )
            self.assertEqual(
                S.member_utility(member),
                name,
                "each catalogue member carries its own name (utilities.md §2): the member "
                "under %r carries %r" % (name, S.member_utility(member)),
            )
            reward = S.member_reward(member)
            self.assertTrue(
                reward,
                "each catalogue member states the reward it delivers as a stable token — "
                "`net-chip-delta` for net-chips, `squared-stack-shortfall-delta` for "
                "stack-shortfall (utilities.md §2): the member %r states %r"
                % (name, sorted(str(key) for key in member)),
            )
            expected = REWARD_TOKENS.get(name)
            if expected is not None:
                self.assertIn(
                    R.tok(expected),
                    R.tok(S.flatten_text(reward)),
                    "the reward %r delivers is the one design token utilities.md §2 pins "
                    "for it — %r — because the token is the reward the catalogue declares "
                    "and not a name an implementation may choose: the member states %r"
                    % (name, expected, reward),
                )
            self.assertTrue(
                S.member_normaliser(member),
                "each catalogue member carries the `normaliser` its reward is divided by, "
                "so one utility's reward is commensurable with the next and neither is "
                "reshaped by the rule (utilities.md §2, ASM-28): the member %r states %r"
                % (name, sorted(str(key) for key in member)),
            )

    # -- the declared default ---------------------------------------------
    def test_fam18_2_a_spec_naming_no_utility_builds_the_catalogue_s_first_member(self):
        """FAM-18.2 a learner spec without a utility is built under the declared default."""
        names = self.catalogue_names()
        first = names[0]
        self.assertEqual(
            first,
            S.UTILITY_DEFAULT,
            "the catalogue's first member is the declared default of utilities.md §5, "
            "which is %r: it publishes %r first" % (S.UTILITY_DEFAULT, names),
        )
        spec = self.learner_spec(width=S.UTILITY_WIDTH, depth=S.UTILITY_DEPTH,
                                 seed=S.SEED_I)
        self.assertNotIn(
            "utility",
            spec,
            "this case's spec names no utility at all, which is the input utilities.md §5 "
            "is about: %r" % (spec,),
        )
        learner = self.ep("agents", "build_learner")(spec)
        self.assertEqual(
            self.utility_of_learner(learner),
            first,
            "a learner spec that names no `utility` is built under the catalogue's first "
            "member, and that default is declared and never inferred from the caller "
            "(records.md §3, utilities.md §5, D-20): the policy carries %r"
            % (self.utility_of_learner(learner),),
        )
        path = self.ep("agents", "save")(
            learner, os.path.join(self.scratch(), "fam18-2-default.ckpt")
        )
        self.assertEqual(
            self.policy_utility(self.ep("evaluation", "policy_from")(path)),
            first,
            "the checkpoint a default-built learner writes records that same utility, "
            "because one utility is named in five places that must agree "
            "(utilities.md §5, §6): %r" % (path,),
        )

    # -- a name outside the catalogue --------------------------------------
    def test_fam18_3_a_utility_outside_the_catalogue_is_refused_by_name(self):
        """FAM-18.3 agents.build_learner refuses an uncatalogued utility, naming it."""
        spec = self.learner_spec(
            width=S.UTILITY_WIDTH,
            depth=S.UTILITY_DEPTH,
            seed=S.SEED_I,
            utility=S.UNKNOWN_UTILITY,
        )
        text = S.refusal_text(lambda: self.ep("agents", "build_learner")(spec))
        self.assertIsNotNone(
            text,
            "a learner spec naming a utility outside the catalogue is refused and never "
            "silently defaulted to the catalogue's first member (utilities.md §5, "
            "e2e-surface.md §2 'Failure', D-20): the spec %r built a learner" % (spec,),
        )
        self.assertIn(
            R.tok(S.UNKNOWN_UTILITY),
            R.tok(text),
            "the refusal names the utility it refused, because a name outside the "
            "catalogue is refused where it is declared, by name (utilities.md §5): %r"
            % (text,),
        )
        self.assertIn(
            R.tok("build_learner"),
            R.tok(text),
            "the refusal is agents.build_learner's own, raised where the spec is read, so "
            "no learner was built and no other entry point is asked to refuse it "
            "(utilities.md §5, e2e-surface.md §2 'Failure'): %r" % (text,),
        )
        control_spec = self.learner_spec(
            width=S.UTILITY_WIDTH,
            depth=S.UTILITY_DEPTH,
            seed=S.SEED_I,
            utility=S.UTILITY_SECOND,
        )
        control = self.ep("agents", "build_learner")(control_spec)
        self.assertGreater(
            int(self.ep("agents", "param_count")(control)),
            0,
            "the same spec naming a catalogued utility builds a learner, so it is the "
            "utility's name that was refused and not the spec's architecture "
            "(utilities.md §5): %r" % (control,),
        )

    # -- what a checkpoint records -----------------------------------------
    def test_fam18_4_a_checkpoint_records_its_utility_and_a_contradicting_load_is_refused(
        self,
    ):
        """FAM-18.4 the container carries its utility; a contradicting load is refused."""
        encoder = self.encoder()
        readout, _legal = self.one_readout()
        for utility, other in (
            (S.UTILITY_DEFAULT, S.UTILITY_SECOND),
            (S.UTILITY_SECOND, S.UTILITY_DEFAULT),
        ):
            learner = self.utility_learner(utility, seed=S.SEED_I)
            path = self.ep("agents", "save")(
                learner,
                os.path.join(self.scratch(), "fam18-4-%s.ckpt" % (R.tok(utility),)),
            )
            self.assertEqual(
                self.policy_utility(self.ep("evaluation", "policy_from")(path)),
                utility,
                "a checkpoint records the utility its learner was trained under, and "
                "evaluation.policy_from reports the utility the file records, so a table "
                "can name each member's objective (utilities.md §6, §7, "
                "e2e-surface.md §3.4): %r" % (path,),
            )

            contradicting = self.learner_spec(
                width=S.UTILITY_WIDTH,
                depth=S.UTILITY_DEPTH,
                seed=S.SEED_I,
                utility=other,
            )
            text = S.refusal_text(lambda: self.ep("agents", "load")(contradicting, path))
            self.assertIsNotNone(
                text,
                "agents.load compares a spec's `utility` with the file's, so a spec naming "
                "%r for a checkpoint trained under %r is refused rather than restored "
                "(utilities.md §6, D-20): %r" % (other, utility, path),
            )
            for named in (utility, other):
                self.assertIn(
                    R.tok(named),
                    R.tok(text),
                    "the refusal names both utilities — the checkpoint's %r and the spec's "
                    "%r — as a spec's `learning_rule` and `seed` disagreement is refused "
                    "naming both (utilities.md §6): %r" % (utility, other, text),
                )

            matching = self.learner_spec(
                width=S.UTILITY_WIDTH,
                depth=S.UTILITY_DEPTH,
                seed=S.SEED_I,
                utility=utility,
            )
            restored = self.ep("agents", "load")(matching, path)
            self.assertEqual(
                self.action_index(self.act(restored, encoder, readout)),
                self.action_index(self.act(learner, encoder, readout)),
                "a load spec naming the utility the file records restores the learner and "
                "keeps its decision boundary, as a load under either rule does "
                "(utilities.md §6, §3): %r" % (path,),
            )

    # -- one architecture, two utilities -----------------------------------
    def test_fam18_5_one_architecture_under_two_utilities_is_one_capacity(self):
        """FAM-18.5 two learners of one architecture under two utilities report one count."""
        count = self.ep("agents", "param_count")
        chips = count(self.utility_learner(S.UTILITY_DEFAULT, seed=S.SEED_I))
        shortfall = count(self.utility_learner(S.UTILITY_SECOND, seed=S.SEED_I))
        for value in (chips, shortfall):
            self.assertTrue(
                S.is_count(value),
                "param_count returns one integer, the matched-budget measurement "
                "(utilities.md §3, ASM-10): %r" % (value,),
            )
        self.assertGreater(
            int(chips),
            0,
            "a learner of the battery's own architecture has trainable parameters "
            "(utilities.md §3, ASM-10): %r" % (chips,),
        )
        self.assertEqual(
            int(chips),
            int(shortfall),
            "a utility changes the number a terminal transition carries and nothing of the "
            "state layout, so two learners of one architecture at one seed under two "
            "utilities hold one capacity and report one param_count (utilities.md §3, "
            "ASM-10, D-20): %r against %r" % (chips, shortfall),
        )

        encoder = self.encoder()
        readout, legal = self.one_readout()
        indices = [int(index) for index in self.ep("features", "legal_indices")(legal)]
        for utility in S.UTILITIES:
            learner = self.utility_learner(utility, seed=S.SEED_I)
            self.assertEqual(
                self.utility_of_learner(learner),
                utility,
                "the two learners this case compares are one per utility, so each says "
                "which utility's reward it was built on — a swap that left both on one "
                "objective would make the comparison one model with itself "
                "(utilities.md §3, §7, e2e-surface.md §2, D-20): the learner under %r "
                "carries %r" % (utility, self.utility_of_learner(learner)),
            )
            index = self.action_index(self.act(learner, encoder, readout))
            self.assertIn(
                int(index),
                indices,
                "under %r, agents.act returns one index of the decision's legal mask, as "
                "under any other utility: `act` is utility-free (utilities.md §3, "
                "e2e-surface.md §3.3): %r not in %r" % (utility, index, indices),
            )
            path = self.ep("agents", "save")(
                learner,
                os.path.join(self.scratch(), "fam18-5-%s.ckpt" % (R.tok(utility),)),
            )
            restored = self.ep("agents", "load")(
                self.learner_spec(
                    width=S.UTILITY_WIDTH,
                    depth=S.UTILITY_DEPTH,
                    seed=S.SEED_I,
                    utility=utility,
                ),
                path,
            )
            self.assertEqual(
                int(self.ep("agents", "param_count")(restored)),
                int(self.ep("agents", "param_count")(learner)),
                "under %r, the restored learner reports the parameter count of the "
                "learner that wrote the file, so one capacity survives the container the "
                "utility's name travels in (utilities.md §3, §6, ASM-10): %r"
                % (utility, path),
            )
            self.assertEqual(
                self.action_index(self.act(restored, encoder, readout)),
                int(index),
                "under %r, save and load are loss-free at the decision boundary, as they "
                "are under the other utility: a utility moves the reward a terminal "
                "transition carries and nothing of what `act` reads (utilities.md §3, §6, "
                "ASM-10): %r" % (utility, path),
            )

    # -- the shipped version-1 set -----------------------------------------
    def test_fam18_6_the_shipped_version_1_set_is_indexed_and_reads_as_net_chips(self):
        """FAM-18.6 the shipped version-1 containers are indexed and read as net-chips."""
        index = self.ep("training", "checkpoints")()
        entries = self.index_entries(index)
        self.assertTrue(
            entries,
            "training.checkpoints() indexes the shipped set — each artefact with the rule "
            "and the utility it was trained under — and the repository ships its version-1 "
            "containers as that set, so the index holds one entry per artefact and this "
            "case has a subject (protocol.md §5, e2e-surface.md §3.5, utilities.md §6): it "
            "returned %r" % (index,),
        )
        names = self.catalogue_names()
        first = names[0]
        self.assertEqual(
            first,
            S.UTILITY_DEFAULT,
            "the catalogue's first member is the declared default of utilities.md §5, and "
            "the utility a container written before the catalogue existed is read as: it "
            "publishes %r first" % (names,),
        )
        for entry in entries:
            utility = S.declared_field(
                entry,
                "an entry of the shipped checkpoint index (protocol.md §5, "
                "e2e-surface.md §3.5)",
                "utility",
            )
            self.assertEqual(
                utility,
                first,
                "every entry of the shipped index names a utility, and every one of them "
                "is the catalogue's first member %r: the shipped containers are version 1, "
                "they carry no `utility` field, and they are read as the declared default "
                "(utilities.md §6, protocol.md §5, records.md §7, D-20): the entry %r "
                "names %r" % (first, entry, utility),
            )
        entry = entries[0]
        path = str(S.declared_field(
            entry,
            "an entry of the shipped checkpoint index (protocol.md §5, "
            "e2e-surface.md §3.5)",
            "path",
        ))
        if not os.path.isabs(path):
            # The shipped index names repository-relative artefacts, because the record
            # travels with the tree instead of naming one machine's directory
            # (protocol.md §5); resolving it against the repository root keeps this
            # assertion about the artefact that ships and not about the caller's cwd.
            path = os.path.join(S.repo_root(), path)
        self.assertTrue(
            os.path.exists(path),
            "the index names artefacts the repository ships, so the one entry this case "
            "loads is on disk (protocol.md §5): %r" % (path,),
        )
        policy = self.ep("evaluation", "policy_from")(path)
        self.assertEqual(
            self.policy_utility(policy),
            S.UTILITY_DEFAULT,
            "a shipped version-1 container loaded through evaluation.policy_from is read "
            "as %r, the utility its own index entry names, and it loads unchanged — the "
            "shipped set is not regenerated (utilities.md §6, ASM-5, protocol.md §5, "
            "D-20): %r reports %r"
            % (S.UTILITY_DEFAULT, path, self.policy_utility(policy)),
        )
        expected_rule = S.declared_field(
            entry,
            "an entry of the shipped checkpoint index (protocol.md §5, "
            "e2e-surface.md §3.5)",
            "rule",
        )
        self.assertEqual(
            getattr(policy, "learning_rule", None),
            expected_rule,
            "the policy that shipped container yields reports the rule its index entry "
            "names, because a version-1 container carries neither catalogue field and both "
            "read as their catalogue's first member (rules.md §6, utilities.md §6, "
            "protocol.md §5): %r reports %r"
            % (path, getattr(policy, "learning_rule", None)),
        )

    # -- a configuration that trains two utilities -------------------------
    def test_fam18_7_a_configuration_declaring_two_utilities_trains_both(self):
        """FAM-18.7 every declared variant is trained, and the two arms' curves differ."""
        seeds = (S.SEED_A, S.SEED_B)
        config = self.two_utility_rung(seeds=seeds)
        names = [str(entry["name"]) for entry in config["variants"]]
        record = self.run_record(config, seeds, S.BUDGET_TINY)

        curves = S.family_value(record, "curves")
        self.assertIsNotNone(
            curves,
            "the run record carries its curves family (records.md §12): %r"
            % (sorted(str(key) for key in record),),
        )
        if S.is_mapping(curves):
            self.assertEqual(
                sorted(str(key) for key in curves),
                sorted(names),
                "every variant a configuration declares is trained, so the curves hold one "
                "entry per variant — not one arm and its opposition (utilities.md §7, "
                "D-20): %r" % (sorted(str(key) for key in curves),),
            )
        else:
            body = R.tok(S.flatten_text(curves))
            for name in names:
                self.assertIn(
                    R.tok(name),
                    body,
                    "the curves the run reports name the variant %r that trained them "
                    "(utilities.md §7): %r" % (name, curves),
                )

        block = S.family_value(record, "checkpoints")
        self.assertIsNotNone(
            block,
            "the run record carries its checkpoints family (records.md §12): %r"
            % (sorted(str(key) for key in record),),
        )
        artefacts = {}
        for name in names:
            subtree = self.named_subtree(block, name)
            self.assertIsNotNone(
                subtree,
                "the checkpoints entry names the artefacts of the variant %r, because each "
                "variant produces its own final model per seed (utilities.md §7, "
                "records.md §12): %r" % (name, block),
            )
            paths = S.checkpoint_paths(subtree)
            self.assertGreaterEqual(
                len(paths),
                len(seeds),
                "the variant %r writes one final model per seed, so its entry names at "
                "least %d artefact (records.md §12, ASM-18): %r"
                % (name, len(seeds), paths),
            )
            for path in paths:
                self.assertTrue(
                    os.path.exists(path),
                    "a checkpoint the run record names is on disk, so the two arms' models "
                    "are two artefacts and not one name twice (protocol.md §5): %r" % (path,),
                )
            finals = S.checkpoint_paths(S.find_values(subtree, "final"))
            if finals:
                self.assertGreaterEqual(
                    len(finals),
                    len(seeds),
                    "the variant %r names one **final** model per seed, so %d seeds are %d "
                    "distinct final artefacts — one trained model per variant per seed "
                    "(records.md §12, utilities.md §7, ASM-18): %r"
                    % (name, len(seeds), len(seeds), finals),
                )
            artefacts[name] = paths

        left, right = names
        self.assertEqual(
            set(artefacts[left]) & set(artefacts[right]),
            set(),
            "the two variants are two trained models, so no artefact is both arms' model "
            "(utilities.md §7, D-20): %r against %r"
            % (artefacts[left], artefacts[right]),
        )
        self.assertEqual(
            {os.path.dirname(path) for path in artefacts[left]}
            & {os.path.dirname(path) for path in artefacts[right]},
            set(),
            "the two variants' final checkpoints are written to two different directories, "
            "so one utility's model never overwrites the other's (utilities.md §7): %r "
            "against %r" % (artefacts[left], artefacts[right]),
        )

        timings = S.family_value(record, "timings")
        self.assertIsNotNone(
            timings,
            "a run of two utilities reports the cost of both (records.md §12): %r"
            % (sorted(str(key) for key in record),),
        )
        body = R.tok(S.flatten_text(timings))
        for name in names:
            self.assertIn(
                R.tok(name),
                body,
                "the timings family has an entry for each trained variant: %r is missing "
                "from %r" % (name, timings),
            )
        facts = R.timing_facts(timings)
        self.assertTrue(
            facts["hands"] and (facts["per_hand"] or facts["throughput"]),
            "each trained variant's cost is the hands it trained for and a per-hand rate "
            "(records.md §12, ASM-15): %r" % (facts,),
        )

        declared = S.run_utilities(record)
        self.assertEqual(
            sorted(S.utility_names_of(declared)),
            sorted(S.UTILITIES),
            "the run records the set of utilities it declared and trained — both of them, "
            "because both variants were trained (records.md §12, utilities.md §7, D-20): "
            "%r" % (declared,),
        )
        entries = S.family_value(record, "variants")
        if S.is_mapping(entries):
            entries = list(entries.values())
        entries = [entry for entry in (entries or ()) if S.is_mapping(entry)]
        self.assertEqual(
            len(entries),
            len(names),
            "the run record carries one entry per declared variant (records.md §12): %r"
            % (entries,),
        )
        for name, utility in ((names[0], S.UTILITY_DEFAULT),
                              (names[1], S.UTILITY_SECOND)):
            entry = None
            for candidate in entries:
                if R.tok(S.variant_name(candidate)) == R.tok(name):
                    entry = candidate
                    break
            self.assertIsNotNone(
                entry, "the run record names no variant %r: %r" % (name, entries)
            )
            self.assertEqual(
                S.variant_utility(entry),
                utility,
                "the run record names each variant's utility, so a run says which "
                "objective produced which curve (records.md §12, utilities.md §7, D-20): "
                "%r" % (entry,),
            )

        # This case's own point: the two arms are trained on two rewards.  Their curves
        # are the observable the changed reward must produce — the same hands, the same
        # initial draw, one rule, one capacity — so an identical pair means the transform
        # never happened (utilities.md §4, §7, battery.md §3 FAM-18).  The comparison is
        # over each arm's own numbers, so the variant's name in its entry cannot make two
        # arms differ by itself.
        left_curves = S.variant_curves(curves, left)
        right_curves = S.variant_curves(curves, right)
        for name, body in ((left, left_curves), (right, right_curves)):
            self.assertIsNotNone(
                body,
                "the curves family says which variant each curve belongs to, so two arms' "
                "curves can be compared at all — records.md §12 makes the family per "
                "variant per seed (utilities.md §7): %r names no curve for %r"
                % (curves, name),
            )
            self.assertTrue(
                S.numbers(body),
                "each variant's curves carry the curve arrays themselves — the sample axis "
                "and a learning signal — so the two arms are comparable "
                "(records.md §12): %r holds %r" % (name, body),
            )
        self.assertNotEqual(
            S.canon(S.numbers(left_curves)),
            S.canon(S.numbers(right_curves)),
            "the two arms are trained on two different rewards — the same hands, the same "
            "initial draw, one rule and one capacity — so their curves differ: an "
            "identical pair of curves means the terminal transform did not happen "
            "(utilities.md §4, §7, battery.md §3 FAM-18): %r against %r"
            % (left_curves, right_curves),
        )

    def test_fam18_8_fairness_reports_the_pair_s_utility_set_and_the_utility_axis(self):
        """FAM-18.8 a pair whose arms declare two utilities differs on the utility axis."""
        config = self.two_utility_rung()
        left, right = config["variants"]
        text = S.refusal_text(lambda: self.ep("training", "fairness")(left, right))
        self.assertIsNone(
            text,
            "a pair whose two arms declare two utilities is a reportable comparison that "
            "differs on the utility, and not a refused pair: `utility` joined the axes "
            "beside `backend`, `encoding`, `architecture`, `connectivity`, `residual` and "
            "`rule` (utilities.md §8, D-20, D-3): %r" % (text,),
        )
        result = self.ep("training", "fairness")(left, right)
        axis = S.axis_text(result)
        self.assertIn(
            "utility",
            axis,
            "the pair differs on the utility, so the axis fairness returns is the utility "
            "(training.fairness returns `axis['of']`: utilities.md §8, "
            "e2e-surface.md §3.5): %r" % (axis,),
        )
        reported = S.find_values(result, "utilit")
        self.assertTrue(
            reported,
            "training.fairness reports the **set** of utilities the pair declares, not one "
            "side's utility (utilities.md §8, D-20): %r" % (result,),
        )
        body = R.tok(S.flatten_text(reported))
        for utility in S.UTILITIES:
            self.assertIn(
                R.tok(utility),
                body,
                "the reported set holds both utilities the two arms declare: %r is missing "
                "from %r" % (utility, reported),
            )
        constants = R.tok(S.flatten_text(result))
        for token in ("budget", "seed", "param"):
            self.assertIn(
                token,
                constants,
                "the pair still reports what it holds constant, including %r, beside the "
                "axis it differs on (ladder.md §4, utilities.md §8): %r" % (token, result),
            )

        # One axis of difference: two arms that declare two utilities **and** differ on
        # `backend` are refused, and both axes are named (utilities.md §8, D-3, D-6).
        doctored = [dict(config["variants"][0]), dict(config["variants"][1])]
        doctored[1]["backend"] = "torch"
        refusal = S.refusal_text(
            lambda: self.ep("training", "fairness")(doctored[0], doctored[1])
        )
        self.assertIsNotNone(
            refusal,
            "a pair whose arms declare two utilities and differ on `backend` differs on two "
            "axes, and such a pair is refused by name (utilities.md §8, D-3, D-6): it was "
            "reported as %r" % (refusal,),
        )
        for axis_name in ("backend", "utility"):
            self.assertIn(
                R.tok(axis_name),
                R.tok(refusal),
                "the refusal names both axes the pair differs on — %r among them — so a "
                "reader can see which comparison the pair was not (utilities.md §8, "
                "ladder.md §4): %r" % (axis_name, refusal),
            )

    def test_fam18_9_a_variant_naming_an_uncatalogued_utility_is_refused(self):
        """FAM-18.9 a variant entry's utility outside the catalogue is refused by name."""
        config = self.two_utility_rung()
        config["variants"][1]["utility"] = S.UNKNOWN_ENTRY_UTILITY
        text = S.refusal_text(
            lambda: self.run_record(config, (S.SEED_A,), S.BUDGET_TINY)
        )
        said = "%s…" % (text[:400],) if text and len(text) > 400 else text
        self.assertTrue(
            R.tok(S.UNKNOWN_ENTRY_UTILITY) in R.tok(text or ""),
            "a variant entry declaring a utility the catalogue does not carry is a "
            "declaration the run would not honour, so the run refuses it by name instead "
            "of training it under another utility — a declaration it cannot honour is "
            "judged where it is read and before a hand is dealt (battery.md §3 FAM-18, "
            "utilities.md §5, §7, D-20): the run said %r" % (said,),
        )

    def test_fam18_10_two_utilities_meet_in_a_table_that_names_its_objectives(self):
        """FAM-18.10 the two utilities' policies meet in a cell and in one matrix."""
        league = S.shared_utility_league(self)
        chips, shortfall = league["chips"], league["shortfall"]
        self.assertEqual(
            self.policy_utility(chips),
            S.UTILITY_DEFAULT,
            "the table's first variant is the learner built under %r, and its policy says "
            "so — a policy carries the utility whose reward its model was trained on "
            "(e2e-surface.md §2, utilities.md §7): %r"
            % (S.UTILITY_DEFAULT, self.policy_utility(chips)),
        )
        self.assertEqual(
            self.policy_utility(shortfall),
            S.UTILITY_SECOND,
            "the table's second variant is the learner built under %r "
            "(utilities.md §7): %r"
            % (S.UTILITY_SECOND, self.policy_utility(shortfall)),
        )
        self.assertNotEqual(
            self.policy_utility(chips),
            self.policy_utility(shortfall),
            "two variants trained under two utilities carry two different utilities, which "
            "is what makes the table's objectives heterogeneous (D-20, utilities.md §7)",
        )

        cell = self.match(
            left=chips, right=shortfall, hands=S.HANDS_TINY, seed=S.TABLE_SEED_B
        )
        named = [utility for _member, utility in S.utilities_of(S.cell_utilities(cell))
                 if utility]
        self.assertEqual(
            sorted(named),
            sorted(S.UTILITIES),
            "a cell names each member's utility, so a cell says which two objectives met "
            "(records.md §9, utilities.md §9): %r" % (S.cell_utilities(cell),),
        )

        matrix = league["matrix"]
        members = R.matrix_members(matrix)
        utilities = {}
        for member, utility in S.utilities_of(S.matrix_utilities(matrix)):
            utilities[R.tok(member)] = utility
        for member in members:
            self.assertIn(
                R.tok(member),
                utilities,
                "a matrix states each member's utility by its id, `None` included for a "
                "baseline that declares none (records.md §10, e2e-surface.md §2): %r is "
                "missing from %r" % (member, S.matrix_utilities(matrix)),
            )
        pool_member_ids = {R.tok(member)
                           for member in R.member_ids(self.members(league["pool"]))}
        trained = [member for member in members if R.tok(member) not in pool_member_ids]
        self.assertEqual(
            len(trained),
            2,
            "the table's membership is the frozen pool plus the rung's two variants "
            "(league.md §4): %r" % (members,),
        )
        self.assertEqual(
            sorted(utilities[R.tok(member)] or "" for member in trained),
            sorted(S.UTILITIES),
            "each trained member's utility is the utility its policy carries, so the table "
            "names the objectives it measured (league.md §4, utilities.md §7, §9, D-20): %r"
            % (S.matrix_utilities(matrix),),
        )
        for member in members:
            if R.tok(member) in pool_member_ids:
                self.assertIsNone(
                    utilities[R.tok(member)],
                    "a baseline carries no utility, because it is a fixed policy and not a "
                    "model trained on a reward (e2e-surface.md §2, records.md §9): %r "
                    "carries %r" % (member, utilities[R.tok(member)]),
                )

        population = S.utility_names_of(S.matrix_utility_population(matrix))
        self.assertEqual(
            sorted(population),
            sorted(S.UTILITIES),
            "the matrix states the `utility_population` its members make up — the distinct "
            "utilities those members declared, sorted — beside the `population` of rules, "
            "so a table says which objectives it fitted over (records.md §10, "
            "utilities.md §9, D-20): %r" % (S.matrix_utility_population(matrix),),
        )

    def test_fam18_11_the_pool_member_and_the_pool_id_certify_the_utility(self):
        """FAM-18.11 a member's utility is reported, and the pool id digests it."""
        learned = self.version("kestrel", utility=S.UTILITY_SECOND)
        self.assertEqual(
            learned.get("utility"),
            S.UTILITY_SECOND,
            "the case's own member record declares the utility its learner was built "
            "under, which is the pair records.md §7 requires of a version "
            "(utilities.md §6, §7): %r" % (learned,),
        )
        pool = self.pool(
            {"members": [dict(learned)], "m": S.LEAGUE_BOUND, "frozen": True}
        )
        row = self.members(pool)
        member = self.member_record(row, learned["id"])
        self.assertIsNotNone(
            member,
            "evaluation.pool_members returns the membership the declaration made, the "
            "version %r among its members (records.md §8): %r"
            % (learned["id"], R.member_ids(row)),
        )
        self.assertEqual(
            S.version_utility(member),
            S.UTILITY_SECOND,
            "a version member of a pool carries the utility it was trained under — a "
            "required key of records.md §7 — so a table can name it and the pool id can "
            "certify it, and it is the name the member's own container records "
            "(utilities.md §6, §7, ASM-27, D-20): %r" % (member,),
        )
        declared = S.utility_names_of(S.pool_utilities(row))
        self.assertEqual(
            declared,
            [S.UTILITY_SECOND],
            "a pool record declares the `utilities` its version members declare, which is the "
            "objective population a table over it measured (records.md §8, utilities.md "
            "§7, D-20): %r" % (S.pool_utilities(row),),
        )
        shortfall_id = R.pool_id(pool, row)

        # The same membership under the other utility: one member field moves, and the id
        # must move with it — the id certifies the objective (records.md §8, ASM-27).
        chips = dict(learned)
        chips["utility"] = S.UTILITY_DEFAULT
        chips["path"] = self.write_version(
            "fam18-11-chips", S.UTILITY_DEFAULT, learned["seed"]
        )
        chips_pool = self.pool(
            {"members": [chips], "m": S.LEAGUE_BOUND, "frozen": True}
        )
        chips_row = self.members(chips_pool)
        self.assertEqual(
            S.utility_names_of(S.pool_utilities(chips_row)),
            [S.UTILITY_DEFAULT],
            "the second pool's one version member declares %r, so its `utilities` set says "
            "so (records.md §8): %r" % (S.UTILITY_DEFAULT, S.pool_utilities(chips_row)),
        )
        self.assertNotEqual(
            R.pool_id(chips_pool, chips_row),
            shortfall_id,
            "the pool id digests each version's id, its rule and its **utility** — a "
            "baseline contributing its name alone — so two pools of one membership under "
            "two objectives do not wear one id, and a table can say which objective "
            "population a rating was fitted over (records.md §8, utilities.md §7, ASM-27, "
            "D-20): %r against %r"
            % (R.pool_id(chips_pool, chips_row), shortfall_id),
        )

        # A corrected snapshot counter is not a membership change, so it does not rename
        # the pool: the id changes when and only when the membership does
        # (records.md §8, ASM-27).
        corrected = dict(learned)
        corrected["step"] = int(learned["step"]) + 907
        corrected_pool = self.pool(
            {"members": [corrected], "m": S.LEAGUE_BOUND, "frozen": True}
        )
        corrected_row = self.members(corrected_pool)
        self.assertEqual(
            R.pool_id(corrected_pool, corrected_row),
            shortfall_id,
            "the same member under the same utility with a corrected `step` is the same "
            "membership, so the pool keeps its id — the id certifies the objective and "
            "changes when and only when the membership does (records.md §8, utilities.md "
            "§7, ASM-27): %r against %r"
            % (R.pool_id(corrected_pool, corrected_row), shortfall_id),
        )

    # -- the other two places a utility is named ---------------------------
    def test_fam18_12_a_pool_member_naming_an_uncatalogued_utility_is_refused(self):
        """FAM-18.12 evaluation.build_pool refuses a member's uncatalogued utility."""
        member = self.version("kestrel", utility=S.UTILITY_SECOND)
        self.assertEqual(
            member["utility"],
            S.UTILITY_SECOND,
            "this case's member is a real checkpoint written under a catalogued utility, "
            "so the name its declaration carries is the only thing that moves "
            "(records.md §7, utilities.md §6): %r" % (member,),
        )
        offending = dict(member)
        offending["utility"] = S.UNKNOWN_UTILITY
        text = S.refusal_text(
            lambda: self.pool(
                {"members": [offending], "m": S.LEAGUE_BOUND, "frozen": True}
            )
        )
        self.assertIsNotNone(
            text,
            "a pool member declaring a utility outside the catalogue is refused where it "
            "is declared and never mapped onto the declared default, because a pool must "
            "be able to certify what its member was trained under (utilities.md §5, "
            "records.md §7, e2e-surface.md §2 'Utility', D-20): the declaration %r built "
            "a pool" % (offending,),
        )
        self.assertIn(
            R.tok(S.UNKNOWN_UTILITY),
            R.tok(text),
            "the refusal names the utility it refused, because a name outside the "
            "catalogue is refused where it is declared, by name (utilities.md §5, "
            "e2e-surface.md §2): %r" % (text,),
        )
        self.assertIn(
            R.tok("build_pool"),
            R.tok(text),
            "the refusal is evaluation.build_pool's own, raised where the declaration is "
            "read, so no pool is built with a member whose objective it cannot certify "
            "(e2e-surface.md §3.4, records.md §8): %r" % (text,),
        )
        control = self.pool(
            {"members": [dict(member)], "m": S.LEAGUE_BOUND, "frozen": True}
        )
        row = self.members(control)
        self.assertIn(
            R.tok(member["id"]),
            {R.tok(name) for name in R.member_ids(row)},
            "the same member declaring the catalogued utility its own container records "
            "builds a pool, so it is the member's utility name that was refused and not "
            "its checkpoint (records.md §7, §8, utilities.md §6): %r"
            % (R.member_ids(row),),
        )

    def test_fam18_13_a_load_spec_naming_an_uncatalogued_utility_is_refused(self):
        """FAM-18.13 agents.load refuses a spec's uncatalogued utility, naming it."""
        learner = self.utility_learner(S.UTILITY_SECOND, seed=S.SEED_I)
        path = self.ep("agents", "save")(
            learner, os.path.join(self.scratch(), "fam18-13-load.ckpt")
        )
        self.assertEqual(
            self.policy_utility(self.ep("evaluation", "policy_from")(path)),
            S.UTILITY_SECOND,
            "the checkpoint this case loads was written under a real utility, so the "
            "spec's name is the only uncatalogued one in the comparison (utilities.md §6): "
            "%r" % (path,),
        )
        spec = self.learner_spec(
            width=S.UTILITY_WIDTH,
            depth=S.UTILITY_DEPTH,
            seed=S.SEED_I,
            utility=S.UNKNOWN_UTILITY,
        )
        text = S.refusal_text(lambda: self.ep("agents", "load")(spec, path))
        self.assertIsNotNone(
            text,
            "a `load` spec carrying a utility outside the catalogue is refused and never "
            "silently restored under the file's utility, as a spec's contradicting "
            "`learning_rule` is (utilities.md §6, e2e-surface.md §2 'Utility', D-20): the "
            "spec %r loaded %r" % (spec, path),
        )
        self.assertIn(
            R.tok(S.UNKNOWN_UTILITY),
            R.tok(text),
            "the refusal names the utility it refused, because a name outside the "
            "catalogue is refused where it is declared, by name (utilities.md §5, §6): %r"
            % (text,),
        )
        self.assertIn(
            R.tok("load"),
            R.tok(text),
            "the refusal is agents.load's own, raised where the spec is read against the "
            "file, so the learner is never restored under a name the catalogue lacks "
            "(e2e-surface.md §3.3, utilities.md §6): %r" % (text,),
        )
        encoder = self.encoder()
        readout, _legal = self.one_readout()
        matching = self.learner_spec(
            width=S.UTILITY_WIDTH,
            depth=S.UTILITY_DEPTH,
            seed=S.SEED_I,
            utility=S.UTILITY_SECOND,
        )
        restored = self.ep("agents", "load")(matching, path)
        self.assertEqual(
            self.action_index(self.act(restored, encoder, readout)),
            self.action_index(self.act(learner, encoder, readout)),
            "the same load under the utility the file records restores the learner at its "
            "decision boundary, so it is the uncatalogued name that was refused and not "
            "the load (utilities.md §6): %r" % (path,),
        )

    # -- one checkpoint under a named utility -------------------------------
    def write_version(self, name, utility, seed):
        """A checkpoint path written by a learner built under one utility.

        The size is the version size the battery's invented versions are built at, so the
        artefact stands beside the one :meth:`version` wrote and differs from it only in
        the utility its container records.
        """
        learner = self.utility_learner(
            utility, seed=seed, width=S.VERSION_WIDTH, depth=S.VERSION_DEPTH
        )
        path = os.path.join(self.scratch(), "%s.pt" % (name,))
        written = self.ep("agents", "save")(learner, path)
        return str(written) if written else path


if __name__ == "__main__":
    unittest.main()
