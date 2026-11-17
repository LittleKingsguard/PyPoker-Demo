"""EVL-12.1 — a strength member is played from its own container, and its input is produced.

``docs/L1/strength-design.md`` §B.3 site 4, §E.3 and §F.2; ``ASM-46``, ``ASM-47``,
``ASM-49``, ``ASM-50``; ``docs/L2/evaluation/surface.md`` §12; ``docs/L3/evaluation/
scheduler.md`` §5.1, §6.

A container written by a learner that declares a strength member was trained on an
observation carrying the encoder's **tenth declared field**, so `policy_from` has to do two
things a reader of an older container does not: build the encoder **with** the member the
container records -- the fourth recorded fact -- and produce the value the readout the cell
hands it does not carry.  The estimator's own name is the container's `seeding.source`, and
a container recording a member whose value cannot be produced is refused by name rather than
encoded into an observation the encoder will reject.

One case, and its three halves:

* the encoder `policy_from` builds is the declaring one, and its policy decides on a readout
  that carries the eleven readout facts and **no** `strength` key;
* a version-6 container whose `strength` field was removed is refused where the container is
  read, because a version-6 container requires one of its two fields;
* a container recording a member and no seed names no estimator, and is refused naming both
  facts instead of substituting one.

The containers this case reads are ones `agents.save` wrote into a scratch directory, so no
shipped artefact is touched (`surface.md` §8, `module-map.md` §5).
"""

import json
import os
import unittest
import zipfile

from _evaluation_support import EvaluationCase, agents, features

#: The eleven readout facts a cell's policy is handed, and nothing else (ASM-30): the
#: `strength` key is the one an encoder's blocks declare and a readout does not carry
#: (`ASM-46`).
READOUT_FACTS = (
    "street",
    "seat",
    "hole",
    "board",
    "stacks",
    "pot",
    "to_call",
    "limit",
    "history",
    "legal",
    "hand_class",
)


def declaring_learner(seeded=True, backend="numpy", width=8, depth=1):
    """One token learner that declares a strength member, seeded or not (`ASM-46`, §D.2)."""
    package = agents()
    import numpy

    encoder = features().build_encoder("card-tokens", strength="supervised")
    spec = {
        "backend": backend,
        "architecture": {"kind": "token-embedding", "width": width, "depth": depth},
        "seed": 4241,
        "encoder": encoder,
        "strength": "supervised",
    }
    if seeded:
        rows = numpy.arange(52 * width, dtype=numpy.float64).reshape(52, width) / 1000.0
        spec["embedding_init"] = {"source": source_name(), "rows": rows}
    return package.build_learner(spec)


def source_name():
    """The first declared source, read off `features`' own table (`ASM-51`)."""
    return tuple(features().cardmodel.STRENGTH_SOURCES)[0]


def container_document(path):
    """`(metadata, parameters)` of one checkpoint (`checkpoint.md` §2)."""
    with zipfile.ZipFile(path) as archive:
        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        parameters = archive.read("parameters.npy")
    return metadata, parameters


def write_container(target, metadata, parameters):
    """Write one container with `metadata` and the array's own bytes."""
    with open(target, "wb") as handle:
        with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_STORED) as archive:
            archive.writestr("metadata.json", json.dumps(metadata).encode("utf-8"))
            archive.writestr("parameters.npy", parameters)
    return target


def probe_readout(tag=0):
    """One invented readout carrying the eleven facts and **no** `strength` key."""
    return {
        "street": "preflop",
        "seat": (0, True),
        "hole": ("Td", "2c") if tag % 2 == 0 else ("As", "Ad"),
        "board": (),
        "stacks": (100, 100),
        "pot": 3,
        "to_call": 2,
        "limit": (2, 0),
        "history": [],
        "legal": ("fold", "check-call"),
        "hand_class": None,
    }


class StrengthPolicyFromTest(EvaluationCase):
    """EVL-12.1 — the fourth recorded fact, read and used."""

    def saved(self, seeded=True, name="strength-arm"):
        """One declaring learner's container in a scratch directory, and its metadata."""
        folder = self.tempdir()
        path = agents().save(
            declaring_learner(seeded=seeded), os.path.join(folder, name + ".ckpt")
        )
        metadata, parameters = container_document(path)
        return path, metadata, parameters, folder

    def test_evl12_1_policy_from_builds_the_encoder_with_the_recorded_member(self):
        """EVL-12.1 `policy_from` of a strength-arm checkpoint builds the encoder **with**
        the recorded member and its policy **decides** on a readout that carries the eleven
        facts and no `strength` key -- which is only possible if the encoder declares the
        tenth field and the frozen estimator supplied the value (`ASM-46`, `ASM-47`, §B.3
        site 4)."""
        path, metadata, _parameters, _folder = self.saved()
        self.assertEqual(
            metadata.get("strength"), "supervised",
            "this case's subject is a container recording the member (§E.1): %r"
            % (metadata.get("strength"),),
        )
        self.assertEqual(
            metadata.get("format_version"), 6,
            "and one written as a version-6 container (§E.1): %r"
            % (metadata.get("format_version"),),
        )
        self.assertIn(
            "seeding", metadata,
            "with the seed record that names the estimator its input came from (`ASM-49`): "
            "%r" % (sorted(metadata),),
        )
        readout = probe_readout()
        self.assertEqual(
            tuple(readout), READOUT_FACTS,
            "this case's readout carries the eleven readout facts and nothing else, which "
            "is the property `ASM-46` keeps (ASM-30): %r" % (tuple(readout),),
        )
        self.assertNotIn(
            "strength", readout,
            "and no `strength` key, so the value is the policy's to produce (`ASM-47`): %r"
            % (sorted(readout),),
        )
        policy = self.evaluation().policy_from(path, exploration="off")
        answer = policy(readout, readout["legal"])
        self.assertIn(
            answer, readout["legal"],
            "the policy decides for a readout that carries no strength, which it can only "
            "do by building the declaring encoder and injecting the recorded estimator's "
            "value (`ASM-47`, §B.3 site 4): %r" % (answer,),
        )
        self.assertEqual(
            policy.learning_rule, metadata.get("learning_rule"),
            "the side reports the rule its container records, read off the policy the "
            "module built (`rules.md` §6, D-19): %r" % (policy.learning_rule,),
        )
        self.assertEqual(
            policy.utility, metadata.get("utility"),
            "and the utility, on the same terms (`utilities.md` §6, D-20): %r"
            % (policy.utility,),
        )
        self.assertEqual(
            int(policy.params),
            int(agents().param_count(agents().load(None, path))),
            "and the capacity its container's learner measures (`scheduler.md` §5, "
            "ASM-10): %r" % (policy.params,),
        )
        # The value really was injected: the declaring encoder refuses this very readout
        # bare, so the policy's answer above is the injection's and not a readout that
        # happened to carry the field (`ASM-46`, `ASM-47`, §E.3).
        declaring = features().build_encoder("card-tokens", strength="supervised")
        with self.assertRaises(Exception) as caught:
            features().encode(declaring, readout)
        self.assertIn(
            "strength", str(caught.exception).lower(),
            "a declaring encoder refuses this readout bare, so the answer the policy gave "
            "is the injection's (ASM-47): %r" % (str(caught.exception),),
        )

    def test_evl12_1b_a_version_six_container_without_either_field_is_refused(self):
        """EVL-12.1 (second half) a version-6 container whose `strength` field was removed
        is refused where the container is read -- a version-6 container requires at least
        one of its two fields -- so the fourth recorded fact cannot be dropped into
        silence (`ASM-50`, §E.1)."""
        path, metadata, parameters, folder = self.saved(seeded=False, name="unseeded-arm")
        self.assertEqual(
            metadata.get("format_version"), 6,
            "the unseeded declaring learner's container is a version-6 one on its member "
            "alone (`ASM-50`): %r" % (metadata.get("format_version"),),
        )
        self.assertIn("strength", metadata, "and it records the member (`ASM-50`)")
        self.assertNotIn(
            "seeding", metadata,
            "and carries no seed record, so removing the member leaves neither field "
            "(`ASM-49`, `ASM-50`): %r" % (sorted(metadata),),
        )
        doctored_metadata = dict(metadata)
        doctored_metadata.pop("strength")
        doctored = write_container(
            os.path.join(folder, "no-strength.ckpt"), doctored_metadata, parameters
        )
        with self.assertRaises(Exception) as caught:
            self.evaluation().policy_from(doctored, exploration="off")
        message = str(caught.exception).lower()
        for wanted in ("format version 6", "strength", "seeding"):
            self.assertIn(
                wanted,
                message,
                "the refusal names the version and both fields a version-6 container "
                "requires one of (`ASM-50`, §E.1): %r" % (str(caught.exception),),
            )

    def test_evl12_1c_a_member_with_no_recorded_source_is_refused_by_name(self):
        """EVL-12.1 (third half) a container that records a member and **no** seed names no
        estimator, so `policy_from` refuses it naming both facts rather than substituting
        one -- the value cannot be produced, and a substituted estimator would play a member
        its container never recorded (`ASM-47`, `ASM-49`)."""
        path, metadata, _parameters, _folder = self.saved(
            seeded=False, name="unseeded-source-arm"
        )
        self.assertEqual(
            metadata.get("strength"), "supervised",
            "this case's subject records the member (`ASM-46`): %r"
            % (metadata.get("strength"),),
        )
        self.assertNotIn(
            "seeding", metadata,
            "and no seed, so no estimator is named (`ASM-49`): %r" % (sorted(metadata),),
        )
        with self.assertRaises(Exception) as caught:
            self.evaluation().policy_from(path, exploration="off")
        message = str(caught.exception).lower()
        for wanted in ("supervised", "seeding.source"):
            self.assertIn(
                wanted,
                message,
                "the refusal names the member and the missing record, so a caller reads "
                "which declaration is incomplete (`ASM-47`, `ASM-49`): %r"
                % (str(caught.exception),),
            )


if __name__ == "__main__":  # pragma: no cover - a case file, run by pytest
    unittest.main()
