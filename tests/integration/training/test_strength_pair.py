"""TRNJ-19 — the strength axis at the run record, and the three witnesses to one declaration.

``docs/L1/strength-design.md`` §C.3, §C.4, §D.4 and §F.2; ``ASM-46``, ``ASM-48``, ``ASM-51``;
``docs/L2/training/declarations.md`` §2-§4; ``docs/L3/training/loop.md`` §1 step 3, §4;
``records.md`` §12.

`strength` is the **fourth** catalogue and it rides **opt-in per variant**, exactly as D-43's
counterfactual member does: an entry's `strength`, absent meaning the catalogue's first, so a
paired arm differs only in it -- on one frozen pool, one seed set and one budget (D-3).

So this file is the run record's half of that join, and it is three facts that no single
module can check about itself:

* **TRN-9.2** a two-arm pair differing only in `strength` trains both arms; the record's
  `variants` rows name the member on the non-default arm **only**, the run-level `strengths`
  set appears only then, and a default configuration's record carries neither key;
* **TRN-9.3** the join: `training.declarations.STRENGTH_SOURCES` equals `features`' declared
  table row for row, so the restatement and its owner cannot drift;
* **TRN-9.4** a declared `strength` is never silently dropped, and the case reads the
  **spec** handed to `agents.build_learner` -- the first of the three witnesses -- beside the
  encoder the loop built with the member (`observation_spec`'s width) and the member the
  learner carries.

One paired run and one control are played, at the invented budget of ten hands per variant,
one seed, on the default shape (seconds).  Every label, seed, budget and pool id below is
this battery's own (`docs/L1/battery.md` §4, D-15); the catalogue members, the shapes and the
source names are read off `agents.learners()` and the declared tables.
"""

import copy
import importlib
import importlib.util
import json
import os
import sys
import unittest
import zipfile

_HERE = os.path.dirname(os.path.abspath(__file__))
# The support module is loaded under a private name: this repository's integration
# batteries share the file name `_join_support.py`, so a plain import would hand one
# battery another's helpers when two test directories are collected in one process.
if "training_join_support" in sys.modules:
    J = sys.modules["training_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "training_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["training_join_support"] = J
    _spec.loader.exec_module(J)

#: The invented pair's facts (`docs/L1/battery.md` §4, D-15): the configuration's label, its
#: two arms' names, the pool it declares, one seed and a budget of ten hands per variant --
#: `training.run`'s smallest accepted budget -- so a pair costs seconds and the interval is 1.
PAIR_RUNG = "rung-invented-strength-pair-19"
PAIR_DEFAULT_ARM = "arm-invented-strength-none-19"
PAIR_DECLARING_ARM = "arm-invented-strength-supervised-19"
PAIR_POOL = "pool-invented-strength-pair-19"
PAIR_SEED = 64283
PAIR_BUDGET = 10

#: The control configuration, whose one arm declares **no** strength declaration at all: it
#: is the shape a default declaration's record keeps, field for field (`records.md` §12).
CONTROL_RUNG = "rung-invented-strength-control-19"
CONTROL_ARM = "arm-invented-strength-control-19"
CONTROL_POOL = "pool-invented-strength-control-19"
CONTROL_SEED = 58031
CONTROL_BUDGET = 10

#: The one declared rows selector (`ASM-49`).
ROW_SELECTOR = "cards"

#: One run per configuration, played once and handed to every case of the class that
#: reads it: a run's record is a function of its configuration and its seeds, so two cases
#: reading one record read one measurement (`docs/L1/battery.md` §2).
_RUNS = {}


def once(key, thunk):
    """Call `thunk` once per session and hand the same record to every case."""
    if key not in _RUNS:
        _RUNS[key] = thunk()
    return _RUNS[key]


def strength_names():
    """The strength catalogue's names, in the order `agents.learners()` publishes them."""
    return tuple(J.learners()["strengths"])


def restated_sources():
    """`training.declarations.STRENGTH_SOURCES`, the restated table (`ASM-51`).

    Read through the module rather than an entry point because a **table** is what the case
    joins, and no declared name returns one: the join battery reads tables for that reason
    and for no other (`D-13`).
    """
    return dict(J.mod("training").declarations.STRENGTH_SOURCES)


def declared_sources():
    """`features`' own source table, the one the restatement is held to (`ASM-51`)."""
    return dict(J.mod("features").cardmodel.STRENGTH_SOURCES)


def container_document(path):
    """`metadata.json` of one checkpoint, parsed (`checkpoint.md` §2)."""
    with zipfile.ZipFile(J.resolve(path)) as archive:
        return json.loads(archive.read("metadata.json").decode("utf-8"))


def token_arm(name, samples=PAIR_BUDGET, seeds=None, **settings):
    """One `card-tokens` variant entry, in `ladder.md` §3's shape (`records.md` §2).

    R3's own entry -- the tokenised learner of the registry -- with the case's labels,
    budget and settings, so nothing but the axis this file is about is this case's
    invention (`docs/L3/training/registry.md` §1).
    """
    entry = copy.deepcopy(J.variant_entry(J.rung("R3"), "card-tokens"))
    entry["name"] = name
    entry["samples"] = samples
    entry["seeds"] = list(seeds if seeds is not None else (PAIR_SEED,))
    entry["snapshot_every"] = max(1, samples // J.SNAPSHOT_POINTS)
    entry.update(settings)
    return entry


def pool_block(identifier):
    """The membership a run declares: the three anchor baselines and no version member."""
    return {"id": identifier, "lineage": None, "m": 5, "frozen": True, "members": []}


def pair_configuration():
    """Two arms on one pool, one seed set and one budget, differing only in `strength`."""
    member = strength_names()[1]
    source = tuple(restated_sources())[0]
    return {
        "name": PAIR_RUNG,
        "axis": "the strength member, at one architecture",
        "carried_from": None,
        "primary": PAIR_DECLARING_ARM,
        "variants": [
            token_arm(PAIR_DEFAULT_ARM),
            token_arm(PAIR_DECLARING_ARM, strength=member, strength_source=source),
        ],
        "pool": pool_block(PAIR_POOL),
        "seeds": [PAIR_SEED],
        "samples": PAIR_BUDGET,
        "param_budget": 12000,
        "table": "live",
        "device": "cpu",
        "snapshot_every": max(1, PAIR_BUDGET // J.SNAPSHOT_POINTS),
    }


def control_configuration():
    """One arm that declares no strength declaration at all: the default's own record."""
    return {
        "name": CONTROL_RUNG,
        "axis": "a configuration in no registry",
        "carried_from": None,
        "primary": CONTROL_ARM,
        "variants": [token_arm(CONTROL_ARM, samples=CONTROL_BUDGET, seeds=(CONTROL_SEED,))],
        "pool": pool_block(CONTROL_POOL),
        "seeds": [CONTROL_SEED],
        "samples": CONTROL_BUDGET,
        "param_budget": 12000,
        "table": "live",
        "device": "cpu",
        "snapshot_every": max(1, CONTROL_BUDGET // J.SNAPSHOT_POINTS),
    }


def pair_run():
    """`run` of the invented pair, played once for the whole battery."""
    configuration = pair_configuration()
    return once(("strength-pair", PAIR_RUNG), lambda: J.run(configuration))


def control_run():
    """`run` of the invented control, played once for the whole battery."""
    configuration = control_configuration()
    return once(("strength-control", CONTROL_RUNG), lambda: J.run(configuration))


class StrengthPairTest(J.JoinCase):
    """TRN-9.2 — the pair trains both arms, and the record says which is which."""

    def test_trn9_2_a_pair_differing_only_in_strength_trains_both_arms(self):
        """TRN-9.2 a two-arm pair differing only in `strength` trains **both** arms; the
        declaring arm's `variants` row names its member and the default arm's row carries no
        such key at all; the run-level `strengths` set appears only then; and the default
        configuration's record carries neither key, field for field (`ASM-46`, §C.3,
        `records.md` §12)."""
        default_member, declaring_member = strength_names()
        record = pair_run()
        rows = list(record["variants"])
        self.assertEqual(
            len(rows), 2,
            "the pair declares two arms and the record carries both, so both arms were "
            "trained (ASM-8, §C.3): %r" % ([row.get("name") for row in rows],),
        )
        by_name = {str(row.get("name")): row for row in rows}
        self.assertIn(
            PAIR_DEFAULT_ARM, by_name,
            "the pair's default arm is in the record (records.md §12): %r"
            % (sorted(by_name),),
        )
        self.assertIn(
            PAIR_DECLARING_ARM, by_name,
            "and its declaring arm is, because both arms of a pair are trained (ASM-8): %r"
            % (sorted(by_name),),
        )
        self.assertEqual(
            set(by_name[PAIR_DECLARING_ARM]),
            set(by_name[PAIR_DEFAULT_ARM]) | {"strength"},
            "the declaring arm's row is the default arm's row plus the one conditional key, "
            "so the two rows differ in exactly the declared axis's record and nothing else "
            "(records.md §12, D-3): %r against %r"
            % (sorted(by_name[PAIR_DECLARING_ARM]), sorted(by_name[PAIR_DEFAULT_ARM])),
        )
        self.assertEqual(
            by_name[PAIR_DECLARING_ARM]["strength"], declaring_member,
            "the declaring arm's row names the member it was built under (ASM-46): %r"
            % (by_name[PAIR_DECLARING_ARM].get("strength"),),
        )
        self.assertNotIn(
            "strength", by_name[PAIR_DEFAULT_ARM],
            "and the default arm's row carries no `strength` key: a row naming the declared "
            "default would be a key the capture does not carry (ASM-46, §C.3): %r"
            % (sorted(by_name[PAIR_DEFAULT_ARM]),),
        )
        self.assertEqual(
            list(record["strengths"]), [declaring_member],
            "the run-level `strengths` set names the member the run declared and trained, "
            "and the catalogued order puts one name in it (ASM-46, records.md §12): %r"
            % (record.get("strengths"),),
        )
        self.assertNotIn(
            default_member, record["strengths"],
            "the declared default is not listed, so a run says which inputs produced which "
            "curve without ever naming `none` (ASM-46): %r" % (record["strengths"],),
        )
        # Both arms' curves and checkpoints are in the record, which is what "trained"
        # means here: a row alone would not be evidence of a pass.
        for arm in (PAIR_DEFAULT_ARM, PAIR_DECLARING_ARM):
            with self.subTest(arm=arm):
                self.assertIn(
                    str(arm), record["curves"],
                    "the arm's curve is in the record, so its pass ran (records.md §12): %r"
                    % (sorted(record["curves"]),),
                )
                self.assertIn(
                    str(arm), record["checkpoints"],
                    "and so is the container it wrote (records.md §12): %r"
                    % (sorted(record["checkpoints"]),),
                )
                points = record["curves"][str(arm)][J.seed_key(PAIR_SEED)]
                self.assertEqual(
                    len(points["td_error"]), PAIR_BUDGET,
                    "the arm's curve has one point per hand, so every hand of its pass "
                    "produced a step (records.md §12, curves.md §2): %r"
                    % (len(points["td_error"]),),
                )
        # The control: a configuration declaring nothing writes neither key.
        control = control_run()
        self.assertNotIn(
            "strengths", control,
            "a run whose every variant is on the catalogue's first member writes no "
            "`strengths` key at all, which is what keeps a default record field for field "
            "at its capture (ASM-46, records.md §12): %r" % (sorted(control),),
        )
        for row in control["variants"]:
            with self.subTest(variant=row.get("name")):
                self.assertNotIn(
                    "strength", row,
                    "and no `variants` row names the default either (ASM-46): %r"
                    % (sorted(row),),
                )
                self.assertNotIn(
                    "seeding", row,
                    "nor carries a seed record, because nothing was seeded (ASM-49): %r"
                    % (sorted(row),),
                )

    def test_trn9_2b_the_declaring_arm_writes_a_version_six_container(self):
        """TRN-9.2 (the container half) the declaring arm's final checkpoint is a format
        version 6 container recording the member, and the default arm's is a version 3 one
        with no such field -- so the era boundary is the declaration's and nothing else's
        (`ASM-50`, §E.1)."""
        record = pair_run()
        declaring = J.checkpoints_of(record, PAIR_DECLARING_ARM, PAIR_SEED)
        default = J.checkpoints_of(record, PAIR_DEFAULT_ARM, PAIR_SEED)
        declaring_metadata = container_document(declaring["final"])
        default_metadata = container_document(default["final"])
        self.assertEqual(
            declaring_metadata.get("format_version"), 6,
            "the declaring arm's container is a version-6 one (ASM-50, §E.1): %r"
            % (declaring_metadata.get("format_version"),),
        )
        self.assertEqual(
            declaring_metadata.get("strength"), strength_names()[1],
            "and it records the member its learner read (ASM-50): %r"
            % (declaring_metadata.get("strength"),),
        )
        self.assertEqual(
            default_metadata.get("format_version"), 3,
            "the default arm's container is the version-3 one it always wrote, so the pair "
            "differs in the declaration and not in the era of every container (ASM-50): %r"
            % (default_metadata.get("format_version"),),
        )
        self.assertNotIn(
            "strength", default_metadata,
            "and it carries no strength field (ASM-50): %r"
            % (sorted(default_metadata),),
        )


class StrengthSourceJoinTest(J.JoinCase):
    """TRN-9.3 — the restated source table is its owner's, row for row."""

    def test_trn9_3_the_declared_source_table_is_features_own(self):
        """TRN-9.3 `training.declarations.STRENGTH_SOURCES` equals `features`' declared table
        row for row -- the restatement pattern `SHAPE_NAMES`/`SHAPE_HISTORY` follow -- so the
        paths and the layout attribute names a run is judged against are the ones the frozen
        estimator's owner declares (`ASM-51`, §D.1, D-13)."""
        restated = restated_sources()
        declared = declared_sources()
        self.assertEqual(
            tuple(restated), tuple(declared),
            "the two tables name the same sources, in the same order (ASM-51, D-13): %r "
            "against %r" % (tuple(restated), tuple(declared)),
        )
        for name in declared:
            with self.subTest(source=name):
                self.assertEqual(
                    dict(restated[name]), dict(declared[name]),
                    "the row for %r is not the owner's own, so a run would judge a source "
                    "against a table that drifted from the artefact's (ASM-51, D-13): %r "
                    "against %r" % (name, dict(restated[name]), dict(declared[name])),
                )
        self.assertEqual(
            len(restated), 2,
            "the declared table carries the two shipped estimators and only those: the "
            "onehot model is deliberately not one of them, because its projection can "
            "produce a probability but cannot seed rows (ASM-51, §D.1): %r"
            % (tuple(restated),),
        )
        for name, row in restated.items():
            with self.subTest(source=name, path=True):
                self.assertIn(
                    ".probe/", str(row.get("path")),
                    "a row names the artefact's repository-relative path (ASM-51): %r"
                    % (row,),
                )
                self.assertFalse(
                    os.path.isabs(str(row.get("path"))),
                    "and it is repository-relative, so the tree stays relocatable "
                    "(ASM-51): %r" % (row,),
                )
                self.assertTrue(
                    os.path.isfile(J.resolve(str(row["path"]))),
                    "and the file the table names is the one the repository carries, so the "
                    "table is not prose about an artefact that is not there (ASM-51): %r"
                    % (row,),
                )


class StrengthWitnessTest(J.JoinCase):
    """TRN-9.4 — a declared member is not silently dropped, read at three sites."""

    def test_trn9_4_a_declared_strength_is_not_silently_dropped(self):
        """TRN-9.4 the spec handed to `agents.build_learner` carries the declared key, the
        encoder the loop built carries the member's tenth block -- its `observation_spec`'s
        width is 41 where the absence encoder's is 40 -- and the learner carries the member:
        three witnesses to one declaration, so no path can read the key and forget it
        (`ASM-46`, `ASM-48`, §C.3)."""
        loop = J.mod("training.loop")
        agents = J.mod("agents")
        features = J.mod("features")
        configuration = pair_configuration()
        configuration["variants"] = [
            token_arm(
                PAIR_DECLARING_ARM,
                strength=strength_names()[1],
                strength_source=tuple(restated_sources())[0],
            )
        ]
        entry = configuration["variants"][0]
        probe = features.load_strength(entry["strength_source"])
        seen = self.witnesses(loop, agents, configuration, entry, probe)
        spec = seen["spec"]
        self.assertIn(
            "strength", spec,
            "the spec the loop handed to `agents.build_learner` carries no `strength` key, "
            "so the declaration was read and dropped (ASM-46, §C.3): %r" % (sorted(spec),),
        )
        self.assertEqual(
            spec["strength"], strength_names()[1],
            "and it names the declared member (ASM-46): %r" % (spec.get("strength"),),
        )
        self.assertIn(
            "encoder", spec,
            "the spec carries the encoder the loop built for the variant (surface.md §4): "
            "%r" % (sorted(spec),),
        )
        declared = features.observation_spec(spec["encoder"])
        self.assertEqual(
            tuple(declared["shape"]), (41,),
            "the encoder was built **with** the member, so its declaration is the ten-block "
            "one -- 41 ids on the default shape where the absence encoder declares 40 -- "
            "which is the second witness (ASM-48, §A.4): %r"
            % (tuple(declared["shape"]),),
        )
        self.assertIn(
            "strength", tuple(declared["fields"]),
            "and its fields carry the tenth fact (ASM-46): %r" % (tuple(declared["fields"]),),
        )
        self.assertEqual(
            declared["vocabulary"], 110,
            "and its vocabulary is the widened 110 the token ladder needs (ASM-48): %r"
            % (declared.get("vocabulary"),),
        )
        self.assertEqual(
            getattr(seen["learner"], "strength", "<absent>"), strength_names()[1],
            "the learner carries the member the spec named -- the third witness (ASM-46): "
            "%r" % (getattr(seen["learner"], "strength", "<absent>"),),
        )
        # And the control: a variant declaring nothing carries none of it.
        quiet = copy.deepcopy(entry)
        for key in ("strength", "strength_source", "embedding_init"):
            quiet.pop(key, None)
        configuration["variants"] = [quiet]
        plain = self.witnesses(loop, agents, configuration, quiet, None)
        self.assertNotIn(
            "strength", plain["spec"],
            "a variant declaring no member forwards no key, so `agents` builds the "
            "catalogue's first and no default is substituted here (ASM-46): %r"
            % (sorted(plain["spec"]),),
        )
        self.assertEqual(
            tuple(features.observation_spec(plain["spec"]["encoder"])["shape"]), (40,),
            "and the encoder it built is the absence one -- 40 ids -- so the 41 above is "
            "the declaration's and not the loop's default (ASM-48): %r"
            % (tuple(features.observation_spec(plain["spec"]["encoder"])["shape"]),),
        )
        self.assertEqual(
            getattr(plain["learner"], "strength", "<absent>"), strength_names()[0],
            "and the learner it built reads the catalogue's first member (ASM-46): %r"
            % (getattr(plain["learner"], "strength", "<absent>"),),
        )

    @staticmethod
    def witnesses(loop, agents, configuration, entry, probe):
        """One `_train_variant_seed` pass, with the spec `agents.build_learner` was handed.

        The loop's step is driven directly so the **spec** is observable: `agents.save`'s
        container records the learner's members and the encoder's width, but not the record
        the loop built, and "the key was forwarded" is a statement about that record
        (`ASM-46`, §C.3).  The spy is put back in a `finally`, so no later case reads a
        patched module.
        """
        seen = {}
        original = agents.build_learner

        def spy(spec):
            seen["spec"] = dict(spec)
            learner = original(spec)
            seen["learner"] = learner
            return learner

        agents.build_learner = spy
        try:
            loop._train_variant_seed(
                configuration,
                entry,
                PAIR_SEED,
                PAIR_BUDGET,
                "cpu",
                shape=J.shape_names()[0],
                model=probe,
            )
        finally:
            agents.build_learner = original
        return seen


if __name__ == "__main__":  # pragma: no cover - a case file, run by pytest
    unittest.main()
