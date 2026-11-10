"""FAM-5 — the six fixed baselines behave as their rules state.

`docs/L1/battery.md` §3 FAM-5, `docs/L1/protocol.md` §3, `docs/L1/folders.md` §2 (D-6,
ASM-4, D-21, ASM-31, ASM-32).  A baseline is a policy of `e2e-surface.md` §2 and a rule a
battery can check: `random` is uniform over the legal indices and seeded, `always-call`
never folds and raises only when it must, `oracle` is consistent with the pot odds against
`engine.equity`, and D-21's three folders fold **exactly** where their rule says — on
unpaired non-face hole cards pre-flop only, on a high-card-only hand from the flop onward,
and on a call worth more than half the declared starting stack — and never raise while a
check/call is legal.

The catalogue is six members since D-21 and the three of D-6 remain the rating's anchor;
that is a league fact and is asserted by the pool, matrix and rating families (FAM-6,
FAM-8, FAM-9 of `battery.md` §3).  Here it appears where the catalogue itself is read:
FAM-5.1 asserts the six names, their order, the zero parameter count and the `anchor`
flag each record carries (`e2e-surface.md` §3.3, `protocol.md` §3, ASM-32).

Every folder case recomputes its rule from the readout the folder was handed — the rank
characters of the two hole spellings, `hand_class`, and the starting stack
`engine.game_config(shape)` declares — so a folder that folded one decision early or late,
on the wrong street, or on the wrong comparison is caught where it decided
(`folders.md` §2, §3, ASM-30, ASM-31).

**D-29 does not move any rule, and it does move the price.**  A baseline is a policy of the
shape in force, so every case here is asserted on the shape it drives: with no shape named
that is today's fixed game, unchanged (`shapes.md` §5), and the no-cap shape is where
`fold-large-bet`'s trigger finally fires — a folder **carries no shape** (it is handed
`(readout, legal_actions)` and nothing else), so its threshold is the declared stack
`engine.game_config()` reports with no shape named, more than 10 of ASM-6's 20, on every
declared shape (`folders.md` §2, ASM-31, `docs/L3/agents/baselines.md` §7); no street of
the fixed game can put a call above 10, and the no-cap game's amounts can, so that shape's
case observes the fold ASM-34 predicted and this one never could (ASM-34, `shapes.md` §2,
D-29).  FAM-5.15 and FAM-5.16 are that shape's cases.
"""

import os
import sys
import unittest

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _surface as S  # noqa: E402

# How far the oracle's own equity sample and the battery's estimate may disagree
# before a decision counts as decisive.  Both are estimates; the case asserts the
# pot-odds rule outside this band and does not pretend to see inside it.
EQUITY_BAND = 0.08

# The opponents a folder is driven against.  `always-call` is the ordinary walk of
# `folders.md` §2, and `random` raises on about a third of its decisions, which is what
# gives a folder a decision on which folding is legal at all: a check is not a fold, so a
# folder facing an opponent that never bets can never fold (D-21, ASM-31).
FOLDER_OPPONENTS = ("always-call", "random")

PREFLOP = "preflop"


class FAM5Baselines(S.SurfaceCase):
    """The fixed baselines of D-6 and the folders of D-21, asserted as rules."""

    def indices(self, walk):
        return [entry[4] for entry in walk]

    # -- helpers over the folders (D-21) -----------------------------------
    def stack(self, shape=None):
        """The starting stack the shape in force declares (ASM-6, ASM-31, shapes.md §2)."""
        return S.starting_stack(self.ep("engine", "game_config")(shape))

    def legal_indices(self, legal):
        return set(self.ep("features", "legal_indices")(legal))

    def street_of(self, readout):
        return str(S.readout_fact(readout, "street")).strip().lower()

    def folder_decisions(self, folder, opponents=FOLDER_OPPONENTS,
                         seeds=None, seats=(0, 1), shape=None):
        """Every decision one folder makes, as one seat's policy, over invented hands.

        One walk per (opponent, seat, seed): the folder plays both seats and meets both
        opponents, so its rule is observed from both positions and both games
        (`folders.md` §2, `battery.md` §4).  Yields ``(seed, seat, readout, legal,
        index)``.  ``shape`` is the shape in force: no name is today's game, and naming
        the no-cap shape drives the folder on that shape's hands (`shapes.md` §2, D-29).
        """
        if seeds is None:
            seeds = S.FOLDER_SEEDS
        for opponent in opponents:
            for seat in seats:
                for seed in seeds:
                    for readout, legal, _action, index in self.folder_walk(
                        folder, opponent, seed, seat, shape
                    ):
                        yield seed, seat, readout, legal, index

    def check_folder_rule(self, folder, shape=None, opponents=FOLDER_OPPONENTS,
                          seeds=None):
        """Assert D-21's rule for ``folder`` on every decision it makes.

        Returns ``(decisions, folds, preflop, later, opportunities)`` so a case can assert
        what it observed; the assertions themselves are the rule, recomputed from the
        readout: the folder folds **iff** its predicate holds and index 0 is legal, and
        otherwise check/calls wherever index 1 is legal (`folders.md` §2, ASM-31, D-21).
        ``opportunities`` counts the decisions on which folding was legal at all.

        The threshold `fold-large-bet` is judged against is the stack the folder itself
        reads on every decision — `engine.game_config()` with **no shape named**, because a
        baseline carries no shape (`folders.md` §2, ASM-31, `docs/L3/agents/baselines.md`
        §7).  `shape` therefore changes the hands the folder is driven on and never the
        rule it is judged by: on the no-cap shape a call can exceed that threshold, and on
        the fixed game it cannot (ASM-34, D-29).
        """
        stack = self.stack()
        decisions = folds = opportunities = 0
        streets = {PREFLOP: 0, "later": 0}
        for seed, seat, readout, legal, index in self.folder_decisions(
            folder, opponents, seeds, shape=shape
        ):
            decisions += 1
            indices = self.legal_indices(legal)
            street = self.street_of(readout)
            streets[PREFLOP if street == PREFLOP else "later"] += 1
            predicate = S.folder_rule_folds(folder, readout, stack)
            fold_legal = 0 in indices
            expected = predicate and fold_legal
            if fold_legal:
                opportunities += 1
            self.assertEqual(
                index == 0,
                expected,
                "D-21's rule for %r: this decision's own facts %s the rule's predicate and "
                "folding is %s legal, so the folder must %s — it chose index %r (seed %r, "
                "seat %r, opponent walk; street %r, hole %r, board %r, to_call %r, "
                "hand_class %r, legal indices %r) (folders.md §2, ASM-30, ASM-31, D-21)"
                % (
                    folder,
                    "satisfies" if predicate else "does not satisfy",
                    "" if fold_legal else "not",
                    "fold" if expected else "check/call",
                    index,
                    seed,
                    seat,
                    street,
                    readout.get("hole"),
                    readout.get("board"),
                    readout.get("to_call"),
                    readout.get("hand_class"),
                    sorted(indices),
                ),
            )
            if not expected and 1 in indices:
                self.assertEqual(
                    index,
                    1,
                    "a folder that does not fold checks or calls wherever that is legal and "
                    "never raises while a check/call is available (folders.md §2, ASM-31, "
                    "D-21): %r chose index %r at seed %r, seat %r" % (folder, index, seed, seat),
                )
            if index == 0:
                folds += 1
        self.assertGreater(
            decisions,
            0,
            "the case must drive %r on real decisions, or it asserts nothing (folders.md "
            "§2, §6)" % (folder,),
        )
        return decisions, folds, streets[PREFLOP], streets["later"], opportunities

    def folder_indices(self, folder, build_seed, deal_seed, seat=0, shape=None):
        """The indices one folder built at ``build_seed`` chooses on one dealt hand."""
        policies = {
            seat: self.baseline(folder, build_seed),
            "default": self.baseline("always-call", S.SEED_G),
        }
        return [
            index
            for decided, _readout, _legal, _action, index in self.seated_walk(
                deal_seed, policies, shape=shape
            )
            if decided == seat
        ]

    # -- the catalogue (protocol.md §3) ------------------------------------
    def test_fam5_1_the_catalogue_is_the_six_baselines_in_catalogue_order(self):
        """FAM-5.1 agents.baselines declares exactly six names, in order, with their flags.

        `protocol.md` §3 names six baselines and `e2e-surface.md` §3.3 makes each record
        carry its rule, `params: 0` and an `anchor` flag — true for the three of D-6,
        false for D-21's folders.  The order is the catalogue's, because a pool's pinned
        baselines and a matrix's rows follow it (`records.md` §8, ASM-32, D-21).
        """
        declared = self.ep("agents", "baselines")()
        catalogue = S.baseline_catalogue(declared)
        self.assertEqual(
            [name for name, _record in catalogue],
            list(S.BASELINES),
            "agents.baselines() declares the six fixed names of protocol.md §3 in catalogue "
            "order — %r — and no other name (e2e-surface.md §3.3, D-6, D-21); it declared %r"
            % (list(S.BASELINES), declared),
        )
        for name, record in catalogue:
            params = S.declared_field(
                record, "a baseline record (protocol.md §3)",
                "params", "parameters", "param count", "param",
            )
            self.assertTrue(
                S.is_count(params) and int(params) == 0,
                "no baseline has a trainable parameter, so its `params` is 0 (protocol.md "
                "§3, e2e-surface.md §3.3, ASM-4): %r declares %r" % (name, params),
            )
            rule = S.declared_field(record, "a baseline record (protocol.md §3)", "rule")
            self.assertTrue(
                str(rule).strip(),
                "each baseline states the rule it plays (protocol.md §3, e2e-surface.md "
                "§3.3): %r states %r" % (name, rule),
            )
            anchor = S.declared_field(record, "a baseline record (protocol.md §3)", "anchor")
            self.assertTrue(
                S.is_flag(anchor),
                "the catalogue's records carry an `anchor` **flag** — true for the three of "
                "D-6, false for D-21's folders (protocol.md §3, e2e-surface.md §3.3, "
                "ASM-32): %r declares %r" % (name, anchor),
            )
            self.assertIs(
                bool(anchor),
                name in S.ANCHOR_BASELINES,
                "anchored is exactly 'one of the three of D-6': the flagged three are the "
                "rating's anchor and a folding baseline is never one (protocol.md §3, "
                "league.md §5, ASM-32, D-21): %r declares anchor=%r" % (name, anchor),
            )

    def test_fam5_2_every_baseline_builds_a_policy_of_section_2(self):
        """FAM-5.2 build_baseline returns a callable that chooses from legal_actions."""
        hand = self.hand(S.SEED_E)
        readout = self.readout(hand)
        legal = self.legal(hand)
        for name in S.BASELINES:
            policy = self.baseline(name, S.SEED_E)
            self.assertTrue(callable(policy), "the %r baseline is not a policy" % (name,))
            action = policy(readout, legal)
            self.assertTrue(
                any(_same(action, candidate) for candidate in legal),
                "the %r baseline chose a descriptor outside legal_actions: %r"
                % (name, action),
            )

    def test_fam5_3_random_never_returns_an_illegal_action(self):
        """FAM-5.3 the random baseline never leaves the legal set, on the shape in force.

        `protocol.md` §3 makes `random` uniform over the legal indices of the decision it
        is handed, so it can choose no index outside that decision's legal set and none
        outside its shape's vocabulary — today's three on the default shape, unchanged,
        and the six of the no-cap shape when that is the shape in force (`shapes.md` §2,
        D-29, `e2e-surface.md` §2 "Action vocabulary").
        """
        vocabulary = set(self.vocabulary())
        self.assertEqual(
            set(self.vocabulary()),
            {0, 1, 2},
            "with no shape named the vocabulary is today's three indices (shapes.md §5): %r"
            % (self.vocabulary(),),
        )
        for seed in (S.SEED_A, S.SEED_E):
            policy = self.baseline("random", S.SEED_G)
            for _hand, _readout, legal, action, index in self.decision_walk(seed, policy):
                self.assertIn(index, vocabulary,
                              "the random baseline chose an index outside the vocabulary")
                self.assertIn(
                    index, self.legal_indices(legal),
                    "the random baseline chose index %r, which is not legal at that "
                    "decision (%r)" % (index, sorted(self.legal_indices(legal))),
                )
                self.assertTrue(
                    any(S.canon(action) == S.canon(candidate) for candidate in legal),
                    "the random baseline returned a descriptor outside legal_actions: %r"
                    % (action,),
                )
        # The same rule on the shape D-29 declares second: six descriptors, legal only.
        shape = self.second_shape()
        six = set(self.vocabulary(shape))
        self.assertEqual(
            six, set(range(len(S.SIZED_ACTIONS))),
            "the named shape's vocabulary is its six descriptors (sizing.md §3): %r" % (six,),
        )
        seen = set()
        decisions = 0
        for seed in S.SHAPE_SEEDS[:3]:
            policy = self.baseline("random", S.SEED_G)
            for _hand, _readout, legal, _action, index in self.decision_walk(
                seed, policy, shape=shape
            ):
                decisions += 1
                seen.add(index)
                self.assertIn(
                    index, six,
                    "on the named shape the random baseline chooses one of that shape's "
                    "six indices: %r" % (index,),
                )
                self.assertIn(
                    index, self.legal_indices(legal),
                    "on the named shape the random baseline left the legal set: index %r "
                    "against %r" % (index, sorted(self.legal_indices(legal))),
                )
        self.assertGreater(decisions, 0, "the case must drive the shape it names")
        self.assertTrue(
            seen,
            "the random baseline answered at least one decision on the named shape",
        )

    def test_fam5_4_random_is_seeded(self):
        """FAM-5.4 one seed agrees twice and two seeds differ (protocol §3)."""
        first = self.indices(
            self.decision_walk(S.SEED_A, self.baseline("random", S.SEED_D))
        )
        same_seed = self.indices(
            self.decision_walk(S.SEED_A, self.baseline("random", S.SEED_D))
        )
        other_seed = self.indices(
            self.decision_walk(S.SEED_A, self.baseline("random", S.SEED_F))
        )
        self.assertEqual(first, same_seed,
                         "two random policies at one seed must agree")
        self.assertNotEqual(first, other_seed,
                            "two random policies at different seeds must differ")

    def test_fam5_5_always_call_never_folds(self):
        """FAM-5.5 always-call never folds in any decision of any hand (D-6)."""
        for seed in (S.SEED_A, S.SEED_E, S.SEED_F):
            policy = self.baseline("always-call", S.SEED_D)
            for _hand, _readout, _legal, _action, index in self.decision_walk(seed, policy):
                self.assertNotEqual(
                    index,
                    0,
                    "the always-call baseline folded at seed %r" % (seed,),
                )

    def test_fam5_6_always_call_calls_whenever_calling_is_legal(self):
        """FAM-5.6 always-call checks/calls when it can, and raises only when forced."""
        for seed in (S.SEED_A, S.SEED_E):
            policy = self.baseline("always-call", S.SEED_D)
            for _hand, _readout, legal, _action, index in self.decision_walk(seed, policy):
                indices = set(self.ep("features", "legal_indices")(legal))
                if 1 in indices:
                    self.assertEqual(
                        index,
                        1,
                        "always-call must check or call whenever that is legal",
                    )
                else:
                    self.assertEqual(
                        index,
                        2,
                        "with check/call unavailable always-call makes the minimum completion",
                    )

    def test_fam5_7_oracle_is_consistent_with_pot_odds_against_equity(self):
        """FAM-5.7 the oracle calls at or above the pot odds and folds below them."""
        decisive = 0
        for seed in (S.SEED_A, S.SEED_C, S.SEED_E):
            oracle = self.baseline("oracle", S.SEED_E)
            for hand, readout, legal, _action, index in self.decision_walk(seed, oracle):
                indices = set(self.ep("features", "legal_indices")(legal))
                if 0 not in indices:
                    self.assertNotEqual(index, 0,
                                        "the oracle folded where folding was not legal")
                    continue
                pot = readout["pot"]
                to_call = readout["to_call"]
                odds = to_call / float(pot + to_call) if (pot + to_call) else 0.0
                equity = self.ep("engine", "equity")(hand, S.SEED_E, S.EQUITY_SAMPLES)
                self.assertGreaterEqual(equity, 0.0)
                self.assertLessEqual(equity, 1.0)
                if abs(equity - odds) <= EQUITY_BAND:
                    continue
                decisive += 1
                if equity >= odds:
                    self.assertNotEqual(
                        index,
                        0,
                        "equity %.3f is at or above the pot odds %.3f, so the oracle "
                        "must not fold (protocol §3)" % (equity, odds),
                    )
                else:
                    self.assertEqual(
                        index,
                        0,
                        "equity %.3f is below the pot odds %.3f, so the oracle must fold "
                        "when folding is legal (protocol §3)" % (equity, odds),
                    )
        self.assertGreaterEqual(
            decisive,
            2,
            "the case saw no decision clear of the pot-odds boundary, so it proved nothing",
        )

    def test_fam5_8_a_rebuilt_baseline_repeats_its_decisions(self):
        """FAM-5.8 a baseline is a fixed rule: rebuilt at one seed, it decides the same."""
        policy = self.baseline("oracle", S.SEED_E)
        first = self.indices(self.decision_walk(S.SEED_A, policy))
        fresh = self.baseline("oracle", S.SEED_E)
        second = self.indices(self.decision_walk(S.SEED_A, fresh))
        self.assertEqual(first, second,
                         "a rebuilt baseline at the same seed must choose the same actions")

    # -- D-21's three folders, as rules on real decisions ------------------
    def test_fam5_9_fold_no_pair_or_face_folds_exactly_on_those_hands(self):
        """FAM-5.9 fold-no-pair-or-face folds unpaired non-face hands pre-flop only.

        D-21 pins the rule: pre-flop only, fold when the two hole cards are unpaired **and**
        neither card's rank is J, Q, K or A; from the flop onward it never folds
        (`folders.md` §2, protocol.md §3).  The case recomputes that predicate from each
        readout's own hole spellings, so a folder that folds a paired hand, a hand with a
        face card, or any post-flop hand is caught; it also asserts a fold was **observed**,
        so the case proves the folder folds at all (ASM-31, D-21).
        """
        decisions, folds, preflop, later, _opportunities = self.check_folder_rule(
            "fold-no-pair-or-face"
        )
        self.assertGreater(
            preflop,
            0,
            "the pre-flop arm of the rule must be observed on a real decision "
            "(folders.md §2)",
        )
        self.assertGreater(
            later,
            0,
            "the case must see this folder decide on a flop, turn or river, or 'it never "
            "folds from the flop onward' is asserted on nothing (folders.md §2, D-21)",
        )
        self.assertGreater(
            folds,
            0,
            "D-21's whole purpose is a baseline that folds, so the case must observe a fold "
            "on a hand whose hole cards are unpaired and carry no J, Q, K or A "
            "(folders.md §1, §2; %d decisions, %d pre-flop)" % (decisions, preflop),
        )

    def test_fam5_10_fold_no_pair_or_better_folds_exactly_on_high_card_hands(self):
        """FAM-5.10 fold-no-pair-or-better folds a high-card-only hand from the flop on.

        D-21 pins the rule: from the flop onward, fold when `hand_class` is 0 — the best
        five-card hand of hole plus board is a high card; before the flop it check/calls
        (`folders.md` §2, §3, protocol.md §3, ASM-30).  The case reads `hand_class` off the
        readout the folder was handed, so a folder that folds a pair or better, that folds
        pre-flop, or that ignores the fact is caught; and it asserts a fold was observed.
        """
        decisions, folds, preflop, later, _opportunities = self.check_folder_rule(
            "fold-no-pair-or-better"
        )
        self.assertGreater(
            preflop,
            0,
            "the case must see this folder decide before the flop, or 'it never folds "
            "pre-flop' is asserted on nothing (folders.md §2, D-21)",
        )
        self.assertGreater(
            later,
            0,
            "the post-flop arm of the rule must be observed on a real decision "
            "(folders.md §2)",
        )
        self.assertGreater(
            folds,
            0,
            "the case must observe this folder fold a high-card-only hand from the flop "
            "onward, or it proves nothing about the rule (folders.md §1, §2, D-21): %d "
            "decisions, %d post-flop" % (decisions, later),
        )

    def test_fam5_11_fold_large_bet_folds_exactly_when_the_call_is_large(self):
        """FAM-5.11 fold-large-bet folds when `to_call` beats half the starting stack.

        D-21 pins the rule at any street: fold when `to_call` exceeds half of
        `engine.game_config()["starting_stack"]` — more than 10 chips at the declared 20 —
        and check/call otherwise (`folders.md` §2, protocol.md §3, ASM-31).  The case is
        driven against an opponent that bets (`random`) as well as against `always-call`,
        because a folder can fold only where folding is legal.

        **Read the finding beside this case.**  At ASM-6's game `to_call` is the amount the
        acting seat must *add* to continue, and heads-up fixed-limit betting never puts the
        actor more than one bet-size increment behind: the increments are 2 pre-flop and on
        the flop and 4 on the turn and river, so no legal decision in this game has
        `to_call` above 4.  D-21's threshold of more than 10 is therefore never met here,
        and the correct folder folds on **no** decision — which is exactly what the rule's
        recomputation below asserts, decision by decision, against the readout's own
        `to_call` and the declared stack.  This case consequently cannot assert a non-zero
        fold count the way FAM-5.9 and FAM-5.10 do; it asserts instead that the folder had
        fold **opportunities** (decisions where folding was legal) and took none of them
        on a call too small to be D-21's.

        **The game the threshold bites on is FAM-5.15's.**  A folder carries no shape, so
        its threshold is the stack `engine.game_config()` declares with no shape named —
        more than 10 of ASM-6's 20 — on every shape (`folders.md` §2, ASM-31,
        `docs/L3/agents/baselines.md` §7); D-29's no-cap shape deals amounts above 10, so
        that shape's case observes the fold this one cannot, which is what "where the game
        changes so that a call above half the stack exists, the same assertion starts
        requiring the fold" asked for (`shapes.md` §2, ASM-34, D-29).
        """
        decisions, folds, preflop, later, opportunities = self.check_folder_rule(
            "fold-large-bet"
        )
        self.assertGreater(
            decisions,
            0,
            "the case must drive this folder on real decisions (folders.md §2)",
        )
        self.assertGreater(
            preflop + later,
            0,
            "the folder's decisions must span the game's streets (folders.md §2)",
        )
        self.assertGreater(
            opportunities,
            0,
            "the case must hand this folder decisions on which folding is legal, or 'it "
            "folds exactly when the call is large' is asserted on decisions that could not "
            "fold whatever the rule said (folders.md §2, ASM-31): %d decisions, %d folds"
            % (decisions, folds),
        )

    def test_fam5_12_no_folder_raises_while_a_check_or_call_is_legal(self):
        """FAM-5.12 a folder raises at no decision where a check/call is legal, any shape.

        ASM-31's pin of D-21's "none of them raises": a raise-only decision is forced by
        the game and never chosen by the rule, so a raise descriptor appears only where
        check/call is unavailable; and a folder folds only where folding is legal, because
        a fold the engine forbids is a contract violation and not a fold (`folders.md` §2,
        `e2e-surface.md` §2, D-21).

        The assertion is read through the **shape in force's** vocabulary — index 2 is the
        fixed shape's only raise and the no-cap shape's first of four bands — so it holds
        on both declared shapes and never depends on a spelling of one index
        (`shapes.md` §2, `sizing.md` §3, D-29).
        """
        for shape in (None, self.second_shape()):
            vocabulary = self.vocabulary(shape)
            raises = {index for index, name in vocabulary.items() if S.is_raise(name)}
            for folder in S.FOLDER_BASELINES:
                decisions = 0
                for seed, seat, readout, legal, index in self.folder_decisions(
                    folder,
                    seeds=(S.SEED_A, S.SEED_E, S.SEED_F, S.SEED_I, S.SEED_J),
                    shape=shape,
                ):
                    decisions += 1
                    indices = self.legal_indices(legal)
                    if 1 in indices:
                        self.assertNotIn(
                            index,
                            raises,
                            "%r raised a decision on which a check/call was legal — a folder "
                            "takes the minimum legal completion only when a raise is the sole "
                            "legal action (folders.md §2, ASM-31, D-21): shape %r, seed %r, "
                            "seat %r, street %r, choice %r, legal indices %r"
                            % (folder, shape, seed, seat, self.street_of(readout),
                               vocabulary.get(index), sorted(indices)),
                        )
                    if 0 not in indices:
                        self.assertNotEqual(
                            index,
                            0,
                            "%r folded where folding was not a legal action, which is a "
                            "contract violation and not a fold (e2e-surface.md §2, folders.md "
                            "§2, ASM-31): shape %r, seed %r, seat %r, street %r, legal "
                            "indices %r" % (folder, shape, seed, seat,
                                            self.street_of(readout), sorted(indices)),
                        )
                self.assertGreater(
                    decisions,
                    0,
                    "the case must drive %r on real decisions (folders.md §2), shape %r"
                    % (folder, shape),
                )

    def test_fam5_13_each_folder_is_deterministic_and_seed_independent(self):
        """FAM-5.13 a folder consumes no randomness: its seed never changes a decision.

        `folders.md` §2: a folder's rule consumes no randomness, so two builds at one seed
        and two builds at different seeds decide identically on the same hands — the
        property `always-call` and `oracle` already have (`protocol.md` §3).  A folder that
        read its seed, or that drew from a generator, would differ here.
        """
        for folder in S.FOLDER_BASELINES:
            hands = 0
            for seat in (0, 1):
                for seed in (S.SEED_A, S.SEED_C, S.SEED_E):
                    first = self.folder_indices(folder, S.SEED_D, seed, seat)
                    same_seed = self.folder_indices(folder, S.SEED_D, seed, seat)
                    other_seed = self.folder_indices(folder, S.SEED_F, seed, seat)
                    self.assertTrue(
                        first,
                        "%r must decide at least once on seed %r as seat %r, or the "
                        "determinism asserted here is vacuous (folders.md §2)"
                        % (folder, seed, seat),
                    )
                    self.assertEqual(
                        first,
                        same_seed,
                        "two builds of %r at one seed decide identically on the same hand "
                        "(folders.md §2, protocol.md §3): seed %r, seat %r"
                        % (folder, seed, seat),
                    )
                    self.assertEqual(
                        first,
                        other_seed,
                        "%r consumes no randomness, so two builds at different seeds decide "
                        "identically on the same hand (folders.md §2, protocol.md §3): seed "
                        "%r, seat %r, %r against %r"
                        % (folder, seed, seat, first, other_seed),
                    )
                    hands += 1
            self.assertGreater(hands, 0, "the case must compare real hands")

    def test_fam5_14_build_baseline_refuses_a_name_outside_the_catalogue(self):
        """FAM-5.14 a name the catalogue does not carry is refused, naming it.

        `agents.build_baseline` takes a catalogue name; `folders.md` §2 and `protocol.md` §3
        make the catalogue the six, so a seventh name is a violated contract and is refused
        by name rather than mapped onto one of the six (ASM-4, ASM-31, D-21).  The name is
        the battery's own and appears in no design document (`battery.md` §4).
        """
        offending = S.UNKNOWN_BASELINE
        self.assertNotIn(
            offending,
            S.BASELINES,
            "the name this case invents is outside the catalogue it names",
        )
        text = S.refusal_text(lambda: self.baseline(offending, S.SEED_E))
        self.assertIsNotNone(
            text,
            "agents.build_baseline(%r, seed) is a contract violation and must be refused, "
            "not answered with a policy (e2e-surface.md §2, protocol.md §3, folders.md §2)"
            % (offending,),
        )
        self.assertIn(
            S._family_token(offending),
            S._family_token(text),
            "the refusal names the baseline name it refused (folders.md §2, protocol.md §3): "
            "%r" % (text,),
        )


    # ==================================================================
    # The same catalogue, on the shape D-29 declares second
    # ==================================================================
    def aggressive_opponent(self):
        """A policy of §2 that bets as large as the decision allows.

        It is the battery's own and appears in no design document (`battery.md` §4): it
        returns the most expensive legal raise descriptor of the shape in force, else the
        check/call, else the first legal descriptor — always a member of
        ``legal_actions``, which is the whole of a policy's contract (`e2e-surface.md`
        §2).  A folder can fold only where folding is legal, so a case that needs a call
        above half a stack must be met by an opponent that bets one (`folders.md` §2,
        ASM-31, ASM-34).
        """

        def policy(readout, legal):
            for wanted in ("raise-all-in", "raise-half", "raise-quarter",
                           "raise-minimum", "raise"):
                if wanted in legal:
                    return wanted
            if "check-call" in legal:
                return "check-call"
            return legal[0]

        return policy

    def test_fam5_15_fold_large_bet_folds_where_the_named_shape_can_threaten_the_stack(self):
        """FAM-5.15 the same rule folds on the shape whose amounts can exceed half the stack.

        D-21's rule is one inequality — fold when `to_call` exceeds half the declared
        starting stack, more than 10 chips at ASM-6's 20 — read through
        `engine.game_config()` on every decision, because a folder carries no shape and is
        handed nothing but `(readout, legal_actions)` (`folders.md` §2, ASM-31,
        `docs/L3/agents/baselines.md` §1, §7).  In D-2's fixed game no legal decision
        reaches a call of 10, so FAM-5.11 observes fold opportunities and no fold
        (ASM-34); in D-29's no-cap game the amounts run to a 100-chip stack, so a call
        above 10 exists — and this case requires the fold the rule then states, decision
        by decision, on the shape in force (`shapes.md` §2, ASM-34, D-29).

        Nothing about the rule moves here: the case recomputes the same inequality from
        each readout's own `to_call` and the declared stack, then additionally requires
        that at least one decision's call is above the threshold and that the folder folds
        at **every** such decision and at none below it.
        """
        shape = self.second_shape()
        stack = self.stack()
        threshold = stack // 2
        decisions, folds, preflop, later, opportunities = self.check_folder_rule(
            "fold-large-bet",
            shape=shape,
            opponents=(self.aggressive_opponent(), "random", "always-call"),
            seeds=(S.SEED_A, S.SEED_B, S.SEED_C, S.SEED_D, S.SEED_E,
                   S.SEED_F, S.SEED_G, S.SEED_H),
        )
        self.assertGreater(decisions, 0,
                           "the case must drive the named shape's hands (folders.md §2)")
        self.assertGreater(
            opportunities,
            0,
            "the folder must be handed decisions on which folding is legal, or the rule "
            "is asserted on decisions that could not fold whatever it said (folders.md §2, "
            "ASM-31): %d decisions, %d folds, shape %r" % (decisions, folds, shape),
        )
        above = 0
        for seed, seat, readout, legal, index in self.folder_decisions(
            "fold-large-bet",
            opponents=(self.aggressive_opponent(), "random", "always-call"),
            seeds=(S.SEED_A, S.SEED_B, S.SEED_C, S.SEED_D, S.SEED_E,
                   S.SEED_F, S.SEED_G, S.SEED_H),
            shape=shape,
        ):
            to_call = int(S.readout_fact(readout, "to_call"))
            if 2 * to_call > stack:
                above += 1
                self.assertIn(
                    0, self.legal_indices(legal),
                    "a call above half the declared stack must be a decision on which "
                    "folding is legal, or the rule cannot be observed (folders.md §2, "
                    "ASM-31): to_call %r, stack %r, legal %r"
                    % (to_call, stack, sorted(self.legal_indices(legal))),
                )
                self.assertEqual(
                    index,
                    0,
                    "'fold-large-bet' folds when `to_call` exceeds half the declared "
                    "starting stack (%r > %r) (folders.md §2, protocol.md §3, ASM-31): "
                    "seed %r, seat %r, street %r, to_call %r, stack %r, choice %r"
                    % (2 * to_call, stack, seed, seat, self.street_of(readout),
                       readout.get("to_call"), stack, index),
                )
            elif index == 0:
                self.fail(
                    "'fold-large-bet' folded a call that does not exceed half the declared "
                    "starting stack: to_call %r against stack %r (folders.md §2, ASM-31): "
                    "seed %r, seat %r, street %r"
                    % (readout.get("to_call"), stack, seed, seat,
                       self.street_of(readout))
                )
        self.assertGreater(
            above,
            0,
            "the named shape's amounts are what makes D-21's threshold reachable — the "
            "fixed game offers no call above %r — so the case must observe one, or it has "
            "asserted FAM-5.11's arm again instead of this one (shapes.md §2, ASM-34, "
            "D-29): %d decisions, %d folds, stack %r" % (threshold, decisions, folds, stack),
        )
        self.assertGreater(
            folds,
            0,
            "the folder must fold at least one call above half the declared stack (%d "
            "observed above it) (folders.md §2, D-21, ASM-31)" % (above,),
        )

    def test_fam5_16_every_baseline_is_a_policy_of_the_named_shape(self):
        """FAM-5.16 all six baselines answer the named shape's decisions, one game over.

        A baseline is a policy, and a policy takes `(readout, legal_actions)` and returns
        one member of `legal_actions` — so on any declared shape every one of the six
        chooses from **that** shape's legal set, `random` included; `always-call` folds at
        no decision of it; and each folder's decision is still the one its rule states,
        recomputed against the shape's own declared stack (`e2e-surface.md` §2, §3.3,
        `protocol.md` §3, `folders.md` §2, `shapes.md` §2, D-29).
        """
        shape = self.second_shape()
        vocabulary = self.vocabulary(shape)
        for name in S.BASELINES:
            policy = self.baseline(name, S.SEED_F)
            decisions = 0
            for seed in (S.SEED_A, S.SEED_C, S.SEED_G):
                for _hand, _readout, legal, action, index in self.decision_walk(
                    seed, policy, shape=shape
                ):
                    decisions += 1
                    self.assertIn(
                        index, vocabulary,
                        "%r chose index %r, which is not one of the named shape's indices "
                        "%r (e2e-surface.md §2)" % (name, index, sorted(vocabulary)),
                    )
                    self.assertIn(
                        index, self.legal_indices(legal),
                        "%r chose index %r, which is not legal at that decision (%r): a "
                        "policy that returns an illegal action is a contract violation and "
                        "not a fold (e2e-surface.md §2)"
                        % (name, index, sorted(self.legal_indices(legal))),
                    )
                    self.assertTrue(
                        any(S.canon(action) == S.canon(candidate) for candidate in legal),
                        "%r returned a descriptor outside legal_actions: %r in %r"
                        % (name, action, legal),
                    )
                    if name == "always-call":
                        self.assertNotEqual(
                            index, 0,
                            "always-call never folds, on any declared shape (protocol.md §3)",
                        )
            self.assertGreater(
                decisions, 0,
                "the case must drive %r on the named shape's hands (protocol.md §3)"
                % (name,),
            )
        # The folders' rules, recomputed against **this** shape's declared stack.
        for folder in S.FOLDER_BASELINES:
            decisions, folds, _preflop, _later, _opportunities = self.check_folder_rule(
                folder, shape=shape, seeds=(S.SEED_A, S.SEED_C, S.SEED_G)
            )
            self.assertGreater(
                decisions, 0,
                "%r must decide on the named shape's hands (folders.md §2)" % (folder,),
            )


def _same(one, other):
    if one is other:
        return True
    try:
        return bool(one == other)
    except Exception:
        return False


if __name__ == "__main__":
    unittest.main()
