"""JOIN-EVL-15 — the second declared game shape at the join (D-29).

`docs/L2/evaluation/surface.md` §2 and §5-§13, `docs/L3/evaluation/shape.md` §1-§5,
`docs/L3/evaluation/scheduler.md` §1, §5-§5.1 and `docs/L3/evaluation/pool.md` §1-§2,
with `docs/L1/shapes.md` §2-§6, `docs/L1/sizing.md` §4, §6 and `docs/L1/records.md` §7,
§8 — D-29, ASM-27, ASM-40.

The shape is declared in one place and **restated** in another. `engine.game_shapes()`
publishes the two rows, default first; `evaluation` holds no arrow to that catalogue
(`module-map.md` §2, D-13) and restates the two **names** in `declarations.py`, which is
why `shape.md` §1 makes holding that restatement equal the **join** battery's duty —
nothing the unit battery can see. In the other direction the shape is a fact about a
file: a learner of a non-default shape writes a **version-4** container carrying
`game`, and `evaluation.policy_from` reads it with the encoder built **for that shape**
and decodes its descriptor in that shape's vocabulary (`shape.md` §2, §4-§5,
`scheduler.md` §5.1, `docs/L1/shapes.md` §5, `docs/L1/sizing.md` §6).

So this file joins the four things no single battery can: the restated catalogue and the
engine's; a real second-shape checkpoint reaching `policy_from` and deciding in the
six-index vocabulary; `policy_from`'s exploration mode and the one `agents.as_policy`
declares; and the cell whose sides name a shape.  Every learner, encoder, checkpoint and
decision here is built through a declared entry point of the module that owns it, and
the one constant compared is the restatement `shape.md` §1 names.

`JOIN-EVL-15.4` asserts the deal those declarations reach: a `match` whose sides name one
shape is **played on that shape**.  The baseline beside a version names none -- a baseline
is shape-silent (`shape.md` §4) -- and the version names `no-limit-100`, so the cell is
dealt `no-limit-100` hands, its own `game` says so, every hand of it is played to an
outcome in both directions at the cell's seat split, and the two policies at its seats
decide over the readouts those hands reach: the version returns only descriptors of that
shape's six-index vocabulary and the shape-silent baseline only descriptors that deal
makes legal.  The same pairing against a version whose container names no second shape
reports the **default**, so a deal that defaulted the cell's shape again is red here
rather than silently accepted -- `engine` reads the default's own name exactly as an
absent one, which is why that mistake moves no other number in any battery
(`scheduler.md` §1, §5, `surface.md` §9, `shape.md` §3-§4, `guardrails.md` G36, ASM-6,
D-29).
"""

import importlib.util
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
# The support module is loaded under a private name: this repository's integration
# batteries share the file name `_join_support.py`, so a plain import would hand one
# battery another's helpers when two test directories are collected in one process.
if "evaluation_join_support" in sys.modules:
    J = sys.modules["evaluation_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "evaluation_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["evaluation_join_support"] = J
    _spec.loader.exec_module(J)

#: The second declared shape, by the name the engine's catalogue publishes second
#: (`docs/L1/shapes.md` §2, D-29).  The battery reads the catalogue and never copies it:
#: the name below is only what the cases spell when they must hand a shape to a call.
NO_LIMIT = "no-limit-100"
FIXED_LIMIT = "fixed-limit-20"

#: The invented facts of this file's second-shape checkpoint: its learner seed, the hand
#: seeds its decisions are read off, and the seed an `off` policy is built at beside the
#: recorded one (`docs/L1/battery.md` §4, D-15).
NO_LIMIT_SEED = J.CHECKPOINT_SEED_E
OTHER_SEED = J.CHECKPOINT_SEED_F
NO_LIMIT_HAND_SEEDS = (J.HAND_BUILT_TABLE_SEED, J.MATCH_SEED_OTHER)

_CACHE = {}


def station(readout_record, legal):
    """A caller-side policy that never folds while calling is legal, else folds.

    Both descriptors are declared in **both** shapes' vocabularies, so one driver plays a
    hand of either shape and the decisions it reaches are the shape's own
    (`docs/L2/engine/surface.md` §6, `docs/L2/features/surface.md` §9).
    """
    for wanted in ("check-call", "fold"):
        if wanted in legal:
            return wanted
    return legal[0]


def no_limit_checkpoint():
    """One real `no-limit-100` checkpoint: `agents.build_learner` then `agents.save`.

    The encoder is built **for the recorded shape** and the learner is built on it, so
    the container is a version-4 one carrying `game` — the fact `policy_from` reads and
    the shape whose vocabulary it decodes in (`features/surface.md` §3-§5,
    `docs/L1/sizing.md` §6, `shape.md` §4-§5, ASM-40).  It is written under the battery's
    scratch root — an absolute path under the platform's temporary area — and built once.
    """
    if "no_limit" not in _CACHE:
        encoder = J.build_encoder(J.encoding_for(J.DEFAULT_KIND), shape=NO_LIMIT)
        learner = J.build_learner(
            {
                "backend": "numpy",
                "architecture": {
                    "kind": J.DEFAULT_KIND,
                    "width": J.WIDTH_A,
                    "depth": J.DEPTH_A,
                },
                "seed": NO_LIMIT_SEED,
                "encoder": encoder,
                "game": NO_LIMIT,
            }
        )
        path = J.save(
            learner, os.path.join(J.scratch_root(), "evaluation-join-no-limit.ckpt")
        )
        _CACHE["no_limit"] = {
            "path": path,
            "learner": learner,
            "encoder": encoder,
            "encoding": J.encoding_for(J.DEFAULT_KIND),
            "seed": NO_LIMIT_SEED,
            "params": J.param_count(learner),
        }
    return _CACHE["no_limit"]


def no_limit_decisions(limit=20):
    """Real `no-limit-100` decisions: the readout, its legal descriptors and the mask."""
    rows = []
    for seed in NO_LIMIT_HAND_SEEDS:
        for facts, legal in J.decisions_of(seed, station, shape=NO_LIMIT):
            rows.append((facts, legal, tuple(J.legal_indices(legal))))
            if len(rows) >= limit:
                return rows
    return rows


def fixed_limit_decisions(limit=12):
    """Real default-shape decisions, for comparing two exploration modes."""
    rows = []
    for seed in (J.MATCH_SEED, J.MATCH_SEED_OTHER):
        for facts, legal in J.decisions_of(seed, station):
            rows.append((facts, legal))
            if len(rows) >= limit:
                return rows
    return rows


def answers_of(policy, decisions):
    """One policy's answers to a fixed list of decisions, as descriptors."""
    return tuple(policy(facts, legal) for facts, legal in decisions)


class RestatedCatalogue(J.JoinCase):
    """The two constants `declarations.py` restates, held equal to the modules that own them."""

    def test_join_evl_15_1_the_restated_catalogue_is_the_engine_s(self):
        """JOIN-EVL-15.1 `evaluation`'s `SHAPE_NAMES` is `tuple(engine.game_shapes())`, in that order and default first, its `DEFAULT_SHAPE` is that catalogue's first row's name, and its `EXPLORATION_MODES` are exactly the modes `agents.as_policy` accepts — both named in the refusal of a third (`shape.md` §1, §5, `docs/L1/shapes.md` §2-§3, `sizing.md` §4, D-29)."""
        catalogue = J.game_shapes()
        names = tuple(str(name) for name in catalogue)
        self.assertEqual(
            names,
            (FIXED_LIMIT, NO_LIMIT),
            "engine.game_shapes() publishes the two declared shapes, default first "
            "(docs/L1/shapes.md §2, engine/surface.md §12): %r" % (names,),
        )
        self.assertTrue(
            bool(catalogue[names[0]].get("default")),
            "the catalogue's first row is the declared default, which is what makes an "
            "absent `game` readable as it (docs/L1/shapes.md §3): %r"
            % (catalogue[names[0]],),
        )
        declared = J.declared_constant("evaluation.declarations", "SHAPE_NAMES")
        self.assertEqual(
            tuple(str(name) for name in declared),
            names,
            "evaluation restates the catalogue's names in the catalogue's order, and "
            "shape.md §1 makes holding them equal this battery's duty -- a restatement "
            "that drifts is a red join case and never a silent second catalogue "
            "(shape.md §1, D-13, D-29): %r vs %r" % (tuple(declared), names),
        )
        self.assertEqual(
            str(J.declared_constant("evaluation.declarations", "DEFAULT_SHAPE")),
            names[0],
            "the edge's default shape is the catalogue's first row's name, which is what "
            "an absent `game` reads as everywhere (shape.md §2, docs/L1/shapes.md §3): "
            "%r vs %r"
            % (
                J.declared_constant("evaluation.declarations", "DEFAULT_SHAPE"),
                names[0],
            ),
        )
        modes = tuple(
            str(mode)
            for mode in J.declared_constant("evaluation.declarations", "EXPLORATION_MODES")
        )
        self.assertEqual(
            modes,
            ("schedule", "off"),
            "evaluation declares the two exploration modes, the default first "
            "(shape.md §5, sizing.md §4): %r" % (modes,),
        )
        self.assertEqual(
            str(J.declared_constant("evaluation.declarations", "EXPLORATION_DEFAULT")),
            modes[0],
            "the declared default mode is the first, so naming none is today's "
            "behaviour (shape.md §5, declarations.md §1): %r" % (modes[0],),
        )
        info = J.checkpoint(J.CHECKPOINT_A, J.CHECKPOINT_SEED)
        for mode in modes:
            with self.subTest(accepted=mode):
                # Each declared mode is one `agents.as_policy` accepts: the restatement is
                # of the module that declares the modes and not of a third list
                # (shape.md §5, docs/L3/agents/rule.md §6).
                policy = J.as_policy(info["learner"], info["encoder"], info["seed"], mode)
                self.assertTrue(
                    callable(policy),
                    "agents.as_policy accepts the declared mode %r (agents/surface.md "
                    "§9-§10, shape.md §5)" % (mode,),
                )
        with self.subTest(case="a third mode is refused by both, naming both"):
            for entry, call in (
                (
                    "as_policy",
                    lambda: J.as_policy(
                        info["learner"], info["encoder"], info["seed"], "greedy"
                    ),
                ),
                (
                    "policy_from",
                    lambda: J.policy_from(info["path"], "greedy"),
                ),
            ):
                with self.subTest(entry=entry):
                    message = self.assert_refusal(
                        entry,
                        [("schedule",), ("off",), ("greedy",)],
                        call,
                        "a mode neither module declares",
                    )
                    self.assertIn(
                        "mode",
                        message.lower(),
                        "the refusal names the field at fault, so the two module's "
                        "contracts are one contract (errors.md §3, shape.md §5): %r"
                        % (message,),
                    )


class SecondShapeCheckpoint(J.JoinCase):
    """A version-4 container, its shape, and the vocabulary its descriptor decodes in."""

    def test_join_evl_15_2_a_no_limit_checkpoint_round_trips_through_policy_from(self):
        """JOIN-EVL-15.2 `policy_from` of a real `no-limit-100` checkpoint carries `game == 'no-limit-100'`, decodes every decision in the six-index vocabulary — never the default shape's `raise` — and reports the same rule and utility `agents.as_policy` of the restored container does (`shape.md` §2, §4-§5, `scheduler.md` §5.1, `docs/L1/shapes.md` §5, `records.md` §7, D-29)."""
        info = no_limit_checkpoint()
        self.assertTrue(
            os.path.isfile(info["path"]),
            "the case reads a checkpoint agents.save wrote at an absolute path under the "
            "platform's temporary area (protocol.md §5): %r" % (info["path"],),
        )
        member = J.policy_from(info["path"])
        self.assertEqual(
            str(getattr(member, "game", None)),
            NO_LIMIT,
            "a policy built from a second-shape container carries the shape its container "
            "records, which is the vocabulary it decodes its descriptor in "
            "(surface.md §2, §12, shape.md §4, D-29): %r"
            % (getattr(member, "game", None),),
        )
        restored = J.load(None, info["path"])
        self.assertEqual(
            str(getattr(restored, "game", None)),
            NO_LIMIT,
            "the format-4 container is what carries the shape, and the learner restored "
            "from it is a second-shape learner — the fact the reader proves by existing "
            "(docs/L1/shapes.md §5, docs/L1/sizing.md §6, ASM-40): %r"
            % (getattr(restored, "game", None),),
        )
        expected = J.as_policy(
            restored,
            J.build_encoder(info["encoding"], shape=NO_LIMIT),
            info["seed"],
        )
        for fact in ("learning_rule", "utility", "game"):
            with self.subTest(fact=fact):
                self.assertEqual(
                    getattr(member, fact, None),
                    getattr(expected, fact, None),
                    "policy_from reports the %r the policy agents.as_policy builds "
                    "carries, because playback is rule-, utility- and shape-free and the "
                    "file is the only witness (rules.md §6, utilities.md §6, shape.md "
                    "§4, ASM-20): %r vs %r"
                    % (
                        fact,
                        getattr(member, fact, None),
                        getattr(expected, fact, None),
                    ),
                )
        self.assertEqual(
            int(member.params),
            int(info["params"]),
            "the side's capacity is agents.param_count of the restored learner, which "
            "the second shape's head width sets (surface.md §2, ASM-10, ASM-40): %r vs %r"
            % (member.params, info["params"]),
        )
        six = tuple(str(name) for name in J.game_shapes()[NO_LIMIT]["actions"])
        self.assertEqual(
            six,
            (
                "fold",
                "check-call",
                "raise-quarter",
                "raise-half",
                "raise-all-in",
                "raise-minimum",
            ),
            "the engine declares six descriptors for the second shape, in the shape's own "
            "order and deliberately not monotone in amount (docs/L1/sizing.md §3, "
            "engine/surface.md §3): %r" % (six,),
        )
        rows = no_limit_decisions()
        self.assertGreaterEqual(
            len(rows),
            6,
            "the batch reaches at least six real decisions of the second shape "
            "(engine/surface.md §4-§6): %r" % (len(rows),),
        )
        indices = []
        for position, (facts, legal, mask) in enumerate(rows):
            chosen = member(facts, legal)
            with self.subTest(decision=position):
                self.assert_descriptor_in(
                    legal, chosen, "policy_from of a no-limit checkpoint"
                )
                index = J.descriptor_index(legal, chosen)
                indices.append(index)
                self.assertEqual(
                    J.decode_action(index, shape=NO_LIMIT),
                    chosen,
                    "the descriptor is the one the **second** shape's vocabulary makes "
                    "from that index, so the reader decoded the index in the shape its "
                    "container records (features/surface.md §9, shape.md §4, D-29): %r"
                    % (chosen,),
                )
                self.assertIn(
                    index,
                    set(mask),
                    "the answer is one of the decision's legal indices, in the second "
                    "shape's index space (features/surface.md §8, D-2): %r against %r"
                    % (index, mask),
                )
                self.assertNotEqual(
                    chosen,
                    J.decode_action(2),
                    "no decision is the default shape's `raise`: an index decoded in the "
                    "three-index vocabulary cannot be applied on a no-limit hand, which "
                    "is what makes this the proof of the reader (shape.md §4, "
                    "docs/L1/sizing.md §4, ASM-37): %r" % (chosen,),
                )
        self.assertTrue(
            [index for index in indices if index >= 3],
            "at least one decision sits at an index the default vocabulary does not have "
            "(3, 4 or 5), so the batch reaches the descriptors only the second shape "
            "declares (features/surface.md §9, shape.md §4): %r" % (indices,),
        )
        self.assertLessEqual(
            max(indices),
            len(six) - 1,
            "and no index lies past the six the shape declares, so the index space is "
            "that shape's alone (shape.md §3-§4, ASM-40): %r" % (indices,),
        )


class ExplorationMode(J.JoinCase):
    """`policy_from`'s second argument held to the module that declares the modes."""

    def test_join_evl_15_3_the_off_mode_is_agents_as_policy_s(self):
        """JOIN-EVL-15.3 `policy_from(path, "off")` and `agents.as_policy(agents.load(None, path), encoder, another_seed, "off")` decide identically on the same readouts, both differ from what either decides under `"schedule"` on at least one readout, and `policy_from(path)` is `agents.as_policy(..., "schedule")` at the recorded seed (`shape.md` §5, `scheduler.md` §5.1, §7, `surface.md` §12, `sizing.md` §4, guardrails.md G34, D-29)."""
        info = J.checkpoint(J.CHECKPOINT_B, J.CHECKPOINT_SEED_B)
        decisions = fixed_limit_decisions()
        self.assertGreaterEqual(
            len(decisions),
            6,
            "the comparison covers real decisions of the shared checkpoint's shape "
            "(engine/surface.md §4-§6): %r" % (len(decisions),),
        )
        greedy = J.policy_from(info["path"], "off")
        scheduled = J.policy_from(info["path"])
        loaded = J.load(None, info["path"])
        agents_greedy = J.as_policy(loaded, info["encoder"], OTHER_SEED, "off")
        agents_scheduled = J.as_policy(loaded, info["encoder"], info["seed"], "schedule")
        off_answers = answers_of(greedy, decisions)
        agents_off_answers = answers_of(agents_greedy, decisions)
        schedule_answers = answers_of(scheduled, decisions)
        agents_schedule_answers = answers_of(agents_scheduled, decisions)
        for position, ((facts, legal), chosen) in enumerate(zip(decisions, off_answers)):
            with self.subTest(decision=position):
                self.assert_descriptor_in(legal, chosen, "policy_from at `off`")
                self.assertEqual(
                    chosen,
                    agents_off_answers[position],
                    "at `off` two policies of one learner built at two seeds decide "
                    "identically, so the mode is agents.as_policy's own and no draw is "
                    "taken (shape.md §5, sizing.md §4, G34): %r vs %r"
                    % (chosen, agents_off_answers[position]),
                )
        self.assertEqual(
            off_answers,
            agents_off_answers,
            "the whole batch agrees, and not one decision of it by accident "
            "(shape.md §5, agents/surface.md §10, D-29)",
        )
        self.assertNotEqual(
            off_answers,
            schedule_answers,
            "the mode is doing something: `off` and `schedule` differ on at least one of "
            "these readouts, so a policy built with the schedule's keyed draw and called "
            "'greedy' is red (shape.md §5, sizing.md §4, G34): %r vs %r"
            % (off_answers, schedule_answers),
        )
        self.assertNotEqual(
            agents_off_answers,
            agents_schedule_answers,
            "the same difference is agents.as_policy's, which is the module whose modes "
            "evaluation restates (shape.md §5, agents/surface.md §9-§10): %r vs %r"
            % (agents_off_answers, agents_schedule_answers),
        )
        self.assertEqual(
            schedule_answers,
            agents_schedule_answers,
            "`policy_from(path)` is agents.as_policy of the restored container at the "
            "seed the checkpoint records, under the declared default mode -- today's "
            "behaviour, unchanged (surface.md §12, scheduler.md §5.1, shape.md §5, "
            "G20): %r vs %r" % (schedule_answers, agents_schedule_answers),
        )
        self.assertEqual(
            schedule_answers,
            answers_of(J.policy_from(info["path"], "schedule"), decisions),
            "naming the mode explicitly and naming none are one policy (shape.md §5, "
            "declarations.md §1)",
        )
        self.assert_stream_unchanged(
            lambda: answers_of(greedy, decisions),
            "an `off` policy's decisions",
        )


class CellOfAShape(J.JoinCase):
    """The cell whose sides name one shape: played on it, and accounted for hand by hand."""

    def test_join_evl_15_4_a_cell_against_a_no_limit_version_is_played_on_that_shape(self):
        """JOIN-EVL-15.4 a `match` pairing a shape-silent default-shape baseline with a `no-limit-100` version is played on `no-limit-100`: the cell's `game` says so, both directions account for every one of its hands at the cell's own seat split, the member decides only in the six-index vocabulary that deal makes legal and the shape-silent baseline opposite it only returns descriptors of that shape, while the same pairing against a version naming no second shape reports the default's `game` (`scheduler.md` §1, §5, `surface.md` §9, `shape.md` §3-§4, `features/surface.md` §8-§9, `guardrails.md` G36, ASM-6, D-29)."""
        package = J.mod("evaluation")
        info = no_limit_checkpoint()
        catalogue = J.game_shapes()
        names = tuple(str(name) for name in catalogue)
        default = names[0]
        six = tuple(str(name) for name in catalogue[NO_LIMIT]["actions"])
        default_actions = tuple(str(name) for name in catalogue[default]["actions"])
        baseline = str(J.protocol()["baselines"][0])
        member = {
            "id": J.VERSION_E,
            "lineage": J.START_LABEL,
            "rung": J.RUNG,
            "variant": J.VARIANT_LABEL,
            "seed": info["seed"],
            "step": J.STEP,
            "samples": J.SAMPLES,
            "path": info["path"],
            "rule": J.DEFAULT_RULE,
            "utility": J.DEFAULT_UTILITY,
            "game": NO_LIMIT,
        }
        cell = package.match(baseline, member, J.HANDS_DOZEN, J.MATCH_SEED)
        self.assertEqual(
            str(cell["game"]),
            NO_LIMIT,
            "the cell's shape is the one its two sides name, the baseline naming none and "
            "the version naming the second, and it is the shape every hand of the cell is "
            "dealt on (scheduler.md §1, §5, shape.md §3-§4, guardrails.md G36): %r"
            % (cell.get("game"),),
        )
        self.assertEqual(
            [str(name) for name in cell["members"]],
            [baseline, J.VERSION_E],
            "the cell pairs the two members it was handed, in argument order "
            "(scheduler.md §1, records.md §9): %r"
            % ([str(name) for name in cell["members"]],),
        )
        hands = int(cell["hands"])
        self.assertEqual(
            hands,
            J.HANDS_DOZEN,
            "the cell is played at the hand count it was given, the shape costing none of "
            "them (scheduler.md §1, §4): %r" % (cell.get("hands"),),
        )
        # Seats alternate hand by hand from the cell's first hand, so the two directions'
        # splits are each other's mirror and each sums to the hand count; a hand of a
        # second-shape cell is one hand of the cell like any other (scheduler.md §2, §4,
        # records.md §9).
        splits = ((hands + 1) // 2, hands // 2), (hands // 2, (hands + 1) // 2)
        for position, direction in enumerate(cell["directions"]):
            with self.subTest(member=str(cell["members"][position])):
                counts = J.counts_of(direction)
                self.assertEqual(
                    sum(int(value) for value in counts),
                    hands,
                    "a hand of a second-shape cell is played to an outcome like any "
                    "other, so one direction's wins, ties and losses are the cell's whole "
                    "hand count (records.md §9, league.md §2, scheduler.md §4): %r"
                    % (counts,),
                )
                split = J.seat_split_of(direction)
                self.assertEqual(
                    sum(split),
                    hands,
                    "every hand of the cell is played from one seat of the direction, so "
                    "its two seat counts are the cell's hand count "
                    "(records.md §9, scheduler.md §2, G10): %r" % (split,),
                )
                self.assertEqual(
                    split,
                    splits[position],
                    "the seats alternate hand by hand, so the two directions' splits are "
                    "each other's mirror whatever the shape's deal costs "
                    "(scheduler.md §2, §4, records.md §9): %r against %r"
                    % (split, splits[position]),
                )
        # The member's decisions over **the cell's own hands**.  Each of the cell's hand
        # seeds is dealt at the cell's shape -- `engine.new_hand(seed, shape)` is the
        # project's single seeding point -- and driven by this file's shape-silent
        # caller-side policy, so the readouts and the legal sets a decision is judged
        # against are the deal's own and not a hand of another shape's (scheduler.md §3,
        # engine/surface.md §4-§6, features/surface.md §8, shapes.md §4).
        driven = J.policy_from(info["path"])
        silent = J.build_baseline(baseline, J.MATCH_SEED)
        indices = []
        masks = []
        decisions = 0
        for index in range(hands):
            seed = J.hand_seed(J.MATCH_SEED, index)
            for facts, legal in J.decisions_of(seed, station, shape=NO_LIMIT):
                decisions += 1
                with self.subTest(hand=index, decision=decisions):
                    mask = tuple(J.legal_indices(legal))
                    masks.append(mask)
                    self.assertTrue(
                        mask,
                        "a decision of the cell's hands has a legal set "
                        "(engine/surface.md §5-§6): %r" % (legal,),
                    )
                    self.assertTrue(
                        all(0 <= int(value) < len(six) for value in mask),
                        "every legal index of the deal is one of the six the cell's shape "
                        "declares, so the hands were dealt on that shape and not on a "
                        "three-index one (features/surface.md §8-§9, shape.md §3-§4, "
                        "guardrails.md G36): %r against %r" % (mask, six),
                    )
                    chosen = driven(facts, legal)
                    self.assert_descriptor_in(
                        legal, chosen, "the no-limit member on the cell's own hands"
                    )
                    self.assertIn(
                        str(chosen),
                        six,
                        "the member answers in the six-index vocabulary its container "
                        "records, the one this cell is played on "
                        "(features/surface.md §9, shape.md §4, D-29): %r against %r"
                        % (chosen, six),
                    )
                    at = J.descriptor_index(legal, chosen)
                    indices.append(at)
                    self.assertEqual(
                        J.decode_action(at, shape=NO_LIMIT),
                        chosen,
                        "the descriptor is the one the **second** shape's vocabulary makes "
                        "from that index, so the member decoded the index in the shape the "
                        "cell is played on (features/surface.md §9, shape.md §4, "
                        "scheduler.md §5.1): %r" % (chosen,),
                    )
                    answer = silent(facts, legal)
                    self.assert_descriptor_in(
                        legal,
                        answer,
                        "the shape-silent baseline opposite a no-limit version",
                    )
                    self.assertIn(
                        str(answer),
                        six,
                        "a baseline names no shape and plays whatever shape the hands it "
                        "is dealt are on, so it returns a descriptor of that deal's "
                        "vocabulary and never one of another's "
                        "(surface.md §9, shape.md §4, D-29): %r against %r"
                        % (answer, six),
                    )
        self.assertGreaterEqual(
            decisions,
            6,
            "the cell's own hands reach at least six real decisions of the second shape "
            "(engine/surface.md §4-§6): %r" % (decisions,),
        )
        self.assertTrue(
            [mask for mask in masks if max(mask) >= len(default_actions)],
            "at least one decision of the cell's hands offers an index the default "
            "vocabulary does not have (%d-%d), so the deal itself is the second shape's "
            "and not a three-index hand the cell's `game` merely labels "
            "(engine/surface.md §5-§6, features/surface.md §8, guardrails.md G36): %r"
            % (len(default_actions), len(six) - 1, masks),
        )
        self.assertLessEqual(
            max(indices),
            len(six) - 1,
            "no decision of the member lies past the six indices the shape declares, so "
            "the index space is that shape's alone (shape.md §3-§4, ASM-40): %r"
            % (indices,),
        )
        self.assertTrue(
            [at for at in indices if at >= len(default_actions)],
            "at least one decision sits at an index the default vocabulary does not have "
            "(%d-%d), so a descriptor exists here that a hand dealt on the default shape "
            "could not legally carry: this is what makes the deal's shape observable at "
            "all (features/surface.md §9, shape.md §4, guardrails.md G36): %r"
            % (len(default_actions), len(six) - 1, indices),
        )
        # The same pairing on the default shape: the version's container names no second
        # shape, so the cell is the one this battery's other cases have always played and
        # its `game` is the catalogue's default.  Two hands are enough here -- the subject
        # is the shape the cell reports, not a census (scheduler.md §5, shape.md §2,
        # guardrails.md G36, ASM-6).
        on_default = package.match(
            baseline,
            J.version(J.VERSION_A, J.START_LABEL),
            J.HANDS_TWO,
            J.MATCH_SEED,
        )
        self.assertEqual(
            str(on_default["game"]),
            default,
            "a cell of two default-shape sides reports the **default's own name**, so the "
            "shape a cell is played on is resolved from its sides and never substituted "
            "for: `engine` reads that name exactly as an absent one, which is why only a "
            "second-shape cell can tell the two apart (shape.md §2, scheduler.md §5, "
            "ASM-6, D-29): %r against %r" % (on_default.get("game"), default),
        )


if __name__ == "__main__":
    unittest.main()
