"""JOIN-AGT-15 — the game shape in the checkpoint, and the containers the tree ships.

`docs/L2/agents/shapes.md` §5-§6, `docs/L3/agents/checkpoint.md` §2-§3, `docs/L3/
agents/shapes.md` §5, `docs/L1/sizing.md` §6, `docs/L1/shapes.md` §5, `docs/L1/
records.md` §7, `docs/L1/protocol.md` §5 — ASM-5, ASM-18, ASM-40, D-29.

The container answers the second declared shape with a **format version, not a
migration** (`shapes.md` §5, `sizing.md` §6): a learner of the default shape writes
version 3 and **no** `game` field, so a fixed-limit save's members are today's, and a
learner of any other declared shape writes version 4 with a `game` field naming it.  A
version-1, 2 or 3 file is read as the default shape and must not carry one, a version-4
container naming the default shape is refused, and a `load` spec naming a shape its
container contradicts is refused naming **both** (`checkpoint.md` §3, `shapes.md` §6).

The shape a container records is read here out of the container's own `metadata.json`
by the support's reader — no entry point reports it — and every save goes to this case's
scratch root, which is a `tempfile.mkdtemp` directory the case removes (`battery.md`
§5): nothing in this file writes under `checkpoints/`, and the shipped set is loaded
read-only and left with its `(size, mtime)` unmoved (ASM-5, ASM-18, ASM-40).
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

#: The version a **default**-shape save writes, and the one any other declared shape's
#: save writes: `docs/L3/agents/checkpoint.md` §3's table, read back from the support
#: rather than spelled twice (`shapes.md` §5, ASM-40).
DEFAULT_VERSION = J.DEFAULT_FORMAT_VERSION
GAME_VERSION = J.GAME_FORMAT_VERSION

class ShapeContainerRoundTrip(J.JoinCase):
    """A format-4 container: its shape, its head and its decisions surviving `load`."""

    def learned(self, name):
        """A learner on `name` that one real batch has moved, and that shape's encoder."""
        encoder = J.shaped_encoder(J.encoding_for("naive-stack"), name)
        learner = J.shaped_learner(
            "naive-stack",
            J.WIDTH_SHAPE,
            J.DEPTH_SHAPE,
            J.LEARNER_SEED_SHAPE,
            name,
        )
        episode = J.shaped_play_hand(
            J.DEAL_SHAPE_B, J.caller_in(name), J.caller_in(name), name
        )
        batch = J.seat_transitions(episode, 0, encoder)
        statistics = J.learn(learner, batch)
        self.assertEqual(
            J.transitions_consumed(statistics),
            len(batch),
            "the batch a real no-limit episode gives is the one learn consumed "
            "(docs/L2/agents/surface.md §7): %r" % (statistics,),
        )
        self.assertTrue(
            J.finite(J.td_error(statistics)),
            "the learning signal on the second shape is finite (docs/L2/agents/"
            "surface.md §7): %r" % (statistics,),
        )
        return encoder, learner

    def decisions(self, name):
        """Observations and masks from two real no-limit deals, driven by a caller."""
        held = []
        for seed in (J.DEAL_SHAPE_B, J.DEAL_SHAPE_C):
            held.extend(J.shaped_walk(seed, name, J.caller_in(name)))
        self.assertGreaterEqual(
            len(held),
            4,
            "the comparison must cover several decisions of two real no-limit hands "
            "(shapes.md §3): %d decisions" % (len(held),),
        )
        return held

    def test_join_agt_15_1_a_format_4_container_round_trips_its_shape(self):
        """JOIN-AGT-15.1 `save` writes a `no-limit-100` learner as format version 4 whose
        `metadata.json` names the shape immediately after `kind`; `load` reads it back —
        from the path alone, as `evaluation.policy_from` does — at the same `game`, the
        same `actions` and the same `param_count`, making the saved learner's decisions
        on real no-limit readouts (`docs/L2/agents/shapes.md` §5-§6, `docs/L3/agents/
        checkpoint.md` §2.1, §3, `docs/L1/records.md` §7, `docs/L1/protocol.md` §5,
        `sizing.md` §6, ASM-5, ASM-40, D-29).
        """
        names = J.shape_names()
        name = names[1]
        encoder, learner = self.learned(name)
        path = J.save(learner, self.checkpoint_path(J.CHECKPOINT_SHAPE_ALPHA))
        self.assertEqual(
            path,
            self.checkpoint_path(J.CHECKPOINT_SHAPE_ALPHA),
            "save returns the path it wrote, byte for byte, so a run record can name the "
            "artefact (docs/L2/agents/surface.md §8, checkpoint.md §2): %r" % (path,),
        )
        metadata = J.container_metadata(path)
        self.assertEqual(
            metadata.get("format_version"),
            GAME_VERSION,
            "a learner of any other declared shape writes format version 4, not a "
            "migration of today's (shapes.md §5, checkpoint.md §3, sizing.md §6, "
            "ASM-40): %r" % (metadata.get("format_version"),),
        )
        self.assertEqual(
            metadata.get("game"),
            name,
            "the container names the shape it was written on -- the identity a member, a "
            "run and a table read (shapes.md §1, §5, checkpoint.md §2.1, D-29): %r"
            % (metadata.get("game"),),
        )
        self.assertEqual(
            list(metadata).index("game"),
            list(metadata).index("kind") + 1,
            "the field is written immediately after `kind`, so the members have one "
            "order and not one per writer (checkpoint.md §2.1, §3, docs/L3/agents/"
            "shapes.md §5): %r" % (list(metadata),),
        )
        self.assertEqual(
            (metadata.get("params") or {}).get("count"),
            J.param_count(learner),
            "the container records the count `param_count` reports, which the head's "
            "width A moved (shapes.md §2, checkpoint.md §2.1, ASM-40): %r"
            % ((metadata.get("params") or {}).get("count"),),
        )
        restored = J.load(None, path)
        self.assertEqual(
            J.learner_game(restored),
            name,
            "load(None, path) -- the path alone, which is how a shipped member is "
            "loaded -- recovers the shape the container names (docs/L2/agents/"
            "surface.md §9, shapes.md §5, records.md §7): %r"
            % (J.learner_game(restored),),
        )
        self.assertEqual(
            J.learner_actions(restored),
            J.head_width(name),
            "the restored learner's head is the shape's descriptor count, rebuilt from "
            "the file rather than defaulted (shapes.md §2, §5, checkpoint.md §3, "
            "ASM-40): %r against %r"
            % (J.learner_actions(restored), J.head_width(name)),
        )
        self.assertEqual(
            J.param_count(restored),
            J.param_count(learner),
            "a restored learner reports the saved capacity (docs/L2/agents/surface.md "
            "§5, §9, ASM-5): %r against %r"
            % (J.param_count(restored), J.param_count(learner)),
        )
        for position, (_hand, facts, legal, _chosen, _index) in enumerate(
            self.decisions(name)
        ):
            observation = J.encode(encoder, facts)
            mask = J.legal_indices(legal)
            self.assertEqual(
                J.action_index(J.act(restored, observation, mask)),
                J.action_index(J.act(learner, observation, mask)),
                "save/load is loss-free at the decision boundary on a real no-limit "
                "readout, which is the equality protocol.md §5 requires (shapes.md §5, "
                "checkpoint.md §1): decision %d" % (position,),
            )
        with_spec = J.load(
            J.shaped_learner_spec(
                "naive-stack",
                J.WIDTH_SHAPE,
                J.DEPTH_SHAPE,
                J.LEARNER_SEED_SHAPE,
                name,
            ),
            path,
        )
        self.assertEqual(
            J.learner_game(with_spec),
            name,
            "a spec naming the shape the container records compares equal and the file's "
            "shape is kept, so the spec's key is a comparison and never a migration "
            "(docs/L2/agents/surface.md §9, shapes.md §5, checkpoint.md §3): %r"
            % (J.learner_game(with_spec),),
        )
        hand = J.shaped_hand(J.DEAL_SHAPE_A, name)
        observation = J.encode(encoder, J.readout(hand))
        mask = J.legal_indices(J.legal_actions(hand))
        self.assertEqual(
            J.action_index(J.act(with_spec, observation, mask)),
            J.action_index(J.act(restored, observation, mask)),
            "one checkpoint restored twice gives two learners that decide alike, the "
            "spec's own shape being the one the file records (docs/L2/agents/surface.md "
            "§9, protocol.md §5, ASM-5): %r"
            % (J.action_index(J.act(with_spec, observation, mask)),),
        )


class ShapeDefaultContainer(J.JoinCase):
    """A default-shape save: today's version 3 and no `game` key at all."""

    def test_join_agt_15_2_a_default_shape_save_writes_format_3_and_no_game(self):
        """JOIN-AGT-15.2 a default-shape learner is saved as format version 3 whose
        `metadata.json` carries no `game` key at all — not one naming the default — and
        the file is read back as the default shape with its head and capacity intact,
        while a spec naming the default explicitly writes the very same version
        (`docs/L2/agents/shapes.md` §5, `docs/L3/agents/checkpoint.md` §2.1, §3,
        `docs/L3/agents/shapes.md` §5, `sizing.md` §6, ASM-40, D-29).
        """
        names = J.shape_names()
        default_name = names[0]
        kind, width, depth = "naive-stack", J.WIDTH_SHAPE, J.DEPTH_SHAPE
        by_absence = J.build_learner(
            J.learner_spec(kind, width, depth, J.LEARNER_SEED_SHAPE)
        )
        named = J.shaped_learner(
            kind, width, depth, J.LEARNER_SEED_SHAPE, default_name
        )
        saved = {}
        for label, learner in (("absence", by_absence), ("named", named)):
            with self.subTest(spec=label):
                path = J.save(
                    learner,
                    self.checkpoint_path(
                        J.CHECKPOINT_SHAPE_ALPHA if label == "absence"
                        else J.CHECKPOINT_SHAPE_BETA
                    ),
                )
                metadata = J.container_metadata(path)
                self.assertEqual(
                    metadata.get("format_version"),
                    DEFAULT_VERSION,
                    "a learner of the default shape writes today's format version 3, so "
                    "a fixed-limit save's members are byte-for-byte today's (shapes.md "
                    "§5, checkpoint.md §3, sizing.md §6, ASM-40): %r"
                    % (metadata.get("format_version"),),
                )
                self.assertNotIn(
                    "game",
                    metadata,
                    "a default-shape save carries no `game` key at all -- a field its "
                    "writer would never have written, which is why a version-4 one "
                    "naming the default is refused (shapes.md §5, checkpoint.md §3): %r"
                    % (sorted(metadata),),
                )
                restored = J.load(None, path)
                self.assertEqual(
                    J.learner_game(restored),
                    default_name,
                    "a version-3 container is read as the default shape, as a version-1 "
                    "one is (shapes.md §5, checkpoint.md §3, D-29): %r"
                    % (J.learner_game(restored),),
                )
                self.assertEqual(
                    J.learner_actions(restored),
                    J.head_width(default_name),
                    "the restored head is the default shape's descriptor count — today's "
                    "three, read off the catalogue (shapes.md §2, sizing.md §6): %r "
                    "against %r"
                    % (J.learner_actions(restored), J.head_width(default_name)),
                )
                self.assertEqual(
                    J.param_count(restored),
                    J.param_count(learner),
                    "and the saved capacity, unmoved (docs/L2/agents/surface.md §5, §9, "
                    "ASM-5): %r against %r"
                    % (J.param_count(restored), J.param_count(learner)),
                )
                saved[label] = (metadata.get("format_version"), sorted(metadata))
        self.assertEqual(
            saved["named"],
            saved["absence"],
            "naming the default shape explicitly and naming no shape write one "
            "container: the same version and the same fields (shapes.md §1, §5, "
            "docs/L2/agents/surface.md §4, D-29): %r against %r"
            % (saved["named"], saved["absence"]),
        )


class ShapeContainerRefusals(J.JoinCase):
    """The two container refusals the shape adds, each naming what it refuses."""

    def test_join_agt_15_3_the_two_container_refusals_name_the_field_and_both_shapes(self):
        """JOIN-AGT-15.3 a version-4 container naming the default shape is refused,
        naming the field and that shape, and a `load` spec naming a shape its container
        contradicts is refused naming **both** shapes — the spellings this case passed,
        read off `engine.game_shapes()` — while the same spec against a container that
        records it is not refused (`docs/L2/agents/shapes.md` §5-§6, `docs/L3/agents/
        checkpoint.md` §3, `docs/L3/agents/shapes.md` §5-§6, `sizing.md` §6, ASM-40,
        D-29).
        """
        names = J.shape_names()
        default_name, second_name = names[0], names[1]
        kind, width, depth = "naive-stack", J.WIDTH_SHAPE, J.DEPTH_SHAPE
        default_path = J.save(
            J.shaped_learner(kind, width, depth, J.LEARNER_SEED_SHAPE, default_name),
            self.checkpoint_path(J.CHECKPOINT_SHAPE_BETA),
        )
        other_path = J.save(
            J.shaped_learner(kind, width, depth, J.LEARNER_SEED_SHAPE, second_name),
            self.checkpoint_path(J.CHECKPOINT_SHAPE_GAMMA),
        )
        doctored = J.rewrite_container(
            default_path,
            self.checkpoint_path(J.CHECKPOINT_SHAPE_ALPHA),
            format_version=GAME_VERSION,
            game=default_name,
        )
        metadata = J.container_metadata(doctored)
        self.assertEqual(
            (metadata.get("format_version"), metadata.get("game")),
            (GAME_VERSION, default_name),
            "the surgery this case drives lands: a version-4 container whose `game` "
            "names the default shape, which no writer of this module writes "
            "(checkpoint.md §3): %r" % (metadata,),
        )
        self.assert_refusal(
            "load",
            (("game",), (default_name,)),
            lambda: J.load(None, doctored),
            note="JOIN-AGT-15.3 a version-4 container naming the default shape",
        )
        contradictory = J.shaped_learner_spec(
            kind, width, depth, J.LEARNER_SEED_SHAPE, default_name
        )
        self.assert_refusal(
            "load",
            ((default_name,), (second_name,)),
            lambda: J.load(contradictory, other_path),
            note="JOIN-AGT-15.3 a spec naming %r against a container read as %r"
            % (default_name, second_name),
        )
        agreeing = J.shaped_learner_spec(
            kind, width, depth, J.LEARNER_SEED_SHAPE, second_name
        )
        self.assertEqual(
            J.learner_game(J.load(agreeing, other_path)),
            second_name,
            "the refusal is the disagreement and not the key: a spec naming the shape "
            "the container records loads, and the shape is the file's (docs/L2/agents/"
            "surface.md §9, checkpoint.md §3, shapes.md §5): %r"
            % (J.learner_game(J.load(agreeing, other_path)),),
        )


class ShapeShippedContainers(J.JoinCase):
    """The tree's version-1 containers, loaded read-only as the default shape."""

    def label(self, path):
        """A container's path under `checkpoints/`, for a subtest's label."""
        return os.path.relpath(path, J.SHIPPED_ROOT)

    def test_join_agt_15_4_a_shipped_version_1_container_loads_as_the_default_shape(self):
        """JOIN-AGT-15.4 every version-1 container the tree ships under `checkpoints/`
        loads unchanged as the default shape — `game` equal to the catalogue's first name
        and `actions` its declared head width (today's three) — at a policy answer that
        is one `engine.legal_actions` offered at a real default-shape readout, and none
        of the files is rewritten: their `(size, mtime)` are unmoved (`docs/L2/agents/
        shapes.md` §5, `docs/L3/agents/checkpoint.md` §3, `docs/L1/shapes.md` §5,
        `docs/L1/records.md` §7, ASM-5, ASM-18, ASM-40, D-29).
        """
        names = J.shape_names()
        default_name = names[0]
        shipped = J.shipped_containers(version=1)
        self.assertTrue(
            shipped,
            "the tree ships version-1 containers under %r, and this case walks every "
            "one of them (shapes.md §5, checkpoint.md §3, ASM-5): %r"
            % (J.SHIPPED_ROOT, shipped),
        )
        stamps = {path: J.container_stamp(path) for path in shipped}
        hand = J.new_hand(J.DEAL_SHAPE_A)
        facts, legal = J.readout(hand), J.legal_actions(hand)
        for path in shipped:
            with self.subTest(container=self.label(path)):
                metadata = J.container_metadata(path)
                self.assertEqual(
                    metadata.get("format_version"),
                    1,
                    "the set this case walks is the version-1 one (checkpoint.md §3): %r"
                    % (path,),
                )
                self.assertNotIn(
                    "game",
                    metadata,
                    "a version-1 container predates any other shape and must not carry a "
                    "`game`; one that did would be refused, not read (shapes.md §5, "
                    "checkpoint.md §3): %r" % (sorted(metadata),),
                )
                member = J.load(None, path)
                self.assertEqual(
                    J.learner_game(member),
                    default_name,
                    "a version-1 container is read as the **default** shape, exactly as "
                    "an absent `learning_rule` reads as the catalogue's first (shapes.md "
                    "§5, checkpoint.md §3, D-19, D-29): %r" % (J.learner_game(member),),
                )
                self.assertEqual(
                    J.learner_actions(member),
                    J.head_width(default_name),
                    "and with the default shape's head width -- the three descriptors the "
                    "catalogue declares -- because no `game` field moved it (shapes.md "
                    "§2, §5, sizing.md §6, ASM-40): %r against %r"
                    % (J.learner_actions(member), J.head_width(default_name)),
                )
                self.assertEqual(
                    J.param_count(J.load(None, path)),
                    J.param_count(member),
                    "one checkpoint restored twice reports one capacity, so the shape's "
                    "geometry was resolved from the file and not from a call's order "
                    "(docs/L2/agents/surface.md §9, ASM-5): %r" % (path,),
                )
                representation = metadata.get("representation") or {}
                encoding = representation.get("encoding")
                self.assertIsInstance(
                    encoding,
                    str,
                    "the container records the representation it was written on, and its "
                    "encoding is the one an encoder is built from (checkpoint.md §1-§2.1): "
                    "%r" % (representation,),
                )
                policy = J.as_policy(
                    member,
                    J.shaped_encoder(encoding, default_name),
                    J.POLICY_SEED_SHAPE,
                )
                chosen = policy(facts, legal)
                self.assert_descriptor_in(
                    legal,
                    chosen,
                    "JOIN-AGT-15.4 the shipped member's policy at one real default-shape "
                    "readout (%r)" % (path,),
                )
        self.assertEqual(
            {path: J.container_stamp(path) for path in shipped},
            stamps,
            "loading a shipped container is read-only: the shipped version-1 files keep "
            "their `(size, mtime)`, so none of them is rewritten or regenerated "
            "(shapes.md §5, ASM-5, ASM-18, ASM-40)",
        )


if __name__ == "__main__":
    unittest.main()
