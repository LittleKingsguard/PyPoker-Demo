"""JOIN-AGT-14 — the second declared game shape at the join.

`docs/L2/agents/shapes.md` §1-§4 and §6, `docs/L2/features/shapes.md` §1-§5,
`docs/L3/agents/shapes.md` §1-§4 and §6, `docs/L1/sizing.md` §3-§4, §6, `docs/L1/
shapes.md` §2, §5, `docs/L1/records.md` §6, §15 and `docs/L1/e2e-surface.md` §3.2,
§3.3 — D-29, D-30, ASM-37 and ASM-40.

The shape is declared twice: `engine.game_shapes()` publishes the two rows and this
module restates their **names** once, while the head's width `A` is a **reading** of
`features.action_space(shape=...)` and never a literal of a table's, a backend's or
this battery's (`shapes.md` §1-§2, `module-map.md` §2, D-13, ASM-40).  No single module
can check that: the catalogue is `engine`'s, the vocabulary is `features`', and the head,
the index space, the `tie` flag and the exploration mode are this module's.  So every
case here reads the engine's catalogue and hands the module what the engine actually
produced — a real hand of one shape, its readout, its own legal descriptors — and never
a shape's descriptors, its head width or an observation of its own.

The shape's **input width** is a second reading, and it is `features`' too: a shape's
history capacity is its own, so its dense observation is 203 wide over 24 slots on the
default shape and 329 over 66 on `no-limit-100`, and a token kind is sized by its
vocabulary on both (`docs/L1/shapes.md` §8, ASM-44, `docs/L2/features/capacity.md` §2).
`shaped_input_size` reads it out of `features.observation_spec`, and every learner this
battery builds on a declared shape is handed that shape's encoder, because a kind's
declared `observation_size` is the default shape's and an encoder-less build on another
shape is refused by name (`docs/L2/agents/shapes.md` §2, §6, `docs/L2/features/capacity.md`
§5).

The one exception is named at `flat_observation` in the support: `act`'s masked values
are not observable through any entry point, so the case that decides the `tie` flag from
the record alone drives a **zero** observation of the declared shape and dtype, which no
readout of either declared shape encodes to.  Every other observation in this file is
`features.encode` of a readout `engine` dealt (`docs/L2/features/surface.md` §6).
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

#: The second shape's price bands between the two shared descriptors and the last one:
#: `raise-half`, `raise-all-in` and `raise-minimum` at the indices `sizing.md` §3 records,
#: which are deliberately not monotone in amount.  The indices are the task's and the
#: descriptors behind them are read off the engine's row, so a case asserts that those
#: indices are reached, never that a band is a size (`sizing.md` §3, ASM-37).
BAND_INDICES = (3, 4, 5)

#: The one width and depth `docs/L2/agents/shapes.md` §2's table is read at — 36 and 2, the
#: R1/R2 rung's own settings — so this battery's reading of that table is at the settings
#: the table itself states (`ladder.md` §3, ASM-10, ASM-44).  They are settings and not
#: counts: every count below comes out of `architecture.md` §5's formula at the width each
#: shape's own encoder declares.
WIDTH_DOCUMENTED = 36
DEPTH_DOCUMENTED = 2


class ShapeCatalogue(J.JoinCase):
    """The catalogue `agents` restates held equal to the one `engine` publishes."""

    def test_join_agt_14_1_the_two_catalogues_are_one_catalogue(self):
        """JOIN-AGT-14.1 `engine.game_shapes()`'s names, in its own order with the
        default first, are the names `build_learner` resolves; for every declared shape
        a learner built on it reports `actions` equal to `len(features.action_space(
        shape=name))` and to that row's `head_width`, whose indices
        `features.decode_action` covers exactly and no further (`docs/L2/agents/
        shapes.md` §1-§2, §6, `docs/L2/features/shapes.md` §3-§4, `docs/L3/agents/
        shapes.md` §1-§2, `sizing.md` §6, ASM-40, D-29).
        """
        catalogue = J.game_shapes()
        names = tuple(catalogue)
        self.assertGreaterEqual(
            len(names),
            2,
            "the catalogue declares the second shape beside the default, so this case "
            "has two statements to hold equal (docs/L2/agents/shapes.md §1, D-29): %r"
            % (list(names),),
        )
        self.assertEqual(
            names[0],
            J.SHAPE_DEFAULT,
            "the catalogue is read in its own order, the default shape first -- the "
            "order this module restates (shapes.md §1-§2, D-29): %r" % (list(names),),
        )
        self.assertEqual(
            names[1],
            J.SHAPE_SECOND,
            "the second declared row is the shape this battery builds learners on "
            "(docs/L2/agents/shapes.md §1, D-29): %r" % (list(names),),
        )
        self.assertTrue(
            catalogue[names[0]].get("default"),
            "the row the catalogue reads first is the row it marks as the default, so "
            "the order and the flag are one statement (shapes.md §1, D-29): %r"
            % (catalogue[names[0]],),
        )
        for name in names:
            with self.subTest(shape=name):
                row = catalogue[name]
                learner = J.shaped_learner(
                    "naive-stack",
                    J.WIDTH_SHAPE,
                    J.DEPTH_SHAPE,
                    J.LEARNER_SEED_SHAPE,
                    name,
                )
                self.assertEqual(
                    J.learner_game(learner),
                    name,
                    "a learner built on a declared shape reports that shape -- the "
                    "identity a container records (shapes.md §1-§2, §5): %r against %r"
                    % (J.learner_game(learner), name),
                )
                space = J.shaped_action_space(name)
                width = len(space)
                self.assertEqual(
                    J.learner_actions(learner),
                    width,
                    "the head's width is the shape's descriptor count, read off "
                    "features.action_space and never a table's literal (shapes.md §1-"
                    "§2, sizing.md §6, ASM-40): %r against %r"
                    % (J.learner_actions(learner), width),
                )
                self.assertEqual(
                    width,
                    row["head_width"],
                    "the row engine publishes declares the head width this module reads, "
                    "so one shape's head is never a second spelling of the other's "
                    "(shapes.md §1-§2, ASM-40): %r against %r"
                    % (width, row["head_width"]),
                )
                self.assertEqual(
                    [space[index]["name"] for index in sorted(space)],
                    list(row["actions"]),
                    "the vocabulary is the row's descriptors in that shape's declared "
                    "order, which this module never defines and never re-derives "
                    "(shapes.md §3, features/shapes.md §3): %r against %r"
                    % ([space[index]["name"] for index in sorted(space)],
                       list(row["actions"])),
                )
                for index in range(width):
                    with self.subTest(shape=name, index=index):
                        self.assertEqual(
                            J.shaped_decode_action(index, name),
                            row["actions"][index],
                            "decode_action covers exactly this shape's indices, and "
                            "index %d is the descriptor the row declares there "
                            "(features/shapes.md §4, docs/L2/agents/surface.md §2, §9): "
                            "%r against %r"
                            % (index, J.shaped_decode_action(index, name),
                               row["actions"][index]),
                        )
                self.assert_refusal(
                    "decode_action",
                    ((name,), (str(width),)),
                    lambda: J.shaped_decode_action(width, name),
                    note="JOIN-AGT-14.1 the index %d past the %d descriptors of %r"
                    % (width, width, name),
                )
        by_absence = J.build_learner(
            J.learner_spec(
                "naive-stack", J.WIDTH_SHAPE, J.DEPTH_SHAPE, J.LEARNER_SEED_SHAPE
            )
        )
        self.assertEqual(
            J.learner_game(by_absence),
            names[0],
            "a spec naming no shape is built on the default shape -- the catalogue's "
            "first row and not a third name (shapes.md §1, docs/L2/agents/surface.md "
            "§4, D-29): %r" % (J.learner_game(by_absence),),
        )
        def undeclared_spec():
            """A spec whose `game` is undeclared and whose encoder is the default's.

            The encoder is built for the default shape on purpose: `features.
            build_encoder` refuses a shape name too, and its refusal standing in front of
            `build_learner`'s would leave this module's own refusal unasserted
            (`features/shapes.md` §6, `docs/L2/agents/shapes.md` §6, D-13).
            """
            spec = J.learner_spec(
                "naive-stack", J.WIDTH_SHAPE, J.DEPTH_SHAPE, J.LEARNER_SEED_SHAPE
            )
            spec["game"] = J.SHAPE_UNDECLARED
            return spec

        message = self.assert_refusal(
            "build_learner",
            ((J.SHAPE_UNDECLARED,),),
            lambda: J.build_learner(undeclared_spec()),
            note="JOIN-AGT-14.1 an undeclared shape name",
        )
        for name in names:
            self.assert_refusal(
                "build_learner",
                ((name,),),
                lambda: J.build_learner(undeclared_spec()),
                note="JOIN-AGT-14.1 the declared name %r the refusal must offer"
                % (name,),
            )
        positions = [message.lower().find(name.lower()) for name in names]
        self.assertNotIn(
            -1,
            positions,
            "the refusal must name every declared shape, so a typo reads as one "
            "(shapes.md §1, §6, D-13): %r" % (message,),
        )
        self.assertEqual(
            positions,
            sorted(positions),
            "the names this module restates are listed in the catalogue's own order, "
            "the default first (shapes.md §1, D-29): %r in %r"
            % (positions, message),
        )


class ShapeHead(J.JoinCase):
    """The head's width following the shape through `param_count`."""

    def test_join_agt_14_2_the_head_width_follows_the_shape_through_param_count(self):
        """JOIN-AGT-14.2 for one kind at one width and one depth the two declared
        shapes' `param_count` each equals `architecture.md` §5's sum with **that**
        shape's `A` in the output term and **that** shape's own input width in the input
        term, the two differing by `(I₂ − I₁)·W` for the wider observation plus
        `(A₂ − A₁)·W + (A₂ − A₁)` for the extra head rows, while a spec naming the default
        shape reports the count a spec naming no shape reports — one learner, one count
        (`docs/L2/agents/shapes.md` §2, `docs/L3/agents/shapes.md` §2, `docs/L1/
        shapes.md` §8, ASM-44, `docs/L2/features/capacity.md` §2, `sizing.md` §6, ASM-10,
        ASM-40, D-29).

        A shape's history capacity is its own, so its encoder's width is too: 203 dense
        over 24 slots on the default shape and 329 over 66 on `no-limit-100`, and a token
        kind is sized by its vocabulary on both.  Both learners are therefore built with
        **that shape's** encoder, which is the size they are built at, and the input
        width each reports is read out of `features.observation_spec` — never written
        down here (`docs/L1/shapes.md` §8, ASM-44).
        """
        kind, width, depth = "naive-stack", J.WIDTH_SHAPE, J.DEPTH_SHAPE
        names = J.shape_names()
        default_name, second_name = names[0], names[1]
        first, second = J.head_width(default_name), J.head_width(second_name)
        catalogue = J.game_shapes()
        for name, counted in ((default_name, first), (second_name, second)):
            with self.subTest(shape=name):
                self.assertEqual(
                    counted,
                    catalogue[name]["head_width"],
                    "A is the row's declared head width, read through the one granted "
                    "call and not a literal of this battery's (shapes.md §1-§2, "
                    "sizing.md §6, ASM-40): %r against %r"
                    % (counted, catalogue[name]["head_width"]),
                )
        widths = {
            default_name: J.shaped_input_size(kind, default_name),
            second_name: J.shaped_input_size(kind, second_name),
        }
        named_default = J.build_learner(
            J.shaped_learner_spec(
                kind, width, depth, J.LEARNER_SEED_SHAPE, default_name
            )
        )
        by_absence = J.build_learner(
            J.learner_spec(kind, width, depth, J.LEARNER_SEED_SHAPE)
        )
        other = J.build_learner(
            J.shaped_learner_spec(
                kind, width, depth, J.LEARNER_SEED_SHAPE, second_name
            )
        )
        self.assertEqual(
            J.param_count(named_default),
            J.param_count(by_absence),
            "naming the default shape explicitly and naming nothing are one learner and "
            "one count -- absence is the default and not a defaulting of a name "
            "(shapes.md §1-§2, docs/L2/agents/surface.md §4, D-29): %r against %r"
            % (J.param_count(named_default), J.param_count(by_absence)),
        )
        for name, learner, counted in (
            (default_name, named_default, first),
            (second_name, other, second),
        ):
            with self.subTest(shape=name, counted=counted):
                self.assertEqual(
                    int(learner.layout.input_dim),
                    widths[name],
                    "the learner's input width is not the one its shape's encoder "
                    "declares, so it was not sized from the shape it decides in "
                    "(docs/L1/shapes.md §8, ASM-44): %r against %r"
                    % (int(learner.layout.input_dim), widths[name]),
                )
                self.assertEqual(
                    J.param_count(learner),
                    J.declared_param_count(kind, width, depth, 0.0, counted, widths[name]),
                    "the count is architecture.md §5's sum with this shape's A in its "
                    "output term A·W + A and this shape's own input width in its input "
                    "term (shapes.md §2, docs/L1/shapes.md §8, ASM-44, sizing.md §6, "
                    "ASM-40): %r against the formula at A = %d, I = %d and W = %d"
                    % (J.param_count(learner), counted, widths[name], width),
                )
        self.assertEqual(
            J.param_count(other) - J.param_count(named_default),
            (widths[second_name] - widths[default_name]) * width
            + (second - first) * width
            + (second - first),
            "the two shapes' counts differ by exactly the wider input block, "
            "(I₂ − I₁)·W, plus the head's extra term, (A₂ − A₁)·W + (A₂ − A₁), so the "
            "shape reaches the measurement through its own width and its own A and "
            "through nothing else (shapes.md §2, docs/L1/shapes.md §8, ASM-44, ASM-10, "
            "ASM-40): %r against %r for I = %d and %d at A = %d and %d and W = %d"
            % (J.param_count(other) - J.param_count(named_default),
               (widths[second_name] - widths[default_name]) * width
               + (second - first) * width + (second - first),
               widths[default_name], widths[second_name], first, second, width),
        )
        hand = J.new_hand(J.DEAL_SHAPE_A)
        observation = J.encode(
            J.build_encoder(J.encoding_for(kind)), J.readout(hand)
        )
        mask = J.legal_indices(J.legal_actions(hand))
        self.assertEqual(
            J.action_index(J.act(named_default, observation, mask)),
            J.action_index(J.act(by_absence, observation, mask)),
            "and they are one learner in the decision too, not only in the count: a "
            "real readout gets one index from both (shapes.md §2, docs/L2/agents/"
            "surface.md §4, §6): %r" % (J.action_index(J.act(by_absence, observation,
                                                            mask)),),
        )


class ShapeDecisionSpace(J.JoinCase):
    """The second shape's six-index decision space on real hands."""

    def test_join_agt_14_3_the_six_index_decision_space_on_real_hands(self):
        """JOIN-AGT-14.3 on real `no-limit-100` hands dealt by `engine.new_hand(seed,
        shape=...)` the mask `features.legal_indices` gives is that shape's own
        positions, including 3, 4 and 5 wherever those descriptors are legal;
        `agents.act` on a no-limit learner answers a member of it at every decision of a
        walked hand; a mask and a transition from that shape handed to a **default-shape**
        learner are refused by `act` and by `learn`, naming the learner's shape and the
        offending index; and a no-limit policy played through `engine.play_hand(...,
        shape=...)` returns only descriptors `engine.legal_actions` offered at that
        decision (`docs/L2/agents/shapes.md` §2-§3, §6, `docs/L2/features/shapes.md` §3-§5,
        `docs/L3/agents/shapes.md` §3, `sizing.md` §3, ASM-37, D-29, D-2).
        """
        catalogue = J.game_shapes()
        names = tuple(catalogue)
        default_name, second_name = names[0], names[1]
        vocabulary = tuple(catalogue[second_name]["actions"])
        width = J.head_width(second_name)
        self.assertEqual(
            len(vocabulary),
            width,
            "the second shape's vocabulary and its head width are one count "
            "(shapes.md §2-§3, sizing.md §6): %r against %r"
            % (list(vocabulary), width),
        )
        self.assertGreater(
            width,
            max(BAND_INDICES),
            "the second shape declares the price bands this case walks (sizing.md §3, "
            "ASM-37): %r" % (list(vocabulary),),
        )
        encoder = J.shaped_encoder(J.encoding_for("naive-stack"), second_name)
        learner = J.shaped_learner(
            "naive-stack",
            J.WIDTH_SHAPE,
            J.DEPTH_SHAPE,
            J.LEARNER_SEED_SHAPE,
            second_name,
        )
        decisions = 0
        bands = {index: 0 for index in BAND_INDICES}
        for seed in (J.DEAL_SHAPE_A, J.DEAL_SHAPE_B):
            walked = J.shaped_walk(seed, second_name, J.caller_in(second_name))
            self.assertGreater(
                len(walked),
                0,
                "a dealt no-limit hand offers at least one decision "
                "(docs/L2/engine/surface.md §6): deal %r" % (seed,),
            )
            for _hand, facts, legal, _chosen, _index in walked:
                with self.subTest(seed=seed, decision=decisions):
                    mask = J.legal_indices(legal)
                    self.assertEqual(
                        mask,
                        tuple(vocabulary.index(descriptor) for descriptor in legal),
                        "the mask is the legal set's positions in that shape's declared "
                        "order -- position-aligned, never sorted and never re-derived "
                        "(features/shapes.md §4, docs/L2/features/surface.md §8): %r "
                        "against %r" % (mask, list(legal)),
                    )
                    self.assertTrue(
                        mask,
                        "the mask is never empty (docs/L2/agents/surface.md §2, "
                        "features/shapes.md §4): %r" % (mask,),
                    )
                    self.assertEqual(
                        len(set(mask)),
                        len(mask),
                        "at most one entry per index of the shape's vocabulary "
                        "(docs/L2/agents/surface.md §2): %r" % (mask,),
                    )
                    for index in mask:
                        self.assertTrue(
                            0 <= index < width,
                            "every index is one of the shape's %d, so a six-index "
                            "learner never reads a default-shape index (shapes.md §3, "
                            "sizing.md §3): %r" % (width, index),
                        )
                    for index in range(width):
                        if vocabulary[index] in legal:
                            self.assertIn(
                                index,
                                mask,
                                "the legal descriptor %r is in the mask at its own "
                                "index %d (features/shapes.md §4, ASM-37): %r"
                                % (vocabulary[index], index, mask),
                            )
                        else:
                            self.assertNotIn(
                                index,
                                mask,
                                "a band with no legal amount in it is simply absent, "
                                "never collapsed onto its neighbour and never padded "
                                "(features/shapes.md §4, sizing.md §2): %r at %r"
                                % (index, mask),
                            )
                    for index in BAND_INDICES:
                        if vocabulary[index] in legal:
                            bands[index] += 1
                    chosen = J.action_index(
                        J.act(learner, J.encode(encoder, facts), mask)
                    )
                    self.assert_index_in(
                        chosen, mask, "JOIN-AGT-14.3 decision %d" % (decisions,)
                    )
                    decisions += 1
        self.assertGreaterEqual(
            decisions,
            width,
            "the walks reach more decisions than the shape has descriptors, so the "
            "six-index space is asserted over a real hand's whole course rather than "
            "at one decision (shapes.md §3): %d decisions" % (decisions,),
        )
        for index in BAND_INDICES:
            self.assertGreater(
                bands[index],
                0,
                "the walk reaches decisions on which the descriptor at index %d (%r) is "
                "legal, so that band's index is asserted and not only the two the two "
                "shapes share (features/shapes.md §3-§4, sizing.md §3, ASM-37): %r"
                % (index, vocabulary[index], bands),
            )
        hand = J.shaped_hand(J.DEAL_SHAPE_C, second_name)
        foreign = J.legal_indices(J.legal_actions(hand))
        default_learner = J.shaped_learner(
            "naive-stack",
            J.WIDTH_SHAPE,
            J.DEPTH_SHAPE,
            J.LEARNER_SEED_SHAPE,
            default_name,
        )
        offender = min(
            index for index in foreign if index >= J.head_width(default_name)
        )
        # The observation alone cannot betray its shape -- both shapes declare the same
        # widths, dtype, vocabulary of tokens and block table -- so the default-shape
        # encoder is used on the no-limit decision on purpose and the refusal must come
        # from the mask (`docs/L2/agents/shapes.md` §3, `docs/L2/features/shapes.md` §5).
        observation = J.encode(
            J.build_encoder(J.encoding_for("naive-stack")), J.readout(hand)
        )
        self.assert_refusal(
            "act",
            ((default_name,), (str(offender),)),
            lambda: J.act(default_learner, observation, foreign),
            note="JOIN-AGT-14.3 a %r mask at a %r learner (shapes.md §3, §6, "
            "features/shapes.md §5)" % (second_name, default_name),
        )
        transition = {
            "observation": observation,
            "next_observation": observation,
            "action": int(foreign[1] if len(foreign) > 1 else foreign[0]),
            "reward": 0.0,
            "terminal": False,
            "legal": list(foreign),
            "next_legal": list(foreign),
            # D-43's boundary is **required** of every transition (`records.md` §4,
            # `counterfactual.md` §2), so this hand-built record carries the seed of the
            # deal it was read off: without it `learn` would refuse the record for the
            # missing key and the shape's indices would never be reached, which is a
            # weaker case than the one this note states.
            "episode": int(J.DEAL_SHAPE_C),
        }
        self.assert_refusal(
            "learn",
            ((default_name,), (str(offender),)),
            lambda: J.learn(default_learner, [transition]),
            note="JOIN-AGT-14.3 a transition recorded on %r read as one of a %r "
            "learner's indices (shapes.md §3: `learn` refuses `action`, `legal` and "
            "`next_legal` alike)" % (second_name, default_name),
        )
        policy = J.recording(
            J.as_policy(learner, encoder, J.POLICY_SEED_SHAPE)
        )
        record = J.shaped_play_hand(
            J.DEAL_SHAPE_B, policy, J.caller_in(second_name), second_name
        )
        held = J.episode_decisions(record)
        self.assertTrue(
            held,
            "a played no-limit episode records at least one decision "
            "(docs/L1/records.md §5): %r" % (record,),
        )
        for decision in held:
            self.assert_descriptor_in(
                J.decision_legal(decision),
                J.decision_action(decision),
                "JOIN-AGT-14.3 the episode's own decision",
            )
        self.assertTrue(
            policy.calls,
            "engine.play_hand(..., shape=...) must call the no-limit policy it was "
            "handed (docs/L2/engine/surface.md §10): %r" % (record,),
        )
        for _facts, legal, chosen in policy.calls:
            self.assert_descriptor_in(
                legal, chosen, "JOIN-AGT-14.3 a no-limit policy's answer"
            )
            self.assertIn(
                chosen,
                vocabulary,
                "the answer decodes in the learner's shape's vocabulary, so a no-limit "
                "policy never returns the default shape's `raise` (shapes.md §3, "
                "docs/L3/agents/shapes.md §4, features/shapes.md §3): %r" % (chosen,),
            )


class ShapeTie(J.JoinCase):
    """The `tie` flag `act` records: on real hands and on a flat value vector."""

    def annealed(self, name, encoder, observation, mask):
        """A learner at the schedule's end whose head was moved by nothing.

        `still_batch`'s transitions carry a TD error of `0.0`, so the position advances
        to the annealed end while every parameter stays exactly as the initialisation
        drew it — which is what keeps a flat observation's masked values flat
        (`docs/L2/agents/shapes.md` §3-§4, `docs/L2/agents/surface.md` §7).
        """
        learner = J.shaped_learner(
            "naive-stack",
            J.WIDTH_SHAPE,
            J.DEPTH_SHAPE,
            J.LEARNER_SEED_SHAPE,
            name,
        )
        samples = J.exploration_samples()
        statistics = J.learn(learner, J.still_batch(observation, mask, samples))
        self.assertEqual(
            J.transitions_consumed(statistics),
            samples,
            "the still batch must reach the schedule's own length, or the learner is "
            "not at the annealed end (docs/L2/agents/surface.md §3, §7): %r"
            % (statistics,),
        )
        self.assertAlmostEqual(
            J.td_error(statistics),
            0.0,
            places=12,
            msg="the still batch moved the head, so the flat vector this case decides "
            "the flag on is gone (docs/L2/agents/shapes.md §3): %r" % (statistics,),
        )
        return learner

    def test_join_agt_14_4_the_tie_flag_on_a_real_decision_record(self):
        """JOIN-AGT-14.4 `act`'s record carries `tie` as a plain `bool` and `action` as a
        plain `int` at every decision of a walked hand of either shape, a member of the
        decision's mask; where the greedy arm's own answer differs the arm was the
        exploring one and the flag is false; and on a flat value vector at the annealed
        end the arm that decided a decision is determinable from the record's own `tie`
        — true means the tie-break chose it off a flat vector, so the index is the
        smallest masked one — while a one-element mask never reports a tie (`docs/L2/
        agents/shapes.md` §3-§4, `docs/L3/agents/shapes.md` §3, `docs/L2/agents/
        surface.md` §6, `records.md` §6, §15, `sizing.md` §3, ASM-37, D-29).
        """
        names = J.shape_names()
        for name in names:
            with self.subTest(shape=name):
                encoder = J.shaped_encoder(J.encoding_for("naive-stack"), name)
                learner = J.shaped_learner(
                    "naive-stack",
                    J.WIDTH_SHAPE,
                    J.DEPTH_SHAPE,
                    J.LEARNER_SEED_SHAPE,
                    name,
                )
                greedy = J.as_policy_mode(
                    learner, encoder, J.POLICY_SEED_SHAPE, "off"
                )
                compared = 0
                for seed in (J.DEAL_SHAPE_A, J.DEAL_SHAPE_C):
                    for _hand, facts, legal, _chosen, _index in J.shaped_walk(
                        seed, name, J.caller_in(name)
                    ):
                        mask = J.legal_indices(legal)
                        record = J.act(learner, J.encode(encoder, facts), mask)
                        index = J.plain_action(record)
                        tie = J.decision_tie(record)
                        self.assert_index_in(
                            index, mask, "JOIN-AGT-14.4 %r decision %d"
                            % (name, compared),
                        )
                        by_greedy = J.descriptor_index(legal, greedy(facts, legal))
                        if index != by_greedy:
                            self.assertFalse(
                                tie,
                                "the exploring arm drew this index -- the greedy arm's "
                                "own answer on the same decision is %r -- so no maximum "
                                "was consulted and the flag is false (shapes.md §3, "
                                "records.md §15, docs/L3/agents/rule.md §4): %r"
                                % (by_greedy, record),
                            )
                        if len(mask) == 1:
                            self.assertFalse(
                                tie,
                                "a one-element mask never reports a tie (shapes.md §3, "
                                "records.md §6, §15): %r" % (record,),
                            )
                        compared += 1
                self.assertGreaterEqual(
                    compared,
                    4,
                    "the flag is asserted over several decisions of two real hands, not "
                    "at one (shapes.md §3, records.md §6): %d decisions"
                    % (compared,),
                )
        start = J.exploration_start()
        self.assertGreaterEqual(
            start,
            1.0,
            "the schedule's declared starting rate is what a fresh learner explores at, "
            "so at position 0 every decision is the exploring arm's (docs/L2/agents/"
            "surface.md §3, docs/L3/agents/rule.md §4): %r" % (start,),
        )
        decided = 0
        for name in names:
            with self.subTest(shape=name, vector="flat"):
                encoder = J.shaped_encoder(J.encoding_for("naive-stack"), name)
                observation = J.flat_observation(encoder)
                whole = tuple(range(J.head_width(name)))
                self.assertEqual(
                    tuple(observation.shape),
                    tuple(J.observation_spec(encoder)["shape"]),
                    "the flat observation must be the declared shape and dtype, or the "
                    "flag is asserted on an observation the learner would refuse "
                    "(docs/L3/agents/architecture.md §6): %r" % (observation.shape,),
                )
                fresh = J.shaped_learner(
                    "naive-stack",
                    J.WIDTH_SHAPE,
                    J.DEPTH_SHAPE,
                    J.LEARNER_SEED_SHAPE,
                    name,
                )
                for candidates in (whole, whole[:2], whole[::2]):
                    record = J.act(fresh, observation, candidates)
                    self.assertIs(
                        type(J.decision_tie(record)),
                        bool,
                        "the flag is a plain bool (records.md §6, §15): %r" % (record,),
                    )
                    self.assert_index_in(
                        J.plain_action(record), candidates, "JOIN-AGT-14.4 fresh"
                    )
                    self.assertFalse(
                        J.decision_tie(record),
                        "at the schedule's start every decision is the exploring arm's, "
                        "which consults no maximum, so the flag is false even on a flat "
                        "vector and a mask of %d members (rule.md §4, shapes.md §3): %r"
                        % (len(candidates), record),
                    )
                annealed = self.annealed(name, encoder, observation, whole)
                for candidates in (whole, whole[:2], whole[2:]):
                    record = J.act(annealed, observation, candidates)
                    index = J.plain_action(record)
                    self.assert_index_in(
                        index, candidates, "JOIN-AGT-14.4 annealed"
                    )
                    if J.decision_tie(record):
                        decided += 1
                        self.assertEqual(
                            index,
                            min(candidates),
                            "the flag says the tie-break and not a strict maximum chose "
                            "this index on a flat vector, so the answer is the smallest "
                            "masked index and the arm is determinable from the record "
                            "alone (shapes.md §3, records.md §6, §15, rule.md §5, "
                            "ASM-37): %r at %r" % (record, candidates),
                        )
                for index in whole:
                    record = J.act(annealed, observation, (index,))
                    self.assertEqual(
                        J.plain_action(record),
                        index,
                        "a one-element mask decides its only member (shapes.md §3): %r"
                        % (record,),
                    )
                    self.assertFalse(
                        J.decision_tie(record),
                        "a one-element mask never reports a tie, even at the annealed "
                        "end (shapes.md §3, records.md §6, §15): %r" % (record,),
                    )
        self.assertGreaterEqual(
            decided,
            1,
            "no decision of the flat set reached the greedy arm, so the true half of "
            "the flag was never asserted: the annealed rate leaves at least one of "
            "these decisions to the tie-break (rule.md §4, shapes.md §3)",
        )


class ShapeExploration(J.JoinCase):
    """The policy's exploration mode: `off` takes no draw, and a third mode is refused."""

    def test_join_agt_14_5_off_answers_one_decision_at_two_seeds_and_draws_nothing(self):
        """JOIN-AGT-14.5 two `off` policies built from one learner and one encoder at two
        different seeds answer the same descriptor at every decision of a walked
        no-limit hand; with `agents.rule._draws` stood aside by a stub that raises, an
        `off` policy still decides while a `schedule` policy refuses, which is what "no
        generator is drawn from at all" means; and a mode outside the two is refused
        naming `as_policy`, the value and both declared modes (`docs/L2/agents/shapes.md`
        §3-§4, §6, `docs/L3/agents/shapes.md` §4, `docs/L2/agents/surface.md` §10,
        `sizing.md` §4, `records.md` §6, ASM-2, D-29).
        """
        names = J.shape_names()
        name = names[1]
        vocabulary = tuple(J.game_shapes()[name]["actions"])
        encoder = J.shaped_encoder(J.encoding_for("naive-stack"), name)
        learner = J.shaped_learner(
            "naive-stack",
            J.WIDTH_SHAPE,
            J.DEPTH_SHAPE,
            J.LEARNER_SEED_SHAPE,
            name,
        )
        one = J.as_policy_mode(learner, encoder, J.POLICY_SEED_SHAPE, "off")
        other = J.as_policy_mode(learner, encoder, J.POLICY_SEED_SHAPE_OTHER, "off")
        compared = 0
        for _hand, facts, legal, _chosen, _index in J.shaped_walk(
            J.DEAL_SHAPE_B, name, J.caller_in(name)
        ):
            first = one(facts, legal)
            second = other(facts, legal)
            self.assert_descriptor_in(
                legal, first, "JOIN-AGT-14.5 an off policy"
            )
            self.assert_descriptor_in(
                legal, second, "JOIN-AGT-14.5 an off policy at another seed"
            )
            self.assertIn(
                first,
                vocabulary,
                "an off policy of the six-index learner answers one of that shape's "
                "descriptors (shapes.md §3, docs/L3/agents/shapes.md §4): %r"
                % (first,),
            )
            self.assertTrue(
                J.same_descriptor(first, second),
                "the mode reads no seed, so two off policies built from one learner and "
                "one encoder at different seeds answer one descriptor at every decision "
                "of a real hand (shapes.md §4, sizing.md §4, ASM-2): %r against %r at "
                "decision %d" % (first, second, compared),
            )
            compared += 1
        self.assertGreaterEqual(
            compared,
            4,
            "the equality must cover several decisions of one walked hand, because a "
            "single coincidence is not the mode's claim (shapes.md §4): %d decisions"
            % (compared,),
        )
        hand = J.shaped_hand(J.DEAL_SHAPE_A, name)
        facts, legal = J.readout(hand), J.legal_actions(hand)
        scheduled = J.as_policy(learner, encoder, J.POLICY_SEED_SHAPE)
        with J.draws_stood_aside():
            chose = J.as_policy_mode(
                learner, encoder, J.POLICY_SEED_SHAPE, "off"
            )(facts, legal)
            self.assert_descriptor_in(
                legal, chose, "JOIN-AGT-14.5 an off policy with the draw stood aside"
            )
            with self.assertRaises(Exception) as raised:
                scheduled(facts, legal)
            self.assertIn(
                "_draws",
                str(raised.exception),
                "the schedule policy must be refused by the stub that replaced "
                "agents.rule._draws, or the stub was not standing and this half shows "
                "nothing (shapes.md §4, sizing.md §4): %r" % (raised.exception,),
            )
        self.assert_descriptor_in(
            legal,
            scheduled(facts, legal),
            "JOIN-AGT-14.5 the draw restored after the block",
        )
        self.assert_refusal(
            "as_policy",
            ((J.EXPLORATION_UNDECLARED,),)
            + tuple((mode,) for mode in J.EXPLORATION_MODES),
            lambda: J.as_policy_mode(
                learner, encoder, J.POLICY_SEED_SHAPE, J.EXPLORATION_UNDECLARED
            ),
            note="JOIN-AGT-14.5 an exploration mode outside the two declared ones",
        )


class ShapeWidth(J.JoinCase):
    """The two shapes' input widths and counts, each its own."""

    def test_join_agt_14_6_the_two_shapes_widths_and_counts_are_each_their_own(self):
        """JOIN-AGT-14.6 for `naive-stack` at one width and one depth a learner built on
        each declared shape with **that shape's** encoder reports the input width its
        encoder's `observation_spec` declares — the two shapes' 203 and 329 dense, which
        `features` publishes and this battery never writes down — and a `param_count` equal
        to `architecture.md` §5's sum at that width, namely 10,119 and 14,766 at width 36
        and depth 2, the two differing by exactly `126·W` for the input block plus
        `(A₂ − A₁)·W + (A₂ − A₁)` for the extra head rows (`docs/L1/shapes.md` §8, ASM-44,
        `docs/L2/agents/shapes.md` §2, `docs/L2/features/capacity.md` §2, `sizing.md` §6,
        `architecture.md` §5, `ladder.md` §3, ASM-10, ASM-40, D-29).

        The input term is the shape's because a shape's history capacity is its own: 24
        slots and `131 + 3·24 = 203` on the default shape against 66 slots and
        `131 + 3·66 = 329` on `no-limit-100`, and a token kind would be sized by its
        vocabulary on both (`docs/L2/features/capacity.md` §2, ASM-42, ASM-44).  So neither
        shape's count is the other's, and the difference is the sum of the two facts the
        shape owns — its width and its `A` — and nothing else.  Every number read here comes
        out of `features.observation_spec`, `features.action_space` and the engine's row;
        the two counts appear as literals only in the failure messages, where they say what
        the design's table records (`docs/L1/battery.md` §4, D-15).
        """
        kind, width, depth = "naive-stack", WIDTH_DOCUMENTED, DEPTH_DOCUMENTED
        names = J.shape_names()
        first_name, second_name = names[0], names[1]
        widths = {name: J.shaped_input_size(kind, name) for name in names}
        heads = {name: J.head_width(name) for name in names}
        counts = {}
        for name in names:
            with self.subTest(shape=name):
                spec = J.observation_spec(
                    J.shaped_encoder(J.encoding_for(kind), name)
                )
                self.assertEqual(
                    int(tuple(spec["shape"])[0]),
                    widths[name],
                    "the shape's dense width is its encoder's `observation_spec`'s own "
                    "`shape`, so the number this case uses is the published one and not a "
                    "copy (docs/L2/features/capacity.md §2, ASM-44): %r against %r"
                    % (spec["shape"], (widths[name],)),
                )
                learner = J.build_learner(
                    J.shaped_learner_spec(
                        kind, width, depth, J.LEARNER_SEED_SHAPE, name
                    )
                )
                self.assertEqual(
                    int(learner.layout.input_dim),
                    widths[name],
                    "a learner built on %r with that shape's encoder is not built at that "
                    "shape's own input width, so the input block is not the shape's "
                    "(docs/L1/shapes.md §8, ASM-44, docs/L2/agents/shapes.md §2): %r "
                    "against %r" % (name, int(learner.layout.input_dim), widths[name]),
                )
                self.assertEqual(
                    tuple(learner.shape),
                    tuple(spec["shape"]),
                    "the learner's declared observation is not one the shape's encoder "
                    "answers, so `act` would refuse the observations its own shape produces "
                    "(architecture.md §6, docs/L1/shapes.md §8, ASM-44): %r against %r"
                    % (learner.shape, spec["shape"]),
                )
                counts[name] = J.param_count(learner)
                self.assertEqual(
                    counts[name],
                    J.declared_param_count(kind, width, depth, 0.0, heads[name],
                                           widths[name]),
                    "the count on %r is not architecture.md §5's sum with that shape's own "
                    "input width in its input term and its own A in the output term: the "
                    "design's table records 10,119 at W = 36, D = 2 on %r and 14,766 on %r "
                    "(docs/L2/agents/shapes.md §2, docs/L2/features/capacity.md §2, "
                    "sizing.md §6, ASM-10, ASM-44): %r against the formula at I = %d, "
                    "A = %d, W = %d and D = %d"
                    % (
                        name,
                        first_name,
                        second_name,
                        counts[name],
                        widths[name],
                        heads[name],
                        width,
                        depth,
                    ),
                )
        self.assertNotEqual(
            widths[first_name],
            widths[second_name],
            "the two declared shapes declare one observation width, so no case here can "
            "say that a learner takes its input width from its own shape "
            "(docs/L2/features/capacity.md §2, ASM-44): %r" % (widths,),
        )
        self.assertEqual(
            counts[second_name] - counts[first_name],
            (widths[second_name] - widths[first_name]) * width
            + (heads[second_name] - heads[first_name]) * width
            + (heads[second_name] - heads[first_name]),
            "the two counts differ by exactly the wider input block, (I₂ − I₁)·W, plus the "
            "head's extra term, (A₂ − A₁)·W + (A₂ − A₁), so the shape reaches the measurement "
            "through its own width and its own A and through nothing else — the design's "
            "10,119 and 14,766 are 126·36 = 4,536 plus 3·36 + 3 = 111 apart at W = 36 "
            "(docs/L1/shapes.md §8, ASM-44, docs/L2/agents/shapes.md §2, ASM-40): %r "
            "against %r for I = %r and A = %r at W = %d"
            % (
                counts[second_name] - counts[first_name],
                (widths[second_name] - widths[first_name]) * width
                + (heads[second_name] - heads[first_name]) * width
                + (heads[second_name] - heads[first_name]),
                widths,
                heads,
                width,
            ),
        )

    def test_join_agt_14_7_an_encoderless_spec_naming_the_second_shape_is_refused(self):
        """JOIN-AGT-14.7 an otherwise valid encoder-less spec naming the second declared
        shape is refused by `agents` itself, naming `build_learner`, that shape and the word
        `encoder`, so no module silently sizes it at the default shape's 203 — while the same
        spec carrying that shape's encoder builds a learner at that shape's own width
        (`docs/L1/shapes.md` §8, ASM-44, `docs/L2/agents/shapes.md` §2, §6,
        `docs/L2/features/capacity.md` §2, §5, `docs/L2/agents/surface.md` §4, §9,
        `docs/L3/agents/errors.md` §3, D-29).

        The spec is `learner_spec`'s — one encoder of the kind's own encoding, the kind's
        settings and an invented seed — with the encoder key **deleted** and the second shape
        named, which is exactly the spec `docs/L1/shapes.md` §8 says has no width to be built
        at: a kind's declared `observation_size` is the **default** shape's, so a learner on
        another shape takes its input width from that shape's encoder and an encoder-less
        build on one is refused by name (`docs/L2/features/capacity.md` §5, ASM-44).  The
        refusal is one number off the twin below it, so the case distinguishes "refused
        because the encoder is absent" from "refused because the spec is invalid".
        """
        kind = "naive-stack"
        default_size = int(J.learners()["architectures"][kind]["observation_size"])
        spec = J.learner_spec(
            kind, J.WIDTH_SHAPE, J.DEPTH_SHAPE, J.LEARNER_SEED_SHAPE
        )
        self.assertIn(
            "encoder",
            spec,
            "the support's own spec no longer carries an encoder, so this case's deletion "
            "below would assert nothing about an encoder-less build (docs/L2/agents/"
            "surface.md §4): %r" % (spec,),
        )
        spec.pop("encoder")
        spec["game"] = J.SHAPE_SECOND
        self.assertNotIn(
            "encoder",
            spec,
            "this case's spec still carries an encoder, and the refusal under judgement is "
            "the encoder-less one's (docs/L1/shapes.md §8, ASM-44): %r" % (spec,),
        )
        self.assertEqual(
            spec["game"],
            J.SHAPE_SECOND,
            "the spec under judgement does not name the second shape (shapes.md §1, D-29): "
            "%r" % (spec,),
        )
        message = self.assert_refusal(
            "build_learner",
            ((J.SHAPE_SECOND,), ("encoder",), (str(default_size),)),
            lambda: J.build_learner(spec),
            note="JOIN-AGT-14.7 an encoder-less spec naming %r" % (J.SHAPE_SECOND,),
        )
        self.assertIn(
            J.SHAPE_DEFAULT,
            message,
            "the refusal does not name the default shape whose declared %d the kind's "
            "observation_size is, so a reader cannot tell which shape that number belongs to "
            "(docs/L1/shapes.md §8, ASM-44, docs/L3/agents/errors.md §3): %r"
            % (default_size, message),
        )
        twin = dict(spec)
        twin["encoder"] = J.shaped_encoder(J.encoding_for(kind), J.SHAPE_SECOND)
        built = J.build_learner(twin)
        self.assertEqual(
            J.learner_game(built),
            J.SHAPE_SECOND,
            "the spec that differs from the refused one only by carrying the shape's encoder "
            "does not build a learner of that shape (shapes.md §1-§2, D-29): %r"
            % (J.learner_game(built),),
        )
        self.assertEqual(
            int(built.layout.input_dim),
            J.shaped_input_size(kind, J.SHAPE_SECOND),
            "the twin's learner is not built at the shape's own input width, so this case "
            "cannot say the refusal was the encoder's absence rather than the shape's "
            "(docs/L1/shapes.md §8, ASM-44): %r against %r"
            % (int(built.layout.input_dim), J.shaped_input_size(kind, J.SHAPE_SECOND)),
        )
        self.assertNotEqual(
            J.param_count(built),
            J.declared_param_count(
                kind, J.WIDTH_SHAPE, J.DEPTH_SHAPE, 0.0, J.head_width(J.SHAPE_SECOND)
            ),
            "the twin reports the count architecture.md §5's sum gives at the **default** "
            "shape's input width, so something sized it at 203 after all "
            "(docs/L1/shapes.md §8, ASM-44, docs/L2/features/capacity.md §5): %r"
            % (J.param_count(built),),
        )
        self.assertEqual(
            J.param_count(built),
            J.declared_param_count(
                kind,
                J.WIDTH_SHAPE,
                J.DEPTH_SHAPE,
                0.0,
                J.head_width(J.SHAPE_SECOND),
                J.shaped_input_size(kind, J.SHAPE_SECOND),
            ),
            "the twin's count is not architecture.md §5's sum at the shape's own input width "
            "(docs/L2/agents/shapes.md §2, sizing.md §6, ASM-44): %r"
            % (J.param_count(built),),
        )


class ShapeBaselines(J.JoinCase):
    """The six fixed baselines on every declared shape: the folder's stack and the oracle's question."""

    def test_join_agt_14_8_the_fixed_baselines_decide_on_every_declared_shape(self):
        """JOIN-AGT-14.8 every one of the six baselines, built for a declared shape with `agents.build_baseline(name, seed, shape=...)`, answers a member of a real decision's `legal_actions` on **every** declared shape — the six-seat row included — `fold-large-bet` folds exactly where `2·to_call` exceeds the `starting_stack` the engine's own row declares for that shape, and `oracle`'s answer is consistent with the pot-odds inequality re-issued through `engine.equity` at that shape, so the shape argument's two jobs are held to the two modules that declare them (`docs/L2/agents/baselines.md` §2-§3, `docs/L1/e2e-surface.md` §3.1, §3.3, `docs/L1/folders.md` §2, `docs/L1/seats.md` §2, §6, ASM-4, ASM-31, D-6, D-21, D-33).

        Two statements and both are cross-module.  **The stack** is the row's: the case
        reads `starting_stack` out of `engine.game_shapes()` and never writes a 20 or a 100
        down, so a folder holding a copy of the default shape's twenty would be red here on
        the six-seat row, where 11 chips is under half of that shape's 100 and over half of
        the default's 20.  **The equity** is the engine's: `engine.equity` reads the seat
        count off the readout's `stacks`, so a six-seat decision is asked six-way, and the
        oracle's index is the inequality's own — which is the whole of what a `shape`-aware
        oracle buys at a table with more than two seats (`docs/L2/engine/surface.md` §11,
        `docs/L1/seats.md` §2, ASM-4, D-33).  The catalogue's baseline names are not
        invented: they are `agents.baselines()`'s, and the shapes are the engine's, as
        `docs/L1/battery.md` §4 requires of a declared game and its fixed standards.
        """
        catalogue = J.game_shapes()
        names = J.shape_names()
        self.assertGreaterEqual(
            len(names),
            3,
            "the catalogue declares the six-seat row this case is about beside the two it "
            "already published (docs/L1/seats.md §2, D-33): %r" % (list(names),),
        )
        baselines = tuple(J.baselines())
        self.assertEqual(
            len(baselines), 6, "agents.baselines() declares the six: %r" % (list(baselines),)
        )
        samples = J.oracle_samples()
        eng = J.mod("engine")
        decisions = 0
        fold_side = 0
        call_side = 0
        for name in names:
            with self.subTest(shape=name):
                row = catalogue[name]
                stack = int(row["starting_stack"])
                self.assertGreater(
                    stack,
                    0,
                    "the row of %r declares no positive starting stack, so this case's "
                    "boundary is undecidable (shapes.md §2): %r" % (name, stack),
                )
                self.assertEqual(
                    int(eng.game_config(name)["starting_stack"]),
                    stack,
                    "the starting stack this case read out of the catalogue row is not the "
                    "one `engine.game_config` declares for %r, so the two readings of the "
                    "shape disagree (docs/L2/engine/surface.md §3, ASM-31): %r against %r"
                    % (name, stack, eng.game_config(name)["starting_stack"]),
                )
                walked = J.shaped_walk(J.DEAL_SHAPE_A, name, J.caller_in(name))
                self.assertGreater(
                    len(walked),
                    0,
                    "a dealt hand of %r offers at least one decision "
                    "(docs/L2/engine/surface.md §6): deal %r" % (name, J.DEAL_SHAPE_A),
                )
                policies = {
                    baseline: J.build_baseline(baseline, J.BASELINE_SEED, name)
                    for baseline in baselines
                }
                for _hand, facts, legal, _chosen, _index in walked[:3]:
                    for baseline, policy in policies.items():
                        with self.subTest(shape=name, baseline=baseline, decision=decisions):
                            answer = policy(facts, legal)
                            self.assert_descriptor_in(
                                legal,
                                answer,
                                "JOIN-AGT-14.8 %r on %r" % (baseline, name),
                            )
                            self.assertFalse(
                                hasattr(policy, "learning_rule")
                                or hasattr(policy, "utility"),
                                "a baseline of %r built for %r carries a rule or a utility, "
                                "and a baseline learns nothing and is trained on no reward "
                                "(e2e-surface.md §2, D-6, D-19, D-20)" % (baseline, name),
                            )
                    decisions += 1
                # The folder's boundary, on a real decision of this shape: half the stack
                # the engine's own row declares, and one chip above it.
                folder = policies["fold-large-bet"]
                for to_call in (stack // 2, stack // 2 + 1):
                    probe = dict(walked[0][1], to_call=to_call)
                    legal = walked[0][2]
                    folds = 2 * to_call > stack
                    with self.subTest(shape=name, to_call=to_call):
                        chosen = folder(probe, legal)
                        self.assert_descriptor_in(
                            legal, chosen, "JOIN-AGT-14.8 fold-large-bet"
                        )
                        if "fold" not in list(legal):
                            continue
                        expected = "fold" if folds else "check-call"
                        self.assertTrue(
                            J.same_descriptor(chosen, expected),
                            "with %d chips to call on the shape %r, whose declared starting "
                            "stack is %d, the folder answered %r and the rule says %r "
                            "(docs/L1/folders.md §2, ASM-31, docs/L2/agents/baselines.md "
                            "§2, D-33)"
                            % (to_call, name, stack, chosen, expected),
                        )
                # The oracle's inequality, re-issued at the baseline's own seed and the
                # catalogue's declared count, on the same real decisions of this shape.
                oracle = policies["oracle"]
                for position, (_hand, facts, legal, _c, _i) in enumerate(walked[:3]):
                    pot = int(facts["pot"])
                    to_call = int(facts["to_call"])
                    total = pot + to_call
                    odds = to_call / total if total else 0.0
                    equity = float(eng.equity(facts, J.BASELINE_SEED, samples))
                    with self.subTest(shape=name, oracle=position):
                        self.assertGreaterEqual(equity, 0.0)
                        self.assertLessEqual(equity, 1.0)
                        answer = oracle(facts, legal)
                        self.assert_descriptor_in(
                            legal, answer, "JOIN-AGT-14.8 the oracle"
                        )
                        if equity >= odds:
                            self.assertFalse(
                                J.same_descriptor(answer, "fold"),
                                "the oracle folded at or above the pot odds %r it was "
                                "handed %r on %r (docs/L2/agents/baselines.md §3, ASM-4): "
                                "%r" % (odds, equity, name, answer),
                            )
                            if "fold" in list(legal):
                                call_side += 1
                        elif "fold" in list(legal):
                            self.assertTrue(
                                J.same_descriptor(answer, "fold"),
                                "the oracle did not fold below the pot odds %r it was handed "
                                "%r on %r (docs/L2/agents/baselines.md §3, ASM-4): %r"
                                % (odds, equity, name, answer),
                            )
                            fold_side += 1
        self.assertGreaterEqual(
            decisions,
            len(names),
            "the walks reach at least one decision per declared shape, so the six baselines "
            "are asserted over real hands of every row: %d decisions" % (decisions,),
        )
        self.assertGreaterEqual(
            call_side + fold_side,
            len(names),
            "fewer than one decision per declared shape was decisive for the oracle's "
            "inequality, so the case does not say what the oracle decides on every row "
            "(ASM-4): %r call-side and %r fold-side across %r decisions"
            % (call_side, fold_side, decisions),
        )


if __name__ == "__main__":
    unittest.main()
