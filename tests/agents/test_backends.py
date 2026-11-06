"""AGT-14 — the torch backend on the token kinds, and its own checkpoint's bytes.

Closes the coverage hole the rest of this battery left: before this file every
torch learner driven here was a dense `naive-stack` one, so a torch token
forward pass, a torch token backward pass, a torch trunk that ignored its kind's
connection or its kind's mask, and a torch checkpoint's round trip could all have
regressed with both batteries green (`backends.md` §1-§4, `architecture.md` §2-§5,
`checkpoint.md` §1-§4, D-7, D-16, ASM-5, ASM-10).

The three cases read the backend axis where an entry point shows it and never
through a private spelling beyond the six `rule.md` §8 declares: `act` and
`learn` on a `token-embedding` learner carrying a `card-tokens` encoder
(AGT-14.1), one invented token batch driving a torch `residual` and a torch
`sparse` trunk each against its dense mate, plus §5's formula for each
(AGT-14.2), and a torch `sparse` learner's own bytes, restored in torch from its
path alone (AGT-14.3). Nothing here imports `torch`: the package's lazy import is
the code under test (`backends.md` §4), and no case needs a device — every
learner is small (widths 10-12, depths 2, batches of 12) and CPU-only
(`strata/platform.md`).

The guardrail cases that assert `torch` is absent from `sys.modules` read a
**clean interpreter** (`test_guardrails.py`'s G6, `test_checkpoint.py`'s
AGT-7.13), so importing torch into this process on a torch learner's first build
leaves them first-class and unaffected (`backends.md` §4).
"""

import os
import unittest

import numpy as np

from _agents_support import (
    LEARNER_SEED,
    AgentsCase,
    declared_internal,
    features,
    finite_float,
    invented_observations,
    learner_spec,
    plain_int,
    token_encoder,
    transition,
)

#: Invented instances: no number or name here appears in a design document.
TORCH_BATCH_SEED = 2419
TOKEN_WIDTH, TOKEN_DEPTH = 10, 2
RESIDUAL_WIDTH, RESIDUAL_DEPTH = 10, 2
SPARSE_WIDTH, SPARSE_DEPTH, SPARSE_SPARSITY = 12, 2, 0.5
MIXED_REWARDS = (7.25, -2.5, 9.0, -4.75)


def mixed_token_batch(kind, count=12, seed=TORCH_BATCH_SEED):
    """`count` invented token transitions, non-degenerate by construction.

    Each observation is an invented token observation of the family's declared
    `(40,) int32` shape — the shape `features.observation_spec` states, read by
    the support helper and never copied (`architecture.md` §1,
    `features/surface.md` §5) — the observations are distinct, and the batch holds
    both terminal and non-terminal records with a non-zero reward on each terminal
    one, which is where ASM-12 delivers it. A mean absolute TD error over this
    batch (`rule.md` §3) is therefore a statistic over varied records and not one
    record's coincidence, which is what the two inequalities of AGT-14.2 rest on.
    """
    values = invented_observations(kind, count + 1, seed)
    records = []
    paid = 0
    for step in range(count):
        terminal = step % 3 == 0
        reward = 0.0
        if terminal:
            reward = MIXED_REWARDS[paid % len(MIXED_REWARDS)]
            paid += 1
        records.append(
            transition(
                values[step],
                action=step % 3,
                reward=reward,
                terminal=terminal,
                next_observation=values[step + 1],
            )
        )
    return records


class TorchBackendTest(AgentsCase):
    def test_agt14_1_a_torch_token_learner_acts_learns_and_round_trips(self):
        """AGT-14.1 a `token-embedding` learner built with `backend="torch"` and a `card-tokens` encoder accepts the `int32` `(40,)` observation `features.encode` makes of a real readout and answers an index of the decision's mask (`surface.md` §6, `backends.md` §2, §4); `learn` consumes one invented batch of real token observations and returns a finite `td_error` and the batch's own `transitions` count (`rule.md` §3, §7); its `param_count` is the numpy learner's at one kind, width and depth, one model in two backends (ASM-10, D-7, `architecture.md` §5); and a `save`→`load` round trip decides as its source does over 6 real decisions and reports the same count and the same next update's `td_error`, a restore being loss-free for a token kind and a torch backend (`checkpoint.md` §1-§4, `surface.md` §9, ASM-5)."""
        package = self.agents()
        encoder = token_encoder()
        spec = features().observation_spec(encoder)
        torch_learner = self.build(
            backend="torch",
            kind="token-embedding",
            width=TOKEN_WIDTH,
            depth=TOKEN_DEPTH,
            encoder=encoder,
        )
        numpy_learner = self.build(
            backend="numpy",
            kind="token-embedding",
            width=TOKEN_WIDTH,
            depth=TOKEN_DEPTH,
            encoder=encoder,
        )
        rows = self.decisions(6)
        self.assertGreaterEqual(
            len(rows), 6, "fewer than six real decisions to decide and to compare"
        )

        for row in rows:
            with self.subTest(hand=row["readout"]["hole"]):
                observation = row["tokens"]
                self.assertEqual(
                    observation.dtype,
                    np.dtype(spec["dtype"]),
                    "features.encode gave a token observation that is not the "
                    "encoding's declared dtype, so this case would not be driving "
                    "the declared family (features/surface.md §5)",
                )
                self.assertEqual(
                    tuple(observation.shape),
                    tuple(spec["shape"]),
                    "the encoded observation is not the shape the encoder declares, "
                    "so the forward pass would not be sized as the model is",
                )
                action = plain_int(
                    package.act(torch_learner, observation, row["mask"])["action"],
                    "act(torch token learner)['action']",
                )
                self.assertIn(
                    action,
                    row["mask"],
                    "the torch path answered an index outside the decision's mask "
                    "(rule.md §4-§5, backends.md §2)",
                )

        records = mixed_token_batch("token-embedding")
        result = package.learn(torch_learner, records)
        self.assertEqual(set(result), {"td_error", "transitions"})
        self.assertEqual(
            plain_int(result["transitions"], "transitions"),
            len(records),
            "the torch path did not consume the caller's batch in full "
            "(rule.md §3)",
        )
        self.assertGreaterEqual(
            finite_float(result["td_error"], "the torch td_error"), 0.0
        )

        self.assertEqual(
            package.param_count(torch_learner),
            package.param_count(numpy_learner),
            "one kind at one width and depth holds two capacities in the two "
            "backends: the swap may not change the sizing record or the model "
            "(backends.md §1, ASM-10, D-7)",
        )

        path = package.save(
            torch_learner, os.path.join(self.tempdir(), "torch-token-8127.pt")
        )
        restored = package.load(None, path)
        for row in rows:
            with self.subTest(hand=row["readout"]["hole"], restored=True):
                self.assertEqual(
                    package.act(restored, row["tokens"], row["mask"])["action"],
                    package.act(torch_learner, row["tokens"], row["mask"])["action"],
                    "the restored torch token learner did not decide as its source, "
                    "so the restore is lossy at the decision boundary for a token "
                    "kind (checkpoint.md §4, ASM-5)",
                )
        self.assertEqual(
            package.param_count(restored),
            package.param_count(torch_learner),
            "the restored learner reports another capacity than its source "
            "(checkpoint.md §4)",
        )

        probe = mixed_token_batch("token-embedding", count=9, seed=TORCH_BATCH_SEED + 7)
        saved = package.learn(torch_learner, probe)
        loaded = package.learn(restored, probe)
        self.assertEqual(
            plain_int(loaded["transitions"], "transitions"),
            plain_int(saved["transitions"], "transitions"),
        )
        self.assertEqual(
            finite_float(loaded["td_error"], "the restored td_error"),
            finite_float(saved["td_error"], "the saved td_error"),
            "the restored learner's first update did not report the saved "
            "learner's own td_error, so the parameters, the target copy or the "
            "position did not travel (checkpoint.md §1, §4, rule.md §3)",
        )

    def test_agt14_2_the_torch_residual_and_sparse_trunks_are_not_a_plain_one(self):
        """AGT-14.2 torch `residual` and torch `sparse` learners each consume one invented token batch returning a finite `td_error` and the batch's own count, report exactly the count `model._param_count_for(kind, width, depth, sparsity)` declares (`architecture.md` §5, §8), and each reports a `td_error` its mate at one shape and one seed does not — `residual` against `plain` for the delta of `architecture.md` §2, `sparse` against `deep` for the mask materialised before the torch matmul — so a torch trunk that adds no delta, or one that ignores its mask, is red (architecture.md §2-§3, §5, backends.md §1-§2, rule.md §2-§3, D-7, ASM-10, R5, R6)."""
        package = self.agents()
        count = declared_internal("model", "_param_count_for")
        records = mixed_token_batch("residual")
        self.assert_mixed(records)
        residual = self.build(
            backend="torch", kind="residual", width=RESIDUAL_WIDTH, depth=RESIDUAL_DEPTH
        )
        plain = self.build(
            backend="torch", kind="plain", width=RESIDUAL_WIDTH, depth=RESIDUAL_DEPTH
        )
        sparse = package.build_learner(
            learner_spec(
                backend="torch",
                architecture={
                    "kind": "sparse",
                    "width": SPARSE_WIDTH,
                    "depth": SPARSE_DEPTH,
                    "sparsity": SPARSE_SPARSITY,
                },
            )
        )
        dense = self.build(
            backend="torch", kind="deep", width=SPARSE_WIDTH, depth=SPARSE_DEPTH
        )

        for kind, learner, width, depth, sparsity in (
            ("residual", residual, RESIDUAL_WIDTH, RESIDUAL_DEPTH, 0.0),
            ("plain", plain, RESIDUAL_WIDTH, RESIDUAL_DEPTH, 0.0),
            ("sparse", sparse, SPARSE_WIDTH, SPARSE_DEPTH, SPARSE_SPARSITY),
            ("deep", dense, SPARSE_WIDTH, SPARSE_DEPTH, 0.0),
        ):
            with self.subTest(kind=kind):
                self.assertEqual(
                    package.param_count(learner),
                    int(count(kind, width, depth, sparsity)),
                    "%s's torch learner does not hold architecture.md §5's count "
                    "at its own settings, so its parameter vector is not the "
                    "model the formula sizes" % kind,
                )
        self.assertEqual(
            package.param_count(residual),
            package.param_count(plain),
            "architecture.md §2 gives `residual` the same D trunks of shape W x W "
            "as `plain` — it adds the delta, not a weight — so the torch pair must "
            "hold one capacity",
        )
        self.assertNotEqual(
            package.param_count(sparse),
            package.param_count(dense),
            "the torch sparse learner holds as many parameters as the torch dense "
            "one at s = 0.5, so no slot of a trunk layer was pinned to zero "
            "(architecture.md §3, §5)",
        )

        errors = {}
        for kind, learner in (
            ("residual", residual),
            ("plain", plain),
            ("sparse", sparse),
            ("deep", dense),
        ):
            result = package.learn(learner, records)
            with self.subTest(kind=kind, phase="learn"):
                self.assertEqual(
                    plain_int(result["transitions"], "transitions"),
                    len(records),
                    "the torch path did not consume the whole invented batch",
                )
                errors[kind] = finite_float(
                    result["td_error"], "the torch %s td_error" % kind
                )
                self.assertGreaterEqual(
                    errors[kind],
                    0.0,
                    "a mean absolute TD error cannot be negative (rule.md §3)",
                )

        self.assertNotEqual(
            errors["residual"],
            errors["plain"],
            "torch `residual` and torch `plain` reported one mean absolute TD "
            "error (%r) for one batch from one seed: the residual connection of "
            "architecture.md §2 is not expressed in the torch trunk, so the R6 "
            "axis is a numpy-only axis (backends.md §1-§2)"
            % (errors["residual"],),
        )
        self.assertNotEqual(
            errors["sparse"],
            errors["deep"],
            "a masked torch trunk and a dense torch one reported one mean absolute "
            "TD error (%r) for one batch from one seed: the mask is not "
            "materialised before the torch matmul, so a torch learner ignores the "
            "connectivity it declares (architecture.md §2-§3, backends.md §2)"
            % (errors["sparse"],),
        )

    def test_agt14_3_a_torch_checkpoint_restores_in_torch(self):
        """AGT-14.3 a torch `sparse` learner's own bytes restore in torch, not only in numpy: the file records `backend` `torch` and the kind `sparse` (`checkpoint.md` §2.1, read through `_read_metadata`, `rule.md` §8), `load` compares that key — a `numpy` spec is refused naming both values while the torch spec loads (`checkpoint.md` §3) — and the learner `load(None, path)` rebuilds decides as its source over 6 real decisions, reports the same `param_count`, re-saves as a torch file and reports the same next `td_error`, which is a restore loss-free whatever the backend (`checkpoint.md` §1, §4, `surface.md` §9, ASM-5, D-16)."""
        package = self.agents()
        read_metadata = declared_internal("checkpoint", "_read_metadata")
        learner = package.build_learner(
            learner_spec(
                backend="torch",
                architecture={
                    "kind": "sparse",
                    "width": SPARSE_WIDTH,
                    "depth": SPARSE_DEPTH,
                    "sparsity": SPARSE_SPARSITY,
                },
            )
        )
        records = mixed_token_batch("sparse", count=10)
        self.assert_mixed(records)
        package.learn(learner, records)
        folder = self.tempdir()
        path = package.save(learner, os.path.join(folder, "torch-sparse-8127.pt"))

        metadata = read_metadata(path)
        self.assertEqual(
            metadata["backend"],
            "torch",
            "the container does not record the learner's own backend, so a torch "
            "member could not load from its path alone (checkpoint.md §1-§2.1)",
        )
        self.assertEqual(
            metadata["kind"],
            "sparse",
            "the container does not record the kind, so the model could not be "
            "rebuilt before any value is scattered into it (checkpoint.md §1)",
        )
        self.assertEqual(
            plain_int(metadata["params"]["count"], "params.count"),
            package.param_count(learner),
            "the container's recorded count is not param_count's answer "
            "(checkpoint.md §2.1, §4)",
        )

        numpy_spec = learner_spec(
            backend="numpy",
            architecture={
                "kind": "sparse",
                "width": SPARSE_WIDTH,
                "depth": SPARSE_DEPTH,
                "sparsity": SPARSE_SPARSITY,
            },
        )
        self.assert_agents_refusal(
            package.load,
            numpy_spec,
            path,
            entry="load",
            groups=(("backend",), ("numpy",), ("torch",)),
            label="a numpy spec against a torch checkpoint",
        )
        agreed = package.load(
            learner_spec(
                backend="torch",
                kind="sparse",
                width=SPARSE_WIDTH,
                depth=SPARSE_DEPTH,
            ),
            path,
        )
        self.assertEqual(
            package.param_count(agreed),
            package.param_count(learner),
            "a torch spec that agrees on backend, kind and seed did not restore "
            "the checkpoint's own model (checkpoint.md §3-§4)",
        )

        restored = package.load(None, path)
        self.assertEqual(
            package.param_count(restored),
            package.param_count(learner),
            "the torch checkpoint restored another capacity than it holds "
            "(checkpoint.md §4)",
        )
        rows = self.decisions(6)
        self.assertGreaterEqual(
            len(rows), 6, "fewer than six real decisions to compare"
        )
        for row in rows:
            with self.subTest(hand=row["readout"]["hole"]):
                self.assertEqual(
                    package.act(restored, row["tokens"], row["mask"])["action"],
                    package.act(learner, row["tokens"], row["mask"])["action"],
                    "the restored torch learner did not decide as its source on a "
                    "real readout (checkpoint.md §4, ASM-5)",
                )

        resaved = package.save(restored, os.path.join(folder, "torch-sparse-restored.pt"))
        self.assertEqual(
            read_metadata(resaved)["backend"],
            "torch",
            "the restored learner re-saves as another backend, so `load` rebuilt "
            "it from something other than the file's recorded backend "
            "(checkpoint.md §1, §3)",
        )

        probe = mixed_token_batch("sparse", count=8, seed=TORCH_BATCH_SEED + 11)
        saved = package.learn(learner, probe)
        loaded = package.learn(restored, probe)
        self.assertEqual(
            plain_int(loaded["transitions"], "transitions"),
            plain_int(saved["transitions"], "transitions"),
        )
        self.assertEqual(
            finite_float(loaded["td_error"], "the restored td_error"),
            finite_float(saved["td_error"], "the saved td_error"),
            "the restored torch learner's first update did not report the saved "
            "learner's own td_error, so the parameters, the masks, the target copy "
            "or the position did not travel (checkpoint.md §1-§2, rule.md §3)",
        )

    def assert_mixed(self, records):
        """Guard the non-degeneracy the two `td_error` inequalities rest on.

        Each inequality of AGT-14.2 is a statement about two forward passes, and
        it holds for any correct implementation **only** while the statistic is
        not one record's: so the batch holds distinct token observations, both
        terminal flags and at least one non-zero reward (`rule.md` §2-§3, ASM-12).
        """
        self.assertGreaterEqual(len(records), 4)
        self.assertEqual(
            len({record["observation"].tobytes() for record in records}),
            len(records),
            "the batch repeats an observation, so its mean absolute TD error is one "
            "record's and an inequality over it could be a coincidence",
        )
        self.assertTrue(
            any(not record["terminal"] for record in records),
            "the batch holds no non-terminal transition, so no target bootstraps "
            "and the successor is never read (rule.md §2)",
        )
        self.assertTrue(
            any(record["terminal"] for record in records),
            "the batch holds no terminal transition, so no target is a reward",
        )
        self.assertTrue(
            any(record["reward"] != 0.0 for record in records),
            "every reward is zero, so the two targets are both pure bootstraps",
        )


if __name__ == "__main__":
    unittest.main()
