"""FAM-17 — the learning-rule catalogue, and a configuration that trains two rules.

`docs/L1/battery.md` §3 FAM-17, `docs/L1/rules.md` §1–§8 and D-19.  The learning rule
stops being a module constant and becomes a **catalogue** a learner spec selects from:
`masked-q-learning` and `double-q-learning`, each stated with the target it aims at, one
capacity and one contract between them, one declared default, and one rule a checkpoint
records.  A configuration may declare its variants under different rules and **every
variant it declares is trained**, so a run of two rules carries two sets of curves, two
sets of artefacts and a run record that names each variant's rule.

The instances below — the two invented rules' refusals (`n-step-returns-battery`,
`monte-carlo-battery`), the configuration `R9-dual-rule`, its variant names and its
width and depth — appear in no design document; they are the battery's own, invented
from the surface alone (``battery.md`` §4, D-15).

Since D-43 the catalogue record carries a **third**, sibling catalogue under
`counterfactuals` — the member whose residual is the transition's resolved whole-hand
values (`counterfactual.md` §4, §6, FAM-22) — so FAM-17.1 asserts that the rule catalogue
is still exactly the two estimators of `rules.md` §2 while the record's key set admits
that one, and that the two catalogues share no member.

**Red is the expected state of this file** until D-19's implementation lands: each case
asserts an observable outcome of the declared surface (`e2e-surface.md` §3.3, §3.4,
§3.5), and one of them is deliberately the attribute a policy carries — `learning_rule`
— which `e2e-surface.md` §2 makes part of the policy protocol (D-19).
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

#: Two invented rule names the catalogue does not carry: the battery's own, one for a
#: learner spec, a pool member and a `load` spec, one for a variant entry (`rules.md` §4:
#: a name outside the catalogue is refused where it is declared, by name).
UNKNOWN_RULE = "n-step-returns-battery"
UNKNOWN_ENTRY_RULE = "monte-carlo-battery"


class FAM17Rules(S.SurfaceCase):
    """The catalogue, one contract under two rules, and a run that trains both."""

    # -- helpers -----------------------------------------------------------
    def catalogue(self):
        """The rule catalogue `agents.learners()` publishes, as ordered pairs.

        `rules.md` §2 makes `learners()["learning_rules"]` the catalogue: more than one
        member, each with its name and the target it aims at, its first member the
        declared default.  The mapping's own key order is not contract; the catalogue's
        order is, because the default is its first member.
        """
        return S.rule_catalogue(self.ep("agents", "learners")())

    def catalogue_names(self):
        return [name for name, _member in self.catalogue()]

    def policy_rule(self, policy):
        """The rule a policy carries, or `None` (`e2e-surface.md` §2, D-19)."""
        return getattr(policy, "learning_rule", None)

    def rule_of_learner(self, learner, seed=S.SEED_H):
        """The rule a learner reports, through the policy the surface builds from it."""
        return self.policy_rule(
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

    # -- the catalogue -----------------------------------------------------
    def test_fam17_1_agents_learners_publishes_the_rule_catalogue(self):
        """FAM-17.1 learners() publishes a catalogue of more than one named rule.

        The catalogue is exactly the two rules of `rules.md` §2 and no third.  D-43's
        counterfactual member is a **sibling** catalogue under `learners()`'s
        `counterfactuals` key and never a third rule — it reads no successor, so it would
        leave §2's table describing a member with no bootstrap (`counterfactual.md` §6,
        `rules.md` §2, §5, D-43) — so the catalogue's key set now admits that third
        catalogue while the estimator axis stays two members, each stated with its target.
        """
        pairs = self.catalogue()
        self.assertGreaterEqual(
            len(pairs),
            2,
            "agents.learners() publishes the learning-rule catalogue with more than one "
            "member, so a spec can select one (rules.md §2, e2e-surface.md §2 'Learning "
            "rule', D-19): it publishes %r" % ([name for name, _ in pairs],),
        )
        names = [name for name, _member in pairs]
        self.assertEqual(
            sorted(names),
            sorted(S.RULES),
            "the rule catalogue holds the two rules of rules.md §2 and no third: D-43's "
            "counterfactual member is a catalogue of its own under a key beside this one and "
            "is never a third estimator (rules.md §2, §5, counterfactual.md §6, D-43): it "
            "holds %r" % (names,),
        )
        declared = self.ep("agents", "learners")()
        counterfactuals = S.counterfactual_names(declared)
        self.assertTrue(
            counterfactuals,
            "D-43's member reaches agents.learners() as a third catalogue under its own key, "
            "which is why this record's key set now admits it and why the rule catalogue "
            "above is unchanged (e2e-surface.md §2 'Counterfactual', counterfactual.md §6, "
            "D-43): learners() publishes %r"
            % (sorted(str(key) for key in declared),),
        )
        for name in names:
            self.assertNotIn(
                name,
                counterfactuals,
                "the two catalogues name two axes and share no member: the rule %r is not a "
                "counterfactual member (rules.md §2, counterfactual.md §6, D-43): the "
                "counterfactual catalogue holds %r" % (name, counterfactuals),
            )
        for wanted in (S.RULE_DEFAULT, S.RULE_SECOND):
            self.assertIn(
                wanted,
                names,
                "the catalogue carries %r by that name, because it is the name a learner "
                "spec, a variant entry, a checkpoint and a pool member all use (rules.md "
                "§2, §4): it carries %r" % (wanted, names),
            )
        for name, member in pairs:
            self.assertTrue(
                S.is_mapping(member),
                "each catalogue member is a mapping stating that rule (rules.md §2): %r "
                "holds a %r" % (name, type(member).__name__),
            )
            self.assertEqual(
                S.member_rule(member),
                name,
                "each catalogue member carries its own name (rules.md §2): the member "
                "under %r carries %r" % (name, S.member_rule(member)),
            )
            self.assertTrue(
                S.member_target(member),
                "each catalogue member states the target it aims at — the masked maximum "
                "of the target copy, or the online parameters' argmax read off the target "
                "copy (rules.md §2): the member %r states %r"
                % (name, sorted(str(key) for key in member)),
            )

    # -- one architecture, two rules ---------------------------------------
    def test_fam17_2_one_architecture_under_two_rules_is_one_capacity(self):
        """FAM-17.2 two learners of one architecture under two rules report one count."""
        count = self.ep("agents", "param_count")
        masked = count(self.rule_learner(S.RULE_DEFAULT, seed=S.SEED_I))
        doubled = count(self.rule_learner(S.RULE_SECOND, seed=S.SEED_I))
        self.assertTrue(S.is_count(masked), "param_count returns an integer: %r" % (masked,))
        self.assertTrue(S.is_count(doubled), "param_count returns an integer: %r" % (doubled,))
        self.assertGreater(
            int(masked),
            0,
            "a learner of the battery's own architecture has trainable parameters (ASM-10): "
            "%r" % (masked,),
        )
        self.assertEqual(
            int(masked),
            int(doubled),
            "a rule changes the arithmetic of a target and nothing of the state layout, so "
            "two learners of one architecture under two rules hold one capacity and report "
            "one param_count (rules.md §3, ASM-10, D-19): %r against %r"
            % (masked, doubled),
        )

    def test_fam17_3_both_rules_answer_the_one_learner_contract(self):
        """FAM-17.3 act/learn/save/load/policy_from/as_policy under either rule."""
        encoder = self.encoder()
        readout, legal = self.one_readout()
        indices = [int(index) for index in self.ep("features", "legal_indices")(legal)]
        for rule in S.RULES:
            learner = self.rule_learner(rule, seed=S.SEED_I)
            index = self.action_index(self.act(learner, encoder, readout))
            self.assertIn(
                int(index),
                indices,
                "under %r, agents.act returns one index of the decision's legal mask, as "
                "under any other rule (rules.md §3, e2e-surface.md §3.3): %r not in %r"
                % (rule, index, indices),
            )

            statistics = self.ep("agents", "learn")(learner, self.transitions(S.SEED_C))
            self.assertTrue(
                S.is_mapping(statistics),
                "under %r, agents.learn returns the update's own statistics for the curve "
                "(rules.md §3): %r" % (rule, statistics),
            )
            for key in ("td_error", "transitions"):
                self.assertIn(
                    R.tok(key),
                    {R.tok(name) for name in statistics},
                    "under %r, the update's statistics carry %r, so one curve is one shape "
                    "whatever the rule (rules.md §3, protocol.md §1): %r"
                    % (rule, key, sorted(str(name) for name in statistics)),
                )

            checkpoint = os.path.join(self.scratch(), "fam17-3-%s.ckpt" % (R.tok(rule),))
            path = self.ep("agents", "save")(learner, checkpoint)
            spec = self.learner_spec(
                width=S.RULE_WIDTH, depth=S.RULE_DEPTH, seed=S.SEED_I, learning_rule=rule
            )
            restored = self.ep("agents", "load")(spec, path)
            self.assertEqual(
                self.action_index(self.act(restored, encoder, readout)),
                self.action_index(self.act(learner, encoder, readout)),
                "under %r, save and load are loss-free at the decision boundary, as they "
                "are under the other rule (rules.md §3): %r" % (rule, path),
            )

            loaded_policy = self.ep("evaluation", "policy_from")(path)
            chosen = loaded_policy(readout, legal)
            self.assertEqual(
                self.chosen_index(legal, chosen),
                self.action_index(self.act(learner, encoder, readout)),
                "under %r, evaluation.policy_from loads the member its learner is at the "
                "same decisions (rules.md §3, §6): %r" % (rule, path),
            )

            policy = self.ep("agents", "as_policy")(learner, encoder, S.SEED_H)
            self.assertTrue(
                callable(policy),
                "under %r, agents.as_policy returns a policy in the sense of "
                "e2e-surface.md §2: %r" % (rule, policy),
            )
            self.assertEqual(
                self.policy_rule(policy),
                rule,
                "a policy returned by agents.as_policy carries `learning_rule`, the "
                "catalogue member its model learned under, so a table names the population "
                "it measured (e2e-surface.md §2, rules.md §7, D-19): %r"
                % (self.policy_rule(policy),),
            )

    # -- the declared default ---------------------------------------------
    def test_fam17_4_a_spec_naming_no_rule_builds_the_catalogue_s_first_member(self):
        """FAM-17.4 a learner spec without a rule is built under the declared default."""
        names = self.catalogue_names()
        first = names[0]
        self.assertEqual(
            first,
            S.RULE_DEFAULT,
            "the catalogue's first member is the declared default of rules.md §4, which is "
            "%r: it publishes %r first" % (S.RULE_DEFAULT, names),
        )
        spec = self.learner_spec(width=S.RULE_WIDTH, depth=S.RULE_DEPTH, seed=S.SEED_I)
        self.assertNotIn(
            "learning_rule",
            spec,
            "this case's spec names no rule at all, which is the input rules.md §4 is "
            "about: %r" % (spec,),
        )
        learner = self.ep("agents", "build_learner")(spec)
        self.assertEqual(
            self.rule_of_learner(learner),
            first,
            "a learner spec that names no `learning_rule` is built under the catalogue's "
            "first member, and that default is declared and never inferred from the caller "
            "(records.md §3, rules.md §4, D-19): the policy carries %r"
            % (self.rule_of_learner(learner),),
        )
        path = self.ep("agents", "save")(
            learner, os.path.join(self.scratch(), "fam17-4-default.ckpt")
        )
        self.assertEqual(
            self.policy_rule(self.ep("evaluation", "policy_from")(path)),
            first,
            "the checkpoint a default-built learner writes records that same rule, because "
            "one rule is named in four places that must agree (rules.md §4, §6): %r"
            % (path,),
        )

    # -- a name outside the catalogue --------------------------------------
    def test_fam17_5_a_rule_outside_the_catalogue_is_refused_by_name(self):
        """FAM-17.5 agents.build_learner refuses an uncatalogued rule, naming it."""
        spec = self.learner_spec(
            width=S.RULE_WIDTH,
            depth=S.RULE_DEPTH,
            seed=S.SEED_I,
            learning_rule=UNKNOWN_RULE,
        )
        text = S.refusal_text(lambda: self.ep("agents", "build_learner")(spec))
        self.assertIsNotNone(
            text,
            "a learner spec naming a rule outside the catalogue is refused and never "
            "silently defaulted to the catalogue's first member (rules.md §4, "
            "e2e-surface.md §2 'Failure', D-19): the spec %r built a learner"
            % (spec,),
        )
        self.assertIn(
            R.tok(UNKNOWN_RULE),
            R.tok(text),
            "the refusal names the rule it refused, because a name outside the catalogue is "
            "refused where it is declared, by name (rules.md §4): %r" % (text,),
        )
        self.assertIn(
            R.tok("build_learner"),
            R.tok(text),
            "the refusal is agents.build_learner's own, raised where the spec is read, so "
            "no learner was built and no other entry point is asked to refuse it "
            "(rules.md §4, e2e-surface.md §2 'Failure'): %r" % (text,),
        )
        control = self.ep("agents", "build_learner")(
            self.learner_spec(
                width=S.RULE_WIDTH,
                depth=S.RULE_DEPTH,
                seed=S.SEED_I,
                learning_rule=S.RULE_SECOND,
            )
        )
        self.assertGreater(
            int(self.ep("agents", "param_count")(control)),
            0,
            "the same spec naming a catalogue rule builds a learner, so it is the rule's "
            "name that was refused and not the spec's architecture (rules.md §4): %r"
            % (control,),
        )

    # -- what a checkpoint records -----------------------------------------
    def test_fam17_6_a_checkpoint_records_its_rule_and_a_contradicting_load_is_refused(self):
        """FAM-17.6 the container carries its rule; a load spec that contradicts is refused."""
        encoder = self.encoder()
        readout, _legal = self.one_readout()
        for rule, other in (
            (S.RULE_DEFAULT, S.RULE_SECOND),
            (S.RULE_SECOND, S.RULE_DEFAULT),
        ):
            learner = self.rule_learner(rule, seed=S.SEED_I)
            path = self.ep("agents", "save")(
                learner, os.path.join(self.scratch(), "fam17-6-%s.ckpt" % (R.tok(rule),))
            )
            self.assertEqual(
                self.policy_rule(self.ep("evaluation", "policy_from")(path)),
                rule,
                "a checkpoint records the rule its learner was trained under, and "
                "evaluation.policy_from reports the rule the file records (rules.md §6, "
                "e2e-surface.md §3.4): %r" % (path,),
            )

            contradicting = self.learner_spec(
                width=S.RULE_WIDTH,
                depth=S.RULE_DEPTH,
                seed=S.SEED_I,
                learning_rule=other,
            )
            text = S.refusal_text(lambda: self.ep("agents", "load")(contradicting, path))
            self.assertIsNotNone(
                text,
                "agents.load compares a spec's `learning_rule` with the file's, so a spec "
                "naming %r for a checkpoint trained under %r is refused rather than "
                "restored (rules.md §6, D-19): %r" % (other, rule, path),
            )
            for named in (rule, other):
                self.assertIn(
                    R.tok(named),
                    R.tok(text),
                    "the refusal names both rules — the checkpoint's %r and the spec's %r — "
                    "as a spec's seed disagreement is refused naming both (rules.md §6): %r"
                    % (rule, other, text),
                )

            matching = self.learner_spec(
                width=S.RULE_WIDTH,
                depth=S.RULE_DEPTH,
                seed=S.SEED_I,
                learning_rule=rule,
            )
            restored = self.ep("agents", "load")(matching, path)
            self.assertEqual(
                self.action_index(self.act(restored, encoder, readout)),
                self.action_index(self.act(learner, encoder, readout)),
                "a load spec naming the rule the file records restores the learner and "
                "keeps its decision boundary (rules.md §6, §3): %r" % (path,),
            )

    # -- a configuration that trains two rules -----------------------------
    def test_fam17_7_a_configuration_declaring_two_rules_trains_both(self):
        """FAM-17.7 every declared variant is trained, under the rule it declares."""
        seeds = (S.SEED_A, S.SEED_B)
        config = self.two_rule_rung(seeds=seeds)
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
                "entry per variant — not one arm and its opposition (rules.md §7, D-19): %r"
                % (sorted(str(key) for key in curves),),
            )
        else:
            body = R.tok(S.flatten_text(curves))
            for name in names:
                self.assertIn(
                    R.tok(name),
                    body,
                    "the curves the run reports name the variant %r that trained them "
                    "(rules.md §7): %r" % (name, curves),
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
                "variant produces its own final model per seed (rules.md §7, records.md "
                "§12): %r" % (name, block),
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
                    "(records.md §12, rules.md §7, ASM-18): %r"
                    % (name, len(seeds), len(seeds), finals),
                )
            artefacts[name] = paths

        left, right = names
        self.assertEqual(
            set(artefacts[left]) & set(artefacts[right]),
            set(),
            "the two variants are two trained models, so no artefact is both arms' model "
            "(rules.md §7, D-19): %r against %r" % (artefacts[left], artefacts[right]),
        )
        self.assertEqual(
            {os.path.dirname(path) for path in artefacts[left]}
            & {os.path.dirname(path) for path in artefacts[right]},
            set(),
            "the two variants' final checkpoints are written to two different directories, "
            "so one rule's model never overwrites the other's (rules.md §7): %r against %r"
            % (artefacts[left], artefacts[right]),
        )

        timings = S.family_value(record, "timings")
        self.assertIsNotNone(
            timings,
            "a run of two rules reports the cost of both (records.md §12): %r"
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

        declared = R.run_rules(record)
        self.assertEqual(
            sorted(R.rule_names_of(declared)),
            sorted(S.RULES),
            "the run records the set of rules it declared and trained — both of them, "
            "because both variants were trained (records.md §12, rules.md §7, D-19): %r"
            % (declared,),
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
        for name, rule in ((names[0], S.RULE_DEFAULT), (names[1], S.RULE_SECOND)):
            entry = None
            for candidate in entries:
                if R.tok(S.variant_name(candidate)) == R.tok(name):
                    entry = candidate
                    break
            self.assertIsNotNone(entry, "the run record names no variant %r: %r" % (name, entries))
            self.assertEqual(
                R.variant_rule(entry),
                rule,
                "the run record names each variant's learning rule, so a run says which "
                "estimator produced which curve (records.md §12, D-19): %r" % (entry,),
            )

    def test_fam17_8_fairness_reports_the_pair_s_rule_set_and_the_rule_axis(self):
        """FAM-17.8 a pair whose arms declare two rules differs on the rule axis."""
        config = self.two_rule_rung()
        left, right = config["variants"]
        text = S.refusal_text(lambda: self.ep("training", "fairness")(left, right))
        self.assertIsNone(
            text,
            "a pair whose two arms declare two rules is a reportable comparison that "
            "differs on the rule, and not a refused pair: `learning_rule` left the settings "
            "a pair must share (rules.md §8, D-19): %r" % (text,),
        )
        result = self.ep("training", "fairness")(left, right)
        axis = S.axis_text(result)
        self.assertIn(
            "rule",
            axis,
            "the pair differs on the rule, so the axis fairness returns is the rule "
            "(training.fairness returns `axis['of']`: rules.md §8, e2e-surface.md §3.5): %r"
            % (axis,),
        )
        reported = S.find_values(result, "rule")
        self.assertTrue(
            reported,
            "training.fairness reports the **set** of rules the pair declares, not one "
            "side's rule (rules.md §8, D-19): %r" % (result,),
        )
        body = R.tok(S.flatten_text(reported))
        for rule in S.RULES:
            self.assertIn(
                R.tok(rule),
                body,
                "the reported set holds both rules the two arms declare: %r is missing from "
                "%r" % (rule, reported),
            )
        constants = R.tok(S.flatten_text(result))
        for token in ("budget", "seed", "param"):
            self.assertIn(
                token,
                constants,
                "the pair still reports what it holds constant, including %r, beside the "
                "axis it differs on (ladder.md §4, rules.md §8): %r" % (token, result),
            )

    def test_fam17_9_a_variant_naming_an_uncatalogued_rule_is_refused(self):
        """FAM-17.9 a variant entry's rule outside the catalogue is refused by name."""
        config = self.two_rule_rung()
        config["variants"][1]["learning_rule"] = UNKNOWN_ENTRY_RULE
        text = S.refusal_text(
            lambda: self.run_record(config, (S.SEED_A,), S.BUDGET_TINY)
        )
        self.assertIsNotNone(
            text,
            "a variant entry declaring a rule the catalogue does not carry is a declaration "
            "the run would not honour, so the run refuses it instead of training it under "
            "another rule (battery.md §3 FAM-17, rules.md §4, D-19): the run returned",
        )
        self.assertIn(
            R.tok(UNKNOWN_ENTRY_RULE),
            R.tok(text),
            "the refusal names the rule it refused, and it is raised before the first hand "
            "is dealt, because a declaration the run cannot honour is judged before the "
            "pool is built (rules.md §4, battery.md §3 FAM-17): %r" % (text,),
        )

    def test_fam17_10_two_rules_meet_in_a_table_that_names_its_population(self):
        """FAM-17.10 the two rules' policies meet in a cell and in one matrix."""
        league = S.shared_rule_league(self)
        masked, doubled = league["masked"], league["doubled"]
        self.assertEqual(
            self.policy_rule(masked),
            S.RULE_DEFAULT,
            "the table's first variant is the learner built under %r, and its policy says "
            "so (e2e-surface.md §2, rules.md §7): %r"
            % (S.RULE_DEFAULT, self.policy_rule(masked)),
        )
        self.assertEqual(
            self.policy_rule(doubled),
            S.RULE_SECOND,
            "the table's second variant is the learner built under %r (rules.md §7): %r"
            % (S.RULE_SECOND, self.policy_rule(doubled)),
        )
        self.assertNotEqual(
            self.policy_rule(masked),
            self.policy_rule(doubled),
            "two variants trained under two rules carry two different rules, which is what "
            "makes the table heterogeneous (D-19, rules.md §7)",
        )

        cell = self.match(
            left=masked, right=doubled, hands=S.HANDS_TINY, seed=S.TABLE_SEED_B
        )
        named = [rule for _member, rule in R.rules_of(R.cell_rules(cell)) if rule]
        self.assertEqual(
            sorted(named),
            sorted(S.RULES),
            "a cell names each member's rule, so a cell says which two estimators met "
            "(records.md §9, league.md §3): %r" % (R.cell_rules(cell),),
        )

        matrix = league["matrix"]
        members = R.matrix_members(matrix)
        rules = {}
        for member, rule in R.rules_of(R.matrix_rules(matrix)):
            rules[R.tok(member)] = rule
        for member in members:
            self.assertIn(
                R.tok(member),
                rules,
                "a matrix states each member's rule by its id, `None` included for a "
                "baseline that declares none (records.md §10, e2e-surface.md §2): %r is "
                "missing from %r" % (member, R.matrix_rules(matrix)),
            )
        pool_member_ids = {R.tok(member) for member in R.member_ids(self.members(league["pool"]))}
        trained = [member for member in members if R.tok(member) not in pool_member_ids]
        self.assertEqual(
            len(trained),
            2,
            "the table's membership is the frozen pool plus the rung's two variants "
            "(league.md §4): %r" % (members,),
        )
        self.assertEqual(
            sorted(rules[R.tok(member)] or "" for member in trained),
            sorted(S.RULES),
            "each trained member's rule is the rule its policy carries, so the table names "
            "the population it measured (league.md §4, rules.md §7, D-19): %r"
            % (R.matrix_rules(matrix),),
        )
        for member in members:
            if R.tok(member) in pool_member_ids:
                self.assertIsNone(
                    rules[R.tok(member)],
                    "a baseline carries no rule, because it is a fixed rule and not a "
                    "trained estimator (e2e-surface.md §2, records.md §9): %r carries %r"
                    % (member, rules[R.tok(member)]),
                )

        population = R.rule_names_of(R.matrix_population(matrix))
        self.assertEqual(
            sorted(population),
            sorted(S.RULES),
            "the matrix states the `population` its members make up — the distinct rules "
            "those members declared, sorted — so a table says which estimators it fitted "
            "over (records.md §10, rules.md §7, D-19): %r"
            % (R.matrix_population(matrix),),
        )


if __name__ == "__main__":
    unittest.main()
