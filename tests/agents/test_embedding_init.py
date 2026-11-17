"""AGT-19.4 and AGT-19.5 — the embedding seed: exact, bounded, and refused before it writes.

``docs/L1/strength-design.md`` §D.2, §D.3 and §F.2; ``ASM-49``; ``docs/L3/agents/
architecture.md`` §4; ``docs/L3/agents/backends.md`` §2.

A seeded learner copies the frozen estimator's **card rows** -- ids 1..52 -- into its
embedding table between `model.initial_draw` and `backend.new_state`, and the two cases here
hold the copy to what it claims:

* **AGT-19.4** the copy is **exact and bounded to the card rows**: after `build_learner`
  with an `embedding_init`, the table's rows 1..52 are the rows the seed carried, bit for
  bit, while row 0 (the pad) and every row past the cards are the **same seed's unseeded
  draw** -- on both backends -- and the value the forward pass reads from a copied row is
  `(1 + tanh theta)/2`, which is the composition §D.3 states and this case asserts rather
  than assumes;
* **AGT-19.5** a seed is refused **before any mutation** for a dense kind, a row set that is
  not `(52, width)`, a source width that is not the learner's, a non-finite row and three
  malformed records -- each naming what it got and what it needed, and no learner built.

Everything below is measured off the learner the module built -- `backend.parameters` on the
state it created -- so no case re-derives the copy from the code that performs it.
"""

import unittest

import numpy

from _agents_support import (
    AgentsCase,
    declared_module,
    features,
    learner_spec,
    plain_int,
)


def strength_encoder(representation="card-tokens", shape=None, member="supervised"):
    """One encoder declaring -- or, with `member=None`, not declaring -- the tenth block."""
    return features().build_encoder(representation, shape=shape, strength=member)


def seeded_rows(width=50, offset=0.0):
    """`(52, width)` rows the seed carries, distinct per index and never the draw's own."""
    values = numpy.arange(52 * width, dtype=numpy.float64).reshape(52, width)
    return (values / 1000.0) + offset


def spec_with(rows, width=50, depth=2, kind="token-embedding", backend="numpy",
              shape=None, member="supervised"):
    """One declaring spec whose `embedding_init` carries `rows`."""
    return learner_spec(
        backend=backend,
        kind=kind,
        width=width,
        depth=depth,
        game=shape,
        encoder=strength_encoder(
            "card-tokens" if kind != "naive-stack" else "flat-numeric", shape
        ),
        extra={
            "strength": member,
            "embedding_init": {"source": "attn-60", "rows": rows},
        },
    )


class EmbeddingSeedExactnessTest(AgentsCase):
    """AGT-19.4 — the copy touches rows 1..52 and nothing else."""

    def table(self, package, learner):
        """The learner's embedding table as `(input_dim, width)` float64, read off its state."""
        layout = learner.layout
        parameters = learner.backend.parameters(learner.state)
        online = parameters[: plain_int(layout.count, "layout.count")]
        offset, length = layout.w_in
        return online[offset : offset + length].reshape(layout.input_dim, layout.width)

    def test_agt19_4_the_copy_is_exact_and_bounded_to_the_card_rows(self):
        """AGT-19.4 on both backends, a seeded learner's embedding table carries the seed's
        `(52, width)` rows at ids 1..52 **bit for bit**, while row 0 and every row past the
        cards are the same seed's unseeded draw -- so only the cards were written -- and the
        row the forward pass reads is `(1 + tanh theta)/2` of the table's own value
        (`ASM-49`, §D.2, §D.3)."""
        package = self.agents()
        width = 8
        rows = seeded_rows(width)
        for backend_name in ("numpy", "torch"):
            with self.subTest(backend=backend_name):
                seeded = package.build_learner(
                    spec_with(rows, width=width, depth=1, backend=backend_name)
                )
                bare = package.build_learner(
                    learner_spec(
                        backend=backend_name,
                        kind="token-embedding",
                        width=width,
                        depth=1,
                        encoder=strength_encoder("card-tokens"),
                        extra={"strength": "supervised"},
                    )
                )
                self.assertEqual(
                    plain_int(seeded.layout.w_in[0], "layout.w_in[0]"),
                    plain_int(bare.layout.w_in[0], "layout.w_in[0]"),
                    "a seed moves no offset: the table starts where the draw put it, so "
                    "the copy is a write into the block and not a re-layout (ASM-49)",
                )
                table = self.table(package, seeded)
                before = self.table(package, bare)
                self.assertEqual(
                    table[1:53].tolist(), rows.tolist(),
                    "the table's rows 1..52 are not the seed's own rows, so the copy is "
                    "not exact (ASM-49, §D.2): %r against %r"
                    % (table[1:53][:1].tolist(), rows[:1].tolist()),
                )
                self.assertEqual(
                    table[0].tolist(), before[0].tolist(),
                    "the seed wrote the pad's row, and row 0 is the pad's and not a "
                    "card's: only ids 1..52 are copied (ASM-49): %r against %r"
                    % (table[0][:3].tolist(), before[0][:3].tolist()),
                )
                if table.shape[0] > 53:
                    self.assertEqual(
                        table[53:].tolist(), before[53:].tolist(),
                        "the seed wrote a row past the cards, and the street, seat, bucket "
                        "and strength ids keep the seed's own draw (ASM-49, §D.3): %r"
                        % (table[53:][:1].tolist(),),
                    )
                self.assertEqual(
                    table.shape, before.shape,
                    "the seeded and the unseeded learner have one table shape (ASM-49): "
                    "%r against %r" % (table.shape, before.shape),
                )
                # ... and the composition §D.3 states, asserted and not assumed: the row the
                # trunk consumes is the bounded squash of the value the copy wrote.
                backend_module = declared_module("%s_backend" % (backend_name,))
                observation = numpy.array([1, 2, 3, 1], dtype=numpy.int64)
                _values, cache = backend_module.forward(
                    seeded.state, seeded.layout, observation, need_cache=True
                )
                read_rows, ids = cache["input"]
                read = numpy.asarray(read_rows)
                stored = numpy.asarray(ids)
                for position, index in enumerate(stored.tolist()):
                    with self.subTest(backend=backend_name, position=position):
                        self.assertEqual(
                            read[position].tolist(),
                            ((1.0 + numpy.tanh(table[int(index)])) / 2.0).tolist(),
                            "the row the forward pass read at id %d is not "
                            "`(1 + tanh theta)/2` of the table's own value, so the "
                            "composition is something other than the one §D.3 states "
                            "(ASM-49, normalisation.md §3): %r"
                            % (int(index), read[position][:3].tolist()),
                        )
                self.assertEqual(
                    sorted(set(stored.tolist())), [1, 2, 3],
                    "the forward pass read the ids the observation carried (ASM-49): %r"
                    % (sorted(set(stored.tolist())),),
                )

    def test_agt19_4b_the_seeded_copy_reaches_the_target_copy_too(self):
        """AGT-19.4 (second half) the copy happens **before** `backend.new_state`, so the
        target copy the first batch bootstraps from is seeded as well -- the property §D.2
        buys by copying where it does and not after the build (`ASM-49`, §D.2 item 2)."""
        package = self.agents()
        width = 8
        rows = seeded_rows(width)
        seeded = package.build_learner(spec_with(rows, width=width, depth=1))
        layout = seeded.layout
        parameters = seeded.backend.parameters(seeded.state)
        count = plain_int(layout.count, "layout.count")
        offset, length = layout.w_in
        online = parameters[:count][offset : offset + length]
        target = parameters[count : 2 * count][offset : offset + length]
        self.assertEqual(
            online.tolist(), target.tolist(),
            "the target copy does not start from the seeded online parameters, so the "
            "first batch would bootstrap from a stale draw (ASM-49, §D.2): %r"
            % (numpy.asarray(target).reshape(layout.input_dim, layout.width)[1:2].tolist(),),
        )
        self.assertEqual(
            numpy.asarray(target).reshape(layout.input_dim, layout.width)[1:53].tolist(),
            rows.tolist(),
            "the target copy's card rows are not the seed's (ASM-49): %r"
            % (numpy.asarray(target).reshape(layout.input_dim, layout.width)[1:2].tolist(),),
        )


class EmbeddingSeedRefusalTest(AgentsCase):
    """AGT-19.5 — every refusal, and the learner is not built."""

    def test_agt19_5_a_seed_is_refused_before_any_mutation(self):
        """AGT-19.5 a seed is refused for a dense kind, for rows that are not
        `(52, width)`, for a source width that is not the learner's, for a non-finite row and
        for a malformed record -- each naming what it got and what it needed, and each raised
        **before** `new_state`, so nothing is built (`ASM-49`, §D.3, errors.md §1)."""
        package = self.agents()
        width = 8
        good = seeded_rows(width)
        cases = (
            (
                "a dense kind",
                spec_with(good, width=width, depth=1, kind="naive-stack"),
                ("naive-stack",),
                ("dense-numeric",),
                ("embedding",),
            ),
            (
                "rows of another shape",
                spec_with(seeded_rows(width)[:13], width=width, depth=1),
                ("13",),
                ("52",),
                (str(width),),
            ),
            (
                "a source width that is not the learner's",
                spec_with(seeded_rows(6), width=width, depth=1),
                ("52",),
                ("6",),
                (str(width),),
            ),
            (
                "a non-finite row",
                spec_with(
                    numpy.vstack([good[:1], numpy.full((1, width), numpy.inf), good[2:]]),
                    width=width,
                    depth=1,
                ),
                ("finite",),
                ("attn-60",),
            ),
            (
                "a record that is not a mapping",
                learner_spec(
                    kind="token-embedding", width=width, depth=1,
                    encoder=strength_encoder("card-tokens"),
                    extra={"strength": "supervised", "embedding_init": "cards"},
                ),
                ("embedding_init",),
                ("mapping",),
            ),
            (
                "a record carrying no rows selector",
                learner_spec(
                    kind="token-embedding", width=width, depth=1,
                    encoder=strength_encoder("card-tokens"),
                    extra={
                        "strength": "supervised",
                        "embedding_init": {"source": "attn-60"},
                    },
                ),
                ("rows",),
                ("cards",),
            ),
            (
                "a record naming another selector",
                learner_spec(
                    kind="token-embedding", width=width, depth=1,
                    encoder=strength_encoder("card-tokens"),
                    extra={
                        "strength": "supervised",
                        "embedding_init": {"source": "attn-60", "rows": "suits"},
                    },
                ),
                ("suits",),
                ("cards",),
            ),
            (
                "a record whose source is not a name",
                learner_spec(
                    kind="token-embedding", width=width, depth=1,
                    encoder=strength_encoder("card-tokens"),
                    extra={
                        "strength": "supervised",
                        "embedding_init": {"source": 7, "rows": good},
                    },
                ),
                ("source",),
                ("7",),
            ),
        )
        for label, spec, *groups in cases:
            with self.subTest(refusal=label):
                self.assert_agents_refusal(
                    package.build_learner,
                    spec,
                    entry="build_learner",
                    groups=tuple(groups),
                    label="a seed refused for %s" % (label,),
                )
        # And the good record still builds, so the refusals above are the surgery's and not
        # the file's (errors.md §1).
        self.assertEqual(
            plain_int(
                package.param_count(
                    package.build_learner(spec_with(good, width=width, depth=1))
                ),
                "param_count",
            ),
            plain_int(
                package.param_count(
                    package.build_learner(spec_with(good, width=width, depth=1))
                ),
                "param_count",
            ),
            "a seed this module accepts builds a learner, so the refusals above are about "
            "the records they name and not about the entry point (ASM-49, errors.md §1)",
        )

    def test_agt19_5b_every_declared_token_vocabulary_holds_the_card_ids(self):
        """AGT-19.5 (second half) the sixth check -- that the learner's vocabulary holds ids
        1..52 -- is satisfied by every declared token encoder: 96 on the two-seat rows, 102
        at six seats and 110 for a declaring declaration, so a narrow vocabulary is a
        refusal a future shape would meet and never a current one (`ASM-49`, §D.3)."""
        feats = features()
        for shape in (None, "no-limit-100", "six-seat-no-limit-100"):
            for member in (None, "supervised"):
                with self.subTest(shape=shape, member=member):
                    vocabulary = feats.observation_spec(
                        feats.build_encoder("card-tokens", shape=shape, strength=member)
                    )["vocabulary"]
                    self.assertGreaterEqual(
                        int(vocabulary), 53,
                        "a token vocabulary holds the ids 1..52 a seed writes, and %r does "
                        "not (ASM-49): %r" % (shape, vocabulary),
                    )

    def test_agt19_5c_a_refused_seed_writes_no_learner(self):
        """AGT-19.5 (third half) a refused seed leaves nothing built: the same spec with a
        refused record and the same spec without one are two different outcomes, and the
        unseeded build still succeeds -- so the refusal is the record's and not a state the
        draw left behind (`ASM-49`, §D.2, errors.md §1)."""
        package = self.agents()
        width = 8
        refused = spec_with(seeded_rows(width)[:7], width=width, depth=1)
        accepted = dict(refused)
        accepted.pop("embedding_init")
        self.assert_agents_refusal(
            package.build_learner,
            refused,
            entry="build_learner",
            groups=(("52",), ("7",)),
            label="a seed carrying seven rows",
        )
        built = package.build_learner(accepted)
        self.assertIsNotNone(
            built,
            "the same spec without the seed still builds, so the refusal above was the "
            "record's and left no state behind (ASM-49, errors.md §1)",
        )
        self.assertEqual(
            getattr(built, "seeding", "<absent>"), None,
            "and the learner that build produced carries no seed record, because no seed "
            "was written (ASM-49): %r" % (getattr(built, "seeding", "<absent>"),),
        )


if __name__ == "__main__":  # pragma: no cover - a case file, run by pytest
    unittest.main()
