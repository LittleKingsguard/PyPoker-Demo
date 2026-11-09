"""surface.md §1 rule 2 — an invalid argument is refused by an error naming the contract.

`docs/L2/features/surface.md` §1 and §3–§9, `docs/L2/features/encodings.md` §2 and §5,
`docs/L1/e2e-surface.md` §2 (failure).  No entry point coerces a value, substitutes a
default, swallows an error or returns part of a record, and **the error's class is free**
(`docs/L1/e2e-surface.md` §2, `docs/L3/features/errors.md`), so every case below asserts
the refusal and that its message names the violated contract — never the class, never a
private name.

The readout each case mutilates is a real one: `engine.readout`'s own at a decision of the
invented seed, so "a readout missing a carried field" means the mapping the engine hands a
policy with one of its ten facts taken away (D-13).
"""

import os
import sys
import unittest

try:  # collected as part of a package
    from . import _join_support as S
except ImportError:  # collected as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _join_support as S  # noqa: E402


class Refusals(S.JoinCase):
    """surface.md §1 rule 2, across the seven entry points of `features`."""

    def real_readout(self):
        """One real readout at a first decision: the mapping a policy is handed."""
        return S.JoinCase.readout(self, self.new_hand(S.SEED_ENCODE))

    def test_refusals_01_build_encoder_refuses_a_name_it_does_not_declare(self):
        """§4 build_encoder refuses a name that is not one of the two, naming it."""
        for bad in (S.UNDECLARED_ENCODING, "", "card_tokens", "FLAT-NUMERIC",
                    "Flat-Numeric", "flat-numeric ", "flat_numeric", None, 7):
            with self.subTest(name=bad):
                self.assert_refused(
                    lambda bad=bad: self.build_encoder(bad),
                    "build_encoder(%r) must be refused, because an encoder exists only by "
                    "a declared encoding and no name is coerced to one (surface.md §4)"
                    % (bad,),
                )
        for bad in (S.UNDECLARED_ENCODING, "Flat-Numeric", "flat_numeric"):
            with self.subTest(named=bad):
                self.assert_refused(
                    lambda bad=bad: self.build_encoder(bad),
                    "build_encoder(%r) must be refused with that name in the error, "
                    "because the caller has to know which spelling named nothing "
                    "(surface.md §4)" % (bad,),
                    words=(bad,),
                )

    def test_refusals_02_a_value_that_is_not_an_encoder_is_refused(self):
        """§5, §6 observation_spec and encode refuse a value that is not an encoder."""
        readout = self.real_readout()
        spec = self.observation_spec(self.encoder("flat-numeric"))
        catalogue = self.encodings()
        for bad in (None, "flat-numeric", {}, spec, catalogue, object(), [], 1, ("flat-numeric",)):
            with self.subTest(value=type(bad).__name__):
                self.assert_refused(
                    lambda bad=bad: self.observation_spec(bad),
                    "observation_spec(%r) must be refused, because an encoder is a value "
                    "this module built and no caller can rebuild one (surface.md §5): the "
                    "value is not an encoder" % (bad,),
                    words=("encoder",),
                )
                self.assert_refused(
                    lambda bad=bad: self.encode(bad, readout),
                    "encode(%r, readout) must be refused, because one observation comes "
                    "from one declared encoding (surface.md §6): the value is not an "
                    "encoder" % (bad,),
                    words=("encoder",),
                )

    def test_refusals_03_encode_refuses_a_readout_missing_a_carried_field(self):
        """§6 encode refuses a readout missing a field this encoding carries, naming it."""
        readout = self.real_readout()
        for name in S.ENCODING_NAMES:
            encoder = self.encoder(name)
            for field in S.CARRIED_FACTS:
                missing = {key: value for key, value in readout.items() if key != field}
                with self.subTest(encoding=name, missing=field):
                    self.assert_named_refusal(
                        lambda encoder=encoder, missing=missing: self.encode(encoder, missing),
                        "encode",
                        "%r refuses a readout with no %r, because the observation carries "
                        "it and no field is defaulted (surface.md §6, encodings.md §2): "
                        "the refusal must name the entry point and the missing field, so "
                        "a bare lookup error from inside the module does not read as this "
                        "refusal (surface.md §1 rule 2)" % (name, field),
                        words=(field,),
                    )

    def test_refusals_04_encode_refuses_a_carried_field_it_cannot_represent(self):
        """§6 encode refuses a carried fact that cannot be represented, naming it."""
        readout = self.real_readout()
        card = tuple(readout["hole"])[0]
        unrepresentable = [
            ("street", "flop2", ("street",)),
            ("street", "", ("street",)),
            ("hole", tuple(readout["hole"])[:1], ("hole",)),
            ("hole", tuple(readout["hole"]) + (card,), ("hole",)),
            ("board", (card,) * 6, ("board",)),
            ("stacks", (int(readout["stacks"][0]),), ("stacks",)),
            ("pot", "3", ("pot",)),
            ("pot", -1, ("pot",)),
            ("to_call", None, ("to_call",)),
            ("limit", str(int(readout["limit"][0])), ("limit",)),
            ("history", [S.INVENTED_ENTRY], ("history",)),
        ]
        for name in S.ENCODING_NAMES:
            encoder = self.encoder(name)
            for fact, value, words in unrepresentable:
                changed = dict(readout)
                changed[fact] = value
                with self.subTest(encoding=name, fact=fact, value=value):
                    self.assert_refused(
                        lambda encoder=encoder, changed=changed: self.encode(encoder, changed),
                        "%r refuses a %r it cannot represent, instead of clamping it or "
                        "substituting a default (surface.md §6, errors.md): %r"
                        % (name, fact, value),
                        words=words,
                    )

    def test_refusals_05_encode_refuses_a_value_that_is_not_a_readout_mapping(self):
        """§6 encode refuses a readout that is not a mapping, and never a partial record."""
        for name in S.ENCODING_NAMES:
            encoder = self.encoder(name)
            for bad in (None, [], (), "readout", 40, object()):
                with self.subTest(encoding=name, value=type(bad).__name__):
                    self.assert_refused(
                        lambda encoder=encoder, bad=bad: self.encode(encoder, bad),
                        "%r refuses a value that is not a readout mapping, because the "
                        "readout arrives as a mapping of the eleven facts and no entry "
                        "point returns part of a record (surface.md §6, encodings.md §5)"
                        % (name,),
                        words=("readout",),
                    )
            self.assert_refused(
                lambda encoder=encoder: self.encode(encoder, {}),
                "%r refuses a mapping that carries none of the nine fields it carries, "
                "naming a field it needs (surface.md §6)" % (name,),
            )

    def test_refusals_06_legal_indices_refuses_an_empty_list_a_non_sequence_and_an_unknown(self):
        """§8 legal_indices refuses an empty sequence, a non-sequence and an unknown action."""
        for bad in ((), [], (S.UNDECLARED_DESCRIPTOR,), None, 0, 1.5, object()):
            with self.subTest(value=bad):
                self.assert_refused(
                    lambda bad=bad: self.legal_indices(bad),
                    "legal_indices(%r) must be refused: a decision has at least one legal "
                    "action, and the argument must be a sequence of descriptors "
                    "(surface.md §8)" % (bad,),
                )
        for bad in ("fold", "check-call", "raise"):
            with self.subTest(string=bad):
                self.assert_refused(
                    lambda bad=bad: self.legal_indices(bad),
                    "legal_indices(%r) must be refused: a str is a sequence of characters "
                    "and not a sequence of descriptors (surface.md §8)" % (bad,),
                    words=("sequence",),
                )
        for bad in ([S.UNDECLARED_DESCRIPTOR], ["fold", S.UNDECLARED_DESCRIPTOR],
                    ["check_call"], ["CHECK-CALL"]):
            with self.subTest(descriptors=bad):
                self.assert_refused(
                    lambda bad=bad: self.legal_indices(bad),
                    "legal_indices(%r) must be refused, because no fold is substituted for "
                    "an unknown action and the error names the descriptor it did not "
                    "recognize (surface.md §8, D-2)" % (bad,),
                    words=(bad[-1],),
                )

    def test_refusals_07_decode_action_refuses_a_non_integer_and_a_foreign_index(self):
        """§9 decode_action refuses a non-integer and an index outside {0, 1, 2}."""
        for bad in (-1, 3, 99, -(2 ** 40), 2 ** 40):
            with self.subTest(index=bad):
                self.assert_refused(
                    lambda bad=bad: self.decode_action(bad),
                    "decode_action(%r) must be refused: the vocabulary is 0, 1 and 2 and "
                    "an unknown action is never mapped to a default (surface.md §9, D-2)"
                    % (bad,),
                )
        for bad in ("1", "fold", 1.0, 2.0, None, [1], (1,), object()):
            with self.subTest(value=bad):
                self.assert_refused(
                    lambda bad=bad: self.decode_action(bad),
                    "decode_action(%r) must be refused, because the index is an integer "
                    "and no entry point coerces a value (surface.md §1 rule 2, §9)" % (bad,),
                    words=("integer",),
                )

    def test_refusals_08_decode_action_refuses_a_bool_index(self):
        """§9 decode_action refuses a bool, because a bool is not an index."""
        # `True` is an `int` in Python and `False` is `0`, so a case that only passed
        # `1.0` and `"1"` would leave the one coercion a caller can make by accident
        # unasserted: `surface.md` §9 refuses "a value that is not an integer, a `bool`
        # included" and `docs/L1/e2e-surface.md` §2 refuses every silent coercion.
        for bad in (True, False):
            with self.subTest(index=bad):
                self.assert_named_refusal(
                    lambda bad=bad: self.decode_action(bad),
                    "decode_action",
                    "decode_action(%r) must be refused, because a bool is not one of the "
                    "three indices and no entry point coerces a value (surface.md §9, "
                    "§1 rule 2): the refusal names the entry point and the violated "
                    "integer contract" % (bad,),
                    words=("integer",),
                )


if __name__ == "__main__":
    unittest.main()
