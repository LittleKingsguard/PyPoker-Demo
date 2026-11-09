"""FAM-16 — the blind instances: one per ``general`` row of e2e-surface.md §5.

`docs/L1/battery.md` §4 (D-15).  ``e2e-surface.md`` §5 marks 37 rows ``general`` — 8 in
``engine``, 3 in ``features``, 7 in ``agents``, 9 in ``evaluation``, 4 in ``training``
and 6 in ``harness``.  For each of them one case below names that row as its **subject**
and drives it with an **instance** invented here, from the declared surface alone:

* seeds ``6174``, ``271828``, ``90210``, ``5150``, ``131``, ``4711``, ``8086``,
  ``314159``, ``424242``, ``99991`` and the table seeds ``40961`` and ``7817`` — the
  protocol's seed set is ``0, 1, 2``;
* learner widths ``61``, ``96`` and ``48`` at depths ``2``, ``3`` and ``4`` — the ladder
  fixes a parameter budget, not these sizes (ASM-10);
* cell sizes ``23`` and ``14`` hands, and ``37`` and ``11`` hands for a single cell —
  the tables' cells are 120 and 1,500 (league.md §6);
* a training budget of ``250`` and ``60`` hands per variant per seed — the live budget is
  1,000 and the shipped one 200,000 (ladder.md §6);
* the version tags ``kestrel``, ``bramble``, ``thistle``, ``quarry``, ``marlin``,
  ``osprey``, ``nimbus`` with their invented lineages, steps and samples, each backed by
  a checkpoint the case writes — the league's own versions are none of these;
* the seventh rung ``R7`` and its ``deep-sparse`` / ``wide-sparse`` pair, and the
  unregistered name ``R7-bottleneck``;
* the seam labels ``echo-legal`` and ``seeded-legal`` — a seam takes **any label**, because
  its contract is the policy protocol and not the label, with ``recording`` and
  ``synthetic`` the documented behaviours (``e2e-surface.md`` §3.6, ``records.md`` §14) —
  and the **observed values** this battery invents for a discovered expectation kind.  The
  expectation kinds are the harness's own and are read from ``harness.fixtures()``, so no
  kind is invented here: the battery invents what is observed, never the vocabulary that
  judges it (D-13, D-15, ``battery.md`` §4).

A case's path may exercise other entry points; being the **subject** is what makes it a
blind instance of that row.
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

_INVENTED = {}


class FAM16Blind(S.SurfaceCase):
    """37 cases; each names one ``general`` entry point as its subject."""

    # -- helpers -----------------------------------------------------------
    def indices_for(self, legal):
        return set(self.ep("features", "legal_indices")(legal))

    def invented_learner(self, width=61, depth=2, seed=S.SEED_I):
        return self.learner(width=width, depth=depth, seed=seed)

    def invented_table(self):
        """The battery's own table: one invented version plus one invented variant."""
        if "table" in _INVENTED:
            return _INVENTED["table"]
        pool = self.pool(tags=("kestrel",), width=61, depth=2)
        variant = self.variant_policy(seed=S.SEED_H, width=61, depth=2)
        matrix = self.matrix_of(pool, [variant], "live")
        value = {
            "pool": pool,
            "variant": variant,
            "matrix": matrix,
            "rating": self.rating_of(matrix),
        }
        _INVENTED["table"] = value
        return value

    def counts(self, cell):
        """``[(wins, ties, losses)]`` of a cell's directions."""
        return [R.direction_counts(row) for row in R.direction_rows(cell)]

    def expect_verdict(self, kind, observation):
        """What one expectation answers, its named refusal included.

        ``e2e-surface.md`` §3.6 contracts ``expect`` for a pass or a named failure, and §2
        lets an invalid argument be refused by raising with the violated contract named.
        """
        try:
            return self.ep("harness", "expect")(kind, observation)
        except S.SurfaceAbsent:
            raise
        except Exception as exc:
            return "%s: %s" % (type(exc).__name__, exc)

    # ======================================================================
    # engine — 8 general rows
    # ======================================================================
    def test_fam16_01_engine_new_hand(self):
        """FAM-16.1 engine.new_hand — instance: seed 424242, with 99991 as contrast."""
        first = S.canon(self.readout(self.hand(S.SEED_I)))
        second = S.canon(self.readout(self.hand(S.SEED_I)))
        self.assertEqual(first, second, "seed 424242 deals the same hand twice (ASM-2)")
        other = S.canon(self.readout(self.hand(S.SEED_J)))
        self.assertNotEqual(
            first,
            other,
            "seed 99991 does not deal the hand seed 424242 deals (ASM-2)",
        )

    def test_fam16_02_engine_readout(self):
        """FAM-16.2 engine.readout — instance: the first decision at seed 99991."""
        readout = self.readout(self.hand(S.SEED_J))
        self.assertEqual(
            set(readout),
            set(S.READOUT_FACTS),
            "the readout is exactly the eleven declared facts (e2e-surface §2, D-21): %r"
            % (readout,),
        )
        self.assertEqual(len(readout["hole"]), 2, "the acting seat holds two cards")
        self.assertEqual(len(readout["board"]), 0, "no public card before the flop")
        self.assertEqual(readout["history"], [], "nothing has happened yet at the first decision")
        # D-21's eleventh fact at this invented decision: fewer than five cards are known
        # before the flop, so no five-card hand exists and the fact is `None` — never a
        # `0`, which is what a high-card hand reads as from the flop onward
        # (e2e-surface §2, folders.md §3, ASM-30).
        self.assertIsNone(
            S.readout_fact(readout, "hand_class"),
            "before the flop `hand_class` is None, never a class (folders.md §3, ASM-30): %r"
            % (readout.get("hand_class"),),
        )
        # ... and the same hand, played to the flop, reads an integer 0..8 there.
        post_flop = None
        for _seat, later, _legal, _action, _index in self.seated_walk(
            S.SEED_J, {"default": self.baseline("always-call", S.SEED_D)}
        ):
            if str(S.readout_fact(later, "street")).strip().lower() == "preflop":
                continue
            post_flop = S.readout_fact(later, "hand_class")
            break
        self.assertIsNotNone(
            post_flop,
            "seed 99991's hand must reach a flop, turn or river decision, so the post-flop "
            "half of `hand_class`'s contract is observed (folders.md §3)",
        )
        self.assertTrue(
            S.is_count(post_flop),
            "from the flop onward `hand_class` is the class of the best five-card hand of "
            "hole plus board, an integer (e2e-surface §2, folders.md §3, ASM-30): %r"
            % (post_flop,),
        )
        self.assertTrue(
            0 <= int(post_flop) <= 8,
            "the nine classes are 0..8, high card 0 and straight flush 8 (folders.md §3): %r"
            % (post_flop,),
        )

    def test_fam16_03_engine_legal_actions(self):
        """FAM-16.3 engine.legal_actions — instance: the first decision at seed 131."""
        hand = self.hand(S.SEED_E)
        legal = self.legal(hand)
        self.assertGreaterEqual(
            len(legal),
            2,
            "facing the big blind, folding and continuing are both legal: %r" % (legal,),
        )
        for descriptor in legal:
            advanced = self.ep("engine", "apply_action")(self.hand(S.SEED_E), descriptor)
            self.assertIsNotNone(
                advanced,
                "every descriptor legal_actions returns is applicable at seed 131: %r"
                % (descriptor,),
            )

    def test_fam16_04_engine_apply_action(self):
        """FAM-16.4 engine.apply_action — instance: the first action of seed 4711's hand."""
        hand = self.hand(S.SEED_F)
        before = self.readout(hand)
        legal = self.legal(hand)
        action = self.baseline("always-call", S.SEED_D)(before, legal)
        after = self.readout(self.ep("engine", "apply_action")(hand, action))
        self.assertEqual(
            len(after["history"]),
            len(before["history"]) + 1,
            "one applied action is one entry in the public history: %r" % (after["history"],),
        )

    def test_fam16_05_engine_is_terminal(self):
        """FAM-16.5 engine.is_terminal — instance: a hand at seed 90210 played out."""
        engine = self.mod("engine")
        hand = self.hand(S.SEED_C)
        self.assertFalse(engine.is_terminal(hand), "a fresh hand is not over")
        finished = self.finished_hand(S.SEED_C, limit=200)
        self.assertTrue(
            engine.is_terminal(finished),
            "a hand of this short-stack game ends within 200 decisions (ASM-6)",
        )

    def test_fam16_06_engine_payoffs(self):
        """FAM-16.6 engine.payoffs — instance: the hand at seed 6174 played to the end."""
        payoffs = self.ep("engine", "payoffs")(self.finished_hand(S.SEED_A))
        values = S.numbers(payoffs)
        self.assertEqual(len(values), 2, "a heads-up hand pays two seats: %r" % (payoffs,))
        self.assertEqual(sum(values), 0, "the payoff is zero-sum: %r" % (payoffs,))

    def test_fam16_07_engine_play_hand(self):
        """FAM-16.7 engine.play_hand — instance: seed 5150, a 61-wide learner vs oracle."""
        policy = self.policy(self.invented_learner(61, 2, S.SEED_J), seed=S.SEED_J)
        episode = self.play(S.SEED_D, policy, self.baseline("oracle", S.SEED_H))
        text = S.flatten_text(episode)
        for fact in S.READOUT_FACTS:
            self.assertIn(
                fact,
                text,
                "every decision of the episode carries its facts, including %r: %r"
                % (fact, episode),
            )
        payoffs = S.numbers(S.find_values(episode, "payoff"))
        self.assertTrue(payoffs, "the episode carries its payoffs: %r" % (episode,))
        self.assertEqual(sum(payoffs), 0, "the episode's payoffs are zero-sum (ASM-12)")
        by_seat = {}
        for decision in R.decision_records(episode):
            reward = R.decision_reward(decision)
            if reward != 0:
                by_seat.setdefault(R.decision_seat(decision), []).append(reward)
        self.assertLessEqual(
            len(by_seat),
            2,
            "a heads-up hand has two seats, so at most two terminal decisions carry a reward "
            "(records.md §5, ASM-12): %r" % (by_seat,),
        )
        for seat, values in by_seat.items():
            self.assertEqual(
                len(values),
                1,
                "the reward is the hand's outcome and not a shaped term, so a seat carries at "
                "most one non-zero reward, at its terminal decision — a non-split hand "
                "therefore carries one per seat, two in all (records.md §5, ASM-12): seat %r "
                "carries %r" % (seat, values),
            )
            self.assertIn(
                values[0],
                payoffs,
                "each terminal reward is that seat's net chip delta (ASM-12): %r not in %r"
                % (values[0], payoffs),
            )

    def test_fam16_08_engine_equity(self):
        """FAM-16.8 engine.equity — instance: 257 samples at seed 90210, 97 as contrast."""
        equity = self.ep("engine", "equity")(self.hand(S.SEED_C), S.SEED_C, S.EQUITY_SAMPLES)
        self.assertGreaterEqual(equity, 0.0, "a win probability cannot be negative")
        self.assertLessEqual(equity, 1.0, "a win probability cannot exceed one")
        again = self.ep("engine", "equity")(self.hand(S.SEED_C), S.SEED_C, S.EQUITY_SAMPLES)
        self.assertEqual(
            equity,
            again,
            "the same hand at the same seed and sample count is the same estimate (ASM-4)",
        )
        coarse = self.ep("engine", "equity")(self.hand(S.SEED_C), S.SEED_C, 97)
        self.assertGreaterEqual(coarse, 0.0)
        self.assertLessEqual(coarse, 1.0)

    # ======================================================================
    # features — 3 general rows
    # ======================================================================
    def test_fam16_09_features_encode(self):
        """FAM-16.9 features.encode — instance: the readout at seed 99991."""
        encoder = self.encoder(S.FLAT)
        readout = self.readout(self.hand(S.SEED_J))
        observation = self.ep("features", "encode")(encoder, readout)
        again = self.ep("features", "encode")(encoder, readout)
        self.assertEqual(
            S.canon(observation),
            S.canon(again),
            "one readout encodes to one observation: %r" % (observation,),
        )
        spec = self.ep("features", "observation_spec")(encoder)
        shape = [int(number) for number in S.numbers(S.find_values(spec, "shape"))]
        if hasattr(observation, "shape"):
            self.assertEqual(
                list(observation.shape),
                shape,
                "the encoded observation has the declared shape: %r against %r"
                % (observation.shape, shape),
            )

    def test_fam16_10_features_legal_indices(self):
        """FAM-16.10 features.legal_indices — instance: seed 131's first two decisions."""
        walk = self.decision_walk(S.SEED_E, self.baseline("always-call", S.SEED_D), limit=2)
        self.assertGreaterEqual(len(walk), 2, "the case needs two decisions of one hand")
        facing, checking = walk[0], walk[1]
        self.assertEqual(
            self.indices_for(facing[2]),
            {0, 1, 2},
            "facing the big blind, fold, call and raise are legal (D-2)",
        )
        self.assertEqual(
            checking[1]["to_call"],
            0,
            "after a call the big blind may check for nothing",
        )
        self.assertEqual(
            self.indices_for(checking[2]),
            {1, 2},
            "with nothing to call, folding is not among the legal indices (e2e-surface §2)",
        )

    def test_fam16_11_features_decode_action(self):
        """FAM-16.11 features.decode_action — instance: seed 4711's legal indices."""
        legal = self.legal(self.hand(S.SEED_F))
        indices = self.indices_for(legal)
        self.assertEqual(
            len(indices),
            len(legal),
            "one index per legal descriptor at seed 4711's first decision: %r" % (legal,),
        )
        for index in indices:
            descriptor = self.ep("features", "decode_action")(index)
            self.assertIsNotNone(
                self.ep("engine", "apply_action")(self.hand(S.SEED_F), descriptor),
                "decode_action(%r) gives a descriptor apply_action accepts (D-2)" % (index,),
            )

    # ======================================================================
    # agents — 7 general rows
    # ======================================================================
    def test_fam16_12_agents_build_learner(self):
        """FAM-16.12 agents.build_learner — instance: 61 wide, 2 deep, seed 424242."""
        learner = self.invented_learner(61, 2, S.SEED_I)
        count = self.ep("agents", "param_count")(learner)
        self.assertGreater(count, 0, "a built learner has trainable parameters")
        twin = self.invented_learner(61, 2, S.SEED_I)
        self.assertEqual(
            self.ep("agents", "param_count")(twin),
            count,
            "one spec builds one learner (ASM-10)",
        )

    def test_fam16_13_agents_param_count(self):
        """FAM-16.13 agents.param_count — instance: 61 wide against 96 wide at depth 2."""
        narrow = self.ep("agents", "param_count")(self.invented_learner(61, 2, S.SEED_I))
        broad = self.ep("agents", "param_count")(self.invented_learner(96, 2, S.SEED_I))
        self.assertTrue(S.is_count(narrow), "the parameter count is an integer count: %r" % (narrow,))
        self.assertTrue(S.is_count(broad), "the parameter count is an integer count: %r" % (broad,))
        self.assertGreater(
            broad,
            narrow,
            "a 96-wide stack has more parameters than a 61-wide one at one depth (ASM-10): "
            "%r against %r" % (broad, narrow),
        )

    def test_fam16_14_agents_act(self):
        """FAM-16.14 agents.act — instance: 61 wide at seed 99991 on seed 5150's decisions."""
        learner = self.invented_learner(61, 2, S.SEED_J)
        encoder = self.encoder()
        walk = self.decision_walk(S.SEED_D, self.baseline("always-call", S.SEED_D), limit=3)
        self.assertTrue(walk, "the case drove no decision")
        for _hand, readout, legal, _action, _index in walk:
            index = self.action_index(self.act(learner, encoder, readout))
            self.assertIn(
                index,
                self.indices_for(legal),
                "agents.act chooses an index the decision allows: %r" % (index,),
            )

    def test_fam16_15_agents_learn(self):
        """FAM-16.15 agents.learn — instance: 61 wide at seed 131 on seed 90210's hand."""
        learner = self.invented_learner(61, 2, S.SEED_E)
        statistics = self.ep("agents", "learn")(learner, self.transitions(S.SEED_C))
        values = [value for value in S.numbers(statistics) if value == value]
        self.assertTrue(
            values,
            "agents.learn returns the update's own statistics for the curve: %r"
            % (statistics,),
        )

    def test_fam16_16_agents_save(self):
        """FAM-16.16 agents.save — instance: 61 wide at seed 424242, an invented path."""
        learner = self.invented_learner(61, 2, S.SEED_I)
        target = os.path.join(self.scratch(), "fam16-16-wide61-d2.ckpt")
        written = self.ep("agents", "save")(learner, target)
        self.assertTrue(
            os.path.exists(str(written)),
            "agents.save returns the path it wrote: %r" % (written,),
        )
        self.assertGreater(
            os.path.getsize(str(written)),
            0,
            "the checkpoint carries the learner's state: %r" % (written,),
        )

    def test_fam16_17_agents_load(self):
        """FAM-16.17 agents.load — instance: the same invented checkpoint, restored."""
        spec = self.learner_spec(width=61, depth=2, seed=S.SEED_I)
        learner = self.ep("agents", "build_learner")(spec)
        path = self.ep("agents", "save")(
            learner, os.path.join(self.scratch(), "fam16-17-wide61-d2.ckpt")
        )
        loaded = self.ep("agents", "load")(spec, path)
        self.assertEqual(
            self.ep("agents", "param_count")(loaded),
            self.ep("agents", "param_count")(learner),
            "the restored learner has the capacity of the saved one (ASM-5)",
        )
        encoder = self.encoder()
        readout = self.readout(self.hand(S.SEED_J))
        self.assertEqual(
            self.action_index(self.act(learner, encoder, readout)),
            self.action_index(self.act(loaded, encoder, readout)),
            "the restored learner decides as the saved one on the same readout (ASM-5)",
        )

    def test_fam16_18_agents_as_policy(self):
        """FAM-16.18 agents.as_policy — instance: 61 wide at seed 314159, seed 8086's hand."""
        learner = self.invented_learner(61, 2, S.SEED_H)
        policy = self.ep("agents", "as_policy")(learner, self.encoder(), S.SEED_H)
        walk = self.decision_walk(S.SEED_G, policy, limit=3)
        self.assertTrue(walk, "the learner's policy answered no decision")
        for _hand, _readout, legal, action, index in walk:
            self.assertIn(index, self.indices_for(legal), "a learner policy chooses legally")
            self.assertTrue(
                any(S.canon(action) == S.canon(candidate) for candidate in legal),
                "a learner policy returns a descriptor from legal_actions: %r" % (action,),
            )
        episode = self.play(S.SEED_G, policy, self.baseline("always-call", S.SEED_D))
        self.assertEqual(
            sum(S.numbers(S.find_values(episode, "payoff"))),
            0,
            "a learner policy plays a zero-sum hand like any other (ASM-12)",
        )

    # ======================================================================
    # evaluation — 9 general rows
    # ======================================================================
    def test_fam16_19_evaluation_build_pool(self):
        """FAM-16.19 evaluation.build_pool — instance: four invented versions at M = 5."""
        versions = R.version_chain(self, ("kestrel", "bramble", "thistle", "quarry"))
        pool = self.pool({"members": versions, "m": S.LEAGUE_BOUND, "frozen": True})
        row = self.members(pool)
        members = R.member_ids(row)
        self.assertEqual(
            len(R.version_members(row)),
            len(versions),
            "a pool under its bound keeps every version it was offered (league.md §2): %r"
            % (members,),
        )
        self.assertEqual(
            len(members),
            len(versions) + len(S.ANCHOR_BASELINES),
            "the baselines are added and pinned, so a pool of four versions has seven "
            "members (league.md §2): %r" % (members,),
        )

    def test_fam16_20_evaluation_pool_members(self):
        """FAM-16.20 evaluation.pool_members — instance: the same invented membership."""
        versions = R.version_chain(self, ("kestrel", "bramble"))
        pool = self.pool({"members": versions, "m": S.LEAGUE_BOUND, "frozen": True})
        row = self.members(pool)
        ordered = R.member_ids(row)
        self.assertEqual(
            R.pool_bound(row),
            S.LEAGUE_BOUND,
            "pool_members reports the bound M the pool holds to (e2e-surface §3.4): %r"
            % (row,),
        )
        self.assertEqual(
            R.version_members(row),
            ["version-kestrel", "version-bramble"],
            "the version members come back in lineage order — bramble descends from kestrel "
            "(records.md §8) — as one fact of this case; where the pinned baselines sit in "
            "that ordered list is left free, so the versions are not required to come first: "
            "%r" % (ordered,),
        )
        for baseline in S.ANCHOR_BASELINES:
            self.assertIsNotNone(
                R.baseline_member(ordered, baseline),
                "the read-back names the %r baseline beside the versions, pinned wherever it "
                "sits in the order (league.md §2): %r" % (baseline, ordered),
            )

    def test_fam16_21_evaluation_offer(self):
        """FAM-16.21 evaluation.offer — instance: a sixth version offered at M = 5."""
        versions = R.version_chain(self, ("kestrel", "bramble", "thistle", "quarry",
                                          "marlin"))
        # A case that advances a window declares it unfrozen: records.md §8 ties frozen-ness
        # to the membership not changing while the pool is used.
        pool = self.pool({"members": versions, "m": S.LEAGUE_BOUND, "frozen": False})
        before = R.version_members(self.members(pool))
        advanced = self.ep("evaluation", "offer")(
            pool, R.next_version(self, "osprey", versions[-1], seed=S.SEED_I)
        )
        after = R.version_members(self.members(advanced))
        self.assertIn(
            "version-osprey",
            after,
            "the offered version descends from the window's newest member and so joins it "
            "(records.md §7): %r" % (after,),
        )
        self.assertNotIn(
            "version-kestrel",
            after,
            "the oldest evictable version is the one offer drops (ASM-18): %r" % (after,),
        )
        self.assertEqual(
            set(after),
            set(before[1:]) | {"version-osprey"},
            "offer drops one version and keeps the rest of the window (league.md §2): "
            "before %r, after %r" % (before, after),
        )

    def test_fam16_22_evaluation_opponent(self):
        """FAM-16.22 evaluation.opponent — instance: three invented versions, eight seeds."""
        versions = R.version_chain(self, ("kestrel", "bramble", "thistle"))
        pool = self.pool({"members": versions, "m": S.LEAGUE_BOUND, "frozen": True})
        drawn = []
        for seed in (S.SEED_A, S.SEED_B, S.SEED_C, S.SEED_D, S.SEED_E, S.SEED_F,
                     S.TABLE_SEED_A, S.TABLE_SEED_B):
            policy = self.opponent(pool, seed)
            self.assertTrue(callable(policy), "opponent returns a policy of §2: %r" % (policy,))
            first = [entry[4] for entry in self.decision_walk(S.SEED_H, policy, limit=3)]
            second = [entry[4] for entry in self.decision_walk(S.SEED_H, policy, limit=3)]
            self.assertEqual(
                first,
                second,
                "one pool and one seed draw one opponent (ASM-2): %r against %r"
                % (first, second),
            )
            drawn.append(tuple(first))
        self.assertGreaterEqual(
            len(set(drawn)),
            2,
            "a draw over a pool of six members does not answer with one fixed policy for "
            "every seed (D-16): %r" % (sorted(set(drawn)),),
        )

    def test_fam16_23_evaluation_match(self):
        """FAM-16.23 evaluation.match — instance: 23 hands at table seed 40961."""
        left = self.policy(self.invented_learner(61, 2, S.SEED_B), seed=S.SEED_B)
        right = self.baseline("oracle", S.SEED_E)
        cell = self.match(left=left, right=right, hands=S.CELL_HANDS, seed=S.TABLE_SEED_A)
        self.assertEqual(
            R.cell_hands(cell),
            S.CELL_HANDS,
            "the cell plays the invented 23 hands (records.md §9): %r" % (cell,),
        )
        for wins, ties, losses in self.counts(cell):
            self.assertEqual(
                wins + ties + losses,
                S.CELL_HANDS,
                "each direction accounts for all 23 hands (league.md §3): %r" % (cell,),
            )

    def test_fam16_24_evaluation_matrix(self):
        """FAM-16.24 evaluation.matrix — instance: the battery's own membership, K = 5."""
        table = self.invented_table()
        matrix = table["matrix"]
        members = R.matrix_members(matrix)
        cells = R.matrix_cells(matrix)
        k = len(members)
        self.assertEqual(
            k,
            len(R.member_ids(self.members(table["pool"]))) + 1,
            "the table's membership is the invented pool plus its one variant (league.md "
            "§4): %r" % (members,),
        )
        self.assertEqual(
            len(cells),
            k * (k - 1) // 2,
            "a K = %d table carries %d unordered pairs: %r"
            % (k, k * (k - 1) // 2, members),
        )
        self.assertIn(
            "version-kestrel",
            members,
            "the invented version is a row and a column of the table (D-16): %r" % (members,),
        )

    def test_fam16_25_evaluation_rating(self):
        """FAM-16.25 evaluation.rating — instance: the fitted rating of that table."""
        table = self.invented_table()
        matrix, rating = table["matrix"], table["rating"]
        entries = R.rating_entries(rating)
        members = R.matrix_members(matrix)
        self.assertEqual(
            set(entries),
            set(members),
            "the rating names exactly the invented table's members, one value each "
            "(records.md §11): %r against %r" % (sorted(entries), members),
        )
        self.assertEqual(
            R.rating_entry_count(rating),
            len(members),
            "the invented table's rating lists one entry per member, repeats included in "
            "the count so a member listed twice cannot pass as one (records.md §11, "
            "battery.md §2): %r" % (rating,),
        )
        baselines = []
        for name in S.ANCHOR_BASELINES:
            member = R.baseline_member(members, name)
            self.assertIsNotNone(member, "the %r baseline is a rated member" % (name,))
            key = member if member in entries else next(
                (candidate for candidate in entries if R.tok(candidate) == R.tok(member)),
                None,
            )
            self.assertIsNotNone(key, "the rating carries the %r baseline's value" % (member,))
            value = R.rating_value(entries[key])
            first, second = R.rating_interval(entries[key])
            # records.md §11 fixes neither the bounds' names nor their order, so the
            # interval is the pair whose extent holds the value, read as a pair.
            self.assertGreaterEqual(
                value,
                first,
                "the value lies between the two bounds of its own interval, whichever "
                "order the invented record states them in: %r" % (entries[key],),
            )
            self.assertLessEqual(
                value,
                second,
                "the value lies between the two bounds of its own interval, whichever "
                "order the invented record states them in: %r" % (entries[key],),
            )
            baselines.append(value)
        self.assertAlmostEqual(
            sum(baselines) / len(baselines),
            0.0,
            places=3,
            msg="the baselines' mean is anchored at zero (league.md §5, ASM-17): %r"
                % (baselines,),
        )

    def test_fam16_26_evaluation_policy_from(self):
        """FAM-16.26 evaluation.policy_from — instance: the 61-wide checkpoint at 8086."""
        spec = self.learner_spec(width=61, depth=2, seed=S.SEED_G)
        learner = self.ep("agents", "build_learner")(spec)
        path = self.ep("agents", "save")(
            learner, os.path.join(self.scratch(), "fam16-26-wide61.ckpt")
        )
        policy = self.ep("evaluation", "policy_from")(path)
        walk = self.decision_walk(S.SEED_F, policy, limit=3)
        self.assertTrue(walk, "the loaded policy answered no decision")
        encoder = self.encoder()
        for _hand, readout, legal, action, _index in walk:
            self.assertIn(
                self.chosen_index(legal, action),
                self.indices_for(legal),
                "a policy loaded in evaluation mode chooses a legal action (D-16): %r"
                % (action,),
            )
            self.assertEqual(
                self.chosen_index(legal, action),
                self.action_index(self.act(learner, encoder, readout)),
                "policy_from loads the checkpoint its learner was saved from (protocol.md §5)",
            )

    def test_fam16_27_evaluation_report(self):
        """FAM-16.27 evaluation.report — instance: R7's report over the invented table."""
        table = self.invented_table()
        pair_cell = self.match(
            left=self.member_policy("kestrel"),
            right=self.member_policy("bramble"),
            hands=S.CELL_HANDS_SMALL,
            seed=S.TABLE_SEED_B,
        )
        record = self.evidence_record(
            self.run_record(S.custom_rung(), (S.SEED_A,), S.BUDGET_TINY),
            matrix=table["matrix"],
            rating=table["rating"],
            pool_row=self.members(table["pool"]),
            axis_row=pair_cell,
            seeds=(S.SEED_A,),
            budget=S.BUDGET_TINY,
        )
        report = self.report_of("R7", record, table["matrix"], table["rating"])
        self.assertTrue(S.is_mapping(report), "the report is a record")
        for family in S.FAMILIES:
            self.assertTrue(
                S.has_family(report, family),
                "the invented rung's report carries the %r family (protocol.md §1): %r"
                % (family, sorted(str(key) for key in report)),
            )
        self.assertIn(
            str(S.SEED_A),
            S.flatten_text(report),
            "the report carries the invented seed set it was run at (protocol.md §2)",
        )

    # ======================================================================
    # training — 4 general rows
    # ======================================================================
    def test_fam16_28_training_rung(self):
        """FAM-16.28 training.rung — instance: the unregistered name 'R7-bottleneck'."""
        name = "R7-bottleneck"
        text = S.refusal_text(lambda: self.ep("training", "rung")(name))
        self.assertIsNotNone(
            text,
            "training.rung refuses a rung name outside the registry (e2e-surface §2)",
        )
        self.assertIn(
            S._family_token(name),
            S._family_token(text),
            "the refusal names the rung it could not resolve: %r" % (text,),
        )
        entries = S.variant_entries(self.ep("training", "rung")("R4"))
        self.assertEqual(
            len(entries),
            2,
            "the registry still resolves its own rungs to their declared pairs (ladder.md §2)",
        )

    def test_fam16_29_training_run(self):
        """FAM-16.29 training.run — instance: the seventh rung, seed 131, 60 hands."""
        record = self.run_record(S.custom_rung(), (S.SEED_E,), S.BUDGET_TINY)
        self.assertTrue(S.is_mapping(record), "training.run returns a run record")
        self.assertTrue(
            self.curves_of(record),
            "the seventh rung's record carries per-seed curves: %r"
            % (sorted(str(key) for key in record),),
        )
        self.assertIn(
            S.SEED_E,
            [int(number) for number in S.declared_numbers(record, "seeds", "seed")],
            "the run record carries the invented seed it actually used: %r" % (record,),
        )
        self.assertIn(
            str(S.BUDGET_TINY),
            S.flatten_text(record),
            "the run record carries the invented sample budget: %r" % (record,),
        )
        paths = R.checkpoint_paths_of(record)
        variants = len(S.variant_entries(S.custom_rung()))
        least, most = R.checkpoint_span(S.LEAGUE_BOUND, variants, 1)
        self.assertGreaterEqual(
            len(paths),
            least,
            "the seventh rung's %d variants write one final checkpoint each, so the run "
            "record names at least %d artefact (records.md §12): %r"
            % (variants, least, paths),
        )
        self.assertLessEqual(
            len(paths),
            most,
            "records.md §12 makes the checkpoints key the retained snapshots plus the final "
            "model per variant per seed: at most %d at M = %d for %d variant × seed pairs, "
            "even though the run wrote ten snapshots per variant (protocol.md §5, ASM-18): %r"
            % (most, S.LEAGUE_BOUND, variants, paths),
        )
        for path in paths:
            self.assertTrue(
                os.path.exists(path),
                "a run of the battery's own configuration writes artefacts that exist: %r"
                % (path,),
            )

    def test_fam16_30_training_fairness(self):
        """FAM-16.30 training.fairness — instance: the seventh rung's invented pair."""
        variants = S.variant_entries(S.custom_rung())
        result = self.ep("training", "fairness")(variants[0], variants[1])
        axis = S.axis_text(result)
        self.assertTrue(
            "depth" in axis or "width" in axis or "spars" in axis,
            "fairness names the pair's own axis (ladder.md §4): %r" % (axis,),
        )
        body = S.flatten_text(result)
        for token in ("budget", "seed", "param"):
            self.assertIn(
                token,
                body,
                "fairness reports what the pair holds constant, including %r: %r"
                % (token, result),
            )

    def test_fam16_31_training_checkpoints(self):
        """FAM-16.31 training.checkpoints — instance: the battery's own artefacts."""
        invented = R.version_chain(self, ("kestrel", "bramble"))
        own_paths = {str(version["path"]) for version in invented}
        index = self.ep("training", "checkpoints")()
        listed = S.checkpoint_path_listing(index)
        self.assertTrue(
            listed,
            "the shipped index names the shipped checkpoints: %r" % (index,),
        )
        carried = own_paths & set(listed)
        self.assertEqual(
            carried,
            set(),
            "the index is the shipped set — each rung variant's final model plus the pool's "
            "retained versions — and not every artefact that happens to be on disk "
            "(protocol.md §5): %r" % (sorted(carried),),
        )
        # What an index really can violate: the shipped set is the set the repository
        # carries, so every path it names is an artefact inside the repository, and every
        # one of them is a member a talk can load (protocol.md §5, e2e-surface §3.4).  An
        # index that scanned a scratch or a cache directory — the battery's own included —
        # is not the shipped set.
        root = os.path.realpath(S.repo_root())
        for path in listed:
            # A relative path the index returns is relative to the repository the battery
            # runs from; resolving it there keeps the assertion about where the artefact
            # ships and not about the caller's working directory.
            resolved = str(path)
            if not os.path.isabs(resolved):
                resolved = os.path.join(root, resolved)
            resolved = os.path.realpath(resolved)
            self.assertTrue(
                os.path.exists(resolved),
                "the index names artefacts that exist, so a talk can load a member "
                "(protocol.md §5): %r" % (path,),
            )
            self.assertTrue(
                resolved == root or resolved.startswith(root + os.sep),
                "the index names the artefacts the repository ships, all of them inside the "
                "repository, and never a file from a scratch or cache directory "
                "(protocol.md §5, D-16): %r" % (path,),
            )
        loadable = self.ep("evaluation", "policy_from")(listed[0])
        self.assertTrue(
            callable(loadable),
            "the index names league members, so the first artefact it names loads through "
            "evaluation.policy_from as a policy of e2e-surface §2: %r" % (listed[0],),
        )

    # ======================================================================
    # harness — 6 general rows
    # ======================================================================
    def test_fam16_32_harness_drive(self):
        """FAM-16.32 harness.drive — instance: case 'fam16-32-blind' at seed 424242."""
        ran = []

        def step():
            ran.append("fam16-32")
            return self.play(S.SEED_I)

        case = {
            "id": "fam16-32-blind",
            "steps": [step],
            # The driver's expectation is a kind the fixture lists — the vocabulary is the
            # harness's own, the case is this battery's (e2e-surface §3.6, records.md §14).
            "expect": [self.an_expectation_kind()],
        }
        result = self.ep("harness", "drive")(case)
        self.assertEqual(
            ran,
            ["fam16-32"],
            "the driver runs the invented case's own step, exactly once: %r" % (result,),
        )
        self.assertIsNotNone(
            S.verdict(result),
            "the driver judges the invented case and records a verdict: %r" % (result,),
        )
        self.assertIn(
            S._family_token("fam16-32"),
            S._family_token(S.flatten_text(result)),
            "the driver's record names the invented case it ran: %r" % (result,),
        )

    def test_fam16_33_harness_fixtures(self):
        """FAM-16.33 harness.fixtures — instance: a scratch probe the fixture must host."""
        fixtures = self.ep("harness", "fixtures")()
        roots = S.find_values(fixtures, "root")
        self.assertTrue(roots, "the fixture names a scratch root: %r" % (fixtures,))
        root = str(roots[0])
        os.makedirs(root, exist_ok=True)
        probe = os.path.join(root, "fam16-33-invented.txt")
        with open(probe, "w", encoding="utf-8") as handle:
            handle.write("fam16-33")
        self.assertTrue(os.path.exists(probe))
        os.remove(probe)
        self.assertTrue(
            S.numbers(S.find_values(fixtures, "seed")),
            "the fixture pins a numeric seed: %r" % (fixtures,),
        )
        self.assertIn(
            "cpu",
            S.flatten_text(S.find_values(fixtures, "device")),
            "the fixture pins the device the sandbox has (D-8, protocol.md §6)",
        )

    def test_fam16_34_harness_factory(self):
        """FAM-16.34 harness.factory — instance: a 48-wide, 4-deep learner at 99991."""
        spec = self.learner_spec(width=48, depth=4, seed=S.SEED_J)
        built = self.ep("harness", "factory")("learner", spec)
        self.assertEqual(
            self.ep("agents", "param_count")(built),
            self.ep("agents", "param_count")(self.ep("agents", "build_learner")(spec)),
            "the factory builds through agents.build_learner, not around it (records.md §14)",
        )

    def test_fam16_35_harness_seam(self):
        """FAM-16.35 harness.seam — instance: the invented labels 'echo-legal', 'seeded-legal'.

        A seam takes any label, because its contract is the policy protocol and not the
        label: ``recording`` and ``synthetic`` are the documented behaviours and any other
        label behaves as ``recording``, so a battery may name its own (e2e-surface §3.6,
        records.md §14).  What the case asserts is that contract — a policy of §2 that
        chooses inside the engine's legal set and re-implements no subsystem
        (module-map §3, brief §5).
        """
        for label in ("echo-legal", "seeded-legal"):
            policy = self.ep("harness", "seam")(label)
            self.assertTrue(
                callable(policy),
                "harness.seam(%r) returns a policy in the sense of e2e-surface §2, whatever "
                "the label: %r" % (label, policy),
            )
            walk = self.decision_walk(S.SEED_H, policy, limit=3)
            self.assertTrue(walk, "the %r seam answered no decision" % (label,))
            for _hand, _readout, legal, action, index in walk:
                self.assertIn(
                    index,
                    self.indices_for(legal),
                    "the %r seam chooses inside the legal indices: %r" % (label, index),
                )
                self.assertTrue(
                    any(S.canon(action) == S.canon(candidate) for candidate in legal),
                    "the %r seam satisfies the policy protocol of §2: %r" % (label, action),
                )

    def test_fam16_36_harness_expect(self):
        """FAM-16.36 harness.expect — instance: an invented observed value, listed kind.

        The expectation kinds are the harness's own set and are discovered from
        ``harness.fixtures()``; the blind instance therefore invents the *observed value*
        and never a kind (``battery.md`` §4, D-15, e2e-surface §3.6).
        """
        kind = self.an_expectation_kind()
        observation = {"north seat": 17, "south seat": -17}
        answered = self.expect_verdict(kind, observation)
        self.assertIsNotNone(
            S.verdict(answered),
            "harness.expect judges the invented observation under a kind the fixture lists — "
            "a pass or a named failure, never nothing at all (e2e-surface §3.6): %r under %r"
            % (observation, kind),
        )
        again = self.expect_verdict(kind, dict(observation))
        self.assertEqual(
            S.verdict(answered),
            S.verdict(again),
            "one observed value under one kind is one verdict: %r against %r"
            % (answered, again),
        )
        unknown = "fam16-36-invented-expectation"
        text = S.refusal_text(
            lambda: self.ep("harness", "expect")(unknown, observation)
        )
        self.assertIsNotNone(
            text,
            "an invented kind is not a kind: the harness lists its own, so an unlisted one is "
            "a named failure and never a silent pass (e2e-surface §3.6, records.md §14): %r"
            % (unknown,),
        )
        self.assertIn(
            S._family_token(unknown),
            S._family_token(text),
            "the named failure names the invented kind it refused: %r" % (text,),
        )

    def test_fam16_37_harness_timings(self):
        """FAM-16.37 harness.timings — instance: the clock of a 37-hand driven case."""
        case = {
            "id": "fam16-37-clock",
            "steps": [lambda: self.play(S.SEED_C)],
            "expect": [self.an_expectation_kind()],
        }
        self.ep("harness", "drive")(case)
        timings = self.ep("harness", "timings")()
        facts = R.timing_facts(timings)
        self.assertTrue(
            facts["hands"] or facts["clock"],
            "the driver collected a timing at all: %r" % (timings,),
        )
        self.assertTrue(
            facts["per_hand"] or facts["throughput"],
            "the timings carry seconds per hand or a throughput beside the hands they "
            "counted, read by what the keys name — seconds_per_hand / hands_per_second "
            "included (ASM-15, e2e-surface §3.6): %r" % (timings,),
        )
        measured = facts["per_hand"] + facts["throughput"] + facts["clock"]
        self.assertTrue(
            any(number > 0 for number in measured),
            "the per-hand cost or the wall clock is a positive measurement: %r" % (timings,),
        )
        # The bound sizes the table and this record is what shows the measurement exists;
        # no case asserts that a wall clock was beaten (battery.md §2, ASM-15).


if __name__ == "__main__":
    unittest.main()
