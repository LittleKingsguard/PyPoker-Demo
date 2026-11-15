"""JOIN-AGT-12 — the utility axis at the join.

`docs/L3/agents/utility.md` §4, §7, `docs/L3/agents/checkpoint.md` §4,
`docs/L1/utilities.md` §3, §5, §6, §7, `docs/L1/reward-scale.md` §2, §4 and D-20, D-65:
a learner spec selects the terminal reward it is trained on, the catalogue's three
members are **one capacity**, and a version carries the member it was trained under so a
table can name the objective it measured.
Every one of those is a join and not a module's own statement — the member is selected
through `agents.build_learner`, the model is driven by observations `features.encode`
makes of readouts `engine.readout` dealt, the reward the terminal transition carries is
`engine.play_hand`'s payoff transformed by `training`'s transition record, and the
objective travels with a checkpoint through `agents.save`/`agents.load` into the policy
`agents.as_policy` returns, whose restore is loss-free in `utility` as in everything else
(`checkpoint.md` §4, `docs/L1/e2e-surface.md` §2, §3.3).  This file walks that path under
**each** catalogue member: it builds one learner per member, encodes real decisions
through the granted `features` calls, learns from a real episode's transitions, saves,
loads, and compares the restored learner's decisions and reported `utility` with the
saved one's — and then states the capacity claim the axis rests on, because a pair whose
arms declare two utilities still has to be matched (`utility.md` §4, ASM-10, D-20).

Nothing here re-asserts what `tests/e2e/test_fam18_utilities.py` already drives one layer
up (the catalogue's own shape, the variant entry's refusals, the run record's utility set,
the pool id, the matrix's `utility_population`), and nothing here asserts the utility's
arithmetic: that lives where the transition record is built (`docs/L1/battery.md` §5,
`utility.md` §5, §6).  The instances — the widths, depths, deals and container names —
are the support module's invented ones (`docs/L1/battery.md` §4, D-15).
"""

import importlib.util
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
# The support module is loaded under a private name: this repository's integration
# batteries share the file name `_join_support.py`, so a plain import would hand one
# battery another's helpers when two test directories are collected in one process.
if "agents_join_support" in sys.modules:
    J = sys.modules["agents_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "agents_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["agents_join_support"] = J
    _spec.loader.exec_module(J)

#: The three utilities `docs/L1/utilities.md` §2 declares, **in its declared order**: the
#: first is the declared default of §5, and the third is the member
#: `docs/L1/reward-scale.md` §2 appends after the two of Rev 1 so no existing member's
#: position -- and so that default -- moves.  The names are spelled here only so the
#: catalogue can be held to the document's order; every value a case reads is read off
#: `agents.learners()`.
UTILITIES = ("net-chips", "stack-shortfall", "net-chips-normalised")

#: That order's first member -- the declared default (`utilities.md` §5) -- and its third.
DEFAULT_UTILITY = UTILITIES[0]
NORMALISED_UTILITY = UTILITIES[2]

#: The three keys `docs/L1/utilities.md` §2 gives every member's record -- its `name`, the
#: `reward` it delivers as a stable token and the `normaliser` it is divided by, in the
#: order the declaration carries them -- and the reward token and normaliser
#: `docs/L1/reward-scale.md` §2 gives the third member.
UTILITY_KEYS = ("name", "reward", "normaliser")
NORMALISED_REWARD = "normalised-net-chip-delta"
NORMALISED_BY = "T"

#: A utility name **outside** the catalogue, one word away from the third member's, so a
#: membership test that is a prefix or a substring test would let it through
#: (`utilities.md` §5, D-20).
UNDECLARED_UTILITY = "net-chips-normalised-battery"


class UtilityAtTheJoin(J.JoinCase):
    """One learner per catalogue utility, driven through the join and restored."""

    def catalogue(self):
        """The utility catalogue `agents.learners()` publishes, in its declared order.

        `docs/L1/utilities.md` §2 makes `learners()` publish **exactly three** members, in
        the order `net-chips`, `stack-shortfall`, `net-chips-normalised`, and §5 makes the
        first the declared default — which `docs/L1/reward-scale.md` §2 keeps in place by
        appending the third after the other two.  So the order is held to the document's,
        the first member to that default, and each member's record to its exactly three
        keys: a catalogue that lost a member, moved the default or grew a record fails here
        rather than in whichever case happened to read one name (`docs/L1/utilities.md` §2,
        §5, `docs/L1/reward-scale.md` §2, §4, D-20).
        """
        names = list(J.utility_names())
        self.assertEqual(
            tuple(names),
            UTILITIES,
            "agents.learners()['utilities'] publishes docs/L1/utilities.md §2's three "
            "members in its declared order, the third appended by "
            "docs/L1/reward-scale.md §2 so no existing member's position moves: %r"
            % (names,),
        )
        self.assertEqual(
            names[0],
            DEFAULT_UTILITY,
            "the catalogue's first member is still `net-chips`, the declared default "
            "docs/L1/utilities.md §5 gives a spec that names none — a claim the third "
            "member's arrival must not move (docs/L1/reward-scale.md §2, §4, D-20): %r"
            % (names,),
        )
        for name in names:
            record = J.utility_record(name)
            self.assertEqual(
                tuple(record),
                UTILITY_KEYS,
                "every catalogue member is a record of exactly the three keys "
                "docs/L1/utilities.md §2 declares — `name`, `reward`, `normaliser`, in "
                "that order — so no published record grows with the third member "
                "(docs/L1/reward-scale.md §4): %r carries %r"
                % (name, sorted(record)),
            )
            self.assertEqual(
                str(record["name"]),
                str(name),
                "a member's record carries its own catalogue name, which is the token a "
                "spec, a pool member and a container spell "
                "(docs/L1/utilities.md §2, §5): %r" % (record,),
            )
            for key in ("reward", "normaliser"):
                self.assertIsInstance(
                    record[key],
                    str,
                    "a member's %r is a stable token and never a sentence "
                    "(docs/L1/utilities.md §2): %r" % (key, record[key]),
                )
        return names

    def spec(self, utility):
        """One invented learner spec (`docs/L1/records.md` §3) naming `utility`."""
        spec = dict(
            J.learner_spec("naive-stack", J.WIDTH_ONE, J.DEPTH_ONE, J.LEARNER_SEED)
        )
        spec["utility"] = utility
        return spec

    def trained(self, utility, path):
        """`(encoder, learned learner)` for one utility, saved at `path`.

        The batch is built from a real episode of an invented deal — the observation of
        each decision is `features.encode` of `engine.readout`'s facts, the action is the
        index `features.legal_indices` aligns to the descriptor the caller played, and the
        terminal record carries `engine.play_hand`'s payoff, which is what the utility
        re-expresses (`docs/L1/records.md` §4, §5, `docs/L1/utilities.md` §4).  It is then
        tiled past the catalogue's exploration `samples`, so the compared decisions are
        the greedy arm's and a restore that dropped the parameters would fail below.
        """
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        learner = J.build_learner(self.spec(utility))
        episode = J.play_hand(J.DEAL_CHECKPOINT_B, J.caller, J.caller)
        batch = J.seat_transitions(episode, 0, encoder)
        self.assertTrue(
            batch,
            "the episode must report a decision for the seat, or no batch is built "
            "(docs/L1/records.md §5)",
        )
        first = J.learn(learner, batch)
        self.assertEqual(
            J.transitions_consumed(first),
            len(batch),
            "learn consumes the real batch it is handed (docs/L2/agents/surface.md §7)",
        )
        annealed = J.learn(learner, J.tiled(batch, J.exploration_samples()))
        self.assertTrue(
            J.finite(J.td_error(annealed)),
            "learn must report a finite td_error under either utility "
            "(docs/L2/agents/surface.md §7, docs/L1/utilities.md §3)",
        )
        J.save(learner, path)
        return encoder, learner

    def decisions(self, encoder):
        """Observations and masks from two invented deals, driven by a caller policy."""
        out = []
        for deal in (J.DEAL_DECISION_A, J.DEAL_TOKEN_B):
            out.extend(J.observations(deal, J.caller, encoder))
        self.assertGreaterEqual(
            len(out),
            4,
            "the comparison must cover several decisions of two real hands",
        )
        return out

    def test_join_agt_12_1_each_utility_survives_save_load_and_as_policy(self):
        """JOIN-AGT-12.1 under each catalogue utility a learner round-trips and reports its own member.

        `docs/L1/utilities.md` §6 and `docs/L1/e2e-surface.md` §2: the container records
        the utility its learner was trained under, a restore recovers the learner under
        it, and the policy `agents.as_policy` builds carries it — so a table can name each
        member's objective even when no record of the run exists yet
        (`docs/L1/records.md` §7).  The restored learner must also **decide as the saved
        one does** on real encoded decisions, and its policy at the recorded seed must
        choose the same descriptor as `act` reads off its own parameters: a restore that
        carried the label and not the state would otherwise pass
        (`docs/L1/protocol.md` §5, ASM-5).
        """
        for utility in self.catalogue():
            with self.subTest(utility=utility):
                path = self.checkpoint_path("%s-%s" % (utility, J.CHECKPOINT_ALPHA))
                encoder, learner = self.trained(utility, path)
                saved_policy = J.as_policy(learner, encoder, J.LEARNER_SEED)
                self.assertEqual(
                    getattr(saved_policy, "utility", None),
                    utility,
                    "a policy carries the catalogue member whose reward its learner was "
                    "trained on (docs/L1/e2e-surface.md §2, docs/L1/utilities.md §7, D-20)",
                )
                restored = J.load(None, path)
                self.assertEqual(
                    J.param_count(restored),
                    J.param_count(learner),
                    "a restored member reports the saved capacity, which no utility "
                    "changes (docs/L1/utilities.md §3, docs/L2/agents/surface.md §5)",
                )
                self.assertEqual(
                    getattr(
                        J.as_policy(restored, encoder, J.LEARNER_SEED), "utility", None
                    ),
                    utility,
                    "a member loaded from its path alone is trained on the member its "
                    "container records (docs/L1/utilities.md §6, D-20)",
                )
                by_spec = J.load(self.spec(utility), path)
                self.assertEqual(
                    getattr(
                        J.as_policy(by_spec, encoder, J.LEARNER_SEED), "utility", None
                    ),
                    utility,
                    "a spec naming the file's own utility agrees on that compared key and "
                    "loads under it (docs/L1/utilities.md §6)",
                )
                for position, (observation, mask) in enumerate(self.decisions(encoder)):
                    chosen = J.action_index(J.act(learner, observation, mask))
                    self.assertEqual(
                        J.action_index(J.act(restored, observation, mask)),
                        chosen,
                        "save/load is loss-free at the decision boundary under %r "
                        "(docs/L1/protocol.md §5, ASM-5), decision %d"
                        % (utility, position),
                    )
                fresh = J.build_learner(self.spec(utility))
                self.assertNotEqual(
                    [
                        J.action_index(J.act(fresh, observation, mask))
                        for observation, mask in self.decisions(encoder)
                    ],
                    [
                        J.action_index(J.act(learner, observation, mask))
                        for observation, mask in self.decisions(encoder)
                    ],
                    "a learner only at its initial draw decides as the saved one on every "
                    "compared decision, so a restore that dropped the learned parameters "
                    "would pass the equality above (docs/L2/agents/surface.md §7, §9)",
                )
                policy = J.as_policy(restored, encoder, J.LEARNER_SEED)
                for deal in (J.DEAL_DECISION_A, J.DEAL_DECISION_B):
                    for _hand, facts, legal, _chosen, _index in J.walk(deal, J.caller):
                        mask = J.legal_indices(legal)
                        by_act = J.action_index(
                            J.act(learner, J.encode(encoder, facts), mask)
                        )
                        descriptor = policy(facts, legal)
                        self.assert_descriptor_in(legal, descriptor, "restored policy")
                        self.assertEqual(
                            J.descriptor_index(legal, descriptor),
                            by_act,
                            "the restored member's policy at the checkpoint's seed "
                            "decides as its saved learner does (docs/L2/agents/"
                            "surface.md §10, docs/L1/protocol.md §5), deal %r" % (deal,),
                        )

    def test_join_agt_12_2_the_catalogue_members_are_one_capacity(self):
        """JOIN-AGT-12.2 every catalogue member's learner reports one `param_count`.

        `docs/L1/utilities.md` §3, ASM-10, D-20 and `docs/L1/reward-scale.md` §4: a
        utility changes the number a terminal transition carries and nothing of the state
        layout, so `param_count` — the matched-budget measurement — is identical under
        **every** member, the normalised third included.  That is what lets two arms of a
        pair differ on the `utility` axis alone and still be comparable
        (`docs/L1/utilities.md` §8, D-3, `docs/L1/reward-scale.md` §2); the member each
        reports then differs, so the equality is a claim about capacity and not about the
        learners being one.
        """
        names = self.catalogue()
        first = names[0]
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        learners = {}
        for utility in names:
            with self.subTest(utility=utility):
                learner = J.build_learner(self.spec(utility))
                self.assertGreater(
                    J.param_count(learner),
                    0,
                    "a learner built under %r is sized like a learner, or there is no "
                    "capacity to match (docs/L2/agents/surface.md §5, "
                    "docs/L1/utilities.md §3)" % (utility,),
                )
                learners[utility] = learner
        for utility in names[1:]:
            self.assertEqual(
                J.param_count(learners[utility]),
                J.param_count(learners[first]),
                "the catalogue's members are one capacity: a pair may differ on the "
                "utility axis and be matched on parameters, so %r reports the "
                "`param_count` %r reports (docs/L1/utilities.md §3, §8, "
                "docs/L1/reward-scale.md §4, ASM-10, D-20): %r against %r"
                % (
                    utility,
                    first,
                    J.param_count(learners[utility]),
                    J.param_count(learners[first]),
                ),
            )
        policies = [
            J.as_policy(learners[utility], encoder, J.LEARNER_SEED)
            for utility in names
        ]
        self.assertEqual(
            [getattr(policy, "utility", None) for policy in policies],
            list(names),
            "each policy names its own catalogue member, so one capacity under three "
            "utilities is still three named objectives (docs/L1/e2e-surface.md §2, "
            "docs/L1/utilities.md §7, D-20): %r"
            % ([getattr(policy, "utility", None) for policy in policies],),
        )

    def test_join_agt_12_3_the_normalised_member_is_a_member_one_capacity_and_a_container(self):
        """JOIN-AGT-12.3 the normalised reward is the third member, one capacity with `net-chips`, and a container records it.

        `docs/L1/reward-scale.md` §2 and `docs/L1/utilities.md` §2 make
        `net-chips-normalised` a catalogue member whose record carries the reward token
        `normalised-net-chip-delta` and the normaliser `T` — the game's chips in play —
        appended after the two of Rev 1 so `net-chips` stays the catalogue's **first**
        member and the declared default of §5, which is what a spec naming no `utility` is
        built under and must still report.  `docs/L1/reward-scale.md` §4 and ASM-10 then
        make it **one capacity** with `net-chips`: the reward is one arithmetic on a
        terminal transition, so at one architecture and one shape the two members' learners
        report the same `param_count`.  §4's container claim is driven on the same file:
        `agents.save` writes the member, `agents.load` restores the learner under it, and a
        `load` spec naming a different catalogue member is refused naming **both** values —
        so a model trained on one reward is never read as one trained on another
        (`docs/L1/utilities.md` §6, `docs/L1/protocol.md` §5, D-20, D-65, ASM-5).
        """
        names = self.catalogue()
        self.assertIn(
            NORMALISED_UTILITY,
            names,
            "the normalised reward is a catalogue member and not a reward `training` "
            "carries privately (docs/L1/reward-scale.md §2, docs/L1/utilities.md §2, "
            "D-65): %r" % (names,),
        )
        record = J.utility_record(NORMALISED_UTILITY)
        self.assertEqual(
            record["reward"],
            NORMALISED_REWARD,
            "the third member's record states its reward as the stable token "
            "`normalised-net-chip-delta`, the name `training`'s reward table is selected "
            "by (docs/L1/reward-scale.md §2, docs/L1/utilities.md §2): %r" % (record,),
        )
        self.assertEqual(
            record["normaliser"],
            NORMALISED_BY,
            "and its normaliser is `T`, the game's chips in play, and neither the "
            "starting stack alone nor the hand's own pot "
            "(docs/L1/reward-scale.md §2, §3, ASM-45): %r" % (record,),
        )
        spec_without_utility = dict(
            J.learner_spec("naive-stack", J.WIDTH_ONE, J.DEPTH_ONE, J.LEARNER_SEED)
        )
        spec_without_utility.pop("utility", None)
        by_default = J.build_learner(spec_without_utility)
        self.assertEqual(
            getattr(by_default, "utility", None),
            DEFAULT_UTILITY,
            "a learner spec that names no `utility` is built under the catalogue's "
            "**first** member — the declared default `net-chips` — and reports it, so the "
            "third member's arrival moved no default (docs/L1/utilities.md §5, "
            "docs/L1/reward-scale.md §2, §4, D-20): %r"
            % (getattr(by_default, "utility", None),),
        )
        self.assertGreater(
            J.param_count(by_default),
            0,
            "the default member's learner is sized like a learner, or there is no "
            "capacity to compare (docs/L2/agents/surface.md §5)",
        )
        normalised = J.build_learner(self.spec(NORMALISED_UTILITY))
        self.assertEqual(
            J.param_count(normalised),
            J.param_count(by_default),
            "at one architecture and one shape the normalised member's learner reports "
            "the `param_count` the default member's does, because the third member changes "
            "one terminal number and nothing of the state layout (docs/L1/reward-scale.md "
            "§4, docs/L1/utilities.md §3, ASM-10, D-65): %r against %r"
            % (J.param_count(normalised), J.param_count(by_default)),
        )
        path = self.checkpoint_path("%s-%s" % (NORMALISED_UTILITY, J.CHECKPOINT_BETA))
        encoder, saved = self.trained(NORMALISED_UTILITY, path)
        self.assertEqual(
            getattr(saved, "utility", None),
            NORMALISED_UTILITY,
            "the learner a spec names the third member to is trained under it and reads "
            "it back as the catalogue's own name (docs/L1/utilities.md §5, "
            "docs/L3/agents/checkpoint.md §1): %r" % (getattr(saved, "utility", None),),
        )
        metadata = J.container_metadata(path)
        self.assertEqual(
            str(metadata["utility"]),
            NORMALISED_UTILITY,
            "the container records the utility its learner was trained under, in the "
            "required `utility` field format 3 already carries, so no container geometry "
            "moved for the third member (docs/L1/reward-scale.md §4, "
            "docs/L1/utilities.md §6, D-20): %r" % (metadata.get("utility"),),
        )
        restored = J.load(None, path)
        self.assertEqual(
            getattr(restored, "utility", None),
            NORMALISED_UTILITY,
            "a member loaded from its path alone is restored under the member its file "
            "records (docs/L1/utilities.md §6, ASM-5): %r"
            % (getattr(restored, "utility", None),),
        )
        self.assertEqual(
            getattr(J.as_policy(restored, encoder, J.LEARNER_SEED), "utility", None),
            NORMALISED_UTILITY,
            "and the policy built from it carries the same member, so a table can name "
            "the objective the model was trained on (docs/L1/e2e-surface.md §2, "
            "docs/L1/utilities.md §7, D-20)",
        )
        by_spec = J.load(self.spec(NORMALISED_UTILITY), path)
        self.assertEqual(
            getattr(by_spec, "utility", None),
            NORMALISED_UTILITY,
            "a `load` spec naming the file's own member agrees on that compared key and "
            "loads under it (docs/L1/utilities.md §6): %r"
            % (getattr(by_spec, "utility", None),),
        )
        message = self.assert_refusal(
            "load",
            ((DEFAULT_UTILITY,), (NORMALISED_UTILITY,)),
            lambda: J.load(self.spec(DEFAULT_UTILITY), path),
            note="JOIN-AGT-12.3 a load spec naming %r against a %r container"
            % (DEFAULT_UTILITY, NORMALISED_UTILITY),
        )
        self.assertIn(
            DEFAULT_UTILITY,
            message,
            "the refusal names the member the spec asked for, so a reader can tell which "
            "side moved (docs/L1/utilities.md §6, D-20): %r" % (message,),
        )
        self.assertIn(
            NORMALISED_UTILITY,
            message,
            "and the member the file records, because a disagreement is refused naming "
            "**both** values and never resolved (docs/L1/utilities.md §6, D-20): %r"
            % (message,),
        )

    def test_join_agt_12_4_a_name_one_word_away_is_refused_at_the_spec_and_at_a_load(self):
        """JOIN-AGT-12.4 a utility name outside the catalogue is refused by name where it is declared and where a load spec carries it.

        `docs/L1/utilities.md` §5: "A name outside the catalogue is refused where it is
        declared, by name, and never mapped onto the default", and §6 makes a `load` spec's
        `utility` compared with the file's — a name the catalogue does not carry refused
        naming it, never read as the default.  The value this case spells is one word away
        from the third member's, so a membership test written as a prefix or a substring
        test would accept it; the catalogue is also checked to be **named** in the refusal,
        by requiring the one member's spelling the stray name does not contain, which no
        message can satisfy while silently reading the closest member.  Two of §5's three
        carriers are in this battery's reach — the learner spec `agents.build_learner`
        reads and the `load` spec `agents.load` compares — while the third, a pool member's
        `utility`, is `evaluation.build_pool`'s to refuse and is driven in that module's
        battery (`docs/L1/records.md` §7, D-20).
        """
        path = self.checkpoint_path("%s-%s" % (NORMALISED_UTILITY, J.CHECKPOINT_GAMMA))
        self.trained(NORMALISED_UTILITY, path)
        stray = self.spec(UNDECLARED_UTILITY)
        message = self.assert_refusal(
            "build_learner",
            (("utility",), (UNDECLARED_UTILITY,), (UTILITIES[1],)),
            lambda: J.build_learner(stray),
            note="JOIN-AGT-12.4 a spec naming %r" % (UNDECLARED_UTILITY,),
        )
        self.assertIn(
            UNDECLARED_UTILITY,
            message,
            "the refusal names the value the spec carried, so the caller can see which "
            "spelling it must fix (docs/L1/utilities.md §5, "
            "docs/L3/agents/errors.md §3): %r" % (message,),
        )
        refusal = self.assert_refusal(
            "load",
            (("utility",), (UNDECLARED_UTILITY,), (UTILITIES[1],)),
            lambda: J.load(stray, path),
            note="JOIN-AGT-12.4 a load spec naming %r" % (UNDECLARED_UTILITY,),
        )
        self.assertIn(
            UNDECLARED_UTILITY,
            refusal,
            "a `load` spec carrying a name the catalogue does not carry is refused naming "
            "it, and is never compared as the member it resembles "
            "(docs/L1/utilities.md §6, D-20): %r" % (refusal,),
        )
        self.assertTrue(
            os.path.exists(path),
            "the container the load spec is refused against is a file `agents.save` "
            "wrote, so the refusal is the name's and not a missing file's "
            "(docs/L1/utilities.md §6, ASM-5): %r" % (path,),
        )


if __name__ == "__main__":
    unittest.main()
