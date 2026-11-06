"""The seeding join -- HRNJ-7 (ASM-2).

`docs/L2/harness/surface.md` §1, §4: "the only path any entry point creates is `fixtures()`'s
scratch root", "no entry point seeds or advances the global `random` stream except by
delegating to `engine.new_hand` through `factory`, and none draws from a generator of its
own", and "a `hand` is a deal, so `engine.new_hand`'s seeding rule applies to it and to
nothing else here" (ASM-2, `protocol.md` §4, `docs/L3/harness/support.md` §2).

The join is the one no single module can check: `engine.new_hand` is the project's single
seeding point (`engine/surface.md` §1, §4), so a support module that borrowed that stream
for its own purposes would silently change every hand a battery deals -- and a harness that
seeded a generator of its own would make a case's deal depend on which case ran first.  The
battery therefore samples `random.getstate()` around the harness's own work, around each of
the six factory kinds, and around a case whose steps call nothing but `factory("hand",
seed)`, and requires the stream to stand exactly where the engine's own calls leave it
(`docs/L1/battery.md` §3 FAM-4, FAM-16, `docs/L2/harness/surface.md` §4, §5).
"""

import importlib.util
import os
import random
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
if "harness_join_support" in sys.modules:
    J = sys.modules["harness_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "harness_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["harness_join_support"] = J
    _spec.loader.exec_module(J)


class SeedsJoin(J.JoinCase):
    """HRNJ-7 -- only dealing, and only through the factory, moves the global stream."""

    def unchanged(self, call, what, citation):
        """Require `call` to leave the global stream as it found it, and restore it."""
        before = random.getstate()
        try:
            call()
        finally:
            after = random.getstate()
            random.setstate(before)
        self.assertEqual(
            after, before,
            "%s must leave the global `random` stream exactly as it found it: the only "
            "way the harness moves it is by delegating to `engine.new_hand` through "
            "`factory`, and the harness seeds nothing itself (%s, ASM-2, protocol.md §4)"
            % (what, citation),
        )
        return after

    def test_hrnj_7_1_the_harness_own_entry_points_do_not_move_the_stream(self):
        """HRNJ-7.1 `fixtures`, `expect`, `seam` and `timings` move nothing.

        `docs/L2/harness/surface.md` §1: "no entry point seeds or advances the global
        `random` stream except by delegating to `engine.new_hand` through `factory`, and
        none draws from a generator of its own" (ASM-2, `protocol.md` §4).  The battery
        samples the stream around each of them, around a seam's call, and around a driven
        case whose steps deal no hand -- because a driven case is the harness's own work,
        and the dealing inside a step is the engine's (`surface.md` §2, §7).
        """
        record, legal = J.readout_and_legal(J.DEAL_SEED)
        observation = J.encode(J.shared_encoder(), record)
        learner = J.build_learner(J.learner_spec())
        pool = J.shared_pool()
        episode = J.shared_episode()
        policy = J.seam(J.SEAM_LABEL)

        def read_pool():
            ids = J.member_ids(J.pool_members(pool))
            return {"chosen": ids[0], "legal": ids}

        def decide():
            index = J.chosen_index(J.act(learner, observation, J.legal_indices(legal)))
            return {"chosen": J.decode_action(index), "legal": list(legal)}

        probes = [
            ("harness.fixtures()", J.fixtures),
            ("harness.timings()", J.timings),
            ("harness.expect()", lambda: J.expect("zero-sum", episode)),
            ("harness.seam()", lambda: J.seam(J.SEAM_LABEL)),
            ("a seam's call", lambda: policy(record, legal)),
            ("harness.drive() over a case that deals nothing",
             lambda: J.drive({"id": "hrnj-7-1-no-deal", "steps": [read_pool, decide],
                              "expect": [{"kind": "legal-choice", "step": 0},
                                         {"kind": "legal-choice", "step": 1}]})),
        ]
        for what, call in probes:
            self.unchanged(
                call, what, "docs/L2/harness/surface.md §1, §5, §6, §7"
            )
        self.assertTrue(
            list(legal),
            "the value the probes were built from is a real decision of the engine's, so "
            "the stream was sampled around harness work and not around nothing "
            "(docs/L2/engine/surface.md §6): %r" % (list(legal),),
        )

    def test_hrnj_7_2_only_the_hand_kind_deals_and_it_deals_through_new_hand(self):
        """HRNJ-7.2 five factory kinds move nothing; the `hand` kind is `new_hand`'s deal.

        `docs/L2/harness/surface.md` §4: "one kind and one `options` value reach one call
        of one entry point and add no state of their own ... A `hand` is a deal, so
        `engine.new_hand`'s seeding rule applies to it and to nothing else here" (ASM-2).
        So the five objects that are not deals leave the stream where they found it, and a
        hand leaves it exactly where `engine.new_hand` leaves it at that seed -- the join
        that makes `factory("hand", seed)` a deal and not a second seeding point
        (`engine/surface.md` §4, §1, `docs/L3/harness/support.md` §2).
        """
        non_deals = [
            ("encoder", J.ENCODING),
            ("learner", J.learner_spec()),
            ("baseline", ("always-call", J.BASELINE_SEED)),
            ("rung", J.RUNG_NAME),
            ("pool", J.pool_declaration()),
        ]
        for kind, options in non_deals:
            self.unchanged(
                lambda kind=kind, options=options: J.factory(kind, options),
                "harness.factory(%r, ...)" % (kind,),
                "docs/L2/harness/surface.md §1, §4",
            )
        # The state a deal leaves is a function of its seed alone, so the comparison is
        # made twice from two different starting states: a seed the stream already stood
        # at would make one comparison a tautology (ASM-2, protocol.md §4).
        landings = []
        for offset in (0, 5):
            for _ in range(offset):
                random.random()
            start = random.getstate()
            try:
                J.factory("hand", J.DEAL_SEED)
                landings.append(("harness.factory", start, random.getstate()))
            finally:
                random.setstate(start)
            try:
                J.new_hand(J.DEAL_SEED)
                landings.append(("engine.new_hand", start, random.getstate()))
            finally:
                random.setstate(start)
        for what, _start, landing in landings:
            self.assertEqual(
                landing, landings[0][2],
                "a hand of this seed leaves the global stream where that seed leaves it, "
                "whatever state the caller's stream was in: the factory delegates the deal "
                "to `engine.new_hand` and seeds nothing of its own "
                "(docs/L2/harness/surface.md §4, docs/L2/engine/surface.md §4, ASM-2, "
                "protocol.md §4); %r landed elsewhere than %r"
                % (what, landings[0][0]),
            )
        self.assertNotEqual(
            landings[0][1], landings[2][1],
            "the two comparisons start from two different stream states, so the "
            "agreement above is the deal's and not the caller's (ASM-2, protocol.md §4)",
        )

    def test_hrnj_7_3_a_hand_the_factory_deals_perturbs_no_other_deal(self):
        """HRNJ-7.3 a case of factory hands leaves every other deal where it was.

        `docs/L2/harness/surface.md` §4 and `engine/surface.md` §4: "the same seed deals
        the same hand", and "a deal depends on its seed and not on the hands dealt before
        it".  A case whose steps call nothing but `factory("hand", seed)` therefore cannot
        change the deal another case gets, and a hand a case drove is reproducible from
        its own seed -- which is the property that makes a battery's red case reproducible
        (`protocol.md` §4, ASM-2, `docs/L1/battery.md` §3 FAM-4).
        """
        reference = J.canon(J.readout(J.new_hand(J.DEAL_SEED_OTHER)))
        played = J.canon(J.play_hand(
            J.DEAL_SEED,
            J.build_baseline("always-call", J.BASELINE_SEED),
            J.build_baseline("random", J.BASELINE_SEED_OTHER),
        ))

        def deal_only():
            hand = J.factory("hand", J.DEAL_SEED_OTHER)
            legal = tuple(J.legal_actions(hand))
            return {"chosen": legal[0], "legal": list(legal)}

        case = {
            "id": "hrnj-7-3-factory-hands",
            "steps": [deal_only, deal_only],
            "expect": [{"kind": "legal-choice", "step": 0},
                       {"kind": "legal-choice", "step": 1}],
        }
        result = J.drive(case)
        self.assert_verdict(
            result, "pass", "a case whose steps call nothing but factory('hand', seed)",
            "docs/L2/harness/surface.md §2, §4",
        )
        self.assertEqual(
            J.canon(J.readout(J.new_hand(J.DEAL_SEED_OTHER))), reference,
            "the deal another case gets is the deal its own seed names, after the driven "
            "case dealt: a hand depends on its seed and not on the hands dealt before it "
            "(docs/L2/engine/surface.md §4, ASM-2): %r" % (reference,),
        )
        self.assertEqual(
            J.canon(J.play_hand(
                J.DEAL_SEED,
                J.build_baseline("always-call", J.BASELINE_SEED),
                J.build_baseline("random", J.BASELINE_SEED_OTHER),
            )),
            played,
            "a driven hand is reproducible from its seed: the episode the engine plays "
            "after the factory dealt is the episode it played before "
            "(docs/L2/harness/surface.md §4, docs/L2/engine/surface.md §10, ASM-2, "
            "protocol.md §4): %r" % (played,),
        )
        self.assertEqual(
            int(result["hands"]), 0,
            "a hand handle is not a hand count: the steps returned composed legal choices, "
            "so the driver counted no hand and the deal stayed the engine's "
            "(docs/L2/harness/surface.md §2, H-5): %r" % (result["hands"],),
        )


if __name__ == "__main__":
    unittest.main()
