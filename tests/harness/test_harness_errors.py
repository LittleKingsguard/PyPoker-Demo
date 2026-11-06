"""HRN-8 — the four refusals, their canonical messages, and the two report edges.

Drives `docs/L3/harness/errors.md` §1-§4 and the two reporting edges of
`docs/L2/harness/surface.md` §1: one base and three subclasses, one refusal per entry
point that can refuse, the four-part message grammar (the offending value, the entry
point by module path, the contract, one language), and the asymmetry that an undeclared
kind is refused while an unlisted expectation **name** is a named failure
(`guardrails.md` G5, G12, G24, FAM-14.4, FAM-14.8, FAM-16.36).
"""

import unittest

from _harness_support import (
    CASE_ID,
    EXPECTATION_KINDS,
    FACTORY_KINDS,
    REFUSAL_NAMES,
    SEAM_INVENTED,
    SEAM_RECORDING,
    SEAM_SYNTHETIC,
    HarnessCase,
    as_mapping,
    as_text,
    case,
    error_class,
    pure_value,
)

class ErrorsTest(HarnessCase):
    def test_hrn_8_1_an_undeclared_factory_kind_is_refused_by_name(self):
        """HRN-8.1 `factory("deck-of-cards", …)` raises `UnknownFactoryKind` with errors §4's canonical message, naming the kind and the six declared kinds in sorted order (errors §2, §4, support §2, G5, FAM-14.4)."""
        exc = self.refuse(
            lambda: self.ep("factory")("deck-of-cards", None),
            "UnknownFactoryKind",
            tokens=(
                "'deck-of-cards'",
                "harness.factory",
                "the map declares " + ", ".join(FACTORY_KINDS),
            ),
            label="factory('deck-of-cards', None)",
        )
        self.assertEqual(
            str(exc),
            "harness.factory refused the kind 'deck-of-cards': the map declares "
            "baseline, encoder, hand, learner, pool, rung",
            "errors §4 fixes the canonical message for an undeclared kind: %r"
            % (str(exc),),
        )

    def test_hrn_8_2_an_unhashable_factory_kind_is_refused_and_never_a_type_error(self):
        """HRN-8.2 the kind check is `not isinstance(kind, str) or kind not in OBJECTS`, so an unhashable kind raises `UnknownFactoryKind` naming the value and never the `TypeError` a bare membership test would raise (errors §2, §4, support §2, G5, FAM-14.4)."""
        for value in (["deck-of-cards"], {"deck-of-cards": True}, {"a", "b"}):
            with self.subTest(kind=value):
                exc = self.refuse(
                    lambda value=value: self.ep("factory")(value, None),
                    "UnknownFactoryKind",
                    tokens=(repr(value), "harness.factory", "the map declares"),
                    label="factory(%r, None)" % (value,),
                )
                self.assertNotIsInstance(
                    exc,
                    TypeError,
                    "an unhashable kind is not this module's refusal as a TypeError: it "
                    "is the factory's own refusal, naming the value (G5): %r" % (exc,),
                )

    def test_hrn_8_3_an_unlisted_expectation_kind_is_a_fail_and_never_a_raise(self):
        """HRN-8.3 a string kind `fixtures()` does not list is **reported**: `fail` with errors §4's kind-set sentence and the kind verbatim, because L1 contracts exactly that named failure (expectations §4, surface §6, errors §1, G12, FAM-14.8, FAM-16.36)."""
        record = as_mapping(
            self.ep("expect")("no-such-kind", [7, -7]),
            "the verdict for an unlisted kind",
        )
        self.assertEqual(
            list(record),
            ["kind", "verdict", "reason"],
            "it is the ordinary verdict record and not an error (expectations §1, §4): "
            "%r" % (list(record),),
        )
        self.assertEqual(
            as_text(record["kind"], "the kind as handed"),
            "no-such-kind",
            "the record repeats the unlisted kind verbatim (expectations §1, §4): %r"
            % (record["kind"],),
        )
        self.assertEqual(
            record["verdict"],
            "fail",
            "an unlisted kind is not raised: it is a fail the driver can report "
            "(expectations §4, surface §1, errors §1, G12): %r" % (record,),
        )
        self.assertEqual(
            record["reason"],
            "harness.expect failed the kind 'no-such-kind': fixtures() lists zero-sum, "
            "legal-choice, counted, refused",
            "errors §4 fixes the kind-set sentence, with the four kinds in KINDS' order "
            "(errors §4, expectations §4, G12): %r" % (record["reason"],),
        )
        for kind in EXPECTATION_KINDS:
            with self.subTest(listed=kind):
                listed = as_mapping(
                    self.ep("expect")(kind, {"invented": "value"}),
                    "the verdict for a listed kind",
                )
                self.assertNotIn(
                    "fixtures() lists",
                    str(listed["reason"]),
                    "a listed kind is judged and not reported as unlisted (%r): %r"
                    % (kind, listed),
                )

    def test_hrn_8_4_a_non_string_expectation_kind_raises_the_named_refusal(self):
        """HRN-8.4 a `kind` that is not a string raises `UnknownExpectationKind` naming the value and the kind set — a non-name is an invalid argument and is refused rather than judged (expectations §4, errors §4, surface §6, G12)."""
        for value in (3, None, [], 3.5, True):
            with self.subTest(kind=value):
                exc = self.refuse(
                    lambda value=value: self.ep("expect")(value, [7, -7]),
                    "UnknownExpectationKind",
                    tokens=(
                        repr(value),
                        "harness.expect",
                        "a kind is a name fixtures() lists",
                        ", ".join(EXPECTATION_KINDS),
                    ),
                    label="expect(%r, …)" % (value,),
                )
                self.assertNotIsInstance(
                    exc,
                    TypeError,
                    "a non-name kind is refused by this module and does not fall "
                    "through as a TypeError (errors §2, §4, G12): %r" % (exc,),
                )
        self.assertEqual(
            str(
                self.refuse(
                    lambda: self.ep("expect")(3, [7, -7]),
                    "UnknownExpectationKind",
                )
            ),
            "harness.expect refused the kind 3: a kind is a name fixtures() lists, "
            "zero-sum, legal-choice, counted, refused",
            "errors §4 fixes the canonical message for a non-string kind (errors §4, "
            "G12)",
        )

    def test_hrn_8_5_an_empty_legal_set_raises_the_named_refusal(self):
        """HRN-8.5 `seam(label)(readout, [])` raises `NoLegalAction` with errors §4's canonical message — a policy returns a member of `legal_actions` and never folds (errors §2, §4, support §3, surface §5, G24, D-2)."""
        policy = self.ep("seam")(SEAM_RECORDING)
        exc = self.refuse(
            lambda: policy({"street": "preflop"}, []),
            "NoLegalAction",
            tokens=("harness.seam", SEAM_RECORDING, "empty legal set"),
            label="seam('recording')(readout, [])",
        )
        self.assertEqual(
            str(exc),
            "harness.seam('recording') refused the empty legal set: a policy returns a "
            "member of legal_actions",
            "errors §4 fixes the canonical message for the empty legal set: %r"
            % (str(exc),),
        )
        for label in (SEAM_SYNTHETIC, SEAM_INVENTED):
            with self.subTest(label=label):
                refused = self.refuse(
                    lambda label=label: self.ep("seam")(label)({"street": "preflop"}, ()),
                    "NoLegalAction",
                    tokens=(label, "a policy returns a member of legal_actions"),
                    label="seam(%r)(readout, ())" % (label,),
                )
                self.assertIn(
                    label,
                    str(refused),
                    "the message names the label of the seam that refused, whatever the "
                    "label is (errors §3 rule 1, §4, G24): %r" % (str(refused),),
                )

    def test_hrn_8_6_the_four_classes_exist_with_one_base(self):
        """HRN-8.6 `HarnessError` is the base and `UnknownFactoryKind`, `UnknownExpectationKind` and `NoLegalAction` are its three subclasses, so a caller can catch this module's refusals without catching a `KeyError` from its own bug (errors §1-§2, README §3)."""
        base = error_class("HarnessError")
        self.assertTrue(
            isinstance(base, type),
            "HarnessError is a class of the harness package (errors §2): %r" % (base,),
        )
        self.assertTrue(
            issubclass(base, Exception),
            "the base is an Exception, so a refusal propagates like one (errors §1-§2): "
            "%r" % (base,),
        )
        for built_in in (KeyError, ValueError, TypeError, RuntimeError):
            self.assertFalse(
                issubclass(base, built_in),
                "the hierarchy exists so a caller does not catch its own %s while "
                "catching a harness refusal (errors §1): %r"
                % (built_in.__name__, base),
            )
        subclasses = []
        for name in REFUSAL_NAMES[1:]:
            klass = error_class(name)
            self.assertTrue(
                issubclass(klass, base),
                "%s is a subclass of HarnessError, one per entry point that can refuse "
                "(errors §2): %r" % (name, klass),
            )
            self.assertIsNot(
                klass,
                base,
                "%s is a subclass and not the base renamed (errors §2): %r"
                % (name, klass),
            )
            subclasses.append(klass)
        self.assertEqual(
            len(set(subclasses)),
            len(subclasses),
            "the three subclasses are three distinct classes (errors §2): %r"
            % (subclasses,),
        )

    def test_hrn_8_7_a_non_string_factory_kind_is_named_in_the_message(self):
        """HRN-8.7 the non-string factory kind's message is errors §4's second row: it names the value as a `%r` and quotes the map's contract, so a reader learns which module refused and what it was given (errors §3-§4, G5)."""
        for value in (7, None, 3.5):
            with self.subTest(kind=value):
                exc = self.refuse(
                    lambda value=value: self.ep("factory")(value, None),
                    "UnknownFactoryKind",
                    tokens=(repr(value), "harness.factory", "the map declares"),
                    label="factory(%r, None)" % (value,),
                )
                self.assertEqual(
                    str(exc),
                    "harness.factory refused the kind %r: the map declares baseline, "
                    "encoder, hand, learner, pool, rung" % (value,),
                    "errors §4's second row fixes the message for a non-string kind: %r"
                    % (str(exc),),
                )

    def test_hrn_8_8_every_message_follows_the_four_part_grammar(self):
        """HRN-8.8 every refusal is one line naming the entry point by module path — qualified by the label where `seam` refuses inside an instance — the offending value and the violated contract, with no traceback text and no `repr` of an internal object (errors §3 rules 1-3, G5, G12, G24)."""
        raisers = (
            ("harness.factory", "an-undeclared-kind", lambda: self.ep("factory")("an-undeclared-kind", None)),
            ("harness.factory", 7, lambda: self.ep("factory")(7, None)),
            ("harness.expect", 3, lambda: self.ep("expect")(3, [7, -7])),
            (
                "harness.seam",
                SEAM_RECORDING,
                lambda: self.ep("seam")(SEAM_RECORDING)({"street": "preflop"}, []),
            ),
        )
        for entry_point, value, thunk in raisers:
            with self.subTest(entry_point=entry_point, value=value):
                exc = self.raised(thunk, "%s with %r" % (entry_point, value))
                message = str(exc)
                if entry_point == "harness.seam":
                    prefix = "%s(%r) refused " % (entry_point, value)
                else:
                    prefix = entry_point + " refused "
                self.assertTrue(
                    message.startswith(prefix),
                    "the message names the entry point by its module path — qualified by "
                    "the label of the seam that refused, because a seam refuses inside "
                    "an instance — and says what it refused, so a caller learns which of "
                    "the three refused it (errors §3 rule 2): %r" % (message,),
                )
                self.assertIn(
                    repr(value),
                    message,
                    "the offending value is named as a %%r of what the caller passed "
                    "(errors §3 rule 1): %r" % (message,),
                )
                self.assertNotIn(
                    "\n",
                    message,
                    "every message is one line (errors §3): %r" % (message,),
                )
                for noise in ("Traceback", "object at 0x", "File \"", "line "):
                    self.assertNotIn(
                        noise,
                        message,
                        "no traceback text and no repr of an internal object: %r is not "
                        "a refusal (errors §3 rule 3): %r" % (noise, message),
                    )
                self.assertGreater(
                    len(message),
                    len(entry_point) + len("harness.factory refused "),
                    "the message carries the contract that was violated and not only a "
                    "class name (errors §3: 'a class name alone is not a refusal'): %r"
                    % (message,),
                )

    def test_hrn_8_9_drive_and_timings_raise_nothing_at_all(self):
        """HRN-8.9 `drive` and `timings` raise no refusal for any argument: the malformed case shapes are reported inside the record, and the cost record has no argument to refuse (driver §1, §7, errors §1, surface §2, §7)."""
        malformed = (
            "not a mapping",
            {},
            {"id": "", "steps": [pure_value()], "expect": ["zero-sum"]},
            {"id": CASE_ID, "steps": [], "expect": ["zero-sum"]},
            {"id": CASE_ID, "steps": [pure_value()], "expect": []},
            case(CASE_ID, [42], ["zero-sum"]),
            case(CASE_ID, [pure_value()], [{"kind": "zero-sum", "step": 9}]),
        )
        for value in malformed:
            with self.subTest(case=value):
                record = self.not_raised(
                    lambda value=value: self.ep("drive")(value),
                    "drive(%r)" % (value,),
                )
                self.assertEqual(
                    as_mapping(record, "the case-result record")["verdict"],
                    "fail",
                    "a case the driver will not run is reported as a fail inside the "
                    "record and never raised (driver §1, §7, errors §1): %r" % (record,),
                )
        timings = self.not_raised(
            lambda: self.ep("timings")(),
            "timings()",
        )
        self.assertIn(
            "hands",
            as_mapping(timings, "the timings record"),
            "timings() has no argument and nothing to refuse (surface §7, errors §1): "
            "%r" % (sorted(timings),),
        )


if __name__ == "__main__":
    unittest.main()
