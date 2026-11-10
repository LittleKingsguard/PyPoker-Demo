"""JOIN-AGT-13 — the divergence refusal at the join.

`docs/L2/agents/divergence.md` §1–§4 is the authority for every claim in this file: the
measurement it answers (§1, `strata/records/lr-probe.md`), its two sites (§2), its four
messages (§3) and what it never does (§4).  It is the one refusal of this surface whose
fault is the learner's own accumulated state and never the caller's argument, so it is
the one a join can reach with legal instances only: a `records.md` §4 transition whose
`reward` is not finite is a number that section allows, and a container carrying a
non-finite parameter is read exactly as it always was
(`docs/L3/agents/errors.md` §4).  The class is `agents.errors.LearningDiverged`
(`docs/L3/agents/errors.md` §2), and, as everywhere in this corpus, the cases assert the
*behaviour* — that the call refuses, that it is catchable as `agents.errors.AgentsError`,
and what the message says (`docs/L3/agents/divergence.md` §3, `errors.md` §5) — never the
subclass name.

The four cases pin, in the order the two sites are reached:

* **13.1** — a transition whose `td_error` is not finite refuses inside `learn` before
  that transition's step is applied, naming `learn`, the transition's index, `td_error`
  and the value, and the learner's position does not advance (`divergence.md` §2–§4,
  `docs/L3/agents/rule.md` §3);
* **13.2** — a step that left a parameter not finite refuses inside `learn` after the
  step, naming `learn`, the transition's index, the parameter's index and the value
  (`divergence.md` §2–§3);
* **13.3** — a non-finite value of the masked set refuses inside the decision, raised by
  `decide`, on a learner restored from a doctored container: `load` gains nothing, and
  both `act` and a policy `as_policy` built refuse by that site's name, never
  `policy(readout)` (`divergence.md` §2, §4; `surface.md` §6, §9, §10);
* **13.4** — the finite path is unchanged: the same action and the same step, bit for
  bit, at the declared `learning_rate` (§1, `docs/L3/agents/rule.md` §6, ASM-7, D-19,
  D-20).

The constants of 13.4 are the **pre-guard** values.  The guard is uncommitted in the
working tree, so `HEAD` is the pre-guard code; the goldens were recorded once, before
this file existed, from that tree in a separate process, and the working tree then
reproduced them exactly:

    T=$(mktemp -d) && git archive HEAD src | tar -x -C "$T"
    PYTHONPATH="$T/src" .venv/bin/python "$T/goldens.py"   # HEAD's src -> the goldens
    PYTHONPATH=src .venv/bin/python "$T/goldens.py"        # fixed tree -> the same ones

`goldens.py` replays the fixtures JOIN-AGT-4.1 and JOIN-AGT-2.1 already drive (one seat
of one played episode at an invented deal; the first decision of a real hand), because
`tests/integration/agents/_join_support.py` puts the working tree's `src` on `sys.path`
itself and so cannot be imported into a pre-guard process.  Both processes printed
`td_error` `1.2273445678753505` over 4 transitions and action index `1`.
"""

import importlib.util
import io
import json
import os
import re
import sys
import unittest
import zipfile

import numpy

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

# The pre-guard goldens of JOIN-AGT-13.4, recorded as this module's docstring describes:
# `learn`'s td_error on JOIN-AGT-4.1's real batch, and `act`'s index at JOIN-AGT-2.1's
# real decision, both at the declared learning rate below (`rule.md` §6,
# `divergence.md` §1: the finite path is the same arithmetic, so the digits are the
# ones the pre-guard tree produced).
TD_ERROR_GOLDEN = 1.2273445678753505
ACTION_GOLDEN = 1
BATCH_LENGTH_GOLDEN = 4

#: `rule.md` §6's shipped learning rate, the one the goldens above were recorded at and
#: the one `divergence.md` §1 says stands as declared (ASM-7, D-19).  No case in this
#: file changes it for the finite path: 13.4 asserts it is still the catalogue's.
DECLARED_LEARNING_RATE = 0.001

#: The aggressive rate 13.2 patches in process.  A terminal reward of the hand's own
#: magnitude times a rate above 1.8 necessarily leaves `float64`'s finite range — which
#: is the overshoot `strata/records/lr-probe.md` measured (`divergence.md` §1) — while
#: the shipped 0.001 cannot do it on this fixture, so 13.2 proves that first and names
#: the patch as the cause of the refusal it then asserts.
AGGRESSIVE_LEARNING_RATE = 10.0

#: `records.md` §4's reward is any number, so this one is a legal transition value
#: (`divergence.md` §4, `errors.md` §4) that only the arithmetic can object to.
HUGE_REWARD = 1e308

#: The schedule-position fields a container may record (`checkpoint.md` §2.1); the reader
#: below stays tolerant of the spelling instead of pinning one (`battery.md` §4).
POSITION_FIELDS = ("position", "steps", "decisions", "consumed")

#: The two spellings a non-finite value prints as in a refusal — `%r` of the `float`, so
#: `divergence.md` §3's sites report whichever of them the arithmetic produced.
VALUE_TOKENS = ("nan", "inf")


# --------------------------------------------------------------------------
# Container surgery: the two members of `checkpoint.md` §2, out and back.
# --------------------------------------------------------------------------
def _members(path):
    """`(metadata name, metadata bytes, parameters name, parameters bytes)` of `path`.

    `checkpoint.md` §2: a checkpoint is one zip carrying a `metadata.json` and a
    `parameters.npy`.  The two are told apart by their content rather than by a literal
    member name, so 13.3 puts back the same two members under the same two names and
    the container it leaves is one `load` reads as it read the writer's.
    """
    with zipfile.ZipFile(path) as container:
        held = [(name, container.read(name)) for name in container.namelist()]
    metadata_name = metadata = parameters_name = parameters = None
    for name, payload in held:
        try:
            json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            parameters_name, parameters = name, payload
            continue
        metadata_name, metadata = name, payload
    if metadata is None or parameters is None:
        raise AssertionError(
            "the container %r must carry one metadata member and one parameters "
            "member (docs/L3/agents/checkpoint.md §2); it carries %r"
            % (path, [name for name, _payload in held])
        )
    return metadata_name, metadata, parameters_name, parameters


def _metadata(path):
    """The `metadata.json` object of one container (`checkpoint.md` §2.1)."""
    _name, raw_metadata, _other, _raw = _members(path)
    return json.loads(raw_metadata.decode("utf-8"))


def _recorded_position(path):
    """The schedule position the container at `path` records (`checkpoint.md` §2.1).

    Reading it back out of the file is how a case observes what `learn` did to the
    position without importing an internal of `src/agents`.
    """
    held = _metadata(path)
    for outer in held.values():
        if not isinstance(outer, dict):
            continue
        for key, value in outer.items():
            if (
                str(key).lower() in POSITION_FIELDS
                and isinstance(value, int)
                and not isinstance(value, bool)
            ):
                return int(value)
    raise AssertionError(
        "cannot read a schedule position out of the container %r: %r" % (path, held)
    )


def _npy_bytes(array):
    """One 1-D `float64` array as the bytes of a `.npy` member (`checkpoint.md` §2)."""
    buffer = io.BytesIO()
    numpy.save(buffer, numpy.ascontiguousarray(array), allow_pickle=False)
    return buffer.getvalue()


def _rewrite(path, members):
    """Rewrite the container at `path` with exactly these `(name, bytes)` members."""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as container:
        for name, payload in members:
            container.writestr(name, payload)


def _hyper():
    """The six fixed declarations `learn` re-reads at call time (`rule.md` §6).

    `learners()` hands back a rebuilt copy of the six declarations, so a case that
    needs the aggressive rate of 13.2 must patch the declaration `learn` itself reads;
    this is the only `src/agents` name in this file that is not one of the ten entry
    points or `agents.errors.AgentsError`.
    """
    return J.mod("agents").declarations.HYPER


class DivergenceAtTheJoin(J.JoinCase):
    """The one refusal of accumulated state, reached through the three open doors."""

    # ------------------------------------------------------------------
    # The fixtures.  Two invented deals and the two learners the catalogue sizes.
    # ------------------------------------------------------------------
    def spec(self):
        """One learner spec at the join's invented sizes (`docs/L1/records.md` §3)."""
        return J.learner_spec(
            "naive-stack", J.WIDTH_ONE, J.DEPTH_ONE, J.LEARNER_SEED
        )

    def encoder(self):
        return J.build_encoder(J.encoding_for("naive-stack"))

    def batch(self, encoder):
        """One real transition batch: one seat of one played episode (`records.md` §4)."""
        record = J.play_hand(J.DEAL_REWARD_A, J.caller, J.caller)
        batch = J.seat_transitions(record, 0, encoder)
        self.assertGreaterEqual(
            len(batch),
            2,
            "the fixture must offer a transition whose step is not its first, or the "
            "guard of docs/L2/agents/divergence.md §2 would sit outside the update",
        )
        return batch

    def decision(self, encoder, deal=J.DEAL_DECISION_A):
        """One real decision: ``(readout, legal, observation, mask)`` (`surface.md` §6)."""
        hand = J.new_hand(deal)
        facts = J.readout(hand)
        legal = J.legal_actions(hand)
        return facts, legal, J.encode(encoder, facts), J.legal_indices(legal)

    # ------------------------------------------------------------------
    # The refusal reader.  The class is asserted by behaviour, not by name.
    # ------------------------------------------------------------------
    def refusal(self, call, note=""):
        """The message of the refusal `call` raised, which must be `AgentsError`.

        The case base's `assert_refusal` asks the same question of a message and leaves
        the class to L3; this reader asks it once, catching the refusal itself, because
        `docs/L3/agents/errors.md` §2 declares `AgentsError` the base of every refusal of
        this module and `docs/L3/agents/divergence.md` §1 puts the divergence refusal
        under it — so a case can require the class by behaviour ("this module refused
        me") without naming the subclass (`errors.md` §5).
        """
        base = J.mod("agents.errors").AgentsError
        try:
            result = call()
        except J.SurfaceAbsent:
            raise
        except Exception as exc:  # noqa: BLE001 - the class is L3's freedom
            self.assertIsInstance(
                exc,
                base,
                "%s: the refusal must be catchable as agents.errors.AgentsError "
                "(docs/L3/agents/errors.md §2, docs/L3/agents/divergence.md §1), got "
                "%s: %s" % (note, type(exc).__name__, exc),
            )
            return str(exc)
        self.fail(
            "%s: the call must refuse and name the divergence, but it returned %r "
            "(docs/L2/agents/divergence.md §2)" % (note, result)
        )

    def assert_names(self, message, groups, note=""):
        """Every group — one spelling or a tuple of them — appears in `message`."""
        lowered = message.lower()
        for group in groups:
            alternatives = (group,) if isinstance(group, str) else tuple(group)
            if not any(str(alternative).lower() in lowered for alternative in alternatives):
                self.fail(
                    "%s: the refusal must name one of %r; the message was %r "
                    "(docs/L3/agents/errors.md §3)"
                    % (note, alternatives, message)
                )

    # ------------------------------------------------------------------
    # 13.1 — the update's first guard.
    # ------------------------------------------------------------------
    def test_join_agt_13_1_a_non_finite_delta_refuses_by_name(self):
        """JOIN-AGT-13.1 a non-finite td_error refuses by name and leaves the position.

        `docs/L2/agents/divergence.md` §2–§4: `learn` refuses a transition whose
        `td = target − q[a]` is not finite **before** that transition's step is applied
        and before `|td|` is accumulated, names the entry point, the transition's index
        in the caller's order and the value, returns no statistics, and leaves the
        schedule position where it was.  A non-finite `reward` is a number `records.md`
        §4 allows, so the batch itself is not refused (`errors.md` §4) — which the
        control learner below shows by consuming it.
        """
        encoder = self.encoder()
        spec = self.spec()
        batch = self.batch(encoder)

        # The batch is a legal batch: an undoctored copy is consumed in full, so the
        # refusal asserted below is the update's and not a validation's.
        control = J.build_learner(spec)
        accepted = J.learn(control, batch)
        self.assertEqual(
            J.transitions_consumed(accepted),
            len(batch),
            "the fixture's batch must pass validation whole (docs/L1/records.md §4)",
        )
        self.assertTrue(J.finite(J.td_error(accepted)))

        learner = J.build_learner(spec)
        doctored = [dict(transition) for transition in batch]
        index = 1
        doctored[index]["reward"] = float("nan")
        message = self.refusal(
            lambda: J.learn(learner, doctored), "JOIN-AGT-13.1"
        )
        self.assert_names(
            message,
            ("learn", "transition index %d" % (index,), "td_error", "nan", "diverged"),
            "JOIN-AGT-13.1",
        )

        # The position did not advance (`divergence.md` §2, §4, `rule.md` §3): the
        # container records it, and a subsequent well-formed batch reports — and
        # counts — its own transitions only.
        J.save(learner, self.checkpoint_path(J.CHECKPOINT_ALPHA))
        self.assertEqual(
            _recorded_position(self.checkpoint_path(J.CHECKPOINT_ALPHA)),
            0,
            "a refused batch must leave the schedule position where it was "
            "(docs/L2/agents/divergence.md §2, docs/L3/agents/rule.md §3)",
        )
        probe = J.tiled(batch, J.BATCH_LENGTH)
        after = J.learn(learner, probe)
        self.assertEqual(
            J.transitions_consumed(after),
            J.BATCH_LENGTH,
            "a well-formed batch after a refusal reports its own transitions only "
            "(docs/L2/agents/surface.md §7)",
        )
        self.assertTrue(J.finite(J.td_error(after)))
        J.save(learner, self.checkpoint_path(J.CHECKPOINT_BETA))
        self.assertEqual(
            _recorded_position(self.checkpoint_path(J.CHECKPOINT_BETA)),
            J.BATCH_LENGTH,
            "the position counts the transitions of the batch that was consumed and "
            "none of the batch that was refused (docs/L2/agents/divergence.md §4)",
        )

        # The doctored transition's step was never applied: the steps before it stand
        # and nothing else (divergence.md §2, §4), so the parameters the refusal left
        # are the ones the well-formed prefix's steps produce, and the next update
        # reports the same td_error to the last digit.
        prefix = J.build_learner(spec)
        J.learn(prefix, doctored[:index])
        self.assertEqual(
            J.td_error(J.learn(prefix, probe)),
            J.td_error(after),
            "the transition whose td_error was not finite was stepped and then "
            "refused, or a transition before it was not: the learner must be left at "
            "the state the steps before it produced "
            "(docs/L2/agents/divergence.md §2, §4)",
        )

    # ------------------------------------------------------------------
    # 13.2 — the update's second guard.
    # ------------------------------------------------------------------
    def test_join_agt_13_2_a_non_finite_parameter_refuses_by_name(self):
        """JOIN-AGT-13.2 a step that leaves a parameter non-finite refuses by name.

        `docs/L2/agents/divergence.md` §2–§3: after its step, `learn` checks every
        parameter — the online values and the target copy together — and refuses a step
        that left one out of finite range, naming `learn`, the transition's index, the
        first parameter index out of range and the value.  The route is the measured
        one: an aggressive `learning_rate` over a real terminal transition whose
        `reward` is a huge finite number (`strata/records/lr-probe.md`,
        `docs/L3/agents/divergence.md` §1).  `learn` re-reads the declaration at call
        time (`rule.md` §6), so the rate is patched in process and restored by
        `addCleanup`, and the declared 0.001 is shown not to overshoot this fixture
        first — which is why the patch, and not the reward, is what the refusal reports.
        """
        encoder = self.encoder()
        spec = self.spec()
        terminal = [
            dict(transition)
            for transition in self.batch(encoder)
            if bool(transition["terminal"])
        ]
        self.assertEqual(
            len(terminal),
            1,
            "a seat's batch carries exactly one terminal transition "
            "(docs/L1/records.md §4, §5)",
        )
        terminal[0]["reward"] = HUGE_REWARD

        # The control: at the declared rate the same transition is stepped and the
        # update reports the huge td_error it produced (no refusal, nothing clipped).
        declared = J.build_learner(spec)
        survived = J.learn(declared, terminal)
        self.assertEqual(J.transitions_consumed(survived), 1)
        self.assertGreater(
            J.td_error(survived),
            1e300,
            "the fixture's reward must be the huge finite one this case steps on "
            "(docs/L2/agents/divergence.md §4)",
        )

        hyper = _hyper()
        original = hyper["learning_rate"]
        self.addCleanup(hyper.__setitem__, "learning_rate", original)
        hyper["learning_rate"] = AGGRESSIVE_LEARNING_RATE
        learner = J.build_learner(spec)
        # The overflow is the case: silence its arithmetic's diagnostic, not the
        # refusal the module must raise for it (`divergence.md` §2).
        with numpy.errstate(over="ignore", invalid="ignore"):
            message = self.refusal(
                lambda: J.learn(learner, terminal), "JOIN-AGT-13.2"
            )
        self.assert_names(
            message,
            ("learn", "transition index 0", "parameter index", "diverged", VALUE_TOKENS),
            "JOIN-AGT-13.2",
        )
        self.assertRegex(
            message,
            re.compile(r"parameter index \d+"),
            "the refusal must name the first parameter index out of finite range "
            "(docs/L2/agents/divergence.md §3)",
        )

    # ------------------------------------------------------------------
    # 13.3 — the decision's defensive guard, from a loaded container.
    # ------------------------------------------------------------------
    def test_join_agt_13_3_a_non_finite_masked_value_refuses_from_a_loaded_container(self):
        """JOIN-AGT-13.3 a doctored container loads, and its decisions refuse by site.

        `docs/L2/agents/divergence.md` §4 and `docs/L3/agents/divergence.md` §1: `load`
        gains nothing — a container carrying a non-finite parameter is read exactly as
        it was, and the refusal arrives at the restored member's first decision.  §2 of
        the same document puts that refusal in `decide`, which checks the masked values
        before either arm, so one raise serves `act` and every policy `as_policy` builds
        and the message names the raising site and never `act` or `policy(readout)`
        (`surface.md` §6, §10).
        """
        encoder = self.encoder()
        spec = self.spec()
        learner = J.build_learner(spec)
        J.learn(learner, self.batch(encoder))
        path = J.save(learner, self.checkpoint_path(J.CHECKPOINT_GAMMA))

        # Doctor the online half of the parameter member and put the same two members
        # back under their own names (checkpoint.md §2): the array is the online
        # parameters, then the target copy, then each sparse layer's mask.
        metadata_name, raw_metadata, parameters_name, raw_parameters = _members(path)
        count = J.param_count(learner)
        array = numpy.load(io.BytesIO(raw_parameters), allow_pickle=False)
        self.assertGreaterEqual(
            int(array.shape[0]),
            2 * count,
            "the container's array must begin with the online half the count names "
            "(docs/L3/agents/checkpoint.md §2)",
        )
        array[:count] = numpy.nan
        _rewrite(
            path,
            [
                (metadata_name, raw_metadata),
                (parameters_name, _npy_bytes(array)),
            ],
        )

        # `load` gained no refusal: the file is read as it always was.
        restored = J.load(None, path)
        self.assertEqual(
            J.param_count(restored),
            count,
            "a container carrying a non-finite parameter still restores, with the "
            "capacity it records (docs/L2/agents/surface.md §9, "
            "docs/L2/agents/divergence.md §4)",
        )

        facts, legal, observation, mask = self.decision(encoder)
        message = self.refusal(
            lambda: J.act(restored, observation, mask), "JOIN-AGT-13.3 act"
        )
        self.assert_names(
            message,
            (
                "decide",
                "index %d" % (mask[0],),
                "not finite",
                "diverged",
                VALUE_TOKENS,
            ),
            "JOIN-AGT-13.3 act",
        )
        self.assertNotIn(
            "_tie_break",
            message.lower(),
            "the refusal must name the site that raised, and `decide` checks the "
            "masked values before the tie-break "
            "(docs/L2/agents/divergence.md §2–§3)",
        )

        policy = J.as_policy(restored, encoder, J.POLICY_SEED)
        by_policy = self.refusal(
            lambda: policy(facts, legal), "JOIN-AGT-13.3 policy"
        )
        self.assert_names(
            by_policy,
            ("decide", "index %d" % (mask[0],), "not finite", VALUE_TOKENS),
            "JOIN-AGT-13.3 policy",
        )
        self.assertNotIn(
            "policy(readout)",
            by_policy.lower(),
            "one raise serves `act`, every policy and `learn`'s bootstrap, so the "
            "message names the raising site and not the policy's own refusal "
            "(docs/L2/agents/divergence.md §3, docs/L3/agents/divergence.md §2)",
        )

    # ------------------------------------------------------------------
    # 13.4 — the finite path is unchanged.
    # ------------------------------------------------------------------
    def test_join_agt_13_4_the_finite_path_is_unchanged(self):
        """JOIN-AGT-13.4 the same action and the same step, at the declared rate.

        `docs/L2/agents/divergence.md` §1: the six declarations, the two rules, the two
        utilities and the tie-break are untouched, so a finite batch takes the same
        steps and `act` makes the same decision — bit for bit (ASM-7, ASM-10, D-19,
        D-20, `docs/L3/agents/rule.md` §3, §6).  The constants are the pre-guard values
        this module's docstring records and says how to record again: JOIN-AGT-4.1's
        real batch and JOIN-AGT-2.1's real decision, replayed here.
        """
        self.assertEqual(
            float(J.learners()["hyper"]["learning_rate"]),
            DECLARED_LEARNING_RATE,
            "this case compares the pre-guard digits at the declared learning rate, "
            "which no case may patch (docs/L3/agents/rule.md §6, "
            "docs/L2/agents/divergence.md §1, ASM-7)",
        )
        encoder = self.encoder()
        spec = self.spec()
        learner = J.build_learner(spec)
        batch = self.batch(encoder)
        self.assertEqual(
            len(batch),
            BATCH_LENGTH_GOLDEN,
            "the golden was recorded over this many transitions of one seat's episode "
            "(docs/L1/records.md §4, §5)",
        )
        statistics = J.learn(learner, batch)
        self.assertEqual(
            float(J.td_error(statistics)),
            TD_ERROR_GOLDEN,
            "learn's td_error must be the pre-guard value to the last digit: the "
            "guards added no arithmetic and reordered none "
            "(docs/L2/agents/divergence.md §1, docs/L3/agents/divergence.md §1)",
        )
        self.assertEqual(J.transitions_consumed(statistics), BATCH_LENGTH_GOLDEN)

        # The same call again: `act` advances nothing (`rule.md` §1), and a second
        # learner from one spec is the same learner (`surface.md` §4), so the numbers
        # do not move (ASM-2, ASM-5).
        facts, legal, observation, mask = self.decision(encoder)
        actor = J.build_learner(spec)
        first = J.action_index(J.act(actor, observation, mask))
        self.assertEqual(
            first,
            ACTION_GOLDEN,
            "act's index must be the pre-guard value (docs/L2/agents/divergence.md §1)",
        )
        self.assert_index_in(first, mask, "JOIN-AGT-13.4")
        self.assertEqual(
            J.action_index(J.act(actor, observation, mask)),
            first,
            "one state and one decision give one answer, so a repeated call returns "
            "the same index (docs/L3/agents/rule.md §1, docs/L2/agents/surface.md §6)",
        )
        self.assertEqual(
            J.action_index(J.act(J.build_learner(spec), observation, mask)),
            ACTION_GOLDEN,
            "a learner built from one spec is the same learner, so the decision is "
            "reproducible (docs/L2/agents/surface.md §4)",
        )
        again = J.learn(J.build_learner(spec), batch)
        self.assertEqual(
            float(J.td_error(again)),
            TD_ERROR_GOLDEN,
            "the same batch on a learner from the same spec must report the same "
            "td_error again (docs/L2/agents/divergence.md §1)",
        )


if __name__ == "__main__":
    unittest.main()
