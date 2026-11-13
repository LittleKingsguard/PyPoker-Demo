"""AGT-19 — the member's finiteness envelope: the target bound and the parameter band.

Drives `docs/L1/counterfactual.md` §10 and `docs/L1/records.md` §12's conditional `finiteness`
block beside the L3 statements the two refusals are published under — `docs/L3/agents/
divergence.md` §2, §4, `docs/L3/agents/errors.md` §2-§4 — and `docs/L1/battery.md` §3's
FAM-23, D-45.

`strata/records/counterfactual-divergence.md` recorded the defect: the six-seat
`reveal-counterfactual` run died on its first transition of a new seed with
`LearningDiverged … got -inf`. `counterfactual.md` §10 answers it with **two bounds, not
another aggregation**, and this file is the module-level half of that answer:

* **the target, bounded by the game.** A counterfactual value is one seat's whole-hand net
  chip delta, so it lies inside the chips a hand holds; `T = seats × starting_stack`, the
  chips in play — read off `engine.game_config` here and never written down — is the bound
  in force. `learn` refuses, as the named `agents.errors.CounterfactualUnbounded`, any
  transition whose `counterfactual` carries a value with `|value| > T`, **before** any
  forward pass, any parameter change and any advance of the schedule position, and the
  message names `learn(transitions)`, the transition index (0-based in the caller's batch),
  the action index, the offending value and the bound. A value exactly at `±T` is inside the
  bound and is stepped normally (§10, §4, `records.md` §4).
* **the update, bounded by a declared parameter band.** `agents.declarations` declares
  `PARAMETER_BAND`, and no parameter of the learner's `2·P` array may leave `±PARAMETER_BAND`.
  `learn` refuses the batch as `agents.errors.LearningDiverged`, naming the site, the
  parameter index, the value found and the band, and it refuses **before any non-finite
  value is ever produced**: the check runs on the parameters at the start of a batch and
  after each step, so a container restored outside the band is refused before a forward
  pass, and **no refusal message ever reports a non-finite number** (`inf`, `-inf`, `nan`).
  The band's *number* is never restated here: it is read out of `agents.declarations`, which
  is why no case in this file fails on the digit a measurement chose (`counterfactual.md`
  §10, `docs/L3/agents/divergence.md` §2, §4).

The three cases are AGT-19.1 (a value past the bound refused by name, with the learner
untouched), AGT-19.2 (a value exactly at `+T` and one exactly at `−T` accepted and stepped)
and AGT-19.3 (a learner restored from a container whose parameters lie outside the band
refused by name, with no `inf` and no `nan` anywhere in the message).  Every number a case
uses is either the declaration's — the chips in play, the band — or this battery's own
invented instance (`docs/L1/battery.md` §4, D-15): the probe step over the bound, the
record count, the doctored parameter index and the seed are invented, and the two catalogue
member names are read off `agents.learners()`.

What this file does **not** assert is whether a diverging run completes or refuses: that is
the measurement recorded beside the artefacts in `counterfactual.md` §10, and the run-record
side of it is the integration battery's (`tests/integration/training/
test_counterfactual_pair.py`, `docs/L1/battery.md` §5).
"""

import io
import os
import re
import unittest
from collections.abc import Mapping

import numpy as np

from _agents_support import (
    LEARNER_SEED,
    AgentsCase,
    SurfaceAbsent,
    container_document,
    declared_module,
    dense_observation,
    engine,
    features,
    finite_float,
    learner_spec,
    plain_int,
    transition,
    write_container,
)

#: The records one batch carries in these cases.  Three is the smallest count that puts the
#: offending transition at an index that is neither the first nor the last, so "the index the
#: message names is the caller's own" is a claim and not a coincidence (`counterfactual.md`
#: §10: the transition index is 0-based in the caller's batch).  An invented instance.
RECORDS = 3

#: The index of the offending transition inside that batch, and the value every ordinary
#: transition of it carries: both invented (`docs/L1/battery.md` §4, D-15).
OFFENDER = 1
ORDINARY_TARGET = 1.0

#: How far past the bound the refused value sits: a whole chip over the chips in play, which
#: is the smallest margin a `float64` states exactly.  Invented.
PROBE_STEP = 5

#: The index of the parameter this file doctors in AGT-19.3, inside the container's `2·P`
#: array, and the multiple of the declared band it is set to: both invented, and neither is
#: the band (`counterfactual.md` §10 names the band a declaration, `checkpoint.md` §2 the
#: array).
DOCTORED_SLOT = 13
BAND_MULTIPLE = 4.0

#: A number as a refusal message states one: an integer or a decimal part, an optional
#: exponent included, and an optional sign.  The two bounds a message must name are read
#: this way rather than by one spelling of theirs (`docs/L3/agents/errors.md` §3 leaves the
#: wording to the implementation).
_NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


def numbers_in(text):
    """Every number a message states, read by value and never by spelling."""
    return [float(match.group(0)) for match in _NUMBER.finditer(str(text))]


def declared_class(name):
    """One refusal class `agents.errors` publishes, or `SurfaceAbsent` naming it.

    `docs/L1/counterfactual.md` §10 names the two refusals this file is about —
    `CounterfactualUnbounded` for a target with no bounded value and `LearningDiverged` for
    a parameter that would leave the declared band — so their names, and not only their
    behaviour, are contract here, and a missing one is the failure of the case that needed it
    rather than a `TypeError` from inside the battery (`errors.md` §2).
    """
    module = declared_module("errors")
    found = getattr(module, name, None)
    if not isinstance(found, type) or not issubclass(found, Exception):
        raise SurfaceAbsent(
            "agents.errors.%s is not declared, and counterfactual.md §10 names it as the "
            "refusal of the member's finiteness envelope" % (name,)
        )
    return found


def parameter_band():
    """`agents.declarations.PARAMETER_BAND`, the declared magnitude no parameter may exceed.

    `counterfactual.md` §10 makes the band a **declaration** — "no parameter of the `2·P`
    array may leave `±PARAMETER_BAND`" — and fixes its name, so it is read from the module
    on every call and never restated as a literal here: a case that typed the digit would
    be the second statement of a value the design leaves to a measurement.
    """
    module = declared_module("declarations")
    value = getattr(module, "PARAMETER_BAND", None)
    if value is None:
        raise SurfaceAbsent(
            "agents.declarations.PARAMETER_BAND is not declared, and counterfactual.md §10 "
            "makes it the band no parameter of a learner may leave"
        )
    return finite_float(float(value), "agents.declarations.PARAMETER_BAND")


class FinitenessEnvelope(AgentsCase):
    """The target bounded by the game, and the update bounded by the declared band."""

    # -- what the game and the catalogue declare (counterfactual.md §10) ----
    def member(self):
        """The catalogue member whose targets this file drives: the second, by order.

        `counterfactual.md` §6 publishes the catalogue with `none` first — the declared
        default, which reads no resolution at all — and `reveal-counterfactual` second, so
        the member a bound can fire under is read off the call and never spelled here.
        """
        catalogue = self.agents().learners()["counterfactuals"]
        names = [str(name) for name in catalogue]
        if len(names) < 2:
            raise SurfaceAbsent(
                "agents.learners()['counterfactuals'] publishes one member and "
                "counterfactual.md §6 declares two, `none` and `reveal-counterfactual`: %r"
                % (names,)
            )
        return names[1]

    def chips_in_play(self):
        """`T = seats × starting_stack` — the bound in force on the shape in force.

        `counterfactual.md` §10 declares the target bounded by the chips a hand can produce,
        and `shapes.md` §2 and `seats.md` §2 make that `pot + sum(stacks)` at every decision:
        40 on the default shape, 200 on the two-seat uncapped one and 600 on the six-seat one.
        Both numbers are read off `engine.game_config`, so no shape's arithmetic is restated
        here (`e2e-surface.md` §3.1, ASM-28, D-29, D-33).
        """
        config = engine().game_config()
        seats = plain_int(config["seats"], "engine.game_config()['seats']")
        stack = plain_int(
            config["starting_stack"], "engine.game_config()['starting_stack']"
        )
        self.assertGreater(seats, 0, "a shape seats at least one seat (seats.md §2)")
        self.assertGreater(stack, 0, "a shape's starting stack is positive (shapes.md §2)")
        return seats * stack

    def width(self):
        """`A`, the default shape's descriptor count, off `features.action_space` (`§3`)."""
        return len(features().action_space())

    def folder(self):
        """This case's own scratch directory, one per case and removed with it."""
        if getattr(self, "_folder", None) is None:
            self._folder = self.tempdir()
        return self._folder

    # -- the learner and the batches these cases drive ---------------------
    def member_learner(self, seed=LEARNER_SEED):
        """One dense learner small enough to read, built under the member.

        `naive-stack` at width 6 and depth 1 is the size the rest of this battery's guard
        cases build, and its declared `observation_size` is the default shape's 203, so the
        observations below are that width with no encoder handed to the build (`surface.md`
        §4, `architecture.md` §1, `docs/L2/features/capacity.md` §2).  The member is written
        into the spec as an explicit key, because absence would build the catalogue's first
        member and read no resolution at all (`counterfactual.md` §6, D-43).
        """
        return self.agents().build_learner(
            learner_spec(
                kind="naive-stack",
                width=6,
                depth=1,
                seed=seed,
                extra={"counterfactual": self.member()},
            )
        )

    def resolved(self, values):
        """One batch of **fully resolved** transitions, `values` one per record.

        `records.md` §4's record with every field the member reads: the two encoded
        observations, the applied index, the reward, the terminal flag, both legal masks,
        the episode boundary and a `counterfactual` sequence of `A` entries.  Every index is
        legal and every one carries that record's value, which is the shape `agents.learn`
        takes `A` semi-gradient steps on — a partial resolution would fall back to the
        ordinary path and no bound of §10's target would be read (`counterfactual.md` §4, §6,
        §10).  The observations are invented and seeded, so the forward pass of a case is a
        number this file can compare with itself and not a design value.
        """
        width = self.width()
        self.assertGreaterEqual(len(values), 1)
        mask = tuple(range(width))
        records = []
        for position, value in enumerate(values):
            records.append(
                transition(
                    dense_observation(0.03 * (position + 1)),
                    action=1,
                    reward=0.0,
                    terminal=False,
                    legal=mask,
                    next_legal=mask,
                    counterfactual=tuple(float(value) for _index in range(width)),
                )
            )
        return records

    def spilled(self, value):
        """A batch whose **one** transition carries a value no hand can produce.

        The transition at :data:`OFFENDER` carries ``value`` at the **last** legal action
        index, and every other record of the batch carries an ordinary in-bound target, so
        the transition index and the action index a refusal names are two different numbers
        that only that record can account for (`counterfactual.md` §10).
        """
        width = self.width()
        mask = tuple(range(width))
        records = self.resolved([ORDINARY_TARGET] * RECORDS)
        carried = [ORDINARY_TARGET] * width
        carried[width - 1] = float(value)
        records[OFFENDER] = transition(
            dense_observation(0.05 * (OFFENDER + 1)),
            action=1,
            reward=0.0,
            terminal=False,
            legal=mask,
            next_legal=mask,
            counterfactual=tuple(float(entry) for entry in carried),
        )
        return records

    def saved(self, learner, name):
        """One container of this learner, written into this case's own directory.

        `save` is the declared entry point for what a learner's parameters *are*
        (`checkpoint.md` §2, `surface.md` §8), so "the parameters did not move" and "the
        schedule position did not advance" are read off two containers this case wrote,
        never off an internal field.
        """
        return self.agents().save(learner, os.path.join(self.folder(), name))

    def state(self, learner, name):
        """`(parameters, position)` of one learner, off the container `save` wrote."""
        path = self.saved(learner, name)
        metadata, parameters = container_document(path)
        return parameters, plain_int(
            metadata["exploration"]["position"], "exploration.position"
        )

    def refusal(self, class_name, call, what):
        """The message of one refusal, after asserting it is the class the design names."""
        wanted = declared_class(class_name)
        try:
            call()
        except SurfaceAbsent:
            raise
        except Exception as exc:
            self.assertIsInstance(
                exc,
                wanted,
                "%s is refused as agents.errors.%s, the name counterfactual.md §10 gives "
                "that refusal, and it arrived as %s: %r"
                % (what, class_name, type(exc).__name__, str(exc)),
            )
            self.assertTrue(
                str(exc).strip(),
                "%s was refused with an empty message (errors.md §3)" % (what,),
            )
            return str(exc)
        self.fail(
            "%s was accepted, and counterfactual.md §10 makes it a named refusal rather "
            "than a value the learner reads" % (what,)
        )

    # -- AGT-19.1 ----------------------------------------------------------
    def test_agt19_1_a_target_beyond_the_chips_in_play_is_refused_by_name(self):
        """AGT-19.1 a `counterfactual` past `±(seats × starting_stack)` is refused as `CounterfactualUnbounded`, naming the transition index, the action index, the value and the bound, and the learner is untouched (`docs/L1/counterfactual.md` §10, §4, `docs/L1/records.md` §4, D-45).

        §10's first bound: a resolved value is one seat's whole-hand net chip delta, so it
        lies inside the chips a hand can produce, and `T = seats × starting_stack` — 40 on the
        default shape, read off `engine.game_config` here — is the declared bound.  A value
        with `|value| > T` is refused **by name**, not clamped and not learned from: a clamp
        would change the target the record already carries and make the member learn
        something a third party cannot recompute from that record.  The case drives it both
        ways — `T + 5` and `−(T + 5)` — because the bound is on the magnitude, and asserts
        what the refusal must say: `learn(transitions)`, the transition index in the caller's
        own 0-based order, the action index, the value and the bound.  And it asserts what
        the refusal must **not** do: the two containers this case wrote around it hold the
        same parameter bytes and the same schedule position, because the refusal is in front
        of the forward pass, the step and the position (`counterfactual.md` §10,
        `docs/L3/agents/divergence.md` §2, §4, `rule.md` §3).
        """
        package = self.agents()
        bound = self.chips_in_play()
        learner = self.member_learner()
        parameters_before, position_before = self.state(learner, "agt19-1-before.pt")
        width = self.width()
        for sign, value in (("a positive", bound + PROBE_STEP),
                            ("a negative", -(bound + PROBE_STEP))):
            message = self.refusal(
                "CounterfactualUnbounded",
                lambda value=value: package.learn(
                    learner, [dict(record) for record in self.spilled(value)]
                ),
                "a %s target of %r on a shape whose chips in play are %r"
                % (sign, value, bound),
            )
            lowered = message.lower()
            self.assertIn(
                "learn(transitions)",
                lowered,
                "the refusal names the call it refused, as errors.md §3's messages do: %r"
                % (message,),
            )
            self.assertIn(
                "transition",
                lowered,
                "the refusal names the transition index the offending value sat at "
                "(counterfactual.md §10): %r" % (message,),
            )
            self.assertIn(
                "action",
                lowered,
                "the refusal names the action index the offending value sat at "
                "(counterfactual.md §10): %r" % (message,),
            )
            stated = numbers_in(message)
            for wanted, what in (
                (float(OFFENDER), "the transition index — 0-based in the caller's batch"),
                (float(width - 1), "the action index"),
                (float(value), "the offending value"),
                (float(bound), "the bound in force"),
            ):
                self.assertTrue(
                    any(abs(number - wanted) <= 1e-9 for number in stated),
                    "the refusal names %s, %r, and the numbers it states are %r: %r"
                    % (what, wanted, stated, message),
                )
        parameters_after, position_after = self.state(learner, "agt19-1-after.pt")
        self.assertEqual(
            parameters_before,
            parameters_after,
            "a refused batch changes no parameter: the bound is checked before the forward "
            "pass and before any step of the transition it refuses (counterfactual.md §10, "
            "docs/L3/agents/divergence.md §4): the container's array moved",
        )
        self.assertEqual(
            position_before,
            position_after,
            "and it does not advance the learner's schedule position, which advances by the "
            "transitions a successful call consumed and by nothing else (counterfactual.md "
            "§10, rule.md §3, §4): %r against %r" % (position_before, position_after),
        )

    # -- AGT-19.2 ----------------------------------------------------------
    def test_agt19_2_a_target_exactly_at_the_bound_is_stepped(self):
        """AGT-19.2 a value exactly at `+T` and one exactly at `−T` are inside the bound, accepted, and take their steps (`docs/L1/counterfactual.md` §10, §6, D-45).

        §10 bounds the magnitude: a value at exactly `±T` is a whole-hand delta the game can
        produce — one seat winning or losing every chip in play is the extreme hand, and 40
        chips is what `seats × starting_stack` names on the default shape — so it is
        **stepped**, not refused.  The case drives one learner per sign and asserts the three
        observables a successful call leaves: `learn` returns the update's statistics with a
        finite learning signal, the members' steps move the parameters the container stores
        (one semi-gradient step per legal action, `counterfactual.md` §6), and the schedule
        position advances by the batch's **transitions** — three — and never by its steps
        (`counterfactual.md` §6, `rule.md` §3, §4).
        """
        package = self.agents()
        bound = self.chips_in_play()
        for sign, value in (("positive", float(bound)), ("negative", -float(bound))):
            with self.subTest(bound=sign):
                learner = self.member_learner()
                parameters_before, position_before = self.state(
                    learner, "agt19-2-%s-before.pt" % (sign,)
                )
                statistics = package.learn(
                    learner,
                    [dict(record) for record in self.resolved([value] * RECORDS)],
                )
                self.assertIsInstance(
                    statistics,
                    Mapping,
                    "learn returns the update's statistics for the curve on the finite path "
                    "too, and a case reads them as a mapping (rule.md §3, "
                    "e2e-surface.md §3.3): %r" % (statistics,),
                )
                self.assertIn(
                    "td_error",
                    statistics,
                    "the statistics carry the learning signal curves read (rule.md §3, "
                    "protocol.md §1): %r" % (sorted(statistics),),
                )
                signal = finite_float(float(statistics["td_error"]), "statistics['td_error']")
                self.assertGreaterEqual(
                    signal,
                    0.0,
                    "the learning signal is the mean **absolute** residual, so a batch of "
                    "resolved transitions reports a non-negative figure and never a "
                    "non-finite one (counterfactual.md §6, rule.md §3): %r" % (signal,),
                )
                parameters_after, position_after = self.state(
                    learner, "agt19-2-%s-after.pt" % (sign,)
                )
                self.assertNotEqual(
                    parameters_before,
                    parameters_after,
                    "a value exactly at the bound is stepped: one semi-gradient step per "
                    "legal action moves the parameters the container stores, and the "
                    "container's array is unchanged (counterfactual.md §6, §10)",
                )
                self.assertEqual(
                    position_after - position_before,
                    RECORDS,
                    "the schedule position advances by the batch's transitions — %d — and "
                    "never by the member's steps (counterfactual.md §6, rule.md §4): %r "
                    "against %r" % (RECORDS, position_after, position_before),
                )

    # -- AGT-19.3 ----------------------------------------------------------
    def test_agt19_3_a_restored_learner_outside_the_band_is_refused_without_infinity(self):
        """AGT-19.3 a learner restored from a container whose parameters lie outside `PARAMETER_BAND` refuses at its first `learn` as `LearningDiverged`, naming the parameter index, the value and the band, and no refusal message reports a non-finite number (`docs/L1/counterfactual.md` §10, `docs/L1/records.md` §4, D-45, `docs/L3/agents/divergence.md` §2).

        §10's second bound makes `-inf` unreachable rather than unlikely: `agents.declarations`
        declares `PARAMETER_BAND`, no parameter of the `2·P` array may leave `±PARAMETER_BAND`,
        and `learn` checks the parameters **at the start of a batch** as well as after each
        step — so a container restored outside the band is refused before a forward pass.  The
        case builds that container from `agents.save`'s own output by rewriting one weight,
        restores it through `agents.load`, which reads the file as it is, and drives one
        ordinary batch.  The band's number is read from the module and never repeated here,
        and the case asserts the last half of the argument on the message's **text**: it
        states no `inf` and no `nan`, because a guard that reported one would be the very
        spelling the fix exists to make impossible (`counterfactual.md` §10,
        `docs/L3/agents/divergence.md` §2, §4, `docs/L3/agents/errors.md` §3).
        """
        package = self.agents()
        band = parameter_band()
        self.assertGreater(
            band,
            0.0,
            "the declared parameter band is a positive magnitude, or it bounds nothing "
            "(counterfactual.md §10): %r" % (band,),
        )
        self.assertTrue(
            np.isfinite(band),
            "the band is a finite float, so the declared envelope is inside the range a "
            "float64 can hold (counterfactual.md §10): %r" % (band,),
        )
        folder = self.folder()
        source = package.save(
            self.member_learner(), os.path.join(folder, "agt19-3-source.pt")
        )
        metadata, blob = container_document(source)
        array = np.load(io.BytesIO(blob), allow_pickle=False)
        self.assertGreater(
            int(array.shape[0]),
            DOCTORED_SLOT,
            "the container's array holds the whole `2·P` array and the index this case "
            "doctors: %r (checkpoint.md §2)" % (array.shape,),
        )
        outside = np.array(array, copy=True)
        outside[DOCTORED_SLOT] = np.float64(BAND_MULTIPLE * band)
        value = float(outside[DOCTORED_SLOT])
        buffer = io.BytesIO()
        np.save(buffer, np.ascontiguousarray(outside), allow_pickle=False)
        doctored = write_container(
            os.path.join(folder, "agt19-3-doctored.pt"), metadata, buffer.getvalue()
        )
        spec = learner_spec(
            kind="naive-stack",
            width=6,
            depth=1,
            seed=LEARNER_SEED,
            extra={"counterfactual": self.member()},
        )
        restored = package.load(spec, doctored)
        message = self.refusal(
            "LearningDiverged",
            lambda: package.learn(
                restored,
                [dict(record) for record in self.resolved([ORDINARY_TARGET] * RECORDS)],
            ),
            "a learner restored with parameter %d at %r against a band of %r"
            % (DOCTORED_SLOT, value, band),
        )
        lowered = message.lower()
        self.assertIn(
            "parameter",
            lowered,
            "the refusal names the site it found the value at — the parameter — and not only "
            "the batch it read (counterfactual.md §10, divergence.md §2): %r" % (message,),
        )
        self.assertIn(
            "band",
            lowered,
            "the refusal names the band it crossed, so a reader can see which envelope the "
            "learner left (counterfactual.md §10): %r" % (message,),
        )
        stated = numbers_in(message)
        for wanted, what in (
            (float(DOCTORED_SLOT), "the parameter index"),
            (value, "the value it found"),
            (band, "the declared band"),
        ):
            self.assertTrue(
                any(abs(number - wanted) <= abs(wanted) * 1e-9 for number in stated),
                "the refusal names %s, %r, and the numbers it states are %r: %r"
                % (what, wanted, stated, message),
            )
        for spelling in ("inf", "nan"):
            self.assertNotIn(
                spelling,
                lowered,
                "no refusal message ever reports a non-finite number: counterfactual.md §10 "
                "makes the band refuse the step *before* a non-finite value is produced, so "
                "the word %r cannot appear in it: %r" % (spelling, message),
            )
        parameters_after, position = self.state(restored, "agt19-3-after.pt")
        self.assertEqual(
            parameters_after,
            buffer.getvalue(),
            "a learner refused at the start of its first batch is left with the container's "
            "own parameters: the check runs before the forward pass and before any step, so "
            "the array it was restored with is the array it still holds (counterfactual.md "
            "§10, divergence.md §4)",
        )
        self.assertEqual(
            position,
            plain_int(metadata["exploration"]["position"], "exploration.position"),
            "and its schedule position is the one the container recorded, so a refused "
            "batch consumed nothing (counterfactual.md §10, rule.md §4): %r" % (position,),
        )


if __name__ == "__main__":
    unittest.main()
