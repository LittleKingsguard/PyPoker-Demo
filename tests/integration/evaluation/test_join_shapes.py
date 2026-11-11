"""JOIN-EVL-15 — the declared game shapes at the join (D-29, D-33).

`docs/L2/evaluation/surface.md` §2 and §5-§13, `docs/L2/evaluation/seats.md` §1-§4,
`docs/L3/evaluation/shape.md` §1-§5, `docs/L3/evaluation/scheduler.md` §1, §5-§5.1 and
`docs/L3/evaluation/pool.md` §1-§2, with `docs/L1/shapes.md` §2-§6, `docs/L1/seats.md`
§2, §4-§5, `docs/L1/league.md` §2, §4, `docs/L1/sizing.md` §4, §6 and
`docs/L1/records.md` §7, §8 — D-29, D-33, ASM-27, ASM-40, ASM-43.

The shape is declared in one place and **restated** in another. `engine.game_shapes()`
publishes the three rows, default first; `evaluation` holds no arrow to that catalogue
(`module-map.md` §2, D-13) and restates the three **names** in `declarations.py`, which is
why `shape.md` §1 makes holding that restatement equal the **join** battery's duty —
nothing the unit battery can see.  The seat count is on the same terms and in the other
direction: `seat_count` reads it off `engine.game_config` and `PAIRWISE_SEATS` is the
instrument's arity, which `JOIN-EVL-15.5` holds to the engine's own numbers and to the
boundary the folder's rule makes on each shape's declared stack (`seats.md` §1, §3, §4,
`docs/L1/seats.md` §5, D-13, D-33). In the other direction the shape is a fact about a
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
import itertools
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

#: The three declared shapes, by the names the engine's catalogue publishes, default
#: first (`docs/L1/shapes.md` §2, `docs/L1/seats.md` §2, D-29, D-33).  The battery reads the
#: catalogue and never copies it: the names below are only what the cases spell when they
#: must hand a shape to a call.
FIXED_LIMIT = "fixed-limit-20"
NO_LIMIT = "no-limit-100"
SIX_SEAT = "six-seat-no-limit-100"

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
        """JOIN-EVL-15.1 `evaluation`'s `SHAPE_NAMES` is `tuple(engine.game_shapes())` -- the catalogue's three rows -- in that order and default first, its `DEFAULT_SHAPE` is that catalogue's first row's name, and its `EXPLORATION_MODES` are exactly the modes `agents.as_policy` accepts — both named in the refusal of a third (`shape.md` §1, §5, `docs/L1/shapes.md` §2-§3, `sizing.md` §4, D-29)."""
        catalogue = J.game_shapes()
        names = tuple(str(name) for name in catalogue)
        self.assertEqual(
            names,
            (FIXED_LIMIT, NO_LIMIT, SIX_SEAT),
            "engine.game_shapes() publishes the three declared shapes, default first "
            "(docs/L1/shapes.md §2, docs/L1/seats.md §2, engine/surface.md §12, D-33): %r"
            % (names,),
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


class SeatCountInstrument(J.JoinCase):
    """The seat count and the instrument's arity, held to the engine and to a real draw."""

    def class_refusal(self, kind, entry, groups, call, note=""):
        """Require the refusal class `kind`, naming the entry point and every group.

        `docs/L2/evaluation/seats.md` §3 declares **one** class for the one contract -- a
        cell is a pair and a placement is not -- and §2 one for a draw above the membership,
        so this join asserts each class by name as well as the message, where
        `assert_refusal` tolerates the class (`errors.md` §2's closing rule, `seats.md`
        §2-§3, §5, D-33).
        """
        try:
            result = call()
        except Exception as exc:  # noqa: BLE001 - the class is the contract here
            self.assertEqual(
                type(exc).__name__,
                kind,
                "%s: the refusal of this contract is %s, and it arrived as %s: %r "
                "(errors.md §2, seats.md §2-§3, §5, D-33)"
                % (note or entry, kind, type(exc).__name__, exc),
            )
            message = str(exc)
        else:
            self.fail(
                "%s: %s must refuse this call, but it returned %r"
                % (note or entry, entry, result)
            )
        lowered = message.lower()
        self.assertIn(
            entry.lower(),
            lowered,
            "%s: the refusal must name the entry point %r; the message was %r "
            "(errors.md §3, seats.md §3)" % (note or entry, entry, message),
        )
        for group in groups:
            alternatives = (group,) if isinstance(group, str) else tuple(group)
            if not any(str(alternative).lower() in lowered for alternative in alternatives):
                self.fail(
                    "%s: the refusal must name one of %r; the message was %r "
                    "(errors.md §3, seats.md §3, §5)" % (note or entry, alternatives, message)
                )
        return message

    def seat_refusal(self, entry, groups, call, note=""):
        """Require `SeatCountExceeded` -- the one class a shape above the arity meets."""
        return self.class_refusal("SeatCountExceeded", entry, groups, call, note)

    def folders(self):
        """The catalogue's three folders, in `agents.baselines()`'s order (`D-21`).

        The names beyond the pinned anchors: with them a six-seat pool holds the six
        members `docs/L1/seats.md` §2, §4 declares (`records.md` §8, ASM-32, D-21).
        """
        anchors = tuple(str(name) for name in J.protocol()["baselines"])
        return tuple(str(name) for name in J.baselines() if name not in anchors)

    def six_seat_pool(self):
        """One real frozen six-seat pool, built through `evaluation.build_pool` and cached.

        Its declaration names the shape -- so the pool's baselines are constructed for it
        and never for the default -- and admits the three folders beside the three pinned
        anchors, which is the six-member composition a six-seat hand seats
        (`docs/L2/evaluation/seats.md` §4, `docs/L1/seats.md` §2, §4, ASM-31, D-33).
        """
        if "six_seat_pool" not in _CACHE:
            declaration = {
                "members": [],
                "m": J.league()["m"],
                "frozen": True,
                "game": SIX_SEAT,
                "baselines": list(self.folders()),
            }
            _CACHE["six_seat_pool"] = J.build_pool(declaration)
        return _CACHE["six_seat_pool"]

    def six_seat_table(self):
        """``(matrix, rating, record)``: a hand-built six-seat table and its report inputs.

        The cells are `records.md` §9's, the record `records.md` §10's, and the shape is
        named on the record **and** on every cell, so the table's one shape resolves to the
        six-seat row before the seat count is read (`rating.md` §1, §6, `report.md` §2,
        `seats.md` §3, §5).  The rating is data: `report` refuses this table in its own
        table checks, before it compares a rating with anything (`report.md` §3, D-33).
        """
        if "six_seat_table" not in _CACHE:
            members = [str(name) for name in J.protocol()["baselines"]] + list(
                self.folders()
            )
            pairs = list(itertools.combinations(range(len(members)), 2))
            table = J.hand_matrix(
                members,
                [(3, 2, J.HANDS_SEVEN - 5)] * len(pairs),
                J.HANDS_SEVEN,
                J.HAND_BUILT_TABLE_SEED,
            )
            table = dict(
                table,
                game=SIX_SEAT,
                cells=[dict(cell, game=SIX_SEAT) for cell in table["cells"]],
            )
            rating = {
                "values": {
                    name: {
                        "value": 0.0,
                        "interval": (-0.5, 0.5),
                        "hands": J.HANDS_SEVEN * (len(members) - 1),
                        "bounded": False,
                    }
                    for name in members
                },
                "method": "Bradley-Terry",
                "anchor": "the three baselines' mean fixed at 0",
                "bound_applied": False,
                "bootstrap_seed": J.bootstrap_seed(table["table_seed"]),
                "converged": True,
                "hands_per_cell": J.HANDS_SEVEN,
                "members": members,
                "table_seed": J.HAND_BUILT_TABLE_SEED,
                "table": "live",
            }
            _CACHE["six_seat_table"] = (
                table,
                rating,
                J.run_record(table, rating),
            )
        return _CACHE["six_seat_table"]

    def test_join_evl_15_5_the_seat_count_is_the_engine_s_and_the_pairwise_instrument_is_two(self):
        """JOIN-EVL-15.5 for every name `engine.game_shapes()` publishes, `declarations.seat_count(name)` is `engine.game_config(name)["seats"]` and `PAIRWISE_SEATS` is the default shape's own seat count; a six-seat pool's drawn `fold-large-bet` answers the boundary **that** shape's declared stack makes while the default-shape build answers the default's; and `match`, `matrix`, `rating` and `report` refuse the six-seat shape as `SeatCountExceeded` naming it and its seats (`seats.md` §1, §3, §4, `docs/L1/seats.md` §2-§5, `league.md` §4, D-13, D-22, D-33)."""
        catalogue = J.game_shapes()
        names = tuple(str(name) for name in catalogue)
        self.assertEqual(
            names,
            (FIXED_LIMIT, NO_LIMIT, SIX_SEAT),
            "the engine publishes the three rows this join holds the restatement to, "
            "default first (docs/L1/shapes.md §2, docs/L1/seats.md §2, engine/surface.md "
            "§12, D-33): %r" % (names,),
        )
        read_seats = J.declared_constant("evaluation.declarations", "seat_count")
        for name in names:
            with self.subTest(shape=name):
                self.assertEqual(
                    int(read_seats(name)),
                    int(J.game_config(name)["seats"]),
                    "seat_count(%r) is engine.game_config(%r)['seats'], the module's one "
                    "source of a seat count (seats.md §1, §3, docs/L1/module-map.md §2, "
                    "D-13, D-33): %r vs %r"
                    % (name, name, read_seats(name), int(J.game_config(name)["seats"])),
                )
        pairwise = int(
            J.declared_constant("evaluation.declarations", "PAIRWISE_SEATS")
        )
        self.assertEqual(
            pairwise,
            int(J.game_config()["seats"]),
            "PAIRWISE_SEATS is the instrument's arity, and the default shape's own seat "
            "count is what a pair is -- read off an absent shape, which is the default "
            "(seats.md §1, §3, docs/L1/seats.md §2, D-13, D-33): %r vs %r"
            % (pairwise, int(J.game_config()["seats"])),
        )
        self.assertLess(
            int(J.game_config(FIXED_LIMIT)["seats"]),
            int(J.game_config(SIX_SEAT)["seats"]),
            "the third row is the one above the instrument's arity, so a cell is no longer "
            "a hand's whole seating (seats.md §1, §3, docs/L1/seats.md §5, D-33): %r vs %r"
            % (
                int(J.game_config(FIXED_LIMIT)["seats"]),
                int(J.game_config(SIX_SEAT)["seats"]),
            ),
        )

        # The pool's baselines on the pool's own shape: a real six-seat readout, its
        # declared stack, and the one boundary the folder's rule makes (`seats.md` §4,
        # `folders.md` §2, ASM-31, D-33).
        pool = self.six_seat_pool()
        record = J.pool_members(pool)
        ids = [str(member["id"]) for member in record["members"]]
        self.assertEqual(
            str(record["game"]),
            SIX_SEAT,
            "the pool reads back on the shape it was declared on (pool.md §5, shape.md §4, "
            "seats.md §4, D-33): %r" % (record["game"],),
        )
        self.assertEqual(
            len(ids),
            len(names) + len(self.folders()),
            "the six-seat pool holds the three anchors and the three folders "
            "(records.md §8, docs/L1/seats.md §2, §4, ASM-32, D-21): %r" % (ids,),
        )
        folder_position = ids.index(self.folders()[-1])
        seed = folder_position
        self.assertEqual(
            seed % len(ids),
            folder_position,
            "a seed congruent to the folder's position draws it, because the draw is "
            "seed %% n (scheduler.md §3, pool.md §7, ASM-43): %r" % (seed,),
        )
        hand = J.new_hand(J.MATCH_SEED, SIX_SEAT)
        readout = J.readout(hand)
        legal = tuple(J.legal_actions(hand))
        drawn = J.mod("evaluation").opponent(pool, seed)
        default_build = J.mod("agents").build_baseline(self.folders()[-1], seed)
        six_stack = int(J.game_config(SIX_SEAT)["starting_stack"])
        default_stack = int(J.game_config()["starting_stack"])
        self.assertGreater(
            six_stack,
            default_stack,
            "the six-seat row's declared stack is the deeper one, which is what moves the "
            "folder's boundary (docs/L1/seats.md §2, folders.md §2, ASM-31, D-33): %r vs %r"
            % (six_stack, default_stack),
        )
        for to_call in (10, 11, 50, 51):
            copy = dict(readout, to_call=to_call)
            with self.subTest(to_call=to_call):
                self.assertEqual(
                    drawn(copy, legal),
                    "fold" if 2 * to_call > six_stack else "check-call",
                    "the drawn folder folds exactly where 2 x to_call exceeds the "
                    "six-seat row's declared stack of %d and calls where it does not, so "
                    "its boundary is 51 and not 11 (seats.md §4, docs/L1/seats.md §2, §4, "
                    "folders.md §2, ASM-31, D-33): to_call %d" % (six_stack, to_call),
                )
                self.assertEqual(
                    default_build(copy, legal),
                    "fold" if 2 * to_call > default_stack else "check-call",
                    "while the default-shape build answers the default row's boundary on "
                    "its %d chips -- one rule, each shape's own stack (seats.md §4, "
                    "folders.md §2, ASM-31, D-33): to_call %d"
                    % (default_stack, to_call),
                )
        self.assertNotEqual(
            drawn(dict(readout, to_call=11), legal),
            default_build(dict(readout, to_call=11), legal),
            "11 is a call on a hundred chips and a fold on twenty, so a pool whose "
            "baselines were built for the wrong shape is red here (seats.md §4, "
            "docs/L1/seats.md §2, ASM-31, D-33)",
        )

        # The four refusals: one contract, one class, the shape and its seat count named
        # (seats.md §3, §5, docs/L1/seats.md §5, league.md §4, D-22, D-33).
        seats = str(int(J.game_config(SIX_SEAT)["seats"]))
        groups = ((SIX_SEAT,), (seats,))

        def six_seat_side(readout_record, legal_actions):
            """An opaque callable whose own `game` names the six-seat shape (`shape.md` §4)."""
            return legal_actions[0]

        six_seat_side.game = SIX_SEAT
        self.seat_refusal(
            "match",
            groups,
            lambda: J.mod("evaluation").match(
                six_seat_side, J.caller, J.HANDS_TWO, J.MATCH_SEED
            ),
            "a two-hand cell of a six-seat side beside a plain one",
        )
        self.seat_refusal(
            "matrix",
            groups,
            lambda: J.mod("evaluation").matrix(pool, [J.caller], "live"),
            "a table over the six-seat pool",
        )
        table, fitted, run = self.six_seat_table()
        self.seat_refusal(
            "rating",
            groups,
            lambda: J.rating(table),
            "a complete hand-built six-seat table",
        )
        self.seat_refusal(
            "report",
            groups,
            lambda: J.report(J.RUNG, run, table, fitted),
            "a report of that table",
        )

        # ... and the counted draw over that same real frozen pool: five distinct members
        # of the six it holds, two calls at one seed agreeing answer for answer, and a draw
        # above the membership refused naming **both** counts (`seats.md` §2, §4,
        # `docs/L1/seats.md` §4, `league.md` §2, ASM-2, ASM-43).
        order = J.draw_order(seed, len(ids))
        self.assertEqual(
            sorted(order),
            list(range(len(ids))),
            "the draw's order is a permutation of the pool's six positions, so no member "
            "is seated twice (seats.md §2, league.md §2, ASM-43): %r" % (order,),
        )
        counted = J.mod("evaluation").opponent(pool, seed, len(ids) - 1)
        again = J.mod("evaluation").opponent(pool, seed, len(ids) - 1)
        self.assertEqual(
            len(counted),
            len(ids) - 1,
            "a six-seat pool seats five opponents, which is a draw of five of its six "
            "members (docs/L1/seats.md §4, seats.md §2, ASM-43): %r" % (counted,),
        )
        batch = (
            (readout, legal),
            (dict(readout, to_call=six_stack), legal),
        )
        for position, (facts, actions) in enumerate(batch):
            with self.subTest(decision=position):
                self.assertEqual(
                    tuple(str(again[seat](facts, actions)) for seat in range(len(counted))),
                    tuple(str(counted[seat](facts, actions)) for seat in range(len(counted))),
                    "two calls at one seed over one pool draw one tuple, answer for answer, "
                    "and every answer is one of the decision's own legal descriptors "
                    "(seats.md §2, §4, ASM-2, ASM-43)",
                )
                self.assertEqual(
                    tuple(
                        str(counted[seat](facts, actions)) in tuple(str(a) for a in actions)
                        for seat in range(len(counted))
                    ),
                    (True,) * len(counted),
                    "each drawn seat answers inside legal_actions on a real six-seat "
                    "decision, so the five seats are policies of that shape "
                    "(surface.md §2, seats.md §4, D-2): %r" % (actions,),
                )
        self.class_refusal(
            "DrawExceedsMembership",
            "opponent",
            ((str(len(ids) + 1),), (str(len(ids)),)),
            lambda: J.mod("evaluation").opponent(pool, seed, len(ids) + 1),
            "a draw of seven from a six-member pool",
        )


if __name__ == "__main__":
    unittest.main()
