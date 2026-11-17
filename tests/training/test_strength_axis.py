"""TRN-9.1 — the fourth axis' declarations are judged before the pool and before a hand.

``docs/L1/strength-design.md`` §C.2-§C.3; ``ASM-46``, ``ASM-49``, ``ASM-51``;
``docs/L2/training/declarations.md`` §2-§4; ``docs/L3/training/errors.md`` §2-§4.

`strength` is a **catalogue axis** and `strength_source` and `embedding_init` are **spec
keys**, and the trap this file is about is the one the design names: a key that is read here
*and* forwarded there can be silently dropped by either side.  So each declaration is judged
at the configuration and at each entry, before the pool is frozen, before a learner is built
and before the first hand:

* an uncatalogued member -- or a member that is not a string -- is `IgnoredDeclaration`
  naming the level, the value and the catalogue;
* a `strength_source` declared beside the catalogue's **first** member and no
  `embedding_init` is a declaration the run would not use, refused as the `_check_hyper`
  precedent refuses one;
* a member other than the default, or a seed, with **no** `strength_source` at all is
  refused too -- the other direction of the same rule;
* an `embedding_init` on a `flat-numeric` variant, of a source the table does not carry, of
  a `rows` selector the table does not declare, or naming a different source than
  `strength_source` is refused by name.

Every case here is a **declaration** case: none of them deals a hand, and
`check_declarations` is driven directly, so the file costs nothing and asserts the layer
that runs first (`docs/L3/training/loop.md` §1 step 1).
"""

import unittest

import _training_support as S
from _training_support import (
    TrainingCase,
    custom_configuration,
    with_setting,
)

#: An invented configuration's labels (`docs/L1/battery.md` §4, D-15): the axis is the only
#: thing these cases vary, and the member and source names are the declared ones.
RUNG = "rung-invented-strength-5601"
VARIANT = "variant-invented-strength-5601"
POOL = "pool-invented-strength-5601"

#: The two declared sources, in the declared order, and the rows selector (`ASM-51`).
SOURCES = ("attn-60", "attn-400")
ROWS = "cards"


def checks():
    """`training.declarations.check_declarations`, the layer these cases drive."""
    return S.internal("declarations", "check_declarations")


def token_configuration(**settings):
    """A one-variant `card-tokens` configuration whose only declaration is `settings`."""
    configuration = custom_configuration(name=RUNG, variant=VARIANT, pool_id=POOL)
    entry = dict(S.variant_entries(configuration)[0])
    entry["backend"] = "torch"
    entry["encoding"] = "card-tokens"
    entry["architecture"] = {
        "kind": "token-embedding",
        "width": 50,
        "depth": 2,
        "sparsity": 0.0,
        "residual": False,
    }
    configuration["variants"] = [with_setting(entry, **settings)]
    configuration["primary"] = VARIANT
    return configuration


def dense_configuration(**settings):
    """The same configuration on the dense encoding, for the seed's family refusal."""
    configuration = custom_configuration(name=RUNG, variant=VARIANT, pool_id=POOL)
    configuration["variants"] = [
        with_setting(S.variant_entries(configuration)[0], **settings)
    ]
    configuration["primary"] = VARIANT
    return configuration


class StrengthMemberTest(TrainingCase):
    """TRN-9.1's member half — the catalogue, at both levels."""

    def test_trn9_1a_an_uncatalogued_member_is_refused_at_either_level(self):
        """TRN-9.1 an uncatalogued `strength` member, or one that is not a string, is
        `IgnoredDeclaration` naming the level, the value and the catalogue `agents
        .learners()` publishes — at the configuration and at each entry — so the key can
        never be silently dropped (`ASM-46`, §C.3, errors.md §3-§4)."""
        catalogue = S.agents().learners()["strengths"]
        self.assertEqual(
            tuple(catalogue), ("none", "supervised"),
            "the catalogue this case judges against is the declared one (ASM-46): %r"
            % (tuple(catalogue),),
        )
        for value in ("strength", "Supervised", "on", "off", "attn-60", True, 1):
            with self.subTest(level="configuration", value=value):
                configuration = token_configuration()
                configuration["strength"] = value
                self.refuse(
                    lambda configuration=configuration: checks()(configuration),
                    "IgnoredDeclaration",
                    groups=(("strength",), (repr(value),), ("none",), ("supervised",)),
                    label="a configuration declaring the uncatalogued member %r" % (value,),
                )
            with self.subTest(level="entry", value=value):
                configuration = token_configuration(strength=value)
                self.refuse(
                    lambda configuration=configuration: checks()(configuration),
                    "IgnoredDeclaration",
                    groups=(("strength",), (repr(value),), ("none",), ("supervised",)),
                    label="a variant entry declaring the uncatalogued member %r" % (value,),
                )

    def test_trn9_1b_the_two_catalogued_members_are_accepted(self):
        """TRN-9.1 (control) both catalogued members pass the declaration check — the
        declared default `none` with no source, and `supervised` with the source it needs —
        so what the two refusals above reject is the uncatalogued name and not the axis
        (`ASM-46`, §C.2)."""
        default = token_configuration()
        self.assertIsNone(
            checks()(default),
            "a configuration declaring no strength declaration at all passes, because a "
            "level that declares none is no claim (declarations.md §2)",
        )
        named = token_configuration(strength="none")
        self.assertIsNone(
            checks()(named),
            "and so does an explicit `none` with no source: the catalogue's first member "
            "reads no model input, so it needs none (ASM-46)",
        )
        declaring = token_configuration(strength="supervised", strength_source=SOURCES[0])
        self.assertIsNone(
            checks()(declaring),
            "and a member other than the default with the source it names, which is the "
            "pair both of §C.2's keys exist for (ASM-46, ASM-51)",
        )


class StrengthSourceTest(TrainingCase):
    """TRN-9.1's source half — a declaration the run would not use, and one it needs."""

    def test_trn9_1c_a_source_beside_the_default_member_is_refused(self):
        """TRN-9.1 a `strength_source` declared with `strength: none` and no
        `embedding_init` is `IgnoredDeclaration` — a declaration the run would not use, the
        `_check_hyper` precedent — at the configuration and at each entry, so a source the
        run never reads cannot sit in a record looking as if it were honoured
        (`ASM-51`, §C.2, declarations.md §2)."""
        for level in ("configuration", "entry"):
            with self.subTest(level=level):
                if level == "configuration":
                    configuration = token_configuration(strength="none")
                    configuration["strength_source"] = SOURCES[0]
                else:
                    configuration = token_configuration(
                        strength="none", strength_source=SOURCES[0]
                    )
                self.refuse(
                    lambda configuration=configuration: checks()(configuration),
                    "IgnoredDeclaration",
                    groups=(("strength_source",), (SOURCES[0],), ("strength",)),
                    label="a %s declaring a source beside the default member" % (level,),
                )

    def test_trn9_1d_a_member_or_a_seed_with_no_source_is_refused(self):
        """TRN-9.1 (the other direction) a member other than the default, or an
        `embedding_init`, with no `strength_source` anywhere is refused naming both keys --
        the member names what the learner reads and the source names which frozen estimator
        produces it, so one without the other is half a declaration
        (`ASM-46`, `ASM-49`, `ASM-51`)."""
        cases = (
            (
                "a declaring member with no source",
                token_configuration(strength="supervised"),
                ("strength", "strength_source"),
            ),
            (
                "a seed with no source",
                token_configuration(
                    embedding_init={"source": SOURCES[0], "rows": ROWS}
                ),
                ("strength_source", "embedding_init"),
            ),
        )
        for label, configuration, groups in cases:
            with self.subTest(case=label):
                self.refuse(
                    lambda configuration=configuration: checks()(configuration),
                    "VariantSettingInvalid",
                    groups=tuple((token,) for token in groups),
                    label=label,
                )
        sourced = token_configuration(strength="supervised", strength_source=SOURCES[0])
        self.assertIsNone(
            checks()(sourced),
            "and the pair of keys together passes, so the refusal above is the missing "
            "source and not the member (ASM-46, ASM-51)",
        )

    def test_trn9_1e_an_uncatalogued_source_is_refused_at_both_levels(self):
        """TRN-9.1 an uncatalogued `strength_source` is refused naming the value and the
        declared sources at the configuration and at each entry, so a path is never
        invented by a run (`ASM-51`, §D.1)."""
        for level in ("configuration", "entry"):
            with self.subTest(level=level):
                if level == "configuration":
                    configuration = token_configuration(strength="supervised")
                    configuration["strength_source"] = "attn-999"
                else:
                    configuration = token_configuration(
                        strength="supervised", strength_source="attn-999"
                    )
                self.refuse(
                    lambda configuration=configuration: checks()(configuration),
                    "VariantSettingInvalid",
                    groups=(("strength_source",), ("attn-999",), (SOURCES[0],), (SOURCES[1],)),
                    label="a %s naming an uncatalogued source" % (level,),
                )


class EmbeddingInitTest(TrainingCase):
    """TRN-9.1's seed half — the record, its source, its selector and its family."""

    def test_trn9_1f_a_malformed_seed_record_is_refused(self):
        """TRN-9.1 an `embedding_init` that is not a mapping, that names a source the table
        does not carry, or that names a `rows` selector the table does not declare is
        refused naming what it got and what it needed; nothing is defaulted onto the
        selector (`ASM-49`, §D.3)."""
        cases = (
            (
                "not a mapping",
                token_configuration(
                    strength="supervised",
                    strength_source=SOURCES[0],
                    embedding_init=ROWS,
                ),
                ("embedding_init", ROWS),
            ),
            (
                "an uncatalogued source",
                token_configuration(
                    strength="supervised",
                    strength_source=SOURCES[0],
                    embedding_init={"source": "attn-999", "rows": ROWS},
                ),
                ("source", "attn-999", SOURCES[1]),
            ),
            (
                "an undeclared rows selector",
                token_configuration(
                    strength="supervised",
                    strength_source=SOURCES[0],
                    embedding_init={"source": SOURCES[0], "rows": "suits"},
                ),
                ("rows", "suits", ROWS),
            ),
        )
        for label, configuration, groups in cases:
            with self.subTest(case=label):
                self.refuse(
                    lambda configuration=configuration: checks()(configuration),
                    "VariantSettingInvalid",
                    groups=tuple((token,) for token in groups),
                    label="an embedding_init refused for %s" % (label,),
                )

    def test_trn9_1g_a_seed_on_a_dense_variant_is_refused(self):
        """TRN-9.1 an `embedding_init` on a `flat-numeric` variant is refused naming the
        kind and its family, because a dense-numeric learner's input block is a matrix and
        has no card rows to write (`ASM-49`, §C.2, §D.3)."""
        configuration = dense_configuration(
            strength="supervised",
            strength_source=SOURCES[0],
            embedding_init={"source": SOURCES[0], "rows": ROWS},
        )
        self.refuse(
            lambda: checks()(configuration),
            "VariantSettingInvalid",
            groups=(("embedding_init",), ("flat-numeric", "naive-stack")),
            label="an embedding_init on a flat-numeric variant",
        )

    def test_trn9_1h_a_source_that_disagrees_with_the_seed_is_refused(self):
        """TRN-9.1 a `strength_source` naming one estimator and an `embedding_init` naming
        another is refused, naming both: one run cannot be seeded from one frozen model and
        read another's value (`ASM-51`, §C.2)."""
        configuration = token_configuration(
            strength="supervised",
            strength_source=SOURCES[0],
            embedding_init={"source": SOURCES[1], "rows": ROWS},
        )
        self.refuse(
            lambda: checks()(configuration),
            "IgnoredDeclaration",
            groups=(("strength_source",), (SOURCES[0],), (SOURCES[1],)),
            label="a source and a seed naming two estimators",
        )

    def test_trn9_1i_the_agreed_pair_passes(self):
        """TRN-9.1 (control) a declaring member, the source it names and a seed from the
        same source pass together, so the four refusals above are the records they name and
        not the axis (`ASM-46`, `ASM-49`, `ASM-51`)."""
        configuration = token_configuration(
            strength="supervised",
            strength_source=SOURCES[0],
            embedding_init={"source": SOURCES[0], "rows": ROWS},
        )
        self.assertIsNone(
            checks()(configuration),
            "the declared pair -- one member, one source, one seed from that source -- "
            "passes the declaration check (ASM-46, ASM-49, ASM-51)",
        )


if __name__ == "__main__":  # pragma: no cover - a case file, run by pytest
    unittest.main()
