"""FAM-25.1 — a seeded, strength-fed learner trains for a few hands, and its control does not.

``docs/L1/strength-design.md`` §F.3 (FAM-25.1), §A.4, §D.2-§D.4 and §E; ``ASM-46``,
``ASM-48``, ``ASM-49``, ``ASM-50``, ``ASM-51``; ``docs/L1/e2e-surface.md`` §3.3-§3.5;
``records.md`` §12, §15.

The whole change, end to end, through declared entry points only: one configuration trains
the six-seat shape at thirty hands with `strength: supervised`, the declared source `attn-60`
and its card rows copied into the learner's embedding table; the same configuration with
**both** declarations absent is the control.  The two arms differ in exactly the declared
axis (D-3) and in nothing else, and every artefact each one writes is checked:

* the record's `variants` row names the member and the seed record, with a 16-hex digest
  (`ASM-46`, `ASM-49`);
* the final container is a **format version 6** one carrying both fields, and the control's
  is a version-4 one carrying neither (`ASM-50`, §E.1);
* rows 1..52 of a learner built from the configuration's **own spec** are
  `features.card_rows(features.load_strength('attn-60'))` bit for bit, reshaped at the
  learner's own `(vocabulary, width)` -- the seed is a parameter-space copy and is asserted
  as one (`ASM-49`, §D.3); and the run's **trained** container's rows 1..52 are still the
  seeded rows, moved only by the pass's own steps (measured: 1.8e-05 over thirty hands,
  against the seed's own draw's O(1)), which is what §D.2's copy buys after a pass;
* the declaring encoder's observation is **123 ids** on the six-seat shape and its last id
  is one of the ladder's eight, while the control's is 122 over the shape row's 102
  (`ASM-46`, `ASM-48`, §A.4);
* the greedy pass is the exploration-off one and its block is the shape it always was
  (`records.md` §15).

The configuration's facts are the design's; the configuration's **label**, its pool id and
the write root are this battery's own (`battery.md` §4, D-15), and the width, the depth and
the two catalogue members are the ones §F.3 names.
"""

import json
import os
import sys
import unittest
import zipfile

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _surface as S  # noqa: E402

#: The declared source the case seeds from and reads with, and the rows selector (`ASM-51`).
SOURCE = "attn-60"
ROW_SELECTOR = "cards"

#: The case's own labels (`battery.md` §4, D-15): the configuration, its one variant and the
#: pool id it declares.
RUNG = "rung-invented-strength-25"
VARIANT = "strength-arm-invented-25"
POOL = "pool-invented-strength-25"
CONTROL_RUNG = "rung-invented-strength-control-25"
CONTROL_VARIANT = "control-arm-invented-25"
CONTROL_POOL = "pool-invented-strength-control-25"

#: The seed set, the budget and the architecture §F.3 names: one seed, thirty hands -- ten at
#: the smallest, and thirty so the snapshot rule holds with room to spare -- the six-seat
#: shape, the token encoding, a width-50 depth-2 embedding, the risk-averse utility and the
#: catalogue's first rule.
SEED = 0
BUDGET = 30
SHAPE = S.SHAPE_THIRD
WIDTH = 50
DEPTH = 2
UTILITY = "stack-shortfall"
RULE = "masked-q-learning"

#: The widths the two arms' observations are, on the six-seat shape (`ASM-46`, `ASM-48`,
#: §A.4): 122 tokens over the row's 102 ids, and 123 over the widened 110.
ABSENCE_WIDTH = 122
ABSENCE_VOCABULARY = 102
DECLARING_WIDTH = 123
DECLARING_VOCABULARY = 110

#: The ladder's eight ids in the declaring arm's last slot (`ASM-48`).
LADDER_FIRST = 102
LADDER_LAST = 109

#: One run per arm, played once and shared by the cases that read it (`battery.md` §2).
_RUNS = {}


def once(key, thunk):
    """Call `thunk` once per session and hand the same record to every case."""
    if key not in _RUNS:
        _RUNS[key] = thunk()
    return _RUNS[key]


def configuration(name, variant, pool, declaring):
    """The six-seat configuration §F.3 names, with the two declarations present or absent.

    `declaring` writes `strength`, `strength_source` and `embedding_init`; its absence writes
    none of them, which is the control: the same shape, encoding, architecture, utility and
    rule, differing in the declared axis alone (D-3, §F.3).
    """
    entry = {
        "name": variant,
        "backend": "torch",
        "encoding": "card-tokens",
        "architecture": {
            "kind": "token-embedding",
            "width": WIDTH,
            "depth": DEPTH,
            "sparsity": 0.0,
            "residual": False,
        },
        "learning_rule": RULE,
        "utility": UTILITY,
        "samples": BUDGET,
        "seeds": [SEED],
        "snapshot_every": max(1, BUDGET // 10),
        "device": "cpu",
        "table": "live",
        "param_budget": 11000,
        "game": SHAPE,
    }
    if declaring:
        entry["strength"] = "supervised"
        entry["strength_source"] = SOURCE
        entry["embedding_init"] = {"source": SOURCE, "rows": ROW_SELECTOR}
    return {
        "name": name,
        "axis": "the strength member and its seed, at one architecture",
        "carried_from": None,
        "primary": variant,
        "game": SHAPE,
        "variants": [entry],
        "pool": {
            "id": pool,
            "lineage": None,
            "m": 5,
            "frozen": True,
            "members": [],
            # A six-seat hand seats five **distinct** opponents, so the pool must hold five
            # members: the three anchor baselines plus the two folders a membership
            # declaration may admit (`seats.md` §4, ASM-43, records.md §8, D-21).
            "baselines": ["fold-no-pair-or-face", "fold-no-pair-or-better"],
            "game": SHAPE,
        },
        "seeds": [SEED],
        "samples": BUDGET,
        "param_budget": 11000,
        "table": "live",
        "device": "cpu",
        "snapshot_every": max(1, BUDGET // 10),
    }


def run_of(case, declaring):
    """`training.run` of one arm, driven through the declared entry point."""
    if declaring:
        key, spec = ("strength-declaring", RUNG), configuration(
            RUNG, VARIANT, POOL, True
        )
    else:
        key, spec = ("strength-control", CONTROL_RUNG), configuration(
            CONTROL_RUNG, CONTROL_VARIANT, CONTROL_POOL, False
        )
    return once(key, lambda: case.run_record(spec, (SEED,), BUDGET))


def final_of(record, variant):
    """The final checkpoint one variant at one seed wrote, through the record's own block."""
    block = S.declared_field(
        record, "a run record (records.md §12)", "checkpoints"
    )[str(variant)][str(SEED)]
    return S.declared_field(block, "a checkpoints block (records.md §12)", "final")


def on_disk(path):
    """One record-named checkpoint path as the file it is (`protocol.md` §5).

    A run record's paths are repository-relative unless the ambient write root redirected
    them, so a case resolves a relative one against the repository root and never invents
    one (`write-root.md` §1, §5, `checkpoints.md` §2).
    """
    text = str(path)
    return text if os.path.isabs(text) else os.path.join(S.repo_root(), text)


def container(path):
    """`(metadata, parameters)` of one checkpoint container, read from the file it wrote."""
    with zipfile.ZipFile(on_disk(path)) as archive:
        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        parameters = archive.read("parameters.npy")
    return metadata, parameters


def declaring_encoder():
    """The declaring encoder on the case's shape, through the declared keyword (`ASM-46`)."""
    return S.module("features").build_encoder(
        "card-tokens", shape=SHAPE, strength="supervised"
    )


def absence_encoder():
    """The same encoder with no member: today's declaration (`ASM-46`, §A.5)."""
    return S.module("features").build_encoder("card-tokens", shape=SHAPE)


class FAM25SeededStrengthRun(S.SurfaceCase):
    """FAM-25.1 — the declaring run, its artefacts, and the control."""

    def test_fam25_1_a_seeded_strength_fed_learner_trains_and_its_control_does_not(self):
        """FAM-25.1 thirty hands of the six-seat shape with `strength: supervised` and
        `embedding_init` from `attn-60` train green; the record names the member and the seed
        with a 16-hex digest; the final container is a version-6 one with both fields; its
        parameter block's rows 1..52 are the source's card rows bit for bit; the declaring
        observation is 123 ids whose last is one of the ladder's eight; and the identical
        configuration with both declarations absent trains green and writes a version-4
        container with a 122-long observation over 102 ids (`ASM-46`-`ASM-51`, §F.3)."""
        record = run_of(self, True)
        self.assertIsNotNone(
            record,
            "the declaring run returned no record, so thirty hands of the six-seat shape "
            "did not train green (FAM-25.1, §F.3)",
        )
        rows = S.declared_field(record, "a run record (records.md §12)", "variants")
        self.assertEqual(
            len(rows), 1,
            "the configuration declares one variant and the record carries one row "
            "(records.md §12): %r" % (len(rows),),
        )
        row = rows[0]
        self.assertEqual(
            row.get("strength"), "supervised",
            "the variant's row names the member it read, so the declaration reached the "
            "record (ASM-46, records.md §12): %r" % (row.get("strength"),),
        )
        seeding = row.get("seeding")
        self.assertTrue(
            S.is_mapping(seeding),
            "and the seed record beside it, so the run is attributable to one estimator "
            "(ASM-49, records.md §12): %r" % (seeding,),
        )
        self.assertEqual(
            seeding.get("source"), SOURCE,
            "the seed record names the source the configuration declared (ASM-49): %r"
            % (seeding,),
        )
        digest = seeding.get("digest")
        self.assertIsInstance(
            digest, str, "the digest is a string of hex (ASM-49): %r" % (digest,)
        )
        self.assertEqual(
            len(digest), 16,
            "the digest is sixteen hexadecimal characters (ASM-49, §E.1): %r" % (digest,),
        )
        for character in digest:
            self.assertIn(
                character, "0123456789abcdef",
                "the digest is hexadecimal (ASM-49): %r" % (digest,),
            )
        self.assertEqual(
            seeding.get("space"), "parameter",
            "and the record states the space the copy was written in (ASM-49, §D.3): %r"
            % (seeding,),
        )
        # The final container: version 6, both fields, and the copy in its parameters.
        final = final_of(record, VARIANT)
        metadata, parameters = container(final)
        self.assertEqual(
            metadata.get("format_version"), 6,
            "the run's final container is a format version 6 one (ASM-50, §E.1): %r"
            % (metadata.get("format_version"),),
        )
        self.assertEqual(
            metadata.get("strength"), "supervised",
            "carrying the member it read (ASM-50): %r" % (metadata.get("strength"),),
        )
        self.assertEqual(
            metadata.get("seeding"), seeding,
            "and the very seed record the run's row carries, so the two witnesses agree "
            "(ASM-49, ASM-50): %r against %r" % (metadata.get("seeding"), seeding),
        )
        width = int(metadata["settings"]["width"])
        vocabulary = int(metadata["representation"]["size"])
        self.assertEqual(
            (vocabulary, width), (DECLARING_VOCABULARY, WIDTH),
            "the container records the widened vocabulary 110 and the width 50 the "
            "configuration declares (ASM-48, §A.4): %r" % ((vocabulary, width),),
        )
        array = _array(parameters)
        count = int(metadata["params"]["count"])
        online = array[:count]
        offset = _input_offset(metadata)
        length = int(metadata["params"]["tensors"][0]["count"])
        table = online[offset : offset + length].reshape(vocabulary, width)
        model = S.module("features").load_strength(SOURCE)
        card_rows, _digest = S.module("features").card_rows(model)
        self.assertEqual(
            card_rows.shape, (52, width),
            "the source's card rows are (52, width) at the learner's own width (ASM-49): "
            "%r" % (card_rows.shape,),
        )
        # The copy, **bit for bit**, on the learner this container's own spec builds: the
        # seed is exact at the build, which is where §D.2 puts it, and the run's container is
        # the trained artefact (the next assertion measures how far the pass moved it).
        import numpy

        fresh = self.ep("agents", "build_learner")(
            {
                "backend": "torch",
                "architecture": {
                    "kind": "token-embedding",
                    "width": WIDTH,
                    "depth": DEPTH,
                    "sparsity": 0.0,
                    "residual": False,
                },
                "seed": SEED,
                "encoder": declaring_encoder(),
                "game": SHAPE,
                "strength": "supervised",
                "strength_source": SOURCE,
                "embedding_init": {"source": SOURCE, "rows": ROW_SELECTOR},
            }
        )
        fresh_parameters = self.ep("agents", "save")(
            fresh, os.path.join(self.scratch(), "fam25-seed-exact.ckpt")
        )
        fresh_metadata, fresh_bytes = container(fresh_parameters)
        fresh_array = _array(fresh_bytes)
        fresh_count = int(fresh_metadata["params"]["count"])
        fresh_offset = _input_offset(fresh_metadata)
        fresh_length = int(fresh_metadata["params"]["tensors"][0]["count"])
        fresh_table = fresh_array[:fresh_count][
            fresh_offset : fresh_offset + fresh_length
        ].reshape(vocabulary, width)
        self.assertEqual(
            fresh_table[1:53].tolist(), card_rows.tolist(),
            "rows 1..52 of a learner built from this configuration's own spec are not the "
            "source's card rows bit for bit, so the `cards` selector does not copy exactly "
            "(ASM-49, §D.2, §D.3): %r against %r"
            % (fresh_table[1:53][:1].tolist(), card_rows[:1].tolist()),
        )
        self.assertEqual(
            fresh_table[0].tolist(), _draw_table(vocabulary, width)[0].tolist(),
            "and row 0 is the pad's, so it keeps the seed's own draw: the copy is bounded "
            "to the card ids (ASM-49, §D.3): %r" % (fresh_table[0][:2].tolist(),),
        )
        # ... and the seed survived the run: the trained container's rows 1..52 are the
        # source's, moved only by the pass's own steps -- measured, not assumed.  `§D.3`'s
        # copy is parameter-exact and read through the bounded squash, so the pass does move
        # the rows; what this asserts is that they are still the seeded rows and not the
        # seed's own draw, which is the difference the copy makes (ASM-49, §G.1 risk 3).
        moved = float(numpy.max(numpy.abs(table[1:53] - card_rows)))
        drawn_rows = _draw_table(vocabulary, width)
        drawn = float(numpy.max(numpy.abs(drawn_rows[1:53] - card_rows)))
        self.assertLess(
            moved, 1e-3,
            "the run's trained card rows moved %.3e from the source's, and a thirty-hand "
            "pass of this configuration moves them by about 2e-5 (measured): the seed is not "
            "in the container the run wrote (ASM-49, §D.2): the largest difference is %.3e"
            % (moved, moved),
        )
        self.assertLess(
            moved, drawn,
            "the run's card rows are no closer to the source's than the seed's own draw "
            "would be, so the copy did not reach the container the run wrote (ASM-49): "
            "%.3e from the source against %.3e for the draw" % (moved, drawn),
        )
        # The observation: 123 ids on this shape, its last one of the ladder's eight.
        declaring_spec = S.module("features").observation_spec(declaring_encoder())
        self.assertEqual(
            tuple(declaring_spec["shape"]), (DECLARING_WIDTH,),
            "the declaring encoder's observation is 123 ids on the six-seat shape -- the "
            "122 the pre-change declaration named and one more (ASM-46, §A.4): %r"
            % (tuple(declaring_spec["shape"]),),
        )
        self.assertEqual(
            declaring_spec["vocabulary"], DECLARING_VOCABULARY,
            "over the widened vocabulary 110 (ASM-48): %r"
            % (declaring_spec.get("vocabulary"),),
        )
        self.assertIn(
            "strength", tuple(declaring_spec["fields"]),
            "and its fields carry the tenth fact last (ASM-46): %r"
            % (tuple(declaring_spec["fields"]),),
        )
        for readout, where in self.live_readouts():
            with self.subTest(decision=where):
                declared = S.module("features").stated(model, readout)
                self.assertIsNot(
                    declared, readout,
                    "the injection is a fresh mapping and never a mutation of the engine's "
                    "own readout (ASM-47): %r" % (where,),
                )
                slots = list(S.numbers(S.module("features").encode(
                    declaring_encoder(), declared
                )))
                self.assertEqual(
                    len(slots), DECLARING_WIDTH,
                    "every observation of the declaring run is 123 ids on this shape "
                    "(ASM-46, FAM-25.1): %d at %r" % (len(slots), where),
                )
                self.assertGreaterEqual(
                    int(slots[-1]), LADDER_FIRST,
                    "and its last id is one of the ladder's eight, never the pad or a "
                    "street id (ASM-48): %r at %r" % (slots[-1], where),
                )
                self.assertLessEqual(
                    int(slots[-1]), LADDER_LAST,
                    "and its last id is one of the ladder's eight (ASM-48): %r at %r"
                    % (slots[-1], where),
                )
        # The greedy pass: exploration off, and the block's own five keys.
        greedy = S.declared_field(record, "a run record (records.md §12)", "greedy")
        block = greedy[str(VARIANT)][str(SEED)]
        self.assertEqual(
            block.get("mode"), "off",
            "the run's one retained decision stream is the exploration-off pass "
            "(records.md §15, sizing.md §4): %r" % (block.get("mode"),),
        )
        self.assertEqual(
            tuple(block),
            ("mode", "seed", "hands", "net_chips", "decisions"),
            "and its block is §15's five keys and nothing else, so the injected fact moved "
            "no record (records.md §15, ASM-47): %r" % (tuple(block),),
        )
        for decision in block["decisions"]:
            with self.subTest(decision="retained"):
                self.assertEqual(
                    tuple(decision),
                    ("index", "descriptor", "amount", "minimum", "maximum", "legal", "tie"),
                    "and every retained decision record is the shape it was -- no readout "
                    "and no injected value is kept (records.md §15, ASM-47): %r"
                    % (tuple(decision),),
                )
        # The control: the same configuration with both declarations absent.
        control = run_of(self, False)
        control_rows = S.declared_field(
            control, "a control run record (records.md §12)", "variants"
        )
        self.assertEqual(
            len(control_rows), 1,
            "the control declares one variant and its record carries one row: %r"
            % (len(control_rows),),
        )
        self.assertNotIn(
            "strength", control_rows[0],
            "the control's row names no member, because it read no model input (ASM-46): %r"
            % (sorted(control_rows[0]),),
        )
        self.assertNotIn(
            "seeding", control_rows[0],
            "and carries no seed record (ASM-49): %r" % (sorted(control_rows[0]),),
        )
        self.assertNotIn(
            "strengths", control,
            "and the run writes no `strengths` set, which is what keeps a default record at "
            "its capture (ASM-46, records.md §12): %r" % (sorted(control),),
        )
        control_metadata, _control_parameters = container(final_of(control, CONTROL_VARIANT))
        self.assertEqual(
            control_metadata.get("format_version"), 4,
            "the control's final container is a version-4 one -- another shape and no "
            "strength declaration -- so the two arms differ in the declared axis and in the "
            "era it implies (ASM-50, §E.1): %r"
            % (control_metadata.get("format_version"),),
        )
        self.assertNotIn(
            "strength", control_metadata,
            "and carries no strength field (ASM-50): %r" % (sorted(control_metadata),),
        )
        self.assertNotIn(
            "seeding", control_metadata,
            "and no seed record (ASM-49): %r" % (sorted(control_metadata),),
        )
        control_spec = S.module("features").observation_spec(absence_encoder())
        self.assertEqual(
            tuple(control_spec["shape"]), (ABSENCE_WIDTH,),
            "the control's observation is the 122 ids the pre-change declaration named "
            "(ASM-46, §A.5, FAM-24.4): %r" % (tuple(control_spec["shape"]),),
        )
        self.assertEqual(
            control_spec["vocabulary"], ABSENCE_VOCABULARY,
            "over the shape row's own 102 ids (ASM-48, capacity.md §4): %r"
            % (control_spec.get("vocabulary"),),
        )
        for readout, where in self.live_readouts():
            with self.subTest(decision="control", where=where):
                slots = list(S.numbers(S.module("features").encode(
                    absence_encoder(), readout
                )))
                self.assertEqual(
                    len(slots), ABSENCE_WIDTH,
                    "every control observation is 122 ids on this shape (ASM-46, FAM-25.1): "
                    "%d at %r" % (len(slots), where),
                )

    def live_readouts(self):
        """Two readouts of real six-seat hands, through the declared engine entry points.

        The run's own decisions are not retained (`records.md` §15, D-28), so the case reads
        two real decisions of the run's shape instead: a hand played through `engine.play_hand`
        carries a `readout` on every decision record, and those are the facts the loop
        encodes (`records.md` §5).
        """
        entries = []
        policy = self.baseline("always-call", S.SEED_D, SHAPE)
        record = self.play(S.SEED_C, shape=SHAPE, seats=[policy] * self.seats_of(SHAPE))
        for position, decision in enumerate(
            S.declared_field(record, "an episode record (records.md §5)", "decisions")
        ):
            entries.append(
                (
                    S.declared_field(decision, "a decision record", "readout"),
                    "hand %d decision %d" % (S.SEED_C, position),
                )
            )
            if len(entries) >= 2:
                break
        self.assertTrue(
            entries,
            "a six-seat hand played by `always-call` produced no decision record, so the "
            "123-id assertion above would be about nothing (records.md §5)",
        )
        return entries


def _draw_table(vocabulary, width):
    """The same seed's **unseeded** draw, as the `(vocabulary, width)` table it writes.

    Built from the same spec with `embedding_init` absent, through the declared entry points,
    so the comparison below is the copy's own effect and not a second model's (ASM-49,
    §D.2).
    """
    learner = S.module("agents").build_learner(
        {
            "backend": "torch",
            "architecture": {
                "kind": "token-embedding",
                "width": width,
                "depth": DEPTH,
                "sparsity": 0.0,
                "residual": False,
            },
            "seed": SEED,
            "encoder": declaring_encoder(),
            "game": SHAPE,
            "strength": "supervised",
        }
    )
    layout = learner.layout
    parameters = learner.backend.parameters(learner.state)
    offset, length = layout.w_in
    online = parameters[: int(layout.count)]
    return online[offset : offset + length].reshape(layout.input_dim, layout.width)


def _array(parameters):
    """One container's `parameters.npy` as a float64 array (`checkpoint.md` §2)."""
    import io

    import numpy

    return numpy.load(io.BytesIO(parameters), allow_pickle=False)


def _input_offset(metadata):
    """The input block's offset, read off the container's own tensor table (`checkpoint.md`)."""
    for tensor in metadata["params"]["tensors"]:
        if str(tensor["name"]) == "input.weights":
            return int(tensor["offset"])
    raise AssertionError(
        "the container's tensor table carries no 'input.weights' entry, so the embedding "
        "table's offset is not recorded (checkpoint.md §2.1): %r" % (metadata["params"],)
    )


if __name__ == "__main__":  # pragma: no cover - a case file, run by pytest
    unittest.main()
