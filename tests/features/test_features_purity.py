"""FEA-10 -- purity: no randomness, no hidden state, and an import boundary.

``docs/L2/features/surface.md`` §1; ``docs/L3/features/README.md`` §3;
``docs/L3/features/layout.md`` §3; ``docs/L3/features/guardrails.md`` G5, G12;
``docs/L1/assumptions.md`` ASM-2; ``docs/L1/battery.md`` §3 FAM-16.

Every one of the seven names is a function of its arguments alone: `engine.new_hand`
is the project's single seeding point, and `features` never draws from either global
stream.
"""

import os
import random
import sys
import unittest

import numpy

try:  # discovered as part of a tests.features package
    from . import _features_support as S
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _features_support as S  # noqa: E402


# --------------------------------------------------------------------------
# The anchors FEA-10.1 and FEA-10.2 hand each call
# --------------------------------------------------------------------------
# A comparison of the stream "as it was" with the stream "as it is left" is only a
# statement about the call when the state before the call is one the call did not
# install -- otherwise a name that seeds a global to a fixed value passes whenever an
# earlier case in the session already left the stream in exactly that state, which is
# what a whole-directory run tends to do.  So each case anchors on a *mid-stream*
# state, two draws past a seed of the battery's own, and puts the stream back on that
# anchor before EVERY call (the technique of
# ``tests/integration/features/test_join_purity.py``::FAM-2.13, ``guardrails.md`` G5,
# ASM-2).
#
# The anchor comes from a private generator of the same class, not from the global
# one, for two reasons: taking it leaves the stream the case is about untouched, and
# it is the same state on every run, whatever any earlier case did.  The number is the
# battery's own invented seed: no seed, constant or entry point of the module is used
# here, and ``features`` declares no seed to use (``surface.md`` §1, D-12).
ANCHOR_SEED = 20250101
ANCHOR_DRAWS = 2


def random_anchor():
    """A mid-stream state of the global `random` generator, as ``getstate`` spells it."""
    generator = random.Random(ANCHOR_SEED)
    for _draw in range(ANCHOR_DRAWS):
        generator.random()
    return generator.getstate()


def numpy_anchor():
    """A mid-stream state of numpy's legacy global, as ``get_state`` spells it."""
    generator = numpy.random.RandomState(ANCHOR_SEED)
    generator.random_sample(ANCHOR_DRAWS)
    return generator.get_state()


class FEA10Purity(S.FeaturesCase):
    """The seven names draw no randomness, keep no state and import nothing beside numpy."""

    # -- the calls, one per entry point ------------------------------------
    def calls(self):
        """One valid call of each of the seven names, labelled by the name."""
        F = self.surface()
        record = S.readout(street="flop", history=S.history_entries(2))
        encoder = F.build_encoder(S.FLAT)
        return (
            ("encodings", lambda: F.encodings()),
            ("build_encoder", lambda: F.build_encoder(S.TOKENS)),
            ("observation_spec", lambda: F.observation_spec(encoder)),
            ("encode", lambda: F.encode(encoder, record)),
            ("action_space", lambda: F.action_space()),
            ("legal_indices", lambda: F.legal_indices(S.ACTIONS)),
            ("decode_action", lambda: F.decode_action(2)),
        )

    def plain(self, value):
        """A returned value as plain comparable data (an observation becomes its slots)."""
        if hasattr(value, "shape"):
            return S.floats(value)
        return value

    # -- the two global streams -------------------------------------------
    def test_fea10_1_no_name_moves_the_global_random_stream(self):
        """FEA-10.1 none of the seven names draws from, seeds or advances the global
        `random` stream: `engine.new_hand` is the project's single seeding point
        (surface.md §1, ASM-2, guardrails.md G5).

        The stream is put back on a mid-stream anchor before every call, so the state
        before the call is one the module did not install: a name that draws, that
        seeds the stream to a fixed value (even one the session already reached), or
        that reseeds it to a value computed from its arguments leaves a state that is
        not this anchor, in any collection order.
        """
        anchor = random_anchor()
        untouched = random.getstate()
        try:
            for name, call in self.calls():
                with self.subTest(name=name):
                    random.setstate(anchor)
                    before = S.random_state()
                    call()
                    self.assertEqual(
                        S.random_state(), before,
                        "features.%s must leave the global random stream byte-identical "
                        "at the mid-stream anchor it was handed -- it drew, seeded or "
                        "advanced the stream (surface.md §1, ASM-2, guardrails.md G5)"
                        % (name,),
                    )
        finally:
            random.setstate(untouched)

    def test_fea10_2_no_name_moves_the_numpy_random_stream(self):
        """FEA-10.2 none of the seven names draws from, seeds or advances numpy's global
        random state (surface.md §1, ASM-2, guardrails.md G5).

        Anchored exactly as FEA-10.1, through ``numpy.random.get_state``/``set_state``:
        the state is a tuple holding an array, so the comparison is
        ``_features_support.numpy_state``'s plain comparable form -- name, the key
        array's bytes, the position and the two gaussian fields -- and never ``==`` on
        the raw tuple.
        """
        anchor = numpy_anchor()
        untouched = numpy.random.get_state()
        try:
            for name, call in self.calls():
                with self.subTest(name=name):
                    numpy.random.set_state(anchor)
                    before = S.numpy_state()
                    call()
                    self.assertEqual(
                        S.numpy_state(), before,
                        "features.%s must leave numpy.random's global state unchanged at "
                        "the mid-stream anchor it was handed -- it drew, seeded or "
                        "advanced the stream (surface.md §1, guardrails.md G5)"
                        % (name,),
                    )
        finally:
            numpy.random.set_state(untouched)

    # -- determinism -------------------------------------------------------
    def test_fea10_3_every_name_is_deterministic(self):
        """FEA-10.3 two calls of each of the seven names give equal values: every name is
        a function of its arguments alone (surface.md §1, §3-§9)."""
        spec_of = self.ep("observation_spec")
        for name, call in self.calls():
            with self.subTest(name=name):
                first = call()
                second = call()
                if name == "build_encoder":
                    self.assertEqual(
                        spec_of(first), spec_of(second),
                        "two encoders built from one name declare equal specs "
                        "(surface.md §4): the encoder itself is opaque and never compared",
                    )
                else:
                    self.assertEqual(
                        self.plain(first), self.plain(second),
                        "features.%s is a function of its arguments alone, so two calls "
                        "give equal values (surface.md §1)" % (name,),
                    )

    def test_fea10_4_the_names_hold_no_state_across_other_work(self):
        """FEA-10.4 the three declarations are unchanged by whatever was built, encoded or
        decoded in between: the module keeps no state and no cache (surface.md §1, §3,
        §5, §7; guardrails.md G4)."""
        F = self.surface()
        encoder = F.build_encoder(S.FLAT)
        before = {
            "encodings": F.encodings(),
            "spec": F.observation_spec(encoder),
            "action_space": F.action_space(),
            "legal_indices": F.legal_indices(("raise", "fold")),
            "decode_action": [F.decode_action(index) for index in (0, 1, 2)],
        }
        for _repeat in range(3):
            F.encode(F.build_encoder(S.TOKENS),
                     S.readout(street="river", history=S.history_entries(9)))
            F.encode(encoder, S.readout(street="turn", seat=(1, False)))
            F.legal_indices(S.ACTIONS)
            F.decode_action(0)
            F.encodings()
        after = {
            "encodings": F.encodings(),
            "spec": F.observation_spec(encoder),
            "action_space": F.action_space(),
            "legal_indices": F.legal_indices(("raise", "fold")),
            "decode_action": [F.decode_action(index) for index in (0, 1, 2)],
        }
        for key in before:
            with self.subTest(declaration=key):
                self.assertEqual(
                    after[key], before[key],
                    "features.%s is a fixed declaration, not a function of what was done "
                    "before it (surface.md §1): %r != %r" % (key, after[key], before[key]),
                )

    # -- the import boundary ----------------------------------------------
    def test_fea10_6_a_fresh_interpreter_imports_nothing_beside_numpy(self):
        """FEA-10.6 a child interpreter that imports `features` itself reports: it
        imports cleanly, pokerkit, torch, engine, agents, evaluation, training and harness
        are all absent from its `sys.modules` afterwards, and `features.__all__` is the
        seven names (layout.md §3, guardrails.md G12, G14).

        A separate process is the only place the boundary is decidable: this process's
        `sys.modules` already holds whatever pytest collected first -- in a whole-tree
        run, `tests/e2e` imports `features` before this battery -- so no case here reads
        this process's import delta.
        """
        self.ep("encodings")
        report = S.import_boundary_report()
        self.assertTrue(
            report["imported"],
            "'import features' must succeed in a fresh interpreter before the boundary "
            "can be read (layout.md §3): %r" % (report,),
        )
        self.assertEqual(
            report["present"], [],
            "a fresh interpreter that imports features must leave pokerkit, torch, engine, "
            "agents, evaluation, training and harness out of sys.modules (layout.md §3, "
            "guardrails.md G12): %r is present" % (report["present"],),
        )
        for forbidden in S.BOUNDARY:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(
                    forbidden, {name.split(".")[0] for name in report["added"]},
                    "importing features must not add %r or any of its submodules to a "
                    "fresh interpreter's sys.modules (layout.md §3, guardrails.md G12): %r"
                    % (forbidden, sorted(report["added"])[:20]),
                )
        self.assertIn(
            "features", {name.split(".")[0] for name in report["added"]},
            "a fresh interpreter really imported features, so the boundary it reports is "
            "the one this case is about (layout.md §3): %r"
            % (sorted(report["added"])[:20],),
        )
        self.assertEqual(
            tuple(report["all"]), S.NINE,
            "the child's features.__all__ is exactly the seven declared entry points, in "
            "the declared order (layout.md §2, guardrails.md G14, D-12): %r"
            % (report["all"],),
        )


if __name__ == "__main__":
    unittest.main()
