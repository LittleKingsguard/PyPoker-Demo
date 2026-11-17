"""AGT-19 — the fourth catalogue: the strength axis and its version-6 container.

``docs/L1/strength-design.md`` §C.1-§C.3, §D.4, §E and §F.2; ``ASM-46``, ``ASM-49``,
``ASM-50``; ``docs/L2/agents/surface.md`` §3-§4; ``docs/L3/agents/checkpoint.md`` §2.1-§3.

`strength` is a **fourth catalogue** and neither a rule, a utility nor a counterfactual: it
names what a learner reads as an **input**.  `none` -- the catalogue's first member and the
declared default -- is today's learner and today's container byte for byte; `supervised`
names a learner whose observation carries the frozen estimator's predicted win probability
as the encoder's tenth declared field, and whose embedding table may be seeded from that
estimator's card rows.

Each case here is one fact about the catalogue, the learner or the container:

* **AGT-19.1** the catalogue's two members, in order, each a record of a `name` and one
  stable `carries` token;
* **AGT-19.2** an uncatalogued member is refused by name, and an explicit `none` builds the
  byte-identical learner an absent key builds;
* **AGT-19.3** a declaring or seeded learner writes format version 6, with `strength`
  immediately after `counterfactual` and `seeding` immediately after it, and every older
  version refuses either field;
* **AGT-19.6** the parameter count a declaring token learner carries;
* **AGT-19.7** a seeded learner's two fields travel through save and load, a spec that
  disagrees is refused naming both values, and a declaring container with no seed is legal
  and distinguishable;
* **AGT-19.8** a policy carries both labels and no decision reads either;
* **AGT-19.9** the `sized_by_kind` width equality is version-scoped, both ways.

AGT-19.4 and AGT-19.5 -- the seed's exactness and its refusals -- are
``test_embedding_init.py``'s, because they are about the copy and not about the catalogue.
"""

import os
import unittest

import numpy

from _agents_support import (
    AgentsCase,
    container_document,
    features,
    learner_spec,
    plain_int,
    shape_encoder,
    write_container,
)

#: The two members, in the declared order, and the two `carries` tokens they state
#: (`ASM-46`, §C.1).  Written here so no case reads them back off the catalogue it checks.
MEMBERS = ("none", "supervised")
CARRIES = {
    "none": "no-model-input",
    "supervised": "predicted-win-probability",
}

#: The parameter counts the design fixes for a declaring token learner at width 50 and
#: depth 2 (§A.4, AGT-19.6): 110×50 + 2×(50² + 50) + A×50 + A, A the shape's head width.
DECLARING_COUNTS = {
    None: 10753,
    "six-seat-no-limit-100": 10906,
}

#: The absence learner's count at the same settings: the vocabulary 96's 10,053.
ABSENCE_COUNT = 10053


def strength_encoder(representation="card-tokens", shape=None, member="supervised"):
    """One encoder declaring -- or, with `member=None`, not declaring -- the tenth block."""
    return features().build_encoder(representation, shape=shape, strength=member)


def seeded_rows(width=50, offset=0.0):
    """`(52, width)` rows an `embedding_init` record can carry, distinct per index."""
    values = numpy.arange(52 * width, dtype=numpy.float64).reshape(52, width)
    return (values / 1000.0) + offset


class StrengthCatalogueTest(AgentsCase):
    """AGT-19.1 and AGT-19.2 — the catalogue and the declared default."""

    def test_agt19_1_the_catalogue_is_two_members_with_a_stable_carries_token(self):
        """AGT-19.1 `learners()['strengths']` is `none` then `supervised`, each a record of
        its `name` and one stable `carries` token with no whitespace and no sentence
        punctuation, and `none` is first because the declared default is derived from the
        order (`ASM-46`, §C.1)."""
        package = self.agents()
        catalogue = package.learners()["strengths"]
        self.assertEqual(
            tuple(catalogue), MEMBERS,
            "the strength catalogue is `none` then `supervised`, in that order, because "
            "the declared default is its first member and a reordering would change which "
            "learner an absent key builds (ASM-46, §C.1): %r" % (tuple(catalogue),),
        )
        for name, record in catalogue.items():
            with self.subTest(member=name):
                self.assertEqual(
                    tuple(record), ("name", "carries"),
                    "a strength member is a record of exactly two keys -- its `name` and "
                    "the token it `carries`, mirroring LEARNING_RULES' own spelling "
                    "(ASM-46, §C.1): %r" % (record,),
                )
                self.assertEqual(
                    record["name"], name,
                    "each member carries its own name (ASM-46): %r under %r"
                    % (record.get("name"), name),
                )
                token = record["carries"]
                self.assertIsInstance(
                    token, str,
                    "a member's `carries` is a string token (ASM-46): %r" % (token,),
                )
                self.assertEqual(
                    token, CARRIES[name],
                    "the member %r carries the token the design fixes, so a report can "
                    "name what a learner reads without quoting a sentence (ASM-46): %r"
                    % (name, token),
                )
                for bad in (" ", "\n", "\t", ".", ","):
                    with self.subTest(member=name, forbidden=bad):
                        self.assertNotIn(
                            bad, token,
                            "a `carries` token is a stable token and never a sentence "
                            "(ASM-46, rules.md §2): %r" % (token,),
                        )
        first = package.learners()["strengths"]
        second = package.learners()["strengths"]
        self.assertEqual(
            first, second,
            "two calls to learners() returned unequal strength catalogues, so the "
            "catalogue is state a caller can drift (ASM-46): %r" % (first,),
        )
        first["none"]["carries"] = "mutated"
        self.assertNotEqual(
            package.learners()["strengths"]["none"]["carries"], "mutated",
            "a caller's edit of a returned catalogue reached the next caller's, so the "
            "record is not rebuilt per call (ASM-46, guardrails.md G11)",
        )

    def test_agt19_2_an_uncatalogued_member_is_refused_and_none_is_the_same_learner(self):
        """AGT-19.2 a spec naming a member outside the catalogue -- or a value that is not a
        string -- is refused naming the value and the declared members and is never mapped
        onto the default, while a spec naming `none` explicitly builds the byte-identical
        learner an absent key builds (`param_count` and the whole `2·P` array compared)
        (`ASM-46`, §C.1, errors.md §3)."""
        package = self.agents()
        for value in (
            "strength", "Supervised", "SUPERVISED", " supervised", "on", "off",
            "attn-60", True, 1, 0, ("supervised",), {"member": "supervised"},
        ):
            with self.subTest(value=value):
                spec = learner_spec(kind="token-embedding", width=8, depth=1)
                spec["strength"] = value
                self.assert_agents_refusal(
                    package.build_learner,
                    spec,
                    entry="build_learner",
                    groups=(
                        ("strength",),
                        (repr(value),),
                        ("none",),
                        ("supervised",),
                    ),
                    label="a spec naming the uncatalogued strength member %r" % (value,),
                )
        quiet = package.build_learner(learner_spec(kind="token-embedding", width=8, depth=1))
        named = package.build_learner(
            learner_spec(kind="token-embedding", width=8, depth=1, extra={"strength": "none"})
        )
        self.assertEqual(
            plain_int(package.param_count(quiet), "param_count"),
            plain_int(package.param_count(named), "param_count"),
            "a learner built under the declared default and one built under an explicit "
            "`none` are one learner: the member owns no parameter (ASM-46, ASM-10)",
        )
        self.assertEqual(
            getattr(quiet, "strength", "<absent>"), "none",
            "a learner naming no member carries the catalogue's first, which is the "
            "declared default (ASM-46): %r" % (getattr(quiet, "strength", "<absent>"),),
        )
        self.assertEqual(
            getattr(named, "strength", "<absent>"), "none",
            "a learner naming `none` carries it (ASM-46): %r"
            % (getattr(named, "strength", "<absent>"),),
        )
        self.assertEqual(
            getattr(named, "seeding", "<absent>"), None,
            "a learner that was not seeded carries no seed record, so 'strength-fed' and "
            "'seeded' can never be confused (ASM-49): %r"
            % (getattr(named, "seeding", "<absent>"),),
        )
        backend = getattr(quiet, "backend", None)
        self.assertIsNotNone(
            backend, "a learner carries the backend module it computes with (backends.md §4)"
        )
        first = backend.parameters(quiet.state)
        second = backend.parameters(named.state)
        self.assertEqual(
            first.shape, second.shape,
            "the two learners carry arrays of one length (ASM-46): %r against %r"
            % (first.shape, second.shape),
        )
        self.assertTrue(
            numpy.array_equal(first, second),
            "the whole `2·P` array of a learner built under an explicit `none` differs "
            "from an absent key's, so the declared default is not the absence's learner "
            "(ASM-46): %d of %d values differ"
            % (int(numpy.count_nonzero(first != second)), first.size),
        )


class StrengthContainerTest(AgentsCase):
    """AGT-19.3, AGT-19.6 and AGT-19.9 — the container and its counts."""

    def declaring(self, shape=None, width=50, depth=2, extra=None, backend="numpy"):
        """One token learner of a declaring encoder, at the width the design fixes."""
        package = self.agents()
        settings = {"strength": "supervised"}
        settings.update(extra or {})
        return package.build_learner(
            learner_spec(
                backend=backend,
                kind="token-embedding",
                width=width,
                depth=depth,
                game=shape,
                encoder=strength_encoder("card-tokens", shape),
                extra=settings,
            )
        )

    @staticmethod
    def as_version(metadata, version):
        """One document in another format version's form (`checkpoint.md` §2.1, §3).

        A version-3 or version-4 container carries no `counterfactual` and no version-6
        field; a version-5 one requires `counterfactual` and refuses `game` for the default
        shape.  The document is rebuilt rather than edited, so an older-version case asserts
        that version's form and not a half-written file.
        """
        record = dict(metadata)
        for field in ("strength", "seeding", "game"):
            record.pop(field, None)
        if version in (3, 4):
            record.pop("counterfactual", None)
        if version == 5:
            record["counterfactual"] = "reveal-counterfactual"
        record["format_version"] = int(version)
        return record

    def test_agt19_3_a_declaring_or_seeded_learner_writes_version_six(self):
        """AGT-19.3 a learner that declares a strength member or was seeded writes format
        version 6, recording `strength` immediately after `counterfactual` and `seeding`
        immediately after it; a `none` and unseeded learner still writes 3 on the default
        shape, 4 on another and 5 when its counterfactual member is revealed; a seed alone
        is version 6 with no `strength` field; and a version 1-to-5 container carrying
        either field is refused by name (`ASM-49`, `ASM-50`, §E.1)."""
        package = self.agents()
        folder = self.tempdir()
        learner = self.declaring(
            extra={
                "counterfactual": "reveal-counterfactual",
                "embedding_init": {"source": "attn-60", "rows": seeded_rows()},
            }
        )
        path = package.save(learner, os.path.join(folder, "v6.ckpt"))
        metadata, parameters = container_document(path)
        self.assertEqual(
            plain_int(metadata["format_version"], "format_version"), 6,
            "a learner that declares a strength member writes format version 6 -- the era "
            "boundary §E.1 draws -- and this container records %r"
            % (metadata.get("format_version"),),
        )
        keys = list(metadata)
        for field in ("counterfactual", "strength", "seeding"):
            self.assertIn(
                field, keys,
                "a version-6 container of this learner carries %r (ASM-49, ASM-50): %r"
                % (field, keys),
            )
        self.assertEqual(
            keys[keys.index("counterfactual") + 1], "strength",
            "`strength` is recorded immediately after `counterfactual`, in §2.1's order "
            "(ASM-50): %r" % (keys,),
        )
        self.assertEqual(
            keys[keys.index("strength") + 1], "seeding",
            "`seeding` is recorded immediately after `strength` (ASM-49, ASM-50): %r"
            % (keys,),
        )
        self.assertEqual(
            metadata["strength"], "supervised",
            "the container records the member its learner reads (ASM-46): %r"
            % (metadata.get("strength"),),
        )
        self.assertEqual(
            tuple(metadata["seeding"]),
            ("source", "rows", "width", "space", "digest"),
            "the seed record carries §2.1's five keys, in that order (ASM-49): %r"
            % (metadata.get("seeding"),),
        )
        self.assertEqual(
            metadata["seeding"]["source"], "attn-60",
            "the seed record names the source it copied (ASM-49): %r"
            % (metadata.get("seeding"),),
        )
        self.assertEqual(
            metadata["seeding"]["space"], "parameter",
            "the copy is written in parameter space, and the record says so (ASM-49, §D.3): "
            "%r" % (metadata.get("seeding"),),
        )
        digest = metadata["seeding"]["digest"]
        self.assertIsInstance(digest, str, "the digest is a string (ASM-49): %r" % (digest,))
        self.assertEqual(
            len(digest), 16,
            "the digest is sixteen hexadecimal characters (ASM-49, §E.1): %r" % (digest,),
        )
        for character in digest:
            self.assertIn(
                character, "0123456789abcdef", "the digest is hexadecimal: %r" % (digest,)
            )
        self.assertEqual(
            plain_int(metadata["params"]["count"], "params.count"),
            plain_int(package.param_count(learner), "param_count"),
            "the recorded count is the learner's own (checkpoint.md §2.1): %r"
            % (metadata["params"]["count"],),
        )
        # The absence arms still write the versions they always wrote.
        plain = package.build_learner(
            learner_spec(kind="token-embedding", width=8, depth=1)
        )
        self.assertEqual(
            plain_int(
                container_document(
                    package.save(plain, os.path.join(folder, "v3.ckpt"))
                )[0]["format_version"],
                "format_version",
            ),
            3,
            "a `none` and unseeded learner of the default shape still writes version 3, so "
            "no shipped container moves (ASM-50, D-61)",
        )
        other = package.build_learner(
            learner_spec(
                kind="token-embedding",
                width=8,
                depth=1,
                game="six-seat-no-limit-100",
                encoder=shape_encoder("card-tokens", "six-seat-no-limit-100"),
            )
        )
        other_metadata = container_document(
            package.save(other, os.path.join(folder, "v4.ckpt"))
        )[0]
        self.assertEqual(
            plain_int(other_metadata["format_version"], "format_version"), 4,
            "a `none` and unseeded learner of another shape still writes version 4 "
            "(ASM-50, shapes.md §5): %r" % (other_metadata.get("format_version"),),
        )
        revealed = package.build_learner(
            learner_spec(
                kind="token-embedding",
                width=8,
                depth=1,
                extra={"counterfactual": "reveal-counterfactual"},
            )
        )
        revealed_metadata = container_document(
            package.save(revealed, os.path.join(folder, "v5.ckpt"))
        )[0]
        self.assertEqual(
            plain_int(revealed_metadata["format_version"], "format_version"), 5,
            "a learner whose counterfactual member is revealed and declares no strength "
            "still writes version 5 (ASM-50, counterfactual.md §6): %r"
            % (revealed_metadata.get("format_version"),),
        )
        self.assertNotIn(
            "strength", revealed_metadata,
            "a version-5 container carries no strength field (ASM-50): %r"
            % (sorted(revealed_metadata),),
        )
        # A `none` member with a seed is still version 6: the seed alone is the boundary.
        seeded_only = self.declaring(
            width=8, depth=1,
            extra={
                "strength": "none",
                "embedding_init": {"source": "attn-60", "rows": seeded_rows(8)},
            },
        )
        seeded_metadata = container_document(
            package.save(seeded_only, os.path.join(folder, "v6-seed.ckpt"))
        )[0]
        self.assertEqual(
            plain_int(seeded_metadata["format_version"], "format_version"), 6,
            "a learner whose embedding table was seeded writes version 6 whether or not it "
            "declares a member, because the seed is the other half of §E.1's boundary "
            "(ASM-49, ASM-50): %r" % (seeded_metadata.get("format_version"),),
        )
        self.assertNotIn(
            "strength", seeded_metadata,
            "and it records no `strength` field, because its member is the declared "
            "default: within version 6 each field's presence is its own condition "
            "(ASM-49, ASM-50): %r" % (sorted(seeded_metadata),),
        )
        self.assertIn(
            "seeding", seeded_metadata,
            "the seed record is what makes the container a version-6 one (ASM-50): %r"
            % (sorted(seeded_metadata),),
        )
        # And versions 1-5 refuse either field by name: no writer of those versions wrote
        # one, so a file carrying one was edited (`checkpoint.md` §3, ASM-50).
        for version in (3, 4, 5):
            for field, value in (
                ("strength", "supervised"),
                ("seeding", dict(metadata["seeding"])),
            ):
                with self.subTest(version=version, field=field):
                    recorded = self.as_version(metadata, version)
                    recorded[field] = value
                    doctored = write_container(
                        os.path.join(folder, "doctored-%d-%s.ckpt" % (version, field)),
                        recorded,
                        parameters,
                    )
                    self.assert_agents_refusal(
                        package.load,
                        None,
                        doctored,
                        entry="load",
                        groups=((field,),),
                        label="a format version %d container carrying the field %r"
                        % (version, field),
                    )

    def test_agt19_6_the_declaring_token_learner_counts_the_widened_vocabulary(self):
        """AGT-19.6 a strength-on token learner at width 50 and depth 2 reports **10,753**
        on the default shape and **10,906** at six seats -- the 700-parameter difference the
        vocabulary's 96 to 110 makes -- and the recorded `params.count` is that number;
        the absence learner at the same settings is still 10,053 (`ASM-48`, §A.4)."""
        package = self.agents()
        folder = self.tempdir()
        for shape, wanted in DECLARING_COUNTS.items():
            learner = self.declaring(shape=shape)
            with self.subTest(shape=shape):
                self.assertEqual(
                    plain_int(package.param_count(learner), "param_count"), wanted,
                    "a declaring token learner's count is the input block at the widened "
                    "vocabulary 110, the trunk, and the shape's head -- %d here, and the "
                    "count the design fixes (ASM-48, §A.4): %r"
                    % (wanted, package.param_count(learner)),
                )
                path = package.save(
                    learner, os.path.join(folder, "count-%s.ckpt" % (shape or "default",))
                )
                self.assertEqual(
                    plain_int(container_document(path)[0]["params"]["count"], "params.count"),
                    wanted,
                    "the container records the count its geometry gives, so a reader holds "
                    "the widened table to it (ASM-48, checkpoint.md §2.1): %r"
                    % (container_document(path)[0]["params"]["count"],),
                )
        quiet = package.build_learner(
            learner_spec(kind="token-embedding", width=50, depth=2)
        )
        self.assertEqual(
            plain_int(package.param_count(quiet), "param_count"), ABSENCE_COUNT,
            "the absence learner's count is today's -- the vocabulary 96 gives 10,053 -- so "
            "the 700 above is the widened block and nothing else (ASM-48, §A.4)",
        )

    def test_agt19_9_the_width_equality_is_version_scoped(self):
        """AGT-19.9 a version-6 container loads at its own widened size --
        `representation.size` 110 on the default shape, which the kind's declared 96
        contradicts -- while a version-3 container whose `representation.size` was doctored
        is still refused naming the field and both numbers, so the exemption is
        version-scoped and not a dropped check (`ASM-50`, §E.2)."""
        package = self.agents()
        folder = self.tempdir()
        learner = self.declaring(width=8, depth=1)
        path = package.save(learner, os.path.join(folder, "v6-token.ckpt"))
        metadata, parameters = container_document(path)
        self.assertEqual(
            plain_int(metadata["format_version"], "format_version"), 6,
            "this case's subject is a version-6 container (ASM-50): %r"
            % (metadata.get("format_version"),),
        )
        self.assertEqual(
            plain_int(metadata["representation"]["size"], "representation.size"), 110,
            "a declaring token learner on the default shape is sized by the widened "
            "vocabulary 110 (ASM-48): %r" % (metadata["representation"]["size"],),
        )
        restored = package.load(None, path)
        self.assertEqual(
            plain_int(package.param_count(restored), "param_count"),
            plain_int(package.param_count(learner), "param_count"),
            "a version-6 container loads at its own widened size, which is the exemption "
            "§E.2 states -- the kind's declared 96 does not refuse it (ASM-50)",
        )
        # ... and the same geometry recorded at the declared width is still refused.
        quiet = package.build_learner(learner_spec(kind="token-embedding", width=8, depth=1))
        plain_path = package.save(quiet, os.path.join(folder, "v3-token.ckpt"))
        plain_metadata, plain_parameters = container_document(plain_path)
        self.assertEqual(
            plain_int(plain_metadata["format_version"], "format_version"), 3,
            "the control is a version-3 container of the same kind (ASM-50): %r"
            % (plain_metadata.get("format_version"),),
        )
        recorded = dict(plain_metadata)
        recorded["representation"] = dict(plain_metadata["representation"])
        recorded["representation"]["size"] = 110
        doctored = write_container(
            os.path.join(folder, "v3-doctored.ckpt"), recorded, plain_parameters
        )
        self.assert_agents_refusal(
            package.load,
            None,
            doctored,
            entry="load",
            groups=(("representation.size",), ("96",), ("110",)),
            label="a version-3 container recording the declaring vocabulary 110",
        )


class StrengthSeedingRoundTripTest(AgentsCase):
    """AGT-19.7 and AGT-19.8 — the record travels, and no decision reads it."""

    def seeded(self, backend="numpy", width=8, depth=1, shape=None, rows=None):
        """One declaring, seeded learner at a small width so a case stays cheap."""
        package = self.agents()
        return package.build_learner(
            learner_spec(
                backend=backend,
                kind="token-embedding",
                width=width,
                depth=depth,
                game=shape,
                encoder=strength_encoder("card-tokens", shape),
                extra={
                    "strength": "supervised",
                    "embedding_init": {
                        "source": "attn-60",
                        "rows": seeded_rows(width) if rows is None else rows,
                    },
                },
            )
        )

    def test_agt19_7_the_two_fields_travel_and_a_spec_that_disagrees_is_refused(self):
        """AGT-19.7 a seeded learner saved and loaded restores `strength` and `seeding`
        (`source`, `digest`, `rows`, `width`, `space`) byte for byte; `load(spec)` compares
        both against the file and refuses a disagreement naming both values; and a container
        that carries `strength: supervised` with no `seeding` is **legal and
        distinguishable**, so a strength-fed learner and a seeded one are never confused
        (`ASM-46`, `ASM-49`, `ASM-50`)."""
        package = self.agents()
        folder = self.tempdir()
        learner = self.seeded()
        path = package.save(learner, os.path.join(folder, "seeded.ckpt"))
        metadata, _parameters = container_document(path)
        restored = package.load(None, path)
        self.assertEqual(
            getattr(restored, "strength", "<absent>"),
            getattr(learner, "strength", "<absent>"),
            "the restored learner's strength member is the saved one's (ASM-50): %r "
            "against %r"
            % (getattr(restored, "strength", "<absent>"),
               getattr(learner, "strength", "<absent>")),
        )
        self.assertEqual(
            dict(getattr(restored, "seeding", {}) or {}),
            dict(getattr(learner, "seeding", {}) or {}),
            "the restored learner's seed record is the saved one's, byte for byte "
            "(ASM-49): %r against %r"
            % (getattr(restored, "seeding", "<absent>"),
               getattr(learner, "seeding", "<absent>")),
        )
        for key in ("source", "rows", "width", "space", "digest"):
            with self.subTest(key=key):
                self.assertEqual(
                    getattr(learner, "seeding")[key], metadata["seeding"][key],
                    "the learner's seed record and the container's are one statement, and "
                    "%r differs (ASM-49): %r against %r"
                    % (key, getattr(learner, "seeding")[key], metadata["seeding"][key]),
                )
        spec = learner_spec(
            kind="token-embedding",
            width=8,
            depth=1,
            encoder=strength_encoder("card-tokens"),
            extra={"strength": "supervised"},
        )
        self.assertEqual(
            plain_int(package.param_count(package.load(spec, path)), "param_count"),
            plain_int(package.param_count(learner), "param_count"),
            "a spec that declares the container's own member loads it (ASM-50)",
        )
        disagreeing = dict(spec)
        disagreeing["strength"] = "none"
        self.assert_agents_refusal(
            package.load, disagreeing, path, entry="load",
            groups=(("strength",), ("none",), ("supervised",)),
            label="a spec naming the member a version-6 container does not record",
        )
        wrong_seed = dict(spec)
        wrong_seed["seeding"] = {
            "source": "attn-400",
            "rows": "cards",
            "width": 8,
            "space": "parameter",
            "digest": "0000000000000000",
        }
        self.assert_agents_refusal(
            package.load, wrong_seed, path, entry="load",
            groups=(("seeding",), ("attn-400",), ("attn-60",)),
            label="a spec naming a seed the container does not record",
        )
        # The anti-confusion half: a declaring container with no seed is legal.
        declaring = package.build_learner(
            learner_spec(
                kind="token-embedding",
                width=8,
                depth=1,
                encoder=strength_encoder("card-tokens"),
                extra={"strength": "supervised"},
            )
        )
        unseeded = package.save(declaring, os.path.join(folder, "unseeded.ckpt"))
        unseeded_metadata, _unseeded_parameters = container_document(unseeded)
        self.assertEqual(
            plain_int(unseeded_metadata["format_version"], "format_version"), 6,
            "a declaring learner with no seed is still a version-6 container (ASM-50): %r"
            % (unseeded_metadata.get("format_version"),),
        )
        self.assertEqual(
            unseeded_metadata.get("strength"), "supervised",
            "and it records the member it reads (ASM-50): %r"
            % (unseeded_metadata.get("strength"),),
        )
        self.assertNotIn(
            "seeding", unseeded_metadata,
            "and no seed record, so a declaring container and a seeded one are "
            "distinguishable facts and not one (ASM-49, ASM-50): %r"
            % (sorted(unseeded_metadata),),
        )
        self.assertEqual(
            getattr(package.load(None, unseeded), "seeding", "<absent>"), None,
            "the restored unseeded learner carries no seed record (ASM-49): %r"
            % (getattr(package.load(None, unseeded), "seeding", "<absent>"),),
        )

    def test_agt19_8_a_policy_carries_both_labels_and_no_decision_reads_them(self):
        """AGT-19.8 `as_policy`'s policy carries `strength` and `seeding`, and neither is
        read by a decision: the same decision at the same mask on the same learner, with and
        without the labels, is one answer (`ASM-46`, `ASM-49`, `e2e-surface.md` §2)."""
        package = self.agents()
        encoder = strength_encoder("card-tokens")
        learner = self.seeded()
        policy = package.as_policy(learner, encoder, 0, "off")
        self.assertEqual(
            getattr(policy, "strength", "<absent>"), "supervised",
            "the policy carries the member its learner read (ASM-46): %r"
            % (getattr(policy, "strength", "<absent>"),),
        )
        self.assertEqual(
            dict(getattr(policy, "seeding", {}) or {}),
            dict(getattr(learner, "seeding", {}) or {}),
            "and the seed record, so a table can name what it was fed (ASM-49): %r"
            % (getattr(policy, "seeding", "<absent>"),),
        )
        for label in ("learning_rule", "utility", "counterfactual", "game"):
            with self.subTest(label=label):
                self.assertIsNotNone(
                    getattr(policy, label, None),
                    "the policy keeps the four labels it already carried beside the two "
                    "new ones (e2e-surface.md §2, rules.md §7, utilities.md §7, "
                    "counterfactual.md §6): %r is absent" % (label,),
                )
        readout = self.strength_readout()
        legal = ("fold", "check-call")
        before = policy(readout, legal)
        policy.strength = "none"
        policy.seeding = None
        after = policy(readout, legal)
        self.assertEqual(
            before, after,
            "a policy whose strength and seeding labels were replaced decided differently, "
            "so a decision reads a label it must only carry (ASM-46, ASM-49, rules.md §7)",
        )

    @staticmethod
    def strength_readout():
        """One invented readout carrying the injected tenth fact and the mask's `legal`."""
        return {
            "street": "preflop",
            "seat": (0, True),
            "hole": ("Td", "2c"),
            "board": (),
            "stacks": (100, 100),
            "pot": 3,
            "to_call": 2,
            "limit": (2, 0),
            "history": [],
            "legal": ("fold", "check-call"),
            "hand_class": None,
            "strength": 0.37,
        }


if __name__ == "__main__":  # pragma: no cover - a case file, run by pytest
    unittest.main()
