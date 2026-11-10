"""AGT-16 — the divergence refusal.

Drives `docs/L2/agents/divergence.md` §2-§4 and `docs/L3/agents/divergence.md`
§2-§4: the one refusal of this surface whose fault is the learner's own
accumulated state, never the caller's argument.  Its two sites are pinned where
the design puts them — `learn`'s two guards inside `docs/L3/agents/rule.md` §3's
per-transition order (a non-finite `td_error` **before** `|td|` is accumulated
and before the step, a non-finite parameter **after** the step and **before**
the counter) and the decision's single raise, checked in `rule.decide` **before**
the exploring draw and in `rule._tie_break` for `double-q-learning`'s bootstrap
index (`rule.md` §5, §8) — and so are the four messages `errors.md` §3's last two
rows state.  Every refusal is asserted the way `errors.md` §2
requires: as a value catchable as `AgentsError` and by what its message says,
never by the subclass's name — `LearningDiverged` is not imported here, and a
message that omits the site, the index or the offending value fails a case.

The other half of the contract is what the refusal never does (`divergence.md`
§4): nothing is clipped, clamped, skipped or replaced by a finite substitute, no
statistics come back, no transition is consumed, the schedule position does not
move, and `load` gains nothing — a container carrying a `nan` parameter is read
exactly as it always was and the refusal arrives at the restored member's first
decision, through `act` and through every policy `as_policy` builds.  The one
patched declaration is put back through `self.addCleanup`, so the six values of
`rule.md` §6 stand as declared for every other case.  AGT-16.1-16.3 pin the
update's two refusals and what they leave untouched, AGT-16.4-16.6 the decision
at its three call sites, and AGT-16.7 the finite path's digits against goldens
recorded from the implementation that had no guards, since a guard must add no
arithmetic (`divergence.md` §5, `guardrails.md` G5, G14).
"""

import importlib
import io
import os
import re
import unittest

import numpy as np

from _agents_support import (
    ALL_MASK,
    LEARNER_SEED,
    NONEMPTY_MASKS,
    AgentsCase,
    SurfaceAbsent,
    batch,
    container_document,
    declared_internal,
    dense_observation,
    finite_float,
    flat_encoder,
    plain_int,
    transition,
    write_container,
)

#: A reward that is a number `records.md` §4 allows and that no step can compute
#: from, which is why it passes `learn`'s validation and reaches the update's
#: guard (`divergence.md` §4, `errors.md` §4).  An invented instance.
NON_FINITE_REWARD = float("nan")

#: The finite reward every other record of a divergence batch carries, so the
#: refusal can only be the `nan` one's.
ORDINARY_REWARD = 3.5

#: The rate AGT-16.3 patches into `agents.declarations.HYPER` for the length of
#: one case: finite, so GUARD 1 passes on a finite `td_error`, and large enough
#: that one declared step overflows `float64`.  The shipped `0.001` is never
#: written to disk and is restored by `self.addCleanup`.
DIVERGING_RATE = 1e300

#: The huge-but-finite terminal reward that pairs with `DIVERGING_RATE`: the
#: target is the reward alone (`rule.md` §2), so `delta` is finite and the step
#: `alpha * delta * gradient` leaves finite range.
OVERFLOWING_REWARD = 1e10

#: AGT-16.7's goldens, recorded on 2026-11-10 from the implementation that had no
#: guards at all (the checkout of `strata/records/lr-probe.md`, before the two
#: predicates of `divergence.md` §5 existed), by one scratch script run outside
#: this repository and deleted afterwards: a `naive-stack` learner at `width 6,
#: depth 1` learning AGT-6.1's eleven-observation batch, the same batch under a
#: `double-q-learning` learner built from one spec, and the indices an annealed
#: `naive-stack` learner at `width 8, depth 2` decides over `decisions()`'s
#: fourteen recorded observations and masks (`rule.md` §3, §5).  A guard may add
#: no arithmetic, so no guard may move one of them: the two `td_error`s are
#: compared to twelve places, the index tuple exactly.  The two figures coincide
#: on this batch — over those eleven transitions both rules bootstrap at the same
#: masked index — and both are recorded, so a change to either path moves one.
GOLDEN_MASKED_TD_ERROR = 1.4639328754860188
GOLDEN_DOUBLE_TD_ERROR = 1.4639328754860188
GOLDEN_ANNEALED_ACTIONS = (0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 2)


class DivergenceTest(AgentsCase):
    @staticmethod
    def declarations():
        """`agents.declarations`, the module `rule.md` §6 declares `HYPER` in.

        `HYPER` is one of the six fixed declarations and not one of the private
        names `rule.md` §8 fixes for this battery, so it is read where it lives:
        AGT-16.3 patches one value in process and restores it with
        `self.addCleanup`, because the shipped `learning_rate` stands as declared
        and no case may leave the catalogue moved (`divergence.md` §1, §4).
        """
        try:
            return importlib.import_module("agents.declarations")
        except Exception as exc:
            raise SurfaceAbsent(
                "src/agents/declarations.py is not importable, so the six fixed "
                "declarations of rule.md §6 cannot be read or patched (%s: %s)"
                % (type(exc).__name__, exc)
            )

    @staticmethod
    def nan_batch(index, length=3):
        """`length` terminal transitions, the one at `index` carrying a `nan` reward.

        Every record is terminal, so the target is the reward alone under either
        rule (`rule.md` §2) and the record at `index` gives `delta = nan` whatever
        the parameters hold.  The others carry a finite reward, so the refusal can
        only be the named index's.
        """
        return [
            transition(
                dense_observation(0.07 * step),
                action=1,
                reward=NON_FINITE_REWARD if step == index else ORDINARY_REWARD,
                terminal=True,
            )
            for step in range(length)
        ]

    def _refusal_message(self, fn, *args, entry, groups=(), label=""):
        """The message one call refused with, after `assert_agents_refusal`'s checks.

        `_agents_support` asserts the behaviour and hands nothing back, and three
        cases here have to read what the message says — the parameter index
        AGT-16.3 refuses over, and the site AGT-16.4 and AGT-16.5 require to be
        `decide` rather than `act(...)`/`policy(readout)`.  The call is made once,
        the message is kept, and the re-raise is what `assert_agents_refusal`
        judges, so the class and the named tokens are still the shared helper's
        (`errors.md` §2-§3).
        """
        seen = []

        def call():
            try:
                return fn(*args)
            except Exception as exc:
                seen.append(str(exc))
                raise

        self.assert_agents_refusal(call, entry=entry, groups=groups, label=label)
        return seen[0]

    def _doctored_container(self):
        """One container whose **last** output bias is `nan`: `(path, index, value)`.

        `index` is that parameter's position in the container's `2·P` array and
        `value` the decision index it poisons.  A **bias** element is the safe one
        to doctor because it needs no observation to propagate: the output layer's
        three values are `carried @ output + output_bias` (`backends.md` §2), the
        bias is added element-wise, so a `nan` in one entry makes that one decision
        value a `nan` at every observation and leaves the other two finite.  That
        is exactly what `divergence.md` §2 and D-2 need of this case: a mask
        holding that index has a non-finite masked value and must refuse, and a
        mask without it inspects only finite ones and must decide.  (A single
        output *weight* would not do: whether it poisons a value depends on the
        observation's own activations.)  The last entry is chosen so the offending
        decision index is `2` rather than the mask's first member, which is what
        makes "the smallest masked index" a claim rather than a coincidence.  The
        member is rewritten with `numpy.save` into a buffer and `write_container`
        writes the file back, so the container is built without touching
        `checkpoints/` (`checkpoint.md` §2, §3, `divergence.md` §1).
        """
        package = self.agents()
        folder = self.tempdir()
        learner = self.build(kind="naive-stack", width=6, depth=1)
        source = package.save(learner, os.path.join(folder, "source-8127.pt"))
        metadata, parameters = container_document(source)
        params = metadata["params"]
        bias = [
            tensor for tensor in params["tensors"] if tensor["name"] == "output.bias"
        ]
        self.assertEqual(
            len(bias),
            1,
            "the container's params.tensors table names one output.bias, and the "
            "element this case doctors is one of its entries (checkpoint.md §2.1)",
        )
        offset = plain_int(bias[0]["offset"], "params.tensors[i].offset")
        carried = plain_int(bias[0]["count"], "params.tensors[i].count")
        self.assertGreaterEqual(offset, 0)
        self.assertGreater(carried, 0)
        value = carried - 1
        index = offset + value
        self.assertLess(
            index,
            plain_int(params["count"], "params.count"),
            "the output bias must sit in the online half of the array, which is "
            "the half a decision's arithmetic reads (backends.md §2): index %d "
            "against %r" % (index, params["count"]),
        )
        array = np.load(io.BytesIO(parameters), allow_pickle=False)
        self.assertEqual(
            int(array.shape[0]), plain_int(params["length"], "params.length")
        )
        array[index] = np.nan
        buffer = io.BytesIO()
        np.save(buffer, np.ascontiguousarray(array), allow_pickle=False)
        target = os.path.join(folder, "doctored-8127.pt")
        write_container(target, metadata, buffer.getvalue())
        return target, index, value

    def test_agt16_1_a_non_finite_td_error_refuses_by_name(self):
        """AGT-16.1 a terminal record whose reward is `nan` at index 1 is refused naming `learn`, `transition index 1`, `td_error` and `nan`, and the schedule position does not advance; the same batch with the `nan` at index 0 or 2 names that index (`divergence.md` §2-§4, `errors.md` §2-§3, `rule.md` §3)."""
        package = self.agents()
        read_metadata = declared_internal("checkpoint", "_read_metadata")
        folder = self.tempdir()
        learner = self.build(kind="naive-stack", width=6, depth=1)
        before = package.save(learner, os.path.join(folder, "before-8127.pt"))
        position = plain_int(
            read_metadata(before)["exploration"]["position"], "exploration.position"
        )
        self.assert_agents_refusal(
            package.learn,
            learner,
            self.nan_batch(1),
            entry="learn",
            groups=(("transition index 1",), ("td_error",), ("nan",)),
            label="a batch whose transition index 1 has a nan reward",
        )
        after = package.save(learner, os.path.join(folder, "after-8127.pt"))
        self.assertEqual(
            plain_int(
                read_metadata(after)["exploration"]["position"],
                "exploration.position",
            ),
            position,
            "a refused batch moved the schedule position: it advances at the last "
            "line of learn and nowhere else, so a transition the update refused "
            "consumed nothing (rule.md §3, divergence.md §2, §4, surface.md §7)",
        )
        for index in (0, 2):
            with self.subTest(index=index):
                self.assert_agents_refusal(
                    package.learn,
                    self.build(kind="naive-stack", width=6, depth=1),
                    self.nan_batch(index),
                    entry="learn",
                    groups=(("transition index %d" % (index,),), ("nan",)),
                    label="a batch whose transition index %d has a nan reward"
                    % (index,),
                )

    def test_agt16_2_the_refusal_is_in_front_of_the_step(self):
        """AGT-16.2 a one-transition `nan` batch is refused naming `transition index 0` and leaves the two containers' `parameters.npy` byte-identical and the position where it was: no corrupting step was taken (`divergence.md` §2, §4, `errors.md` §3, `rule.md` §3)."""
        package = self.agents()
        folder = self.tempdir()
        learner = self.build(kind="naive-stack", width=6, depth=1)
        before = package.save(learner, os.path.join(folder, "before-8127.pt"))
        self.assert_agents_refusal(
            package.learn,
            learner,
            self.nan_batch(0, length=1),
            entry="learn",
            groups=(("transition index 0",), ("nan",)),
            label="a one-transition batch whose reward is nan",
        )
        after = package.save(learner, os.path.join(folder, "after-8127.pt"))
        _metadata_before, parameters_before = container_document(before)
        metadata_after, parameters_after = container_document(after)
        self.assertEqual(
            parameters_after,
            parameters_before,
            "the refused transition reached the step: the learner's parameters "
            "differ from the ones a save taken before the call wrote, and GUARD 1 "
            "refuses a non-finite td_error before |td| is accumulated and before "
            "backend.apply runs (divergence.md §2, rule.md §3, D-19)",
        )
        self.assertEqual(
            plain_int(metadata_after["exploration"]["position"], "exploration.position"),
            plain_int(
                container_document(before)[0]["exploration"]["position"],
                "exploration.position",
            ),
            "a refused batch moved the schedule position (rule.md §3, surface.md §7)",
        )

    def test_agt16_3_a_non_finite_parameter_refuses_by_name(self):
        """AGT-16.3 at a large finite rate one terminal transition overflows a parameter and `learn` refuses naming `transition index 0`, `parameter index` and a non-finite value — and the saved container still carries it, so nothing was clipped or substituted (`divergence.md` §2, §4, `errors.md` §2-§3, `rule.md` §3, §6, D-19)."""
        package = self.agents()
        declarations = self.declarations()
        shipped = declarations.HYPER["learning_rate"]
        self.addCleanup(
            declarations.HYPER.__setitem__, "learning_rate", shipped
        )
        declarations.HYPER["learning_rate"] = DIVERGING_RATE
        learner = self.build(kind="naive-stack", width=6, depth=1)
        record = transition(
            dense_observation(0.0),
            action=1,
            reward=OVERFLOWING_REWARD,
            terminal=True,
        )
        with np.errstate(all="ignore"):
            message = self._refusal_message(
                package.learn,
                learner,
                [record],
                entry="learn",
                groups=(
                    ("transition index 0",),
                    ("parameter index",),
                    ("nan", "inf"),
                ),
                label="a step at a diverging rate that left a parameter out of range",
            )
        match = re.search(r"parameter index\s+(\d+)", message, re.IGNORECASE)
        if match is None:
            self.fail(
                "the parameter refusal names no parameter index, and a caller "
                "cannot tell which value its step drove out of range "
                "(divergence.md §3, errors.md §3): %r" % (message,)
            )
        index = int(match.group(1))
        count = plain_int(package.param_count(learner), "param_count(learner)")
        self.assertGreaterEqual(index, 0)
        self.assertLess(
            index,
            2 * count,
            "the refusal named parameter index %d and the guard reads the whole "
            "2*P array — online values and target copy together, %d of them "
            "(divergence.md §2, backends.md §2)" % (index, 2 * count),
        )
        path = package.save(learner, os.path.join(self.tempdir(), "diverged-8127.pt"))
        _metadata, parameters = container_document(path)
        array = np.load(io.BytesIO(parameters), allow_pickle=False)
        self.assertFalse(
            np.isfinite(array).all(),
            "every value the diverged learner's container carries is finite, so "
            "the step's non-finite result was clipped, clamped or replaced by a "
            "finite substitute — the design refuses by name instead "
            "(divergence.md §1, §4, D-19, D-20)",
        )

    def test_agt16_4_a_non_finite_masked_value_refuses_in_a_decision(self):
        """AGT-16.4 `load` reads a container carrying a `nan` parameter unchanged, and the restored learner's `act` is refused as `decide` naming the smallest masked index and the value — never as `act(...)`, never masked by the exploring arm at position 0, and only for a mask that holds the non-finite index (`divergence.md` §1-§4, `errors.md` §3, `rule.md` §4-§5, D-2)."""
        package = self.agents()
        path, _index, value = self._doctored_container()
        restored = package.load(None, path)
        self.assertGreater(
            plain_int(
                package.param_count(restored), "param_count(load(None, doctored))"
            ),
            0,
            "load gains nothing and reads a container carrying a nan parameter as "
            "it always did — the refusal arrives at the restored member's first "
            "decision (divergence.md §1, §4, checkpoint.md §1, surface.md §9)",
        )
        self.assertIn(
            value,
            ALL_MASK,
            "the doctored bias must be one of the decision's three values: the "
            "declared vocabulary is (0, 1, 2) (features/surface.md §8, D-2)",
        )
        observation = dense_observation()
        message = self._refusal_message(
            package.act,
            restored,
            observation,
            ALL_MASK,
            entry="decide",
            groups=(("masked value",), ("index %d" % (value,),), ("nan",)),
            label="act at a learner whose output bias is nan",
        )
        self.assertFalse(
            message.strip().lower().startswith("act("),
            "the message names act(...) and the site that raised is decide, whose "
            "one raise serves act, every policy and learn's bootstrap "
            "(divergence.md §2-§3, surface.md §6, §10): %r" % (message,)
        )
        for mask in NONEMPTY_MASKS:
            with self.subTest(mask=mask):
                # A fresh restore per mask: act advances nothing, but a refusal
                # must not depend on what an earlier call left behind (ASM-5).
                probe = package.load(None, path)
                if value in mask:
                    self.assert_agents_refusal(
                        package.act,
                        probe,
                        observation,
                        mask,
                        entry="decide",
                        groups=(("index %d" % (value,),), ("nan",)),
                        label="act over the mask %r holding the nan index"
                        % (mask,),
                    )
                else:
                    answer = package.act(probe, observation, mask)["action"]
                    self.assertIn(
                        answer,
                        mask,
                        "a mask holding no non-finite index is a finite "
                        "decision: only masked indices are inspected (D-2), so a "
                        "nan outside the mask must not refuse one "
                        "(divergence.md §2, rule.md §5): %r over %r"
                        % (answer, mask),
                    )

    def test_agt16_5_a_policy_refuses_on_the_same_doctored_member(self):
        """AGT-16.5 `as_policy` snapshots the doctored learner and the policy's first real readout is refused as `decide`, not as `policy(readout)`: one raise serves every decision site (`divergence.md` §2-§3, `errors.md` §3, `rule.md` §7, `surface.md` §10)."""
        package = self.agents()
        path, _index, value = self._doctored_container()
        restored = package.load(None, path)
        policy = package.as_policy(restored, flat_encoder(), LEARNER_SEED)
        self.assertTrue(
            callable(policy),
            "as_policy only snapshots the parameters, the position and the "
            "encoder, so a non-finite parameter does not stop a policy being "
            "built (rule.md §7, divergence.md §2)",
        )
        rows = [
            row for row in self.decisions() if value in tuple(row["mask"])
        ]
        self.assertTrue(
            rows,
            "no recorded decision's legal mask holds the doctored value %d, so "
            "this case cannot drive a policy's refused decision (features/"
            "surface.md §8, divergence.md §2)" % (value,),
        )
        row = rows[0]
        message = self._refusal_message(
            policy,
            row["readout"],
            row["legal"],
            entry="decide",
            groups=(("masked value",), ("index %d" % (value,),), ("nan",)),
            label="a policy built from a learner whose output bias is nan",
        )
        self.assertFalse(
            message.strip().lower().startswith("policy("),
            "the refusal is a policy's own readout refusal, and a non-finite "
            "parameter is this module's state refusal at one raise serving act, "
            "every policy and learn's bootstrap (divergence.md §2-§3, "
            "errors.md §3, surface.md §10): %r" % (message,)
        )

    def test_agt16_6_the_tie_break_refuses_by_name(self):
        """AGT-16.6 `_tie_break` refuses a non-finite **masked** value naming `_tie_break`, the smallest offending masked index and the value, while a finite masked set — and a mask that holds no non-finite index — still decides by §5 (`rule.md` §5, §8, `divergence.md` §2-§3, `errors.md` §3, D-2)."""
        tie_break = declared_internal("rule", "_tie_break")
        nan = float("nan")
        infinity = float("inf")

        # The finite side: nothing non-finite is masked, so §5's rule decides.
        self.assertEqual(
            int(tie_break((0.0, 0.0, 0.0), ALL_MASK)),
            min(ALL_MASK),
            "equal values did not decide on the smallest masked index (rule.md §5)",
        )
        self.assertEqual(
            int(tie_break((2.0, 2.0 + 1e-12, 0.5), ALL_MASK)),
            0,
            "a near tie inside 1e-9 x max(1, |best|) did not resolve to the "
            "smallest masked index (rule.md §5)",
        )
        self.assertEqual(
            int(tie_break((0.0, 5.0, 4.0), ALL_MASK)),
            1,
            "a strict maximum outside the tolerance did not win (rule.md §5)",
        )
        self.assertEqual(
            int(tie_break((0.5, nan, 1.25), (0,))),
            0,
            "only masked indices are inspected (D-2), so a non-finite value "
            "outside the mask must not make a finite decision refuse "
            "(divergence.md §2, rule.md §5)",
        )

        # Every case names the **smallest masked index whose value is not
        # finite** — which, when mask 0 holds a finite value and mask 2 a `nan`,
        # is 2 and not the mask's first member (`divergence.md` §3).
        cases = (
            ("nan at index 1 over the singleton mask", (0.5, nan, 1.25), (1,), 1, "nan"),
            ("nan at index 1 over the whole vocabulary", (0.5, nan, 1.25), ALL_MASK, 1, "nan"),
            ("nan at index 0", (nan, 1.0, 2.0), (0, 2), 0, "nan"),
            ("nan at the last index", (0.0, 1.0, nan), ALL_MASK, 2, "nan"),
            ("two nan values, the smallest wins", (nan, 1.0, nan), ALL_MASK, 0, "nan"),
            ("two nan values under a mask without index 0", (nan, 1.0, nan), (1, 2), 2, "nan"),
            ("a masked infinity", (0.0, infinity, 1.0), ALL_MASK, 1, "inf"),
        )
        for label, values, mask, index, spelling in cases:
            with self.subTest(case=label):
                self.assert_agents_refusal(
                    tie_break,
                    values,
                    mask,
                    entry="_tie_break",
                    groups=(("index %d" % (index,),), (spelling,)),
                    label=label,
                )

    def test_agt16_7_the_finite_path_is_unchanged(self):
        """AGT-16.7 the finite path reports the pre-guard digits: AGT-6.1's masked and double-Q `td_error` to twelve places and an annealed learner's decided indices exactly, so the two predicates added no arithmetic (`divergence.md` §1, §4-§5, `rule.md` §3, §5, D-19, ASM-10)."""
        package = self.agents()
        records = batch(
            [dense_observation(0.03 * index) for index in range(11)]
        )
        masked = finite_float(
            package.learn(
                self.build(kind="naive-stack", width=6, depth=1), records
            )["td_error"],
            "the masked-q-learning td_error",
        )
        self.assertAlmostEqual(
            masked,
            GOLDEN_MASKED_TD_ERROR,
            places=12,
            msg="the masked rule's batch td_error moved away from the figure the "
            "implementation without guards reported, so the divergence guard "
            "added arithmetic to the update (divergence.md §1, §4, rule.md §3)",
        )
        double = finite_float(
            package.learn(
                self.build(
                    kind="naive-stack",
                    width=6,
                    depth=1,
                    extra={"learning_rule": "double-q-learning"},
                ),
                records,
            )["td_error"],
            "the double-q-learning td_error",
        )
        self.assertAlmostEqual(
            double,
            GOLDEN_DOUBLE_TD_ERROR,
            places=12,
            msg="the double-Q rule's batch td_error moved away from the figure the "
            "implementation without guards reported, so the guard changed the "
            "bootstrap index's arithmetic (divergence.md §1, §4, rule.md §2, §5)",
        )
        annealed = self.annealed_learner(
            "golden", {"kind": "naive-stack", "width": 8, "depth": 2}
        )
        pairs = self.decision_observations(self.decisions(), "naive-stack")
        actions = tuple(
            int(package.act(annealed, observation, mask)["action"])
            for observation, mask in pairs
        )
        self.assertEqual(
            actions,
            GOLDEN_ANNEALED_ACTIONS,
            "an annealed learner decides a different tuple than it did before the "
            "guards existed, so a decision's arithmetic or its keyed draw moved "
            "(divergence.md §1, §4, rule.md §4-§5, ASM-5)",
        )


if __name__ == "__main__":
    unittest.main()
