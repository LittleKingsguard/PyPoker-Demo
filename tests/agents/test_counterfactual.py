"""AGT-18 — the third catalogue, the transition record's resolution, and its container.

Drives `docs/L1/counterfactual.md` §2-§6 and §9 and `strata/decisions.md` D-43, beside the L1
statements the same contract is published under — `docs/L1/records.md` §4, `docs/L2/agents/
surface.md` §3-§4, §8-§10, `docs/L3/agents/checkpoint.md` §2.1-§3, `docs/L1/battery.md` §5 and
`docs/L3/agents/errors.md` §1-§4: `learners()` publishes a **third** catalogue under
`counterfactuals`, after `utilities` and before `hyper`, of two members in a declared order —
`none`, the rule's own target and one step per transition, which is the declared default,
then `reveal-counterfactual`, whose residual is the transition's own whole-hand value at
every legal action and whose step count is one per legal action — each a record of exactly
three keys, its `name`, the `reads` it takes its residual from and its `steps`, each value a
stable token and never a sentence (`counterfactual.md` §6).  A learner spec selects one with
`counterfactual`, an absent key being the catalogue's first member and never a value
inferred from the caller's silence; a name the catalogue does not carry — a non-string
included — is refused by name and never defaulted (§6, `surface.md` §4, `errors.md` §3).
It is neither a rule nor a utility: a rule owns the **bootstrap** and a utility owns one
terminal number read by `training`, while this names what a learner takes its **targets**
from, which `learn` alone reads and every container it writes records (`counterfactual.md`
§6, `rules.md` §3, `utilities.md` §3, D-19, D-20, D-43).

The record it feeds gains two keys, and neither is a rule's (`counterfactual.md` §2, §4-§5,
`records.md` §4).  `episode` is **required** and an integer: a float, a `None`, a flag and a
string are refused by name, a `numpy` integer is accepted.  `counterfactual` is **optional**
and is `None` or a sequence of `A` entries, `A` the shape's descriptor count, a number at
every index of the transition's own `legal` mask and `None` outside it: a wrong length and a
non-`None` value at an illegal index are refused by name, while a `None` at a legal one is a
resolution the member does not read and falls back from.  And the container carries the
member a learner was trained under: one under `none` writes exactly the version it wrote
before — 3 on the default shape and 4 on another — with **no** `counterfactual` field, while
one under any other member writes **format version 5** with that field immediately after
`utility`; versions 1-4 are read as `none` and must not carry the field, a version-5
container without it is refused, and one naming the declared default is refused too
(`checkpoint.md` §2.1, §3, `counterfactual.md` §9, D-43).

`docs/L1/battery.md` §5 draws the boundary this file exists for: the member has no entry
point of its own, so its catalogue, the spec key that selects it, the two record keys, its
step count, the container's field and the attribute a policy carries are asserted **here**,
one layer below the e2e battery that drives the same surface through `training`.  Three
spellings below an entry point are read here and all three are contract: `counterfactuals`
through `learners()` (`surface.md` §3), the member a learner carries through `as_policy`'s
`counterfactual` (`e2e-surface.md` §2, `surface.md` §10), and the container's own
`metadata.json`, whose member names and field order `checkpoint.md` §2 and §2.1 fix.  Every
container a case doctors is built by rewriting one this module wrote — both members the
file's own bytes, the version and the field the case is about rewritten
(`container_document`, `write_container`, `version_container`) — so no case here writes under
`checkpoints/` (`surface.md` §8, `module-map.md` §5, ASM-18).
"""

import io
import os
import unittest
from collections.abc import Mapping

import numpy as np

from _agents_support import (
    ALL_MASK,
    LEARNER_SEED,
    OTHER_SHAPE,
    AgentsCase,
    batch,
    container_document,
    declared_internal,
    dense_observation,
    finite_float,
    flat_encoder,
    learner_spec,
    plain_int,
    shape_encoder,
    target_interval,
    transition,
    version_container,
    write_container,
)

#: The two catalogue members, in `counterfactual.md` §6's declared order, each with the
#: `reads` it takes its residual from and its `steps`.  These are **design tokens** — the
#: spelling `learners()` publishes — and not invented instances: §6's table and D-43 fix
#: every one of them.
DECLARED_COUNTERFACTUALS = (
    ("none", "the-rule-own-target", "one-per-transition"),
    (
        "reveal-counterfactual",
        "whole-hand-value-at-every-legal-action",
        "one-per-legal-action",
    ),
)

#: The declared default of `counterfactual.md` §6: the catalogue's **first** member, which is
#: what a spec naming none is built under and what a version-1-to-4 container is read as.
DECLARED_DEFAULT = "none"

#: The sentence punctuation a stable token carries none of: the test AGT-2.3 applies to a
#: rule's `target` (`surface.md` §3), applied here to `reads` and `steps`.
FORBIDDEN_IN_A_TOKEN = ".,;:!?\"'()"

#: An invented name the catalogue does not carry (`battery.md` §4, D-15): no document in
#: `docs/` or `strata/` holds the spelling, and it names no member of any catalogue.
UNCATALOGUED_COUNTERFACTUAL = "monte-carlo"

#: The fourteen fields a container of the **default** shape under `none` records, in the
#: order its document holds them: `utility` immediately after `learning_rule`, no `game` and
#: no `counterfactual` (`checkpoint.md` §2.1, §3, `utilities.md` §6, `counterfactual.md` §6).
CONTAINER_KEYS = (
    "format",
    "format_version",
    "dtype",
    "backend",
    "kind",
    "learning_rule",
    "utility",
    "settings",
    "representation",
    "seed",
    "exploration",
    "target",
    "params",
    "tie_break",
)

#: One invented resolution, one value per descriptor of `ALL_MASK`'s order: three whole-hand
#: net chip deltas, none of them a design number (`counterfactual.md` §4-§5, `records.md` §4).
RESOLUTION = (-1.5, 0.25, 2.0)

#: The invented record count of the paired batches of AGT-18.6, whose `A·32` steps stay below
#: the declared target interval, so no refresh has fired when the case reads the counter.
PAIRED_RECORDS = 32


def spec(under=None, extra=None, **kwargs):
    """One invented learner spec, under `under` when a case names a member.

    A dense kind at width 6 and depth 1, so `flat_encoder` is the encoder any policy of it is
    built with (`learner.md` §6, `surface.md` §10).  `counterfactual` is written **only** when
    a case names a member, because absence **is** the declared default and is not a
    defaulting of a name (`counterfactual.md` §6, `records.md` §3, D-43).
    """
    pairs = dict(extra or {})
    if under is not None:
        pairs["counterfactual"] = under
    return learner_spec(
        kind="naive-stack", width=6, depth=1, extra=pairs or None, **kwargs
    )


def parameters(path):
    """One container's whole `parameters.npy` array: online block, target copy and masks.

    A checkpoint is one zip of `metadata.json` and `parameters.npy` (`checkpoint.md` §2), and
    the array is one 1-D `float64` of length `2·P + M` — the online parameters, the target
    copy, then each sparse layer's mask — so a case that has to say what a `learn` call wrote
    reads it here rather than through the metadata's tensor table (`checkpoint.md` §2.1).
    """
    _metadata, blob = container_document(path)
    return np.load(io.BytesIO(blob), allow_pickle=False)


class CounterfactualCatalogueTest(AgentsCase):
    """The third catalogue, the sixth key, and the spec's `counterfactual`."""

    def test_agt18_1_the_third_catalogue(self):
        """AGT-18.1 `counterfactuals` is exactly two members in the declared order, each carrying only `name`, `reads` and `steps` in that order, and a learner built without the key is the catalogue's first member (`docs/L1/counterfactual.md` §6, `docs/L2/agents/surface.md` §3, `docs/L3/agents/checkpoint.md` §2.1, D-43, D-19, D-20).

        §6 publishes the catalogue through `learners()`: two members in that order, each a
        plain record of its `name`, the `reads` it takes its residual from and its `steps`,
        both as a **stable token and never a sentence** — no whitespace, no sentence
        punctuation — because a record quotes the token as a name (`surface.md` §3).  The
        order is contract and not decoration: its first member is the declared default, so
        the order and the default are one statement.  The two members must differ in **both**
        fields, or one of them would read the rule's target and take the rule's step count
        under another name (`counterfactual.md` §6).
        """
        package = self.agents()
        catalogue = package.learners()["counterfactuals"]
        self.assertIsInstance(
            catalogue,
            Mapping,
            "learners()['counterfactuals'] is one plain record of the catalogue's members "
            "(counterfactual.md §6, surface.md §3)",
        )
        self.assertEqual(
            tuple(catalogue),
            tuple(name for name, _reads, _steps in DECLARED_COUNTERFACTUALS),
            "counterfactuals is keyed by the two catalogue members in counterfactual.md §6's "
            "declared order — none first, the declared default — and each key is the "
            "member's own name (surface.md §3, D-43)",
        )
        readings, steppings = [], []
        for name, entry in catalogue.items():
            with self.subTest(counterfactual=name):
                self.assertIsInstance(
                    entry,
                    Mapping,
                    "a catalogue member is one plain record (counterfactual.md §6)",
                )
                self.assertEqual(
                    tuple(entry),
                    ("name", "reads", "steps"),
                    "a member carries its name, the reads it takes its residual from and its "
                    "steps, in that order, and nothing else (counterfactual.md §6, "
                    "surface.md §3): %r" % (tuple(entry),),
                )
                self.assertEqual(
                    entry["name"],
                    name,
                    "a catalogue member's `name` is the key it is published under",
                )
                for field in ("reads", "steps"):
                    token = entry[field]
                    where = "the %s of the member %r" % (field, name)
                    self.assertIsInstance(
                        token,
                        str,
                        "%s is a stable token, so it is a string (counterfactual.md §6): %r"
                        % (where, token),
                    )
                    self.assertTrue(
                        token.strip(), "%s is a non-empty token: %r" % (where, token)
                    )
                    self.assertEqual(
                        token,
                        token.strip(),
                        "%s carries surrounding whitespace: %r" % (where, token),
                    )
                    forbidden = [
                        character
                        for character in token
                        if character.isspace() or character in FORBIDDEN_IN_A_TOKEN
                    ]
                    self.assertEqual(
                        forbidden,
                        [],
                        "%s carries %r: counterfactual.md §6 declares a stable token and "
                        "never a sentence, and this is the token test surface.md §3 fixes for "
                        "a rule's target (AGT-2.3)" % (where, forbidden),
                    )
                readings.append(entry["reads"])
                steppings.append(entry["steps"])
        self.assertEqual(
            len(set(readings)),
            len(readings),
            "the two members take their residuals from the same place, and these are "
            "identical: %r (counterfactual.md §6)" % (readings,),
        )
        self.assertEqual(
            len(set(steppings)),
            len(steppings),
            "the two members state one step count, and these are identical: %r "
            "(counterfactual.md §6)" % (steppings,),
        )
        for name, reads, steps in DECLARED_COUNTERFACTUALS:
            with self.subTest(declared=name):
                self.assertEqual(
                    catalogue[name]["reads"],
                    reads,
                    "the member %r reads %r, the stable token counterfactual.md §6's table "
                    "declares (D-43)" % (name, reads),
                )
                self.assertEqual(
                    catalogue[name]["steps"],
                    steps,
                    "the member %r takes %r, the step count counterfactual.md §6's table "
                    "declares (D-43)" % (name, steps),
                )
        self.assertEqual(
            tuple(catalogue)[0],
            DECLARED_DEFAULT,
            "the catalogue's first member — the default a spec naming no `counterfactual` is "
            "built under — is %r (counterfactual.md §6, records.md §3, D-43)"
            % (DECLARED_DEFAULT,),
        )
        # The declared default, observed through the public surface a caller has: a learner
        # built with no `counterfactual` key reports the member its policy carries
        # (`surface.md` §10, `e2e-surface.md` §2), and its container is the version this
        # module wrote before the axis existed (`checkpoint.md` §2.1, §3).
        learner = package.build_learner(spec())
        policy = package.as_policy(learner, flat_encoder(), LEARNER_SEED)
        self.assertEqual(
            getattr(policy, "counterfactual", None),
            DECLARED_DEFAULT,
            "a learner built with no `counterfactual` key takes its targets from the "
            "catalogue's first member, %r, and its policy carries that member "
            "(surface.md §10, counterfactual.md §6, D-43): %r"
            % (DECLARED_DEFAULT, getattr(policy, "counterfactual", None)),
        )
        folder = self.tempdir()
        path = package.save(learner, os.path.join(folder, "default-8127.pt"))
        metadata, _parameters = container_document(path)
        self.assertEqual(
            plain_int(metadata["format_version"], "metadata['format_version']"),
            3,
            "a learner under the declared default writes the container it wrote before: "
            "format version 3 on the default shape (checkpoint.md §2.1, §3, "
            "counterfactual.md §6, D-43)",
        )

    def test_agt18_2_six_keys(self):
        """AGT-18.2 `learners()` carries six keys in order, `counterfactuals` after `utilities` and before `hyper`, and two calls return equal records (`surface.md` §3, `README.md` §5, `counterfactual.md` §6, D-19, D-20, D-43).

        The third catalogue is an **addition** to §3's record and not a replacement of
        either axis beside it: D-19's rule catalogue and D-20's utility catalogue keep
        their places, `counterfactuals` sits between the second and `hyper`, and the
        record is rebuilt on every call, so two calls are equal data and not two views of
        one mutable mapping.
        """
        package = self.agents()
        record = package.learners()
        keys = tuple(record)
        self.assertEqual(
            len(keys),
            6,
            "learners() carries the six keys of surface.md §3 and this call carried %d: %r"
            % (len(keys), keys),
        )
        self.assertEqual(
            keys,
            (
                "backends",
                "architectures",
                "learning_rules",
                "utilities",
                "counterfactuals",
                "hyper",
            ),
            "learners() must carry backends, architectures, learning_rules, utilities, "
            "counterfactuals, hyper in that order: D-20 publishes the utility catalogue and "
            "D-43 the counterfactual one after it and before hyper (surface.md §3, "
            "counterfactual.md §6)",
        )
        self.assertEqual(
            keys.index("counterfactuals"),
            keys.index("utilities") + 1,
            "`counterfactuals` is published immediately after `utilities` (surface.md §3, "
            "counterfactual.md §6): %r" % (keys,),
        )
        self.assertEqual(
            keys.index("counterfactuals"),
            keys.index("hyper") - 1,
            "`counterfactuals` is published immediately before `hyper` (surface.md §3, "
            "counterfactual.md §6): %r" % (keys,),
        )
        first = package.learners()
        second = package.learners()
        self.assertEqual(
            first,
            second,
            "two calls to learners() returned unequal records, so the catalogue is state a "
            "caller can drift (surface.md §3, counterfactual.md §6)",
        )
        self.assertIsNot(
            first,
            second,
            "two calls to learners() returned one object, so a caller can mutate the "
            "catalogue through a returned mapping (surface.md §3)",
        )

    def test_agt18_3_the_specs_key(self):
        """AGT-18.3 a spec naming a member the catalogue does not carry — or a value that is not a name at all — is refused by name, while a spec naming the declared default explicitly builds the learner an absent key builds (`surface.md` §4, §9, `counterfactual.md` §6, `errors.md` §3-§4, D-43).

        §6 refuses a name outside the catalogue **where it is declared** and never maps it
        onto the default, because a silent substitution would train a model on targets its
        spec does not name; a non-string is refused the same way, so no `str()` and no
        lookup coerces a caller's value (`errors.md` §3-§4).  The refusal is this module's
        own, so a caller catching `AgentsError` catches it (`errors.md` §2).

        The other direction is the silence's: a spec naming `none` **explicitly** and one
        naming no member at all are one learner, because absence **is** the catalogue's
        first member and not a second default (`records.md` §3, `surface.md` §4).  The two
        are measured on one batch and compared twice — the statistic each reports and the
        whole parameter array each holds afterwards.
        """
        package = self.agents()
        catalogue = tuple(package.learners()["counterfactuals"])
        self.assertEqual(
            catalogue,
            tuple(name for name, _reads, _steps in DECLARED_COUNTERFACTUALS),
            "the catalogue's two members, in counterfactual.md §6's order, are what this case "
            "selects between (D-43)",
        )
        for label, value in (
            ("a name outside the catalogue", UNCATALOGUED_COUNTERFACTUAL),
            ("an integer", 3),
        ):
            with self.subTest(case=label):
                self.assert_agents_refusal(
                    package.build_learner,
                    spec(value),
                    entry="build_learner",
                    groups=(
                        ("counterfactual",),
                        (str(value),),
                        (catalogue[0],),
                        (catalogue[1],),
                    ),
                    label="%s: counterfactual = %r" % (label, value),
                )
        records = batch([dense_observation(0.07 * step) for step in range(4)])
        folder = self.tempdir()
        silent = package.build_learner(spec())
        explicit = package.build_learner(spec(DECLARED_DEFAULT))
        silent_before = package.save(silent, os.path.join(folder, "silent-8127.pt"))
        explicit_before = package.save(explicit, os.path.join(folder, "explicit-8127.pt"))
        self.assertTrue(
            np.array_equal(parameters(silent_before), parameters(explicit_before)),
            "a spec naming the declared default %r and one naming no member at all did not "
            "build one learner: both are the same initial draw from the same spec and seed "
            "(surface.md §4, records.md §3, architecture.md §4)"
            % (DECLARED_DEFAULT,),
        )
        by_silent = package.learn(silent, records)
        by_explicit = package.learn(explicit, records)
        silent_after = package.save(silent, os.path.join(folder, "silent-after-8127.pt"))
        explicit_after = package.save(explicit, os.path.join(folder, "explicit-after-8127.pt"))
        self.assertEqual(
            finite_float(by_explicit["td_error"], "learn(...)['td_error']"),
            finite_float(by_silent["td_error"], "learn(...)['td_error']"),
            "a spec naming %r explicitly and one naming no member reported different "
            "td_errors on one batch, so the explicit name did not select the catalogues's "
            "first member (counterfactual.md §6, rule.md §3, D-43)" % (DECLARED_DEFAULT,),
        )
        self.assertTrue(
            np.array_equal(parameters(silent_after), parameters(explicit_after)),
            "one batch under an explicit %r and under no key left two parameter arrays: "
            "absence is the catalogue's first member, so the two learners are one "
            "(surface.md §4, counterfactual.md §6)" % (DECLARED_DEFAULT,),
        )


class CounterfactualRecordTest(AgentsCase):
    """The transition record's two keys, and the step count the member takes."""

    def test_agt18_4_the_episode_boundary_is_required_and_integral(self):
        """AGT-18.4 `learn` refuses a transition with no `episode` and one whose `episode` is not an integer — a float, `None`, a flag and a string among them — naming the key, and accepts a `numpy` integer (`docs/L1/records.md` §4-§5, `docs/L1/counterfactual.md` §2, `surface.md` §7, `errors.md` §3-§4, D-43).

        The boundary is D-43's, and it is required of **every** transition rather than of one
        catalogue member, because it is what makes an episode-scoped target expressible for
        each of them (`counterfactual.md` §2, `rules.md` §5).  It is one integer per hand —
        the episode's own seed — so a float, a `None`, a flag and a string are all values no
        reader may coerce, and a `numpy` integer is a count and not another type to refuse
        (`errors.md` §4).  Both acceptances are asserted by the call succeeding and
        returning the two declared keys, which is the only reading that distinguishes a
        coerced `9300` from a refused one.
        """
        package = self.agents()
        learner = package.build_learner(spec())
        good = transition(dense_observation(0.0))
        missing = dict(good)
        del missing["episode"]
        self.assert_agents_refusal(
            package.learn,
            learner,
            [missing],
            entry="episode",
            groups=(("learn",),),
            label="a transition missing its episode boundary",
        )
        for label, value in (
            ("a float", 1.5),
            ("None", None),
            ("a flag", True),
            ("a string", "9300"),
        ):
            with self.subTest(episode=label):
                self.assert_agents_refusal(
                    package.learn,
                    learner,
                    [dict(good, episode=value)],
                    entry="episode",
                    groups=(("learn",), (str(value),)),
                    label="%s: episode = %r" % (label, value),
                )
        for label, value in (
            ("numpy.int64", np.int64(9300)),
            ("numpy.int32", np.int32(1)),
        ):
            with self.subTest(accepted=label):
                result = package.learn(learner, [dict(good, episode=value)])
                self.assertIsInstance(
                    result,
                    Mapping,
                    "learn returns the record surface.md §7 declares, and %s was refused or "
                    "coerced instead of read as a count (errors.md §4)" % (label,),
                )
                self.assertEqual(
                    set(result),
                    {"td_error", "transitions"},
                    "learn's record is the two declared keys (surface.md §7, rule.md §3): %r"
                    % (sorted(result),),
                )
                self.assertEqual(
                    plain_int(result["transitions"], "learn(...)['transitions']"),
                    1,
                    "a batch of one transition reports one consumed (rule.md §3)",
                )
                finite_float(result["td_error"], "learn(...)['td_error']")

    def test_agt18_5_the_records_resolution(self):
        """AGT-18.5 `learn` refuses a `counterfactual` of the wrong length, one that is not a sequence at all, and a non-`None` value at an index outside the transition's `legal` mask, while it accepts `None`, a complete resolution, an all-`None` one and one that is `None` outside the mask (`docs/L1/records.md` §4, `docs/L1/counterfactual.md` §4-§5, `surface.md` §7, `errors.md` §3-§4, D-43).

        The key is **optional** and its absence is `None`: a transition of a hand §4 refuses
        to resolve carries no values, and the member falls back from it (`counterfactual.md`
        §2, §4).  Present, it is one entry per descriptor of the shape — `A` on the default
        shape — a number at every index of the transition's own `legal` mask and `None`
        outside it, so a masked action is never valued and never updated (§5).  A wrong
        length is another shape's resolution and a value at an illegal index is a value for
        an action the transition could not take; both are refused naming the key, the length
        or the offending index and the mask, before any parameter moves (`errors.md` §1, §4).

        The four accepted forms are the ones the contract states, and each is asserted by
        the call succeeding and reporting one consumed record: `None`, a complete
        resolution, a resolution that is `None` everywhere — a hand with no value at any
        action, which the member falls back from exactly as it falls back from the key's
        absence — and one that is `None` only outside the mask (`counterfactual.md` §4-§5,
        §6).
        """
        package = self.agents()
        learner = package.build_learner(spec())
        A = len(ALL_MASK)
        self.assertEqual(
            len(RESOLUTION),
            A,
            "the invented resolution of this file carries one value per descriptor of the "
            "default shape's vocabulary (counterfactual.md §5, shapes.md §3)",
        )
        observation = dense_observation(0.0)
        refusals = (
            (
                "a resolution of %d values" % (A - 1,),
                transition(
                    observation,
                    counterfactual=tuple(float(index) for index in range(A - 1)),
                ),
                ((str(A - 1),),),
            ),
            (
                "a resolution of %d values" % (A + 1,),
                transition(
                    observation,
                    counterfactual=tuple(float(index) for index in range(A + 1)),
                ),
                ((str(A + 1),),),
            ),
            (
                "a plain number",
                transition(observation, counterfactual=7.5),
                (),
            ),
            (
                "a string",
                transition(observation, counterfactual="0,1,2"),
                (),
            ),
            (
                "a value at an index outside the transition's legal mask",
                transition(
                    observation,
                    legal=(0, 1),
                    counterfactual=(RESOLUTION[0], RESOLUTION[1], RESOLUTION[2]),
                ),
                (("index",), ("2",), ("(0, 1)",)),
            ),
        )
        for label, record, groups in refusals:
            with self.subTest(case=label):
                self.assert_agents_refusal(
                    package.learn,
                    learner,
                    [record],
                    entry="counterfactual",
                    groups=groups,
                    label=label,
                )
        acceptances = (
            ("None", transition(observation, counterfactual=None)),
            ("a complete resolution", transition(observation, counterfactual=RESOLUTION)),
            (
                "a resolution that is None everywhere",
                transition(observation, counterfactual=tuple(None for _index in ALL_MASK)),
            ),
            (
                "a resolution that is None outside the mask",
                transition(
                    observation,
                    legal=(0, 1),
                    counterfactual=(RESOLUTION[0], RESOLUTION[1], None),
                ),
            ),
        )
        for label, record in acceptances:
            with self.subTest(accepted=label):
                result = package.learn(learner, [record])
                self.assertEqual(
                    plain_int(result["transitions"], "learn(...)['transitions']"),
                    1,
                    "an accepted resolution reports one consumed transition, whatever the "
                    "step count its member takes (rule.md §3, counterfactual.md §6)",
                )
                self.assertEqual(
                    set(result),
                    {"td_error", "transitions"},
                    "learn's record is the two declared keys (surface.md §7): %r"
                    % (sorted(result),),
                )

    def test_agt18_6_the_step_count_through_the_public_surface(self):
        """AGT-18.6 the member takes `A` steps per resolved transition and the two counters its container records separate exactly that way: `transitions` and the schedule position count **records**, the target copy's counter counts **steps**, so the refresh fires `A` times sooner under the member than under `none` (`docs/L1/counterfactual.md` §4, §6, `docs/L3/agents/rule.md` §3-§4, §8, `docs/L3/agents/checkpoint.md` §2.1, D-43).

        Two learners of one spec and one seed, `none` and the member, are handed the same
        batch and differ in one thing: the member's records carry a resolution over the whole
        of `ALL_MASK`, so each takes `A` steps where the `none` record takes one
        (`counterfactual.md` §6).  What the file then records is the contract: `transitions`
        is the record count and so is `exploration.position` — the schedule advances by the
        decisions it was handed and never by the steps they cost — while `target.counter`
        counts the **steps** the refresh is measured in, so the member reaches
        `target_update_interval` `A` times faster (`rule.md` §3-§4, `checkpoint.md` §2.1).

        The refresh is then observed on both sides of its interval.  A batch one step past
        the interval leaves the counter at that one step under the member, which a batch of
        the same **record** count could never do — that batch's counter would be its record
        count and no refresh would have fired at all — and the `none` batch of the same length
        leaves its own record count.  The last clause reads three records' step counts the same
        way: a **terminal** record carrying a complete resolution takes `A` steps like any
        other, the terminal transition being where the outcome is known and **not** exempt
        (`counterfactual.md` §4, §6), while a record whose `counterfactual` is `None` and one
        that carries no such key at all are the ordinary single step — a partial resolution is
        not a resolution — so a batch of all three leaves `A + 2`.
        """
        package = self.agents()
        catalogue = tuple(package.learners()["counterfactuals"])
        self.assertGreaterEqual(
            len(catalogue),
            2,
            "the counterfactual catalogue declares the two members this case pairs "
            "(counterfactual.md §6, D-43): %r" % (catalogue,),
        )
        member = catalogue[1]
        A = len(ALL_MASK)
        interval = target_interval()
        folder = self.tempdir()
        read_metadata = declared_internal("checkpoint", "_read_metadata")

        def paired(count):
            """`count` non-terminal transitions, and the same batch with the resolution."""
            records = [
                transition(
                    dense_observation(0.01 * step),
                    action=1,
                    reward=0.0,
                    terminal=False,
                    legal=ALL_MASK,
                    next_legal=ALL_MASK,
                )
                for step in range(count)
            ]
            return records, [dict(record, counterfactual=RESOLUTION) for record in records]

        def recorded(under, records, tag):
            """One learner's two statistics, and the two counters its container records."""
            held = package.build_learner(spec(under))
            result = package.learn(held, records)
            path = package.save(held, os.path.join(folder, "%s-8127.pt" % (tag,)))
            metadata, _array = container_document(path)
            return {
                "transitions": plain_int(
                    result["transitions"], "learn(...)['transitions']"
                ),
                "td_error": finite_float(result["td_error"], "learn(...)['td_error']"),
                "counter": plain_int(
                    metadata["target"]["counter"], "metadata['target']['counter']"
                ),
                "position": plain_int(
                    read_metadata(path)["exploration"]["position"],
                    "exploration.position",
                ),
            }

        shared, resolved = paired(PAIRED_RECORDS)
        self.assertEqual(
            len(RESOLUTION),
            A,
            "the invented resolution carries one value per descriptor, so each member record "
            "is a complete resolution and takes `A` steps (counterfactual.md §5-§6)",
        )
        under_none = recorded(None, shared, "paired-none")
        under_member = recorded(member, resolved, "paired-member")
        for label, figure in (("none", under_none), ("member", under_member)):
            with self.subTest(member=label):
                self.assertEqual(
                    figure["transitions"],
                    len(shared),
                    "a %r batch of %d resolved records reported %r consumed: `transitions` "
                    "is the record count and never the step count (rule.md §3, "
                    "counterfactual.md §6)"
                    % (label, len(shared), figure["transitions"]),
                )
                self.assertGreaterEqual(
                    figure["td_error"],
                    0.0,
                    "a %r batch reported a negative td_error, which is a mean absolute "
                    "residual (rule.md §3)" % (label,),
                )
        for label, figure in (("none", under_none), ("member", under_member)):
            with self.subTest(position=label):
                self.assertEqual(
                    figure["position"],
                    len(shared),
                    "the %r batch of %d records left the schedule position at %r: the "
                    "position advances by the records consumed and never by the steps they "
                    "took (counterfactual.md §6, rule.md §3-§4)"
                    % (label, len(shared), figure["position"]),
                )
        self.assertEqual(
            under_none["counter"],
            len(shared),
            "the `none` batch of %d records left the target copy's counter at %r: under "
            "`none` one record is one step, so the two counts are one number "
            "(counterfactual.md §6, rule.md §3)"
            % (len(shared), under_none["counter"]),
        )
        self.assertEqual(
            under_member["counter"],
            len(shared) * A,
            "the member's batch of %d records took %d steps and left the target copy's "
            "counter at %r: the counter is consumed one step at a time, so %d records are "
            "%d steps at `A` = %d (counterfactual.md §6, rule.md §3)"
            % (
                len(shared),
                len(shared) * A,
                under_member["counter"],
                len(shared),
                len(shared) * A,
                A,
            ),
        )
        self.assertLess(
            len(shared) * A,
            interval,
            "the member's %d steps must stay below the declared target interval %d for the "
            "counter above to be the step count itself and not a count past one refresh "
            "(rule.md §3, §6)" % (len(shared) * A, interval),
        )

        # The refresh, observed on both sides of its interval: one step past it under the
        # member, and the same **record** count under `none`, which never reaches it.
        crossing = -(-(interval + 1) // A)
        steps = crossing * A
        self.assertGreater(
            steps,
            interval,
            "the crossing batch's %d steps must pass the interval %d (rule.md §3, §6)"
            % (steps, interval),
        )
        self.assertLess(
            steps,
            2 * interval,
            "the crossing batch's %d steps must pass the interval %d once and not twice, or "
            "the counter below would be a wrapped one (rule.md §3, §6)" % (steps, interval),
        )
        shared_cross, resolved_cross = paired(crossing)
        under_none_cross = recorded(None, shared_cross, "crossing-none")
        under_member_cross = recorded(member, resolved_cross, "crossing-member")
        self.assertEqual(
            under_member_cross["counter"],
            steps - interval,
            "the member's %d records took %d steps, passing the interval %d once, and left "
            "the counter at %r instead of %r: the refresh fires on steps, which a batch of "
            "%d records could never do — that batch's counter is its record count and no "
            "refresh has fired at all (counterfactual.md §6, rule.md §3)"
            % (
                crossing,
                steps,
                interval,
                under_member_cross["counter"],
                steps - interval,
                crossing,
            ),
        )
        self.assertNotEqual(
            under_member_cross["counter"],
            crossing,
            "the member's crossing batch left the counter at its own record count %d, which "
            "is the count of a counter that counts transitions and not steps: %d steps pass "
            "the interval %d and %d records do not (counterfactual.md §6, rule.md §3)"
            % (crossing, steps, interval, crossing),
        )
        self.assertEqual(
            under_none_cross["counter"],
            crossing,
            "the `none` batch of %d records left the counter at %r: with one step per record "
            "it never reaches the interval %d, so the refresh cannot have fired "
            "(counterfactual.md §6, rule.md §3)"
            % (crossing, under_none_cross["counter"], interval),
        )
        self.assertEqual(
            under_member_cross["position"],
            crossing,
            "the member's crossing batch left the schedule position at %r for %d records: the "
            "position counts transitions even when their steps pass a refresh "
            "(counterfactual.md §6, rule.md §4)" % (under_member_cross["position"], crossing),
        )

        # Three step counts in one batch.  A **terminal** record carrying a complete resolution
        # takes `A` steps — the seat's last decision of a hand carries the whole-hand value of
        # every legal action and the realised one equals that transition's `reward`, so the
        # terminal transition is where the outcome is known and is not exempt — while a record
        # whose `counterfactual` is `None` and one carrying no such key at all take the single
        # ordinary step, a partial resolution being no resolution (`counterfactual.md` §4, §6).
        mixed = [
            transition(
                dense_observation(0.0),
                action=1,
                reward=RESOLUTION[1],
                terminal=True,
                legal=ALL_MASK,
                next_legal=ALL_MASK,
                counterfactual=RESOLUTION,
            ),
            transition(
                dense_observation(0.2),
                action=1,
                reward=0.0,
                terminal=False,
                counterfactual=None,
            ),
            transition(dense_observation(0.3), action=1, reward=0.0, terminal=False),
        ]
        expected_steps = {member: A + 2, None: len(mixed)}
        for under, tag in ((member, "mixed-member"), (None, "mixed-none")):
            with self.subTest(batch=tag):
                figure = recorded(under, mixed, tag)
                self.assertEqual(
                    figure["transitions"],
                    len(mixed),
                    "a batch of a resolved terminal record, an unresolved one and one carrying "
                    "no resolution at all reports its records consumed (rule.md §3)",
                )
                self.assertEqual(
                    figure["counter"],
                    expected_steps[under],
                    "the %r three-record batch left the target copy's counter at %r instead of "
                    "%r: a terminal record carrying a complete resolution takes `A` steps like "
                    "any other transition — the terminal one is **not** exempt — while a `None` "
                    "resolution, and an absent key which is the same thing, is no resolution "
                    "and takes the single ordinary step (counterfactual.md §4, §6, rule.md "
                    "§2-§3, D-43)"
                    % (tag, figure["counter"], expected_steps[under]),
                )
                if under is not None:
                    self.assertNotEqual(
                        figure["counter"],
                        len(mixed),
                        "the member's three-record batch left the counter at its own record "
                        "count %d, which is the count of a counter that counts transitions and "
                        "not steps: `A` = %d steps for the resolved terminal record and one "
                        "each for the other two are %d steps (counterfactual.md §6, rule.md §3)"
                        % (len(mixed), A, expected_steps[under]),
                    )
                self.assertEqual(
                    figure["position"],
                    len(mixed),
                    "the %r three-record batch left the schedule position at %r "
                    "(counterfactual.md §6, rule.md §4)" % (tag, figure["position"]),
                )


class CounterfactualContainerTest(AgentsCase):
    """The container's format versions, its field and its two older readings."""

    def setUp(self):
        """One scratch directory per case, made on first use and removed with the case."""
        super().setUp()
        self._folder = None

    def path(self, name):
        """A container's path inside this case's own scratch directory."""
        if self._folder is None:
            self._folder = self.tempdir()
        return os.path.join(self._folder, name)

    def test_agt18_7_the_container(self):
        """AGT-18.7 a container under `none` records format version 3 on the default shape and 4 on another, with **no** `counterfactual` field, while a member's records version **5** with the field immediately after `utility` and `game` only on a shape that is not the default (`docs/L3/agents/checkpoint.md` §2-§3, `docs/L1/counterfactual.md` §6, §9, `docs/L1/shapes.md` §5, D-43, D-29, ASM-40).

        The member is a **format version and not a migration**: a learner under `none` writes
        exactly the container it wrote before — version 3 with the fourteen fields of §2.1 on
        the default shape, version 4 with `game` on any other — so its two decompressed
        members stay today's byte for byte, and only a member that is not `none` asks for
        version 5 (`counterfactual.md` §6, §9).  Version 5 keeps version 4's own condition on
        the shape: a member of the default shape carries no `game`, and one of
        `no-limit-100` carries that name, which is the pair a reader needs to rebuild a head
        of the right width (`shapes.md` §5, `sizing.md` §6, ASM-40).

        The document is read from the container's own `metadata.json` — the member name
        `checkpoint.md` §2 fixes — with the JSON's key order preserved, which is the only way
        "immediately after `utility`" is observable at all (`utilities.md` §6, D-20, D-43).
        """
        package = self.agents()
        catalogue = tuple(package.learners()["counterfactuals"])
        self.assertGreaterEqual(
            len(catalogue),
            2,
            "the counterfactual catalogue declares the member this case writes second, after "
            "`none` (counterfactual.md §6, D-43): %r" % (catalogue,),
        )
        member = catalogue[1]
        other_encoder = shape_encoder("flat-numeric", OTHER_SHAPE)

        silent = package.build_learner(spec())
        silent_path = package.save(silent, self.path("none-8127.pt"))
        metadata, _array = container_document(silent_path)
        self.assertEqual(
            plain_int(metadata["format_version"], "metadata['format_version']"),
            3,
            "a learner under `none` writes format version 3 on the default shape, exactly as "
            "it wrote before this axis existed (counterfactual.md §6, §9, checkpoint.md §2.1)",
        )
        self.assertNotIn(
            "counterfactual",
            metadata,
            "a `none` container carries no `counterfactual` field at all, so its metadata is "
            "today's (counterfactual.md §6, §9, checkpoint.md §2.1): %r" % (tuple(metadata),),
        )
        self.assertEqual(
            tuple(metadata),
            CONTAINER_KEYS,
            "a version-3 container of the default shape records the fourteen fields of "
            "checkpoint.md §2.1 in that order, `utility` after `learning_rule` and no `game` "
            "and no `counterfactual`: %r" % (tuple(metadata),),
        )

        silent_other = package.build_learner(
            spec(game=OTHER_SHAPE, encoder=other_encoder)
        )
        other_path = package.save(silent_other, self.path("none-no-limit-8127.pt"))
        other, _array = container_document(other_path)
        self.assertEqual(
            plain_int(other["format_version"], "metadata['format_version']"),
            4,
            "a learner under `none` on any declared shape other than the default writes "
            "format version 4 (checkpoint.md §2.1, §3, shapes.md §5, ASM-40)",
        )
        self.assertEqual(
            other.get("game"),
            OTHER_SHAPE,
            "a version-4 container records, in `game`, the declared shape it was written on "
            "(checkpoint.md §2.1, §3, shapes.md §5, D-29)",
        )
        self.assertNotIn(
            "counterfactual",
            other,
            "a `none` container of another shape carries no `counterfactual` field either: "
            "the field is the member's, not the shape's (counterfactual.md §6, "
            "checkpoint.md §3)",
        )

        revealed = package.build_learner(spec(member))
        revealed_path = package.save(revealed, self.path("member-8127.pt"))
        recorded, _array = container_document(revealed_path)
        self.assertEqual(
            plain_int(recorded["format_version"], "metadata['format_version']"),
            5,
            "a learner whose counterfactual member is not `none` writes format version 5 "
            "(counterfactual.md §6, §9, checkpoint.md §2.1, §3)",
        )
        self.assertIn(
            "counterfactual",
            recorded,
            "a version-5 container records the member its learner took its targets from, as a "
            "required field (counterfactual.md §6, §9): %r" % (tuple(recorded),),
        )
        self.assertEqual(
            recorded["counterfactual"],
            member,
            "the container records the catalogue member its learner carries "
            "(counterfactual.md §6, §9, D-43)",
        )
        keys = tuple(recorded)
        self.assertIn("utility", keys, "a version-5 container records the utility too")
        self.assertEqual(
            keys.index("counterfactual"),
            keys.index("utility") + 1,
            "`counterfactual` is written immediately after `utility` in the document's own key "
            "order, so a version's catalogue members are read as one run "
            "(counterfactual.md §6, checkpoint.md §2.1); the document's order was %r"
            % (keys,),
        )
        self.assertNotIn(
            "game",
            recorded,
            "a version-5 member of the **default** shape carries no `game`, version 4's own "
            "condition on the shape (checkpoint.md §2.1, §3, shapes.md §5): %r" % (keys,),
        )

        revealed_other = package.build_learner(
            spec(member, game=OTHER_SHAPE, encoder=other_encoder)
        )
        other_member_path = package.save(
            revealed_other, self.path("member-no-limit-8127.pt")
        )
        other_member, _array = container_document(other_member_path)
        self.assertEqual(
            plain_int(other_member["format_version"], "metadata['format_version']"),
            5,
            "a member of any declared shape writes format version 5 (counterfactual.md §6, "
            "§9, checkpoint.md §3)",
        )
        self.assertEqual(
            other_member.get("game"),
            OTHER_SHAPE,
            "a version-5 container carries `game` exactly when its shape is not the default: "
            "this one was written on %r (checkpoint.md §2.1, §3, shapes.md §5, ASM-40)"
            % (OTHER_SHAPE,),
        )
        self.assertEqual(
            other_member["counterfactual"],
            member,
            "the version-5 container of another shape records its member beside its shape "
            "(counterfactual.md §6, shapes.md §5)",
        )

    def test_agt18_8_the_reading(self):
        """AGT-18.8 a version-5 container without `counterfactual`, one naming the declared default, one naming an uncatalogued member, and a version-1, 2, 3 or 4 container that *carries* the field are each refused by name, the undoctored member container loads, and a `load` spec that disagrees with the file is refused naming both values (`docs/L3/agents/checkpoint.md` §3, `docs/L1/counterfactual.md` §6, §9, `surface.md` §9, `errors.md` §2-§3, D-43).

        One rule runs over all five versions: a container carries exactly the fields its own
        writer wrote, so a field present where no writer of that version wrote it was edited
        and is refused by name, and a field absent where its writer always wrote it is a form
        this module does not read (`checkpoint.md` §3).  Version 5 **requires** the member and
        refuses the declared default, whose container is a version-3 or a version-4 one;
        versions 1-4 predate the field and must not carry it, the rule `utility` already
        follows (`utilities.md` §6, `counterfactual.md` §9).  A member the catalogue does not
        carry is refused where it is named, and the container is one of the places it is.

        Every doctored copy is built from a container this module wrote — both members the
        file's own bytes and only `metadata.json` rewritten — so no case here writes under
        `checkpoints/`, and the undoctored source still loads afterwards, which is what makes
        each refusal the doctored field's and not the file's (`checkpoint.md` §2, `surface.md`
        §8, ASM-18).
        """
        package = self.agents()
        catalogue = tuple(package.learners()["counterfactuals"])
        self.assertGreaterEqual(
            len(catalogue),
            2,
            "the counterfactual catalogue declares the member these containers were written "
            "under (counterfactual.md §6, D-43): %r" % (catalogue,),
        )
        member = catalogue[1]
        other_encoder = shape_encoder("flat-numeric", OTHER_SHAPE)
        none_path = package.save(
            package.build_learner(spec()), self.path("source-none-8127.pt")
        )
        member_path = package.save(
            package.build_learner(spec(member)), self.path("source-member-8127.pt")
        )
        other_member_path = package.save(
            package.build_learner(spec(member, game=OTHER_SHAPE, encoder=other_encoder)),
            self.path("source-member-no-limit-8127.pt"),
        )
        metadata, array = container_document(member_path)
        self.assertEqual(
            metadata["counterfactual"],
            member,
            "the source of the doctored copies below is a version-5 container of the member "
            "(counterfactual.md §6, checkpoint.md §2.1)",
        )
        without = {key: value for key, value in metadata.items() if key != "counterfactual"}
        dropped = write_container(self.path("v5-dropped-8127.pt"), without, array)
        named_default = dict(metadata)
        named_default["counterfactual"] = DECLARED_DEFAULT
        default_value = write_container(self.path("v5-default-8127.pt"), named_default, array)
        named_uncarried = dict(metadata)
        named_uncarried["counterfactual"] = UNCATALOGUED_COUNTERFACTUAL
        uncarried = write_container(
            self.path("v5-uncarried-8127.pt"), named_uncarried, array
        )
        carried = (
            (
                "a version 3 container carrying `counterfactual`",
                version_container(member_path, self.path("v3-carried-8127.pt"), 3),
                3,
            ),
            (
                "a version 2 container carrying `counterfactual`",
                version_container(
                    member_path, self.path("v2-carried-8127.pt"), 2, drop=("utility",)
                ),
                2,
            ),
            (
                "a version 1 container carrying `counterfactual`",
                version_container(
                    member_path,
                    self.path("v1-carried-8127.pt"),
                    1,
                    drop=("learning_rule", "utility"),
                ),
                1,
            ),
            (
                "a version 4 container carrying `counterfactual`",
                version_container(
                    other_member_path, self.path("v4-carried-8127.pt"), 4
                ),
                4,
            ),
        )
        refusals = [
            (
                "a version 5 container without the field",
                dropped,
                (("metadata",),),
            ),
            (
                "a version 5 container naming the declared default",
                default_value,
                (("counterfactual",), (DECLARED_DEFAULT,)),
            ),
            (
                "a version 5 container naming a member the catalogue does not carry",
                uncarried,
                (
                    (UNCATALOGUED_COUNTERFACTUAL,),
                    (catalogue[0],),
                    (catalogue[1],),
                ),
            ),
        ]
        for label, path, version in carried:
            self.assertEqual(
                plain_int(
                    container_document(path)[0]["format_version"], "metadata['format_version']"
                ),
                version,
                "the doctored copy this case refuses must be the version it is about: %r"
                % (label,),
            )
            self.assertIn(
                "counterfactual",
                container_document(path)[0],
                "the doctored copy this case refuses must *carry* the field, which is the "
                "edited file checkpoint.md §3 describes: %r" % (label,),
            )
            refusals.append(
                (
                    label,
                    path,
                    (("format version %d" % (version,),), (member,)),
                )
            )
        for label, path, groups in refusals:
            with self.subTest(case=label):
                self.assert_agents_refusal(
                    package.load,
                    None,
                    path,
                    entry="counterfactual",
                    groups=groups,
                    label=label,
                )
        # A `load` spec is compared with the file on the member exactly as it is on the rule
        # and the utility: a disagreement names both values, and `load(spec)` is what tells
        # this refusal apart from a container's own (`checkpoint.md` §3, `surface.md` §9).
        self.assert_refused(
            package.load,
            {"counterfactual": member},
            none_path,
            entry="load",
            groups=(
                ("load(spec)",),
                ("counterfactual",),
                (member,),
                (DECLARED_DEFAULT,),
            ),
            label="a spec naming the member where the file records none",
        )
        self.assert_refused(
            package.load,
            {"counterfactual": DECLARED_DEFAULT},
            member_path,
            entry="load",
            groups=(
                ("load(spec)",),
                ("counterfactual",),
                (member,),
                (DECLARED_DEFAULT,),
            ),
            label="a spec naming none where the file records the member",
        )
        restored = package.load(None, member_path)
        policy = package.as_policy(restored, flat_encoder(), LEARNER_SEED)
        self.assertEqual(
            getattr(policy, "counterfactual", None),
            member,
            "the container the doctored copies were built from must still load, and the "
            "learner it restores must carry the member the file records, so each refusal "
            "above is the doctored field's and not the file's (counterfactual.md §6, §9, "
            "checkpoint.md §3)",
        )


class CounterfactualPolicyTest(AgentsCase):
    """The attribute a policy carries, its round trip, and a baseline's absence of it."""

    def test_agt18_9_the_policy_and_the_round_trip(self):
        """AGT-18.9 `as_policy` carries `counterfactual` beside `learning_rule` and `utility` for both catalogue members, a `save` → `load` → `as_policy` round trip preserves all three, and a baseline's policy carries none (`docs/L2/agents/surface.md` §10-§12, `docs/L3/agents/rule.md` §7, `docs/L1/e2e-surface.md` §2, `docs/L1/counterfactual.md` §6, D-43, D-6, D-19, D-20).

        `e2e-surface.md` §2 declares the three attributes a policy carries, and
        `surface.md` §10 makes them a copy of what its learner learned under: `learning_rule`
        the rule, `utility` the reward its model was trained on, and `counterfactual` the
        member it took its targets from.  A table reads them to label its population, so a
        variant built in process and never written down still names the population and the
        objectives it measured — and no decision the policy makes reads any of the three
        (`counterfactual.md` §6, `rules.md` §7, `utilities.md` §7).  The round trip is
        asserted through the file because that is where the member has to survive: `load`
        restores what the container records, and `as_policy` copies it onto the policy.
        A baseline learns nothing and is trained on no reward, so it carries none of the
        three — `getattr(..., None) is None` is the honest assertion for an attribute a
        baseline's policy does not have at all (`surface.md` §12, `baselines.md` §2, D-6).
        """
        package = self.agents()
        catalogue = tuple(package.learners()["counterfactuals"])
        rules = tuple(package.learners()["learning_rules"])
        utilities = tuple(package.learners()["utilities"])
        self.assertGreaterEqual(
            len(catalogue),
            2,
            "the counterfactual catalogue carries both members this case walks "
            "(counterfactual.md §6, D-43): %r" % (catalogue,),
        )
        # A rule and a utility that are **not** the declared defaults, so "preserved" is a
        # claim about the two axes beside the third and not about three defaults
        # (`rules.md` §4, `utilities.md` §5).
        rule, utility = rules[-1], utilities[-1]
        folder = self.tempdir()
        for name in catalogue:
            with self.subTest(counterfactual=name):
                held = package.build_learner(
                    spec(name, extra={"learning_rule": rule, "utility": utility})
                )
                policy = package.as_policy(held, flat_encoder(), LEARNER_SEED)
                carried = (
                    ("learning_rule", rule),
                    ("utility", utility),
                    ("counterfactual", name),
                )
                for attribute, wanted in carried:
                    self.assertEqual(
                        getattr(policy, attribute, None),
                        wanted,
                        "a policy's `%s` is %r where its learner was built under %r: the "
                        "policy carries what the learner learned under so a table can name "
                        "its population (e2e-surface.md §2, surface.md §10, "
                        "counterfactual.md §6, D-43)"
                        % (attribute, getattr(policy, attribute, None), wanted),
                    )
                path = package.save(
                    held, os.path.join(folder, "round-trip-%s-8127.pt" % (name,))
                )
                again = package.as_policy(
                    package.load(None, path), flat_encoder(), LEARNER_SEED
                )
                for attribute, wanted in carried:
                    self.assertEqual(
                        getattr(again, attribute, None),
                        wanted,
                        "a save → load → as_policy round trip did not preserve `%s`, which "
                        "the policy reports as %r where the member %r was written: the "
                        "container records the member and `load` restores it "
                        "(counterfactual.md §6, §9, checkpoint.md §2.1, §3, surface.md §10)"
                        % (attribute, getattr(again, attribute, None), name),
                    )
        for name in package.baselines():
            with self.subTest(baseline=name):
                baseline = package.build_baseline(name, LEARNER_SEED)
                self.assertIsNone(
                    getattr(baseline, "counterfactual", None),
                    "a baseline's policy carries a `counterfactual` (%r): a baseline learns "
                    "nothing and takes its targets from no member, so it names no population "
                    "and no objective (surface.md §12, e2e-surface.md §2, baselines.md §2, "
                    "D-6, D-43)" % (getattr(baseline, "counterfactual", None),),
                )
